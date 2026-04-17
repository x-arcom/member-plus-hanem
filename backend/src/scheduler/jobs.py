"""
DB-tracked scheduled jobs — PRD §17.

All jobs are idempotent. Status tracked in `scheduled_jobs` table.
Each job function takes a DB session + optional `now` for testing.

Job types:
  1. generate_monthly_coupons — 28th of month 09:00 KSA
  2. renewal_charge — per-member, scheduled on subscription.created
  3. grace_period_expiry — per-member, 3 days after charge.failed
  4. remove_from_group — per-member, at current_period_end
  5. group_health_check — daily 03:00 KSA

Shared retry rules (PRD §17.6):
  - 5xx/timeout: 3× with backoff 1s, 2s, 4s
  - 429: wait Retry-After header
  - 401: force refresh token, retry once
  - 404/other 4xx: do NOT retry
"""
import logging
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional

logger = logging.getLogger("scheduler.jobs")


# ---------------------------------------------------------------------------
# Job runner — picks up pending jobs from DB and executes them
# ---------------------------------------------------------------------------
def run_pending_jobs(
    session_factory: Callable,
    now: Optional[datetime] = None,
    max_per_tick: int = 100,
) -> List[Dict]:
    """Pick up pending jobs where scheduled_for <= now, execute each, update status.

    Returns a list of results per job.
    """
    from database.models import ScheduledJob

    now = now or datetime.utcnow()
    db = session_factory()
    results = []

    try:
        pending = (
            db.query(ScheduledJob)
            .filter(
                ScheduledJob.status == "pending",
                ScheduledJob.scheduled_for <= now,
                ScheduledJob.attempts < ScheduledJob.max_attempts,
            )
            .order_by(ScheduledJob.scheduled_for)
            .limit(max_per_tick)
            .all()
        )

        for job in pending:
            job.status = "running"
            job.attempts += 1
            db.commit()

            try:
                handler = _JOB_HANDLERS.get(job.job_type)
                if not handler:
                    job.status = "skipped"
                    job.error_message = f"Unknown job type: {job.job_type}"
                    db.commit()
                    results.append({"job_id": job.id, "status": "skipped"})
                    continue

                handler(db, job)
                job.status = "completed"
                db.commit()
                results.append({"job_id": job.id, "status": "completed", "type": job.job_type})
                logger.info("job %s (%s) completed", job.id, job.job_type)

            except Exception as exc:
                job.status = "failed" if job.attempts >= job.max_attempts else "pending"
                job.error_message = str(exc)[:500]
                db.commit()
                results.append({"job_id": job.id, "status": "failed", "error": str(exc)[:200]})
                logger.warning("job %s (%s) failed: %s", job.id, job.job_type, exc)

    finally:
        db.close()

    return results


# ---------------------------------------------------------------------------
# Job: generate_monthly_coupons — PRD §17.1
# ---------------------------------------------------------------------------
def _job_generate_monthly_coupons(db, job) -> None:
    """Runs on 28th. Generates gift + free shipping coupons for next month.

    - UNIQUE (member_id, month) prevents duplicates.
    - If gift not configured by merchant: skip gift, create alert.
    - Rate limit: max 10 Salla API calls/sec (handled by SallaClient).
    """
    from database.models import Member, MembershipPlan, GiftCoupon, FreeShippingCoupon
    import secrets

    now = datetime.utcnow()
    next_month = (now.replace(day=28) + timedelta(days=5)).replace(day=1)
    month_str = next_month.strftime("%Y-%m")
    last_day = (next_month.replace(day=28) + timedelta(days=5)).replace(day=1) - timedelta(seconds=1)

    merchant_id = job.merchant_id
    if not merchant_id:
        raise ValueError("generate_monthly_coupons requires merchant_id")

    members = db.query(Member).filter(
        Member.merchant_id == merchant_id,
        Member.status.in_(["active", "grace_period"]),
    ).all()

    for member in members:
        plan = db.query(MembershipPlan).filter(MembershipPlan.id == member.plan_id).first()
        if not plan:
            continue

        # Free shipping coupon
        existing_ship = db.query(FreeShippingCoupon).filter(
            FreeShippingCoupon.member_id == member.id,
            FreeShippingCoupon.month == month_str,
        ).first()
        if not existing_ship:
            code = f"FS-{secrets.token_hex(4).upper()}"
            db.add(FreeShippingCoupon(
                member_id=member.id,
                merchant_id=merchant_id,
                month=month_str,
                coupon_code=code,
                quota=plan.free_shipping_uses,
                expires_at=last_day,
            ))

        # Gift coupon (Gold tier only per PRD — Silver has no monthly gift)
        if plan.tier == "gold":
            existing_gift = db.query(GiftCoupon).filter(
                GiftCoupon.member_id == member.id,
                GiftCoupon.month == month_str,
            ).first()
            if not existing_gift:
                code = f"GIFT-{secrets.token_hex(4).upper()}"
                db.add(GiftCoupon(
                    member_id=member.id,
                    merchant_id=merchant_id,
                    plan_id=plan.id,
                    month=month_str,
                    coupon_code=code,
                    gift_description_ar=plan.gift_name_ar,
                    gift_description_en=plan.gift_name_en,
                    status="generated",
                    expires_at=last_day,
                ))

    db.commit()
    logger.info("generated monthly coupons for merchant %s, month %s", merchant_id, month_str)


# ---------------------------------------------------------------------------
# Job: grace_period_expiry — PRD §17.3
# ---------------------------------------------------------------------------
def _job_grace_period_expiry(db, job) -> None:
    """Created on subscription.charge.failed. Cancellable if charge succeeds.

    Execute: Remove from Salla Group. Call Salla Cancel. Set status=expired.
    """
    from database.models import Member

    member_id = job.member_id
    if not member_id:
        raise ValueError("grace_period_expiry requires member_id")

    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        return

    # Guard: only process if still in grace_period (PRD §21 R-02)
    if member.status != "grace_period":
        logger.info("grace_period_expiry skipped — member %s status is %s", member_id, member.status)
        return

    if member.grace_period_ends_at and member.grace_period_ends_at > datetime.utcnow():
        # Not yet expired — reschedule
        raise ValueError("Grace period not yet ended")

    member.status = "expired"
    # TODO Phase 3: call Salla Cancel Subscription API
    # TODO Phase 3: remove from Salla Customer Group
    db.commit()
    logger.info("member %s expired after grace period", member_id)


# ---------------------------------------------------------------------------
# Job: remove_from_group — PRD §17.4
# ---------------------------------------------------------------------------
def _job_remove_from_group(db, job) -> None:
    """Created on subscription.cancelled. Runs at current_period_end.

    Member paid for full period — we only remove them on end date.
    """
    from database.models import Member

    member_id = job.member_id
    if not member_id:
        raise ValueError("remove_from_group requires member_id")

    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        return

    if member.status != "cancelled":
        logger.info("remove_from_group skipped — member %s status is %s", member_id, member.status)
        return

    if member.current_period_end and member.current_period_end > datetime.utcnow():
        raise ValueError("Period not yet ended")

    member.status = "expired"
    # TODO Phase 3: Salla Cancel + remove from Customer Group
    db.commit()
    logger.info("member %s removed from group after period end", member_id)


# ---------------------------------------------------------------------------
# Job: group_health_check — PRD §17.5
# ---------------------------------------------------------------------------
def _job_group_health_check(db, job) -> None:
    """Daily 03:00 KSA.

    - Verify all Customer Groups exist (recreate if missing).
    - Verify each active member is in correct group.
    - At-risk detection: last_order_at < NOW()-45d.
    """
    from database.models import Member

    merchant_id = job.merchant_id
    if not merchant_id:
        raise ValueError("group_health_check requires merchant_id")

    now = datetime.utcnow()
    cutoff = now - timedelta(days=45)

    # At-risk detection
    at_risk_updated = 0
    members = db.query(Member).filter(
        Member.merchant_id == merchant_id,
        Member.status == "active",
    ).all()

    for m in members:
        should_be_at_risk = (m.last_order_at is None or m.last_order_at < cutoff)
        if m.is_at_risk != should_be_at_risk:
            m.is_at_risk = should_be_at_risk
            at_risk_updated += 1

    # TODO Phase 3: Verify Salla Customer Groups exist via SallaClient
    # TODO Phase 3: Verify member-group membership matches DB

    if at_risk_updated:
        db.commit()
        logger.info("health check: %d at-risk flags updated for merchant %s", at_risk_updated, merchant_id)


# ---------------------------------------------------------------------------
# Job: renewal_charge — PRD §17.2
# ---------------------------------------------------------------------------
def _job_renewal_charge(db, job) -> None:
    """Call Salla Charge Subscription API. Wait for webhook.

    PRD §17.2: Do NOT update records before webhook confirms.
    """
    # Phase 3 stub — requires real Salla Recurring Payments integration
    logger.info("renewal_charge stub — will be wired in Phase 3 (Salla integration)")


# ---------------------------------------------------------------------------
# Handler registry
# ---------------------------------------------------------------------------
_JOB_HANDLERS = {
    "generate_monthly_coupons": _job_generate_monthly_coupons,
    "grace_period_expiry": _job_grace_period_expiry,
    "remove_from_group": _job_remove_from_group,
    "group_health_check": _job_group_health_check,
    "renewal_charge": _job_renewal_charge,
}


# ---------------------------------------------------------------------------
# Helper: create a scheduled job
# ---------------------------------------------------------------------------
def schedule_job(
    db,
    job_type: str,
    scheduled_for: datetime,
    merchant_id: Optional[str] = None,
    member_id: Optional[str] = None,
    max_attempts: int = 3,
) -> str:
    """Insert a job into the scheduled_jobs table. Returns the job id."""
    from database.models import ScheduledJob

    job = ScheduledJob(
        job_type=job_type,
        scheduled_for=scheduled_for,
        merchant_id=merchant_id,
        member_id=member_id,
        max_attempts=max_attempts,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job.id

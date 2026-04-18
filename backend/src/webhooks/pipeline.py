"""
Webhook processing pipeline — PRD §16.

Rules (§16.1):
1. Return 200 to Salla FAST. Process async via job queue.
2. INSERT webhook_events ON CONFLICT DO NOTHING. If rows_affected=0: skip.
3. Signature verification HMAC-SHA256 on raw body BEFORE JSON parsing.

Flow:
  raw body → verify HMAC → parse JSON → extract salla_event_id →
  INSERT webhook_events (idempotency) → if new: enqueue for processing →
  return 200 immediately.

The `process_event(event_id)` function is called by the job queue (or inline
for V1 simplicity) and dispatches to the correct handler.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from sqlalchemy.exc import IntegrityError

from webhooks.signature import verify_webhook_signature

logger = logging.getLogger("webhooks.pipeline")


def receive_and_store(
    session,
    raw_body: bytes,
    signature: Optional[str],
    secret: str,
) -> Tuple[int, Dict]:
    """Verify signature, parse JSON, store in webhook_events for idempotency.

    Returns (http_status, response_body).

    Per PRD §16.1: always return 200 quickly. Only return non-200 for
    signature failures (which are silent 401s, but we use 400 for clarity
    in our own logs).
    """
    # Step 1: Verify HMAC BEFORE parsing JSON (PRD §20)
    if not signature:
        return 400, {"status": "rejected", "reason": "missing-signature"}

    if not verify_webhook_signature(raw_body, signature, secret):
        return 400, {"status": "rejected", "reason": "invalid-signature"}

    # Step 2: Parse JSON
    try:
        payload = json.loads(raw_body.decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        return 400, {"status": "rejected", "reason": "invalid-json"}

    event_type = str(payload.get("event") or "").strip()
    salla_event_id = str(
        payload.get("event_id") or payload.get("id") or payload.get("salla_event_id") or ""
    ).strip()

    if not event_type:
        return 400, {"status": "rejected", "reason": "missing-event-type"}

    # Generate a fallback event id if Salla doesn't provide one
    if not salla_event_id:
        import hashlib
        salla_event_id = hashlib.sha256(raw_body).hexdigest()[:32]

    # Step 3: Extract merchant from payload
    merchant_salla_id = _extract_merchant_id(payload)

    # Step 4: INSERT with idempotency — ON CONFLICT DO NOTHING
    from database.models import WebhookEvent

    event = WebhookEvent(
        event_type=event_type,
        salla_event_id=salla_event_id,
        payload=raw_body.decode("utf-8", errors="replace"),
        status="received",
    )

    # Resolve merchant_id from salla_store_id if available
    if merchant_salla_id:
        from database.models import Merchant
        merchant = session.query(Merchant).filter(
            Merchant.salla_store_id == int(merchant_salla_id)
        ).first()
        if merchant:
            event.merchant_id = merchant.id

    try:
        session.add(event)
        session.flush()  # triggers the UNIQUE constraint check
        session.commit()
    except IntegrityError:
        session.rollback()
        # Already processed — idempotency hit (PRD §21 R-01)
        logger.info("webhook idempotency hit: %s", salla_event_id)
        return 200, {"status": "ok", "reason": "already-processed"}

    # Step 5: Process the event (V1: inline. V2: job queue.)
    try:
        event.status = "processing"
        session.commit()

        result = _dispatch(session, event.id, event_type, payload)

        event.status = "processed"
        session.commit()

        return 200, {
            "status": "ok",
            "event": event_type,
            "event_id": salla_event_id,
            **result,
        }

    except Exception as exc:
        logger.exception("webhook processing failed: %s %s", event_type, exc)
        event.status = "failed"
        event.error_message = str(exc)[:500]
        event.attempts += 1
        try:
            session.commit()
        except Exception:
            session.rollback()

        # Still return 200 so Salla doesn't retry forever (PRD §16.1)
        return 200, {"status": "ok", "reason": "processing-failed-will-retry"}


def _extract_merchant_id(payload: Dict) -> Optional[str]:
    """Extract salla_store_id from various webhook payload shapes."""
    for key in ("merchant", "store_id"):
        if payload.get(key):
            return str(payload[key])
    data = payload.get("data") or {}
    for key in ("store_id", "merchant_id", "merchant"):
        if isinstance(data, dict) and data.get(key):
            return str(data[key])
    return None


def _dispatch(session, event_db_id: str, event_type: str, payload: Dict) -> Dict:
    """Route to the correct handler. Unknown events are acknowledged."""
    handlers = {
        "app.store.authorize": _handle_app_authorize,
        "app.subscription.started": _handle_app_subscription_started,
        "app.subscription.renewed": _handle_app_subscription_renewed,
        "app.subscription.canceled": _handle_app_subscription_ended,
        "app.subscription.expired": _handle_app_subscription_ended,
        "app.uninstalled": _handle_app_uninstalled,
        "subscription.created": _handle_subscription_created,
        "subscription.charge.succeeded": _handle_charge_succeeded,
        "subscription.charge.failed": _handle_charge_failed,
        "subscription.updated": _handle_subscription_updated,
        "order.created": _handle_order_created,
        "order.cancelled": _handle_order_cancelled,
        "customer.updated": _handle_customer_updated,
    }

    handler = handlers.get(event_type)
    if handler:
        return handler(session, payload)

    logger.info("unhandled webhook event type: %s", event_type)
    return {"handled": False, "reason": "no-handler"}


# ---------------------------------------------------------------------------
# Event handlers — wired to real business logic per PRD §16
# ---------------------------------------------------------------------------

def _handle_app_authorize(session, payload) -> Dict:
    """PRD §16: Create merchant record. Set trial (7 days). Send welcome email.

    Salla sends merchant/store ID as top-level `merchant` field (integer).
    OAuth tokens are inside `data` object.
    """
    from database.models import Merchant, OAuthToken
    from auth.crypto import encrypt
    from datetime import timedelta

    data = payload.get("data") or {}

    # Salla puts store ID at top level, NOT inside data
    salla_store_id = payload.get("merchant") or payload.get("store_id") or data.get("store_id") or data.get("id")
    if not salla_store_id:
        return {"handled": False, "reason": "missing-store-id"}

    access_tok = str(data.get("access_token") or "")
    refresh_tok = str(data.get("refresh_token") or "")
    token_scope = str(data.get("scope") or "")
    expires_in = int(data.get("expires") or data.get("expires_in") or 1209600)

    existing = session.query(Merchant).filter(
        Merchant.salla_store_id == int(salla_store_id)
    ).first()
    if existing:
        existing.status = "trial"
        existing.access_token = encrypt(access_tok)
        existing.refresh_token = encrypt(refresh_tok)
        _upsert_oauth_token(session, existing.id, access_tok, refresh_tok, token_scope, expires_in)
        session.commit()
        return {"handled": True, "action": "merchant-reactivated", "merchant_id": existing.id}

    now = datetime.utcnow()
    merchant = Merchant(
        salla_store_id=int(salla_store_id),
        access_token=encrypt(access_tok),
        refresh_token=encrypt(refresh_tok),
        store_name="",
        status="trial",
        trial_ends_at=now + timedelta(days=7),
    )
    session.add(merchant)
    session.flush()

    _upsert_oauth_token(session, merchant.id, access_tok, refresh_tok, token_scope, expires_in)
    session.commit()
    session.refresh(merchant)

    logger.info("merchant %s created via app.store.authorize", merchant.id)
    return {"handled": True, "action": "merchant-created", "merchant_id": merchant.id}


def _upsert_oauth_token(session, merchant_id, access_tok, refresh_tok, scope, expires_in):
    """Create or update the OAuthToken row so SallaClient can find tokens."""
    from database.models import OAuthToken
    from auth.crypto import encrypt

    token = session.query(OAuthToken).filter(OAuthToken.merchant_id == merchant_id).first()
    if token:
        token.access_token = encrypt(access_tok)
        token.refresh_token = encrypt(refresh_tok)
        token.scope = scope
        token.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    else:
        session.add(OAuthToken(
            merchant_id=merchant_id,
            access_token=encrypt(access_tok),
            refresh_token=encrypt(refresh_tok),
            scope=scope,
            expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
        ))


def _handle_app_subscription_started(session, payload) -> Dict:
    """PRD §16: Merchant started paying us. If setup done → activate plans page."""
    from database.models import Merchant

    store_id = _extract_merchant_id(payload)
    if not store_id:
        return {"handled": False, "reason": "missing-store-id"}

    merchant = session.query(Merchant).filter(
        Merchant.salla_store_id == int(store_id)
    ).first()
    if not merchant:
        return {"handled": False, "reason": "merchant-not-found"}

    merchant.status = "active"
    merchant.activated_at = datetime.utcnow()

    # Determine SaaS plan from payload if available
    data = payload.get("data") or {}
    plan_name = str(data.get("plan") or data.get("plan_name") or "").lower()
    if "unlimited" in plan_name:
        merchant.our_plan = "unlimited"
    elif "pro" in plan_name:
        merchant.our_plan = "pro"
    else:
        merchant.our_plan = "starter"

    session.commit()
    logger.info("merchant %s activated (plan: %s)", merchant.id, merchant.our_plan)
    return {"handled": True, "action": "merchant-activated", "merchant_id": merchant.id}


def _handle_app_subscription_renewed(session, payload) -> Dict:
    """Salla fires app.subscription.renewed when merchant renews their app subscription."""
    from database.models import Merchant

    store_id = _extract_merchant_id(payload)
    if not store_id:
        return {"handled": False, "reason": "missing-store-id"}

    merchant = session.query(Merchant).filter(
        Merchant.salla_store_id == int(store_id)
    ).first()
    if not merchant:
        return {"handled": False, "reason": "merchant-not-found"}

    merchant.status = "active"
    session.commit()
    logger.info("merchant %s app subscription renewed", merchant.id)
    return {"handled": True, "action": "merchant-renewed", "merchant_id": merchant.id}


def _handle_app_subscription_ended(session, payload) -> Dict:
    """PRD §30: Full offboarding. Cancel ALL member subscriptions."""
    from database.models import Merchant, Member, MembershipPlan
    from benefits.engine import deactivate_all_benefits

    store_id = _extract_merchant_id(payload)
    if not store_id:
        return {"handled": False, "reason": "missing-store-id"}

    merchant = session.query(Merchant).filter(
        Merchant.salla_store_id == int(store_id)
    ).first()
    if not merchant:
        return {"handled": False, "reason": "merchant-not-found"}

    # Step 2: Cancel all active members
    active_members = session.query(Member).filter(
        Member.merchant_id == merchant.id,
        Member.status.in_(["active", "grace_period"]),
    ).all()

    for member in active_members:
        plan = session.query(MembershipPlan).filter(
            MembershipPlan.id == member.plan_id
        ).first()
        if plan:
            try:
                deactivate_all_benefits(session, member, plan)
            except Exception as exc:
                logger.warning("deactivation failed for member %s: %s", member.id, exc)
        member.status = "expired"

    # Step 6: Set merchant cancelled
    merchant.status = "cancelled"
    session.commit()

    logger.info("merchant %s offboarded, %d members expired", merchant.id, len(active_members))
    return {"handled": True, "action": "merchant-offboarded",
            "merchant_id": merchant.id, "members_expired": len(active_members)}


def _handle_app_uninstalled(session, payload) -> Dict:
    """Same as app.subscription.canceled — full offboarding."""
    return _handle_app_subscription_ended(session, payload)


def _handle_subscription_created(session, payload) -> Dict:
    """PRD §16: Create member. Add to Customer Group. Activate all benefits.

    This fires when a CUSTOMER subscribes to a merchant's membership plan
    via Salla's native checkout.
    """
    from database.models import Merchant, Member, MembershipPlan
    from benefits.engine import activate_all_benefits

    data = payload.get("data") or payload
    salla_subscription_id = str(data.get("subscription_id") or data.get("id") or "")
    salla_customer_id = data.get("customer_id") or data.get("customer", {}).get("id")
    store_id = _extract_merchant_id(payload)

    if not salla_customer_id or not store_id:
        return {"handled": False, "reason": "missing-customer-or-store"}

    merchant = session.query(Merchant).filter(
        Merchant.salla_store_id == int(store_id)
    ).first()
    if not merchant:
        return {"handled": False, "reason": "merchant-not-found"}

    # Determine tier from subscription data
    tier = "silver"
    product_name = str(data.get("product_name") or data.get("plan_name") or "").lower()
    if "gold" in product_name or "ذهب" in product_name:
        tier = "gold"

    plan = session.query(MembershipPlan).filter(
        MembershipPlan.merchant_id == merchant.id,
        MembershipPlan.tier == tier,
        MembershipPlan.status == "active",
    ).first()
    if not plan:
        return {"handled": False, "reason": f"no-active-{tier}-plan"}

    # Check for duplicate subscription (PRD §21 R-01)
    existing = session.query(Member).filter(
        Member.salla_subscription_id == salla_subscription_id,
    ).first() if salla_subscription_id else None
    if existing:
        return {"handled": True, "action": "member-already-exists", "member_id": existing.id}

    price = float(data.get("price") or data.get("amount") or plan.price)
    now = datetime.utcnow()

    member = Member(
        merchant_id=merchant.id,
        plan_id=plan.id,
        salla_customer_id=int(salla_customer_id),
        salla_subscription_id=salla_subscription_id or None,
        status="active",
        subscribed_price=price,
        free_shipping_quota=plan.free_shipping_uses,
        current_period_end=now + timedelta(days=30),
        next_renewal_at=now + timedelta(days=30),
    )
    session.add(member)
    session.flush()

    # Update merchant member count
    merchant.member_count = (merchant.member_count or 0) + 1

    # Activate all 6 benefits (PRD Appendix C: immediately)
    benefit_results = activate_all_benefits(session, member, plan)

    session.commit()
    logger.info("member %s created for merchant %s (tier: %s)", member.id, merchant.id, tier)
    return {
        "handled": True, "action": "member-created",
        "member_id": member.id, "tier": tier,
        "benefits": [r["benefit"] for r in benefit_results if r["status"] == "activated"],
    }


def _handle_charge_succeeded(session, payload) -> Dict:
    """PRD §16: Reset quotas. Generate new gift. Update period dates."""
    from database.models import Member, MembershipPlan
    from benefits.engine import reset_monthly_benefits

    data = payload.get("data") or payload
    salla_subscription_id = str(data.get("subscription_id") or data.get("id") or "")

    member = session.query(Member).filter(
        Member.salla_subscription_id == salla_subscription_id,
    ).first() if salla_subscription_id else None

    if not member:
        return {"handled": False, "reason": "member-not-found"}

    # Guard: only process if active or grace_period (PRD §15.1)
    if member.status == "grace_period":
        member.status = "active"
        member.grace_period_ends_at = None

    now = datetime.utcnow()
    member.current_period_end = now + timedelta(days=30)
    member.next_renewal_at = now + timedelta(days=30)

    plan = session.query(MembershipPlan).filter(MembershipPlan.id == member.plan_id).first()
    if plan:
        reset_monthly_benefits(session, member, plan)

    session.commit()
    logger.info("charge succeeded for member %s — quotas reset", member.id)
    return {"handled": True, "action": "renewal-processed", "member_id": member.id}


def _handle_charge_failed(session, payload) -> Dict:
    """PRD §16: Start 3-day grace period. Create expiry job."""
    from database.models import Member
    from scheduler.jobs import schedule_job

    data = payload.get("data") or payload
    salla_subscription_id = str(data.get("subscription_id") or data.get("id") or "")

    member = session.query(Member).filter(
        Member.salla_subscription_id == salla_subscription_id,
    ).first() if salla_subscription_id else None

    if not member:
        return {"handled": False, "reason": "member-not-found"}

    # Guard: only start grace if currently active (PRD §15.1)
    if member.status != "active":
        return {"handled": True, "action": "already-non-active", "status": member.status}

    now = datetime.utcnow()
    member.status = "grace_period"
    member.grace_period_ends_at = now + timedelta(days=3)

    # Schedule expiry job (PRD §17.3 — cancellable if charge succeeds)
    schedule_job(
        session,
        job_type="grace_period_expiry",
        scheduled_for=now + timedelta(days=3),
        member_id=member.id,
    )

    session.commit()
    logger.info("grace period started for member %s — expires %s",
                member.id, member.grace_period_ends_at)
    return {"handled": True, "action": "grace-started", "member_id": member.id}


def _handle_subscription_updated(session, payload) -> Dict:
    """PRD §16: Sync subscription data. Also detect cancellation — Salla sends
    cancellation as subscription.updated with status='cancelled', NOT as a
    separate subscription.cancelled event."""
    from database.models import Member
    from scheduler.jobs import schedule_job

    data = payload.get("data") or payload
    salla_subscription_id = str(data.get("subscription_id") or data.get("id") or "")

    member = session.query(Member).filter(
        Member.salla_subscription_id == salla_subscription_id,
    ).first() if salla_subscription_id else None

    if not member:
        return {"handled": False, "reason": "member-not-found"}

    # Detect cancellation via status field
    salla_status = str(data.get("status") or "").lower()
    if salla_status in ("cancelled", "canceled") and member.status in ("active", "grace_period"):
        member.status = "cancelled"
        member.cancelled_at = datetime.utcnow()
        if member.current_period_end:
            schedule_job(
                session,
                job_type="remove_from_group",
                scheduled_for=member.current_period_end,
                member_id=member.id,
            )
        session.commit()
        logger.info("member %s cancelled via subscription.updated — benefits active until %s",
                    member.id, member.current_period_end)
        return {"handled": True, "action": "cancellation-recorded", "member_id": member.id}

    # Sync fields from Salla if provided
    if data.get("price"):
        member.subscribed_price = float(data["price"])
    if data.get("next_renewal_at"):
        try:
            member.next_renewal_at = datetime.fromisoformat(str(data["next_renewal_at"]).replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass

    session.commit()
    return {"handled": True, "action": "subscription-synced", "member_id": member.id}


def _handle_order_created(session, payload) -> Dict:
    """PRD §16: Log to benefit_events. Update total_saved. Update last_order."""
    from database.models import Member, BenefitEvent
    from decimal import Decimal

    data = payload.get("data") or payload
    salla_customer_id = data.get("customer_id") or (data.get("customer") or {}).get("id")
    salla_order_id = data.get("order_id") or data.get("id")
    store_id = _extract_merchant_id(payload)

    if not salla_customer_id or not store_id:
        return {"handled": True, "action": "order-logged-no-member-context"}

    from database.models import Merchant
    merchant = session.query(Merchant).filter(
        Merchant.salla_store_id == int(store_id)
    ).first()
    if not merchant:
        return {"handled": True, "action": "order-logged-unknown-merchant"}

    member = session.query(Member).filter(
        Member.merchant_id == merchant.id,
        Member.salla_customer_id == int(salla_customer_id),
        Member.status.in_(["active", "grace_period"]),
    ).first()

    if not member:
        return {"handled": True, "action": "order-logged-non-member"}

    # Update last_order_at + clear at-risk
    member.last_order_at = datetime.utcnow()
    member.is_at_risk = False

    # Calculate discount savings — Salla puts discounts in data.amounts.discounts[]
    amounts = data.get("amounts") or {}
    discounts_list = amounts.get("discounts") or []
    discount_amount = 0.0
    if isinstance(discounts_list, list):
        for d in discounts_list:
            discount_amount += float(d.get("amount") or d.get("value") or 0)
    elif isinstance(amounts.get("total_discount"), (int, float)):
        discount_amount = float(amounts["total_discount"])
    if discount_amount > 0:
        member.total_saved_sar = float(member.total_saved_sar or 0) + discount_amount
        session.add(BenefitEvent(
            member_id=member.id,
            merchant_id=merchant.id,
            salla_order_id=int(salla_order_id) if salla_order_id else None,
            event_type="discount_applied",
            amount_saved=Decimal(str(discount_amount)),
        ))

    session.commit()
    return {"handled": True, "action": "order-logged", "member_id": member.id}


def _handle_order_cancelled(session, payload) -> Dict:
    """PRD §16: Restore free shipping credit. Atomic: used_count-1 WHERE used_count>0."""
    from database.models import Member, FreeShippingCoupon

    data = payload.get("data") or payload
    salla_customer_id = data.get("customer_id") or (data.get("customer") or {}).get("id")
    store_id = _extract_merchant_id(payload)

    if not salla_customer_id or not store_id:
        return {"handled": True, "action": "no-member-context"}

    from database.models import Merchant
    merchant = session.query(Merchant).filter(
        Merchant.salla_store_id == int(store_id)
    ).first()
    if not merchant:
        return {"handled": True, "action": "unknown-merchant"}

    member = session.query(Member).filter(
        Member.merchant_id == merchant.id,
        Member.salla_customer_id == int(salla_customer_id),
    ).first()

    if not member:
        return {"handled": True, "action": "non-member"}

    # PRD §21 R-04: Atomic restore
    now = datetime.utcnow()
    month_str = now.strftime("%Y-%m")
    coupon = session.query(FreeShippingCoupon).filter(
        FreeShippingCoupon.member_id == member.id,
        FreeShippingCoupon.month == month_str,
        FreeShippingCoupon.used_count > 0,
    ).first()

    if coupon:
        coupon.used_count -= 1
        if member.free_shipping_used > 0:
            member.free_shipping_used -= 1
        if coupon.status == "exhausted":
            coupon.status = "active"
        session.commit()
        logger.info("restored 1 free shipping credit for member %s", member.id)
        return {"handled": True, "action": "shipping-restored", "member_id": member.id}

    return {"handled": True, "action": "no-shipping-to-restore"}


def _handle_customer_updated(session, payload) -> Dict:
    """PRD §16: Refresh cached data. Never store contact info locally."""
    # We don't store customer PII per PRD §20. Just log the event.
    logger.info("customer.updated received — no cached data to refresh")
    return {"handled": True, "action": "customer-synced"}

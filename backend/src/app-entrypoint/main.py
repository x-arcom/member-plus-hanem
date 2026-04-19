"""
Member Plus — FastAPI Application Entrypoint

PRD V3.0 compliant. Routes use /api/v1/ versioning.
Auth via permanent access token → HttpOnly session cookie (PRD Appendix B).
Webhooks via idempotent pipeline (PRD §16).
"""
import sys
import logging
from contextlib import asynccontextmanager

try:
    from fastapi import FastAPI, Request, Depends, HTTPException, Query, Body
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
except ImportError:
    print("FastAPI not installed. Install with: pip install fastapi uvicorn")
    sys.exit(1)

sys.path.insert(0, "/Users/hanemrayess/Desktop/HANEMM/backend/src")

from config.loader import load_config, validate_config
from observability.logging import configure_logging, RequestIdMiddleware
from auth.session import require_merchant

_config = load_config()
configure_logging(environment=_config.environment)
logger = logging.getLogger(__name__)


def _db_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database.models import Base
    config = load_config()
    engine = create_engine(config.database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Member Plus backend...")
    try:
        config = load_config()
        validate_config(config)
        logger.info("Configuration loaded. Environment: %s", config.environment)
    except RuntimeError as e:
        logger.error("Configuration validation failed: %s", e)
        raise

    try:
        from scheduler.runner import start as start_scheduler, stop as stop_scheduler
        start_scheduler()
    except Exception:
        logger.info("Scheduler not available")
        stop_scheduler = lambda: None

    try:
        yield
    finally:
        stop_scheduler()
        logger.info("Member Plus backend stopped")


app = FastAPI(
    title="Member Plus",
    description="Salla Partner App — Paid membership programs for merchants",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}


# ---------------------------------------------------------------------------
# Dashboard access — PRD Appendix B
# ---------------------------------------------------------------------------
from auth.access import router as access_router
app.include_router(access_router)


# ---------------------------------------------------------------------------
# Webhooks — PRD §16 (idempotent pipeline)
# ---------------------------------------------------------------------------
@app.post("/webhooks/salla")
async def handle_webhook(request: Request):
    from webhooks.pipeline import receive_and_store

    body = await request.body()
    signature = request.headers.get("X-Salla-Signature")
    config = load_config()
    db = _db_session()

    try:
        status, response_body = receive_and_store(
            db, body, signature, config.salla_webhook_secret,
        )
        return JSONResponse(response_body, status_code=status)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Merchant API — /api/v1/merchant/* (PRD §18.1)
# ---------------------------------------------------------------------------
@app.get("/api/v1/merchant/overview")
async def merchant_overview(
    period: str = Query(default="30d"),
    merchant_id: str = Depends(require_merchant),
):
    """PRD §8.4: Member count by tier, revenue, churn, at-risk, ROI.
    Time filtered: 7d / 30d / 3m / 12m."""
    from datetime import timedelta
    from decimal import Decimal

    db = _db_session()
    try:
        from database.models import Merchant, Member, MembershipPlan, BenefitEvent
        merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
        if not merchant:
            raise HTTPException(404, "Merchant not found")

        # Time window
        now = datetime.utcnow()
        period_days = {"7d": 7, "30d": 30, "3m": 90, "12m": 365}.get(period, 30)
        window_start = now - timedelta(days=period_days)

        # All members for this merchant
        all_members = db.query(Member).filter(Member.merchant_id == merchant_id).all()

        active = [m for m in all_members if m.status == "active"]
        cancelled = [m for m in all_members if m.status in ("cancelled", "expired")]
        at_risk = [m for m in all_members if m.is_at_risk]

        # Tier breakdown
        plan_map = {}
        for p in db.query(MembershipPlan).filter(MembershipPlan.merchant_id == merchant_id).all():
            plan_map[p.id] = p

        gold_count = sum(1 for m in active if m.plan_id in plan_map and plan_map[m.plan_id].tier == "gold")
        silver_count = sum(1 for m in active if m.plan_id in plan_map and plan_map[m.plan_id].tier == "silver")

        # Revenue = sum of subscribed_price for active members (monthly recurring)
        monthly_revenue = sum(float(m.subscribed_price or 0) for m in active)

        # Total savings across all members
        total_saved = sum(float(m.total_saved_sar or 0) for m in all_members)

        # Churn: members who cancelled/expired in the time window
        churned_in_period = sum(
            1 for m in cancelled
            if m.cancelled_at and m.cancelled_at >= window_start
        )
        total_at_start = len(active) + churned_in_period
        churn_rate = round((churned_in_period / total_at_start * 100) if total_at_start > 0 else 0, 1)

        # New members in period
        new_in_period = sum(
            1 for m in all_members
            if m.created_at and m.created_at >= window_start
        )

        # Benefit cost = total_saved (what members saved = merchant's cost)
        benefit_cost = total_saved

        # ROI: app cost vs member revenue
        plan_prices = {"starter": 149, "pro": 299, "unlimited": 499}
        app_cost = plan_prices.get(merchant.our_plan, 149)
        net_value = monthly_revenue - benefit_cost - app_cost

        # Salla store ID for public reference
        salla_store_id = merchant.salla_store_id

        return {
            "store_name": merchant.store_name,
            "salla_store_id": salla_store_id,
            "status": merchant.status,
            "our_plan": merchant.our_plan,
            "trial_ends_at": merchant.trial_ends_at.isoformat() if merchant.trial_ends_at else None,
            "setup_completed": merchant.setup_completed,
            "setup_step": merchant.setup_step,
            "period": period,
            # KPIs
            "member_count": len(active),
            "gold_count": gold_count,
            "silver_count": silver_count,
            "monthly_revenue": round(monthly_revenue, 2),
            "total_saved": round(total_saved, 2),
            "churn_rate": churn_rate,
            "churned_in_period": churned_in_period,
            "new_in_period": new_in_period,
            "at_risk_count": len(at_risk),
            "cancelled_count": len(cancelled),
            # Financial
            "benefit_cost": round(benefit_cost, 2),
            "app_cost": app_cost,
            "net_value": round(net_value, 2),
        }
    finally:
        db.close()


@app.get("/api/v1/merchant/members")
async def merchant_members(
    tier: str = Query(None),
    status: str = Query(None),
    page: int = Query(1),
    per_page: int = Query(50),
    merchant_id: str = Depends(require_merchant),
):
    db = _db_session()
    try:
        from database.models import Member, MembershipPlan
        query = db.query(Member).filter(Member.merchant_id == merchant_id)

        if tier:
            plan_ids = [p.id for p in db.query(MembershipPlan).filter(
                MembershipPlan.merchant_id == merchant_id,
                MembershipPlan.tier == tier,
            ).all()]
            query = query.filter(Member.plan_id.in_(plan_ids))
        if status:
            query = query.filter(Member.status == status)

        total = query.count()
        members = query.order_by(Member.created_at.desc()).offset(
            (page - 1) * per_page
        ).limit(per_page).all()

        plan_map = {}
        for p in db.query(MembershipPlan).filter(MembershipPlan.merchant_id == merchant_id).all():
            plan_map[p.id] = p

        return {
            "members": [
                {
                    "id": m.id,
                    "salla_customer_id": m.salla_customer_id,
                    "tier": plan_map[m.plan_id].tier if m.plan_id in plan_map else "silver",
                    "tier_name_ar": plan_map[m.plan_id].display_name_ar if m.plan_id in plan_map else "",
                    "tier_name_en": plan_map[m.plan_id].display_name_en if m.plan_id in plan_map else "",
                    "status": m.status,
                    "subscribed_price": str(m.subscribed_price),
                    "current_period_end": m.current_period_end.isoformat() if m.current_period_end else None,
                    "next_renewal_at": m.next_renewal_at.isoformat() if m.next_renewal_at else None,
                    "is_at_risk": m.is_at_risk,
                    "total_saved_sar": str(m.total_saved_sar),
                    "free_shipping_used": m.free_shipping_used,
                    "free_shipping_quota": m.free_shipping_quota,
                    "last_order_at": m.last_order_at.isoformat() if m.last_order_at else None,
                    "cancelled_at": m.cancelled_at.isoformat() if m.cancelled_at else None,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in members
            ],
            "total": total,
            "page": page,
        }
    finally:
        db.close()


@app.get("/api/v1/merchant/plans")
async def merchant_plans(merchant_id: str = Depends(require_merchant)):
    db = _db_session()
    try:
        from database.models import MembershipPlan, PlanPriceVersion
        plans = db.query(MembershipPlan).filter(
            MembershipPlan.merchant_id == merchant_id,
        ).order_by(MembershipPlan.tier).all()

        return {
            "plans": [
                {
                    "id": p.id,
                    "tier": p.tier,
                    "display_name_ar": p.display_name_ar,
                    "display_name_en": p.display_name_en,
                    "price": str(p.price),
                    "status": p.status,
                    "discount_pct": str(p.discount_pct),
                    "free_shipping_uses": p.free_shipping_uses,
                    "gift_name_ar": p.gift_name_ar,
                    "gift_name_en": p.gift_name_en,
                    "salla_group_id": p.salla_group_id,
                }
                for p in plans
            ],
        }
    finally:
        db.close()


@app.get("/api/v1/merchant/settings")
async def merchant_settings(merchant_id: str = Depends(require_merchant)):
    db = _db_session()
    try:
        from database.models import Merchant
        m = db.query(Merchant).filter(Merchant.id == merchant_id).first()
        if not m:
            raise HTTPException(404, "Merchant not found")
        return {
            "store_name": m.store_name,
            "status": m.status,
            "our_plan": m.our_plan,
            "setup_completed": m.setup_completed,
            "dashboard_language": m.dashboard_language,
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Today's Focus Card — PRD §22.3
# ---------------------------------------------------------------------------
@app.get("/api/v1/merchant/focus")
async def todays_focus(merchant_id: str = Depends(require_merchant)):
    """PRD §22.3: ONE single contextual action. Priority order:
    1. Gift not configured within 3 days of month end
    2. Members in grace period near expiry
    3. Plan limit within 10 members
    4. Zero members after 7 days live
    5. All good
    """
    from datetime import datetime, timedelta
    db = _db_session()
    try:
        from database.models import Merchant, Member, GiftCoupon, MembershipPlan

        m = db.query(Merchant).filter(Merchant.id == merchant_id).first()
        if not m:
            raise HTTPException(404, "Merchant not found")

        now = datetime.utcnow()
        next_month = (now.replace(day=28) + timedelta(days=5)).replace(day=1)
        days_to_month_end = (next_month - now).days

        # Priority 1: Gift not configured within 3 days of month end
        if days_to_month_end <= 3:
            next_month_str = next_month.strftime("%Y-%m")
            gold_plan = db.query(MembershipPlan).filter(
                MembershipPlan.merchant_id == merchant_id,
                MembershipPlan.tier == "gold",
                MembershipPlan.status == "active",
            ).first()
            if gold_plan:
                has_gift_config = db.query(GiftCoupon).filter(
                    GiftCoupon.merchant_id == merchant_id,
                    GiftCoupon.month == next_month_str,
                ).first()
                if not has_gift_config:
                    return {
                        "priority": 1,
                        "type": "gift_not_configured",
                        "days_left": days_to_month_end,
                        "message_ar": f"الهدية الشهرية — {days_to_month_end} يوم متبقي",
                        "message_en": f"Configure next month's gift — {days_to_month_end} days left",
                        "action": "gift-config",
                    }

        # Priority 2: Members in grace period near expiry
        grace_count = db.query(Member).filter(
            Member.merchant_id == merchant_id,
            Member.status == "grace_period",
        ).count()
        if grace_count > 0:
            return {
                "priority": 2,
                "type": "grace_expiry",
                "count": grace_count,
                "message_ar": f"{grace_count} عضو قد يفقد الوصول اليوم",
                "message_en": f"{grace_count} member(s) may lose access today",
                "action": "members",
            }

        # Priority 3: Plan limit within 10 members
        active_count = db.query(Member).filter(
            Member.merchant_id == merchant_id,
            Member.status == "active",
        ).count()
        plan_limits = {"starter": 50, "pro": 200, "unlimited": 99999}
        limit = plan_limits.get(m.our_plan or "starter", 50)
        if limit - active_count <= 10 and limit != 99999:
            return {
                "priority": 3,
                "type": "plan_limit",
                "current": active_count,
                "limit": limit,
                "message_ar": "اقتراب من الحد — قم بترقية خطتك",
                "message_en": "Approaching limit — upgrade your plan",
                "action": "settings",
            }

        # Priority 4: Zero members after 7 days live
        if m.setup_completed and active_count == 0:
            days_live = (now - m.activated_at).days if m.activated_at else 0
            if days_live >= 7:
                return {
                    "priority": 4,
                    "type": "zero_members",
                    "days_live": days_live,
                    "message_ar": "أضف رابط العضوية إلى تنقل المتجر",
                    "message_en": "Add membership link to store navigation",
                    "action": "promote",
                }

        # Priority 5: All good
        return {
            "priority": 5,
            "type": "all_good",
            "message_ar": "لا يوجد إجراء مطلوب اليوم",
            "message_en": "No action required today",
            "action": None,
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Member Profile — PRD §18.1
# ---------------------------------------------------------------------------
@app.get("/api/v1/merchant/members/{member_id}")
async def member_profile(
    member_id: str,
    merchant_id: str = Depends(require_merchant),
):
    """PRD §18.1: Full history — charges, benefits, orders, total savings."""
    db = _db_session()
    try:
        from database.models import (
            Member, MembershipPlan, BenefitEvent,
            GiftCoupon, FreeShippingCoupon,
        )

        member = db.query(Member).filter(
            Member.id == member_id,
            Member.merchant_id == merchant_id,
        ).first()
        if not member:
            raise HTTPException(404, "Member not found")

        plan = db.query(MembershipPlan).filter(
            MembershipPlan.id == member.plan_id,
        ).first()

        benefit_events = db.query(BenefitEvent).filter(
            BenefitEvent.member_id == member_id,
        ).order_by(BenefitEvent.created_at.desc()).limit(50).all()

        gift_history = db.query(GiftCoupon).filter(
            GiftCoupon.member_id == member_id,
        ).order_by(GiftCoupon.month.desc()).all()

        shipping_history = db.query(FreeShippingCoupon).filter(
            FreeShippingCoupon.member_id == member_id,
        ).order_by(FreeShippingCoupon.month.desc()).all()

        return {
            "id": member.id,
            "salla_customer_id": member.salla_customer_id,
            "status": member.status,
            "plan": {
                "tier": plan.tier if plan else None,
                "display_name_ar": plan.display_name_ar if plan else None,
                "display_name_en": plan.display_name_en if plan else None,
            },
            "subscribed_price": str(member.subscribed_price),
            "current_period_end": member.current_period_end.isoformat() if member.current_period_end else None,
            "next_renewal_at": member.next_renewal_at.isoformat() if member.next_renewal_at else None,
            "grace_period_ends_at": member.grace_period_ends_at.isoformat() if member.grace_period_ends_at else None,
            "is_at_risk": member.is_at_risk,
            "total_saved_sar": str(member.total_saved_sar),
            "free_shipping_used": member.free_shipping_used,
            "free_shipping_quota": member.free_shipping_quota,
            "created_at": member.created_at.isoformat() if member.created_at else None,
            "benefit_events": [
                {
                    "event_type": e.event_type,
                    "amount_saved": str(e.amount_saved) if e.amount_saved else None,
                    "salla_order_id": e.salla_order_id,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in benefit_events
            ],
            "gift_history": [
                {
                    "month": g.month,
                    "gift_type": g.gift_type,
                    "status": g.status,
                    "coupon_code": g.coupon_code,
                }
                for g in gift_history
            ],
            "shipping_history": [
                {
                    "month": s.month,
                    "quota": s.quota,
                    "used_count": s.used_count,
                    "status": s.status,
                }
                for s in shipping_history
            ],
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Gift Management — PRD §8.4
# ---------------------------------------------------------------------------
@app.get("/api/v1/merchant/gift-coupons")
async def gift_coupons_list(
    month: str = Query(None),
    merchant_id: str = Depends(require_merchant),
):
    """PRD §18.1: Gift config + history + redemption stats."""
    db = _db_session()
    try:
        from database.models import GiftCoupon
        query = db.query(GiftCoupon).filter(GiftCoupon.merchant_id == merchant_id)
        if month:
            query = query.filter(GiftCoupon.month == month)
        coupons = query.order_by(GiftCoupon.month.desc()).limit(200).all()

        return {
            "coupons": [
                {
                    "id": c.id,
                    "member_id": c.member_id,
                    "month": c.month,
                    "coupon_code": c.coupon_code,
                    "gift_type": c.gift_type,
                    "gift_description_ar": c.gift_description_ar,
                    "gift_description_en": c.gift_description_en,
                    "status": c.status,
                    "expires_at": c.expires_at.isoformat() if c.expires_at else None,
                }
                for c in coupons
            ],
        }
    finally:
        db.close()


@app.post("/api/v1/merchant/gift-coupons/config")
async def configure_gift(
    payload: dict = Body(...),
    merchant_id: str = Depends(require_merchant),
):
    """PRD §18.1: Configure next month's gift. Validates category has products."""
    # Phase 2 stub — full Salla category validation in Phase 3
    return {
        "status": "configured",
        "gift_type": payload.get("gift_type"),
        "gift_value": payload.get("gift_value"),
        "gift_description_ar": payload.get("gift_description_ar"),
        "gift_description_en": payload.get("gift_description_en"),
    }


# ---------------------------------------------------------------------------
# Activity Log — PRD §14.10, §18.1
# ---------------------------------------------------------------------------
@app.get("/api/v1/merchant/activity")
async def activity_log(
    event_type: str = Query(None),
    member_id: str = Query(None),
    page: int = Query(1),
    per_page: int = Query(50),
    merchant_id: str = Depends(require_merchant),
):
    """PRD §18.1: Chronological feed of all events."""
    db = _db_session()
    try:
        from database.models import ActivityLog
        query = db.query(ActivityLog).filter(ActivityLog.merchant_id == merchant_id)
        if event_type:
            query = query.filter(ActivityLog.event_type == event_type)
        if member_id:
            query = query.filter(ActivityLog.member_id == member_id)

        total = query.count()
        events = query.order_by(ActivityLog.created_at.desc()).offset(
            (page - 1) * per_page
        ).limit(per_page).all()

        return {
            "events": [
                {
                    "id": e.id,
                    "event_type": e.event_type,
                    "member_id": e.member_id,
                    "metadata": e.metadata_json,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in events
            ],
            "total": total,
            "page": page,
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Export — PRD §18.1
# ---------------------------------------------------------------------------
@app.get("/api/v1/merchant/export")
async def merchant_export(
    type: str = Query("members"),
    merchant_id: str = Depends(require_merchant),
):
    """PRD §18.1: CSV download for members/revenue/benefits/coupons."""
    import csv
    import io
    from fastapi.responses import StreamingResponse

    db = _db_session()
    try:
        output = io.StringIO()
        writer = csv.writer(output)

        if type == "members":
            from database.models import Member
            members = db.query(Member).filter(Member.merchant_id == merchant_id).all()
            writer.writerow(["id", "salla_customer_id", "status", "subscribed_price",
                            "total_saved_sar", "created_at"])
            for m in members:
                writer.writerow([m.id, m.salla_customer_id, m.status,
                               str(m.subscribed_price), str(m.total_saved_sar),
                               m.created_at.isoformat() if m.created_at else ""])

        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={type}_export.csv"},
        )
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Member State — PRD §18.2 (lightweight, for App Snippet)
# ---------------------------------------------------------------------------
@app.get("/api/v1/member/state")
async def member_state(request: Request):
    """PRD §18.2: Lightweight endpoint. App Snippet uses on every page.
    SessionStorage cached 5 min. Returns member status + active benefits.

    Auth via salla_customer_id query param (from Twilight SDK).
    """
    salla_customer_id = request.query_params.get("salla_customer_id")
    store_id = request.query_params.get("store_id")

    if not salla_customer_id or not store_id:
        return {"is_member": False}

    db = _db_session()
    try:
        from database.models import Merchant, Member, MembershipPlan

        merchant = db.query(Merchant).filter(
            Merchant.salla_store_id == int(store_id)
        ).first()
        if not merchant:
            return {"is_member": False}

        member = db.query(Member).filter(
            Member.merchant_id == merchant.id,
            Member.salla_customer_id == int(salla_customer_id),
            Member.status.in_(["active", "grace_period"]),
        ).first()

        if not member:
            # Check if former member (for win-back)
            former = db.query(Member).filter(
                Member.merchant_id == merchant.id,
                Member.salla_customer_id == int(salla_customer_id),
                Member.status.in_(["expired", "cancelled"]),
            ).first()
            return {
                "is_member": False,
                "is_former_member": former is not None,
                "former_tier": former.plan_id if former else None,
                "total_saved": str(former.total_saved_sar) if former else "0",
            }

        plan = db.query(MembershipPlan).filter(
            MembershipPlan.id == member.plan_id,
        ).first()

        return {
            "is_member": True,
            "status": member.status,
            "tier": plan.tier if plan else None,
            "display_name_ar": plan.display_name_ar if plan else None,
            "display_name_en": plan.display_name_en if plan else None,
            "discount_pct": str(plan.discount_pct) if plan else "0",
            "free_shipping_remaining": max(0, member.free_shipping_quota - member.free_shipping_used),
            "current_period_end": member.current_period_end.isoformat() if member.current_period_end else None,
            "total_saved_sar": str(member.total_saved_sar),
        }
    except (ValueError, TypeError):
        return {"is_member": False}
    finally:
        db.close()


@app.get("/api/v1/member/dashboard")
async def member_dashboard(request: Request):
    """Customer-facing full membership dashboard. Returns tier, benefits,
    active gift/shipping codes, savings history."""
    salla_customer_id = request.query_params.get("salla_customer_id")
    store_id = request.query_params.get("store_id")

    if not salla_customer_id or not store_id:
        return {"is_member": False}

    db = _db_session()
    try:
        from database.models import (
            Merchant, Member, MembershipPlan,
            GiftCoupon, FreeShippingCoupon, BenefitEvent,
        )

        merchant = db.query(Merchant).filter(
            Merchant.salla_store_id == int(store_id)
        ).first()
        if not merchant:
            return {"is_member": False}

        member = db.query(Member).filter(
            Member.merchant_id == merchant.id,
            Member.salla_customer_id == int(salla_customer_id),
            Member.status.in_(["active", "cancelled"]),
        ).first()

        if not member:
            return {"is_member": False}

        plan = db.query(MembershipPlan).filter(
            MembershipPlan.id == member.plan_id,
        ).first()

        gifts = db.query(GiftCoupon).filter(
            GiftCoupon.member_id == member.id,
        ).order_by(GiftCoupon.month.desc()).limit(6).all()

        shipping = db.query(FreeShippingCoupon).filter(
            FreeShippingCoupon.member_id == member.id,
        ).order_by(FreeShippingCoupon.month.desc()).limit(6).all()

        recent_savings = db.query(BenefitEvent).filter(
            BenefitEvent.member_id == member.id,
        ).order_by(BenefitEvent.created_at.desc()).limit(10).all()

        return {
            "is_member": True,
            "status": member.status,
            "tier": plan.tier if plan else None,
            "plan_name_ar": plan.display_name_ar if plan else None,
            "plan_name_en": plan.display_name_en if plan else None,
            "discount_pct": str(plan.discount_pct) if plan else "0",
            "price": str(member.subscribed_price),
            "free_shipping_used": member.free_shipping_used,
            "free_shipping_quota": member.free_shipping_quota,
            "current_period_end": member.current_period_end.isoformat() if member.current_period_end else None,
            "total_saved_sar": str(member.total_saved_sar),
            "member_since": member.created_at.isoformat() if member.created_at else None,
            "gifts": [
                {"month": g.month, "code": g.coupon_code, "status": g.status,
                 "desc_ar": g.gift_description_ar, "expires": g.expires_at.isoformat() if g.expires_at else None}
                for g in gifts
            ],
            "shipping": [
                {"month": s.month, "code": s.coupon_code, "quota": s.quota,
                 "used": s.used_count, "status": s.status}
                for s in shipping
            ],
            "recent_savings": [
                {"type": e.event_type, "amount": str(e.amount_saved) if e.amount_saved else None,
                 "date": e.created_at.isoformat() if e.created_at else None}
                for e in recent_savings
            ],
        }
    except (ValueError, TypeError):
        return {"is_member": False}
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Setup Wizard — PRD §8.2, §43.4
# ---------------------------------------------------------------------------
@app.get("/api/v1/merchant/setup/state")
async def setup_state(merchant_id: str = Depends(require_merchant)):
    db = _db_session()
    try:
        from database.models import Merchant
        m = db.query(Merchant).filter(Merchant.id == merchant_id).first()
        if not m:
            raise HTTPException(404, "Merchant not found")
        return {
            "setup_completed": m.setup_completed,
            "setup_step": m.setup_step,
            "total_steps": 5,
        }
    finally:
        db.close()


@app.post("/api/v1/merchant/setup/complete")
async def setup_complete(
    payload: dict = Body(...),
    merchant_id: str = Depends(require_merchant),
):
    """PRD §43.4 Step 4 — Review & Launch. Creates Silver + Gold plans."""
    db = _db_session()
    try:
        from database.models import Merchant, MembershipPlan, PlanPriceVersion

        merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
        if not merchant:
            raise HTTPException(404, "Merchant not found")

        silver = payload.get("silver", {})
        gold = payload.get("gold", {})

        if not payload.get("consent_terms") or not payload.get("consent_cancel"):
            raise HTTPException(400, "Both consent checkboxes required (PRD §43.4 Step 4)")

        # Validate Gold > Silver
        s_disc = float(silver.get("discount_pct", 0))
        g_disc = float(gold.get("discount_pct", 0))
        if g_disc <= s_disc:
            raise HTTPException(400, "Gold discount must exceed Silver")

        for tier_name, config in [("silver", silver), ("gold", gold)]:
            plan = db.query(MembershipPlan).filter(
                MembershipPlan.merchant_id == merchant_id,
                MembershipPlan.tier == tier_name,
            ).first()

            data = {
                "display_name_ar": config.get("display_name_ar", ""),
                "display_name_en": config.get("display_name_en", ""),
                "price": float(config.get("price", 0)),
                "discount_pct": float(config.get("discount_pct", 0)),
                "free_shipping_uses": int(config.get("free_shipping_uses", 0)),
                "gift_name_ar": config.get("gift_name_ar", "الهدية الشهرية"),
                "gift_name_en": config.get("gift_name_en", "Monthly Gift"),
            }

            if plan:
                for k, v in data.items():
                    setattr(plan, k, v)
            else:
                plan = MembershipPlan(merchant_id=merchant_id, tier=tier_name, **data)
                db.add(plan)
                db.flush()

            # Initial price version
            exists = db.query(PlanPriceVersion).filter(
                PlanPriceVersion.plan_id == plan.id,
                PlanPriceVersion.effective_to == None,
            ).first()
            if not exists:
                db.add(PlanPriceVersion(plan_id=plan.id, price=data["price"]))

        merchant.setup_completed = True
        merchant.setup_step = 5
        db.commit()

        # Provision Salla resources (customer groups + special offers) async
        # Also enable recurring payments on the merchant's store
        try:
            from salla.provisioning import provision_merchant_program
            from salla.client import SallaClient
            client = SallaClient(db, merchant.id)
            # Enable recurring payments on merchant's Salla store
            try:
                client._call("PUT", "https://api.salla.dev/admin/v2/settings/fields/enable_recurring_payment",
                             {"value": True})
                merchant.recurring_enabled = True
                db.commit()
            except Exception as exc:
                logger.warning("Failed to enable recurring payments: %s", exc)
            provision_merchant_program(db, merchant.id)
        except Exception as exc:
            logger.warning("Salla provisioning failed (non-blocking): %s", exc)

        return {"setup_completed": True, "message": "Program launched"}
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("setup failed: %s", exc)
        raise HTTPException(500, "Setup failed")
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Public — PRD §18.2
# ---------------------------------------------------------------------------
@app.get("/api/v1/store/{store_id}/plans")
async def public_plans(store_id: str):
    db = _db_session()
    try:
        from database.models import Merchant, MembershipPlan
        merchant = db.query(Merchant).filter(
            Merchant.salla_store_id == int(store_id)
        ).first() if store_id.isdigit() else None

        if not merchant or merchant.status == "cancelled":
            raise HTTPException(404, "Store not found")

        if not merchant.setup_completed:
            return {"store_name": merchant.store_name, "coming_soon": True, "plans": []}

        plans = db.query(MembershipPlan).filter(
            MembershipPlan.merchant_id == merchant.id,
            MembershipPlan.status == "active",
        ).order_by(MembershipPlan.price).all()

        return {
            "store_name": merchant.store_name,
            "coming_soon": False,
            "plans": [
                {
                    "tier": p.tier,
                    "display_name_ar": p.display_name_ar,
                    "display_name_en": p.display_name_en,
                    "price": str(p.price),
                    "discount_pct": str(p.discount_pct),
                    "free_shipping_uses": p.free_shipping_uses,
                }
                for p in plans
            ],
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Interest Registration — public endpoint for pre-launch signups
# ---------------------------------------------------------------------------
@app.post("/api/v1/store/{store_id}/interest")
async def register_interest(store_id: str, payload: dict = Body(...)):
    """Allow potential members to register interest before launch."""
    db = _db_session()
    try:
        from database.models import Merchant, InterestRegistration

        merchant = db.query(Merchant).filter(
            Merchant.salla_store_id == int(store_id)
        ).first() if store_id.isdigit() else None
        if not merchant:
            raise HTTPException(404, "Store not found")

        salla_customer_id = payload.get("salla_customer_id")
        if not salla_customer_id:
            raise HTTPException(400, "Missing salla_customer_id")

        # Check duplicate
        existing = db.query(InterestRegistration).filter(
            InterestRegistration.merchant_id == merchant.id,
            InterestRegistration.salla_customer_id == int(salla_customer_id),
        ).first()
        if existing:
            return {"status": "already_registered", "id": existing.id}

        reg = InterestRegistration(
            merchant_id=merchant.id,
            salla_customer_id=int(salla_customer_id),
            preferred_tier=payload.get("preferred_tier", "gold"),
        )
        db.add(reg)
        db.commit()
        return {"status": "registered", "id": reg.id}
    finally:
        db.close()


# ---------------------------------------------------------------------------
# OAuth Access — exchange permanent token for session
# ---------------------------------------------------------------------------
@app.get("/api/v1/access")
async def access_redirect(request: Request, token: str = Query(...), goto: str = Query("dashboard")):
    """PRD Appendix B: Exchange permanent access token for session cookie."""
    from auth.session import create_session
    from fastapi.responses import RedirectResponse

    db = _db_session()
    try:
        from database.models import Merchant
        merchant = db.query(Merchant).filter(
            Merchant.permanent_access_token == token
        ).first()
        if not merchant:
            raise HTTPException(401, "Invalid access token")

        response = RedirectResponse(url=f"/frontend/{goto}.html")
        create_session(response, merchant.id)
        return response
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Admin Auth — login / logout / session
# ---------------------------------------------------------------------------
_admin_sessions = {}  # token → {admin_id, email, role, expires_at}

@app.post("/api/v1/admin/login")
async def admin_login(payload: dict = Body(...)):
    """Admin login with email + password."""
    import hashlib
    from datetime import datetime, timedelta
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not email or not password:
        raise HTTPException(400, "Email and password required")

    db = _db_session()
    try:
        from database.models import AdminUser
        admin = db.query(AdminUser).filter(AdminUser.email == email).first()

        if not admin:
            # Dev convenience: auto-create admin if none exist
            existing_count = db.query(AdminUser).count()
            if existing_count == 0 and email and password:
                admin = AdminUser(
                    email=email,
                    password_hash=hashlib.sha256(password.encode()).hexdigest(),
                    role="admin",
                )
                db.add(admin)
                db.commit()
                db.refresh(admin)
            else:
                raise HTTPException(401, "Invalid credentials")

        # Verify password
        if admin.password_hash != hashlib.sha256(password.encode()).hexdigest():
            raise HTTPException(401, "Invalid credentials")

        # Create session token
        import secrets
        token = secrets.token_urlsafe(32)
        _admin_sessions[token] = {
            "admin_id": admin.id,
            "email": admin.email,
            "role": admin.role,
            "expires_at": (datetime.utcnow() + timedelta(hours=8)).isoformat(),
        }

        admin.last_login_at = datetime.utcnow()
        db.commit()

        return {"token": token, "email": admin.email, "role": admin.role}
    finally:
        db.close()


@app.get("/api/v1/admin/me")
async def admin_me(request: Request):
    """Verify admin session."""
    from datetime import datetime
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    session = _admin_sessions.get(token)
    if not session:
        raise HTTPException(401, "Not authenticated")
    if datetime.fromisoformat(session["expires_at"]) < datetime.utcnow():
        del _admin_sessions[token]
        raise HTTPException(401, "Session expired")
    return {"email": session["email"], "role": session["role"]}


@app.post("/api/v1/admin/logout")
async def admin_logout(request: Request):
    """Destroy admin session."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    _admin_sessions.pop(token, None)
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Admin API — internal platform management (PRD §39)
# ---------------------------------------------------------------------------
@app.get("/api/v1/admin/stats")
async def admin_platform_stats():
    """Platform-wide KPIs for admin dashboard."""
    db = _db_session()
    try:
        from database.models import Merchant, Member, MembershipPlan, WebhookEvent, EmailLog

        total_merchants = db.query(Merchant).count()
        active_merchants = db.query(Merchant).filter(Merchant.status == "active").count()
        trial_merchants = db.query(Merchant).filter(Merchant.status == "trial").count()
        suspended_merchants = db.query(Merchant).filter(Merchant.status == "suspended").count()
        cancelled_merchants = db.query(Merchant).filter(Merchant.status == "cancelled").count()

        total_members = db.query(Member).count()
        active_members = db.query(Member).filter(Member.status == "active").count()

        total_revenue = sum(float(m.subscribed_price or 0) for m in db.query(Member).filter(Member.status == "active").all())

        webhooks_total = db.query(WebhookEvent).count()

        plan_counts = {}
        for plan in ["starter", "pro", "unlimited"]:
            plan_counts[plan] = db.query(Merchant).filter(Merchant.our_plan == plan).count()

        return {
            "merchants": {
                "total": total_merchants,
                "active": active_merchants,
                "trial": trial_merchants,
                "suspended": suspended_merchants,
                "cancelled": cancelled_merchants,
            },
            "members": {
                "total": total_members,
                "active": active_members,
            },
            "revenue": {
                "mrr": round(total_revenue, 2),
            },
            "plans": plan_counts,
            "webhooks_processed": webhooks_total,
        }
    finally:
        db.close()


@app.get("/api/v1/admin/merchants")
async def admin_merchant_list(
    status: str = Query(None),
    plan: str = Query(None),
    page: int = Query(1),
    per_page: int = Query(20),
):
    """List all merchants with filters."""
    db = _db_session()
    try:
        from database.models import Merchant, Member

        query = db.query(Merchant)
        if status:
            query = query.filter(Merchant.status == status)
        if plan:
            query = query.filter(Merchant.our_plan == plan)

        total = query.count()
        merchants = query.order_by(Merchant.created_at.desc()).offset(
            (page - 1) * per_page
        ).limit(per_page).all()

        result = []
        for m in merchants:
            member_count = db.query(Member).filter(
                Member.merchant_id == m.id, Member.status == "active"
            ).count()
            result.append({
                "id": m.id,
                "salla_store_id": m.salla_store_id,
                "store_name": m.store_name or "",
                "status": m.status,
                "our_plan": m.our_plan,
                "member_count": member_count,
                "setup_completed": m.setup_completed,
                "trial_ends_at": m.trial_ends_at.isoformat() if m.trial_ends_at else None,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            })

        return {"merchants": result, "total": total, "page": page}
    finally:
        db.close()


@app.get("/api/v1/admin/merchants/{merchant_id}")
async def admin_merchant_detail(merchant_id: str):
    """Full merchant detail for admin."""
    db = _db_session()
    try:
        from database.models import Merchant, Member, MembershipPlan, WebhookEvent, AdminNote

        m = db.query(Merchant).filter(Merchant.id == merchant_id).first()
        if not m:
            raise HTTPException(404, "Merchant not found")

        members = db.query(Member).filter(Member.merchant_id == m.id).all()
        plans = db.query(MembershipPlan).filter(MembershipPlan.merchant_id == m.id).all()
        webhooks = db.query(WebhookEvent).filter(WebhookEvent.merchant_id == m.id).order_by(WebhookEvent.created_at.desc()).limit(20).all()
        notes = db.query(AdminNote).filter(AdminNote.merchant_id == m.id).order_by(AdminNote.created_at.desc()).all()

        active_members = [mb for mb in members if mb.status == "active"]
        revenue = sum(float(mb.subscribed_price or 0) for mb in active_members)

        return {
            "merchant": {
                "id": m.id,
                "salla_store_id": m.salla_store_id,
                "store_name": m.store_name,
                "status": m.status,
                "our_plan": m.our_plan,
                "setup_completed": m.setup_completed,
                "recurring_enabled": m.recurring_enabled,
                "trial_ends_at": m.trial_ends_at.isoformat() if m.trial_ends_at else None,
                "activated_at": m.activated_at.isoformat() if m.activated_at else None,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "permanent_access_token": m.permanent_access_token[:8] + "...",
            },
            "stats": {
                "total_members": len(members),
                "active_members": len(active_members),
                "cancelled_members": sum(1 for mb in members if mb.status in ("cancelled", "expired")),
                "monthly_revenue": round(revenue, 2),
            },
            "plans": [
                {"tier": p.tier, "name": p.display_name_ar, "price": str(p.price), "discount": str(p.discount_pct), "shipping": p.free_shipping_uses}
                for p in plans
            ],
            "recent_webhooks": [
                {"event_type": w.event_type, "status": w.status, "created_at": w.created_at.isoformat() if w.created_at else None}
                for w in webhooks
            ],
            "admin_notes": [
                {"id": n.id, "note": n.note, "created_at": n.created_at.isoformat() if n.created_at else None}
                for n in notes
            ],
        }
    finally:
        db.close()


@app.post("/api/v1/admin/merchants/{merchant_id}/notes")
async def admin_add_note(merchant_id: str, payload: dict = Body(...)):
    """Add admin note to a merchant."""
    db = _db_session()
    try:
        from database.models import Merchant, AdminNote
        m = db.query(Merchant).filter(Merchant.id == merchant_id).first()
        if not m:
            raise HTTPException(404, "Merchant not found")

        note = AdminNote(
            admin_user_id="system",
            merchant_id=merchant_id,
            note=payload.get("note", ""),
        )
        db.add(note)
        db.commit()
        return {"status": "ok", "id": note.id}
    finally:
        db.close()


@app.post("/api/v1/admin/merchants/{merchant_id}/suspend")
async def admin_suspend_merchant(merchant_id: str):
    """Suspend a merchant."""
    db = _db_session()
    try:
        from database.models import Merchant
        m = db.query(Merchant).filter(Merchant.id == merchant_id).first()
        if not m:
            raise HTTPException(404, "Merchant not found")
        m.status = "suspended"
        db.commit()
        return {"status": "ok", "merchant_status": "suspended"}
    finally:
        db.close()


@app.post("/api/v1/admin/merchants/{merchant_id}/reactivate")
async def admin_reactivate_merchant(merchant_id: str):
    """Reactivate a suspended merchant."""
    db = _db_session()
    try:
        from database.models import Merchant
        m = db.query(Merchant).filter(Merchant.id == merchant_id).first()
        if not m:
            raise HTTPException(404, "Merchant not found")
        m.status = "active"
        db.commit()
        return {"status": "ok", "merchant_status": "active"}
    finally:
        db.close()


@app.get("/api/v1/admin/members")
async def admin_members_list(
    merchant_id: str = Query(None),
    status: str = Query(None),
    tier: str = Query(None),
    page: int = Query(1),
    per_page: int = Query(20),
):
    """All members across all merchants."""
    db = _db_session()
    try:
        from database.models import Member, MembershipPlan, Merchant

        query = db.query(Member)
        if merchant_id:
            query = query.filter(Member.merchant_id == merchant_id)
        if status:
            query = query.filter(Member.status == status)

        total = query.count()
        members = query.order_by(Member.created_at.desc()).offset((page-1)*per_page).limit(per_page).all()

        plan_cache = {}
        merchant_cache = {}
        result = []
        for m in members:
            if m.plan_id not in plan_cache:
                plan_cache[m.plan_id] = db.query(MembershipPlan).filter(MembershipPlan.id == m.plan_id).first()
            if m.merchant_id not in merchant_cache:
                merchant_cache[m.merchant_id] = db.query(Merchant).filter(Merchant.id == m.merchant_id).first()
            plan = plan_cache.get(m.plan_id)
            merchant = merchant_cache.get(m.merchant_id)

            if tier and plan and plan.tier != tier:
                continue

            result.append({
                "id": m.id,
                "salla_customer_id": m.salla_customer_id,
                "status": m.status,
                "tier": plan.tier if plan else None,
                "plan_name": plan.display_name_ar if plan else "",
                "price": str(m.subscribed_price),
                "merchant_id": m.merchant_id,
                "store_name": merchant.store_name if merchant else "",
                "total_saved": str(m.total_saved_sar),
                "is_at_risk": m.is_at_risk,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            })

        return {"members": result, "total": total, "page": page}
    finally:
        db.close()


@app.get("/api/v1/admin/emails")
async def admin_email_list(
    merchant_id: str = Query(None),
    email_type: str = Query(None),
    page: int = Query(1),
    per_page: int = Query(20),
):
    """All sent emails/notifications."""
    db = _db_session()
    try:
        from database.models import EmailLog

        query = db.query(EmailLog)
        if merchant_id:
            query = query.filter(EmailLog.merchant_id == merchant_id)
        if email_type:
            query = query.filter(EmailLog.email_type == email_type)

        total = query.count()
        emails = query.order_by(EmailLog.created_at.desc()).offset((page-1)*per_page).limit(per_page).all()

        return {
            "emails": [
                {
                    "id": e.id,
                    "merchant_id": e.merchant_id,
                    "member_id": e.member_id,
                    "email_type": e.email_type,
                    "recipient_email": e.recipient_email,
                    "subject": e.subject,
                    "status": e.status,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in emails
            ],
            "total": total,
            "page": page,
        }
    finally:
        db.close()


@app.get("/api/v1/admin/plans-summary")
async def admin_plans_summary():
    """Our SaaS plans with merchant counts."""
    db = _db_session()
    try:
        from database.models import Merchant, Member

        plans = [
            {"id": "starter", "name": "Starter", "price": 79, "cycle": "شهري", "member_limit": 50},
            {"id": "pro", "name": "Pro", "price": 149, "cycle": "شهري", "member_limit": 200},
            {"id": "unlimited", "name": "Unlimited", "price": 249, "cycle": "شهري", "member_limit": None},
        ]

        for p in plans:
            merchants = db.query(Merchant).filter(Merchant.our_plan == p["id"], Merchant.status.in_(["active","trial"])).all()
            p["merchant_count"] = len(merchants)
            total_members = 0
            total_revenue = 0
            for m in merchants:
                count = db.query(Member).filter(Member.merchant_id == m.id, Member.status == "active").count()
                total_members += count
                total_revenue += sum(float(mb.subscribed_price or 0) for mb in db.query(Member).filter(Member.merchant_id == m.id, Member.status == "active").all())
            p["total_members"] = total_members
            p["total_revenue"] = round(total_revenue, 2)
            p["app_revenue"] = p["price"] * p["merchant_count"]

        return {"plans": plans}
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Notification Preview (dev/merchant)
# ---------------------------------------------------------------------------
@app.get("/api/v1/notifications/preview/{template_name}")
async def preview_notification(template_name: str):
    """Preview email templates. Returns raw HTML for iframe rendering."""
    from email_service.service import (
        welcome_merchant, trial_ending, setup_complete,
        new_member_joined, payment_failed, monthly_report,
        customer_interest,
        member_welcome, member_gift_ready, member_renewal_reminder,
        member_payment_failed, member_cancelled,
    )
    from fastapi.responses import HTMLResponse

    templates = {
        "merchant-welcome": lambda: welcome_merchant("متجر الأناقة", "#"),
        "merchant-trial-ending": lambda: trial_ending("متجر الأناقة", 3, "#"),
        "merchant-setup-complete": lambda: setup_complete("متجر الأناقة", 0, "#"),
        "merchant-new-member": lambda: new_member_joined("نورة الشمري", "gold", "99.00", "#"),
        "merchant-payment-failed": lambda: payment_failed("ريم المطيري", "99.00", "#"),
        "merchant-monthly-report": lambda: monthly_report("متجر الأناقة", {"member_count":12,"revenue":740,"new_members":3,"churn_rate":8.3}, "#"),
        "merchant-customer-interest": lambda: customer_interest("أحمد الغامدي", "متجر الأناقة", 7, "#"),
        "member-welcome": lambda: member_welcome("نورة الشمري", "gold", "متجر الأناقة", "#"),
        "member-gift-ready": lambda: member_gift_ready("نورة الشمري", "خصم 25% على جميع المنتجات", "GIFT-A8F2K3", "April 30, 2026", "متجر الأناقة"),
        "member-renewal": lambda: member_renewal_reminder("نورة الشمري", "gold", "99.00", "May 10, 2026", "متجر الأناقة"),
        "member-payment-failed": lambda: member_payment_failed("نورة الشمري", "99.00", "متجر الأناقة"),
        "member-cancelled": lambda: member_cancelled("نورة الشمري", "gold", "May 10, 2026", "245.50", "متجر الأناقة"),
    }
    if template_name not in templates:
        return {"available": list(templates.keys())}
    notif = templates[template_name]()
    return HTMLResponse(content=notif["html"])


# ---------------------------------------------------------------------------
# Dev-only demo login (NOT in production)
# ---------------------------------------------------------------------------
import os
if os.getenv("ENVIRONMENT") != "production":
    @app.post("/api/v1/auth/demo")
    async def demo_login():
        """Creates a test merchant and returns a JWT token. Dev only."""
        from datetime import timedelta
        from auth.crypto import encrypt
        from auth.jwt import create_jwt_token
        from database.models import Merchant

        db = _db_session()
        try:
            existing = db.query(Merchant).filter(Merchant.salla_store_id == 99999).first()
            if existing:
                return {"token": create_jwt_token(existing.id), "merchant_id": existing.id}

            now = datetime.utcnow()
            merchant = Merchant(
                salla_store_id=99999,
                access_token=encrypt("demo-tok"),
                refresh_token=encrypt("demo-ref"),
                store_name="متجر تجريبي",
                status="trial",
                trial_ends_at=now + timedelta(days=7),
            )
            db.add(merchant)
            db.commit()
            db.refresh(merchant)

            token = create_jwt_token(merchant.id)
            return {"token": token, "merchant_id": merchant.id}
        finally:
            db.close()

    from datetime import datetime


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    return {
        "app": "Member Plus",
        "version": "1.0.0",
        "api": "/api/v1/",
        "health": "/health",
        "webhooks": "/webhooks/salla",
    }


import os as _os
_frontend_dir = _os.path.join(_os.path.dirname(__file__), "..", "..", "..", "frontend")
_frontend_dir = _os.path.abspath(_frontend_dir)
if _os.path.isdir(_frontend_dir):
    app.mount("/frontend", StaticFiles(directory=_frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

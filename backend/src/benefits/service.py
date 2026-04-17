"""Benefits service — generate benefit deliveries when members activate,
and run the monthly-gift tick.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from database.models import (
    BenefitDelivery, CustomerSubscription, MembershipPlan,
)
from salla.coupons import create_coupon, CouponResult


logger = logging.getLogger("benefits")


def _sub_and_plan(session, subscription_id: str):
    row = (
        session.query(CustomerSubscription, MembershipPlan)
        .join(MembershipPlan, MembershipPlan.id == CustomerSubscription.plan_id)
        .filter(CustomerSubscription.id == subscription_id)
        .first()
    )
    return row


def _delivery_to_dict(d: BenefitDelivery) -> Dict:
    return {
        "id": d.id,
        "subscription_id": d.subscription_id,
        "kind": d.kind,
        "period_key": d.period_key,
        "coupon_code": d.coupon_code,
        "uses_allowed": d.uses_allowed,
        "uses_remaining": d.uses_remaining,
        "valid_until": d.valid_until.isoformat() if d.valid_until else None,
        "salla_coupon_id": d.salla_coupon_id,
        "status": d.status,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


def list_for_subscription(session, subscription_id: str) -> List[Dict]:
    rows = (
        session.query(BenefitDelivery)
        .filter(BenefitDelivery.subscription_id == subscription_id)
        .order_by(BenefitDelivery.created_at.desc())
        .all()
    )
    return [_delivery_to_dict(r) for r in rows]


def revoke_for_subscription(session, subscription_id: str) -> int:
    """Phase G clawback — mark every still-usable coupon delivery for this
    subscription as `revoked` and zero its `uses_remaining`. Flag-only rows
    are left alone (they cost nothing to retain as history). Returns the
    number of rows changed.
    """
    rows = (
        session.query(BenefitDelivery)
        .filter(
            BenefitDelivery.subscription_id == subscription_id,
            BenefitDelivery.status.in_(("delivered", "delivered-mock")),
        )
        .all()
    )
    changed = 0
    for row in rows:
        row.status = "revoked"
        row.uses_remaining = 0
        changed += 1
    if changed:
        session.commit()
    return changed


def redeem(session, coupon_code: str) -> Dict:
    """Phase G — decrement a coupon's `uses_remaining` by 1. Raises:
    KeyError → unknown code, ValueError → already depleted/revoked."""
    row = (
        session.query(BenefitDelivery)
        .filter(BenefitDelivery.coupon_code == coupon_code)
        .first()
    )
    if not row:
        raise KeyError("coupon not found")
    if row.status == "revoked":
        raise ValueError("coupon revoked")
    if row.uses_remaining is None or row.uses_remaining <= 0:
        raise ValueError("coupon depleted")
    row.uses_remaining -= 1
    session.commit()
    session.refresh(row)
    return _delivery_to_dict(row)


def sum_savings_for_subscription(session, subscription_id: str, default_order_value: float = 100.0) -> float:
    """Phase 7 — a demonstrative "you've saved" number for the member view.

    We intentionally don't promise a real currency figure — this is a
    friendly heuristic (uses consumed × default order value × effective
    discount). Phase 8 will swap this for ledger-backed tracking once the
    Salla order webhook is wired.
    """
    from database.models import BenefitDelivery as BD, MembershipPlan, CustomerSubscription as CS

    row = (
        session.query(CS, MembershipPlan)
        .join(MembershipPlan, MembershipPlan.id == CS.plan_id)
        .filter(CS.id == subscription_id)
        .first()
    )
    if not row:
        return 0.0
    sub, plan = row

    deliveries = session.query(BD).filter(BD.subscription_id == subscription_id).all()
    used = 0
    for d in deliveries:
        if d.uses_allowed is not None and d.uses_remaining is not None:
            used += max(0, d.uses_allowed - d.uses_remaining)
    if not used:
        return 0.0

    discount_pct = float(plan.discount_percent or 0) / 100.0
    per_use_saving = default_order_value * max(0.05, discount_pct)
    return round(per_use_saving * used, 2)


def list_for_merchant(session, merchant_id: str, subscription_id: Optional[str] = None) -> List[Dict]:
    q = session.query(BenefitDelivery).filter(BenefitDelivery.merchant_id == merchant_id)
    if subscription_id:
        q = q.filter(BenefitDelivery.subscription_id == subscription_id)
    rows = q.order_by(BenefitDelivery.created_at.desc()).all()
    return [_delivery_to_dict(r) for r in rows]


def _flag_only(session, sub: CustomerSubscription, kind: str) -> BenefitDelivery:
    row = BenefitDelivery(
        subscription_id=sub.id,
        merchant_id=sub.merchant_id,
        kind=kind,
        status="flag-only",
    )
    session.add(row)
    return row


def _coupon_delivery(
    session,
    sub: CustomerSubscription,
    plan: MembershipPlan,
    kind: str,
    payload: Dict,
    valid_days: Optional[int] = None,
    uses: int = 1,
    period_key: Optional[str] = None,
    client_factory=None,
) -> BenefitDelivery:
    result: CouponResult = create_coupon(
        session, sub.merchant_id, payload, client_factory=client_factory
    )
    row = BenefitDelivery(
        subscription_id=sub.id,
        merchant_id=sub.merchant_id,
        kind=kind,
        period_key=period_key,
        coupon_code=result.coupon_code,
        uses_allowed=uses,
        uses_remaining=uses,
        valid_until=(datetime.utcnow() + timedelta(days=valid_days)) if valid_days else None,
        salla_coupon_id=result.salla_coupon_id,
        status=result.status,
    )
    session.add(row)
    return row


def generate_on_activation(
    session,
    subscription_id: str,
    client_factory=None,
) -> List[Dict]:
    """Create all relevant BenefitDelivery rows for a newly-activated
    subscription. Idempotent per (subscription, kind, period) — running it
    twice for the same activation won't duplicate rows."""
    row = _sub_and_plan(session, subscription_id)
    if not row:
        return []
    sub, plan = row

    period_key = sub.activated_at.strftime("%Y-%m") if sub.activated_at else datetime.utcnow().strftime("%Y-%m")

    existing = {
        (d.kind, d.period_key)
        for d in session.query(BenefitDelivery).filter(
            BenefitDelivery.subscription_id == subscription_id
        ).all()
    }

    created: List[BenefitDelivery] = []

    # Auto-discount: attached via customer group (Phase R). Record a flag row
    # if the plan has a discount configured.
    if plan.discount_percent and float(plan.discount_percent) > 0:
        if ("auto_discount", None) not in existing:
            created.append(_flag_only(session, sub, "auto_discount"))

    if plan.free_shipping_quota and int(plan.free_shipping_quota) > 0:
        if ("free_shipping", None) not in existing:
            created.append(_coupon_delivery(
                session, sub, plan,
                kind="free_shipping",
                payload={
                    "kind": "free_shipping",
                    "code_prefix": "FS",
                    "amount": 100,
                    "amount_type": "percentage",
                    "usage_limit": int(plan.free_shipping_quota),
                    "valid_days": plan.duration_days,
                    "reason": f"Free shipping — {plan.name_en or plan.tier or 'member'}",
                },
                valid_days=plan.duration_days,
                uses=int(plan.free_shipping_quota),
                client_factory=client_factory,
            ))

    if plan.monthly_gift_enabled and ("monthly_gift", period_key) not in existing:
        created.append(_coupon_delivery(
            session, sub, plan,
            kind="monthly_gift",
            payload={
                "kind": "monthly_gift",
                "code_prefix": "GIFT",
                "amount": 100,
                "amount_type": "fixed",
                "usage_limit": 1,
                "valid_days": 30,
                "reason": f"Monthly gift — {period_key}",
            },
            valid_days=30, uses=1,
            period_key=period_key,
            client_factory=client_factory,
        ))

    if plan.early_access_enabled and ("early_access", None) not in existing:
        created.append(_flag_only(session, sub, "early_access"))
    if plan.badge_enabled and ("badge", None) not in existing:
        created.append(_flag_only(session, sub, "badge"))

    if created:
        session.commit()
    return [_delivery_to_dict(r) for r in created]


def generate_monthly_gifts(
    session,
    now: Optional[datetime] = None,
    client_factory=None,
) -> List[Dict]:
    """For every active subscription whose plan has `monthly_gift_enabled`,
    issue this month's gift coupon if one doesn't already exist."""
    now = now or datetime.utcnow()
    period_key = now.strftime("%Y-%m")

    eligible = (
        session.query(CustomerSubscription, MembershipPlan)
        .join(MembershipPlan, MembershipPlan.id == CustomerSubscription.plan_id)
        .filter(
            CustomerSubscription.status == "active",
            MembershipPlan.monthly_gift_enabled.is_(True),
        )
        .all()
    )

    created: List[Dict] = []
    for sub, plan in eligible:
        has_gift = (
            session.query(BenefitDelivery)
            .filter(
                BenefitDelivery.subscription_id == sub.id,
                BenefitDelivery.kind == "monthly_gift",
                BenefitDelivery.period_key == period_key,
            )
            .first()
        )
        if has_gift:
            continue
        row = _coupon_delivery(
            session, sub, plan,
            kind="monthly_gift",
            payload={
                "kind": "monthly_gift",
                "code_prefix": "GIFT",
                "amount": 100,
                "amount_type": "fixed",
                "usage_limit": 1,
                "valid_days": 30,
                "reason": f"Monthly gift — {period_key}",
            },
            valid_days=30, uses=1,
            period_key=period_key,
            client_factory=client_factory,
        )
        created.append(_delivery_to_dict(row))

    if created:
        session.commit()
    return created

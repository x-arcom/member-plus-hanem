"""
Benefits engine — PRD §10, Appendix C.

Core rule (LOCKED): Every benefit activates the moment a member subscribes.
No waiting. No scheduling. No prorating. Member pays — member gets everything
immediately.

6 benefits:
  B1 — Auto Discount (Salla Special Offer, percentage, unlimited)
  B2 — Member-Only Price (Salla Special Offer, special_price, per product)
  B3 — Free Shipping (personal coupon, monthly quota, manual code entry)
  B4 — Monthly Gift (personal coupon, 1 use, expires end of month)
  B5 — Early Product Access (customer group visibility, binary)
  B6 — Identity Badge (App Snippet, always active)

Each benefit has:
  - activate(session, member, plan, client?) — called on subscription.created
  - deactivate(session, member, plan, client?) — called on expiry/cancellation
  - reset_monthly(session, member, plan, client?) — called on charge.succeeded

The SallaClient is injected for testability. When Salla is unavailable,
benefits degrade gracefully with local fallback codes.
"""
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger("benefits.engine")


class BenefitResult:
    def __init__(self, benefit: str, status: str, detail: Optional[str] = None):
        self.benefit = benefit
        self.status = status  # activated | skipped | failed
        self.detail = detail

    def as_dict(self):
        return {"benefit": self.benefit, "status": self.status, "detail": self.detail}


# ---------------------------------------------------------------------------
# B1 — Auto Discount (PRD §10 Benefit 1)
# Salla Special Offer API: offer_type=percentage, customer_groups=[group_id]
# Quota: unlimited. Every order during membership.
# ---------------------------------------------------------------------------
def activate_auto_discount(session, member, plan, salla_client=None) -> BenefitResult:
    """B1 is activated by adding the member to the Salla Customer Group.
    The Special Offer (created during setup wizard) auto-applies to all
    group members. No per-member action needed — group membership IS the
    activation."""
    # The member is added to the customer group in activate_all_benefits().
    # B1 is inherently active once they're in the group.
    return BenefitResult("auto_discount", "activated",
                         f"{plan.discount_pct}% via Salla Special Offer")


# ---------------------------------------------------------------------------
# B2 — Member-Only Price (PRD §10 Benefit 2)
# Salla Special Offer API: offer_type=special_price, per product
# ---------------------------------------------------------------------------
def activate_member_price(session, member, plan, salla_client=None) -> BenefitResult:
    """B2 is also activated by customer group membership. Products with
    member-only pricing are configured by the merchant in Salla directly.
    Our system ensures the member is in the correct group."""
    return BenefitResult("member_price", "activated",
                         "Active via customer group membership")


# ---------------------------------------------------------------------------
# B3 — Free Shipping (PRD §10 Benefit 3)
# Personal coupon with include_customer_ids, monthly quota.
# CANNOT auto-apply (Salla constraint C-04). Manual code entry required.
# ---------------------------------------------------------------------------
def activate_free_shipping(session, member, plan, salla_client=None) -> BenefitResult:
    """Generate the first free shipping coupon for the current month.
    Full quota regardless of join date (PRD Appendix C.1)."""
    from database.models import FreeShippingCoupon

    now = datetime.utcnow()
    month_str = now.strftime("%Y-%m")
    last_day = _end_of_month(now)

    existing = session.query(FreeShippingCoupon).filter(
        FreeShippingCoupon.member_id == member.id,
        FreeShippingCoupon.month == month_str,
    ).first()

    if existing:
        return BenefitResult("free_shipping", "skipped", "Already generated for this month")

    code = f"FS-{secrets.token_hex(4).upper()}"

    # TODO Phase 3: Create via Salla Coupon API with:
    #   free_shipping: true
    #   include_customer_ids: [member.salla_customer_id]
    #   usage_limit_per_user: plan.free_shipping_uses
    #   expiry: last_day
    # For now: local code (mock-fallback pattern)

    coupon = FreeShippingCoupon(
        member_id=member.id,
        merchant_id=member.merchant_id,
        month=month_str,
        coupon_code=code,
        quota=plan.free_shipping_uses,
        expires_at=last_day,
        status="active",
    )
    session.add(coupon)

    # Update member's quota tracking
    member.free_shipping_quota = plan.free_shipping_uses
    member.free_shipping_used = 0

    return BenefitResult("free_shipping", "activated",
                         f"Code: {code}, quota: {plan.free_shipping_uses}/month")


# ---------------------------------------------------------------------------
# B4 — Monthly Gift Coupon (PRD §10 Benefit 4)
# 1 use per month. Expires last day of month. No rollover.
# Gold tier ONLY (PRD §10: "Most important retention driver")
# ---------------------------------------------------------------------------
def activate_monthly_gift(session, member, plan, salla_client=None) -> BenefitResult:
    """Generate the first gift coupon. Only for Gold tier.
    Full gift regardless of join date (PRD Appendix C.1)."""
    if plan.tier != "gold":
        return BenefitResult("monthly_gift", "skipped", "Silver tier — no monthly gift")

    from database.models import GiftCoupon

    now = datetime.utcnow()
    month_str = now.strftime("%Y-%m")
    last_day = _end_of_month(now)

    existing = session.query(GiftCoupon).filter(
        GiftCoupon.member_id == member.id,
        GiftCoupon.month == month_str,
    ).first()

    if existing:
        return BenefitResult("monthly_gift", "skipped", "Already generated for this month")

    code = f"GIFT-{secrets.token_hex(4).upper()}"

    coupon = GiftCoupon(
        member_id=member.id,
        merchant_id=member.merchant_id,
        plan_id=plan.id,
        month=month_str,
        coupon_code=code,
        gift_description_ar=plan.gift_name_ar,
        gift_description_en=plan.gift_name_en,
        status="generated",
        expires_at=last_day,
    )
    session.add(coupon)

    return BenefitResult("monthly_gift", "activated",
                         f"Code: {code}, expires: {last_day.date()}")


# ---------------------------------------------------------------------------
# B5 — Early Product Access (PRD §10 Benefit 5)
# Products hidden from public — visible only to customer group members.
# Binary: on/off based on group membership.
# ---------------------------------------------------------------------------
def activate_early_access(session, member, plan, salla_client=None) -> BenefitResult:
    """B5 is activated by customer group membership. Products are hidden
    via Salla's native product visibility tied to customer groups.
    No per-member action — the group controls access."""
    return BenefitResult("early_access", "activated",
                         "Active via customer group membership")


# ---------------------------------------------------------------------------
# B6 — Identity Badge (PRD §10 Benefit 6)
# Visible on every store page via App Snippet. Tap → mini-dashboard.
# Always active while membership is active.
# ---------------------------------------------------------------------------
def activate_badge(session, member, plan, salla_client=None) -> BenefitResult:
    """B6 is delivered by the App Snippet reading /api/v1/member/state.
    No backend action needed — the member state endpoint returns tier info
    which the snippet renders as a badge."""
    return BenefitResult("badge", "activated",
                         f"{plan.display_name_ar} / {plan.display_name_en}")


# ---------------------------------------------------------------------------
# Master activation — called on subscription.created (PRD Appendix C)
# ---------------------------------------------------------------------------
def activate_all_benefits(session, member, plan, salla_client=None) -> List[Dict]:
    """Activate all 6 benefits immediately on subscription.

    PRD Appendix C: "Every benefit activates the moment a member subscribes.
    No waiting. No scheduling. No prorating."

    Also adds member to the Salla Customer Group (which enables B1, B2, B5).
    """
    results = []

    # Step 1: Add to Salla Customer Group (enables B1, B2, B5)
    if salla_client and plan.salla_group_id:
        try:
            salla_client.post(
                f"https://api.salla.dev/admin/v2/customers/groups/{plan.salla_group_id}/customers",
                {"customer_ids": [member.salla_customer_id]},
            )
            results.append(BenefitResult("customer_group", "activated",
                                         f"Added to group {plan.salla_group_id}").as_dict())
        except Exception as exc:
            logger.warning("Failed to add member %s to Salla group: %s", member.id, exc)
            results.append(BenefitResult("customer_group", "failed", str(exc)).as_dict())
    else:
        results.append(BenefitResult("customer_group", "skipped",
                                     "No Salla client or group not provisioned").as_dict())

    # Step 2: Activate each benefit
    for activate_fn in [
        activate_auto_discount,
        activate_member_price,
        activate_free_shipping,
        activate_monthly_gift,
        activate_early_access,
        activate_badge,
    ]:
        try:
            result = activate_fn(session, member, plan, salla_client)
            results.append(result.as_dict())
        except Exception as exc:
            logger.warning("Benefit activation failed: %s", exc)
            results.append(BenefitResult(activate_fn.__name__, "failed", str(exc)).as_dict())

    session.commit()

    # Step 3: Log to activity_log
    _log_activity(session, member, "member.joined", {
        "tier": plan.tier,
        "benefits": [r["benefit"] for r in results if r["status"] == "activated"],
    })

    return results


def deactivate_all_benefits(session, member, plan, salla_client=None) -> List[Dict]:
    """Remove member from Salla Customer Group. Deactivate active coupons.
    Called on expiry/cancellation."""
    from database.models import FreeShippingCoupon, GiftCoupon

    results = []

    # Remove from Salla group
    if salla_client and plan.salla_group_id:
        try:
            salla_client.post(
                f"https://api.salla.dev/admin/v2/customers/groups/{plan.salla_group_id}/customers/remove",
                {"customer_ids": [member.salla_customer_id]},
            )
            results.append({"benefit": "customer_group", "status": "deactivated"})
        except Exception as exc:
            results.append({"benefit": "customer_group", "status": "failed", "detail": str(exc)})

    # Deactivate active shipping coupons
    active_shipping = session.query(FreeShippingCoupon).filter(
        FreeShippingCoupon.member_id == member.id,
        FreeShippingCoupon.status == "active",
    ).all()
    for c in active_shipping:
        c.status = "deactivated"
    if active_shipping:
        results.append({"benefit": "free_shipping", "status": "deactivated",
                        "detail": f"{len(active_shipping)} coupons"})

    # Deactivate pending/generated gift coupons
    active_gifts = session.query(GiftCoupon).filter(
        GiftCoupon.member_id == member.id,
        GiftCoupon.status.in_(["pending", "generated"]),
    ).all()
    for c in active_gifts:
        c.status = "expired"
    if active_gifts:
        results.append({"benefit": "monthly_gift", "status": "deactivated",
                        "detail": f"{len(active_gifts)} coupons"})

    session.commit()
    return results


def reset_monthly_benefits(session, member, plan, salla_client=None) -> List[Dict]:
    """Reset quotas on renewal. Called on subscription.charge.succeeded.
    PRD §8.3: "Quota resets. New gift generated. Member notified."
    """
    results = []

    # Reset free shipping
    fs_result = activate_free_shipping(session, member, plan, salla_client)
    results.append(fs_result.as_dict())

    # New gift (Gold only)
    gift_result = activate_monthly_gift(session, member, plan, salla_client)
    results.append(gift_result.as_dict())

    session.commit()
    return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _end_of_month(dt: datetime) -> datetime:
    """Last moment of the current month."""
    next_month = (dt.replace(day=28) + timedelta(days=5)).replace(day=1)
    return next_month - timedelta(seconds=1)


def _log_activity(session, member, event_type: str, metadata: dict) -> None:
    """Write to activity_log."""
    import json
    from database.models import ActivityLog

    session.add(ActivityLog(
        merchant_id=member.merchant_id,
        event_type=event_type,
        member_id=member.id,
        metadata_json=json.dumps(metadata, ensure_ascii=False),
    ))
    session.commit()

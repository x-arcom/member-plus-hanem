"""Benefits service — V2 adapter.

Provides generate_monthly_gifts() for the scheduler, using V2 models (Member,
MembershipPlan, GiftCoupon) instead of the old V1 models.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger("benefits.service")


def generate_monthly_gifts(
    session,
    now: Optional[datetime] = None,
    client_factory=None,
) -> List[Dict]:
    """For every active Gold member, issue this month's gift coupon
    if one doesn't already exist. Uses V2 models."""
    from database.models import Member, MembershipPlan, GiftCoupon
    from benefits.engine import activate_monthly_gift

    now = now or datetime.utcnow()
    month_str = now.strftime("%Y-%m")

    # Find all active members on Gold plans
    members = session.query(Member).filter(Member.status == "active").all()
    plan_cache = {}
    created = []

    for member in members:
        if member.plan_id not in plan_cache:
            plan_cache[member.plan_id] = session.query(MembershipPlan).filter(
                MembershipPlan.id == member.plan_id
            ).first()
        plan = plan_cache.get(member.plan_id)
        if not plan or plan.tier != "gold":
            continue

        # Check if gift already exists for this month
        existing = session.query(GiftCoupon).filter(
            GiftCoupon.member_id == member.id,
            GiftCoupon.month == month_str,
        ).first()
        if existing:
            continue

        result = activate_monthly_gift(session, member, plan, salla_client=None)
        if result.status == "activated":
            created.append(result.as_dict())

    if created:
        session.commit()
        logger.info("monthly gifts: %d generated for %s", len(created), month_str)

    return created

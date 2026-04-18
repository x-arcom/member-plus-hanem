"""Salla resource provisioning.

Phase R scope: create a Salla customer group for each of a merchant's
membership plans and persist the returned group id on the plan.

Design:
- `provision_plan(session, plan_id, client_factory=...)` is the unit of work —
  creates a group if the plan doesn't yet have one.
- `provision_merchant_program(session, merchant_id, client_factory=...)` runs
  `provision_plan` for each plan that needs one, returning a per-plan report.
- The client is injected so unit tests supply a fake `SallaClient` (or a
  stub transport) without real HTTP.
- All failures are captured per-plan — one plan failing doesn't abort the
  rest. Callers log + continue.
"""
import logging
from datetime import datetime
from typing import Callable, Dict, List, Optional

from database.models import MembershipPlan
from salla.client import SallaClient, SallaClientError


logger = logging.getLogger("salla.provisioning")


ClientFactory = Callable[[object, str], SallaClient]


def _default_client_factory(session, merchant_id: str) -> SallaClient:
    return SallaClient(session, merchant_id)


def _group_payload(plan: MembershipPlan) -> Dict:
    """Translate a plan into the Salla customer-group payload shape."""
    name = plan.display_name_en or plan.display_name_ar or f"Member Plus — {plan.tier or 'plan'}"
    return {"name": name}


def provision_plan(
    session,
    plan_id: str,
    client_factory: Optional[ClientFactory] = None,
) -> Dict:
    plan = session.query(MembershipPlan).filter(MembershipPlan.id == plan_id).first()
    if not plan:
        return {"plan_id": plan_id, "status": "not-found"}
    if plan.salla_group_id:
        return {"plan_id": plan_id, "status": "already-provisioned",
                "salla_group_id": plan.salla_group_id}

    factory = client_factory or _default_client_factory
    try:
        client = factory(session, plan.merchant_id)
    except SallaClientError as exc:
        logger.warning("cannot build SallaClient for merchant %s: %s", plan.merchant_id, exc)
        return {"plan_id": plan_id, "status": "failed", "error": str(exc)}

    try:
        response = client.post(
            "https://api.salla.dev/admin/v2/customers/groups",
            _group_payload(plan),
        )
    except SallaClientError as exc:
        logger.warning("customer-group create failed for plan %s: %s", plan_id, exc)
        return {"plan_id": plan_id, "status": "failed", "error": str(exc)}

    body = response.body or {}
    data = body.get("data") if isinstance(body, dict) else None
    group_id = None
    if isinstance(data, dict):
        group_id = data.get("id") or data.get("group_id")
    if not group_id and isinstance(body, dict):
        group_id = body.get("id")

    if not group_id:
        logger.warning("customer-group response missing id for plan %s: %s", plan_id, body)
        return {"plan_id": plan_id, "status": "failed", "error": "missing-group-id"}

    plan.salla_group_id = str(group_id)
    session.commit()
    logger.info("provisioned Salla customer group %s for plan %s", group_id, plan_id)
    return {
        "plan_id": plan_id, "status": "created",
        "salla_group_id": str(group_id),
    }


def _special_offer_payload(plan: MembershipPlan) -> Dict:
    """Translate a plan into a Salla special-offer payload matching their API.

    Salla requires: name, applied_channel, offer_type, applied_to,
    customer_groups (array), start_date, expiry_date, and a buy/get structure.
    """
    discount = float(plan.discount_pct or 0)
    name = f"{plan.display_name_en or plan.display_name_ar or plan.tier or 'Member'} — member discount"
    now = datetime.utcnow()
    far_future = now.replace(year=now.year + 5)

    return {
        "name": name,
        "applied_channel": "browser_and_application",
        "offer_type": "buy_x_get_y",
        "applied_to": "order",
        "customer_groups": [int(plan.salla_group_id)] if plan.salla_group_id else [],
        "start_date": now.strftime("%Y-%m-%d %H:%M"),
        "expiry_date": far_future.strftime("%Y-%m-%d %H:%M"),
        "buy": {"quantity": 1, "type": "product"},
        "get": {"discount_type": "percentage", "discount_amount": str(discount)},
    }


def provision_special_offer(
    session,
    plan_id: str,
    client_factory: Optional[ClientFactory] = None,
) -> Dict:
    """Phase G — create a Salla special offer bound to the plan's customer
    group. No-ops when the plan has no discount configured or no customer
    group yet."""
    plan = session.query(MembershipPlan).filter(MembershipPlan.id == plan_id).first()
    if not plan:
        return {"plan_id": plan_id, "status": "not-found"}
    if plan.salla_offer_id:
        return {
            "plan_id": plan_id, "status": "already-provisioned",
            "salla_offer_id": plan.salla_offer_id,
        }
    if not plan.discount_pct or float(plan.discount_pct) <= 0:
        return {"plan_id": plan_id, "status": "skipped", "reason": "no-discount"}
    if not plan.salla_group_id:
        return {"plan_id": plan_id, "status": "skipped", "reason": "no-customer-group"}

    factory = client_factory or _default_client_factory
    try:
        client = factory(session, plan.merchant_id)
    except SallaClientError as exc:
        logger.warning("cannot build SallaClient for merchant %s: %s", plan.merchant_id, exc)
        return {"plan_id": plan_id, "status": "failed", "error": str(exc)}

    try:
        response = client.post(
            "https://api.salla.dev/admin/v2/specialoffers",
            _special_offer_payload(plan),
        )
    except SallaClientError as exc:
        logger.warning("special-offer create failed for plan %s: %s", plan_id, exc)
        return {"plan_id": plan_id, "status": "failed", "error": str(exc)}

    body = response.body or {}
    data = body.get("data") if isinstance(body, dict) else None
    offer_id = None
    if isinstance(data, dict):
        offer_id = data.get("id") or data.get("offer_id")
    if not offer_id and isinstance(body, dict):
        offer_id = body.get("id")

    if not offer_id:
        logger.warning("special-offer response missing id for plan %s: %s", plan_id, body)
        return {"plan_id": plan_id, "status": "failed", "error": "missing-offer-id"}

    plan.salla_offer_id = str(offer_id)
    session.commit()
    logger.info("provisioned Salla special offer %s for plan %s", offer_id, plan_id)
    return {
        "plan_id": plan_id, "status": "created",
        "salla_offer_id": str(offer_id),
    }


def provision_merchant_program(
    session,
    merchant_id: str,
    client_factory: Optional[ClientFactory] = None,
) -> List[Dict]:
    """Create both the customer group and the special offer for every plan
    of a merchant. Order matters — the offer is bound to the group."""
    plans = (
        session.query(MembershipPlan)
        .filter(MembershipPlan.merchant_id == merchant_id)
        .all()
    )
    reports = []
    for plan in plans:
        reports.append(provision_plan(session, plan.id, client_factory=client_factory))
        reports.append(provision_special_offer(session, plan.id, client_factory=client_factory))
    return reports

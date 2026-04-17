"""Billing / subscription service."""
from datetime import datetime, timedelta
from typing import List, Optional

from database.models import Merchant, Subscription
from billing.adapter import PaymentAdapter, get_payment_adapter, reset_payment_adapter  # noqa: F401


TIERS: List[dict] = [
    {"tier": "starter", "name_en": "Starter", "name_ar": "المبتدئ", "price": 49.0, "currency": "SAR", "period_days": 30},
    {"tier": "growth",  "name_en": "Growth",  "name_ar": "النمو",   "price": 149.0, "currency": "SAR", "period_days": 30},
    {"tier": "pro",     "name_en": "Pro",     "name_ar": "المحترف", "price": 299.0, "currency": "SAR", "period_days": 30},
]


class BillingError(Exception):
    """Raised for billing business-rule violations (mapped to 4xx in routes)."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _tier(tier_name: str) -> Optional[dict]:
    return next((t for t in TIERS if t["tier"] == tier_name), None)


def _to_dict(sub: Subscription) -> dict:
    return {
        "id": sub.id,
        "merchant_id": sub.merchant_id,
        "tier": sub.tier,
        "status": sub.status,
        "started_at": sub.started_at.isoformat() if sub.started_at else None,
        "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
        "payment_reference": sub.payment_reference,
    }


class BillingService:
    def __init__(self, db_session, adapter: Optional[PaymentAdapter] = None):
        self.db = db_session
        self.adapter = adapter or get_payment_adapter()

    def tiers(self) -> List[dict]:
        return list(TIERS)

    def get_subscription(self, merchant_id: str) -> Optional[dict]:
        sub = self._latest(merchant_id)
        return _to_dict(sub) if sub else None

    def subscribe(self, merchant_id: str, tier_name: str) -> dict:
        tier = _tier(tier_name)
        if not tier:
            raise BillingError(f"Unknown tier: {tier_name}", status_code=400)

        existing = self._active(merchant_id)
        if existing:
            raise BillingError("Merchant already has an active subscription", status_code=409)

        intent = self.adapter.create_intent(
            merchant_id, tier_name, tier["price"], tier["currency"]
        )
        sub = Subscription(
            merchant_id=merchant_id,
            tier=tier_name,
            status="pending",
            payment_reference=intent.reference,
        )
        self.db.add(sub)
        self.db.commit()
        self.db.refresh(sub)
        return {
            "subscription": _to_dict(sub),
            "payment_intent": {
                "reference": intent.reference,
                "amount": intent.amount,
                "currency": intent.currency,
                "status": intent.status,
            },
        }

    def confirm(self, merchant_id: str, subscription_id: str, success: bool = True) -> dict:
        sub = (
            self.db.query(Subscription)
            .filter(Subscription.id == subscription_id, Subscription.merchant_id == merchant_id)
            .first()
        )
        if not sub:
            raise BillingError("Subscription not found", status_code=404)
        if sub.status != "pending":
            raise BillingError(f"Subscription is already {sub.status}", status_code=409)

        if not sub.payment_reference:
            raise BillingError("Subscription has no payment reference", status_code=400)

        intent = self.adapter.confirm(sub.payment_reference, success=success)

        if intent.status == "succeeded":
            tier = _tier(sub.tier) or {"period_days": 30}
            sub.status = "active"
            sub.started_at = datetime.utcnow()
            sub.current_period_end = sub.started_at + timedelta(days=tier["period_days"])
            merchant = self.db.query(Merchant).filter(Merchant.id == merchant_id).first()
            if merchant:
                merchant.subscription_id = sub.id
        else:
            sub.status = "cancelled"

        self.db.commit()
        self.db.refresh(sub)
        return _to_dict(sub)

    def _active(self, merchant_id: str) -> Optional[Subscription]:
        return (
            self.db.query(Subscription)
            .filter(Subscription.merchant_id == merchant_id, Subscription.status == "active")
            .first()
        )

    def _latest(self, merchant_id: str) -> Optional[Subscription]:
        return (
            self.db.query(Subscription)
            .filter(Subscription.merchant_id == merchant_id)
            .order_by(Subscription.created_at.desc())
            .first()
        )

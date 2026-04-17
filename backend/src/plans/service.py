"""Plan service — merchant-scoped CRUD for membership plans."""
from decimal import Decimal, InvalidOperation
from typing import List, Optional

from database.models import MembershipPlan


class PlanValidationError(ValueError):
    """Raised when a plan payload is invalid."""


def _coerce_price(value) -> Decimal:
    try:
        price = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise PlanValidationError("price must be a number")
    if price < 0:
        raise PlanValidationError("price must be >= 0")
    return price


VALID_TIERS = ("silver", "gold")


def _validate_payload(payload: dict, partial: bool = False) -> dict:
    required = ["name_ar", "name_en", "price", "duration_days"]
    if not partial:
        for key in required:
            if key not in payload or payload[key] in (None, ""):
                raise PlanValidationError(f"{key} is required")

    cleaned = {}
    if "name_ar" in payload:
        if not str(payload["name_ar"]).strip():
            raise PlanValidationError("name_ar must be non-empty")
        cleaned["name_ar"] = str(payload["name_ar"]).strip()
    if "name_en" in payload:
        if not str(payload["name_en"]).strip():
            raise PlanValidationError("name_en must be non-empty")
        cleaned["name_en"] = str(payload["name_en"]).strip()
    if "price" in payload:
        cleaned["price"] = _coerce_price(payload["price"])
    if "duration_days" in payload:
        try:
            days = int(payload["duration_days"])
        except (ValueError, TypeError):
            raise PlanValidationError("duration_days must be an integer")
        if days <= 0:
            raise PlanValidationError("duration_days must be > 0")
        cleaned["duration_days"] = days
    if "currency" in payload and payload["currency"]:
        cleaned["currency"] = str(payload["currency"]).upper()[:10]
    if "benefits" in payload:
        cleaned["benefits"] = payload["benefits"]
    if "is_active" in payload:
        cleaned["is_active"] = bool(payload["is_active"])

    # Phase-R structured benefit fields
    if "tier" in payload and payload["tier"] is not None:
        tier = str(payload["tier"]).lower()
        if tier not in VALID_TIERS:
            raise PlanValidationError(f"tier must be one of {VALID_TIERS} or null")
        cleaned["tier"] = tier

    if "discount_percent" in payload and payload["discount_percent"] is not None:
        try:
            pct = Decimal(str(payload["discount_percent"]))
        except (InvalidOperation, TypeError):
            raise PlanValidationError("discount_percent must be a number")
        if pct < 0 or pct > 100:
            raise PlanValidationError("discount_percent must be between 0 and 100")
        cleaned["discount_percent"] = pct

    if "free_shipping_quota" in payload and payload["free_shipping_quota"] is not None:
        try:
            q = int(payload["free_shipping_quota"])
        except (ValueError, TypeError):
            raise PlanValidationError("free_shipping_quota must be an integer")
        if q < 0:
            raise PlanValidationError("free_shipping_quota must be >= 0")
        cleaned["free_shipping_quota"] = q

    for bool_key in ("monthly_gift_enabled", "early_access_enabled", "badge_enabled"):
        if bool_key in payload:
            cleaned[bool_key] = bool(payload[bool_key])

    return cleaned


def _to_dict(plan: MembershipPlan) -> dict:
    return {
        "id": plan.id,
        "merchant_id": plan.merchant_id,
        "tier": plan.tier,
        "name_ar": plan.name_ar,
        "name_en": plan.name_en,
        "price": str(plan.price),
        "currency": plan.currency,
        "duration_days": plan.duration_days,
        "benefits": plan.benefits,
        "discount_percent": str(plan.discount_percent) if plan.discount_percent is not None else None,
        "free_shipping_quota": plan.free_shipping_quota,
        "monthly_gift_enabled": plan.monthly_gift_enabled,
        "early_access_enabled": plan.early_access_enabled,
        "badge_enabled": plan.badge_enabled,
        "salla_customer_group_id": plan.salla_customer_group_id,
        "is_active": plan.is_active,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
        "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
    }


class PlanService:
    def __init__(self, db_session):
        self.db = db_session

    def create(self, merchant_id: str, payload: dict) -> dict:
        data = _validate_payload(payload)
        plan = MembershipPlan(
            merchant_id=merchant_id,
            tier=data.get("tier"),
            name_ar=data["name_ar"],
            name_en=data["name_en"],
            price=data["price"],
            currency=data.get("currency", "SAR"),
            duration_days=data["duration_days"],
            benefits=data.get("benefits"),
            discount_percent=data.get("discount_percent"),
            free_shipping_quota=data.get("free_shipping_quota"),
            monthly_gift_enabled=data.get("monthly_gift_enabled", False),
            early_access_enabled=data.get("early_access_enabled", False),
            badge_enabled=data.get("badge_enabled", False),
            is_active=data.get("is_active", True),
        )
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return _to_dict(plan)

    def list(self, merchant_id: str, active_only: bool = False) -> List[dict]:
        query = self.db.query(MembershipPlan).filter(MembershipPlan.merchant_id == merchant_id)
        if active_only:
            query = query.filter(MembershipPlan.is_active.is_(True))
        return [_to_dict(p) for p in query.order_by(MembershipPlan.created_at.desc()).all()]

    def get(self, merchant_id: str, plan_id: str) -> Optional[dict]:
        plan = self._get_owned(merchant_id, plan_id)
        return _to_dict(plan) if plan else None

    def update(self, merchant_id: str, plan_id: str, payload: dict) -> Optional[dict]:
        plan = self._get_owned(merchant_id, plan_id)
        if not plan:
            return None
        data = _validate_payload(payload, partial=True)
        for key, value in data.items():
            setattr(plan, key, value)
        self.db.commit()
        self.db.refresh(plan)
        return _to_dict(plan)

    def delete(self, merchant_id: str, plan_id: str) -> bool:
        plan = self._get_owned(merchant_id, plan_id)
        if not plan:
            return False
        self.db.delete(plan)
        self.db.commit()
        return True

    def _get_owned(self, merchant_id: str, plan_id: str) -> Optional[MembershipPlan]:
        return (
            self.db.query(MembershipPlan)
            .filter(MembershipPlan.id == plan_id, MembershipPlan.merchant_id == merchant_id)
            .first()
        )

"""Customer enrollment service — public, no-auth path."""
import re
from typing import Optional

from datetime import datetime

from database.models import (
    Customer, CustomerSubscription, InterestSignup, Merchant, MembershipPlan,
)


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class EnrollmentError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _customer_to_dict(c: Customer) -> dict:
    return {
        "id": c.id, "merchant_id": c.merchant_id,
        "name": c.name, "email": c.email, "phone": c.phone,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


def _sub_to_dict(s: CustomerSubscription) -> dict:
    return {
        "id": s.id, "customer_id": s.customer_id,
        "merchant_id": s.merchant_id, "plan_id": s.plan_id,
        "status": s.status,
        "started_at": s.started_at.isoformat() if s.started_at else None,
        "expires_at": s.expires_at.isoformat() if s.expires_at else None,
        "activated_at": s.activated_at.isoformat() if s.activated_at else None,
        "price": str(s.price_at_enrollment),
        "currency": s.currency_at_enrollment,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


class CustomerEnrollmentService:
    def __init__(self, db_session):
        self.db = db_session

    def lookup_membership(self, salla_store_id: str, email: str) -> dict:
        """Phase R — customer-side read-only membership summary.

        Returns the customer's current subscription for a given merchant, or
        an empty summary if they haven't enrolled yet. Keyed by email for
        Phase R (real auth arrives in a later phase)."""
        merchant = self._resolve_active_merchant(salla_store_id)
        email = (email or "").strip().lower()
        if not email or not EMAIL_RE.match(email):
            raise EnrollmentError("email is invalid")

        customer = (
            self.db.query(Customer)
            .filter(Customer.merchant_id == merchant.id, Customer.email == email)
            .first()
        )
        if not customer:
            return {
                "merchant": {"id": merchant.id, "store_name": merchant.store_name},
                "customer": None, "subscriptions": [],
            }

        subs = (
            self.db.query(CustomerSubscription, MembershipPlan)
            .join(MembershipPlan, MembershipPlan.id == CustomerSubscription.plan_id)
            .filter(CustomerSubscription.customer_id == customer.id)
            .order_by(CustomerSubscription.created_at.desc())
            .all()
        )

        from benefits.service import list_for_subscription, sum_savings_for_subscription

        def _with_plan(sub, plan):
            return {
                **_sub_to_dict(sub),
                "grace_ends_at": sub.grace_ends_at.isoformat() if sub.grace_ends_at else None,
                "plan": {
                    "id": plan.id, "tier": plan.tier,
                    "name_ar": plan.name_ar, "name_en": plan.name_en,
                    "discount_percent": str(plan.discount_percent) if plan.discount_percent is not None else None,
                    "free_shipping_quota": plan.free_shipping_quota,
                    "monthly_gift_enabled": plan.monthly_gift_enabled,
                    "early_access_enabled": plan.early_access_enabled,
                    "badge_enabled": plan.badge_enabled,
                    "duration_days": plan.duration_days,
                },
                "benefits": list_for_subscription(self.db, sub.id),
                "savings_estimate": sum_savings_for_subscription(self.db, sub.id),
            }

        return {
            "merchant": {"id": merchant.id, "store_name": merchant.store_name},
            "customer": _customer_to_dict(customer),
            "subscriptions": [_with_plan(s, p) for s, p in subs],
        }

    def list_active_plans_for_store(self, salla_store_id: str) -> dict:
        merchant = self._resolve_active_merchant(salla_store_id)
        plans = (
            self.db.query(MembershipPlan)
            .filter(
                MembershipPlan.merchant_id == merchant.id,
                MembershipPlan.is_active.is_(True),
            )
            .order_by(MembershipPlan.price.asc())
            .all()
        )
        return {
            "merchant": {
                "id": merchant.id,
                "store_name": merchant.store_name,
                "salla_store_id": merchant.salla_store_id,
            },
            # Phase G — frontend switches to the interest/coming-soon variant
            # when there are zero active plans.
            "store_state": "available" if plans else "coming_soon",
            "plans": [
                {
                    "id": p.id,
                    "tier": p.tier,
                    "name_ar": p.name_ar, "name_en": p.name_en,
                    "price": str(p.price), "currency": p.currency,
                    "duration_days": p.duration_days,
                    "benefits": p.benefits,
                    "discount_percent": str(p.discount_percent) if p.discount_percent is not None else None,
                    "free_shipping_quota": p.free_shipping_quota,
                    "monthly_gift_enabled": p.monthly_gift_enabled,
                    "early_access_enabled": p.early_access_enabled,
                    "badge_enabled": p.badge_enabled,
                }
                for p in plans
            ],
        }

    def register_interest(self, salla_store_id: str, email: str) -> dict:
        """Phase G — capture interest when the program isn't live yet."""
        email = (email or "").strip().lower()
        if not email or not EMAIL_RE.match(email):
            raise EnrollmentError("email is invalid")

        merchant = (
            self.db.query(Merchant)
            .filter(Merchant.salla_store_id == str(salla_store_id))
            .first()
        )

        row = (
            self.db.query(InterestSignup)
            .filter(
                InterestSignup.salla_store_id == str(salla_store_id),
                InterestSignup.email == email,
            )
            .first()
        )
        if row:
            row.signed_up_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(row)
            return {"id": row.id, "already_registered": True}

        row = InterestSignup(
            salla_store_id=str(salla_store_id),
            merchant_id=merchant.id if merchant else None,
            email=email,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return {"id": row.id, "already_registered": False}

    def enroll(self, salla_store_id: str, payload: dict) -> dict:
        merchant = self._resolve_active_merchant(salla_store_id)

        name = (payload.get("name") or "").strip()
        email = (payload.get("email") or "").strip().lower()
        phone = (payload.get("phone") or "").strip() or None
        plan_id = (payload.get("plan_id") or "").strip()

        if not name:
            raise EnrollmentError("name is required")
        if not email or not EMAIL_RE.match(email):
            raise EnrollmentError("email is invalid")
        if not plan_id:
            raise EnrollmentError("plan_id is required")

        plan = (
            self.db.query(MembershipPlan)
            .filter(
                MembershipPlan.id == plan_id,
                MembershipPlan.merchant_id == merchant.id,
                MembershipPlan.is_active.is_(True),
            )
            .first()
        )
        if not plan:
            raise EnrollmentError("plan not found or inactive", status_code=404)

        # Upsert customer by (merchant_id, email)
        customer = (
            self.db.query(Customer)
            .filter(Customer.merchant_id == merchant.id, Customer.email == email)
            .first()
        )
        if customer:
            customer.name = name  # allow correction on re-enroll
            if phone:
                customer.phone = phone
        else:
            customer = Customer(
                merchant_id=merchant.id, name=name, email=email, phone=phone,
            )
            self.db.add(customer)
            self.db.flush()  # get id

        # Block duplicate active or pending for the same plan (idempotency)
        existing_open = (
            self.db.query(CustomerSubscription)
            .filter(
                CustomerSubscription.customer_id == customer.id,
                CustomerSubscription.plan_id == plan.id,
                CustomerSubscription.status.in_(["pending", "active"]),
            )
            .first()
        )
        if existing_open:
            self.db.commit()
            return {
                "customer": _customer_to_dict(customer),
                "subscription": _sub_to_dict(existing_open),
                "already_enrolled": True,
            }

        subscription = CustomerSubscription(
            customer_id=customer.id,
            merchant_id=merchant.id,
            plan_id=plan.id,
            status="pending",
            price_at_enrollment=plan.price,
            currency_at_enrollment=plan.currency,
        )
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(customer)
        self.db.refresh(subscription)

        return {
            "customer": _customer_to_dict(customer),
            "subscription": _sub_to_dict(subscription),
            "already_enrolled": False,
        }

    def _resolve_active_merchant(self, salla_store_id: str) -> Merchant:
        if not salla_store_id:
            raise EnrollmentError("store id is required", status_code=404)
        merchant = (
            self.db.query(Merchant)
            .filter(Merchant.salla_store_id == str(salla_store_id))
            .first()
        )
        if not merchant:
            raise EnrollmentError("merchant not found", status_code=404)
        if merchant.is_active is False:
            raise EnrollmentError("merchant is inactive", status_code=410)
        return merchant

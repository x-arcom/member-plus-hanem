"""Member management service — authenticated, merchant-scoped."""
from datetime import datetime, timedelta
from typing import List, Optional

from database.models import (
    Customer, CustomerSubscription, MembershipPlan,
)


class MemberError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _row_to_dict(sub: CustomerSubscription, customer: Customer, plan: MembershipPlan, lang: str = "ar") -> dict:
    return {
        "subscription_id": sub.id,
        "customer": {
            "id": customer.id, "name": customer.name,
            "email": customer.email, "phone": customer.phone,
        },
        "plan": {
            "id": plan.id,
            "name": plan.name_ar if lang == "ar" else plan.name_en,
            "name_ar": plan.name_ar, "name_en": plan.name_en,
            "price": str(plan.price), "currency": plan.currency,
            "duration_days": plan.duration_days,
        },
        "status": sub.status,
        "started_at": sub.started_at.isoformat() if sub.started_at else None,
        "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
        "activated_at": sub.activated_at.isoformat() if sub.activated_at else None,
        "enrolled_at": sub.created_at.isoformat() if sub.created_at else None,
        "price_at_enrollment": str(sub.price_at_enrollment),
    }


class MemberService:
    def __init__(self, db_session):
        self.db = db_session

    def list(self, merchant_id: str, status: Optional[str] = None) -> List[dict]:
        # Precompute benefit counts per subscription for the merchant
        from sqlalchemy import func
        from database.models import BenefitDelivery

        bc_rows = (
            self.db.query(
                BenefitDelivery.subscription_id,
                func.count(BenefitDelivery.id),
            )
            .filter(BenefitDelivery.merchant_id == merchant_id)
            .group_by(BenefitDelivery.subscription_id)
            .all()
        )
        benefit_counts = {sid: n for sid, n in bc_rows}

        query = (
            self.db.query(CustomerSubscription, Customer, MembershipPlan)
            .join(Customer, Customer.id == CustomerSubscription.customer_id)
            .join(MembershipPlan, MembershipPlan.id == CustomerSubscription.plan_id)
            .filter(CustomerSubscription.merchant_id == merchant_id)
        )
        if status:
            query = query.filter(CustomerSubscription.status == status)
        query = query.order_by(CustomerSubscription.created_at.desc())
        out = []
        for sub, cust, plan in query.all():
            row = _row_to_dict(sub, cust, plan)
            row["benefit_count"] = int(benefit_counts.get(sub.id, 0))
            out.append(row)
        return out

    def confirm(self, merchant_id: str, subscription_id: str) -> dict:
        sub, cust, plan = self._get_owned(merchant_id, subscription_id)
        if sub.status == "active":
            return _row_to_dict(sub, cust, plan)
        if sub.status not in ("pending",):
            raise MemberError(f"cannot confirm a {sub.status} subscription", status_code=409)

        now = datetime.utcnow()
        sub.status = "active"
        sub.started_at = now
        sub.activated_at = now
        sub.expires_at = now + timedelta(days=plan.duration_days)
        self.db.commit()
        self.db.refresh(sub)

        # Fire benefit generation in a background thread so Salla API calls
        # don't make the confirm endpoint slow or block the DB session.
        self._fire_benefit_generation(subscription_id)

        return _row_to_dict(sub, cust, plan)

    @staticmethod
    def _fire_benefit_generation(subscription_id: str) -> None:
        import threading
        try:
            from benefits.service import generate_on_activation
        except ImportError:
            return

        def _run():
            try:
                from sqlalchemy import create_engine
                from sqlalchemy.orm import sessionmaker
                from config.loader import load_config
                from database.models import Base

                engine = create_engine(load_config().database_url)
                Base.metadata.create_all(engine)
                Session = sessionmaker(bind=engine)
                session = Session()
                try:
                    generate_on_activation(session, subscription_id)
                finally:
                    session.close()
            except Exception:
                import logging
                logging.getLogger("members").exception("benefit generation thread failed")

        threading.Thread(target=_run, daemon=True).start()

    def cancel(self, merchant_id: str, subscription_id: str) -> dict:
        sub, cust, plan = self._get_owned(merchant_id, subscription_id)
        if sub.status in ("cancelled", "expired"):
            return _row_to_dict(sub, cust, plan)
        sub.status = "cancelled"
        self.db.commit()
        self.db.refresh(sub)

        # Phase G clawback — revoke still-usable coupons
        try:
            from benefits.service import revoke_for_subscription
            revoke_for_subscription(self.db, sub.id)
        except Exception:
            import logging
            logging.getLogger("members").exception("clawback failed for %s", sub.id)

        return _row_to_dict(sub, cust, plan)

    def renew(self, merchant_id: str, subscription_id: str) -> dict:
        """Phase G. From active/grace: extend current period. From
        expired/cancelled: start a fresh subscription on the same plan."""
        sub, cust, plan = self._get_owned(merchant_id, subscription_id)
        now = datetime.utcnow()

        if sub.status in ("active", "grace"):
            base = sub.expires_at if (sub.expires_at and sub.expires_at > now) else now
            sub.expires_at = base + timedelta(days=plan.duration_days)
            sub.grace_ends_at = None
            sub.status = "active"
            self.db.commit()
            self.db.refresh(sub)
            return _row_to_dict(sub, cust, plan)

        if sub.status in ("expired", "cancelled"):
            new_sub = CustomerSubscription(
                customer_id=sub.customer_id,
                merchant_id=sub.merchant_id,
                plan_id=sub.plan_id,
                status="active",
                started_at=now,
                activated_at=now,
                expires_at=now + timedelta(days=plan.duration_days),
                price_at_enrollment=plan.price,
                currency_at_enrollment=plan.currency,
            )
            self.db.add(new_sub)
            self.db.commit()
            self.db.refresh(new_sub)
            self._fire_benefit_generation(new_sub.id)
            return _row_to_dict(new_sub, cust, plan)

        raise MemberError(f"cannot renew a {sub.status} subscription", status_code=409)

    def _get_owned(self, merchant_id: str, subscription_id: str):
        row = (
            self.db.query(CustomerSubscription, Customer, MembershipPlan)
            .join(Customer, Customer.id == CustomerSubscription.customer_id)
            .join(MembershipPlan, MembershipPlan.id == CustomerSubscription.plan_id)
            .filter(
                CustomerSubscription.id == subscription_id,
                CustomerSubscription.merchant_id == merchant_id,
            )
            .first()
        )
        if not row:
            raise MemberError("subscription not found", status_code=404)
        return row

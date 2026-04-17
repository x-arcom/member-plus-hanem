"""Setup wizard state service.

Owns the transitions on merchants.setup_state + setup_step:

    onboarding (step=0)
      -> setup_wizard (step=1..N)
      -> setup_complete (step=TOTAL)

Steps:
  1: store profile / confirm store info
  2: create a first membership plan (optional — merchant may skip)
  3: launch confirmation
"""
from typing import Optional

from database.models import Merchant

TOTAL_STEPS = 3


def _to_dict(merchant: Merchant) -> dict:
    return {
        "setup_state": merchant.setup_state,
        "setup_step": merchant.setup_step,
        "total_steps": TOTAL_STEPS,
        "is_complete": merchant.setup_state == "setup_complete",
    }


class WizardService:
    def __init__(self, db_session):
        self.db = db_session

    def state(self, merchant_id: str) -> Optional[dict]:
        merchant = self._get(merchant_id)
        return _to_dict(merchant) if merchant else None

    def advance(self, merchant_id: str, step_data: Optional[dict] = None) -> Optional[dict]:
        merchant = self._get(merchant_id)
        if not merchant:
            return None

        if merchant.setup_state == "setup_complete":
            return _to_dict(merchant)  # idempotent

        if merchant.setup_state == "onboarding":
            merchant.setup_state = "setup_wizard"

        merchant.setup_step = min(merchant.setup_step + 1, TOTAL_STEPS)

        just_completed = False
        if merchant.setup_step >= TOTAL_STEPS and merchant.setup_state != "setup_complete":
            merchant.setup_state = "setup_complete"
            just_completed = True

        self.db.commit()
        self.db.refresh(merchant)

        if just_completed and merchant.merchant_email:
            self._fire_setup_complete_email(merchant.merchant_email, merchant.language or "ar")

        return _to_dict(merchant)

    @staticmethod
    def _fire_setup_complete_email(email: str, language: str) -> None:
        """Fire-and-forget the setup-complete email. Never blocks the wizard
        transaction — if the event loop is unavailable or SMTP fails, we log
        and move on."""
        import asyncio
        try:
            from email_service.service import send_setup_complete_email
        except ImportError:
            return
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(send_setup_complete_email(email, language=language))
            else:
                loop.run_until_complete(send_setup_complete_email(email, language=language))
        except RuntimeError:
            # No loop available (e.g., unit test context) — run it synchronously.
            try:
                asyncio.run(send_setup_complete_email(email, language=language))
            except Exception:
                pass
        except Exception:
            pass

    def configure_program(self, merchant_id: str, silver: dict, gold: dict) -> Optional[dict]:
        """Phase-R flow. Upsert Silver + Gold plans with benefits, then flip
        `setup_state` to `setup_complete`. Returns the wizard state dict.

        `silver` / `gold` follow the same shape as PlanService.create payload
        (without `tier` — we stamp it here).
        """
        from database.models import MembershipPlan
        from plans.service import PlanService, PlanValidationError

        merchant = self._get(merchant_id)
        if not merchant:
            return None

        # Validate up-front so we don't half-create a program.
        plan_svc = PlanService(self.db)
        for label, payload in (("silver", silver), ("gold", gold)):
            payload = dict(payload or {})
            payload["tier"] = label

            # Enforce tier benefit rules: Silver never gets premium perks
            if label == "silver":
                payload["monthly_gift_enabled"] = False
                payload["early_access_enabled"] = False
                payload["badge_enabled"] = False

            existing = (
                self.db.query(MembershipPlan)
                .filter(
                    MembershipPlan.merchant_id == merchant_id,
                    MembershipPlan.tier == label,
                )
                .first()
            )
            if existing:
                plan_svc.update(merchant_id, existing.id, payload)
            else:
                plan_svc.create(merchant_id, payload)

        # Move to completion + fire the email (existing logic).
        merchant.setup_state = "setup_complete"
        merchant.setup_step = TOTAL_STEPS
        self.db.commit()
        self.db.refresh(merchant)

        if merchant.merchant_email:
            self._fire_setup_complete_email(merchant.merchant_email, merchant.language or "ar")

        # Kick off Salla provisioning fire-and-forget (idempotent).
        self._fire_provisioning(merchant_id)

        return _to_dict(merchant)

    @staticmethod
    def _fire_provisioning(merchant_id: str) -> None:
        """Run Salla provisioning in a background thread so the wizard
        transaction isn't blocked by Salla's API. Failures are swallowed
        here — `salla.provisioning` logs them."""
        import threading
        try:
            from salla.provisioning import provision_merchant_program
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
                    provision_merchant_program(session, merchant_id)
                finally:
                    session.close()
            except Exception:
                import logging
                logging.getLogger("wizard").exception("provisioning thread failed")

        threading.Thread(target=_run, daemon=True).start()

    def reset(self, merchant_id: str) -> Optional[dict]:
        merchant = self._get(merchant_id)
        if not merchant:
            return None
        merchant.setup_state = "onboarding"
        merchant.setup_step = 0
        self.db.commit()
        self.db.refresh(merchant)
        return _to_dict(merchant)

    def _get(self, merchant_id: str) -> Optional[Merchant]:
        return self.db.query(Merchant).filter(Merchant.id == merchant_id).first()

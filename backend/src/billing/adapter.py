"""Payment adapter protocol + mock implementation.

Phase 2 uses MockPaymentAdapter. Phase 3 will add a real adapter (Stripe /
Paymob / Salla Pay) by implementing the same Protocol.
"""
from dataclasses import dataclass
from typing import Dict, Optional, Protocol
import uuid


@dataclass
class PaymentIntent:
    reference: str
    tier: str
    amount: float
    currency: str
    status: str  # 'requires_confirmation' | 'succeeded' | 'failed'


class PaymentAdapter(Protocol):
    def create_intent(self, merchant_id: str, tier: str, amount: float, currency: str) -> PaymentIntent: ...
    def confirm(self, reference: str, success: bool = True) -> PaymentIntent: ...


class MockPaymentAdapter:
    """In-memory payment adapter for Phase 2 tests and local dev."""

    def __init__(self):
        self._intents: Dict[str, PaymentIntent] = {}

    def create_intent(self, merchant_id: str, tier: str, amount: float, currency: str) -> PaymentIntent:
        ref = f"mock_pi_{uuid.uuid4().hex[:16]}"
        intent = PaymentIntent(
            reference=ref,
            tier=tier,
            amount=amount,
            currency=currency,
            status="requires_confirmation",
        )
        self._intents[ref] = intent
        return intent

    def confirm(self, reference: str, success: bool = True) -> PaymentIntent:
        intent = self._intents.get(reference)
        if not intent:
            raise KeyError(f"Unknown payment reference: {reference}")
        intent.status = "succeeded" if success else "failed"
        return intent


_singleton: Optional[PaymentAdapter] = None


def get_payment_adapter() -> PaymentAdapter:
    """Return the process-wide payment adapter.

    Selection order:
      1. `PAYMENT_PROVIDER=moyasar` with `MOYASAR_API_KEY` set → real adapter.
      2. Anything else → in-memory `MockPaymentAdapter` (Phase 2 default).

    Selection is lazy and cached — tests that want a fresh mock call
    `reset_payment_adapter()`.
    """
    global _singleton
    if _singleton is not None:
        return _singleton

    import os
    provider = (os.getenv("PAYMENT_PROVIDER") or "mock").strip().lower()
    if provider == "moyasar":
        api_key = os.getenv("MOYASAR_API_KEY", "").strip()
        if api_key:
            from billing.moyasar_adapter import MoyasarPaymentAdapter, MoyasarConfig
            _singleton = MoyasarPaymentAdapter(MoyasarConfig(
                api_key=api_key,
                base_url=os.getenv("MOYASAR_BASE_URL", "https://api.moyasar.com"),
                callback_url=os.getenv("MOYASAR_CALLBACK_URL") or None,
            ))
            return _singleton
        # provider asked for, but key missing: fall through to mock with a warning
        import logging
        logging.getLogger("billing").warning(
            "PAYMENT_PROVIDER=moyasar but MOYASAR_API_KEY is empty — falling back to mock adapter"
        )

    _singleton = MockPaymentAdapter()
    return _singleton


def reset_payment_adapter() -> None:
    """Force the next `get_payment_adapter()` call to re-read env."""
    global _singleton
    _singleton = None

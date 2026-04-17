"""Moyasar-compatible real payment adapter.

Moyasar is a popular Saudi payment gateway with a simple HTTP API. The
adapter here follows the same pattern as every other real integration in
this codebase:

- When MOYASAR_API_KEY is missing the adapter cannot operate, and the
  factory in `billing.adapter.get_payment_adapter` transparently falls back
  to `MockPaymentAdapter`.
- Transport is injectable for tests — pass a callable that mimics
  (method, url, payload, auth_header) -> (status, json_body).

This implementation uses Moyasar's `invoices` resource, which produces a
hosted-checkout URL suitable for redirecting the merchant — no card data
ever touches our servers.
"""
import base64
import json
import ssl
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from billing.adapter import PaymentAdapter, PaymentIntent


MoyasarTransport = Callable[[str, str, Optional[Dict], str], Tuple[int, Dict]]


def _default_transport(method, url, payload, auth_header) -> Tuple[int, Dict]:
    body = None
    headers = {"Accept": "application/json", "Authorization": auth_header}
    if payload is not None:
        body = urlencode(payload).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    req = Request(url, data=body, headers=headers, method=method)
    try:
        context = ssl.create_default_context()
        resp = urlopen(req, context=context, timeout=15)
        raw = resp.read().decode("utf-8") or "{}"
        return resp.status, json.loads(raw)
    except HTTPError as exc:
        try:
            raw = exc.read().decode("utf-8") or "{}"
            return exc.code, json.loads(raw)
        except (ValueError, AttributeError):
            return exc.code, {"error": str(exc)}
    except (URLError, ValueError) as exc:
        raise RuntimeError(f"Moyasar transport failed: {exc}") from exc


@dataclass
class MoyasarConfig:
    api_key: str
    base_url: str = "https://api.moyasar.com"
    callback_url: Optional[str] = None


class MoyasarPaymentAdapter:
    """PaymentAdapter backed by Moyasar's `invoices` API."""

    def __init__(self, config: MoyasarConfig, transport: Optional[MoyasarTransport] = None):
        if not config.api_key:
            raise ValueError("MoyasarPaymentAdapter requires a non-empty api_key")
        self.config = config
        self._transport = transport or _default_transport

    def _auth(self) -> str:
        token = base64.b64encode(f"{self.config.api_key}:".encode()).decode()
        return f"Basic {token}"

    def create_intent(self, merchant_id: str, tier: str, amount: float, currency: str) -> PaymentIntent:
        # Moyasar expects amount in the minor unit (halalas for SAR).
        amount_minor = int(round(amount * 100))
        payload = {
            "amount": amount_minor,
            "currency": currency,
            "description": f"Member Plus {tier} subscription",
            "metadata[merchant_id]": merchant_id,
            "metadata[tier]": tier,
        }
        if self.config.callback_url:
            payload["callback_url"] = self.config.callback_url

        status, body = self._transport(
            "POST",
            f"{self.config.base_url}/v1/invoices",
            payload,
            self._auth(),
        )
        if status >= 400 or "id" not in body:
            raise RuntimeError(f"Moyasar create_invoice failed ({status}): {body}")

        return PaymentIntent(
            reference=body["id"],
            tier=tier,
            amount=amount,
            currency=currency,
            status="requires_confirmation",
        )

    def confirm(self, reference: str, success: bool = True) -> PaymentIntent:
        """Poll Moyasar for the invoice status and translate it."""
        status, body = self._transport(
            "GET",
            f"{self.config.base_url}/v1/invoices/{reference}",
            None,
            self._auth(),
        )
        if status >= 400:
            raise RuntimeError(f"Moyasar get_invoice failed ({status}): {body}")

        gateway_status = (body.get("status") or "").lower()
        tier = (body.get("metadata") or {}).get("tier", "unknown")
        amount = (body.get("amount") or 0) / 100.0
        currency = body.get("currency", "SAR")

        if gateway_status in ("paid", "succeeded"):
            result = "succeeded"
        elif gateway_status in ("failed", "cancelled", "void"):
            result = "failed"
        else:
            # Still pending on Moyasar's side: in Phase 3 we don't long-poll —
            # callers treat this as `requires_confirmation` and re-check later.
            result = "requires_confirmation"

        # The caller of `confirm(..., success=False)` is explicitly forcing a
        # cancellation (e.g., the merchant aborted). We honor that without
        # hitting Moyasar for a refund — real refund flow is out of scope
        # for Phase 3.
        if success is False:
            result = "failed"

        return PaymentIntent(
            reference=reference,
            tier=tier,
            amount=amount,
            currency=currency,
            status=result,
        )


# ---- Implements PaymentAdapter Protocol -----------------------------------
_: PaymentAdapter = None  # type: ignore  # keeps type-checkers happy without runtime cost

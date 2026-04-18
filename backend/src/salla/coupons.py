"""Salla coupon creation with a mock fallback.

Design:
- `create_coupon(session, merchant_id, payload, client_factory=...)` is the
  unit of work — takes a generic payload dict that describes the coupon
  (kind, code, amount, usage_limit, valid_until, reason).
- When a real `SallaClient` can be built AND the Salla POST succeeds the
  returned id is recorded. Any SallaClientError (including 4xx / 5xx) is
  caught and the caller receives a fallback result — a local mock coupon
  with `salla_coupon_id=None` and `status='delivered-mock'`. This matches
  the same fallback pattern used for SMTP, OAuth and payments.
"""
import logging
import secrets
from dataclasses import dataclass
from typing import Callable, Dict, Optional

from salla.client import SallaClient, SallaClientError


logger = logging.getLogger("salla.coupons")


@dataclass
class CouponResult:
    coupon_code: str
    salla_coupon_id: Optional[str]
    status: str             # 'delivered' | 'delivered-mock'

    def as_dict(self) -> Dict:
        return {
            "coupon_code": self.coupon_code,
            "salla_coupon_id": self.salla_coupon_id,
            "status": self.status,
        }


ClientFactory = Callable[[object, str], SallaClient]


def _default_client_factory(session, merchant_id: str) -> SallaClient:
    return SallaClient(session, merchant_id)


def _mock_code(prefix: str) -> str:
    return f"MP-{prefix}-{secrets.token_hex(4).upper()}"


def create_coupon(
    session,
    merchant_id: str,
    payload: Dict,
    client_factory: Optional[ClientFactory] = None,
) -> CouponResult:
    """Create a Salla coupon, falling back to a locally-generated mock code
    whenever the Salla call cannot succeed.

    `payload` shape (Salla-agnostic):
      {
        "kind": "free_shipping" | "monthly_gift" | ...,
        "code_prefix": "FS" | "GIFT" | ...,
        "amount": 10,              # currency amount or percent (optional)
        "amount_type": "percentage" | "fixed",
        "usage_limit": 1,
        "expiry_date": "2026-04-30",  # YYYY-MM-DD (required by Salla)
        "free_shipping": False,       # True for free-shipping coupons
        "customer_ids": [123],        # restrict to specific customers
        "reason": "free string",
      }
    """
    from datetime import datetime, timedelta

    prefix = payload.get("code_prefix") or (payload.get("kind") or "CPN")[:2].upper()
    fallback_code = _mock_code(prefix)

    is_free_shipping = payload.get("free_shipping", False)
    expiry = payload.get("expiry_date")
    if not expiry:
        expiry = (datetime.utcnow() + timedelta(days=payload.get("valid_days", 30))).strftime("%Y-%m-%d")

    salla_body = {
        "code": fallback_code,
        "type": "fixed" if is_free_shipping else payload.get("amount_type", "percentage"),
        "amount": 0 if is_free_shipping else (payload.get("amount") or 0),
        "free_shipping": is_free_shipping,
        "expiry_date": expiry,
        "exclude_sale_products": payload.get("exclude_sale_products", False),
        "usage_limit": payload.get("usage_limit", 1),
    }

    # Personal coupon: restrict to specific customer IDs
    customer_ids = payload.get("customer_ids")
    if customer_ids:
        salla_body["include_customer_ids"] = customer_ids

    # Per-user usage limit
    if payload.get("usage_limit_per_user"):
        salla_body["usage_limit_per_user"] = payload["usage_limit_per_user"]

    factory = client_factory or _default_client_factory
    try:
        client = factory(session, merchant_id)
    except SallaClientError as exc:
        logger.info("coupon fallback — cannot build SallaClient for %s: %s", merchant_id, exc)
        return CouponResult(fallback_code, None, "delivered-mock")

    try:
        response = client.post(
            "https://api.salla.dev/admin/v2/coupons",
            {k: v for k, v in salla_body.items() if v is not None},
        )
    except SallaClientError as exc:
        logger.info("coupon fallback — Salla POST failed: %s", exc)
        return CouponResult(fallback_code, None, "delivered-mock")

    body = response.body or {}
    data = body.get("data") if isinstance(body, dict) else None
    returned_code = None
    returned_id = None
    if isinstance(data, dict):
        returned_code = data.get("code")
        returned_id = data.get("id") or data.get("coupon_id")

    final_code = returned_code or fallback_code
    if returned_id:
        return CouponResult(final_code, str(returned_id), "delivered")
    logger.info("coupon fallback — Salla response missing id: %s", body)
    return CouponResult(final_code, None, "delivered-mock")

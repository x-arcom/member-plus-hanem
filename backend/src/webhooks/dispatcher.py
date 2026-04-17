"""Salla webhook event dispatcher.

Translates a verified webhook payload into a domain action. The
signature verification stays in `webhooks.receiver` / the `main.py`
route; the dispatcher assumes authenticity and focuses on business logic.

Salla webhooks generally look like:
    {"event": "app.uninstalled", "merchant": 123456, "data": {...}}
but we also accept variants that nest the store id under `data.store_id`
or `data.id`.
"""
import logging
from typing import Any, Dict, Optional

from salla.service import deactivate_merchant, find_merchant_by_salla_store

logger = logging.getLogger("webhooks.dispatcher")


class WebhookResult:
    def __init__(self, *, handled: bool, event: str, reason: Optional[str] = None, merchant_id: Optional[str] = None):
        self.handled = handled
        self.event = event
        self.reason = reason
        self.merchant_id = merchant_id

    def as_dict(self) -> Dict[str, Any]:
        return {
            "handled": self.handled,
            "event": self.event,
            "reason": self.reason,
            "merchant_id": self.merchant_id,
        }


def _extract_salla_store_id(payload: Dict) -> Optional[str]:
    for key in ("merchant", "store_id"):
        if payload.get(key):
            return str(payload[key])
    data = payload.get("data") or {}
    for key in ("store_id", "id", "merchant"):
        if data.get(key):
            return str(data[key])
    return None


def dispatch(session, payload: Dict) -> WebhookResult:
    event = str(payload.get("event") or "").strip()
    if not event:
        logger.warning("webhook without event name")
        return WebhookResult(handled=False, event="", reason="missing-event")

    salla_store_id = _extract_salla_store_id(payload)
    merchant = find_merchant_by_salla_store(session, salla_store_id) if salla_store_id else None
    merchant_id = merchant.id if merchant else None

    if event == "app.uninstalled":
        if not merchant:
            logger.info("app.uninstalled for unknown merchant %s", salla_store_id)
            return WebhookResult(handled=False, event=event, reason="merchant-not-found")
        deactivate_merchant(session, merchant.id)
        logger.info("merchant %s deactivated via webhook", merchant.id)
        return WebhookResult(handled=True, event=event, merchant_id=merchant.id)

    if event == "app.installed":
        # OAuth callback path handles install — the webhook is informational.
        logger.info("app.installed webhook received for %s", salla_store_id)
        return WebhookResult(handled=True, event=event, merchant_id=merchant_id, reason="info-only")

    # Known but not-yet-implemented events: 200-OK so Salla doesn't retry forever.
    logger.info("webhook event %s acknowledged (no handler)", event)
    return WebhookResult(handled=True, event=event, merchant_id=merchant_id, reason="no-handler")

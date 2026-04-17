"""Salla domain operations.

Small, focused service layer that sits above `salla.client.SallaClient` and
the database models. Phase 3 only implements what the webhook dispatcher
and token-refresh job need — Phase 4 will add customer-group provisioning.
"""
from datetime import datetime
from typing import Optional

from database.models import Merchant, OAuthToken


def deactivate_merchant(session, merchant_id: str) -> Optional[Merchant]:
    """Called on `app.uninstalled`. Flips the merchant to inactive and
    removes their stored OAuth tokens (we can't use them anymore)."""
    merchant = session.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        return None
    merchant.is_active = False
    merchant.deactivated_at = datetime.utcnow()
    merchant.setup_state = "uninstalled"

    session.query(OAuthToken).filter(OAuthToken.merchant_id == merchant_id).delete()
    if merchant.oauth_token_id:
        merchant.oauth_token_id = None

    session.commit()
    session.refresh(merchant)
    return merchant


def find_merchant_by_salla_store(session, salla_store_id: str) -> Optional[Merchant]:
    return session.query(Merchant).filter(Merchant.salla_store_id == str(salla_store_id)).first()


def reactivate_merchant_if_known(session, salla_store_id: str) -> Optional[Merchant]:
    """If an inactive merchant re-appears (e.g., reinstall), flip them back
    on. The OAuth callback handler still writes fresh tokens — this just
    unsets the deactivated flag."""
    merchant = find_merchant_by_salla_store(session, salla_store_id)
    if not merchant:
        return None
    merchant.is_active = True
    merchant.deactivated_at = None
    if merchant.setup_state == "uninstalled":
        merchant.setup_state = "onboarding"
    session.commit()
    session.refresh(merchant)
    return merchant

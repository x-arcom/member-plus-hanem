"""
Salla OAuth `refresh_token` exchange + persistence.

Design:
- Pure function `refresh_with_salla(refresh_token, config)` does the HTTP call.
  Returns the parsed response dict or raises `TokenRefreshError` on any failure.
- `refresh_token_for_merchant(session, merchant_id, transport=...)` looks up
  the OAuthToken row, calls the HTTP function, and persists the new
  encrypted access/refresh pair + expiry.

`transport` is a seam so tests can replace the HTTP call without monkey-
patching urllib. In production it is `_default_transport`.
"""
from datetime import datetime, timedelta
import json
import ssl
from typing import Callable, Dict, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from auth.crypto import encrypt, decrypt
from config.loader import load_config
from database.models import OAuthToken


class TokenRefreshError(RuntimeError):
    pass


Transport = Callable[[str, bytes, Dict[str, str]], Dict]


def _default_transport(url: str, body: bytes, headers: Dict[str, str]) -> Dict:
    req = Request(url, data=body, headers=headers)
    try:
        context = ssl.create_default_context()
        response = urlopen(req, context=context, timeout=10)
        return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, ValueError) as exc:
        raise TokenRefreshError(f"Salla refresh transport failed: {exc}") from exc


def refresh_with_salla(
    refresh_token: str,
    config=None,
    transport: Optional[Transport] = None,
) -> Dict:
    """Exchange a Salla refresh_token for a new access_token pair."""
    config = config or load_config()
    if not config.salla_oauth_token_url:
        raise TokenRefreshError("SALLA_OAUTH_TOKEN_URL is not configured")
    if not refresh_token:
        raise TokenRefreshError("refresh_token is empty")

    payload = urlencode({
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": config.salla_client_id,
        "client_secret": config.salla_client_secret,
    }).encode("utf-8")

    data = (transport or _default_transport)(
        config.salla_oauth_token_url,
        payload,
        {"Content-Type": "application/x-www-form-urlencoded"},
    )
    if not data.get("access_token"):
        raise TokenRefreshError("Salla refresh did not return access_token")
    return data


def refresh_token_for_merchant(
    session,
    merchant_id: str,
    transport: Optional[Transport] = None,
) -> Optional[OAuthToken]:
    """Refresh the merchant's OAuth token row. Returns the updated row, or
    None if no token record exists."""
    token = session.query(OAuthToken).filter(OAuthToken.merchant_id == merchant_id).first()
    if not token:
        return None

    plaintext_refresh = decrypt(token.refresh_token)
    if not plaintext_refresh:
        raise TokenRefreshError(f"Merchant {merchant_id} has no refresh_token")

    data = refresh_with_salla(plaintext_refresh, transport=transport)

    token.access_token = encrypt(data["access_token"])
    if data.get("refresh_token"):
        token.refresh_token = encrypt(data["refresh_token"])
    expires_in = int(data.get("expires_in", 3600))
    token.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    if data.get("scope"):
        token.scope = data["scope"]
    session.commit()
    session.refresh(token)
    return token

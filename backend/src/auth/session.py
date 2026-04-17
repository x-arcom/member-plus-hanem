"""
Merchant authentication — PRD Appendix B.

Core rule: There is NO login screen. Merchants access their dashboard by
clicking a link in an email or opening the app from inside Salla. We verify
their identity silently. They land directly in their dashboard.

Two access methods:
1. Email link: `dashboard.ourapp.com/access?token={permanent_token}`
2. From Salla: Salla passes identity, we create a session.

Session is stored as an HttpOnly + Secure + SameSite=Strict cookie with an
8-hour timeout. In dev (HTTP, not HTTPS), Secure is relaxed.

This module provides:
- `create_session(merchant_id)` → sets the cookie on a Response
- `get_current_merchant(request)` → FastAPI dependency, reads the cookie
- `clear_session(response)` → logout
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, Request, Response

SESSION_COOKIE_NAME = "mp_session"
SESSION_TTL_HOURS = 8

# In-memory session store. Production should use Redis or DB-backed sessions.
# For V1 this is acceptable per PRD §13 (single region, single process).
_sessions: dict = {}  # session_id → {merchant_id, expires_at}


def create_session(response: Response, merchant_id: str) -> str:
    """Create an 8-hour session and set the cookie on the response."""
    session_id = secrets.token_urlsafe(32)
    _sessions[session_id] = {
        "merchant_id": merchant_id,
        "expires_at": datetime.utcnow() + timedelta(hours=SESSION_TTL_HOURS),
    }
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        samesite="strict",
        max_age=SESSION_TTL_HOURS * 3600,
        # Secure=True in production; relaxed in dev for HTTP
        secure=False,  # Set to True behind HTTPS reverse proxy
        path="/",
    )
    return session_id


def get_session_merchant(request: Request) -> Optional[str]:
    """Read the session cookie and return the merchant_id, or None."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return None
    session = _sessions.get(session_id)
    if not session:
        return None
    if datetime.utcnow() > session["expires_at"]:
        del _sessions[session_id]
        return None
    return session["merchant_id"]


async def require_merchant(request: Request) -> str:
    """FastAPI dependency — returns merchant_id or raises 401.

    Checks session cookie first (PRD primary path). Falls back to
    Authorization: Bearer header for backward compatibility during
    migration and for API testing.
    """
    # Primary: session cookie (PRD Appendix B)
    merchant_id = get_session_merchant(request)
    if merchant_id:
        return merchant_id

    # Fallback: Bearer token (for API testing / migration period)
    from auth.jwt import get_token_from_request, verify_jwt_token
    token = get_token_from_request(request)
    if token:
        payload = verify_jwt_token(token)
        if payload and payload.get("merchant_id"):
            return payload["merchant_id"]

    raise HTTPException(status_code=401, detail="Authentication required")


def clear_session(response: Response, request: Request) -> None:
    """Logout — clear the session cookie."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id and session_id in _sessions:
        del _sessions[session_id]
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")

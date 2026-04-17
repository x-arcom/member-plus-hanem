"""
JWT token generation and validation for merchant authentication.
"""

from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional, Dict
from functools import wraps
from fastapi import HTTPException, Depends, Request

from config.loader import load_config


JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60 * 24  # 24 hours


def _secret() -> str:
    secret = load_config().jwt_secret
    if not secret:
        raise RuntimeError("JWT_SECRET is not configured")
    return secret


def create_jwt_token(merchant_id: str, expires_minutes: int = JWT_EXPIRATION_MINUTES) -> str:
    """
    Create JWT token for merchant.
    
    Args:
        merchant_id: Merchant UUID
        expires_minutes: Token expiration time in minutes
        
    Returns:
        JWT token string
    """
    payload = {
        "merchant_id": merchant_id,
        "exp": datetime.utcnow() + timedelta(minutes=expires_minutes),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, _secret(), algorithm=JWT_ALGORITHM)


def verify_jwt_token(token: str) -> Optional[Dict]:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload if valid, None if invalid
    """
    try:
        return jwt.decode(token, _secret(), algorithms=[JWT_ALGORITHM])
    except (JWTError, RuntimeError):
        return None


def get_token_from_request(request: Request) -> Optional[str]:
    """
    Extract JWT token from request headers.
    
    Looks for: Authorization: Bearer <token>
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return None
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    return parts[1]


async def get_current_merchant(request: Request) -> str:
    """
    FastAPI dependency to get current merchant from JWT token.
    
    Raises:
        HTTPException: If token is missing or invalid
        
    Returns:
        Merchant ID
    """
    token = get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=401, detail="Missing authorization token")
    
    payload = verify_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    merchant_id = payload.get("merchant_id")
    if not merchant_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    return merchant_id

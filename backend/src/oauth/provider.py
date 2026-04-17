"""
OAuth callback handler for Salla app installation.

In Phase 1 MVP, uses mock OAuth flow for testing.
Phase 1 full will integrate real Salla OAuth.
"""

from typing import Dict, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import ssl
import json


class MockOAuthProvider:
    """
    Mock OAuth provider for testing Phase 1 flow.
    
    In production (Phase 1 full), replace with real Salla OAuth provider.
    """
    
    @staticmethod
    def exchange_code_for_token(code: str, state: str, **kwargs) -> Optional[Dict]:
        """
        Mock OAuth code exchange.
        
        In production: POST to Salla OAuth token endpoint with code
        """
        if not code or not state:
            return None
        
        return {
            "access_token": f"mock-access-{code[:10]}",
            "refresh_token": f"mock-refresh-{code[:10]}",
            "expires_in": 3600,
            "scope": "customers orders products discounts",
            "salla_store_id": "mock-store-123",
            "store_name": "My Test Store",
            "merchant_email": "merchant@example.com",
        }
    
    @staticmethod
    def get_store_info(access_token: str, **kwargs) -> Optional[Dict]:
        """
        Mock endpoint to get Salla store information.
        
        In production: Call Salla API with access token
        """
        if not access_token:
            return None
        
        return {
            "salla_store_id": "mock-store-123",
            "store_name": "My Test Store",
            "merchant_email": "merchant@example.com",
            "merchant_phone": "+966912345678",
        }


class SallaOAuthProvider:
    """Real Salla OAuth exchange helper."""

    @staticmethod
    def exchange_code_for_token(code: str, state: str, config) -> Optional[Dict]:
        if not config.salla_oauth_token_url or not config.salla_client_id or not config.salla_client_secret:
            return MockOAuthProvider.exchange_code_for_token(code, state)

        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": config.salla_client_id,
            "client_secret": config.salla_client_secret,
            "redirect_uri": config.salla_oauth_redirect_uri,
        }
        body = urlencode(payload).encode("utf-8")
        request = Request(
            config.salla_oauth_token_url,
            data=body,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        try:
            context = ssl.create_default_context()
            response = urlopen(request, context=context)
            data = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, ValueError) as exc:
            raise ValueError(f"Salla token exchange failed: {exc}") from exc

        if not data.get("access_token"):
            raise ValueError("Salla token response did not include access_token")

        return data

    @staticmethod
    def get_store_info(access_token: str, config) -> Optional[Dict]:
        if not access_token:
            return None

        if config.salla_store_info_url:
            request = Request(
                config.salla_store_info_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
            try:
                context = ssl.create_default_context()
                response = urlopen(request, context=context)
                data = json.loads(response.read().decode("utf-8"))
                return {
                    "salla_store_id": data.get("store_id") or data.get("id"),
                    "store_name": data.get("store_name") or data.get("name"),
                    "merchant_email": data.get("email"),
                    "merchant_phone": data.get("mobile") or data.get("phone"),
                }
            except (HTTPError, URLError, ValueError):
                return MockOAuthProvider.get_store_info(access_token)

        return MockOAuthProvider.get_store_info(access_token)


async def handle_oauth_callback(code: str, state: str) -> Dict:
    """
    Handle OAuth callback from Salla.
    
    Flow:
    1. Exchange code for OAuth token
    2. Get store info from Salla
    3. Create merchant record (if new) or update (if reinstall)
    4. Persist OAuth token information
    5. Activate trial
    6. Send welcome email
    7. Return JWT token for merchant
    """
    from merchant.service import MerchantService, MerchantCreateRequest
    from auth.jwt import create_jwt_token
    from email_service.service import send_welcome_email
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database.models import Base, Merchant, OAuthToken
    from config.loader import load_config
    from datetime import datetime, timedelta

    config = load_config()

    oauth_result = SallaOAuthProvider.exchange_code_for_token(code, state, config)
    if not oauth_result:
        raise ValueError("OAuth code exchange failed")

    store_info = SallaOAuthProvider.get_store_info(oauth_result["access_token"], config)
    if not store_info or not store_info.get("salla_store_id"):
        raise ValueError("Unable to determine Salla store information")

    db_url = config.database_url
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db_session = Session()

    merchant_service = MerchantService(db_session)
    existing_merchant = merchant_service.get_merchant_by_salla_id(store_info["salla_store_id"])

    if existing_merchant:
        merchant_obj = db_session.query(Merchant).filter(Merchant.id == existing_merchant["id"]).first()
        merchant_id = existing_merchant["id"]
        if merchant_obj:
            merchant_obj.store_name = store_info.get("store_name", merchant_obj.store_name)
            merchant_obj.merchant_email = store_info.get("merchant_email", merchant_obj.merchant_email)
            merchant_obj.merchant_phone = store_info.get("merchant_phone", merchant_obj.merchant_phone)
            db_session.commit()
    else:
        request = MerchantCreateRequest(
            salla_store_id=store_info["salla_store_id"],
            store_name=store_info["store_name"],
            merchant_email=store_info["merchant_email"] or "",
            language="ar",
        )
        merchant_data = merchant_service.create_merchant(request)
        merchant_id = merchant_data["id"]
        merchant_obj = db_session.query(Merchant).filter(Merchant.id == merchant_id).first()

    from auth.crypto import encrypt

    expires_in = int(oauth_result.get("expires_in", 3600))
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    enc_access = encrypt(oauth_result["access_token"])
    enc_refresh = encrypt(oauth_result.get("refresh_token"))

    token_record = db_session.query(OAuthToken).filter(OAuthToken.merchant_id == merchant_id).first()
    if token_record:
        token_record.access_token = enc_access
        token_record.refresh_token = enc_refresh
        token_record.expires_at = expires_at
        token_record.scope = oauth_result.get("scope", token_record.scope)
    else:
        token_record = OAuthToken(
            merchant_id=merchant_id,
            access_token=enc_access,
            refresh_token=enc_refresh,
            expires_at=expires_at,
            scope=oauth_result.get("scope", ""),
        )
        db_session.add(token_record)
        db_session.commit()

    if merchant_obj:
        merchant_obj.oauth_token_id = token_record.id
        db_session.commit()

    jwt_token = create_jwt_token(merchant_id)

    try:
        await send_welcome_email(
            merchant_name=store_info.get("store_name", "Merchant"),
            merchant_email=store_info.get("merchant_email", ""),
            language="ar"
        )
    except Exception as e:
        print(f"❌ Email send failed (non-blocking): {e}")

    db_session.close()

    return {
        "status": "success",
        "message": "Merchant onboarded successfully",
        "merchant_id": merchant_id,
        "token": jwt_token,
        "dashboard_url": "http://localhost:3000/dashboard",
    }

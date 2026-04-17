import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PlatformConfig:
    # Core
    salla_api_key: str
    salla_webhook_secret: str
    database_url: str
    environment: str

    # Security
    jwt_secret: str
    encryption_key: str
    cors_origins: List[str]

    # Salla OAuth
    salla_client_id: str
    salla_client_secret: str
    salla_oauth_authorize_url: str
    salla_oauth_token_url: str
    salla_oauth_redirect_uri: str
    salla_store_info_url: str

    # Email / SMTP
    email_host: str
    email_port: Optional[int]
    email_user: str
    email_password: str
    email_from: str
    email_use_tls: bool
    email_use_ssl: bool


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    return value.lower() in ("1", "true", "yes", "on")


def _as_list(value: str, default: Optional[List[str]] = None) -> List[str]:
    if not value:
        return list(default or [])
    return [part.strip() for part in value.split(",") if part.strip()]


def load_config() -> PlatformConfig:
    return PlatformConfig(
        salla_api_key=os.getenv("SALLA_API_KEY", ""),
        salla_webhook_secret=os.getenv("SALLA_WEBHOOK_SECRET", ""),
        database_url=os.getenv("DATABASE_URL", ""),
        environment=os.getenv("ENVIRONMENT", "development"),
        jwt_secret=os.getenv("JWT_SECRET", ""),
        encryption_key=os.getenv("ENCRYPTION_KEY", ""),
        cors_origins=_as_list(
            os.getenv("CORS_ORIGINS", ""),
            default=["http://localhost:3000", "http://127.0.0.1:3000"],
        ),
        salla_client_id=os.getenv("SALLA_CLIENT_ID", ""),
        salla_client_secret=os.getenv("SALLA_CLIENT_SECRET", ""),
        salla_oauth_authorize_url=os.getenv("SALLA_OAUTH_AUTHORIZE_URL", ""),
        salla_oauth_token_url=os.getenv("SALLA_OAUTH_TOKEN_URL", ""),
        salla_oauth_redirect_uri=os.getenv("SALLA_OAUTH_REDIRECT_URI", ""),
        salla_store_info_url=os.getenv("SALLA_STORE_INFO_URL", ""),
        email_host=os.getenv("EMAIL_HOST", ""),
        email_port=int(os.getenv("EMAIL_PORT", "0")) if os.getenv("EMAIL_PORT") else None,
        email_user=os.getenv("EMAIL_USER", ""),
        email_password=os.getenv("EMAIL_PASSWORD", ""),
        email_from=os.getenv("EMAIL_FROM", ""),
        email_use_tls=_as_bool(os.getenv("EMAIL_USE_TLS", "true"), default=True),
        email_use_ssl=_as_bool(os.getenv("EMAIL_USE_SSL", "false"), default=False),
    )


def validate_config(config: PlatformConfig) -> None:
    """Fail-fast validation at startup.

    Rules:
      - Core env vars always required (api key, webhook secret, database url).
      - Security env vars (JWT_SECRET, ENCRYPTION_KEY) required in all environments
        but a deterministic dev fallback is NEVER used — starting the server
        without them is a bug. Generate them via `python -m config.gen_keys`.
      - In `production`, the dev JWT sentinel is explicitly rejected.
    """
    missing = []
    if not config.salla_api_key:
        missing.append("SALLA_API_KEY")
    if not config.salla_webhook_secret:
        missing.append("SALLA_WEBHOOK_SECRET")
    if not config.database_url:
        missing.append("DATABASE_URL")
    if not config.jwt_secret:
        missing.append("JWT_SECRET")
    if not config.encryption_key:
        missing.append("ENCRYPTION_KEY")

    if missing:
        raise RuntimeError(f"Missing required configuration: {', '.join(missing)}")

    if config.environment == "production":
        if config.jwt_secret in ("dev-secret-change-in-production", "changeme"):
            raise RuntimeError("JWT_SECRET is set to a dev placeholder in production")
        if len(config.jwt_secret) < 32:
            raise RuntimeError("JWT_SECRET must be at least 32 characters in production")

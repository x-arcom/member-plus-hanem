import importlib

import pytest


@pytest.fixture
def fresh_config(monkeypatch):
    """Reload the config module each test so env vars take effect."""
    import backend.src.config.loader as loader
    importlib.reload(loader)
    return loader


def test_load_config_reads_all_env_vars(monkeypatch, fresh_config):
    monkeypatch.setenv("SALLA_API_KEY", "k")
    monkeypatch.setenv("SALLA_WEBHOOK_SECRET", "s")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///x.db")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("SALLA_CLIENT_ID", "cid")
    monkeypatch.setenv("SALLA_CLIENT_SECRET", "csec")
    monkeypatch.setenv("EMAIL_HOST", "smtp.example.com")
    monkeypatch.setenv("EMAIL_PORT", "587")
    monkeypatch.setenv("EMAIL_USE_TLS", "true")
    monkeypatch.setenv("EMAIL_USE_SSL", "false")

    config = fresh_config.load_config()

    assert config.salla_api_key == "k"
    assert config.salla_webhook_secret == "s"
    assert config.database_url == "sqlite:///x.db"
    assert config.environment == "test"
    assert config.salla_client_id == "cid"
    assert config.salla_client_secret == "csec"
    assert config.email_host == "smtp.example.com"
    assert config.email_port == 587
    assert config.email_use_tls is True
    assert config.email_use_ssl is False


def test_load_config_uses_defaults_when_missing(monkeypatch, fresh_config):
    for var in [
        "SALLA_API_KEY", "SALLA_WEBHOOK_SECRET", "DATABASE_URL",
        "SALLA_CLIENT_ID", "SALLA_CLIENT_SECRET", "EMAIL_HOST", "EMAIL_PORT",
    ]:
        monkeypatch.delenv(var, raising=False)

    config = fresh_config.load_config()
    assert config.salla_api_key == ""
    assert config.salla_webhook_secret == ""
    assert config.database_url == ""
    assert config.environment == "development"
    assert config.email_port is None


def test_validate_config_raises_on_missing_required(fresh_config):
    config = fresh_config.PlatformConfig(
        salla_api_key="", salla_webhook_secret="", database_url="",
        environment="development",
        jwt_secret="", encryption_key="", cors_origins=[],
        salla_client_id="", salla_client_secret="",
        salla_oauth_authorize_url="", salla_oauth_token_url="",
        salla_oauth_redirect_uri="", salla_store_info_url="",
        email_host="", email_port=None, email_user="", email_password="",
        email_from="", email_use_tls=True, email_use_ssl=False,
    )

    with pytest.raises(RuntimeError) as excinfo:
        fresh_config.validate_config(config)

    message = str(excinfo.value)
    assert "SALLA_API_KEY" in message
    assert "SALLA_WEBHOOK_SECRET" in message
    assert "DATABASE_URL" in message
    assert "JWT_SECRET" in message
    assert "ENCRYPTION_KEY" in message


def test_validate_config_accepts_required_values(fresh_config):
    config = fresh_config.PlatformConfig(
        salla_api_key="k", salla_webhook_secret="s", database_url="sqlite:///x.db",
        environment="development",
        jwt_secret="a-sufficiently-long-jwt-secret-for-dev", encryption_key="any-non-empty",
        cors_origins=["http://localhost:3000"],
        salla_client_id="", salla_client_secret="",
        salla_oauth_authorize_url="", salla_oauth_token_url="",
        salla_oauth_redirect_uri="", salla_store_info_url="",
        email_host="", email_port=None, email_user="", email_password="",
        email_from="", email_use_tls=True, email_use_ssl=False,
    )

    fresh_config.validate_config(config)


def test_validate_config_rejects_dev_jwt_secret_in_production(fresh_config):
    config = fresh_config.PlatformConfig(
        salla_api_key="k", salla_webhook_secret="s", database_url="sqlite:///x.db",
        environment="production",
        jwt_secret="dev-secret-change-in-production", encryption_key="any-non-empty",
        cors_origins=[],
        salla_client_id="", salla_client_secret="",
        salla_oauth_authorize_url="", salla_oauth_token_url="",
        salla_oauth_redirect_uri="", salla_store_info_url="",
        email_host="", email_port=None, email_user="", email_password="",
        email_from="", email_use_tls=True, email_use_ssl=False,
    )
    with pytest.raises(RuntimeError, match="dev placeholder"):
        fresh_config.validate_config(config)


def test_cors_origins_parsed_from_comma_list(monkeypatch, fresh_config):
    monkeypatch.setenv("CORS_ORIGINS", "https://a.com,  https://b.com ,https://c.com")
    assert fresh_config.load_config().cors_origins == [
        "https://a.com", "https://b.com", "https://c.com",
    ]

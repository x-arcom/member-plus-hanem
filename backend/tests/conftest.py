"""Shared pytest fixtures — PRD V2 schema."""
import sys
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

BACKEND_SRC = Path(__file__).resolve().parent.parent / "src"

_SESSION_FERNET_KEY = Fernet.generate_key().decode()
_SESSION_JWT_SECRET = "test-jwt-secret-" + "x" * 32


def _set_required_env(monkeypatch, tmp_path):
    monkeypatch.setenv("SALLA_API_KEY", "test-api-key")
    monkeypatch.setenv("SALLA_WEBHOOK_SECRET", "test-webhook-secret")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/test.db")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("JWT_SECRET", _SESSION_JWT_SECRET)
    monkeypatch.setenv("ENCRYPTION_KEY", _SESSION_FERNET_KEY)
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
    monkeypatch.setenv("SCHEDULER_ENABLED", "false")


def _flush_app_modules():
    for mod in list(sys.modules):
        if mod.startswith((
            "config", "health", "webhooks", "dashboard", "auth", "oauth",
            "email_service", "merchant", "database", "scheduler", "i18n",
            "plans", "setup_wizard", "billing", "observability",
            "salla", "customers", "members", "benefits", "notifications",
        )):
            del sys.modules[mod]
        if mod in ("main", "memberplus_main"):
            del sys.modules[mod]


@pytest.fixture
def app_client(tmp_path, monkeypatch):
    """FastAPI TestClient with V2 schema and fresh DB."""
    _set_required_env(monkeypatch, tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(BACKEND_SRC))
    _flush_app_modules()

    from importlib.util import spec_from_file_location, module_from_spec
    spec_path = BACKEND_SRC / "app-entrypoint" / "main.py"
    spec = spec_from_file_location("memberplus_main", spec_path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)

    from fastapi.testclient import TestClient
    with TestClient(module.app) as client:
        yield client, module


@pytest.fixture
def src_on_path(tmp_path, monkeypatch):
    """For unit tests that import app modules directly."""
    _set_required_env(monkeypatch, tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(BACKEND_SRC))
    _flush_app_modules()
    yield

"""Integration tests for PRD V2 API — /api/v1/ endpoints."""
import hmac
import hashlib
import json


def _seed_merchant(client):
    """Seed a merchant via direct DB insert and return a JWT for testing."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from config.loader import load_config
    from auth.crypto import encrypt
    from database.models import Base, Merchant

    config = load_config()
    engine = create_engine(config.database_url)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()

    merchant = Merchant(
        id="m-test",
        salla_store_id=99999,
        access_token=encrypt("tok"),
        refresh_token=encrypt("ref"),
        store_name="Test Store",
        status="trial",
    )
    db.add(merchant)
    db.commit()
    db.close()

    from auth.jwt import create_jwt_token
    return create_jwt_token("m-test"), "m-test"


def test_health(app_client):
    client, _ = app_client
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_root_shows_api_v1(app_client):
    client, _ = app_client
    r = client.get("/")
    assert r.json()["api"] == "/api/v1/"


def test_overview_requires_auth(app_client):
    client, _ = app_client
    assert client.get("/api/v1/merchant/overview").status_code == 401


def test_overview_with_auth(app_client):
    client, _ = app_client
    token, _ = _seed_merchant(client)
    r = client.get(
        "/api/v1/merchant/overview",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["store_name"] == "Test Store"
    assert body["status"] == "trial"
    assert body["member_count"] == 0


def test_plans_empty_before_setup(app_client):
    client, _ = app_client
    token, _ = _seed_merchant(client)
    r = client.get(
        "/api/v1/merchant/plans",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["plans"] == []


def test_setup_complete_creates_plans(app_client):
    client, _ = app_client
    token, _ = _seed_merchant(client)

    r = client.post(
        "/api/v1/merchant/setup/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "silver": {
                "display_name_ar": "الفضية",
                "display_name_en": "Silver",
                "price": 49,
                "discount_pct": 10,
                "free_shipping_uses": 2,
            },
            "gold": {
                "display_name_ar": "الذهبية",
                "display_name_en": "Gold",
                "price": 99,
                "discount_pct": 15,
                "free_shipping_uses": 4,
            },
            "consent_terms": True,
            "consent_cancel": True,
        },
    )
    assert r.status_code == 200
    assert r.json()["setup_completed"] is True

    # Verify plans created
    plans = client.get(
        "/api/v1/merchant/plans",
        headers={"Authorization": f"Bearer {token}"},
    ).json()["plans"]
    assert len(plans) == 2
    tiers = {p["tier"] for p in plans}
    assert tiers == {"silver", "gold"}


def test_setup_rejects_without_consent(app_client):
    client, _ = app_client
    token, _ = _seed_merchant(client)
    r = client.post(
        "/api/v1/merchant/setup/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "silver": {"display_name_ar": "ف", "display_name_en": "S", "price": 49, "discount_pct": 10},
            "gold": {"display_name_ar": "ذ", "display_name_en": "G", "price": 99, "discount_pct": 15},
            "consent_terms": False,
            "consent_cancel": True,
        },
    )
    assert r.status_code == 400


def test_setup_rejects_gold_not_exceeding_silver(app_client):
    client, _ = app_client
    token, _ = _seed_merchant(client)
    r = client.post(
        "/api/v1/merchant/setup/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "silver": {"display_name_ar": "ف", "display_name_en": "S", "price": 49, "discount_pct": 15},
            "gold": {"display_name_ar": "ذ", "display_name_en": "G", "price": 99, "discount_pct": 10},
            "consent_terms": True,
            "consent_cancel": True,
        },
    )
    assert r.status_code == 400
    assert "Gold discount must exceed Silver" in r.json()["detail"]


def test_public_plans_coming_soon_before_setup(app_client):
    client, _ = app_client
    _seed_merchant(client)
    r = client.get("/api/v1/store/99999/plans")
    assert r.status_code == 200
    assert r.json()["coming_soon"] is True
    assert r.json()["plans"] == []


def test_public_plans_available_after_setup(app_client):
    client, _ = app_client
    token, _ = _seed_merchant(client)
    client.post(
        "/api/v1/merchant/setup/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "silver": {"display_name_ar": "ف", "display_name_en": "Silver", "price": 49, "discount_pct": 10, "free_shipping_uses": 2},
            "gold": {"display_name_ar": "ذ", "display_name_en": "Gold", "price": 99, "discount_pct": 15, "free_shipping_uses": 4},
            "consent_terms": True, "consent_cancel": True,
        },
    )
    r = client.get("/api/v1/store/99999/plans")
    assert r.json()["coming_soon"] is False
    assert len(r.json()["plans"]) == 2


def test_webhook_idempotency_via_api(app_client):
    client, _ = app_client
    _seed_merchant(client)

    payload = json.dumps({
        "event": "customer.updated",
        "merchant": "99999",
        "event_id": "evt-api-1",
    }).encode()
    sig = hmac.new(b"test-webhook-secret", payload, hashlib.sha256).hexdigest()

    r1 = client.post("/webhooks/salla", content=payload,
                      headers={"X-Salla-Signature": sig, "Content-Type": "application/json"})
    r2 = client.post("/webhooks/salla", content=payload,
                      headers={"X-Salla-Signature": sig, "Content-Type": "application/json"})

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r2.json()["reason"] == "already-processed"

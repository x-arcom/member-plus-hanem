"""Integration tests for PRD §16 webhook handlers — fully wired."""
import hmac
import hashlib
import json
from datetime import datetime, timedelta
from decimal import Decimal


def _sign(payload: bytes) -> str:
    return hmac.new(b"test-webhook-secret", payload, hashlib.sha256).hexdigest()


def _send(client, payload_dict):
    body = json.dumps(payload_dict).encode()
    return client.post(
        "/webhooks/salla",
        content=body,
        headers={"X-Salla-Signature": _sign(body), "Content-Type": "application/json"},
    )


def _seed_merchant(client):
    """Seed a merchant via app.store.authorize webhook."""
    r = _send(client, {
        "event": "app.store.authorize",
        "event_id": "auth-001",
        "data": {
            "store_id": 55555,
            "store_name": "Webhook Test Store",
            "access_token": "salla-access-tok",
            "refresh_token": "salla-refresh-tok",
        }
    })
    assert r.status_code == 200
    return r.json().get("merchant_id")


def _activate_merchant(client):
    _send(client, {
        "event": "app.subscription.started",
        "event_id": "sub-start-001",
        "merchant": "55555",
        "data": {"plan": "pro"},
    })


def _setup_plans(client, merchant_id):
    """Complete wizard via API to create Silver + Gold plans."""
    from auth.jwt import create_jwt_token
    token = create_jwt_token(merchant_id)
    client.post(
        "/api/v1/merchant/setup/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "silver": {"display_name_ar": "ف", "display_name_en": "Silver",
                       "price": 49, "discount_pct": 10, "free_shipping_uses": 2},
            "gold": {"display_name_ar": "ذ", "display_name_en": "Gold",
                     "price": 99, "discount_pct": 15, "free_shipping_uses": 4},
            "consent_terms": True, "consent_cancel": True,
        },
    )


# ---- Tests ----

def test_app_authorize_creates_merchant(app_client):
    client, _ = app_client
    merchant_id = _seed_merchant(client)
    assert merchant_id is not None

    from auth.jwt import create_jwt_token
    token = create_jwt_token(merchant_id)
    overview = client.get(
        "/api/v1/merchant/overview",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    assert overview["store_name"] == "Webhook Test Store"
    assert overview["status"] == "trial"


def test_app_subscription_started_activates(app_client):
    client, _ = app_client
    merchant_id = _seed_merchant(client)
    _activate_merchant(client)

    from auth.jwt import create_jwt_token
    token = create_jwt_token(merchant_id)
    overview = client.get(
        "/api/v1/merchant/overview",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    assert overview["status"] == "active"


def test_subscription_created_creates_member_with_benefits(app_client):
    client, _ = app_client
    merchant_id = _seed_merchant(client)
    _activate_merchant(client)
    _setup_plans(client, merchant_id)

    r = _send(client, {
        "event": "subscription.created",
        "event_id": "sub-001",
        "merchant": "55555",
        "data": {
            "id": "salla-sub-abc",
            "customer_id": 9001,
            "product_name": "Gold Membership",
            "price": 99,
        },
    })
    assert r.status_code == 200
    body = r.json()
    assert body["action"] == "member-created"
    assert body["tier"] == "gold"
    assert "free_shipping" in body.get("benefits", [])
    assert "monthly_gift" in body.get("benefits", [])


def test_charge_failed_starts_grace_period(app_client):
    client, _ = app_client
    merchant_id = _seed_merchant(client)
    _activate_merchant(client)
    _setup_plans(client, merchant_id)

    # Create member first
    _send(client, {
        "event": "subscription.created",
        "event_id": "sub-002",
        "merchant": "55555",
        "data": {"id": "sub-grace-test", "customer_id": 9002, "product_name": "Silver", "price": 49},
    })

    # Charge fails
    r = _send(client, {
        "event": "subscription.charge.failed",
        "event_id": "fail-001",
        "data": {"subscription_id": "sub-grace-test"},
    })
    assert r.status_code == 200
    assert r.json()["action"] == "grace-started"

    # Verify scheduled job was created
    from config.loader import load_config
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database.models import ScheduledJob, Base

    engine = create_engine(load_config().database_url)
    db = sessionmaker(bind=engine)()
    try:
        jobs = db.query(ScheduledJob).filter(
            ScheduledJob.job_type == "grace_period_expiry"
        ).all()
        assert len(jobs) >= 1
    finally:
        db.close()


def test_charge_succeeded_resets_grace(app_client):
    client, _ = app_client
    merchant_id = _seed_merchant(client)
    _activate_merchant(client)
    _setup_plans(client, merchant_id)

    _send(client, {
        "event": "subscription.created",
        "event_id": "sub-003",
        "merchant": "55555",
        "data": {"id": "sub-recover", "customer_id": 9003, "product_name": "Gold", "price": 99},
    })

    # Fail → grace
    _send(client, {
        "event": "subscription.charge.failed",
        "event_id": "fail-002",
        "data": {"subscription_id": "sub-recover"},
    })

    # Succeed → back to active
    r = _send(client, {
        "event": "subscription.charge.succeeded",
        "event_id": "success-001",
        "data": {"subscription_id": "sub-recover"},
    })
    assert r.status_code == 200
    assert r.json()["action"] == "renewal-processed"


def test_subscription_cancelled_schedules_removal(app_client):
    client, _ = app_client
    merchant_id = _seed_merchant(client)
    _activate_merchant(client)
    _setup_plans(client, merchant_id)

    _send(client, {
        "event": "subscription.created",
        "event_id": "sub-004",
        "merchant": "55555",
        "data": {"id": "sub-cancel-test", "customer_id": 9004, "product_name": "Silver", "price": 49},
    })

    r = _send(client, {
        "event": "subscription.cancelled",
        "event_id": "cancel-001",
        "data": {"subscription_id": "sub-cancel-test"},
    })
    assert r.status_code == 200
    assert r.json()["action"] == "cancellation-recorded"

    from config.loader import load_config
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database.models import ScheduledJob

    engine = create_engine(load_config().database_url)
    db = sessionmaker(bind=engine)()
    try:
        jobs = db.query(ScheduledJob).filter(
            ScheduledJob.job_type == "remove_from_group"
        ).all()
        assert len(jobs) >= 1
    finally:
        db.close()


def test_app_subscription_ended_offboards_all_members(app_client):
    client, _ = app_client
    merchant_id = _seed_merchant(client)
    _activate_merchant(client)
    _setup_plans(client, merchant_id)

    # Create 2 members
    _send(client, {
        "event": "subscription.created", "event_id": "sub-off-1",
        "merchant": "55555",
        "data": {"id": "sub-off-a", "customer_id": 8001, "product_name": "Gold", "price": 99},
    })
    _send(client, {
        "event": "subscription.created", "event_id": "sub-off-2",
        "merchant": "55555",
        "data": {"id": "sub-off-b", "customer_id": 8002, "product_name": "Silver", "price": 49},
    })

    # Merchant cancels our app
    r = _send(client, {
        "event": "app.subscription.canceled",
        "event_id": "app-cancel-001",
        "merchant": "55555",
    })
    assert r.status_code == 200
    assert r.json()["action"] == "merchant-offboarded"
    assert r.json()["members_expired"] == 2

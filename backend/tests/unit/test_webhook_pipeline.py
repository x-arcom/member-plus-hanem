"""Unit tests for the PRD-compliant webhook pipeline with idempotency."""
import hmac
import hashlib
import json
import pytest


@pytest.fixture
def db(src_on_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database.models import Base, Merchant
    from auth.crypto import encrypt

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine)()
    s.add(Merchant(
        id="m1", salla_store_id=12345,
        access_token=encrypt("tok"), refresh_token=encrypt("ref"),
        store_name="Test Store",
    ))
    s.commit()
    yield s
    s.close()


def _sign(payload: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def test_rejects_missing_signature(db):
    from webhooks.pipeline import receive_and_store
    status, body = receive_and_store(db, b'{}', None, "secret")
    assert status == 400
    assert body["reason"] == "missing-signature"


def test_rejects_invalid_signature(db):
    from webhooks.pipeline import receive_and_store
    status, body = receive_and_store(db, b'{}', "bad", "secret")
    assert status == 400
    assert body["reason"] == "invalid-signature"


def test_stores_and_processes_valid_event(db):
    from webhooks.pipeline import receive_and_store
    from database.models import WebhookEvent

    payload = json.dumps({"event": "app.uninstalled", "merchant": "12345", "event_id": "evt-1"}).encode()
    sig = _sign(payload, "secret")

    status, body = receive_and_store(db, payload, sig, "secret")
    assert status == 200
    assert body["status"] == "ok"

    stored = db.query(WebhookEvent).filter(WebhookEvent.salla_event_id == "evt-1").first()
    assert stored is not None
    assert stored.status == "processed"
    assert stored.event_type == "app.uninstalled"


def test_idempotency_skips_duplicate(db):
    from webhooks.pipeline import receive_and_store

    payload = json.dumps({"event": "customer.updated", "event_id": "evt-dup"}).encode()
    sig = _sign(payload, "secret")

    s1, b1 = receive_and_store(db, payload, sig, "secret")
    s2, b2 = receive_and_store(db, payload, sig, "secret")

    assert s1 == 200
    assert s2 == 200
    assert b2["reason"] == "already-processed"


def test_unknown_event_acknowledged(db):
    from webhooks.pipeline import receive_and_store

    payload = json.dumps({"event": "some.future.event", "event_id": "evt-unk"}).encode()
    sig = _sign(payload, "secret")

    status, body = receive_and_store(db, payload, sig, "secret")
    assert status == 200
    assert body["handled"] is False
    assert body["reason"] == "no-handler"


def test_merchant_resolved_from_payload(db):
    from webhooks.pipeline import receive_and_store
    from database.models import WebhookEvent

    payload = json.dumps({"event": "order.created", "merchant": "12345", "event_id": "evt-m"}).encode()
    sig = _sign(payload, "secret")

    receive_and_store(db, payload, sig, "secret")

    stored = db.query(WebhookEvent).filter(WebhookEvent.salla_event_id == "evt-m").first()
    assert stored.merchant_id == "m1"

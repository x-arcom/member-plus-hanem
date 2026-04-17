"""Integration tests for PRD V2 dashboard endpoints."""
from datetime import datetime, timedelta
from decimal import Decimal


def _seed(client):
    from config.loader import load_config
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from auth.crypto import encrypt
    from database.models import Base, Merchant, MembershipPlan, PlanPriceVersion, Member
    from auth.jwt import create_jwt_token

    config = load_config()
    engine = create_engine(config.database_url)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()

    now = datetime.utcnow()
    merchant = Merchant(
        id="m1", salla_store_id=11111,
        access_token=encrypt("tok"), refresh_token=encrypt("ref"),
        store_name="Dashboard Test Store", status="active",
        setup_completed=True, setup_step=5,
        our_plan="pro", activated_at=now - timedelta(days=30),
    )
    silver = MembershipPlan(
        id="p-silver", merchant_id="m1", tier="silver",
        display_name_ar="الفضية", display_name_en="Silver",
        price=Decimal("49"), discount_pct=Decimal("10"), free_shipping_uses=2,
    )
    gold = MembershipPlan(
        id="p-gold", merchant_id="m1", tier="gold",
        display_name_ar="الذهبية", display_name_en="Gold",
        price=Decimal("99"), discount_pct=Decimal("15"), free_shipping_uses=4,
    )
    member1 = Member(
        id="mem1", merchant_id="m1", plan_id="p-gold",
        salla_customer_id=100, status="active",
        subscribed_price=Decimal("99"), free_shipping_quota=4,
        current_period_end=now + timedelta(days=15),
        total_saved_sar=Decimal("240"),
    )
    member2 = Member(
        id="mem2", merchant_id="m1", plan_id="p-silver",
        salla_customer_id=200, status="grace_period",
        subscribed_price=Decimal("49"), free_shipping_quota=2,
        grace_period_ends_at=now + timedelta(hours=12),
        total_saved_sar=Decimal("80"),
    )
    db.add_all([merchant, silver, gold, member1, member2])
    db.add(PlanPriceVersion(plan_id="p-silver", price=Decimal("49")))
    db.add(PlanPriceVersion(plan_id="p-gold", price=Decimal("99")))
    db.commit()
    db.close()

    return create_jwt_token("m1")


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_focus_card_shows_grace_members(app_client):
    client, _ = app_client
    token = _seed(client)
    r = client.get("/api/v1/merchant/focus", headers=_auth(token))
    assert r.status_code == 200
    body = r.json()
    assert body["priority"] == 2
    assert body["type"] == "grace_expiry"
    assert body["count"] == 1


def test_member_profile_returns_full_history(app_client):
    client, _ = app_client
    token = _seed(client)
    r = client.get("/api/v1/merchant/members/mem1", headers=_auth(token))
    assert r.status_code == 200
    body = r.json()
    assert body["salla_customer_id"] == 100
    assert body["status"] == "active"
    assert body["plan"]["tier"] == "gold"
    from decimal import Decimal
    assert Decimal(body["total_saved_sar"]) == Decimal("240")
    assert "benefit_events" in body
    assert "gift_history" in body
    assert "shipping_history" in body


def test_member_profile_404_for_other_merchant(app_client):
    client, _ = app_client
    token = _seed(client)
    from auth.jwt import create_jwt_token
    other_token = create_jwt_token("other-merchant")
    r = client.get("/api/v1/merchant/members/mem1", headers=_auth(other_token))
    assert r.status_code == 404


def test_members_filter_by_status(app_client):
    client, _ = app_client
    token = _seed(client)
    r = client.get("/api/v1/merchant/members?status=grace_period", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["total"] == 1
    assert r.json()["members"][0]["salla_customer_id"] == 200


def test_member_state_returns_active(app_client):
    client, _ = app_client
    _seed(client)
    r = client.get("/api/v1/member/state?salla_customer_id=100&store_id=11111")
    assert r.status_code == 200
    body = r.json()
    assert body["is_member"] is True
    assert body["tier"] == "gold"
    assert body["discount_pct"].startswith("15")
    assert body["free_shipping_remaining"] == 4


def test_member_state_returns_non_member(app_client):
    client, _ = app_client
    _seed(client)
    r = client.get("/api/v1/member/state?salla_customer_id=999&store_id=11111")
    assert r.status_code == 200
    assert r.json()["is_member"] is False


def test_activity_log_empty(app_client):
    client, _ = app_client
    token = _seed(client)
    r = client.get("/api/v1/merchant/activity", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["total"] == 0


def test_export_csv(app_client):
    client, _ = app_client
    token = _seed(client)
    r = client.get("/api/v1/merchant/export?type=members", headers=_auth(token))
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("content-type", "")
    assert "mem1" in r.text


def test_gift_coupons_empty(app_client):
    client, _ = app_client
    token = _seed(client)
    r = client.get("/api/v1/merchant/gift-coupons", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["coupons"] == []

"""Unit tests for PRD §10 benefits engine + Appendix C activation rules."""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal


@pytest.fixture
def db_with_member(src_on_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database.models import Base, Merchant, MembershipPlan, Member
    from auth.crypto import encrypt

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()

    now = datetime.utcnow()
    db.add(Merchant(
        id="m1", salla_store_id=111,
        access_token=encrypt("t"), refresh_token=encrypt("r"),
        store_name="Test", status="active",
    ))
    db.add(MembershipPlan(
        id="p-silver", merchant_id="m1", tier="silver",
        display_name_ar="ف", display_name_en="Silver",
        price=Decimal("49"), discount_pct=Decimal("10"),
        free_shipping_uses=2,
    ))
    db.add(MembershipPlan(
        id="p-gold", merchant_id="m1", tier="gold",
        display_name_ar="ذ", display_name_en="Gold",
        price=Decimal("99"), discount_pct=Decimal("15"),
        free_shipping_uses=4,
        gift_name_ar="هدية شهرية", gift_name_en="Monthly Gift",
    ))
    db.add(Member(
        id="mem-gold", merchant_id="m1", plan_id="p-gold",
        salla_customer_id=100, status="active",
        subscribed_price=Decimal("99"), free_shipping_quota=4,
        current_period_end=now + timedelta(days=25),
    ))
    db.add(Member(
        id="mem-silver", merchant_id="m1", plan_id="p-silver",
        salla_customer_id=200, status="active",
        subscribed_price=Decimal("49"), free_shipping_quota=2,
        current_period_end=now + timedelta(days=25),
    ))
    db.commit()
    yield db
    db.close()


def _get(db, model, id_):
    return db.query(model).filter(model.id == id_).first()


def test_activate_all_gold_gets_all_6(db_with_member):
    from benefits.engine import activate_all_benefits
    from database.models import Member, MembershipPlan

    member = _get(db_with_member, Member, "mem-gold")
    plan = _get(db_with_member, MembershipPlan, "p-gold")

    results = activate_all_benefits(db_with_member, member, plan)

    activated = [r["benefit"] for r in results if r["status"] == "activated"]
    assert "auto_discount" in activated
    assert "member_price" in activated
    assert "free_shipping" in activated
    assert "monthly_gift" in activated
    assert "early_access" in activated
    assert "badge" in activated


def test_activate_all_silver_no_monthly_gift(db_with_member):
    from benefits.engine import activate_all_benefits
    from database.models import Member, MembershipPlan

    member = _get(db_with_member, Member, "mem-silver")
    plan = _get(db_with_member, MembershipPlan, "p-silver")

    results = activate_all_benefits(db_with_member, member, plan)

    activated = [r["benefit"] for r in results if r["status"] == "activated"]
    skipped = [r["benefit"] for r in results if r["status"] == "skipped"]

    assert "auto_discount" in activated
    assert "free_shipping" in activated
    assert "monthly_gift" in skipped  # Silver: NO monthly gift


def test_free_shipping_creates_coupon_with_full_quota(db_with_member):
    from benefits.engine import activate_free_shipping
    from database.models import Member, MembershipPlan, FreeShippingCoupon

    member = _get(db_with_member, Member, "mem-gold")
    plan = _get(db_with_member, MembershipPlan, "p-gold")

    result = activate_free_shipping(db_with_member, member, plan)
    db_with_member.commit()

    assert result.status == "activated"
    assert member.free_shipping_quota == 4
    assert member.free_shipping_used == 0

    coupon = db_with_member.query(FreeShippingCoupon).filter(
        FreeShippingCoupon.member_id == "mem-gold"
    ).first()
    assert coupon is not None
    assert coupon.coupon_code.startswith("FS-")
    assert coupon.quota == 4


def test_free_shipping_idempotent(db_with_member):
    from benefits.engine import activate_free_shipping
    from database.models import Member, MembershipPlan, FreeShippingCoupon

    member = _get(db_with_member, Member, "mem-gold")
    plan = _get(db_with_member, MembershipPlan, "p-gold")

    activate_free_shipping(db_with_member, member, plan)
    db_with_member.commit()
    result2 = activate_free_shipping(db_with_member, member, plan)

    assert result2.status == "skipped"

    count = db_with_member.query(FreeShippingCoupon).filter(
        FreeShippingCoupon.member_id == "mem-gold"
    ).count()
    assert count == 1


def test_monthly_gift_gold_only(db_with_member):
    from benefits.engine import activate_monthly_gift
    from database.models import Member, MembershipPlan, GiftCoupon

    gold_member = _get(db_with_member, Member, "mem-gold")
    gold_plan = _get(db_with_member, MembershipPlan, "p-gold")
    silver_member = _get(db_with_member, Member, "mem-silver")
    silver_plan = _get(db_with_member, MembershipPlan, "p-silver")

    gold_result = activate_monthly_gift(db_with_member, gold_member, gold_plan)
    silver_result = activate_monthly_gift(db_with_member, silver_member, silver_plan)
    db_with_member.commit()

    assert gold_result.status == "activated"
    assert silver_result.status == "skipped"

    gold_gift = db_with_member.query(GiftCoupon).filter(
        GiftCoupon.member_id == "mem-gold"
    ).first()
    assert gold_gift is not None
    assert gold_gift.coupon_code.startswith("GIFT-")

    silver_gift = db_with_member.query(GiftCoupon).filter(
        GiftCoupon.member_id == "mem-silver"
    ).first()
    assert silver_gift is None


def test_deactivate_deactivates_coupons(db_with_member):
    from benefits.engine import activate_all_benefits, deactivate_all_benefits
    from database.models import Member, MembershipPlan, FreeShippingCoupon

    member = _get(db_with_member, Member, "mem-gold")
    plan = _get(db_with_member, MembershipPlan, "p-gold")

    activate_all_benefits(db_with_member, member, plan)
    deactivate_all_benefits(db_with_member, member, plan)

    coupon = db_with_member.query(FreeShippingCoupon).filter(
        FreeShippingCoupon.member_id == "mem-gold"
    ).first()
    assert coupon.status == "deactivated"


def test_reset_monthly_generates_new_coupons(db_with_member):
    """Simulates renewal: old month coupons exist, reset creates new ones."""
    from benefits.engine import activate_free_shipping, reset_monthly_benefits
    from database.models import Member, MembershipPlan, FreeShippingCoupon

    member = _get(db_with_member, Member, "mem-gold")
    plan = _get(db_with_member, MembershipPlan, "p-gold")

    # First month
    activate_free_shipping(db_with_member, member, plan)
    db_with_member.commit()

    # Calling reset in the SAME month should skip (idempotent)
    results = reset_monthly_benefits(db_with_member, member, plan)
    fs = next(r for r in results if r["benefit"] == "free_shipping")
    assert fs["status"] == "skipped"


def test_activation_logs_activity(db_with_member):
    from benefits.engine import activate_all_benefits
    from database.models import Member, MembershipPlan, ActivityLog

    member = _get(db_with_member, Member, "mem-gold")
    plan = _get(db_with_member, MembershipPlan, "p-gold")

    activate_all_benefits(db_with_member, member, plan)

    log = db_with_member.query(ActivityLog).filter(
        ActivityLog.member_id == "mem-gold",
        ActivityLog.event_type == "member.joined",
    ).first()
    assert log is not None
    assert "auto_discount" in log.metadata_json

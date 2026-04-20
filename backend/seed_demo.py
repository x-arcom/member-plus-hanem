"""Seed realistic mock data for the demo merchant (salla_store_id=99999).

Run after `/api/v1/auth/demo` has created the merchant. Idempotent: wipes
existing children and re-seeds. Marks merchant as setup_completed so
the demo viewer lands on a populated dashboard instead of the wizard.
"""
import os
import sys
import random
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.loader import load_config
from database.models import (
    Base, Merchant, MembershipPlan, PlanPriceVersion, Member,
    GiftCoupon, FreeShippingCoupon, BenefitEvent, ActivityLog, EmailLog,
)

DEMO_STORE_ID = 99999

ARABIC_NAMES = [
    "نورة الشمري", "ريم المطيري", "سارة الغامدي", "هند القحطاني", "لينا العتيبي",
    "منى الدوسري", "أمل الزهراني", "روان الحربي", "دانة السبيعي", "مها الرشيد",
    "فاطمة العنزي", "جواهر الفهد", "بدور السديري", "العنود الراجحي", "شهد الخالدي",
    "أحمد الغامدي", "خالد العتيبي", "محمد الشهري", "عبدالله القحطاني", "فهد الدوسري",
    "سلطان المطيري", "يوسف الزهراني", "بدر الحربي",
]

GIFT_DESCRIPTIONS = [
    ("خصم 25% على جميع المنتجات", "25% off all products"),
    ("هدية مجانية مع طلبك", "Free gift with order"),
    ("خصم 30% على فئة العطور", "30% off perfumes"),
    ("منتج مجاني عند الشراء بـ 200 ريال", "Free product on 200 SAR purchase"),
]


def main():
    cfg = load_config()
    engine = create_engine(cfg.database_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        merchant = db.query(Merchant).filter(Merchant.salla_store_id == DEMO_STORE_ID).first()
        if not merchant:
            print("Demo merchant not found. POST /api/v1/auth/demo first.")
            return

        mid = merchant.id
        print(f"Seeding merchant {mid} ({merchant.store_name})")

        # Wipe existing children
        for model in (BenefitEvent, ActivityLog, GiftCoupon, FreeShippingCoupon, EmailLog, Member):
            db.query(model).filter(model.merchant_id == mid).delete(synchronize_session=False)
        plan_ids = [p.id for p in db.query(MembershipPlan).filter(MembershipPlan.merchant_id == mid).all()]
        if plan_ids:
            db.query(PlanPriceVersion).filter(PlanPriceVersion.plan_id.in_(plan_ids)).delete(synchronize_session=False)
            db.query(MembershipPlan).filter(MembershipPlan.merchant_id == mid).delete(synchronize_session=False)
        db.flush()

        # --- Plans ---
        silver = MembershipPlan(
            merchant_id=mid, tier="silver", status="active",
            display_name_ar="الفضية", display_name_en="Silver",
            price=Decimal("49.00"), discount_pct=Decimal("10.00"),
            free_shipping_uses=2,
            gift_name_ar="هدية شهرية", gift_name_en="Monthly Gift",
        )
        gold = MembershipPlan(
            merchant_id=mid, tier="gold", status="active",
            display_name_ar="الذهبية", display_name_en="Gold",
            price=Decimal("99.00"), discount_pct=Decimal("20.00"),
            free_shipping_uses=5,
            gift_name_ar="هدية شهرية مميزة", gift_name_en="Premium Monthly Gift",
        )
        db.add_all([silver, gold])
        db.flush()
        db.add(PlanPriceVersion(plan_id=silver.id, price=silver.price))
        db.add(PlanPriceVersion(plan_id=gold.id, price=gold.price))
        db.flush()

        # --- Members ---
        now = datetime.utcnow()
        members = []
        for i, name in enumerate(ARABIC_NAMES):
            # Distribution: 60% gold, 35% silver, 5% mix (irrelevant for plan choice)
            tier = "gold" if random.random() < 0.55 else "silver"
            plan = gold if tier == "gold" else silver
            joined_days_ago = random.randint(5, 240)
            joined = now - timedelta(days=joined_days_ago)

            # Status distribution
            roll = random.random()
            if i < 15:
                status = "active"
            elif roll < 0.5:
                status = "grace_period"
            elif roll < 0.8:
                status = "cancelled"
            else:
                status = "expired"

            period_end = joined + timedelta(days=30 * ((joined_days_ago // 30) + 1))
            cancelled_at = None
            grace_end = None
            if status == "cancelled":
                cancelled_at = now - timedelta(days=random.randint(1, 60))
                period_end = cancelled_at + timedelta(days=15)
            if status == "expired":
                cancelled_at = now - timedelta(days=random.randint(60, 180))
                period_end = cancelled_at - timedelta(days=10)
            if status == "grace_period":
                grace_end = now + timedelta(days=random.randint(1, 3))
                period_end = now - timedelta(days=random.randint(1, 5))

            total_saved = Decimal(str(round(random.uniform(20, 800), 2)))
            free_used = random.randint(0, plan.free_shipping_uses)

            m = Member(
                merchant_id=mid,
                plan_id=plan.id,
                salla_customer_id=10_000_000 + i,
                status=status,
                subscribed_price=plan.price,
                current_period_end=period_end,
                grace_period_ends_at=grace_end,
                next_renewal_at=period_end if status == "active" else None,
                is_at_risk=(status == "grace_period") or (status == "active" and random.random() < 0.15),
                total_saved_sar=total_saved,
                free_shipping_used=free_used,
                free_shipping_quota=plan.free_shipping_uses,
                last_order_at=now - timedelta(days=random.randint(0, 30)) if status in ("active", "grace_period") else None,
                cancelled_at=cancelled_at,
                created_at=joined,
            )
            db.add(m)
            members.append(m)
        db.flush()

        active_members = [m for m in members if m.status == "active"]

        # --- Monthly gifts: GOLD TIER ONLY (per product spec) ---
        # 6 months back + current + next 2 months
        # offset 0 = current month (active), >0 = scheduled, <0 = expired
        gold_recipients = [
            m for m in members
            if m.plan_id == gold.id and m.status in ("active", "grace_period", "cancelled")
        ]
        for offset in (-6, -5, -4, -3, -2, -1, 0, 1, 2):
            target = (now.replace(day=15) + timedelta(days=30 * offset))
            month_str = target.strftime("%Y-%m")
            ar, en = GIFT_DESCRIPTIONS[abs(offset) % len(GIFT_DESCRIPTIONS)]
            eligible = [m for m in gold_recipients if m.created_at <= target]
            for m in eligible:
                plan = gold
                if offset > 0:
                    status = "pending"
                    code = None
                elif offset == 0:
                    # Current month: codes generated, ~30% used so far
                    status = "used" if random.random() < 0.3 else "generated"
                    code = f"GIFT-{month_str.replace('-', '')}-{m.id[:6].upper()}"
                else:
                    # Past: most used, few expired, few generated-but-unused
                    roll = random.random()
                    if roll < 0.65:
                        status = "used"
                    elif roll < 0.85:
                        status = "expired"
                    else:
                        status = "generated"
                    code = f"GIFT-{month_str.replace('-', '')}-{m.id[:6].upper()}"
                db.add(GiftCoupon(
                    member_id=m.id, merchant_id=mid, plan_id=plan.id,
                    month=month_str, coupon_code=code,
                    gift_type=random.choice(["pct_all", "pct_category", "fixed", "free_product"]),
                    gift_description_ar=ar, gift_description_en=en,
                    status=status,
                    expires_at=target + timedelta(days=30),
                    created_at=target - timedelta(days=2),
                ))

        # --- Free shipping coupons (current month) ---
        current_month = now.strftime("%Y-%m")
        for m in active_members:
            db.add(FreeShippingCoupon(
                member_id=m.id, merchant_id=mid,
                month=current_month,
                coupon_code=f"SHIP-{m.id[:8].upper()}",
                quota=m.free_shipping_quota,
                used_count=m.free_shipping_used,
                status="exhausted" if m.free_shipping_used >= m.free_shipping_quota else "active",
                expires_at=now.replace(day=28) + timedelta(days=5),
            ))

        # --- Benefit events (savings history) ---
        for m in members:
            count = random.randint(2, 12) if m.status == "active" else random.randint(0, 4)
            for _ in range(count):
                ago = random.randint(0, 180)
                event_type = random.choice([
                    "discount_applied", "shipping_coupon_used",
                    "gift_coupon_used", "member_price_applied",
                ])
                amount = Decimal(str(round(random.uniform(5, 80), 2)))
                db.add(BenefitEvent(
                    member_id=m.id, merchant_id=mid,
                    salla_order_id=900_000 + random.randint(0, 99999),
                    event_type=event_type,
                    amount_saved=amount,
                    created_at=now - timedelta(days=ago),
                ))

        # --- Activity log ---
        events = []
        for m in members:
            events.append(("member.joined", m.id, m.created_at))
            if m.cancelled_at:
                events.append(("member.cancelled", m.id, m.cancelled_at))
        for _ in range(40):
            m = random.choice(members)
            events.append((
                random.choice(["benefit.discount_applied", "benefit.shipping_used", "benefit.gift_used"]),
                m.id,
                now - timedelta(days=random.randint(0, 60), hours=random.randint(0, 23)),
            ))
        events.sort(key=lambda e: e[2], reverse=True)
        for ev_type, member_id, when in events[:120]:
            db.add(ActivityLog(
                merchant_id=mid, event_type=ev_type, member_id=member_id, created_at=when,
            ))

        # --- Mark merchant as set up & on Pro plan ---
        merchant.setup_completed = True
        merchant.setup_step = 5
        merchant.our_plan = "pro"
        merchant.activated_at = now - timedelta(days=45)
        merchant.status = "active"
        merchant.trial_ends_at = None

        db.commit()

        # Summary
        print(f"  plans:        2 (silver/gold)")
        print(f"  members:      {len(members)} ({sum(1 for m in members if m.status == 'active')} active, "
              f"{sum(1 for m in members if m.status == 'grace_period')} grace, "
              f"{sum(1 for m in members if m.status == 'cancelled')} cancelled, "
              f"{sum(1 for m in members if m.status == 'expired')} expired)")
        print(f"  gifts:        {db.query(GiftCoupon).filter(GiftCoupon.merchant_id == mid).count()}")
        print(f"  shipping:     {db.query(FreeShippingCoupon).filter(FreeShippingCoupon.merchant_id == mid).count()}")
        print(f"  benefits:     {db.query(BenefitEvent).filter(BenefitEvent.merchant_id == mid).count()}")
        print(f"  activity:     {db.query(ActivityLog).filter(ActivityLog.merchant_id == mid).count()}")
        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

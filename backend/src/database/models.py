"""
Member Plus — Database Schema V2

Rebuilt to match PRD V3.0 §14 exactly. 11 core tables + 3 admin/email tables.

Changes from V1:
- merchants: added permanent_access_token, recurring_enabled, our_plan enum,
  member_count cache, status enum (trial|active|suspended|cancelled).
  Removed is_active bool + deactivated_at (replaced by status enum).
  Removed subscription_id FK (our_plan is the merchant's SaaS tier).
- membership_plans: status enum (active|paused|deactivating|deactivated),
  gift_name_ar/en, salla_offer_id renamed.
- plan_price_versions: NEW — price lock architecture per PRD §14.3.
- members: NEW — single table combining identity + subscription + benefit
  tracking per PRD §14.4. Replaces Customer + CustomerSubscription.
- gift_coupons: NEW — dedicated table per PRD §14.5.
- free_shipping_coupons: NEW — dedicated table per PRD §14.6.
- webhook_events: NEW — idempotency layer per PRD §14.7.
- interest_registrations: updated to use salla_customer_id per PRD §14.8.
- benefit_events: NEW — dispute audit trail per PRD §14.9.
- activity_log: NEW — per PRD §14.10.
- scheduled_jobs: NEW — per PRD §14.11.
- admin_users + admin_notes: per PRD §39.3.
- email_log: per PRD §41.7.
"""

import secrets
import uuid
from datetime import datetime, timedelta

from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Enum, ForeignKey,
    Index, Integer, Numeric, String, Text,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def _uuid():
    return str(uuid.uuid4())


def _access_token():
    return secrets.token_urlsafe(48)  # 64 chars


# ---------------------------------------------------------------------------
# §14.1 merchants
# ---------------------------------------------------------------------------
class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(String(36), primary_key=True, default=_uuid)
    salla_store_id = Column(BigInteger, unique=True, nullable=False, index=True)

    # OAuth (encrypted at rest via auth.crypto)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    token_expires_at = Column(DateTime, nullable=True)

    # Merchant status
    status = Column(
        String(20), nullable=False, default="trial", index=True,
    )  # trial | active | suspended | cancelled

    trial_ends_at = Column(DateTime, nullable=True)
    activated_at = Column(DateTime, nullable=True)

    # Setup
    setup_completed = Column(Boolean, default=False, nullable=False)
    setup_step = Column(Integer, default=0, nullable=False)  # 0-5

    # Salla recurring payments
    recurring_enabled = Column(Boolean, default=False, nullable=False)

    # Our SaaS plan
    our_plan = Column(
        String(20), nullable=True,
    )  # starter | pro | unlimited

    # Cached member count (updated by trigger/service)
    member_count = Column(Integer, default=0, nullable=False)

    # Dashboard access — PRD Appendix B
    permanent_access_token = Column(
        String(64), unique=True, nullable=False, default=_access_token,
    )
    dashboard_language = Column(String(5), default="ar", nullable=False)

    # Store info (from Salla, refreshed on customer.updated)
    store_name = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_merchants_status", "status"),
        Index("idx_merchants_trial_ends_at", "trial_ends_at"),
    )

    def __repr__(self):
        return f"<Merchant {self.id} | {self.store_name} | {self.status}>"


# ---------------------------------------------------------------------------
# §14.2 membership_plans
# ---------------------------------------------------------------------------
class MembershipPlan(Base):
    __tablename__ = "membership_plans"

    id = Column(String(36), primary_key=True, default=_uuid)
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=False, index=True)

    tier = Column(String(10), nullable=False, index=True)  # silver | gold
    display_name_ar = Column(String(100), nullable=False)
    display_name_en = Column(String(100), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)

    status = Column(
        String(20), nullable=False, default="active",
    )  # active | paused | deactivating | deactivated

    # Benefits
    discount_pct = Column(Numeric(5, 2), nullable=False)
    free_shipping_uses = Column(Integer, nullable=False)
    gift_name_ar = Column(String(100), default="الهدية الشهرية")
    gift_name_en = Column(String(100), default="Monthly Gift")

    # Salla linkage
    salla_offer_id = Column(BigInteger, nullable=True)
    salla_group_id = Column(BigInteger, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_plans_merchant_tier", "merchant_id", "tier"),
    )

    def __repr__(self):
        return f"<MembershipPlan {self.tier} | {self.display_name_en} | {self.price}>"


# ---------------------------------------------------------------------------
# §14.3 plan_price_versions — price lock architecture
# ---------------------------------------------------------------------------
class PlanPriceVersion(Base):
    __tablename__ = "plan_price_versions"

    id = Column(String(36), primary_key=True, default=_uuid)
    plan_id = Column(String(36), ForeignKey("membership_plans.id"), nullable=False, index=True)
    price = Column(Numeric(10, 2), nullable=False)
    salla_product_id = Column(BigInteger, nullable=True)
    salla_product_slug = Column(String(255), nullable=True)
    effective_from = Column(DateTime, nullable=False, default=datetime.utcnow)
    effective_to = Column(DateTime, nullable=True)  # NULL = currently active

    def __repr__(self):
        return f"<PriceVersion {self.id} | plan={self.plan_id} | {self.price}>"


# ---------------------------------------------------------------------------
# §14.4 members
# ---------------------------------------------------------------------------
class Member(Base):
    __tablename__ = "members"

    id = Column(String(36), primary_key=True, default=_uuid)
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=False, index=True)
    plan_id = Column(String(36), ForeignKey("membership_plans.id"), nullable=False)
    price_version_id = Column(String(36), ForeignKey("plan_price_versions.id"), nullable=True)

    salla_customer_id = Column(BigInteger, nullable=False, index=True)
    salla_subscription_id = Column(String(255), unique=True, nullable=True)

    status = Column(
        String(20), nullable=False, default="active", index=True,
    )  # active | grace_period | cancelled | expired | complimentary

    subscribed_price = Column(Numeric(10, 2), nullable=False)
    current_period_end = Column(DateTime, nullable=True)
    grace_period_ends_at = Column(DateTime, nullable=True)
    next_renewal_at = Column(DateTime, nullable=True)

    is_at_risk = Column(Boolean, default=False, nullable=False, index=True)
    total_saved_sar = Column(Numeric(10, 2), default=0, nullable=False)

    free_shipping_used = Column(Integer, default=0, nullable=False)
    free_shipping_quota = Column(Integer, nullable=False, default=0)

    last_order_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_members_salla_customer_id", "salla_customer_id"),
        Index("idx_members_next_renewal_at", "next_renewal_at"),
        Index("idx_members_current_period_end", "current_period_end"),
        Index("idx_members_is_at_risk", "is_at_risk"),
    )

    def __repr__(self):
        return f"<Member {self.id} | merchant={self.merchant_id} | {self.status}>"


# ---------------------------------------------------------------------------
# §14.5 gift_coupons
# ---------------------------------------------------------------------------
class GiftCoupon(Base):
    __tablename__ = "gift_coupons"

    id = Column(String(36), primary_key=True, default=_uuid)
    member_id = Column(String(36), ForeignKey("members.id"), nullable=False)
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=False)
    plan_id = Column(String(36), ForeignKey("membership_plans.id"), nullable=False)

    month = Column(String(10), nullable=False)  # e.g. '2026-05'
    coupon_code = Column(String(100), nullable=True)
    gift_type = Column(String(20), nullable=True)  # pct_all | pct_category | fixed | free_product
    gift_description_ar = Column(String(255), nullable=True)
    gift_description_en = Column(String(255), nullable=True)

    status = Column(
        String(20), nullable=False, default="pending",
    )  # pending | generated | used | expired | failed

    expires_at = Column(DateTime, nullable=True)
    attempts = Column(Integer, default=0, nullable=False)
    salla_coupon_id = Column(String(64), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_gift_member_month", "member_id", "month", unique=True),
        Index("idx_gift_merchant_month", "merchant_id", "month"),
        Index("idx_gift_status", "status"),
    )


# ---------------------------------------------------------------------------
# §14.6 free_shipping_coupons
# ---------------------------------------------------------------------------
class FreeShippingCoupon(Base):
    __tablename__ = "free_shipping_coupons"

    id = Column(String(36), primary_key=True, default=_uuid)
    member_id = Column(String(36), ForeignKey("members.id"), nullable=False)
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=False)

    month = Column(String(10), nullable=False)  # e.g. '2026-05'
    coupon_code = Column(String(100), nullable=True)
    quota = Column(Integer, nullable=False)
    used_count = Column(Integer, default=0, nullable=False)

    status = Column(
        String(20), nullable=False, default="active",
    )  # active | exhausted | expired | deactivated

    expires_at = Column(DateTime, nullable=True)
    salla_coupon_id = Column(String(64), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_shipping_member_month", "member_id", "month", unique=True),
        Index("idx_shipping_merchant_month", "merchant_id", "month"),
    )


# ---------------------------------------------------------------------------
# §14.7 webhook_events — idempotency
# ---------------------------------------------------------------------------
class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(String(36), primary_key=True, default=_uuid)
    event_type = Column(String(100), nullable=False)
    salla_event_id = Column(String(255), unique=True, nullable=False, index=True)
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=True, index=True)
    payload = Column(Text, nullable=False)  # full raw JSON

    status = Column(
        String(20), nullable=False, default="received",
    )  # received | processing | processed | failed | skipped

    attempts = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_webhook_status", "status"),
    )


# ---------------------------------------------------------------------------
# §14.8 interest_registrations — coming soon widget
# ---------------------------------------------------------------------------
class InterestRegistration(Base):
    __tablename__ = "interest_registrations"

    id = Column(String(36), primary_key=True, default=_uuid)
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=True, index=True)
    salla_customer_id = Column(BigInteger, nullable=False, index=True)

    clicked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    notified_at = Column(DateTime, nullable=True)
    subscribed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_interest_merchant_customer", "merchant_id", "salla_customer_id", unique=True),
    )


# ---------------------------------------------------------------------------
# §14.9 benefit_events — dispute investigation
# ---------------------------------------------------------------------------
class BenefitEvent(Base):
    __tablename__ = "benefit_events"

    id = Column(String(36), primary_key=True, default=_uuid)
    member_id = Column(String(36), ForeignKey("members.id"), nullable=False, index=True)
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=False, index=True)
    salla_order_id = Column(BigInteger, nullable=True, index=True)

    event_type = Column(
        String(30), nullable=False,
    )  # discount_applied | shipping_coupon_used | gift_coupon_used | member_price_applied | benefit_not_applied

    amount_saved = Column(Numeric(10, 2), nullable=True)
    reason_not_applied = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ---------------------------------------------------------------------------
# §14.10 activity_log
# ---------------------------------------------------------------------------
class ActivityLog(Base):
    __tablename__ = "activity_log"

    id = Column(String(36), primary_key=True, default=_uuid)
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=False, index=True)

    event_type = Column(String(100), nullable=False)
    # member.joined | member.cancelled | member.payment_failed |
    # benefit.discount_applied | benefit.shipping_used | benefit.gift_used |
    # coupon.generated | plan.benefit_changed

    member_id = Column(String(36), ForeignKey("members.id"), nullable=True, index=True)
    metadata_json = Column(Text, nullable=True)  # JSON string for event-specific details

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


# ---------------------------------------------------------------------------
# §14.11 scheduled_jobs
# ---------------------------------------------------------------------------
class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"

    id = Column(String(36), primary_key=True, default=_uuid)

    job_type = Column(String(100), nullable=False)
    # generate_monthly_coupons | renewal_charge | grace_period_expiry |
    # remove_from_group | group_health_check

    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=True, index=True)
    member_id = Column(String(36), ForeignKey("members.id"), nullable=True)

    scheduled_for = Column(DateTime, nullable=False)
    status = Column(
        String(20), nullable=False, default="pending",
    )  # pending | running | completed | failed | skipped

    attempts = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=3, nullable=False)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_jobs_status_scheduled_for", "status", "scheduled_for"),
        Index("idx_jobs_merchant_id", "merchant_id"),
    )


# ---------------------------------------------------------------------------
# §39.3 admin_users
# ---------------------------------------------------------------------------
class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(String(36), primary_key=True, default=_uuid)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    totp_secret = Column(Text, nullable=True)  # encrypted, for 2FA
    role = Column(String(20), nullable=False)  # admin | support | devops

    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ---------------------------------------------------------------------------
# §39.3 admin_notes
# ---------------------------------------------------------------------------
class AdminNote(Base):
    __tablename__ = "admin_notes"

    id = Column(String(36), primary_key=True, default=_uuid)
    admin_user_id = Column(String(36), ForeignKey("admin_users.id"), nullable=False)
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=False, index=True)
    note = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ---------------------------------------------------------------------------
# §41.7 email_log
# ---------------------------------------------------------------------------
class EmailLog(Base):
    __tablename__ = "email_log"

    id = Column(String(36), primary_key=True, default=_uuid)
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=False, index=True)
    member_id = Column(String(36), ForeignKey("members.id"), nullable=True, index=True)

    email_type = Column(String(100), nullable=False, index=True)
    recipient_email = Column(String(255), nullable=False)
    language = Column(String(5), nullable=False)  # ar | en
    subject = Column(String(500), nullable=True)

    status = Column(
        String(20), nullable=False, default="sent",
    )  # sent | delivered | opened | bounced | failed

    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    delivered_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    dashboard_link = Column(String(500), nullable=True)

    __table_args__ = (
        Index("idx_email_log_status", "status"),
        Index("idx_email_log_language", "language"),
    )

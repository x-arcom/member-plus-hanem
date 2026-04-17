"""
Phase 1 + Phase 2 Database Models

Phase 1: Merchant, OAuth Token, Session.
Phase 2: MembershipPlan, Subscription, plus new merchant.setup_step/subscription_id.
"""

import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Integer, Numeric
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Merchant(Base):
    """
    Merchant record representing a Salla store owner with trial and setup state.
    
    Phase 1: Core merchant profile with trial activation.
    Phase 2+: Extended with billing, subscription, setup wizard completion.
    """
    __tablename__ = "merchants"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Salla Integration
    salla_store_id = Column(String(255), unique=True, nullable=False, index=True)
    store_name = Column(String(255), nullable=True)
    merchant_email = Column(String(255), nullable=True)
    merchant_phone = Column(String(20), nullable=True)
    
    # Preferences
    language = Column(String(10), default="ar", nullable=False)  # 'ar' or 'en'
    
    # OAuth Token Reference
    oauth_token_id = Column(String(36), ForeignKey("oauth_tokens.id"), nullable=True)
    
    # Trial State (Phase 1)
    trial_start_date = Column(DateTime, nullable=False)
    trial_end_date = Column(DateTime, nullable=False)
    trial_active = Column(Boolean, default=True, nullable=False)
    
    # Setup Progress (Phase 1+)
    setup_state = Column(String(50), default="onboarding", nullable=False, index=True)
    # Possible states:
    # - 'onboarding' (Phase 1: just installed)
    # - 'setup_wizard' (Phase 2: in progress)
    # - 'setup_complete' (Phase 2: ready to provision)
    # - 'provisioning' (Phase 3: creating Salla resources)
    # - 'active' (Phase 4+: live and operational)

    # Phase 2 wizard step (0..N). 0 means not started; increments per completed step.
    setup_step = Column(Integer, default=0, nullable=False)

    # Phase 2 subscription reference (merchant's own subscription to Member Plus).
    subscription_id = Column(String(36), ForeignKey("subscriptions.id"), nullable=True)

    # Phase 3 lifecycle — set to False and populated on app.uninstalled webhook.
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    deactivated_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Merchant {self.id} | {self.store_name} | {self.setup_state}>"
    
    def get_remaining_trial_days(self) -> int:
        """Calculate remaining trial days."""
        if not self.trial_active:
            return 0
        remaining = (self.trial_end_date - datetime.utcnow()).days
        return max(0, remaining)


class OAuthToken(Base):
    """
    Salla OAuth token storage with encryption.
    
    Tokens are stored encrypted and automatically refreshed before expiration.
    """
    __tablename__ = "oauth_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant_id = Column(String(36), ForeignKey("merchants.id"), unique=True, nullable=False, index=True)
    
    # Encrypted Token Fields (stored encrypted in database)
    access_token = Column(Text, nullable=False)  # Encrypted
    refresh_token = Column(Text, nullable=True)  # Encrypted
    
    # Token Metadata
    expires_at = Column(DateTime, nullable=False, index=True)
    scope = Column(String(500), nullable=True)  # OAuth scopes granted
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<OAuthToken {self.id} | expires={self.expires_at}>"
    
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.utcnow() >= self.expires_at
    
    def is_expiring_soon(self, minutes: int = 5) -> bool:
        """Check if token will expire within N minutes."""
        expiry_threshold = datetime.utcnow() + timedelta(minutes=minutes)
        return self.expires_at <= expiry_threshold


class Session(Base):
    """
    Merchant dashboard session tokens.
    
    Used for merchant authentication to dashboard.
    Can be JWT tokens stored for revocation or session records.
    """
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=False, index=True)
    
    # Session Token (JWT or opaque token)
    token = Column(String(512), unique=True, nullable=False, index=True)
    
    # Expiration
    expires_at = Column(DateTime, nullable=False, index=True)
    
    # Metadata
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Session {self.id} | merchant={self.merchant_id} | expires={self.expires_at}>"
    
    def is_valid(self) -> bool:
        """Check if session is still valid."""
        return datetime.utcnow() < self.expires_at


class MembershipPlan(Base):
    """
    A membership plan a merchant sells to their customers.

    Phase 2 shipped a generic plan. Phase-R (realignment to plane.md) adds
    structured benefit fields — discount_percent, free_shipping_quota,
    monthly_gift, early_access, badge — plus a tier (`silver` | `gold` | null)
    and a Salla customer-group id stamped by provisioning.

    `tier` is nullable so legacy generic plans created before Phase R
    continue to work; new plans created via the program wizard always have
    one of `silver` / `gold`.
    """
    __tablename__ = "membership_plans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=False, index=True)

    tier = Column(String(20), nullable=True, index=True)  # 'silver' | 'gold' | None

    name_ar = Column(String(255), nullable=False)
    name_en = Column(String(255), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="SAR", nullable=False)
    duration_days = Column(Integer, nullable=False)
    benefits = Column(Text, nullable=True)  # free-form marketing copy

    # Structured benefits (Phase R)
    discount_percent = Column(Numeric(5, 2), nullable=True)        # 0..100
    free_shipping_quota = Column(Integer, nullable=True)           # per period
    monthly_gift_enabled = Column(Boolean, default=False, nullable=False)
    early_access_enabled = Column(Boolean, default=False, nullable=False)
    badge_enabled = Column(Boolean, default=False, nullable=False)

    # Provisioning linkage (Phase R / G)
    salla_customer_group_id = Column(String(64), nullable=True)
    salla_special_offer_id = Column(String(64), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<MembershipPlan {self.id} | {self.tier or 'generic'} | {self.name_en} | {self.price} {self.currency}>"


class Customer(Base):
    """
    A shopper who has enrolled in one of a merchant's membership plans.

    Phase 4: created via the public enrollment form. One customer per
    (merchant, email) — re-enrollment just adds another subscription row.
    """
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(32), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Customer {self.id} | merchant={self.merchant_id} | {self.email}>"


class CustomerSubscription(Base):
    """
    A customer's subscription to a specific membership plan.

    Phase 4: status machine is `pending -> active -> {cancelled, expired}`.
    `pending -> cancelled` is also allowed (never paid).
    """
    __tablename__ = "customer_subscriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=False, index=True)
    plan_id = Column(String(36), ForeignKey("membership_plans.id"), nullable=False, index=True)

    status = Column(String(20), default="pending", nullable=False, index=True)
    # 'pending' | 'active' | 'grace' | 'cancelled' | 'expired'

    started_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    grace_ends_at = Column(DateTime, nullable=True)  # Phase G — end of grace window
    activated_at = Column(DateTime, nullable=True)  # set when moved to `active`

    # Price captured at enrollment so changing the plan's price later doesn't
    # rewrite history.
    price_at_enrollment = Column(Numeric(10, 2), nullable=False)
    currency_at_enrollment = Column(String(10), nullable=False, default="SAR")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<CustomerSubscription {self.id} | cust={self.customer_id} | {self.status}>"


class InterestSignup(Base):
    """
    Phase G — prospective-customer email capture for merchants whose
    program isn't launched yet (no active plans). Persists across
    re-submissions (`signed_up_at` updated, `notified_at` stays until the
    launch-notification job fires).
    """
    __tablename__ = "interest_signups"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=True, index=True)
    salla_store_id = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)

    signed_up_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    notified_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<InterestSignup {self.email} @ {self.salla_store_id}>"


class BenefitDelivery(Base):
    """
    Phase 6 — one row per benefit issued to a member subscription.

    `kind` is one of:
      - free_shipping   : a shipping-credit coupon
      - monthly_gift    : a single-use gift coupon
      - auto_discount   : discount attached via customer group (no coupon)
      - early_access    : feature flag, no coupon
      - badge           : feature flag, no coupon

    `status`:
      - delivered       : Salla coupon was created; `salla_coupon_id` set
      - delivered-mock  : fallback when Salla unavailable; coupon_code is
                          a locally-generated MP-* string
      - flag-only       : used for early_access / badge / auto_discount
      - revoked         : future use (e.g. after cancellation clawback)
    """
    __tablename__ = "benefit_deliveries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subscription_id = Column(String(36), ForeignKey("customer_subscriptions.id"), nullable=False, index=True)
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=False, index=True)

    kind = Column(String(32), nullable=False, index=True)
    period_key = Column(String(16), nullable=True, index=True)  # 'YYYY-MM' for monthly items

    coupon_code = Column(String(64), nullable=True)
    uses_allowed = Column(Integer, nullable=True)
    uses_remaining = Column(Integer, nullable=True)
    valid_until = Column(DateTime, nullable=True)

    salla_coupon_id = Column(String(64), nullable=True)
    status = Column(String(32), default="delivered", nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<BenefitDelivery {self.id} | sub={self.subscription_id} | {self.kind}/{self.status}>"


class Subscription(Base):
    """
    The merchant's own subscription to Member Plus.

    Phase 2 uses a mock payment adapter. Phase 3 will wire a real one.
    """
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant_id = Column(String(36), ForeignKey("merchants.id"), nullable=False, index=True)

    tier = Column(String(50), nullable=False)                 # 'starter' | 'growth' | 'pro'
    status = Column(String(20), default="pending", nullable=False, index=True)
    # 'pending' | 'active' | 'cancelled' | 'expired'

    started_at = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    payment_reference = Column(String(255), nullable=True)    # mock token, real gateway id later

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Subscription {self.id} | merchant={self.merchant_id} | {self.tier}/{self.status}>"

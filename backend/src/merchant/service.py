"""
Merchant service for business logic.

Handles merchant creation, retrieval, trial state, setup progress tracking.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, EmailStr


class MerchantCreateRequest(BaseModel):
    """Request model for creating a merchant."""
    salla_store_id: str
    store_name: str
    merchant_email: EmailStr
    language: str = "ar"


class MerchantResponse(BaseModel):
    """Response model for merchant data."""
    id: str
    salla_store_id: str
    store_name: str
    merchant_email: str
    language: str
    trial_start_date: datetime
    trial_end_date: datetime
    trial_active: bool
    setup_state: str
    remaining_trial_days: int
    
    class Config:
        from_attributes = True


class TrialResponse(BaseModel):
    """Response model for trial status."""
    trial_active: bool
    trial_start_date: datetime
    trial_end_date: datetime
    remaining_days: int


class MerchantService:
    """Service for merchant operations."""
    
    def __init__(self, db_session):
        """Initialize with database session."""
        self.db = db_session
    
    def create_merchant(self, request: MerchantCreateRequest) -> dict:
        """
        Create a new merchant record.
        
        Args:
            request: Merchant creation request with store info
            
        Returns:
            Merchant record as dict with id, trial dates, setup_state
            
        Raises:
            ValueError: If merchant with same salla_store_id already exists
        """
        from database.models import Merchant
        
        # Check for duplicate
        existing = self.db.query(Merchant).filter(
            Merchant.salla_store_id == request.salla_store_id
        ).first()
        
        if existing:
            raise ValueError(f"Merchant with salla_store_id {request.salla_store_id} already exists")
        
        # Calculate trial dates
        trial_start = datetime.utcnow()
        trial_duration = timedelta(days=14)  # TODO: Make configurable
        trial_end = trial_start + trial_duration
        
        # Create merchant
        merchant = Merchant(
            id=str(uuid.uuid4()),
            salla_store_id=request.salla_store_id,
            store_name=request.store_name,
            merchant_email=request.merchant_email,
            language=request.language,
            trial_start_date=trial_start,
            trial_end_date=trial_end,
            trial_active=True,
            setup_state="onboarding",
        )
        
        self.db.add(merchant)
        self.db.commit()
        
        return {
            "id": str(merchant.id),
            "salla_store_id": merchant.salla_store_id,
            "store_name": merchant.store_name,
            "merchant_email": merchant.merchant_email,
            "language": merchant.language,
            "trial_start_date": merchant.trial_start_date,
            "trial_end_date": merchant.trial_end_date,
            "trial_active": merchant.trial_active,
            "setup_state": merchant.setup_state,
        }
    
    def get_merchant(self, merchant_id: str) -> Optional[dict]:
        """Get merchant by ID."""
        from database.models import Merchant
        
        merchant = self.db.query(Merchant).filter(
            Merchant.id == merchant_id
        ).first()
        
        if not merchant:
            return None
        
        return {
            "id": str(merchant.id),
            "salla_store_id": merchant.salla_store_id,
            "store_name": merchant.store_name,
            "merchant_email": merchant.merchant_email,
            "language": merchant.language,
            "trial_start_date": merchant.trial_start_date,
            "trial_end_date": merchant.trial_end_date,
            "trial_active": merchant.trial_active,
            "setup_state": merchant.setup_state,
            "remaining_trial_days": merchant.get_remaining_trial_days(),
        }
    
    def get_merchant_by_salla_id(self, salla_store_id: str) -> Optional[dict]:
        """Get merchant by Salla store ID."""
        from database.models import Merchant
        
        merchant = self.db.query(Merchant).filter(
            Merchant.salla_store_id == salla_store_id
        ).first()
        
        if not merchant:
            return None
        
        return {
            "id": str(merchant.id),
            "salla_store_id": merchant.salla_store_id,
            "store_name": merchant.store_name,
            "merchant_email": merchant.merchant_email,
            "language": merchant.language,
            "trial_start_date": merchant.trial_start_date,
            "trial_end_date": merchant.trial_end_date,
            "trial_active": merchant.trial_active,
            "setup_state": merchant.setup_state,
            "remaining_trial_days": merchant.get_remaining_trial_days(),
        }
    
    def get_trial_status(self, merchant_id: str) -> Optional[dict]:
        """Get trial status for a merchant."""
        merchant = self.get_merchant(merchant_id)
        if not merchant:
            return None
        
        return {
            "trial_active": merchant["trial_active"],
            "trial_start_date": merchant["trial_start_date"],
            "trial_end_date": merchant["trial_end_date"],
            "remaining_days": merchant["remaining_trial_days"],
        }
    
    def update_setup_state(self, merchant_id: str, new_state: str) -> bool:
        """Update merchant setup state."""
        from database.models import Merchant
        
        merchant = self.db.query(Merchant).filter(
            Merchant.id == merchant_id
        ).first()
        
        if not merchant:
            return False
        
        merchant.setup_state = new_state
        merchant.updated_at = datetime.utcnow()
        self.db.commit()
        
        return True
    
    def get_dashboard_overview(self, merchant_id: str) -> Optional[dict]:
        """Get dashboard overview data for merchant.

        Phase 4: `member_count` and `monthly_revenue` are computed from
        `CustomerSubscription` rows — no longer placeholders.
        """
        from database.models import CustomerSubscription
        from sqlalchemy import func
        from decimal import Decimal

        merchant = self.get_merchant(merchant_id)
        if not merchant:
            return None

        # Active members = any active subscription
        member_count = (
            self.db.query(func.count(CustomerSubscription.id))
            .filter(
                CustomerSubscription.merchant_id == merchant_id,
                CustomerSubscription.status == "active",
            )
            .scalar()
        ) or 0

        # Monthly revenue = sum of price_at_enrollment for subs activated
        # within the current calendar month.
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        revenue = (
            self.db.query(func.coalesce(func.sum(CustomerSubscription.price_at_enrollment), 0))
            .filter(
                CustomerSubscription.merchant_id == merchant_id,
                CustomerSubscription.status == "active",
                CustomerSubscription.activated_at >= month_start,
            )
            .scalar()
        ) or Decimal("0")

        return {
            "merchant_name": merchant["store_name"],
            "store_name": merchant["store_name"],
            "setup_state": merchant["setup_state"],
            "trial_remaining_days": merchant["remaining_trial_days"],
            "trial_active": merchant["trial_active"],
            "member_count": int(member_count),
            "monthly_revenue": float(revenue),
            "currency": "SAR",
            "language": merchant["language"],
        }

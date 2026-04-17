"""
Dashboard API routes for merchant access.
"""

from fastapi import APIRouter, Depends, HTTPException
from auth.jwt import get_current_merchant
from merchant.service import MerchantService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base
from config.loader import load_config

router = APIRouter(prefix="/api/merchant", tags=["merchant"])


def get_db_session():
    """Get database session for dependency injection."""
    db_url = load_config().database_url or "sqlite:///memberplus_phase1.db"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


@router.get("/profile")
async def get_merchant_profile(merchant_id: str = Depends(get_current_merchant)):
    """
    Get merchant profile and store information.
    
    Requires: Valid JWT token in Authorization header
    """
    db_session = get_db_session()
    service = MerchantService(db_session)
    
    merchant = service.get_merchant(merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    
    db_session.close()
    
    return {
        "id": merchant["id"],
        "salla_store_id": merchant["salla_store_id"],
        "store_name": merchant["store_name"],
        "merchant_email": merchant["merchant_email"],
        "language": merchant["language"],
    }


@router.get("/trial")
async def get_trial_status(merchant_id: str = Depends(get_current_merchant)):
    """
    Get merchant's trial status and countdown.
    
    Requires: Valid JWT token
    """
    db_session = get_db_session()
    service = MerchantService(db_session)
    
    trial = service.get_trial_status(merchant_id)
    if not trial:
        raise HTTPException(status_code=404, detail="Merchant not found")
    
    db_session.close()
    
    return trial


@router.get("/dashboard")
async def get_dashboard_overview(merchant_id: str = Depends(get_current_merchant)):
    """
    Get dashboard overview data.
    
    Includes: setup state, trial status, member count (placeholder), revenue (placeholder)
    """
    db_session = get_db_session()
    service = MerchantService(db_session)
    
    dashboard = service.get_dashboard_overview(merchant_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Merchant not found")
    
    db_session.close()
    
    return dashboard

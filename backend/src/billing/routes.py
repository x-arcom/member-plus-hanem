"""Billing routes (JWT-protected, merchant-scoped)."""
from fastapi import APIRouter, Body, Depends, HTTPException

from auth.jwt import get_current_merchant
from dashboard.routes import get_db_session
from billing.service import BillingService, BillingError

router = APIRouter(prefix="/api/merchant/billing", tags=["billing"])


def _service() -> BillingService:
    return BillingService(get_db_session())


@router.get("/tiers")
async def list_tiers(merchant_id: str = Depends(get_current_merchant)):
    svc = _service()
    try:
        return {"tiers": svc.tiers()}
    finally:
        svc.db.close()


@router.get("/subscription")
async def get_subscription(merchant_id: str = Depends(get_current_merchant)):
    svc = _service()
    try:
        return {"subscription": svc.get_subscription(merchant_id)}
    finally:
        svc.db.close()


@router.post("/subscribe")
async def subscribe(
    payload: dict = Body(...),
    merchant_id: str = Depends(get_current_merchant),
):
    svc = _service()
    try:
        tier = payload.get("tier")
        if not tier:
            raise HTTPException(status_code=400, detail="tier is required")
        return svc.subscribe(merchant_id, tier)
    except BillingError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    finally:
        svc.db.close()


@router.post("/mock-confirm")
async def mock_confirm(
    payload: dict = Body(...),
    merchant_id: str = Depends(get_current_merchant),
):
    svc = _service()
    try:
        subscription_id = payload.get("subscription_id")
        success = bool(payload.get("success", True))
        if not subscription_id:
            raise HTTPException(status_code=400, detail="subscription_id is required")
        return {"subscription": svc.confirm(merchant_id, subscription_id, success=success)}
    except BillingError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    finally:
        svc.db.close()

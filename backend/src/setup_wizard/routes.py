"""Setup wizard routes (JWT-protected, merchant-scoped)."""
from fastapi import APIRouter, Body, Depends, HTTPException

from auth.jwt import get_current_merchant
from dashboard.routes import get_db_session
from setup_wizard.service import WizardService

router = APIRouter(prefix="/api/merchant/setup", tags=["setup"])


@router.get("/state")
async def get_state(merchant_id: str = Depends(get_current_merchant)):
    svc = WizardService(get_db_session())
    try:
        state = svc.state(merchant_id)
        if not state:
            raise HTTPException(status_code=404, detail="Merchant not found")
        return state
    finally:
        svc.db.close()


@router.post("/advance")
async def advance(
    payload: dict = Body(default={}),
    merchant_id: str = Depends(get_current_merchant),
):
    svc = WizardService(get_db_session())
    try:
        state = svc.advance(merchant_id, step_data=payload)
        if not state:
            raise HTTPException(status_code=404, detail="Merchant not found")
        return state
    finally:
        svc.db.close()


@router.post("/program")
async def configure_program(
    payload: dict = Body(...),
    merchant_id: str = Depends(get_current_merchant),
):
    """Phase-R endpoint. Receives `{silver: {...}, gold: {...}}` and
    upserts both plans, completes setup, triggers provisioning.
    """
    svc = WizardService(get_db_session())
    try:
        silver = payload.get("silver") or {}
        gold = payload.get("gold") or {}
        if not silver and not gold:
            raise HTTPException(status_code=400, detail="silver and/or gold configuration required")

        try:
            state = svc.configure_program(merchant_id, silver, gold)
        except Exception as exc:
            # PlanValidationError (ValueError) or anything the plan validator raises
            raise HTTPException(status_code=400, detail=str(exc))

        if not state:
            raise HTTPException(status_code=404, detail="Merchant not found")
        return state
    finally:
        svc.db.close()


@router.post("/reset")
async def reset(merchant_id: str = Depends(get_current_merchant)):
    svc = WizardService(get_db_session())
    try:
        state = svc.reset(merchant_id)
        if not state:
            raise HTTPException(status_code=404, detail="Merchant not found")
        return state
    finally:
        svc.db.close()

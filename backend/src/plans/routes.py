"""Plan CRUD routes (JWT-protected, merchant-scoped)."""
from fastapi import APIRouter, Body, Depends, HTTPException, Query

from auth.jwt import get_current_merchant
from dashboard.routes import get_db_session
from plans.service import PlanService, PlanValidationError

router = APIRouter(prefix="/api/merchant/plans", tags=["plans"])


def _service() -> PlanService:
    return PlanService(get_db_session())


@router.get("")
async def list_plans(
    active_only: bool = Query(False),
    merchant_id: str = Depends(get_current_merchant),
):
    svc = _service()
    try:
        return {"plans": svc.list(merchant_id, active_only=active_only)}
    finally:
        svc.db.close()


@router.post("", status_code=201)
async def create_plan(
    payload: dict = Body(...),
    merchant_id: str = Depends(get_current_merchant),
):
    svc = _service()
    try:
        return svc.create(merchant_id, payload)
    except PlanValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        svc.db.close()


@router.get("/{plan_id}")
async def get_plan(plan_id: str, merchant_id: str = Depends(get_current_merchant)):
    svc = _service()
    try:
        plan = svc.get(merchant_id, plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        return plan
    finally:
        svc.db.close()


@router.patch("/{plan_id}")
async def update_plan(
    plan_id: str,
    payload: dict = Body(...),
    merchant_id: str = Depends(get_current_merchant),
):
    svc = _service()
    try:
        plan = svc.update(merchant_id, plan_id, payload)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        return plan
    except PlanValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        svc.db.close()


@router.delete("/{plan_id}", status_code=204)
async def delete_plan(plan_id: str, merchant_id: str = Depends(get_current_merchant)):
    svc = _service()
    try:
        if not svc.delete(merchant_id, plan_id):
            raise HTTPException(status_code=404, detail="Plan not found")
    finally:
        svc.db.close()

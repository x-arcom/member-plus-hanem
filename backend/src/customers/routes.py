"""Public (unauthenticated) enrollment routes."""
from fastapi import APIRouter, Body, HTTPException

from customers.service import CustomerEnrollmentService, EnrollmentError
from dashboard.routes import get_db_session

router = APIRouter(prefix="/api/public/merchants", tags=["public-enrollment"])


@router.get("/{salla_store_id}/plans")
async def public_plans(salla_store_id: str):
    db = get_db_session()
    svc = CustomerEnrollmentService(db)
    try:
        return svc.list_active_plans_for_store(salla_store_id)
    except EnrollmentError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    finally:
        db.close()


@router.post("/{salla_store_id}/enroll", status_code=201)
async def public_enroll(salla_store_id: str, payload: dict = Body(...)):
    db = get_db_session()
    svc = CustomerEnrollmentService(db)
    try:
        return svc.enroll(salla_store_id, payload)
    except EnrollmentError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    finally:
        db.close()


@router.get("/{salla_store_id}/membership")
async def public_membership_lookup(salla_store_id: str, email: str):
    """Phase-R read-only membership summary keyed by email. A full member
    login + dashboard arrives in a later phase."""
    db = get_db_session()
    svc = CustomerEnrollmentService(db)
    try:
        return svc.lookup_membership(salla_store_id, email)
    except EnrollmentError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    finally:
        db.close()


@router.post("/{salla_store_id}/interest", status_code=201)
async def public_interest(salla_store_id: str, payload: dict = Body(...)):
    """Phase G — interest signup for a not-yet-launched program."""
    db = get_db_session()
    svc = CustomerEnrollmentService(db)
    try:
        return svc.register_interest(salla_store_id, payload.get("email") or "")
    except EnrollmentError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    finally:
        db.close()

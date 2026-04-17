"""Public benefit redemption endpoint.

Phase G — a coupon code is POSTed here, we decrement `uses_remaining`.
In production this will be driven by a Salla webhook ("coupon used"); for
now the endpoint is callable directly so the frontend + tests can exercise
the full loop.
"""
from fastapi import APIRouter, Body, HTTPException

from dashboard.routes import get_db_session
from benefits.service import redeem


router = APIRouter(prefix="/api/public/benefits", tags=["benefits"])


@router.post("/redeem")
async def redeem_coupon(payload: dict = Body(...)):
    code = (payload.get("coupon_code") or "").strip()
    if not code:
        raise HTTPException(status_code=400, detail="coupon_code is required")
    db = get_db_session()
    try:
        try:
            delivery = redeem(db, code)
        except KeyError:
            raise HTTPException(status_code=404, detail="coupon not found")
        except ValueError as exc:
            raise HTTPException(status_code=410, detail=str(exc))
        return {"delivery": delivery}
    finally:
        db.close()

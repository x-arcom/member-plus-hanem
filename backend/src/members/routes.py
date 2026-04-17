"""Member management routes (JWT-protected, merchant-scoped)."""
from fastapi import APIRouter, Depends, HTTPException, Query

from auth.jwt import get_current_merchant
from dashboard.routes import get_db_session
from members.service import MemberService, MemberError

router = APIRouter(prefix="/api/merchant/members", tags=["members"])


@router.get("")
async def list_members(
    status: str = Query(None),
    merchant_id: str = Depends(get_current_merchant),
):
    db = get_db_session()
    svc = MemberService(db)
    try:
        return {"members": svc.list(merchant_id, status=status)}
    finally:
        db.close()


@router.post("/{subscription_id}/confirm")
async def confirm_member(
    subscription_id: str,
    merchant_id: str = Depends(get_current_merchant),
):
    db = get_db_session()
    svc = MemberService(db)
    try:
        return svc.confirm(merchant_id, subscription_id)
    except MemberError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    finally:
        db.close()


@router.post("/{subscription_id}/cancel")
async def cancel_member(
    subscription_id: str,
    merchant_id: str = Depends(get_current_merchant),
):
    db = get_db_session()
    svc = MemberService(db)
    try:
        return svc.cancel(merchant_id, subscription_id)
    except MemberError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    finally:
        db.close()


@router.post("/{subscription_id}/renew")
async def renew_member(
    subscription_id: str,
    merchant_id: str = Depends(get_current_merchant),
):
    db = get_db_session()
    svc = MemberService(db)
    try:
        return svc.renew(merchant_id, subscription_id)
    except MemberError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc))
    finally:
        db.close()


@router.get("/{subscription_id}/benefits")
async def list_member_benefits(
    subscription_id: str,
    merchant_id: str = Depends(get_current_merchant),
):
    """Phase 6 — list BenefitDelivery rows for one subscription.

    Enforces merchant isolation: the subscription must belong to the
    authenticated merchant or we return 404.
    """
    from benefits.service import list_for_merchant

    db = get_db_session()
    svc = MemberService(db)
    try:
        # _get_owned will raise MemberError(404) if the sub isn't the
        # caller's — reuse that isolation check before returning benefits.
        try:
            svc._get_owned(merchant_id, subscription_id)
        except MemberError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc))
        return {"benefits": list_for_merchant(db, merchant_id, subscription_id=subscription_id)}
    finally:
        db.close()

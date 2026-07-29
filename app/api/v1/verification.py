from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_admin
from app.models.user import User as UserModel
from app.schemas.verification import (
    RejectionReasonCreate,
    RejectionReasonRead,
    VerificationRequestRead,
)
from app.services.user_service import get_user_by_bale_id
from app.services.verification_service import (
    approve_verification_request,
    create_rejection_reason,
    create_verification_request,
    deactivate_rejection_reason,
    get_active_rejection_reasons,
    get_pending_verification_requests,
    reject_verification_request,
    update_rejection_reason,
)

router = APIRouter(prefix="/verification", tags=["verification"])


@router.post("/submit", response_model=VerificationRequestRead)
async def submit_verification(
    bale_user_id: int,
    bale_file_id: str,
    db: AsyncSession = Depends(get_db),
) -> VerificationRequestRead:
    user = await get_user_by_bale_id(db, bale_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    request = await create_verification_request(db, user.id, bale_file_id)
    return VerificationRequestRead.model_validate(request)


@router.get("/pending", response_model=list[VerificationRequestRead])
async def list_pending_verifications(
    db: AsyncSession = Depends(get_db),
    _admin: UserModel = Depends(require_admin),
) -> list[VerificationRequestRead]:
    requests = await get_pending_verification_requests(db)
    return [VerificationRequestRead.model_validate(r) for r in requests]


@router.post("/{request_id}/approve", response_model=VerificationRequestRead)
async def approve_verification(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    admin: UserModel = Depends(require_admin),
) -> VerificationRequestRead:
    request = await approve_verification_request(db, request_id, admin.id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return VerificationRequestRead.model_validate(request)


@router.post("/{request_id}/reject", response_model=VerificationRequestRead)
async def reject_verification(
    request_id: int,
    rejection_reason_id: int,
    db: AsyncSession = Depends(get_db),
    admin: UserModel = Depends(require_admin),
) -> VerificationRequestRead:
    request = await reject_verification_request(db, request_id, admin.id, rejection_reason_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return VerificationRequestRead.model_validate(request)


@router.post("/rejection-reasons", response_model=RejectionReasonRead)
async def create_reason(
    payload: RejectionReasonCreate,
    db: AsyncSession = Depends(get_db),
    _admin: UserModel = Depends(require_admin),
) -> RejectionReasonRead:
    reason = await create_rejection_reason(db, payload.text)
    return RejectionReasonRead.model_validate(reason)


@router.get("/rejection-reasons", response_model=list[RejectionReasonRead])
async def list_reasons(
    db: AsyncSession = Depends(get_db),
    _admin: UserModel = Depends(require_admin),
) -> list[RejectionReasonRead]:
    reasons = await get_active_rejection_reasons(db)
    return [RejectionReasonRead.model_validate(r) for r in reasons]


@router.put("/rejection-reasons/{reason_id}", response_model=RejectionReasonRead)
async def edit_reason(
    reason_id: int,
    payload: RejectionReasonCreate,
    db: AsyncSession = Depends(get_db),
    _admin: UserModel = Depends(require_admin),
) -> RejectionReasonRead:
    reason = await update_rejection_reason(db, reason_id, payload.text)
    if not reason:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reason not found")
    return RejectionReasonRead.model_validate(reason)


@router.delete("/rejection-reasons/{reason_id}", response_model=RejectionReasonRead)
async def delete_reason(
    reason_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: UserModel = Depends(require_admin),
) -> RejectionReasonRead:
    reason = await deactivate_rejection_reason(db, reason_id)
    if not reason:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reason not found")
    return RejectionReasonRead.model_validate(reason)
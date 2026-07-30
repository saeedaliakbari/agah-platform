from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_admin
from app.models.user import User as UserModel
from app.schemas.loan import (
    LoanAccountCreate,
    LoanAccountRead,
    LoanRateRead,
    LoanRequestCreate,
    LoanRequestRead,
)
from app.services.loan_service import (
    cancel_loan_request,
    complete_loan_request,
    create_loan_account,
    create_loan_request,
    get_loan_account,
    get_loan_rate,
    get_user_loan_requests,
    get_waiting_list,
)
from app.services.user_service import get_user_by_bale_id

router = APIRouter(prefix="/loans", tags=["loans"])


@router.post("/account/submit", response_model=LoanAccountRead)
async def submit_loan_account(
    bale_user_id: int,
    payload: LoanAccountCreate,
    db: AsyncSession = Depends(get_db),
) -> LoanAccountRead:
    user = await get_user_by_bale_id(db, bale_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    account = await create_loan_account(
        db,
        user.id,
        payload.bank_type,
        payload.national_id,
        payload.full_name,
        payload.phone_number,
        payload.account_number,
    )
    return LoanAccountRead.model_validate(account)


@router.get("/account/{bale_user_id}/{bank_type}", response_model=LoanAccountRead)
async def get_user_loan_account(
    bale_user_id: int, bank_type: str, db: AsyncSession = Depends(get_db)
) -> LoanAccountRead:
    user = await get_user_by_bale_id(db, bale_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    account = await get_loan_account(db, user.id, bank_type)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not registered")
    return LoanAccountRead.model_validate(account)


@router.get("/rate/{bank_type}/{action_type}", response_model=LoanRateRead)
async def get_rate(
    bank_type: str, action_type: str, db: AsyncSession = Depends(get_db)
) -> LoanRateRead:
    rate = await get_loan_rate(db, bank_type, action_type)
    if not rate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rate not configured")
    return LoanRateRead.model_validate(rate)


@router.post("/request/submit", response_model=LoanRequestRead)
async def submit_loan_request(
    bale_user_id: int,
    payload: LoanRequestCreate,
    db: AsyncSession = Depends(get_db),
) -> LoanRequestRead:
    user = await get_user_by_bale_id(db, bale_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    request = await create_loan_request(
        db,
        user.id,
        payload.bank_type,
        payload.action_type,
        payload.point_type,
        payload.amount,
        payload.recipient_is_self,
        payload.recipient_national_id,
        payload.recipient_full_name,
        payload.recipient_phone_number,
        payload.recipient_account_number,
    )
    if not request:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rate not configured")
    return LoanRequestRead.model_validate(request)


@router.get("/waiting-list/{bank_type}/{action_type}", response_model=list[LoanRequestRead])
async def waiting_list(
    bank_type: str, action_type: str, db: AsyncSession = Depends(get_db)
) -> list[LoanRequestRead]:
    requests = await get_waiting_list(db, bank_type, action_type)
    return [LoanRequestRead.model_validate(r) for r in requests]


@router.get("/my-requests/{bale_user_id}", response_model=list[LoanRequestRead])
async def my_requests(
    bale_user_id: int, db: AsyncSession = Depends(get_db)
) -> list[LoanRequestRead]:
    user = await get_user_by_bale_id(db, bale_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    requests = await get_user_loan_requests(db, user.id)
    return [LoanRequestRead.model_validate(r) for r in requests]


@router.post("/request/{request_id}/complete", response_model=LoanRequestRead)
async def complete_request(
    request_id: int, bale_user_id: int, db: AsyncSession = Depends(get_db)
) -> LoanRequestRead:
    user = await get_user_by_bale_id(db, bale_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    request = await complete_loan_request(db, request_id, user.id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot complete this request"
        )
    return LoanRequestRead.model_validate(request)


@router.post("/request/{request_id}/cancel", response_model=LoanRequestRead)
async def cancel_request(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    admin: UserModel = Depends(require_admin),
) -> LoanRequestRead:
    request = await cancel_loan_request(db, request_id, admin.id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot cancel this request"
        )
    return LoanRequestRead.model_validate(request)
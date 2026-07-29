from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_admin
from app.models.user import User as UserModel
from app.schemas.bank_account import BankAccountCreate, BankAccountRead
from app.services.bank_account_service import (
    approve_bank_account,
    create_bank_account,
    get_approved_bank_accounts_for_user,
    get_pending_bank_accounts,
    reject_bank_account,
)
from app.services.user_service import get_user_by_bale_id

router = APIRouter(prefix="/bank-accounts", tags=["bank-accounts"])


@router.post("/submit", response_model=BankAccountRead)
async def submit_bank_account(
    bale_user_id: int,
    payload: BankAccountCreate,
    db: AsyncSession = Depends(get_db),
) -> BankAccountRead:
    user = await get_user_by_bale_id(db, bale_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    account = await create_bank_account(
        db, user.id, payload.sheba_number, payload.card_number, payload.account_holder_name
    )
    return BankAccountRead.model_validate(account)


@router.get("/user/{bale_user_id}", response_model=list[BankAccountRead])
async def list_user_bank_accounts(
    bale_user_id: int, db: AsyncSession = Depends(get_db)
) -> list[BankAccountRead]:
    user = await get_user_by_bale_id(db, bale_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    accounts = await get_approved_bank_accounts_for_user(db, user.id)
    return [BankAccountRead.model_validate(a) for a in accounts]


@router.get("/pending", response_model=list[BankAccountRead])
async def list_pending_bank_accounts(
    db: AsyncSession = Depends(get_db),
    _admin: UserModel = Depends(require_admin),
) -> list[BankAccountRead]:
    accounts = await get_pending_bank_accounts(db)
    return [BankAccountRead.model_validate(a) for a in accounts]


@router.post("/{account_id}/approve", response_model=BankAccountRead)
async def approve_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: UserModel = Depends(require_admin),
) -> BankAccountRead:
    account = await approve_bank_account(db, account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return BankAccountRead.model_validate(account)


@router.post("/{account_id}/reject", response_model=BankAccountRead)
async def reject_account(
    account_id: int,
    rejection_reason_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: UserModel = Depends(require_admin),
) -> BankAccountRead:
    account = await reject_bank_account(db, account_id, rejection_reason_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return BankAccountRead.model_validate(account)
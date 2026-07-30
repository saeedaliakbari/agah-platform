from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.bank_account import BankAccountRead
from app.schemas.withdrawal import MatchedWithdrawal, WithdrawalRequestRead
from app.services.bank_account_service import get_bank_account_by_id
from app.services.user_service import get_user_by_bale_id,get_user_by_id
from app.services.withdrawal_service import (
    create_withdrawal_request,
    find_matching_withdrawals,
    reserve_withdrawal_amounts,
    release_withdrawal_amount,
)
from app.schemas.user import UserRead
from app.models.withdrawal_request import WithdrawalRequest as WithdrawalRequestModel

router = APIRouter(prefix="/withdrawal", tags=["withdrawal"])


@router.post("/submit", response_model=WithdrawalRequestRead)
async def submit_withdrawal(
    bale_user_id: int,
    bank_account_id: int,
    amount: float,
    db: AsyncSession = Depends(get_db),
) -> WithdrawalRequestRead:
    user = await get_user_by_bale_id(db, bale_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    withdrawal = await create_withdrawal_request(db, user.id, bank_account_id, amount)
    if not withdrawal:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance or invalid request"
        )
    return WithdrawalRequestRead.model_validate(withdrawal)


@router.get("/match", response_model=list[MatchedWithdrawal])
async def get_matches(amount: float, db: AsyncSession = Depends(get_db)) -> list[MatchedWithdrawal]:
    """با گرفتن مبلغ شارژ، لیست حساب‌های بانکی تطبیق‌یافته را برمی‌گرداند (بدون رزرو کردن)."""
    matches = await find_matching_withdrawals(db, amount)
    if not matches:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No matching withdrawal requests found"
        )

    result = []
    for withdrawal, amount_to_pay in matches:
        bank_account = await get_bank_account_by_id(db, withdrawal.bank_account_id)
        result.append(
            MatchedWithdrawal(
                withdrawal_request_id=withdrawal.id,
                amount_to_pay=amount_to_pay,
                bank_account=BankAccountRead.model_validate(bank_account),
            )
        )
    return result


@router.post("/reserve", response_model=list[MatchedWithdrawal])
async def reserve_matches(amount: float, db: AsyncSession = Depends(get_db)) -> list[MatchedWithdrawal]:
    """تطبیق را پیدا کرده و بلافاصله رزرو می‌کند (برای جلوگیری از تخصیص دوباره)."""
    matches = await find_matching_withdrawals(db, amount)
    if not matches:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No matching withdrawal requests found"
        )

    await reserve_withdrawal_amounts(db, matches)

    result = []
    for withdrawal, amount_to_pay in matches:
        bank_account = await get_bank_account_by_id(db, withdrawal.bank_account_id)
        result.append(
            MatchedWithdrawal(
                withdrawal_request_id=withdrawal.id,
                amount_to_pay=amount_to_pay,
                bank_account=BankAccountRead.model_validate(bank_account),
            )
        )
    return result

@router.post("/{withdrawal_request_id}/release")
async def release_amount(
    withdrawal_request_id: int,
    amount: float,
    db: AsyncSession = Depends(get_db),
) -> dict:
    await release_withdrawal_amount(db, withdrawal_request_id, amount)
    return {"ok": True}

@router.get("/{withdrawal_request_id}/owner", response_model=UserRead)
async def get_withdrawal_owner(
    withdrawal_request_id: int, db: AsyncSession = Depends(get_db)
) -> UserRead:
    withdrawal = await db.get(WithdrawalRequestModel, withdrawal_request_id)
    if not withdrawal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Withdrawal not found")

    user = await get_user_by_id(db, withdrawal.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserRead.model_validate(user)
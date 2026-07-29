from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import require_admin
from app.models.user import User as UserModel
from app.schemas.wallet import WalletBalanceRead, WalletTransactionRead
from app.services.bale_notification_service import edit_channel_caption, send_bale_message
from app.services.user_service import get_user_by_bale_id, get_user_by_id
from app.services.verification_service import get_active_rejection_reasons
from app.services.wallet_service import (
    approve_deposit_request,
    create_deposit_request,
    get_pending_deposit_requests,
    get_user_transactions,
    reject_deposit_request,
)

router = APIRouter(prefix="/wallet", tags=["wallet"])
settings = get_settings()


@router.post("/deposit/submit", response_model=WalletTransactionRead)
async def submit_deposit(
    bale_user_id: int,
    amount: float,
    receipt_bale_file_id: str,
    bale_channel_message_id: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> WalletTransactionRead:
    user = await get_user_by_bale_id(db, bale_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    transaction = await create_deposit_request(
        db, user.id, amount, receipt_bale_file_id, bale_channel_message_id
    )
    return WalletTransactionRead.model_validate(transaction)


@router.get("/balance/{bale_user_id}", response_model=WalletBalanceRead)
async def get_balance(bale_user_id: int, db: AsyncSession = Depends(get_db)) -> WalletBalanceRead:
    user = await get_user_by_bale_id(db, bale_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return WalletBalanceRead(balance=float(user.wallet_balance))


@router.get("/transactions/{bale_user_id}", response_model=list[WalletTransactionRead])
async def get_transactions(
    bale_user_id: int, db: AsyncSession = Depends(get_db)
) -> list[WalletTransactionRead]:
    user = await get_user_by_bale_id(db, bale_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    transactions = await get_user_transactions(db, user.id)
    return [WalletTransactionRead.model_validate(t) for t in transactions]


@router.get("/deposit/pending", response_model=list[WalletTransactionRead])
async def list_pending_deposits(
    db: AsyncSession = Depends(get_db),
    _admin: UserModel = Depends(require_admin),
) -> list[WalletTransactionRead]:
    transactions = await get_pending_deposit_requests(db)
    return [WalletTransactionRead.model_validate(t) for t in transactions]


@router.post("/deposit/{transaction_id}/approve", response_model=WalletTransactionRead)
async def approve_deposit(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    admin: UserModel = Depends(require_admin),
) -> WalletTransactionRead:
    transaction = await approve_deposit_request(db, transaction_id, admin.id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found or already reviewed",
        )

    user = await get_user_by_id(db, transaction.user_id)
    if user and user.bale_user_id:
        await send_bale_message(
            user.bale_user_id,
            f"✅ واریز شما به مبلغ {transaction.amount:,.0f} تومان تایید و به کیف پول اضافه شد.",
        )

    if transaction.bale_channel_message_id:
        caption = (
            f"💰 درخواست شارژ کیف پول\n\n"
            f"👤 نام: {user.full_name if user else 'نامشخص'}\n"
            f"🆔 آیدی بله: {user.bale_user_id if user else 'نامشخص'}\n"
            f"💵 مبلغ: {transaction.amount:,.0f} تومان\n"
            f"📋 وضعیت: تایید شد ✅"
        )
        await edit_channel_caption(
            settings.wallet_channel_id, transaction.bale_channel_message_id, caption
        )

    return WalletTransactionRead.model_validate(transaction)


@router.post("/deposit/{transaction_id}/reject", response_model=WalletTransactionRead)
async def reject_deposit(
    transaction_id: int,
    rejection_reason_id: int,
    db: AsyncSession = Depends(get_db),
    admin: UserModel = Depends(require_admin),
) -> WalletTransactionRead:
    transaction = await reject_deposit_request(db, transaction_id, admin.id, rejection_reason_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found or already reviewed",
        )

    user = await get_user_by_id(db, transaction.user_id)
    reasons = await get_active_rejection_reasons(db)
    reason_text = next((r.text for r in reasons if r.id == rejection_reason_id), "دلیل نامشخص")

    if user and user.bale_user_id:
        await send_bale_message(
            user.bale_user_id,
            f"❌ واریز شما به مبلغ {transaction.amount:,.0f} تومان رد شد.\nدلیل: {reason_text}",
        )

    if transaction.bale_channel_message_id:
        caption = (
            f"💰 درخواست شارژ کیف پول\n\n"
            f"👤 نام: {user.full_name if user else 'نامشخص'}\n"
            f"🆔 آیدی بله: {user.bale_user_id if user else 'نامشخص'}\n"
            f"💵 مبلغ: {transaction.amount:,.0f} تومان\n"
            f"📋 وضعیت: رد شد ❌\n"
            f"دلیل: {reason_text}"
        )
        await edit_channel_caption(
            settings.wallet_channel_id, transaction.bale_channel_message_id, caption
        )

    return WalletTransactionRead.model_validate(transaction)
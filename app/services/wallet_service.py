from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.wallet_transaction import TransactionStatus, TransactionType, WalletTransaction


async def create_deposit_request(
    db: AsyncSession,
    user_id: int,
    amount: float,
    receipt_bale_file_id: str,
    transfer_method: str | None = None,
    bale_channel_message_id: int | None = None,
) -> WalletTransaction:
    transaction = WalletTransaction(
        user_id=user_id,
        type=TransactionType.DEPOSIT,
        amount=amount,
        receipt_bale_file_id=receipt_bale_file_id,
        transfer_method=transfer_method,
        bale_channel_message_id=bale_channel_message_id,
        status=TransactionStatus.PENDING,
    )
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    return transaction


async def get_pending_deposit_requests(db: AsyncSession) -> list[WalletTransaction]:
    result = await db.execute(
        select(WalletTransaction).where(
            WalletTransaction.type == TransactionType.DEPOSIT,
            WalletTransaction.status == TransactionStatus.PENDING,
        )
    )
    return list(result.scalars().all())


async def approve_deposit_request(
    db: AsyncSession, transaction_id: int, admin_id: int
) -> WalletTransaction | None:
    transaction = await db.get(WalletTransaction, transaction_id)
    if not transaction or transaction.status != TransactionStatus.PENDING:
        return None

    transaction.status = TransactionStatus.APPROVED
    transaction.reviewed_by_admin_id = admin_id
    transaction.reviewed_at = datetime.now(timezone.utc)

    user = await db.get(User, transaction.user_id)
    if user:
        user.wallet_balance = float(user.wallet_balance) + float(transaction.amount)

    await db.commit()
    await db.refresh(transaction)
    return transaction


async def reject_deposit_request(
    db: AsyncSession, transaction_id: int, admin_id: int, rejection_reason_id: int
) -> WalletTransaction | None:
    transaction = await db.get(WalletTransaction, transaction_id)
    if not transaction or transaction.status != TransactionStatus.PENDING:
        return None

    transaction.status = TransactionStatus.REJECTED
    transaction.rejection_reason_id = rejection_reason_id
    transaction.reviewed_by_admin_id = admin_id
    transaction.reviewed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(transaction)
    return transaction


async def get_user_transactions(db: AsyncSession, user_id: int) -> list[WalletTransaction]:
    result = await db.execute(
        select(WalletTransaction)
        .where(WalletTransaction.user_id == user_id)
        .order_by(WalletTransaction.created_at.desc())
    )
    return list(result.scalars().all())
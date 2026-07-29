from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bank_account import BankAccount, BankAccountStatus
from app.services.sheba_service import detect_bank_name


async def create_bank_account(
    db: AsyncSession, user_id: int, sheba_number: str, card_number: str | None, account_holder_name: str
) -> BankAccount:
    account = BankAccount(
        user_id=user_id,
        sheba_number=sheba_number,
        card_number=card_number,
        bank_name=detect_bank_name(sheba_number),
        account_holder_name=account_holder_name,
        status=BankAccountStatus.PENDING,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def get_approved_bank_accounts_for_user(db: AsyncSession, user_id: int) -> list[BankAccount]:
    result = await db.execute(
        select(BankAccount).where(
            BankAccount.user_id == user_id, BankAccount.status == BankAccountStatus.APPROVED
        )
    )
    return list(result.scalars().all())


async def get_pending_bank_accounts(db: AsyncSession) -> list[BankAccount]:
    result = await db.execute(
        select(BankAccount).where(BankAccount.status == BankAccountStatus.PENDING)
    )
    return list(result.scalars().all())


async def approve_bank_account(db: AsyncSession, account_id: int) -> BankAccount | None:
    account = await db.get(BankAccount, account_id)
    if not account or account.status != BankAccountStatus.PENDING:
        return None

    account.status = BankAccountStatus.APPROVED
    await db.commit()
    await db.refresh(account)
    return account


async def reject_bank_account(db: AsyncSession, account_id: int, rejection_reason_id: int) -> BankAccount | None:
    account = await db.get(BankAccount, account_id)
    if not account or account.status != BankAccountStatus.PENDING:
        return None

    account.status = BankAccountStatus.REJECTED
    account.rejection_reason_id = rejection_reason_id
    await db.commit()
    await db.refresh(account)
    return account


async def get_bank_account_by_id(db: AsyncSession, account_id: int) -> BankAccount | None:
    return await db.get(BankAccount, account_id)
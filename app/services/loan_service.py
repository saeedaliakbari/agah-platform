from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.loan_account import LoanAccount
from app.models.loan_rate import LoanRate
from app.models.loan_request import LoanActionType, LoanRequest, LoanRequestStatus


async def create_loan_account(
    db: AsyncSession,
    user_id: int,
    bank_type: str,
    national_id: str,
    full_name: str,
    phone_number: str,
    account_number: str,
) -> LoanAccount:
    existing = await get_loan_account(db, user_id, bank_type)
    if existing:
        existing.national_id = national_id
        existing.full_name = full_name
        existing.phone_number = phone_number
        existing.account_number = account_number
        await db.commit()
        await db.refresh(existing)
        return existing

    account = LoanAccount(
        user_id=user_id,
        bank_type=bank_type,
        national_id=national_id,
        full_name=full_name,
        phone_number=phone_number,
        account_number=account_number,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def get_loan_account(db: AsyncSession, user_id: int, bank_type: str) -> LoanAccount | None:
    result = await db.execute(
        select(LoanAccount).where(
            LoanAccount.user_id == user_id, LoanAccount.bank_type == bank_type
        )
    )
    return result.scalar_one_or_none()


async def get_loan_rate(db: AsyncSession, bank_type: str, action_type: str) -> LoanRate | None:
    result = await db.execute(
        select(LoanRate).where(
            LoanRate.bank_type == bank_type, LoanRate.action_type == action_type
        )
    )
    return result.scalar_one_or_none()


async def create_loan_request(
    db: AsyncSession,
    user_id: int,
    bank_type: str,
    action_type: LoanActionType,
    point_type: str,
    amount: float,
    recipient_is_self: bool = True,
    recipient_national_id: str | None = None,
    recipient_full_name: str | None = None,
    recipient_phone_number: str | None = None,
    recipient_account_number: str | None = None,
) -> LoanRequest | None:
    rate = await get_loan_rate(db, bank_type, action_type.value)
    if not rate:
        return None

    final_amount = (amount / 1_000_000) * float(rate.rate_per_million) + float(rate.commission)

    request = LoanRequest(
        user_id=user_id,
        bank_type=bank_type,
        action_type=action_type,
        point_type=point_type,
        amount=amount,
        installment_months=rate.installment_months,
        rate_per_million=rate.rate_per_million,
        commission=rate.commission,
        final_amount=final_amount,
        recipient_is_self=recipient_is_self,
        recipient_national_id=recipient_national_id,
        recipient_full_name=recipient_full_name,
        recipient_phone_number=recipient_phone_number,
        recipient_account_number=recipient_account_number,
        status=LoanRequestStatus.PENDING,
    )
    db.add(request)
    await db.commit()
    await db.refresh(request)
    return request


async def get_waiting_list(db: AsyncSession, bank_type: str, action_type: str) -> list[LoanRequest]:
    result = await db.execute(
        select(LoanRequest)
        .where(
            LoanRequest.bank_type == bank_type,
            LoanRequest.action_type == action_type,
            LoanRequest.status == LoanRequestStatus.PENDING,
        )
        .order_by(LoanRequest.created_at.asc())
    )
    return list(result.scalars().all())


async def get_user_loan_requests(db: AsyncSession, user_id: int) -> list[LoanRequest]:
    result = await db.execute(
        select(LoanRequest)
        .where(LoanRequest.user_id == user_id)
        .order_by(LoanRequest.created_at.desc())
    )
    return list(result.scalars().all())


async def complete_loan_request(db: AsyncSession, request_id: int, user_id: int) -> LoanRequest | None:
    """فقط خود کاربر صاحب درخواست می‌تواند آن را تکمیل‌شده علامت بزند."""
    request = await db.get(LoanRequest, request_id)
    if not request or request.user_id != user_id or request.status != LoanRequestStatus.PENDING:
        return None

    request.status = LoanRequestStatus.COMPLETED
    request.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(request)
    return request


async def cancel_loan_request(db: AsyncSession, request_id: int, admin_id: int) -> LoanRequest | None:
    """فقط ادمین می‌تواند یک معامله را لغو کند."""
    request = await db.get(LoanRequest, request_id)
    if not request or request.status != LoanRequestStatus.PENDING:
        return None

    request.status = LoanRequestStatus.CANCELLED
    request.cancelled_by_admin_id = admin_id
    await db.commit()
    await db.refresh(request)
    return request
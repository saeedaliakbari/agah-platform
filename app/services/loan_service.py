from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.loan_account import LoanAccount
from app.models.loan_rate import LoanRate
from app.models.loan_request import LoanActionType, LoanRequest, LoanRequestStatus
STANDARD_LOAN_AMOUNTS = {
    5_000_000: "پنج_میلیون",
    10_000_000: "ده_میلیون",
    20_000_000: "بیست_میلیون",
    50_000_000: "پنجاه_میلیون",
    100_000_000: "یکصد_میلیون",
}


async def get_headline_prices(db: AsyncSession, bank_type: str, action_type: str) -> list[dict]:
    """برای هر مبلغ استاندارد، بهترین قیمت (کمترین برای فروش، بیشترین برای خرید) را برمی‌گرداند."""
    requests = await get_waiting_list(db, bank_type, action_type)

    headlines = []
    for amount, label in STANDARD_LOAN_AMOUNTS.items():
        matching = [r for r in requests if float(r.amount) == amount]
        if not matching:
            continue

        if action_type == "sell":
            best = min(matching, key=lambda r: float(r.rate_per_million))
        else:
            best = max(matching, key=lambda r: float(r.rate_per_million))

        rate = float(best.rate_per_million)
        total = (amount / 1_000_000) * rate
        headlines.append({"label": label, "rate_per_million": rate, "total": total})

    headlines.sort(key=lambda h: h["rate_per_million"])
    return headlines


async def get_bucket_counts(db: AsyncSession, bank_type: str, action_type: str) -> dict:
    """تعداد درخواست‌های در انتظار برای هر باکت مبلغ (استاندارد + آزاد، آزاد به تفکیک نوع امتیاز)."""
    requests = await get_waiting_list(db, bank_type, action_type)

    counts = {label: 0 for label in STANDARD_LOAN_AMOUNTS.values()}
    custom_real = 0
    custom_legal = 0

    for r in requests:
        amount = float(r.amount)
        if amount in STANDARD_LOAN_AMOUNTS:
            counts[STANDARD_LOAN_AMOUNTS[amount]] += 1
        elif r.point_type.value == "real":
            custom_real += 1
        else:
            custom_legal += 1

    counts["مقدار_آزاد"] = custom_real
    counts["مقدار_آزاد_حقوقی"] = custom_legal
    return counts

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
    rate_per_million: float,
    recipient_is_self: bool = True,
    recipient_national_id: str | None = None,
    recipient_full_name: str | None = None,
    recipient_phone_number: str | None = None,
    recipient_account_number: str | None = None,
) -> LoanRequest | None:
    rate = await get_loan_rate(db, bank_type, action_type.value)
    if not rate:
        return None

    final_amount = (amount / 1_000_000) * rate_per_million + float(rate.commission)

    request = LoanRequest(
        user_id=user_id,
        bank_type=bank_type,
        action_type=action_type,
        point_type=point_type,
        amount=amount,
        installment_months=rate.installment_months,
        rate_per_million=rate_per_million,
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
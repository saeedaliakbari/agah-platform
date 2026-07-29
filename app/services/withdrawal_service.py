from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bank_account import BankAccount
from app.models.user import User
from app.models.withdrawal_request import WithdrawalRequest, WithdrawalStatus


async def create_withdrawal_request(
    db: AsyncSession, user_id: int, bank_account_id: int, amount: float
) -> WithdrawalRequest | None:
    user = await db.get(User, user_id)
    if not user or float(user.wallet_balance) < amount:
        return None

    withdrawal = WithdrawalRequest(
        user_id=user_id,
        bank_account_id=bank_account_id,
        amount=amount,
        remaining_amount=amount,
        status=WithdrawalStatus.PENDING,
    )
    db.add(withdrawal)

    # مبلغ فوراً از موجودی کم می‌شود (رزرو) تا برداشت مضاعف رخ ندهد
    user.wallet_balance = float(user.wallet_balance) - amount

    await db.commit()
    await db.refresh(withdrawal)
    return withdrawal


async def find_matching_withdrawals(
    db: AsyncSession, deposit_amount: float
) -> list[tuple[WithdrawalRequest, float]]:
    """
    الگوریتم تطبیق:
    1. اگر حداقل یک درخواست با remaining_amount <= deposit_amount وجود دارد،
       از قدیمی‌ترین شروع کن و جمع بزن تا مبلغ پوشش داده شود.
    2. در غیر این صورت (هیچ درخواستی به‌تنهایی کافی نیست)، نزدیک‌ترین
       (کمترین) مبلغ را انتخاب کن (تسویه‌ی جزئی).
    """
    result = await db.execute(
        select(WithdrawalRequest)
        .where(
            WithdrawalRequest.status.in_(
                [WithdrawalStatus.PENDING, WithdrawalStatus.PARTIALLY_SETTLED]
            ),
            WithdrawalRequest.remaining_amount > 0,
        )
        .order_by(WithdrawalRequest.created_at.asc())
    )
    pending = list(result.scalars().all())

    if not pending:
        return []

    # حالت ۱: حداقل یکی با مبلغ <= deposit_amount هست
    eligible = [w for w in pending if float(w.remaining_amount) <= deposit_amount]

    if eligible:
        matches: list[tuple[WithdrawalRequest, float]] = []
        remaining_to_cover = deposit_amount
        for withdrawal in eligible:
            if remaining_to_cover <= 0:
                break
            amount_to_pay = min(float(withdrawal.remaining_amount), remaining_to_cover)
            matches.append((withdrawal, amount_to_pay))
            remaining_to_cover -= amount_to_pay

        if remaining_to_cover > 0:
            # مبلغ eligible ها کافی نبود، از بقیه (بزرگ‌تر از deposit) هم اضافه کن
            others = [w for w in pending if w not in [m[0] for m in matches]]
            others.sort(key=lambda w: float(w.remaining_amount))
            for withdrawal in others:
                if remaining_to_cover <= 0:
                    break
                amount_to_pay = min(float(withdrawal.remaining_amount), remaining_to_cover)
                matches.append((withdrawal, amount_to_pay))
                remaining_to_cover -= amount_to_pay

        return matches

    # حالت ۲: هیچ‌کدام به‌تنهایی کافی نیست -> نزدیک‌ترین (کمترین مبلغ) را انتخاب کن
    closest = min(pending, key=lambda w: float(w.remaining_amount))
    return [(closest, deposit_amount)]


async def reserve_withdrawal_amounts(
    db: AsyncSession, matches: list[tuple[WithdrawalRequest, float]]
) -> None:
    """مبلغ تطبیق‌یافته را از remaining_amount هر درخواست کم می‌کند (رزرو موقت)."""
    for withdrawal, amount in matches:
        withdrawal.remaining_amount = float(withdrawal.remaining_amount) - amount
        if withdrawal.remaining_amount <= 0:
            withdrawal.status = WithdrawalStatus.SETTLED
        else:
            withdrawal.status = WithdrawalStatus.PARTIALLY_SETTLED
    await db.commit()


async def release_withdrawal_amount(db: AsyncSession, withdrawal_id: int, amount: float) -> None:
    """اگر واریز رد شد، مبلغ رزروشده به درخواست برداشت برمی‌گردد."""
    withdrawal = await db.get(WithdrawalRequest, withdrawal_id)
    if withdrawal:
        withdrawal.remaining_amount = float(withdrawal.remaining_amount) + amount
        withdrawal.status = (
            WithdrawalStatus.PENDING
            if withdrawal.remaining_amount >= float(withdrawal.amount)
            else WithdrawalStatus.PARTIALLY_SETTLED
        )
        await db.commit()
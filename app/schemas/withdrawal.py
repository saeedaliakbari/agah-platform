from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.models.withdrawal_request import WithdrawalStatus
from app.schemas.bank_account import BankAccountRead


class WithdrawalRequestCreate(BaseModel):
    bank_account_id: int
    amount: float


class WithdrawalRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    bank_account_id: int
    amount: float
    remaining_amount: float
    status: WithdrawalStatus
    created_at: datetime


class MatchedWithdrawal(BaseModel):
    """یک درخواست برداشت که با شارژ فعلی تطبیق داده شده، همراه با مبلغ اختصاص‌یافته."""

    withdrawal_request_id: int
    amount_to_pay: float
    bank_account: BankAccountRead
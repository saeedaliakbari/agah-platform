from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.loan_request import LoanActionType, LoanPointType, LoanRequestStatus


class LoanAccountCreate(BaseModel):
    bank_type: str
    national_id: str
    full_name: str
    phone_number: str
    account_number: str


class LoanAccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bank_type: str
    national_id: str
    full_name: str
    phone_number: str
    account_number: str


class LoanRateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bank_type: str
    action_type: str
    installment_months: int
    rate_per_million: float
    commission: float


class LoanRequestCreate(BaseModel):
    bank_type: str
    action_type: LoanActionType
    point_type: LoanPointType
    amount: float
    recipient_is_self: bool = True
    recipient_national_id: str | None = None
    recipient_full_name: str | None = None
    recipient_phone_number: str | None = None
    recipient_account_number: str | None = None


class LoanRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    bank_type: str
    action_type: LoanActionType
    point_type: LoanPointType
    amount: float
    installment_months: int
    rate_per_million: float
    commission: float
    final_amount: float
    recipient_is_self: bool
    status: LoanRequestStatus
    created_at: datetime
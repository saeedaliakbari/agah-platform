from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.bank_account import BankAccountStatus


class BankAccountCreate(BaseModel):
    sheba_number: str
    card_number: str | None = None
    account_holder_name: str


class BankAccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sheba_number: str
    card_number: str | None
    bank_name: str
    account_holder_name: str
    status: BankAccountStatus
    created_at: datetime
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.wallet_transaction import TransactionStatus, TransactionType


class WalletTransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    type: TransactionType
    amount: float
    transfer_method: str | None
    status: TransactionStatus
    rejection_reason_id: int | None
    created_at: datetime
    reviewed_at: datetime | None


class WalletBalanceRead(BaseModel):
    balance: float
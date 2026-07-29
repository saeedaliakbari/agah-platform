import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WithdrawalStatus(str, enum.Enum):
    PENDING = "pending"
    PARTIALLY_SETTLED = "partially_settled"
    SETTLED = "settled"
    REJECTED = "rejected"


class WithdrawalRequest(Base):
    __tablename__ = "withdrawal_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    remaining_amount: Mapped[float] = mapped_column(Numeric(12, 2))

    card_number: Mapped[str] = mapped_column(String(32))
    sheba_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    bank_name: Mapped[str] = mapped_column(String(64))
    account_holder_name: Mapped[str] = mapped_column(String(255))

    status: Mapped[WithdrawalStatus] = mapped_column(
        Enum(WithdrawalStatus), default=WithdrawalStatus.PENDING
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
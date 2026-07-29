import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BankAccountStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    sheba_number: Mapped[str] = mapped_column(String(32))
    card_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    bank_name: Mapped[str] = mapped_column(String(64))
    account_holder_name: Mapped[str] = mapped_column(String(255))

    status: Mapped[BankAccountStatus] = mapped_column(
        Enum(BankAccountStatus), default=BankAccountStatus.PENDING
    )
    rejection_reason_id: Mapped[int | None] = mapped_column(
        ForeignKey("rejection_reasons.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
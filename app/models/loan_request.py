import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LoanActionType(str, enum.Enum):
    SELL = "sell"
    BUY = "buy"


class LoanPointType(str, enum.Enum):
    REAL = "real"  # حقیقی
    LEGAL = "legal"  # حقوقی


class LoanRequestStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class LoanRequest(Base):
    __tablename__ = "loan_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    bank_type: Mapped[str] = mapped_column(String(32))
    action_type: Mapped[LoanActionType] = mapped_column(Enum(LoanActionType))
    point_type: Mapped[LoanPointType] = mapped_column(Enum(LoanPointType))

    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    installment_months: Mapped[int] = mapped_column()
    rate_per_million: Mapped[float] = mapped_column(Numeric(12, 2))
    commission: Mapped[float] = mapped_column(Numeric(12, 2))
    final_amount: Mapped[float] = mapped_column(Numeric(12, 2))

    # فقط برای «خرید»: آیا وام برای خود کاربر است یا شخص دیگر
    recipient_is_self: Mapped[bool] = mapped_column(default=True)
    recipient_national_id: Mapped[str | None] = mapped_column(String(16), nullable=True)
    recipient_full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recipient_phone_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    recipient_account_number: Mapped[str | None] = mapped_column(String(64), nullable=True)

    status: Mapped[LoanRequestStatus] = mapped_column(
        Enum(LoanRequestStatus), default=LoanRequestStatus.PENDING
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
from sqlalchemy import Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LoanRate(Base):
    __tablename__ = "loan_rates"

    id: Mapped[int] = mapped_column(primary_key=True)

    bank_type: Mapped[str] = mapped_column(String(32))
    action_type: Mapped[str] = mapped_column(String(8))  # "sell" یا "buy"

    installment_months: Mapped[int] = mapped_column(Integer)
    rate_per_million: Mapped[float] = mapped_column(Numeric(12, 2))
    commission: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
import enum
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    # کاربر بله (مشتری) - از طریق ربات یا مینی‌اپ شناسایی میشه
    bale_user_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)

    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # فقط برای ادمین‌ها پر میشه
    username: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)

    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.CUSTOMER)
    is_active: Mapped[bool] = mapped_column(default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
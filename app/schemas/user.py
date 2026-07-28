from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.user import UserRole


class UserBase(BaseModel):
    full_name: str | None = None
    phone_number: str | None = None


class UserCreate(UserBase):
    username: str | None = None
    password: str | None = None
    bale_user_id: int | None = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bale_user_id: int | None = None
    bale_username: str | None = None
    role: UserRole
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.verification_request import VerificationStatus


class RejectionReasonBase(BaseModel):
    text: str


class RejectionReasonCreate(RejectionReasonBase):
    pass


class RejectionReasonRead(RejectionReasonBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool


class VerificationRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: VerificationStatus
    rejection_reason_id: int | None
    created_at: datetime
    reviewed_at: datetime | None
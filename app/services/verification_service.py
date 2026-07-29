from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rejection_reason import RejectionReason
from app.models.user import User
from app.models.verification_request import VerificationRequest, VerificationStatus


async def create_verification_request(
    db: AsyncSession, user_id: int, bale_file_id: str, bale_channel_message_id: int | None = None
) -> VerificationRequest:
    request = VerificationRequest(
        user_id=user_id,
        bale_file_id=bale_file_id,
        bale_channel_message_id=bale_channel_message_id,
        status=VerificationStatus.PENDING,
    )
    db.add(request)

    user = await db.get(User, user_id)
    if user:
        user.verification_status = VerificationStatus.PENDING

    await db.commit()
    await db.refresh(request)
    return request


async def get_pending_verification_requests(db: AsyncSession) -> list[VerificationRequest]:
    result = await db.execute(
        select(VerificationRequest).where(VerificationRequest.status == VerificationStatus.PENDING)
    )
    return list(result.scalars().all())


async def approve_verification_request(
    db: AsyncSession, request_id: int, admin_id: int
) -> VerificationRequest | None:
    request = await db.get(VerificationRequest, request_id)
    if not request:
        return None

    request.status = VerificationStatus.APPROVED
    request.reviewed_by_admin_id = admin_id
    request.reviewed_at = datetime.now(timezone.utc)

    user = await db.get(User, request.user_id)
    if user:
        user.verification_status = VerificationStatus.APPROVED

    await db.commit()
    await db.refresh(request)
    return request


async def reject_verification_request(
    db: AsyncSession, request_id: int, admin_id: int, rejection_reason_id: int
) -> VerificationRequest | None:
    request = await db.get(VerificationRequest, request_id)
    if not request:
        return None

    request.status = VerificationStatus.REJECTED
    request.rejection_reason_id = rejection_reason_id
    request.reviewed_by_admin_id = admin_id
    request.reviewed_at = datetime.now(timezone.utc)

    user = await db.get(User, request.user_id)
    if user:
        user.verification_status = VerificationStatus.REJECTED

    await db.commit()
    await db.refresh(request)
    return request


async def create_rejection_reason(db: AsyncSession, text: str) -> RejectionReason:
    reason = RejectionReason(text=text)
    db.add(reason)
    await db.commit()
    await db.refresh(reason)
    return reason


async def get_active_rejection_reasons(db: AsyncSession) -> list[RejectionReason]:
    result = await db.execute(select(RejectionReason).where(RejectionReason.is_active == True))  # noqa: E712
    return list(result.scalars().all())


async def update_rejection_reason(db: AsyncSession, reason_id: int, text: str) -> RejectionReason | None:
    reason = await db.get(RejectionReason, reason_id)
    if not reason:
        return None
    reason.text = text
    await db.commit()
    await db.refresh(reason)
    return reason


async def deactivate_rejection_reason(db: AsyncSession, reason_id: int) -> RejectionReason | None:
    reason = await db.get(RejectionReason, reason_id)
    if not reason:
        return None
    reason.is_active = False
    await db.commit()
    await db.refresh(reason)
    return reason
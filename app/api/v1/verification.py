from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.services.bale_notification_service import edit_channel_caption, send_bale_message
from app.core.database import get_db
from app.core.deps import require_admin
from app.models.user import User as UserModel
from app.schemas.verification import (
    RejectionReasonCreate,
    RejectionReasonRead,
    VerificationRequestRead,
)
from app.services.user_service import get_user_by_bale_id, get_user_by_id
from app.services.verification_service import (
    approve_verification_request,
    create_rejection_reason,
    create_verification_request,
    deactivate_rejection_reason,
    get_active_rejection_reasons,
    get_pending_verification_requests,
    reject_verification_request,
    update_rejection_reason,
)
settings = get_settings()
router = APIRouter(prefix="/verification", tags=["verification"])


@router.post("/submit", response_model=VerificationRequestRead)
async def submit_verification(
    bale_user_id: int,
    bale_file_id: str,
    bale_channel_message_id: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> VerificationRequestRead:
    user = await get_user_by_bale_id(db, bale_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    request = await create_verification_request(
        db, user.id, bale_file_id, bale_channel_message_id
    )
    return VerificationRequestRead.model_validate(request)

@router.get("/pending", response_model=list[VerificationRequestRead])
async def list_pending_verifications(
    db: AsyncSession = Depends(get_db),
    _admin: UserModel = Depends(require_admin),
) -> list[VerificationRequestRead]:
    requests = await get_pending_verification_requests(db)
    return [VerificationRequestRead.model_validate(r) for r in requests]


@router.post("/{request_id}/approve", response_model=VerificationRequestRead)
async def approve_verification(
    request_id: int,
    db: AsyncSession = Depends(get_db),
    admin: UserModel = Depends(require_admin),
) -> VerificationRequestRead:
    request = await approve_verification_request(db, request_id, admin.id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    user = await get_user_by_id(db, request.user_id)
    if user and user.bale_user_id:
        await send_bale_message(
            user.bale_user_id,
            "✅ احراز هویت شما با موفقیت تایید شد.",
        )

    if request.bale_channel_message_id:
        caption = (
            f"🪪 درخواست احراز هویت\n\n"
            f"👤 نام: {user.full_name if user else 'نامشخص'}\n"
            f"🔖 یوزرنیم: @{user.bale_username if user and user.bale_username else 'ثبت نشده'}\n"
            f"🆔 آیدی بله: {user.bale_user_id if user else 'نامشخص'}\n"
            f"📞 شماره تماس: {user.phone_number if user and user.phone_number else 'ثبت نشده'}\n"
            f"📋 وضعیت: تایید شد ✅"
        )
        await edit_channel_caption(
            settings.verification_channel_id, request.bale_channel_message_id, caption
        )

    return VerificationRequestRead.model_validate(request)


@router.post("/{request_id}/reject", response_model=VerificationRequestRead)
async def reject_verification(
    request_id: int,
    rejection_reason_id: int,
    db: AsyncSession = Depends(get_db),
    admin: UserModel = Depends(require_admin),
) -> VerificationRequestRead:
    request = await reject_verification_request(db, request_id, admin.id, rejection_reason_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    user = await get_user_by_id(db, request.user_id)
    reasons = await get_active_rejection_reasons(db)
    reason_text = next(
        (r.text for r in reasons if r.id == rejection_reason_id), "دلیل نامشخص"
    )

    if user and user.bale_user_id:
        await send_bale_message(
            user.bale_user_id,
            f"❌ احراز هویت شما رد شد.\nدلیل: {reason_text}\n\nلطفاً مجدداً مدرک خود را ارسال کنید.",
        )

    if request.bale_channel_message_id:
        caption = (
            f"🪪 درخواست احراز هویت\n\n"
            f"👤 نام: {user.full_name if user else 'نامشخص'}\n"
            f"🔖 یوزرنیم: @{user.bale_username if user and user.bale_username else 'ثبت نشده'}\n"
            f"🆔 آیدی بله: {user.bale_user_id if user else 'نامشخص'}\n"
            f"📞 شماره تماس: {user.phone_number if user and user.phone_number else 'ثبت نشده'}\n"
            f"📋 وضعیت: رد شد ❌\n"
            f"دلیل: {reason_text}"
        )
        await edit_channel_caption(
            settings.verification_channel_id, request.bale_channel_message_id, caption
        )

    return VerificationRequestRead.model_validate(request)

@router.post("/rejection-reasons", response_model=RejectionReasonRead)
async def create_reason(
    payload: RejectionReasonCreate,
    db: AsyncSession = Depends(get_db),
    _admin: UserModel = Depends(require_admin),
) -> RejectionReasonRead:
    reason = await create_rejection_reason(db, payload.text)
    return RejectionReasonRead.model_validate(reason)


@router.get("/rejection-reasons", response_model=list[RejectionReasonRead])
async def list_reasons(
    db: AsyncSession = Depends(get_db),
    _admin: UserModel = Depends(require_admin),
) -> list[RejectionReasonRead]:
    reasons = await get_active_rejection_reasons(db)
    return [RejectionReasonRead.model_validate(r) for r in reasons]


@router.put("/rejection-reasons/{reason_id}", response_model=RejectionReasonRead)
async def edit_reason(
    reason_id: int,
    payload: RejectionReasonCreate,
    db: AsyncSession = Depends(get_db),
    _admin: UserModel = Depends(require_admin),
) -> RejectionReasonRead:
    reason = await update_rejection_reason(db, reason_id, payload.text)
    if not reason:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reason not found")
    return RejectionReasonRead.model_validate(reason)


@router.delete("/rejection-reasons/{reason_id}", response_model=RejectionReasonRead)
async def delete_reason(
    reason_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: UserModel = Depends(require_admin),
) -> RejectionReasonRead:
    reason = await deactivate_rejection_reason(db, reason_id)
    if not reason:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reason not found")
    return RejectionReasonRead.model_validate(reason)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.user import UserRead
from app.services.user_service import get_or_create_bale_user, get_user_by_bale_id, update_phone_number,get_all_customers
from app.core.deps import require_admin
from app.models.user import User as UserModel

router = APIRouter(prefix="/users", tags=["users"])
from app.services.user_service import (
    count_referrals,
    get_or_create_referral_code,
    set_referrer,
)

@router.post("/bale/identify", response_model=UserRead)
async def identify_bale_user(
    bale_user_id: int,
    full_name: str | None = None,
    bale_username: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    user = await get_or_create_bale_user(db, bale_user_id, full_name, bale_username)
    return UserRead.model_validate(user)


@router.get("/bale/{bale_user_id}", response_model=UserRead)
async def get_bale_user_profile(
    bale_user_id: int,
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    user = await get_user_by_bale_id(db, bale_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserRead.model_validate(user)

@router.patch("/bale/{bale_user_id}/phone", response_model=UserRead)
async def update_bale_user_phone(
    bale_user_id: int,
    phone_number: str,
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    user = await update_phone_number(db, bale_user_id, phone_number)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserRead.model_validate(user)

@router.get("/", response_model=list[UserRead])
async def list_customers(
    db: AsyncSession = Depends(get_db),
    _admin: UserModel = Depends(require_admin),
) -> list[UserRead]:
    users = await get_all_customers(db)
    return [UserRead.model_validate(u) for u in users]

@router.get("/bale/{bale_user_id}/referral")
async def get_referral_info(
    bale_user_id: int, db: AsyncSession = Depends(get_db)
) -> dict:
    user = await get_user_by_bale_id(db, bale_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    code = await get_or_create_referral_code(db, user)
    count = await count_referrals(db, user.id)
    return {"referral_code": code, "referral_count": count}


@router.post("/bale/{bale_user_id}/set-referrer")
async def set_user_referrer(
    bale_user_id: int, referral_code: str, db: AsyncSession = Depends(get_db)
) -> dict:
    user = await get_user_by_bale_id(db, bale_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    success = await set_referrer(db, user, referral_code)
    return {"success": success}
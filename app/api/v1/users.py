from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.user import UserRead
from app.services.user_service import get_or_create_bale_user, get_user_by_bale_id

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/bale/identify", response_model=UserRead)
async def identify_bale_user(
    bale_user_id: int,
    full_name: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    user = await get_or_create_bale_user(db, bale_user_id, full_name)
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
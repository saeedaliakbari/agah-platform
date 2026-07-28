from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.user import UserRead
from app.services.user_service import get_or_create_bale_user
from app.core.deps import require_admin
from app.models.user import User as UserModel

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/bale/identify", response_model=UserRead)
async def identify_bale_user(
    bale_user_id: int,
    full_name: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    user = await get_or_create_bale_user(db, bale_user_id, full_name)
    return user

@router.get("/me", response_model=UserRead)
async def read_current_admin(current_user: UserModel = Depends(require_admin)) -> UserRead:
    return current_user
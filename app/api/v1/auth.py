from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, verify_password
from app.services.user_service import get_user_by_username

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/admin/login")
async def admin_login(
    username: str,
    password: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    user = await get_user_by_username(db, username)

    if not user or not user.hashed_password or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(subject=str(user.id), extra_claims={"role": user.role.value})
    return {"access_token": token, "token_type": "bearer"}
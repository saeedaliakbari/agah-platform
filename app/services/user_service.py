from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


async def get_user_by_bale_id(db: AsyncSession, bale_user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.bale_user_id == bale_user_id))
    return result.scalar_one_or_none()


async def get_or_create_bale_user(
    db: AsyncSession, bale_user_id: int, full_name: str | None
) -> User:
    user = await get_user_by_bale_id(db, bale_user_id)
    if user:
        return user

    user = User(bale_user_id=bale_user_id, full_name=full_name, role=UserRole.CUSTOMER)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
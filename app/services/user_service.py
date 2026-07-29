from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole

from app.core.security import hash_password

async def get_user_by_bale_id(db: AsyncSession, bale_user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.bale_user_id == bale_user_id))
    return result.scalar_one_or_none()


async def get_or_create_bale_user(
    db: AsyncSession, bale_user_id: int, full_name: str | None, bale_username: str | None = None
) -> User:
    """Used by the bot / mini-app: find an existing customer or create one on first contact."""
    user = await get_user_by_bale_id(db, bale_user_id)
    if user:
        # اگه یوزرنیم بله تغییر کرده باشه (کاربر تو بله عوضش کرده)، بروزش می‌کنیم
        if bale_username and user.bale_username != bale_username:
            user.bale_username = bale_username
            await db.commit()
            await db.refresh(user)
        return user

    user = User(
        bale_user_id=bale_user_id,
        full_name=full_name,
        bale_username=bale_username,
        role=UserRole.CUSTOMER,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def create_admin_user(db: AsyncSession, username: str, password: str) -> User:
    user = User(
        username=username,
        hashed_password=hash_password(password),
        role=UserRole.ADMIN,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def update_phone_number(db: AsyncSession, bale_user_id: int, phone_number: str) -> User | None:
    user = await get_user_by_bale_id(db, bale_user_id)
    if not user:
        return None

    user.phone_number = phone_number
    await db.commit()
    await db.refresh(user)
    return user
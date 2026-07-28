import asyncio

from app.core.database import AsyncSessionLocal
from app.services.user_service import create_admin_user


async def main() -> None:
    username = input("Username: ")
    password = input("Password: ")

    async with AsyncSessionLocal() as db:
        user = await create_admin_user(db, username, password)
        print(f"Admin created: id={user.id}, username={user.username}")


if __name__ == "__main__":
    asyncio.run(main())
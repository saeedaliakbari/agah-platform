import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.database import Base, get_db
from app.main import app

settings = get_settings()

test_engine = create_async_engine(settings.test_database_url)
TestSessionLocal = async_sessionmaker(bind=test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """قبل از هر تست، جدول‌ها رو از صفر می‌سازه؛ بعدش پاک می‌کنه."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
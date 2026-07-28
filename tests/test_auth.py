import pytest

from app.services.user_service import create_admin_user


@pytest.mark.asyncio
async def test_login_with_correct_credentials(client, db_session):
    await create_admin_user(db_session, username="testadmin", password="testpass123")

    response = await client.post(
        "/api/v1/auth/admin/login",
        data={"username": "testadmin", "password": "testpass123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_with_wrong_password(client, db_session):
    await create_admin_user(db_session, username="testadmin", password="testpass123")

    response = await client.post(
        "/api/v1/auth/admin/login",
        data={"username": "testadmin", "password": "wrongpassword"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_with_nonexistent_user(client):
    response = await client.post(
        "/api/v1/auth/admin/login",
        data={"username": "doesnotexist", "password": "whatever"},
    )

    assert response.status_code == 401
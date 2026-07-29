import pytest

from app.services.user_service import create_admin_user, get_or_create_bale_user
from app.services.verification_service import create_rejection_reason


@pytest.mark.asyncio
async def test_submit_verification_request(client, db_session):
    await get_or_create_bale_user(db_session, bale_user_id=111, full_name="Test User")

    response = await client.post(
        "/api/v1/verification/submit",
        params={"bale_user_id": 111, "bale_file_id": "fake_file_id_123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending"


@pytest.mark.asyncio
async def test_submit_verification_for_nonexistent_user(client):
    response = await client.post(
        "/api/v1/verification/submit",
        params={"bale_user_id": 999999, "bale_file_id": "fake_file_id"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_pending_requires_admin(client, db_session):
    await get_or_create_bale_user(db_session, bale_user_id=222, full_name="Test User 2")
    await client.post(
        "/api/v1/verification/submit",
        params={"bale_user_id": 222, "bale_file_id": "fake_file_id_456"},
    )

    # بدون لاگین ادمین، باید رد بشه
    response = await client.get("/api/v1/verification/pending")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_can_approve_verification(client, db_session):
    await create_admin_user(db_session, username="testadmin", password="testpass123")
    await get_or_create_bale_user(db_session, bale_user_id=333, full_name="Test User 3")

    submit_response = await client.post(
        "/api/v1/verification/submit",
        params={"bale_user_id": 333, "bale_file_id": "fake_file_id_789"},
    )
    request_id = submit_response.json()["id"]

    login_response = await client.post(
        "/api/v1/auth/admin/login",
        data={"username": "testadmin", "password": "testpass123"},
    )
    token = login_response.json()["access_token"]

    approve_response = await client.post(
        f"/api/v1/verification/{request_id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"


@pytest.mark.asyncio
async def test_admin_can_reject_with_reason(client, db_session):
    await create_admin_user(db_session, username="testadmin2", password="testpass123")
    await get_or_create_bale_user(db_session, bale_user_id=444, full_name="Test User 4")
    reason = await create_rejection_reason(db_session, "عکس نامشخص است")

    submit_response = await client.post(
        "/api/v1/verification/submit",
        params={"bale_user_id": 444, "bale_file_id": "fake_file_id_000"},
    )
    request_id = submit_response.json()["id"]

    login_response = await client.post(
        "/api/v1/auth/admin/login",
        data={"username": "testadmin2", "password": "testpass123"},
    )
    token = login_response.json()["access_token"]

    reject_response = await client.post(
        f"/api/v1/verification/{request_id}/reject",
        params={"rejection_reason_id": reason.id},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert reject_response.status_code == 200
    body = reject_response.json()
    assert body["status"] == "rejected"
    assert body["rejection_reason_id"] == reason.id
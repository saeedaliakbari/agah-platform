import pytest

from app.services.user_service import create_admin_user, get_or_create_bale_user
from app.services.verification_service import create_rejection_reason


@pytest.mark.asyncio
async def test_submit_deposit_request(client, db_session):
    await get_or_create_bale_user(db_session, bale_user_id=555, full_name="Wallet Test User")

    response = await client.post(
        "/api/v1/wallet/deposit/submit",
        params={
            "bale_user_id": 555,
            "amount": 100000,
            "receipt_bale_file_id": "fake_receipt_id",
            "transfer_method": "کارت به کارت",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending"
    assert body["amount"] == 100000
    assert body["transfer_method"] == "کارت به کارت"


@pytest.mark.asyncio
async def test_submit_deposit_for_nonexistent_user(client):
    response = await client.post(
        "/api/v1/wallet/deposit/submit",
        params={
            "bale_user_id": 999998,
            "amount": 50000,
            "receipt_bale_file_id": "fake_receipt_id",
        },
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_balance_starts_at_zero(client, db_session):
    await get_or_create_bale_user(db_session, bale_user_id=666, full_name="Balance Test User")

    response = await client.get("/api/v1/wallet/balance/666")

    assert response.status_code == 200
    assert response.json()["balance"] == 0.0


@pytest.mark.asyncio
async def test_approve_deposit_increases_balance(client, db_session):
    await create_admin_user(db_session, username="wallettest_admin", password="testpass123")
    await get_or_create_bale_user(db_session, bale_user_id=777, full_name="Approve Test User")

    submit_response = await client.post(
        "/api/v1/wallet/deposit/submit",
        params={
            "bale_user_id": 777,
            "amount": 200000,
            "receipt_bale_file_id": "fake_receipt_id_2",
        },
    )
    transaction_id = submit_response.json()["id"]

    login_response = await client.post(
        "/api/v1/auth/admin/login",
        data={"username": "wallettest_admin", "password": "testpass123"},
    )
    token = login_response.json()["access_token"]

    approve_response = await client.post(
        f"/api/v1/wallet/deposit/{transaction_id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "approved"

    balance_response = await client.get("/api/v1/wallet/balance/777")
    assert balance_response.json()["balance"] == 200000


@pytest.mark.asyncio
async def test_reject_deposit_does_not_change_balance(client, db_session):
    await create_admin_user(db_session, username="wallettest_admin2", password="testpass123")
    await get_or_create_bale_user(db_session, bale_user_id=888, full_name="Reject Test User")
    reason = await create_rejection_reason(db_session, "رسید نامعتبر است")

    submit_response = await client.post(
        "/api/v1/wallet/deposit/submit",
        params={
            "bale_user_id": 888,
            "amount": 150000,
            "receipt_bale_file_id": "fake_receipt_id_3",
        },
    )
    transaction_id = submit_response.json()["id"]

    login_response = await client.post(
        "/api/v1/auth/admin/login",
        data={"username": "wallettest_admin2", "password": "testpass123"},
    )
    token = login_response.json()["access_token"]

    reject_response = await client.post(
        f"/api/v1/wallet/deposit/{transaction_id}/reject",
        params={"rejection_reason_id": reason.id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == "rejected"

    balance_response = await client.get("/api/v1/wallet/balance/888")
    assert balance_response.json()["balance"] == 0.0


@pytest.mark.asyncio
async def test_cannot_approve_same_transaction_twice(client, db_session):
    await create_admin_user(db_session, username="wallettest_admin3", password="testpass123")
    await get_or_create_bale_user(db_session, bale_user_id=999, full_name="Double Approve Test")

    submit_response = await client.post(
        "/api/v1/wallet/deposit/submit",
        params={
            "bale_user_id": 999,
            "amount": 100000,
            "receipt_bale_file_id": "fake_receipt_id_4",
        },
    )
    transaction_id = submit_response.json()["id"]

    login_response = await client.post(
        "/api/v1/auth/admin/login",
        data={"username": "wallettest_admin3", "password": "testpass123"},
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    first_approve = await client.post(
        f"/api/v1/wallet/deposit/{transaction_id}/approve", headers=headers
    )
    assert first_approve.status_code == 200

    second_approve = await client.post(
        f"/api/v1/wallet/deposit/{transaction_id}/approve", headers=headers
    )
    assert second_approve.status_code == 404

    balance_response = await client.get("/api/v1/wallet/balance/999")
    assert balance_response.json()["balance"] == 100000  # نه 200000!


@pytest.mark.asyncio
async def test_get_transaction_history(client, db_session):
    await get_or_create_bale_user(db_session, bale_user_id=1010, full_name="History Test User")

    await client.post(
        "/api/v1/wallet/deposit/submit",
        params={
            "bale_user_id": 1010,
            "amount": 75000,
            "receipt_bale_file_id": "fake_receipt_id_5",
            "transfer_method": "پایا",
        },
    )

    response = await client.get("/api/v1/wallet/transactions/1010")

    assert response.status_code == 200
    transactions = response.json()
    assert len(transactions) == 1
    assert transactions[0]["amount"] == 75000
    assert transactions[0]["transfer_method"] == "پایا"
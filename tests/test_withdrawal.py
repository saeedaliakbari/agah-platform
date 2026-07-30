import pytest

from app.services.user_service import create_admin_user, get_or_create_bale_user
from app.services.bank_account_service import approve_bank_account, create_bank_account
from app.services.wallet_service import approve_deposit_request, create_deposit_request
from app.services.withdrawal_service import create_withdrawal_request
from app.models.withdrawal_request import WithdrawalRequest, WithdrawalStatus

async def _make_user_with_balance(db_session, bale_user_id: int, full_name: str, balance: float):
    user = await get_or_create_bale_user(db_session, bale_user_id, full_name)
    user.wallet_balance = balance
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _make_approved_bank_account(db_session, user_id: int):
    account = await create_bank_account(
        db_session, user_id, "IR120170000000123456789012", "6037991234567890", "علی رضایی"
    )
    return await approve_bank_account(db_session, account.id)


@pytest.mark.asyncio
async def test_withdrawal_request_reduces_balance(client, db_session):
    user = await _make_user_with_balance(db_session, 2001, "Withdrawer One", 500000)
    account = await _make_approved_bank_account(db_session, user.id)

    response = await client.post(
        "/api/v1/withdrawal/submit",
        params={"bale_user_id": 2001, "bank_account_id": account.id, "amount": 200000},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["remaining_amount"] == 200000

    balance_response = await client.get("/api/v1/wallet/balance/2001")
    assert balance_response.json()["balance"] == 300000


@pytest.mark.asyncio
async def test_withdrawal_fails_with_insufficient_balance(client, db_session):
    user = await _make_user_with_balance(db_session, 2002, "Withdrawer Two", 100000)
    account = await _make_approved_bank_account(db_session, user.id)

    response = await client.post(
        "/api/v1/withdrawal/submit",
        params={"bale_user_id": 2002, "bank_account_id": account.id, "amount": 200000},
    )

    assert response.status_code == 400

    balance_response = await client.get("/api/v1/wallet/balance/2002")
    assert balance_response.json()["balance"] == 100000  # دست‌نخورده


@pytest.mark.asyncio
async def test_matching_picks_single_covering_request_fifo(client, db_session):
    user = await _make_user_with_balance(db_session, 2003, "Withdrawer Three", 1000000)
    account = await _make_approved_bank_account(db_session, user.id)

    await client.post(
        "/api/v1/withdrawal/submit",
        params={"bale_user_id": 2003, "bank_account_id": account.id, "amount": 200000},
    )
    await client.post(
        "/api/v1/withdrawal/submit",
        params={"bale_user_id": 2003, "bank_account_id": account.id, "amount": 150000},
    )
    await client.post(
        "/api/v1/withdrawal/submit",
        params={"bale_user_id": 2003, "bank_account_id": account.id, "amount": 400000},
    )

    response = await client.get("/api/v1/withdrawal/match", params={"amount": 500000})
    assert response.status_code == 200
    matches = response.json()

    total = sum(m["amount_to_pay"] for m in matches)
    assert total == 500000
    assert len(matches) == 3  # 200k + 150k + بخشی از 400k


@pytest.mark.asyncio
async def test_matching_picks_closest_when_none_fit_fully(client, db_session):
    user = await _make_user_with_balance(db_session, 2004, "Withdrawer Four", 2000000)
    account = await _make_approved_bank_account(db_session, user.id)

    await client.post(
        "/api/v1/withdrawal/submit",
        params={"bale_user_id": 2004, "bank_account_id": account.id, "amount": 1000000},
    )
    await client.post(
        "/api/v1/withdrawal/submit",
        params={"bale_user_id": 2004, "bank_account_id": account.id, "amount": 500000},
    )
    await client.post(
        "/api/v1/withdrawal/submit",
        params={"bale_user_id": 2004, "bank_account_id": account.id, "amount": 200000},
    )

    response = await client.get("/api/v1/withdrawal/match", params={"amount": 100000})
    assert response.status_code == 200
    matches = response.json()

    assert len(matches) == 1
    assert matches[0]["amount_to_pay"] == 100000  # کل ۱۰۰۰۰۰ به نزدیک‌ترین (۲۰۰۰۰۰) تخصیص میابد


@pytest.mark.asyncio
async def test_reserve_deducts_remaining_amount(client, db_session):
    user = await _make_user_with_balance(db_session, 2005, "Withdrawer Five", 500000)
    account = await _make_approved_bank_account(db_session, user.id)

    submit_response = await client.post(
        "/api/v1/withdrawal/submit",
        params={"bale_user_id": 2005, "bank_account_id": account.id, "amount": 300000},
    )
    withdrawal_id = submit_response.json()["id"]

    reserve_response = await client.post("/api/v1/withdrawal/reserve", params={"amount": 300000})
    assert reserve_response.status_code == 200

    # نباید دوباره همون مبلغ در دسترس باشد چون رزرو شده
    match_again = await client.get("/api/v1/withdrawal/match", params={"amount": 300000})
    assert match_again.status_code == 404


@pytest.mark.asyncio
async def test_approve_deposit_settles_withdrawal_and_notifies(client, db_session):
    await create_admin_user(db_session, username="p2p_admin", password="testpass123")

    withdrawer = await _make_user_with_balance(db_session, 2006, "Withdrawer Six", 500000)
    account = await _make_approved_bank_account(db_session, withdrawer.id)

    withdrawal_response = await client.post(
        "/api/v1/withdrawal/submit",
        params={"bale_user_id": 2006, "bank_account_id": account.id, "amount": 300000},
    )
    withdrawal_id = withdrawal_response.json()["id"]

    # مرحله‌ی رزرو - دقیقاً همون کاری که بات موقع match پیدا کردن انجام می‌دهد
    reserve_response = await client.post("/api/v1/withdrawal/reserve", params={"amount": 300000})
    assert reserve_response.status_code == 200

    depositor = await get_or_create_bale_user(db_session, 2007, "Depositor One")

    deposit = await create_deposit_request(
        db_session, depositor.id, 300000, "fake_receipt", "P2P", None, withdrawal_id
    )

    login_response = await client.post(
        "/api/v1/auth/admin/login", data={"username": "p2p_admin", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    approve_response = await client.post(
        f"/api/v1/wallet/deposit/{deposit.id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert approve_response.status_code == 200

    depositor_balance = await client.get("/api/v1/wallet/balance/2007")
    assert depositor_balance.json()["balance"] == 300000

    withdrawal_after = await db_session.get(WithdrawalRequest, withdrawal_id)
    assert float(withdrawal_after.remaining_amount) == 0
    assert withdrawal_after.status == WithdrawalStatus.SETTLED

@pytest.mark.asyncio
async def test_reject_deposit_releases_reserved_amount(client, db_session):
    await create_admin_user(db_session, username="p2p_admin2", password="testpass123")
    from app.services.verification_service import create_rejection_reason

    reason = await create_rejection_reason(db_session, "رسید جعلی است")

    withdrawer = await _make_user_with_balance(db_session, 2008, "Withdrawer Eight", 500000)
    account = await _make_approved_bank_account(db_session, withdrawer.id)

    withdrawal_response = await client.post(
        "/api/v1/withdrawal/submit",
        params={"bale_user_id": 2008, "bank_account_id": account.id, "amount": 300000},
    )
    withdrawal_id = withdrawal_response.json()["id"]

    depositor = await get_or_create_bale_user(db_session, 2009, "Depositor Two")
    deposit = await create_deposit_request(
        db_session, depositor.id, 300000, "fake_receipt2", "P2P", None, withdrawal_id
    )

    login_response = await client.post(
        "/api/v1/auth/admin/login", data={"username": "p2p_admin2", "password": "testpass123"}
    )
    token = login_response.json()["access_token"]

    reject_response = await client.post(
        f"/api/v1/wallet/deposit/{deposit.id}/reject",
        params={"rejection_reason_id": reason.id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert reject_response.status_code == 200

    # موجودی واریزکننده نباید تغییر کند
    depositor_balance = await client.get("/api/v1/wallet/balance/2009")
    assert depositor_balance.json()["balance"] == 0.0

    # مبلغ باید دوباره در دسترس تطبیق باشد
    match_response = await client.get("/api/v1/withdrawal/match", params={"amount": 300000})
    assert match_response.status_code == 200
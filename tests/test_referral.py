import pytest

from app.services.user_service import get_or_create_bale_user


@pytest.mark.asyncio
async def test_get_referral_info_generates_code(client, db_session):
    await get_or_create_bale_user(db_session, 3001, "Referrer User")

    response = await client.get("/api/v1/users/bale/3001/referral")

    assert response.status_code == 200
    body = response.json()
    assert body["referral_code"] is not None
    assert len(body["referral_code"]) == 8
    assert body["referral_count"] == 0


@pytest.mark.asyncio
async def test_referral_code_is_stable_across_calls(client, db_session):
    await get_or_create_bale_user(db_session, 3002, "Stable Code User")

    first_response = await client.get("/api/v1/users/bale/3002/referral")
    second_response = await client.get("/api/v1/users/bale/3002/referral")

    assert first_response.json()["referral_code"] == second_response.json()["referral_code"]


@pytest.mark.asyncio
async def test_set_referrer_increases_referrer_count(client, db_session):
    await get_or_create_bale_user(db_session, 3003, "Referrer Two")
    await get_or_create_bale_user(db_session, 3004, "Referred User")

    referral_response = await client.get("/api/v1/users/bale/3003/referral")
    code = referral_response.json()["referral_code"]

    set_response = await client.post(
        "/api/v1/users/bale/3004/set-referrer", params={"referral_code": code}
    )
    assert set_response.status_code == 200
    assert set_response.json()["success"] is True

    updated_referral = await client.get("/api/v1/users/bale/3003/referral")
    assert updated_referral.json()["referral_count"] == 1


@pytest.mark.asyncio
async def test_cannot_set_referrer_twice(client, db_session):
    await get_or_create_bale_user(db_session, 3005, "Referrer Three")
    await get_or_create_bale_user(db_session, 3006, "Referrer Four")
    await get_or_create_bale_user(db_session, 3007, "Referred Twice User")

    referral_a = await client.get("/api/v1/users/bale/3005/referral")
    referral_b = await client.get("/api/v1/users/bale/3006/referral")

    first_set = await client.post(
        "/api/v1/users/bale/3007/set-referrer",
        params={"referral_code": referral_a.json()["referral_code"]},
    )
    assert first_set.json()["success"] is True

    second_set = await client.post(
        "/api/v1/users/bale/3007/set-referrer",
        params={"referral_code": referral_b.json()["referral_code"]},
    )
    assert second_set.json()["success"] is False

    # همچنان فقط اولین معرف باید شمرده شود
    updated_a = await client.get("/api/v1/users/bale/3005/referral")
    updated_b = await client.get("/api/v1/users/bale/3006/referral")
    assert updated_a.json()["referral_count"] == 1
    assert updated_b.json()["referral_count"] == 0


@pytest.mark.asyncio
async def test_invalid_referral_code_fails(client, db_session):
    await get_or_create_bale_user(db_session, 3008, "Invalid Code User")

    response = await client.post(
        "/api/v1/users/bale/3008/set-referrer", params={"referral_code": "NONEXIST"}
    )

    assert response.status_code == 200
    assert response.json()["success"] is False


@pytest.mark.asyncio
async def test_cannot_refer_self(client, db_session):
    await get_or_create_bale_user(db_session, 3009, "Self Referrer")

    referral_info = await client.get("/api/v1/users/bale/3009/referral")
    code = referral_info.json()["referral_code"]

    response = await client.post(
        "/api/v1/users/bale/3009/set-referrer", params={"referral_code": code}
    )

    assert response.json()["success"] is False
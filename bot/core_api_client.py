import httpx


class CoreApiClient:

    def __init__(self, base_url: str) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=10)

    async def identify_user(
        self, bale_user_id: int, full_name: str | None, bale_username: str | None = None
    ) -> dict:
        response = await self._client.post(
            "/api/v1/users/bale/identify",
            params={
                "bale_user_id": bale_user_id,
                "full_name": full_name,
                "bale_username": bale_username,
            },
        )
        response.raise_for_status()
        return response.json()

    
    async def get_user_profile(self, bale_user_id: int) -> dict | None:
        response = await self._client.get(f"/api/v1/users/bale/{bale_user_id}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
            await self._client.aclose()

    async def update_phone_number(self, bale_user_id: int, phone_number: str) -> dict:
        response = await self._client.patch(
            f"/api/v1/users/bale/{bale_user_id}/phone",
            params={"phone_number": phone_number},
        )
        response.raise_for_status()
        return response.json()
        
    async def submit_verification(
        self, bale_user_id: int, bale_file_id: str, bale_channel_message_id: int | None = None
    ) -> dict:
        response = await self._client.post(
            "/api/v1/verification/submit",
            params={
                "bale_user_id": bale_user_id,
                "bale_file_id": bale_file_id,
                "bale_channel_message_id": bale_channel_message_id,
            },
        )
        response.raise_for_status()
        return response.json()
    
    async def get_balance(self, bale_user_id: int) -> dict:
        response = await self._client.get(f"/api/v1/wallet/balance/{bale_user_id}")
        response.raise_for_status()
        return response.json()

    async def get_transactions(self, bale_user_id: int) -> list[dict]:
        response = await self._client.get(f"/api/v1/wallet/transactions/{bale_user_id}")
        response.raise_for_status()
        return response.json()

    async def submit_deposit(
        self,
        bale_user_id: int,
        amount: float,
        receipt_bale_file_id: str,
        transfer_method: str | None = None,
        bale_channel_message_id: int | None = None,
        withdrawal_request_id: int | None = None,
    ) -> dict:
        response = await self._client.post(
            "/api/v1/wallet/deposit/submit",
            params={
                "bale_user_id": bale_user_id,
                "amount": amount,
                "receipt_bale_file_id": receipt_bale_file_id,
                "transfer_method": transfer_method,
                "bale_channel_message_id": bale_channel_message_id,
                "withdrawal_request_id": withdrawal_request_id,
            },
        )
        response.raise_for_status()
        return response.json()

    async def submit_bank_account(
        self, bale_user_id: int, sheba_number: str, card_number: str | None, account_holder_name: str
    ) -> dict:
        response = await self._client.post(
            "/api/v1/bank-accounts/submit",
            params={"bale_user_id": bale_user_id},
            json={
                "sheba_number": sheba_number,
                "card_number": card_number,
                "account_holder_name": account_holder_name,
            },
        )
        response.raise_for_status()
        return response.json()

    async def get_user_bank_accounts(self, bale_user_id: int) -> list[dict]:
        response = await self._client.get(f"/api/v1/bank-accounts/user/{bale_user_id}")
        response.raise_for_status()
        return response.json()

    async def submit_withdrawal(self, bale_user_id: int, bank_account_id: int, amount: float) -> dict | None:
        response = await self._client.post(
            "/api/v1/withdrawal/submit",
            params={"bale_user_id": bale_user_id, "bank_account_id": bank_account_id, "amount": amount},
        )
        if response.status_code == 400:
            return None
        response.raise_for_status()
        return response.json()

    async def reserve_withdrawal_matches(self, amount: float) -> list[dict]:
        response = await self._client.post(
            "/api/v1/withdrawal/reserve", params={"amount": amount}
        )
        if response.status_code == 404:
            return []
        response.raise_for_status()
        return response.json()

    async def release_withdrawal_amount(self, withdrawal_request_id: int, amount: float) -> None:
        response = await self._client.post(
            f"/api/v1/withdrawal/{withdrawal_request_id}/release", params={"amount": amount}
        )
        response.raise_for_status()

    async def get_user_profile_by_withdrawal(self, withdrawal_request_id: int) -> dict | None:
        response = await self._client.get(
            f"/api/v1/withdrawal/{withdrawal_request_id}/owner"
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    async def set_referrer(self, bale_user_id: int, referral_code: str) -> dict:
        response = await self._client.post(
            f"/api/v1/users/bale/{bale_user_id}/set-referrer",
            params={"referral_code": referral_code},
        )
        response.raise_for_status()
        return response.json()

    async def get_referral_info(self, bale_user_id: int) -> dict:
        response = await self._client.get(f"/api/v1/users/bale/{bale_user_id}/referral")
        response.raise_for_status()
        return response.json()

    async def submit_loan_account(
        self, bale_user_id: int, bank_type: str, national_id: str,
        full_name: str, phone_number: str, account_number: str,
    ) -> dict:
        response = await self._client.post(
            "/api/v1/loans/account/submit",
            params={"bale_user_id": bale_user_id},
            json={
                "bank_type": bank_type,
                "national_id": national_id,
                "full_name": full_name,
                "phone_number": phone_number,
                "account_number": account_number,
            },
        )
        response.raise_for_status()
        return response.json()

    async def get_loan_account(self, bale_user_id: int, bank_type: str) -> dict | None:
        response = await self._client.get(f"/api/v1/loans/account/{bale_user_id}/{bank_type}")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    async def get_loan_rate(self, bank_type: str, action_type: str) -> dict:
        response = await self._client.get(f"/api/v1/loans/rate/{bank_type}/{action_type}")
        response.raise_for_status()
        return response.json()

    async def submit_loan_request(
        self, bale_user_id: int, bank_type: str, action_type: str, point_type: str,
        amount: float, rate_per_million: float, recipient_is_self: bool = True,
        recipient_national_id: str | None = None, recipient_full_name: str | None = None,
        recipient_phone_number: str | None = None, recipient_account_number: str | None = None,
    ) -> dict:
        response = await self._client.post(
            "/api/v1/loans/request/submit",
            params={"bale_user_id": bale_user_id},
            json={
                "bank_type": bank_type,
                "action_type": action_type,
                "point_type": point_type,
                "amount": amount,
                "rate_per_million": rate_per_million,
                "recipient_is_self": recipient_is_self,
                "recipient_national_id": recipient_national_id,
                "recipient_full_name": recipient_full_name,
                "recipient_phone_number": recipient_phone_number,
                "recipient_account_number": recipient_account_number,
            },
        )
        response.raise_for_status()
        return response.json()
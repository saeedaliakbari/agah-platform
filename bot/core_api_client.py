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
    ) -> dict:
        response = await self._client.post(
            "/api/v1/wallet/deposit/submit",
            params={
                "bale_user_id": bale_user_id,
                "amount": amount,
                "receipt_bale_file_id": receipt_bale_file_id,
                "transfer_method": transfer_method,
                "bale_channel_message_id": bale_channel_message_id,
            },
        )
        response.raise_for_status()
        return response.json()
import httpx


class CoreApiClient:

    def __init__(self, base_url: str) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=10)

    async def identify_user(self, bale_user_id: int, full_name: str | None) -> dict:
        response = await self._client.post(
            "/api/v1/users/bale/identify",
            params={"bale_user_id": bale_user_id, "full_name": full_name},
        )
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()
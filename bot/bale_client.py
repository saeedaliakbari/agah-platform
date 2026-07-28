import httpx


class BaleClient:
    def __init__(self, token: str) -> None:
        self._base_url = f"https://tapi.bale.ai/bot{token}"
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=10)

    async def send_message(self, chat_id: int, text: str) -> dict:
        response = await self._client.post(
            "/sendMessage", json={"chat_id": chat_id, "text": text}
        )
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()
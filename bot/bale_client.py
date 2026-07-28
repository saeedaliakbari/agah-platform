import httpx


class BaleClient:
    """کلاینت ساده برای صحبت با API بله (ارسال پیام و ...)."""

    def __init__(self, token: str) -> None:
        self._base_url = f"https://tapi.bale.ai/bot{token}"
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=10)

    async def send_message(
        self, chat_id: int, text: str, reply_markup: dict | None = None
    ) -> dict:
        payload: dict = {"chat_id": chat_id, "text": text}
        if reply_markup:
            payload["reply_markup"] = reply_markup

        response = await self._client.post("/sendMessage", json=payload)
        response.raise_for_status()
        return response.json()

    async def answer_callback_query(self, callback_query_id: str, text: str = "") -> dict:
        response = await self._client.post(
            "/answerCallbackQuery",
            json={"callback_query_id": callback_query_id, "text": text},
        )
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()
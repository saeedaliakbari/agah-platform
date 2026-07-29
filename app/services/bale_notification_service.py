import httpx

from app.core.config import get_settings

settings = get_settings()


async def send_bale_message(chat_id: int, text: str) -> None:
    """پیام مستقیم به کاربر بله می‌فرستد (برای اطلاع‌رسانی نتیجه‌ی احراز هویت و مشابه)."""
    if not settings.bale_bot_token:
        return

    url = f"https://tapi.bale.ai/bot{settings.bale_bot_token}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.post(url, json={"chat_id": chat_id, "text": text})
            response.raise_for_status()
        except httpx.HTTPError as exc:
            print(f"Failed to notify user {chat_id}: {exc}")
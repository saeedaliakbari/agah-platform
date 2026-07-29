import httpx

from app.core.config import get_settings

settings = get_settings()


def _bale_url(method: str) -> str:
    return f"https://tapi.bale.ai/bot{settings.bale_bot_token}/{method}"


async def send_bale_message(chat_id: int, text: str) -> None:
    """پیام مستقیم به کاربر بله می‌فرستد (برای اطلاع‌رسانی نتیجه‌ی احراز هویت و مشابه)."""
    if not settings.bale_bot_token:
        return

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.post(
                _bale_url("sendMessage"), json={"chat_id": chat_id, "text": text}
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            print(f"Failed to notify user {chat_id}: {exc}")


async def edit_channel_caption(chat_id: int, message_id: int, caption: str) -> None:
    """caption پیام کانال احراز هویت را پس از تایید/رد بروزرسانی می‌کند."""
    if not settings.bale_bot_token:
        return

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.post(
                _bale_url("editMessageCaption"),
                json={"chat_id": chat_id, "message_id": message_id, "caption": caption},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            print(f"Failed to edit channel caption for message {message_id}: {exc}")
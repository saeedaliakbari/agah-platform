import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request

from bale_client import BaleClient
from core_api_client import CoreApiClient

load_dotenv()

BOT_TOKEN = os.getenv("BALE_BOT_TOKEN", "")
CORE_API_URL = os.getenv("CORE_API_URL", "http://localhost:8000")

app = FastAPI(title="Agah Bot Webhook")
bale_client = BaleClient(token=BOT_TOKEN)
core_api = CoreApiClient(base_url=CORE_API_URL)

MENU_LOANS = "💰 وام‌های بانکی"
MENU_CLUB_SERVICES = "🎁 خدمات باشگاه آگاه"
MENU_STOCKS = "📈 معرفی سهام"
MENU_WALLET = "👛 کیف پول"
MENU_PROFILE = "👤 پروفایل"
MENU_INVITE = "🤝 دعوت دوستان"
MENU_ORDER_SEARCH = "🔍 جستجوی سفارش"
MENU_MORE = "⚙️ گزینه‌های بیشتر"


def main_menu_keyboard() -> dict:
    """چیدمان دکمه‌های منوی اصلی (Reply Keyboard - پایین صفحه)."""
    return {
        "keyboard": [
            [{"text": MENU_LOANS}, {"text": MENU_CLUB_SERVICES}],
            [{"text": MENU_STOCKS}, {"text": MENU_WALLET}],
            [{"text": MENU_PROFILE}, {"text": MENU_INVITE}],
            [{"text": MENU_ORDER_SEARCH}, {"text": MENU_MORE}],
        ],
        "resize_keyboard": True,
    }


@app.post("/webhook")
async def handle_update(request: Request) -> dict:
    update = await request.json()

    if "message" in update:
        await handle_message(update["message"])
    elif "callback_query" in update:
        await handle_callback_query(update["callback_query"])

    return {"ok": True}


async def handle_message(message: dict) -> None:
    chat_id = message["chat"]["id"]
    from_user = message.get("from", {})
    text = message.get("text", "")

    user = await core_api.identify_user(
        bale_user_id=from_user.get("id"),
        full_name=from_user.get("first_name"),
    )

    try:
        if text == "/start":
            await bale_client.send_message(
                chat_id,
                f"سلام {user.get('full_name') or ''}! یکی از گزینه‌های زیر رو انتخاب کن:",
                reply_markup=main_menu_keyboard(),
            )
        elif text == MENU_LOANS:
            await bale_client.send_message(chat_id, "بخش وام‌های بانکی (به‌زودی تکمیل می‌شود)")
        elif text == MENU_CLUB_SERVICES:
            await bale_client.send_message(chat_id, "بخش خدمات باشگاه آگاه (به‌زودی تکمیل می‌شود)")
        elif text == MENU_STOCKS:
            await bale_client.send_message(chat_id, "بخش معرفی سهام (به‌زودی تکمیل می‌شود)")
        elif text == MENU_WALLET:
            await bale_client.send_message(chat_id, "بخش کیف پول (به‌زودی تکمیل می‌شود)")
        elif text == MENU_PROFILE:
            await bale_client.send_message(chat_id, "بخش پروفایل (به‌زودی تکمیل می‌شود)")
        elif text == MENU_INVITE:
            await bale_client.send_message(chat_id, "بخش دعوت دوستان (به‌زودی تکمیل می‌شود)")
        elif text == MENU_ORDER_SEARCH:
            await bale_client.send_message(chat_id, "بخش جستجوی سفارش (به‌زودی تکمیل می‌شود)")
        elif text == MENU_MORE:
            await bale_client.send_message(chat_id, "بخش گزینه‌های بیشتر (به‌زودی تکمیل می‌شود)")
    except Exception as exc:
       print(f"Failed to send message to {chat_id}: {type(exc).__name__}: {exc!r}")


async def handle_callback_query(callback_query: dict) -> None:
    callback_id = callback_query["id"]
    chat_id = callback_query["message"]["chat"]["id"]
    data = callback_query.get("data", "")

    try:
        await bale_client.answer_callback_query(callback_id, text="در حال بررسی...")
        await bale_client.send_message(chat_id, f"گزینه‌ی انتخابی: {data}")
    except Exception as exc:
        print(f"Failed to send message to {chat_id}: {type(exc).__name__}: {exc!r}")


@app.on_event("shutdown")
async def shutdown() -> None:
    await bale_client.close()
    await core_api.close()
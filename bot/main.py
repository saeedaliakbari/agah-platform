import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request

from bale_client import BaleClient
from core_api_client import CoreApiClient

from datetime import datetime, timezone
import jdatetime

load_dotenv()

BOT_TOKEN = os.getenv("BALE_BOT_TOKEN", "")
CORE_API_URL = os.getenv("CORE_API_URL", "http://localhost:8000")
VERIFICATION_CHANNEL_ID = int(os.getenv("VERIFICATION_CHANNEL_ID", "0"))
WALLET_CHANNEL_ID = int(os.getenv("WALLET_CHANNEL_ID", "0"))

app = FastAPI(title="Agah Bot Webhook")
bale_client = BaleClient(token=BOT_TOKEN)
core_api = CoreApiClient(base_url=CORE_API_URL)
# حالت مکالمه‌ی هر کاربر (in-memory، ساده - بعداً می‌تونه به Redis منتقل بشه)
user_states: dict[int, dict] = {}

MENU_LOANS = "💰 وام‌های بانکی"
MENU_CLUB_SERVICES = "🎁 خدمات باشگاه آگاه"
MENU_STOCKS = "📈 معرفی سهام"
MENU_WALLET = "👛 کیف پول"
MENU_PROFILE = "👤 پروفایل"
MENU_INVITE = "🤝 دعوت دوستان"
MENU_ORDER_SEARCH = "🔍 جستجوی سفارش"
MENU_MORE = "⚙️ گزینه‌های بیشتر"
MENU_BACK = "🔙 بازگشت"
MENU_DEPOSIT = "💳 واریز وجه"
MENU_TRANSACTIONS = "📜 تاریخچه تراکنش‌ها"

EMOJI_MONEY = "💰"
EMOJI_RECEIPT = "🧾"
EMOJI_CALENDAR = "📅"
EMOJI_ID = "🆔"
EMOJI_USERNAME = "🔖"
EMOJI_NAME = "👤"
EMOJI_PHONE = "📞"
EMOJI_USERNAME_TAG = "🔖"
EMOJI_STATUS = "📋"
EMOJI_DOCUMENT = "🪪"
EMOJI_SUCCESS = "✅"

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

def wallet_submenu_keyboard() -> dict:
    return {
        "keyboard": [
            [{"text": MENU_DEPOSIT}, {"text": MENU_TRANSACTIONS}],
            [{"text": "🔙 بازگشت"}],
        ],
        "resize_keyboard": True,
    }
def transfer_method_keyboard() -> dict:
    return {
        "keyboard": [
            [{"text": "پایا"}, {"text": "پل"}],
            [{"text": "کارت به کارت"}, {"text": "حساب به حساب"}],
            [{"text": "🔙 بازگشت"}],
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

def mask_phone(phone: str | None) -> str:
    if not phone:
        return "ثبت نشده"

    normalized = phone
    if normalized.startswith("98"):
        normalized = "0" + normalized[2:]
    elif normalized.startswith("+98"):
        normalized = "0" + normalized[3:]

    if len(normalized) < 8:
        return "ثبت نشده"

    return f"{normalized[-4:]}***{normalized[:4]}"


def format_join_date(created_at_str: str) -> str:
    created_at = datetime.fromisoformat(created_at_str)
    jalali_date = jdatetime.datetime.fromgregorian(datetime=created_at)
    days_since = (datetime.now(timezone.utc) - created_at).days
    return f"{jalali_date.strftime('%Y/%m/%d')} ( {days_since} روز )"


def profile_submenu_keyboard() -> dict:
    return {
        "keyboard": [
            [{"text": "✏️ ویرایش پروفایل"}, {"text": "🔙 بازگشت"}],
        ],
        "resize_keyboard": True,
    }

def request_contact_keyboard() -> dict:
    return {
        "keyboard": [
            [{"text": "📱 ارسال شماره تماس", "request_contact": True}],
        ],
        "resize_keyboard": True,
    }


async def handle_message(message: dict) -> None:
    chat_id = message["chat"]["id"]
    from_user = message.get("from", {})
    text = message.get("text", "")

    user = await core_api.identify_user(
        bale_user_id=from_user.get("id"),
        full_name=from_user.get("first_name"),
        bale_username=from_user.get("username"),
    )

    try:
        if "photo" in message:
            photo_file_id = message["photo"][-1]["file_id"]
            state = user_states.get(from_user.get("id"))

            if state and state.get("step") == "awaiting_receipt":
                caption = (
                    f"💰 درخواست شارژ کیف پول\n\n"
                    f"{EMOJI_NAME} نام: {user.get('full_name') or 'نامشخص'}\n"
                    f"{EMOJI_ID} آیدی بله: {from_user.get('id')}\n"
                    f"💳 روش انتقال: {state['transfer_method']}\n"
                    f"💵 مبلغ: {state['amount']:,.0f} تومان\n"
                    f"{EMOJI_STATUS} وضعیت: در انتظار بررسی ⏳"
                )
                channel_message = await bale_client.send_photo(
                    WALLET_CHANNEL_ID, photo_file_id, caption=caption
                )
                channel_file_id = channel_message["result"]["photo"][-1]["file_id"]
                channel_message_id = channel_message["result"]["message_id"]

                await core_api.submit_deposit(
                    from_user.get("id"),
                    state["amount"],
                    channel_file_id,
                    state["transfer_method"],
                    channel_message_id,
                )

                del user_states[from_user.get("id")]

                await bale_client.send_message(
                    chat_id,
                    f"{EMOJI_SUCCESS} درخواست واریز شما ثبت شد و در حال بررسی است.",
                    reply_markup=wallet_submenu_keyboard(),
                )
            else:
                # جریان احراز هویت (کد قبلی)
                caption = (
                    f"{EMOJI_DOCUMENT} درخواست احراز هویت جدید\n\n"
                    f"{EMOJI_NAME} نام: {user.get('full_name') or 'نامشخص'}\n"
                    f"{EMOJI_USERNAME_TAG} یوزرنیم: @{user.get('bale_username') or 'ثبت نشده'}\n"
                    f"{EMOJI_ID} آیدی بله: {from_user.get('id')}\n"
                    f"{EMOJI_PHONE} شماره تماس: {user.get('phone_number') or 'ثبت نشده'}\n"
                    f"{EMOJI_STATUS} وضعیت: در انتظار بررسی ⏳"
                )
                channel_message = await bale_client.send_photo(
                    VERIFICATION_CHANNEL_ID, photo_file_id, caption=caption
                )
                channel_file_id = channel_message["result"]["photo"][-1]["file_id"]
                channel_message_id = channel_message["result"]["message_id"]

                await core_api.submit_verification(
                    from_user.get("id"), channel_file_id, channel_message_id
                )

                await bale_client.send_message(
                    chat_id,
                    f"{EMOJI_SUCCESS} مدرک شما با موفقیت دریافت شد و در حال بررسی است.\n"
                    f"⏳ نتیجه به‌زودی به شما اطلاع داده خواهد شد.",
                )
        elif "contact" in message:
            contact = message["contact"]
            await core_api.update_phone_number(from_user.get("id"), contact["phone_number"])
            await bale_client.send_message(
                chat_id,
                "شماره تماس شما با موفقیت ثبت شد ✅",
                reply_markup=main_menu_keyboard(),
            )
        if text == "/start":
            profile = await core_api.get_user_profile(from_user.get("id"))
            if profile and not profile.get("phone_number"):
                await bale_client.send_message(
                    chat_id,
                    "برای استفاده از امکانات ربات، لطفاً شماره تماس خود را ارسال کنید:",
                    reply_markup=request_contact_keyboard(),
                )
            else:
                await bale_client.send_message(
                    chat_id,
                    f"سلام {user.get('full_name') or ''}! یکی از گزینه‌های زیر رو انتخاب کن:",
                    reply_markup=main_menu_keyboard(),
                )
        elif from_user.get("id") in user_states:
            state = user_states[from_user.get("id")]

            if state["step"] == "awaiting_amount":
                try:
                    amount = float(text.replace(",", "").strip())
                    if amount <= 0:
                        raise ValueError
                except ValueError:
                    await bale_client.send_message(chat_id, "لطفاً یک عدد معتبر وارد کنید.")
                else:
                    state["amount"] = amount
                    state["step"] = "awaiting_transfer_method"
                    await bale_client.send_message(
                        chat_id, "روش انتقال را انتخاب کنید:", reply_markup=transfer_method_keyboard()
                    )

            elif state["step"] == "awaiting_transfer_method":
                if text in ("پایا", "پل", "کارت به کارت", "حساب به حساب"):
                    state["transfer_method"] = text
                    state["step"] = "awaiting_receipt"
                    await bale_client.send_message(chat_id, "لطفاً تصویر رسید واریز را ارسال کنید:")
                elif text == "🔙 بازگشت":
                    del user_states[from_user.get("id")]
                    await bale_client.send_message(
                        chat_id, "به منوی کیف پول برگشتی:", reply_markup=wallet_submenu_keyboard()
                    )
                else:
                    await bale_client.send_message(chat_id, "لطفاً یکی از روش‌های موجود را انتخاب کنید.")
        elif text == MENU_LOANS:
            await bale_client.send_message(chat_id, "بخش وام‌های بانکی (به‌زودی تکمیل می‌شود)")
        elif text == MENU_CLUB_SERVICES:
            await bale_client.send_message(chat_id, "بخش خدمات باشگاه آگاه (به‌زودی تکمیل می‌شود)")
        elif text == MENU_STOCKS:
            await bale_client.send_message(chat_id, "بخش معرفی سهام (به‌زودی تکمیل می‌شود)")
        elif text == MENU_WALLET:
            balance_data = await core_api.get_balance(from_user.get("id"))
            await bale_client.send_message(
                chat_id,
                f"{EMOJI_MONEY} موجودی کیف پول شما: {balance_data['balance']:,.0f} تومان",
                reply_markup=wallet_submenu_keyboard(),
            )
        elif text == MENU_DEPOSIT:
            user_states[from_user.get("id")] = {"step": "awaiting_amount"}
            await bale_client.send_message(chat_id, "لطفاً مبلغ واریزی خود را به تومان وارد کنید:")

        elif text == MENU_TRANSACTIONS:
            transactions = await core_api.get_transactions(from_user.get("id"))
            if not transactions:
                await bale_client.send_message(chat_id, "هنوز تراکنشی ثبت نشده است.")
            else:
                status_emoji = {"pending": "⏳", "approved": "✅", "rejected": "❌"}
                lines = [f"{EMOJI_RECEIPT} تاریخچه تراکنش‌ها:\n"]
                for t in transactions[:10]:
                    emoji = status_emoji.get(t["status"], "")
                    lines.append(f"{emoji} {t['amount']:,.0f} تومان - {t['status']}")
                await bale_client.send_message(chat_id, "\n".join(lines))
        elif text == MENU_PROFILE:
            profile = await core_api.get_user_profile(from_user.get("id"))
            if profile:
                profile_text = (
                    f"{EMOJI_CALENDAR} تاریخ عضویت: {format_join_date(profile['created_at'])}\n\n"
                    f"{EMOJI_ID} شناسه من: {profile.get('bale_user_id')}\n"
                    f"{EMOJI_USERNAME} یوزرنیم: @{profile.get('bale_username') or 'ثبت نشده'}\n"
                    f"{EMOJI_NAME} نام و نام خانوادگی: {profile.get('full_name') or 'ثبت نشده'}\n"
                    f"{EMOJI_PHONE} شماره موبایل: {mask_phone(profile.get('phone_number'))}"
                )
                await bale_client.send_message(
                    chat_id, profile_text, reply_markup=profile_submenu_keyboard()
                )
            else:
                await bale_client.send_message(chat_id, "پروفایل شما پیدا نشد.")
        
        elif text == MENU_INVITE:
            await bale_client.send_message(chat_id, "بخش دعوت دوستان (به‌زودی تکمیل می‌شود)")
        elif text == MENU_ORDER_SEARCH:
            await bale_client.send_message(chat_id, "بخش جستجوی سفارش (به‌زودی تکمیل می‌شود)")
        elif text == MENU_MORE:
            await bale_client.send_message(chat_id, "بخش گزینه‌های بیشتر (به‌زودی تکمیل می‌شود)")
        elif text == MENU_BACK:
            await bale_client.send_message(
                chat_id, "به منوی اصلی برگشتی:", reply_markup=main_menu_keyboard()
            )
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
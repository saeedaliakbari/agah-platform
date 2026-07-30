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
MENU_WITHDRAWAL = "🏧 برداشت وجه"
MENU_MY_ACCOUNTS = "🏦 حساب‌های بانکی من"
MENU_ADD_ACCOUNT = "➕ ثبت حساب جدید"

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

TRANSACTION_TYPE_FA = {
    "deposit": "واریز",
    "withdrawal": "برداشت",
}

TRANSACTION_STATUS_FA = {
    "pending": "در انتظار بررسی ⏳",
    "approved": "تایید شده ✅",
    "rejected": "رد شده ❌",
}

def format_transaction_datetime(created_at_str: str) -> str:
    created_at = datetime.fromisoformat(created_at_str)
    jalali_date = jdatetime.datetime.fromgregorian(datetime=created_at)
    return jalali_date.strftime("%Y/%m/%d - %H:%M")


def format_transaction(t: dict) -> str:
    type_label = TRANSACTION_TYPE_FA.get(t["type"], t["type"])
    status_label = TRANSACTION_STATUS_FA.get(t["status"], t["status"])

    lines = [
        f"{EMOJI_RECEIPT} نوع: {type_label}",
        f"💵 مبلغ: {t['amount']:,.0f} تومان",
        f"{EMOJI_CALENDAR} تاریخ: {format_transaction_datetime(t['created_at'])}",
        f"{EMOJI_STATUS} وضعیت: {status_label}",
    ]

    if t.get("transfer_method"):
        lines.append(f"💳 روش انتقال: {t['transfer_method']}")

    if t["status"] == "rejected" and t.get("rejection_reason_text"):
        lines.append(f"دلیل رد: {t['rejection_reason_text']}")

    return "\n".join(lines)

def format_join_date(created_at_str: str) -> str:
    created_at = datetime.fromisoformat(created_at_str)
    jalali_date = jdatetime.datetime.fromgregorian(datetime=created_at)
    days_since = (datetime.now(timezone.utc) - created_at).days
    return f"{jalali_date.strftime('%Y/%m/%d')} ( {days_since} روز )"

def format_datetime(datetime_str: str) -> str:
    dt = datetime.fromisoformat(datetime_str)
    jalali_dt = jdatetime.datetime.fromgregorian(datetime=dt)
    return jalali_dt.strftime("%Y/%m/%d - %H:%M")

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

def wallet_submenu_keyboard() -> dict:
    return {
        "keyboard": [
            [{"text": MENU_DEPOSIT}, {"text": MENU_WITHDRAWAL}],
            [{"text": MENU_TRANSACTIONS}, {"text": MENU_MY_ACCOUNTS}],
            [{"text": "🔙 بازگشت"}],
        ],
        "resize_keyboard": True,
    }


def bank_accounts_menu_keyboard(accounts: list[dict]) -> dict:
    keyboard = []
    for acc in accounts:
        label = f"💳 {acc['bank_name']} - {acc['account_holder_name']}"
        keyboard.append([{"text": label}])
    keyboard.append([{"text": MENU_ADD_ACCOUNT}])
    keyboard.append([{"text": "🔙 بازگشت"}])
    return {"keyboard": keyboard, "resize_keyboard": True}


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





async def handle_message(message: dict) -> None:
     # پیام‌هایی که از کانال (echo پیام‌های خودمون) می‌آیند را نادیده بگیر
    if message.get("chat", {}).get("type") == "channel" or "sender_chat" in message:
        return
    
    chat_id = message["chat"]["id"]
    from_user = message.get("from", {})
    text = message.get("text", "")
    user_id = from_user.get("id")

    user = await core_api.identify_user(
        bale_user_id=user_id,
        full_name=from_user.get("first_name"),
        bale_username=from_user.get("username"),
    )

    try:
        state = user_states.get(user_id)

        if "photo" in message:
            photo_file_id = message["photo"][-1]["file_id"]

            if state and state.get("step") == "awaiting_receipt":
                caption_lines = [
                    "💰 درخواست شارژ کیف پول (تسویه P2P)\n",
                    f"{EMOJI_NAME} نام واریزکننده: {user.get('full_name') or 'نامشخص'}",
                    f"{EMOJI_ID} آیدی بله: {user_id}",
                    f"💵 مبلغ کل: {state['amount']:,.0f} تومان\n",
                    "🏦 حساب‌های مقصد:",
                ]
                for m in state["matches"]:
                    acc = m["bank_account"]
                    caption_lines.append(
                        f"- {acc['bank_name']} ({acc['account_holder_name']}): {m['amount_to_pay']:,.0f} تومان"
                    )
                caption_lines.append(f"\n{EMOJI_STATUS} وضعیت: در انتظار بررسی ⏳")
                caption = "\n".join(caption_lines)

                channel_message = await bale_client.send_photo(
                    WALLET_CHANNEL_ID, photo_file_id, caption=caption
                )
                channel_file_id = channel_message["result"]["photo"][-1]["file_id"]
                channel_message_id = channel_message["result"]["message_id"]

                # برای هر تطبیق، یک تراکنش واریز جدا ثبت می‌کنیم
                for m in state["matches"]:
                    await core_api.submit_deposit(
                        user_id,
                        m["amount_to_pay"],
                        channel_file_id,
                        transfer_method=f"P2P - {m['bank_account']['bank_name']}",
                        bale_channel_message_id=channel_message_id,
                        withdrawal_request_id=m["withdrawal_request_id"],
                    )

                del user_states[user_id]

                await bale_client.send_message(
                    chat_id,
                    f"{EMOJI_SUCCESS} درخواست واریز شما ثبت شد و در حال بررسی است.",
                    reply_markup=wallet_submenu_keyboard(),
                )
            else:
                caption = (
                    f"{EMOJI_DOCUMENT} درخواست احراز هویت جدید\n\n"
                    f"{EMOJI_NAME} نام: {user.get('full_name') or 'نامشخص'}\n"
                    f"{EMOJI_USERNAME_TAG} یوزرنیم: @{user.get('bale_username') or 'ثبت نشده'}\n"
                    f"{EMOJI_ID} آیدی بله: {user_id}\n"
                    f"{EMOJI_PHONE} شماره تماس: {user.get('phone_number') or 'ثبت نشده'}\n"
                    f"{EMOJI_STATUS} وضعیت: در انتظار بررسی ⏳"
                )
                channel_message = await bale_client.send_photo(
                    VERIFICATION_CHANNEL_ID, photo_file_id, caption=caption
                )
                channel_file_id = channel_message["result"]["photo"][-1]["file_id"]
                channel_message_id = channel_message["result"]["message_id"]

                await core_api.submit_verification(user_id, channel_file_id, channel_message_id)

                await bale_client.send_message(
                    chat_id,
                    f"{EMOJI_SUCCESS} مدرک شما با موفقیت دریافت شد و در حال بررسی است.\n"
                    f"⏳ نتیجه به‌زودی به شما اطلاع داده خواهد شد.",
                )

        elif "contact" in message:
            contact = message["contact"]
            await core_api.update_phone_number(user_id, contact["phone_number"])
            await bale_client.send_message(
                chat_id,
                "شماره تماس شما با موفقیت ثبت شد ✅",
                reply_markup=main_menu_keyboard(),
            )

        elif text == "/start":
            profile = await core_api.get_user_profile(user_id)
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

        elif state is not None:
            if text == "🔙 بازگشت":
                del user_states[user_id]
                await bale_client.send_message(
                    chat_id, "به منوی کیف پول برگشتی:", reply_markup=wallet_submenu_keyboard()
                )
            elif state["step"] == "awaiting_amount":
                try:
                    amount = float(text.replace(",", "").strip())
                    if amount <= 0:
                        raise ValueError
                except ValueError:
                    await bale_client.send_message(chat_id, "لطفاً یک عدد معتبر وارد کنید.")
                else:
                    matches = await core_api.reserve_withdrawal_matches(amount)
                    if not matches:
                        await bale_client.send_message(
                            chat_id,
                            "در حال حاضر درخواست برداشتی برای تطبیق وجود ندارد. لطفاً بعداً تلاش کنید.",
                            reply_markup=wallet_submenu_keyboard(),
                        )
                        del user_states[user_id]
                    else:
                        state["amount"] = amount
                        state["matches"] = matches
                        state["step"] = "awaiting_receipt"

                        lines = ["💳 لطفاً مبلغ خود را به حساب(های) زیر واریز کنید:\n"]
                        for m in matches:
                            acc = m["bank_account"]
                            lines.append(
                                f"🏦 بانک: {acc['bank_name']}\n"
                                f"👤 صاحب حساب: {acc['account_holder_name']}\n"
                                f"💳 شماره کارت: {acc.get('card_number') or 'ثبت نشده'}\n"
                                f"🔢 شبا: {acc['sheba_number']}\n"
                                f"💵 مبلغ: {m['amount_to_pay']:,.0f} تومان\n"
                            )
                        lines.append("\nپس از واریز، تصویر رسید را ارسال کنید:")
                        await bale_client.send_message(chat_id, "\n".join(lines))
            elif state["step"] == "awaiting_transfer_method":
                if text in ("پایا", "پل", "کارت به کارت", "حساب به حساب"):
                    state["transfer_method"] = text
                    state["step"] = "awaiting_receipt"
                    await bale_client.send_message(chat_id, "لطفاً تصویر رسید واریز را ارسال کنید:")
                else:
                    await bale_client.send_message(chat_id, "لطفاً یکی از روش‌های موجود را انتخاب کنید.")
            elif state["step"] == "awaiting_sheba":
                sheba = text.strip().upper().replace(" ", "")
                if not sheba.startswith("IR"):
                    sheba = "IR" + sheba
                state["sheba_number"] = sheba
                state["step"] = "awaiting_card_optional"
                await bale_client.send_message(
                    chat_id,
                    "شماره کارت را وارد کنید (اختیاری - اگر ندارید عدد 0 را بفرستید):",
                )

            elif state["step"] == "awaiting_card_optional":
                state["card_number"] = None if text.strip() == "0" else text.strip()
                state["step"] = "awaiting_account_holder"
                await bale_client.send_message(chat_id, "نام و نام خانوادگی صاحب حساب را وارد کنید:")

            elif state["step"] == "awaiting_account_holder":
                await core_api.submit_bank_account(
                    user_id, state["sheba_number"], state["card_number"], text.strip()
                )
                del user_states[user_id]
                await bale_client.send_message(
                    chat_id,
                    f"{EMOJI_SUCCESS} حساب بانکی شما ثبت شد و در انتظار تایید ادمین است.",
                    reply_markup=wallet_submenu_keyboard(),
                )
            elif state["step"] == "awaiting_withdrawal_account":
                accounts = state["accounts"]
                selected = next(
                    (a for a in accounts if f"💳 {a['bank_name']} - {a['account_holder_name']}" == text),
                    None,
                )
                if not selected:
                    await bale_client.send_message(chat_id, "لطفاً یکی از حساب‌های موجود را انتخاب کنید.")
                else:
                    state["bank_account_id"] = selected["id"]
                    state["step"] = "awaiting_withdrawal_amount"
                    await bale_client.send_message(chat_id, "مبلغ برداشتی را به تومان وارد کنید:")

            elif state["step"] == "awaiting_withdrawal_amount":
                try:
                    amount = float(text.replace(",", "").strip())
                    if amount <= 0:
                        raise ValueError
                except ValueError:
                    await bale_client.send_message(chat_id, "لطفاً یک عدد معتبر وارد کنید.")
                else:
                    result = await core_api.submit_withdrawal(
                        user_id, state["bank_account_id"], amount
                    )
                    if result is None:
                        await bale_client.send_message(
                            chat_id, "موجودی کافی نیست یا خطایی رخ داد."
                        )
                    else:
                        await bale_client.send_message(
                            chat_id,
                            f"{EMOJI_SUCCESS} درخواست برداشت شما به مبلغ {amount:,.0f} تومان ثبت شد.\n"
                            f"⏳ به محض تسویه توسط سایر کاربران، موجودی شما اضافه خواهد شد.",
                            reply_markup=wallet_submenu_keyboard(),
                        )
                    del user_states[user_id]

        elif text == MENU_LOANS:
            await bale_client.send_message(chat_id, "بخش وام‌های بانکی (به‌زودی تکمیل می‌شود)")
        elif text == MENU_CLUB_SERVICES:
            await bale_client.send_message(chat_id, "بخش خدمات باشگاه آگاه (به‌زودی تکمیل می‌شود)")
        elif text == MENU_STOCKS:
            await bale_client.send_message(chat_id, "بخش معرفی سهام (به‌زودی تکمیل می‌شود)")
        elif text == MENU_WALLET:
            balance_data = await core_api.get_balance(user_id)
            await bale_client.send_message(
                chat_id,
                f"{EMOJI_MONEY} موجودی کیف پول شما: {balance_data['balance']:,.0f} تومان",
                reply_markup=wallet_submenu_keyboard(),
            )
        elif text == MENU_DEPOSIT:
            user_states[user_id] = {"step": "awaiting_amount"}
            await bale_client.send_message(chat_id, "لطفاً مبلغی که می‌خواهید شارژ کنید را به تومان وارد کنید:")
        elif text == MENU_TRANSACTIONS:
            transactions = await core_api.get_transactions(user_id)
            if not transactions:
                await bale_client.send_message(chat_id, "هنوز تراکنشی ثبت نشده است.")
            else:
                for t in transactions[:10]:
                    await bale_client.send_message(chat_id, format_transaction(t))
        elif text == MENU_PROFILE:
            profile = await core_api.get_user_profile(user_id)
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
        elif text == MENU_MY_ACCOUNTS:
            accounts = await core_api.get_user_bank_accounts(user_id)
            if not accounts:
                await bale_client.send_message(
                    chat_id,
                    "هنوز حساب بانکی تاییدشده‌ای ندارید.\nبرای ثبت حساب جدید، دکمه‌ی زیر را بزنید:",
                    reply_markup={
                        "keyboard": [[{"text": MENU_ADD_ACCOUNT}], [{"text": "🔙 بازگشت"}]],
                        "resize_keyboard": True,
                    },
                )
            else:
                lines = ["🏦 حساب‌های بانکی تاییدشده‌ی شما:\n"]
                for acc in accounts:
                    lines.append(
                        f"• {acc['bank_name']} - {acc['account_holder_name']}\n"
                        f"  شبا: {acc['sheba_number']}"
                    )
                await bale_client.send_message(
                    chat_id, "\n".join(lines), reply_markup=bank_accounts_menu_keyboard(accounts)
                )
        elif text == MENU_WITHDRAWAL:
            accounts = await core_api.get_user_bank_accounts(user_id)
            if not accounts:
                await bale_client.send_message(
                    chat_id,
                    "برای برداشت وجه، ابتدا باید یک حساب بانکی تاییدشده ثبت کنید.",
                    reply_markup={
                        "keyboard": [[{"text": MENU_ADD_ACCOUNT}], [{"text": "🔙 بازگشت"}]],
                        "resize_keyboard": True,
                    },
                )
            else:
                user_states[user_id] = {"step": "awaiting_withdrawal_account", "accounts": accounts}
                await bale_client.send_message(
                    chat_id,
                    "حساب بانکی مقصد را انتخاب کنید:",
                    reply_markup=bank_accounts_menu_keyboard(accounts),
                )
        elif text == MENU_ADD_ACCOUNT:
            user_states[user_id] = {"step": "awaiting_sheba"}
            await bale_client.send_message(chat_id, "لطفاً شماره شبا خود را وارد کنید (بدون IR یا با آن):")   
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
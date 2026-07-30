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
user_reserved_matches: dict[int, list[dict]] = {}

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
MENU_MY_DEPOSITS = "📝 واریزهای رزروشده من"

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
            [{"text": MENU_DEPOSIT}, {"text": MENU_WITHDRAWAL}],
            [{"text": MENU_TRANSACTIONS}, {"text": MENU_MY_ACCOUNTS}],
            [{"text": MENU_MY_DEPOSITS}],
            [{"text": "🔙 بازگشت"}],
        ],
        "resize_keyboard": True,
    }

def reserved_deposits_keyboard(matches: list[dict]) -> dict:
    keyboard = []
    for i, m in enumerate(matches, start=1):
        keyboard.append([{"text": f"✅ تکمیل {i}"}, {"text": f"❌ لغو {i}"}])
    keyboard.append([{"text": "🔙 بازگشت"}])
    return {"keyboard": keyboard, "resize_keyboard": True}

def transfer_method_keyboard() -> dict:
    return {
        "keyboard": [
            [{"text": "پایا"}, {"text": "پل"}],
            [{"text": "کارت به کارت"}, {"text": "حساب به حساب"}],
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

            if state and state.get("step") == "awaiting_final_receipt":
                match = user_reserved_matches[user_id][state["match_index"]]
                acc = match["bank_account"]

                withdrawal_owner_info = await core_api.get_user_profile_by_withdrawal(
                    match["withdrawal_request_id"]
                )

                caption_lines = [
                    "💰 درخواست شارژ کیف پول (P2P)\n",
                    f"👤 واریزکننده: {user.get('full_name') or 'نامشخص'}",
                    f"🔖 یوزرنیم واریزکننده: @{user.get('bale_username') or 'ثبت نشده'}",
                    f"🆔 آیدی بله واریزکننده: {user_id}",
                    f"📞 موبایل واریزکننده: {user.get('phone_number') or 'ثبت نشده'}\n",
                    f"🏦 بانک مقصد: {acc['bank_name']}",
                    f"👤 صاحب حساب: {acc['account_holder_name']}",
                    f"💳 شماره کارت: {acc.get('card_number') or 'ثبت نشده'}",
                    f"🔢 شماره شبا: {acc['sheba_number']}\n",
                ]
                if withdrawal_owner_info:
                    caption_lines.extend([
                        f"👤 دریافت‌کننده: {withdrawal_owner_info.get('full_name') or 'نامشخص'}",
                        f"🔖 یوزرنیم دریافت‌کننده: @{withdrawal_owner_info.get('bale_username') or 'ثبت نشده'}",
                        f"🆔 آیدی بله دریافت‌کننده: {withdrawal_owner_info.get('bale_user_id')}",
                        f"📞 موبایل دریافت‌کننده: {withdrawal_owner_info.get('phone_number') or 'ثبت نشده'}\n",
                    ])
                caption_lines.extend([
                    f"💳 روش انتقال: {state['transfer_method_choice']}",
                    f"💵 مبلغ: {state['actual_amount']:,.0f} تومان",
                    f"{EMOJI_STATUS} وضعیت: در انتظار بررسی ⏳",
                ])
                caption = "\n".join(caption_lines)

                channel_message = await bale_client.send_photo(
                    WALLET_CHANNEL_ID, photo_file_id, caption=caption
                )
                channel_file_id = channel_message["result"]["photo"][-1]["file_id"]
                channel_message_id = channel_message["result"]["message_id"]

                await core_api.submit_deposit(
                    user_id,
                    state["actual_amount"],
                    channel_file_id,
                    transfer_method=state["transfer_method_choice"],
                    bale_channel_message_id=channel_message_id,
                    withdrawal_request_id=match["withdrawal_request_id"],
                )

                user_reserved_matches[user_id].pop(state["match_index"])
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

        elif text.startswith("/start"):
            parts = text.split(maxsplit=1)
            if len(parts) > 1:
                referral_code = parts[1].strip()
                await core_api.set_referrer(user_id, referral_code)

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
                    del user_states[user_id]

                    if not matches:
                        await bale_client.send_message(
                            chat_id,
                            "در حال حاضر درخواست برداشتی برای تطبیق وجود ندارد. لطفاً بعداً تلاش کنید.",
                            reply_markup=wallet_submenu_keyboard(),
                        )
                    else:
                        existing = user_reserved_matches.setdefault(user_id, [])
                        existing.extend(matches)

                        lines = ["✅ تطبیق با موفقیت انجام شد و رزرو گردید.\n"]
                        for m in matches:
                            acc = m["bank_account"]
                            lines.append(
                                f"🏦 {acc['bank_name']} - {acc['account_holder_name']}: "
                                f"{m['amount_to_pay']:,.0f} تومان"
                            )
                        lines.append(
                            "\nبرای تکمیل واریز (ارسال مبلغ واقعی، روش انتقال و رسید)، "
                            f"به بخش «{MENU_MY_DEPOSITS}» بروید."
                        )
                        await bale_client.send_message(
                            chat_id, "\n".join(lines), reply_markup=wallet_submenu_keyboard()
                        )
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
            elif state["step"] == "awaiting_actual_amount":
                if text == "🔙 بازگشت":
                    del user_states[user_id]
                    await bale_client.send_message(
                        chat_id, "ثبت واریز لغو شد.", reply_markup=wallet_submenu_keyboard()
                    )
                else:
                    try:
                        actual_amount = float(text.replace(",", "").strip())
                        if actual_amount <= 0:
                            raise ValueError
                    except ValueError:
                        await bale_client.send_message(chat_id, "لطفاً یک عدد معتبر وارد کنید.")
                    else:
                        match = user_reserved_matches[user_id][state["match_index"]]
                        if actual_amount > match["amount_to_pay"]:
                            await bale_client.send_message(
                                chat_id,
                                f"❌ مبلغ وارد شده بیشتر از حداکثر مجاز است.\n"
                                f"حداکثر مبلغ قابل واریز: {match['amount_to_pay']:,.0f} تومان\n"
                                f"لطفاً مبلغ صحیح را وارد کنید:",
                            )
                        else:
                            if actual_amount < match["amount_to_pay"]:
                                difference = match["amount_to_pay"] - actual_amount
                                await core_api.release_withdrawal_amount(
                                    match["withdrawal_request_id"], difference
                                )
                                match["amount_to_pay"] = actual_amount

                            state["actual_amount"] = actual_amount
                            state["step"] = "awaiting_transfer_method"
                            await bale_client.send_message(
                                chat_id, "روش انتقال را انتخاب کنید:", reply_markup=transfer_method_keyboard()
                            )

            elif state["step"] == "awaiting_transfer_method":
                if text == "🔙 بازگشت":
                    del user_states[user_id]
                    await bale_client.send_message(
                        chat_id, "ثبت واریز لغو شد.", reply_markup=wallet_submenu_keyboard()
                    )
                elif text in ("پایا", "پل", "کارت به کارت", "حساب به حساب"):
                    state["transfer_method_choice"] = text
                    state["step"] = "awaiting_final_receipt"
                    await bale_client.send_message(chat_id, "لطفاً تصویر رسید واریز را ارسال کنید:")
                else:
                    await bale_client.send_message(chat_id, "لطفاً یکی از روش‌های موجود را انتخاب کنید.")


        elif text.startswith("✅ تکمیل ") or text.startswith("❌ لغو "):
            matches = user_reserved_matches.get(user_id, [])
            try:
                index = int(text.split()[-1]) - 1
                selected_match = matches[index]
            except (ValueError, IndexError):
                await bale_client.send_message(chat_id, "مورد انتخابی نامعتبر است.")
            else:
                if text.startswith("❌ لغو "):
                    await core_api.release_withdrawal_amount(
                        selected_match["withdrawal_request_id"], selected_match["amount_to_pay"]
                    )
                    matches.pop(index)
                    await bale_client.send_message(
                        chat_id, "رزرو لغو شد.", reply_markup=wallet_submenu_keyboard()
                    )
                else:
                    user_states[user_id] = {
                        "step": "awaiting_actual_amount",
                        "match_index": index,
                    }
                    acc = selected_match["bank_account"]
                    await bale_client.send_message(
                        chat_id,
                        f"مبلغی که واقعاً به حساب زیر واریز کردید را وارد کنید:\n"
                        f"🏦 {acc['bank_name']} - {acc['account_holder_name']}\n"
                        f"(حداکثر مبلغ قابل واریز: {selected_match['amount_to_pay']:,.0f} تومان)",
                        reply_markup={"keyboard": [[{"text": "🔙 بازگشت"}]], "resize_keyboard": True},
                    )

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
        elif text == MENU_MY_DEPOSITS:
            matches = user_reserved_matches.get(user_id, [])
            if not matches:
                await bale_client.send_message(
                    chat_id,
                    f"{EMOJI_RECEIPT} شما در حال حاضر واریز رزروشده‌ای ندارید.",
                    reply_markup=wallet_submenu_keyboard(),
                )
            else:
                lines = [f"📝 واریزهای رزروشده‌ی شما ({len(matches)} مورد):\n"]
                for i, m in enumerate(matches, start=1):
                    acc = m["bank_account"]
                    lines.append(
                        f"━━━━━━━━━━━━━━━\n"
                        f"🔢 مورد {i}\n"
                        f"🏦 بانک: {acc['bank_name']}\n"
                        f"👤 صاحب حساب: {acc['account_holder_name']}\n"
                        f"💳 شماره کارت: {acc.get('card_number') or 'ثبت نشده'}\n"
                        f"🔢 شماره شبا: {acc['sheba_number']}\n"
                        f"💵 حداکثر مبلغ قابل واریز: {m['amount_to_pay']:,.0f} تومان\n"
                    )
                lines.append("━━━━━━━━━━━━━━━\nبرای هر مورد، از دکمه‌های زیر استفاده کنید 👇")
                await bale_client.send_message(
                    chat_id, "\n".join(lines), reply_markup=reserved_deposits_keyboard(matches)
                )
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
            referral_info = await core_api.get_referral_info(user_id)
            bot_username = os.getenv("BALE_BOT_USERNAME", "your_bot")
            invite_link = f"https://ble.ir/{bot_username}?start={referral_info['referral_code']}"

            await bale_client.send_message(
                chat_id,
                f"🤝 دعوت دوستان\n\n"
                f"کد دعوت شما: {referral_info['referral_code']}\n"
                f"تعداد افراد دعوت‌شده: {referral_info['referral_count']} نفر\n\n"
                f"لینک دعوت شما:\n{invite_link}",
            )
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
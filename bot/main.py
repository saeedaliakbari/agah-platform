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


@app.post("/webhook")
async def handle_update(request: Request) -> dict:
    update = await request.json()
    message = update.get("message")

    if not message:
        return {"ok": True}

    chat_id = message["chat"]["id"]
    from_user = message.get("from", {})
    text = message.get("text", "")

    user = await core_api.identify_user(
        bale_user_id=from_user.get("id"),
        full_name=from_user.get("first_name"),
    )

    if text == "/start":
        try:
            await bale_client.send_message(
                chat_id, f"سلام {user.get('full_name') or ''}! خوش اومدی."
            )
        except Exception as exc:
            print(f"Failed to send message to {chat_id}: {exc}")

    return {"ok": True}


@app.on_event("shutdown")
async def shutdown() -> None:
    await bale_client.close()
    await core_api.close()
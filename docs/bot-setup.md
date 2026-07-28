# راه‌اندازی بات بله (محیط توسعه)

این سند نحوه‌ی اتصال بات به بله در محیط توسعه (لوکال) را توضیح می‌دهد.

## پیش‌نیازها

- یک ربات تستی در بله (توکن از طریق BotFather بله)
- یک دامنه که DNS آن روی Cloudflare مدیریت می‌شود
- نصب `cloudflared`

## اجزای در حال اجرا

برای تست کامل، باید همزمان در حال اجرا باشند:

1. **Core API** (پورت ۸۰۰۰): `uvicorn app.main:app --reload`
2. **Bot** (پورت ۸۰۰۱): `cd bot && uvicorn main:app --reload --port 8001`
3. **Cloudflare Tunnel**: `cloudflared tunnel run agah-bot`
4. دیتابیس PostgreSQL: `docker compose up -d`

## راه‌اندازی اولیه‌ی Cloudflare Tunnel (فقط یک‌بار)

```bash
cloudflared tunnel login
cloudflared tunnel create agah-bot
cloudflared tunnel route dns agah-bot bot.yourdomain.ir
```

فایل تنظیمات در `~/.cloudflared/config.yml`:

```yaml
tunnel: <TUNNEL_ID>
credentials-file: /home/<user>/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: bot.yourdomain.ir
    service: http://localhost:8001
  - service: http_status:404
```

## تنظیم Webhook در بله

پس از بالا آمدن تونل:

```bash
curl -X POST "https://tapi.bale.ai/bot<TOKEN>/setWebhook" -H "Content-Type: application/json" -d "{\"url\": \"https://bot.yourdomain.ir/webhook\"}"
```

بررسی وضعیت:

```bash
curl "https://tapi.bale.ai/bot<TOKEN>/getWebhookInfo"
```

## نکات مهم

- در ایران، اتصال به Cloudflare Tunnel معمولاً نیاز به یک VPN با حالت **TUN mode** دارد (نه فقط تنظیم `HTTP_PROXY`)، چون پورت اختصاصی تونل (`7844`) اغلب مسدود است.
- توکن ربات هرگز نباید در کد یا گیت باشد؛ فقط در `.env` (که در `.gitignore` است).
- استفاده از دامنه‌ی شخصی روی Cloudflare Tunnel، پایدارتر از سرویس‌های موقت (ngrok رایگان، Quick Tunnel) است و آدرس ثابت می‌ماند.
# Notification Setup Guide

ReadingView uses [Apprise API](https://github.com/caronc/apprise-api) to deliver notifications about upcoming book releases. Apprise supports 100+ notification services — you configure which ones you want in Apprise, and ReadingView sends to them.

## 1. Deploy Apprise API

### Docker one-liner

```bash
docker run -d --name apprise \
  -p 8000:8000 \
  -v apprise-config:/config \
  --restart unless-stopped \
  caronc/apprise:latest
```

### Docker Compose

```yaml
services:
  apprise:
    image: caronc/apprise:latest
    container_name: apprise
    ports:
      - "8000:8000"
    volumes:
      - apprise-config:/config
    restart: unless-stopped

volumes:
  apprise-config:
```

Verify it's running: `curl http://localhost:8000/status`

## 2. Set Up Telegram

### Create a bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the prompts
3. Copy the **bot token** (e.g., `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Get your chat ID

1. Message your new bot (send anything)
2. Run:
   ```bash
   curl -s "https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates" | python3 -m json.tool
   ```
   Replace `YOUR_BOT_TOKEN` with the token from BotFather (no angle brackets).
3. Find `"chat":{"id": 123456789}` — that's your chat ID

### Add Telegram to Apprise

```bash
curl -X POST http://localhost:8000/add/readingview \
  -H "Content-Type: application/json" \
  -d '{"urls": ["tgram://YOUR_BOT_TOKEN/YOUR_CHAT_ID"]}'
```

Replace `readingview` with whatever key you want to use.

## 3. Configure ReadingView

Add these to your `.env` file:

```env
ENABLE_NOTIFICATIONS=true
APPRISE_API_URL=http://your-apprise-server:8000
APPRISE_NOTIFICATION_KEY=readingview
```

- **`APPRISE_API_URL`** — URL of your Apprise API instance
- **`APPRISE_NOTIFICATION_KEY`** — the key you used when adding URLs to Apprise (e.g., `readingview`). This is a routing tag you define — any string works. All notification URLs added under this key will receive notifications.

## 4. Add Other Services

Add more notification URLs to the same key. Here are common Apprise URL schemes:

| Service | URL Format | Example |
|---------|-----------|---------|
| Telegram | `tgram://bottoken/ChatID` | `tgram://123:ABC/987654` |
| Discord | `discord://WebhookID/WebhookToken` | `discord://id/token` |
| Slack | `slack://TokenA/TokenB/TokenC/#channel` | `slack://a/b/c/#general` |
| Email (SMTP) | `mailto://user:pass@smtp.example.com?to=dest@example.com` | — |
| Gotify | `gotify://host/token` | `gotify://gotify.local/abcdef` |
| Pushover | `pover://user_key@app_token` | `pover://ukey@atoken` |
| ntfy | `ntfy://topic` or `ntfy://host/topic` | `ntfy://ntfy.sh/mytopic` |

Full list: [Apprise Supported Notifications](https://github.com/caronc/apprise/wiki#supported-notifications)

To add a service:

```bash
curl -X POST http://localhost:8000/add/readingview \
  -H "Content-Type: application/json" \
  -d '{"urls": ["discord://WebhookID/WebhookToken"]}'
```

## 5. Manage Services

**List configured URLs:**

```bash
curl http://localhost:8000/json/urls/readingview
```

**Remove all URLs for a key:**

```bash
curl -X DELETE http://localhost:8000/del/readingview
```

**Replace all URLs (remove existing + add new):**

```bash
curl -X POST http://localhost:8000/add/readingview \
  -H "Content-Type: application/json" \
  -d '{"urls": ["tgram://bot/chat", "discord://id/token"]}'
```

## 6. Test

**From the command line:**

```bash
curl -X POST http://localhost:8000/notify/readingview \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "body": "Hello from Apprise!", "type": "info"}'
```

**From ReadingView:**

Go to the Notifications tab and click **Send Test Notification**.

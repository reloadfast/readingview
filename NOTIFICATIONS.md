# Notifications

ReadingView sends release-digest notifications via [Apprise](https://github.com/caronc/apprise), which supports 100+ services including Telegram, Discord, Slack, Gotify, ntfy, email, and more.

## Configuration

All notification settings are managed through the **Settings UI** at `/settings` — no environment variables needed.

| Setting | Default | Description |
|---------|---------|-------------|
| Enable notifications | off | Master switch — no messages are sent when disabled |
| Apprise URL | — | Your Apprise-formatted notification URL (stored encrypted) |
| Days before release | 7 | How many days ahead to look for upcoming releases |
| Notify time | 09:00 | Time of day (24h) to run the daily digest check |
| Timezone | UTC | Timezone for the notify time |

## How it works

A background job runs once per day at the configured `Notify time`. If there are upcoming releases within the `Days before release` window, it sends a digest notification listing the book titles, authors, and dates.

The digest is also fired automatically when the scheduled release-refresh job finds newly added releases.

## API endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/notifications/test` | Send a test message to verify the Apprise URL |
| `POST /api/notifications/digest/preview` | Return the would-be digest body without sending |
| `POST /api/notifications/digest/send` | Send the digest immediately |

## Apprise URL examples

```
# ntfy (self-hosted)
ntfy://192.168.1.110/readingview

# Gotify
gotifys://gotify.example.com/TOKEN

# Telegram
tgram://BOT_TOKEN/CHAT_ID

# Discord webhook
discord://WEBHOOK_ID/WEBHOOK_TOKEN
```

See the [Apprise wiki](https://github.com/caronc/apprise/wiki) for the full URL format for each service.

## Refs

Closes issue #80. Related: #71 (deleted NOTIFICATIONS.md restored here).

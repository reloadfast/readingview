# Deployment Guide

## Prerequisites

- **Docker** or **Python 3.11+**
- Audiobookshelf instance running and accessible
- Audiobookshelf API token (see [Getting Your API Token](#getting-your-api-token))

## Docker (Recommended)

```bash
docker run -d \
  --name readingview \
  -p 8506:8506 \
  -e ABS_URL=https://your-audiobookshelf-url \
  -e ABS_TOKEN=your_api_token \
  --restart unless-stopped \
  readingview:latest
```

Access at: **http://localhost:8506**

### Building from Source

```bash
git clone https://github.com/reloadfast/readingview.git
cd readingview
docker build -t readingview:latest .
```

## Docker Compose

```yaml
version: '3.8'
services:
  readingview:
    image: readingview:latest
    container_name: readingview
    ports:
      - "8506:8506"
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8506/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

```bash
cp env.example .env   # edit with your credentials
docker-compose up -d
```

## Local Development

```bash
git clone https://github.com/reloadfast/readingview.git
cd readingview
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp env.example .env   # edit with your credentials
streamlit run app.py
```

Streamlit auto-reloads on file changes.


## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ABS_URL` | Yes | — | Audiobookshelf server URL |
| `ABS_TOKEN` | Yes | — | API authentication token |
| `APP_TITLE` | No | ReadingView | Dashboard title |
| `CACHE_TTL` | No | 300 | Cache duration in seconds |
| `ENABLE_RELEASE_TRACKER` | No | true | Enable release tracking features |
| `DB_PATH` | No | database/release_tracker.db | SQLite database path |

## Getting Your API Token

1. Log into your Audiobookshelf instance
2. Go to **Settings** → **Users** → click your username
3. Scroll to **API Tokens** → **Generate Token**
4. Copy the token (shown only once)

## Reverse Proxy

### Nginx

```nginx
server {
    listen 80;
    server_name readingview.yourdomain.com;

    location / {
        proxy_pass http://localhost:8506;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

### Caddy

```
readingview.yourdomain.com {
    reverse_proxy localhost:8506
}
```

## Updating

```bash
# Docker
docker pull readingview:latest
docker stop readingview && docker rm readingview
# Re-run with same settings

# Docker Compose
docker-compose pull && docker-compose up -d

# Local
git pull && pip install -r requirements.txt
```

## Troubleshooting

**Cannot connect to Audiobookshelf** — Verify `ABS_URL` is reachable (`curl $ABS_URL/api/ping`) and token is valid.

**Port already in use** — Map to a different host port: `-p 8502:8506`

**Covers not loading** — Check that covers display in the Audiobookshelf web UI. Inspect browser console for CORS errors.

**Slow performance** — Increase `CACHE_TTL` or check Audiobookshelf server response times.

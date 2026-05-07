# Deployment Guide

## Prerequisites

- **Docker** and **Docker Compose**
- Audiobookshelf instance running and accessible
- Audiobookshelf API token (see [Getting Your API Token](#getting-your-api-token))

## Docker Compose (Recommended)

```bash
cp .env.example .env
# Edit .env: set SECRET_KEY to a long random string
docker-compose up -d
```

Access at: **http://localhost:8000**

Complete ABS setup in the **Settings UI** — no additional env vars needed.

### Building from Source

```bash
git clone forgejo:Wind/readingview
cd readingview
docker build -t readingview:latest .
```

## Local Development

```bash
# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
DATABASE_URL=sqlite+aiosqlite:////tmp/readingview.db SECRET_KEY=dev uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
pnpm install
pnpm dev
```

Backend: **http://localhost:8000** | Frontend dev server: **http://localhost:5173**

## Getting Your API Token

1. Log into your Audiobookshelf instance
2. Go to **Settings** → **Users** → click your username
3. Scroll to **API Tokens** → **Generate Token**
4. Copy the token — paste it into the ReadingView **Settings UI**

## Reverse Proxy

### Nginx

```nginx
server {
    listen 80;
    server_name readingview.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Caddy

```
readingview.yourdomain.com {
    reverse_proxy localhost:8000
}
```

## Updating

```bash
# Docker Compose
docker-compose pull && docker-compose up -d
```

## Troubleshooting

**Cannot connect to Audiobookshelf** — Check the ABS URL and token in the Settings UI. Verify reachability: `curl $ABS_URL/api/ping`.

**Port already in use** — Set `PORT=8001` in `.env` and update `docker-compose.yml` accordingly.

**Covers not loading** — Check that covers display in the Audiobookshelf web UI. Inspect browser console for CORS errors.

**Slow performance** — Check Audiobookshelf server response times. Cache TTL is configurable in the Settings UI.

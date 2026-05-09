# ReadingView

A self-hosted audiobook dashboard for [Audiobookshelf](https://www.audiobookshelf.org/). Browse your library, track listening statistics, follow upcoming releases from your favorite authors, and get AI-powered book recommendations — all from a single interface.

Designed for single-user, self-hosted deployments. No cloud services required.

## Features

### Library
- **Bookshelf grid** with cover art, progress bars, and time remaining
- **In Progress** and **Full Library** views with search, pagination, and sorting
- **Finished books** toggle with "Recently Finished" sort
- **Bulk ingest** books into the AI recommender catalog

### Statistics
- **Overview cards** — books completed, hours listened, average books per month
- **Yearly and monthly breakdowns** with interactive charts and expandable book lists
- **Year in Recap** — Spotify Wrapped-style summary per year: top authors, longest/shortest book, fastest/slowest read, monthly pace chart, top series

### Authors
- **Author grid** with search and pagination
- **Detail view** — bio and photo from Open Library, books in your library, external links
- **Release tracking** — one-click to start tracking an author's upcoming releases

### Series Progress
- **Per-series completion** with visual progress bars
- **Book-level status** — finished, in progress, or not started
- **Sort and filter** — by name, completion %, book count; filter by status

### Release Tracker
- **Upcoming releases** with highlighted next-3 cards, author filtering, and sorting
- **Add from library** — auto-detect authors from your Audiobookshelf library
- **Manual entry** — add any author or release by hand
- **Manage** — edit/delete tracked authors, series, and individual releases
- **Open Library integration** — auto-fill release details from search results

### Notifications (optional)
- **Apprise integration** — supports 100+ services (Telegram, Discord, Slack, Gotify, ntfy, email, and more)
- **Scheduled digests** — daily or weekly release notification emails via background scheduler
- **Manual digest** — preview and send upcoming release summaries on demand
- **Connection status** — live indicator showing configured notification services
- Configured through the **Settings UI** — no env vars needed after initial setup

### Book Recommender (optional)
- **Local AI** — runs entirely on your machine via [Ollama](https://ollama.com/), no cloud APIs
- **Ingest** books by ISBN, title, or directly from your library with an edition picker
- **Recommendations** from liked books, free-text prompts ("epic fantasy with complex magic systems"), or both
- **Similar Books** dialog — one-click recommendations from any library card
- **Feedback loop** — thumbs up/down adjusts future recommendation scores
- **Optional explanations** — LLM-generated reasoning for each recommendation
- **Vector backends** — FAISS for speed or pure-Python cosine similarity (zero extra dependencies)

## Quick Start

```bash
cp .env.example .env   # set SECRET_KEY and DATABASE_URL
docker-compose up -d
```

Access at **http://localhost:8000** — configure ABS credentials and all other settings through the Settings UI.

## Architecture

```
readingview/
├── backend/                   # FastAPI Python backend
│   ├── app/
│   │   ├── main.py            # App entrypoint, router registration, SPA serving
│   │   ├── config.py          # Pydantic-settings config
│   │   ├── db.py              # SQLAlchemy async engine
│   │   ├── api/               # FastAPI routers
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic schemas
│   │   └── services/          # Business logic (ABS client, OL client, etc.)
│   ├── book_recommender/      # Pluggable AI recommendation module (Ollama)
│   ├── alembic/               # Database migrations
│   └── pyproject.toml         # Dependencies
├── frontend/                  # React + Vite SPA
├── Dockerfile                 # Multi-stage build (Python 3.12 + Node 22)
├── docker-compose.yml         # Production compose
└── .env.example               # Bootstrap env vars
```

## Configuration

Four environment variables bootstrap the container. All other settings (Audiobookshelf credentials, notifications, appearance) are managed through the **Settings UI** at `/settings`.

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | `sqlite+aiosqlite:////data/readingview.db` |
| `SECRET_KEY` | Yes | Long random string for session signing |
| `PORT` | No | Container port (default: 8000) |
| `TZ` | No | Timezone (default: UTC) |

See [`.env.example`](.env.example) for the full template.

## Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** — Docker, Docker Compose, reverse proxy, local dev, updating

## License

MIT License

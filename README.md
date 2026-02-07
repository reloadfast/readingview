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

### Book Recommender (optional)
- **Local AI** — runs entirely on your machine via [Ollama](https://ollama.com/), no cloud APIs
- **Ingest** books by ISBN, title, or directly from your library with an edition picker
- **Recommendations** from liked books, free-text prompts ("epic fantasy with complex magic systems"), or both
- **Similar Books** dialog — one-click recommendations from any library card
- **Feedback loop** — thumbs up/down adjusts future recommendation scores
- **Optional explanations** — LLM-generated reasoning for each recommendation
- **Vector backends** — FAISS for speed or pure-Python cosine similarity (zero extra dependencies)

### UI Polish
- Dark theme with custom typography
- Loading skeletons instead of spinners
- Keyboard shortcuts: `1`-`9` switch tabs, `/` focuses search, `Esc` closes dialogs
- Toast notifications for non-blocking action feedback
- Error boundaries per tab — one broken tab won't take down the dashboard

## Quick Start

### Docker (recommended)

```bash
docker run -d \
  --name readingview \
  -p 8506:8506 \
  -v readingview-data:/app/data \
  -e ABS_URL=https://your-audiobookshelf-url \
  -e ABS_TOKEN=your_api_token \
  --restart unless-stopped \
  readingview:latest
```

### Local

```bash
git clone https://github.com/reloadfast/readingview.git
cd readingview
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp env.example .env   # edit with your credentials
streamlit run app.py
```

Access at: **http://localhost:8506**

## Configuration

All configuration is via environment variables (or a `.env` file). See [`env.example`](env.example) for a complete template.

### Required

| Variable | Description |
|----------|-------------|
| `ABS_URL` | Audiobookshelf server URL |
| `ABS_TOKEN` | API token ([how to get one](DEPLOYMENT.md#getting-your-api-token)) |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_TITLE` | `ReadingView` | Dashboard title |
| `CACHE_TTL` | `300` | Data cache duration in seconds |
| `ITEMS_PER_ROW` | `5` | Grid columns for book/author cards |
| `THEME` | `dark` | Color theme (`dark` or `light`) |
| `ENABLE_RELEASE_TRACKER` | `true` | Show release tracker and authors tabs |
| `DB_PATH` | `/app/data/release_tracker.db` | SQLite database path |

### Notifications (via Apprise)

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_NOTIFICATIONS` | `false` | Enable notification features |
| `APPRISE_API_URL` | — | Apprise API server URL |
| `APPRISE_NOTIFICATION_KEY` | — | Routing key configured in Apprise |

See [NOTIFICATIONS.md](NOTIFICATIONS.md) for setup instructions.

### Book Recommender (via Ollama)

| Variable | Default | Description |
|----------|---------|-------------|
| `BOOK_RECOMMENDER_ENABLED` | `false` | Enable the recommender module |
| `BOOK_RECOMMENDER_OLLAMA_URL` | `http://localhost:11434` | Ollama API endpoint |
| `BOOK_RECOMMENDER_EMBED_MODEL` | `nomic-embed-text` | Embedding model |
| `BOOK_RECOMMENDER_LLM_MODEL` | `llama3` | LLM for explanations |
| `BOOK_RECOMMENDER_VECTOR_BACKEND` | `python` | `faiss` or `python` |
| `BOOK_RECOMMENDER_DB_PATH` | `/app/data/book_recommender.db` | Recommender database path |
| `BOOK_RECOMMENDER_ENABLE_EXPLANATIONS` | `false` | Generate LLM explanations |
| `BOOK_RECOMMENDER_TOP_K` | `10` | Number of recommendations to return |
| `BOOK_RECOMMENDER_MIN_SIMILARITY` | `0.2` | Minimum similarity threshold |

Requires [Ollama](https://ollama.com/) running locally with the configured models pulled.

## Architecture

```
readingview/
├── app.py                     # Streamlit entry point
├── config/config.py           # Environment variable loading
├── api/
│   ├── audiobookshelf.py      # ABS API client
│   └── openlibrary.py         # Open Library API client
├── components/                # UI tab components
│   ├── library.py             # Library + In Progress views
│   ├── statistics.py          # Stats + Year in Recap
│   ├── authors.py             # Author browser
│   ├── series_tracker.py      # Series progress
│   ├── release_tracker.py     # Release tracking
│   ├── recommendations.py     # Recommender UI
│   └── notifications.py       # Notification settings
├── book_recommender/          # Pluggable AI recommendation module
│   ├── __init__.py            # Public API
│   ├── service.py             # Orchestration
│   ├── _db.py, _ollama.py     # Storage + AI clients
│   ├── _vector.py             # FAISS / cosine backends
│   └── _ingestion.py          # Open Library metadata fetcher
├── database/db.py             # Release tracker SQLite schema
├── utils/
│   ├── helpers.py             # Formatting, grouping, skeletons
│   ├── notifications.py       # Apprise client
│   └── scheduler.py           # APScheduler background jobs
├── Dockerfile                 # Multi-stage Docker build
└── docker-compose.yml         # Full-stack compose config
```

Data is stored in two SQLite databases (under `/app/data/` in Docker):
- **release_tracker.db** — tracked authors, series, releases, notification preferences
- **book_recommender.db** — ingested book metadata, embeddings, feedback

## Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** — Docker, Docker Compose, reverse proxy, local dev, updating
- **[NOTIFICATIONS.md](NOTIFICATIONS.md)** — Apprise notification setup (Telegram, Discord, etc.)
- **[OPEN_LIBRARY_USER_GUIDE.md](OPEN_LIBRARY_USER_GUIDE.md)** — Release tracker search guide

## License

MIT License

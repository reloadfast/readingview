# ReadingView — Project Rules

## Infrastructure (authoritative)

- **Git remote**: Forgejo at `forgejo.moseisley.es` (SSH port 1022, web port 3022). No GitHub. No other remotes.
- **Container registry**: Forgejo's built-in OCI registry at `forgejo.moseisley.es`. No Docker Hub. No GHCR. No other registries.
- **CI runner**: `unraid-runner` (self-hosted, Forgejo Actions). No GitHub Actions.
- **CI image push**: tag and push to `forgejo.moseisley.es/wind/readingview`. Use `FORGEJO_TOKEN` secret — never `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN`.
- **No cloud services of any kind**: everything stays on-premises.

## CI Workflow Rules

- Workflow file lives at `.forgejo/workflows/` — the runner ignores `.github/workflows/`.
- Never use actions not mirrored on `data.forgejo.org`. Use `run:` shell steps instead.
- Confirmed unavailable on `data.forgejo.org`: `aquasecurity/trivy-action`, `github/codeql-action`, `actions/upload-artifact`, `peter-evans/dockerhub-description`. Replace all with CLI equivalents.
- Trivy: install via `curl | sh`, run as CLI. Exit-code 0 (report, don't block).

## Architecture

ReadingView is a **FastAPI + React** application:

```
readingview/
├── backend/                   # FastAPI Python backend
│   ├── app/
│   │   ├── main.py            # App entrypoint, router registration, SPA serving
│   │   ├── config.py          # Pydantic-settings config (reads env vars)
│   │   ├── db.py              # SQLAlchemy async engine + session factory
│   │   ├── api/               # FastAPI routers (one per feature area)
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   └── services/          # Business logic (ABS client, OL client, etc.)
│   ├── book_recommender/      # Pluggable AI recommendation module (Ollama)
│   ├── alembic/               # Database migrations
│   ├── tests/                 # pytest test suite
│   └── pyproject.toml         # Dependencies, ruff, mypy, pytest config
├── frontend/                  # React + Vite SPA
│   ├── src/                   # Component source
│   └── dist/                  # Built assets (served by FastAPI, gitignored)
├── Dockerfile                 # Multi-stage build (Python 3.12 + Node 22)
├── docker-compose.yml         # Production compose (port 8000)
└── .env.example               # Bootstrap env vars (4 vars only)
```

## Bootstrap Environment Variables

Only 4 env vars are needed to start the container. All other configuration (ABS credentials, notifications, appearance) is managed through the **Settings UI**:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | SQLite path e.g. `sqlite+aiosqlite:////data/readingview.db` |
| `SECRET_KEY` | Yes | Long random string for session signing |
| `PORT` | No | Container port (default: 8000) |
| `TZ` | No | Timezone (default: UTC) |

## book_recommender Module

Pluggable, feature-flagged AI recommendation module. Runs entirely on-device via Ollama.

Activated only when `BOOK_RECOMMENDER_ENABLED=true` is set. When disabled: no-op on import, no network calls, no side effects.

Required env vars (when enabled):
- `BOOK_RECOMMENDER_ENABLED=true`
- `BOOK_RECOMMENDER_DB_PATH`
- `BOOK_RECOMMENDER_VECTOR_BACKEND` (`faiss` | `python`)
- `BOOK_RECOMMENDER_EMBED_MODEL` (e.g. `nomic-embed-text`)
- `BOOK_RECOMMENDER_LLM_MODEL` (e.g. `llama3`)
- `BOOK_RECOMMENDER_ENABLE_EXPLANATIONS` (`true` | `false`)
- `BOOK_RECOMMENDER_OLLAMA_URL` (e.g. `http://localhost:11434`)

Optional: `BOOK_RECOMMENDER_TOP_K`, `BOOK_RECOMMENDER_MIN_SIMILARITY`

Public API surface: `book_recommender/__init__.py` + `book_recommender/service.py` only.

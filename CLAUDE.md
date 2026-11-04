# ReadingView — Project Rules

## Infrastructure (authoritative)

- **Git remote**: Forgejo at `forgejo.moseisley.es` (SSH port 1022, web port 3022). No GitHub. No other remotes.
- **Container registry**: Forgejo's built-in OCI registry at `forgejo.moseisley.es`. No Docker Hub. No GHCR. No other registries.
- **CI runner**: `unraid-runner` (self-hosted, Forgejo Actions). No GitHub Actions.
- **CI image push**: tag and push to `forgejo.moseisley.es/wind/readingview`. Use `FORGEJO_TOKEN` secret — never `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN`.
- **No cloud services of any kind**: everything stays on-premises.

## CI Workflow Rules

- Follow Golden CI 4.0.0 at global-standards commit
  `64ec40904a302c81c23aeb51c9de1fb2292969ba`; see `docs/ci.md` for provenance,
  runner prerequisites and the outstanding live adoption gates.
- `.forgejo/workflows/ci.yml` verifies main PRs, main pushes and manual runs in
  one job. Every check, including OpenAPI, gates the single local image build,
  smoke test and blocking Trivy scan. Only a successful main push may publish.
- Use fully qualified `data.forgejo.org` action URLs pinned to reviewed commits.
  Checkout uses the automatic workflow token without persistent credentials.
- Tooling is pre-provisioned and pinned in the maintained internal runner image;
  no `curl | sh`, `@latest` installers or shared toolcache mutation in CI.
- Trivy scans the local candidate for HIGH/CRITICAL vulnerabilities and secrets
  with exit-code 1. Gitleaks redacts repository findings; dependency audits fail
  on findings or scanner/service errors.
- Keep `scripts/ci/container.sh`, `publish.sh` and `prune_registry.py` identical
  to the recorded standards revision. Publication promotes the tested digest,
  verifies latest, then retains three distinct releases. No global Docker prune
  or automatic deployment. Review rollback requirements before live adoption.

### Python in CI — hard-won rules

**Use `uv`, not `actions/setup-python`.** The runner mounts a shared toolcache volume at `/mnt/cache/appdata/ci-tool-cache`. Concurrent jobs both calling `actions/setup-python` race to install Python there and corrupt each other's pip. `uv` avoids this entirely — it manages Python in `~/.local/share/uv` which is safe for concurrent access.

CI uses the committed lockfile and the runner's Python 3.12:
```bash
uv sync --project backend --frozen --extra dev --python 3.12
uv run --project backend --frozen --extra dev ruff check backend/
uv run --project backend --frozen --extra dev mypy --ignore-missing-imports backend/
```

Key points:
- Never resolve unlocked development tools during CI. Use `uv sync --frozen`
  with the dev extra and run Python checks through `uv run --frozen --extra dev`.
- The production image uses the same lockfile without development extras.
- **Do not use Python 3.14 in CI.** The `actions/python-versions` release for 3.14 is broken (missing `mmap` module, pip fails to install). Stay on 3.12.

**mypy must be invoked as `mypy --ignore-missing-imports backend/` from the repo root.** Running `mypy .` from `working-directory: backend` finds `backend/pyproject.toml` and applies `strict = true`, which surfaces ~400 pre-existing violations that have never been enforced. The pre-push hook also uses `--ignore-missing-imports backend/` from root — keep CI identical to the hook.

**Local Python (3.14) and CI Python (3.12) generate different OpenAPI schemas.** The pre-push hook warns about this but does not block — it restores the committed file before pushing. The committed `api.generated.ts` is always the CI (Python 3.12) version. Never commit the locally-regenerated version unless you have verified CI also produces it. Do not run `pnpm openapi` manually and commit the result.

### book_recommender optional dependency rules

`numpy` is an optional dependency of the optional `book_recommender` module. It is **not** installed in the base dev/CI environment. Any test that exercises a code path reaching `_compute_query_vector` (in `book_recommender/service.py`) must mock it:

```python
patch("book_recommender.service._compute_query_vector", return_value=[0.1] * 16)
```

Do not add `numpy` to dev dependencies to fix a test — mock the boundary instead.

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

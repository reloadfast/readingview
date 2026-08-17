# ReadingView — Agent Guide

## Purpose and boundaries

ReadingView is a single-user, self-hosted audiobook dashboard for Audiobookshelf (ABS). It provides a React SPA for library browsing, listening statistics, authors/narrators/series, release tracking, collections and notes, goals, optional Apprise release notifications, and optional local-Ollama recommendations.

- Keep the product on-premises. Forgejo (`forgejo.moseisley.es`) is the only git host and OCI registry; do not introduce GitHub, Docker Hub, GHCR, or cloud services.
- Treat ABS URLs/tokens, `SECRET_KEY`, backup tokens, Apprise URLs, and LLM keys as secrets. Do not print or commit them. User-managed settings containing credentials are encrypted by `backend/app/crypto.py`.
- Preserve unrelated working-tree changes. Check `git status --short` before and after edits.

`CLAUDE.md` is authoritative for infrastructure and CI-specific constraints; read it before editing CI, publishing, or changing recommender/OpenAPI behavior.

## Layout and runtime

```
backend/app/          FastAPI app: routers, schemas, ORM models, services
backend/book_recommender/  optional local embedding/recommendation module
backend/alembic/      ordered SQLite schema migrations
backend/tests/        pytest unit/integration-style API tests
frontend/src/         React 18 + TypeScript + Vite + Tailwind 4 SPA
frontend/src/lib/     API client and generated OpenAPI schema types
.forgejo/workflows/   Forgejo Actions CI (not .github/workflows)
```

Production is one Docker image: Node 22 builds the SPA; Python 3.12 runs FastAPI. At start, `entrypoint.sh` applies `alembic upgrade head`, then starts `backend.app.main:app`. FastAPI serves `frontend/dist` and uses `/api` for API/WebSocket traffic. Development runs FastAPI on `:8000` and Vite on `:5173`; Vite proxies `/api` to the backend.

The supported persistent database is async SQLite (`DATABASE_URL`, normally under `/data`). Add an Alembic revision for every persistent-model/schema change; do not rely on `Base.metadata.create_all`.

## Production access and diagnostics

- The production ReadingView instance is available at `http://192.168.1.110:8004` for in-scope verification and diagnostics.
- Container logs can be inspected through the Dozzle MCP endpoint at `https://dozzle.moseisley.es/api/mcp`.
- Treat production as user data: use these endpoints only as needed for the task, avoid printing sensitive data from responses or logs, and do not make production changes unless the user has explicitly requested them.

## Architecture conventions

- Add an API feature across `backend/app/schemas/` (Pydantic contract), `models/` if persisted, `services/` (business/external-client logic), `api/` (thin router), and `main.py` router registration where applicable. Add focused tests in `backend/tests/`.
- Routers use async SQLAlchemy sessions from `get_db`. Keep external calls async, translate expected HTTP client failures into useful HTTP responses, and use transactions for database writes.
- Settings are one row (`id=1`), created with SQLite `INSERT ... ON CONFLICT DO NOTHING`. Keep sensitive settings encrypted and masked in GET responses; settings changes may need to restart the ABS socket/cache or reschedule jobs.
- ABS data is accessed through `services/audiobookshelf.py` and the cache/socket services. The backend broadcasts live ABS changes at `/api/ws`; frontend query keys must remain aligned with `WebSocketContext` invalidations.
- Background release refresh and digest jobs live in `services/scheduler.py`; validate rescheduling behavior with its tests.
- Frontend pages compose feature hooks, hooks own TanStack Query keys/mutations, and `src/lib/api.ts` owns HTTP calls. Reuse `components/ui` and the theme tokens in `src/index.css`; do not bypass the shared API helper.

## API contract discipline

- FastAPI OpenAPI is the source of truth. `frontend/src/lib/api.generated.ts` and `api.schemas.ts` are generated: never hand-edit either.
- An API schema/route change requires regenerating the frontend types and checking the resulting diff. CI uses Python 3.12 because local Python 3.14 can produce a different schema. Prefer the exact CI-style export:

  ```bash
  cd backend
  SECRET_KEY=dev DATABASE_URL=sqlite+aiosqlite:////tmp/readingview-openapi.db \
    python -c "import json; from app.main import app; print(json.dumps(app.openapi()))" \
    > /tmp/openapi.json
  cd ../frontend && pnpm openapi --spec-path /tmp/openapi.json
  ```

  Only commit the generated file after verifying it is from Python 3.12 / matches CI.

## Local development and verification

Install backend dependencies with Python 3.12 and `uv` when available (CI requires it):

```bash
uv venv --python 3.12 backend/.venv
cd backend && uv pip install -e '.[dev]'
cd frontend && corepack enable && pnpm install --frozen-lockfile
```

Run locally:

```bash
cd backend && SECRET_KEY=dev DATABASE_URL=sqlite+aiosqlite:////tmp/readingview.db \
  ../backend/.venv/bin/uvicorn app.main:app --reload
cd frontend && pnpm dev
```

Use focused tests first, then proportionate checks:

```bash
cd backend && pytest tests/test_library.py
cd backend && pytest
ruff check backend/ && ruff format --check backend/
mypy --ignore-missing-imports backend/
cd frontend && pnpm lint && pnpm type-check && pnpm build
```

Important: `make lint` and `backend/Makefile` run `ruff --fix` and `ruff format`, so they modify files. Use the non-mutating CI commands above for inspection/checking. CI also runs Bandit + `pip-audit`, frontend `pnpm audit`, and requires backend test coverage of at least 80%.

`book_recommender` must remain feature-gated and local-only. Its base dev environment intentionally does not install NumPy: mock `book_recommender.service._compute_query_vector` in tests that reach it rather than adding NumPy to dev dependencies.

## CI and delivery

- CI is `.forgejo/workflows/ci.yml`, run on Forgejo’s self-hosted runner. Use actions mirrored at `data.forgejo.org`; use `uv` rather than `actions/setup-python`.
- The image is built from the root `Dockerfile`, smoke-tested, and pushed only on `main` to `forgejo.moseisley.es/wind/readingview` using `FORGEJO_TOKEN`.
- Do not change deployment, registry, or CI behavior incidentally while making an application change.

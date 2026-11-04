#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."

# Runtimes and tooling come from the maintained runner, never per-job installers.
node -e 'const [major, minor] = process.versions.node.split(".").map(Number); if (major !== 22 || minor < 12) throw new Error("CI requires Node 22.12+")'
test "$(pnpm --version)" = "10.32.1"
export UV_PYTHON_DOWNLOADS=never
uv sync --project backend --frozen --extra dev --python 3.12

# Run from the root to preserve the project's established mypy configuration.
uv run --project backend --frozen --extra dev ruff check backend/
uv run --project backend --frozen --extra dev ruff format --check backend/
uv run --project backend --frozen --extra dev mypy --ignore-missing-imports backend/
(cd backend && uv run --frozen --extra dev pytest)

(
  cd frontend
  pnpm install --frozen-lockfile
  pnpm lint
  pnpm format:check
  pnpm type-check
  pnpm test
  pnpm build
)

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
(
  cd backend
  SECRET_KEY=ci-openapi-check DATABASE_URL="sqlite+aiosqlite:///$work/openapi.db" \
    COVER_CACHE_ENABLED=false uv run --frozen --extra dev python -c \
    'import json; from app.main import app; print(json.dumps(app.openapi()))'
) > "$work/openapi.json"
(cd frontend && pnpm openapi --spec-path "$work/openapi.json")
git diff --exit-code -- frontend/src/lib/api.generated.ts frontend/src/lib/api.schemas.ts

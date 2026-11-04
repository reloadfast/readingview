#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."

# Pin repository policy and include redacted finding locations in job logs.
gitleaks dir . --config .gitleaks.toml --redact --verbose --exit-code 1
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
(
  cd backend
  uv run --frozen --extra dev bandit -r app book_recommender -c pyproject.toml
  # Audit every installed distribution except our own unpublished source package.
  # Explicit versions avoid resolving dependencies again or suppressing skips
  # with --skip-editable (which conflicts with pip-audit --strict).
  uv run --frozen --extra dev python - <<'PY' > "$work/installed.txt"
from importlib.metadata import distributions

for distribution in sorted(distributions(), key=lambda item: item.metadata["Name"].lower()):
    name = distribution.metadata["Name"]
    if name.lower() != "readingview":
        print(f"{name}=={distribution.version}")
PY
  uv run --frozen --extra dev pip-audit --strict --disable-pip --no-deps \
    --progress-spinner off --requirement "$work/installed.txt"
)
(cd frontend && pnpm audit --audit-level high)

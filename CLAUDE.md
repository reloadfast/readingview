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

---

pluggable book-recommendation module inside an existing Python project.

This module must not run standalone. It is feature-flagged and entirely configured via environment variables.

Core constraints

All AI functionality must run locally using Ollama

No cloud AI services of any kind

Minimize dependencies

Python 3.11+

Linux

SQLite for persistence

All configuration via .env

If the feature is disabled, the module must:

not initialize Ollama

not create vector indexes

not make network calls

expose no side effects

Feature flagging

The module must activate only if:

BOOK_RECOMMENDER_ENABLED=true


If the variable is missing or false:

the module must behave as a no-op

public functions must return empty results or raise a controlled “feature disabled” exception

Environment configuration (authoritative)

All configuration must be read from environment variables only.

Required variables (when enabled):

BOOK_RECOMMENDER_ENABLED=true
BOOK_RECOMMENDER_DB_PATH=/path/to/sqlite.db
BOOK_RECOMMENDER_VECTOR_BACKEND=faiss|python
BOOK_RECOMMENDER_EMBED_MODEL=nomic-embed-text
BOOK_RECOMMENDER_LLM_MODEL=llama3
BOOK_RECOMMENDER_ENABLE_EXPLANATIONS=true|false
BOOK_RECOMMENDER_OLLAMA_URL=http://localhost:11434


Optional tuning variables:

BOOK_RECOMMENDER_TOP_K=10
BOOK_RECOMMENDER_MIN_SIMILARITY=0.2


No defaults may be hardcoded except where unavoidable.

Functional requirements
1. Module boundaries

The feature must expose a single public interface:

book_recommender/
  __init__.py
  service.py


The rest of the implementation is private.

Public API:

def recommend(
    liked_book_ids: list[str] | None = None,
    free_text_prompt: str | None = None,
) -> list[dict]:
    ...


If the feature is disabled:

return []

or raise BookRecommenderDisabled

2. Metadata ingestion (internal only)

Use Open Library API

Support ingestion by ISBN or title

Ingestion must be callable programmatically, not via CLI

Store:

title

authors

description

subjects / genres

ISBNs

3. Embeddings (local only)

Use Ollama HTTP API

Default embedding model from env

Embed:

description + subjects (concatenated)

Cache embeddings in SQLite

Do not recompute embeddings unless content changes

4. Vector similarity search

Backend selected via env:

faiss if available

pure-Python cosine similarity fallback

Index must:

load lazily

rebuild only if embeddings change

No global state

5. Recommendations

Support:

recommendations from one or more liked book IDs

recommendations from free-text prompt

If both provided:

merge embeddings via weighted average

Respect:

TOP_K

MIN_SIMILARITY

6. Optional explanation generation

If:

BOOK_RECOMMENDER_ENABLE_EXPLANATIONS=true


Call local LLM via Ollama

Generate short, structured explanations

Never block recommendations if LLM fails

Hard timeout on LLM calls

Non-functional requirements

No logging to stdout unless enabled by env

Clear error messages for misconfiguration

No background threads

No automatic ingestion

All network calls must be explicit

Integration expectations

The module must be safe to import even when disabled

No side effects on import

All initialization must be lazy

README section describing:

required env vars

how to enable / disable

expected performance characteristics

Implementation approach

Proceed in this order:

Environment parsing & feature gating

SQLite schema

Metadata ingestion

Embedding client

Vector backend

Recommendation logic

Optional explanation layer

Defensive failure modes

Do not build UI, CLI, or background jobs.

Do not assume this is the main application.

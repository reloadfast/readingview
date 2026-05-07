# ── Stage 1: frontend builder ─────────────────────────────────────────────────
FROM node:22-slim AS frontend-builder
WORKDIR /app/frontend
RUN corepack enable
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm build

# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim
WORKDIR /app

ARG GIT_SHA=dev
ENV GIT_SHA=$GIT_SHA
ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -r -u 1001 appuser

COPY backend/ ./backend/
RUN pip install --no-cache-dir -e ./backend/

COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

RUN mkdir -p /data && chown -R appuser /data

LABEL org.opencontainers.image.title="ReadingView"
LABEL org.opencontainers.image.description="Self-hosted audiobook dashboard for Audiobookshelf"
LABEL org.opencontainers.image.source="https://forgejo.moseisley.es/Wind/readingview"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.revision=$GIT_SHA

VOLUME ["/data"]

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -sf http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

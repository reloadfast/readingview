# ── Stage 1: frontend builder ─────────────────────────────────────────────────
FROM node:24.19.0-slim AS frontend-builder
WORKDIR /app/frontend
RUN corepack enable
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm build

# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM forgejo.moseisley.es/wind/readingview-python:3.12.16-alpine3.24@sha256:69ebe56e2a764c399514a0a6117131cb730cc4d0e71e85c08deb9af74cbb9f41
WORKDIR /app

ARG GIT_SHA=dev
ENV GIT_SHA=$GIT_SHA
ENV PYTHONPATH=/app

# Alpine's users group is GID 100, preserving the persistent-volume identity.
RUN apk upgrade --no-cache \
    && apk add --no-cache tzdata \
    && adduser -S -D -H -u 99 -G users appuser

COPY backend/ ./backend/
# Use the same locked runtime dependencies as CI; dev extras stay out of the image.
RUN pip install --no-cache-dir uv==0.13.5 \
    && uv sync --project backend --frozen --no-dev --no-editable --no-cache \
    && pip uninstall --yes uv
ENV PATH="/app/backend/.venv/bin:$PATH"

COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

RUN mkdir -p /data && chown -R 99:100 /data

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

LABEL org.opencontainers.image.title="ReadingView"
LABEL org.opencontainers.image.description="Self-hosted audiobook dashboard for Audiobookshelf"
LABEL org.opencontainers.image.source="https://forgejo.moseisley.es/Wind/readingview"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.revision=$GIT_SHA

VOLUME ["/data"]

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=5).close()"]

CMD ["/entrypoint.sh"]

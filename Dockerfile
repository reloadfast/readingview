# ReadingView — multi-stage build: frontend → backend → runtime

# ── Stage 1: frontend ────────────────────────────────────────────────────────
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
RUN corepack enable
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm build

# ── Stage 2: backend deps ─────────────────────────────────────────────────────
FROM python:3.11-slim AS backend-builder
WORKDIR /app
RUN pip install --no-cache-dir --upgrade pip setuptools
COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir --no-build-isolation --user .

# ── Stage 3: runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim
WORKDIR /app

ARG GIT_SHA=dev
ENV GIT_SHA=$GIT_SHA
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

COPY --from=backend-builder /root/.local /root/.local
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist
COPY backend/ ./backend/

RUN mkdir -p /data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

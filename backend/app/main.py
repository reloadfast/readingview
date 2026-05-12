import json
import logging
import logging.config
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from .api import (
    authors,
    backup,
    collections,
    connections,
    covers,
    goals,
    health,
    library,
    narrators,
    notes,
    notifications,
    recommendations,
    releases,
    series,
    statistics,
)
from .api import (
    settings as settings_router,
)
from .api import (
    ws as ws_router,
)
from .api.ws import manager as ws_manager
from .config import settings
from .db import _AsyncSession
from .models.settings import Settings
from .services import abs_socket as abs_socket_svc
from .services import scheduler as scheduler_svc


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return json.dumps(
            {
                "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
                "level": record.levelname,
                "logger": record.name,
                "msg": record.getMessage(),
            }
        )


def _configure_logging() -> None:
    use_json = settings.LOG_FORMAT.lower() == "json"
    level = settings.LOG_LEVEL.upper()
    cfg: dict = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "text": {
                "format": "%(asctime)s %(levelname)-8s %(name)s — %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            },
            "json": {
                "()": _JsonFormatter,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json" if use_json else "text",
                "stream": "ext://sys.stdout",
            }
        },
        "root": {"level": level, "handlers": ["console"]},
        "loggers": {
            "uvicorn": {"propagate": True, "handlers": []},
            "uvicorn.error": {"propagate": True, "handlers": []},
            "uvicorn.access": {"propagate": True, "handlers": []},
        },
    }
    logging.config.dictConfig(cfg)


_configure_logging()


async def _get_startup_settings() -> tuple[str, str, str, str | None, str | None]:
    async with _AsyncSession() as db:
        await db.execute(
            sqlite_insert(Settings).values(id=1).on_conflict_do_nothing(index_elements=["id"])
        )
        row = await db.get(Settings, 1)
    refresh_cron = row.releases_refresh_cron if row else "0 6 * * *"
    notify_time = row.notify_time if row else "09:00"
    notify_timezone = row.timezone if row else "UTC"
    abs_url = row.abs_url if row else None
    abs_token_enc = row.abs_token if row else None
    return refresh_cron, notify_time, notify_timezone, abs_url, abs_token_enc


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    cron_parts = await _get_startup_settings()
    refresh_cron, notify_time, notify_timezone, abs_url, abs_token_enc = cron_parts
    await scheduler_svc.start(refresh_cron, notify_time, notify_timezone)
    await abs_socket_svc.start(ws_manager, abs_url, abs_token_enc)
    yield
    await abs_socket_svc.stop()
    scheduler_svc.stop()


app = FastAPI(title="ReadingView", lifespan=_lifespan)

if settings.COVER_CACHE_ENABLED:
    from .services.cover_cache import initialize as _init_cache

    _cache_instance = _init_cache(
        settings.COVER_CACHE_DIR,
        settings.COVER_CACHE_MAX_SIZE,
    )

app.include_router(ws_router.router, prefix="/api")
app.include_router(health.router, prefix="/api")
app.include_router(covers.router, prefix="/api")
app.include_router(settings_router.router, prefix="/api")
app.include_router(connections.router, prefix="/api")
app.include_router(library.router, prefix="/api")
app.include_router(statistics.router, prefix="/api")
app.include_router(authors.router, prefix="/api")
app.include_router(series.router, prefix="/api")
app.include_router(releases.router, prefix="/api")
app.include_router(narrators.router, prefix="/api")
app.include_router(collections.router, prefix="/api")
app.include_router(backup.router, prefix="/api")
app.include_router(notes.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(recommendations.router, prefix="/api")
app.include_router(goals.router, prefix="/api")


@app.api_route(
    "/api/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def api_catch_all(path: str) -> JSONResponse:  # noqa: ARG001
    return JSONResponse({"detail": "Not Found"}, status_code=404)


_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"

if _dist.exists():
    app.mount("/assets", StaticFiles(directory=str(_dist / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str) -> FileResponse:  # noqa: ARG001
        return FileResponse(str(_dist / "index.html"))

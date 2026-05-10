import os

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

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
    recommendations,
    releases,
    series,
    settings as settings_router,
    statistics,
)
from .config import settings

_cache_instance: "services.cover_cache.CoverCache | None" = None

if settings.COVER_CACHE_ENABLED:
    from .services.cover_cache import initialize as _init_cache

    _cache_instance = _init_cache(
        settings.COVER_CACHE_DIR,
        settings.COVER_CACHE_MAX_SIZE,
    )

_cache_instance: object | None = None

if settings.COVER_CACHE_ENABLED:
    from .services.cover_cache import initialize

    _cache_instance = initialize(settings.COVER_CACHE_DIR, settings.COVER_CACHE_MAX_SIZE)

app = FastAPI(title="ReadingView")

app.include_router(health.router, prefix="/api")
app.include_router(covers.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
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

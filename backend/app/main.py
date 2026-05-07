from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api import authors, backup, collections, connections, health, library, narrators, recommendations, releases, series, settings, statistics

app = FastAPI(title="ReadingView")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
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
app.include_router(recommendations.router, prefix="/api")

_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"

if _dist.exists():
    app.mount("/assets", StaticFiles(directory=str(_dist / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str) -> FileResponse:  # noqa: ARG001
        return FileResponse(str(_dist / "index.html"))

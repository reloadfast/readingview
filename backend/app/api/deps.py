"""Shared FastAPI dependencies.

``current_settings`` fetches and caches the Settings row on ``request.state``
so routes that call multiple dependencies only hit the DB once per request.

``abs_client`` yields a ready-to-use AudiobookshelfClient, raising 503 when
ABS is not configured.  The client is closed after the request completes.

``abs_cache`` returns the module-level AbsDataCache singleton, raising 503
when ABS is not configured.
"""

from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..crypto import decrypt
from ..db import get_db
from ..models.settings import Settings
from ..services import abs_cache as abs_cache_svc
from ..services.abs_cache import AbsDataCache
from ..services.audiobookshelf import AudiobookshelfClient


async def current_settings(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Settings | None:
    if not hasattr(request.state, "settings"):
        request.state.settings = await db.get(Settings, 1)
    return request.state.settings


async def abs_client(
    settings: Settings | None = Depends(current_settings),
) -> AsyncGenerator[AudiobookshelfClient, None]:
    if not settings or not settings.abs_url or not settings.abs_token:
        raise HTTPException(status_code=503, detail="ABS connection not configured")
    client = AudiobookshelfClient(settings.abs_url, decrypt(settings.abs_token))
    try:
        yield client
    finally:
        await client.aclose()


async def abs_cache(
    settings: Settings | None = Depends(current_settings),
) -> AbsDataCache:
    cache = abs_cache_svc.get()
    if cache is None:
        raise HTTPException(status_code=503, detail="ABS connection not configured")
    return cache

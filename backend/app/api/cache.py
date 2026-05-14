from fastapi import APIRouter, Depends

from ..api.deps import abs_cache
from ..services.abs_cache import AbsDataCache

router = APIRouter()


@router.get("/cache/status")
async def cache_status(cache: AbsDataCache = Depends(abs_cache)) -> dict:
    return cache.status()


@router.post("/cache/refresh", status_code=204)
async def refresh_cache(cache: AbsDataCache = Depends(abs_cache)) -> None:
    cache.invalidate()

import asyncio

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..crypto import decrypt
from ..db import get_db
from ..models.settings import Settings
from ..schemas.series import SeriesDetail, SeriesSummary
from ..services import series as series_svc
from ..services.audiobookshelf import AudiobookshelfClient

router = APIRouter()


async def _get_client(db: AsyncSession) -> AudiobookshelfClient:
    row = await db.get(Settings, 1)
    if not row or not row.abs_url or not row.abs_token:
        raise HTTPException(status_code=503, detail="ABS connection not configured")
    return AudiobookshelfClient(row.abs_url, decrypt(row.abs_token))


async def _fetch_series_data(client: AudiobookshelfClient) -> tuple[list[list[dict]], dict]:
    libraries = await client.get_libraries()
    all_series, progress_map = await asyncio.gather(
        asyncio.gather(*[client.get_library_series(lib["id"]) for lib in libraries]),
        client.get_media_progress_map(),
    )
    return list(all_series), progress_map


@router.get("/series", response_model=list[SeriesSummary])
async def list_series(db: AsyncSession = Depends(get_db)) -> list[SeriesSummary]:
    async with db.begin():
        client = await _get_client(db)

    try:
        all_series, progress_map = await _fetch_series_data(client)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return series_svc.compute_series_list(all_series, progress_map)


@router.get("/series/{series_name}", response_model=SeriesDetail)
async def get_series(
    series_name: str,
    db: AsyncSession = Depends(get_db),
) -> SeriesDetail:
    async with db.begin():
        client = await _get_client(db)

    try:
        all_series, progress_map = await _fetch_series_data(client)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    detail = series_svc.compute_series_detail(series_name, all_series, progress_map)
    if detail is None:
        raise HTTPException(status_code=404, detail="Series not found")
    return detail

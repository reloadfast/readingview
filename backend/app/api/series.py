import asyncio

import httpx
from fastapi import APIRouter, Depends, HTTPException

from ..api.deps import abs_client
from ..schemas.series import SeriesDetail, SeriesSummary
from ..services import series as series_svc
from ..services.audiobookshelf import AudiobookshelfClient

router = APIRouter()


async def _fetch_series_data(client: AudiobookshelfClient) -> tuple[list[list[dict]], dict]:
    libraries = await client.get_libraries()
    all_series, progress_map = await asyncio.gather(
        asyncio.gather(*[client.get_library_series(lib["id"]) for lib in libraries]),
        client.get_media_progress_map(),
    )
    return list(all_series), progress_map


@router.get("/series", response_model=list[SeriesSummary])
async def list_series(
    client: AudiobookshelfClient = Depends(abs_client),
) -> list[SeriesSummary]:
    try:
        all_series, progress_map = await _fetch_series_data(client)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return series_svc.compute_series_list(all_series, progress_map)


@router.get("/series/{series_name}", response_model=SeriesDetail)
async def get_series(
    series_name: str,
    client: AudiobookshelfClient = Depends(abs_client),
) -> SeriesDetail:
    try:
        all_series, progress_map = await _fetch_series_data(client)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    detail = series_svc.compute_series_detail(series_name, all_series, progress_map)
    if detail is None:
        raise HTTPException(status_code=404, detail="Series not found")
    return detail

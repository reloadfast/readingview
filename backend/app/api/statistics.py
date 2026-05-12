import asyncio
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query

from ..api.deps import abs_client
from ..schemas.statistics import HeatmapData, OverallStats, RecapStats, YearlyStats
from ..services import statistics as stats_svc
from ..services.audiobookshelf import AudiobookshelfClient

router = APIRouter()


@router.get("/statistics", response_model=OverallStats)
async def get_statistics(
    client: AudiobookshelfClient = Depends(abs_client),
) -> OverallStats:
    try:
        progress_map, listening_stats, sessions = await asyncio.gather(
            client.get_media_progress_map(),
            client.get_user_listening_stats(),
            client.get_user_listening_sessions(),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return stats_svc.compute_overall_stats(progress_map, listening_stats, sessions)


@router.get("/statistics/yearly", response_model=YearlyStats)
async def get_yearly_stats(
    year: str = Query(default=str(datetime.now().year)),
    client: AudiobookshelfClient = Depends(abs_client),
) -> YearlyStats:
    try:
        progress_map, listening_stats = await asyncio.gather(
            client.get_media_progress_map(),
            client.get_user_listening_stats(),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return stats_svc.compute_yearly_stats(year, progress_map, listening_stats)


@router.get("/statistics/recap", response_model=RecapStats)
async def get_recap(
    year: str = Query(default=str(datetime.now().year)),
    client: AudiobookshelfClient = Depends(abs_client),
) -> RecapStats:
    try:
        progress_map, listening_stats = await asyncio.gather(
            client.get_media_progress_map(),
            client.get_user_listening_stats(),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return stats_svc.compute_recap(year, progress_map, listening_stats)


@router.get("/statistics/heatmap", response_model=HeatmapData)
async def get_heatmap(
    year: str = Query(default=str(datetime.now().year)),
    client: AudiobookshelfClient = Depends(abs_client),
) -> HeatmapData:
    try:
        sessions = await client.get_user_listening_sessions()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return stats_svc.compute_heatmap(year, sessions)

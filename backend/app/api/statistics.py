import asyncio
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..crypto import decrypt
from ..db import get_db
from ..models.settings import Settings
from ..schemas.statistics import OverallStats, RecapStats, YearlyStats
from ..services import statistics as stats_svc
from ..services.audiobookshelf import AudiobookshelfClient

router = APIRouter()


async def _get_client(db: AsyncSession) -> AudiobookshelfClient:
    row = await db.get(Settings, 1)
    if not row or not row.abs_url or not row.abs_token:
        raise HTTPException(status_code=503, detail="ABS connection not configured")
    return AudiobookshelfClient(row.abs_url, decrypt(row.abs_token))


@router.get("/statistics", response_model=OverallStats)
async def get_statistics(db: AsyncSession = Depends(get_db)) -> OverallStats:
    async with db.begin():
        client = await _get_client(db)

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
    year: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> YearlyStats:
    resolved_year = year or str(datetime.now().year)
    async with db.begin():
        client = await _get_client(db)

    try:
        progress_map, listening_stats = await asyncio.gather(
            client.get_media_progress_map(),
            client.get_user_listening_stats(),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return stats_svc.compute_yearly_stats(resolved_year, progress_map, listening_stats)


@router.get("/statistics/recap", response_model=RecapStats)
async def get_recap(
    year: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> RecapStats:
    resolved_year = year or str(datetime.now().year)
    async with db.begin():
        client = await _get_client(db)

    try:
        progress_map, listening_stats = await asyncio.gather(
            client.get_media_progress_map(),
            client.get_user_listening_stats(),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return stats_svc.compute_recap(resolved_year, progress_map, listening_stats)

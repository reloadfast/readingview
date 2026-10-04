import asyncio
from datetime import datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..api.deps import abs_cache, current_settings
from ..db import get_db
from ..models.goals import ReadingGoal
from ..models.settings import Settings
from ..schemas.statistics import (
    AuthorNarratorAffinity,
    BacklogHealth,
    BookLengthPreferences,
    CompletionVelocity,
    DurationCompletionCorrelation,
    ExtraListening,
    GenreCompletionCorrelation,
    GoalForecast,
    HeatmapData,
    ListeningHabits,
    MonthlyComparison,
    OverallStats,
    RecapStats,
    SeriesProgress,
    StatisticsDetail,
    YearlyStats,
)
from ..services import statistics as stats_svc
from ..services.abs_cache import AbsDataCache

router = APIRouter()


@router.get("/statistics", response_model=OverallStats)
async def get_statistics(
    client: AbsDataCache = Depends(abs_cache),
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
    client: AbsDataCache = Depends(abs_cache),
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
    client: AbsDataCache = Depends(abs_cache),
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
    client: AbsDataCache = Depends(abs_cache),
    settings: Settings | None = Depends(current_settings),
) -> HeatmapData:
    try:
        sessions = await client.get_user_listening_sessions()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    timezone = settings.timezone if settings else "UTC"
    return stats_svc.compute_heatmap(year, sessions, timezone)


@router.get("/statistics/habits", response_model=ListeningHabits)
async def get_listening_habits(
    year: str = Query(default=str(datetime.now().year)),
    client: AbsDataCache = Depends(abs_cache),
    settings: Settings | None = Depends(current_settings),
) -> ListeningHabits:
    try:
        sessions = await client.get_user_listening_sessions()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    timezone = settings.timezone if settings else "UTC"
    return stats_svc.compute_listening_habits(year, sessions, timezone)


@router.get("/statistics/completion-velocity", response_model=CompletionVelocity)
async def get_completion_velocity(
    year: str = Query(default=str(datetime.now().year)),
    client: AbsDataCache = Depends(abs_cache),
    settings: Settings | None = Depends(current_settings),
) -> CompletionVelocity:
    try:
        progress_map, listening_stats = await asyncio.gather(
            client.get_media_progress_map(),
            client.get_user_listening_stats(),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    timezone = settings.timezone if settings else "UTC"
    return stats_svc.compute_completion_velocity(year, progress_map, listening_stats, timezone)


@router.get("/statistics/monthly-comparison", response_model=MonthlyComparison)
async def get_monthly_comparison(
    year: str = Query(default=str(datetime.now().year)),
    client: AbsDataCache = Depends(abs_cache),
    settings: Settings | None = Depends(current_settings),
) -> MonthlyComparison:
    try:
        progress_map, listening_stats, sessions = await asyncio.gather(
            client.get_media_progress_map(),
            client.get_user_listening_stats(),
            client.get_user_listening_sessions(),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    timezone = settings.timezone if settings else "UTC"
    return stats_svc.compute_monthly_comparison(
        year, progress_map, listening_stats, sessions, timezone
    )


@router.get("/statistics/book-length-preferences", response_model=BookLengthPreferences)
async def get_book_length_preferences(
    year: str = Query(default=str(datetime.now().year)),
    client: AbsDataCache = Depends(abs_cache),
    settings: Settings | None = Depends(current_settings),
) -> BookLengthPreferences:
    try:
        progress_map, listening_stats = await asyncio.gather(
            client.get_media_progress_map(),
            client.get_user_listening_stats(),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    timezone = settings.timezone if settings else "UTC"
    return stats_svc.compute_book_length_preferences(year, progress_map, listening_stats, timezone)


@router.get("/statistics/goal-forecast", response_model=GoalForecast)
async def get_goal_forecast(
    year: int = Query(default=datetime.now().year),
    client: AbsDataCache = Depends(abs_cache),
    settings: Settings | None = Depends(current_settings),
    db: AsyncSession = Depends(get_db),
) -> GoalForecast:
    goal = await db.get(ReadingGoal, year)
    if goal is None:
        return GoalForecast(year=year, has_goal=False)
    try:
        progress_map, listening_stats = await asyncio.gather(
            client.get_media_progress_map(),
            client.get_user_listening_stats(),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    timezone = settings.timezone if settings else "UTC"
    return stats_svc.compute_goal_forecast(
        year, goal.target_books, progress_map, listening_stats, timezone
    )


@router.get("/statistics/backlog-health", response_model=BacklogHealth)
async def get_backlog_health(
    client: AbsDataCache = Depends(abs_cache),
) -> BacklogHealth:
    try:
        library_items, progress_map = await asyncio.gather(
            client.get_all_library_items(),
            client.get_media_progress_map(),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return stats_svc.compute_backlog_health(library_items, progress_map)


@router.get("/statistics/series-progress", response_model=list[SeriesProgress])
async def get_series_progress(
    client: AbsDataCache = Depends(abs_cache),
) -> list[SeriesProgress]:
    try:
        libraries = await client.get_libraries()
        all_series, progress_map = await asyncio.gather(
            asyncio.gather(*[client.get_library_series(library["id"]) for library in libraries]),
            client.get_media_progress_map(),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return stats_svc.compute_series_progress(list(all_series), progress_map)


@router.get("/statistics/affinity", response_model=AuthorNarratorAffinity)
async def get_author_narrator_affinity(
    client: AbsDataCache = Depends(abs_cache),
) -> AuthorNarratorAffinity:
    try:
        library_items, progress_map, listening_stats = await asyncio.gather(
            client.get_all_library_items(),
            client.get_media_progress_map(),
            client.get_user_listening_stats(),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return stats_svc.compute_author_narrator_affinity(library_items, progress_map, listening_stats)


@router.get("/statistics/genre-completion", response_model=list[GenreCompletionCorrelation])
async def get_genre_completion_correlation(
    client: AbsDataCache = Depends(abs_cache),
) -> list[GenreCompletionCorrelation]:
    try:
        library_items, progress_map = await asyncio.gather(
            client.get_all_library_items(),
            client.get_media_progress_map(),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return stats_svc.compute_genre_completion_correlation(library_items, progress_map)


@router.get("/statistics/duration-completion", response_model=DurationCompletionCorrelation)
async def get_duration_completion_correlation(
    year: str = Query(default=str(datetime.now().year)),
    client: AbsDataCache = Depends(abs_cache),
    settings: Settings | None = Depends(current_settings),
) -> DurationCompletionCorrelation:
    try:
        progress_map, listening_stats = await asyncio.gather(
            client.get_media_progress_map(),
            client.get_user_listening_stats(),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    timezone = settings.timezone if settings else "UTC"
    return stats_svc.compute_duration_completion_correlation(
        year, progress_map, listening_stats, timezone
    )


@router.get("/statistics/extra-listening", response_model=ExtraListening)
async def get_extra_listening(
    year: str = Query(default=str(datetime.now().year)),
    client: AbsDataCache = Depends(abs_cache),
    settings: Settings | None = Depends(current_settings),
) -> ExtraListening:
    try:
        progress_map, listening_stats = await asyncio.gather(
            client.get_media_progress_map(),
            client.get_user_listening_stats(),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    timezone = settings.timezone if settings else "UTC"
    return stats_svc.compute_extra_listening(year, progress_map, listening_stats, timezone)


@router.get("/statistics/detail", response_model=StatisticsDetail)
async def get_statistics_detail(
    year: str = Query(default=str(datetime.now().year)),
    client: AbsDataCache = Depends(abs_cache),
    settings: Settings | None = Depends(current_settings),
) -> StatisticsDetail:
    try:
        progress_map, listening_stats, sessions = await asyncio.gather(
            client.get_media_progress_map(),
            client.get_user_listening_stats(),
            client.get_user_listening_sessions(),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    timezone = settings.timezone if settings else "UTC"
    return stats_svc.compute_statistics_detail(
        year, progress_map, listening_stats, sessions, timezone
    )

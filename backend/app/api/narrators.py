import asyncio

import httpx
from fastapi import APIRouter, Depends, HTTPException

from ..api.deps import abs_cache
from ..schemas.narrators import NarratorDetail, NarratorSummary
from ..services import narrators as narrator_svc
from ..services.abs_cache import AbsDataCache

router = APIRouter()


@router.get("/narrators", response_model=list[NarratorSummary])
async def list_narrators(
    client: AbsDataCache = Depends(abs_cache),
) -> list[NarratorSummary]:
    try:
        items, progress_map = await asyncio.gather(
            client.get_all_library_items(),
            client.get_media_progress_map(),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return narrator_svc.compute_narrator_list(items, progress_map)


@router.get("/narrators/{narrator_name}", response_model=NarratorDetail)
async def get_narrator(
    narrator_name: str,
    client: AbsDataCache = Depends(abs_cache),
) -> NarratorDetail:
    try:
        items, progress_map = await asyncio.gather(
            client.get_all_library_items(),
            client.get_media_progress_map(),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    detail = narrator_svc.compute_narrator_detail(narrator_name, items, progress_map)
    if detail is None:
        raise HTTPException(status_code=404, detail="Narrator not found")
    return detail

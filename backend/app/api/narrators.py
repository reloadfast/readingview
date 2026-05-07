import asyncio

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..crypto import decrypt
from ..db import get_db
from ..models.settings import Settings
from ..schemas.narrators import NarratorDetail, NarratorSummary
from ..services import narrators as narrator_svc
from ..services.audiobookshelf import AudiobookshelfClient

router = APIRouter()


async def _get_client(db: AsyncSession) -> AudiobookshelfClient:
    row = await db.get(Settings, 1)
    if not row or not row.abs_url or not row.abs_token:
        raise HTTPException(status_code=503, detail="ABS connection not configured")
    return AudiobookshelfClient(row.abs_url, decrypt(row.abs_token))


@router.get("/narrators", response_model=list[NarratorSummary])
async def list_narrators(db: AsyncSession = Depends(get_db)) -> list[NarratorSummary]:
    async with db.begin():
        client = await _get_client(db)

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
    db: AsyncSession = Depends(get_db),
) -> NarratorDetail:
    async with db.begin():
        client = await _get_client(db)

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

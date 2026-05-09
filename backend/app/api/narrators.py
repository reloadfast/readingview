import asyncio

from fastapi import APIRouter, Depends, HTTPException

from ..api.deps import abs_client
from ..schemas.narrators import NarratorDetail, NarratorSummary
from ..services import narrators as narrator_svc
from ..services.audiobookshelf import AudiobookshelfClient

router = APIRouter()


@router.get("/narrators", response_model=list[NarratorSummary])
async def list_narrators(
    client: AudiobookshelfClient = Depends(abs_client),
) -> list[NarratorSummary]:
    items, progress_map = await asyncio.gather(
        client.get_all_library_items(),
        client.get_media_progress_map(),
    )

    return narrator_svc.compute_narrator_list(items, progress_map)


@router.get("/narrators/{narrator_name}", response_model=NarratorDetail)
async def get_narrator(
    narrator_name: str,
    client: AudiobookshelfClient = Depends(abs_client),
) -> NarratorDetail:
    items, progress_map = await asyncio.gather(
        client.get_all_library_items(),
        client.get_media_progress_map(),
    )

    detail = narrator_svc.compute_narrator_detail(narrator_name, items, progress_map)
    if detail is None:
        raise HTTPException(status_code=404, detail="Narrator not found")
    return detail

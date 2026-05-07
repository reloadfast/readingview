from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..services.recommendations import get_recommendations, get_status, run_ingest

router = APIRouter()


class IngestRequest(BaseModel):
    isbn: str | None = None
    title: str | None = None
    author: str | None = None
    work_key: str | None = None


class IngestResponse(BaseModel):
    book_id: str


class StatusResponse(BaseModel):
    enabled: bool
    model: str | None
    vector_backend: str | None


@router.get("/recommendations")
async def recommendations(
    book_ids: str | None = None,
    prompt: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    ids = [b.strip() for b in book_ids.split(",") if b.strip()] if book_ids else None
    return await get_recommendations(db, book_ids=ids, prompt=prompt)


@router.post("/recommendations/ingest", response_model=IngestResponse)
async def ingest(
    body: IngestRequest,
    db: AsyncSession = Depends(get_db),
) -> IngestResponse:
    if not any([body.isbn, body.title, body.work_key]):
        raise HTTPException(status_code=422, detail="Provide isbn, title, or work_key")

    status = await get_status(db)
    if not status["enabled"]:
        raise HTTPException(status_code=404, detail="Book recommender is not enabled")

    book_id = await run_ingest(
        db,
        isbn=body.isbn,
        title=body.title,
        author=body.author,
        work_key=body.work_key,
    )
    if book_id is None:
        raise HTTPException(status_code=422, detail="Ingestion failed — book not found")
    return IngestResponse(book_id=book_id)


@router.get("/recommendations/status", response_model=StatusResponse)
async def recommendations_status(db: AsyncSession = Depends(get_db)) -> StatusResponse:
    status = await get_status(db)
    return StatusResponse(**status)

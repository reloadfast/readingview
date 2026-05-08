import time

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..models.notes import BookNote
from ..schemas.notes import NoteOut, NotePut

router = APIRouter()


@router.get("/notes/{abs_item_id}", response_model=NoteOut)
async def get_note(abs_item_id: str, db: AsyncSession = Depends(get_db)) -> NoteOut:
    async with db.begin():
        row = await db.get(BookNote, abs_item_id)
    return NoteOut(body=row.body if row else None)


@router.put("/notes/{abs_item_id}", response_model=NoteOut)
async def upsert_note(
    abs_item_id: str,
    payload: NotePut,
    db: AsyncSession = Depends(get_db),
) -> NoteOut:
    async with db.begin():
        row = await db.get(BookNote, abs_item_id)
        if row is None:
            row = BookNote(abs_item_id=abs_item_id, body=payload.body, updated_at=time.time())
            db.add(row)
        else:
            row.body = payload.body
            row.updated_at = time.time()
    return NoteOut(body=row.body)


@router.delete("/notes/{abs_item_id}", status_code=204)
async def delete_note(abs_item_id: str, db: AsyncSession = Depends(get_db)) -> None:
    async with db.begin():
        row = await db.get(BookNote, abs_item_id)
        if row is not None:
            await db.delete(row)

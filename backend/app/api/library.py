import asyncio
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..api.deps import abs_client
from ..db import get_db
from ..models.notes import BookNote
from ..schemas.library import BookProgress, LibraryBook, SeriesEntry
from ..services.audiobookshelf import AudiobookshelfClient

router = APIRouter()


def _parse_progress(raw: dict, duration: float) -> BookProgress:
    current_time = raw.get("currentTime", 0) or 0
    return BookProgress(
        is_finished=raw.get("isFinished", False),
        progress_pct=(raw.get("progress", 0) or 0) * 100,
        current_time=current_time,
        time_remaining=max(0.0, duration - current_time),
        started_at=raw.get("startedAt"),
        finished_at=raw.get("finishedAt"),
        last_update=raw.get("lastUpdate"),
    )


def _parse_series(raw_series: list) -> list[SeriesEntry]:
    entries = []
    for s in raw_series or []:
        if isinstance(s, dict):
            entries.append(SeriesEntry(name=s.get("name", ""), sequence=s.get("sequence")))
        elif isinstance(s, str):
            entries.append(SeriesEntry(name=s))
    return entries


def _item_to_book(item: dict, progress_map: dict, cover_url_fn) -> LibraryBook:
    media = item.get("media", {})
    meta = media.get("metadata", {})
    item_id = item.get("id", "")
    duration = media.get("duration", 0) or 0

    progress_raw = (
        progress_map.get(item_id)
        or item.get("userMediaProgress")
        or item.get("mediaProgress")
        or {}
    )
    progress = _parse_progress(progress_raw, duration) if progress_raw else None

    return LibraryBook(
        id=item_id,
        title=meta.get("title", "Unknown Title"),
        authors=meta.get("authorName", "Unknown Author"),
        narrator=meta.get("narratorName"),
        series=_parse_series(meta.get("series", [])),
        cover_url=cover_url_fn(item_id),
        duration=duration,
        genres=meta.get("genres", []),
        description=meta.get("description"),
        published_year=meta.get("publishedYear"),
        isbn=meta.get("isbn"),
        asin=meta.get("asin"),
        progress=progress,
    )


def _sort_books(
    books: list[LibraryBook],
    sort: str,
) -> list[LibraryBook]:
    if sort == "title":
        return sorted(books, key=lambda b: b.title.lower())
    if sort == "progress_asc":
        return sorted(books, key=lambda b: b.progress.progress_pct if b.progress else 0.0)
    if sort == "progress_desc":
        return sorted(
            books, key=lambda b: b.progress.progress_pct if b.progress else 0.0, reverse=True
        )
    if sort == "updated":
        return sorted(
            books,
            key=lambda b: b.progress.last_update if b.progress and b.progress.last_update else 0,
            reverse=True,
        )
    if sort == "finished":
        return sorted(
            books,
            key=lambda b: b.progress.finished_at if b.progress and b.progress.finished_at else 0,
            reverse=True,
        )
    return books


@router.get("/library", response_model=list[LibraryBook])
async def get_library(
    search: str | None = Query(default=None),
    sort: Literal["title", "progress_asc", "progress_desc", "updated", "finished"] = Query(
        default="updated"
    ),
    page: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
    client: AudiobookshelfClient = Depends(abs_client),
    db: AsyncSession = Depends(get_db),
) -> list[LibraryBook]:
    items, progress_map = await _parallel_fetch(client)

    books = [_item_to_book(item, progress_map, client.cover_url) for item in items]

    if search:
        q = search.lower()
        async with db.begin():
            rows = (await db.execute(select(BookNote))).scalars().all()
        notes_map = {r.abs_item_id: r.body.lower() for r in rows}
        books = [
            b
            for b in books
            if q in b.title.lower()
            or q in b.authors.lower()
            or any(q in s.name.lower() for s in b.series)
            or q in notes_map.get(b.id, "")
        ]

    books = _sort_books(books, sort)
    return books[page * limit : (page + 1) * limit]


async def _parallel_fetch(client: AudiobookshelfClient):
    items_task = asyncio.create_task(client.get_all_library_items())
    progress_task = asyncio.create_task(client.get_media_progress_map())
    items = await items_task
    progress_map = await progress_task
    return items, progress_map


@router.get("/library/in-progress", response_model=list[LibraryBook])
async def get_in_progress(
    client: AudiobookshelfClient = Depends(abs_client),
) -> list[LibraryBook]:
    items_task = asyncio.create_task(client.get_user_items_in_progress())
    progress_task = asyncio.create_task(client.get_media_progress_map())
    items = await items_task
    progress_map = await progress_task

    return [_item_to_book(item, progress_map, client.cover_url) for item in items]


@router.get("/library/{item_id}", response_model=LibraryBook)
async def get_library_item(
    item_id: str,
    client: AudiobookshelfClient = Depends(abs_client),
) -> LibraryBook:
    item_task = asyncio.create_task(client.get_item(item_id))
    progress_task = asyncio.create_task(client.get_media_progress_map())
    item = await item_task
    progress_map = await progress_task

    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    return _item_to_book(item, progress_map, client.cover_url)

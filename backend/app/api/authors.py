import time

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..api.deps import abs_client
from ..db import get_db
from ..models.authors import TrackedAuthor
from ..schemas.authors import FollowRequest, LibraryAuthor, OLAuthorResult, TrackedAuthorOut
from ..services.openlibrary import OpenLibraryClient

router = APIRouter()

_OL = OpenLibraryClient()


def _extract_abs_authors(items: list[dict]) -> list[LibraryAuthor]:
    counts: dict[str, int] = {}
    for item in items:
        raw_authors = item.get("media", {}).get("metadata", {}).get("authors", [])
        for a in raw_authors:
            name = a.get("name", "").strip() if isinstance(a, dict) else str(a).strip()
            if name:
                counts[name] = counts.get(name, 0) + 1
    return sorted(
        [LibraryAuthor(name=n, book_count=c) for n, c in counts.items()],
        key=lambda x: x.name,
    )


# /authors/search must be registered before /authors so it isn't shadowed
@router.get("/authors/search", response_model=list[OLAuthorResult])
async def search_authors(q: str = Query(..., min_length=1)) -> list[OLAuthorResult]:
    try:
        docs = await _OL.search_authors(q, limit=10)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    results = []
    for doc in docs:
        ol_key = OpenLibraryClient.normalise_key(doc.get("key", ""))
        if not ol_key:
            continue
        photos = doc.get("photos", [])
        photo_url: str | None = None
        if photos and photos[0] and photos[0] != -1:
            photo_url = f"https://covers.openlibrary.org/a/id/{photos[0]}-M.jpg"
        results.append(
            OLAuthorResult(
                ol_key=ol_key,
                name=doc.get("name", ""),
                birth_date=doc.get("birth_date"),
                death_date=doc.get("death_date"),
                photo_url=photo_url,
                top_work=doc.get("top_work"),
                work_count=doc.get("work_count", 0),
            )
        )
    return results


@router.get("/authors/library", response_model=list[LibraryAuthor])
async def get_library_authors(
    client: AudiobookshelfClient = Depends(abs_client),
    db: AsyncSession = Depends(get_db),
) -> list[LibraryAuthor]:
    try:
        items = await client.get_all_library_items()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return _extract_abs_authors(items)


@router.get("/authors", response_model=list[TrackedAuthorOut])
async def list_followed_authors(db: AsyncSession = Depends(get_db)) -> list[TrackedAuthorOut]:
    async with db.begin():
        result = await db.execute(select(TrackedAuthor).order_by(TrackedAuthor.name))
        rows = result.scalars().all()
        return [TrackedAuthorOut.model_validate(r, from_attributes=True) for r in rows]


@router.post("/authors", response_model=TrackedAuthorOut, status_code=201)
async def follow_author(
    body: FollowRequest,
    db: AsyncSession = Depends(get_db),
) -> TrackedAuthorOut:
    try:
        if body.ol_key:
            details = await _OL.get_author_details(body.ol_key)
            ol_key = body.ol_key
        else:
            docs = await _OL.search_authors(body.name, limit=1)
            if not docs:
                raise HTTPException(status_code=404, detail="Author not found on Open Library")
            ol_key = OpenLibraryClient.normalise_key(docs[0].get("key", ""))
            details = await _OL.get_author_details(ol_key) if ol_key else None
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    bio_raw = details.get("bio") if details else None
    bio = bio_raw if isinstance(bio_raw, str) else (bio_raw.get("value", "") if bio_raw else None)

    async with db.begin():
        where = TrackedAuthor.name == body.name
        if ol_key:
            where = or_(where, TrackedAuthor.ol_key == ol_key)
        existing = (await db.execute(select(TrackedAuthor).where(where))).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=409, detail="Author already followed")

        author = TrackedAuthor(
            name=body.name,
            ol_key=ol_key or None,
            photo_url=OpenLibraryClient.photo_url(details) if details else None,
            bio=bio,
            birth_date=details.get("birth_date") if details else None,
            death_date=details.get("death_date") if details else None,
            followed_at=int(time.time() * 1000),
        )
        db.add(author)

    await db.refresh(author)
    return TrackedAuthorOut.model_validate(author)


@router.delete("/authors/{author_key}", status_code=204)
async def unfollow_author(
    author_key: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    async with db.begin():
        row = (
            await db.execute(
                select(TrackedAuthor).where(TrackedAuthor.ol_key == author_key)
            )
        ).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Author not followed")
        await db.delete(row)

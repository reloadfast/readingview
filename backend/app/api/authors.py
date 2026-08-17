import asyncio
import hashlib
import logging
import time

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..api.deps import abs_cache
from ..db import get_db
from ..models.authors import TrackedAuthor
from ..schemas.authors import (
    AuthorDetail,
    FollowRequest,
    LibraryAuthor,
    OLAuthorResult,
    TrackedAuthorOut,
)
from ..services import authors as author_svc
from ..services.abs_cache import AbsDataCache
from ..services.cover_cache import get as get_cover_cache
from ..services.openlibrary import OpenLibraryClient

router = APIRouter()

_OL = OpenLibraryClient()
logger = logging.getLogger(__name__)
_PHOTO_CACHE_MAX_AGE = 604800  # one week


def _author_to_out(author: TrackedAuthor) -> TrackedAuthorOut:
    """Expose cached local portrait URLs instead of Open Library URLs."""
    photo_url = f"/api/authors/{author.id}/photo" if author.photo_url else None
    return TrackedAuthorOut.model_validate(author).model_copy(update={"photo_url": photo_url})


def _compute_etag(data: bytes) -> str:
    return f'"{hashlib.sha256(data, usedforsecurity=False).hexdigest()[:16]}"'


def _extract_abs_authors(items: list[dict]) -> list[LibraryAuthor]:
    counts: dict[str, int] = {}
    for item in items:
        metadata = item.get("media", {}).get("metadata", {})
        raw_authors = metadata.get("authors", [])
        if raw_authors:
            names = [
                a.get("name", "").strip() if isinstance(a, dict) else str(a).strip()
                for a in raw_authors
            ]
        else:
            author_name_str = metadata.get("authorName", "").strip()
            names = [n.strip() for n in author_name_str.split(",") if n.strip()]
        for name in names:
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


@router.get("/authors/library/{author_name}", response_model=AuthorDetail)
async def get_library_author_detail(
    author_name: str,
    client: AbsDataCache = Depends(abs_cache),
) -> AuthorDetail:
    try:
        items, progress_map = await asyncio.gather(
            client.get_all_library_items(),
            client.get_media_progress_map(),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    detail = author_svc.compute_author_detail(author_name, items, progress_map)
    if detail is None:
        raise HTTPException(status_code=404, detail="Author not found")
    return detail


@router.get("/authors/library", response_model=list[LibraryAuthor])
async def get_library_authors(
    client: AbsDataCache = Depends(abs_cache),
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
        return [_author_to_out(row) for row in rows]


@router.post("/authors", response_model=TrackedAuthorOut, status_code=201)
async def follow_author(
    body: FollowRequest,
    db: AsyncSession = Depends(get_db),
) -> TrackedAuthorOut:
    if body.ol_key:
        ol_key = OpenLibraryClient.normalise_key(body.ol_key)
        search_data: dict = {"key": f"/authors/{ol_key}"}
    else:
        docs: list[dict] | None
        try:
            docs = await _OL.search_authors(body.name, limit=1)
        except httpx.HTTPError as exc:
            # Following a local library author must not depend on Open Library
            # being available.  Release tracking can use the author name alone.
            logger.warning(
                "Could not look up followed author %r: %s", body.name, type(exc).__name__
            )
            docs = None
        if docs is None:
            ol_key = ""
            search_data = {}
        elif docs:
            ol_key = OpenLibraryClient.normalise_key(docs[0].get("key", ""))
            search_data = docs[0]
        else:
            raise HTTPException(status_code=404, detail="Author not found on Open Library")

    details: dict | None = None
    if ol_key:
        try:
            details = await _OL.get_author_details(ol_key)
        except httpx.HTTPError as exc:
            logger.warning("Could not enrich followed author %r: %s", body.name, type(exc).__name__)

    author_data = details or search_data
    bio_raw = author_data.get("bio")
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
            photo_url=OpenLibraryClient.photo_url(author_data),
            bio=bio,
            birth_date=author_data.get("birth_date"),
            death_date=author_data.get("death_date"),
            followed_at=int(time.time() * 1000),
        )
        db.add(author)

    await db.refresh(author)
    return _author_to_out(author)


@router.get("/authors/{author_id}/photo", include_in_schema=False)
async def get_author_photo(author_id: int, db: AsyncSession = Depends(get_db)) -> Response:
    async with db.begin():
        author = await db.get(TrackedAuthor, author_id)
        source_url = author.photo_url if author else None
    if source_url is None:
        raise HTTPException(status_code=404, detail="Author photo not found")

    cache_key = f"author-photo:{source_url}"
    if cache := get_cover_cache():
        cached = await cache.get(cache_key)
        if cached is not None:
            return Response(
                content=cached,
                media_type="image/jpeg",
                headers={
                    "Cache-Control": f"public, max-age={_PHOTO_CACHE_MAX_AGE}",
                    "ETag": _compute_etag(cached),
                },
            )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            remote = await client.get(source_url)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail="Could not fetch author photo") from exc
    if not remote.is_success:
        raise HTTPException(status_code=502, detail="Could not fetch author photo")

    if cache := get_cover_cache():
        await cache.put(cache_key, remote.content)
    return Response(
        content=remote.content,
        media_type=remote.headers.get("content-type", "image/jpeg"),
        headers={
            "Cache-Control": f"public, max-age={_PHOTO_CACHE_MAX_AGE}",
            "ETag": _compute_etag(remote.content),
        },
    )


@router.delete("/authors/{author_key}", status_code=204)
async def unfollow_author(
    author_key: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    async with db.begin():
        row = (
            await db.execute(select(TrackedAuthor).where(TrackedAuthor.ol_key == author_key))
        ).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Author not followed")
        await db.delete(row)

import hashlib
import json
import logging
import time
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..config import settings
from ..db import get_db
from ..models.releases import ManualRelease, Release, ReleaseTrackedAuthor
from ..schemas.releases import (
    ManualReleaseCreate,
    ManualReleaseOut,
    ManualReleasePatch,
    PatchReleaseRequest,
    RefreshResult,
    ReleaseOut,
    ReleaseTrackedAuthorOut,
    TrackAuthorRequest,
)
from ..services import release_tracker as rt_svc

logger = logging.getLogger(__name__)

router = APIRouter()


# --- helpers ---


def _release_to_out(r: Release) -> ReleaseOut:
    return ReleaseOut(
        id=r.id,
        title=r.title,
        author_name=r.author.name,
        release_date=r.release_date,
        release_date_confirmed=r.release_date_confirmed,
        book_number=r.book_number,
        ol_key=r.ol_key,
        link_url=r.link_url,
        notes=r.notes,
        source=r.source,
    )


def _manual_dedupe_key(
    author: str | None, title: str | None, release_date: str | None, media: list[str]
) -> str:
    """Use the identifying fields agreed for local records, independent of formatting."""
    parts = [
        (author or "").strip().casefold(),
        (title or "").strip().casefold(),
        (release_date or "").strip().casefold(),
        ",".join(sorted(m.casefold() for m in media)),
    ]
    return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()


def _manual_to_out(row: ManualRelease) -> ManualReleaseOut:
    return ManualReleaseOut(
        id=row.id,
        author=row.author,
        title=row.title,
        series=row.series,
        series_number=row.series_number,
        release_date=row.release_date,
        media=json.loads(row.media) if row.media else [],
        cover_url=row.cover_url,
        uploaded_cover_url=(f"/api/releases/manual/{row.id}/cover" if row.cover_filename else None),
        link_url=row.link_url,
        comments=row.comments,
        last_checked_at=row.last_checked_at,
        updated_at=row.updated_at,
        status=row.status,  # type: ignore[arg-type]
        archived=row.archived,
    )


def _clean_optional(value: str | None) -> str | None:
    value = value.strip() if value else None
    return value or None


def _cover_dir() -> Path:
    path = Path(settings.MANUAL_RELEASE_COVER_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


# --- tracked authors ---


@router.get("/releases/tracked-authors", response_model=list[ReleaseTrackedAuthorOut])
async def list_tracked_authors(db: AsyncSession = Depends(get_db)) -> list[ReleaseTrackedAuthorOut]:
    async with db.begin():
        result = await db.execute(select(ReleaseTrackedAuthor).order_by(ReleaseTrackedAuthor.name))
        rows = result.scalars().all()
        return [ReleaseTrackedAuthorOut.model_validate(r, from_attributes=True) for r in rows]


@router.post("/releases/tracked-authors", response_model=ReleaseTrackedAuthorOut, status_code=201)
async def track_author(
    body: TrackAuthorRequest,
    db: AsyncSession = Depends(get_db),
) -> ReleaseTrackedAuthorOut:
    async with db.begin():
        where = ReleaseTrackedAuthor.name == body.name
        if body.ol_key:
            from sqlalchemy import or_

            where = or_(where, ReleaseTrackedAuthor.ol_key == body.ol_key)
        existing = (
            await db.execute(select(ReleaseTrackedAuthor).where(where))
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=409, detail="Author already tracked")

        author = ReleaseTrackedAuthor(
            name=body.name,
            ol_key=body.ol_key or None,
            added_at=int(time.time() * 1000),
        )
        db.add(author)

    await db.refresh(author)
    return ReleaseTrackedAuthorOut.model_validate(author)


@router.delete("/releases/tracked-authors/{author_id}", status_code=204)
async def untrack_author(
    author_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    async with db.begin():
        row = (
            await db.execute(
                select(ReleaseTrackedAuthor).where(ReleaseTrackedAuthor.id == author_id)
            )
        ).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Tracked author not found")
        await db.delete(row)


# --- releases ---


@router.get("/releases", response_model=list[ReleaseOut])
async def list_releases(
    author: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[ReleaseOut]:
    async with db.begin():
        q = (
            select(Release)
            .join(Release.author)
            .where(Release.is_active.is_(True))
            .order_by(Release.release_date.asc().nullslast())
        )
        if author:
            q = q.where(ReleaseTrackedAuthor.name.ilike(f"%{author}%"))
        rows = (await db.execute(q)).scalars().all()

    return [_release_to_out(r) for r in rows]


@router.patch("/releases/{release_id}", response_model=ReleaseOut)
async def patch_release(
    release_id: int,
    body: PatchReleaseRequest,
    db: AsyncSession = Depends(get_db),
) -> ReleaseOut:
    async with db.begin():
        row = (
            await db.execute(
                select(Release)
                .options(selectinload(Release.author))
                .where(Release.id == release_id)
            )
        ).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Release not found")
        for field, value in body.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
    return _release_to_out(row)


# --- manual releases ---


@router.get("/releases/manual", response_model=list[ManualReleaseOut])
async def list_manual_releases(
    include_archived: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
) -> list[ManualReleaseOut]:
    async with db.begin():
        query = select(ManualRelease).order_by(ManualRelease.release_date.asc().nullslast())
        if not include_archived:
            query = query.where(ManualRelease.archived.is_(False))
        rows = (await db.execute(query)).scalars().all()
    return [_manual_to_out(row) for row in rows]


@router.post("/releases/manual", response_model=ManualReleaseOut, status_code=201)
async def create_manual_release(
    body: ManualReleaseCreate,
    db: AsyncSession = Depends(get_db),
) -> ManualReleaseOut:
    values = body.model_dump(exclude_unset=True)
    media = sorted(values.pop("media", []))
    for field in ("author", "title", "series", "release_date", "cover_url", "link_url", "comments"):
        if field not in values:
            values[field] = None
        values[field] = _clean_optional(values[field])
    now = int(time.time() * 1000)
    values.setdefault("series_number", None)
    values.setdefault("status", "watching")
    values.setdefault("last_checked_at", now)
    row = ManualRelease(
        **values,
        media=json.dumps(media),
        updated_at=now,
        dedupe_key=_manual_dedupe_key(
            values["author"], values["title"], values["release_date"], media
        ),
    )
    try:
        async with db.begin():
            db.add(row)
        await db.refresh(row)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="A manual release with the same author, title, release date, and media exists",
        ) from exc
    return _manual_to_out(row)


@router.patch("/releases/manual/{manual_release_id}", response_model=ManualReleaseOut)
async def patch_manual_release(
    manual_release_id: int,
    body: ManualReleasePatch,
    db: AsyncSession = Depends(get_db),
) -> ManualReleaseOut:
    updates = body.model_dump(exclude_unset=True)
    try:
        async with db.begin():
            row = await db.get(ManualRelease, manual_release_id)
            if row is None:
                raise HTTPException(status_code=404, detail="Manual release not found")
            media = sorted(updates.pop("media", json.loads(row.media) if row.media else []))
            for field, value in updates.items():
                if field in {
                    "author",
                    "title",
                    "series",
                    "release_date",
                    "cover_url",
                    "link_url",
                    "comments",
                }:
                    value = _clean_optional(value)
                setattr(row, field, value)
            row.media = json.dumps(media)
            now = int(time.time() * 1000)
            row.updated_at = now
            if "last_checked_at" not in updates:
                row.last_checked_at = now
            row.dedupe_key = _manual_dedupe_key(row.author, row.title, row.release_date, media)
        await db.refresh(row)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="A manual release with the same author, title, release date, and media exists",
        ) from exc
    return _manual_to_out(row)


@router.post("/releases/manual/{manual_release_id}/cover", response_model=ManualReleaseOut)
async def upload_manual_release_cover(
    manual_release_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> ManualReleaseOut:
    extensions = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
    }
    extension = extensions.get(file.content_type or "")
    if extension is None:
        raise HTTPException(status_code=415, detail="Cover must be a JPEG, PNG, WebP, or GIF image")
    content = await file.read(settings.MANUAL_RELEASE_COVER_MAX_BYTES + 1)
    if len(content) > settings.MANUAL_RELEASE_COVER_MAX_BYTES:
        raise HTTPException(status_code=413, detail="Cover image exceeds size limit")
    if not content:
        raise HTTPException(status_code=400, detail="Cover image is empty")
    async with db.begin():
        row = await db.get(ManualRelease, manual_release_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Manual release not found")
        old_path = _cover_dir() / row.cover_filename if row.cover_filename else None
        filename = f"{uuid4().hex}{extension}"
        (_cover_dir() / filename).write_bytes(content)
        row.cover_filename = filename
        row.updated_at = int(time.time() * 1000)
    if old_path:
        old_path.unlink(missing_ok=True)
    await db.refresh(row)
    return _manual_to_out(row)


@router.get("/releases/manual/{manual_release_id}/cover")
async def get_manual_release_cover(
    manual_release_id: int,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    row = await db.get(ManualRelease, manual_release_id)
    if row is None or not row.cover_filename:
        raise HTTPException(status_code=404, detail="Cover not found")
    path = _cover_dir() / row.cover_filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Cover not found")
    return FileResponse(path, headers={"Cache-Control": "public, max-age=86400"})


# --- refresh ---


@router.post("/releases/refresh", response_model=RefreshResult)
async def refresh_releases(db: AsyncSession = Depends(get_db)) -> RefreshResult:
    return await rt_svc.run_refresh(db)

import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..db import get_db
from ..models.releases import Release, ReleaseTrackedAuthor
from ..schemas.releases import (
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


# --- refresh ---


@router.post("/releases/refresh", response_model=RefreshResult)
async def refresh_releases(db: AsyncSession = Depends(get_db)) -> RefreshResult:
    return await rt_svc.run_refresh(db)

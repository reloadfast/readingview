import logging

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.releases import Release, ReleaseTrackedAuthor
from ..schemas.releases import RefreshError, RefreshResult

logger = logging.getLogger(__name__)

_TIMEOUT = 15.0
_BASE_URL = "https://openlibrary.org"
_HEADERS = {
    "User-Agent": "ReadingView/1.0 (Audiobook tracker)",
    "Accept": "application/json",
}


async def fetch_author_works(author_name: str, limit: int = 20) -> list[dict]:
    params: dict[str, str | int] = {
        "author": author_name,
        "limit": limit,
        "fields": "key,title,author_name,first_publish_year,isbn,cover_i",
    }
    async with httpx.AsyncClient(headers=_HEADERS, timeout=_TIMEOUT) as c:
        r = await c.get(f"{_BASE_URL}/search.json", params=params)
        r.raise_for_status()
    return r.json().get("docs", [])


def _ol_work_url(work_key: str) -> str:
    key = work_key if work_key.startswith("/") else f"/works/{work_key}"
    return f"{_BASE_URL}{key}"


def extract_releases(docs: list[dict], author_name: str) -> list[dict]:
    """Normalise OL search docs into release dicts, deduplicating by title."""
    seen: set[str] = set()
    releases: list[dict] = []
    for doc in docs:
        title = (doc.get("title") or "").strip()
        if not title:
            continue
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)

        year = doc.get("first_publish_year")
        release_date = str(year) if year else None

        isbns = doc.get("isbn") or []
        isbn = isbns[0] if isbns else None

        work_key = doc.get("key") or ""

        releases.append(
            {
                "title": title,
                "author_name": author_name,
                "release_date": release_date,
                "release_date_confirmed": year is not None,
                "ol_key": work_key,
                "link_url": _ol_work_url(work_key) if work_key else None,
                "source": "openlibrary",
                "isbn": isbn,
            }
        )

    releases.sort(key=lambda r: r["release_date"] or "", reverse=True)
    return releases


async def run_refresh(db: AsyncSession) -> RefreshResult:
    """Run a full release refresh and return counts. Suitable for both HTTP and scheduler use."""
    async with db.begin():
        authors = (await db.execute(select(ReleaseTrackedAuthor))).scalars().all()

    if not authors:
        return RefreshResult(added=0, skipped=0)

    added = 0
    skipped = 0
    failed = 0
    errors: list[RefreshError] = []

    for author in authors:
        try:
            docs = await fetch_author_works(author.name)
        except httpx.HTTPError as exc:
            logger.warning("Failed to fetch works for %r: %s", author.name, type(exc).__name__)
            failed += 1
            errors.append(RefreshError(author=author.name, message=type(exc).__name__))
            continue

        releases = extract_releases(docs, author.name)

        async with db.begin():
            existing_keys = set(
                (await db.execute(select(Release.ol_key).where(Release.author_id == author.id)))
                .scalars()
                .all()
            )
            existing_titles = set(
                (await db.execute(select(Release.title).where(Release.author_id == author.id)))
                .scalars()
                .all()
            )

            for rel in releases:
                ol_key = rel["ol_key"]
                title = rel["title"]
                if (ol_key and ol_key in existing_keys) or title in existing_titles:
                    skipped += 1
                    continue
                db.add(
                    Release(
                        author_id=author.id,
                        title=title,
                        release_date=rel["release_date"],
                        release_date_confirmed=rel.get("release_date_confirmed", False),
                        ol_key=ol_key or None,
                        link_url=rel["link_url"],
                        source=rel["source"],
                    )
                )
                added += 1

    logger.info("Release refresh complete: added=%d skipped=%d failed=%d", added, skipped, failed)
    return RefreshResult(added=added, skipped=skipped, failed=failed, errors=errors)

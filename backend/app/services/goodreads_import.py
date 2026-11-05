"""Translate Goodreads lookup diagnostics into a local release creation draft."""

import asyncio
import json
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.releases import ManualRelease
from ..schemas.releases import (
    GoodreadsExistingRelease,
    GoodreadsLookupOut,
    GoodreadsReleaseDraft,
)
from . import goodreads

LOOKUP_DEADLINE = 25.0


class GoodreadsImportError(Exception):
    def __init__(self, reason: Literal["invalid_url", "timeout", "unavailable"], message: str):
        self.reason = reason
        super().__init__(message)


async def lookup_release(url: str, db: AsyncSession) -> GoodreadsLookupOut:
    try:
        source_url = goodreads.canonical_url(url)
    except ValueError as exc:
        raise GoodreadsImportError(
            "invalid_url", "Use an HTTPS Goodreads /book/show/<id> URL."
        ) from exc

    # Fetch before querying: do not hold a database transaction during external I/O.
    try:
        async with asyncio.timeout(LOOKUP_DEADLINE):
            result = await goodreads.probe(source_url)
    except TimeoutError as exc:
        raise GoodreadsImportError(
            "timeout", "Goodreads took too long to respond. Retry or add the release manually."
        ) from exc

    if result["status"] == "network_error" and result.get("error_type") in {
        "ConnectTimeout",
        "ReadTimeout",
        "WriteTimeout",
        "PoolTimeout",
    }:
        raise GoodreadsImportError(
            "timeout", "Goodreads took too long to respond. Retry or add the release manually."
        )
    messages = {
        "blocked": "Goodreads blocked access to this page. Retry or add the release manually.",
        "too_large": "The Goodreads page is too large to import. Add the release manually.",
        "no_metadata": "No usable book details were found. Try another link or add it manually.",
    }
    if result["status"] not in {"ok", "partial"} or not result.get("fields", {}).get("title"):
        raise GoodreadsImportError(
            "unavailable",
            messages.get(
                result["status"], "Could not read Goodreads. Retry or add the release manually."
            ),
        )

    fields = result["fields"]
    try:
        draft = GoodreadsReleaseDraft.model_validate(
            {**fields, "media": fields["media"] or [], "link_url": source_url, "status": "watching"}
        )
    except ValueError as exc:
        raise GoodreadsImportError(
            "unavailable", "Goodreads returned unusable book details. Add the release manually."
        ) from exc

    rows = (
        (
            await db.execute(
                select(ManualRelease)
                .where(ManualRelease.link_url.is_not(None))
                .order_by(ManualRelease.id)
            )
        )
        .scalars()
        .all()
    )
    existing = []
    for row in rows:
        try:
            if goodreads.canonical_url(row.link_url or "") != source_url:
                continue
        except ValueError:
            continue
        existing.append(
            GoodreadsExistingRelease.model_validate(
                {
                    "id": row.id,
                    "title": row.title,
                    "author": row.author,
                    "release_date": row.release_date,
                    "media": json.loads(row.media or "[]"),
                    "status": row.status,
                    "archived": row.archived,
                }
            )
        )

    return GoodreadsLookupOut(
        status="ok" if result["status"] == "ok" else "partial",
        source_url=source_url,
        draft=draft,
        sources=result.get("sources", {}),
        missing_fields=result.get("missing_fields", []),
        warnings=result.get("warnings", []),
        existing_releases=existing,
    )

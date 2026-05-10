import hashlib

import httpx
from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..crypto import decrypt
from ..db import get_db
from ..models.settings import Settings
from ..services.cover_cache import get

router = APIRouter()

_TIMEOUT = 15.0


def _compute_etag(data: bytes) -> str:
    return f'"{hashlib.sha256(data, usedforsecurity=False).hexdigest()[:16]}"'


@router.delete("/cache")
async def clear_cover_cache() -> JSONResponse:
    if not (cache := get()):
        return JSONResponse({"ok": True})
    await cache.clear()
    return JSONResponse({"ok": True, "cleared": True})


def _compute_etag(data: bytes) -> str:
    return f'"{hashlib.sha256(data, usedforsecurity=False).hexdigest()[:16]}"'


@router.delete("/cache")
async def clear_cover_cache() -> JSONResponse:
    if not (cache := get()):
        return JSONResponse({"ok": True})
    await cache.clear()
    return JSONResponse({"ok": True, "cleared": True})


@router.get("/cover/{item_id}")
async def get_cover(
    item_id: str,
    if_none_match: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> Response:
    async with db.begin():
        row = await db.get(Settings, 1)

    if not row or not row.abs_url or not row.abs_token:
        return Response(status_code=503, content="ABS not configured")

    if cache := get():
        cached = await cache.get(item_id)
        if cached is not None:
            etag = _compute_etag(cached)
            if if_none_match == etag:
                return Response(status_code=304)
            return Response(content=cached, media_type="image/jpeg", headers={"Cache-Control": "public, max-age=86400", "ETag": etag})

    etag = f'"{hashlib.sha1(item_id.encode(), usedforsecurity=False).hexdigest()[:16]}"'
    if if_none_match == etag:
        return Response(status_code=304)

    url = f"{row.abs_url.rstrip('/')}/api/items/{item_id}/cover"
    headers = {"Authorization": f"Bearer {decrypt(row.abs_token)}"}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.get(url, headers=headers)
    except httpx.RequestError:
        return Response(status_code=502)

    if r.status_code == 404:
        return Response(status_code=404)
    if not r.is_success:
        return Response(status_code=502)

    if cache := get():
        await cache.put(item_id, r.content)

    return Response(content=r.content, media_type=r.headers.get("content-type", "image/jpeg"), headers={"Cache-Control": "public, max-age=86400", "ETag": etag})

    etag = f'"{hashlib.sha1(item_id.encode(), usedforsecurity=False).hexdigest()[:16]}"'
    if if_none_match == etag:
        return Response(status_code=304)

    url = f"{row.abs_url.rstrip('/')}/api/items/{item_id}/cover"
    headers = {"Authorization": f"Bearer {decrypt(row.abs_token)}"}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.get(url, headers=headers)
    except httpx.RequestError:
        return Response(status_code=502)

    if r.status_code == 404:
        return Response(status_code=404)
    if not r.is_success:
        return Response(status_code=502)

    if cache := get():
        await cache.put(item_id, r.content)

    return Response(
        content=r.content,
        media_type=r.headers.get("content-type", "image/jpeg"),
        headers={
            "Cache-Control": "public, max-age=86400",
            "ETag": etag,
        },
    )

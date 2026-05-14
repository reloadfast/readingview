"""In-memory TTL cache for slow Audiobookshelf API calls.

Cached (24 h TTL): get_all_library_items, get_library_series, get_user_listening_stats,
get_user_listening_sessions.
Pass-through (live): get_media_progress_map, get_user_items_in_progress, get_item, get_libraries.
"""

import asyncio
import logging
import time
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

from .audiobookshelf import AudiobookshelfClient

logger = logging.getLogger(__name__)

_TTL = 86_400  # 24 hours
_T = TypeVar("_T")

_cache: "AbsDataCache | None" = None


class AbsDataCache:
    def __init__(self, abs_url: str, abs_token: str) -> None:
        self._client = AudiobookshelfClient(abs_url, abs_token)
        self._store: dict[str, tuple[Any, float]] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def _lock(self, key: str) -> asyncio.Lock:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    def _get(self, key: str) -> Any:
        entry = self._store.get(key)
        if entry and time.monotonic() - entry[1] < _TTL:
            return entry[0]
        return None

    def _set(self, key: str, data: Any) -> None:
        self._store[key] = (data, time.monotonic())

    async def _cached(self, key: str, fn: Callable[[], Coroutine[Any, Any, _T]]) -> _T:
        hit = self._get(key)
        if hit is not None:
            return hit
        async with self._lock(key):
            hit = self._get(key)
            if hit is not None:
                return hit
            data = await fn()
            self._set(key, data)
            logger.debug("ABS cache populated: %s", key)
            return data

    # ---- cached methods ----

    async def get_all_library_items(self) -> list[dict]:
        return await self._cached("all_library_items", self._client.get_all_library_items)

    async def get_library_series(self, library_id: str) -> list[dict]:
        return await self._cached(
            f"library_series_{library_id}",
            lambda: self._client.get_library_series(library_id),
        )

    async def get_user_listening_stats(self) -> dict:
        return await self._cached("listening_stats", self._client.get_user_listening_stats)

    async def get_user_listening_sessions(self) -> list[dict]:
        return await self._cached("listening_sessions", self._client.get_user_listening_sessions)

    # ---- live pass-through methods ----

    async def get_media_progress_map(self) -> dict:
        return await self._client.get_media_progress_map()

    async def get_libraries(self) -> list[dict]:
        return await self._client.get_libraries()

    async def get_user_items_in_progress(self) -> list[dict]:
        return await self._client.get_user_items_in_progress()

    async def get_item(self, item_id: str) -> dict | None:
        return await self._client.get_item(item_id)

    def cover_url(self, item_id: str) -> str:
        return self._client.cover_url(item_id)

    # ---- cache management ----

    def invalidate(self) -> None:
        self._store.clear()
        logger.info("ABS data cache cleared")

    def status(self) -> dict:
        now = time.monotonic()
        return {
            "ttl_seconds": _TTL,
            "cached_keys": {
                key: {
                    "age_seconds": int(now - ts),
                    "expires_in_seconds": max(0, int(_TTL - (now - ts))),
                }
                for key, (_, ts) in self._store.items()
            },
        }

    async def aclose(self) -> None:
        await self._client.aclose()


def get() -> "AbsDataCache | None":
    return _cache


async def start(abs_url: str, abs_token_enc: str) -> None:
    """Initialize cache with an encrypted token (called from lifespan)."""
    global _cache
    if _cache is not None:
        await _cache.aclose()
        _cache = None
    try:
        from ..crypto import decrypt

        token = decrypt(abs_token_enc)
    except Exception:
        logger.warning("Failed to decrypt ABS token; data cache disabled")
        return
    _cache = AbsDataCache(abs_url, token)
    logger.info("ABS data cache initialized")


async def restart(abs_url: str | None, abs_token: str | None) -> None:
    """Restart with plaintext credentials (called after a settings PATCH)."""
    global _cache
    if _cache is not None:
        await _cache.aclose()
        _cache = None
    if not abs_url or not abs_token:
        return
    _cache = AbsDataCache(abs_url, abs_token)
    logger.info("ABS data cache restarted")


async def stop() -> None:
    global _cache
    if _cache is not None:
        await _cache.aclose()
        _cache = None

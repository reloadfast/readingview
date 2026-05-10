"""In-memory LRU cover cache with disk persistence."""

import asyncio
import hashlib
from pathlib import Path


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


class CoverCache:
    """Cache for cover images backed by local disk storage.

    Tracks in-memory sizes and evicts (on disk + RAM) when the
    total exceeds `max_bytes`.
    """

    def __init__(self, base_dir: str, max_bytes: int) -> None:
        self._base = Path(base_dir)
        self._max_bytes = max_bytes
        self._current_bytes = 0
        self._lock: asyncio.Lock | None = None
        self._base.mkdir(parents=True, exist_ok=True)

    async def _ensure_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def start(self) -> None:
        """Rebuild size from disk (called once at startup)."""
        await self._rebuild_size()

    async def _rebuild_size(self) -> None:
        """Walk disk and reconcile _current_bytes (called once at startup)."""
        total = 0
        for f in self._base.iterdir():
            if f.is_file():
                total += f.stat().st_size
        self._current_bytes = total

    async def get(self, key: str) -> bytes | None:
        filepath = self._base / _hash_key(key)
        if filepath.exists():
            return await asyncio.to_thread(filepath.read_bytes)
        return None

    async def put(self, key: str, data: bytes) -> None:
        lock = await self._ensure_lock()
        async with lock:
            await self._evict_if_needed(len(data))
            filepath = self._base / _hash_key(key)
            await asyncio.to_thread(filepath.write_bytes, data)
            self._current_bytes += len(data)

    async def clear(self) -> None:
        lock = await self._ensure_lock()
        async with lock:
            for f in self._base.iterdir():
                if f.is_file():
                    await asyncio.to_thread(f.unlink)
            self._current_bytes = 0

    async def clear_key(self, key: str) -> None:
        filepath = self._base / _hash_key(key)
        if filepath.exists():
            size = (await asyncio.to_thread(filepath.stat)).st_size
            await asyncio.to_thread(filepath.unlink)
            lock = await self._ensure_lock()
            async with lock:
                self._current_bytes = max(0, self._current_bytes - size)

    async def _evict_if_needed(self, needed: int) -> None:
        """Prune oldest files until we have room, or nothing left."""
        if self._current_bytes + needed <= self._max_bytes:
            return

        candidates = sorted(
            (f for f in self._base.iterdir() if f.is_file()),
            key=lambda p: p.stat().st_mtime,
        )
        for f in candidates:
            size = f.stat().st_size
            await asyncio.to_thread(f.unlink)
            self._current_bytes -= size
            if self._current_bytes + needed <= self._max_bytes:
                break

    @property
    def current_size(self) -> int:
        return self._current_bytes

    @property
    def max_size(self) -> int:
        return self._max_bytes

    @property
    def directory(self) -> str:
        return str(self._base)


# Singleton instance -- initialized at app startup.
# Can be created via `initialize()`. Access via `get()`.
_cache: CoverCache | None = None
_initialized = False


def initialize(base_dir: str, max_bytes: int) -> CoverCache | None:
    """Instantiate the cache singleton. Returns the instance or None on failure."""
    global _cache, _initialized
    if _initialized:
        return _cache
    try:
        _cache = CoverCache(base_dir, max_bytes)
        _initialized = True
        return _cache
    except Exception:
        _cache = None
        return None


def get() -> CoverCache | None:
    """Return the current cache singleton."""
    return _cache

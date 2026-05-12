import asyncio
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..api.ws import ConnectionManager

logger = logging.getLogger(__name__)

_task: asyncio.Task[None] | None = None


async def _run(manager: "ConnectionManager", abs_url: str, abs_token: str) -> None:
    try:
        import socketio  # type: ignore[import-untyped]
    except ImportError:
        logger.warning("python-socketio not installed; ABS live events disabled")
        return

    sio: Any = socketio.AsyncClient(
        reconnection=True,
        reconnection_attempts=0,
        reconnection_delay=5,
    )

    @sio.on("library_item_updated")
    async def _on_lib(data: Any) -> None:
        await manager.broadcast({"type": "library_item_updated", "data": data})

    @sio.on("user_progress_updated")
    async def _on_progress(data: Any) -> None:
        await manager.broadcast({"type": "user_progress_updated", "data": data})

    url = abs_url.rstrip("/")
    try:
        await sio.connect(url, auth={"token": abs_token}, transports=["websocket", "polling"])
        logger.info("ABS socket.io connected to %s", url)
        await sio.wait()
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("ABS socket.io connection failed for %s", url)
    finally:
        try:
            if sio.connected:
                await sio.disconnect()
        except Exception:  # noqa: BLE001
            logger.debug("Error during sio disconnect", exc_info=True)


async def _cancel_existing() -> None:
    global _task
    if _task and not _task.done():
        _task.cancel()
        try:
            await _task
        except (asyncio.CancelledError, Exception):  # noqa: BLE001, S110
            pass
    _task = None


async def start(
    manager: "ConnectionManager", abs_url: str | None, abs_token_enc: str | None
) -> None:
    """Start the ABS socket.io bridge using an encrypted token from the DB."""
    await _cancel_existing()
    if not abs_url or not abs_token_enc:
        return
    try:
        from ..crypto import decrypt

        abs_token = decrypt(abs_token_enc)
    except Exception:
        logger.warning("Failed to decrypt ABS token; ABS live events disabled")
        return
    global _task
    _task = asyncio.create_task(_run(manager, abs_url, abs_token))


async def restart(manager: "ConnectionManager", abs_url: str | None, abs_token: str | None) -> None:
    """Restart with plaintext credentials (called after a settings PATCH)."""
    await _cancel_existing()
    if not abs_url or not abs_token:
        return
    global _task
    _task = asyncio.create_task(_run(manager, abs_url, abs_token))


async def stop() -> None:
    await _cancel_existing()

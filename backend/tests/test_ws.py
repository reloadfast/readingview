from unittest.mock import AsyncMock

import pytest

from app.api.ws import ConnectionManager


async def test_broadcast_sends_to_all_clients():
    manager = ConnectionManager()
    ws1, ws2 = AsyncMock(), AsyncMock()
    await manager.connect(ws1)
    await manager.connect(ws2)

    await manager.broadcast({"type": "library_item_updated", "data": {}})

    ws1.send_json.assert_awaited_once_with({"type": "library_item_updated", "data": {}})
    ws2.send_json.assert_awaited_once_with({"type": "library_item_updated", "data": {}})


async def test_broadcast_removes_dead_clients():
    manager = ConnectionManager()
    ws = AsyncMock()
    ws.send_json.side_effect = Exception("connection closed")
    await manager.connect(ws)

    await manager.broadcast({"type": "test"})

    assert ws not in manager._clients


async def test_disconnect_removes_client():
    manager = ConnectionManager()
    ws = AsyncMock()
    await manager.connect(ws)
    manager.disconnect(ws)

    assert ws not in manager._clients


async def test_broadcast_empty_manager_is_noop():
    manager = ConnectionManager()
    await manager.broadcast({"type": "test"})  # should not raise


async def test_disconnect_unknown_client_is_noop():
    manager = ConnectionManager()
    ws = AsyncMock()
    manager.disconnect(ws)  # never connected — should not raise

"""Unit tests for AudiobookshelfClient — mocked httpx responses."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.audiobookshelf import AudiobookshelfClient

pytestmark = pytest.mark.unit


def _client() -> AudiobookshelfClient:
    return AudiobookshelfClient("http://abs.test", "token")


def _mock_http(json_data: dict | list) -> AsyncMock:
    """Return a mock httpx async client that returns json_data on any GET."""
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.status_code = 200
    resp.json.return_value = json_data
    http = AsyncMock()
    http.get = AsyncMock(return_value=resp)
    http.__aenter__ = AsyncMock(return_value=http)
    http.__aexit__ = AsyncMock(return_value=None)
    return http


async def test_get_media_progress_map():
    c = _client()
    data = {
        "mediaProgress": [
            {"libraryItemId": "item-1", "progress": 0.5},
            {"libraryItemId": "item-2", "progress": 1.0},
            {"progress": 0.1},  # no libraryItemId — should be skipped
        ]
    }
    with patch.object(c, "_client", return_value=_mock_http(data)):
        result = await c.get_media_progress_map()
    assert "item-1" in result
    assert "item-2" in result
    assert len(result) == 2


async def test_get_libraries():
    c = _client()
    data = {"libraries": [{"id": "lib-1", "name": "Audiobooks"}]}
    with patch.object(c, "_client", return_value=_mock_http(data)):
        result = await c.get_libraries()
    assert len(result) == 1
    assert result[0]["id"] == "lib-1"


async def test_get_library_items():
    c = _client()
    data = {"results": [{"id": "b1"}, {"id": "b2"}]}
    with patch.object(c, "_client", return_value=_mock_http(data)):
        result = await c.get_library_items("lib-1")
    assert len(result) == 2


async def test_get_user_items_in_progress():
    c = _client()
    data = {"libraryItems": [{"id": "in-progress-1"}]}
    with patch.object(c, "_client", return_value=_mock_http(data)):
        result = await c.get_user_items_in_progress()
    assert result[0]["id"] == "in-progress-1"


async def test_get_item_found():
    c = _client()
    data = {"id": "item-123", "media": {}}
    with patch.object(c, "_client", return_value=_mock_http(data)):
        result = await c.get_item("item-123")
    assert result is not None
    assert result["id"] == "item-123"


async def test_get_item_not_found():
    c = _client()
    resp = MagicMock()
    resp.status_code = 404
    http = AsyncMock()
    http.get = AsyncMock(return_value=resp)
    http.__aenter__ = AsyncMock(return_value=http)
    http.__aexit__ = AsyncMock(return_value=None)
    with patch.object(c, "_client", return_value=http):
        result = await c.get_item("no-such-item")
    assert result is None


async def test_get_user_listening_stats():
    c = _client()
    data = {"totalTime": 3600, "items": {}}
    with patch.object(c, "_client", return_value=_mock_http(data)):
        result = await c.get_user_listening_stats()
    assert result["totalTime"] == 3600


async def test_cover_url():
    c = _client()
    assert c.cover_url("item-1") == "/api/cover/item-1"


async def test_get_library_series_single_page():
    c = _client()
    data = {"results": [{"id": "s1"}], "total": 1}
    with patch.object(c, "_client", return_value=_mock_http(data)):
        result = await c.get_library_series("lib-1")
    assert len(result) == 1


async def test_get_user_listening_sessions_single_page():
    c = _client()
    data = {"sessions": [{"id": "sess-1"}], "total": 1}
    with patch.object(c, "_client", return_value=_mock_http(data)):
        result = await c.get_user_listening_sessions()
    assert len(result) == 1


async def test_get_all_library_items_aggregates():
    c = _client()
    libs_data = {"libraries": [{"id": "lib-a"}, {"id": "lib-b"}]}
    items_data = {"results": [{"id": "book-1"}]}

    call_count = 0

    def _make_http():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _mock_http(libs_data)
        return _mock_http(items_data)

    with patch.object(c, "_client", side_effect=_make_http):
        result = await c.get_all_library_items()

    assert len(result) == 2  # one item per library

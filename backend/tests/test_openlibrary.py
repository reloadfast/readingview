"""Unit tests for OpenLibraryClient (mocked httpx)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.openlibrary import OpenLibraryClient

pytestmark = pytest.mark.unit


def _client() -> OpenLibraryClient:
    return OpenLibraryClient()


def _mock_http(json_data: dict | list) -> AsyncMock:
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.status_code = 200
    resp.json.return_value = json_data
    http = AsyncMock()
    http.get = AsyncMock(return_value=resp)
    http.__aenter__ = AsyncMock(return_value=http)
    http.__aexit__ = AsyncMock(return_value=None)
    return http


async def test_search_authors_returns_docs():
    c = _client()
    data = {
        "docs": [
            {"key": "/authors/OL123A", "name": "Brandon Sanderson", "work_count": 20},
        ]
    }
    with patch("httpx.AsyncClient", return_value=_mock_http(data)):
        result = await c.search_authors("Brandon Sanderson")
    assert len(result) == 1
    assert result[0]["name"] == "Brandon Sanderson"


async def test_search_authors_empty_result():
    c = _client()
    with patch("httpx.AsyncClient", return_value=_mock_http({"docs": []})):
        result = await c.search_authors("Nobody McFake")
    assert result == []


async def test_get_author_details_found():
    c = _client()
    data = {"key": "/authors/OL123A", "name": "Brandon Sanderson", "bio": "Author"}
    with patch("httpx.AsyncClient", return_value=_mock_http(data)):
        result = await c.get_author_details("OL123A")
    assert result is not None
    assert result["name"] == "Brandon Sanderson"


async def test_get_author_details_not_found():
    c = _client()
    resp = MagicMock()
    resp.status_code = 404
    http = AsyncMock()
    http.get = AsyncMock(return_value=resp)
    http.__aenter__ = AsyncMock(return_value=http)
    http.__aexit__ = AsyncMock(return_value=None)
    with patch("httpx.AsyncClient", return_value=http):
        result = await c.get_author_details("nonexistent")
    assert result is None


def test_photo_url_with_photos():
    c = _client()
    url = c.photo_url({"photos": [12345]}, size="M")
    assert url is not None
    assert "12345" in url


def test_photo_url_with_olid_fallback():
    c = _client()
    url = c.photo_url({"key": "/authors/OL123A", "photos": []}, size="S")
    assert url is not None
    assert "OL123A" in url


def test_photo_url_no_data():
    c = _client()
    assert c.photo_url({}) is None


def test_normalise_key():
    c = _client()
    assert c.normalise_key("/authors/OL123A") == "OL123A"
    assert c.normalise_key("OL123A") == "OL123A"

"""Tests for the cover proxy endpoint."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


async def _configure_abs(client):
    await client.patch("/api/settings", json={"abs_url": "http://abs.test", "abs_token": "t"})


def _mock_response(status_code: int = 200, content: bytes = b"img", content_type: str = "image/jpeg"):
    r = MagicMock(spec=httpx.Response)
    r.status_code = status_code
    r.content = content
    r.headers = {"content-type": content_type}
    r.is_success = 200 <= status_code < 300
    return r


pytestmark = pytest.mark.asyncio


async def test_cover_503_without_abs_config(client):
    r = await client.get("/api/cover/item-1")
    assert r.status_code == 503


async def test_cover_returns_image(client):
    await _configure_abs(client)
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=_mock_response(200, b"fake-image-bytes"))

    with patch("app.api.covers.httpx.AsyncClient", return_value=mock_client):
        r = await client.get("/api/cover/item-1")

    assert r.status_code == 200
    assert r.content == b"fake-image-bytes"
    assert r.headers["content-type"] == "image/jpeg"
    assert "public" in r.headers["cache-control"]
    assert "max-age=86400" in r.headers["cache-control"]
    assert "etag" in r.headers


async def test_cover_304_on_matching_etag(client):
    await _configure_abs(client)
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=_mock_response(200, b"fake-image-bytes"))

    with patch("app.api.covers.httpx.AsyncClient", return_value=mock_client):
        r1 = await client.get("/api/cover/item-1")

    etag = r1.headers["etag"]

    with patch("app.api.covers.httpx.AsyncClient", return_value=mock_client):
        r2 = await client.get("/api/cover/item-1", headers={"If-None-Match": etag})

    assert r2.status_code == 304


async def test_cover_404_when_abs_returns_404(client):
    await _configure_abs(client)
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=_mock_response(404))

    with patch("app.api.covers.httpx.AsyncClient", return_value=mock_client):
        r = await client.get("/api/cover/no-such-item")

    assert r.status_code == 404


async def test_cover_502_on_abs_server_error(client):
    await _configure_abs(client)
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=_mock_response(500))

    with patch("app.api.covers.httpx.AsyncClient", return_value=mock_client):
        r = await client.get("/api/cover/item-1")

    assert r.status_code == 502


async def test_cover_502_on_network_error(client):
    await _configure_abs(client)
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=httpx.RequestError("connection refused"))

    with patch("app.api.covers.httpx.AsyncClient", return_value=mock_client):
        r = await client.get("/api/cover/item-1")

    assert r.status_code == 502

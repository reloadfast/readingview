"""Tests for /api/abs/test-connection and /api/llm/test-connection."""

from unittest.mock import AsyncMock, MagicMock, patch


def _mock_ok_response(json_data=None):
    resp = MagicMock()
    resp.status_code = 200
    resp.raise_for_status = MagicMock()
    resp.json.return_value = json_data or {}
    http = AsyncMock()
    http.get = AsyncMock(return_value=resp)
    http.__aenter__ = AsyncMock(return_value=http)
    http.__aexit__ = AsyncMock(return_value=None)
    return http


def _mock_error_response(status_code=401):
    from httpx import HTTPStatusError, Request

    resp_mock = MagicMock()
    resp_mock.status_code = status_code
    exc = HTTPStatusError(
        message=f"HTTP {status_code}",
        request=MagicMock(spec=Request),
        response=resp_mock,
    )
    http = AsyncMock()
    http.get = AsyncMock(side_effect=exc)
    http.__aenter__ = AsyncMock(return_value=http)
    http.__aexit__ = AsyncMock(return_value=None)
    return http


async def test_abs_connection_ok(client):
    with patch("httpx.AsyncClient", return_value=_mock_ok_response()):
        r = await client.post(
            "/api/abs/test-connection",
            json={"url": "http://abs.test", "token": "tok"},
        )
    assert r.status_code == 200
    assert r.json()["ok"] is True


async def test_abs_connection_http_error(client):
    with patch("httpx.AsyncClient", return_value=_mock_error_response(401)):
        r = await client.post(
            "/api/abs/test-connection",
            json={"url": "http://abs.test", "token": "bad-tok"},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is False
    assert "401" in data["error"]


async def test_abs_connection_network_error(client):
    http = AsyncMock()
    http.get = AsyncMock(side_effect=Exception("Connection refused"))
    http.__aenter__ = AsyncMock(return_value=http)
    http.__aexit__ = AsyncMock(return_value=None)
    with patch("httpx.AsyncClient", return_value=http):
        r = await client.post(
            "/api/abs/test-connection",
            json={"url": "http://unreachable.test", "token": "tok"},
        )
    assert r.status_code == 200
    assert r.json()["ok"] is False


async def test_llm_connection_ok(client):
    with patch(
        "httpx.AsyncClient",
        return_value=_mock_ok_response({"data": [{"id": "llama3"}, {"id": "mistral"}]}),
    ):
        r = await client.post(
            "/api/llm/test-connection",
            json={"endpoint": "http://ollama.test:11434"},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert "llama3" in data["models"]


async def test_llm_connection_with_api_key(client):
    with patch("httpx.AsyncClient", return_value=_mock_ok_response({"data": []})):
        r = await client.post(
            "/api/llm/test-connection",
            json={"endpoint": "http://ollama.test:11434", "api_key": "sk-test"},
        )
    assert r.status_code == 200
    assert r.json()["ok"] is True


async def test_llm_connection_error(client):
    with patch("httpx.AsyncClient", return_value=_mock_error_response(500)):
        r = await client.post(
            "/api/llm/test-connection",
            json={"endpoint": "http://ollama.test:11434"},
        )
    assert r.status_code == 200
    assert r.json()["ok"] is False

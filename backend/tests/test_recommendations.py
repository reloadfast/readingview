"""Verify recommendations returns [] and makes no Ollama calls when disabled."""

from unittest.mock import patch


async def test_recommendations_disabled_returns_empty_list(client):
    # Default DB settings have recommender_enabled=False
    r = await client.get("/api/recommendations")
    assert r.status_code == 200
    assert r.json() == []


async def test_recommendations_with_book_ids_disabled(client):
    r = await client.get("/api/recommendations?book_ids=book-1,book-2")
    assert r.status_code == 200
    assert r.json() == []


async def test_recommendations_with_prompt_disabled(client):
    r = await client.get("/api/recommendations?prompt=fantasy+adventure")
    assert r.status_code == 200
    assert r.json() == []


async def test_recommendations_status_disabled(client):
    r = await client.get("/api/recommendations/status")
    assert r.status_code == 200
    data = r.json()
    assert data["enabled"] is False
    assert data["model"] is None
    assert data["vector_backend"] is None


async def test_ingest_returns_404_when_disabled(client):
    r = await client.post("/api/recommendations/ingest", json={"isbn": "9780316129084"})
    assert r.status_code == 404


async def test_no_ollama_calls_when_disabled(client):
    with patch("httpx.AsyncClient.get") as mock_get:
        await client.get("/api/recommendations")
        # httpx should not have been called for Ollama
        ollama_calls = [
            call
            for call in mock_get.call_args_list
            if "11434" in str(call) or "ollama" in str(call).lower()
        ]
        assert ollama_calls == []

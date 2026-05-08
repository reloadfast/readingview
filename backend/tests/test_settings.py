import asyncio

import pytest


async def test_get_settings_defaults(client):
    r = await client.get("/api/settings")
    assert r.status_code == 200
    data = r.json()
    assert data["recommender_enabled"] is False
    assert data["abs_url"] is None
    assert data["abs_token"] is None
    assert data["notifications_enabled"] is False


async def test_patch_abs_url_persists(client):
    r = await client.patch("/api/settings", json={"abs_url": "http://abs.example.com"})
    assert r.status_code == 200
    assert r.json()["abs_url"] == "http://abs.example.com"

    r2 = await client.get("/api/settings")
    assert r2.json()["abs_url"] == "http://abs.example.com"


async def test_patch_abs_token_masked(client):
    r = await client.patch("/api/settings", json={"abs_token": "my-secret-token"})
    assert r.status_code == 200
    assert r.json()["abs_token"] == ""


async def test_patch_recommender_fields(client):
    r = await client.patch(
        "/api/settings",
        json={
            "recommender_enabled": True,
            "recommender_top_k": 5,
            "recommender_min_similarity": 0.3,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["recommender_enabled"] is True
    assert data["recommender_top_k"] == 5
    assert data["recommender_min_similarity"] == pytest.approx(0.3)


async def test_patch_llm_api_key_masked(client):
    r = await client.patch("/api/settings", json={"llm_api_key": "sk-test-key"})
    assert r.status_code == 200
    assert r.json()["llm_api_key"] == ""


async def test_patch_notifications(client):
    r = await client.patch(
        "/api/settings",
        json={
            "notifications_enabled": True,
            "notify_days_before": 3,
            "notify_time": "08:00",
            "timezone": "Europe/Madrid",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["notifications_enabled"] is True
    assert data["notify_days_before"] == 3
    assert data["notify_time"] == "08:00"
    assert data["timezone"] == "Europe/Madrid"


async def test_concurrent_first_requests_both_succeed(client):
    r1, r2 = await asyncio.gather(
        client.get("/api/settings"),
        client.get("/api/settings"),
    )
    assert r1.status_code == 200
    assert r2.status_code == 200

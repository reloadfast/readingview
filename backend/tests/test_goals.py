"""Tests for /api/goals endpoints."""


async def test_list_goals_empty(client):
    r = await client.get("/api/goals")
    assert r.status_code == 200
    assert r.json() == []


async def test_upsert_goal_creates(client):
    r = await client.put("/api/goals/2026", json={"target_books": 24})
    assert r.status_code == 200
    data = r.json()
    assert data["year"] == 2026
    assert data["target_books"] == 24


async def test_upsert_goal_updates(client):
    await client.put("/api/goals/2026", json={"target_books": 24})
    r = await client.put("/api/goals/2026", json={"target_books": 30})
    assert r.status_code == 200
    assert r.json()["target_books"] == 30


async def test_list_goals_after_create(client):
    await client.put("/api/goals/2025", json={"target_books": 20})
    await client.put("/api/goals/2026", json={"target_books": 24})
    r = await client.get("/api/goals")
    assert r.status_code == 200
    years = [g["year"] for g in r.json()]
    assert 2025 in years
    assert 2026 in years


async def test_upsert_goal_invalid_target(client):
    r = await client.put("/api/goals/2026", json={"target_books": 0})
    assert r.status_code == 422


async def test_upsert_goal_negative_target(client):
    r = await client.put("/api/goals/2026", json={"target_books": -1})
    assert r.status_code == 422

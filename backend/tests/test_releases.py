"""Tests for /api/releases — tracked-author CRUD and release listing."""


async def test_list_tracked_authors_empty(client):
    r = await client.get("/api/releases/tracked-authors")
    assert r.status_code == 200
    assert r.json() == []


async def test_track_author(client):
    r = await client.post(
        "/api/releases/tracked-authors",
        json={"name": "Brandon Sanderson", "ol_key": "OL123A"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Brandon Sanderson"
    assert data["ol_key"] == "OL123A"
    assert "id" in data
    assert "added_at" in data


async def test_track_author_without_ol_key(client):
    r = await client.post(
        "/api/releases/tracked-authors",
        json={"name": "Patrick Rothfuss"},
    )
    assert r.status_code == 201
    assert r.json()["ol_key"] is None


async def test_track_duplicate_author_returns_409(client):
    await client.post("/api/releases/tracked-authors", json={"name": "Terry Pratchett"})
    r = await client.post("/api/releases/tracked-authors", json={"name": "Terry Pratchett"})
    assert r.status_code == 409


async def test_list_tracked_authors_after_add(client):
    await client.post("/api/releases/tracked-authors", json={"name": "Author One"})
    await client.post("/api/releases/tracked-authors", json={"name": "Author Two"})
    r = await client.get("/api/releases/tracked-authors")
    assert r.status_code == 200
    names = [a["name"] for a in r.json()]
    assert "Author One" in names
    assert "Author Two" in names


async def test_untrack_author(client):
    create = await client.post("/api/releases/tracked-authors", json={"name": "To Untrack"})
    author_id = create.json()["id"]
    r = await client.delete(f"/api/releases/tracked-authors/{author_id}")
    assert r.status_code == 204
    remaining = await client.get("/api/releases/tracked-authors")
    assert all(a["id"] != author_id for a in remaining.json())


async def test_untrack_nonexistent_author(client):
    r = await client.delete("/api/releases/tracked-authors/99999")
    assert r.status_code == 404


async def test_list_releases_empty(client):
    r = await client.get("/api/releases")
    assert r.status_code == 200
    assert r.json() == []


async def test_refresh_no_tracked_authors(client):
    r = await client.post("/api/releases/refresh")
    assert r.status_code == 200
    data = r.json()
    assert data["added"] == 0
    assert data["skipped"] == 0
    assert data["failed"] == 0
    assert data["errors"] == []

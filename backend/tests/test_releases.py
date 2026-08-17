"""Tests for /api/releases — tracked-author CRUD and release listing."""

import time

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models.releases import Release, ReleaseTrackedAuthor


@pytest.fixture
async def db(engine):
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session


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


# --- PATCH /api/releases/{id} ---


async def _seed_author_and_release(db, *, confirmed: bool = False) -> Release:
    async with db.begin():
        author = ReleaseTrackedAuthor(name="Seed Author", added_at=int(time.time() * 1000))
        db.add(author)
        await db.flush()
        rel = Release(
            author_id=author.id,
            title="Test Book",
            release_date="2025",
            release_date_confirmed=confirmed,
            source="test",
        )
        db.add(rel)
        await db.flush()
    return rel


async def test_patch_release_toggle_confirmed(client, db):
    rel = await _seed_author_and_release(db, confirmed=False)
    r = await client.patch(f"/api/releases/{rel.id}", json={"release_date_confirmed": True})
    assert r.status_code == 200
    assert r.json()["release_date_confirmed"] is True


async def test_patch_release_update_date(client, db):
    rel = await _seed_author_and_release(db)
    r = await client.patch(f"/api/releases/{rel.id}", json={"release_date": "2026-03-15"})
    assert r.status_code == 200
    assert r.json()["release_date"] == "2026-03-15"


async def test_patch_release_update_notes(client, db):
    rel = await _seed_author_and_release(db)
    r = await client.patch(f"/api/releases/{rel.id}", json={"notes": "Publisher confirmed"})
    assert r.status_code == 200
    assert r.json()["notes"] == "Publisher confirmed"


async def test_patch_release_not_found(client):
    r = await client.patch("/api/releases/99999", json={"release_date_confirmed": True})
    assert r.status_code == 404


async def test_patch_release_partial_leaves_other_fields(client, db):
    rel = await _seed_author_and_release(db)
    r = await client.patch(f"/api/releases/{rel.id}", json={"notes": "note only"})
    assert r.status_code == 200
    data = r.json()
    assert data["notes"] == "note only"
    assert data["release_date"] == rel.release_date


# --- manual releases ---


async def test_create_and_list_manual_release(client):
    create = await client.post(
        "/api/releases/manual",
        json={
            "author": "N. K. Jemisin",
            "title": "The Stone Sky",
            "series": "The Broken Earth",
            "series_number": 3,
            "release_date": "2027-04-01",
            "media": ["audiobook", "ebook"],
            "comments": "Check publisher catalogue",
            "last_checked_at": 1_700_000_000_000,
        },
    )
    assert create.status_code == 201
    data = create.json()
    assert data["media"] == ["audiobook", "ebook"]
    assert data["series_number"] == 3
    assert data["status"] == "watching"
    assert data["uploaded_cover_url"] is None

    assert data["last_checked_at"] == 1_700_000_000_000

    listed = await client.get("/api/releases/manual")
    assert listed.status_code == 200
    assert [row["id"] for row in listed.json()] == [data["id"]]


async def test_manual_release_patch_sets_last_checked_to_updated_when_omitted(client):
    created = await client.post("/api/releases/manual", json={"title": "Check me"})
    assert created.json()["last_checked_at"] == created.json()["updated_at"]
    updated = await client.patch(
        f"/api/releases/manual/{created.json()['id']}", json={"comments": "Updated"}
    )
    assert updated.status_code == 200
    assert updated.json()["last_checked_at"] == updated.json()["updated_at"]


async def test_manual_release_patch_preserves_explicit_last_checked(client):
    created = await client.post("/api/releases/manual", json={"title": "Check me"})
    updated = await client.patch(
        f"/api/releases/manual/{created.json()['id']}",
        json={"last_checked_at": 1_700_000_000_000},
    )
    assert updated.status_code == 200
    assert updated.json()["last_checked_at"] == 1_700_000_000_000


async def test_manual_release_duplicate_is_rejected_despite_case_or_spacing(client):
    payload = {
        "author": " Ursula Le Guin ",
        "title": "  New Book",
        "release_date": "2027",
        "media": ["audiobook"],
    }
    assert (await client.post("/api/releases/manual", json=payload)).status_code == 201
    duplicate = await client.post(
        "/api/releases/manual",
        json={
            "author": "ursula le guin",
            "title": "new book",
            "release_date": "2027",
            "media": ["audiobook"],
        },
    )
    assert duplicate.status_code == 409


async def test_manual_release_archive_hides_it_by_default_and_can_be_listed(client):
    created = await client.post("/api/releases/manual", json={"title": "Archive me"})
    assert created.status_code == 201
    release_id = created.json()["id"]
    archived = await client.patch(f"/api/releases/manual/{release_id}", json={"archived": True})
    assert archived.status_code == 200
    assert archived.json()["archived"] is True
    assert (await client.get("/api/releases/manual")).json() == []
    all_entries = await client.get("/api/releases/manual?include_archived=true")
    assert [entry["id"] for entry in all_entries.json()] == [release_id]


async def test_manual_release_patch_prevents_duplicate(client):
    first = await client.post(
        "/api/releases/manual",
        json={"author": "Author", "title": "Book", "release_date": "2027-01-01"},
    )
    second = await client.post(
        "/api/releases/manual",
        json={"author": "Other", "title": "Other book", "release_date": "2027-01-01"},
    )
    result = await client.patch(
        f"/api/releases/manual/{second.json()['id']}",
        json={"author": "Author", "title": "Book"},
    )
    assert first.status_code == 201
    assert second.status_code == 201
    assert result.status_code == 409

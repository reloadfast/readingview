"""Read-only release import API, using mocked Goodreads metadata and access."""

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.services import goodreads, goodreads_import

URL = "https://www.goodreads.com/book/show/257149406-bog-standard-isekai"
SOURCE = "https://www.goodreads.com/book/show/257149406"
ENDPOINT = "/api/releases/manual/lookup-goodreads"


@pytest.fixture
def lookup():
    html = (
        '<script type="application/ld+json">'
        + json.dumps(
            {
                "@type": "Book",
                "url": URL,
                "name": "Towering",
                "author": {"name": "Miles English"},
                "datePublished": "2027-08-17",
                "bookFormat": "EBook",
                "image": "https://example.org/cover.jpg",
            }
        )
        + "</script>"
    )
    with patch("app.services.goodreads.probe", new_callable=AsyncMock) as mock:
        mock.return_value = goodreads.parse_page(html, URL)
        yield mock


async def test_lookup_returns_editable_draft_without_creating_record(client, lookup):
    response = await client.post(ENDPOINT, json={"url": URL + "?from_search=true#reviews"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "partial"
    assert data["source_url"] == SOURCE
    assert data["draft"] == {
        "title": "Towering",
        "author": "Miles English",
        "series": None,
        "series_number": None,
        "release_date": "2027-08-17",
        "media": ["ebook"],
        "cover_url": "https://example.org/cover.jpg",
        "link_url": SOURCE,
        "status": "watching",
    }
    assert data["sources"]["release_date"] == "json_ld"
    assert data["missing_fields"] == ["series", "series_number"]
    assert any("work rather than this edition" in item for item in data["warnings"])
    assert data["existing_releases"] == []
    assert (await client.get("/api/releases/manual?include_archived=true")).json() == []
    lookup.assert_awaited_once_with(SOURCE)

    # The returned draft can be saved through the unchanged create contract.
    created = await client.post("/api/releases/manual", json=data["draft"])
    assert created.status_code == 201
    assert created.json()["last_checked_at"] is not None


async def test_existing_matches_include_other_media_statuses_and_archives(client, lookup):
    expected = []
    for medium, status, archived, link in [
        ("ebook", "watching", False, URL + "?x=y#fragment"),
        ("audiobook", "owned", False, "https://goodreads.com/book/show/257149406.Other-Slug"),
        ("hardcover", "released", True, SOURCE),
    ]:
        created = (
            await client.post(
                "/api/releases/manual",
                json={
                    "title": "Towering",
                    "author": "Miles English",
                    "media": [medium],
                    "status": status,
                    "link_url": link,
                },
            )
        ).json()
        if archived:
            await client.patch(f"/api/releases/manual/{created['id']}", json={"archived": True})
        expected.append((created["id"], [medium], status, archived))
    for link in [
        "https://www.goodreads.com/book/show/2571494060",
        "https://example.org/book/show/257149406",
        "invalid",
        None,
    ]:
        await client.post("/api/releases/manual", json={"title": str(link), "link_url": link})

    before = (await client.get("/api/releases/manual?include_archived=true")).json()
    response = await client.post(ENDPOINT, json={"url": URL})
    assert response.status_code == 200
    matches = response.json()["existing_releases"]
    assert [
        (row["id"], row["media"], row["status"], row["archived"]) for row in matches
    ] == expected
    assert (await client.get("/api/releases/manual?include_archived=true")).json() == before


async def test_missing_medium_normalizes_to_empty_list(client, lookup):
    lookup.return_value = goodreads.parse_page(
        '<script type="application/ld+json">{"@type":"Book","name":"Sample"}</script>', URL
    )
    response = await client.post(ENDPOINT, json={"url": URL})
    assert response.status_code == 200
    assert response.json()["draft"]["media"] == []
    assert response.json()["draft"]["release_date"] is None


@pytest.mark.parametrize(
    "url",
    [
        "",
        "not a url",
        "https://localhost/book/show/123",
        "https://user:secret@www.goodreads.com/book/show/123",
    ],
)
async def test_invalid_url_never_fetches(client, lookup, url):
    response = await client.post(ENDPOINT, json={"url": url})
    assert response.status_code == 422
    lookup.assert_not_awaited()
    if "secret" in url:
        assert "secret" not in response.text


@pytest.mark.parametrize(
    ("status", "error_type", "expected"),
    [
        ("blocked", None, 502),
        ("too_large", None, 502),
        ("no_metadata", None, 502),
        ("http_error", None, 502),
        ("network_error", "ConnectError", 502),
        ("network_error", "ReadTimeout", 504),
        ("network_error", "ConnectTimeout", 504),
    ],
)
async def test_upstream_failures_are_actionable_without_writes(
    client, lookup, status, error_type, expected
):
    lookup.return_value = {"status": status, "url": SOURCE, "message": "upstream secret"}
    if error_type:
        lookup.return_value["error_type"] = error_type
    response = await client.post(ENDPOINT, json={"url": URL})
    assert response.status_code == expected
    assert isinstance(response.json()["detail"], str)
    assert "manually" in response.json()["detail"]
    assert "secret" not in response.text
    assert (await client.get("/api/releases/manual?include_archived=true")).json() == []


async def test_overall_lookup_deadline(client, lookup, monkeypatch):
    async def slow_lookup(url):
        await asyncio.sleep(1)

    lookup.side_effect = slow_lookup
    monkeypatch.setattr(goodreads_import, "LOOKUP_DEADLINE", 0.001)
    response = await client.post(ENDPOINT, json={"url": URL})
    assert response.status_code == 504


async def test_fetch_does_not_hold_database_transaction(engine, lookup):
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db:
        report = lookup.return_value

        async def check_transaction(url):
            assert not db.in_transaction()
            return report

        lookup.side_effect = check_transaction
        result = await goodreads_import.lookup_release(URL, db)
        assert result.draft.title == "Towering"
        assert not db.new and not db.dirty and not db.deleted


async def test_bad_metadata_is_an_upstream_failure(client, lookup):
    lookup.return_value["fields"]["series_number"] = "invalid"
    response = await client.post(ENDPOINT, json={"url": URL})
    assert response.status_code == 502

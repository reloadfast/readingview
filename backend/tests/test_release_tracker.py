"""Unit tests for release dedup and sort logic in services/release_tracker.py."""

import time
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models.releases import Release, ReleaseTrackedAuthor
from app.services.release_tracker import extract_releases, run_refresh

pytestmark = pytest.mark.unit

_SAMPLE_DOCS = [
    {
        "title": "Leviathan Wakes",
        "first_publish_year": 2011,
        "isbn": ["978-0316129084"],
        "key": "/works/OL123W",
    },
    {
        "title": "Caliban's War",
        "first_publish_year": 2012,
        "isbn": [],
        "key": "/works/OL456W",
    },
    {
        "title": "Leviathan Wakes",  # duplicate
        "first_publish_year": 2011,
        "isbn": ["978-0316129084"],
        "key": "/works/OL123W",
    },
    {
        "title": "",  # missing title — should be skipped
        "first_publish_year": 2020,
        "isbn": [],
        "key": "/works/OL000W",
    },
]


def test_extract_releases_deduplication():
    releases = extract_releases(_SAMPLE_DOCS, "James S.A. Corey")
    titles = [r["title"] for r in releases]
    assert titles.count("Leviathan Wakes") == 1


def test_extract_releases_skips_empty_title():
    releases = extract_releases(_SAMPLE_DOCS, "James S.A. Corey")
    assert all(r["title"] for r in releases)


def test_extract_releases_sorted_desc_by_date():
    releases = extract_releases(_SAMPLE_DOCS, "James S.A. Corey")
    dates = [r["release_date"] for r in releases if r["release_date"]]
    assert dates == sorted(dates, reverse=True)


def test_extract_releases_author_name_propagated():
    releases = extract_releases(_SAMPLE_DOCS, "Test Author")
    assert all(r["author_name"] == "Test Author" for r in releases)


def test_extract_releases_isbn_first_entry():
    releases = extract_releases(_SAMPLE_DOCS, "Test Author")
    lw = next(r for r in releases if r["title"] == "Leviathan Wakes")
    assert lw["isbn"] == "978-0316129084"


def test_extract_releases_no_isbn():
    releases = extract_releases(_SAMPLE_DOCS, "Test Author")
    cw = next(r for r in releases if r["title"] == "Caliban's War")
    assert cw["isbn"] is None


def test_extract_releases_link_url_constructed():
    releases = extract_releases(_SAMPLE_DOCS, "Test Author")
    lw = next(r for r in releases if r["title"] == "Leviathan Wakes")
    assert lw["link_url"] is not None
    assert "/works/" in lw["link_url"]


def test_extract_releases_source_is_openlibrary():
    releases = extract_releases(_SAMPLE_DOCS, "Test Author")
    assert all(r["source"] == "openlibrary" for r in releases)


def test_extract_releases_empty_docs():
    assert extract_releases([], "Nobody") == []


def test_extract_releases_no_year():
    docs = [{"title": "Untitled", "key": "/works/OL1W"}]
    releases = extract_releases(docs, "Author")
    assert releases[0]["release_date"] is None


def test_extract_releases_confirmed_when_year_present():
    releases = extract_releases(_SAMPLE_DOCS, "James S.A. Corey")
    lw = next(r for r in releases if r["title"] == "Leviathan Wakes")
    assert lw["release_date_confirmed"] is True


def test_extract_releases_not_confirmed_when_no_year():
    docs = [{"title": "Untitled", "key": "/works/OL1W"}]
    releases = extract_releases(docs, "Author")
    assert releases[0]["release_date_confirmed"] is False


# ---------------------------------------------------------------------------
# run_refresh integration tests (mocked HTTP)
# ---------------------------------------------------------------------------


@pytest.fixture
async def db(engine):
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session


_MOCK_DOCS = [
    {
        "title": "New Book",
        "first_publish_year": 2025,
        "isbn": ["978-1234567890"],
        "key": "/works/OL999W",
    }
]


async def test_run_refresh_no_authors(db):
    result = await run_refresh(db)
    assert result.added == 0
    assert result.skipped == 0
    assert result.failed == 0


async def test_run_refresh_adds_new_release(db):
    async with db.begin():
        author = ReleaseTrackedAuthor(name="Test Author", added_at=int(time.time() * 1000))
        db.add(author)

    with patch(
        "app.services.release_tracker.fetch_author_works",
        new_callable=AsyncMock,
        return_value=_MOCK_DOCS,
    ):
        result = await run_refresh(db)

    assert result.added == 1
    assert result.skipped == 0
    assert result.failed == 0


async def test_run_refresh_skips_existing_release(db):
    async with db.begin():
        author = ReleaseTrackedAuthor(name="Known Author", added_at=int(time.time() * 1000))
        db.add(author)
        await db.flush()
        db.add(
            Release(
                author_id=author.id,
                title="New Book",
                release_date="2025",
                release_date_confirmed=True,
                ol_key="/works/OL999W",
                link_url=None,
                source="openlibrary",
            )
        )

    with patch(
        "app.services.release_tracker.fetch_author_works",
        new_callable=AsyncMock,
        return_value=_MOCK_DOCS,
    ):
        result = await run_refresh(db)

    assert result.added == 0
    assert result.skipped == 1


async def test_run_refresh_records_http_failure(db):
    async with db.begin():
        author = ReleaseTrackedAuthor(name="Failing Author", added_at=int(time.time() * 1000))
        db.add(author)

    with patch(
        "app.services.release_tracker.fetch_author_works",
        new_callable=AsyncMock,
        side_effect=httpx.ConnectError("timeout"),
    ):
        result = await run_refresh(db)

    assert result.failed == 1
    assert result.errors[0].author == "Failing Author"

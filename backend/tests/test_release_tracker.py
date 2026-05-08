"""Unit tests for release dedup and sort logic in services/release_tracker.py."""

import pytest

from app.services.release_tracker import extract_releases

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

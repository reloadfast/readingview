"""Tests for library API — field mapping and pure helpers."""

import pytest

from app.api.library import _item_to_book, _parse_progress, _parse_series, _sort_books
from app.schemas.library import BookProgress, LibraryBook

pytestmark = pytest.mark.unit


def _make_item(
    item_id: str = "item-1",
    title: str = "Test Book",
    author: str = "Test Author",
    narrator: str | None = "Test Narrator",
    duration: float = 3600.0,
    genres: list | None = None,
    series: list | None = None,
) -> dict:
    return {
        "id": item_id,
        "media": {
            "duration": duration,
            "metadata": {
                "title": title,
                "authorName": author,
                "narratorName": narrator,
                "genres": genres or [],
                "series": series or [],
                "description": "A test book.",
                "publishedYear": "2020",
                "isbn": "123-456",
                "asin": None,
            },
        },
    }


def _cover(item_id: str) -> str:
    return f"http://abs.test/api/items/{item_id}/cover"


# --- _parse_progress ---


def test_parse_progress_finished():
    raw = {"isFinished": True, "progress": 1.0, "currentTime": 3600.0, "finishedAt": 1700000000000}
    p = _parse_progress(raw, 3600.0)
    assert p.is_finished is True
    assert p.progress_pct == 100.0
    assert p.time_remaining == 0.0


def test_parse_progress_partial():
    raw = {"isFinished": False, "progress": 0.5, "currentTime": 1800.0}
    p = _parse_progress(raw, 3600.0)
    assert p.is_finished is False
    assert p.progress_pct == pytest.approx(50.0)
    assert p.time_remaining == pytest.approx(1800.0)


def test_parse_progress_none_fields():
    raw = {"isFinished": False}
    p = _parse_progress(raw, 3600.0)
    assert p.progress_pct == 0.0
    assert p.current_time == 0.0


# --- _parse_series ---


def test_parse_series_dict_entries():
    raw = [{"name": "The Expanse", "sequence": "1"}, {"name": "Spin-off", "sequence": None}]
    entries = _parse_series(raw)
    assert entries[0].name == "The Expanse"
    assert entries[0].sequence == "1"


def test_parse_series_string_entries():
    entries = _parse_series(["The Expanse"])
    assert entries[0].name == "The Expanse"
    assert entries[0].sequence is None


def test_parse_series_empty():
    assert _parse_series([]) == []
    assert _parse_series(None) == []


# --- _item_to_book ---


def test_item_to_book_fields():
    item = _make_item("id-1", "My Book", "An Author", duration=7200.0)
    book = _item_to_book(item, {}, _cover)
    assert book.id == "id-1"
    assert book.title == "My Book"
    assert book.authors == "An Author"
    assert book.duration == 7200.0
    assert book.cover_url == "http://abs.test/api/items/id-1/cover"
    assert book.progress is None


def test_item_to_book_with_progress_map():
    item = _make_item("id-2", duration=3600.0)
    progress_map = {"id-2": {"isFinished": True, "progress": 1.0, "currentTime": 3600.0}}
    book = _item_to_book(item, progress_map, _cover)
    assert book.progress is not None
    assert book.progress.is_finished is True


def test_item_to_book_missing_title_fallback():
    item = {"id": "x", "media": {"duration": 0, "metadata": {}}}
    book = _item_to_book(item, {}, _cover)
    assert book.title == "Unknown Title"
    assert book.authors == "Unknown Author"


# --- _sort_books ---


def _make_book(
    title: str, progress_pct: float = 0.0, last_update: int = 0, finished_at: int = 0
) -> LibraryBook:
    progress = BookProgress(
        is_finished=finished_at > 0,
        progress_pct=progress_pct,
        current_time=0,
        time_remaining=0,
        last_update=last_update,
        finished_at=finished_at if finished_at else None,
    )
    return LibraryBook(
        id=title,
        title=title,
        authors="Author",
        duration=0,
        cover_url="",
        genres=[],
        series=[],
        progress=progress,
    )


def test_sort_by_title():
    books = [_make_book("Zebra"), _make_book("Apple"), _make_book("Mango")]
    sorted_books = _sort_books(books, "title")
    assert [b.title for b in sorted_books] == ["Apple", "Mango", "Zebra"]


def test_sort_by_progress_asc():
    books = [_make_book("C", 80.0), _make_book("A", 20.0), _make_book("B", 50.0)]
    sorted_books = _sort_books(books, "progress_asc")
    pcts = [b.progress.progress_pct for b in sorted_books]
    assert pcts == sorted(pcts)


def test_sort_by_progress_desc():
    books = [_make_book("C", 80.0), _make_book("A", 20.0), _make_book("B", 50.0)]
    sorted_books = _sort_books(books, "progress_desc")
    pcts = [b.progress.progress_pct for b in sorted_books]
    assert pcts == sorted(pcts, reverse=True)


def test_sort_by_updated():
    books = [
        _make_book("A", last_update=100),
        _make_book("B", last_update=300),
        _make_book("C", last_update=200),
    ]
    sorted_books = _sort_books(books, "updated")
    updates = [b.progress.last_update for b in sorted_books]
    assert updates == sorted(updates, reverse=True)


def test_sort_unknown_key_returns_unchanged():
    books = [_make_book("Z"), _make_book("A")]
    result = _sort_books(books, "unknown")
    assert [b.title for b in result] == ["Z", "A"]

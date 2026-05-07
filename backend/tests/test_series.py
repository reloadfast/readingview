"""Unit tests for series grouping and progress calculation."""
import pytest

from app.services.series import (
    _format_duration,
    _parse_sequence,
    compute_series_detail,
    compute_series_list,
)

pytestmark = pytest.mark.unit

_LIBRARY_SERIES = [
    [
        {
            "name": "The Expanse",
            "books": [
                {
                    "id": "book-1",
                    "sequence": "1",
                    "media": {
                        "duration": 72000.0,
                        "metadata": {"title": "Leviathan Wakes", "authorName": "James S.A. Corey"},
                    },
                },
                {
                    "id": "book-2",
                    "sequence": "2",
                    "media": {
                        "duration": 80000.0,
                        "metadata": {"title": "Caliban's War", "authorName": "James S.A. Corey"},
                    },
                },
                {
                    "id": "book-3",
                    "sequence": "3",
                    "media": {
                        "duration": 68000.0,
                        "metadata": {"title": "Abaddon's Gate", "authorName": "James S.A. Corey"},
                    },
                },
            ],
        }
    ]
]

_PROGRESS_FINISHED = {"book-1": {"isFinished": True, "progress": 1.0}}
_PROGRESS_PARTIAL = {"book-2": {"isFinished": False, "progress": 0.5}}


# --- _parse_sequence ---

def test_parse_sequence_integer():
    assert _parse_sequence("1") == 1.0


def test_parse_sequence_float():
    assert _parse_sequence("2.5") == 2.5


def test_parse_sequence_none():
    assert _parse_sequence(None) == float("inf")


def test_parse_sequence_empty():
    assert _parse_sequence("") == float("inf")


def test_parse_sequence_non_numeric():
    assert _parse_sequence("prequel") == float("inf")


# --- _format_duration ---

def test_format_duration_hours_and_minutes():
    assert _format_duration(3661) == "1h 1m"


def test_format_duration_under_one_hour():
    assert _format_duration(1800) == "30m"


def test_format_duration_zero():
    assert _format_duration(0) == "0m"


# --- compute_series_list ---

def test_compute_series_list_returns_summary():
    summaries = compute_series_list(_LIBRARY_SERIES, {})
    assert len(summaries) == 1
    s = summaries[0]
    assert s.name == "The Expanse"
    assert s.total == 3
    assert s.finished == 0
    assert s.not_started == 3
    assert s.percent_complete == 0.0


def test_compute_series_list_with_progress():
    progress = {
        "book-1": {"isFinished": True, "progress": 1.0},
        "book-2": {"isFinished": False, "progress": 0.6},
    }
    summaries = compute_series_list(_LIBRARY_SERIES, progress)
    s = summaries[0]
    assert s.finished == 1
    assert s.in_progress == 1
    assert s.not_started == 1
    assert s.percent_complete == pytest.approx(33.3, rel=1e-1)


def test_compute_series_list_sorted_by_name():
    two_series = [
        [{"name": "Zebra", "books": []}],
        [{"name": "Alpha", "books": []}],
    ]
    summaries = compute_series_list(two_series, {})
    names = [s.name for s in summaries]
    assert names == sorted(names, key=str.lower)


def test_compute_series_list_skips_unnamed():
    unnamed = [[{"name": "", "books": []}]]
    assert compute_series_list(unnamed, {}) == []


# --- compute_series_detail ---

def test_compute_series_detail_found():
    detail = compute_series_detail("The Expanse", _LIBRARY_SERIES, {})
    assert detail is not None
    assert detail.name == "The Expanse"
    assert len(detail.books) == 3


def test_compute_series_detail_books_sorted_by_sequence():
    detail = compute_series_detail("The Expanse", _LIBRARY_SERIES, {})
    assert detail is not None
    sequences = [float(b.sequence) for b in detail.books if b.sequence]
    assert sequences == sorted(sequences)


def test_compute_series_detail_not_found():
    assert compute_series_detail("Unknown Series", _LIBRARY_SERIES, {}) is None


def test_compute_series_detail_progress():
    progress = {"book-1": {"isFinished": True, "progress": 1.0}}
    detail = compute_series_detail("The Expanse", _LIBRARY_SERIES, progress)
    assert detail is not None
    book1 = next(b for b in detail.books if b.id == "book-1")
    assert book1.is_finished is True
    assert book1.progress == 100.0

"""Unit tests for pure calculation functions in services/statistics.py."""

from datetime import UTC, date, datetime

import pytest

from app.services.statistics import (
    _compute_streaks,
    _get_finished_books,
    _group_by_month,
    _group_by_year,
    compute_overall_stats,
    compute_recap,
    compute_yearly_stats,
)

pytestmark = pytest.mark.unit


def _ts(year: int, month: int, day: int) -> int:
    return int(datetime(year, month, day, tzinfo=UTC).timestamp() * 1000)


_PROGRESS_MAP = {
    "book-1": {
        "isFinished": True,
        "finishedAt": _ts(2024, 1, 15),
        "startedAt": _ts(2024, 1, 1),
        "duration": 36000,
        "progress": 1.0,
    },
    "book-2": {
        "isFinished": True,
        "finishedAt": _ts(2024, 3, 20),
        "startedAt": _ts(2024, 3, 5),
        "duration": 72000,
        "progress": 1.0,
    },
    "book-3": {
        "isFinished": True,
        "finishedAt": _ts(2023, 10, 10),
        "startedAt": _ts(2023, 9, 25),
        "duration": 54000,
        "progress": 1.0,
    },
    "book-4": {"isFinished": False, "progress": 0.5},
}

_STATS_ITEMS = {
    "book-1": {
        "timeListening": 34000,
        "mediaMetadata": {
            "title": "Book One",
            "authors": [{"name": "Author A"}],
            "narrators": ["Narrator X"],
            "genres": ["Fantasy"],
            "series": [],
        },
    },
    "book-2": {
        "timeListening": 70000,
        "mediaMetadata": {
            "title": "Book Two",
            "authors": [{"name": "Author B"}],
            "narrators": ["Narrator Y"],
            "genres": ["Sci-Fi", "Adventure"],
            "series": [{"name": "The Series"}],
        },
    },
    "book-3": {
        "timeListening": 50000,
        "mediaMetadata": {
            "title": "Book Three",
            "authors": [{"name": "Author A"}],
            "narrators": ["Narrator X"],
            "genres": ["Mystery"],
            "series": [],
        },
    },
    "book-4": {
        "timeListening": 10000,
        "mediaMetadata": {
            "title": "Book Four (In Progress)",
            "authors": [{"name": "Author C"}],
            "narrators": [],
            "genres": [],
            "series": [],
        },
    },
}

_LISTENING_STATS = {"totalTime": 154000, "items": _STATS_ITEMS}


# --- _get_finished_books ---


def test_get_finished_books_excludes_in_progress():
    finished = _get_finished_books(_PROGRESS_MAP, _STATS_ITEMS)
    ids = {b["id"] for b in finished}
    assert "book-4" not in ids
    assert len(finished) == 3


def test_get_finished_books_sorted_by_finished_at():
    finished = _get_finished_books(_PROGRESS_MAP, _STATS_ITEMS)
    timestamps = [b["finished_at"] for b in finished]
    assert timestamps == sorted(timestamps)


def test_get_finished_books_unknown_author_fallback():
    finished = _get_finished_books(
        {"x": {"isFinished": True, "finishedAt": _ts(2024, 1, 1)}},
        {},
    )
    assert finished[0]["author"] == "Unknown Author"


# --- _group_by_year / _group_by_month ---


def test_group_by_year():
    books = _get_finished_books(_PROGRESS_MAP, _STATS_ITEMS)
    by_year = _group_by_year(books)
    assert "2024" in by_year
    assert "2023" in by_year
    assert len(by_year["2024"]) == 2
    assert len(by_year["2023"]) == 1


def test_group_by_month():
    books = _get_finished_books(_PROGRESS_MAP, _STATS_ITEMS)
    by_month = _group_by_month(books)
    assert "2024-01" in by_month
    assert "2024-03" in by_month
    assert len(by_month["2024-01"]) == 1


def test_group_by_year_skips_missing_timestamp():
    by_year = _group_by_year([{"finished_at": None, "id": "x"}])
    assert by_year == {}


# --- _compute_streaks ---


def test_compute_streaks_empty():
    result = _compute_streaks([])
    assert result.current == 0
    assert result.longest == 0
    assert result.total_days == 0


def test_compute_streaks_consecutive():
    today = date.today()
    sessions = [
        {
            "updatedAt": int(
                datetime(today.year, today.month, today.day, tzinfo=UTC).timestamp() * 1000
            )
        },
        {
            "updatedAt": int(
                datetime(today.year, today.month, today.day, tzinfo=UTC).timestamp() * 1000
            )
            - 86_400_000
        },
        {
            "updatedAt": int(
                datetime(today.year, today.month, today.day, tzinfo=UTC).timestamp() * 1000
            )
            - 2 * 86_400_000
        },
    ]
    result = _compute_streaks(sessions)
    assert result.longest >= 3
    assert result.total_days >= 3


def test_compute_streaks_broken():
    sessions = [
        {"updatedAt": _ts(2024, 1, 1)},
        {"updatedAt": _ts(2024, 1, 3)},  # gap on Jan 2
    ]
    result = _compute_streaks(sessions)
    assert result.longest == 1
    assert result.current == 0  # not active recently


def test_compute_streaks_ignores_invalid_ts():
    result = _compute_streaks([{"updatedAt": "bad"}, {"startedAt": None}])
    assert result.total_days == 0


# --- compute_overall_stats ---


def test_compute_overall_stats_counts():
    stats = compute_overall_stats(_PROGRESS_MAP, _LISTENING_STATS, [])
    assert stats.books_completed == 3
    assert stats.unique_authors == 3  # Author A, Author B, Author C (all stats_items counted)
    assert stats.hours_listened == pytest.approx(154000 / 3600, rel=1e-2)


def test_compute_overall_stats_empty():
    stats = compute_overall_stats({}, {}, [])
    assert stats.books_completed == 0
    assert stats.hours_listened == 0.0


# --- compute_yearly_stats ---


def test_compute_yearly_stats_2024():
    stats = compute_yearly_stats("2024", _PROGRESS_MAP, _LISTENING_STATS)
    assert stats.year == "2024"
    assert stats.books_in_year == 2
    assert len(stats.monthly_chart) == 12
    jan = next(p for p in stats.monthly_chart if p.month == "2024-01")
    assert jan.books == 1


def test_compute_yearly_stats_genre_breakdown():
    stats = compute_yearly_stats("2024", _PROGRESS_MAP, _LISTENING_STATS)
    genre_names = {g.name for g in stats.genre_breakdown}
    assert "Fantasy" in genre_names
    assert "Sci-Fi" in genre_names


def test_compute_yearly_stats_empty_year():
    stats = compute_yearly_stats("2099", _PROGRESS_MAP, _LISTENING_STATS)
    assert stats.books_in_year == 0


# --- compute_recap ---


def test_compute_recap_basic():
    recap = compute_recap("2024", _PROGRESS_MAP, _LISTENING_STATS)
    assert recap.year == "2024"
    assert recap.books_finished == 2
    assert recap.longest_book is not None
    assert recap.shortest_book is not None


def test_compute_recap_fastest_slowest():
    recap = compute_recap("2024", _PROGRESS_MAP, _LISTENING_STATS)
    assert recap.fastest_read is not None
    assert recap.slowest_read is not None
    assert recap.fastest_read.days <= recap.slowest_read.days


def test_compute_recap_empty_year():
    recap = compute_recap("2099", _PROGRESS_MAP, _LISTENING_STATS)
    assert recap.books_finished == 0
    assert recap.longest_book is None

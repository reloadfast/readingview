"""Unit tests for pure calculation functions in services/statistics.py."""

from datetime import UTC, date, datetime

import pytest

from app.services.statistics import (
    _compute_streaks,
    _get_finished_books,
    _group_by_month,
    _group_by_year,
    compute_author_narrator_affinity,
    compute_backlog_health,
    compute_book_length_preferences,
    compute_completion_velocity,
    compute_duration_completion_correlation,
    compute_extra_listening,
    compute_genre_completion_correlation,
    compute_goal_forecast,
    compute_heatmap,
    compute_listening_habits,
    compute_monthly_comparison,
    compute_overall_stats,
    compute_recap,
    compute_series_progress,
    compute_statistics_detail,
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


# ---------------------------------------------------------------------------
# compute_completion_velocity
# ---------------------------------------------------------------------------


def test_completion_velocity_reports_median_and_monthly_threshold():
    progress = {
        "jan-1": {"isFinished": True, "startedAt": _ts(2024, 1, 1), "finishedAt": _ts(2024, 1, 2)},
        "jan-2": {"isFinished": True, "startedAt": _ts(2024, 1, 1), "finishedAt": _ts(2024, 1, 4)},
        "jan-3": {"isFinished": True, "startedAt": _ts(2024, 1, 1), "finishedAt": _ts(2024, 1, 10)},
        "feb-1": {"isFinished": True, "startedAt": _ts(2024, 2, 1), "finishedAt": _ts(2024, 2, 3)},
        "invalid": {
            "isFinished": True,
            "startedAt": _ts(2024, 2, 4),
            "finishedAt": _ts(2024, 2, 4),
        },
        "missing": {"isFinished": True, "finishedAt": _ts(2024, 2, 5)},
    }

    result = compute_completion_velocity("2024", progress, {"items": {}})

    assert result.qualifying_books == 4
    assert result.median_days == 2.5
    assert [
        (month.month, month.qualifying_books, month.median_days) for month in result.monthly_trend
    ] == [
        ("2024-01", 3, 3.0),
        ("2024-02", 1, None),
    ]


def test_completion_velocity_uses_local_finished_year_and_handles_empty_data():
    # Midnight UTC is still Dec. 31 in Los Angeles, so it belongs to 2023 there.
    progress = {
        "boundary": {
            "isFinished": True,
            "startedAt": _ts(2023, 12, 30),
            "finishedAt": _ts(2024, 1, 1),
        }
    }

    result = compute_completion_velocity("2023", progress, {"items": {}}, "America/Los_Angeles")
    empty = compute_completion_velocity("2024", progress, {"items": {}}, "America/Los_Angeles")

    assert result.qualifying_books == 1
    assert result.median_days == 2.0
    assert empty.qualifying_books == 0
    assert empty.median_days is None
    assert empty.monthly_trend == []


# ---------------------------------------------------------------------------
# compute_monthly_comparison
# ---------------------------------------------------------------------------


def test_monthly_comparison_uses_sessions_for_hours_and_includes_empty_months():
    progress = {
        "finished": {"isFinished": True, "finishedAt": _ts(2024, 1, 10)},
        "not-finished": {"isFinished": False, "finishedAt": _ts(2024, 1, 12)},
    }
    sessions = [
        _session(2024, 1, 5, 90 * 60),
        _session(2024, 2, 1, 30 * 60),
        _session(2024, 2, 2, 0),
        _session(2023, 12, 31, 60 * 60),
    ]

    result = compute_monthly_comparison("2024", progress, {"items": {}}, sessions)

    assert result.timezone == "UTC"
    assert len(result.monthly) == 12
    assert result.monthly[0].model_dump() == {
        "month": "2024-01",
        "books_completed": 1,
        "listening_hours": 1.5,
    }
    assert result.monthly[1].model_dump() == {
        "month": "2024-02",
        "books_completed": 0,
        "listening_hours": 0.5,
    }
    assert result.monthly[2].model_dump() == {
        "month": "2024-03",
        "books_completed": 0,
        "listening_hours": 0.0,
    }


def test_monthly_comparison_applies_local_timezone_to_sessions_and_completions():
    progress = {
        "boundary": {
            "isFinished": True,
            "finishedAt": _ts(2024, 1, 1),
        }
    }
    sessions = [{"updatedAt": _ts(2024, 1, 1), "timeListening": 3600}]

    result = compute_monthly_comparison(
        "2023", progress, {"items": {}}, sessions, "America/Los_Angeles"
    )

    assert result.monthly[-1].model_dump() == {
        "month": "2023-12",
        "books_completed": 1,
        "listening_hours": 1.0,
    }


# ---------------------------------------------------------------------------
# compute_book_length_preferences
# ---------------------------------------------------------------------------


def test_book_length_preferences_buckets_durations_and_completion_pace():
    progress = {
        "short": {
            "isFinished": True,
            "duration": 4 * 3600,
            "startedAt": _ts(2024, 1, 1),
            "finishedAt": _ts(2024, 1, 3),
        },
        "medium-1": {
            "isFinished": True,
            "duration": 6 * 3600,
            "startedAt": _ts(2024, 1, 1),
            "finishedAt": _ts(2024, 1, 5),
        },
        "medium-2": {"isFinished": True, "duration": 9.5 * 3600, "finishedAt": _ts(2024, 2, 5)},
        "long": {
            "isFinished": True,
            "duration": 35 * 3600,
            "startedAt": _ts(2024, 2, 1),
            "finishedAt": _ts(2024, 2, 11),
        },
        "invalid": {"isFinished": True, "duration": 0, "finishedAt": _ts(2024, 2, 3)},
    }

    result = compute_book_length_preferences("2024", progress, {"items": {}})

    assert result.qualifying_books == 4
    assert result.median_duration_hours == 7.8
    assert [
        (
            item.label,
            item.completed_books,
            item.pace_qualifying_books,
            item.median_days_to_finish,
        )
        for item in result.distribution
    ] == [
        ("Under 5 hours", 1, 1, 2.0),
        ("5–9:59 hours", 2, 1, 4.0),
        ("10–19:59 hours", 0, 0, None),
        ("20–29:59 hours", 0, 0, None),
        ("30 hours or more", 1, 1, 10.0),
    ]


def test_book_length_preferences_excludes_unattributable_or_wrong_year_books():
    progress = {
        "boundary": {"isFinished": True, "duration": 4 * 3600, "finishedAt": _ts(2024, 1, 1)},
        "missing-finish": {"isFinished": True, "duration": 4 * 3600},
    }

    result = compute_book_length_preferences("2023", progress, {"items": {}}, "America/Los_Angeles")

    assert result.qualifying_books == 1
    assert result.distribution[0].completed_books == 1
    assert result.distribution[0].median_days_to_finish is None


# ---------------------------------------------------------------------------
# compute_goal_forecast
# ---------------------------------------------------------------------------


def test_goal_forecast_projects_from_trailing_30_day_completion_pace():
    progress = {
        "old": {"isFinished": True, "finishedAt": _ts(2024, 1, 1)},
        "recent-1": {"isFinished": True, "finishedAt": _ts(2024, 1, 20)},
        "recent-2": {"isFinished": True, "finishedAt": _ts(2024, 2, 10)},
    }

    result = compute_goal_forecast(2024, 12, progress, {"items": {}}, as_of=date(2024, 2, 15))

    assert result.eligible is True
    assert result.books_completed == 3
    assert result.trailing_30_day_completions == 2
    assert result.projected_books == 24.3
    assert result.required_books_per_week == 0.2


def test_goal_forecast_enforces_eligibility_rules():
    progress = {"old": {"isFinished": True, "finishedAt": _ts(2024, 1, 1)}}

    too_early = compute_goal_forecast(2024, 12, progress, {"items": {}}, as_of=date(2024, 1, 10))
    no_recent_completion = compute_goal_forecast(
        2024, 12, progress, {"items": {}}, as_of=date(2024, 2, 15)
    )
    no_goal = compute_goal_forecast(2024, None, progress, {"items": {}}, as_of=date(2024, 2, 15))

    assert too_early.eligible is False
    assert "14 days" in (too_early.ineligibility_reason or "")
    assert no_recent_completion.eligible is False
    assert "last 30 days" in (no_recent_completion.ineligibility_reason or "")
    assert no_goal.has_goal is False


# ---------------------------------------------------------------------------
# compute_backlog_health
# ---------------------------------------------------------------------------


def test_backlog_health_counts_statuses_and_remaining_time():
    items = [
        {"id": "unstarted", "media": {"duration": 10 * 3600}},
        {"id": "in-progress", "media": {"duration": 20 * 3600}},
        {"id": "completed", "media": {"duration": 5 * 3600}},
        {"id": "missing-duration", "media": {}},
    ]
    progress = {
        "in-progress": {"progress": 0.25, "isFinished": False},
        "completed": {"progress": 1, "isFinished": True},
        "missing-duration": {"progress": 0.5, "isFinished": False},
    }

    result = compute_backlog_health(items, progress)

    assert result.unstarted_books == 1
    assert result.in_progress_books == 2
    assert result.completed_books == 1
    assert result.partially_started_books == 2
    assert result.unstarted_remaining_hours == 10.0
    assert result.in_progress_remaining_hours == 15.0
    assert result.total_remaining_hours == 25.0
    assert result.unstarted_duration_books == 1
    assert result.in_progress_duration_books == 1


def test_backlog_health_omits_invalid_progress_and_duration_from_totals():
    items = [
        {"id": "zero-progress", "media": {"duration": 4 * 3600}},
        {"id": "invalid-progress", "media": {"duration": 4 * 3600}},
        {"id": "invalid-duration", "media": {"duration": -10}},
    ]
    progress = {
        "zero-progress": {"progress": 0, "isFinished": False},
        "invalid-progress": {"progress": "half", "isFinished": False},
        "invalid-duration": {"progress": 0.5, "isFinished": False},
    }

    result = compute_backlog_health(items, progress)

    assert result.unstarted_books == 1
    assert result.in_progress_books == 1
    assert result.unstarted_remaining_hours == 4.0
    assert result.in_progress_remaining_hours == 0.0
    assert result.total_remaining_hours == 4.0


# ---------------------------------------------------------------------------
# compute_series_progress
# ---------------------------------------------------------------------------


def test_series_progress_orders_closest_series_and_calculates_remaining_hours():
    series = [
        [
            {
                "name": "Two Left",
                "books": [
                    {"id": "done", "media": {"duration": 10 * 3600}},
                    {"id": "partial", "media": {"duration": 10 * 3600}},
                    {"id": "new", "media": {"duration": 5 * 3600}},
                ],
            },
            {
                "name": "One Left",
                "books": [
                    {"id": "done-2", "media": {"duration": 10 * 3600}},
                    {"id": "new-2", "media": {"duration": 8 * 3600}},
                ],
            },
        ]
    ]
    progress = {
        "done": {"isFinished": True},
        "partial": {"isFinished": False, "progress": 0.5},
        "done-2": {"isFinished": True},
    }

    result = compute_series_progress(series, progress)

    assert [item.name for item in result] == ["One Left", "Two Left"]
    assert result[0].model_dump() == {
        "name": "One Left",
        "completed_books": 1,
        "remaining_books": 1,
        "remaining_hours": 8.0,
        "remaining_duration_books": 1,
    }
    assert result[1].remaining_hours == 10.0


def test_series_progress_excludes_complete_and_insufficient_series_data():
    series = [
        [
            {"name": "Complete", "books": [{"id": "done", "media": {"duration": 3600}}]},
            {"name": "No books", "books": []},
            {"name": "Missing id", "books": [{"media": {"duration": 3600}}]},
        ]
    ]

    result = compute_series_progress(series, {"done": {"isFinished": True}})

    assert result == []


# ---------------------------------------------------------------------------
# compute_author_narrator_affinity
# ---------------------------------------------------------------------------


def test_author_narrator_affinity_counts_multi_credit_and_filters_small_libraries():
    items = [
        {"id": "one", "media": {"metadata": {"authorName": "Ada, Bea", "narratorName": "Nia"}}},
        {
            "id": "two",
            "media": {"metadata": {"authors": [{"name": "Ada"}], "narrators": ["Nia", "Omar"]}},
        },
        {"id": "three", "media": {"metadata": {"authorName": "Ada", "narratorName": "Nia"}}},
        {"id": "four", "media": {"metadata": {"authorName": "Bea", "narratorName": "Omar"}}},
    ]
    progress = {
        "one": {"isFinished": True},
        "two": {"isFinished": True},
        "three": {"isFinished": False},
    }
    stats = {
        "items": {
            "one": {"timeListening": 3600},
            "two": {"timeListening": 7200},
            "three": {"timeListening": 1800},
            "four": {"timeListening": -1},
        }
    }

    result = compute_author_narrator_affinity(items, progress, stats)

    assert [person.model_dump() for person in result.authors] == [
        {
            "name": "Ada",
            "available_books": 3,
            "completed_books": 2,
            "completion_rate": 66.7,
            "listened_hours": 3.5,
        }
    ]
    assert [person.model_dump() for person in result.narrators] == [
        {
            "name": "Nia",
            "available_books": 3,
            "completed_books": 2,
            "completion_rate": 66.7,
            "listened_hours": 3.5,
        }
    ]


# ---------------------------------------------------------------------------
# compute_genre_completion_correlation
# ---------------------------------------------------------------------------


def test_genre_completion_correlation_uses_known_progress_denominator():
    items = [
        {"id": "one", "media": {"metadata": {"genres": ["Fantasy", "Adventure"]}}},
        {"id": "two", "media": {"metadata": {"genres": ["Fantasy"]}}},
        {"id": "three", "media": {"metadata": {"genres": ["Fantasy"]}}},
        {"id": "four", "media": {"metadata": {"genres": ["Fantasy"]}}},
        {"id": "five", "media": {"metadata": {"genres": ["Adventure"]}}},
    ]
    progress = {
        "one": {"isFinished": True, "startedAt": _ts(2024, 1, 1), "finishedAt": _ts(2024, 1, 3)},
        "two": {"isFinished": True, "startedAt": _ts(2024, 1, 1), "finishedAt": _ts(2024, 1, 7)},
        "three": {"isFinished": False, "progress": 0.5},
        "four": {"isFinished": False, "progress": 0},
        "five": {"isFinished": True, "startedAt": _ts(2024, 1, 1), "finishedAt": _ts(2024, 1, 5)},
    }

    result = compute_genre_completion_correlation(items, progress)

    assert [genre.model_dump() for genre in result] == [
        {
            "name": "Fantasy",
            "known_progress_books": 4,
            "started_or_completed_books": 3,
            "completed_books": 2,
            "completion_rate": 50.0,
            "pace_qualifying_books": 2,
            "median_days_to_finish": 4.0,
        }
    ]


# ---------------------------------------------------------------------------
# compute_duration_completion_correlation
# ---------------------------------------------------------------------------


def test_duration_completion_correlation_reports_pearson_direction_for_ten_books():
    progress = {
        f"book-{index}": {
            "isFinished": True,
            "duration": index * 3600,
            "startedAt": _ts(2024, 1, 1),
            "finishedAt": _ts(2024, 1, 1 + index),
        }
        for index in range(1, 11)
    }
    stats = {
        "items": {
            f"book-{index}": {"mediaMetadata": {"title": f"Book {index}"}} for index in range(1, 11)
        }
    }

    result = compute_duration_completion_correlation("2024", progress, stats)

    assert result.qualifying_books == 10
    assert result.correlation_coefficient == 1.0
    assert result.correlation_method == "Pearson correlation coefficient"
    assert result.direction == "positive"


def test_duration_completion_correlation_omits_coefficient_without_variation():
    progress = {
        f"book-{index}": {
            "isFinished": True,
            "duration": 10 * 3600,
            "startedAt": _ts(2024, 1, 1),
            "finishedAt": _ts(2024, 1, 1 + index),
        }
        for index in range(1, 11)
    }

    result = compute_duration_completion_correlation("2024", progress, {"items": {}})

    assert result.correlation_coefficient is None
    assert result.correlation_method is None
    assert result.direction == "no clear"


# ---------------------------------------------------------------------------
# compute_extra_listening
# ---------------------------------------------------------------------------


def test_extra_listening_surfaces_completed_titles_at_125_percent_or_more():
    progress = {
        "threshold": {"isFinished": True, "duration": 10 * 3600, "finishedAt": _ts(2024, 1, 1)},
        "above": {"isFinished": True, "duration": 5 * 3600, "finishedAt": _ts(2024, 1, 2)},
        "below": {"isFinished": True, "duration": 5 * 3600, "finishedAt": _ts(2024, 1, 3)},
        "invalid": {"isFinished": True, "duration": 0, "finishedAt": _ts(2024, 1, 4)},
    }
    stats = {
        "items": {
            "threshold": {"timeListening": 12.5 * 3600, "mediaMetadata": {"title": "Threshold"}},
            "above": {"timeListening": 8 * 3600, "mediaMetadata": {"title": "Above"}},
            "below": {"timeListening": 6 * 3600, "mediaMetadata": {"title": "Below"}},
            "invalid": {"timeListening": 100 * 3600},
        }
    }

    result = compute_extra_listening("2024", progress, stats)

    assert result.qualifying_books == 3
    assert [(book.title, book.listening_ratio) for book in result.books] == [
        ("Above", 160.0),
        ("Threshold", 125.0),
    ]


# ---------------------------------------------------------------------------
# compute_heatmap
# ---------------------------------------------------------------------------


def _session(year: int, month: int, day: int, seconds: int) -> dict:
    return {
        "updatedAt": _ts(year, month, day),
        "timeListening": seconds,
    }


def test_compute_heatmap_basic():
    sessions = [
        _session(2024, 3, 5, 3600),  # 60 min
        _session(2024, 3, 5, 1800),  # 30 min — same day, should sum to 90
        _session(2024, 6, 1, 7200),  # 120 min
    ]
    result = compute_heatmap("2024", sessions)
    assert result.year == "2024"
    assert len(result.data) == 2
    by_date = {p.date: p.minutes for p in result.data}
    assert by_date["2024-03-05"] == 90
    assert by_date["2024-06-01"] == 120


def test_compute_heatmap_filters_other_years():
    sessions = [
        _session(2023, 12, 31, 3600),
        _session(2024, 1, 1, 1800),
        _session(2025, 1, 1, 600),
    ]
    result = compute_heatmap("2024", sessions)
    assert len(result.data) == 1
    assert result.data[0].date == "2024-01-01"
    assert result.data[0].minutes == 30


def test_compute_heatmap_uses_configured_timezone_before_filtering_year():
    # Midnight UTC is still Dec 31 in Los Angeles.
    sessions = [{"updatedAt": _ts(2024, 1, 1), "timeListening": 1800}]

    result = compute_heatmap("2023", sessions, "America/Los_Angeles")

    assert [(point.date, point.minutes) for point in result.data] == [("2023-12-31", 30)]


def test_compute_heatmap_empty():
    result = compute_heatmap("2024", [])
    assert result.year == "2024"
    assert result.data == []


def test_compute_statistics_detail_groups_listening_by_day_and_book():
    sessions = [
        {"updatedAt": _ts(2024, 3, 5), "timeListening": 3600, "libraryItemId": "book-2"},
        {"updatedAt": _ts(2024, 3, 5), "timeListening": 1800, "libraryItemId": "book-2"},
        {"updatedAt": _ts(2023, 10, 10), "timeListening": 600, "libraryItemId": "book-3"},
    ]
    detail = compute_statistics_detail("2024", _PROGRESS_MAP, _LISTENING_STATS, sessions)
    assert [book.id for book in detail.books] == ["book-2", "book-1"]
    assert detail.books[0].authors == ["Author B"]
    assert detail.books[0].narrator == "Narrator Y"
    assert detail.books[0].narrators == ["Narrator Y"]
    assert detail.books[0].genres == ["Sci-Fi", "Adventure"]
    assert len(detail.listening_days) == 1
    assert detail.listening_days[0].minutes == 90
    assert detail.listening_days[0].books[0].title == "Book Two"


def test_compute_statistics_detail_uses_configured_timezone_for_books_and_sessions():
    progress = {
        "boundary-book": {
            "isFinished": True,
            "finishedAt": _ts(2024, 1, 1),
            "duration": 3600,
        }
    }
    stats = {
        "items": {"boundary-book": {"mediaMetadata": {"title": "Boundary Book", "authors": []}}}
    }
    sessions = [
        {
            "updatedAt": _ts(2024, 1, 1),
            "timeListening": 1800,
            "libraryItemId": "boundary-book",
        }
    ]

    detail = compute_statistics_detail("2023", progress, stats, sessions, "America/Los_Angeles")

    assert [book.id for book in detail.books] == ["boundary-book"]
    assert [(day.date, day.minutes) for day in detail.listening_days] == [("2023-12-31", 30)]


def test_compute_heatmap_skips_missing_ts():
    sessions = [{"timeListening": 3600}]  # no updatedAt/startedAt
    result = compute_heatmap("2024", sessions)
    assert result.data == []


# ---------------------------------------------------------------------------
# compute_listening_habits
# ---------------------------------------------------------------------------


def test_listening_habits_calculates_summary_distribution_and_cadence():
    sessions = [
        _session(2024, 3, 4, 10 * 60),  # Monday
        _session(2024, 3, 4, 20 * 60),
        _session(2024, 3, 5, 45 * 60),  # Tuesday
        _session(2024, 3, 5, 60 * 60),
        _session(2024, 3, 5, 0),  # excluded
        {"updatedAt": _ts(2024, 3, 5), "timeListening": -60},  # excluded
    ]
    result = compute_listening_habits("2024", sessions, "UTC")

    assert result.session_summary.qualifying_sessions == 4
    assert result.session_summary.average_minutes == 33.8
    assert result.session_summary.median_minutes == 32.5
    assert result.session_summary.longest_session_minutes == 60.0
    assert result.session_summary.sessions_per_active_day == 2.0
    assert result.cadence.active_days == 2
    assert result.cadence.total_days == 366
    assert result.cadence.active_day_percentage == pytest.approx(0.5)
    assert [(item.label, item.sessions) for item in result.duration_distribution] == [
        ("Under 15 min", 1),
        ("15–29 min", 1),
        ("30–59 min", 1),
        ("60 min or more", 1),
    ]


def test_listening_habits_uses_configured_timezone_before_filtering_year():
    # This timestamp is 2024 in UTC, but still Dec 31, 2023 in Los Angeles.
    sessions = [{"updatedAt": _ts(2024, 1, 1), "timeListening": 3600}]

    result = compute_listening_habits("2023", sessions, "America/Los_Angeles")

    assert result.timezone == "America/Los_Angeles"
    assert result.session_summary.qualifying_sessions == 1
    assert result.weekday_hour[0].weekday == 6
    assert result.weekday_hour[0].hour == 16


def test_listening_habits_empty_and_all_time_span():
    empty = compute_listening_habits("2024", [{"updatedAt": _ts(2024, 1, 1), "timeListening": 0}])
    assert empty.session_summary.qualifying_sessions == 0
    assert empty.cadence.active_days == 0
    assert empty.cadence.total_days == 366
    assert empty.cadence.active_day_percentage == 0.0

    all_time = compute_listening_habits(
        "all",
        [_session(2024, 1, 1, 60), _session(2024, 1, 3, 60)],
    )
    assert all_time.cadence.total_days == 3

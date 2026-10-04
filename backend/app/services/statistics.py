from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from ..schemas.statistics import (
    AffinityPerson,
    AuthorCount,
    AuthorNarratorAffinity,
    BacklogHealth,
    BookLengthBucket,
    BookLengthPreferences,
    BookSummary,
    CompletionVelocity,
    CompletionVelocityMonth,
    DurationCompletionCorrelation,
    DurationCompletionPoint,
    ExtraListening,
    ExtraListeningBook,
    GenreCompletionCorrelation,
    GenreCount,
    GoalForecast,
    HeatmapData,
    HeatmapPoint,
    ListeningBook,
    ListeningCadence,
    ListeningDay,
    ListeningHabitCell,
    ListeningHabits,
    MonthlyComparison,
    MonthlyComparisonPoint,
    MonthlyPoint,
    OverallStats,
    ReadDuration,
    RecapStats,
    SeriesProgress,
    SessionDurationBin,
    SessionHabitSummary,
    StatisticBook,
    StatisticsDetail,
    StreakInfo,
    YearlyPoint,
    YearlyStats,
)


def _local_timezone(timezone: str) -> ZoneInfo:
    """Return the configured local timezone, falling back safely to UTC."""
    try:
        return ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _session_datetime(session: dict[str, Any], timezone: ZoneInfo) -> datetime | None:
    timestamp = session.get("updatedAt") or session.get("startedAt")
    if not timestamp:
        return None
    try:
        return datetime.fromtimestamp(timestamp / 1000, tz=timezone)
    except (ValueError, TypeError, OSError):
        return None


def _get_finished_books(
    progress_map: dict[str, Any],
    stats_items: dict[str, Any],
) -> list[dict[str, Any]]:
    finished: list[dict[str, Any]] = []
    for lib_item_id, progress in progress_map.items():
        if not progress.get("isFinished"):
            continue
        stats_item = stats_items.get(lib_item_id, {})
        metadata = stats_item.get("mediaMetadata", {})
        authors = [
            author["name"]
            for author in metadata.get("authors", [])
            if isinstance(author, dict) and isinstance(author.get("name"), str) and author["name"]
        ]
        narrators = [
            narrator
            for narrator in metadata.get("narrators", [])
            if isinstance(narrator, str) and narrator
        ]
        author_str = ", ".join(authors) if authors else "Unknown Author"
        finished.append(
            {
                "id": lib_item_id,
                "title": metadata.get("title", "Unknown Title"),
                "author": author_str,
                "authors": authors,
                "narrator": ", ".join(narrators),
                "narrators": narrators,
                "series": metadata.get("series", []),
                "genres": metadata.get("genres", []),
                "finished_at": progress.get("finishedAt"),
                "started_at": progress.get("startedAt"),
                "duration": progress.get("duration", 0) or 0,
                "time_listening": stats_item.get("timeListening", 0) or 0,
            }
        )
    finished.sort(key=lambda x: x.get("finished_at") or 0)
    return finished


def _group_by_year(books: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for b in books:
        ts = b.get("finished_at")
        if ts:
            grouped[str(datetime.fromtimestamp(ts / 1000).year)].append(b)
    return dict(sorted(grouped.items()))


def _group_by_month(books: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for b in books:
        ts = b.get("finished_at")
        if ts:
            grouped[datetime.fromtimestamp(ts / 1000).strftime("%Y-%m")].append(b)
    return dict(sorted(grouped.items()))


def _compute_streaks(sessions: list[dict]) -> StreakInfo:
    if not sessions:
        return StreakInfo(current=0, longest=0, total_days=0)

    active_dates: set[date] = set()
    for s in sessions:
        ts = s.get("updatedAt") or s.get("startedAt")
        if ts:
            try:
                active_dates.add(datetime.fromtimestamp(ts / 1000).date())
            except (ValueError, TypeError, OSError):
                pass

    if not active_dates:
        return StreakInfo(current=0, longest=0, total_days=0)

    sorted_dates = sorted(active_dates)
    total_days = len(sorted_dates)

    longest = 1
    run = 1
    for i in range(1, len(sorted_dates)):
        if sorted_dates[i] - sorted_dates[i - 1] == timedelta(days=1):
            run += 1
            longest = max(longest, run)
        else:
            run = 1

    today = date.today()
    if sorted_dates[-1] >= today - timedelta(days=1):
        current = 1
        for i in range(len(sorted_dates) - 1, 0, -1):
            if sorted_dates[i] - sorted_dates[i - 1] == timedelta(days=1):
                current += 1
            else:
                break
    else:
        current = 0

    return StreakInfo(current=current, longest=longest, total_days=total_days)


def compute_overall_stats(
    progress_map: dict[str, Any],
    listening_stats: dict[str, Any],
    sessions: list[dict[str, Any]],
) -> OverallStats:
    stats_items = listening_stats.get("items", {}) if listening_stats else {}
    finished = _get_finished_books(progress_map, stats_items)
    by_month = _group_by_month(finished)
    by_year = _group_by_year(finished)

    total_time_hours = (listening_stats.get("totalTime", 0) or 0) / 3600 if listening_stats else 0.0
    books_completed = len(finished)
    avg_per_month = books_completed / len(by_month) if by_month else 0.0

    unique_authors: set[str] = set()
    for item in stats_items.values():
        for author in item.get("mediaMetadata", {}).get("authors", []):
            name = author.get("name")
            if name:
                unique_authors.add(name)

    return OverallStats(
        books_completed=books_completed,
        hours_listened=round(total_time_hours, 1),
        avg_books_per_month=round(avg_per_month, 1),
        unique_authors=len(unique_authors),
        streak=_compute_streaks(sessions),
        by_year=[YearlyPoint(year=yr, books=len(bks)) for yr, bks in by_year.items()],
    )


def compute_yearly_stats(
    year: str,
    progress_map: dict[str, Any],
    listening_stats: dict[str, Any],
) -> YearlyStats:
    stats_items = listening_stats.get("items", {}) if listening_stats else {}
    finished = _get_finished_books(progress_map, stats_items)
    by_year = _group_by_year(finished)
    by_month = _group_by_month(finished)

    if year == "all":
        year_books = finished
        monthly_chart = [
            MonthlyPoint(month=yr, books=len(bks)) for yr, bks in sorted(by_year.items())
        ]
    else:
        year_books = by_year.get(year, [])
        monthly_chart = [
            MonthlyPoint(month=f"{year}-{m:02d}", books=len(by_month.get(f"{year}-{m:02d}", [])))
            for m in range(1, 13)
        ]

    author_counts: Counter[str] = Counter()
    for b in year_books:
        for name in (n.strip() for n in b["author"].split(",") if n.strip()):
            author_counts[name] += 1
    top_authors = [AuthorCount(name=a, books=c) for a, c in author_counts.most_common(5)]

    narrator_counts: Counter[str] = Counter()
    for b in year_books:
        narrator_str = b.get("narrator", "")
        if narrator_str:
            for name in (n.strip() for n in narrator_str.split(",") if n.strip()):
                narrator_counts[name] += 1
    top_narrators = [AuthorCount(name=n, books=c) for n, c in narrator_counts.most_common(5)]

    genre_counts: Counter[str] = Counter()
    for b in year_books:
        for g in b.get("genres", []):
            if g:
                genre_counts[g] += 1
    genre_breakdown = [GenreCount(name=g, books=c) for g, c in genre_counts.most_common(15)]

    return YearlyStats(
        year=year,
        books_in_year=len(year_books),
        monthly_chart=monthly_chart,
        top_authors=top_authors,
        top_narrators=top_narrators,
        genre_breakdown=genre_breakdown,
    )


def compute_recap(
    year: str,
    progress_map: dict[str, Any],
    listening_stats: dict[str, Any],
) -> RecapStats:
    stats_items = listening_stats.get("items", {}) if listening_stats else {}
    finished = _get_finished_books(progress_map, stats_items)
    by_year = _group_by_year(finished)
    by_month = _group_by_month(finished)

    year_books = by_year.get(year, [])

    year_hours = sum(b.get("time_listening", 0) for b in year_books) / 3600
    year_duration_hours = sum(b.get("duration", 0) for b in year_books) / 3600
    active_months = len([m for m in by_month if m.startswith(year)])

    author_counts: Counter[str] = Counter(b["author"] for b in year_books)
    top_authors = [AuthorCount(name=a, books=c) for a, c in author_counts.most_common(5)]

    books_with_dur = [b for b in year_books if b.get("duration", 0) > 0]
    longest_book: BookSummary | None = None
    shortest_book: BookSummary | None = None
    if books_with_dur:
        lb = max(books_with_dur, key=lambda b: b["duration"])
        longest_book = BookSummary(
            id=lb["id"], title=lb["title"], author=lb["author"], duration=lb["duration"]
        )
        sb = min(books_with_dur, key=lambda b: b["duration"])
        shortest_book = BookSummary(
            id=sb["id"], title=sb["title"], author=sb["author"], duration=sb["duration"]
        )

    def _read_days(b: dict) -> float:
        return (b["finished_at"] - b["started_at"]) / (1000 * 86400)

    books_with_times = [
        b
        for b in year_books
        if b.get("started_at") and b.get("finished_at") and b["finished_at"] > b["started_at"]
    ]
    fastest_read: ReadDuration | None = None
    slowest_read: ReadDuration | None = None
    if books_with_times:
        fb = min(books_with_times, key=_read_days)
        fastest_read = ReadDuration(id=fb["id"], title=fb["title"], days=round(_read_days(fb), 1))
        slb = max(books_with_times, key=_read_days)
        slowest_read = ReadDuration(
            id=slb["id"], title=slb["title"], days=round(_read_days(slb), 1)
        )

    monthly_pace = [
        MonthlyPoint(month=f"{year}-{m:02d}", books=len(by_month.get(f"{year}-{m:02d}", [])))
        for m in range(1, 13)
    ]

    series_counts: Counter[str] = Counter()
    for b in year_books:
        for s in b.get("series", []):
            name = s.get("name") if isinstance(s, dict) else None
            if name:
                series_counts[name] += 1
    top_series = [GenreCount(name=n, books=c) for n, c in series_counts.most_common(5)]

    return RecapStats(
        year=year,
        books_finished=len(year_books),
        hours_listened=round(year_hours, 1),
        hours_of_content=round(year_duration_hours, 1),
        active_months=active_months,
        top_authors=top_authors,
        longest_book=longest_book,
        shortest_book=shortest_book,
        fastest_read=fastest_read,
        slowest_read=slowest_read,
        monthly_pace=monthly_pace,
        top_series=top_series,
    )


def compute_heatmap(
    year: str,
    sessions: list[dict[str, Any]],
    timezone: str = "UTC",
) -> HeatmapData:
    """Aggregate sessions by their configured local calendar date."""
    local_timezone = _local_timezone(timezone)
    daily: dict[str, int] = defaultdict(int)
    for session in sessions:
        dt = _session_datetime(session, local_timezone)
        if dt is None:
            continue
        if str(dt.year) != year:
            continue
        day = dt.strftime("%Y-%m-%d")
        seconds = session.get("timeListening", 0) or 0
        daily[day] += int(seconds / 60)

    data = [HeatmapPoint(date=d, minutes=m) for d, m in sorted(daily.items())]
    return HeatmapData(year=year, timezone=local_timezone.key, data=data)


def compute_listening_habits(
    year: str,
    sessions: list[dict[str, Any]],
    timezone: str = "UTC",
) -> ListeningHabits:
    """Calculate local-time listening habits from positive-duration ABS sessions."""
    local_timezone = _local_timezone(timezone)
    cells: dict[tuple[int, int], dict[str, Any]] = defaultdict(
        lambda: {"seconds": 0, "sessions": 0}
    )
    active_dates: set[date] = set()
    durations: list[float] = []

    for session in sessions:
        dt = _session_datetime(session, local_timezone)
        seconds = session.get("timeListening", 0) or 0
        if dt is None or not isinstance(seconds, (int, float)) or seconds <= 0:
            continue
        if year != "all" and str(dt.year) != year:
            continue

        cells[(dt.weekday(), dt.hour)]["seconds"] += seconds
        cells[(dt.weekday(), dt.hour)]["sessions"] += 1
        active_dates.add(dt.date())
        durations.append(float(seconds))

    weekday_hour = [
        ListeningHabitCell(
            weekday=weekday,
            hour=hour,
            minutes=round(value["seconds"] / 60),
            sessions=value["sessions"],
        )
        for (weekday, hour), value in sorted(cells.items())
    ]
    peak = max(weekday_hour, key=lambda cell: (cell.minutes, cell.sessions), default=None)

    bins = [
        ("Under 15 min", 0, 15 * 60),
        ("15–29 min", 15 * 60, 30 * 60),
        ("30–59 min", 30 * 60, 60 * 60),
        ("60 min or more", 60 * 60, None),
    ]
    duration_distribution = [
        SessionDurationBin(
            label=label,
            sessions=sum(
                1
                for duration in durations
                if duration >= lower and (upper is None or duration < upper)
            ),
        )
        for label, lower, upper in bins
    ]

    if durations:
        sorted_durations = sorted(durations)
        midpoint = len(sorted_durations) // 2
        median_seconds = (
            sorted_durations[midpoint]
            if len(sorted_durations) % 2
            else (sorted_durations[midpoint - 1] + sorted_durations[midpoint]) / 2
        )
        summary = SessionHabitSummary(
            qualifying_sessions=len(durations),
            average_minutes=round(sum(durations) / len(durations) / 60, 1),
            median_minutes=round(median_seconds / 60, 1),
            sessions_per_active_day=round(len(durations) / len(active_dates), 1),
            longest_session_minutes=round(max(durations) / 60, 1),
        )
    else:
        summary = SessionHabitSummary(qualifying_sessions=0)

    if year == "all" and active_dates:
        total_days = (max(active_dates) - min(active_dates)).days + 1
    elif year != "all":
        try:
            selected_year = int(year)
            total_days = 366 if date(selected_year, 12, 31).timetuple().tm_yday == 366 else 365
        except ValueError:
            total_days = 0
    else:
        total_days = 0
    cadence = ListeningCadence(
        active_days=len(active_dates),
        total_days=total_days,
        active_day_percentage=(
            round(len(active_dates) / total_days * 100, 1) if total_days else None
        ),
    )
    return ListeningHabits(
        year=year,
        timezone=local_timezone.key,
        weekday_hour=weekday_hour,
        peak=peak,
        session_summary=summary,
        duration_distribution=duration_distribution,
        cadence=cadence,
    )


def compute_completion_velocity(
    year: str,
    progress_map: dict[str, Any],
    listening_stats: dict[str, Any],
    timezone: str = "UTC",
) -> CompletionVelocity:
    """Return representative completion pace for finished books in a period."""
    local_timezone = _local_timezone(timezone)
    stats_items = listening_stats.get("items", {}) if listening_stats else {}
    qualifying: list[tuple[datetime, float]] = []

    for book in _get_finished_books(progress_map, stats_items):
        started_at = book.get("started_at")
        finished_at = book.get("finished_at")
        if (
            not isinstance(started_at, (int, float))
            or isinstance(started_at, bool)
            or not isinstance(finished_at, (int, float))
            or isinstance(finished_at, bool)
            or finished_at <= started_at
        ):
            continue
        try:
            finished = datetime.fromtimestamp(finished_at / 1000, tz=local_timezone)
        except (ValueError, OSError, OverflowError):
            continue
        if year != "all" and str(finished.year) != year:
            continue
        qualifying.append((finished, (finished_at - started_at) / 86_400_000))

    def median(values: list[float]) -> float:
        ordered = sorted(values)
        midpoint = len(ordered) // 2
        return (
            ordered[midpoint]
            if len(ordered) % 2
            else (ordered[midpoint - 1] + ordered[midpoint]) / 2
        )

    monthly: dict[str, list[float]] = defaultdict(list)
    for finished, days in qualifying:
        monthly[finished.strftime("%Y-%m")].append(days)
    monthly_trend = [
        CompletionVelocityMonth(
            month=month,
            qualifying_books=len(days),
            median_days=round(median(days), 1) if len(days) >= 3 else None,
        )
        for month, days in sorted(monthly.items())
    ]
    return CompletionVelocity(
        year=year,
        qualifying_books=len(qualifying),
        median_days=round(median([days for _, days in qualifying]), 1) if qualifying else None,
        monthly_trend=monthly_trend,
    )


def compute_monthly_comparison(
    year: str,
    progress_map: dict[str, Any],
    listening_stats: dict[str, Any],
    sessions: list[dict[str, Any]],
    timezone: str = "UTC",
) -> MonthlyComparison:
    """Compare completed books with session-derived listening hours by local month."""
    local_timezone = _local_timezone(timezone)
    stats_items = listening_stats.get("items", {}) if listening_stats else {}
    completed: Counter[str] = Counter()
    listened_seconds: dict[str, float] = defaultdict(float)

    for book in _get_finished_books(progress_map, stats_items):
        finished_at = book.get("finished_at")
        if not isinstance(finished_at, (int, float)) or isinstance(finished_at, bool):
            continue
        try:
            finished = datetime.fromtimestamp(finished_at / 1000, tz=local_timezone)
        except (ValueError, OSError, OverflowError):
            continue
        if year == "all" or str(finished.year) == year:
            completed[finished.strftime("%Y-%m")] += 1

    for session in sessions:
        timestamp = _session_datetime(session, local_timezone)
        seconds = session.get("timeListening", 0) or 0
        if (
            timestamp is None
            or not isinstance(seconds, (int, float))
            or isinstance(seconds, bool)
            or seconds <= 0
            or (year != "all" and str(timestamp.year) != year)
        ):
            continue
        listened_seconds[timestamp.strftime("%Y-%m")] += seconds

    months = sorted(set(completed) | set(listened_seconds))
    if year != "all":
        try:
            months = [f"{int(year):04d}-{month:02d}" for month in range(1, 13)]
        except ValueError:
            months = []
    return MonthlyComparison(
        year=year,
        timezone=local_timezone.key,
        monthly=[
            MonthlyComparisonPoint(
                month=month,
                books_completed=completed[month],
                listening_hours=round(listened_seconds[month] / 3600, 1),
            )
            for month in months
        ],
    )


def compute_book_length_preferences(
    year: str,
    progress_map: dict[str, Any],
    listening_stats: dict[str, Any],
    timezone: str = "UTC",
) -> BookLengthPreferences:
    """Summarize completed-book durations and completion pace by length."""
    local_timezone = _local_timezone(timezone)
    stats_items = listening_stats.get("items", {}) if listening_stats else {}
    buckets = [
        ("Under 5 hours", 0, 5 * 3600),
        ("5–9:59 hours", 5 * 3600, 10 * 3600),
        ("10–19:59 hours", 10 * 3600, 20 * 3600),
        ("20–29:59 hours", 20 * 3600, 30 * 3600),
        ("30 hours or more", 30 * 3600, None),
    ]
    durations_by_bucket: dict[str, list[float]] = defaultdict(list)
    pace_by_bucket: dict[str, list[float]] = defaultdict(list)
    all_durations: list[float] = []

    for book in _get_finished_books(progress_map, stats_items):
        duration = book.get("duration")
        finished_at = book.get("finished_at")
        if (
            not isinstance(duration, (int, float))
            or isinstance(duration, bool)
            or duration <= 0
            or not isinstance(finished_at, (int, float))
            or isinstance(finished_at, bool)
        ):
            continue
        try:
            finished = datetime.fromtimestamp(finished_at / 1000, tz=local_timezone)
        except (ValueError, OSError, OverflowError):
            continue
        if year != "all" and str(finished.year) != year:
            continue
        bucket = next(
            (
                label
                for label, lower, upper in buckets
                if duration >= lower and (upper is None or duration < upper)
            ),
            None,
        )
        if bucket is None:
            continue
        all_durations.append(float(duration))
        durations_by_bucket[bucket].append(float(duration))
        started_at = book.get("started_at")
        if (
            isinstance(started_at, (int, float))
            and not isinstance(started_at, bool)
            and finished_at > started_at
        ):
            pace_by_bucket[bucket].append((finished_at - started_at) / 86_400_000)

    def median(values: list[float]) -> float:
        ordered = sorted(values)
        midpoint = len(ordered) // 2
        return (
            ordered[midpoint]
            if len(ordered) % 2
            else (ordered[midpoint - 1] + ordered[midpoint]) / 2
        )

    return BookLengthPreferences(
        year=year,
        timezone=local_timezone.key,
        qualifying_books=len(all_durations),
        median_duration_hours=(round(median(all_durations) / 3600, 1) if all_durations else None),
        distribution=[
            BookLengthBucket(
                label=label,
                completed_books=len(durations_by_bucket[label]),
                pace_qualifying_books=len(pace_by_bucket[label]),
                median_days_to_finish=(
                    round(median(pace_by_bucket[label]), 1) if pace_by_bucket[label] else None
                ),
            )
            for label, _, _ in buckets
        ],
    )


def compute_goal_forecast(
    year: int,
    target_books: int | None,
    progress_map: dict[str, Any],
    listening_stats: dict[str, Any],
    timezone: str = "UTC",
    as_of: date | None = None,
) -> GoalForecast:
    """Estimate a current-year goal from the preceding 30 calendar days."""
    if target_books is None:
        return GoalForecast(year=year, has_goal=False)

    local_timezone = _local_timezone(timezone)
    today = as_of or datetime.now(local_timezone).date()
    if today.year != year:
        return GoalForecast(
            year=year,
            has_goal=True,
            target_books=target_books,
            ineligibility_reason="Forecasts are available only for the current calendar year.",
        )

    days_elapsed = (today - date(year, 1, 1)).days + 1
    if days_elapsed < 14:
        return GoalForecast(
            year=year,
            has_goal=True,
            target_books=target_books,
            ineligibility_reason="A forecast needs at least 14 days in the calendar year.",
        )

    stats_items = listening_stats.get("items", {}) if listening_stats else {}
    completed_dates: list[date] = []
    for book in _get_finished_books(progress_map, stats_items):
        finished_at = book.get("finished_at")
        if not isinstance(finished_at, (int, float)) or isinstance(finished_at, bool):
            continue
        try:
            finished = datetime.fromtimestamp(finished_at / 1000, tz=local_timezone).date()
        except (ValueError, OSError, OverflowError):
            continue
        if finished.year == year and finished <= today:
            completed_dates.append(finished)

    trailing_start = today - timedelta(days=29)
    trailing_completions = sum(day >= trailing_start for day in completed_dates)
    if trailing_completions == 0:
        return GoalForecast(
            year=year,
            has_goal=True,
            target_books=target_books,
            books_completed=len(completed_dates),
            ineligibility_reason="No completed books were recorded in the last 30 days.",
        )

    days_remaining = (date(year, 12, 31) - today).days
    projected_books = len(completed_dates) + trailing_completions / 30 * days_remaining
    required_books_per_week = (
        max(target_books - len(completed_dates), 0) / (days_remaining / 7) if days_remaining else 0
    )
    return GoalForecast(
        year=year,
        has_goal=True,
        eligible=True,
        target_books=target_books,
        books_completed=len(completed_dates),
        trailing_30_day_completions=trailing_completions,
        projected_books=round(projected_books, 1),
        required_books_per_week=round(required_books_per_week, 1),
    )


def compute_backlog_health(
    library_items: list[dict[str, Any]], progress_map: dict[str, Any]
) -> BacklogHealth:
    """Summarize current library backlog without estimating missing durations or progress."""
    unstarted_books = 0
    in_progress_books = 0
    completed_books = 0
    unstarted_remaining_seconds = 0.0
    in_progress_remaining_seconds = 0.0
    unstarted_duration_books = 0
    in_progress_duration_books = 0

    for item in library_items:
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            continue
        progress = progress_map.get(item_id)
        raw_media = item.get("media")
        media: dict[str, Any] = raw_media if isinstance(raw_media, dict) else {}
        duration = media.get("duration", 0)
        valid_duration = (
            isinstance(duration, (int, float)) and not isinstance(duration, bool) and duration > 0
        )
        if isinstance(progress, dict) and progress.get("isFinished"):
            completed_books += 1
            continue

        progress_value = progress.get("progress") if isinstance(progress, dict) else None
        valid_progress = (
            isinstance(progress_value, (int, float))
            and not isinstance(progress_value, bool)
            and 0 < progress_value < 1
        )
        if valid_progress:
            in_progress_books += 1
            if (
                valid_duration
                and isinstance(duration, (int, float))
                and isinstance(progress_value, (int, float))
            ):
                in_progress_remaining_seconds += duration * (1 - progress_value)
                in_progress_duration_books += 1
        elif progress is None or progress_value == 0:
            unstarted_books += 1
            if valid_duration and isinstance(duration, (int, float)):
                unstarted_remaining_seconds += duration
                unstarted_duration_books += 1

    return BacklogHealth(
        unstarted_books=unstarted_books,
        in_progress_books=in_progress_books,
        completed_books=completed_books,
        partially_started_books=in_progress_books,
        unstarted_remaining_hours=round(unstarted_remaining_seconds / 3600, 1),
        in_progress_remaining_hours=round(in_progress_remaining_seconds / 3600, 1),
        total_remaining_hours=round(
            (unstarted_remaining_seconds + in_progress_remaining_seconds) / 3600, 1
        ),
        unstarted_duration_books=unstarted_duration_books,
        in_progress_duration_books=in_progress_duration_books,
    )


def compute_series_progress(
    all_library_series: list[list[dict[str, Any]]], progress_map: dict[str, Any]
) -> list[SeriesProgress]:
    """List complete series records that still have books left to finish."""
    results: list[SeriesProgress] = []
    for library_series in all_library_series:
        for series in library_series:
            name = series.get("name")
            books = series.get("books")
            if (
                not isinstance(name, str)
                or not name.strip()
                or not isinstance(books, list)
                or not books
            ):
                continue
            if any(
                not isinstance(book, dict) or not isinstance(book.get("id"), str) or not book["id"]
                for book in books
            ):
                continue

            completed = 0
            remaining = 0
            remaining_seconds = 0.0
            remaining_duration_books = 0
            for book in books:
                book_id = book["id"]
                progress = progress_map.get(book_id)
                if isinstance(progress, dict) and progress.get("isFinished"):
                    completed += 1
                    continue
                remaining += 1
                media = book.get("media") if isinstance(book.get("media"), dict) else {}
                duration = media.get("duration", 0)
                if (
                    not isinstance(duration, (int, float))
                    or isinstance(duration, bool)
                    or duration <= 0
                ):
                    continue
                progress_value = progress.get("progress") if isinstance(progress, dict) else None
                if progress is None:
                    remaining_seconds += duration
                    remaining_duration_books += 1
                elif (
                    isinstance(progress_value, (int, float))
                    and not isinstance(progress_value, bool)
                    and 0 <= progress_value < 1
                ):
                    remaining_seconds += duration * (1 - progress_value)
                    remaining_duration_books += 1

            if remaining:
                results.append(
                    SeriesProgress(
                        name=name.strip(),
                        completed_books=completed,
                        remaining_books=remaining,
                        remaining_hours=round(remaining_seconds / 3600, 1),
                        remaining_duration_books=remaining_duration_books,
                    )
                )
    return sorted(
        results,
        key=lambda series: (
            series.remaining_books,
            series.remaining_hours if series.remaining_duration_books else float("inf"),
            series.name.lower(),
        ),
    )


def _credit_names(metadata: dict[str, Any], plural_key: str, singular_key: str) -> list[str]:
    """Return distinct credited names from ABS's list and display-name variants."""
    raw = metadata.get(plural_key)
    names: list[str] = []
    if isinstance(raw, list):
        for value in raw:
            if isinstance(value, dict) and isinstance(value.get("name"), str):
                names.append(value["name"])
            elif isinstance(value, str):
                names.append(value)
    elif isinstance(raw, str):
        names.extend(raw.split(","))
    if not names:
        display_name = metadata.get(singular_key)
        if isinstance(display_name, str):
            names.extend(display_name.split(","))
    return list(dict.fromkeys(name.strip() for name in names if name.strip()))


def compute_author_narrator_affinity(
    library_items: list[dict[str, Any]],
    progress_map: dict[str, Any],
    listening_stats: dict[str, Any],
) -> AuthorNarratorAffinity:
    """Rank people credited on at least three library books by listening affinity."""
    stats_items = listening_stats.get("items", {}) if listening_stats else {}
    people: dict[str, dict[str, dict[str, float]]] = {
        "authors": defaultdict(lambda: {"available": 0, "completed": 0, "seconds": 0}),
        "narrators": defaultdict(lambda: {"available": 0, "completed": 0, "seconds": 0}),
    }
    keys = {
        "authors": ("authors", "authorName"),
        "narrators": ("narrators", "narratorName"),
    }

    for item in library_items:
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            continue
        raw_media = item.get("media")
        media: dict[str, Any] = raw_media if isinstance(raw_media, dict) else {}
        raw_metadata = media.get("metadata")
        metadata: dict[str, Any] = raw_metadata if isinstance(raw_metadata, dict) else {}
        progress = progress_map.get(item_id)
        completed = isinstance(progress, dict) and progress.get("isFinished") is True
        stats_item = stats_items.get(item_id, {})
        seconds = stats_item.get("timeListening", 0) if isinstance(stats_item, dict) else 0
        valid_seconds = (
            float(seconds)
            if isinstance(seconds, (int, float)) and not isinstance(seconds, bool) and seconds >= 0
            else 0.0
        )
        for group, (plural_key, singular_key) in keys.items():
            for name in _credit_names(metadata, plural_key, singular_key):
                person = people[group][name]
                person["available"] += 1
                person["completed"] += int(completed)
                person["seconds"] += valid_seconds

    def ranking(group: str) -> list[AffinityPerson]:
        result = [
            AffinityPerson(
                name=name,
                available_books=int(values["available"]),
                completed_books=int(values["completed"]),
                completion_rate=round(values["completed"] / values["available"] * 100, 1),
                listened_hours=round(values["seconds"] / 3600, 1),
            )
            for name, values in people[group].items()
            if values["available"] >= 3
        ]
        return sorted(
            result,
            key=lambda person: (
                -person.completion_rate,
                -person.completed_books,
                -person.listened_hours,
                person.name.lower(),
            ),
        )

    return AuthorNarratorAffinity(authors=ranking("authors"), narrators=ranking("narrators"))


def compute_genre_completion_correlation(
    library_items: list[dict[str, Any]], progress_map: dict[str, Any]
) -> list[GenreCompletionCorrelation]:
    """Describe completion outcomes by genre without making causal claims."""
    genres: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"known": 0, "started": 0, "completed": 0, "pace": []}
    )
    for item in library_items:
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            continue
        raw_media = item.get("media")
        media: dict[str, Any] = raw_media if isinstance(raw_media, dict) else {}
        raw_metadata = media.get("metadata")
        metadata: dict[str, Any] = raw_metadata if isinstance(raw_metadata, dict) else {}
        item_genres = metadata.get("genres")
        if not isinstance(item_genres, list):
            continue
        progress = progress_map.get(item_id)
        if not isinstance(progress, dict):
            continue
        is_finished = progress.get("isFinished") is True
        progress_value = progress.get("progress")
        is_started = (
            is_finished
            or (
                isinstance(progress_value, (int, float))
                and not isinstance(progress_value, bool)
                and progress_value > 0
            )
            or isinstance(progress.get("startedAt"), (int, float))
        )
        genre_names = dict.fromkeys(
            name.strip() for name in item_genres if isinstance(name, str) and name.strip()
        )
        for genre in genre_names:
            entry = genres[genre]
            entry["known"] += 1
            entry["started"] += int(is_started)
            entry["completed"] += int(is_finished)
            started_at = progress.get("startedAt")
            finished_at = progress.get("finishedAt")
            if (
                is_finished
                and isinstance(started_at, (int, float))
                and not isinstance(started_at, bool)
                and isinstance(finished_at, (int, float))
                and not isinstance(finished_at, bool)
                and finished_at > started_at
            ):
                entry["pace"].append((finished_at - started_at) / 86_400_000)

    def median(values: list[float]) -> float:
        ordered = sorted(values)
        midpoint = len(ordered) // 2
        return (
            ordered[midpoint]
            if len(ordered) % 2
            else (ordered[midpoint - 1] + ordered[midpoint]) / 2
        )

    result = [
        GenreCompletionCorrelation(
            name=name,
            known_progress_books=entry["known"],
            started_or_completed_books=entry["started"],
            completed_books=entry["completed"],
            completion_rate=round(entry["completed"] / entry["known"] * 100, 1),
            pace_qualifying_books=len(entry["pace"]),
            median_days_to_finish=round(median(entry["pace"]), 1) if entry["pace"] else None,
        )
        for name, entry in genres.items()
        if entry["started"] >= 3
    ]
    return sorted(result, key=lambda genre: (-genre.completion_rate, genre.name.lower()))


def compute_duration_completion_correlation(
    year: str,
    progress_map: dict[str, Any],
    listening_stats: dict[str, Any],
    timezone: str = "UTC",
) -> DurationCompletionCorrelation:
    """Compare completed-book duration with elapsed days using Pearson correlation."""
    local_timezone = _local_timezone(timezone)
    stats_items = listening_stats.get("items", {}) if listening_stats else {}
    points: list[DurationCompletionPoint] = []
    for book in _get_finished_books(progress_map, stats_items):
        duration = book.get("duration")
        started_at = book.get("started_at")
        finished_at = book.get("finished_at")
        if (
            not isinstance(duration, (int, float))
            or isinstance(duration, bool)
            or duration <= 0
            or not isinstance(started_at, (int, float))
            or isinstance(started_at, bool)
            or not isinstance(finished_at, (int, float))
            or isinstance(finished_at, bool)
            or finished_at <= started_at
        ):
            continue
        try:
            finished = datetime.fromtimestamp(finished_at / 1000, tz=local_timezone)
        except (ValueError, OSError, OverflowError):
            continue
        if year != "all" and str(finished.year) != year:
            continue
        points.append(
            DurationCompletionPoint(
                id=book["id"],
                title=book["title"],
                duration_hours=round(duration / 3600, 1),
                days_to_finish=round((finished_at - started_at) / 86_400_000, 1),
            )
        )

    coefficient: float | None = None
    direction: str | None = None
    if len(points) >= 10:
        durations = [point.duration_hours for point in points]
        days = [point.days_to_finish for point in points]
        duration_mean = sum(durations) / len(durations)
        days_mean = sum(days) / len(days)
        duration_variance = sum((value - duration_mean) ** 2 for value in durations)
        days_variance = sum((value - days_mean) ** 2 for value in days)
        if duration_variance > 0 and days_variance > 0:
            covariance = sum(
                (duration - duration_mean) * (day - days_mean)
                for duration, day in zip(durations, days, strict=True)
            )
            coefficient = round(covariance / (duration_variance * days_variance) ** 0.5, 2)
            if coefficient >= 0.2:
                direction = "positive"
            elif coefficient <= -0.2:
                direction = "negative"
            else:
                direction = "no clear"
        else:
            direction = "no clear"

    return DurationCompletionCorrelation(
        year=year,
        qualifying_books=len(points),
        points=points,
        correlation_coefficient=coefficient,
        correlation_method="Pearson correlation coefficient" if coefficient is not None else None,
        direction=direction,
    )


def compute_extra_listening(
    year: str,
    progress_map: dict[str, Any],
    listening_stats: dict[str, Any],
    timezone: str = "UTC",
) -> ExtraListening:
    """Surface completed titles whose ABS listening time reaches 125% of duration."""
    local_timezone = _local_timezone(timezone)
    stats_items = listening_stats.get("items", {}) if listening_stats else {}
    qualifying_books = 0
    books: list[ExtraListeningBook] = []
    for book in _get_finished_books(progress_map, stats_items):
        duration = book.get("duration")
        listened = book.get("time_listening")
        finished_at = book.get("finished_at")
        if (
            not isinstance(duration, (int, float))
            or isinstance(duration, bool)
            or duration <= 0
            or not isinstance(listened, (int, float))
            or isinstance(listened, bool)
            or listened < 0
            or not isinstance(finished_at, (int, float))
            or isinstance(finished_at, bool)
        ):
            continue
        try:
            finished = datetime.fromtimestamp(finished_at / 1000, tz=local_timezone)
        except (ValueError, OSError, OverflowError):
            continue
        if year != "all" and str(finished.year) != year:
            continue
        qualifying_books += 1
        ratio = listened / duration
        if ratio >= 1.25:
            books.append(
                ExtraListeningBook(
                    id=book["id"],
                    title=book["title"],
                    author=book["author"],
                    duration_hours=round(duration / 3600, 1),
                    listened_hours=round(listened / 3600, 1),
                    listening_ratio=round(ratio * 100, 1),
                )
            )
    return ExtraListening(
        year=year,
        qualifying_books=qualifying_books,
        books=sorted(books, key=lambda book: (-book.listening_ratio, book.title.lower())),
    )


def compute_statistics_detail(
    year: str,
    progress_map: dict[str, Any],
    listening_stats: dict[str, Any],
    sessions: list[dict[str, Any]],
    timezone: str = "UTC",
) -> StatisticsDetail:
    """Return the title-level records that support the statistics dashboard."""
    local_timezone = _local_timezone(timezone)
    stats_items = listening_stats.get("items", {}) if listening_stats else {}
    finished = _get_finished_books(progress_map, stats_items)
    if year != "all":
        finished = [
            book
            for book in finished
            if book.get("finished_at")
            and str(datetime.fromtimestamp(book["finished_at"] / 1000, tz=local_timezone).year)
            == year
        ]

    books = [
        StatisticBook(
            id=book["id"],
            title=book["title"],
            author=book["author"],
            authors=book["authors"],
            narrator=book["narrator"],
            narrators=book["narrators"],
            genres=book["genres"],
            finished_at=book.get("finished_at"),
            duration=book.get("duration", 0),
            time_listening=book.get("time_listening", 0),
        )
        for book in reversed(finished)
    ]

    daily: dict[str, dict[str, Any]] = {}
    for session in sessions:
        dt = _session_datetime(session, local_timezone)
        if dt is None:
            continue
        if year != "all" and str(dt.year) != year:
            continue

        day = dt.strftime("%Y-%m-%d")
        item_id = session.get("libraryItemId") or session.get("mediaItemId")
        metadata = stats_items.get(item_id, {}).get("mediaMetadata", {})
        authors = metadata.get("authors", [])
        author = ", ".join(a.get("name", "") for a in authors) if authors else "Unknown Author"
        title = metadata.get("title") or session.get("title") or "Unknown audiobook"
        minutes = int((session.get("timeListening", 0) or 0) / 60)

        entry = daily.setdefault(day, {"minutes": 0, "books": {}})
        entry["minutes"] += minutes
        book = entry["books"].setdefault(
            item_id or title,
            {"id": item_id, "title": title, "author": author, "minutes": 0},
        )
        book["minutes"] += minutes

    listening_days = [
        ListeningDay(
            date=day,
            minutes=entry["minutes"],
            books=[ListeningBook(**book) for book in entry["books"].values()],
        )
        for day, entry in sorted(daily.items(), reverse=True)
    ]
    return StatisticsDetail(
        year=year,
        timezone=local_timezone.key,
        books=books,
        listening_days=listening_days,
    )

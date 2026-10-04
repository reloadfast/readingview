from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from ..schemas.statistics import (
    AuthorCount,
    BookSummary,
    GenreCount,
    HeatmapData,
    HeatmapPoint,
    ListeningBook,
    ListeningCadence,
    ListeningDay,
    ListeningHabitCell,
    ListeningHabits,
    MonthlyPoint,
    OverallStats,
    ReadDuration,
    RecapStats,
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
        authors = metadata.get("authors", [])
        author_str = ", ".join(a.get("name", "") for a in authors) if authors else "Unknown Author"
        finished.append(
            {
                "id": lib_item_id,
                "title": metadata.get("title", "Unknown Title"),
                "author": author_str,
                "narrator": ", ".join(metadata.get("narrators", [])),
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


def compute_heatmap(year: str, sessions: list[dict]) -> HeatmapData:
    daily: dict[str, int] = defaultdict(int)
    for s in sessions:
        ts = s.get("updatedAt") or s.get("startedAt")
        if not ts:
            continue
        try:
            dt = datetime.fromtimestamp(ts / 1000)
        except (ValueError, TypeError, OSError):
            continue
        if str(dt.year) != year:
            continue
        day = dt.strftime("%Y-%m-%d")
        seconds = s.get("timeListening", 0) or 0
        daily[day] += int(seconds / 60)

    data = [HeatmapPoint(date=d, minutes=m) for d, m in sorted(daily.items())]
    return HeatmapData(year=year, data=data)


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


def compute_statistics_detail(
    year: str,
    progress_map: dict[str, Any],
    listening_stats: dict[str, Any],
    sessions: list[dict[str, Any]],
) -> StatisticsDetail:
    """Return the title-level records that support the statistics dashboard."""
    stats_items = listening_stats.get("items", {}) if listening_stats else {}
    finished = _get_finished_books(progress_map, stats_items)
    if year != "all":
        finished = [
            book
            for book in finished
            if book.get("finished_at")
            and str(datetime.fromtimestamp(book["finished_at"] / 1000).year) == year
        ]

    books = [
        StatisticBook(
            id=book["id"],
            title=book["title"],
            author=book["author"],
            finished_at=book.get("finished_at"),
            duration=book.get("duration", 0),
            time_listening=book.get("time_listening", 0),
        )
        for book in reversed(finished)
    ]

    daily: dict[str, dict[str, Any]] = {}
    for session in sessions:
        timestamp = session.get("updatedAt") or session.get("startedAt")
        if not timestamp:
            continue
        try:
            dt = datetime.fromtimestamp(timestamp / 1000)
        except (ValueError, TypeError, OSError):
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
    return StatisticsDetail(year=year, books=books, listening_days=listening_days)

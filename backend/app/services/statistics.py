from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Any

from ..schemas.statistics import (
    AuthorCount,
    BookSummary,
    GenreCount,
    HeatmapData,
    HeatmapPoint,
    MonthlyPoint,
    OverallStats,
    ReadDuration,
    RecapStats,
    StreakInfo,
    YearlyPoint,
    YearlyStats,
)


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

    year_books = by_year.get(year, [])

    monthly_chart = [
        MonthlyPoint(month=f"{year}-{m:02d}", books=len(by_month.get(f"{year}-{m:02d}", [])))
        for m in range(1, 13)
    ]

    author_counts: Counter[str] = Counter(b["author"] for b in year_books)
    top_authors = [AuthorCount(name=a, books=c) for a, c in author_counts.most_common(5)]

    narrator_counts: Counter[str] = Counter()
    for b in year_books:
        if b.get("narrator"):
            narrator_counts[b["narrator"]] += 1
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

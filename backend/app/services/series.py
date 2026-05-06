from ..schemas.series import SeriesBook, SeriesDetail, SeriesSummary


def _parse_sequence(seq: object) -> float:
    if not seq:
        return float("inf")
    try:
        return float(str(seq))
    except (ValueError, TypeError):
        return float("inf")


def _format_duration(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"


def _build_series_map(
    all_library_series: list[list[dict]],
    progress_map: dict,
) -> dict[str, dict]:
    series_map: dict[str, dict] = {}

    for lib_series in all_library_series:
        for series_data in lib_series:
            name = series_data.get("name", "").strip()
            if not name:
                continue

            if name not in series_map:
                series_map[name] = {"name": name, "author": "", "books": []}

            for book in series_data.get("books", []):
                media = book.get("media", {})
                metadata = media.get("metadata", {})
                book_id = book.get("id", "")
                duration = float(media.get("duration") or 0)

                progress_data = progress_map.get(book_id, {})
                is_finished = progress_data.get("isFinished", False)
                raw_progress = progress_data.get("progress", 0.0)
                progress_pct = raw_progress * 100 if not is_finished else 100.0

                author = metadata.get("authorName", "Unknown Author")
                if not series_map[name]["author"]:
                    series_map[name]["author"] = author

                series_map[name]["books"].append(SeriesBook(
                    id=book_id,
                    title=metadata.get("title", "Unknown Title"),
                    author=author,
                    sequence=str(book.get("sequence") or ""),
                    is_finished=is_finished,
                    progress=round(progress_pct, 1),
                    duration=duration,
                    duration_formatted=_format_duration(duration),
                ))

    for entry in series_map.values():
        entry["books"].sort(key=lambda b: _parse_sequence(b.sequence))

    return series_map


def _to_summary(name: str, entry: dict) -> SeriesSummary:
    books: list[SeriesBook] = entry["books"]
    total = len(books)
    finished = sum(1 for b in books if b.is_finished)
    in_progress = sum(1 for b in books if not b.is_finished and b.progress > 0)
    not_started = total - finished - in_progress
    percent = round(finished / total * 100, 1) if total > 0 else 0.0
    return SeriesSummary(
        name=name,
        author=entry["author"],
        total=total,
        finished=finished,
        in_progress=in_progress,
        not_started=not_started,
        percent_complete=percent,
    )


def compute_series_list(
    all_library_series: list[list[dict]],
    progress_map: dict,
) -> list[SeriesSummary]:
    series_map = _build_series_map(all_library_series, progress_map)
    return sorted(
        [_to_summary(name, entry) for name, entry in series_map.items()],
        key=lambda s: s.name.lower(),
    )


def compute_series_detail(
    series_name: str,
    all_library_series: list[list[dict]],
    progress_map: dict,
) -> SeriesDetail | None:
    series_map = _build_series_map(all_library_series, progress_map)
    entry = series_map.get(series_name)
    if entry is None:
        return None
    books: list[SeriesBook] = entry["books"]
    total = len(books)
    finished = sum(1 for b in books if b.is_finished)
    in_progress = sum(1 for b in books if not b.is_finished and b.progress > 0)
    not_started = total - finished - in_progress
    percent = round(finished / total * 100, 1) if total > 0 else 0.0
    return SeriesDetail(
        name=series_name,
        author=entry["author"],
        total=total,
        finished=finished,
        in_progress=in_progress,
        not_started=not_started,
        percent_complete=percent,
        books=books,
    )

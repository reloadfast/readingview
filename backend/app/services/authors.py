from ..schemas.authors import AuthorBook, AuthorDetail


def _format_duration(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"


def compute_author_detail(
    author_name: str, items: list[dict], progress_map: dict
) -> AuthorDetail | None:
    books = []
    total_duration = 0.0
    finished_count = 0

    for item in items:
        media = item.get("media", {})
        metadata = media.get("metadata", {})
        raw_authors = metadata.get("authors", [])
        names = [
            a.get("name", "").strip()
            for a in raw_authors
            if isinstance(a, dict)
        ]
        if author_name not in names:
            continue

        item_id = item.get("id", "")
        title = metadata.get("title", "Unknown Title")
        narrator = (metadata.get("narratorName") or "").strip()
        duration = float(media.get("duration") or 0)
        progress = progress_map.get(item_id, {})
        is_finished = progress.get("isFinished", False)

        total_duration += duration
        if is_finished:
            finished_count += 1

        books.append(
            AuthorBook(
                id=item_id,
                title=title,
                narrator=narrator,
                duration=duration,
                duration_formatted=_format_duration(duration),
                is_finished=is_finished,
            )
        )

    if not books:
        return None

    return AuthorDetail(
        name=author_name,
        book_count=len(books),
        total_hours=round(total_duration / 3600, 1),
        finished_count=finished_count,
        books=sorted(books, key=lambda b: b.title.lower()),
    )

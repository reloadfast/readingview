from ..schemas.narrators import NarratorBook, NarratorDetail, NarratorSummary


def _format_duration(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"


def _build_narrator_map(items: list[dict], progress_map: dict) -> dict[str, dict]:
    narrators: dict[str, dict] = {}
    for item in items:
        media = item.get("media", {})
        metadata = media.get("metadata", {})
        narrator_str = (metadata.get("narratorName") or "").strip()
        if not narrator_str:
            continue

        item_id = item.get("id", "")
        title = metadata.get("title", "Unknown Title")
        author = metadata.get("authorName", "Unknown Author")
        duration = float(media.get("duration") or 0)
        progress = progress_map.get(item_id, {})
        is_finished = progress.get("isFinished", False)

        for name in [n.strip() for n in narrator_str.split(",") if n.strip()]:
            if name not in narrators:
                narrators[name] = {"name": name, "books": [], "total_duration": 0.0, "finished": 0}
            narrators[name]["books"].append(
                NarratorBook(
                    id=item_id,
                    title=title,
                    author=author,
                    duration=duration,
                    duration_formatted=_format_duration(duration),
                    is_finished=is_finished,
                )
            )
            narrators[name]["total_duration"] += duration
            if is_finished:
                narrators[name]["finished"] += 1

    return narrators


def compute_narrator_list(items: list[dict], progress_map: dict) -> list[NarratorSummary]:
    nm = _build_narrator_map(items, progress_map)
    return sorted(
        [
            NarratorSummary(
                name=name,
                book_count=len(entry["books"]),
                total_hours=round(entry["total_duration"] / 3600, 1),
                finished_count=entry["finished"],
            )
            for name, entry in nm.items()
        ],
        key=lambda n: n.name.lower(),
    )


def compute_narrator_detail(
    narrator_name: str, items: list[dict], progress_map: dict
) -> NarratorDetail | None:
    nm = _build_narrator_map(items, progress_map)
    entry = nm.get(narrator_name)
    if entry is None:
        return None
    return NarratorDetail(
        name=narrator_name,
        book_count=len(entry["books"]),
        total_hours=round(entry["total_duration"] / 3600, 1),
        finished_count=entry["finished"],
        books=sorted(entry["books"], key=lambda b: b.title.lower()),
    )

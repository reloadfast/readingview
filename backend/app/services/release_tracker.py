import httpx

_TIMEOUT = 15.0
_BASE_URL = "https://openlibrary.org"
_HEADERS = {
    "User-Agent": "ReadingView/1.0 (Audiobook tracker)",
    "Accept": "application/json",
}


async def fetch_author_works(author_name: str, limit: int = 20) -> list[dict]:
    params: dict[str, str | int] = {
        "author": author_name,
        "limit": limit,
        "fields": "key,title,author_name,first_publish_year,isbn,cover_i",
    }
    async with httpx.AsyncClient(headers=_HEADERS, timeout=_TIMEOUT) as c:
        r = await c.get(f"{_BASE_URL}/search.json", params=params)
        r.raise_for_status()
    return r.json().get("docs", [])


def _ol_work_url(work_key: str) -> str:
    key = work_key if work_key.startswith("/") else f"/works/{work_key}"
    return f"{_BASE_URL}{key}"


def extract_releases(docs: list[dict], author_name: str) -> list[dict]:
    """Normalise OL search docs into release dicts, deduplicating by title."""
    seen: set[str] = set()
    releases: list[dict] = []
    for doc in docs:
        title = (doc.get("title") or "").strip()
        if not title:
            continue
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)

        year = doc.get("first_publish_year")
        release_date = str(year) if year else None

        isbns = doc.get("isbn") or []
        isbn = isbns[0] if isbns else None

        work_key = doc.get("key") or ""

        releases.append(
            {
                "title": title,
                "author_name": author_name,
                "release_date": release_date,
                "release_date_confirmed": year is not None,
                "ol_key": work_key,
                "link_url": _ol_work_url(work_key) if work_key else None,
                "source": "openlibrary",
                "isbn": isbn,
            }
        )

    releases.sort(key=lambda r: r["release_date"] or "", reverse=True)
    return releases

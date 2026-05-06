import httpx

_TIMEOUT = 10.0
_BASE_URL = "https://openlibrary.org"
_COVERS_URL = "https://covers.openlibrary.org"
_HEADERS = {
    "User-Agent": "ReadingView/1.0 (Audiobook tracker)",
    "Accept": "application/json",
}


class OpenLibraryClient:
    async def search_authors(self, name: str, limit: int = 10) -> list[dict]:
        params = {
            "q": name,
            "limit": limit,
            "fields": "key,name,birth_date,death_date,photos,top_work,work_count",
        }
        async with httpx.AsyncClient(headers=_HEADERS, timeout=_TIMEOUT) as c:
            r = await c.get(f"{_BASE_URL}/search/authors.json", params=params)
            r.raise_for_status()
        return r.json().get("docs", [])

    async def get_author_details(self, author_key: str) -> dict | None:
        key = author_key if author_key.startswith("/authors/") else f"/authors/{author_key}"
        async with httpx.AsyncClient(headers=_HEADERS, timeout=_TIMEOUT) as c:
            r = await c.get(f"{_BASE_URL}{key}.json")
            if r.status_code == 404:
                return None
            r.raise_for_status()
        return r.json()

    @staticmethod
    def photo_url(ol_data: dict, size: str = "M") -> str | None:
        photos = ol_data.get("photos", [])
        if photos:
            pid = photos[0]
            if pid and pid != -1:
                return f"{_COVERS_URL}/a/id/{pid}-{size}.jpg"
        key = ol_data.get("key", "")
        if key:
            olid = key.replace("/authors/", "")
            if olid:
                return f"{_COVERS_URL}/a/olid/{olid}-{size}.jpg"
        return None

    @staticmethod
    def normalise_key(raw_key: str) -> str:
        return raw_key.replace("/authors/", "")

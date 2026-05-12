import httpx

_TIMEOUT = 10.0


class AudiobookshelfClient:
    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._http = httpx.AsyncClient(
            base_url=f"{self.base_url}/api",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=_TIMEOUT,
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "AudiobookshelfClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def get_media_progress_map(self) -> dict:
        r = await self._http.get("/me")
        r.raise_for_status()
        progress_list = r.json().get("mediaProgress", [])
        return {p["libraryItemId"]: p for p in progress_list if p.get("libraryItemId")}

    async def get_libraries(self) -> list[dict]:
        r = await self._http.get("/libraries")
        r.raise_for_status()
        return r.json().get("libraries", [])

    async def get_library_items(self, library_id: str) -> list[dict]:
        r = await self._http.get(f"/libraries/{library_id}/items")
        r.raise_for_status()
        return r.json().get("results", [])

    async def get_all_library_items(self) -> list[dict]:
        items: list[dict] = []
        for lib in await self.get_libraries():
            items.extend(await self.get_library_items(lib["id"]))
        return items

    async def get_user_items_in_progress(self) -> list[dict]:
        r = await self._http.get("/me/items-in-progress")
        r.raise_for_status()
        return r.json().get("libraryItems", [])

    async def get_item(self, item_id: str) -> dict | None:
        r = await self._http.get(f"/items/{item_id}")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    async def get_library_series(self, library_id: str) -> list[dict]:
        all_series: list[dict] = []
        page = 0
        limit = 100
        while True:
            r = await self._http.get(f"/libraries/{library_id}/series?limit={limit}&page={page}")
            r.raise_for_status()
            data = r.json()
            batch = data.get("results", [])
            all_series.extend(batch)
            if len(all_series) >= data.get("total", 0) or not batch:
                break
            page += 1
        return all_series

    async def get_user_listening_stats(self) -> dict:
        r = await self._http.get("/me/listening-stats")
        r.raise_for_status()
        return r.json()

    async def get_user_listening_sessions(self) -> list[dict]:
        all_sessions: list[dict] = []
        page = 0
        items_per_page = 100
        while True:
            url = f"/me/listening-sessions?itemsPerPage={items_per_page}&page={page}"
            r = await self._http.get(url)
            r.raise_for_status()
            data = r.json()
            sessions = data.get("sessions", [])
            all_sessions.extend(sessions)
            total = data.get("total", 0)
            if len(all_sessions) >= total or not sessions:
                break
            page += 1
        return all_sessions

    def cover_url(self, item_id: str) -> str:
        return f"/api/cover/{item_id}"

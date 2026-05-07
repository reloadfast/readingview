"""Synchronous Open Library client for use inside book_recommender (httpx-based)."""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_BASE_URL = "https://openlibrary.org"
_HEADERS = {"User-Agent": "ReadingView/1.0 (Audiobook tracker)", "Accept": "application/json"}
_TIMEOUT = 10.0


class OpenLibraryAPI:
    """Sync httpx-based client for Open Library — exposes only what ingestion needs."""

    def search_books(
        self,
        query: str | None = None,
        title: str | None = None,
        author: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limit": limit}
        if query:
            params["q"] = query
        if title:
            params["title"] = title
        if author:
            params["author"] = author
        try:
            r = httpx.get(
                f"{_BASE_URL}/search.json",
                params=params,
                headers=_HEADERS,
                timeout=_TIMEOUT,
            )
            r.raise_for_status()
            return r.json().get("docs", [])
        except httpx.RequestError as e:
            logger.error("Open Library search failed: %s", e)
            return []

    def get_work_details(self, work_key: str) -> dict[str, Any] | None:
        if not work_key.startswith("/works/"):
            work_key = f"/works/{work_key}"
        try:
            r = httpx.get(f"{_BASE_URL}{work_key}.json", headers=_HEADERS, timeout=_TIMEOUT)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()
        except httpx.RequestError as e:
            logger.error("Open Library get_work_details failed: %s", e)
            return None

    def get_author_details(self, author_key: str) -> dict[str, Any] | None:
        if not author_key.startswith("/authors/"):
            author_key = f"/authors/{author_key}"
        try:
            r = httpx.get(f"{_BASE_URL}{author_key}.json", headers=_HEADERS, timeout=_TIMEOUT)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()
        except httpx.RequestError as e:
            logger.error("Open Library get_author_details failed: %s", e)
            return None

    @staticmethod
    def extract_book_info(result: dict[str, Any]) -> dict[str, Any]:
        return {
            "title": result.get("title", "Unknown"),
            "author_names": result.get("author_name", []),
            "isbn": result.get("isbn", [None])[0] if result.get("isbn") else None,
            "cover_id": result.get("cover_i"),
            "work_key": result.get("key"),
        }

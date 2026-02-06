"""Metadata ingestion from Open Library into the recommender database."""

import logging
from typing import Optional

from ._db import RecommenderDB

logger = logging.getLogger(__name__)


class MetadataIngester:
    """Fetches book metadata from Open Library and stores it in the recommender DB."""

    def __init__(self, db: RecommenderDB, openlibrary_api=None):
        self.db = db
        if openlibrary_api is None:
            from api.openlibrary import OpenLibraryAPI
            openlibrary_api = OpenLibraryAPI()
        self.ol = openlibrary_api

    def ingest_by_isbn(self, isbn: str) -> Optional[str]:
        """Ingest a book by ISBN. Returns book_id or None."""
        results = self.ol.search_books(query=f"isbn:{isbn}", limit=1)
        if not results:
            logger.warning("No results found for ISBN %s", isbn)
            return None
        return self._ingest_search_result(results[0])

    def ingest_by_title(self, title: str, author: Optional[str] = None) -> Optional[str]:
        """Ingest a book by title (and optional author). Returns book_id or None."""
        results = self.ol.search_books(title=title, author=author, limit=1)
        if not results:
            logger.warning("No results found for title=%s author=%s", title, author)
            return None
        return self._ingest_search_result(results[0])

    def ingest_by_work_key(self, work_key: str) -> Optional[str]:
        """Ingest a book by Open Library work key. Returns book_id or None."""
        details = self.ol.get_work_details(work_key)
        if not details:
            logger.warning("No work details found for key %s", work_key)
            return None
        return self._ingest_work_details(work_key, details)

    def _ingest_search_result(self, result: dict) -> str:
        """Process a search result into the DB."""
        info = self.ol.extract_book_info(result)
        work_key = info.get("work_key", "")
        book_id = work_key or info.get("isbn") or info["title"]

        # Try to get richer description from work details
        description = None
        subjects = result.get("subject", [])
        if work_key:
            details = self.ol.get_work_details(work_key)
            if details:
                description = self._extract_description(details)
                subjects = subjects or details.get("subjects", [])

        self.db.upsert_book(
            book_id=book_id,
            title=info["title"],
            authors=info.get("author_names", []),
            description=description,
            subjects=subjects[:50],  # cap to avoid huge lists
            isbns=[info["isbn"]] if info.get("isbn") else result.get("isbn", [])[:10],
            cover_id=info.get("cover_id"),
            work_key=work_key,
        )
        return book_id

    def _ingest_work_details(self, work_key: str, details: dict) -> str:
        """Process work details into the DB."""
        if not work_key.startswith("/works/"):
            work_key = f"/works/{work_key}"

        title = details.get("title", "Unknown")
        description = self._extract_description(details)
        subjects = details.get("subjects", [])

        # Extract author names from author references
        authors = []
        for author_ref in details.get("authors", []):
            author_obj = author_ref
            if isinstance(author_ref, dict) and "author" in author_ref:
                author_obj = author_ref["author"]
            if isinstance(author_obj, dict) and "key" in author_obj:
                author_details = self.ol.get_author_details(author_obj["key"])
                if author_details:
                    authors.append(author_details.get("name", "Unknown"))

        cover_ids = details.get("covers", [])
        cover_id = cover_ids[0] if cover_ids else None

        self.db.upsert_book(
            book_id=work_key,
            title=title,
            authors=authors,
            description=description,
            subjects=subjects[:50],
            cover_id=cover_id,
            work_key=work_key,
        )
        return work_key

    @staticmethod
    def _extract_description(details: dict) -> Optional[str]:
        """Extract description handling OL's varying formats."""
        desc = details.get("description")
        if desc is None:
            return None
        if isinstance(desc, str):
            return desc
        if isinstance(desc, dict):
            return desc.get("value")
        return None

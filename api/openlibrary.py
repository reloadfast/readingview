"""
Open Library API client for book metadata and release information.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class OpenLibraryAPI:
    """Client for interacting with Open Library API."""

    BASE_URL = "https://openlibrary.org"
    COVERS_URL = "https://covers.openlibrary.org"

    def __init__(self):
        """Initialize the API client."""
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "ReadingView/1.0 (Audiobook tracker)",
                "Accept": "application/json",
            }
        )

    def search_books(
        self,
        query: Optional[str] = None,
        title: Optional[str] = None,
        author: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search for books using Open Library Search API.

        Args:
            query: General search query
            title: Search by title
            author: Search by author
            limit: Maximum results to return

        Returns:
            List of book results
        """
        url = f"{self.BASE_URL}/search.json"
        params = {"limit": limit}

        if query:
            params["q"] = query
        if title:
            params["title"] = title
        if author:
            params["author"] = author

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("docs", [])
        except requests.exceptions.RequestException as e:
            logger.error(f"Open Library search failed: {e}")
            return []

    def get_author_works(
        self, author_name: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get works by an author.

        Args:
            author_name: Author's name
            limit: Maximum results

        Returns:
            List of works
        """
        return self.search_books(author=author_name, limit=limit)

    def get_series_books(
        self, series_name: str, author_name: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for books in a series.

        Args:
            series_name: Series name
            author_name: Author name
            limit: Maximum results

        Returns:
            List of books in the series
        """
        query = f"{series_name} {author_name}"
        return self.search_books(query=query, limit=limit)

    def get_work_details(self, work_key: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a work.

        Args:
            work_key: Work key (e.g., "OL45804W")

        Returns:
            Work details or None
        """
        if not work_key.startswith("/works/"):
            work_key = f"/works/{work_key}"

        url = f"{self.BASE_URL}{work_key}.json"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get work details: {e}")
            return None

    def get_edition_details(self, edition_key: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about an edition.

        Args:
            edition_key: Edition key (e.g., "OL7353617M")

        Returns:
            Edition details or None
        """
        if not edition_key.startswith("/books/"):
            edition_key = f"/books/{edition_key}"

        url = f"{self.BASE_URL}{edition_key}.json"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get edition details: {e}")
            return None

    def get_author_details(self, author_key: str) -> Optional[Dict[str, Any]]:
        """
        Get author information.

        Args:
            author_key: Author key (e.g., "OL26320A")

        Returns:
            Author details or None
        """
        if not author_key.startswith("/authors/"):
            author_key = f"/authors/{author_key}"

        url = f"{self.BASE_URL}{author_key}.json"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get author details: {e}")
            return None

    def get_cover_url(
        self,
        cover_id: Optional[int] = None,
        isbn: Optional[str] = None,
        olid: Optional[str] = None,
        size: str = "M",
    ) -> Optional[str]:
        """
        Get cover image URL.

        Args:
            cover_id: Cover ID number
            isbn: ISBN
            olid: Open Library ID
            size: Size (S=small, M=medium, L=large)

        Returns:
            Cover URL or None
        """
        if cover_id:
            return f"{self.COVERS_URL}/b/id/{cover_id}-{size}.jpg"
        elif isbn:
            return f"{self.COVERS_URL}/b/isbn/{isbn}-{size}.jpg"
        elif olid:
            return f"{self.COVERS_URL}/b/olid/{olid}-{size}.jpg"
        return None

    def search_for_next_in_series(
        self, series_name: str, author_name: str, last_book_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Try to find the next book in a series.

        Args:
            series_name: Series name
            author_name: Author name
            last_book_number: Last book number read

        Returns:
            List of potential next books
        """
        books = self.get_series_books(series_name, author_name, limit=30)

        # Sort by first publish year
        books_with_year = [b for b in books if b.get("first_publish_year")]
        books_with_year.sort(key=lambda x: x["first_publish_year"])

        # If we have a book number, try to filter
        if last_book_number is not None:
            # Look for books published after the last book
            # This is heuristic since we don't have reliable book numbers
            return books_with_year

        return books_with_year

    def extract_book_info(self, search_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract useful information from a search result.

        Args:
            search_result: Book data from search API

        Returns:
            Cleaned book information
        """
        return {
            "title": search_result.get("title", "Unknown"),
            "author_names": search_result.get("author_name", []),
            "author_keys": search_result.get("author_key", []),
            "first_publish_year": search_result.get("first_publish_year"),
            "edition_count": search_result.get("edition_count", 0),
            "isbn": search_result.get("isbn", [None])[0]
            if search_result.get("isbn")
            else None,
            "cover_id": search_result.get("cover_i"),
            "work_key": search_result.get("key"),
            "ebook_access": search_result.get("ebook_access"),
            "has_fulltext": search_result.get("has_fulltext", False),
            "language": search_result.get("language", []),
            "publisher": search_result.get("publisher", []),
        }

    def get_openlibrary_url(self, key: str) -> str:
        """
        Get the Open Library URL for a work/edition/author.

        Args:
            key: The key (e.g., "/works/OL45804W")

        Returns:
            Full URL
        """
        if key.startswith("http"):
            return key
        return f"{self.BASE_URL}{key}"

    def suggest_next_release(
        self, author_name: str, series_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Suggest the next upcoming release for an author/series.

        This is best-effort since Open Library doesn't have official release dates.

        Args:
            author_name: Author name
            series_name: Optional series name

        Returns:
            Suggested book information or None
        """
        if series_name:
            books = self.get_series_books(series_name, author_name, limit=20)
        else:
            books = self.get_author_works(author_name, limit=20)

        if not books:
            return None

        # Sort by publication year (most recent first)
        books_with_year = [b for b in books if b.get("first_publish_year")]
        books_with_year.sort(key=lambda x: x["first_publish_year"], reverse=True)

        # Get the most recent book as a suggestion
        if books_with_year:
            most_recent = books_with_year[0]
            return self.extract_book_info(most_recent)

        return None

"""
Book Recommender — pluggable, feature-flagged recommendation module.

Safe to import when disabled. No side effects on import.
All initialization is deferred to first use.

Public API:
    recommend(liked_book_ids, free_text_prompt) -> list[dict]
    ingest(isbn, title, author, work_key) -> str | None
"""

from ._exceptions import BookRecommenderDisabled, BookRecommenderConfigError

__all__ = [
    "recommend",
    "ingest",
    "BookRecommenderDisabled",
    "BookRecommenderConfigError",
]


def recommend(
    liked_book_ids: list[str] | None = None,
    free_text_prompt: str | None = None,
) -> list[dict]:
    """Get book recommendations. Returns [] if the feature is disabled."""
    from .service import recommend as _recommend
    return _recommend(liked_book_ids=liked_book_ids, free_text_prompt=free_text_prompt)


def ingest(
    isbn: str | None = None,
    title: str | None = None,
    author: str | None = None,
    work_key: str | None = None,
) -> str | None:
    """
    Ingest a book into the recommender database.

    Raises BookRecommenderDisabled if the feature is not enabled.
    """
    from .service import ingest as _ingest
    return _ingest(isbn=isbn, title=title, author=author, work_key=work_key)

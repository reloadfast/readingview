"""
Book Recommender — pluggable, feature-flagged recommendation module.

Safe to import when disabled. No side effects on import.
All initialization is deferred to first use.

Public API:
    recommend(liked_book_ids, free_text_prompt) -> list[dict]
    ingest(isbn, title, author, work_key) -> str | None
    remove_book(book_id) -> bool
"""

from ._exceptions import BookRecommenderDisabled, BookRecommenderConfigError

__all__ = [
    "recommend",
    "ingest",
    "remove_book",
    "submit_feedback",
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


def remove_book(book_id: str) -> bool:
    """
    Remove a book from the recommender catalog.

    Raises BookRecommenderDisabled if the feature is not enabled.
    """
    from .service import remove_book as _remove_book
    return _remove_book(book_id=book_id)


def submit_feedback(
    book_id: str,
    rating: int,
    source_book_ids: list[str] | None = None,
    source_prompt: str | None = None,
) -> None:
    """
    Submit user feedback for a recommendation (+1 thumbs up, -1 thumbs down).

    Raises BookRecommenderDisabled if the feature is not enabled.
    """
    from .service import submit_feedback as _submit_feedback
    _submit_feedback(
        book_id=book_id,
        rating=rating,
        source_book_ids=source_book_ids,
        source_prompt=source_prompt,
    )

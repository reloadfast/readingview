"""Exceptions for the book recommender module."""


class BookRecommenderDisabledError(Exception):
    """Raised when the book recommender feature is not enabled."""

    def __init__(self):
        super().__init__(
            "Book recommender is disabled. Enable it via Settings → recommender_enabled."
        )


class BookRecommenderConfigError(Exception):
    """Raised when required configuration is missing or invalid."""

    def __init__(self, message: str):
        super().__init__(f"Book recommender configuration error: {message}")

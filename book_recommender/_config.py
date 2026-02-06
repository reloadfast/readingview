"""Environment-based configuration for the book recommender module."""

import os
from typing import Optional

from ._exceptions import BookRecommenderConfigError

_config_instance: Optional["RecommenderConfig"] = None


class RecommenderConfig:
    """Configuration parsed from BOOK_RECOMMENDER_* environment variables."""

    def __init__(self):
        self.enabled: bool = (
            os.getenv("BOOK_RECOMMENDER_ENABLED", "false").lower() == "true"
        )

        if not self.enabled:
            return

        self.db_path: str = os.getenv("BOOK_RECOMMENDER_DB_PATH", "")
        self.vector_backend: str = os.getenv(
            "BOOK_RECOMMENDER_VECTOR_BACKEND", ""
        )
        self.embed_model: str = os.getenv("BOOK_RECOMMENDER_EMBED_MODEL", "")
        self.llm_model: str = os.getenv("BOOK_RECOMMENDER_LLM_MODEL", "")
        self.enable_explanations: bool = (
            os.getenv("BOOK_RECOMMENDER_ENABLE_EXPLANATIONS", "false").lower()
            == "true"
        )
        self.ollama_url: str = os.getenv("BOOK_RECOMMENDER_OLLAMA_URL", "")
        self.top_k: int = int(os.getenv("BOOK_RECOMMENDER_TOP_K", "10"))
        self.min_similarity: float = float(
            os.getenv("BOOK_RECOMMENDER_MIN_SIMILARITY", "0.2")
        )

    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate configuration. Returns (is_valid, error_message)."""
        if not self.enabled:
            return True, None

        if not self.db_path:
            return False, "BOOK_RECOMMENDER_DB_PATH is required"
        if not self.vector_backend:
            return False, "BOOK_RECOMMENDER_VECTOR_BACKEND is required (faiss|python)"
        if self.vector_backend not in ("faiss", "python"):
            return False, "BOOK_RECOMMENDER_VECTOR_BACKEND must be 'faiss' or 'python'"
        if not self.embed_model:
            return False, "BOOK_RECOMMENDER_EMBED_MODEL is required"
        if not self.llm_model:
            return False, "BOOK_RECOMMENDER_LLM_MODEL is required"
        if not self.ollama_url:
            return False, "BOOK_RECOMMENDER_OLLAMA_URL is required"

        return True, None

    def validate_or_raise(self) -> None:
        """Validate configuration and raise on error."""
        is_valid, error = self.validate()
        if not is_valid:
            raise BookRecommenderConfigError(error)


def get_config() -> RecommenderConfig:
    """Return the lazy singleton config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = RecommenderConfig()
    return _config_instance


def reset_config() -> None:
    """Reset the singleton (for testing or reload)."""
    global _config_instance
    _config_instance = None

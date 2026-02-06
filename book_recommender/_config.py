"""Environment-based configuration for the book recommender module."""

import logging
import os
from typing import Optional

from ._exceptions import BookRecommenderConfigError

_config_instance: Optional["RecommenderConfig"] = None
_logging_configured = False


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
        self.log_level: str = os.getenv("BOOK_RECOMMENDER_LOG_LEVEL", "WARNING")

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


def configure_logging(level_name: str) -> None:
    """Set up logging for the book_recommender hierarchy."""
    global _logging_configured
    if _logging_configured:
        return
    level = getattr(logging, level_name.upper(), logging.WARNING)
    root_logger = logging.getLogger("book_recommender")
    root_logger.setLevel(level)
    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
        ))
        root_logger.addHandler(handler)
    _logging_configured = True


def get_config() -> RecommenderConfig:
    """Return the lazy singleton config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = RecommenderConfig()
        if _config_instance.enabled:
            configure_logging(_config_instance.log_level)
    return _config_instance


def reset_config() -> None:
    """Reset the singleton (for testing or reload)."""
    global _config_instance, _logging_configured
    _config_instance = None
    _logging_configured = False

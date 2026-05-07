"""Configuration for the book recommender module — sourced from DB settings row."""

import logging
from typing import TYPE_CHECKING, Optional

from ._exceptions import BookRecommenderConfigError

if TYPE_CHECKING:
    pass

_config_instance: Optional["RecommenderConfig"] = None
_logging_configured = False


class RecommenderConfig:
    """Configuration built from the database settings row."""

    def __init__(
        self,
        enabled: bool,
        db_path: str,
        vector_backend: str = "python",
        embed_model: str = "nomic-embed-text",
        llm_model: str = "",
        enable_explanations: bool = False,
        ollama_url: str = "",
        top_k: int = 10,
        min_similarity: float = 0.2,
    ):
        self.enabled = enabled
        self.db_path = db_path
        self.vector_backend = vector_backend
        self.embed_model = embed_model
        self.llm_model = llm_model
        self.enable_explanations = enable_explanations
        self.ollama_url = ollama_url
        self.top_k = top_k
        self.min_similarity = min_similarity

    def validate(self) -> tuple[bool, str | None]:
        if not self.enabled:
            return True, None
        if not self.db_path:
            return False, "db_path is required (derived from DATABASE_URL)"
        if not self.vector_backend or self.vector_backend not in ("faiss", "python"):
            return False, "recommender_vector_backend must be 'faiss' or 'python'"
        if not self.embed_model:
            return False, "recommender_embed_model is required"
        if not self.llm_model:
            return False, "llm_model is required"
        if not self.ollama_url:
            return False, "llm_endpoint (Ollama URL) is required"
        return True, None

    def validate_or_raise(self) -> None:
        is_valid, error = self.validate()
        if not is_valid:
            raise BookRecommenderConfigError(error)  # type: ignore[arg-type]


def configure_logging(level_name: str = "WARNING") -> None:
    global _logging_configured
    if _logging_configured:
        return
    level = getattr(logging, level_name.upper(), logging.WARNING)
    root_logger = logging.getLogger("book_recommender")
    root_logger.setLevel(level)
    if not root_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s"))
        root_logger.addHandler(handler)
    _logging_configured = True


def get_config() -> RecommenderConfig | None:
    """Return the current config, or None if not yet configured."""
    return _config_instance


def configure(cfg: RecommenderConfig) -> None:
    """Set the module-level config singleton."""
    global _config_instance
    _config_instance = cfg
    if cfg.enabled:
        configure_logging()


def reset_config() -> None:
    global _config_instance, _logging_configured
    _config_instance = None
    _logging_configured = False

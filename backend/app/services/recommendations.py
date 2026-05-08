"""Thin wrapper that bridges DB settings to the book_recommender module."""

import hashlib
import logging

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings as app_settings
from ..models.settings import Settings as DBSettings

logger = logging.getLogger(__name__)

_last_config_hash: str | None = None


def _db_path_from_url(database_url: str) -> str:
    """Extract filesystem path from a SQLite DATABASE_URL.

    sqlite+aiosqlite:////data/foo.db  →  /data/foo.db
    sqlite+aiosqlite:///./foo.db      →  ./foo.db
    """
    if "sqlite" in database_url:
        db = make_url(database_url).database
        return db if db is not None else database_url
    return database_url


def _settings_hash(row: DBSettings | None) -> str:
    if row is None:
        return "none"
    fields = (
        row.recommender_enabled,
        row.recommender_vector_backend,
        row.recommender_embed_model,
        row.llm_model,
        row.recommender_explanations_enabled,
        row.llm_endpoint,
        row.recommender_top_k,
        row.recommender_min_similarity,
    )
    return hashlib.md5(str(fields).encode()).hexdigest()  # noqa: S324  # nosec B324


async def _configure_recommender(db: AsyncSession) -> None:
    """Load settings from DB and (re)configure the recommender if anything changed."""
    global _last_config_hash

    row = await db.get(DBSettings, 1)
    current_hash = _settings_hash(row)

    if current_hash == _last_config_hash:
        return

    from book_recommender._config import RecommenderConfig, configure
    from book_recommender.service import reset as reset_service

    reset_service()

    if row is None or not row.recommender_enabled:
        configure(RecommenderConfig(enabled=False, db_path=""))
    else:
        db_path = _db_path_from_url(app_settings.DATABASE_URL)
        cfg = RecommenderConfig(
            enabled=True,
            db_path=db_path,
            vector_backend=row.recommender_vector_backend,
            embed_model=row.recommender_embed_model,
            llm_model=row.llm_model or "",
            enable_explanations=row.recommender_explanations_enabled,
            ollama_url=row.llm_endpoint or "",
            top_k=row.recommender_top_k,
            min_similarity=row.recommender_min_similarity,
        )
        configure(cfg)

    _last_config_hash = current_hash


async def get_recommendations(
    db: AsyncSession,
    book_ids: list[str] | None = None,
    prompt: str | None = None,
) -> list[dict]:
    await _configure_recommender(db)
    from book_recommender.service import recommend

    return recommend(liked_book_ids=book_ids, free_text_prompt=prompt)


async def run_ingest(
    db: AsyncSession,
    isbn: str | None = None,
    title: str | None = None,
    author: str | None = None,
    work_key: str | None = None,
) -> str | None:
    await _configure_recommender(db)
    from book_recommender._exceptions import BookRecommenderDisabledError
    from book_recommender.service import ingest

    try:
        return ingest(isbn=isbn, title=title, author=author, work_key=work_key)
    except BookRecommenderDisabledError:
        return None


async def get_status(db: AsyncSession) -> dict:
    await _configure_recommender(db)
    from book_recommender._config import get_config

    cfg = get_config()
    if cfg is None or not cfg.enabled:
        return {"enabled": False, "model": None, "vector_backend": None}
    return {
        "enabled": True,
        "model": cfg.embed_model,
        "vector_backend": cfg.vector_backend,
    }

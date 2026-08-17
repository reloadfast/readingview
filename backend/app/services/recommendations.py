"""Thin wrapper that bridges DB settings to the book_recommender module."""

import hashlib
import logging

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings as app_settings
from ..crypto import decrypt
from ..models.settings import Settings as DBSettings
from .audiobookshelf import AudiobookshelfClient

logger = logging.getLogger(__name__)


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
        row.llm_type,
        row.llm_api_key,
        row.recommender_explanations_enabled,
        row.llm_endpoint,
        row.recommender_top_k,
        row.recommender_min_similarity,
    )
    return hashlib.sha256(str(fields).encode()).hexdigest()[:32]


async def _configure_recommender(db: AsyncSession) -> None:
    """Load settings from DB and (re)configure the recommender if anything changed.

    Uses recommender_config_hash persisted on the settings row so all uvicorn
    workers share the same source of truth instead of per-process in-memory state.
    """
    row = await db.get(DBSettings, 1)
    current_hash = _settings_hash(row)
    stored_hash = row.recommender_config_hash if row is not None else None

    from book_recommender._config import get_config as _get_config

    if current_hash == stored_hash and _get_config() is not None:
        return

    from book_recommender._config import RecommenderConfig, configure
    from book_recommender.service import reset as reset_service

    reset_service()

    if row is None or not row.recommender_enabled:
        configure(RecommenderConfig(enabled=False, db_path=""))
    else:
        db_path = _db_path_from_url(app_settings.DATABASE_URL)
        try:
            api_key = decrypt(row.llm_api_key) if row.llm_api_key else None
        except Exception:
            logger.warning("Failed to decrypt recommender API key")
            api_key = None
        cfg = RecommenderConfig(
            enabled=True,
            db_path=db_path,
            vector_backend=row.recommender_vector_backend,
            embed_model=row.recommender_embed_model,
            llm_model=row.llm_model or "",
            enable_explanations=row.recommender_explanations_enabled,
            ollama_url=row.llm_endpoint or "",
            llm_type=row.llm_type,
            api_key=api_key,
            top_k=row.recommender_top_k,
            min_similarity=row.recommender_min_similarity,
        )
        configure(cfg)

    if row is not None:
        row.recommender_config_hash = current_hash
        await db.commit()


async def get_recommendations(
    db: AsyncSession,
    book_ids: list[str] | None = None,
    prompt: str | None = None,
) -> list[dict]:
    await _configure_recommender(db)
    if book_ids:
        book_ids = await _ingest_selected_library_books(db, book_ids)
    from book_recommender.service import recommend

    return recommend(liked_book_ids=book_ids, free_text_prompt=prompt)


async def _ingest_selected_library_books(db: AsyncSession, book_ids: list[str]) -> list[str]:
    """Ensure ABS selections have embeddings before they are used as sources."""
    row = await db.get(DBSettings, 1)
    if row is None or not row.abs_url or not row.abs_token:
        return book_ids

    from book_recommender.service import ingest_library_book

    try:
        token = decrypt(row.abs_token)
        async with AudiobookshelfClient(row.abs_url, token) as client:
            resolved: list[str] = []
            for book_id in book_ids:
                item = await client.get_item(book_id)
                if item is None:
                    resolved.append(book_id)
                    continue
                metadata = item.get("media", {}).get("metadata", {})
                raw_authors = metadata.get("authors", [])
                authors = [a.get("name", "") for a in raw_authors if isinstance(a, dict)]
                if not authors and metadata.get("authorName"):
                    authors = [a.strip() for a in metadata["authorName"].split(",") if a.strip()]
                ingest_library_book(
                    book_id=book_id,
                    title=metadata.get("title", "Unknown Title"),
                    authors=authors or ["Unknown Author"],
                    description=metadata.get("description"),
                    subjects=metadata.get("genres", []) or [],
                    isbn=metadata.get("isbn"),
                )
                resolved.append(book_id)
            return resolved
    except Exception as exc:
        from book_recommender._exceptions import BookRecommenderProviderError

        if isinstance(exc, BookRecommenderProviderError):
            raise
        logger.warning("Failed to ingest selected Audiobookshelf books", exc_info=True)
        return book_ids


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


async def submit_feedback_for_book(
    db: AsyncSession,
    book_id: str,
    vote: int,
) -> None:
    await _configure_recommender(db)
    from book_recommender._exceptions import BookRecommenderDisabledError
    from book_recommender.service import submit_feedback

    try:
        submit_feedback(book_id, vote)
    except BookRecommenderDisabledError as exc:
        raise exc


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

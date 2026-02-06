"""Orchestration layer for book recommendations."""

import json
import logging
from typing import Optional

from ._config import get_config
from ._exceptions import BookRecommenderDisabled

logger = logging.getLogger(__name__)

# Lazy singletons — initialized only on first use
_db = None
_ollama = None
_backend = None
_ingester = None
_initialized = False


def _ensure_initialized():
    """Validate config and create singletons. No-op after first call."""
    global _db, _ollama, _backend, _ingester, _initialized
    if _initialized:
        return

    cfg = get_config()
    if not cfg.enabled:
        raise BookRecommenderDisabled()

    cfg.validate_or_raise()

    from ._db import RecommenderDB
    from ._ollama import OllamaClient
    from ._vector import create_backend
    from ._ingestion import MetadataIngester

    _db = RecommenderDB(cfg.db_path)
    _ollama = OllamaClient(cfg.ollama_url, cfg.embed_model, cfg.llm_model)
    _backend = create_backend(cfg.vector_backend)
    _ingester = MetadataIngester(_db)
    _initialized = True
    logger.info(
        "Recommender initialized: db=%s vector=%s embed_model=%s ollama=%s",
        cfg.db_path, cfg.vector_backend, cfg.embed_model, cfg.ollama_url,
    )


def _embed_stale_books() -> int:
    """Embed books that need (re-)embedding. Returns count of newly embedded books."""
    cfg = get_config()
    stale = _db.get_stale_books(cfg.embed_model)
    logger.debug("Stale books needing embedding: %d", len(stale))
    if not stale:
        return 0

    count = 0
    for book in stale:
        text = _build_embed_text(book)
        embedding = _ollama.embed(text)
        if embedding is None:
            logger.warning("Failed to embed book %s", book["id"])
            continue
        _db.upsert_embedding(
            book_id=book["id"],
            embedding=embedding,
            model_name=cfg.embed_model,
            content_hash=book["content_hash"],
        )
        count += 1
    logger.info("Embedded %d/%d stale books", count, len(stale))
    return count


def _build_embed_text(book: dict) -> str:
    """Concatenate description + subjects for embedding."""
    parts = []
    if book.get("description"):
        parts.append(book["description"])
    subjects = book.get("subjects", [])
    if isinstance(subjects, str):
        subjects = json.loads(subjects)
    if subjects:
        parts.append("Subjects: " + ", ".join(subjects[:20]))
    if book.get("title"):
        parts.insert(0, book["title"])
    return "\n".join(parts)


def _rebuild_index_if_needed() -> None:
    """Rebuild the vector index if embeddings have changed."""
    current_hash = _db.compute_embeddings_hash()
    stored_hash = _db.get_index_state()
    if current_hash == stored_hash:
        return

    all_embeddings = _db.get_all_embeddings()
    if not all_embeddings:
        return

    ids = [e[0] for e in all_embeddings]
    vectors = [e[1] for e in all_embeddings]
    _backend.build(ids, vectors)
    _db.set_index_state(current_hash)


def recommend(
    liked_book_ids: Optional[list[str]] = None,
    free_text_prompt: Optional[str] = None,
) -> list[dict]:
    """
    Get book recommendations.

    Args:
        liked_book_ids: IDs of books the user liked (used for similarity).
        free_text_prompt: Free-text description of what the user wants.

    Returns:
        List of recommendation dicts with book metadata + score + optional explanation.
        Returns [] if the feature is disabled.
    """
    cfg = get_config()
    if not cfg.enabled:
        return []

    try:
        _ensure_initialized()
    except BookRecommenderDisabled:
        return []

    if not liked_book_ids and not free_text_prompt:
        return []

    logger.info("recommend() called: liked_book_ids=%s prompt_length=%d",
                liked_book_ids, len(free_text_prompt or ""))

    # Rebuild index if embeddings changed (embedding happens at ingest time)
    _rebuild_index_if_needed()

    query_vector = _compute_query_vector(liked_book_ids, free_text_prompt)
    if query_vector is None:
        return []

    # Search with extra margin for filtering
    raw_results = _backend.search(query_vector, cfg.top_k + len(liked_book_ids or []))

    # Filter by min similarity and exclude input books
    exclude = set(liked_book_ids or [])
    results = []
    for book_id, score in raw_results:
        if book_id in exclude:
            continue
        if score < cfg.min_similarity:
            continue
        results.append((book_id, score))
        if len(results) >= cfg.top_k:
            break

    # Build output with book metadata
    output = []
    source_books = []
    if liked_book_ids and cfg.enable_explanations:
        source_books = [_db.get_book(bid) for bid in liked_book_ids]
        source_books = [b for b in source_books if b is not None]

    for book_id, score in results:
        book = _db.get_book(book_id)
        if book is None:
            continue
        rec = {
            "book_id": book_id,
            "title": book["title"],
            "authors": book["authors"],
            "description": book.get("description"),
            "subjects": book.get("subjects", []),
            "cover_id": book.get("cover_id"),
            "work_key": book.get("work_key"),
            "score": round(score, 4),
            "explanation": None,
        }

        if cfg.enable_explanations:
            rec["explanation"] = _generate_explanation(
                source_books, free_text_prompt, book
            )

        output.append(rec)

    logger.info("recommend() returning %d results (searched %d candidates)", len(output), len(raw_results))
    return output


def _compute_query_vector(
    liked_book_ids: Optional[list[str]],
    free_text_prompt: Optional[str],
) -> Optional[list[float]]:
    """Merge liked-book embeddings and/or prompt embedding into a single query vector."""
    import numpy as np

    book_vec = None
    prompt_vec = None

    if liked_book_ids:
        embeddings = []
        for bid in liked_book_ids:
            emb = _db.get_embedding(bid)
            if emb is not None:
                embeddings.append(emb)
        if embeddings:
            book_vec = np.mean(embeddings, axis=0).astype(np.float32)

    if free_text_prompt:
        emb = _ollama.embed(free_text_prompt)
        if emb is not None:
            prompt_vec = np.array(emb, dtype=np.float32)

    if book_vec is not None and prompt_vec is not None:
        # Weighted merge: 0.6 liked books + 0.4 text prompt
        merged = 0.6 * book_vec + 0.4 * prompt_vec
        return merged.tolist()
    elif book_vec is not None:
        return book_vec.tolist()
    elif prompt_vec is not None:
        return prompt_vec.tolist()

    return None


def _generate_explanation(
    source_books: list[dict],
    free_text_prompt: Optional[str],
    rec_book: dict,
) -> Optional[str]:
    """Generate an explanation, never blocking on failure."""
    try:
        from ._explanations import explain_recommendation, explain_prompt_recommendation

        if source_books:
            return explain_recommendation(_ollama, source_books, rec_book)
        if free_text_prompt:
            return explain_prompt_recommendation(_ollama, free_text_prompt, rec_book)
    except Exception:
        logger.debug("Explanation generation failed", exc_info=True)
    return None


def ingest(
    isbn: Optional[str] = None,
    title: Optional[str] = None,
    author: Optional[str] = None,
    work_key: Optional[str] = None,
) -> Optional[str]:
    """
    Ingest a book into the recommender database.

    Provide one of: isbn, title (+optional author), or work_key.
    Embeddings are computed immediately after ingestion so that
    subsequent recommend() calls stay fast.

    Returns:
        The book_id of the ingested book, or None on failure.

    Raises:
        BookRecommenderDisabled: If the feature is not enabled.
    """
    _ensure_initialized()
    logger.info("ingest() called: isbn=%s title=%s author=%s work_key=%s", isbn, title, author, work_key)

    book_id = None
    if work_key:
        book_id = _ingester.ingest_by_work_key(work_key)
    elif isbn:
        book_id = _ingester.ingest_by_isbn(isbn)
    elif title:
        book_id = _ingester.ingest_by_title(title, author)

    if book_id is not None:
        _embed_stale_books()

    return book_id


def remove_book(book_id: str) -> bool:
    """
    Remove a book from the recommender catalog.

    Returns:
        True if the book was found and removed, False otherwise.

    Raises:
        BookRecommenderDisabled: If the feature is not enabled.
    """
    _ensure_initialized()
    logger.info("remove_book() called: book_id=%s", book_id)
    return _db.delete_book(book_id)

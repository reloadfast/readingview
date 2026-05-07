"""Orchestration layer for book recommendations."""

import json
import logging

from ._config import get_config
from ._exceptions import BookRecommenderDisabledError

logger = logging.getLogger(__name__)

_db = None
_ollama = None
_backend = None
_ingester = None
_initialized = False


def reset() -> None:
    """Reset all singletons so the next call re-initializes with fresh config."""
    global _db, _ollama, _backend, _ingester, _initialized
    _db = _ollama = _backend = _ingester = None
    _initialized = False


def _ensure_initialized():
    global _db, _ollama, _backend, _ingester, _initialized
    if _initialized:
        return

    cfg = get_config()
    if cfg is None or not cfg.enabled:
        raise BookRecommenderDisabledError()

    cfg.validate_or_raise()

    from ._db import RecommenderDB
    from ._ingestion import MetadataIngester
    from ._ollama import OllamaClient
    from ._vector import create_backend

    _db = RecommenderDB(cfg.db_path)
    _ollama = OllamaClient(cfg.ollama_url, cfg.embed_model, cfg.llm_model)
    _backend = create_backend(cfg.vector_backend)
    _ingester = MetadataIngester(_db)
    _initialized = True
    logger.info(
        "Recommender initialized: db=%s vector=%s embed_model=%s ollama=%s",
        cfg.db_path,
        cfg.vector_backend,
        cfg.embed_model,
        cfg.ollama_url,
    )


def _embed_stale_books() -> int:
    cfg = get_config()
    if cfg is None:
        return 0
    stale = _db.get_stale_books(cfg.embed_model)
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
    return count


def _build_embed_text(book: dict) -> str:
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
    liked_book_ids: list[str] | None = None,
    free_text_prompt: str | None = None,
) -> list[dict]:
    cfg = get_config()
    if cfg is None or not cfg.enabled:
        return []

    try:
        _ensure_initialized()
    except BookRecommenderDisabledError:
        return []

    if not liked_book_ids and not free_text_prompt:
        return []

    _rebuild_index_if_needed()

    query_vector = _compute_query_vector(liked_book_ids, free_text_prompt)
    if query_vector is None:
        return []

    raw_results = _backend.search(query_vector, cfg.top_k + len(liked_book_ids or []))
    feedback_scores = _db.get_feedback_scores()

    exclude = set(liked_book_ids or [])
    results = []
    for book_id, score in raw_results:
        if book_id in exclude:
            continue
        fb = feedback_scores.get(book_id, 0)
        adjusted_score = score + (fb * 0.05)
        if adjusted_score < cfg.min_similarity:
            continue
        results.append((book_id, adjusted_score))

    results.sort(key=lambda x: x[1], reverse=True)
    results = results[: cfg.top_k]

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
            rec["explanation"] = _generate_explanation(source_books, free_text_prompt, book)
        output.append(rec)

    return output


def _compute_query_vector(
    liked_book_ids: list[str] | None,
    free_text_prompt: str | None,
) -> list[float] | None:
    import numpy as np

    book_vec = None
    prompt_vec = None

    if liked_book_ids:
        embeddings = [_db.get_embedding(bid) for bid in liked_book_ids]
        valid = [e for e in embeddings if e is not None]
        if valid:
            book_vec = np.mean(valid, axis=0).astype(np.float32)

    if free_text_prompt:
        emb = _ollama.embed(free_text_prompt)
        if emb is not None:
            prompt_vec = np.array(emb, dtype=np.float32)

    if book_vec is not None and prompt_vec is not None:
        merged = 0.6 * book_vec + 0.4 * prompt_vec
        return merged.tolist()
    elif book_vec is not None:
        return book_vec.tolist()
    elif prompt_vec is not None:
        return prompt_vec.tolist()
    return None


def _generate_explanation(
    source_books: list[dict],
    free_text_prompt: str | None,
    rec_book: dict,
) -> str | None:
    try:
        from ._explanations import explain_prompt_recommendation, explain_recommendation

        if source_books:
            return explain_recommendation(_ollama, source_books, rec_book)
        if free_text_prompt:
            return explain_prompt_recommendation(_ollama, free_text_prompt, rec_book)
    except Exception:
        logger.debug("Explanation generation failed", exc_info=True)
    return None


def ingest(
    isbn: str | None = None,
    title: str | None = None,
    author: str | None = None,
    work_key: str | None = None,
) -> str | None:
    _ensure_initialized()
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


def submit_feedback(
    book_id: str,
    rating: int,
    source_book_ids: list[str] | None = None,
    source_prompt: str | None = None,
) -> None:
    _ensure_initialized()
    _db.add_feedback(book_id, rating, source_book_ids, source_prompt)


def remove_book(book_id: str) -> bool:
    _ensure_initialized()
    return _db.delete_book(book_id)

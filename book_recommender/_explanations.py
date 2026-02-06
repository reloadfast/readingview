"""Optional LLM-based explanation generation for recommendations."""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def explain_recommendation(
    ollama,
    source_books: list[dict[str, Any]],
    rec_book: dict[str, Any],
    timeout: int = 30,
) -> Optional[str]:
    """Generate a short explanation for why a book was recommended based on liked books."""
    try:
        source_titles = ", ".join(b["title"] for b in source_books)
        prompt = (
            f"In 1-2 sentences, explain why someone who liked '{source_titles}' "
            f"might enjoy '{rec_book['title']}' by {', '.join(rec_book.get('authors', []))}. "
            f"Be specific about shared themes or style. Do not use bullet points."
        )
        return ollama.generate(prompt, timeout=timeout)
    except Exception:
        logger.debug("Explanation generation failed", exc_info=True)
        return None


def explain_prompt_recommendation(
    ollama,
    prompt_text: str,
    rec_book: dict[str, Any],
    timeout: int = 30,
) -> Optional[str]:
    """Generate a short explanation for why a book matches a free-text prompt."""
    try:
        prompt = (
            f"In 1-2 sentences, explain why '{rec_book['title']}' by "
            f"{', '.join(rec_book.get('authors', []))} is a good match for someone "
            f"looking for: '{prompt_text}'. Be specific. Do not use bullet points."
        )
        return ollama.generate(prompt, timeout=timeout)
    except Exception:
        logger.debug("Prompt explanation generation failed", exc_info=True)
        return None

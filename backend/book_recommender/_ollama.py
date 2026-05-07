"""Ollama HTTP client for embeddings and text generation."""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT_EMBED = 60.0
_TIMEOUT_GENERATE = 30.0
_TIMEOUT_HEALTH = 5.0


class OllamaClient:
    """HTTP client for the Ollama API (embeddings + generation)."""

    def __init__(self, base_url: str, embed_model: str, llm_model: str):
        self.base_url = base_url.rstrip("/")
        self.embed_model = embed_model
        self.llm_model = llm_model

    def is_available(self) -> bool:
        try:
            r = httpx.get(f"{self.base_url}/api/tags", timeout=_TIMEOUT_HEALTH)
            return r.status_code == 200
        except httpx.RequestError:
            return False

    def embed(self, text: str) -> Optional[list[float]]:
        try:
            r = httpx.post(
                f"{self.base_url}/api/embed",
                json={"model": self.embed_model, "input": text},
                timeout=_TIMEOUT_EMBED,
            )
            r.raise_for_status()
            data = r.json()
            if "embeddings" in data and data["embeddings"]:
                return data["embeddings"][0]
            if "embedding" in data:
                return data["embedding"]
            logger.warning("Unexpected embed response shape: %s", list(data.keys()))
            return None
        except httpx.RequestError as e:
            logger.error("Ollama embed failed: %s", e)
            return None

    def generate(self, prompt: str, timeout: float = _TIMEOUT_GENERATE) -> Optional[str]:
        try:
            r = httpx.post(
                f"{self.base_url}/api/generate",
                json={"model": self.llm_model, "prompt": prompt, "stream": False},
                timeout=timeout,
            )
            r.raise_for_status()
            return r.json().get("response")
        except httpx.RequestError as e:
            logger.error("Ollama generate failed: %s", e)
            return None

"""Ollama HTTP client for embeddings and text generation."""

import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class OllamaClient:
    """HTTP client for the Ollama API (embeddings + generation)."""

    def __init__(self, base_url: str, embed_model: str, llm_model: str):
        self.base_url = base_url.rstrip("/")
        self.embed_model = embed_model
        self.llm_model = llm_model
        self.session = requests.Session()

    def is_available(self) -> bool:
        """Check if Ollama is reachable."""
        try:
            resp = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def embed(self, text: str) -> Optional[list[float]]:
        """Generate an embedding for the given text. Returns None on failure."""
        try:
            resp = self.session.post(
                f"{self.base_url}/api/embed",
                json={"model": self.embed_model, "input": text},
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
            # New API shape: {"embeddings": [[...]]}
            if "embeddings" in data and data["embeddings"]:
                return data["embeddings"][0]
            # Old API shape: {"embedding": [...]}
            if "embedding" in data:
                return data["embedding"]
            logger.warning("Unexpected embed response shape: %s", list(data.keys()))
            return None
        except requests.RequestException as e:
            logger.error("Ollama embed failed: %s", e)
            return None

    def generate(self, prompt: str, timeout: int = 30) -> Optional[str]:
        """Generate text from the LLM. Returns None on failure."""
        try:
            resp = self.session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.llm_model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response")
        except requests.RequestException as e:
            logger.error("Ollama generate failed: %s", e)
            return None

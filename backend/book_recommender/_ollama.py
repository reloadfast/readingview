"""Ollama HTTP client for embeddings and text generation."""

import logging

import httpx

from ._exceptions import BookRecommenderProviderError

logger = logging.getLogger(__name__)

_TIMEOUT_EMBED = 60.0
_TIMEOUT_GENERATE = 30.0
_TIMEOUT_HEALTH = 5.0


class OllamaClient:
    """HTTP client for the Ollama API (embeddings + generation)."""

    def __init__(
        self,
        base_url: str,
        embed_model: str,
        llm_model: str,
        provider_type: str = "ollama",
        api_key: str | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.embed_model = embed_model
        self.llm_model = llm_model
        self.provider_type = provider_type
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    def is_available(self) -> bool:
        try:
            path = "/v1/models" if self.provider_type == "openai" else "/api/tags"
            r = httpx.get(f"{self.base_url}{path}", headers=self.headers, timeout=_TIMEOUT_HEALTH)
            return r.status_code == 200
        except httpx.RequestError:
            return False

    def embed(self, text: str) -> list[float] | None:
        try:
            if self.provider_type == "openai":
                r = httpx.post(
                    f"{self.base_url}/v1/embeddings",
                    json={"model": self.embed_model, "input": text},
                    headers=self.headers,
                    timeout=_TIMEOUT_EMBED,
                )
            else:
                r = httpx.post(
                    f"{self.base_url}/api/embed",
                    json={"model": self.embed_model, "input": text},
                    headers=self.headers,
                    timeout=_TIMEOUT_EMBED,
                )
            r.raise_for_status()
            data = r.json()
            if self.provider_type == "openai":
                embeddings = data.get("data", [])
                if embeddings and embeddings[0].get("embedding"):
                    return embeddings[0]["embedding"]
            if "embeddings" in data and data["embeddings"]:
                return data["embeddings"][0]
            if "embedding" in data:
                return data["embedding"]
            logger.warning("Unexpected embed response shape: %s", list(data.keys()))
            return None
        except httpx.HTTPError as exc:
            raise BookRecommenderProviderError(f"Embedding request failed: {exc}") from exc

    def generate(self, prompt: str, timeout: float = _TIMEOUT_GENERATE) -> str | None:
        try:
            if self.provider_type == "openai":
                r = httpx.post(
                    f"{self.base_url}/v1/chat/completions",
                    json={
                        "model": self.llm_model,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                    headers=self.headers,
                    timeout=timeout,
                )
            else:
                r = httpx.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.llm_model, "prompt": prompt, "stream": False},
                    headers=self.headers,
                    timeout=timeout,
                )
            r.raise_for_status()
            if self.provider_type == "openai":
                choices = r.json().get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content")
            return r.json().get("response")
        except httpx.HTTPError as e:
            logger.error("Text generation failed: %s", e)
            return None

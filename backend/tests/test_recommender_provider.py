"""Unit tests for the recommender's Ollama and OpenAI-compatible providers."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from book_recommender._config import RecommenderConfig
from book_recommender._exceptions import BookRecommenderProviderError
from book_recommender._ollama import OllamaClient

pytestmark = pytest.mark.unit


def _response(payload: dict) -> MagicMock:
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = payload
    return response


def test_openai_compatible_embeddings_use_v1_endpoint_and_bearer_key():
    client = OllamaClient(
        "http://models.test/",
        "nomic-embed-text",
        "chat-model",
        provider_type="openai",
        api_key="test-key",
    )

    with patch(
        "book_recommender._ollama.httpx.post",
        return_value=_response(
            {
                "data": [{"embedding": [0.1, 0.2]}],
            }
        ),
    ) as post:
        assert client.embed("space opera") == [0.1, 0.2]

    post.assert_called_once_with(
        "http://models.test/v1/embeddings",
        json={"model": "nomic-embed-text", "input": "space opera"},
        headers={"Authorization": "Bearer test-key"},
        timeout=60.0,
    )


def test_embedding_http_errors_are_reported_to_the_api():
    request = httpx.Request("POST", "http://models.test/v1/embeddings")
    response = httpx.Response(404, request=request)
    client = OllamaClient(
        "http://models.test",
        "embed",
        "chat",
        provider_type="openai",
        api_key="key",
    )

    with patch("book_recommender._ollama.httpx.post", return_value=response):
        with pytest.raises(BookRecommenderProviderError, match="Embedding request failed"):
            client.embed("space opera")


def test_openai_provider_requires_an_api_key():
    config = RecommenderConfig(
        enabled=True,
        db_path="recommender.db",
        embed_model="nomic-embed-text",
        llm_model="chat-model",
        ollama_url="http://models.test",
        llm_type="openai",
    )

    assert config.validate() == (False, "llm_api_key is required for the selected LLM type")

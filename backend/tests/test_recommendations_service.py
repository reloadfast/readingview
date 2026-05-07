"""Unit tests for recommendations service helpers."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.recommendations import _db_path_from_url, _settings_hash

pytestmark = pytest.mark.unit


# --- _db_path_from_url ---


def test_db_path_from_url_absolute():
    assert _db_path_from_url("sqlite+aiosqlite:////data/readingview.db") == "/data/readingview.db"


def test_db_path_from_url_relative():
    result = _db_path_from_url("sqlite+aiosqlite:///./readingview.db")
    assert result == "./readingview.db"


def test_db_path_from_url_non_sqlite_passthrough():
    url = "postgresql+asyncpg://user:pass@host/db"
    assert _db_path_from_url(url) == url


# --- _settings_hash ---


def test_settings_hash_none_returns_none_string():
    assert _settings_hash(None) == "none"


def test_settings_hash_deterministic():
    row = MagicMock()
    row.recommender_enabled = False
    row.recommender_vector_backend = "python"
    row.recommender_embed_model = "nomic-embed-text"
    row.llm_model = None
    row.recommender_explanations_enabled = False
    row.llm_endpoint = None
    row.recommender_top_k = 10
    row.recommender_min_similarity = 0.2

    h1 = _settings_hash(row)
    h2 = _settings_hash(row)
    assert h1 == h2
    assert isinstance(h1, str)
    assert len(h1) == 32  # MD5 hex digest


def test_settings_hash_changes_with_field():
    row1 = MagicMock()
    row1.recommender_enabled = False
    row1.recommender_vector_backend = "python"
    row1.recommender_embed_model = "nomic-embed-text"
    row1.llm_model = None
    row1.recommender_explanations_enabled = False
    row1.llm_endpoint = None
    row1.recommender_top_k = 10
    row1.recommender_min_similarity = 0.2

    row2 = MagicMock()
    row2.recommender_enabled = True  # changed
    row2.recommender_vector_backend = "python"
    row2.recommender_embed_model = "nomic-embed-text"
    row2.llm_model = None
    row2.recommender_explanations_enabled = False
    row2.llm_endpoint = None
    row2.recommender_top_k = 10
    row2.recommender_min_similarity = 0.2

    assert _settings_hash(row1) != _settings_hash(row2)


# --- _configure_recommender via get_recommendations ---


async def test_configure_recommender_disabled_path(engine):
    """Verify _configure_recommender runs the disabled path when row is None."""
    import app.services.recommendations as rec_mod

    # Reset cache so _configure_recommender runs fresh
    rec_mod._last_config_hash = None

    from sqlalchemy.ext.asyncio import async_sessionmaker

    factory = async_sessionmaker(engine, expire_on_commit=False)

    with (
        patch("app.services.recommendations.reset_service", create=True),
        patch("book_recommender._config.configure"),
        patch("book_recommender._config.RecommenderConfig"),
        patch("book_recommender.service.reset"),
    ):
        async with factory() as session:
            # No settings row — should configure with enabled=False
            await rec_mod._configure_recommender(session)

    assert rec_mod._last_config_hash == "none"


async def test_configure_recommender_skips_when_hash_unchanged(engine):
    """When hash matches, _configure_recommender returns early without reconfiguring."""
    import app.services.recommendations as rec_mod

    rec_mod._last_config_hash = "none"  # pre-set to match None settings

    from sqlalchemy.ext.asyncio import async_sessionmaker

    factory = async_sessionmaker(engine, expire_on_commit=False)

    called = []

    with patch("book_recommender._config.configure", side_effect=lambda *a, **kw: called.append(1)):
        async with factory() as session:
            await rec_mod._configure_recommender(session)

    assert called == []  # should have returned early


async def test_get_status_disabled(engine):
    import app.services.recommendations as rec_mod

    rec_mod._last_config_hash = None  # reset

    from sqlalchemy.ext.asyncio import async_sessionmaker

    factory = async_sessionmaker(engine, expire_on_commit=False)

    with (
        patch("book_recommender.service.reset"),
        patch("book_recommender._config.configure"),
        patch("book_recommender._config.RecommenderConfig"),
        patch("book_recommender._config.get_config", return_value=None),
    ):
        async with factory() as session:
            status = await rec_mod.get_status(session)

    assert status["enabled"] is False
    assert status["model"] is None

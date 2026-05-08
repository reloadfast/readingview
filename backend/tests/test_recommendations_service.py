"""Unit tests for recommendations service helpers."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.models.settings import Settings
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
    from sqlalchemy.ext.asyncio import async_sessionmaker

    factory = async_sessionmaker(engine, expire_on_commit=False)

    with (
        patch("book_recommender._config.configure") as mock_configure,
        patch("book_recommender._config.RecommenderConfig"),
        patch("book_recommender.service.reset"),
    ):
        async with factory() as session:
            # No settings row — stored_hash is None, current_hash is "none" → reconfigure
            await rec_mod._configure_recommender(session)

    mock_configure.assert_called_once()


async def test_configure_recommender_skips_when_hash_unchanged(engine):
    """When DB hash matches current settings, _configure_recommender returns early."""
    import app.services.recommendations as rec_mod
    from sqlalchemy.ext.asyncio import async_sessionmaker

    factory = async_sessionmaker(engine, expire_on_commit=False)

    # Insert settings row and pre-populate recommender_config_hash with the current hash
    async with factory() as session:
        async with session.begin():
            await session.execute(sqlite_insert(Settings).values(id=1))
        row = await session.get(Settings, 1)
        row.recommender_config_hash = _settings_hash(row)
        await session.commit()

    called = []

    with patch("book_recommender._config.configure", side_effect=lambda *a, **kw: called.append(1)):
        async with factory() as session:
            await rec_mod._configure_recommender(session)

    assert called == []  # hash unchanged → early return


async def test_configure_recommender_redetects_after_settings_change(engine):
    """After settings change, the next call must reconfigure — not return stale results.

    This is the regression guard for issue #64: all workers read the persisted
    recommender_config_hash from the DB, so a hash mismatch is visible to every
    process, not just the one that handled the PATCH.
    """
    import app.services.recommendations as rec_mod
    from sqlalchemy.ext.asyncio import async_sessionmaker

    factory = async_sessionmaker(engine, expire_on_commit=False)

    # Initial state: settings row with hash matching current field values
    async with factory() as session:
        async with session.begin():
            await session.execute(sqlite_insert(Settings).values(id=1))
        row = await session.get(Settings, 1)
        row.recommender_config_hash = _settings_hash(row)
        await session.commit()

    # Simulate a settings change (toggle recommender_enabled) from another worker
    async with factory() as session:
        async with session.begin():
            row = await session.get(Settings, 1)
            row.recommender_enabled = True  # hash will now differ from stored value

    configure_calls = []

    with (
        patch("book_recommender.service.reset"),
        patch("book_recommender._config.configure", side_effect=lambda *a, **kw: configure_calls.append(1)),
        patch("book_recommender._config.RecommenderConfig"),
        patch("app.services.recommendations.app_settings") as mock_settings,
    ):
        mock_settings.DATABASE_URL = "sqlite+aiosqlite:////tmp/test.db"
        async with factory() as session:
            await rec_mod._configure_recommender(session)

    assert configure_calls, "configure must be called when DB hash is stale after settings change"


async def test_get_status_disabled(engine):
    import app.services.recommendations as rec_mod
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

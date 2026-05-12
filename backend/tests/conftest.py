import asyncio
import os
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import get_db
from app.main import app

ABS_URL = "http://abs.test"
ABS_TOKEN = "test-abs-token"

_ALEMBIC_INI = Path(__file__).parent.parent / "alembic.ini"


def _run_migrations(db_url: str) -> None:
    cfg = Config(str(_ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")


@pytest.fixture
async def engine(tmp_path):
    db_file = tmp_path / "test.db"
    db_url = f"sqlite+aiosqlite:///{db_file}"
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _run_migrations, db_url)
    e = create_async_engine(db_url)
    yield e
    await e.dispose()


@pytest.fixture
async def client(engine):
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _override():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

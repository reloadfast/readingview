from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings

_url = make_url(settings.DATABASE_URL)
if _url.drivername.startswith("sqlite"):
    _db_path = _url.database
    if _db_path and _db_path != ":memory:":
        Path(_db_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(settings.DATABASE_URL)
_AsyncSession = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _AsyncSession() as session:
        yield session

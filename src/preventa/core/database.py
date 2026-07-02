import re
from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from preventa.core.config import get_settings


def _async_url(url: str) -> str:
    """Ensure an async driver URL.

    The Neon/Vercel integration injects a sync ``postgres://`` DSN; the async
    engine needs ``postgresql+asyncpg://``. A URL that already names a driver
    (``postgresql+...``) is left untouched.
    """
    if url.startswith("postgresql+"):
        return url
    return re.sub(r"^postgres(?:ql)?://", "postgresql+asyncpg://", url)


@lru_cache(maxsize=1)
def _engine() -> AsyncEngine:
    # Created lazily so importing this module never opens a connection or fails
    # on a misconfigured URL; only ORM/RAG routes that request a session build it.
    return create_async_engine(_async_url(get_settings().database_url), pool_pre_ping=True)


@lru_cache(maxsize=1)
def _session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(_engine(), expire_on_commit=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    factory = _session_factory()
    async with factory() as session:
        yield session

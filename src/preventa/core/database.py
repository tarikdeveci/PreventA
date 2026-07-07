import re
from collections.abc import AsyncIterator
from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from preventa.core.config import get_settings

# libpq query params that asyncpg rejects as connect() kwargs. asyncpg does its
# own SCRAM channel binding and takes SSL via a dedicated ``ssl`` arg, so Neon's
# ``channel_binding``/``sslmode`` must be dropped from the URL and translated
# into connect_args (see ``async_connect_args``).
_ASYNCPG_INCOMPATIBLE_PARAMS = {"channel_binding", "sslmode"}


def _strip_asyncpg_incompatible_params(url: str) -> str:
    parts = urlsplit(url)
    if not parts.query:
        return url
    kept = [(k, v) for k, v in parse_qsl(parts.query) if k not in _ASYNCPG_INCOMPATIBLE_PARAMS]
    return urlunsplit(parts._replace(query=urlencode(kept)))


def _async_url(url: str) -> str:
    """Ensure an async driver URL.

    The Neon/Vercel integration injects a sync ``postgres://`` DSN; the async
    engine needs ``postgresql+asyncpg://``. A URL that already names a driver
    (``postgresql+...``) is left untouched. Neon appends ``sslmode`` and
    ``channel_binding`` which asyncpg does not accept as kwargs, so they are
    stripped here; SSL is re-applied via :func:`async_connect_args`.
    """
    if not url.startswith("postgresql+"):
        url = re.sub(r"^postgres(?:ql)?://", "postgresql+asyncpg://", url)
    if "+asyncpg://" in url:
        url = _strip_asyncpg_incompatible_params(url)
    return url


def async_connect_args(url: str) -> dict[str, object]:
    """asyncpg connect_args derived from the original URL's ``sslmode``.

    Neon requires TLS (``sslmode=require``); asyncpg takes this as ``ssl=True``
    (full verification against the server cert), not a URL query param. Local
    dev/test DSNs without ``sslmode`` (or ``disable``) connect without SSL.
    """
    query = dict(parse_qsl(urlsplit(url).query))
    sslmode = query.get("sslmode")
    if sslmode and sslmode != "disable":
        return {"ssl": True}
    return {}


@lru_cache(maxsize=1)
def _engine() -> AsyncEngine:
    # Created lazily so importing this module never opens a connection or fails
    # on a misconfigured URL; only ORM/RAG routes that request a session build it.
    url = get_settings().database_url
    return create_async_engine(
        _async_url(url),
        pool_pre_ping=True,
        connect_args=async_connect_args(url),
    )


@lru_cache(maxsize=1)
def _session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(_engine(), expire_on_commit=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    factory = _session_factory()
    async with factory() as session:
        yield session

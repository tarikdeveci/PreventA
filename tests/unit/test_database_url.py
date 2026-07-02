"""The async engine URL must use an async driver regardless of what's injected."""

from __future__ import annotations

from preventa.core.database import _async_url


def test_sync_neon_url_is_upgraded_to_asyncpg() -> None:
    assert _async_url("postgres://u:p@host/db") == "postgresql+asyncpg://u:p@host/db"
    assert _async_url("postgresql://u:p@host/db") == "postgresql+asyncpg://u:p@host/db"


def test_existing_driver_is_preserved() -> None:
    assert _async_url("postgresql+asyncpg://u:p@host/db") == "postgresql+asyncpg://u:p@host/db"


def test_query_string_is_kept() -> None:
    assert (
        _async_url("postgres://u:p@host/db?sslmode=require")
        == "postgresql+asyncpg://u:p@host/db?sslmode=require"
    )

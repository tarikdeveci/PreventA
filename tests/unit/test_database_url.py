"""The async engine URL must use an async driver and be asyncpg-safe.

Neon injects a sync ``postgres://`` DSN with ``sslmode``/``channel_binding``
query params that asyncpg rejects as connect() kwargs; those are stripped from
the URL and SSL is re-applied via ``async_connect_args``.
"""

from __future__ import annotations

from preventa.core.database import _async_url, async_connect_args


def test_sync_neon_url_is_upgraded_to_asyncpg() -> None:
    assert _async_url("postgres://u:p@host/db") == "postgresql+asyncpg://u:p@host/db"
    assert _async_url("postgresql://u:p@host/db") == "postgresql+asyncpg://u:p@host/db"


def test_existing_driver_is_preserved() -> None:
    assert _async_url("postgresql+asyncpg://u:p@host/db") == "postgresql+asyncpg://u:p@host/db"


def test_asyncpg_incompatible_params_are_stripped() -> None:
    # Neon's real DSN shape: both params present.
    assert (
        _async_url("postgres://u:p@host/db?sslmode=require&channel_binding=require")
        == "postgresql+asyncpg://u:p@host/db"
    )
    # channel_binding first (param order must not leave a dangling separator).
    assert (
        _async_url("postgres://u:p@host/db?channel_binding=require&sslmode=require")
        == "postgresql+asyncpg://u:p@host/db"
    )


def test_unrelated_query_params_are_kept() -> None:
    assert (
        _async_url("postgres://u:p@host/db?application_name=preventa")
        == "postgresql+asyncpg://u:p@host/db?application_name=preventa"
    )


def test_connect_args_enable_ssl_for_neon() -> None:
    assert async_connect_args("postgres://u:p@host/db?sslmode=require") == {"ssl": True}
    assert async_connect_args("postgres://u:p@host/db?sslmode=verify-full") == {"ssl": True}


def test_connect_args_no_ssl_for_local() -> None:
    assert async_connect_args("postgres://u:p@localhost/db") == {}
    assert async_connect_args("postgres://u:p@localhost/db?sslmode=disable") == {}

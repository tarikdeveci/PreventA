"""Backend selection for the workspace store (which DSN, if any, is used)."""

from __future__ import annotations

import pytest

from preventa.features.workspace.store import _store_dsn, _sync_dsn, _use_postgres


def test_defaults_to_sqlite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PREVENTA_STORE_DSN", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_URL", raising=False)
    assert _store_dsn() is None
    assert _use_postgres() is False


def test_explicit_dsn_wins_anywhere(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("PREVENTA_STORE_DSN", "postgresql://u:p@host:5432/db")
    assert _store_dsn() == "postgresql://u:p@host:5432/db"
    assert _use_postgres() is True


def test_injected_database_url_used_only_on_vercel(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PREVENTA_STORE_DSN", raising=False)
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@neon-pooler/db?sslmode=require")

    # Locally the injected var must be ignored so dev/tests stay on SQLite.
    monkeypatch.delenv("VERCEL", raising=False)
    assert _store_dsn() is None

    # In the Vercel runtime it is picked up automatically.
    monkeypatch.setenv("VERCEL", "1")
    assert _store_dsn() == "postgres://u:p@neon-pooler/db?sslmode=require"


def test_async_driver_marker_is_stripped_for_psycopg2() -> None:
    assert _sync_dsn("postgresql+asyncpg://u:p@host/db") == "postgresql://u:p@host/db"
    assert _sync_dsn("postgres://u:p@host/db") == "postgres://u:p@host/db"

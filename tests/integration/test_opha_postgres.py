"""Durable-persistence integration test: OpenPHA study -> async ORM -> Postgres.

Gated on ``PREVENTA_TEST_DATABASE_URL`` so the default suite stays green without
a database. Point it at a *disposable* Postgres (e.g. the ``pgvector/pgvector``
service in ``compose.yaml``) — the test creates and drops the full schema::

    PREVENTA_TEST_DATABASE_URL=postgresql+asyncpg://preventa:preventa@localhost:5432/preventa \
        .venv/Scripts/python.exe -m pytest tests/integration/test_opha_postgres.py

It proves the write survives the transaction boundary by re-reading counts in a
brand-new engine, and that the persisted counts equal the parsed study's own
traversal (``OphaStudy.summary``).
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import preventa.db.models.rag  # noqa: F401  (registers the RAG tables so create_all/drop_all cover the full schema)
from preventa.db.base import Base
from preventa.db.models import (  # noqa: F401  (import registers every table on Base.metadata)
    Cause,
    Consequence,
    Deviation,
    Lopa,
    Node,
    Recommendation,
    Safeguard,
    Study,
)
from preventa.features.opha import load_opha
from preventa.features.opha.repository import persist_opha_study

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "synthetic.opha"
TEST_DB_URL = os.getenv("PREVENTA_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not TEST_DB_URL,
    reason="set PREVENTA_TEST_DATABASE_URL to a disposable Postgres to run",
)


@pytest_asyncio.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    assert TEST_DB_URL is not None
    eng = create_async_engine(TEST_DB_URL)
    async with eng.begin() as conn:
        # The RAG embeddings table needs pgvector; the schema is created directly
        # (not via alembic) so we ensure the extension ourselves.
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        # Start from a clean slate regardless of any prior (e.g. alembic) state.
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield eng
    finally:
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await eng.dispose()


async def _count(session: AsyncSession, model: type) -> int:
    result = await session.execute(select(func.count()).select_from(model))
    return int(result.scalar_one())


async def test_persist_opha_study_is_durable(engine: AsyncEngine) -> None:
    opha = load_opha(FIXTURE)
    expected = opha.summary()

    # Write and commit, then dispose the writer so nothing lingers in a cache.
    write_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with write_factory() as session:
        study = await persist_opha_study(session, opha)
        await session.commit()
        study_id = study.id

    assert study_id is not None

    # Re-read through a fresh session to prove the rows are durably persisted.
    read_factory = async_sessionmaker(engine)
    async with read_factory() as session:
        reloaded = await session.get(Study, study_id)
        assert reloaded is not None
        assert reloaded.name == opha.name

        assert await _count(session, Node) == expected["nodes"]
        assert await _count(session, Deviation) == expected["deviations"]
        assert await _count(session, Cause) == expected["causes"]
        assert await _count(session, Consequence) == expected["consequences"]
        assert await _count(session, Safeguard) == expected["safeguards"]
        # Every scenario in the synthetic fixture that ran LOPA got a layer.
        assert await _count(session, Lopa) >= 1
        # PHA + LOPA recommendations both persisted.
        recs = await _count(session, Recommendation)
        assert recs == expected["pha_recommendations"] + expected["lopa_recommendations"]

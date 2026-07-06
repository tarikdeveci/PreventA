"""Prove the hybrid retrieval backbone (pgvector dense + FTS sparse + RRF) works.

Gated on ``PREVENTA_TEST_DATABASE_URL`` (async Postgres with pgvector, e.g. the
compose ``pgvector/pgvector:pg16`` service). Uses the dependency-free
``HashingEmbedder`` so the whole ingest → retrieve → fuse path runs with no model
host or API key — the model provider is the only piece swapped for production.

    PREVENTA_TEST_DATABASE_URL=postgresql+asyncpg://preventa:preventa@localhost:5432/preventa \
        .venv/Scripts/python.exe -m pytest tests/integration/test_rag_retrieval.py
"""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

import preventa.db.models.rag  # noqa: F401  (registers the RAG tables on Base.metadata)
from preventa.db.base import Base
from preventa.features.rag.providers import HashingEmbedder
from preventa.features.rag.repository import CorpusIngestionRepository, HybridRetrievalRepository
from preventa.features.rag.schemas import ChunkInput

TEST_DB_URL = os.getenv("PREVENTA_TEST_DATABASE_URL")
CORPUS = Path(__file__).resolve().parents[1] / "fixtures" / "safety_corpus.json"

pytestmark = pytest.mark.skipif(
    not TEST_DB_URL,
    reason="set PREVENTA_TEST_DATABASE_URL to a pgvector Postgres to run",
)


@pytest_asyncio.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    assert TEST_DB_URL is not None
    eng = create_async_engine(TEST_DB_URL)
    async with eng.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield eng
    finally:
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await eng.dispose()


async def _ingest_corpus(engine: AsyncEngine) -> int:
    embedder = HashingEmbedder()
    payload = json.loads(CORPUS.read_text(encoding="utf-8"))
    factory = async_sessionmaker(engine, expire_on_commit=False)
    total = 0
    async with factory() as session:
        repo = CorpusIngestionRepository(session, embedder)
        for doc in payload["documents"]:
            result = await repo.ingest(
                title=doc["title"],
                source_type=doc["source_type"],
                source_ref=doc["source_ref"],
                version=doc.get("version"),
                chunks=[ChunkInput(**c) for c in doc["chunks"]],
            )
            total += result.chunks_indexed
    return total


async def test_hybrid_retrieval_grounds_a_pump_no_flow_query(engine: AsyncEngine) -> None:
    indexed = await _ingest_corpus(engine)
    assert indexed >= 7

    embedder = HashingEmbedder()
    query = "Centrifugal pump no flow suction valve closed loss of feed"
    embedding = await embedder.embed(query)

    factory = async_sessionmaker(engine)
    async with factory() as session:
        results = await HybridRetrievalRepository(session).search(
            query=query, embedding=embedding,
            dense_limit=30, sparse_limit=30, fused_limit=12, rrf_k=60,
        )

    assert results, "hybrid search returned nothing"
    top = results[0]
    # The most relevant chunk for this query is the pump 'No flow' pattern.
    assert "pump" in top.content.lower()
    assert "no flow" in top.content.lower()
    # Fusion ran: the top hit is ranked by at least one retrieval arm and scored.
    assert (top.dense_rank is not None) or (top.sparse_rank is not None)
    assert top.fused_score > 0.0
    assert top.source_ref == "generic/pump-deviations"


async def test_retrieval_is_query_specific(engine: AsyncEngine) -> None:
    await _ingest_corpus(engine)
    embedder = HashingEmbedder()
    factory = async_sessionmaker(engine)

    async with factory() as session:
        repo = HybridRetrievalRepository(session)
        pressure = await repo.search(
            query="pressure vessel overpressure blocked outlet PSV relief rupture",
            embedding=await embedder.embed(
                "pressure vessel overpressure blocked outlet PSV relief rupture"
            ),
            dense_limit=30, sparse_limit=30, fused_limit=12, rrf_k=60,
        )

    # A different deviation retrieves the overpressure knowledge, not the pump one.
    assert pressure
    assert pressure[0].source_ref == "generic/vessel-overpressure"

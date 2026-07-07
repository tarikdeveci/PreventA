"""Prove REAL semantic retrieval with self-hosted open embeddings (no API key).

Doubly gated: needs ``PREVENTA_TEST_DATABASE_URL`` (pgvector Postgres) and
``PREVENTA_OLLAMA_URL`` (a running Ollama with an embedding model). The queries
deliberately avoid the corpus's wording, so a pass demonstrates semantic (dense
vector) matching — not keyword overlap — using an open model that runs on our
own hardware.

    PREVENTA_TEST_DATABASE_URL=postgresql+asyncpg://preventa:preventa@localhost:5432/preventa \
    PREVENTA_OLLAMA_URL=http://localhost:11434 \
        .venv/Scripts/python.exe -m pytest tests/integration/test_rag_semantic_ollama.py
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
from preventa.features.rag.providers import OllamaClient
from preventa.features.rag.repository import CorpusIngestionRepository, HybridRetrievalRepository
from preventa.features.rag.schemas import ChunkInput

TEST_DB_URL = os.getenv("PREVENTA_TEST_DATABASE_URL")
OLLAMA_URL = os.getenv("PREVENTA_OLLAMA_URL")
EMBED_MODEL = os.getenv("PREVENTA_OLLAMA_EMBED_MODEL", "nomic-embed-text")
CORPUS = Path(__file__).resolve().parents[1] / "fixtures" / "safety_corpus.json"

pytestmark = pytest.mark.skipif(
    not (TEST_DB_URL and OLLAMA_URL),
    reason="set PREVENTA_TEST_DATABASE_URL and PREVENTA_OLLAMA_URL to run",
)

# Queries phrased WITHOUT the corpus's exact terms -> only semantics can match.
SEMANTIC_QUERIES = [
    ("loss of cooling makes the exothermic reaction accelerate uncontrollably",
     "generic/reactor-runaway"),
    ("the pump stops delivering because its inlet line is blocked",
     "generic/pump-deviations"),
    ("liquid spilled over the top of the tank into the containment area",
     "generic/tank-overfill"),
]


def _client() -> OllamaClient:
    assert OLLAMA_URL is not None
    return OllamaClient(base_url=OLLAMA_URL, chat_model="unused", embed_model=EMBED_MODEL)


@pytest_asyncio.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    assert TEST_DB_URL is not None
    eng = create_async_engine(TEST_DB_URL)
    async with eng.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(eng, expire_on_commit=False)
    client = _client()
    payload = json.loads(CORPUS.read_text(encoding="utf-8"))
    async with factory() as session:
        repo = CorpusIngestionRepository(session, client)
        for doc in payload["documents"]:
            await repo.ingest(
                title=doc["title"], source_type=doc["source_type"],
                source_ref=doc["source_ref"], version=doc.get("version"),
                chunks=[ChunkInput(**c) for c in doc["chunks"]],
            )
    try:
        yield eng
    finally:
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await eng.dispose()


async def test_open_embeddings_ground_paraphrased_queries(engine: AsyncEngine) -> None:
    client = _client()
    factory = async_sessionmaker(engine)
    async with factory() as session:
        retriever = HybridRetrievalRepository(session)
        for query, expected in SEMANTIC_QUERIES:
            embedding = await client.embed(query)
            results = await retriever.search(
                query=query, embedding=embedding,
                dense_limit=30, sparse_limit=30, fused_limit=3, rrf_k=60,
            )
            assert results, f"no retrieval for: {query}"
            assert results[0].source_ref == expected, (
                f"{query!r} -> {results[0].source_ref} (expected {expected})"
            )
            # These paraphrases share no keywords, so the dense arm must carry it.
            assert results[0].dense_rank is not None

"""Ingest a knowledge corpus into the RAG store (knowledge_documents/chunks).

Uses the configured embedder (``get_embedder`` — keyless HashingEmbedder by
default), so it works with no model host and stays consistent with query-time
embeddings. Creates the two knowledge tables and the pgvector extension if
missing, then ingests each document.

Run against the target database via ``DATABASE_URL`` (or the local default)::

    DATABASE_URL=postgresql+asyncpg://user:pass@host/db \
        .venv/Scripts/python.exe scripts/ingest_safety_corpus.py [corpus.json]

Idempotent per source_ref: a document whose ``source_ref`` already exists is
skipped (the ``source_ref`` column is unique).
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from preventa.api.dependencies import get_embedder
from preventa.core.config import get_settings
from preventa.core.database import _async_url
from preventa.db.models.rag import KnowledgeChunk, KnowledgeDocument
from preventa.features.rag.repository import CorpusIngestionRepository
from preventa.features.rag.schemas import ChunkInput

DEFAULT_CORPUS = (
    Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "safety_corpus.json"
)


async def main(payload: dict[str, Any]) -> None:
    settings = get_settings()
    embedder = get_embedder(settings)
    engine = create_async_engine(_async_url(settings.database_url))

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(
            lambda sync_conn: KnowledgeDocument.metadata.create_all(
                sync_conn,
                tables=[KnowledgeDocument.__table__, KnowledgeChunk.__table__],
            )
        )

    factory = async_sessionmaker(engine, expire_on_commit=False)
    ingested, skipped = 0, 0

    for doc in payload["documents"]:
        async with factory() as session:
            exists = await session.execute(
                select(KnowledgeDocument.id).where(
                    KnowledgeDocument.source_ref == doc["source_ref"]
                )
            )
            if exists.first() is not None:
                skipped += 1
                print(f"skip (exists): {doc['source_ref']}")
                continue
            repo = CorpusIngestionRepository(session, embedder)
            result = await repo.ingest(
                title=doc["title"],
                source_type=doc["source_type"],
                source_ref=doc["source_ref"],
                version=doc.get("version"),
                chunks=[ChunkInput(**c) for c in doc["chunks"]],
            )
            ingested += result.chunks_indexed
            print(f"ingested: {doc['source_ref']} ({result.chunks_indexed} chunks)")

    await engine.dispose()
    print(
        f"\nDone. embedder={settings.rag_embedder} "
        f"chunks_ingested={ingested} docs_skipped={skipped}"
    )


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CORPUS
    corpus = json.loads(path.read_text(encoding="utf-8"))
    asyncio.run(main(corpus))

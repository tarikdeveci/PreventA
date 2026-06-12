from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from preventa.db.models.rag import KnowledgeChunk, KnowledgeDocument, SourceType
from preventa.features.rag.fusion import reciprocal_rank_fusion
from preventa.features.rag.providers import Embedder
from preventa.features.rag.schemas import (
    ChunkInput,
    CorpusIngestResponse,
    DeviationAssistRequest,
    RetrievedChunk,
)


class HybridRetrievalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def search(
        self,
        *,
        query: str,
        embedding: list[float],
        dense_limit: int,
        sparse_limit: int,
        fused_limit: int,
        rrf_k: int,
    ) -> list[RetrievedChunk]:
        dense_rows = (
            await self._session.execute(self._dense_query(embedding, dense_limit))
        ).scalars().all()
        sparse_rows = (
            await self._session.execute(self._sparse_query(query, sparse_limit))
        ).scalars().all()

        dense_ids = [row.id for row in dense_rows]
        sparse_ids = [row.id for row in sparse_rows]
        fused = reciprocal_rank_fusion([dense_ids, sparse_ids], k=rrf_k)[:fused_limit]

        chunks_by_id = {row.id: row for row in [*dense_rows, *sparse_rows]}
        dense_ranks = {chunk_id: rank for rank, chunk_id in enumerate(dense_ids, start=1)}
        sparse_ranks = {chunk_id: rank for rank, chunk_id in enumerate(sparse_ids, start=1)}

        return [
            self._to_schema(
                chunks_by_id[chunk_id],
                dense_rank=dense_ranks.get(chunk_id),
                sparse_rank=sparse_ranks.get(chunk_id),
                fused_score=score,
            )
            for chunk_id, score in fused
        ]

    @staticmethod
    def _dense_query(embedding: list[float], limit: int) -> Select[tuple[KnowledgeChunk]]:
        return (
            select(KnowledgeChunk)
            .options(selectinload(KnowledgeChunk.document))
            .where(KnowledgeChunk.document.has(is_active=True))
            .order_by(KnowledgeChunk.embedding.cosine_distance(embedding))
            .limit(limit)
        )

    @staticmethod
    def _sparse_query(query: str, limit: int) -> Select[tuple[KnowledgeChunk]]:
        ts_query = func.websearch_to_tsquery("english", query)
        return (
            select(KnowledgeChunk)
            .options(selectinload(KnowledgeChunk.document))
            .where(
                KnowledgeChunk.document.has(is_active=True),
                KnowledgeChunk.content_tsv.op("@@")(ts_query),
            )
            .order_by(func.ts_rank_cd(KnowledgeChunk.content_tsv, ts_query).desc())
            .limit(limit)
        )

    @staticmethod
    def _to_schema(
        chunk: KnowledgeChunk,
        *,
        dense_rank: int | None,
        sparse_rank: int | None,
        fused_score: float,
    ) -> RetrievedChunk:
        return RetrievedChunk(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            source_ref=chunk.document.source_ref,
            section_ref=chunk.section_ref,
            content=chunk.content,
            dense_rank=dense_rank,
            sparse_rank=sparse_rank,
            fused_score=fused_score,
        )


def build_retrieval_query(request: DeviationAssistRequest) -> str:
    fields = (
        request.equipment_type,
        request.design_intent,
        request.parameter,
        request.guideword,
        request.deviation,
    )
    return "\n".join(str(field) for field in fields)


class CorpusIngestionRepository:
    def __init__(self, session: AsyncSession, embedder: Embedder) -> None:
        self._session = session
        self._embedder = embedder

    async def ingest(
        self,
        *,
        title: str,
        source_type: str,
        source_ref: str,
        version: str | None,
        chunks: list[ChunkInput],
    ) -> CorpusIngestResponse:
        document = KnowledgeDocument(
            title=title,
            source_type=SourceType(source_type),
            source_ref=source_ref,
            version=version,
            is_active=True,
        )
        self._session.add(document)
        await self._session.flush()  # populate document.id

        for chunk_input in chunks:
            embedding = await self._embedder.embed(chunk_input.content)
            chunk = KnowledgeChunk(
                document_id=document.id,
                ordinal=chunk_input.ordinal,
                section_ref=chunk_input.section_ref,
                content=chunk_input.content,
                embedding=embedding,
            )
            self._session.add(chunk)

        await self._session.commit()
        return CorpusIngestResponse(
            document_id=document.id,
            chunks_indexed=len(chunks),
            source_ref=source_ref,
        )

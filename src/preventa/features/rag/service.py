from sqlalchemy.ext.asyncio import AsyncSession

from preventa.core.config import Settings
from preventa.db.models.rag import (
    RagSuggestion,
    RetrievalTrace,
    SuggestionStatus,
)
from preventa.features.rag.guardrails import (
    UngroundedSuggestionError,
    require_citations,
)
from preventa.features.rag.prompts import PROMPT_VERSION
from preventa.features.rag.providers import DraftGenerator, Embedder, Reranker
from preventa.features.rag.repository import HybridRetrievalRepository, build_retrieval_query
from preventa.features.rag.schemas import (
    DeviationAssistRequest,
    DeviationAssistResponse,
    GeneratedDraft,
    RetrievedChunk,
)


class DeviationAssistService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        settings: Settings,
        embedder: Embedder,
        generator: DraftGenerator,
        reranker: Reranker,
    ) -> None:
        self._session = session
        self._settings = settings
        self._embedder = embedder
        self._generator = generator
        self._reranker = reranker
        self._retriever = HybridRetrievalRepository(session)

    async def assist(self, request: DeviationAssistRequest) -> DeviationAssistResponse:
        query = build_retrieval_query(request)
        embedding = await self._embedder.embed(query)
        context = await self._retriever.search(
            query=query,
            embedding=embedding,
            dense_limit=self._settings.rag_dense_limit,
            sparse_limit=self._settings.rag_sparse_limit,
            fused_limit=self._settings.rag_fused_limit,
            rrf_k=self._settings.rag_rrf_k,
        )
        context = await self._reranker.rerank(
            query,
            context,
            limit=self._settings.rag_fused_limit,
        )
        draft = await self._generator.generate(request, context)
        suggestion = self._build_suggestion(request, draft)

        try:
            require_citations(
                draft,
                minimum=self._settings.rag_min_citations,
                allowed_chunk_ids={chunk.chunk_id for chunk in context},
            )
            suggestion.status = SuggestionStatus.GENERATED
        except UngroundedSuggestionError as exc:
            suggestion.status = SuggestionStatus.BLOCKED
            suggestion.block_reason = str(exc)

        self._session.add(suggestion)
        await self._session.flush()
        self._session.add_all(self._build_traces(suggestion, draft, context))
        await self._session.commit()

        if suggestion.status is SuggestionStatus.BLOCKED:
            raise UngroundedSuggestionError(
                suggestion.block_reason or "Suggestion failed grounding checks."
            )

        return DeviationAssistResponse(
            suggestion_id=suggestion.id,
            candidates=draft.candidates,
        )

    def _build_suggestion(
        self,
        request: DeviationAssistRequest,
        draft: GeneratedDraft,
    ) -> RagSuggestion:
        return RagSuggestion(
            prompt_version=PROMPT_VERSION,
            model_name=self._generator.model_name,
            request_payload=request.model_dump(mode="json"),
            response_payload=draft.model_dump(mode="json"),
            status=SuggestionStatus.GENERATED,
        )

    @staticmethod
    def _build_traces(
        suggestion: RagSuggestion,
        draft: GeneratedDraft,
        context: list[RetrievedChunk],
    ) -> list[RetrievalTrace]:
        cited_ids = {
            citation.chunk_id
            for candidate in draft.candidates
            for citation in candidate.citations
        }
        return [
            RetrievalTrace(
                suggestion_id=suggestion.id,
                chunk_id=chunk.chunk_id,
                dense_rank=chunk.dense_rank,
                sparse_rank=chunk.sparse_rank,
                fused_score=chunk.fused_score,
                rerank_score=chunk.rerank_score,
                was_cited=chunk.chunk_id in cited_ids,
            )
            for chunk in context
        ]

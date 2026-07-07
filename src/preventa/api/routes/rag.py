from fastapi import APIRouter, HTTPException, status

from preventa.api.auth_dependencies import RagUserDep
from preventa.api.dependencies import (
    CorpusRepositoryDep,
    DeviationAssistServiceDep,
    EmbedderDep,
    SessionDep,
    SettingsDep,
)
from preventa.features.rag.guardrails import UngroundedSuggestionError
from preventa.features.rag.repository import HybridRetrievalRepository, build_retrieval_query
from preventa.features.rag.schemas import (
    CorpusIngestRequest,
    CorpusIngestResponse,
    DeviationAssistRequest,
    DeviationAssistResponse,
    RetrievedChunk,
)

router = APIRouter()


@router.post(
    "/deviation-evidence",
    response_model=list[RetrievedChunk],
    summary="Retrieve cited safety-knowledge evidence for a deviation (no generation)",
)
async def deviation_evidence(
    payload: DeviationAssistRequest,
    session: SessionDep,
    embedder: EmbedderDep,
    settings: SettingsDep,
    _: RagUserDep,
) -> list[RetrievedChunk]:
    """Ground a deviation in the corpus and return the most relevant cited chunks.

    This is the retrieval half of the assistant — it needs no LLM, so it runs
    keyless and in-process. It powers the "grounded evidence" demo that shows the
    hybrid search + citations working before a generation model is provisioned.
    """
    query = build_retrieval_query(payload)
    embedding = await embedder.embed(query)
    return await HybridRetrievalRepository(session).search(
        query=query,
        embedding=embedding,
        dense_limit=settings.rag_dense_limit,
        sparse_limit=settings.rag_sparse_limit,
        fused_limit=settings.rag_fused_limit,
        rrf_k=settings.rag_rrf_k,
    )


@router.post(
    "/deviation-assist",
    response_model=DeviationAssistResponse,
    status_code=status.HTTP_201_CREATED,
)
async def deviation_assist(
    payload: DeviationAssistRequest,
    service: DeviationAssistServiceDep,
    _: RagUserDep,
) -> DeviationAssistResponse:
    try:
        return await service.assist(payload)
    except UngroundedSuggestionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "ungrounded_suggestion",
                "message": str(exc),
            },
        ) from exc


@router.post(
    "/corpus/documents",
    response_model=CorpusIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a document and its text chunks into the knowledge corpus",
)
async def ingest_corpus_document(
    payload: CorpusIngestRequest,
    corpus: CorpusRepositoryDep,
    _: RagUserDep,
) -> CorpusIngestResponse:
    return await corpus.ingest(
        title=payload.title,
        source_type=payload.source_type,
        source_ref=payload.source_ref,
        version=payload.version,
        chunks=payload.chunks,
    )

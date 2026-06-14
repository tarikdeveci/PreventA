from fastapi import APIRouter, HTTPException, status

from preventa.api.auth_dependencies import RagUserDep
from preventa.api.dependencies import CorpusRepositoryDep, DeviationAssistServiceDep
from preventa.features.rag.guardrails import UngroundedSuggestionError
from preventa.features.rag.schemas import (
    CorpusIngestRequest,
    CorpusIngestResponse,
    DeviationAssistRequest,
    DeviationAssistResponse,
)

router = APIRouter()


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

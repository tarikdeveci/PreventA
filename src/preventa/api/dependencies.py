from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from preventa.core.config import Settings, get_settings
from preventa.core.database import get_db_session
from preventa.features.rag.providers import (
    Embedder,
    HashingEmbedder,
    OllamaClient,
    PassthroughReranker,
)
from preventa.features.rag.repository import CorpusIngestionRepository
from preventa.features.rag.service import DeviationAssistService

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_embedder(settings: SettingsDep) -> Embedder:
    """Select the embedding backend.

    Defaults to the dependency-free ``HashingEmbedder`` so retrieval works with
    no model host or API key (including on serverless). Set ``rag_embedder`` to
    ``"ollama"`` to use a self-hosted open model for higher-quality semantics.
    """
    if settings.rag_embedder == "ollama":
        return OllamaClient(
            base_url=settings.ollama_base_url,
            chat_model=settings.ollama_chat_model,
            embed_model=settings.ollama_embed_model,
        )
    return HashingEmbedder()


EmbedderDep = Annotated[Embedder, Depends(get_embedder)]


def get_deviation_assist_service(
    session: SessionDep,
    settings: SettingsDep,
) -> DeviationAssistService:
    ollama = OllamaClient(
        base_url=settings.ollama_base_url,
        chat_model=settings.ollama_chat_model,
        embed_model=settings.ollama_embed_model,
    )
    return DeviationAssistService(
        session=session,
        settings=settings,
        embedder=ollama,
        generator=ollama,
        reranker=PassthroughReranker(),
    )


def get_corpus_repository(
    session: SessionDep,
    embedder: EmbedderDep,
) -> CorpusIngestionRepository:
    # Ingestion must use the same embedder as querying so the vectors are
    # comparable, hence the shared ``get_embedder`` factory.
    return CorpusIngestionRepository(session=session, embedder=embedder)


DeviationAssistServiceDep = Annotated[
    DeviationAssistService,
    Depends(get_deviation_assist_service),
]

CorpusRepositoryDep = Annotated[
    CorpusIngestionRepository,
    Depends(get_corpus_repository),
]

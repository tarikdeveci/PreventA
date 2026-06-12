from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from preventa.core.config import Settings, get_settings
from preventa.core.database import get_db_session
from preventa.features.rag.providers import OllamaClient, PassthroughReranker
from preventa.features.rag.repository import CorpusIngestionRepository
from preventa.features.rag.service import DeviationAssistService

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


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
    settings: SettingsDep,
) -> CorpusIngestionRepository:
    ollama = OllamaClient(
        base_url=settings.ollama_base_url,
        chat_model=settings.ollama_chat_model,
        embed_model=settings.ollama_embed_model,
    )
    return CorpusIngestionRepository(session=session, embedder=ollama)


DeviationAssistServiceDep = Annotated[
    DeviationAssistService,
    Depends(get_deviation_assist_service),
]

CorpusRepositoryDep = Annotated[
    CorpusIngestionRepository,
    Depends(get_corpus_repository),
]

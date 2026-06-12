from enum import StrEnum
from typing import Any
from uuid import UUID

from pgvector.sqlalchemy import Vector  # type: ignore[import-untyped]
from sqlalchemy import Boolean, Computed, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from preventa.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

EMBEDDING_DIMENSIONS = 768


class SourceType(StrEnum):
    STANDARD = "standard"
    PAST_STUDY = "past_study"
    INCIDENT = "incident"
    PUBLIC_EXAMPLE = "public_example"
    SYNTHETIC = "synthetic"


class SuggestionStatus(StrEnum):
    GENERATED = "generated"
    ACCEPTED = "accepted"
    EDITED = "edited"
    REJECTED = "rejected"
    BLOCKED = "blocked"


class KnowledgeDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_documents"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(String(50), index=True, nullable=False)
    source_ref: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    version: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)

    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )


class KnowledgeChunk(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "knowledge_chunks"

    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    section_ref: Mapped[str | None] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_tsv: Mapped[Any] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english', coalesce(content, ''))", persisted=True),
        nullable=False,
    )
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSIONS), nullable=False)
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)

    document: Mapped[KnowledgeDocument] = relationship(back_populates="chunks")


class RagSuggestion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "rag_suggestions"

    worksheet_row_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hazop_worksheet_rows.id", ondelete="SET NULL"),
        index=True,
    )
    prompt_version: Mapped[str] = mapped_column(String(50), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    request_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    response_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[SuggestionStatus] = mapped_column(String(50), index=True, nullable=False)
    block_reason: Mapped[str | None] = mapped_column(Text)
    reviewer_notes: Mapped[str | None] = mapped_column(Text)

    traces: Mapped[list["RetrievalTrace"]] = relationship(
        back_populates="suggestion",
        cascade="all, delete-orphan",
    )


class RetrievalTrace(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "retrieval_traces"

    suggestion_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("rag_suggestions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    chunk_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("knowledge_chunks.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    dense_rank: Mapped[int | None] = mapped_column(Integer)
    sparse_rank: Mapped[int | None] = mapped_column(Integer)
    fused_score: Mapped[float] = mapped_column(Float, nullable=False)
    rerank_score: Mapped[float | None] = mapped_column(Float)
    was_cited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    suggestion: Mapped[RagSuggestion] = relationship(back_populates="traces")

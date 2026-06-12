from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class DeviationAssistRequest(BaseModel):
    study_id: UUID
    node_id: UUID
    equipment_type: str = Field(min_length=1, max_length=100)
    design_intent: str = Field(min_length=1)
    parameter: str = Field(min_length=1, max_length=100)
    guideword: str = Field(min_length=1, max_length=100)
    deviation: str = Field(min_length=1)
    existing_safeguards: list[str] = Field(default_factory=list)


class Citation(BaseModel):
    chunk_id: UUID
    source_ref: str
    section_ref: str | None = None
    excerpt: str = Field(max_length=500)


class Candidate(BaseModel):
    kind: Literal["cause", "consequence", "safeguard"]
    text: str
    citations: list[Citation] = Field(min_length=1)
    confidence: Literal["low", "medium", "high"]


class DeviationAssistResponse(BaseModel):
    suggestion_id: UUID
    candidates: list[Candidate]
    disclaimer: str = (
        "Draft assistance only. A qualified process-safety engineer must review every candidate."
    )


class RetrievedChunk(BaseModel):
    chunk_id: UUID
    document_id: UUID
    source_ref: str
    section_ref: str | None
    content: str
    dense_rank: int | None = None
    sparse_rank: int | None = None
    fused_score: float = 0.0
    rerank_score: float | None = None


class GeneratedDraft(BaseModel):
    candidates: list[Candidate]


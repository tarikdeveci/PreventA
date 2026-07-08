from preventa.db.models.hazop import (
    AnalysisMode,
    Cause,
    Consequence,
    Deviation,
    Lopa,
    LopaModifier,
    Node,
    Recommendation,
    RecommendationKind,
    ReviewStatus,
    RiskMatrix,
    Safeguard,
    Study,
    StudyStatus,
    consequence_recommendation,
    consequence_safeguard,
)
from preventa.db.models.registers import (
    Checklist,
    Drawing,
    Incident,
    Moc,
    ParkingLotItem,
    Scai,
    Session,
    TeamMember,
    session_attendance,
)

__all__ = [
    "AnalysisMode",
    "Cause",
    "Checklist",
    "Consequence",
    "Deviation",
    "Drawing",
    "Incident",
    "Lopa",
    "LopaModifier",
    "Moc",
    "Node",
    "ParkingLotItem",
    "Recommendation",
    "RecommendationKind",
    "ReviewStatus",
    "RiskMatrix",
    "Safeguard",
    "Scai",
    "Session",
    "Study",
    "StudyStatus",
    "TeamMember",
    "consequence_recommendation",
    "consequence_safeguard",
    "session_attendance",
]


def _load_rag_models() -> tuple[type, type, type, type]:
    """Lazy-load RAG models to avoid importing pgvector at module level.

    pgvector requires a native C extension that is not available on Vercel's
    serverless runtime.  By deferring the import, workspace-only routes can
    operate without it.
    """
    from preventa.db.models.rag import (
        KnowledgeChunk,
        KnowledgeDocument,
        RagSuggestion,
        RetrievalTrace,
    )
    return KnowledgeChunk, KnowledgeDocument, RagSuggestion, RetrievalTrace

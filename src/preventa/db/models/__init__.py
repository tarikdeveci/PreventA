from preventa.db.models.hazop import (
    AnalysisMode,
    Cause,
    Consequence,
    Deviation,
    Lopa,
    Node,
    Recommendation,
    RecommendationKind,
    ReviewStatus,
    RiskMatrix,
    Safeguard,
    Study,
    StudyStatus,
    consequence_safeguard,
)

__all__ = [
    "AnalysisMode",
    "Cause",
    "Consequence",
    "Deviation",
    "Lopa",
    "Node",
    "Recommendation",
    "RecommendationKind",
    "ReviewStatus",
    "RiskMatrix",
    "Safeguard",
    "Study",
    "StudyStatus",
    "consequence_safeguard",
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

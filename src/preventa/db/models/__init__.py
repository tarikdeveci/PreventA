from preventa.db.models.hazop import HazopNode, HazopWorksheetRow, Study

__all__ = [
    "HazopNode",
    "HazopWorksheetRow",
    "Study",
]


def _load_rag_models() -> tuple:
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

import logging
import os

from fastapi import APIRouter

from preventa.api.routes import workspace

logger = logging.getLogger(__name__)

api_router = APIRouter()
api_router.include_router(workspace.router, tags=["workspace"])

# RAG routes depend on pgvector which requires a native C extension.
# On Vercel's serverless runtime the extension is unavailable, so we
# guard the import to keep workspace routes functional regardless.
_rag_available = False
try:
    from preventa.api.routes import rag

    api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
    _rag_available = True
except ImportError:
    if not os.getenv("VERCEL"):
        raise  # Re-raise in non-Vercel environments where pgvector should exist
    logger.warning(
        "RAG routes disabled: pgvector native extension not available in this environment."
    )

from fastapi import APIRouter

from preventa.api.routes import rag, workspace

api_router = APIRouter()
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
api_router.include_router(workspace.router, tags=["workspace"])


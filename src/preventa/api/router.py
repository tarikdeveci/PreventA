from fastapi import APIRouter

from preventa.api.routes import rag

api_router = APIRouter()
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])


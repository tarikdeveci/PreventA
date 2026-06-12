from fastapi import APIRouter

from preventa.features.workspace.schemas import ProductStatusResponse, WorkspaceResponse
from preventa.features.workspace.service import get_product_status, get_workspace

router = APIRouter()


@router.get("/workspace", response_model=WorkspaceResponse)
async def workspace() -> WorkspaceResponse:
    return get_workspace()


@router.get("/status", response_model=ProductStatusResponse)
async def product_status() -> ProductStatusResponse:
    return get_product_status()


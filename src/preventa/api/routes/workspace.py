from io import BytesIO

from fastapi import APIRouter, HTTPException, Response, status
from fastapi.responses import StreamingResponse

from preventa.features.workspace.crud_schemas import (
    LopaLayerCreate,
    NodeCreate,
    NodeUpdate,
    RowCreate,
    RowUpdate,
    StudyCreate,
    StudyItem,
)
from preventa.features.workspace.report import build_docx
from preventa.features.workspace.repository import WorkspaceRepository
from preventa.features.workspace.schemas import ProductStatusResponse, WorkspaceResponse
from preventa.features.workspace.service import get_product_status, get_workspace

router = APIRouter()
repository = WorkspaceRepository()


@router.get("/workspace", response_model=WorkspaceResponse)
async def workspace() -> WorkspaceResponse:
    try:
        return get_workspace(repository)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/status", response_model=ProductStatusResponse)
async def product_status() -> ProductStatusResponse:
    return get_product_status()


@router.get("/studies", response_model=list[StudyItem])
async def list_studies() -> list[dict[str, object]]:
    return repository.list_studies()


@router.post("/studies", response_model=StudyItem, status_code=status.HTTP_201_CREATED)
async def create_study(payload: StudyCreate) -> dict[str, object]:
    return repository.create_study(payload)


@router.delete("/studies/{study_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_study(study_id: str) -> Response:
    if not repository.delete_study(study_id):
        raise HTTPException(status_code=404, detail="Study not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/studies/{study_id}/nodes")
async def list_nodes(study_id: str) -> list[dict[str, object]]:
    return repository.list_nodes(study_id)


@router.post("/studies/{study_id}/nodes", status_code=status.HTTP_201_CREATED)
async def create_node(study_id: str, payload: NodeCreate) -> dict[str, object]:
    if repository.get_study(study_id) is None:
        raise HTTPException(status_code=404, detail="Study not found")
    return repository.create_node(study_id, payload)


@router.patch("/nodes/{node_id}")
async def update_node(node_id: str, payload: NodeUpdate) -> dict[str, object]:
    node = repository.update_node(node_id, payload)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.delete("/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(node_id: str) -> Response:
    if not repository.delete_node(node_id):
        raise HTTPException(status_code=404, detail="Node not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/nodes/{node_id}/rows")
async def list_rows(node_id: str) -> list[dict[str, object]]:
    return repository.list_rows(node_id)


@router.post("/nodes/{node_id}/rows", status_code=status.HTTP_201_CREATED)
async def create_row(node_id: str, payload: RowCreate) -> dict[str, object]:
    if repository.get_node(node_id) is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return repository.create_row(node_id, payload)


@router.patch("/rows/{row_id}")
async def update_row(row_id: int, payload: RowUpdate) -> dict[str, object]:
    row = repository.update_row(row_id, payload)
    if row is None:
        raise HTTPException(status_code=404, detail="Row not found")
    return row


@router.delete("/rows/{row_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_row(row_id: int) -> Response:
    if not repository.delete_row(row_id):
        raise HTTPException(status_code=404, detail="Row not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/rows/{row_id}/lopa")
async def list_lopa_layers(row_id: int) -> list[dict[str, object]]:
    return repository.list_lopa_layers(row_id)


@router.post("/rows/{row_id}/lopa", status_code=status.HTTP_201_CREATED)
async def add_lopa_layer(row_id: int, payload: LopaLayerCreate) -> dict[str, object]:
    if repository.get_row(row_id) is None:
        raise HTTPException(status_code=404, detail="HAZOP row not found")
    return repository.add_lopa_layer(row_id, payload)


@router.delete("/lopa/{layer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lopa_layer(layer_id: str) -> Response:
    if not repository.delete_lopa_layer(layer_id):
        raise HTTPException(status_code=404, detail="LOPA layer not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/studies/{study_id}/nodes/{node_id}/report.docx")
async def download_report(study_id: str, node_id: str) -> StreamingResponse:
    study = repository.get_study(study_id)
    node = repository.get_node(node_id)
    if study is None or node is None or node["study_id"] != study_id:
        raise HTTPException(status_code=404, detail="Study or node not found")
    content = build_docx(study, node, repository.list_rows(node_id))
    headers = {"Content-Disposition": 'attachment; filename="preventa-hazop-report.docx"'}
    return StreamingResponse(
        BytesIO(content),
        media_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        headers=headers,
    )

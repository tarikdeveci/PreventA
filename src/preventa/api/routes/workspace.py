import hashlib
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse

from preventa.api.auth_dependencies import (
    CurrentUserDep,
    DeleteUserDep,
    WriteUserDep,
    require_permission,
)
from preventa.core.config import get_settings
from preventa.features.opha import loads_opha
from preventa.features.workspace.crud_schemas import (
    LibraryEntryCreate,
    LopaLayerCreate,
    NodeCreate,
    NodeUpdate,
    RiskMatrixUpdate,
    RowCreate,
    RowUpdate,
    SourceCreate,
    SourceUpdate,
    StudyCreate,
    StudyItem,
    StudyUpdate,
)
from preventa.features.workspace.opha_import import import_opha_study
from preventa.features.workspace.report import build_docx
from preventa.features.workspace.repository import WorkspaceRepository
from preventa.features.workspace.schemas import (
    OphaImportResult,
    ProductStatusResponse,
    WorkspaceResponse,
)
from preventa.features.workspace.service import get_product_status, get_workspace

router = APIRouter(
    dependencies=[Depends(require_permission("workspace:read"))],
)
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
async def create_study(
    payload: StudyCreate,
    _: WriteUserDep,
) -> dict[str, object]:
    return repository.create_study(payload)


@router.post(
    "/studies/import",
    response_model=OphaImportResult,
    status_code=status.HTTP_201_CREATED,
)
async def import_opha(request: Request, _: WriteUserDep) -> OphaImportResult:
    """Import an OpenPHA study. POST the raw ``.opha`` file bytes as the body."""
    settings = get_settings()
    raw = await request.body()
    if len(raw) > settings.import_max_bytes:
        raise HTTPException(
            status_code=413,
            detail="The .opha file is too large to import.",
        )
    # Idempotency: the same file re-uploaded returns the existing import.
    content_hash = hashlib.sha256(raw).hexdigest()
    existing = repository.find_import(content_hash)
    if existing is not None:
        return OphaImportResult(**existing)
    try:
        study = loads_opha(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, RecursionError):
        raise HTTPException(
            status_code=422,
            detail="The file is not a valid OpenPHA (.opha) document.",
        ) from None
    try:
        result = import_opha_study(
            repository, study, max_scenarios=settings.import_max_scenarios
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=413, detail=str(exc)
        ) from exc
    repository.record_import(content_hash, result["study_id"], result)
    return OphaImportResult(**result)


@router.patch("/studies/{study_id}")
async def update_study(study_id: str, payload: StudyUpdate, _: WriteUserDep) -> dict[str, object]:
    study = repository.update_study(study_id, payload)
    if study is None:
        raise HTTPException(status_code=404, detail="Study not found")
    return study


@router.delete("/studies/{study_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_study(study_id: str, _: DeleteUserDep) -> Response:
    if not repository.delete_study(study_id):
        raise HTTPException(status_code=404, detail="Study not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/studies/{study_id}/nodes")
async def list_nodes(study_id: str) -> list[dict[str, object]]:
    return repository.list_nodes(study_id)


@router.post("/studies/{study_id}/nodes", status_code=status.HTTP_201_CREATED)
async def create_node(
    study_id: str,
    payload: NodeCreate,
    _: WriteUserDep,
) -> dict[str, object]:
    if repository.get_study(study_id) is None:
        raise HTTPException(status_code=404, detail="Study not found")
    return repository.create_node(study_id, payload)


@router.patch("/nodes/{node_id}")
async def update_node(
    node_id: str,
    payload: NodeUpdate,
    _: WriteUserDep,
) -> dict[str, object]:
    node = repository.update_node(node_id, payload)
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.delete("/nodes/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_node(node_id: str, _: DeleteUserDep) -> Response:
    if not repository.delete_node(node_id):
        raise HTTPException(status_code=404, detail="Node not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/nodes/{node_id}/rows")
async def list_rows(node_id: str) -> list[dict[str, object]]:
    return repository.list_rows(node_id)


@router.post("/nodes/{node_id}/rows", status_code=status.HTTP_201_CREATED)
async def create_row(
    node_id: str,
    payload: RowCreate,
    _: WriteUserDep,
) -> dict[str, object]:
    if repository.get_node(node_id) is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return repository.create_row(node_id, payload)


@router.patch("/rows/{row_id}")
async def update_row(
    row_id: int,
    payload: RowUpdate,
    _: WriteUserDep,
) -> dict[str, object]:
    row = repository.update_row(row_id, payload)
    if row is None:
        raise HTTPException(status_code=404, detail="Row not found")
    return row


@router.delete("/rows/{row_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_row(row_id: int, _: DeleteUserDep) -> Response:
    if not repository.delete_row(row_id):
        raise HTTPException(status_code=404, detail="Row not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/rows/{row_id}/lopa")
async def list_lopa_layers(row_id: int) -> list[dict[str, object]]:
    return repository.list_lopa_layers(row_id)


@router.post("/rows/{row_id}/lopa", status_code=status.HTTP_201_CREATED)
async def add_lopa_layer(
    row_id: int,
    payload: LopaLayerCreate,
    _: WriteUserDep,
) -> dict[str, object]:
    if repository.get_row(row_id) is None:
        raise HTTPException(status_code=404, detail="HAZOP row not found")
    return repository.add_lopa_layer(row_id, payload)


@router.delete("/lopa/{layer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lopa_layer(layer_id: str, _: DeleteUserDep) -> Response:
    if not repository.delete_lopa_layer(layer_id):
        raise HTTPException(status_code=404, detail="LOPA layer not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/library")
async def list_library(q: str = "") -> list[dict[str, object]]:
    return repository.list_library(q)


@router.post("/library", status_code=status.HTTP_201_CREATED)
async def create_library_entry(payload: LibraryEntryCreate, _: WriteUserDep) -> dict[str, object]:
    return repository.create_library_entry(payload)


@router.delete("/library/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_library_entry(entry_id: str, _: DeleteUserDep) -> Response:
    if not repository.delete_library_entry(entry_id):
        raise HTTPException(status_code=404, detail="Library entry not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/studies/{study_id}/sources")
async def list_sources(study_id: str) -> list[dict[str, object]]:
    return repository.list_sources(study_id)


@router.post("/sources", status_code=status.HTTP_201_CREATED)
async def create_source(payload: SourceCreate, _: WriteUserDep) -> dict[str, object]:
    if repository.get_study(payload.study_id) is None:
        raise HTTPException(status_code=404, detail="Study not found")
    return repository.create_source(payload)


@router.patch("/sources/{source_id}")
async def update_source(
    source_id: str, payload: SourceUpdate, _: WriteUserDep
) -> dict[str, object]:
    source = repository.update_source(source_id, payload)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(source_id: str, _: DeleteUserDep) -> Response:
    if not repository.delete_source(source_id):
        raise HTTPException(status_code=404, detail="Source not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/studies/{study_id}/risk-matrix")
async def get_risk_matrix(study_id: str) -> dict[str, object]:
    if repository.get_study(study_id) is None:
        raise HTTPException(status_code=404, detail="Study not found")
    return repository.get_risk_matrix(study_id)


@router.put("/studies/{study_id}/risk-matrix")
async def update_risk_matrix(
    study_id: str, payload: RiskMatrixUpdate, _: WriteUserDep
) -> dict[str, object]:
    if repository.get_study(study_id) is None:
        raise HTTPException(status_code=404, detail="Study not found")
    try:
        return repository.update_risk_matrix(study_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/audit")
async def list_audit(limit: int = 100) -> list[dict[str, object]]:
    return repository.list_audit(limit)


@router.get("/reports")
async def list_reports() -> list[dict[str, object]]:
    return repository.list_reports()


@router.get("/studies/{study_id}/nodes/{node_id}/report.docx")
async def download_report(study_id: str, node_id: str, user: CurrentUserDep) -> StreamingResponse:
    study = repository.get_study(study_id)
    node = repository.get_node(node_id)
    if study is None or node is None or node["study_id"] != study_id:
        raise HTTPException(status_code=404, detail="Study or node not found")
    content = build_docx(study, node, repository.list_rows(node_id))
    report = repository.record_report(study_id, node_id, user.email)
    headers = {"Content-Disposition": f'attachment; filename="{report["filename"]}"'}
    return StreamingResponse(
        BytesIO(content),
        media_type=("application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        headers=headers,
    )

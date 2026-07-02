from preventa.features.workspace.repository import WorkspaceRepository
from preventa.features.workspace.schemas import (
    DeliveryModule,
    ProductStatusResponse,
    WorkspaceNode,
    WorkspaceResponse,
    WorkspaceRow,
    WorkspaceStudy,
)
from preventa.features.workspace.store import _use_postgres


def get_workspace(repository: WorkspaceRepository) -> WorkspaceResponse:
    studies = repository.list_studies()
    if not studies:
        raise LookupError("No workspace study is available.")

    study_data = next(
        (study for study in studies if study["id"] == "study-reactor-2026"),
        studies[0],
    )
    study_id = str(study_data["id"])
    node_data = repository.list_nodes(study_id)
    active_node = next(
        (node for node in node_data if node["state"] == "active"),
        node_data[0] if node_data else None,
    )

    all_rows = [row for node in node_data for row in repository.list_rows(str(node["id"]))]
    reviewed_scenarios = sum(row["status"] == "İncelendi" for row in all_rows)
    total_scenarios = len(all_rows)
    progress = round(reviewed_scenarios * 100 / total_scenarios) if total_scenarios else 0
    active_rows = repository.list_rows(str(active_node["id"])) if active_node is not None else []

    return WorkspaceResponse(
        source="database",
        study=WorkspaceStudy(
            id=study_id,
            title=str(study_data["title"]),
            client=str(study_data["client"]),
            facility=str(study_data["facility"]),
            progress=progress,
            reviewed_scenarios=reviewed_scenarios,
            total_scenarios=total_scenarios,
        ),
        active_node_id=str(active_node["id"]) if active_node is not None else "",
        nodes=[WorkspaceNode.model_validate(node) for node in node_data],
        rows=[WorkspaceRow.model_validate(row) for row in active_rows],
        suggestions=[],
    )


def get_product_status() -> ProductStatusResponse:
    durable = _use_postgres()
    if durable:
        database_module = DeliveryModule(
            id="database",
            name="Production persistence",
            status="complete",
            progress=100,
            detail=(
                "Durable managed PostgreSQL persistence is active: all studies, "
                "scenarios, LOPA layers, imports and accounts survive restarts."
            ),
        )
    else:
        database_module = DeliveryModule(
            id="database",
            name="Production persistence",
            status="in_progress",
            progress=35,
            detail=(
                "SQLite persistence is volatile on serverless (/tmp is per-instance "
                "and reset on cold start), so imported studies are not durable. Set "
                "PREVENTA_STORE_DSN to a managed PostgreSQL to make storage durable."
            ),
        )
    return ProductStatusResponse(
        release="MVP beta",
        stage="Operational workspace",
        overall_progress=78 if durable else 62,
        api_connected=True,
        persistence="postgresql" if durable else "volatile_sqlite",
        ai_runtime="contract_ready",
        deployment="Vercel frontend + serverless API",
        modules=[
            DeliveryModule(
                id="ui",
                name="Product interface",
                status="complete",
                progress=100,
                detail=(
                    "Study navigation, scenario library, reporting, sources, audit history, "
                    "RBAC and administration are connected."
                ),
            ),
            DeliveryModule(
                id="api",
                name="Frontend API integration",
                status="complete",
                progress=100,
                detail=(
                    "Study, node, worksheet, LOPA, library, source, report, audit and RAG "
                    "clients are connected."
                ),
            ),
            database_module,
            DeliveryModule(
                id="rag",
                name="Grounded RAG suggestions",
                status="in_progress",
                progress=45,
                detail=(
                    "UI contracts, citation display and guardrail errors are connected, "
                    "but RAG is not live on Vercel (pgvector native extension unavailable); "
                    "live Ollama, corpus ingestion and end-to-end smoke tests remain."
                ),
            ),
            DeliveryModule(
                id="crud",
                name="Study and HAZOP CRUD",
                status="complete",
                progress=100,
                detail=(
                    "Study, node, worksheet and LOPA create/update/delete " "flows are operational."
                ),
            ),
            DeliveryModule(
                id="report",
                name="Editable reporting",
                status="complete",
                progress=100,
                detail="Live DOCX generation and report history are operational.",
            ),
        ],
    )

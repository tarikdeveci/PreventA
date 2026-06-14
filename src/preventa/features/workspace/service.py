from preventa.features.workspace.repository import WorkspaceRepository
from preventa.features.workspace.schemas import (
    DeliveryModule,
    ProductStatusResponse,
    WorkspaceNode,
    WorkspaceResponse,
    WorkspaceRow,
    WorkspaceStudy,
)


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

    all_rows = [
        row
        for node in node_data
        for row in repository.list_rows(str(node["id"]))
    ]
    reviewed_scenarios = sum(row["status"] == "İncelendi" for row in all_rows)
    total_scenarios = len(all_rows)
    progress = round(reviewed_scenarios * 100 / total_scenarios) if total_scenarios else 0
    active_rows = (
        repository.list_rows(str(active_node["id"]))
        if active_node is not None
        else []
    )

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
    return ProductStatusResponse(
        release="MVP beta",
        stage="Canlı CRUD + RAG istemcisi",
        overall_progress=58,
        api_connected=True,
        persistence="volatile_sqlite",
        ai_runtime="contract_ready",
        deployment="Vercel frontend + serverless API",
        modules=[
            DeliveryModule(
                id="ui",
                name="Ürün arayüzü",
                status="in_progress",
                progress=78,
                detail=(
                    "Canlı CRUD ve kaynaklı öneri paneli bağlı; App.tsx modülerleştirmesi "
                    "ve responsive doğrulama sürüyor."
                ),
            ),
            DeliveryModule(
                id="api",
                name="Frontend API bağlantısı",
                status="complete",
                progress=100,
                detail="Study, node, worksheet, LOPA, rapor ve RAG istemcileri API'ye bağlı.",
            ),
            DeliveryModule(
                id="database",
                name="Production kalıcılığı",
                status="in_progress",
                progress=45,
                detail=(
                    "SQLite repository ve gerçek workspace özeti çalışıyor; Vercel için "
                    "yönetilen PostgreSQL geçişi tamamlanmadı."
                ),
            ),
            DeliveryModule(
                id="rag",
                name="Kaynaklı RAG önerileri",
                status="in_progress",
                progress=55,
                detail=(
                    "UI sözleşmesi, citation gösterimi ve guardrail hataları bağlı; canlı "
                    "Ollama, corpus ingestion ve uçtan uca smoke test eksik."
                ),
            ),
            DeliveryModule(
                id="crud",
                name="Study ve HAZOP CRUD",
                status="complete",
                progress=100,
                detail="Study, node, worksheet ve LOPA create/update/delete akışları çalışıyor.",
            ),
            DeliveryModule(
                id="report",
                name="DOCX/PDF rapor",
                status="in_progress",
                progress=55,
                detail="Canlı DOCX üretiliyor; PDF ve müşteri şablonu henüz tamamlanmadı.",
            ),
            DeliveryModule(
                id="import",
                name="Excel ve geçmiş çalışma import",
                status="planned",
                progress=0,
                detail="Veri eşleme ve doğrulama akışı henüz uygulanmadı.",
            ),
            DeliveryModule(
                id="pilot",
                name="Gerçek pilot çalışma",
                status="planned",
                progress=0,
                detail="Gerçek müşteri verisiyle uçtan uca pilot henüz yapılmadı.",
            ),
        ],
    )

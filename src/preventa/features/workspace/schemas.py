from typing import Literal

from pydantic import BaseModel


class WorkspaceStudy(BaseModel):
    id: str
    title: str
    client: str
    facility: str
    progress: int
    reviewed_scenarios: int
    total_scenarios: int


class WorkspaceNode(BaseModel):
    id: str
    code: str
    name: str
    equipment_type: str
    design_intent: str
    scenario_count: int
    state: Literal["complete", "active", "review", "empty"]


class WorkspaceRow(BaseModel):
    id: int
    guideword: str
    deviation: str
    cause: str
    consequence: str
    safeguard: str
    severity: int
    likelihood: int
    risk: Literal["Düşük", "Orta", "Yüksek", "Kritik"]
    status: Literal["İncelendi", "Taslak", "Eksik"]
    # Multi-category severity (item 4): carried on the initial load too, so the
    # category-severity editor is populated without a second fetch.
    category_severities: dict[str, int] = {}
    governing_category: str | None = None
    governing_severity: int | None = None


class WorkspaceSuggestion(BaseModel):
    id: str
    kind: Literal["Neden", "Sonuç", "Önlem"]
    text: str
    confidence: Literal["Yüksek", "Orta"]
    source: str
    section: str
    target: Literal["cause", "consequence", "safeguard"]


class WorkspaceResponse(BaseModel):
    source: Literal["api_seed", "database"]
    study: WorkspaceStudy
    active_node_id: str
    nodes: list[WorkspaceNode]
    rows: list[WorkspaceRow]
    suggestions: list[WorkspaceSuggestion]


class OphaImportResult(BaseModel):
    study_id: str
    study_title: str
    nodes: int
    rows: int
    lopa_layers: int
    dropped: dict[str, int]


class DeliveryModule(BaseModel):
    id: str
    name: str
    status: Literal["complete", "in_progress", "planned"]
    progress: int
    detail: str


class ProductStatusResponse(BaseModel):
    release: str
    stage: str
    overall_progress: int
    api_connected: bool
    persistence: Literal["seed", "volatile_sqlite", "postgresql"]
    ai_runtime: Literal["contract_ready", "ollama_connected"]
    deployment: str
    modules: list[DeliveryModule]

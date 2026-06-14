from pathlib import Path

import pytest
from preventa.features.workspace.repository import WorkspaceRepository
from preventa.features.workspace.service import get_product_status, get_workspace


def test_workspace_is_derived_from_repository(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PREVENTA_DB_PATH", str(tmp_path / "preventa.db"))
    workspace = get_workspace(WorkspaceRepository())

    assert workspace.source == "database"
    assert workspace.active_node_id == "node-p101"
    assert len(workspace.rows) == 4
    assert workspace.study.total_scenarios == 15
    assert workspace.study.reviewed_scenarios == 5
    assert workspace.study.progress == 33
    assert workspace.suggestions == []


def test_product_status_reports_external_runtime_dependencies() -> None:
    status = get_product_status()

    assert status.api_connected is True
    assert status.persistence == "volatile_sqlite"
    assert status.overall_progress == 88
    assert status.ai_runtime == "contract_ready"
    assert any(
        module.id == "database" and module.status == "in_progress" for module in status.modules
    )

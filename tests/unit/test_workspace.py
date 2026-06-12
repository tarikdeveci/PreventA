from preventa.features.workspace.service import get_product_status, get_workspace


def test_workspace_exposes_api_seed_transparently() -> None:
    workspace = get_workspace()

    assert workspace.source == "api_seed"
    assert workspace.active_node_id == "node-p101"
    assert len(workspace.rows) == 4
    assert all(suggestion.source for suggestion in workspace.suggestions)


def test_product_status_reports_unfinished_persistence() -> None:
    status = get_product_status()

    assert status.api_connected is True
    assert status.persistence == "seed"
    assert status.overall_progress < 100
    assert any(module.status == "planned" for module in status.modules)


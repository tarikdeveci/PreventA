from pathlib import Path

import pytest
from preventa.features.workspace.crud_schemas import (
    LopaLayerCreate,
    NodeCreate,
    RowCreate,
    RowUpdate,
    StudyCreate,
)
from preventa.features.workspace.repository import WorkspaceRepository
from preventa.features.workspace.store import connection, initialize_store


def test_workspace_crud_and_lopa(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PREVENTA_DB_PATH", str(tmp_path / "preventa.db"))
    repository = WorkspaceRepository()

    study = repository.create_study(
        StudyCreate(title="Pilot HAZOP", client="Anar", facility="Pilot tesis")
    )
    node = repository.create_node(
        study["id"],
        NodeCreate(
            code="N-01",
            name="Besleme pompası",
            equipment_type="Santrifüj pompa",
            design_intent="Kesintisiz besleme sağlamak.",
        ),
    )
    row = repository.create_row(
        node["id"],
        RowCreate(
            guideword="Yok",
            deviation="Akış yok",
            severity=4,
            likelihood=3,
        ),
    )

    assert row["risk"] == "Kritik"

    updated = repository.update_row(
        row["id"],
        RowUpdate(cause="Emiş vanası kapalı", status="Taslak"),
    )
    assert updated is not None
    assert updated["cause"] == "Emiş vanası kapalı"

    layer = repository.add_lopa_layer(
        row["id"],
        LopaLayerCreate(
            description="Bağımsız yüksek basınç tripi",
            pfd=0.01,
            note="Yıllık test",
        ),
    )
    assert layer["pfd"] == 0.01
    assert len(repository.list_lopa_layers(row["id"])) == 1

    assert repository.delete_row(row["id"]) is True
    assert repository.get_row(row["id"]) is None


def test_seed_is_idempotent_and_links_rows_to_multiple_nodes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PREVENTA_DB_PATH", str(tmp_path / "preventa.db"))

    initialize_store()
    initialize_store()

    with connection() as database:
        study_count = database.execute("SELECT COUNT(*) FROM mvp_studies").fetchone()[0]
        row_count = database.execute("SELECT COUNT(*) FROM mvp_rows").fetchone()[0]
        populated_nodes = database.execute(
            """
            SELECT COUNT(DISTINCT node_id)
            FROM mvp_rows
            """
        ).fetchone()[0]
        lopa_count = database.execute(
            "SELECT COUNT(*) FROM mvp_lopa_layers"
        ).fetchone()[0]

    assert study_count == 3
    assert row_count == 15
    assert populated_nodes == 5
    assert lopa_count > 0

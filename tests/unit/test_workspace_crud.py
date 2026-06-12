from pathlib import Path

from preventa.features.workspace.crud_schemas import (
    LopaLayerCreate,
    NodeCreate,
    RowCreate,
    RowUpdate,
    StudyCreate,
)
from preventa.features.workspace.repository import WorkspaceRepository


def test_workspace_crud_and_lopa(monkeypatch, tmp_path: Path) -> None:
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


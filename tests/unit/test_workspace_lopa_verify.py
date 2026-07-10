"""LOPA verifier on the live workspace store (OpenPHA review item 4).

Proves the running app turns stored IPLs into a real check: MEL = initiating
frequency x product(valid IPL PFDs), compared against the scenario's TMEL.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from preventa.features.workspace.crud_schemas import LopaLayerCreate, NodeCreate, RowCreate
from preventa.features.workspace.repository import WorkspaceRepository


def _repo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> WorkspaceRepository:
    monkeypatch.setenv("PREVENTA_DB_PATH", str(tmp_path / "preventa.db"))
    return WorkspaceRepository()


def _row(repo: WorkspaceRepository, **kwargs: object) -> int:
    node = repo.create_node(
        "study-reactor-2026",
        NodeCreate(
            code="N-LOPA",
            name="LOPA verify node",
            equipment_type="Pressure vessel",
            design_intent="Test scenario for the LOPA verifier.",
        ),
    )
    created = repo.create_row(str(node["id"]), RowCreate(**kwargs))  # type: ignore[arg-type]
    return int(created["id"])


def test_missing_row_returns_none(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = _repo(monkeypatch, tmp_path)
    assert repo.verify_lopa(999999) is None


def test_two_ipls_meet_target(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = _repo(monkeypatch, tmp_path)
    row_id = _row(
        repo,
        consequence="Overpressure and loss of containment",
        severity=5,
        likelihood=3,
        initiating_frequency=0.1,
        tmel=1e-5,
    )
    for _ in range(2):
        repo.add_lopa_layer(
            row_id,
            LopaLayerCreate(description="Independent SIS trip", pfd=1e-2, is_valid=True, note=""),
        )
    result = repo.verify_lopa(row_id)
    assert result is not None
    assert result["ipl_count"] == 2
    # MEL = 0.1 * 1e-2 * 1e-2 = 1e-5, exactly the target -> adequately protected.
    assert result["mel_calc"] == pytest.approx(1e-5)
    assert result["meets_tmel"] is True
    assert result["required_rrf"] == pytest.approx(1e4)


def test_single_ipl_fails_target(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = _repo(monkeypatch, tmp_path)
    row_id = _row(
        repo,
        consequence="Runaway reaction",
        severity=4,
        likelihood=3,
        initiating_frequency=0.1,
        tmel=1e-4,
    )
    repo.add_lopa_layer(
        row_id,
        LopaLayerCreate(description="Single relief valve", pfd=1e-2, is_valid=True, note=""),
    )
    result = repo.verify_lopa(row_id)
    assert result is not None
    # MEL = 0.1 * 1e-2 = 1e-3 > TMEL 1e-4 -> not adequately protected.
    assert result["mel_calc"] == pytest.approx(1e-3)
    assert result["meets_tmel"] is False


def test_invalid_ipl_is_not_credited(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = _repo(monkeypatch, tmp_path)
    row_id = _row(
        repo,
        consequence="Tank overflow",
        severity=4,
        likelihood=3,
        initiating_frequency=0.1,
        tmel=1e-3,
    )
    repo.add_lopa_layer(
        row_id,
        LopaLayerCreate(description="Valid alarm", pfd=1e-1, is_valid=True, note=""),
    )
    repo.add_lopa_layer(
        row_id,
        LopaLayerCreate(description="Disqualified layer", pfd=1e-2, is_valid=False, note="not IPL"),
    )
    result = repo.verify_lopa(row_id)
    assert result is not None
    assert result["ipl_count"] == 1  # only the valid layer counts
    assert result["mel_calc"] == pytest.approx(1e-2)


def test_seeded_critical_row_has_verifier_inputs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The seeded demo study exposes a ready-to-verify LOPA scenario."""
    repo = _repo(monkeypatch, tmp_path)
    nodes = repo.list_nodes("study-reactor-2026")
    verified = 0
    for node in nodes:
        for row in repo.list_rows(str(node["id"])):
            if row.get("initiating_frequency") and row.get("tmel"):
                result = repo.verify_lopa(int(row["id"]))
                assert result is not None
                assert result["initiating_frequency"] is not None
                verified += 1
    assert verified >= 1

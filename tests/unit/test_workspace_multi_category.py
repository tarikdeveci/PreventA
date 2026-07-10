"""Multi-category severity on the live store (OpenPHA review item 4, "the big one").

A scenario is scored on several client categories (Safety AND Environment ...),
and the app surfaces the governing (worst) category instead of a single number.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from preventa.features.workspace.crud_schemas import NodeCreate, RowCreate, RowUpdate
from preventa.features.workspace.repository import WorkspaceRepository

STUDY = "study-reactor-2026"


def _repo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> WorkspaceRepository:
    monkeypatch.setenv("PREVENTA_DB_PATH", str(tmp_path / "preventa.db"))
    return WorkspaceRepository()


def _node(repo: WorkspaceRepository) -> str:
    node = repo.create_node(
        STUDY,
        NodeCreate(
            code="N-MC",
            name="Multi-category node",
            equipment_type="Pressure vessel",
            design_intent="Scenario for multi-category severity.",
        ),
    )
    return str(node["id"])


def test_create_row_with_category_severities(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo = _repo(monkeypatch, tmp_path)
    row = repo.create_row(
        _node(repo),
        RowCreate(
            consequence="Loss of containment",
            severity=4,
            likelihood=3,
            category_severities={"Safety": 3, "Environment": 2, "Asset": 1},
        ),
    )
    assert row["category_severities"] == {"Safety": 3, "Environment": 2, "Asset": 1}
    # The governing (worst) category is Safety at level 3.
    assert row["governing_category"] == "Safety"
    assert row["governing_severity"] == 3


def test_row_without_categories_has_empty_dict(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo = _repo(monkeypatch, tmp_path)
    row = repo.create_row(_node(repo), RowCreate(consequence="No categories", severity=2))
    assert row["category_severities"] == {}
    assert row["governing_category"] is None


def test_update_row_category_severities(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo = _repo(monkeypatch, tmp_path)
    row = repo.create_row(_node(repo), RowCreate(consequence="Runaway", severity=3))
    updated = repo.update_row(
        int(row["id"]),
        RowUpdate(category_severities={"Safety": 2, "Environment": 3}),
    )
    assert updated is not None
    assert updated["category_severities"] == {"Safety": 2, "Environment": 3}
    # Environment now governs at level 3.
    assert updated["governing_category"] == "Environment"
    assert updated["governing_severity"] == 3


def test_seeded_critical_rows_are_multi_category(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo = _repo(monkeypatch, tmp_path)
    scored = 0
    for node in repo.list_nodes(STUDY):
        for row in repo.list_rows(str(node["id"])):
            cats = row["category_severities"]
            if cats:
                assert "Safety" in cats and "Environment" in cats
                assert row["governing_category"] in cats
                scored += 1
    assert scored >= 1

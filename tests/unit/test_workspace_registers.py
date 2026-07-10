"""Supporting registers on the live workspace store (OpenPHA review item 6).

Team / sessions / drawings / MOC / SCAI / incidents / checklists / parking lot
are now viewable and editable in the running app, not just the structured ORM.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from preventa.features.workspace.crud_schemas import RegisterCreate
from preventa.features.workspace.repository import WorkspaceRepository

STUDY = "study-reactor-2026"


def _repo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> WorkspaceRepository:
    monkeypatch.setenv("PREVENTA_DB_PATH", str(tmp_path / "preventa.db"))
    return WorkspaceRepository()


def test_seeded_registers_cover_every_kind(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo = _repo(monkeypatch, tmp_path)
    kinds = {item["kind"] for item in repo.list_registers(STUDY)}
    assert kinds == {
        "team",
        "session",
        "drawing",
        "moc",
        "scai",
        "incident",
        "checklist",
        "parking_lot",
    }


def test_filter_by_kind(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = _repo(monkeypatch, tmp_path)
    team = repo.list_registers(STUDY, "team")
    assert len(team) >= 2
    assert all(item["kind"] == "team" for item in team)


def test_create_and_delete_register(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = _repo(monkeypatch, tmp_path)
    created = repo.create_register(
        RegisterCreate(
            study_id=STUDY,
            kind="moc",
            title="Relocate PSV-201 discharge",
            reference="MOC-2026-020",
            detail="Route relief to a safe location.",
            status="open",
        )
    )
    assert created["id"].startswith("reg-")
    mocs = repo.list_registers(STUDY, "moc")
    assert any(item["id"] == created["id"] for item in mocs)

    assert repo.delete_register(created["id"]) is True
    assert repo.delete_register(created["id"]) is False
    remaining = {item["id"] for item in repo.list_registers(STUDY, "moc")}
    assert created["id"] not in remaining

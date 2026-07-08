"""Tests for mapping OpenPHA supporting registers onto the ORM (review item 6)."""

from __future__ import annotations

from pathlib import Path

from preventa.features.opha import load_opha, to_orm

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "synthetic.opha"


def _study():
    return to_orm(load_opha(FIXTURE))


def test_team_members_mapped() -> None:
    study = _study()
    names = sorted(m.name or "" for m in study.team_members)
    assert names == ["Alice", "Bob"]
    assert all(m.raw is not None for m in study.team_members)


def test_sessions_and_attendance_resolved() -> None:
    study = _study()
    assert len(study.sessions) == 1
    session = study.sessions[0]
    assert session.opha_id == "ses1"
    assert session.session_date is not None
    # Attendance resolves back to the imported TeamMember rows by OpenPHA id.
    attendees = sorted(m.name or "" for m in session.attendees)
    assert attendees == ["Alice", "Bob"]


def test_drawings_mapped() -> None:
    study = _study()
    assert len(study.drawings) == 1
    assert study.drawings[0].number == "P-001"
    assert study.drawings[0].title == "Process Flow Diagram"


def test_empty_registers_are_absent() -> None:
    study = _study()
    # The synthetic fixture defines no MOCs / SCAIs / incidents / checklists.
    assert study.mocs == []
    assert study.scais == []
    assert study.incidents == []
    assert study.checklists == []

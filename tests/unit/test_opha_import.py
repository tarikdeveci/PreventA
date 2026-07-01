"""Tests for importing an OpenPHA study into the live SQLite workspace store."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from preventa.api.auth_dependencies import get_current_user
from preventa.features.auth.schemas import AuthUser
from preventa.features.opha import load_opha
from preventa.features.workspace.opha_import import import_opha_study
from preventa.features.workspace.repository import WorkspaceRepository
from preventa.features.workspace.store import initialize_store
from preventa.main import create_app

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "synthetic.opha"


def test_import_populates_store(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PREVENTA_DB_PATH", str(tmp_path / "preventa.db"))
    repo = WorkspaceRepository()
    result = import_opha_study(repo, load_opha(FIXTURE))

    assert result["study_title"] == "Synthetic Demo HAZOP & LOPA"
    assert result["nodes"] == 1
    assert result["rows"] == 2  # one row per Consequence
    assert result["lopa_layers"] >= 1

    nodes = repo.list_nodes(result["study_id"])
    assert len(nodes) == 1
    rows = repo.list_rows(str(nodes[0]["id"]))
    assert len(rows) == 2
    con1 = next(r for r in rows if r["consequence"].startswith("Loss of feed"))
    # Two safeguards were collapsed into one text cell.
    assert " | " in con1["safeguard"]


def test_import_loss_report(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PREVENTA_DB_PATH", str(tmp_path / "preventa.db"))
    repo = WorkspaceRepository()
    dropped = import_opha_study(repo, load_opha(FIXTURE))["dropped"]

    assert dropped["PHA recommendations dropped"] == 1
    assert dropped["LOPA recommendations dropped"] == 1
    assert dropped["Team members dropped"] == 2
    assert dropped["Sessions dropped"] == 1
    assert "Structured IPL/SIL safeguards flattened to text" in dropped


def _client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    monkeypatch.setenv("PREVENTA_DB_PATH", str(tmp_path / "preventa.db"))
    initialize_store()  # module-level repository was created against a different path
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: AuthUser(
        id="u1",
        email="importer@example.com",
        full_name="Importer",
        role="facilitator",
        permissions=["workspace:read", "workspace:write"],
    )
    return TestClient(app)


def test_import_endpoint_accepts_opha(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client = _client(monkeypatch, tmp_path)
    response = client.post("/api/v1/studies/import", content=FIXTURE.read_bytes())
    assert response.status_code == 201
    body = response.json()
    assert body["nodes"] == 1
    assert body["rows"] == 2
    assert "dropped" in body


def test_import_endpoint_rejects_invalid_body(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client = _client(monkeypatch, tmp_path)
    response = client.post("/api/v1/studies/import", content=b"not json at all")
    assert response.status_code == 422


def test_import_endpoint_requires_auth(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PREVENTA_DB_PATH", str(tmp_path / "preventa.db"))
    client = TestClient(create_app())
    response = client.post("/api/v1/studies/import", content=FIXTURE.read_bytes())
    assert response.status_code == 401

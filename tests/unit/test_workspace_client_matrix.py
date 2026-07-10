"""Native client risk matrix on the live store (OpenPHA review item 3).

The app renders the client's own OpenPHA ``Risk_Criteria`` -- multi-category
severities, real intersection cells and coloured ranks -- not a synthetic 5x5.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from preventa.features.opha.matrix_view import build_client_matrix
from preventa.features.workspace.repository import WorkspaceRepository

STUDY = "study-reactor-2026"


def _repo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> WorkspaceRepository:
    monkeypatch.setenv("PREVENTA_DB_PATH", str(tmp_path / "preventa.db"))
    return WorkspaceRepository()


def test_build_client_matrix_none_when_absent() -> None:
    assert build_client_matrix(None) is None
    assert build_client_matrix({}) is None


def test_build_client_matrix_multi_category() -> None:
    criteria = {
        "Likelihoods": [
            {"ID": "L1", "Name": "Rare", "Level": 1},
            {"ID": "L2", "Name": "Frequent", "Level": 2},
        ],
        "Severities": [
            {"ID": "S1", "Name": "Safety 1", "Level": 1, "Category": "Safety"},
            {"ID": "S2", "Name": "Safety 2", "Level": 2, "Category": "Safety"},
            {"ID": "E1", "Name": "Env 1", "Level": 1, "Category": "Environment"},
        ],
        "Intersections": [
            {"Likelihood_ID": "L2", "Severity_ID": "S2", "Risk_Rank_ID": "RK_HIGH"},
        ],
        "Risk_Rankings": [
            {"ID": "RK_HIGH", "Name": "High", "Color": "#d9822b"},
        ],
    }
    view = build_client_matrix(criteria)
    assert view is not None
    assert view["categories"] == ["Safety", "Environment"]
    safety = next(g for g in view["grids"] if g["category"] == "Safety")
    assert safety["severities"] == ["Safety 1", "Safety 2"]
    # Rows are highest-likelihood first, so the top row is "Frequent" (L2).
    top = safety["rows"][0]
    assert top["likelihood"] == "Frequent"
    # (L2, S2) resolves to the High rank with its colour.
    assert top["cells"][1] == {"rank": "High", "color": "#d9822b"}


def test_seeded_study_exposes_client_matrix(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo = _repo(monkeypatch, tmp_path)
    matrix = repo.get_risk_matrix(STUDY)
    assert "criteria_json" not in matrix  # raw blob is not leaked to the client
    view = matrix["client_matrix"]
    assert view is not None
    assert view["categories"] == ["Safety", "Environment"]
    assert len(view["grids"]) == 2
    # Each grid is 4 likelihoods x 3 severities with coloured ranks.
    grid = view["grids"][0]
    assert len(grid["rows"]) == 4
    assert all(len(row["cells"]) == 3 for row in grid["rows"])
    assert any(cell["color"] for row in grid["rows"] for cell in row["cells"])


def test_study_without_criteria_has_null_client_matrix(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo = _repo(monkeypatch, tmp_path)
    # study-utility-2026 is seeded without a client Risk_Criteria.
    matrix = repo.get_risk_matrix("study-utility-2026")
    assert matrix["client_matrix"] is None
    # The synthetic threshold fields remain available as the fallback.
    assert matrix["low_max"] == 3

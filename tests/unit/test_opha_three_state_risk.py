"""Tests for three-state risk in the flat workspace store (review item 7b).

Two units, no database required:
* ``_scores_from_rank`` maps each localised OpenPHA rank label to a 5x5 pair.
* ``WorkspaceRepository._serialize_row`` labels the before/after states only when
  both axes are scored, leaving them null (ungraded) otherwise.
"""

from __future__ import annotations

from typing import Any

from preventa.features.workspace.opha_import import _scores_from_rank
from preventa.features.workspace.repository import WorkspaceRepository


def test_scores_from_rank_localized_labels() -> None:
    assert _scores_from_rank("Kritik") == (5, 5)
    assert _scores_from_rank("Aşırı") == (5, 5)
    assert _scores_from_rank("asiri") == (5, 5)
    assert _scores_from_rank("critical") == (5, 5)
    assert _scores_from_rank("Yüksek") == (4, 2)
    assert _scores_from_rank("yuksek") == (4, 2)
    assert _scores_from_rank("High") == (4, 2)
    assert _scores_from_rank("Orta") == (2, 2)
    assert _scores_from_rank("Moderate") == (2, 2)
    assert _scores_from_rank("Düşük") == (1, 1)
    assert _scores_from_rank("dusuk") == (1, 1)
    assert _scores_from_rank("Low") == (1, 1)


def test_scores_from_rank_blank_or_unknown_is_none() -> None:
    assert _scores_from_rank(None) is None
    assert _scores_from_rank("") is None
    assert _scores_from_rank("   ") is None
    assert _scores_from_rank("Bilinmeyen") is None


def _row(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "severity": 3,
        "likelihood": 3,
        "severity_before": None,
        "likelihood_before": None,
        "severity_after": None,
        "likelihood_after": None,
    }
    base.update(overrides)
    return base


def test_serialize_row_current_state_always_graded() -> None:
    result = WorkspaceRepository._serialize_row(_row())
    assert result["risk"] == "Yüksek"  # 3*3 = 9
    # Neither optional state is graded.
    assert result["risk_before"] is None
    assert result["risk_after"] is None


def test_serialize_row_graded_only_before() -> None:
    result = WorkspaceRepository._serialize_row(
        _row(severity_before=5, likelihood_before=5)
    )
    assert result["risk_before"] == "Kritik"  # 25
    assert result["risk_after"] is None


def test_serialize_row_graded_only_after() -> None:
    result = WorkspaceRepository._serialize_row(
        _row(severity_after=1, likelihood_after=1)
    )
    assert result["risk_after"] == "Düşük"  # 1
    assert result["risk_before"] is None


def test_serialize_row_partial_axis_stays_ungraded() -> None:
    # One axis scored, the other null -> not enough to grade the state.
    result = WorkspaceRepository._serialize_row(
        _row(severity_before=4, likelihood_before=None)
    )
    assert result["risk_before"] is None

"""Tests for mapping a parsed OpenPHA study onto the PreventA ORM graph.

Runs against the committed synthetic fixture (no client data); constructs the
ORM object tree in memory without a database.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from preventa.db.models.hazop import AnalysisMode, RecommendationKind
from preventa.features.opha import load_opha, to_orm
from preventa.features.opha.coerce import as_sil

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "synthetic.opha"


def _study():
    return to_orm(load_opha(FIXTURE))


def test_study_header_mapped() -> None:
    study = _study()
    assert study.name == "Synthetic Demo HAZOP & LOPA"
    assert study.facility == "Demo Facility"
    assert study.unit == "Demo Unit"
    assert study.analysis_mode is AnalysisMode.HAZOP
    assert study.lopa_enabled is True


def test_tree_shape_and_counts() -> None:
    study = _study()
    assert len(study.nodes) == 1
    node = study.nodes[0]
    assert node.opha_id == "node1"
    assert node.description == "Feed Pump P-101"
    assert len(node.deviations) == 2
    causes = [c for d in node.deviations for c in d.causes]
    assert len(causes) == 2
    consequences = [c for ca in causes for c in ca.consequences]
    assert len(consequences) == 2


def test_scenario_typed_fields_and_lopa() -> None:
    study = _study()
    con = next(
        c
        for n in study.nodes
        for d in n.deviations
        for ca in d.causes
        for c in ca.consequences
        if c.opha_id == "con1"
    )
    assert con.consequence == "Loss of feed and pump damage"
    assert con.consequence_type_id == "Safety"
    assert con.risk_rank_current == "Yuksek"
    # Severity/likelihood are OpenPHA ID refs, not 1-5 ints -> left unset.
    assert con.severity_current is None
    assert con.likelihood_current is None
    assert con.lopa is not None
    assert con.lopa.lopa_required is True
    assert con.lopa.tmel == pytest.approx(1e-5)
    assert con.lopa.rrf == pytest.approx(1000.0)
    assert con.lopa.recommended_sil == 2  # "SIL 2" -> 2


def test_second_scenario_has_no_lopa() -> None:
    study = _study()
    con = next(
        c
        for n in study.nodes
        for d in n.deviations
        for ca in d.causes
        for c in ca.consequences
        if c.opha_id == "con2"
    )
    assert con.lopa is None


def test_safeguard_m2m_links_resolved() -> None:
    study = _study()
    assert len(study.safeguards) == 2
    con1 = next(
        c
        for n in study.nodes
        for d in n.deviations
        for ca in d.causes
        for c in ca.consequences
        if c.opha_id == "con1"
    )
    linked = sorted(s.opha_id or "" for s in con1.safeguards)
    assert linked == ["sg1", "sg2"]
    sg2 = next(s for s in study.safeguards if s.opha_id == "sg2")
    assert sg2.is_ipl is True
    assert sg2.selected_sil == 2
    assert sg2.pfd == pytest.approx(1e-2)


def test_recommendations_mapped_and_attached() -> None:
    study = _study()
    assert len(study.recommendations) == 2
    kinds = {r.opha_id: r.kind for r in study.recommendations}
    assert kinds["phar1"] is RecommendationKind.PHA
    assert kinds["lopar1"] is RecommendationKind.LOPA
    lopa_rec = next(r for r in study.recommendations if r.opha_id == "lopar1")
    assert lopa_rec.pfd == pytest.approx(1e-2)
    # Both are referenced by con1, so they attach to that scenario.
    con1_recs = {r.opha_id for r in study.recommendations if r.consequence is not None}
    assert con1_recs == {"phar1", "lopar1"}


def test_cause_frequency_and_risk_matrix() -> None:
    study = _study()
    cause = study.nodes[0].deviations[0].causes[0]
    assert cause.opha_id == "cau1"
    assert cause.frequency == pytest.approx(0.1)
    assert study.risk_matrix is not None
    assert study.risk_matrix.likelihoods is not None


def test_as_sil_helper() -> None:
    assert as_sil("SIL 3") == 3
    assert as_sil("2") == 2
    assert as_sil("") is None
    assert as_sil("none") is None

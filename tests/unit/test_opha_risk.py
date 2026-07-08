"""Tests for the risk-matrix resolver (review item 3)."""

from __future__ import annotations

import json
from pathlib import Path

from preventa.features.opha import load_opha, to_orm
from preventa.features.opha.risk import RiskMatrixResolver

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "synthetic.opha"


def _resolver() -> RiskMatrixResolver:
    study = load_opha(FIXTURE)
    return RiskMatrixResolver.from_criteria(study.raw.get("Risk_Criteria"))


def test_ordinals_resolved_from_levels() -> None:
    resolver = _resolver()
    assert resolver.likelihood_ordinal("lk1") == 3
    assert resolver.severity("sevS3").ordinal == 3
    assert resolver.severity("sevE2").ordinal == 2
    assert resolver.likelihood_ordinal("missing") is None


def test_rank_lookup_through_intersection_cells() -> None:
    resolver = _resolver()
    rank = resolver.rank_for("lk1", "sevS3")
    assert rank is not None
    assert rank.name == "Yuksek"
    assert rank.color == "#e11d48"
    assert rank.priority == 2
    assert rank.required_lopa_credits == 1
    # No cell defined for this pair.
    assert resolver.rank_for("lk1", "sevE2") is None


def test_severity_categories_discovered() -> None:
    resolver = _resolver()
    assert resolver.categories() == ["Safety", "Environment"]


def test_resolve_bundles_ordinals_and_rank() -> None:
    resolution = _resolver().resolve("lk1", "sevS3")
    assert resolution.likelihood_ordinal == 3
    assert resolution.severity_ordinal == 3
    assert resolution.severity_category == "Safety"
    assert resolution.rank is not None and resolution.rank.name == "Yuksek"


def test_ordinal_falls_back_to_position_without_level() -> None:
    resolver = RiskMatrixResolver.from_criteria(
        {"Likelihoods": [{"ID": "a", "Name": "First"}, {"ID": "b", "Name": "Second"}]}
    )
    assert resolver.likelihood_ordinal("a") == 1
    assert resolver.likelihood_ordinal("b") == 2


def test_multi_category_severity_stored_on_consequence() -> None:
    study = to_orm(load_opha(FIXTURE))
    con1 = next(
        c
        for n in study.nodes
        for d in n.deviations
        for ca in d.causes
        for c in ca.consequences
        if c.opha_id == "con1"
    )
    assert con1.severity_by_category is not None
    by_cat = json.loads(con1.severity_by_category)
    assert by_cat["Safety"]["ordinal"] == 3
    assert by_cat["Environment"]["ordinal"] == 2
    assert by_cat["Environment"]["name"] == "Moderate"

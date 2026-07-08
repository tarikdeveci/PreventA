"""Reverse-export proof: import -> database(ORM) -> export -> compare (item 1).

This is the "real proof" the review asks for: not "we kept the raw dict", but that
the ORM graph can *regenerate* a faithful OpenPHA document.  We import the fixture,
map it to the ORM, export it back with ``orm_to_opha``, re-parse the result and
assert the structure survives the round-trip through the database.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from preventa.features.opha import load_opha, orm_to_opha, to_orm

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "synthetic.opha"


def _reexported():
    original = load_opha(FIXTURE)
    study = to_orm(original)
    exported = orm_to_opha(study)
    return original, load_opha(exported)


def test_summary_survives_roundtrip_through_database() -> None:
    original, rebuilt = _reexported()
    keys = [
        "nodes",
        "deviations",
        "causes",
        "consequences",
        "safeguards",
        "pha_recommendations",
        "lopa_recommendations",
        "team_members",
        "sessions",
    ]
    o, r = original.summary(), rebuilt.summary()
    assert {k: r[k] for k in keys} == {k: o[k] for k in keys}


def test_scenario_fields_survive_roundtrip() -> None:
    _, rebuilt = _reexported()
    con1 = next(c for c in rebuilt.iter_consequences() if c.id == "con1")
    assert con1.text == "Loss of feed and pump damage"
    assert con1.raw.get("Risk_Rank_ID") == "Yuksek"
    assert con1.lopa_required is True
    assert con1.tmel == pytest.approx(1e-5)
    assert con1.mel == pytest.approx(1e-2)
    assert con1.rrf == pytest.approx(1000.0)
    assert con1.recommended_sil == "SIL 2"
    assert sorted(con1.safeguard_ids) == ["sg1", "sg2"]


def test_recommendation_m2m_survives_roundtrip() -> None:
    """A shared recommendation is re-emitted on every consequence (item 1 + 2)."""
    _, rebuilt = _reexported()
    con1 = next(c for c in rebuilt.iter_consequences() if c.id == "con1")
    con2 = next(c for c in rebuilt.iter_consequences() if c.id == "con2")
    assert con1.pha_recommendation_ids == ["phar1"]
    assert con1.lopa_recommendation_ids == ["lopar1"]
    # phar1 was referenced by both scenarios; it must reappear on both.
    assert con2.pha_recommendation_ids == ["phar1"]


def test_conditional_modifiers_survive_roundtrip() -> None:
    _, rebuilt = _reexported()
    con1 = next(c for c in rebuilt.iter_consequences() if c.id == "con1")
    mods = con1.conditional_modifiers
    assert len(mods) == 1
    assert mods[0]["probability"] == pytest.approx(1e-1)


def test_registers_survive_roundtrip() -> None:
    _, rebuilt = _reexported()
    assert {s.description for s in rebuilt.safeguards} == {
        "Low-flow alarm FAL-101",
        "Independent high-pressure trip (SIS)",
    }
    assert len(rebuilt.raw.get("Drawings", [])) == 1
    assert rebuilt.settings.get("Ds_Rev") == "5"

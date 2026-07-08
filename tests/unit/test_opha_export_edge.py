"""Edge-case reverse-export tests for ``orm_to_opha`` (review items 1, 2, 6).

Builds ORM object trees in memory (no database, no session) to exercise export
paths the fixture round-trip does not reach: a study stripped of its risk matrix
and supporting registers, a consequence with no LOPA layer, and recommendation
many-to-many corner cases (an orphan recommendation, and one shared by two
consequences).
"""

from __future__ import annotations

from collections.abc import Sequence

from preventa.db.models.hazop import (
    AnalysisMode,
    Cause,
    Consequence,
    Deviation,
    Node,
    Recommendation,
    RecommendationKind,
    Study,
)
from preventa.features.opha import load_opha, orm_to_opha, to_orm


def _consequence(opha_id: str = "con1", text: str = "Loss of feed") -> Consequence:
    return Consequence(opha_id=opha_id, consequence=text)


def _wrap(consequences: Sequence[Consequence]) -> Node:
    """Nest consequences inside a single node -> deviation -> cause tree."""
    cause = Cause(opha_id="cau1", cause="Pump trips", consequences=list(consequences))
    deviation = Deviation(
        opha_id="dev1",
        parameter="Flow",
        guideword="No",
        deviation="No flow",
        causes=[cause],
    )
    return Node(opha_id="node1", description="Feed Pump P-101", deviations=[deviation])


def _study(nodes: list[Node], **kwargs: object) -> Study:
    return Study(
        name="Edge study",
        analysis_mode=AnalysisMode.HAZOP,
        lopa_enabled=True,
        nodes=nodes,
        **kwargs,
    )


def test_minimal_study_exports_and_parses() -> None:
    """A study with no matrix, no registers and an unmitigated consequence exports."""
    study = _study([_wrap([_consequence()])])
    doc = orm_to_opha(study)
    rebuilt = load_opha(doc)

    summary = rebuilt.summary()
    assert summary["nodes"] == 1
    assert summary["consequences"] == 1
    assert summary["safeguards"] == 0
    assert summary["team_members"] == 0
    # No risk matrix -> the Risk_Criteria block is omitted entirely.
    assert "Risk_Criteria" not in doc
    # Registers are present but empty (the reader tolerates empty lists).
    assert doc["Team_Members"] == []
    assert doc["Drawings"] == []
    # The consequence carries no LOPA fields at all.
    only = next(rebuilt.iter_consequences())
    assert only.lopa_required is None
    assert only.tmel is None


def test_minimal_study_round_trips_through_orm() -> None:
    """Export -> parse -> re-map to ORM -> export again is structurally stable."""
    doc = orm_to_opha(_study([_wrap([_consequence()])]))
    reexported = orm_to_opha(to_orm(load_opha(doc)))
    assert load_opha(reexported).summary()["consequences"] == 1
    assert reexported["Nodes"][0]["ID"] == "node1"


def test_orphan_recommendation_still_exports() -> None:
    """A recommendation referenced by zero consequences is still emitted (item 6)."""
    orphan = Recommendation(
        opha_id="phar_orphan",
        kind=RecommendationKind.PHA,
        text="Review isolation philosophy",
    )
    doc = orm_to_opha(_study([_wrap([_consequence()])], recommendations=[orphan]))

    assert [r["ID"] for r in doc["Pha_Recommendations"]] == ["phar_orphan"]
    # ...but it attaches to no consequence.
    only = next(load_opha(doc).iter_consequences())
    assert only.pha_recommendation_ids == []


def test_consequence_reference_to_unregistered_recommendation_is_ignored() -> None:
    """A dangling in-memory relationship does not crash reverse export."""
    dangling = Recommendation(
        opha_id="phar_dangling",
        kind=RecommendationKind.PHA,
        text="Review isolation philosophy",
    )
    consequence = _consequence()
    consequence.recommendations = [dangling]

    doc = orm_to_opha(_study([_wrap([consequence])], recommendations=[]))

    only = next(load_opha(doc).iter_consequences())
    assert only.pha_recommendation_ids == []
    assert doc["Pha_Recommendations"] == []


def test_shared_recommendation_emitted_on_both_consequences() -> None:
    """One recommendation shared by two consequences reappears on each (item 6)."""
    con_a = _consequence("con1", "Loss of feed")
    con_b = _consequence("con2", "Overpressure")
    shared = Recommendation(
        opha_id="phar1",
        kind=RecommendationKind.PHA,
        text="Add an independent trip",
        consequences=[con_a, con_b],
    )
    doc = orm_to_opha(_study([_wrap([con_a, con_b])], recommendations=[shared]))

    cons = {c.id: c for c in load_opha(doc).iter_consequences()}
    assert cons["con1"].pha_recommendation_ids == ["phar1"]
    assert cons["con2"].pha_recommendation_ids == ["phar1"]
    # The register lists it exactly once.
    assert [r["ID"] for r in doc["Pha_Recommendations"]] == ["phar1"]

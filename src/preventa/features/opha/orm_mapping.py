"""Map a parsed OpenPHA study onto PreventA's ORM graph.

``to_orm(study)`` builds an unpersisted ``Study`` object tree
(Study -> Node -> Deviation -> Cause -> Consequence, plus Safeguards, a LOPA
layer, Recommendations) that a repository can ``session.add`` and commit.  It is
DB-free: it only constructs mapped instances and wires relationships in memory.

Fidelity notes (see the OpenPHA review): OpenPHA is stringly-typed and
ID-referenced, so a few fields do not have a clean typed home in the relational
model:

* ``opha_id`` preserves each entity's native OpenPHA ID for link resolution and
  re-export.
* Severity/likelihood in OpenPHA are ID references into ``Risk_Criteria`` (not
  1-5 integers), so the integer ``severity_*``/``likelihood_*`` columns are left
  unset on import; the human-readable ``Risk_Rank_ID`` labels are kept in the
  ``risk_rank_*`` columns instead.
* The exact, lossless representation lives in ``preventa.features.opha.model``;
  this mapping is the typed projection for querying and reporting.
"""

from __future__ import annotations

import json
from datetime import date

from preventa.db.models.hazop import (
    AnalysisMode,
    Cause,
    Consequence,
    Deviation,
    Lopa,
    Node,
    Recommendation,
    RecommendationKind,
    RiskMatrix,
    Safeguard,
    Study,
)
from preventa.features.opha.coerce import as_bool, as_float, as_sil, as_str
from preventa.features.opha.model import Consequence as OphaConsequence
from preventa.features.opha.model import OphaStudy

_ANALYSIS_MODES = {
    "hazop": AnalysisMode.HAZOP,
    "what_if": AnalysisMode.WHAT_IF,
    "whatif": AnalysisMode.WHAT_IF,
    "checklist": AnalysisMode.CHECKLIST,
}


def _as_date(value: object) -> date | None:
    text = as_str(value)
    if text is None:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _json_or_none(value: object) -> str | None:
    """Serialise a non-empty OpenPHA sub-array to JSON, else ``None``."""
    if isinstance(value, list) and value:
        return json.dumps(value, ensure_ascii=False)
    return None


def _build_study(opha: OphaStudy) -> Study:
    ov = opha.overview
    settings = opha.settings
    mode_key = (as_str(settings.get("Analysis_Mode")) or "hazop").lower().replace(" ", "_")
    return Study(
        name=opha.name or "Untitled study",
        coordinator=as_str(ov.get("Study_Coordinator")),
        coordinator_contact=as_str(ov.get("Study_Coordinator_Contact_Info")),
        pha_type=as_str(ov.get("Pha_Type")),
        facility=as_str(ov.get("Facility")),
        facility_location=as_str(ov.get("Facility_Location")),
        facility_owner=as_str(ov.get("Facility_Owner")),
        company=as_str(ov.get("Overview_Company")),
        site=as_str(ov.get("Site")),
        plant=as_str(ov.get("Plant")),
        unit=as_str(ov.get("Unit")),
        report_number=as_str(ov.get("Report_Number")),
        project_number=as_str(ov.get("Project_Number")),
        project_description=as_str(ov.get("Project_Description")),
        general_notes=as_str(ov.get("General_Notes")),
        revalidation_due_date=_as_date(ov.get("Revalidation_Due_Date")),
        analysis_mode=_ANALYSIS_MODES.get(mode_key, AnalysisMode.HAZOP),
        lopa_enabled=as_bool(settings.get("Lopa_Mode")) is not False,
    )


def _build_safeguards(opha: OphaStudy) -> dict[str, Safeguard]:
    by_id: dict[str, Safeguard] = {}
    for sg in opha.safeguards:
        raw = sg.raw
        orm = Safeguard(
            opha_id=sg.id,
            description=sg.description or "",
            safeguard_type=as_str(raw.get("Safeguard_Type")),
            category=as_str(raw.get("Safeguard_Category")),
            ipl_tag=as_str(raw.get("Ipl_Tag")),
            is_safeguard=as_bool(raw.get("Is_Safeguard")) is not False,
            independent=as_bool(raw.get("Safeguard_Independent")),
            auditable=as_bool(raw.get("Safeguard_Auditable")),
            effective=as_bool(raw.get("Safeguard_Effective")),
            is_ipl=as_bool(raw.get("Is_Ipl")) is True,
            pfd=as_float(raw.get("Pfd")),
            safety_critical=as_bool(raw.get("Safety_Critical")),
            selected_sil=as_sil(raw.get("Selected_Sil")),
            required_response_time=as_str(raw.get("Required_Response_Time")),
            test_interval=as_str(raw.get("Test_Interval")),
            comments=as_str(raw.get("Safeguard_Comments")),
        )
        if sg.id is not None:
            by_id[sg.id] = orm
    return by_id


def _build_recommendations(opha: OphaStudy) -> dict[str, Recommendation]:
    by_id: dict[str, Recommendation] = {}
    for raw in opha.raw.get("Pha_Recommendations", []):
        ident = as_str(raw.get("ID"))
        rec = Recommendation(
            opha_id=ident,
            kind=RecommendationKind.PHA,
            text=as_str(raw.get("Pha_Recommendation")) or "",
            priority=as_str(raw.get("Pha_Recommendation_Priority")),
            responsible_party=as_str(raw.get("Pha_Recommendation_Responsible_Party")),
            status=as_str(raw.get("Pha_Recommendation_Status")),
            due_date=_as_date(raw.get("Pha_Recommendation_Due_Date")),
            comments=as_str(raw.get("Pha_Recommendation_Comments")),
        )
        if ident is not None:
            by_id[ident] = rec
    for raw in opha.raw.get("Lopa_Recommendations", []):
        ident = as_str(raw.get("ID"))
        rec = Recommendation(
            opha_id=ident,
            kind=RecommendationKind.LOPA,
            text=as_str(raw.get("Lopa_Recommendation")) or "",
            priority=as_str(raw.get("Lopa_Recommendation_Priority")),
            responsible_party=as_str(raw.get("Lopa_Recommendation_Responsible_Party")),
            status=as_str(raw.get("Lopa_Recommendation_Status")),
            due_date=_as_date(raw.get("Lopa_Recommendation_Due_Date")),
            pfd=as_float(raw.get("Lopa_Recommendation_Pfd")),
            comments=as_str(raw.get("Lopa_Recommendation_Comments")),
        )
        if ident is not None:
            by_id[ident] = rec
    return by_id


def _build_lopa(con: OphaConsequence) -> Lopa | None:
    lopa_required = con.lopa_required is True
    # Only create a LOPA layer for scenarios where LOPA was actually performed.
    # ``Mel`` is excluded from the trigger: OpenPHA derives it for every
    # scenario, so it would spuriously create a layer on all of them. The real
    # signals are Lopa_Required plus the LOPA analysis inputs/outputs below.
    triggers = (con.tmel, con.rrf, con.lopa_ratio, con.recommended_sil)
    if not lopa_required and all(t is None for t in triggers):
        return None
    return Lopa(
        lopa_required=lopa_required,
        recommended_sil=as_sil(con.recommended_sil),
        tmel=con.tmel,
        mel=con.mel,
        lopa_ratio=con.lopa_ratio,
        rrf=con.rrf,
        alarp_required=as_bool(con.raw.get("Alarp_Required")),
        conditional_modifiers=_json_or_none(con.raw.get("Conditional_Modifiers")),
    )


def to_orm(opha: OphaStudy) -> Study:
    """Build an unpersisted PreventA ``Study`` ORM graph from an OpenPHA study."""
    study = _build_study(opha)
    safeguards_by_id = _build_safeguards(opha)
    recommendations_by_id = _build_recommendations(opha)

    study.safeguards = list(safeguards_by_id.values())
    study.recommendations = list(recommendations_by_id.values())

    for node in opha.nodes:
        orm_node = Node(
            opha_id=node.id,
            description=node.description or "",
            intention=node.intention,
            boundary=as_str(node.raw.get("Boundary")),
            design_conditions=as_str(node.raw.get("Design_Conditions")),
            operating_conditions=as_str(node.raw.get("Operating_Conditions")),
            hazardous_materials=as_str(node.raw.get("Hazardous_Materials")),
            equipment_tags=node.equipment_tags,
            location=as_str(node.raw.get("Location")),
            comments=as_str(node.raw.get("Node_Comments")),
        )
        for deviation in node.deviations:
            orm_dev = Deviation(
                opha_id=deviation.id,
                parameter=deviation.parameter or "",
                guideword=deviation.guideword or "",
                deviation=deviation.text or "",
                design_intent=as_str(deviation.raw.get("Design_Intent")),
                comments=as_str(deviation.raw.get("Deviation_Comments")),
            )
            for cause in deviation.causes:
                orm_cause = Cause(
                    opha_id=cause.id,
                    cause=cause.text or "",
                    cause_type=cause.cause_type,
                    enabling_events=_json_or_none(cause.raw.get("Enabling_Events")),
                    frequency=cause.frequency,
                )
                for con in cause.consequences:
                    orm_con = Consequence(
                        opha_id=con.id,
                        consequence=con.text or "",
                        consequence_type_id=con.consequence_type,
                        risk_rank_before=as_str(con.raw.get("Risk_Rank_ID_Before_Safeguards")),
                        risk_rank_current=as_str(con.raw.get("Risk_Rank_ID")),
                        risk_rank_after_recs=as_str(
                            con.raw.get("Risk_Rank_ID_After_Recommendations")
                        ),
                    )
                    orm_con.safeguards = [
                        safeguards_by_id[i] for i in con.safeguard_ids if i in safeguards_by_id
                    ]
                    lopa = _build_lopa(con)
                    if lopa is not None:
                        orm_con.lopa = lopa
                    for rid in con.pha_recommendation_ids + con.lopa_recommendation_ids:
                        rec = recommendations_by_id.get(rid)
                        if rec is not None and rec.consequence is None:
                            rec.consequence = orm_con
                    orm_cause.consequences.append(orm_con)
                orm_dev.causes.append(orm_cause)
            orm_node.deviations.append(orm_dev)
        study.nodes.append(orm_node)

    # A study needs a RiskMatrix row; the OpenPHA Risk_Criteria is stored as JSON.
    criteria = opha.raw.get("Risk_Criteria")
    if isinstance(criteria, dict):
        study.risk_matrix = RiskMatrix(
            likelihoods=_json_or_none(criteria.get("Likelihoods")),
            severities=_json_or_none(criteria.get("Severities")),
            intersections=_json_or_none(criteria.get("Intersections")),
            risk_rankings=_json_or_none(criteria.get("Risk_Rankings")),
            alarp_categories=_json_or_none(criteria.get("Alarp_Analysis_Categories")),
        )

    return study

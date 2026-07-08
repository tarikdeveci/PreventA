"""Rebuild an OpenPHA (``.opha``) document from the PreventA ORM graph (item 1).

Until now "export" could only hand back the raw dict retained at import time, so a
study *edited* in PreventA had no way to become a ``.opha`` again.  ``orm_to_opha``
closes the loop: it walks the persisted ORM tree
(Study -> Node -> Deviation -> Cause -> Consequence, plus Safeguards, LOPA layers,
Recommendations, the risk matrix and the supporting registers) and reconstructs a
valid OpenPHA document from the database.  That is what turns PreventA from "reads
OpenPHA files" into "is an OpenPHA tool" and enables client-ready deliverables.

Fidelity: entities keep their native ``opha_id`` from import, so links resolve on
re-export; supporting registers keep a raw JSON snapshot and are emitted verbatim.
The typed risk tree is rebuilt from the typed columns.  OpenPHA is stringly-typed,
so scalars are emitted as strings and links as ``[{"ID": ...}]`` arrays — the exact
shapes :mod:`preventa.features.opha.model` parses back, giving a faithful
import -> database -> export round-trip (proven in the tests).
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from typing import Any

from preventa.db.models.hazop import (
    Cause,
    Consequence,
    Deviation,
    Node,
    Recommendation,
    RecommendationKind,
    Safeguard,
    Study,
)

_OphaDict = dict[str, Any]
_RecsFor = Callable[[Consequence], dict[str, list[str]]]


def _s(value: object) -> str | None:
    """Emit a scalar the OpenPHA way (as a string), or ``None`` to omit it."""
    if value is None:
        return None
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _put(target: _OphaDict, key: str, value: object) -> None:
    """Set ``key`` only when the value is present, keeping the document lean."""
    emitted = _s(value)
    if emitted is not None:
        target[key] = emitted


def _sil(level: int | None) -> str | None:
    """Re-emit an integer SIL level as OpenPHA's ``"SIL n"`` label."""
    return f"SIL {level}" if level is not None else None


def _link_array(ids: list[str]) -> list[_OphaDict]:
    return [{"ID": i} for i in ids]


def _raw_or_none(raw: str | None) -> _OphaDict | None:
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _ident(opha_id: str | None, prefix: str, index: int) -> str:
    """Use the native OpenPHA id, or synthesise a stable one for new entities."""
    return opha_id or f"{prefix}{index}"


def _consequence_dict(
    con: Consequence,
    *,
    index: int,
    rec_ids_by_kind: dict[str, list[str]],
) -> _OphaDict:
    out: _OphaDict = {"ID": _ident(con.opha_id, "con", index)}
    _put(out, "Consequence", con.consequence)
    _put(out, "Consequence_Type_ID", con.consequence_type_id)
    _put(out, "Likelihood_ID", con.likelihood_current)
    _put(out, "Consequence_Severity_ID", con.severity_current)
    _put(out, "Risk_Rank_ID_Before_Safeguards", con.risk_rank_before)
    _put(out, "Risk_Rank_ID", con.risk_rank_current)
    _put(out, "Risk_Rank_ID_After_Recommendations", con.risk_rank_after_recs)

    out["Safeguard_IDs"] = _link_array([s.opha_id for s in con.safeguards if s.opha_id])
    out["Pha_Recommendation_IDs"] = _link_array(rec_ids_by_kind.get("pha", []))
    out["Lopa_Recommendation_IDs"] = _link_array(rec_ids_by_kind.get("lopa", []))

    lopa = con.lopa
    if lopa is not None:
        _put(out, "Lopa_Required", lopa.lopa_required)
        _put(out, "Recommended_Sil", _sil(lopa.recommended_sil))
        _put(out, "Tmel", lopa.tmel)
        _put(out, "Mel", lopa.mel)
        _put(out, "Lopa_Ratio", lopa.lopa_ratio)
        _put(out, "Rrf", lopa.rrf)
        _put(out, "Alarp_Required", lopa.alarp_required)
        modifiers = _raw_or_none_list(lopa.conditional_modifiers)
        if modifiers is not None:
            out["Conditional_Modifiers"] = modifiers
        elif lopa.modifiers:
            out["Conditional_Modifiers"] = [
                {
                    "ID": _ident(m.opha_id, "cm", i),
                    "CM_Description": m.description or "",
                    "CM_Probability": _s(m.probability) or "",
                }
                for i, m in enumerate(lopa.modifiers, start=1)
            ]
    return out


def _raw_or_none_list(raw: str | None) -> list[Any] | None:
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        return None
    return parsed if isinstance(parsed, list) else None


def _cause_dict(cause: Cause, *, index: int, recs_for: _RecsFor) -> _OphaDict:
    out: _OphaDict = {"ID": _ident(cause.opha_id, "cau", index)}
    _put(out, "Cause", cause.cause)
    _put(out, "Cause_Type", cause.cause_type)
    _put(out, "Frequency", cause.frequency)
    enabling = _raw_or_none_list(cause.enabling_events)
    if enabling is not None:
        out["Enabling_Events"] = enabling
    out["Consequences"] = [
        _consequence_dict(con, index=i, rec_ids_by_kind=recs_for(con))
        for i, con in enumerate(cause.consequences, start=1)
    ]
    return out


def _deviation_dict(dev: Deviation, *, index: int, recs_for: _RecsFor) -> _OphaDict:
    out: _OphaDict = {"ID": _ident(dev.opha_id, "dev", index)}
    _put(out, "Parameter", dev.parameter)
    _put(out, "Guide_Word", dev.guideword)
    _put(out, "Deviation", dev.deviation)
    _put(out, "Design_Intent", dev.design_intent)
    _put(out, "Deviation_Comments", dev.comments)
    out["Causes"] = [
        _cause_dict(c, index=i, recs_for=recs_for)
        for i, c in enumerate(dev.causes, start=1)
    ]
    return out


def _node_dict(node: Node, *, index: int, recs_for: _RecsFor) -> _OphaDict:
    out: _OphaDict = {"ID": _ident(node.opha_id, "node", index)}
    _put(out, "Node_Description", node.description)
    _put(out, "Intention", node.intention)
    _put(out, "Boundary", node.boundary)
    _put(out, "Equipment_Tags", node.equipment_tags)
    _put(out, "Node_Comments", node.comments)
    out["Deviations"] = [
        _deviation_dict(d, index=i, recs_for=recs_for)
        for i, d in enumerate(node.deviations, start=1)
    ]
    return out


def _safeguard_dict(safeguard: Safeguard, *, index: int) -> _OphaDict:
    out: _OphaDict = {"ID": _ident(safeguard.opha_id, "sg", index)}
    _put(out, "Safeguard", safeguard.description)
    _put(out, "Safeguard_Type", safeguard.safeguard_type)
    _put(out, "Safeguard_Category", safeguard.category)
    _put(out, "Ipl_Tag", safeguard.ipl_tag)
    _put(out, "Is_Safeguard", safeguard.is_safeguard)
    _put(out, "Safeguard_Independent", safeguard.independent)
    _put(out, "Safeguard_Auditable", safeguard.auditable)
    _put(out, "Safeguard_Effective", safeguard.effective)
    _put(out, "Is_Ipl", safeguard.is_ipl)
    _put(out, "Pfd", safeguard.pfd)
    _put(out, "Safety_Critical", safeguard.safety_critical)
    _put(out, "Selected_Sil", _sil(safeguard.selected_sil))
    _put(out, "Test_Interval", safeguard.test_interval)
    _put(out, "Safeguard_Comments", safeguard.comments)
    return out


def _recommendation_dict(rec: Recommendation, *, index: int) -> _OphaDict:
    kind = "Pha" if rec.kind is RecommendationKind.PHA else "Lopa"
    out: _OphaDict = {"ID": _ident(rec.opha_id, "rec", index)}
    _put(out, f"{kind}_Recommendation", rec.text)
    _put(out, f"{kind}_Recommendation_Priority", rec.priority)
    _put(out, f"{kind}_Recommendation_Responsible_Party", rec.responsible_party)
    _put(out, f"{kind}_Recommendation_Status", rec.status)
    _put(out, f"{kind}_Recommendation_Due_Date", rec.due_date)
    _put(out, f"{kind}_Recommendation_Comments", rec.comments)
    if rec.kind is RecommendationKind.LOPA:
        _put(out, "Lopa_Recommendation_Pfd", rec.pfd)
    return out


def _register_list(
    rows: Iterable[Any], fallback: Callable[[Any, int], _OphaDict]
) -> list[_OphaDict]:
    """Emit a register verbatim from each row's raw snapshot, else rebuild it."""
    out: list[_OphaDict] = []
    for index, row in enumerate(rows, start=1):
        raw = _raw_or_none(row.raw)
        out.append(raw if raw is not None else fallback(row, index))
    return out


def orm_to_opha(study: Study) -> _OphaDict:
    """Rebuild a full OpenPHA document dict from a persisted PreventA ``Study``."""
    # Give every recommendation a stable id and index its consequence links so a
    # consequence can list exactly the recommendation IDs that reference it.
    rec_ids: dict[int, str] = {}
    for index, rec in enumerate(study.recommendations, start=1):
        rec_ids[id(rec)] = _ident(rec.opha_id, "rec", index)

    def recs_for(con: Consequence) -> dict[str, list[str]]:
        by_kind: dict[str, list[str]] = {"pha": [], "lopa": []}
        for rec in con.recommendations:
            rec_id = rec_ids.get(id(rec))
            if rec_id is not None:
                by_kind[rec.kind.value].append(rec_id)
        return by_kind

    doc: _OphaDict = {}

    overview: _OphaDict = {}
    _put(overview, "Study_Name", study.name)
    _put(overview, "Study_Coordinator", study.coordinator)
    _put(overview, "Study_Coordinator_Contact_Info", study.coordinator_contact)
    _put(overview, "Pha_Type", study.pha_type)
    _put(overview, "Facility", study.facility)
    _put(overview, "Facility_Location", study.facility_location)
    _put(overview, "Facility_Owner", study.facility_owner)
    _put(overview, "Overview_Company", study.company)
    _put(overview, "Site", study.site)
    _put(overview, "Plant", study.plant)
    _put(overview, "Unit", study.unit)
    _put(overview, "Report_Number", study.report_number)
    _put(overview, "Project_Number", study.project_number)
    _put(overview, "Project_Description", study.project_description)
    _put(overview, "General_Notes", study.general_notes)
    _put(overview, "Revalidation_Due_Date", study.revalidation_due_date)
    doc["Overview"] = overview

    settings: _OphaDict = {}
    _put(settings, "Analysis_Mode", study.analysis_mode.value)
    _put(settings, "Lopa_Mode", study.lopa_enabled)
    _put(settings, "Ds_Rev", study.ds_rev)
    doc["Settings"] = settings

    doc["Nodes"] = [
        _node_dict(n, index=i, recs_for=recs_for)
        for i, n in enumerate(study.nodes, start=1)
    ]
    doc["Safeguards"] = [
        _safeguard_dict(s, index=i) for i, s in enumerate(study.safeguards, start=1)
    ]
    doc["Pha_Recommendations"] = [
        _recommendation_dict(r, index=i)
        for i, r in enumerate(study.recommendations, start=1)
        if r.kind is RecommendationKind.PHA
    ]
    doc["Lopa_Recommendations"] = [
        _recommendation_dict(r, index=i)
        for i, r in enumerate(study.recommendations, start=1)
        if r.kind is RecommendationKind.LOPA
    ]

    if study.risk_matrix is not None:
        rm = study.risk_matrix
        criteria: _OphaDict = {}
        for key, column in (
            ("Likelihoods", rm.likelihoods),
            ("Severities", rm.severities),
            ("Intersections", rm.intersections),
            ("Risk_Rankings", rm.risk_rankings),
            ("Alarp_Analysis_Categories", rm.alarp_categories),
        ):
            values = _raw_or_none_list(column)
            if values is not None:
                criteria[key] = values
        if criteria:
            doc["Risk_Criteria"] = criteria

    # Supporting registers: emit verbatim from each row's raw snapshot.
    doc["Team_Members"] = _register_list(
        study.team_members,
        lambda m, i: {"ID": _ident(m.opha_id, "tm", i), "Name": m.name or ""},
    )
    doc["Sessions"] = _register_list(
        study.sessions,
        lambda s, i: {
            "ID": _ident(s.opha_id, "ses", i),
            "Team_Member_IDs": _link_array(
                [a.opha_id for a in s.attendees if a.opha_id]
            ),
        },
    )
    doc["Drawings"] = _register_list(
        study.drawings, lambda d, i: {"ID": _ident(d.opha_id, "dwg", i)}
    )
    doc["Parking_Lot"] = _register_list(
        study.parking_lot, lambda p, i: {"ID": _ident(p.opha_id, "pl", i)}
    )
    doc["Mocs"] = _register_list(study.mocs, lambda m, i: {"ID": _ident(m.opha_id, "moc", i)})
    doc["Scais"] = _register_list(study.scais, lambda s, i: {"ID": _ident(s.opha_id, "scai", i)})
    doc["Previous_Incidents"] = _register_list(
        [inc for inc in study.incidents if inc.kind == "previous"],
        lambda inc, i: {"ID": _ident(inc.opha_id, "inc", i)},
    )
    doc["Industry_Incidents"] = _register_list(
        [inc for inc in study.incidents if inc.kind == "industry"],
        lambda inc, i: {"ID": _ident(inc.opha_id, "iinc", i)},
    )
    doc["Check_Lists"] = _register_list(
        study.checklists, lambda c, i: {"ID": _ident(c.opha_id, "cl", i)}
    )

    return doc

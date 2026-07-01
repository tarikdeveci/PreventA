"""Import an OpenPHA (``.opha``) study into the live SQLite workspace store.

The running app persists to the flat MVP store (``mvp_studies`` / ``mvp_nodes`` /
``mvp_rows`` / ``mvp_lopa_layers``), so this importer flattens the OpenPHA tree
one row per Consequence — exactly the shape the workspace already renders.  It
lets a real study be loaded into the deployed app today.

Flattening is lossy by nature; the returned ``dropped`` report names what has no
home in the flat store (per the compatibility review's loss report).  The
lossless, structured representation lives in ``preventa.features.opha`` and its
ORM mapping — used once persistence moves to PostgreSQL.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from preventa.features.opha.model import OphaStudy
from preventa.features.workspace.crud_schemas import (
    LopaLayerCreate,
    NodeCreate,
    RowCreate,
    StudyCreate,
)
from preventa.features.workspace.repository import WorkspaceRepository


def _atleast(value: str | None, fallback: str, *, limit: int = 160) -> str:
    """Return a store-safe field value (min 2 chars, trimmed to ``limit``)."""
    text = (value or "").strip()
    if len(text) < 2:
        return fallback
    return text[:limit]


def import_opha_study(repo: WorkspaceRepository, opha: OphaStudy) -> dict[str, Any]:
    """Flatten an OpenPHA study into the workspace store; return an import report."""
    dropped: Counter[str] = Counter()

    study = repo.create_study(
        StudyCreate(
            title=_atleast(opha.name, "Imported OpenPHA study"),
            client=_atleast(
                opha.overview.get("Facility_Owner") or opha.overview.get("Overview_Company"),
                "Unknown client",
            ),
            facility=_atleast(opha.facility, "Unknown facility"),
        )
    )
    study_id = str(study["id"])

    safeguards_by_id = opha.safeguards_by_id()
    if safeguards_by_id:
        dropped["Structured IPL/SIL safeguards flattened to text"] += len(safeguards_by_id)

    rows_created = 0
    lopa_created = 0

    for index, node in enumerate(opha.nodes, start=1):
        created_node = repo.create_node(
            study_id,
            NodeCreate(
                code=f"N-{index:02d}",
                name=_atleast(node.description, f"Node {index}"),
                equipment_type=_atleast(node.equipment_tags, "Genel", limit=120),
                design_intent=_atleast(node.intention or node.description, "—", limit=2000),
            ),
        )
        node_id = str(created_node["id"])

        for deviation in node.deviations:
            for cause in deviation.causes:
                if cause.frequency is not None:
                    dropped["Cause frequency values dropped"] += 1
                for con in cause.consequences:
                    sg_texts = [
                        safeguards_by_id[i].description or ""
                        for i in con.safeguard_ids
                        if i in safeguards_by_id
                    ]
                    if len(sg_texts) > 1:
                        dropped["Multiple safeguards collapsed into one cell"] += 1
                    dropped["Three-state risk collapsed to one severity/likelihood"] += 1
                    if con.tmel is not None or con.rrf is not None:
                        dropped["LOPA metrics (TMEL/MEL/RRF) dropped"] += 1

                    row = repo.create_row(
                        node_id,
                        RowCreate(
                            guideword=deviation.guideword or "Yok",
                            deviation=deviation.text or "",
                            cause=cause.text or "",
                            consequence=con.text or "",
                            safeguard=" | ".join(t for t in sg_texts if t),
                            severity=1,
                            likelihood=1,
                            status="Taslak",
                        ),
                    )
                    rows_created += 1

                    # Attach linked IPL safeguards with a valid PFD as LOPA layers.
                    for sg_id in con.safeguard_ids:
                        safeguard = safeguards_by_id.get(sg_id)
                        if safeguard is None or safeguard.pfd is None:
                            continue
                        if not 0 < safeguard.pfd <= 1:
                            continue
                        repo.add_lopa_layer(
                            int(row["id"]),
                            LopaLayerCreate(
                                description=_atleast(safeguard.description, "IPL"),
                                pfd=safeguard.pfd,
                                is_valid=safeguard.is_ipl is not False,
                                note=safeguard.selected_sil or "",
                            ),
                        )
                        lopa_created += 1

    # Whole registers with no home in the flat store.
    for key, label in (
        ("Pha_Recommendations", "PHA recommendations dropped"),
        ("Lopa_Recommendations", "LOPA recommendations dropped"),
        ("Team_Members", "Team members dropped"),
        ("Sessions", "Sessions dropped"),
        ("Drawings", "Drawings dropped"),
        ("Parking_Lot", "Parking-lot items dropped"),
        ("Mocs", "MOCs dropped"),
        ("Scais", "SCAIs dropped"),
        ("Previous_Incidents", "Previous incidents dropped"),
        ("Industry_Incidents", "Industry incidents dropped"),
        ("Check_Lists", "Checklists dropped"),
    ):
        items = opha.raw.get(key)
        if isinstance(items, list) and items:
            dropped[label] += len(items)

    return {
        "study_id": study_id,
        "study_title": str(study["title"]),
        "nodes": len(opha.nodes),
        "rows": rows_created,
        "lopa_layers": lopa_created,
        "dropped": dict(sorted(dropped.items(), key=lambda kv: (-kv[1], kv[0]))),
    }

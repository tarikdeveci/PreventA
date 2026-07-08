"""A faithful, lossless in-memory view over an OpenPHA (``.opha``) study.

Each wrapper *retains the original OpenPHA dict* and exposes typed, navigable
accessors on top of it (tree traversal ``Study -> Node -> Deviation -> Cause ->
Consequence`` plus link resolution for safeguards and recommendations).  Because
the raw dict is never mutated, ``dump_opha(load_opha(doc)) == doc`` exactly — the
round-trip the OpenPHA compatibility review asks for.

The typed layer is deliberately separate from ``preventa.db.models.hazop``: the
ORM is a *typed projection* for persistence/querying (ints, floats, enums),
whereas OpenPHA is stringly-typed and ID-referenced.  Mapping this view onto the
ORM is a later step; keeping them apart is what makes the round-trip lossless.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from preventa.features.opha.coerce import as_bool, as_float, as_str, id_list

_OphaDict = dict[str, Any]


class _Wrapper:
    """Base wrapper holding the untouched OpenPHA object."""

    __slots__ = ("raw",)

    def __init__(self, raw: _OphaDict) -> None:
        self.raw = raw

    @property
    def id(self) -> str | None:
        return as_str(self.raw.get("ID"))

    def to_opha(self) -> _OphaDict:
        """Return the original OpenPHA object (lossless)."""
        return self.raw


class Consequence(_Wrapper):
    """OpenPHA ``...Causes[].Consequences[]`` — one HAZOP/LOPA scenario."""

    @property
    def text(self) -> str | None:
        return as_str(self.raw.get("Consequence"))

    @property
    def consequence_type(self) -> str | None:
        return as_str(self.raw.get("Consequence_Type_ID"))

    # Coded references into Risk_Criteria for the three risk states. OpenPHA
    # suffixes the before/after states; the "current" state is unsuffixed.
    def likelihood_code(self, state: str = "current") -> str | None:
        key = {
            "current": "Likelihood_ID",
            "before": "Likelihood_ID_Before_Safeguards",
            "after": "Likelihood_ID_After_Recommendations",
        }[state]
        return as_str(self.raw.get(key))

    def severity_code(self, state: str = "current") -> str | None:
        key = {
            "current": "Consequence_Severity_ID",
            "before": "Consequence_Severity_ID_Before_Safeguards",
            "after": "Consequence_Severity_ID_After_Recommendations",
        }[state]
        return as_str(self.raw.get(key))

    @property
    def classifications(self) -> list[dict[str, str | None]]:
        """Per-category severity codes (``Consequence_Classifications[]``).

        A rich client matrix scores a scenario on several severity categories at
        once; each classification names a category and its severity code.  Empty
        placeholder rows are dropped.
        """
        out: list[dict[str, str | None]] = []
        raw = self.raw.get("Consequence_Classifications")
        if not isinstance(raw, list):
            return out
        for item in raw:
            if not isinstance(item, dict):
                continue
            severity = as_str(item.get("Consequence_Severity_ID") or item.get("Magnitude_ID"))
            category = as_str(item.get("Category") or item.get("Category_Name"))
            if severity is None and category is None:
                continue
            out.append({"category": category, "severity_code": severity})
        return out

    @property
    def lopa_required(self) -> bool | None:
        return as_bool(self.raw.get("Lopa_Required"))

    @property
    def tmel(self) -> float | None:
        return as_float(self.raw.get("Tmel"))

    @property
    def mel(self) -> float | None:
        return as_float(self.raw.get("Mel"))

    @property
    def rrf(self) -> float | None:
        return as_float(self.raw.get("Rrf"))

    @property
    def lopa_ratio(self) -> float | None:
        return as_float(self.raw.get("Lopa_Ratio"))

    @property
    def recommended_sil(self) -> str | None:
        # OpenPHA stores e.g. "SIL 3" — a label, not an int.
        return as_str(self.raw.get("Recommended_Sil"))

    @property
    def conditional_modifiers(self) -> list[dict[str, Any]]:
        """Itemised LOPA conditional modifiers (``Conditional_Modifiers[]``).

        Each entry is normalised to ``{"id", "description", "probability"}``;
        OpenPHA placeholder rows (blank description *and* probability) are
        dropped so they do not distort the LOPA arithmetic.
        """
        out: list[dict[str, Any]] = []
        raw = self.raw.get("Conditional_Modifiers")
        if not isinstance(raw, list):
            return out
        for item in raw:
            if not isinstance(item, dict):
                continue
            description = as_str(item.get("CM_Description"))
            probability = as_float(item.get("CM_Probability"))
            if description is None and probability is None:
                continue
            out.append(
                {
                    "id": as_str(item.get("ID")),
                    "description": description,
                    "probability": probability,
                }
            )
        return out

    @property
    def safeguard_ids(self) -> list[str]:
        return id_list(self.raw.get("Safeguard_IDs"))

    @property
    def pha_recommendation_ids(self) -> list[str]:
        return id_list(self.raw.get("Pha_Recommendation_IDs"))

    @property
    def lopa_recommendation_ids(self) -> list[str]:
        return id_list(self.raw.get("Lopa_Recommendation_IDs"))


class Cause(_Wrapper):
    """OpenPHA ``...Deviations[].Causes[]``."""

    @property
    def text(self) -> str | None:
        return as_str(self.raw.get("Cause"))

    @property
    def cause_type(self) -> str | None:
        return as_str(self.raw.get("Cause_Type"))

    @property
    def frequency(self) -> float | None:
        return as_float(self.raw.get("Frequency"))

    @property
    def consequences(self) -> list[Consequence]:
        return [Consequence(c) for c in self.raw.get("Consequences", [])]


class Deviation(_Wrapper):
    """OpenPHA ``Nodes[].Deviations[]``."""

    @property
    def parameter(self) -> str | None:
        return as_str(self.raw.get("Parameter"))

    @property
    def guideword(self) -> str | None:
        return as_str(self.raw.get("Guide_Word"))

    @property
    def text(self) -> str | None:
        return as_str(self.raw.get("Deviation"))

    @property
    def causes(self) -> list[Cause]:
        return [Cause(c) for c in self.raw.get("Causes", [])]


class Node(_Wrapper):
    """OpenPHA ``Nodes[]``."""

    @property
    def description(self) -> str | None:
        return as_str(self.raw.get("Node_Description"))

    @property
    def intention(self) -> str | None:
        return as_str(self.raw.get("Intention"))

    @property
    def equipment_tags(self) -> str | None:
        return as_str(self.raw.get("Equipment_Tags"))

    @property
    def deviations(self) -> list[Deviation]:
        return [Deviation(d) for d in self.raw.get("Deviations", [])]


class Safeguard(_Wrapper):
    """OpenPHA ``Safeguards[]`` — a structured IPL / SIL object."""

    @property
    def description(self) -> str | None:
        return as_str(self.raw.get("Safeguard"))

    @property
    def is_ipl(self) -> bool | None:
        return as_bool(self.raw.get("Is_Ipl"))

    @property
    def pfd(self) -> float | None:
        return as_float(self.raw.get("Pfd"))

    @property
    def selected_sil(self) -> str | None:
        return as_str(self.raw.get("Selected_Sil"))


class OphaStudy:
    """Top-level view over a parsed ``.opha`` document.

    Retains the whole document so :meth:`to_opha` is an exact round-trip; the
    accessors below give typed, navigable entry points into it.
    """

    def __init__(self, raw: _OphaDict) -> None:
        self.raw = raw

    # --- header ---------------------------------------------------------- #
    @property
    def overview(self) -> _OphaDict:
        overview: _OphaDict = self.raw.get("Overview", {})
        return overview

    @property
    def settings(self) -> _OphaDict:
        settings: _OphaDict = self.raw.get("Settings", {})
        return settings

    @property
    def name(self) -> str | None:
        return as_str(self.overview.get("Study_Name"))

    @property
    def facility(self) -> str | None:
        return as_str(self.overview.get("Facility"))

    @property
    def ds_rev(self) -> str | None:
        """OpenPHA data-structure revision (``Settings.Ds_Rev``).

        Identifies the schema version the file was written with.  Kept so import
        can branch on it rather than silently mis-reading a renamed field.
        """
        return as_str(self.settings.get("Ds_Rev"))

    # --- tree ------------------------------------------------------------ #
    @property
    def nodes(self) -> list[Node]:
        return [Node(n) for n in self.raw.get("Nodes", [])]

    @property
    def safeguards(self) -> list[Safeguard]:
        return [Safeguard(s) for s in self.raw.get("Safeguards", [])]

    def safeguards_by_id(self) -> dict[str, Safeguard]:
        return {s.id: s for s in self.safeguards if s.id is not None}

    def iter_consequences(self) -> Iterator[Consequence]:
        for node in self.nodes:
            for deviation in node.deviations:
                for cause in deviation.causes:
                    yield from cause.consequences

    # --- summary (proves faithful traversal) ----------------------------- #
    def summary(self) -> dict[str, int]:
        nodes = self.nodes
        deviations = [d for n in nodes for d in n.deviations]
        causes = [c for d in deviations for c in d.causes]
        consequences = [c for ca in causes for c in ca.consequences]
        return {
            "nodes": len(nodes),
            "deviations": len(deviations),
            "causes": len(causes),
            "consequences": len(consequences),
            "safeguards": len(self.safeguards),
            "pha_recommendations": len(self.raw.get("Pha_Recommendations", [])),
            "lopa_recommendations": len(self.raw.get("Lopa_Recommendations", [])),
            "team_members": len(self.raw.get("Team_Members", [])),
            "sessions": len(self.raw.get("Sessions", [])),
        }

    def to_opha(self) -> _OphaDict:
        """Return the original document unchanged (lossless round-trip)."""
        return self.raw

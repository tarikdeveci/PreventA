"""Resolve OpenPHA risk codes into ordinal numbers, ranks and colours (item 3).

OpenPHA does not store a scenario's risk as a 1-5 severity/likelihood pair.  It
stores *coded references* into the study's ``Risk_Criteria`` object:

* ``Likelihoods[]`` and ``Severities[]`` -- the axes, each an ``{ID, Name, ...}``
  with an ordinal level.  A rich client matrix (e.g. ENTEK DRES) carries several
  *parallel* severity categories (Safety, Environment, Asset, ...), so a scenario
  is scored per category, not on one axis.
* ``Intersections[]`` -- the cells, each mapping a (likelihood, severity) pair to
  a ``Risk_Rank_ID``.
* ``Risk_Rankings[]`` -- the ranks, each with a colour, priority and
  ``Required_Lopa_Credits``.

This resolver turns those codes into ordinals and rank metadata so PreventA can
compute, sort and colour risk and drive LOPA from the matrix -- instead of
leaving the numeric fields blank.  It is deliberately tolerant of OpenPHA's key
spellings and degrades gracefully when parts of the matrix are absent.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from preventa.features.opha.coerce import as_int, as_str

# Candidate key spellings OpenPHA uses for a level's ordinal value and its axis
# code inside intersection cells. Tried in order; first hit wins.
_ORDINAL_KEYS = ("Level", "Value", "Number", "Order", "Rank", "Weight", "Index")
_LIKELIHOOD_CELL_KEYS = ("Likelihood_ID", "Likelihood", "Likelihood_Id")
_SEVERITY_CELL_KEYS = (
    "Severity_ID",
    "Consequence_Severity_ID",
    "Magnitude_ID",
    "Severity",
    "Severity_Id",
)
_RANK_CELL_KEYS = ("Risk_Rank_ID", "Risk_Ranking_ID", "Risk_Rank", "Rank_ID")


def _first(raw: dict[str, Any], keys: Iterable[str]) -> str | None:
    for key in keys:
        value = as_str(raw.get(key))
        if value is not None:
            return value
    return None


@dataclass(frozen=True)
class Level:
    """One axis level (a likelihood or a severity)."""

    id: str
    name: str | None
    ordinal: int
    category: str | None = None  # severities only; e.g. "Safety", "Environment"


@dataclass(frozen=True)
class RankInfo:
    """A resolved risk ranking with the metadata the UI and LOPA need."""

    id: str
    name: str | None
    color: str | None
    priority: int | None
    required_lopa_credits: int | None


@dataclass(frozen=True)
class RiskResolution:
    """The outcome of resolving a scenario's coded risk against the matrix."""

    likelihood_ordinal: int | None
    severity_ordinal: int | None
    severity_category: str | None
    rank: RankInfo | None


class RiskMatrixResolver:
    """Parse an OpenPHA ``Risk_Criteria`` object and resolve coded risk."""

    def __init__(
        self,
        likelihoods: list[Level],
        severities: list[Level],
        intersections: dict[tuple[str, str], str],
        rankings: dict[str, RankInfo],
    ) -> None:
        self._likelihoods = {level.id: level for level in likelihoods}
        self._severities = {level.id: level for level in severities}
        self._intersections = intersections
        self._rankings = rankings

    # --- construction ---------------------------------------------------- #
    @classmethod
    def from_criteria(cls, criteria: dict[str, Any] | None) -> RiskMatrixResolver:
        criteria = criteria or {}
        likelihoods = cls._parse_levels(criteria.get("Likelihoods"))
        severities = cls._parse_levels(
            criteria.get("Severities"), category_keys=("Category", "Category_Name", "Type")
        )
        intersections = cls._parse_intersections(criteria.get("Intersections"))
        rankings = cls._parse_rankings(criteria.get("Risk_Rankings"))
        return cls(likelihoods, severities, intersections, rankings)

    @staticmethod
    def _parse_levels(
        raw: Any, *, category_keys: tuple[str, ...] = ()
    ) -> list[Level]:
        if not isinstance(raw, list):
            return []
        levels: list[Level] = []
        for index, item in enumerate(raw, start=1):
            if not isinstance(item, dict):
                continue
            ident = as_str(item.get("ID"))
            if ident is None:
                continue
            # Fall back to position when the file carries no parseable level.
            parsed = as_int(_first(item, _ORDINAL_KEYS))
            levels.append(
                Level(
                    id=ident,
                    name=as_str(item.get("Name")),
                    ordinal=parsed if parsed is not None else index,
                    category=_first(item, category_keys) if category_keys else None,
                )
            )
        return levels

    @staticmethod
    def _parse_intersections(raw: Any) -> dict[tuple[str, str], str]:
        cells: dict[tuple[str, str], str] = {}
        if not isinstance(raw, list):
            return cells
        for item in raw:
            if not isinstance(item, dict):
                continue
            likelihood = _first(item, _LIKELIHOOD_CELL_KEYS)
            severity = _first(item, _SEVERITY_CELL_KEYS)
            rank = _first(item, _RANK_CELL_KEYS)
            if likelihood and severity and rank:
                cells[(likelihood, severity)] = rank
        return cells

    @staticmethod
    def _parse_rankings(raw: Any) -> dict[str, RankInfo]:
        ranks: dict[str, RankInfo] = {}
        if not isinstance(raw, list):
            return ranks
        for item in raw:
            if not isinstance(item, dict):
                continue
            ident = as_str(item.get("ID"))
            if ident is None:
                continue
            ranks[ident] = RankInfo(
                id=ident,
                name=as_str(item.get("Name")),
                color=as_str(item.get("Color") or item.get("Colour")),
                priority=as_int(item.get("Priority")),
                required_lopa_credits=as_int(item.get("Required_Lopa_Credits")),
            )
        return ranks

    # --- queries --------------------------------------------------------- #
    def categories(self) -> list[str]:
        """Distinct severity categories present, in first-seen order."""
        seen: list[str] = []
        for level in self._severities.values():
            if level.category and level.category not in seen:
                seen.append(level.category)
        return seen

    def likelihood_ordinal(self, code: str | None) -> int | None:
        level = self._likelihoods.get(code) if code else None
        return level.ordinal if level else None

    def severity(self, code: str | None) -> Level | None:
        return self._severities.get(code) if code else None

    def rank_for(
        self, likelihood_code: str | None, severity_code: str | None
    ) -> RankInfo | None:
        if not likelihood_code or not severity_code:
            return None
        rank_id = self._intersections.get((likelihood_code, severity_code))
        return self._rankings.get(rank_id) if rank_id else None

    def rank_by_id(self, rank_id: str | None) -> RankInfo | None:
        return self._rankings.get(rank_id) if rank_id else None

    def resolve(
        self, likelihood_code: str | None, severity_code: str | None
    ) -> RiskResolution:
        """Resolve a scenario's coded (likelihood, severity) into ordinals + rank."""
        severity = self.severity(severity_code)
        return RiskResolution(
            likelihood_ordinal=self.likelihood_ordinal(likelihood_code),
            severity_ordinal=severity.ordinal if severity else None,
            severity_category=severity.category if severity else None,
            rank=self.rank_for(likelihood_code, severity_code),
        )

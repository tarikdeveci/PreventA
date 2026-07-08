"""Edge-case tests for the risk-matrix resolver (review item 3 / item 2 in brief).

Covers OpenPHA's tolerant key spellings inside intersection cells, a matrix with
no ``Intersections`` table, incomplete/garbage cells, and the ``rank_by_id``
direct lookup.
"""

from __future__ import annotations

from preventa.features.opha.risk import RiskMatrixResolver


def test_alternate_cell_key_spellings_resolve() -> None:
    """``Likelihood_Id`` / ``Severity_Id`` / ``Risk_Ranking_ID`` cells resolve."""
    resolver = RiskMatrixResolver.from_criteria(
        {
            "Likelihoods": [{"ID": "lk1", "Level": "2"}],
            "Severities": [{"ID": "sev1", "Level": "3"}],
            "Intersections": [
                {"Likelihood_Id": "lk1", "Severity_Id": "sev1", "Risk_Ranking_ID": "R2"}
            ],
            "Risk_Rankings": [
                {"ID": "R2", "Name": "High", "Colour": "#f00", "Priority": "2"}
            ],
        }
    )
    rank = resolver.rank_for("lk1", "sev1")
    assert rank is not None
    assert rank.name == "High"
    # The British ``Colour`` spelling is accepted alongside ``Color``.
    assert rank.color == "#f00"


def test_magnitude_and_consequence_severity_cell_keys() -> None:
    """Severity may be coded as ``Magnitude_ID`` or ``Consequence_Severity_ID``."""
    resolver = RiskMatrixResolver.from_criteria(
        {
            "Likelihoods": [{"ID": "lk1"}],
            "Severities": [{"ID": "sevA"}, {"ID": "sevB"}],
            "Intersections": [
                {"Likelihood": "lk1", "Magnitude_ID": "sevA", "Risk_Rank": "R1"},
                {"Likelihood_ID": "lk1", "Consequence_Severity_ID": "sevB", "Rank_ID": "R1"},
            ],
            "Risk_Rankings": [{"ID": "R1", "Name": "Low"}],
        }
    )
    assert resolver.rank_for("lk1", "sevA") is not None
    assert resolver.rank_for("lk1", "sevA").name == "Low"  # type: ignore[union-attr]
    assert resolver.rank_for("lk1", "sevB") is not None
    assert resolver.rank_for("lk1", "sevB").name == "Low"  # type: ignore[union-attr]


def test_missing_intersections_yields_no_rank_but_keeps_ordinals() -> None:
    resolver = RiskMatrixResolver.from_criteria(
        {
            "Likelihoods": [{"ID": "lk1", "Level": "1"}],
            "Severities": [{"ID": "sev1", "Level": "1"}],
            "Risk_Rankings": [{"ID": "R1", "Name": "Low"}],
        }
    )
    assert resolver.rank_for("lk1", "sev1") is None
    # Ordinals still resolve without an intersection table.
    assert resolver.likelihood_ordinal("lk1") == 1
    assert resolver.severity("sev1") is not None
    assert resolver.severity("sev1").ordinal == 1  # type: ignore[union-attr]


def test_incomplete_and_nondict_cells_are_skipped() -> None:
    resolver = RiskMatrixResolver.from_criteria(
        {
            "Likelihoods": [{"ID": "lk1"}],
            "Severities": [{"ID": "sev1"}],
            "Intersections": [
                {"Likelihood_ID": "lk1", "Severity_ID": "sev1"},  # no rank -> dropped
                "not a dict",
            ],
            "Risk_Rankings": [{"ID": "R1", "Name": "Low"}],
        }
    )
    assert resolver.rank_for("lk1", "sev1") is None


def test_rank_by_id_direct_lookup() -> None:
    resolver = RiskMatrixResolver.from_criteria(
        {
            "Risk_Rankings": [
                {
                    "ID": "R3",
                    "Name": "Kritik",
                    "Priority": "1",
                    "Required_Lopa_Credits": "2",
                }
            ]
        }
    )
    rank = resolver.rank_by_id("R3")
    assert rank is not None
    assert rank.name == "Kritik"
    assert rank.priority == 1
    assert rank.required_lopa_credits == 2
    # Unknown and missing ids resolve to None (not an error).
    assert resolver.rank_by_id("nope") is None
    assert resolver.rank_by_id(None) is None

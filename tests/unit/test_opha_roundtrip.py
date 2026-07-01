"""OpenPHA import/export round-trip and typed-accessor tests.

The committed test runs against a small synthetic ``.opha`` fixture (no client
data).  An optional test runs against a real study file if the environment
variable ``PREVENTA_OPHA_FIXTURE`` points at one — used to verify against the
ANAGOLD study locally without committing sensitive data to the repo.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from preventa.features.opha import dump_opha, dumps_opha, load_opha, loads_opha
from preventa.features.opha.coerce import as_bool, as_float, as_int, as_str, id_list

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "synthetic.opha"


def test_roundtrip_is_lossless_dict() -> None:
    original = json.loads(FIXTURE.read_text(encoding="utf-8"))
    study = load_opha(dict(original))
    assert dump_opha(study) == original


def test_roundtrip_is_lossless_via_string() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    study = loads_opha(text)
    assert json.loads(dumps_opha(study)) == json.loads(text)


def test_summary_counts() -> None:
    study = load_opha(FIXTURE)
    summary = study.summary()
    assert summary["nodes"] == 1
    assert summary["deviations"] == 2
    assert summary["causes"] == 2
    assert summary["consequences"] == 2
    assert summary["safeguards"] == 2
    assert summary["pha_recommendations"] == 1
    assert summary["lopa_recommendations"] == 1
    assert summary["team_members"] == 2
    assert summary["sessions"] == 1


def test_header_accessors() -> None:
    study = load_opha(FIXTURE)
    assert study.name == "Synthetic Demo HAZOP & LOPA"
    assert study.facility == "Demo Facility"


def test_typed_scenario_accessors() -> None:
    study = load_opha(FIXTURE)
    con = next(c for c in study.iter_consequences() if c.id == "con1")
    assert con.text == "Loss of feed and pump damage"
    assert con.lopa_required is True
    assert con.tmel == pytest.approx(1e-5)
    assert con.mel == pytest.approx(1e-2)
    assert con.rrf == pytest.approx(1000.0)
    # OpenPHA stores SIL as a label, not an int — preserved as a string.
    assert con.recommended_sil == "SIL 2"
    assert con.safeguard_ids == ["sg1", "sg2"]
    assert con.pha_recommendation_ids == ["phar1"]
    assert con.lopa_recommendation_ids == ["lopar1"]


def test_safeguard_link_resolution() -> None:
    study = load_opha(FIXTURE)
    by_id = study.safeguards_by_id()
    con = next(c for c in study.iter_consequences() if c.id == "con1")
    linked = [by_id[i] for i in con.safeguard_ids]
    assert [s.description for s in linked] == [
        "Low-flow alarm FAL-101",
        "Independent high-pressure trip (SIS)",
    ]
    assert by_id["sg2"].is_ipl is True
    assert by_id["sg2"].pfd == pytest.approx(1e-2)


def test_cause_frequency_parsed() -> None:
    study = load_opha(FIXTURE)
    node = study.nodes[0]
    cause = node.deviations[0].causes[0]
    assert cause.frequency == pytest.approx(0.1)


def test_coerce_helpers() -> None:
    assert as_str("null") is None
    assert as_str("  x ") == "x"
    assert as_float("1E-5") == pytest.approx(1e-5)
    assert as_float("") is None
    assert as_int("3.0") == 3
    assert as_int("bogus") is None
    assert as_bool("true") is True
    assert as_bool("false") is False
    assert as_bool("null") is None
    assert id_list([{"ID": "a"}, {"ID": ""}, {"ID": "b"}]) == ["a", "b"]
    assert id_list(["a", "b"]) == ["a", "b"]
    assert id_list(None) == []


@pytest.mark.skipif(
    not os.getenv("PREVENTA_OPHA_FIXTURE"),
    reason="set PREVENTA_OPHA_FIXTURE to a real .opha file to run",
)
def test_real_study_roundtrip() -> None:
    path = Path(os.environ["PREVENTA_OPHA_FIXTURE"])
    original = json.loads(path.read_text(encoding="utf-8"))
    study = load_opha(dict(original))
    assert dump_opha(study) == original
    summary = study.summary()
    assert summary["nodes"] >= 1
    assert summary["consequences"] >= summary["causes"] >= summary["deviations"]

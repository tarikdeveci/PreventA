"""Tests for the LOPA recompute/verify layer (review item 4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from preventa.features.opha import load_opha, to_orm
from preventa.features.opha.lopa_check import recompute_lopa

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "synthetic.opha"


def test_recompute_basic_arithmetic() -> None:
    result = recompute_lopa(
        initiating_frequency=1e-1,
        ipl_pfds=[1e-2],
        modifier_probabilities=[1e-1],
        tmel=1e-5,
        stored_mel=1e-2,
    )
    assert result.mel_calc == pytest.approx(1e-4)
    assert result.meets_tmel is False  # 1e-4 > 1e-5
    assert result.required_rrf == pytest.approx(1e4)  # freq / tmel
    assert result.mel_matches_stored is False  # 1e-4 vs 1e-2 is >2x off


def test_recompute_meets_target_when_ipls_sufficient() -> None:
    result = recompute_lopa(
        initiating_frequency=1e-1,
        ipl_pfds=[1e-2, 1e-2, 1e-2],  # three IPLs -> 1e-6
        modifier_probabilities=[],
        tmel=1e-5,
    )
    assert result.mel_calc == pytest.approx(1e-7)
    assert result.meets_tmel is True


def test_invalid_pfds_are_ignored() -> None:
    result = recompute_lopa(
        initiating_frequency=1.0,
        ipl_pfds=[0.0, 2.0, None, 1e-2],  # only 1e-2 is a valid credit
        modifier_probabilities=[],
        tmel=None,
    )
    assert result.ipl_pfd_product == pytest.approx(1e-2)
    assert result.mel_calc == pytest.approx(1e-2)
    assert result.meets_tmel is None  # no target to check against


def test_unknown_frequency_leaves_mel_none() -> None:
    result = recompute_lopa(
        initiating_frequency=None,
        ipl_pfds=[1e-2],
        modifier_probabilities=[],
        tmel=1e-5,
    )
    assert result.mel_calc is None
    assert result.meets_tmel is None


def test_to_orm_populates_lopa_check_and_modifiers() -> None:
    study = to_orm(load_opha(FIXTURE))
    con1 = next(
        c
        for n in study.nodes
        for d in n.deviations
        for ca in d.causes
        for c in ca.consequences
        if c.opha_id == "con1"
    )
    assert con1.lopa is not None
    # Only the real modifier survives; the blank placeholder is dropped.
    assert len(con1.lopa.modifiers) == 1
    assert con1.lopa.modifiers[0].probability == pytest.approx(1e-1)
    # freq 1e-1 x IPL sg2 (1e-2) x modifier (1e-1) = 1e-4.
    assert con1.lopa.mel_calc == pytest.approx(1e-4)
    assert con1.lopa.meets_tmel is False

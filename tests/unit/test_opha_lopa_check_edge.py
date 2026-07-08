"""Edge-case tests for the LOPA recompute/verify layer (review item 4).

Exercises the boundaries of ``recompute_lopa``: a zero/None initiating frequency,
empty IPL and modifier sets, conditional-modifier products, the zero-target guard
on ``required_rrf``, and the factor-of-two window used by ``mel_matches_stored``.
"""

from __future__ import annotations

import pytest

from preventa.features.opha.lopa_check import recompute_lopa


def test_zero_frequency_gives_zero_mel_and_meets_target() -> None:
    result = recompute_lopa(
        initiating_frequency=0.0,
        ipl_pfds=[1e-2],
        modifier_probabilities=[],
        tmel=1e-5,
    )
    assert result.mel_calc == 0.0
    assert result.meets_tmel is True  # 0 <= 1e-5
    assert result.required_rrf == 0.0  # 0 / 1e-5


def test_empty_ipls_and_modifiers_leave_frequency_unreduced() -> None:
    result = recompute_lopa(
        initiating_frequency=1e-1,
        ipl_pfds=[],
        modifier_probabilities=[],
        tmel=None,
    )
    assert result.ipl_pfd_product == 1.0
    assert result.modifier_product == 1.0
    assert result.mel_calc == pytest.approx(1e-1)


def test_modifier_product_multiplies_into_mel() -> None:
    result = recompute_lopa(
        initiating_frequency=1.0,
        ipl_pfds=[1e-1],
        modifier_probabilities=[1e-1, 5e-1],
        tmel=None,
    )
    assert result.modifier_product == pytest.approx(5e-2)
    assert result.mel_calc == pytest.approx(1.0 * 1e-1 * 5e-2)


def test_invalid_modifiers_are_ignored() -> None:
    result = recompute_lopa(
        initiating_frequency=1.0,
        ipl_pfds=[],
        modifier_probabilities=[0.0, 2.0, None, 3e-1],  # only 3e-1 is a valid factor
        tmel=None,
    )
    assert result.modifier_product == pytest.approx(3e-1)


def test_zero_tmel_suppresses_required_rrf() -> None:
    result = recompute_lopa(
        initiating_frequency=1e-1,
        ipl_pfds=[],
        modifier_probabilities=[],
        tmel=0.0,
    )
    # Division-by-zero is guarded: no risk-reduction ratio is reported.
    assert result.required_rrf is None
    assert result.mel_calc == pytest.approx(1e-1)
    assert result.meets_tmel is False  # 1e-1 <= 0 is False


def test_no_match_or_rrf_without_a_computed_mel() -> None:
    result = recompute_lopa(
        initiating_frequency=None,
        ipl_pfds=[1e-2],
        modifier_probabilities=[],
        tmel=1e-5,
        stored_mel=1e-2,
    )
    assert result.mel_calc is None
    assert result.meets_tmel is None
    assert result.required_rrf is None
    assert result.mel_matches_stored is None


def test_mel_matches_stored_at_factor_of_two_boundary() -> None:
    # Powers of two divide exactly in binary, so the boundary ratios are exact.
    at_2x = recompute_lopa(
        initiating_frequency=0.5,
        ipl_pfds=[],
        modifier_probabilities=[],
        tmel=None,
        stored_mel=0.25,
    )
    assert at_2x.mel_matches_stored is True  # ratio == 2.0
    at_half = recompute_lopa(
        initiating_frequency=0.125,
        ipl_pfds=[],
        modifier_probabilities=[],
        tmel=None,
        stored_mel=0.25,
    )
    assert at_half.mel_matches_stored is True  # ratio == 0.5
    over_2x = recompute_lopa(
        initiating_frequency=0.75,
        ipl_pfds=[],
        modifier_probabilities=[],
        tmel=None,
        stored_mel=0.25,
    )
    assert over_2x.mel_matches_stored is False  # ratio == 3.0
    under_half = recompute_lopa(
        initiating_frequency=0.1,
        ipl_pfds=[],
        modifier_probabilities=[],
        tmel=None,
        stored_mel=0.25,
    )
    assert under_half.mel_matches_stored is False  # ratio == 0.4


def test_zero_stored_mel_uses_isclose_not_ratio() -> None:
    both_zero = recompute_lopa(
        initiating_frequency=0.0,
        ipl_pfds=[],
        modifier_probabilities=[],
        tmel=None,
        stored_mel=0.0,
    )
    assert both_zero.mel_calc == 0.0
    assert both_zero.mel_matches_stored is True
    calc_zero_stored_nonzero = recompute_lopa(
        initiating_frequency=0.0,
        ipl_pfds=[],
        modifier_probabilities=[],
        tmel=None,
        stored_mel=1e-3,
    )
    assert calc_zero_stored_nonzero.mel_matches_stored is False

"""Recompute the LOPA arithmetic so PreventA verifies a scenario, not just stores it.

LOPA (Layer of Protection Analysis) reduces an initiating event's frequency by the
independent protection layers (IPLs) guarding it, optionally adjusted by
conditional modifiers (probability of ignition, probability a person is present,
etc.), and checks the result against a tolerable target (TMEL):

    MEL = initiating_frequency
          x product(IPL PFDs)
          x product(conditional-modifier probabilities)

    scenario is adequately protected  <=>  MEL <= TMEL

This module (item 4 of the OpenPHA review) turns the stored LOPA numbers into a
check: on import PreventA recomputes ``MEL`` from the modelled inputs and flags
(a) scenarios whose recomputed MEL fails to meet the target and (b) scenarios
whose recomputed MEL disagrees with the value stored in the file -- a data-quality
signal that the source study's arithmetic may be stale.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TypeGuard


@dataclass(frozen=True)
class LopaResult:
    """Outcome of recomputing a scenario's LOPA arithmetic."""

    initiating_frequency: float | None
    ipl_pfd_product: float
    modifier_product: float
    mel_calc: float | None
    tmel: float | None
    meets_tmel: bool | None
    required_rrf: float | None  # frequency / tmel -- the risk reduction LOPA must buy
    stored_mel: float | None
    mel_matches_stored: bool | None


def _product(values: Iterable[float]) -> float:
    total = 1.0
    for value in values:
        total *= value
    return total


def _valid_pfd(pfd: float | None) -> TypeGuard[float]:
    return pfd is not None and 0.0 < pfd <= 1.0


def recompute_lopa(
    *,
    initiating_frequency: float | None,
    ipl_pfds: Iterable[float | None],
    modifier_probabilities: Iterable[float | None],
    tmel: float | None,
    stored_mel: float | None = None,
) -> LopaResult:
    """Recompute a scenario's mitigated event likelihood and compare to targets.

    Only PFDs in ``(0, 1]`` count as protection layers; other values are ignored
    (an out-of-range PFD is bad data, not a credit).  ``mel_calc`` is ``None`` when
    the initiating frequency is unknown -- the arithmetic cannot start without it.
    """
    ipl_product = _product(p for p in ipl_pfds if _valid_pfd(p))
    modifier_product = _product(
        m for m in modifier_probabilities if _valid_pfd(m)
    )

    mel_calc: float | None = None
    if initiating_frequency is not None:
        mel_calc = initiating_frequency * ipl_product * modifier_product

    meets_tmel: bool | None = None
    if mel_calc is not None and tmel is not None:
        meets_tmel = mel_calc <= tmel

    required_rrf: float | None = None
    if initiating_frequency is not None and tmel not in (None, 0):
        required_rrf = initiating_frequency / tmel  # type: ignore[operator]

    mel_matches_stored: bool | None = None
    if mel_calc is not None and stored_mel is not None:
        # LOPA figures are order-of-magnitude estimates; treat a recomputed value
        # within a factor of two of the stored one as agreement.
        if mel_calc == 0 or stored_mel == 0:
            mel_matches_stored = math.isclose(mel_calc, stored_mel, abs_tol=1e-12)
        else:
            ratio = mel_calc / stored_mel
            mel_matches_stored = 0.5 <= ratio <= 2.0

    return LopaResult(
        initiating_frequency=initiating_frequency,
        ipl_pfd_product=ipl_product,
        modifier_product=modifier_product,
        mel_calc=mel_calc,
        tmel=tmel,
        meets_tmel=meets_tmel,
        required_rrf=required_rrf,
        stored_mel=stored_mel,
        mel_matches_stored=mel_matches_stored,
    )

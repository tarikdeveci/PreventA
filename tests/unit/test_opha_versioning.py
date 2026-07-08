"""Tests for OpenPHA data-structure revision handling (review item 5)."""

from __future__ import annotations

import pytest

from preventa.features.opha.versioning import KNOWN_DS_REVS, check_ds_rev


@pytest.mark.parametrize("rev", ["", "1", "2", "3", "4", "5"])
def test_known_ds_rev_produces_no_warnings(rev: str) -> None:
    assert check_ds_rev(rev) == []


def test_missing_ds_rev_warns_about_legacy_layout() -> None:
    warnings = check_ds_rev(None)
    assert len(warnings) == 1
    assert "no Settings.Ds_Rev" in warnings[0]


def test_unknown_ds_rev_warns_about_field_renames() -> None:
    warnings = check_ds_rev("99")
    assert len(warnings) == 1
    assert "Ds_Rev='99'" in warnings[0]
    # The message lists the known revisions, excluding the empty-string one.
    assert "1, 2, 3, 4, 5" in warnings[0]


def test_empty_string_is_recognised_not_missing() -> None:
    # "" is a known revision, so a present-but-empty value is safe, not "missing".
    assert "" in KNOWN_DS_REVS
    assert check_ds_rev("") == []

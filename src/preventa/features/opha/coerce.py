"""Typed coercion helpers for OpenPHA's stringly-typed values.

OpenPHA stores every scalar as a string — numbers as ``"1E-5"`` / ``"1000"``,
booleans as ``"true"`` / ``"false"``, and absent values as ``""`` or the literal
``"null"``.  These helpers turn those into real Python types for consumers
(e.g. a future ORM mapping) without ever mutating the source document, so the
round-trip stays lossless.
"""

from __future__ import annotations

_NULLISH = {"", "null", "none", "undefined"}


def as_str(value: object) -> str | None:
    """Return a cleaned string, or ``None`` for OpenPHA's null-ish markers."""
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in _NULLISH:
        return None
    return text


def as_float(value: object) -> float | None:
    """Parse an OpenPHA numeric string (``"1E-5"``, ``"1000"``) into a float."""
    text = as_str(value)
    if text is None:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def as_int(value: object) -> int | None:
    """Parse an OpenPHA integer string into an int (tolerating ``"3.0"``)."""
    text = as_str(value)
    if text is None:
        return None
    try:
        return int(text)
    except ValueError:
        try:
            return int(float(text))
        except ValueError:
            return None


def as_bool(value: object) -> bool | None:
    """Parse OpenPHA's ``"true"`` / ``"false"`` (and common variants)."""
    text = as_str(value)
    if text is None:
        return None
    lowered = text.lower()
    if lowered in {"true", "1", "yes", "y"}:
        return True
    if lowered in {"false", "0", "no", "n"}:
        return False
    return None


def id_list(value: object) -> list[str]:
    """Flatten OpenPHA link arrays (``[{"ID": "abc"}, ...]``) to plain IDs.

    Also tolerates already-flat ``["abc", ...]`` lists and drops empties.
    """
    if not isinstance(value, list):
        return []
    ids: list[str] = []
    for item in value:
        if isinstance(item, dict):
            ident = as_str(item.get("ID"))
        else:
            ident = as_str(item)
        if ident is not None:
            ids.append(ident)
    return ids

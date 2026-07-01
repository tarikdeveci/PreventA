"""OpenPHA (``.opha``) import/export for PreventA.

Public API::

    study = load_opha(path_or_dict)   # parse a .opha document into a typed view
    doc   = dump_opha(study)          # serialise back (lossless round-trip)

The round-trip is exact: ``dump_opha(load_opha(doc)) == doc``.  See
``preventa.features.opha.model`` for the navigable, typed accessors.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from preventa.features.opha.model import OphaStudy

__all__ = ["OphaStudy", "dump_opha", "dumps_opha", "load_opha", "loads_opha"]


def load_opha(source: str | Path | dict[str, Any]) -> OphaStudy:
    """Parse a ``.opha`` document from a path, or wrap an already-parsed dict."""
    if isinstance(source, dict):
        return OphaStudy(source)
    text = Path(source).read_text(encoding="utf-8")
    return loads_opha(text)


def loads_opha(text: str) -> OphaStudy:
    """Parse a ``.opha`` document from a JSON string."""
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("An .opha document must be a JSON object at the top level.")
    return OphaStudy(data)


def dump_opha(study: OphaStudy) -> dict[str, Any]:
    """Return the OpenPHA document dict for ``study`` (lossless)."""
    return study.to_opha()


def dumps_opha(study: OphaStudy, *, indent: int | None = None) -> str:
    """Serialise ``study`` back to a ``.opha`` JSON string."""
    return json.dumps(study.to_opha(), ensure_ascii=False, indent=indent)

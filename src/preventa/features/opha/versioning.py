"""OpenPHA data-structure revision (``Ds_Rev``) handling.

OpenPHA stamps every file with ``Settings.Ds_Rev`` -- the revision of its data
structure.  When OpenPHA renames or restructures fields in a new release it bumps
this value.  PreventA records the revision on import (item 5 of the review) and
uses this module to decide whether the file is one it understands, so a file from
a newer or older version fails loudly with a clear message instead of silently
importing garbage.

``KNOWN_DS_REVS`` lists the revisions whose field layout this importer was built
and tested against.  Extend it (and add any field-rename branches to the mapping)
when a new OpenPHA revision is verified.
"""

from __future__ import annotations

# Revisions this importer has been verified against. The real ANAGOLD / ENTEK
# DRES exports the mapping was built from carry these; extend as new OpenPHA
# releases are checked.
KNOWN_DS_REVS: frozenset[str] = frozenset({"", "1", "2", "3", "4", "5"})


def check_ds_rev(ds_rev: str | None) -> list[str]:
    """Return human-readable warnings about an OpenPHA file's ``Ds_Rev``.

    An empty list means the revision is recognised and safe to import.  A missing
    revision is warned about (older files predate the field); an unrecognised
    revision is warned about because field names may have changed.
    """
    warnings: list[str] = []
    if ds_rev is None:
        warnings.append(
            "OpenPHA file has no Settings.Ds_Rev; assuming a legacy layout. "
            "Verify the import if fields look wrong."
        )
        return warnings
    if ds_rev not in KNOWN_DS_REVS:
        warnings.append(
            f"OpenPHA data-structure revision Ds_Rev={ds_rev!r} is newer or older "
            f"than the revisions this importer was tested against "
            f"({', '.join(sorted(r for r in KNOWN_DS_REVS if r))}). "
            "Some fields may have been renamed; review the import."
        )
    return warnings

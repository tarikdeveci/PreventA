"""Render an OpenPHA ``Risk_Criteria`` object into a display grid (item 3).

The live app used to draw a synthetic 5x5 matrix. This turns the client's real
``Risk_Criteria`` -- its own likelihoods, per-category severities, intersection
cells, and coloured risk ranks -- into a compact structure the React matrix view
can render as-is, so what the facilitator sees IS the client's matrix.
"""

from __future__ import annotations

from typing import Any

from preventa.features.opha.risk import RiskMatrixResolver


def build_client_matrix(criteria: dict[str, Any] | None) -> dict[str, Any] | None:
    """Return a render-ready matrix view, or ``None`` when there is no usable matrix.

    Shape::

        {
          "categories": ["Safety", "Environment"],   # [] when single-axis
          "grids": [
            {
              "category": "Safety",
              "severities": ["Safety 1", "Safety 2", "Safety 3"],
              "rows": [                                # high likelihood first
                {"likelihood": "Frequent",
                 "cells": [{"rank": "Medium", "color": "#b3771a"}, ...]},
                ...
              ],
            },
            ...
          ],
        }
    """
    if not criteria:
        return None
    resolver = RiskMatrixResolver.from_criteria(criteria)
    likelihoods = resolver.likelihood_levels()
    if not likelihoods or not resolver.severity_levels():
        return None

    categories = resolver.categories()
    # ``None`` means "single severity axis" -- one grid over every severity.
    category_keys: list[str | None] = list(categories) if categories else [None]

    grids: list[dict[str, Any]] = []
    for category in category_keys:
        severities = resolver.severity_levels(category)
        if not severities:
            continue
        rows: list[dict[str, Any]] = []
        for likelihood in reversed(likelihoods):  # highest likelihood on top
            cells: list[dict[str, Any]] = []
            for severity in severities:
                rank = resolver.rank_for(likelihood.id, severity.id)
                cells.append(
                    {
                        "rank": rank.name if rank else None,
                        "color": rank.color if rank else None,
                    }
                )
            rows.append({"likelihood": likelihood.name or likelihood.id, "cells": cells})
        grids.append(
            {
                "category": category or "Risk",
                "severities": [level.name or level.id for level in severities],
                "rows": rows,
            }
        )

    if not grids:
        return None
    return {"categories": list(categories), "grids": grids}

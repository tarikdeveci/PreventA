"""Durable persistence of a parsed OpenPHA study into PreventA's Postgres store.

This is the async ORM path (Roadmap P3): unlike the SQLite MVP importer in
``features/workspace/opha_import.py`` — which flattens the study into ``mvp_*``
tables for the running app — this writes the full OpenPHA hierarchy
(Study -> Node -> Deviation -> Cause -> Consequence, plus Safeguards, LOPA layers
and Recommendations) into the relational schema defined in ``db/models/hazop.py``.

The caller owns the transaction boundary so the write can be composed with other
work in the same unit of work.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from preventa.db.models.hazop import Study
from preventa.features.opha.model import OphaStudy
from preventa.features.opha.orm_mapping import to_orm


async def persist_opha_study(session: AsyncSession, opha: OphaStudy) -> Study:
    """Persist ``opha`` as a full ORM graph and return the saved ``Study``.

    ``to_orm`` builds the unpersisted tree; a single ``session.add`` cascades to
    every child (all relationships use ``cascade="all, delete-orphan"``). The
    flush assigns primary keys without committing, leaving the transaction
    boundary to the caller.
    """
    study = to_orm(opha)
    session.add(study)
    await session.flush()
    return study

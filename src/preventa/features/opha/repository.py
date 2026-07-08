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

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from preventa.db.models.hazop import (
    Cause,
    Consequence,
    Deviation,
    Lopa,
    Node,
    Recommendation,
    Study,
)
from preventa.db.models.registers import Session as OphaSession
from preventa.features.opha.export import orm_to_opha
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


async def export_opha_study(session: AsyncSession, study_id: UUID | str) -> dict[str, Any]:
    """Load a persisted study and rebuild its OpenPHA (``.opha``) document (item 1).

    Symmetric with :func:`persist_opha_study`: it eager-loads the whole ORM graph
    (so ``orm_to_opha`` never triggers a lazy load under async) and reconstructs
    the ``.opha`` document from the database -- the reverse export that lets an
    edited study become a client-ready deliverable.  Raises ``LookupError`` if no
    study matches ``study_id``.
    """
    consequences = (
        selectinload(Study.nodes)
        .selectinload(Node.deviations)
        .selectinload(Deviation.causes)
        .selectinload(Cause.consequences)
    )
    stmt = (
        select(Study)
        .where(Study.id == study_id)
        .options(
            consequences.selectinload(Consequence.safeguards),
            consequences.selectinload(Consequence.recommendations),
            consequences.selectinload(Consequence.lopa).selectinload(Lopa.modifiers),
            selectinload(Study.safeguards),
            selectinload(Study.recommendations).selectinload(Recommendation.consequences),
            selectinload(Study.risk_matrix),
            selectinload(Study.team_members),
            selectinload(Study.sessions).selectinload(OphaSession.attendees),
            selectinload(Study.drawings),
            selectinload(Study.parking_lot),
            selectinload(Study.mocs),
            selectinload(Study.scais),
            selectinload(Study.incidents),
            selectinload(Study.checklists),
        )
    )
    study = (await session.execute(stmt)).scalar_one_or_none()
    if study is None:
        raise LookupError(f"No study with id {study_id!r}")
    return orm_to_opha(study)

"""Preserve original OpenPHA IDs on imported entities.

Adds a nullable ``opha_id`` to nodes, deviations, causes, consequences,
safeguards and recommendations so an imported ``.opha`` study keeps its native
identity (used to resolve links and to re-export losslessly).

Revision ID: 20260701_0003
Revises: 20260701_0002
Create Date: 2026-07-01
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260701_0003"
down_revision: str | None = "20260701_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = (
    "nodes",
    "deviations",
    "causes",
    "consequences",
    "safeguards",
    "recommendations",
)


def upgrade() -> None:
    for table in _TABLES:
        op.execute(f"ALTER TABLE {table} ADD COLUMN opha_id VARCHAR(64)")
        op.execute(f"CREATE INDEX ix_{table}_opha_id ON {table}(opha_id)")


def downgrade() -> None:
    for table in _TABLES:
        op.execute(f"DROP INDEX IF EXISTS ix_{table}_opha_id")
        op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS opha_id")

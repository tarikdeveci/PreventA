"""Apply the OpenPHA review improvements (items 1-6).

* item 2 -- recommendations become many-to-many with consequences: drop the
  single ``recommendations.consequence_id`` FK and add a ``consequence_recommendation``
  link table (mirrors ``consequence_safeguard``).
* item 5 -- record the OpenPHA data-structure revision on the study (``ds_rev``).
* item 4 -- LOPA becomes a check: itemise conditional modifiers into
  ``lopa_modifiers`` and store the recomputed ``mel_calc`` / ``meets_tmel``.
* item 3 -- multi-category severity: ``consequences.severity_by_category`` JSON.
* item 6 -- supporting registers: team members, sessions (+ attendance),
  drawings, parking lot, MOCs, SCAIs, incidents and checklists.

Revision ID: 20260708_0004
Revises: 20260701_0003
Create Date: 2026-07-08
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260708_0004"
down_revision: str | None = "20260701_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        -- item 2: recommendations many-to-many ---------------------------- --
        DROP INDEX IF EXISTS ix_recommendations_consequence_id;
        ALTER TABLE recommendations DROP COLUMN IF EXISTS consequence_id;
        CREATE TABLE consequence_recommendation (
            consequence_id UUID NOT NULL
                REFERENCES consequences(id) ON DELETE CASCADE,
            recommendation_id UUID NOT NULL
                REFERENCES recommendations(id) ON DELETE CASCADE,
            PRIMARY KEY (consequence_id, recommendation_id)
        );

        -- item 5: OpenPHA data-structure revision ------------------------- --
        ALTER TABLE studies ADD COLUMN ds_rev VARCHAR(32);

        -- item 3: multi-category severity --------------------------------- --
        ALTER TABLE consequences ADD COLUMN severity_by_category TEXT;

        -- item 4: LOPA as a check ----------------------------------------- --
        ALTER TABLE lopa ADD COLUMN mel_calc DOUBLE PRECISION;
        ALTER TABLE lopa ADD COLUMN meets_tmel BOOLEAN;
        CREATE TABLE lopa_modifiers (
            id UUID PRIMARY KEY,
            lopa_id UUID NOT NULL REFERENCES lopa(id) ON DELETE CASCADE,
            opha_id VARCHAR(64),
            description TEXT,
            probability DOUBLE PRECISION,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_lopa_modifiers_lopa_id ON lopa_modifiers(lopa_id);
        CREATE INDEX ix_lopa_modifiers_opha_id ON lopa_modifiers(opha_id);

        -- item 6: supporting registers ------------------------------------ --
        CREATE TABLE team_members (
            id UUID PRIMARY KEY,
            study_id UUID NOT NULL REFERENCES studies(id) ON DELETE CASCADE,
            opha_id VARCHAR(64),
            name VARCHAR(255),
            role VARCHAR(255),
            company VARCHAR(255),
            email VARCHAR(255),
            raw TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_team_members_study_id ON team_members(study_id);
        CREATE INDEX ix_team_members_opha_id ON team_members(opha_id);

        CREATE TABLE sessions (
            id UUID PRIMARY KEY,
            study_id UUID NOT NULL REFERENCES studies(id) ON DELETE CASCADE,
            opha_id VARCHAR(64),
            session_date DATE,
            description TEXT,
            raw TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_sessions_study_id ON sessions(study_id);
        CREATE INDEX ix_sessions_opha_id ON sessions(opha_id);

        CREATE TABLE session_attendance (
            session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            team_member_id UUID NOT NULL
                REFERENCES team_members(id) ON DELETE CASCADE,
            PRIMARY KEY (session_id, team_member_id)
        );

        CREATE TABLE drawings (
            id UUID PRIMARY KEY,
            study_id UUID NOT NULL REFERENCES studies(id) ON DELETE CASCADE,
            opha_id VARCHAR(64),
            number VARCHAR(255),
            title TEXT,
            raw TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_drawings_study_id ON drawings(study_id);
        CREATE INDEX ix_drawings_opha_id ON drawings(opha_id);

        CREATE TABLE parking_lot_items (
            id UUID PRIMARY KEY,
            study_id UUID NOT NULL REFERENCES studies(id) ON DELETE CASCADE,
            opha_id VARCHAR(64),
            text TEXT,
            raw TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_parking_lot_items_study_id ON parking_lot_items(study_id);
        CREATE INDEX ix_parking_lot_items_opha_id ON parking_lot_items(opha_id);

        CREATE TABLE mocs (
            id UUID PRIMARY KEY,
            study_id UUID NOT NULL REFERENCES studies(id) ON DELETE CASCADE,
            opha_id VARCHAR(64),
            number VARCHAR(255),
            title TEXT,
            status VARCHAR(64),
            raw TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_mocs_study_id ON mocs(study_id);
        CREATE INDEX ix_mocs_opha_id ON mocs(opha_id);

        CREATE TABLE scais (
            id UUID PRIMARY KEY,
            study_id UUID NOT NULL REFERENCES studies(id) ON DELETE CASCADE,
            opha_id VARCHAR(64),
            tag VARCHAR(255),
            description TEXT,
            raw TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_scais_study_id ON scais(study_id);
        CREATE INDEX ix_scais_opha_id ON scais(opha_id);

        CREATE TABLE incidents (
            id UUID PRIMARY KEY,
            study_id UUID NOT NULL REFERENCES studies(id) ON DELETE CASCADE,
            opha_id VARCHAR(64),
            kind VARCHAR(32),
            title TEXT,
            description TEXT,
            raw TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_incidents_study_id ON incidents(study_id);
        CREATE INDEX ix_incidents_opha_id ON incidents(opha_id);

        CREATE TABLE checklists (
            id UUID PRIMARY KEY,
            study_id UUID NOT NULL REFERENCES studies(id) ON DELETE CASCADE,
            opha_id VARCHAR(64),
            name TEXT,
            raw TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_checklists_study_id ON checklists(study_id);
        CREATE INDEX ix_checklists_opha_id ON checklists(opha_id);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS checklists;
        DROP TABLE IF EXISTS incidents;
        DROP TABLE IF EXISTS scais;
        DROP TABLE IF EXISTS mocs;
        DROP TABLE IF EXISTS parking_lot_items;
        DROP TABLE IF EXISTS drawings;
        DROP TABLE IF EXISTS session_attendance;
        DROP TABLE IF EXISTS sessions;
        DROP TABLE IF EXISTS team_members;

        DROP TABLE IF EXISTS lopa_modifiers;
        ALTER TABLE lopa DROP COLUMN IF EXISTS meets_tmel;
        ALTER TABLE lopa DROP COLUMN IF EXISTS mel_calc;

        ALTER TABLE consequences DROP COLUMN IF EXISTS severity_by_category;
        ALTER TABLE studies DROP COLUMN IF EXISTS ds_rev;

        DROP TABLE IF EXISTS consequence_recommendation;
        ALTER TABLE recommendations
            ADD COLUMN consequence_id UUID
            REFERENCES consequences(id) ON DELETE SET NULL;
        CREATE INDEX ix_recommendations_consequence_id
            ON recommendations(consequence_id);
        """
    )

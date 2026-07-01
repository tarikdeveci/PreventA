"""Refactor the flat HAZOP worksheet into the OpenPHA hierarchy.

Replaces ``hazop_nodes`` + ``hazop_worksheet_rows`` with the real OpenPHA tree
(Study -> Node -> Deviation -> Cause -> Consequence) plus structured Safeguards
(IPL/SIL), a per-Consequence LOPA layer, Recommendations and a configurable
Risk matrix.  RAG suggestions now ground a Consequence instead of the dropped
flat worksheet row.

This is a destructive, pre-production migration: per the OpenPHA compatibility
review, PreventA is still at MVP stage with no real production data to migrate,
so the flat tables are dropped rather than transformed.

Revision ID: 20260701_0002
Revises: 20260612_0001
Create Date: 2026-07-01
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260701_0002"
down_revision: str | None = "20260612_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        -- 1. Detach and drop the flat model -------------------------------- --
        ALTER TABLE rag_suggestions DROP COLUMN IF EXISTS worksheet_row_id;
        DROP TABLE IF EXISTS hazop_worksheet_rows;
        DROP TABLE IF EXISTS hazop_nodes;

        -- 2. New enums (study_status / review_status already exist) --------- --
        CREATE TYPE analysis_mode AS ENUM ('HAZOP', 'WHAT_IF', 'CHECKLIST');
        CREATE TYPE recommendation_kind AS ENUM ('PHA', 'LOPA');

        -- 3. Extend the Study (Overview + Settings) ------------------------- --
        ALTER TABLE studies
            ADD COLUMN coordinator VARCHAR(255),
            ADD COLUMN coordinator_contact VARCHAR(255),
            ADD COLUMN pha_type VARCHAR(100),
            ADD COLUMN facility_location VARCHAR(255),
            ADD COLUMN facility_owner VARCHAR(255),
            ADD COLUMN company VARCHAR(255),
            ADD COLUMN site VARCHAR(255),
            ADD COLUMN plant VARCHAR(255),
            ADD COLUMN unit VARCHAR(255),
            ADD COLUMN report_number VARCHAR(100),
            ADD COLUMN project_number VARCHAR(100),
            ADD COLUMN project_description TEXT,
            ADD COLUMN general_notes TEXT,
            ADD COLUMN revalidation_due_date DATE,
            ADD COLUMN analysis_mode analysis_mode NOT NULL DEFAULT 'HAZOP',
            ADD COLUMN lopa_enabled BOOLEAN NOT NULL DEFAULT true;

        -- 4. Node --------------------------------------------------------- --
        CREATE TABLE nodes (
            id UUID PRIMARY KEY,
            study_id UUID NOT NULL REFERENCES studies(id) ON DELETE CASCADE,
            description TEXT NOT NULL,
            intention TEXT,
            boundary TEXT,
            design_conditions TEXT,
            operating_conditions TEXT,
            hazardous_materials TEXT,
            equipment_tags TEXT,
            location VARCHAR(255),
            comments TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_nodes_study_id ON nodes(study_id);

        -- 5. Deviation ---------------------------------------------------- --
        CREATE TABLE deviations (
            id UUID PRIMARY KEY,
            node_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
            parameter VARCHAR(100) NOT NULL,
            guideword VARCHAR(100) NOT NULL,
            deviation TEXT NOT NULL,
            design_intent TEXT,
            comments TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_deviations_node_id ON deviations(node_id);

        -- 6. Cause -------------------------------------------------------- --
        CREATE TABLE causes (
            id UUID PRIMARY KEY,
            deviation_id UUID NOT NULL REFERENCES deviations(id) ON DELETE CASCADE,
            cause TEXT NOT NULL,
            cause_type VARCHAR(100),
            enabling_events TEXT,
            frequency DOUBLE PRECISION,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_causes_deviation_id ON causes(deviation_id);

        -- 7. Consequence (the HAZOP scenario, three-state risk) ----------- --
        CREATE TABLE consequences (
            id UUID PRIMARY KEY,
            cause_id UUID NOT NULL REFERENCES causes(id) ON DELETE CASCADE,
            consequence TEXT NOT NULL,
            consequence_type_id VARCHAR(64),
            severity_before INTEGER,
            likelihood_before INTEGER,
            risk_rank_before VARCHAR(32),
            severity_current INTEGER,
            likelihood_current INTEGER,
            risk_rank_current VARCHAR(32),
            severity_after_recs INTEGER,
            likelihood_after_recs INTEGER,
            risk_rank_after_recs VARCHAR(32),
            review_status review_status NOT NULL DEFAULT 'DRAFT',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_consequences_cause_id ON consequences(cause_id);

        -- 8. Safeguard (structured IPL / SIL) ----------------------------- --
        CREATE TABLE safeguards (
            id UUID PRIMARY KEY,
            study_id UUID NOT NULL REFERENCES studies(id) ON DELETE CASCADE,
            description TEXT NOT NULL,
            safeguard_type VARCHAR(100),
            category VARCHAR(100),
            ipl_tag VARCHAR(100),
            is_safeguard BOOLEAN NOT NULL DEFAULT true,
            independent BOOLEAN,
            auditable BOOLEAN,
            effective BOOLEAN,
            is_ipl BOOLEAN NOT NULL DEFAULT false,
            pfd DOUBLE PRECISION,
            safety_critical BOOLEAN,
            selected_sil INTEGER,
            required_response_time VARCHAR(64),
            test_interval VARCHAR(64),
            comments TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_safeguards_study_id ON safeguards(study_id);

        -- 9. Consequence <-> Safeguard (m2m) ------------------------------ --
        CREATE TABLE consequence_safeguard (
            consequence_id UUID NOT NULL
                REFERENCES consequences(id) ON DELETE CASCADE,
            safeguard_id UUID NOT NULL
                REFERENCES safeguards(id) ON DELETE CASCADE,
            PRIMARY KEY (consequence_id, safeguard_id)
        );

        -- 10. LOPA layer (1:1 with Consequence) --------------------------- --
        CREATE TABLE lopa (
            id UUID PRIMARY KEY,
            consequence_id UUID NOT NULL UNIQUE
                REFERENCES consequences(id) ON DELETE CASCADE,
            lopa_required BOOLEAN NOT NULL DEFAULT false,
            recommended_sil INTEGER,
            tmel DOUBLE PRECISION,
            mel DOUBLE PRECISION,
            lopa_ratio DOUBLE PRECISION,
            rrf DOUBLE PRECISION,
            alarp_required BOOLEAN,
            conditional_modifiers TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        -- 11. Recommendation (PHA + LOPA) --------------------------------- --
        CREATE TABLE recommendations (
            id UUID PRIMARY KEY,
            study_id UUID NOT NULL REFERENCES studies(id) ON DELETE CASCADE,
            consequence_id UUID REFERENCES consequences(id) ON DELETE SET NULL,
            kind recommendation_kind NOT NULL,
            text TEXT NOT NULL,
            priority VARCHAR(32),
            responsible_party VARCHAR(255),
            status VARCHAR(64),
            due_date DATE,
            pfd DOUBLE PRECISION,
            comments TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_recommendations_study_id ON recommendations(study_id);
        CREATE INDEX ix_recommendations_consequence_id
            ON recommendations(consequence_id);

        -- 12. Risk matrix (configurable Risk_Criteria) -------------------- --
        CREATE TABLE risk_matrices (
            id UUID PRIMARY KEY,
            study_id UUID NOT NULL UNIQUE
                REFERENCES studies(id) ON DELETE CASCADE,
            likelihoods TEXT,
            severities TEXT,
            intersections TEXT,
            risk_rankings TEXT,
            alarp_categories TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

        -- 13. Re-ground RAG suggestions on Consequence -------------------- --
        ALTER TABLE rag_suggestions
            ADD COLUMN consequence_id UUID
                REFERENCES consequences(id) ON DELETE SET NULL;
        CREATE INDEX ix_rag_suggestions_consequence_id
            ON rag_suggestions(consequence_id);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        -- Reverse of upgrade(): restore the flat model. -------------------- --
        ALTER TABLE rag_suggestions DROP COLUMN IF EXISTS consequence_id;

        DROP TABLE IF EXISTS risk_matrices;
        DROP TABLE IF EXISTS recommendations;
        DROP TABLE IF EXISTS lopa;
        DROP TABLE IF EXISTS consequence_safeguard;
        DROP TABLE IF EXISTS safeguards;
        DROP TABLE IF EXISTS consequences;
        DROP TABLE IF EXISTS causes;
        DROP TABLE IF EXISTS deviations;
        DROP TABLE IF EXISTS nodes;

        ALTER TABLE studies
            DROP COLUMN IF EXISTS coordinator,
            DROP COLUMN IF EXISTS coordinator_contact,
            DROP COLUMN IF EXISTS pha_type,
            DROP COLUMN IF EXISTS facility_location,
            DROP COLUMN IF EXISTS facility_owner,
            DROP COLUMN IF EXISTS company,
            DROP COLUMN IF EXISTS site,
            DROP COLUMN IF EXISTS plant,
            DROP COLUMN IF EXISTS unit,
            DROP COLUMN IF EXISTS report_number,
            DROP COLUMN IF EXISTS project_number,
            DROP COLUMN IF EXISTS project_description,
            DROP COLUMN IF EXISTS general_notes,
            DROP COLUMN IF EXISTS revalidation_due_date,
            DROP COLUMN IF EXISTS analysis_mode,
            DROP COLUMN IF EXISTS lopa_enabled;

        DROP TYPE IF EXISTS recommendation_kind;
        DROP TYPE IF EXISTS analysis_mode;

        CREATE TABLE hazop_nodes (
            id UUID PRIMARY KEY,
            study_id UUID NOT NULL REFERENCES studies(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            design_intent TEXT NOT NULL,
            equipment_type VARCHAR(100),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_hazop_nodes_study_id ON hazop_nodes(study_id);
        CREATE INDEX ix_hazop_nodes_equipment_type ON hazop_nodes(equipment_type);

        CREATE TABLE hazop_worksheet_rows (
            id UUID PRIMARY KEY,
            node_id UUID NOT NULL REFERENCES hazop_nodes(id) ON DELETE CASCADE,
            parameter VARCHAR(100) NOT NULL,
            guideword VARCHAR(100) NOT NULL,
            deviation TEXT NOT NULL,
            cause TEXT,
            consequence TEXT,
            safeguard TEXT,
            review_status review_status NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_hazop_worksheet_rows_node_id
            ON hazop_worksheet_rows(node_id);

        ALTER TABLE rag_suggestions
            ADD COLUMN worksheet_row_id UUID
                REFERENCES hazop_worksheet_rows(id) ON DELETE SET NULL;
        CREATE INDEX ix_rag_suggestions_worksheet_row_id
            ON rag_suggestions(worksheet_row_id);
        """
    )

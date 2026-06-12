"""Initial HAZOP and grounded RAG schema.

Revision ID: 20260612_0001
Revises:
Create Date: 2026-06-12
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260612_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        CREATE TYPE study_status AS ENUM ('DRAFT', 'IN_REVIEW', 'APPROVED', 'ARCHIVED');
        CREATE TYPE review_status AS ENUM ('DRAFT', 'ACCEPTED', 'EDITED', 'REJECTED');

        CREATE TABLE studies (
            id UUID PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            facility VARCHAR(255),
            status study_status NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );

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
        CREATE INDEX ix_hazop_worksheet_rows_node_id ON hazop_worksheet_rows(node_id);

        CREATE TABLE knowledge_documents (
            id UUID PRIMARY KEY,
            title VARCHAR(500) NOT NULL,
            source_type VARCHAR(50) NOT NULL,
            source_ref VARCHAR(500) NOT NULL UNIQUE,
            version VARCHAR(100),
            is_active BOOLEAN NOT NULL DEFAULT true,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_knowledge_documents_source_type
            ON knowledge_documents(source_type);

        CREATE TABLE knowledge_chunks (
            id UUID PRIMARY KEY,
            document_id UUID NOT NULL
                REFERENCES knowledge_documents(id) ON DELETE CASCADE,
            ordinal INTEGER NOT NULL,
            section_ref VARCHAR(255),
            content TEXT NOT NULL,
            content_tsv TSVECTOR GENERATED ALWAYS AS (
                to_tsvector('english', coalesce(content, ''))
            ) STORED,
            embedding VECTOR(768) NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE(document_id, ordinal)
        );
        CREATE INDEX ix_knowledge_chunks_document_id
            ON knowledge_chunks(document_id);
        CREATE INDEX ix_knowledge_chunks_content_tsv
            ON knowledge_chunks USING GIN(content_tsv);
        CREATE INDEX ix_knowledge_chunks_embedding_hnsw
            ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);

        CREATE TABLE rag_suggestions (
            id UUID PRIMARY KEY,
            worksheet_row_id UUID
                REFERENCES hazop_worksheet_rows(id) ON DELETE SET NULL,
            prompt_version VARCHAR(50) NOT NULL,
            model_name VARCHAR(100) NOT NULL,
            request_payload JSONB NOT NULL,
            response_payload JSONB NOT NULL,
            status VARCHAR(50) NOT NULL,
            block_reason TEXT,
            reviewer_notes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_rag_suggestions_worksheet_row_id
            ON rag_suggestions(worksheet_row_id);
        CREATE INDEX ix_rag_suggestions_status ON rag_suggestions(status);

        CREATE TABLE retrieval_traces (
            id UUID PRIMARY KEY,
            suggestion_id UUID NOT NULL
                REFERENCES rag_suggestions(id) ON DELETE CASCADE,
            chunk_id UUID NOT NULL
                REFERENCES knowledge_chunks(id) ON DELETE RESTRICT,
            dense_rank INTEGER,
            sparse_rank INTEGER,
            fused_score DOUBLE PRECISION NOT NULL,
            rerank_score DOUBLE PRECISION,
            was_cited BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_retrieval_traces_suggestion_id
            ON retrieval_traces(suggestion_id);
        CREATE INDEX ix_retrieval_traces_chunk_id
            ON retrieval_traces(chunk_id);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE IF EXISTS retrieval_traces;
        DROP TABLE IF EXISTS rag_suggestions;
        DROP TABLE IF EXISTS knowledge_chunks;
        DROP TABLE IF EXISTS knowledge_documents;
        DROP TABLE IF EXISTS hazop_worksheet_rows;
        DROP TABLE IF EXISTS hazop_nodes;
        DROP TABLE IF EXISTS studies;
        DROP TYPE IF EXISTS review_status;
        DROP TYPE IF EXISTS study_status;
        """
    )


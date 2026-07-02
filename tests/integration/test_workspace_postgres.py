"""Durable-storage integration test: the SQLite MVP store running on Postgres.

Gated on ``PREVENTA_STORE_TEST_DSN`` (a sync ``postgresql://`` URL) so the default
suite stays on SQLite. Point it at a disposable Postgres, e.g. the compose
service::

    PREVENTA_STORE_TEST_DSN=postgresql://preventa:preventa@localhost:5432/preventa \
        .venv/Scripts/python.exe -m pytest tests/integration/test_workspace_postgres.py

It exercises every SQLite-ism the Postgres shim has to translate: ``?``
placeholders, ``INSERT OR IGNORE`` (risk matrix), ``ON CONFLICT`` upserts
(risk-matrix update, import dedup), ``RETURNING id`` (row creation) and the
backend-agnostic integrity-error handling in the auth repository.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import psycopg2
import pytest

from preventa.features.auth.repository import AuthRepository
from preventa.features.auth.schemas import UserCreate
from preventa.features.opha import load_opha
from preventa.features.workspace.crud_schemas import (
    LopaLayerCreate,
    NodeCreate,
    RiskMatrixUpdate,
    RowCreate,
    StudyCreate,
)
from preventa.features.workspace.opha_import import import_opha_study
from preventa.features.workspace.repository import WorkspaceRepository

STORE_DSN = os.getenv("PREVENTA_STORE_TEST_DSN")
FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "synthetic.opha"

pytestmark = pytest.mark.skipif(
    not STORE_DSN,
    reason="set PREVENTA_STORE_TEST_DSN to a disposable Postgres to run",
)

_TABLES = (
    "mvp_imports",
    "mvp_reports",
    "mvp_risk_matrix",
    "mvp_sources",
    "mvp_library",
    "mvp_audit",
    "mvp_lopa_layers",
    "mvp_rows",
    "mvp_nodes",
    "mvp_studies",
    "app_revoked_sessions",
    "app_sessions",
    "app_users",
)


def _drop_all() -> None:
    assert STORE_DSN is not None
    conn = psycopg2.connect(STORE_DSN)
    try:
        with conn.cursor() as cur:
            for table in _TABLES:
                cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def pg_store(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("PREVENTA_STORE_DSN", STORE_DSN or "")
    _drop_all()  # start clean; initialize_store recreates the schema
    try:
        yield
    finally:
        _drop_all()


def test_workspace_crud_on_postgres(pg_store: None) -> None:
    repo = WorkspaceRepository()  # initialize_store() creates the schema on Postgres

    study = repo.create_study(
        StudyCreate(title="PG Study", client="ACWA", facility="Konya")
    )
    study_id = str(study["id"])
    assert any(s["id"] == study_id for s in repo.list_studies())

    node = repo.create_node(
        study_id,
        NodeCreate(
            code="N-01",
            name="Pump P-1",
            equipment_type="Centrifugal pump",
            design_intent="Provide feed.",
        ),
    )
    node_id = str(node["id"])

    # RETURNING id must yield the generated serial primary key.
    row = repo.create_row(
        node_id,
        RowCreate(
            guideword="Yok",
            deviation="No flow",
            cause="Valve closed",
            consequence="Loss of feed",
            safeguard="Low-flow alarm",
            severity=4,
            likelihood=3,
            status="İncelendi",
        ),
    )
    row_id = int(row["id"])
    assert row["risk"] == "Kritik"  # 4 * 3 = 12
    assert repo.get_row(row_id) is not None

    # LOPA layer round-trips with a real boolean flag.
    repo.add_lopa_layer(
        row_id, LopaLayerCreate(description="SIS trip", pfd=1e-2, is_valid=True, note="")
    )
    layers = repo.list_lopa_layers(row_id)
    assert len(layers) == 1
    assert layers[0]["is_valid"] is True

    # INSERT OR IGNORE (create default) then ON CONFLICT upsert (bump revision).
    baseline = repo.get_risk_matrix(study_id)
    updated = repo.update_risk_matrix(
        study_id, RiskMatrixUpdate(low_max=4, medium_max=8, high_max=12)
    )
    assert updated["high_max"] == 12
    assert updated["revision"] == baseline["revision"] + 1


def test_opha_import_and_dedup_on_postgres(pg_store: None) -> None:
    repo = WorkspaceRepository()
    result = import_opha_study(repo, load_opha(FIXTURE))
    assert result["nodes"] == 1
    assert result["rows"] == 2

    # INSERT OR REPLACE dedup fingerprint round-trips on Postgres.
    repo.record_import("hash-abc", str(result["study_id"]), result)
    again = repo.find_import("hash-abc")
    assert again is not None
    assert again["study_id"] == result["study_id"]


def test_status_reports_durable_on_postgres(pg_store: None) -> None:
    from preventa.features.workspace.service import get_product_status

    status = get_product_status()
    assert status.persistence == "postgresql"
    database = next(module for module in status.modules if module.id == "database")
    assert database.status == "complete"


def test_duplicate_user_raises_on_postgres(pg_store: None) -> None:
    auth = AuthRepository()
    payload = UserCreate(
        email="dupe@example.com",
        full_name="Dupe",
        role="viewer",
        password="Sufficiently-Long-Passw0rd!",
    )
    auth.create_user(payload)
    # The unique-violation must be caught via the backend-agnostic tuple.
    with pytest.raises(ValueError, match="already exists"):
        auth.create_user(payload)

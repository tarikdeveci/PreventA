import json
from typing import Any, cast

from preventa.features.workspace.crud_schemas import (
    LibraryEntryCreate,
    LopaLayerCreate,
    NodeCreate,
    NodeUpdate,
    RiskMatrixUpdate,
    RowCreate,
    RowUpdate,
    SourceCreate,
    SourceUpdate,
    StudyCreate,
    StudyUpdate,
)
from preventa.features.workspace.store import (
    audit,
    connection,
    initialize_store,
    new_id,
    risk_label,
    row_dict,
)


class WorkspaceRepository:
    def __init__(self) -> None:
        initialize_store()

    def list_studies(self) -> list[dict[str, Any]]:
        with connection() as database:
            rows = database.execute(
                """
                SELECT s.*, COUNT(n.id) AS node_count
                FROM mvp_studies s
                LEFT JOIN mvp_nodes n ON n.study_id = s.id
                GROUP BY s.id
                ORDER BY s.created_at DESC
                """
            ).fetchall()
            return [row_dict(row) for row in rows]

    def create_study(self, payload: StudyCreate) -> dict[str, Any]:
        study_id = new_id("study")
        with connection() as database:
            database.execute(
                """
                INSERT INTO mvp_studies (id, title, client, facility)
                VALUES (?, ?, ?, ?)
                """,
                (study_id, payload.title, payload.client, payload.facility),
            )
            audit(database, "study", study_id, "created")
        return {**payload.model_dump(), "id": study_id, "status": "draft", "node_count": 0}

    def get_study(self, study_id: str) -> dict[str, Any] | None:
        with connection() as database:
            row = database.execute(
                "SELECT * FROM mvp_studies WHERE id = ?",
                (study_id,),
            ).fetchone()
            return row_dict(row) if row else None

    def update_study(self, study_id: str, payload: StudyUpdate) -> dict[str, Any] | None:
        values = payload.model_dump(exclude_none=True)
        if not values:
            return self.get_study(study_id)
        assignments = ", ".join(f"{field} = ?" for field in values)
        with connection() as database:
            cursor = database.execute(
                f"UPDATE mvp_studies SET {assignments} WHERE id = ?",  # noqa: S608
                (*values.values(), study_id),
            )
            if cursor.rowcount:
                audit(database, "study", study_id, "updated")
        return self.get_study(study_id)

    def delete_study(self, study_id: str) -> bool:
        with connection() as database:
            cursor = database.execute("DELETE FROM mvp_studies WHERE id = ?", (study_id,))
            if cursor.rowcount:
                audit(database, "study", study_id, "deleted")
            return bool(cursor.rowcount)

    def list_nodes(self, study_id: str) -> list[dict[str, Any]]:
        with connection() as database:
            rows = database.execute(
                """
                SELECT n.*, COUNT(r.id) AS scenario_count
                FROM mvp_nodes n
                LEFT JOIN mvp_rows r ON r.node_id = n.id
                WHERE n.study_id = ?
                GROUP BY n.id
                ORDER BY n.code
                """,
                (study_id,),
            ).fetchall()
            return [row_dict(row) for row in rows]

    def create_node(self, study_id: str, payload: NodeCreate) -> dict[str, Any]:
        node_id = new_id("node")
        with connection() as database:
            database.execute(
                """
                INSERT INTO mvp_nodes
                    (id, study_id, code, name, equipment_type, design_intent, state)
                VALUES (?, ?, ?, ?, ?, ?, 'empty')
                """,
                (
                    node_id,
                    study_id,
                    payload.code,
                    payload.name,
                    payload.equipment_type,
                    payload.design_intent,
                ),
            )
            audit(database, "node", node_id, "created")
        return {
            **payload.model_dump(),
            "id": node_id,
            "study_id": study_id,
            "state": "empty",
            "scenario_count": 0,
        }

    def update_node(self, node_id: str, payload: NodeUpdate) -> dict[str, Any] | None:
        values = payload.model_dump(exclude_none=True)
        if not values:
            return self.get_node(node_id)
        _ALLOWED_NODE_FIELDS = {"name", "equipment_type", "design_intent", "state"}
        values = {k: v for k, v in values.items() if k in _ALLOWED_NODE_FIELDS}
        if not values:
            return self.get_node(node_id)
        assignments = ", ".join(f"{field} = ?" for field in values)
        with connection() as database:
            cursor = database.execute(
                f"UPDATE mvp_nodes SET {assignments} WHERE id = ?",  # noqa: S608
                (*values.values(), node_id),
            )
            if cursor.rowcount:
                audit(database, "node", node_id, "updated")
        return self.get_node(node_id)

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        with connection() as database:
            row = database.execute("SELECT * FROM mvp_nodes WHERE id = ?", (node_id,)).fetchone()
            return row_dict(row) if row else None

    def delete_node(self, node_id: str) -> bool:
        with connection() as database:
            cursor = database.execute("DELETE FROM mvp_nodes WHERE id = ?", (node_id,))
            if cursor.rowcount:
                audit(database, "node", node_id, "deleted")
            return bool(cursor.rowcount)

    def list_rows(self, node_id: str) -> list[dict[str, Any]]:
        with connection() as database:
            rows = database.execute(
                "SELECT * FROM mvp_rows WHERE node_id = ? ORDER BY id",
                (node_id,),
            ).fetchall()
            return [self._serialize_row(row) for row in rows]

    def create_row(self, node_id: str, payload: RowCreate) -> dict[str, Any]:
        with connection() as database:
            cursor = database.execute(
                """
                INSERT INTO mvp_rows
                    (node_id, guideword, deviation, cause, consequence, safeguard,
                     severity, likelihood, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    node_id,
                    payload.guideword,
                    payload.deviation,
                    payload.cause,
                    payload.consequence,
                    payload.safeguard,
                    payload.severity,
                    payload.likelihood,
                    payload.status,
                ),
            )
            if cursor.lastrowid is None:
                raise RuntimeError("SQLite did not return a row id.")
            row_id = int(cursor.lastrowid)
            audit(database, "row", str(row_id), "created")
        return self.get_row(row_id) or {}

    def update_row(self, row_id: int, payload: RowUpdate) -> dict[str, Any] | None:
        values = payload.model_dump(exclude_none=True)
        if not values:
            return self.get_row(row_id)
        _ALLOWED_ROW_FIELDS = {
            "guideword",
            "deviation",
            "cause",
            "consequence",
            "safeguard",
            "severity",
            "likelihood",
            "status",
        }
        values = {k: v for k, v in values.items() if k in _ALLOWED_ROW_FIELDS}
        if not values:
            return self.get_row(row_id)
        assignments = ", ".join(f"{field} = ?" for field in values)
        with connection() as database:
            cursor = database.execute(
                f"""
                UPDATE mvp_rows
                SET {assignments}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,  # noqa: S608
                (*values.values(), row_id),
            )
            if cursor.rowcount:
                audit(database, "row", str(row_id), "updated")
        return self.get_row(row_id)

    def get_row(self, row_id: int) -> dict[str, Any] | None:
        with connection() as database:
            row = database.execute("SELECT * FROM mvp_rows WHERE id = ?", (row_id,)).fetchone()
            return self._serialize_row(row) if row else None

    def delete_row(self, row_id: int) -> bool:
        with connection() as database:
            cursor = database.execute("DELETE FROM mvp_rows WHERE id = ?", (row_id,))
            if cursor.rowcount:
                audit(database, "row", str(row_id), "deleted")
            return bool(cursor.rowcount)

    def add_lopa_layer(self, row_id: int, payload: LopaLayerCreate) -> dict[str, Any]:
        layer_id = new_id("ipl")
        with connection() as database:
            database.execute(
                """
                INSERT INTO mvp_lopa_layers
                    (id, row_id, description, pfd, is_valid, note)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    layer_id,
                    row_id,
                    payload.description,
                    payload.pfd,
                    int(payload.is_valid),
                    payload.note,
                ),
            )
            audit(database, "lopa_layer", layer_id, "created")
        return {**payload.model_dump(), "id": layer_id, "row_id": row_id}

    def list_lopa_layers(self, row_id: int) -> list[dict[str, Any]]:
        with connection() as database:
            rows = database.execute(
                "SELECT * FROM mvp_lopa_layers WHERE row_id = ? ORDER BY id",
                (row_id,),
            ).fetchall()
            return [{**row_dict(row), "is_valid": bool(row["is_valid"])} for row in rows]

    def delete_lopa_layer(self, layer_id: str) -> bool:
        with connection() as database:
            cursor = database.execute("DELETE FROM mvp_lopa_layers WHERE id = ?", (layer_id,))
            if cursor.rowcount:
                audit(database, "lopa_layer", layer_id, "deleted")
            return bool(cursor.rowcount)

    def list_library(self, query: str = "") -> list[dict[str, Any]]:
        with connection() as database:
            pattern = f"%{query.strip()}%"
            rows = database.execute(
                """
                SELECT * FROM mvp_library
                WHERE ? = '' OR equipment_type LIKE ? OR deviation LIKE ?
                    OR cause LIKE ? OR consequence LIKE ? OR source_ref LIKE ?
                ORDER BY equipment_type, deviation
                """,
                (query.strip(), pattern, pattern, pattern, pattern, pattern),
            ).fetchall()
            return [self._serialize_library(row) for row in rows]

    def create_library_entry(self, payload: LibraryEntryCreate) -> dict[str, Any]:
        entry_id = new_id("library")
        with connection() as database:
            database.execute(
                """
                INSERT INTO mvp_library
                    (id, equipment_type, guideword, deviation, cause, consequence,
                     safeguard, severity, likelihood, source_ref)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (entry_id, *payload.model_dump().values()),
            )
            audit(database, "library", entry_id, "created")
        return {
            "id": entry_id,
            **payload.model_dump(),
            "risk": risk_label(payload.severity, payload.likelihood),
        }

    def delete_library_entry(self, entry_id: str) -> bool:
        with connection() as database:
            cursor = database.execute("DELETE FROM mvp_library WHERE id = ?", (entry_id,))
            if cursor.rowcount:
                audit(database, "library", entry_id, "deleted")
            return bool(cursor.rowcount)

    def list_sources(self, study_id: str) -> list[dict[str, Any]]:
        with connection() as database:
            rows = database.execute(
                "SELECT * FROM mvp_sources WHERE study_id = ? ORDER BY indexed_at DESC",
                (study_id,),
            ).fetchall()
            return [{**row_dict(row), "is_active": bool(row["is_active"])} for row in rows]

    def create_source(self, payload: SourceCreate) -> dict[str, Any]:
        source_id = new_id("source")
        with connection() as database:
            database.execute(
                """
                INSERT INTO mvp_sources
                    (id, study_id, title, source_type, reference, section_count)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    payload.study_id,
                    payload.title,
                    payload.source_type,
                    payload.reference,
                    payload.section_count,
                ),
            )
            audit(database, "source", source_id, "created")
        return {
            "id": source_id,
            **payload.model_dump(),
            "is_active": True,
            "indexed_at": "just now",
        }

    def update_source(self, source_id: str, payload: SourceUpdate) -> dict[str, Any] | None:
        values = payload.model_dump(exclude_none=True)
        if not values:
            return self.get_source(source_id)
        if "is_active" in values:
            values["is_active"] = int(values["is_active"])
        assignments = ", ".join(f"{field} = ?" for field in values)
        with connection() as database:
            cursor = database.execute(
                f"UPDATE mvp_sources SET {assignments} WHERE id = ?",  # noqa: S608
                (*values.values(), source_id),
            )
            if cursor.rowcount:
                audit(database, "source", source_id, "updated")
        return self.get_source(source_id)

    def get_source(self, source_id: str) -> dict[str, Any] | None:
        with connection() as database:
            row = database.execute(
                "SELECT * FROM mvp_sources WHERE id = ?", (source_id,)
            ).fetchone()
            return {**row_dict(row), "is_active": bool(row["is_active"])} if row else None

    def delete_source(self, source_id: str) -> bool:
        with connection() as database:
            cursor = database.execute("DELETE FROM mvp_sources WHERE id = ?", (source_id,))
            if cursor.rowcount:
                audit(database, "source", source_id, "deleted")
            return bool(cursor.rowcount)

    def get_risk_matrix(self, study_id: str) -> dict[str, Any]:
        with connection() as database:
            database.execute(
                "INSERT OR IGNORE INTO mvp_risk_matrix (study_id) VALUES (?)",
                (study_id,),
            )
            row = database.execute(
                "SELECT * FROM mvp_risk_matrix WHERE study_id = ?", (study_id,)
            ).fetchone()
            return row_dict(row)

    def update_risk_matrix(self, study_id: str, payload: RiskMatrixUpdate) -> dict[str, Any]:
        if not payload.low_max < payload.medium_max < payload.high_max:
            raise ValueError("Risk thresholds must increase from low to high.")
        with connection() as database:
            database.execute(
                """
                INSERT INTO mvp_risk_matrix
                    (study_id, low_max, medium_max, high_max, revision)
                VALUES (?, ?, ?, ?, 1)
                ON CONFLICT(study_id) DO UPDATE SET
                    low_max = excluded.low_max,
                    medium_max = excluded.medium_max,
                    high_max = excluded.high_max,
                    revision = revision + 1,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (study_id, payload.low_max, payload.medium_max, payload.high_max),
            )
            audit(database, "risk_matrix", study_id, "updated")
        return self.get_risk_matrix(study_id)

    def list_audit(self, limit: int = 100) -> list[dict[str, Any]]:
        with connection() as database:
            rows = database.execute(
                "SELECT * FROM mvp_audit ORDER BY id DESC LIMIT ?",
                (max(1, min(limit, 500)),),
            ).fetchall()
            return [row_dict(row) for row in rows]

    def record_report(self, study_id: str, node_id: str, created_by: str) -> dict[str, Any]:
        report_id = new_id("report")
        filename = f"preventa-{node_id}-hazop.docx"
        with connection() as database:
            database.execute(
                """
                INSERT INTO mvp_reports
                    (id, study_id, node_id, filename, created_by)
                VALUES (?, ?, ?, ?, ?)
                """,
                (report_id, study_id, node_id, filename, created_by),
            )
            audit(database, "report", report_id, "generated")
        return {
            "id": report_id,
            "study_id": study_id,
            "node_id": node_id,
            "filename": filename,
            "created_by": created_by,
        }

    def list_reports(self) -> list[dict[str, Any]]:
        with connection() as database:
            rows = database.execute(
                """
                SELECT r.*, s.title AS study_title, n.name AS node_name
                FROM mvp_reports r
                JOIN mvp_studies s ON s.id = r.study_id
                JOIN mvp_nodes n ON n.id = r.node_id
                ORDER BY r.created_at DESC
                """
            ).fetchall()
            return [row_dict(row) for row in rows]

    def find_import(self, content_hash: str) -> dict[str, Any] | None:
        """Return a previous import's report for this exact file, if still present."""
        with connection() as database:
            row = database.execute(
                "SELECT study_id, result_json FROM mvp_imports WHERE content_hash = ?",
                (content_hash,),
            ).fetchone()
            if row is None:
                return None
            study = database.execute(
                "SELECT 1 FROM mvp_studies WHERE id = ?", (row["study_id"],)
            ).fetchone()
            if study is None:
                # The imported study was deleted; allow a fresh import.
                database.execute(
                    "DELETE FROM mvp_imports WHERE content_hash = ?", (content_hash,)
                )
                return None
        return cast(dict[str, Any], json.loads(row["result_json"]))

    def record_import(self, content_hash: str, study_id: str, result: dict[str, Any]) -> None:
        """Persist an import fingerprint (for dedup) and an auditable loss report."""
        with connection() as database:
            database.execute(
                """
                INSERT OR REPLACE INTO mvp_imports (content_hash, study_id, result_json)
                VALUES (?, ?, ?)
                """,
                (content_hash, study_id, json.dumps(result)),
            )
            detail = json.dumps(
                {
                    "nodes": result.get("nodes"),
                    "rows": result.get("rows"),
                    "lopa_layers": result.get("lopa_layers"),
                    "dropped": result.get("dropped", {}),
                },
                ensure_ascii=False,
            )
            database.execute(
                """
                INSERT INTO mvp_audit (entity_type, entity_id, action, detail)
                VALUES (?, ?, ?, ?)
                """,
                ("import", study_id, "imported", detail),
            )

    @staticmethod
    def _serialize_library(row: Any) -> dict[str, Any]:
        result = row_dict(row)
        result["risk"] = risk_label(result["severity"], result["likelihood"])
        return result

    @staticmethod
    def _serialize_row(row: Any) -> dict[str, Any]:
        result = row_dict(row)
        result["risk"] = risk_label(result["severity"], result["likelihood"])
        return result

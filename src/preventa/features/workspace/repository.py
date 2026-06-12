from typing import Any

from preventa.features.workspace.crud_schemas import (
    LopaLayerCreate,
    NodeCreate,
    NodeUpdate,
    RowCreate,
    RowUpdate,
    StudyCreate,
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
        return {**payload.model_dump(), "id": node_id, "study_id": study_id, "state": "empty"}

    def update_node(self, node_id: str, payload: NodeUpdate) -> dict[str, Any] | None:
        values = payload.model_dump(exclude_none=True)
        if not values:
            return self.get_node(node_id)
        assignments = ", ".join(f"{field} = ?" for field in values)
        with connection() as database:
            database.execute(
                f"UPDATE mvp_nodes SET {assignments} WHERE id = ?",  # noqa: S608
                (*values.values(), node_id),
            )
            audit(database, "node", node_id, "updated")
        return self.get_node(node_id)

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        with connection() as database:
            row = database.execute("SELECT * FROM mvp_nodes WHERE id = ?", (node_id,)).fetchone()
            return row_dict(row) if row else None

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
        assignments = ", ".join(f"{field} = ?" for field in values)
        with connection() as database:
            database.execute(
                f"""
                UPDATE mvp_rows
                SET {assignments}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,  # noqa: S608
                (*values.values(), row_id),
            )
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
            return [
                {**row_dict(row), "is_valid": bool(row["is_valid"])}
                for row in rows
            ]

    @staticmethod
    def _serialize_row(row: Any) -> dict[str, Any]:
        result = row_dict(row)
        result["risk"] = risk_label(result["severity"], result["likelihood"])
        return result

import os
import sqlite3
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from preventa.features.auth.schemas import AuthUser, Role, UserCreate
from preventa.features.auth.security import (
    hash_password,
    hash_session_token,
    new_session_token,
    verify_password,
)
from preventa.features.workspace.store import connection, initialize_store, new_id

ROLE_PERMISSIONS: dict[Role, list[str]] = {
    "viewer": ["workspace:read", "report:read"],
    "facilitator": [
        "workspace:read",
        "workspace:write",
        "report:read",
        "rag:use",
    ],
    "admin": [
        "workspace:read",
        "workspace:write",
        "workspace:delete",
        "report:read",
        "rag:use",
        "users:manage",
    ],
}


class AuthRepository:
    def __init__(self) -> None:
        initialize_store()
        self._seed_users()

    def _seed_users(self) -> None:
        users: list[tuple[str, str, str, Role]] = [
            (
                "admin",
                "admin@preventa.com",
                "System Administrator",
                "admin",
            ),
            (
                "facilitator",
                "facilitator@preventa.com",
                "HAZOP Facilitator",
                "facilitator",
            ),
            (
                "viewer",
                "viewer@preventa.com",
                "Auditor",
                "viewer",
            ),
        ]
        defaults = {
            "admin": "PreventA-Admin-2026!",
            "facilitator": "PreventA-Facilitator-2026!",
            "viewer": "PreventA-Viewer-2026!",
        }
        with connection() as database:
            for key, email, full_name, role in users:
                user_id = f"user-{key}"
                existing = database.execute(
                    "SELECT id FROM app_users WHERE id = ? OR email = ?",
                    (user_id, email),
                ).fetchone()
                if existing:
                    database.execute(
                        """
                        UPDATE app_users
                        SET email = ?, full_name = ?, role = ?
                        WHERE id = ?
                        """,
                        (email, full_name, role, str(existing["id"])),
                    )
                    continue
                password = os.getenv(
                    f"PREVENTA_{key.upper()}_PASSWORD",
                    defaults[key],
                )
                database.execute(
                    """
                    INSERT INTO app_users
                        (id, email, full_name, role, password_hash)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        email,
                        full_name,
                        role,
                        hash_password(password),
                    ),
                )

    def authenticate(self, email: str, password: str) -> AuthUser | None:
        with connection() as database:
            row = database.execute(
                """
                SELECT * FROM app_users
                WHERE lower(email) = lower(?) AND is_active = 1
                """,
                (email,),
            ).fetchone()
        if row is None or not verify_password(password, str(row["password_hash"])):
            return None
        return self._to_user(row)

    def create_session(self, user_id: str, *, hours: int = 12) -> str:
        token = new_session_token()
        expires_at = datetime.now(UTC) + timedelta(hours=hours)
        with connection() as database:
            database.execute(
                """
                INSERT INTO app_sessions (token_hash, user_id, expires_at)
                VALUES (?, ?, ?)
                """,
                (hash_session_token(token), user_id, expires_at.isoformat()),
            )
        return token

    def get_user_for_session(self, token: str) -> AuthUser | None:
        now = datetime.now(UTC).isoformat()
        with connection() as database:
            database.execute("DELETE FROM app_sessions WHERE expires_at <= ?", (now,))
            row = database.execute(
                """
                SELECT u.*
                FROM app_sessions s
                JOIN app_users u ON u.id = s.user_id
                WHERE s.token_hash = ? AND s.expires_at > ? AND u.is_active = 1
                """,
                (hash_session_token(token), now),
            ).fetchone()
        return self._to_user(row) if row else None

    def delete_session(self, token: str) -> None:
        with connection() as database:
            database.execute(
                "DELETE FROM app_sessions WHERE token_hash = ?",
                (hash_session_token(token),),
            )

    def list_users(self) -> list[AuthUser]:
        with connection() as database:
            rows = database.execute(
                "SELECT * FROM app_users ORDER BY created_at, email"
            ).fetchall()
        return [self._to_user(row) for row in rows]

    def create_user(self, payload: UserCreate) -> AuthUser:
        user_id = new_id("user")
        try:
            with connection() as database:
                database.execute(
                    """
                    INSERT INTO app_users
                        (id, email, full_name, role, password_hash)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        str(payload.email).lower(),
                        payload.full_name,
                        payload.role,
                        hash_password(payload.password),
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise ValueError("A user with this email already exists.") from exc
        return AuthUser(
            id=user_id,
            email=payload.email,
            full_name=payload.full_name,
            role=payload.role,
            permissions=ROLE_PERMISSIONS[payload.role],
        )

    @staticmethod
    def _to_user(row: Any) -> AuthUser:
        role = cast(Role, str(row["role"]))
        return AuthUser(
            id=str(row["id"]),
            email=str(row["email"]),
            full_name=str(row["full_name"]),
            role=role,
            permissions=ROLE_PERMISSIONS[role],
        )

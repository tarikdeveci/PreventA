import base64
import hashlib
import hmac
import os
import time
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from preventa.core.config import get_settings
from preventa.features.auth.schemas import AuthUser, Role, UserCreate
from preventa.features.auth.security import hash_password, hash_session_token, verify_password
from preventa.features.workspace.store import (
    INTEGRITY_ERRORS,
    connection,
    initialize_store,
    new_id,
)

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
        self._revoked_tokens: set[str] = set()
        initialize_store()
        self._seed_users()

    @staticmethod
    def _session_secret() -> bytes:
        configured = os.getenv("PREVENTA_SESSION_SECRET")
        if configured:
            return configured.encode()
        # Fail closed: never derive the signing key from a public default in a
        # deployed environment — that would let anyone forge admin sessions.
        if get_settings().is_production:
            raise RuntimeError(
                "PREVENTA_SESSION_SECRET must be set in production; "
                "refusing to sign sessions with an insecure default."
            )
        return b"preventa-dev-insecure-session-secret-do-not-use-in-production"

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
                password = os.getenv(f"PREVENTA_{key.upper()}_PASSWORD")
                if password is None:
                    # Never seed accounts with hardcoded passwords in production.
                    if get_settings().is_production:
                        continue
                    password = defaults[key]
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
        expires_at = int((datetime.now(UTC) + timedelta(hours=hours)).timestamp())
        payload = f"{user_id}.{expires_at}"
        signature = hmac.new(
            self._session_secret(), payload.encode(), hashlib.sha256
        ).digest()
        encoded_signature = base64.urlsafe_b64encode(signature).decode().rstrip("=")
        return f"{payload}.{encoded_signature}"

    def get_user_for_session(self, token: str) -> AuthUser | None:
        token_hash = hash_session_token(token)
        if token_hash in self._revoked_tokens:
            return None
        try:
            user_id, expires_at_text, signature = token.split(".", 2)
            expires_at = int(expires_at_text)
        except (TypeError, ValueError):
            return None
        if expires_at <= int(time.time()):
            return None
        payload = f"{user_id}.{expires_at}"
        expected = base64.urlsafe_b64encode(
            hmac.new(self._session_secret(), payload.encode(), hashlib.sha256).digest()
        ).decode().rstrip("=")
        if not hmac.compare_digest(signature, expected):
            return None
        with connection() as database:
            revoked = database.execute(
                "SELECT 1 FROM app_revoked_sessions WHERE token_hash = ?",
                (token_hash,),
            ).fetchone()
            if revoked:
                return None
            row = database.execute(
                "SELECT * FROM app_users WHERE id = ? AND is_active = 1",
                (user_id,),
            ).fetchone()
        return self._to_user(row) if row else None

    def delete_session(self, token: str) -> None:
        token_hash = hash_session_token(token)
        self._revoked_tokens.add(token_hash)
        # Persist the revocation so logout survives across worker processes.
        with connection() as database:
            database.execute(
                "INSERT OR IGNORE INTO app_revoked_sessions (token_hash) VALUES (?)",
                (token_hash,),
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
        except INTEGRITY_ERRORS as exc:
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

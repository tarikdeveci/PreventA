"""Tests for the red-team security hardening (auth secret, seeding, revocation, throttle)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from preventa.features.auth.repository import AuthRepository
from preventa.features.workspace.store import initialize_store
from preventa.main import create_app


def test_session_secret_fails_closed_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PREVENTA_SESSION_SECRET", raising=False)
    monkeypatch.setenv("VERCEL", "1")  # marks the environment as production
    with pytest.raises(RuntimeError):
        AuthRepository._session_secret()


def test_dev_session_secret_is_stable_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PREVENTA_SESSION_SECRET", raising=False)
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.setenv("APP_ENV", "development")
    # A fixed dev secret keeps stateless sessions valid across worker restarts.
    assert AuthRepository._session_secret() == AuthRepository._session_secret()


def test_no_default_users_seeded_in_production(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PREVENTA_DB_PATH", str(tmp_path / "preventa.db"))
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("PREVENTA_SESSION_SECRET", "x" * 32)
    for role in ("ADMIN", "FACILITATOR", "VIEWER"):
        monkeypatch.delenv(f"PREVENTA_{role}_PASSWORD", raising=False)

    repo = AuthRepository()
    assert repo.list_users() == []
    assert repo.authenticate("admin@preventa.com", "PreventA-Admin-2026!") is None


def test_revocation_persists_across_worker_instances(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("PREVENTA_DB_PATH", str(tmp_path / "preventa.db"))
    repo = AuthRepository()
    user = repo.authenticate("admin@preventa.com", "PreventA-Admin-2026!")
    assert user is not None
    token = repo.create_session(user.id)
    repo.delete_session(token)

    # A fresh instance (empty in-memory denylist) must still reject via the DB.
    assert AuthRepository().get_user_for_session(token) is None


def test_login_is_rate_limited(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PREVENTA_DB_PATH", str(tmp_path / "preventa.db"))
    initialize_store()  # the module-level auth repo was created against another path
    client = TestClient(create_app())
    payload = {"email": "throttle-probe@example.com", "password": "wrong-password"}

    statuses = [
        client.post("/api/v1/auth/login", json=payload).status_code for _ in range(9)
    ]
    assert statuses[:8].count(401) == 8
    assert statuses[-1] == 429

from pathlib import Path

import pytest
from fastapi import HTTPException

from preventa.api.auth_dependencies import require_permission
from preventa.features.auth.repository import AuthRepository
from preventa.features.auth.schemas import AuthUser


def test_authentication_and_session_round_trip(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("PREVENTA_DB_PATH", str(tmp_path / "preventa.db"))
    repository = AuthRepository()

    user = repository.authenticate(
        "facilitator@preventa.com",
        "PreventA-Facilitator-2026!",
    )
    assert user is not None
    assert user.role == "facilitator"
    assert "workspace:write" in user.permissions

    token = repository.create_session(user.id)
    restored = repository.get_user_for_session(token)
    assert restored == user

    repository.delete_session(token)
    assert repository.get_user_for_session(token) is None


def test_viewer_cannot_write() -> None:
    viewer = AuthUser(
        id="viewer",
        email="viewer@preventa.com",
        full_name="Viewer",
        role="viewer",
        permissions=["workspace:read"],
    )

    with pytest.raises(HTTPException) as exc_info:
        require_permission("workspace:write")(viewer)

    assert exc_info.value.status_code == 403

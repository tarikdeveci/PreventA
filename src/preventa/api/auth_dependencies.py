from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from preventa.features.auth.repository import AuthRepository
from preventa.features.auth.schemas import AuthUser

SESSION_COOKIE = "preventa_session"
auth_repository = AuthRepository()


def get_current_user(request: Request) -> AuthUser:
    token = request.cookies.get(SESSION_COOKIE)
    user = auth_repository.get_user_for_session(token) if token else None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    return user


CurrentUserDep = Annotated[AuthUser, Depends(get_current_user)]


def require_permission(permission: str) -> Callable[[CurrentUserDep], AuthUser]:
    def dependency(user: CurrentUserDep) -> AuthUser:
        if permission not in user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission}",
            )
        return user

    return dependency


ReadUserDep = Annotated[AuthUser, Depends(require_permission("workspace:read"))]
WriteUserDep = Annotated[AuthUser, Depends(require_permission("workspace:write"))]
DeleteUserDep = Annotated[AuthUser, Depends(require_permission("workspace:delete"))]
RagUserDep = Annotated[AuthUser, Depends(require_permission("rag:use"))]
AdminUserDep = Annotated[AuthUser, Depends(require_permission("users:manage"))]

from fastapi import APIRouter, HTTPException, Request, Response, status

from preventa.api.auth_dependencies import (
    SESSION_COOKIE,
    AdminUserDep,
    CurrentUserDep,
    auth_repository,
)
from preventa.features.auth.schemas import (
    AuthUser,
    LoginRequest,
    SessionResponse,
    UserCreate,
)

router = APIRouter()


@router.post("/login", response_model=SessionResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
) -> SessionResponse:
    user = auth_repository.authenticate(str(payload.email), payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email or password is incorrect.",
        )
    token = auth_repository.create_session(user.id)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        secure=(
            request.url.scheme == "https"
            or request.headers.get("x-forwarded-proto") == "https"
        ),
        samesite="lax",
        max_age=12 * 60 * 60,
        path="/",
    )
    return SessionResponse(user=user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, response: Response) -> Response:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        auth_repository.delete_session(token)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


@router.get("/me", response_model=SessionResponse)
async def me(user: CurrentUserDep) -> SessionResponse:
    return SessionResponse(user=user)


@router.get("/users", response_model=list[AuthUser])
async def list_users(_: AdminUserDep) -> list[AuthUser]:
    return auth_repository.list_users()


@router.post("/users", response_model=AuthUser, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, _: AdminUserDep) -> AuthUser:
    try:
        return auth_repository.create_user(payload)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

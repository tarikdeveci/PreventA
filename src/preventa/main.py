from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from preventa.api.router import api_router
from preventa.core.config import get_settings
from preventa.core.logging import configure_logging


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="PreventA API",
        version="0.1.0",
        description="Grounded process-safety workflows for HAZOP, LOPA, and SIL studies.",
        lifespan=lifespan,
    )

    # CORS — configurable via ALLOWED_ORIGINS (comma-separated); otherwise a
    # default allow-list covering local dev and the known production domains.
    default_origins = [
        "http://localhost:5173",
        "http://localhost:4173",
        "https://preventa.vercel.app",
        "https://preventa-ui.vercel.app",
        "https://preventa-nu.vercel.app",
        "https://preventa-api.vercel.app",
    ]
    configured_origins = [
        origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=configured_origins or default_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Accept", "Content-Type", "Authorization"],
    )

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/health", tags=["operations"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

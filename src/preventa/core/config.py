from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+asyncpg://preventa:preventa@localhost:5432/preventa"
    allowed_origins: str = ""  # Comma-separated; overrides default CORS list when set

    # OpenPHA import guardrails (defence against oversized / amplified uploads).
    import_max_bytes: int = Field(default=5_000_000, ge=1_000)
    import_max_scenarios: int = Field(default=10_000, ge=1)

    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "qwen2.5:7b"
    ollama_embed_model: str = "nomic-embed-text"

    rag_dense_limit: int = Field(default=30, ge=1, le=100)
    rag_sparse_limit: int = Field(default=30, ge=1, le=100)
    rag_fused_limit: int = Field(default=12, ge=1, le=50)
    rag_rrf_k: int = Field(default=60, ge=1)
    rag_min_citations: int = Field(default=1, ge=1)

    @property
    def is_production(self) -> bool:
        """True on a deployed target where insecure defaults must be refused."""
        import os

        return self.app_env.lower() in {"production", "prod", "staging"} or bool(
            os.getenv("VERCEL")
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


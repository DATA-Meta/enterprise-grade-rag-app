"""
Central application settings.

Every other module (ingestion, embeddings, vectorstore, retrieval, generation)
should import `settings` from here instead of calling os.getenv() directly.
This keeps all configuration in one place and makes it easy to see, at a
glance, everything the app depends on.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- LLM Provider ---
    openai_api_key: str | None = None

    # --- Vector DB (Qdrant) ---
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None

    # --- LLM Gateway (Portkey) ---
    portkey_api_key: str | None = None

    # --- Guardrails (NVIDIA NeMo / AI Endpoints) ---
    nvidia_api_key: str | None = None

    # --- Observability ---
    langchain_api_key: str | None = None
    langchain_tracing_v2: bool = False
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None

    # --- Postgres (LangGraph checkpointing) ---
    postgres_url: str = "postgresql://user:password@localhost:5432/ragdb"

    # --- Redis (rate limiting) ---
    redis_url: str = "redis://localhost:6379/0"

    # --- App ---
    app_env: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Cached so the .env file is only read once per process."""
    return Settings()


settings = get_settings()
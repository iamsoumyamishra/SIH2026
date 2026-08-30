"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # apps/api


class Settings(BaseSettings):
    """Central, env-driven configuration for the API."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Security
    jwt_secret: str = "change-me-to-a-long-random-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Demo credentials (seeded only in-memory for the MVP)
    demo_username: str = "admin"
    demo_password: str = "admin"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Database
    # "sqlite" -> local dev file; "postgresql" -> compose Postgres
    database_backend: str = "sqlite"
    postgres_user: str = "saw"
    postgres_password: str = "change-me"
    postgres_db: str = "sovereign_ai"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # Ollama
    ollama_base_url: str = "http://localhost:11434"

    # Model configuration (also mirrored in models/registry.yaml)
    ollama_general_model: str = ""
    ollama_reasoning_model: str = ""
    ollama_coding_model: str = ""
    ollama_vision_model: str = ""
    ollama_embedding_model: str = "nomic-embed-text"

    # RAG
    # "local" -> in-process fallback vector store; "qdrant" -> Qdrant service
    rag_backend: str = "local"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "knowledge_chunks"
    embedding_dim: int = 768

    # Agent
    max_agent_iterations: int = 12

    # Storage
    storage_root: str = "workspaces"

    @property
    def database_url(self) -> str:
        if self.database_backend == "postgresql":
            return (
                f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        db_path = BASE_DIR / "data" / "sovereign_ai.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path}"

    @property
    def workspaces_root(self) -> Path:
        root = Path(self.storage_root)
        if not root.is_absolute():
            root = BASE_DIR / root
        return root


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()


settings = get_settings()

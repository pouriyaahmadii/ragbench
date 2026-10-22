from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Literal, Optional
import secrets


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_ENV: Literal["development", "production", "testing"] = "development"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    LOG_FORMAT: Literal["json", "console"] = "json"

    # Database
    POSTGRES_DB: str = "ragbench"
    POSTGRES_USER: str = "ragbench"
    POSTGRES_PASSWORD: str = "changeme"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Vector Store
    QDRANT_URL: str = "http://qdrant:6333"
    QDRANT_API_KEY: Optional[str] = None

    # Cache/Queue
    REDIS_URL: str = "redis://redis:6379/0"

    # Mock Mode
    MOCK_MODE: bool = True

    # Embedding Provider
    EMBEDDING_PROVIDER: Literal["mock", "ollama", "openai", "cohere"] = "mock"
    EMBEDDING_MODEL: str = "mock"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_BATCH_SIZE: int = 100
    EMBEDDING_TIMEOUT_SECONDS: int = 60
    OLLAMA_EMBEDDING_URL: Optional[str] = "http://host.docker.internal:11434"
    OPENAI_API_KEY: Optional[str] = None
    COHERE_API_KEY: Optional[str] = None

    # Generation Provider
    GENERATION_PROVIDER: Literal["mock", "ollama", "openai", "anthropic"] = "mock"
    GENERATION_MODEL: str = "mock"
    GENERATION_TEMPERATURE: float = 0.0
    GENERATION_MAX_TOKENS: int = 1024
    GENERATION_TIMEOUT_SECONDS: int = 60
    OLLAMA_GENERATION_URL: Optional[str] = "http://host.docker.internal:11434"
    ANTHROPIC_API_KEY: Optional[str] = None

    # Ingestion Limits
    MAX_UPLOAD_SIZE_MB: int = 20
    MAX_PDF_PAGES: int = 200
    MAX_EXTRACTED_CHARS: int = 1_000_000
    PARSER_TIMEOUT_SECONDS: int = 30

    # Chunking
    CHUNK_SIZE_CHARS: int = 1200
    CHUNK_OVERLAP_CHARS: int = 150

    # Retrieval
    DEFAULT_TOP_K: int = 5
    MAX_TOP_K: int = 20

    # Generation Context
    MAX_CONTEXT_CHARS: int = 4000

    # Optional: Observability
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = None
    OTEL_SERVICE_NAME: str = "ragbench-api"

    @field_validator("CHUNK_OVERLAP_CHARS")
    @classmethod
    def validate_overlap(cls, v, info):
        if info.data.get("CHUNK_SIZE_CHARS") and v >= info.data["CHUNK_SIZE_CHARS"]:
            raise ValueError("CHUNK_OVERLAP_CHARS must be less than CHUNK_SIZE_CHARS")
        return v

    @field_validator("DEFAULT_TOP_K")
    @classmethod
    def validate_top_k(cls, v, info):
        if info.data.get("MAX_TOP_K") and v > info.data["MAX_TOP_K"]:
            raise ValueError("DEFAULT_TOP_K must be <= MAX_TOP_K")
        return v


settings = Settings()
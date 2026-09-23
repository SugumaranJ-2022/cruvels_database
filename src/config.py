"""
Configuration module for the Legal AI Platform backend.
Supports PostgreSQL with fallback to SQLite for local development without database server setup.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Central configuration parameters."""
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "legal_db")

    USE_SQLITE_FALLBACK: bool = os.getenv("USE_SQLITE_FALLBACK", "true").lower() == "true"

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
    )
    ASYNC_DATABASE_URL: str = os.getenv(
        "ASYNC_DATABASE_URL",
        f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
    )

    SQLITE_DATABASE_URL: str = "sqlite:///./legal_db.sqlite"
    ASYNC_SQLITE_DATABASE_URL: str = "sqlite+aiosqlite:///./legal_db.sqlite"

    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "1536"))
    MAX_CHARS_SLIDING_WINDOW: int = int(os.getenv("MAX_CHARS_SLIDING_WINDOW", "12000"))
    MAX_RETRIES_LLM: int = int(os.getenv("MAX_RETRIES_LLM", "2"))


settings = Settings()

"""
Database session and engine management supporting PostgreSQL with automatic SQLite fallback.
"""

import socket
from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config import settings


def is_postgres_available(host: str = settings.POSTGRES_HOST, port: int = int(settings.POSTGRES_PORT), timeout: float = 1.0) -> bool:
    """Check if PostgreSQL server is accepting TCP connections."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


# Determine engine database dialect
IS_POSTGRES = is_postgres_available()

if IS_POSTGRES:
    print(f"--> Using PostgreSQL database server at {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
    sync_engine = create_engine(settings.DATABASE_URL, echo=False)
    async_engine = create_async_engine(settings.ASYNC_DATABASE_URL, echo=False)
else:
    print("--> PostgreSQL connection refused. Using SQLite database fallback (legal_db.sqlite)...")
    sync_engine = create_engine(settings.SQLITE_DATABASE_URL, echo=False)
    async_engine = create_async_engine(settings.ASYNC_SQLITE_DATABASE_URL, echo=False)

SessionLocal = sessionmaker(bind=sync_engine, autoflush=False, autocommit=False)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

"""
Database initialization script supporting both PostgreSQL and SQLite fallback.
"""

import os
from sqlalchemy import text
from src.config import settings
from src.db.database import IS_POSTGRES, sync_engine
from src.db.models import Base


def init_database() -> None:
    """
    Initialize database extensions and schema tables idempotently.
    """
    if IS_POSTGRES:
        print(f"Initializing PostgreSQL database at {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}...")
        with sync_engine.connect() as connection:
            connection.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
            connection.execute(text('CREATE EXTENSION IF NOT EXISTS vector;'))
            connection.execute(text('CREATE EXTENSION IF NOT EXISTS pg_trgm;'))
            connection.commit()

        schema_sql_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        if os.path.exists(schema_sql_path):
            with open(schema_sql_path, "r", encoding="utf-8") as f:
                sql_script = f.read()
            with sync_engine.connect() as connection:
                connection.execute(text(sql_script))
                connection.commit()
            print("Successfully applied schema.sql DDL to PostgreSQL!")
        else:
            Base.metadata.create_all(bind=sync_engine)
            print("Successfully initialized PostgreSQL tables via SQLAlchemy Metadata!")
    else:
        print("Initializing SQLite database fallback (legal_db.sqlite)...")
        Base.metadata.create_all(bind=sync_engine)
        print("Successfully created all SQLite tables in legal_db.sqlite!")


if __name__ == "__main__":
    init_database()

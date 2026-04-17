"""
Phase 3 one-shot migration for existing SQLite DBs.

Adds merchants.is_active and merchants.deactivated_at if missing.

Usage:
    cd backend/src && python -m database.migrate_phase3
"""
from typing import Optional

from sqlalchemy import create_engine, inspect, text

from config.loader import load_config
from database.models import Base


def run_migration(db_url: Optional[str] = None) -> dict:
    db_url = db_url or load_config().database_url or "sqlite:///memberplus_phase1.db"
    engine = create_engine(db_url)
    inspector = inspect(engine)

    result = {"db_url": db_url, "columns_added": []}

    if "merchants" in inspector.get_table_names():
        existing = {c["name"] for c in inspector.get_columns("merchants")}
        with engine.begin() as conn:
            if "is_active" not in existing:
                conn.execute(text(
                    "ALTER TABLE merchants ADD COLUMN is_active BOOLEAN DEFAULT 1 NOT NULL"
                ))
                result["columns_added"].append("is_active")
            if "deactivated_at" not in existing:
                conn.execute(text(
                    "ALTER TABLE merchants ADD COLUMN deactivated_at DATETIME"
                ))
                result["columns_added"].append("deactivated_at")

    Base.metadata.create_all(engine)
    return result


if __name__ == "__main__":
    print(run_migration())

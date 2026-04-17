"""
Phase 2 one-shot migration for existing SQLite DBs.

Adds merchants.setup_step and merchants.subscription_id if missing, and
creates the new membership_plans / subscriptions tables via SQLAlchemy
metadata if they don't already exist.

Usage:
    python -m database.migrate_phase2
"""
from typing import Optional

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from config.loader import load_config
from database.models import Base


def run_migration(db_url: Optional[str] = None) -> dict:
    db_url = db_url or load_config().database_url or "sqlite:///memberplus_phase1.db"
    engine = create_engine(db_url)
    inspector = inspect(engine)

    result = {"db_url": db_url, "columns_added": [], "tables_created": []}

    if "merchants" in inspector.get_table_names():
        existing_cols = {c["name"] for c in inspector.get_columns("merchants")}
        with engine.begin() as conn:
            if "setup_step" not in existing_cols:
                conn.execute(text("ALTER TABLE merchants ADD COLUMN setup_step INTEGER DEFAULT 0 NOT NULL"))
                result["columns_added"].append("setup_step")
            if "subscription_id" not in existing_cols:
                conn.execute(text("ALTER TABLE merchants ADD COLUMN subscription_id VARCHAR(36)"))
                result["columns_added"].append("subscription_id")

    before = set(inspector.get_table_names())
    Base.metadata.create_all(engine)
    after = set(inspect(engine).get_table_names())
    result["tables_created"] = sorted(after - before)

    return result


if __name__ == "__main__":
    summary = run_migration()
    print(summary)

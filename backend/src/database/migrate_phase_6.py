"""
Phase 6 one-shot migration: creates the `benefit_deliveries` table.

Usage:
    cd backend/src && python -m database.migrate_phase_6
"""
from typing import Optional

from sqlalchemy import create_engine, inspect

from config.loader import load_config
from database.models import Base


def run_migration(db_url: Optional[str] = None) -> dict:
    db_url = db_url or load_config().database_url or "sqlite:///memberplus_phase1.db"
    engine = create_engine(db_url)
    before = set(inspect(engine).get_table_names())
    Base.metadata.create_all(engine)
    after = set(inspect(engine).get_table_names())
    return {"db_url": db_url, "tables_created": sorted(after - before)}


if __name__ == "__main__":
    print(run_migration())

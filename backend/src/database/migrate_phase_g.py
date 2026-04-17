"""
Phase G one-shot migration: adds grace window + Salla special-offer id +
interest signups.

Idempotent.

Usage:
    cd backend/src && python -m database.migrate_phase_g
"""
from typing import Optional

from sqlalchemy import create_engine, inspect, text

from config.loader import load_config
from database.models import Base


CUSTOMER_SUB_NEW = [
    ("grace_ends_at", "DATETIME"),
]
PLAN_NEW = [
    ("salla_special_offer_id", "VARCHAR(64)"),
]


def _ensure_columns(engine, table: str, cols):
    inspector = inspect(engine)
    if table not in inspector.get_table_names():
        return []
    existing = {c["name"] for c in inspector.get_columns(table)}
    added = []
    with engine.begin() as conn:
        for name, decl in cols:
            if name not in existing:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {decl}"))
                added.append(f"{table}.{name}")
    return added


def run_migration(db_url: Optional[str] = None) -> dict:
    db_url = db_url or load_config().database_url or "sqlite:///memberplus_phase1.db"
    engine = create_engine(db_url)

    added = []
    added += _ensure_columns(engine, "customer_subscriptions", CUSTOMER_SUB_NEW)
    added += _ensure_columns(engine, "membership_plans", PLAN_NEW)

    before = set(inspect(engine).get_table_names())
    Base.metadata.create_all(engine)
    after = set(inspect(engine).get_table_names())
    tables_created = sorted(after - before)

    return {"db_url": db_url, "columns_added": added, "tables_created": tables_created}


if __name__ == "__main__":
    print(run_migration())

"""
Phase R one-shot migration: adds structured benefit fields + tier + Salla
linkage to membership_plans.

Idempotent — each ALTER is guarded by an inspector check.

Usage:
    cd backend/src && python -m database.migrate_phase_r
"""
from typing import Optional

from sqlalchemy import create_engine, inspect, text

from config.loader import load_config
from database.models import Base


NEW_COLUMNS = [
    ("tier",                   "VARCHAR(20)"),
    ("discount_percent",       "NUMERIC(5, 2)"),
    ("free_shipping_quota",    "INTEGER"),
    ("monthly_gift_enabled",   "BOOLEAN DEFAULT 0 NOT NULL"),
    ("early_access_enabled",   "BOOLEAN DEFAULT 0 NOT NULL"),
    ("badge_enabled",          "BOOLEAN DEFAULT 0 NOT NULL"),
    ("salla_customer_group_id","VARCHAR(64)"),
]


def run_migration(db_url: Optional[str] = None) -> dict:
    db_url = db_url or load_config().database_url or "sqlite:///memberplus_phase1.db"
    engine = create_engine(db_url)
    inspector = inspect(engine)

    result = {"db_url": db_url, "columns_added": []}

    if "membership_plans" in inspector.get_table_names():
        existing = {c["name"] for c in inspector.get_columns("membership_plans")}
        with engine.begin() as conn:
            for name, decl in NEW_COLUMNS:
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE membership_plans ADD COLUMN {name} {decl}"))
                    result["columns_added"].append(name)

    Base.metadata.create_all(engine)
    return result


if __name__ == "__main__":
    print(run_migration())

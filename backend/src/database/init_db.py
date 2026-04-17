"""
Database initialization and migrations.

Creates Phase 1 tables: merchants, oauth_tokens, sessions.
"""

import sqlite3
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def init_db_sqlite(db_path: str = "test.db"):
    """Initialize SQLite database with Phase 1 schema."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Create merchants table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS merchants (
            id TEXT PRIMARY KEY,
            salla_store_id TEXT UNIQUE NOT NULL,
            store_name TEXT,
            merchant_email TEXT,
            merchant_phone TEXT,
            language TEXT DEFAULT 'ar' NOT NULL,
            oauth_token_id TEXT,
            trial_start_date TEXT NOT NULL,
            trial_end_date TEXT NOT NULL,
            trial_active INTEGER DEFAULT 1 NOT NULL,
            setup_state TEXT DEFAULT 'onboarding' NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (oauth_token_id) REFERENCES oauth_tokens(id)
        )
    """)
    
    # Create indexes for merchants
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_merchants_salla_store_id ON merchants(salla_store_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_merchants_setup_state ON merchants(setup_state)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_merchants_created_at ON merchants(created_at)")
    
    # Create oauth_tokens table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS oauth_tokens (
            id TEXT PRIMARY KEY,
            merchant_id TEXT UNIQUE NOT NULL,
            access_token TEXT NOT NULL,
            refresh_token TEXT,
            expires_at TEXT NOT NULL,
            scope TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (merchant_id) REFERENCES merchants(id)
        )
    """)
    
    # Create indexes for oauth_tokens
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_oauth_tokens_merchant_id ON oauth_tokens(merchant_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_oauth_tokens_expires_at ON oauth_tokens(expires_at)")
    
    # Create sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            merchant_id TEXT NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (merchant_id) REFERENCES merchants(id)
        )
    """)
    
    # Create indexes for sessions
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_merchant_id ON sessions(merchant_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at)")
    
    conn.commit()
    conn.close()
    
    print("✅ SQLite database initialized successfully")


def init_db_postgresql(db_url: str):
    """Initialize PostgreSQL database with Phase 1 schema using SQLAlchemy."""
    from database.models import Base
    
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    
    print("✅ PostgreSQL database initialized successfully")


def get_session_maker(db_url: str):
    """Get SQLAlchemy sessionmaker for the database."""
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session


if __name__ == "__main__":
    # Run this file directly to initialize database
    import sys
    
    if len(sys.argv) > 1:
        db_type = sys.argv[1]
        if db_type == "sqlite":
            db_path = sys.argv[2] if len(sys.argv) > 2 else "test.db"
            init_db_sqlite(db_path)
        elif db_type == "postgresql":
            db_url = sys.argv[2] if len(sys.argv) > 2 else "postgresql://user:password@localhost:5432/memberplus"
            init_db_postgresql(db_url)
    else:
        print("Usage: python init_db.py [sqlite|postgresql] [db_path|db_url]")
        print("Example: python init_db.py sqlite test.db")
        print("Example: python init_db.py postgresql postgresql://user:pass@localhost/memberplus")

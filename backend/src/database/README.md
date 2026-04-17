# Phase 1 Database Schema

## Overview

Phase 1 introduces the core database schema for merchant management, OAuth token storage, and session management.

## Tables

### merchants
Stores merchant profile information and trial/setup state.

```sql
CREATE TABLE merchants (
    id UUID PRIMARY KEY,
    salla_store_id VARCHAR(255) UNIQUE NOT NULL,
    store_name VARCHAR(255),
    merchant_email VARCHAR(255),
    merchant_phone VARCHAR(20),
    language VARCHAR(10) DEFAULT 'ar',
    
    oauth_token_id UUID FK -> oauth_tokens.id,
    
    trial_start_date TIMESTAMP NOT NULL,
    trial_end_date TIMESTAMP NOT NULL,
    trial_active BOOLEAN DEFAULT TRUE,
    
    setup_state VARCHAR(50) DEFAULT 'onboarding',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_merchants_salla_store_id ON merchants(salla_store_id);
CREATE INDEX idx_merchants_setup_state ON merchants(setup_state);
CREATE INDEX idx_merchants_created_at ON merchants(created_at);
```

**Fields**:
- `salla_store_id`: Unique identifier from Salla (prevents duplicates on reinstall)
- `language`: Merchant language preference ('ar' for Arabic, 'en' for English)
- `trial_start_date`, `trial_end_date`: Trial period boundaries
- `trial_active`: True until trial_end_date is reached
- `setup_state`: Tracks Phase progress (onboarding → setup_wizard → provisioning → active)

### oauth_tokens
Securely stores encrypted Salla OAuth tokens with refresh logic support.

```sql
CREATE TABLE oauth_tokens (
    id UUID PRIMARY KEY,
    merchant_id UUID UNIQUE FK -> merchants.id,
    
    access_token TEXT ENCRYPTED,
    refresh_token TEXT ENCRYPTED,
    expires_at TIMESTAMP NOT NULL,
    scope VARCHAR(500),
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX idx_oauth_tokens_merchant_id ON oauth_tokens(merchant_id);
CREATE INDEX idx_oauth_tokens_expires_at ON oauth_tokens(expires_at);
```

**Fields**:
- `access_token`: Salla API access token (MUST be encrypted)
- `refresh_token`: Token used to refresh access_token before expiration
- `expires_at`: When access_token expires (index for auto-refresh job)
- `scope`: OAuth scopes granted (e.g., "customers orders products discounts")

**Security Note**: Both tokens must be encrypted using AES or similar. See `backend/src/oauth/encryption.py` for implementation.

### sessions
Merchant dashboard session tokens for temporary authentication.

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    merchant_id UUID FK -> merchants.id,
    
    token VARCHAR(512) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    
    created_at TIMESTAMP
);

CREATE INDEX idx_sessions_merchant_id ON sessions(merchant_id);
CREATE INDEX idx_sessions_token ON sessions(token);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
```

**Fields**:
- `token`: JWT or opaque session token (should be unique)
- `expires_at`: When session expires (index for cleanup job)
- `ip_address`, `user_agent`: Audit trail

## Setup Instructions

### Initialize SQLite (Local Development)

```bash
cd backend
python -m src.database.init_db sqlite test.db
```

This creates `test.db` with all Phase 1 tables and indexes.

### Initialize PostgreSQL (Staging/Production)

```bash
python -m src.database.init_db postgresql "postgresql://user:password@localhost:5432/memberplus"
```

### Using SQLAlchemy (Alternative)

```python
from sqlalchemy import create_engine
from backend.src.database.models import Base

engine = create_engine("sqlite:///test.db")
Base.metadata.create_all(engine)
```

## Data Integrity Rules

### Constraints
- `merchants.salla_store_id` is UNIQUE (prevents duplicate merchant records)
- `oauth_tokens.merchant_id` is UNIQUE (one token per merchant)
- `sessions.token` is UNIQUE (one session per token)
- Foreign keys are enforced (ON DELETE CASCADE for dependent records)

### Indexes
- Index on `merchants.salla_store_id` for fast lookup by Salla ID
- Index on `merchants.setup_state` for filtering by phase
- Index on `oauth_tokens.expires_at` for token refresh scheduler
- Index on `sessions.expires_at` for session cleanup

## Migrations (Alembic)

Phase 1 includes Alembic setup for managing schema changes:

```bash
# Generate migration after model changes
alembic revision --autogenerate -m "Add Phase 1 tables"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Typical Queries

### Get merchant by Salla store ID
```python
from sqlalchemy.orm import Session
from backend.src.database.models import Merchant

merchant = session.query(Merchant).filter(
    Merchant.salla_store_id == "12345"
).first()
```

### Get tokens expiring soon
```python
from datetime import datetime, timedelta

expiring_tokens = session.query(OAuthToken).filter(
    OAuthToken.expires_at <= datetime.utcnow() + timedelta(minutes=5)
).all()
```

### Get active sessions for merchant
```python
active_sessions = session.query(Session).filter(
    Session.merchant_id == merchant_id,
    Session.expires_at > datetime.utcnow()
).all()
```

## Phase 2 Schema Extensions

Phase 2 will add:
- `membership_plans` table (Silver/Gold plans)
- `memberships` table (active subscriptions)
- `salla_resources` table (linked Salla customer groups, special offers)
- `setup_wizard_progress` table (track wizard step completion)

These will reference merchants via `merchant_id` foreign key.

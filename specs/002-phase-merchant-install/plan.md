# Implementation Plan: Phase 1 — Merchant Install and Trial Onboarding

**Branch**: `002-phase-merchant-install` | **Spec**: [spec.md](spec.md)

## Summary

Phase 1 enables merchants to install Member Plus from Salla, authorize app access via OAuth 2.0, automatically enter a trial state, and access a personal merchant dashboard. This phase unblocks Phase 2 (setup wizard) and establishes the merchant journey foundation.

**Primary Requirements**:
- OAuth 2.0 integration with Salla for app authorization
- Secure OAuth token storage and automatic refresh
- Merchant record creation upon authorization
- Trial state activation with configurable duration
- Merchant dashboard with authentication and bilingual support
- Welcome email upon successful installation

**Technical Approach**:
- Extend Phase 0 FastAPI backend with OAuth routes, merchant models, and dashboard API
- Add database migrations for merchant and OAuth token tables
- Build dashboard frontend as React SPA or server-rendered template
- Integrate email service for welcome email delivery
- Implement JWT or session-based merchant authentication

---

## Technical Context

**Language/Version**: Python 3.9+  
**Primary Dependencies**: FastAPI 0.104.1, Uvicorn 0.24.0, SQLAlchemy (ORM), Pydantic (validation)  
**Storage**: PostgreSQL or SQLite (for testing); tables: merchants, oauth_tokens, sessions  
**Testing**: pytest 8.4.2 for unit/integration; real Salla OAuth for staging/prod testing  
**Target Platform**: Linux server (ASGI with Uvicorn)  
**Project Type**: Web service (backend API + dashboard frontend)  
**Performance Goals**: OAuth callback handled in <500ms; dashboard API responses <200ms p95  
**Constraints**: OAuth token refresh must not block merchant requests; email must not block onboarding  
**Scale/Scope**: Initial target 1000 merchants in trial; 5 core backend modules + dashboard + email

---

## Architecture & Implementation Plan

### Phase 1 Backend Modules (Extensions to Phase 0)

**1. OAuth Module** (`backend/src/oauth/`)
- OAuth callback handler for Salla OAuth code flow
- Token management: secure storage, refresh logic, expiration handling
- Scope validation and error handling
- Modules: `provider.py` (OAuth logic), `store.py` (token persistence), `decorators.py` (auth checks)

**2. Merchant Module** (`backend/src/merchant/`)
- Merchant record creation, retrieval, updates
- Trial state management and countdown calculation
- Setup progress tracking (foundation for Phase 2+)
- Modules: `models.py` (ORM models), `service.py` (business logic), `repository.py` (DB access)

**3. Dashboard API Module** (`backend/src/dashboard/`)
- REST endpoints for dashboard frontend
- GET /api/merchant/profile — merchant and store info
- GET /api/merchant/trial — trial status and countdown
- GET /api/merchant/dashboard — overview data (placeholders for Phase 2+)
- Authentication middleware and merchant isolation checks

**4. Email Module** (`backend/src/email/`)
- Welcome email template (AR/EN)
- Email queue and send logic (async, with retry)
- Integration with email service (SendGrid, AWS SES, or similar)
- Modules: `templates.py` (template rendering), `queue.py` (async send), `service.py` (provider integration)

**5. Authentication Module** (`backend/src/auth/`)
- JWT token generation and validation (or session-based alternative)
- Merchant login/logout endpoints
- Session/token expiration and refresh logic
- Modules: `jwt.py` (token handling), `session.py` (if session-based), `middleware.py` (auth checks)

### Database Schema Additions

```sql
-- merchants table
CREATE TABLE merchants (
  id UUID PRIMARY KEY,
  salla_store_id VARCHAR(255) UNIQUE NOT NULL,
  store_name VARCHAR(255),
  merchant_email VARCHAR(255),
  merchant_phone VARCHAR(20),
  language VARCHAR(10) DEFAULT 'ar',
  
  oauth_token_id UUID FK REFERENCES oauth_tokens(id),
  
  trial_start_date TIMESTAMP NOT NULL,
  trial_end_date TIMESTAMP NOT NULL,
  trial_active BOOLEAN DEFAULT TRUE,
  
  setup_state VARCHAR(50) DEFAULT 'onboarding',
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- oauth_tokens table
CREATE TABLE oauth_tokens (
  id UUID PRIMARY KEY,
  merchant_id UUID FK REFERENCES merchants(id),
  access_token TEXT ENCRYPTED,
  refresh_token TEXT ENCRYPTED,
  expires_at TIMESTAMP,
  scope VARCHAR(500),
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- sessions table (if using session-based auth)
CREATE TABLE sessions (
  id UUID PRIMARY KEY,
  merchant_id UUID FK REFERENCES merchants(id),
  token TEXT UNIQUE,
  expires_at TIMESTAMP,
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### API Endpoints

**OAuth & Authentication**:
- `GET /api/oauth/authorize` — Redirect to Salla OAuth consent screen
- `GET /api/oauth/callback?code=... state=...` — OAuth callback handler (creates merchant record, returns redirect to dashboard)
- `POST /api/auth/login` — Manual login (if applicable; redirect to /auth/salla for standard flow)
- `POST /api/auth/logout` — Logout (clears session/token)

**Merchant Dashboard**:
- `GET /api/merchant/profile` — Merchant profile (name, email, store name, language)
- `GET /api/merchant/trial` — Trial status (start_date, end_date, remaining_days, active)
- `GET /api/merchant/dashboard` — Dashboard overview (setup_state, member_count[0 for Phase 1], revenue[0 for Phase 1])
- `PATCH /api/merchant/preferences` — Update language preference

**Health & Status**:
- `GET /health` — Phase 0 health endpoint (reused)
- `GET /status` — Phase 1 status (includes Salla OAuth connectivity check)

### Dashboard Frontend

**Technology**: React SPA (recommended) or server-rendered Jinja2 template (simpler)

**Routes**:
- `/login` — OAuth redirect or manual login form
- `/dashboard` — Main dashboard (protected route)
- `/dashboard/profile` — Merchant profile editor
- `/dashboard/setup` — Setup progress tracker (placeholder for Phase 2)

**Components**:
- AuthGuard (protected routes)
- Dashboard layout (header, sidebar, main content)
- Trial countdown widget
- Merchant profile card
- Placeholder widgets for Phase 2+ features
- Language toggle (AR/EN)
- Responsive design (mobile-first)

### Email Integration

**Welcome Email Template** (Bilingual):

**English**:
```
Subject: Welcome to Member Plus! 🎉

Hi [Merchant Name],

Thank you for installing Member Plus on your store "[Store Name]"!

Your trial is now active and will last for 14 days. During this time, you can:
✓ Set up your membership program
✓ Configure plans and pricing
✓ Test the entire member experience
✓ Get support from our team

Next Steps:
1. Go to your dashboard: [Dashboard Link]
2. Complete the setup wizard
3. Configure your membership plans

Questions? We're here to help: support@memberplus.com

Best regards,
Member Plus Team
```

**Arabic**: [Similar content in Arabic]

---

## Implementation Phases (Sub-Tasks)

### Phase 1.1: OAuth Integration (Days 1-3)
- Implement OAuth callback route
- Integrate with Salla OAuth API
- Secure token storage and encryption
- Token refresh background job
- Error handling and logging

### Phase 1.2: Merchant Module & Database (Days 2-3)
- Create merchant database schema
- Implement merchant service (create, update, retrieve)
- Add trial state logic
- Database migrations

### Phase 1.3: Dashboard Backend API (Days 4-5)
- Implement /api/merchant/* endpoints
- Add merchant authentication middleware
- Merchant isolation checks (authorization tests)
- Error responses and status codes

### Phase 1.4: Dashboard Frontend (Days 5-7)
- Create dashboard React/template
- Implement OAuth redirect flow
- Build responsive layout
- Add language toggle
- Trial countdown widget

### Phase 1.5: Email Service (Days 6-7)
- Integrate with email provider (SendGrid, etc.)
- Create welcome email templates (AR/EN)
- Implement async email queue
- Retry logic and error handling

### Phase 1.6: Testing & Documentation (Days 7-8)
- Unit tests for OAuth, merchant service, email
- Integration tests for OAuth callback, dashboard API
- E2E tests for complete onboarding flow
- Documentation (Quickstart, API docs, email setup)
- Staging deployment and validation

---

## Clarifications & Open Items

| Item | Status | Impact |
|------|--------|--------|
| Salla OAuth app registration details | PENDING | Blocks OAuth implementation (coordinate with Salla) |
| Email service provider choice | PENDING | Blocks email implementation (decision needed: SendGrid, SES, Postmark?) |
| Dashboard tech stack (React vs. server-rendered?) | PENDING | Affects frontend architecture and timeline |
| Merchant authentication method (JWT vs. session?) | PENDING | Affects auth middleware and session management |
| Trial duration (14 days? 30 days?) | PENDING | Can default to 14 days; configurable via env var |
| Should Phase 1 include Salla uninstall webhooks? | PENDING | May be Phase 2+ scope; clarify with product |

---

## Dependencies & Prerequisites

**From Phase 0**:
- ✅ FastAPI backend foundation
- ✅ Config and secrets management
- ✅ Health checks and logging
- ✅ Webhook receiver skeleton (reuse for Phase 1+ events)

**External**:
- 🔵 Salla OAuth app registration (must be completed before development)
- 🔵 Email service account and credentials (SendGrid, SES, etc.)
- 🔵 Database (PostgreSQL recommended; SQLite for local dev)

**Timeline Assumption**: ~8 days (including testing, documentation, and deployment to staging)

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Salla OAuth API changes/delays | Start with mock OAuth in dev; real integration in staging |
| Email service outage | Make email async; don't block onboarding; log and retry |
| Token refresh fails repeatedly | Alert merchant; force re-auth flow; don't silently fail |
| Dashboard feature scope creeps | Freeze requirements at spec; defer Phase 2 features to Phase 2 |
| Database performance (many merchants) | Add indexes on salla_store_id, merchant_id; plan for sharding later |
| Security issues (token leakage, auth bypass) | Security review before staging; pen test in Phase 0 hardening |

---

## Deliverables

- OAuth integration module with token management
- Merchant service and database schema
- Dashboard API endpoints (5+ routes)
- Dashboard frontend (React or template-based)
- Welcome email templates (AR/EN) and email service integration
- Merchant authentication system (JWT or session-based)
- Database migrations
- Unit tests (OAuth, merchant service, email, auth) — target 80%+ coverage
- Integration tests (OAuth callback, dashboard API, email)
- E2E test (complete onboarding flow)
- Quickstart guide (Phase 1 local setup and testing)
- API documentation (endpoints, request/response formats, auth)
- Deployment checklist (env vars, secrets, database setup)

---

## Success Metrics

- All user stories from spec can be tested independently
- OAuth callback converts to merchant record in <500ms
- Dashboard API responses in <200ms p95
- Welcome email sent within 1 minute of OAuth completion
- Trial calculation is accurate (±1 second)
- No merchant can access another merchant's data (comprehensive auth tests)
- Phase 2 can seamlessly build on Phase 1 (API contracts stable, setup_state tracking works)


| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |

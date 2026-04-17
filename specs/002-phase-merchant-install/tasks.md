# Phase 1 Tasks: Merchant Install and Trial Onboarding

**Feature**: 002-phase-merchant-install  
**Total Tasks**: 32 across 6 phases  
**Status**: Ready for Implementation

---

## Phase 1.1: Setup & Foundation (5 tasks)

### T001: [Setup] Initialize Phase 1 database schema

**Story**: Setup  
**Parallelizable**: [P]  
**Location**: `backend/src/oauth/`, `backend/src/merchant/models.py`, database migrations  

Define and create database tables: `merchants`, `oauth_tokens`, `sessions`. Include indexes on `salla_store_id`, `merchant_id`, `expires_at`. Write migration scripts and rollback logic.

**Dependencies**: Phase 0 database setup  
**Estimated**: 4 hours  
**Acceptance**: Schema created, migrations tested locally

---

### T002: [Setup] Set up email service integration

**Story**: Setup  
**Parallelizable**: [P]  
**Location**: `backend/src/email/`  

Choose email provider (SendGrid, AWS SES, Postmark), obtain API keys, configure SMTP or HTTP integration, implement basic send test. Create email configuration in Phase 0 config loader.

**Dependencies**: Email provider account  
**Estimated**: 3 hours  
**Acceptance**: Test email sends successfully to test recipient

---

### T003: [Setup] Configure Salla OAuth credentials

**Story**: Setup  
**Parallelizable**: [P]  
**Location**: Config files, environment setup  

Obtain Salla OAuth app ID, secret, and redirect URI from Salla app registration. Document OAuth scopes (customers, orders, products, discounts, etc.). Store credentials in Phase 0 config system.

**Dependencies**: Salla app registration completed  
**Estimated**: 2 hours  
**Acceptance**: OAuth credentials stored and verified in config

---

### T004: [Setup] Implement OAuth configuration and constants

**Story**: Setup  
**Parallelizable**: [P]  
**Location**: `backend/src/oauth/config.py`  

Define OAuth constants (Salla authorization URL, token endpoint, scopes, redirect URI). Create OAuth configuration dataclass matching Phase 0 config pattern.

**Dependencies**: T003 (OAuth credentials)  
**Estimated**: 2 hours  
**Acceptance**: OAuth config loads correctly, all constants defined

---

### T005: [Setup] Create empty OAuth and merchant modules

**Story**: Setup  
**Parallelizable**: [P]  
**Location**: `backend/src/oauth/`, `backend/src/merchant/`, `backend/src/email/`, `backend/src/auth/`  

Create module structure with `__init__.py` files. Add basic module docstrings. Prepare for implementation phases.

**Dependencies**: Phase 0 structure  
**Estimated**: 1 hour  
**Acceptance**: All module directories created with correct structure

---

## Phase 1.2: OAuth & Token Management (6 tasks)

### T006: [OAuth] Implement OAuth provider integration

**Story**: Merchant Can Authorize App Access  
**Parallelizable**: [P]  
**Location**: `backend/src/oauth/provider.py`  

Implement OAuth 2.0 authorization code flow: generate authorization URL, exchange code for token, refresh token logic. Use requests library or similar.

**Dependencies**: T003, T004  
**Estimated**: 6 hours  
**Acceptance**: OAuth flow works end-to-end with Salla test app; tokens are returned correctly

---

### T007: [OAuth] Implement secure token storage

**Story**: Merchant Can Authorize App Access  
**Parallelizable**: [P]  
**Location**: `backend/src/oauth/store.py`, `backend/src/merchant/models.py`  

Implement encrypted token storage in `oauth_tokens` table. Use encryption (e.g., Fernet from cryptography library) for access_token and refresh_token. Add retrieve, update, and delete functions.

**Dependencies**: T001 (database schema), T006  
**Estimated**: 5 hours  
**Acceptance**: Tokens stored encrypted; retrieval decrypts correctly; encryption key management validated

---

### T008: [OAuth] Implement automatic token refresh

**Story**: Merchant Can Authorize App Access  
**Parallelizable**: [P]  
**Location**: `backend/src/oauth/store.py`, background jobs  

Create background job (scheduler from Phase 0) to refresh tokens 5 minutes before expiration. Update tokens in database, log refresh events. Handle refresh failures gracefully.

**Dependencies**: T007, Phase 0 scheduler  
**Estimated**: 4 hours  
**Acceptance**: Token refresh happens automatically; no merchant interruption; failures logged

---

### T009: [OAuth] Create OAuth callback route

**Story**: Merchant Can Install the App  
**Parallelizable**: N  
**Location**: `backend/src/app-entrypoint/main.py`, new route  

Implement `GET /api/oauth/callback?code=...&state=...` route. Exchange code for token, create merchant record (call T011), set trial state (call T013), send welcome email (call T018). Return redirect to dashboard.

**Dependencies**: T006, T007, T008, T011, T013, T018  
**Estimated**: 5 hours  
**Acceptance**: Callback handler creates merchant record, sets trial, sends email, redirects to dashboard

---

### T010: [OAuth] Add OAuth error handling

**Story**: Merchant Can Authorize App Access  
**Parallelizable**: [P]  
**Location**: `backend/src/oauth/provider.py`, error handlers  

Implement OAuth error scenarios: denied authorization, invalid code, expired state, network failures. Return user-friendly error pages with messaging.

**Dependencies**: T006, T009  
**Estimated**: 3 hours  
**Acceptance**: All OAuth error scenarios handled gracefully; error messages clear

---

### T011: [OAuth] Write unit tests for OAuth module

**Story**: (Cross-cutting)  
**Parallelizable**: [P]  
**Location**: `backend/tests/unit/test_oauth_provider.py`, `test_oauth_store.py`  

Write unit tests for OAuth functions: authorization URL generation, token exchange, token refresh, error cases. Mock Salla API responses.

**Dependencies**: T006, T007, T008  
**Estimated**: 4 hours  
**Acceptance**: 15+ tests passing; 80%+ code coverage

---

## Phase 1.3: Merchant Record Management (5 tasks)

### T012: [Merchant] Implement merchant service

**Story**: Merchant Can Install the App  
**Parallelizable**: [P]  
**Location**: `backend/src/merchant/service.py`  

Implement merchant CRUD operations: create_merchant(), get_merchant_by_id(), get_merchant_by_salla_store_id(), update_merchant(), delete_merchant(). Handle duplicate prevention (unique salla_store_id).

**Dependencies**: T001 (database schema)  
**Estimated**: 4 hours  
**Acceptance**: All CRUD operations work; duplicate prevention validated

---

### T013: [Merchant] Implement trial activation logic

**Story**: Merchant Enters Trial State Automatically  
**Parallelizable**: [P]  
**Location**: `backend/src/merchant/service.py`  

Implement trial state: set trial_start_date, calculate trial_end_date (start + configurable duration), set trial_active = true. Implement countdown calculation (remaining_days).

**Dependencies**: T012  
**Estimated**: 2 hours  
**Acceptance**: Trial dates calculated correctly; countdown accurate

---

### T014: [Merchant] Implement setup progress tracking

**Story**: Phase 1 → Phase 2 Handoff  
**Parallelizable**: [P]  
**Location**: `backend/src/merchant/service.py`, merchant model  

Add setup_state field to merchant record: 'onboarding' (Phase 1), 'setup_wizard' (Phase 2), 'provisioning' (Phase 3), 'active' (Phase 4+). Implement state transition logic.

**Dependencies**: T012  
**Estimated**: 2 hours  
**Acceptance**: Setup state stored and retrieved correctly; transitions work

---

### T015: [Merchant] Implement merchant repository pattern

**Story**: (Cross-cutting)  
**Parallelizable**: [P]  
**Location**: `backend/src/merchant/repository.py`  

Implement database access layer for merchants: find by ID, find by salla_store_id, save, update, delete. Use SQLAlchemy ORM.

**Dependencies**: T001, T012  
**Estimated**: 3 hours  
**Acceptance**: All repo methods work; database operations verified

---

### T016: [Merchant] Write unit tests for merchant service

**Story**: (Cross-cutting)  
**Parallelizable**: [P]  
**Location**: `backend/tests/unit/test_merchant_service.py`, `test_trial_logic.py`  

Write unit tests for merchant CRUD, trial calculations, setup state transitions. Mock database.

**Dependencies**: T012, T013, T014, T015  
**Estimated**: 4 hours  
**Acceptance**: 20+ tests passing; 80%+ coverage

---

## Phase 1.4: Dashboard Backend API (5 tasks)

### T017: [Dashboard API] Implement merchant authentication middleware

**Story**: Merchant Can Access Dashboard Shell  
**Parallelizable**: [P]  
**Location**: `backend/src/auth/middleware.py`, `backend/src/auth/jwt.py`  

Implement JWT or session-based authentication. Create middleware that validates token/session and extracts merchant_id. Add auth decorators for protected routes.

**Dependencies**: Phase 0 config  
**Estimated**: 5 hours  
**Acceptance**: Protected routes reject unauthenticated requests; valid tokens grant access

---

### T018: [Dashboard API] Implement /api/merchant/profile endpoint

**Story**: Merchant Can Access Dashboard Shell  
**Parallelizable**: [P]  
**Location**: `backend/src/dashboard/routes.py`  

Implement `GET /api/merchant/profile` endpoint. Return merchant ID, name, email, store_name, language. Authenticate and validate merchant owns the data.

**Dependencies**: T017, T012  
**Estimated**: 2 hours  
**Acceptance**: Endpoint returns correct merchant data; authorization validated

---

### T019: [Dashboard API] Implement /api/merchant/trial endpoint

**Story**: Merchant Enters Trial State Automatically  
**Parallelizable**: [P]  
**Location**: `backend/src/dashboard/routes.py`  

Implement `GET /api/merchant/trial` endpoint. Return trial_start_date, trial_end_date, trial_active, remaining_days. Authenticate request.

**Dependencies**: T017, T013  
**Estimated**: 2 hours  
**Acceptance**: Endpoint returns accurate trial data; countdown correct

---

### T020: [Dashboard API] Implement /api/merchant/dashboard endpoint

**Story**: Merchant Can Access Dashboard Shell  
**Parallelizable**: [P]  
**Location**: `backend/src/dashboard/routes.py`  

Implement `GET /api/merchant/dashboard` endpoint. Return overview data: setup_state, member_count (0 for Phase 1), revenue (0 for Phase 1), trial status. Add placeholder for Phase 2+ metrics.

**Dependencies**: T017, T014  
**Estimated**: 2 hours  
**Acceptance**: Endpoint returns dashboard overview; supports future metric additions

---

### T021: [Dashboard API] Write integration tests for dashboard API

**Story**: (Cross-cutting)  
**Parallelizable**: [P]  
**Location**: `backend/tests/integration/test_dashboard_api.py`  

Write integration tests for dashboard endpoints: auth checks, merchant isolation, data correctness, edge cases.

**Dependencies**: T017, T018, T019, T020  
**Estimated**: 5 hours  
**Acceptance**: 15+ integration tests passing; merchant isolation verified

---

## Phase 1.5: Dashboard Frontend (5 tasks)

### T022: [Frontend] Create dashboard project structure

**Story**: Merchant Can Access Dashboard Shell  
**Parallelizable**: [P]  
**Location**: `frontend/` or `backend/frontend/`  

Initialize React/Vue project (or template if server-rendered). Set up build system, routing, authentication guards. Create basic layout structure.

**Dependencies**: Project decision on tech stack  
**Estimated**: 3 hours  
**Acceptance**: Project builds; basic structure in place

---

### T023: [Frontend] Implement dashboard layout & components

**Story**: Merchant Can Access Dashboard Shell  
**Parallelizable**: [P]  
**Location**: `frontend/src/components/`, `frontend/src/pages/`  

Build responsive dashboard layout: header, sidebar, main content area. Create trial countdown widget, merchant profile card, placeholder widgets. Style for mobile-first responsiveness.

**Dependencies**: T022  
**Estimated**: 8 hours  
**Acceptance**: Dashboard is responsive (mobile, tablet, desktop); all components render correctly

---

### T024: [Frontend] Implement language toggle (AR/EN)

**Story**: Merchant Can Access Dashboard Shell  
**Parallelizable**: [P]  
**Location**: `frontend/src/i18n/`, `frontend/src/components/LanguageToggle.jsx`  

Implement i18n library (react-intl, vue-i18n, etc.). Create translation files for Arabic and English. Add language toggle button.

**Dependencies**: T023  
**Estimated**: 4 hours  
**Acceptance**: Toggle switches language; all UI text translated

---

### T025: [Frontend] Implement OAuth redirect flow

**Story**: Merchant Can Install the App  
**Parallelizable**: [P]  
**Location**: `frontend/src/pages/Login.jsx`, `frontend/src/auth/`  

Create login page that redirects to Salla OAuth. Handle OAuth callback, store token in localStorage (or secure cookie), redirect to dashboard.

**Dependencies**: T022, T009  
**Estimated**: 4 hours  
**Acceptance**: OAuth redirect works; token stored; dashboard loads after auth

---

### T026: [Frontend] Write frontend tests (unit + E2E)

**Story**: (Cross-cutting)  
**Parallelizable**: [P]  
**Location**: `frontend/tests/unit/`, `frontend/tests/e2e/`  

Write Jest/React Testing Library tests for components, routing, language toggle. Write Cypress/Selenium E2E tests for onboarding flow.

**Dependencies**: T023, T024, T025  
**Estimated**: 6 hours  
**Acceptance**: 20+ tests passing; happy path E2E test passes

---

## Phase 1.6: Email & Notifications (4 tasks)

### T027: [Email] Create welcome email templates (AR/EN)

**Story**: Merchant Receives Welcome Email  
**Parallelizable**: [P]  
**Location**: `backend/src/email/templates/`  

Create HTML email templates for welcome email in Arabic and English. Include merchant name, store name, trial duration, dashboard link, next steps.

**Dependencies**: T002  
**Estimated**: 3 hours  
**Acceptance**: Templates render correctly; links work; bilingual content complete

---

### T028: [Email] Implement email queue and async sending

**Story**: Merchant Receives Welcome Email  
**Parallelizable**: [P]  
**Location**: `backend/src/email/queue.py`, `backend/src/email/service.py`  

Implement email queue (Redis or in-memory for Phase 1) and async background job to send emails. Do not block onboarding flow on email failures.

**Dependencies**: T002, T027  
**Estimated**: 4 hours  
**Acceptance**: Emails sent asynchronously; failures logged; onboarding completes even if email fails

---

### T029: [Email] Implement email retry and error handling

**Story**: Merchant Receives Welcome Email  
**Parallelizable**: [P]  
**Location**: `backend/src/email/service.py`  

Add retry logic for failed email sends (exponential backoff). Log all email events (sent, failed, retried). Send alert if repeated failures.

**Dependencies**: T028  
**Estimated**: 3 hours  
**Acceptance**: Failed emails retried; logs captured; alerts triggered

---

### T030: [Email] Write unit tests for email module

**Story**: (Cross-cutting)  
**Parallelizable**: [P]  
**Location**: `backend/tests/unit/test_email_service.py`  

Write tests for email template rendering, queue operations, retry logic. Mock email provider.

**Dependencies**: T027, T028, T029  
**Estimated**: 3 hours  
**Acceptance**: 15+ email tests passing; template rendering validated

---

## Phase 1.7: Integration & Testing (2 tasks)

### T031: [Integration] Write end-to-end onboarding test

**Story**: (Phase 1 Acceptance)  
**Parallelizable**: N  
**Location**: `backend/tests/integration/test_phase1_e2e.py`  

Write comprehensive E2E test covering full Phase 1 flow: OAuth callback → merchant creation → trial activation → dashboard access → email sent. Use test fixtures and mock Salla API.

**Dependencies**: T009, T012, T013, T017, T027, T028  
**Estimated**: 6 hours  
**Acceptance**: E2E test passes; covers all happy path scenarios

---

### T032: [Integration] Write quickstart guide and Phase 1 documentation

**Story**: (Cross-cutting)  
**Location**: `specs/002-phase-merchant-install/quickstart.md`, `backend/README.md`  

Write Phase 1 quickstart: local setup, environment variables, running server, accessing dashboard, testing OAuth callback. Document API endpoints and error codes.

**Dependencies**: All Phase 1 tasks  
**Estimated**: 4 hours  
**Acceptance**: Quickstart is complete; new developer can follow and run Phase 1 successfully

---

## Phase 1.8: Security & Documentation (2 tasks)

### T033: [Security] Implement merchant data isolation tests

**Story**: (Cross-cutting)  
**Parallelizable**: [P]  
**Location**: `backend/tests/integration/test_merchant_isolation.py`  

Write comprehensive authorization tests: Merchant A cannot access Merchant B's profile, trial, or any endpoint. Test token/session validation. Verify API returns 403 Forbidden for unauthorized access.

**Dependencies**: T017, T018, T019, T020  
**Estimated**: 4 hours  
**Acceptance**: 10+ isolation tests passing; no data leakage between merchants

---

### T034: [Documentation] Write Phase 1 API documentation

**Story**: (Cross-cutting)  
**Location**: `backend/docs/Phase1_API.md`  

Document all Phase 1 API endpoints: OAuth routes, dashboard API, authentication. Include request/response formats, error codes, example curl commands, language support.

**Dependencies**: All Phase 1 API tasks  
**Estimated**: 3 hours  
**Acceptance**: Complete API documentation; all endpoints documented with examples

---

## Phase 1.9: Deployment & Hardening (1 task)

### T035: [Deployment] Prepare Phase 1 for staging deployment

**Story**: (Cross-cutting)  
**Parallelizable**: N  
**Location**: `deployment/`, `docker-compose.yml`, `.env.example`  

Create deployment configs: Docker setup, environment variable checklist, database migration scripts, secrets management. Document staging deployment process.

**Dependencies**: All Phase 1 tasks  
**Estimated**: 4 hours  
**Acceptance**: Staging deployment checklist complete; all required env vars documented

---

## Summary

**Total Tasks**: 35 across 9 sub-phases  
**Estimated Timeline**: 12-14 days (assuming 2 developers, some parallelization)  
**Dependencies**: 
- Phase 0 complete (backend foundation, config, scheduler)
- Salla OAuth app registration completed
- Email service account and credentials available

**Key Milestones**:
- ✓ T001-T005: Foundation setup (Day 1-2)
- ✓ T006-T011: OAuth & token mgmt complete (Day 3-5)
- ✓ T012-T016: Merchant records & logic (Day 5-7)
- ✓ T017-T021: Dashboard API (Day 7-9)
- ✓ T022-T026: Dashboard frontend (Day 7-12)
- ✓ T027-T030: Email service (Day 9-11)
- ✓ T031-T035: Testing, docs, deployment (Day 11-14)

**Definition of Done for Phase 1**:
- ✅ All 35 tasks completed
- ✅ Unit tests: 80%+ coverage
- ✅ Integration tests: E2E onboarding passes
- ✅ Security: Merchant isolation verified
- ✅ Deployed to staging and validated
- ✅ Documentation complete (API, quickstart, deployment)
- ✅ Merchant can install app → reach dashboard → receive email

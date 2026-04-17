# Phase 1 Specification: Merchant Install and Trial Onboarding

**Feature**: 002-phase-merchant-install  
**Status**: Open  
**Objective**: Enable a merchant to install the app, authorize it, enter trial state, and access the initial dashboard shell.

## Overview

Phase 1 is the first operational entry point for merchants. A merchant must be able to install the app from Salla, authorize it to access their store, automatically enter a trial state, and access a working merchant dashboard.

---

## User Stories & Acceptance Scenarios

### User Story 1 - Merchant Can Install the App (Priority: P1)

A Salla merchant can discover and install the Member Plus app from the Salla app store, triggering the OAuth authorization flow and creating their initial merchant record.

**Why this priority**: Installation is the entry point for all merchants. Without this, no other Phase 1 functionality is reachable.

**Independent Test**: Can be fully tested by navigating Salla app store, clicking "Install", completing OAuth, and verifying merchant record exists in database.

**Acceptance Scenarios**:

1. **Given** merchant is on Salla app store, **When** they click "Install Member Plus", **Then** the OAuth authorization screen appears
2. **Given** merchant completes OAuth authorization, **When** authorization succeeds, **Then** they are redirected to Member Plus dashboard
3. **Given** merchant completes OAuth, **When** dashboard loads, **Then** a merchant record is created in the database
4. **Given** merchant installs app twice, **When** second install completes, **Then** no duplicate record is created (existing record is updated)

---

### User Story 2 - Merchant Can Authorize App Access (Priority: P1)

A merchant can review and approve OAuth permissions for Member Plus to access their store data (customers, orders, products, discounts, etc.), and the system securely stores and manages the OAuth token.

**Why this priority**: Authorization is required before any store integration can occur. Without valid OAuth token, the app cannot function.

**Independent Test**: Can be fully tested by capturing OAuth request, verifying scopes, approving, and confirming token is stored securely and can be used for API calls.

**Acceptance Scenarios**:

1. **Given** merchant is on OAuth screen, **When** they view requested scopes, **Then** scopes include customers, orders, products, discounts, and store info
2. **Given** merchant clicks "Approve", **When** OAuth completes, **Then** OAuth token is securely stored in database
3. **Given** OAuth token is about to expire, **When** background job runs, **Then** token is automatically refreshed before expiration
4. **Given** merchant clicks "Deny" on OAuth screen, **When** authorization fails, **Then** user sees error message and install flow is halted gracefully

---

### User Story 3 - Merchant Enters Trial State Automatically (Priority: P1)

Upon successful OAuth authorization, the merchant's account automatically enters a trial state with a configurable trial duration (e.g., 14 or 30 days).

**Why this priority**: Trial state unlocks Phase 2 setup wizard and all subsequent features. Without trial state, merchant cannot progress beyond onboarding.

**Independent Test**: Can be fully tested by completing OAuth and verifying trial_start_date and trial_end_date are set correctly, trial_active is true, and dashboard displays accurate countdown.

**Acceptance Scenarios**:

1. **Given** merchant completes OAuth authorization, **When** merchant record is created, **Then** trial_start_date is set to current date
2. **Given** trial duration is 14 days, **When** trial_start_date is set, **Then** trial_end_date is calculated as start_date + 14 days
3. **Given** merchant is in trial, **When** they view dashboard, **Then** trial status and remaining days are displayed correctly
4. **Given** trial end date approaches, **When** remaining days are 0, **Then** trial_active is set to false (disabled merchant signup for next phase handling)

---

### User Story 4 - Merchant Can Access Dashboard Shell (Priority: P1)

A merchant can log in to their personal dashboard, which displays their merchant profile, store information, trial status, and placeholder widgets for future features.

**Why this priority**: Dashboard is the hub for all merchant operations. Every future phase (setup wizard, provisioning, analytics) connects to dashboard.

**Independent Test**: Can be fully tested by logging in as merchant, verifying dashboard displays correct merchant/store info and trial countdown, and checking all placeholder widgets are present.

**Acceptance Scenarios**:

1. **Given** merchant has completed OAuth, **When** they access `/dashboard`, **Then** authentication check passes and dashboard loads
2. **Given** merchant is viewing dashboard, **When** page fully loads, **Then** it displays merchant name, store name, and trial countdown
3. **Given** merchant is viewing dashboard, **When** they toggle language, **Then** all dashboard text switches to Arabic or English
4. **Given** merchant is not authenticated, **When** they try to access `/dashboard`, **Then** they are redirected to login page
5. **Given** merchant is viewing dashboard on mobile, **When** page is viewed at 375px width, **Then** layout is responsive and readable

---

### User Story 5 - Merchant Receives Welcome Email (Priority: P2)

Immediately after successful OAuth authorization, the merchant receives a welcome email confirming app installation and providing next steps.

**Why this priority**: Email confirms installation success and drives engagement. Without this touchpoint, merchants may be unsure if setup worked correctly. P2 because it's not blocking functionality but is critical for user confidence.

**Independent Test**: Can be fully tested by completing OAuth, checking email inbox, verifying email content is correct, and clicking dashboard link in email works.

**Acceptance Scenarios**:

1. **Given** merchant completes OAuth authorization, **When** authorization succeeds, **Then** welcome email is queued for sending
2. **Given** welcome email is sent, **When** merchant receives it, **Then** email includes merchant name, store name, and trial duration
3. **Given** merchant receives welcome email, **When** they click dashboard link, **Then** link is valid and dashboard loads
4. **Given** email service is unavailable, **When** email send fails, **Then** failure is logged but merchant onboarding is not blocked
5. **Given** merchant's language preference is Arabic, **When** welcome email is sent, **Then** email content is in Arabic

---

### Edge Cases

- What happens if OAuth token expires while merchant is using dashboard? (Auto-refresh or force re-auth?)
- What if merchant uninstalls and reinstalls the app? (Should restore previous record or create new?)
- What if email service fails to send welcome email? (Should retry or allow onboarding to complete anyway?)
- What if merchant changes their store name on Salla after installing? (Should we sync on each login or periodically?)

---

## Functional Requirements

- **FR-001**: System MUST implement OAuth 2.0 authorization code flow with Salla API
- **FR-002**: System MUST securely store OAuth tokens encrypted in database
- **FR-003**: System MUST automatically refresh OAuth tokens 5 minutes before expiration
- **FR-004**: System MUST create a merchant record upon successful OAuth authorization
- **FR-005**: System MUST prevent duplicate merchant records for same Salla store ID
- **FR-006**: System MUST automatically activate trial state with configurable duration upon merchant creation
- **FR-007**: System MUST provide authenticated dashboard accessible only to the merchant owning it
- **FR-008**: System MUST display merchant name, store name, and trial countdown on dashboard
- **FR-009**: System MUST support bilingual dashboard (Arabic and English) with language toggle
- **FR-010**: System MUST send welcome email within 1 minute of successful OAuth
- **FR-011**: System MUST support merchant authentication via JWT tokens or sessions
- **FR-012**: System MUST provide API endpoints for dashboard to query merchant profile and trial status
- **FR-013**: System MUST log all OAuth events, merchant creation, and authentication attempts for audit
- **FR-014**: System MUST handle OAuth failures gracefully with user-friendly error messages
- **FR-015**: System MUST validate merchant isolation (no merchant can access another merchant's data)

### Key Entities

- **Merchant**: Represents a Salla store owner. Attributes: salla_store_id (unique), store_name, merchant_email, language preference, oauth_token (encrypted), trial_start_date, trial_end_date, trial_active, created_at, updated_at
- **OAuth Token**: Salla OAuth credential. Attributes: access_token, refresh_token, expires_at, scope, merchant_id (FK)
- **Session/Token**: Merchant authentication credential for dashboard access. Attributes: token_value, merchant_id (FK), expires_at, created_at

---

## Success Criteria

- **SC-001**: A merchant can successfully install the app, complete OAuth, and land on dashboard without errors (end-to-end happy path works)
- **SC-002**: Dashboard displays accurate merchant name, store name, and trial countdown matching database records
- **SC-003**: Merchant authentication is validated; one merchant cannot access another merchant's dashboard or data
- **SC-004**: OAuth token refresh works automatically; merchants remain logged in for 24+ hours without re-auth
- **SC-005**: Welcome email is sent and arrives within 5 minutes with correct merchant name, store name, and clickable dashboard link
- **SC-006**: Dashboard is fully responsive and functional on desktop (1920px), tablet (768px), and mobile (375px) viewports
- **SC-007**: Merchant can toggle language on dashboard and all text switches between Arabic and English
- **SC-008**: Trial end date is calculated correctly; remaining days count down accurately
- **SC-009**: All OAuth errors (denied, expired, network failure) are handled gracefully with clear error messaging
- **SC-010**: Setup progress tracking foundation exists so Phase 2 can detect Phase 1 completion

---

## Assumptions

- Salla OAuth app registration and credentials are completed before Phase 1 implementation begins
- The email service (SendGrid, AWS SES, etc.) is available and configured with merchant-facing email address
- Merchant record database is available and functional
- Dashboard frontend can be built independently of backend (API contracts defined early)
- Language preference defaults to Arabic if not specified
- Trial duration is configurable via environment variable (default 14 days)
- HTTPS/TLS is enforced for all OAuth and authentication flows
- Merchant email from Salla OAuth is accurate and deliverable

---

## Dependencies

**From Phase 0**:
- Phase 0 backend foundation (FastAPI, config, health checks)
- Webhook receiver skeleton (for future Salla events)
- Configuration and secrets management system
- Logging infrastructure

**External**:
- Salla OAuth API and app registration (must be completed)
- Email service provider (SendGrid, AWS SES, Postmark, or similar)
- Database (PostgreSQL, MySQL, or similar)
- Session/JWT authentication library for merchant dashboard

**Future Phases**:
- Phase 2 will depend on trial_start_date, trial_end_date, and setup_state in merchant record
- Phase 3 will depend on valid OAuth token to provision Salla resources
- Phase 7 will depend on merchant authentication system from Phase 1

---

## Open Questions

- **NEEDS CLARIFICATION**: Should Phase 1 include Salla webhook handling for app uninstall events? (Currently listed as Phase 1+ but may be Phase 2+)
- **NEEDS CLARIFICATION**: Which authentication method should be used for merchants (stateless JWT, session-based, or both)?
- **NEEDS CLARIFICATION**: Should merchant's Salla store name be synced automatically on each login or only during initial installation?
- **NEEDS CLARIFICATION**: What should happen if OAuth token refresh fails multiple times (auto-retry, notify merchant, force re-auth)?
- **NEEDS CLARIFICATION**: Should the welcome email include a CTA to immediately start the setup wizard, or just provide dashboard link?
- **NEEDS CLARIFICATION**: Should Phase 1 include Salla webhook verification to detect app uninstall/reinstall?
- **NEEDS CLARIFICATION**: Is the dashboard a server-rendered template or a single-page application (React/Vue/Angular)?
- **NEEDS CLARIFICATION**: What metrics should be captured for the dashboard overview (total members, monthly revenue, etc.) in placeholder widgets?

---

## Not Included in Phase 1

- Payment processing or subscription billing (Phase 2 onwards)
- Merchant setup wizard (Phase 2)
- Salla resource provisioning (Phase 3)
- Public plans page or customer-facing features (Phase 4+)
- Member accounts or subscription lifecycle (Phase 5+)
- Email notifications for trial expiration (Phase 6+)
- Detailed analytics or reporting (future phase)
- Member dashboard (Phase 7)
- Support tickets or help chat (future phase)

---

## Rollout and Risk Mitigation

### Rollout Plan
1. **Dev**: Build with mock Salla OAuth responses
2. **Staging**: Deploy with real Salla test app credentials
3. **Production**: Deploy with production Salla app registration

### Risks and Mitigations
| Risk | Mitigation |
|------|-----------|
| OAuth token expiration during merchant session | Auto-refresh 5min before expiration; log failures; graceful error UI |
| Email delivery fails; merchant unsure if setup worked | Make email async; log failures; display success message on dashboard regardless of email status |
| Merchant installs twice; duplicate records created | Validate Salla store ID uniqueness at DB level; update existing record on re-install |
| Dashboard leaks data between merchants | Comprehensive authorization tests; API endpoint tests verify merchant isolation |
| OAuth scopes insufficient to provision Salla resources | Consult with Salla; include all necessary scopes (customers, orders, products, discounts, etc.) |
| Welcome email lands in spam folder | Use professional email service with proper SPF/DKIM; test deliverability |

---

## Deliverables (Expected)

- OAuth integration module with token refresh logic
- Merchant record creation and database schema
- Trial activation and date calculation logic
- Merchant dashboard backend API (profile, trial, dashboard endpoints)
- Merchant dashboard frontend (responsive HTML/React/Vue)
- Welcome email templates (Arabic and English)
- Merchant authentication system (JWT or session-based)
- Integration tests for OAuth flow, merchant creation, and dashboard access
- Unit tests for trial date calculations and authorization logic
- Database migrations
- Quickstart guide for Phase 1 development and testing
- Documentation on merchant authentication, session handling, and OAuth token refresh


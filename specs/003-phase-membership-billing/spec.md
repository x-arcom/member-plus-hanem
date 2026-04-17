# Phase 2 Specification: Membership Management, Setup Wizard, and Billing

**Feature**: 003-phase-membership-billing
**Status**: Open
**Objective**: Let a merchant move from "installed + trial active" to "launch-ready" by configuring membership plans through a guided wizard, and by choosing a subscription for Member Plus itself.

## Overview

Phase 2 builds on Phase 1 (install + trial + dashboard shell). It covers:

- A **Setup Wizard** that walks a merchant through configuring their membership program in a small number of steps, tracked on `merchants.setup_state`.
- **Membership Plan Management**: CRUD for the plans a merchant will sell to their customers (name, price, duration, benefits).
- **Subscription/Billing foundation**: a data model + API for the merchant's own subscription to Member Plus. Real payment processing is explicitly deferred; Phase 2 lands the model, status machine, and a mock payment adapter.

---

## User Stories & Acceptance Scenarios

### User Story 1 — Merchant Completes Setup Wizard (P1)

A merchant who just installed the app is guided through a short wizard (store profile → first plan → launch confirmation) that flips `setup_state` from `onboarding` → `setup_wizard` → `setup_complete`.

**Acceptance Scenarios**:
1. Given a merchant with `setup_state=onboarding`, when they open the wizard, step 1 is shown and `setup_state` becomes `setup_wizard`.
2. Given a merchant completes all required steps, when they submit the final step, `setup_state` becomes `setup_complete`.
3. Given the merchant returns mid-wizard, when they reopen it, they resume at the last incomplete step.
4. Given a merchant has `setup_state=setup_complete`, the wizard entry point redirects them to the dashboard instead.

### User Story 2 — Merchant Manages Membership Plans (P1)

A merchant can create, update, activate/deactivate, and delete plans they will sell to their customers.

**Acceptance Scenarios**:
1. Given an authenticated merchant, when they create a plan with name, price, duration_days, they receive the persisted plan.
2. Given a merchant lists plans, they only see their own plans (merchant isolation).
3. Given a merchant deactivates a plan, listing with `active_only=true` omits it.
4. Given invalid input (empty name, negative price), the API rejects it with 400.

### User Story 3 — Merchant Subscribes to Member Plus (P1)

After the trial, a merchant selects a subscription tier for Member Plus itself. Payment processing is stubbed via a mock adapter in Phase 2.

**Acceptance Scenarios**:
1. Given a merchant with an active trial, when they call `GET /api/merchant/billing/tiers`, they see the available Member Plus tiers.
2. Given a merchant picks a tier, when they call `POST /api/merchant/billing/subscribe`, a `Subscription` record is created in state `pending` and a mock "payment intent" is returned.
3. Given the mock payment succeeds (via `POST /api/merchant/billing/mock-confirm`), subscription state becomes `active` and `merchant.subscription_id` is set.
4. Given a merchant already has an `active` subscription, `POST /subscribe` is rejected with 409.

### User Story 4 — Dashboard Reflects Setup and Subscription State (P2)

**Acceptance Scenarios**:
1. Dashboard shows the merchant's `setup_state` and a "Continue Setup" CTA when not complete.
2. Dashboard shows the merchant's subscription status (trial / active / expired) and upgrade CTA.

---

## Functional Requirements

- **FR-001**: System MUST persist membership plans per merchant with fields: id, merchant_id, name (bilingual), price, currency, duration_days, benefits (free text / JSON), is_active, created_at, updated_at.
- **FR-002**: System MUST expose CRUD endpoints for plans under `/api/merchant/plans`, all JWT-protected, all scoped to the authenticated merchant.
- **FR-003**: System MUST track wizard progress with a `setup_state` transition: `onboarding → setup_wizard → setup_complete`.
- **FR-004**: System MUST expose `GET /api/merchant/setup/state` and `POST /api/merchant/setup/advance` (with optional payload per step).
- **FR-005**: System MUST define a `Subscription` entity with fields: id, merchant_id, tier, status (`pending`,`active`,`cancelled`,`expired`), started_at, current_period_end, payment_reference (nullable), created_at, updated_at.
- **FR-006**: System MUST expose billing endpoints: `GET /tiers`, `POST /subscribe`, `POST /mock-confirm`, `GET /subscription`.
- **FR-007**: System MUST reject a second active subscription for the same merchant.
- **FR-008**: System MUST enforce merchant isolation on all Phase 2 endpoints (no cross-merchant reads/writes).
- **FR-009**: System MUST keep real payment integration pluggable — a `PaymentAdapter` interface with a `MockPaymentAdapter` for Phase 2.
- **FR-010**: System MUST validate all input (non-empty name, non-negative price, known tier, known step).

### Key Entities

- **MembershipPlan**: merchant-owned plan sold to their customers.
- **Subscription**: merchant's subscription to Member Plus.
- **SetupWizardProgress**: per-merchant progress record; for Phase 2 scope, we use `merchants.setup_state` + a new `setup_step` column (small int) rather than a separate table.

---

## Non-Goals (Phase 2)

- Real Stripe / Paymob / Salla-billing integration (Phase 3).
- Customer-facing membership enrollment (Phase 4+).
- Coupon/discount codes.
- Analytics / reporting.

---

## Dependencies

- Phase 1 merchant + JWT auth.
- Phase 0 config + health.

## Deliverables

- Database model extensions (MembershipPlan, Subscription, merchant.setup_step).
- Services for plans, wizard, billing.
- API routers under `/api/merchant/{plans,setup,billing}`.
- Frontend: wizard.html, plans.html, dashboard integration.
- Tests: unit for services, integration for routes.

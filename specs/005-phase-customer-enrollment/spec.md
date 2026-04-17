# Phase 4 Specification: Customer Enrollment, Member Management, Scheduled Jobs

**Feature**: 005-phase-customer-enrollment
**Status**: Open
**Objective**: Close the loop from "merchant has plans" to "customers are enrolled and appear in a members list". Phase 4 also turns the in-memory scheduler skeleton into a real background process that refreshes tokens and sends trial-expiring reminders.

## Overview

Phases 0–3 built the merchant experience. Phase 4 opens the product to the
merchant's customers:

- **Public enrollment** — a shopper lands on a public page for a specific
  merchant, picks a plan, and submits their contact details. A `Customer` +
  `CustomerSubscription` are created in `pending` status.
- **Member management** — the merchant sees enrolled members in a dashboard
  with state (pending / active / cancelled / expired), and can manually
  confirm payment to activate a subscription. Automated payment capture
  lands in Phase 5.
- **Real dashboard metrics** — `member_count` and `monthly_revenue` stop
  being placeholders and are computed from `CustomerSubscription` rows.
- **Scheduled jobs** — APScheduler runs two jobs:
  - `refresh_expiring_tokens` every 5 min (uses Phase 3 `scheduler.job`).
  - `send_trial_expiring_reminders` once a day; emails merchants whose
    trial is 3 days from expiry.

## User Stories

### US1 — Shopper enrolls in a merchant plan (P1)
A shopper opens `customer.html?store=<salla_store_id>`, picks a plan,
enters name + email + phone, and submits. A `CustomerSubscription` is
created in status `pending` and a success confirmation is shown with
next-steps ("Your merchant will contact you to confirm payment").

### US2 — Merchant sees members and activates them (P1)
The merchant opens `members.html`, sees all customers + their subscription
status. For `pending` rows they can click "Confirm payment" to move the
subscription to `active`; the subscription's `expires_at` is computed from
the plan's `duration_days`.

### US3 — Merchant sees real metrics on dashboard (P2)
Dashboard's "Active members" and "Monthly revenue" reflect actual
`CustomerSubscription` rows (active-in-current-month).

### US4 — Tokens refresh automatically (P1)
On server startup APScheduler schedules `refresh_expiring_tokens` every
5 minutes. In non-scheduler environments (tests, CI) the scheduler is
disabled via `SCHEDULER_ENABLED=false`.

### US5 — Merchants get a trial-expiring email (P2)
Once a day, the trial-reminder job finds merchants whose `trial_end_date`
is within 3 days and `trial_active=true`, and calls
`send_trial_expiring_email`.

## Functional Requirements

- **FR-001** New tables: `customers`, `customer_subscriptions`.
- **FR-002** Public endpoints (no auth):
  - `GET /api/public/merchants/{salla_store_id}/plans` — active plans only, merchants-scoped, returns 404 on inactive/unknown merchant.
  - `POST /api/public/merchants/{salla_store_id}/enroll` — `{plan_id, name, email, phone?}` → creates `Customer` (idempotent by email-per-merchant) + `CustomerSubscription` in `pending`.
- **FR-003** Merchant endpoints (JWT):
  - `GET /api/merchant/members` — returns customers + subscription rollup.
  - `POST /api/merchant/members/{subscription_id}/confirm` — moves `pending` → `active`, stamps `started_at` + `expires_at = started_at + plan.duration_days`.
  - `POST /api/merchant/members/{subscription_id}/cancel` — moves `active`/`pending` → `cancelled`.
- **FR-004** `merchant.service.get_dashboard_overview` returns real `member_count` (active subs) and `monthly_revenue` (sum of plan prices for subs activated in the current month).
- **FR-005** Enrollment validates: required fields, email format, plan belongs to merchant and is active; rejects inactive merchants (is_active=false).
- **FR-006** A shopper can only have one active subscription per merchant at a time (duplicate active → 409).
- **FR-007** Scheduler is disabled when `SCHEDULER_ENABLED=false` or not installed; enabled by default in production containers.

## Non-goals (Phase 4)
- Automated customer payment collection (Phase 5).
- Customer self-service login / cancel flow (Phase 6).
- Real Salla provisioning (customer-group tagging) — the `SallaClient` is
  ready and `salla/provisioning.py` gets stubbed for Phase 5 wiring.
- Multi-language customer emails.

## Deliverables
- `backend/src/customers/{service,routes}.py`
- `backend/src/members/{service,routes}.py`
- `backend/src/scheduler/runner.py` with APScheduler
- `backend/src/database/migrate_phase4.py`
- `frontend/customer.html`, `frontend/members.html`
- Tests (unit + integration)
- Spec + plan + tasks docs

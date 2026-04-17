# Phase 3 Specification: Salla Integration Depth, Token Lifecycle, Real Payments

**Feature**: 004-phase-salla-integration
**Status**: Open
**Objective**: Turn the platform from "wired up with mocks" into "operational" — use
the stored OAuth tokens to talk to Salla, react to Salla webhooks, refresh
tokens before they expire, send lifecycle emails, and plug a real (Moyasar-
compatible) payment adapter alongside the existing mock.

## Overview

Phases 0–2 ship all the primitives (auth, plans, billing data model). Phase 3
makes them *live*:

- A **Salla HTTP client** uses the encrypted OAuth token from Phase 2 hardening
  to talk to Salla, auto-decrypts it per request, and retries once after a
  `refresh_token` exchange on 401.
- A **webhook event dispatcher** parses Salla webhooks and reacts to at least
  `app.installed` / `app.uninstalled` — the latter deactivates the merchant
  and clears their tokens.
- A **scheduled token-refresh job** refreshes every token that is within 5
  minutes of expiry.
- **Trial + setup lifecycle emails** are filled in (today they are `return False`
  stubs).
- A **real payment adapter** (`MoyasarPaymentAdapter`) is added behind the
  existing `PaymentAdapter` Protocol. Selection is env-driven with a mock
  fallback — same pattern as Salla OAuth and SMTP.

## User Stories

### US1 — Merchant is deactivated when they uninstall (P1)
When Salla sends the `app.uninstalled` webhook, the merchant's `is_active`
flips to `false`, `deactivated_at` is set, and their OAuth tokens are
cleared.

### US2 — Tokens refresh automatically (P1)
When a merchant's access token is within 5 minutes of expiry, the scheduled
refresh job exchanges the `refresh_token` for a new pair and updates the DB
(re-encrypting the new values).

### US3 — Lifecycle emails ship (P2)
On trial reaching 3 days remaining → trial-expiring email; on setup
completion → setup-complete email. Both bilingual, both fall back to the
mock logger when SMTP is not configured.

### US4 — Real payments are pluggable (P1)
When `PAYMENT_PROVIDER=moyasar` with an `MOYASAR_API_KEY`, `BillingService`
uses `MoyasarPaymentAdapter`; otherwise it uses `MockPaymentAdapter`. The
billing routes stay the same — the adapter difference is internal.

### US5 — Webhook events are auditable (P2)
Every valid webhook event is logged with `event_type`, `merchant_id` (when
derivable), and `request_id`. Unhandled event types are logged + 200-OK-ed
(Salla expects 2xx).

## Functional Requirements

- **FR-001** Add `merchants.is_active` (bool, default true, indexed) and
  `merchants.deactivated_at` (datetime, nullable).
- **FR-002** `salla.client.SallaClient(merchant_id)` loads + decrypts the
  stored token and exposes `get(path)` / `post(path, json)`.
- **FR-003** On 401 from Salla, `SallaClient` calls `refresh_token_for(merchant_id)`
  once, retries the original request; on second 401 it raises.
- **FR-004** `webhooks.dispatcher.dispatch(event)` routes by `event` name;
  unknown events no-op with a warning log.
- **FR-005** `app.uninstalled` handler: mark merchant inactive, delete OAuth
  token row.
- **FR-006** `scheduler.job.refresh_expiring_tokens(now=...)` iterates
  tokens with `expires_at <= now + 5min` and refreshes them.
- **FR-007** `notifications.email` fills in `send_trial_expiring_email` and
  `send_setup_complete_email` — real SMTP when configured, mock log otherwise.
- **FR-008** `MoyasarPaymentAdapter` implements `PaymentAdapter`:
  - `create_intent` → POST `{base}/v1/invoices` and returns reference + hosted-
    checkout URL.
  - `confirm(reference, success)` → GET `{base}/v1/invoices/{id}` and translates
    gateway status to `succeeded` / `failed`.
- **FR-009** Adapter selection: `billing.adapter.get_payment_adapter()` honors
  `PAYMENT_PROVIDER` env (`mock` default, `moyasar` when key set).
- **FR-010** All endpoints still respond with explicit 4xx errors — no
  hidden 500s on expected business states.

## Non-goals

- Real Salla product/customer-group provisioning (Phase 4+)
- Customer-facing plan enrollment UI (Phase 4+)
- Multi-currency or tax handling (later)
- Paymob / HyperPay / Stripe adapters (the Protocol makes these trivial later)

## Deliverables

- `backend/src/salla/{client,service}.py`, `backend/src/auth/token_refresh.py`
- Webhook event dispatcher wired in `main.py`
- Scheduler refresh job
- Email notification fills
- `backend/src/billing/moyasar_adapter.py`
- Unit + integration tests
- Docs + env vars in `backend/README.md` and `.env.example`

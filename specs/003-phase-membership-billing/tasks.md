# Tasks: Phase 2 — Membership, Setup Wizard, Billing

## Setup
- [x] T001 Create `backend/src/{plans,setup_wizard,billing}/` modules
- [x] T002 Extend `database/models.py` with `MembershipPlan`, `Subscription`, `Merchant.setup_step`/`Merchant.subscription_id`
- [x] T003 Add `migrate_phase2.py` for existing SQLite DBs

## Setup Wizard
- [x] T010 Service: `advance_step(merchant_id, step_data)` with state transitions
- [x] T011 Routes: `GET /setup/state`, `POST /setup/advance`, `POST /setup/reset`
- [x] T012 Tests: integration (`tests/integration/test_setup_wizard_api.py`)

## Plans
- [x] T020 Service: create/list/get/update/delete, merchant-scoped
- [x] T021 Routes: `/api/merchant/plans` CRUD
- [x] T022 Tests: integration (`tests/integration/test_plans_api.py`)

## Billing
- [x] T030 `PaymentAdapter` protocol + `MockPaymentAdapter`
- [x] T031 Service: list tiers, subscribe, confirm, get subscription
- [x] T032 Routes: `/api/merchant/billing/*`
- [x] T033 Tests: integration (`tests/integration/test_billing_api.py`) — includes duplicate-active guard + failed-confirmation path

## Wiring
- [x] T040 Register new routers in `main.py`
- [x] T041 Update root endpoint listing

## Frontend
- [x] T050 `frontend/wizard.html` — multi-step wizard (store info → first plan → launch)
- [x] T051 `frontend/plans.html` — list/create/toggle/delete plans
- [x] T052 `frontend/dashboard.html` — setup progress + subscription status + CTAs

## Docs
- [x] T060 Update `backend/README.md` with Phase 2 endpoints + modules
- [x] T061 Update `frontend/README.md` with new pages

## Validation
- [x] T070 Run full test suite — 38/38 passing

---

## Status: COMPLETE

All Phase 2 tasks implemented and covered by tests. Real payment integration is intentionally deferred to Phase 3 (the `PaymentAdapter` Protocol is the extension point).

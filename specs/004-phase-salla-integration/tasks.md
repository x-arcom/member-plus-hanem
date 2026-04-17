# Tasks: Phase 3 — Salla Integration Depth, Token Lifecycle, Real Payments

## Data model
- [x] T001 Add `merchants.is_active` + `merchants.deactivated_at`
- [x] T002 Provide `migrate_phase3.py` for existing SQLite DBs

## Salla client + token refresh
- [x] T010 `salla/client.py` — encrypted-token-aware HTTP client, 401 → refresh → retry
- [x] T011 `auth/token_refresh.py` — refresh_token exchange against Salla, re-encrypted on write
- [x] T012 `salla/service.py` — `deactivate_merchant`, `find_merchant_by_salla_store`, `reactivate_merchant_if_known`

## Webhooks
- [x] T020 `webhooks/dispatcher.py` — `app.installed`, `app.uninstalled`, unknown-event fallthrough
- [x] T021 Wire dispatcher into `main.py` webhook handler, parse JSON payload, open DB session
- [x] T022 Tolerant of multiple payload shapes (merchant at top-level or under `data.{store_id,id}`)

## Scheduler
- [x] T030 `scheduler/job.py::refresh_expiring_tokens(session_factory, now, horizon_minutes)`
- [x] T031 Per-merchant failures captured without aborting the tick

## Notifications
- [x] T040 Fill `send_trial_expiring_email` (SMTP + mock fallback, bilingual)
- [x] T041 Fill `send_setup_complete_email` (SMTP + mock fallback, bilingual)
- [x] T042 Hook setup-complete email into `WizardService.advance` (fire-and-forget, never blocks DB txn)

## Payments
- [x] T050 `billing/moyasar_adapter.py` implementing `PaymentAdapter`
- [x] T051 `get_payment_adapter()` respects `PAYMENT_PROVIDER` + `MOYASAR_API_KEY`, falls back to mock with a warning if the key is missing
- [x] T052 `reset_payment_adapter()` exposed for tests
- [x] T053 `.env.example` updated with Phase 3 vars

## Tests (24 new, 95 total)
- [x] T060 `tests/unit/test_salla_client.py` — Bearer header, 401-retry once, persistent-401 failure, missing-token row
- [x] T061 `tests/unit/test_token_refresh.py` — happy path re-encrypts, missing token URL, broken gateway response, unknown merchant
- [x] T062 `tests/unit/test_webhook_dispatcher.py` — uninstall deactivation, unknown-store no-op, missing-event, unknown-event 200-OK, `data.store_id` envelope
- [x] T063 `tests/integration/test_webhook_uninstall.py` — end-to-end signed webhook deactivates merchant + wipes OAuthToken
- [x] T064 `tests/unit/test_scheduler_refresh.py` — horizon filtering, per-merchant failure reporting
- [x] T065 `tests/unit/test_moyasar_adapter.py` — payload shape, paid/failed/explicit-cancel translation, env-driven selection, missing-key fallback

## Docs
- [x] T070 `backend/README.md` Phase 3 section (salla client, dispatcher, scheduler, emails, Moyasar adapter, env table, migration)
- [x] T071 `.env.example` Phase 3 vars (`PAYMENT_PROVIDER`, `MOYASAR_*`)

---

## Status: COMPLETE

All Phase 3 tasks implemented and covered by tests (95 passing). `app.uninstalled`
now translates into real state changes; tokens refresh in-place with re-encryption;
the first real payment adapter is behind an env-driven switch with a safe
fallback.

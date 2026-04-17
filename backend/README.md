# Member Plus Backend (Phases 0 / 1 / 2 / 3 / 4 + R + 6 + G)

FastAPI service powering the Member Plus merchant onboarding + membership
plans + billing experience.

## Features by phase

- **Phase 0** — config, fail-fast validation, health, signed webhooks, scheduler skeleton, bilingual content
- **Phase 1 MVP** — mock OAuth, JWT auth, merchant + dashboard API, mock email
- **Phase 1 Full** — real Salla OAuth with mock fallback, real SMTP with mock fallback
- **Phase 2** — membership plan CRUD, setup-wizard state machine, merchant subscription model + `PaymentAdapter` protocol (mock impl)
- **Hardening** — required `JWT_SECRET` + `ENCRYPTION_KEY`, Fernet-encrypted OAuth tokens at rest, env-driven CORS allowlist, JSON structured logging with per-request IDs, Docker + docker-compose
- **Phase 3** — Salla HTTP client with 401-refresh, `app.uninstalled` webhook → merchant deactivation, scheduled token refresh, lifecycle emails, Moyasar real payment adapter
- **Phase 4** — public customer enrollment, merchant member management (list / confirm / cancel), real `member_count` + `monthly_revenue`, APScheduler background process running token refresh + daily trial reminders
- **Phase R (realignment to `plane.md`)** — the generic plan shape grew a `tier` + structured benefits (`discount_percent`, `free_shipping_quota`, `monthly_gift_enabled`, `early_access_enabled`, `badge_enabled`, `salla_customer_group_id`). The setup wizard became a Silver/Gold program configuration flow (`POST /api/merchant/setup/program`). A new `salla.provisioning` module creates Salla customer groups via `SallaClient` when a program is launched. A customer-side `GET /api/public/merchants/{store}/membership?email=` lookup powers the new `member.html` page. An `expire_overdue_subscriptions` scheduler job (daily 02:00) retires active subscriptions past their `expires_at`.
- **Phase 6 (benefits engine)** — new `BenefitDelivery` table + `benefits` service issue real entitlements when a member's payment is confirmed: free-shipping coupon (uses=`free_shipping_quota`), monthly-gift coupon (idempotent per YYYY-MM), plus flag rows for `auto_discount` / `early_access` / `badge`. Coupons are created via Salla's `/admin/v2/coupons` through `SallaClient`; any failure falls back to a local `MP-*` code with `status='delivered-mock'` so the experience never silently no-ops. New endpoint `GET /api/merchant/members/{id}/benefits` and `benefits[]` on the public membership lookup. Scheduler adds a monthly-gift tick (day=1, 03:00 UTC).
- **Phase G (gap closure)** — drives every remaining 🟡 in the `plane.md` coverage matrix to ✅: subscription state machine gains a `grace` step (active → grace → expired) with `grace_ends_at` and a daily sweep that respects both windows; a `POST /api/merchant/members/{id}/renew` extends (or re-starts) a subscription; cancelling a subscription now triggers benefit clawback (active coupons → `status='revoked'`, uses zeroed); a `POST /api/public/benefits/redeem` endpoint decrements coupon uses and 410s when depleted; the public plans endpoint returns `store_state` so `coming_soon` merchants get a dedicated interest-capture variant; `POST /api/public/merchants/{store}/interest` backs it with an `InterestSignup` table; Salla provisioning now also creates a **special offer** for each plan's customer group (`salla_special_offer_id` on `MembershipPlan`); and the public membership lookup gains a `savings_estimate` number for the member dashboard.

## Enabling real Salla OAuth + SMTP

Set the following in `.env` (see `.env.example`):

```
SALLA_CLIENT_ID=...
SALLA_CLIENT_SECRET=...
SALLA_OAUTH_AUTHORIZE_URL=https://accounts.salla.sa/oauth2/auth
SALLA_OAUTH_TOKEN_URL=https://accounts.salla.sa/oauth2/token
SALLA_OAUTH_REDIRECT_URI=http://localhost:8000/api/oauth/callback
SALLA_STORE_INFO_URL=https://api.salla.dev/admin/v2/store/info

EMAIL_HOST=smtp.yourprovider.com
EMAIL_PORT=587
EMAIL_USER=...
EMAIL_PASSWORD=...
EMAIL_FROM="Member Plus <no-reply@memberplus.com>"
EMAIL_USE_TLS=true
```

When any of the `SALLA_CLIENT_*` / `SALLA_OAUTH_*` variables are missing, the
OAuth routes fall back to mock responses so local development still works.
When `EMAIL_HOST` / `EMAIL_PORT` are missing, welcome emails are logged to
stdout instead of being sent.

## Quick Start

See `../specs/001-phase-foundation-and/quickstart.md` for setup instructions.

## How to use

1. Install dependencies: `pip install -r requirements.txt`
2. Configure environment variables in a `.env` file (see `src/config/README.md` and `../.env.example`)
3. Start the server: `python src/app-entrypoint/main.py`
4. Test the health endpoint: `curl http://localhost:8000/health`
5. Review the Phase 0 spec and plan in `../specs/001-phase-foundation-and/`

## Architecture

Phase 0 modules:
- `src/app-entrypoint/main.py` — FastAPI application entrypoint
- `src/config/` — environment loading and validation
- `src/health/` — health check and readiness endpoint
- `src/webhooks/` — webhook receiver and signature verification
- `src/scheduler/` — scheduled job skeleton
- `src/i18n/` — bilingual content handling rules

Phase 1 modules:
- `src/oauth/` — Salla OAuth (real + mock fallback)
- `src/auth/` — JWT tokens
- `src/merchant/` — Merchant service (create, trial, dashboard overview)
- `src/dashboard/` — merchant-facing read API
- `src/email_service/` — welcome email (SMTP + mock fallback)
- `src/database/` — SQLAlchemy models (Merchant, OAuthToken, Session)

Phase 2 modules:
- `src/plans/` — CRUD for merchant membership plans
- `src/setup_wizard/` — `setup_state` transitions (`onboarding → setup_wizard → setup_complete`)
- `src/billing/` — subscription service + `PaymentAdapter` (mock now, real later)
- `src/database/models.py` — extended with `MembershipPlan`, `Subscription`, `merchant.setup_step`, `merchant.subscription_id`
- `src/database/migrate_phase2.py` — run once against an existing SQLite DB to add the new columns/tables

`tests/` contains unit + integration suites (26 baseline + 12 Phase 2 = 38 tests).

## Phase 2 endpoints

```
GET    /api/merchant/setup/state
POST   /api/merchant/setup/advance
POST   /api/merchant/setup/reset

GET    /api/merchant/plans?active_only=
POST   /api/merchant/plans
GET    /api/merchant/plans/{id}
PATCH  /api/merchant/plans/{id}
DELETE /api/merchant/plans/{id}

GET    /api/merchant/billing/tiers
GET    /api/merchant/billing/subscription
POST   /api/merchant/billing/subscribe       { tier }
POST   /api/merchant/billing/mock-confirm    { subscription_id, success }
```

To apply Phase 2 schema changes to an existing DB:

```bash
cd backend/src && python -m database.migrate_phase2
```

## Security & required config

Validated fail-fast at startup by `config.validate_config`. Missing any of these
refuses to boot:

| Variable            | Purpose                                                        |
|---------------------|----------------------------------------------------------------|
| `SALLA_API_KEY`     | Salla API authentication                                        |
| `SALLA_WEBHOOK_SECRET` | HMAC key used by `/webhooks/salla`                           |
| `DATABASE_URL`      | SQLAlchemy URL (SQLite locally, PostgreSQL in prod)             |
| `JWT_SECRET`        | Signs merchant JWTs. ≥32 chars in production; dev sentinel rejected in `ENVIRONMENT=production` |
| `ENCRYPTION_KEY`    | Fernet key (URL-safe base64, 32 bytes). Encrypts `OAuthToken.access_token` / `.refresh_token` at rest |
| `CORS_ORIGINS`      | Comma-separated allowlist. Defaults to `http://localhost:3000`  |

Generate both secrets:

```bash
cd backend/src && python -m config.gen_keys
```

### Token encryption at rest

`src/auth/crypto.py` wraps `cryptography.fernet.Fernet`. OAuth access/refresh
tokens are encrypted on write (`oauth/provider.py`) and decrypted on read via
`auth.crypto.decrypt()`. Existing plaintext rows are tolerated — any value
that isn't a valid Fernet token is returned unchanged, so the feature can be
rolled out without a forced data migration. Rotate `ENCRYPTION_KEY` by
re-encrypting rows on next write (Phase 3 will add a `rotate_keys` job).

### CORS

```bash
CORS_ORIGINS=https://app.example.com,https://admin.example.com
```

The list is evaluated once at process start; restart the service after
editing. Localhost defaults are applied only when the env var is absent.

## Observability

`src/observability/logging.py` installs a JSON formatter and attaches a
`request_id` to every request (taken from `X-Request-ID` header if present,
otherwise generated). Each request logs one structured line:

```json
{"ts":"2026-04-17T09:12:33+0000","level":"INFO","logger":"http",
 "message":"request","method":"POST","path":"/api/merchant/plans",
 "status":201,"latency_ms":38.7,"request_id":"a3f…"}
```

In `ENVIRONMENT=development` the formatter falls back to a human-readable
format so local stack traces stay scannable. Level is controlled by
`LOG_LEVEL` (default `INFO`).

## Running with Docker

```bash
# From repository root:
docker compose up --build
# Backend: http://localhost:8000   Frontend: http://localhost:3000
```

`docker-compose.yml` wires the backend + a static-file server for the
frontend. The backend mounts a named volume at `/data` for the default SQLite
file (`sqlite:////data/memberplus.db`). Swap `DATABASE_URL` to a PostgreSQL
URL for production.

The image runs as a non-root user (`uid 10001`) and includes a HEALTHCHECK
against `/health`.

## Phase 3 additions

### Salla client + token refresh
- `src/salla/client.py` — `SallaClient(session, merchant_id)`: decrypts the
  stored OAuth token per call, attaches `Authorization: Bearer …`, retries
  once after a `refresh_token` exchange when Salla returns 401.
- `src/auth/token_refresh.py` — `refresh_token_for_merchant(session, id)`
  swaps the stored refresh token for a new access/refresh pair and
  re-encrypts both before committing.

### Webhook dispatcher
- `src/webhooks/dispatcher.py` — routes verified payloads by `event` name:
  - `app.uninstalled` → flips merchant `is_active=false`, sets
    `deactivated_at`, deletes the OAuth token row.
  - `app.installed` → logged (OAuth callback already handles the state).
  - Unknown events → acknowledged with 200 so Salla doesn't retry forever.

### Scheduler: token refresh job
- `src/scheduler/job.py::refresh_expiring_tokens` — scan tokens within 5
  minutes of expiry and refresh each via `token_refresh`. Per-merchant
  failures are reported but do not abort the job. Wire to your preferred
  scheduler (cron / APScheduler / k8s CronJob) — the function is
  side-effect-driven and accepts an injected `now` for deterministic
  tests.

### Lifecycle emails
- `send_trial_expiring_email(email, days, lang)` — bilingual template, SMTP
  when configured, mock logger otherwise.
- `send_setup_complete_email(email, lang)` — fired by `WizardService` the
  moment `setup_state` flips to `setup_complete`.

### Payments (real adapter)
- `src/billing/moyasar_adapter.py::MoyasarPaymentAdapter` — Moyasar
  `invoices`-based flow (hosted checkout), injectable transport, base64
  basic-auth.
- Selection in `billing.adapter.get_payment_adapter()`:

  | `PAYMENT_PROVIDER` | `MOYASAR_API_KEY` | Adapter used |
  |--------------------|-------------------|--------------|
  | unset / `mock`     | —                 | `MockPaymentAdapter` |
  | `moyasar`          | set               | `MoyasarPaymentAdapter` |
  | `moyasar`          | empty             | `MockPaymentAdapter` (with warning log) |

  `reset_payment_adapter()` is exposed for tests.

### Phase 3 migration

```bash
cd backend/src && python -m database.migrate_phase3
```

Adds `merchants.is_active` + `merchants.deactivated_at` to existing DBs.

## Testing

```bash
cd backend && python3 -m pytest tests/ -q
```

**170 tests** cover: config loader + validation, webhook signature + full
dispatcher flow (including the `app.uninstalled` deactivation path), crypto
round-trip + legacy tolerance, JWT sign/verify + rotation, OAuth token
encryption at rest, plan / wizard / billing services (in-memory sqlite),
token-refresh success + failure paths, SallaClient 401-retry behaviour, the
scheduler refresh job horizon logic, Moyasar adapter payload + env-driven
selection, the public customer enrollment flow (valid / invalid email /
inactive merchant / idempotent re-enroll), merchant member management
(list / confirm / cancel / isolation), the real `member_count` +
`monthly_revenue` dashboard metrics, and the trial-reminder picker +
sender.

## Phase 4 additions

### Public customer enrollment
- `GET /api/public/merchants/{salla_store_id}/plans` — returns the active plans of a given merchant. No auth.
- `POST /api/public/merchants/{salla_store_id}/enroll` — `{plan_id, name, email, phone?}`. Creates `Customer` (upsert by `(merchant, email)`) + `CustomerSubscription` in `pending`. Idempotent for the same (customer, plan) combo.

### Member management (merchant)
- `GET /api/merchant/members?status=...` — JWT-protected, merchant-scoped list of customer subscriptions.
- `POST /api/merchant/members/{id}/confirm` — flips `pending → active`, stamps `started_at` + `expires_at = now + plan.duration_days`.
- `POST /api/merchant/members/{id}/cancel` — flips any non-terminal status to `cancelled`.

### Real dashboard metrics
`merchant.service.get_dashboard_overview` now computes:
- `member_count` — active `CustomerSubscription` rows for the merchant.
- `monthly_revenue` — sum of `price_at_enrollment` for subs activated since the first of the current month.

### Scheduler
`src/scheduler/runner.py` wraps APScheduler:
- `refresh_expiring_tokens` — every 5 minutes (from Phase 3).
- `trial_reminders` — daily at 09:00 (UTC by default); finds merchants whose trial ends within `TRIAL_REMINDER_DAYS` (default 3) and calls `send_trial_expiring_email`.

Controlled by env:

| Variable                | Default | Purpose |
|-------------------------|---------|---------|
| `SCHEDULER_ENABLED`     | `true`  | Set to `false` in tests / CI |
| `SCHEDULER_TIMEZONE`    | `UTC`   | APScheduler timezone |
| `TRIAL_REMINDER_DAYS`   | `3`     | Reminder window |

APScheduler is a new dependency (`apscheduler==3.10.4`). When it's not installed the scheduler no-ops cleanly.

### Phase 4 migration

```bash
cd backend/src && python -m database.migrate_phase4
```

Creates the new `customers` + `customer_subscriptions` tables.

### Phase R migration

```bash
cd backend/src && python -m database.migrate_phase_r
```

Adds the tier + benefits columns to `membership_plans` (idempotent).

### Phase R endpoints

```
POST /api/merchant/setup/program
      { silver: {...}, gold: {...} }
      upserts both plans, flips setup_state to setup_complete, and fires
      Salla customer-group provisioning in the background.

GET  /api/public/merchants/{salla_store_id}/membership?email=...
      Customer-side read-only summary of their subscriptions + benefits.
```

Plans now return + accept: `tier`, `discount_percent`, `free_shipping_quota`,
`monthly_gift_enabled`, `early_access_enabled`, `badge_enabled`,
`salla_customer_group_id`.

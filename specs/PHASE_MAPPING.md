# Phase Mapping — Old Work → New 16-Phase Plan

**Purpose**: Map existing code to the new phase plan. Carry forward what's solid, mark what needs rework, identify what's missing.

---

## Phase 0 — Validation, access, launch blockers

| Item | Status | Location | Notes |
|------|--------|----------|-------|
| OAuth refresh utility | ✅ Done | `auth/token_refresh.py` | Works with injected transport for tests |
| Salla retry utility | ✅ Done | `salla/retry.py` | PRD §17.6 rules (5xx backoff, 429 wait, 401 refresh) |
| Webhook signature verification | ✅ Done | `webhooks/signature.py` | HMAC-SHA256 |
| Config validation (fail-fast) | ✅ Done | `config/loader.py` | JWT_SECRET + ENCRYPTION_KEY required |
| Token encryption at rest | ✅ Done | `auth/crypto.py` | Fernet with legacy plaintext tolerance |
| Dev/staging/prod setup | ✅ Done | `.env.example`, `Dockerfile`, `docker-compose.yml` | 3-env structure |
| Salla scope request | ❌ TODO | — | Manual: contact Salla Support for `subscriptions.read_write` |
| Test customer groups at scale | ❌ TODO | — | Manual: test 1000+ members on demo store (PRD D-01) |
| Test recurring payments | ❌ TODO | — | Manual: test on staging (PRD D-05) |
| Test cancel subscription | ❌ TODO | — | Manual: test exact behavior (PRD D-06) |
| Legal (ToS, Privacy Policy) | ❌ TODO | — | Business task (PRD H-02 through H-05) |
| Pricing/commission confirmation | ❌ TODO | — | Business task (PRD H-01) |
| Scheduler monitoring | 🟡 Partial | `scheduler/runner.py` | APScheduler wired, but no health alerts |

**Phase 0 verdict**: Code foundations are solid. Remaining items are manual Salla tests + legal — these run in parallel with development.

---

## Phase 1 — Core platform foundation

| Item | Status | Location | Notes |
|------|--------|----------|-------|
| DB schema (14 tables) | ✅ Done | `database/models.py` | PRD §14 exact match |
| Install flow (app.store.authorize) | ✅ Done | `webhooks/pipeline.py` | Creates merchant + 7-day trial |
| Merchant record + trial | ✅ Done | Model + webhook handler | status enum, trial_ends_at |
| Dashboard access flow | ✅ Done | `auth/session.py`, `auth/access.py` | Permanent token → cookie |
| Merchant session handling | ✅ Done | `auth/session.py` | HttpOnly, 8h timeout, JWT fallback |
| Webhook storage (idempotency) | ✅ Done | `webhooks/pipeline.py` | webhook_events table, ON CONFLICT |
| Scheduled jobs table | ✅ Done | `scheduler/jobs.py` | DB-tracked, 5 job types |
| Activity log | ✅ Done | Model + benefit engine logs | ActivityLog table |
| API structure (/api/v1/) | ✅ Done | `main.py` | Versioned from day one |
| Security rules | ✅ Done | HMAC, Fernet, session cookies | Per PRD §20 |
| Status models | ✅ Done | Merchant/Member/Plan enums | Per PRD §15 |

**Phase 1 verdict**: ✅ Complete. All items implemented and tested (61 tests).

---

## Phase 2 — Merchant access and onboarding

| Item | Status | Location | Notes |
|------|--------|----------|-------|
| Welcome email | 🟡 Stub | `email_service/service.py` | Template exists, not PRD-exact copy |
| Dashboard link in email | ❌ TODO | — | Needs permanent_access_token in link |
| Onboarding entry screen | 🟡 Exists | `wizard.html` | Needs PRD §43.4 Welcome screen |
| Required setup enforcement | ✅ Done | `setup_state` endpoint | `setup_completed` blocks plans page |
| Pricing setup | 🟡 Partial | Setup complete endpoint | Needs separate step UI |
| Billing cycle setup | ❌ TODO | — | Per-plan monthly/annual (PRD §43.6) |
| Benefits selection | 🟡 Partial | Wizard creates Silver/Gold | Needs all 6 benefits shown |
| Save and continue | ❌ TODO | — | Wizard is all-or-nothing currently |
| Dashboard after setup | ✅ Done | Dashboard redirects | Focus card shows setup CTA |

**Phase 2 verdict**: 🟡 Foundation exists, needs UI refinement for PRD compliance.

---

## Phase 3 — Membership Settings page

| Item | Status | Location | Notes |
|------|--------|----------|-------|
| Settings page | 🟡 Exists | `settings.html` | Has billing, needs membership config section |
| Pricing fields | ✅ Done | Plan model has price | Editable via API |
| Billing cycle fields | ❌ TODO | — | Per-plan monthly/annual not built |
| Benefits section | ❌ TODO | — | Needs toggle cards per benefit |

**Phase 3 verdict**: 🟡 Settings page exists but needs membership-specific sections.

---

## Phase 4–8 — Benefits, Shipping, Coupons, Offers

| Item | Status | Location | Notes |
|------|--------|----------|-------|
| Benefits engine (6 types) | ✅ Done | `benefits/engine.py` | activate/deactivate/reset |
| Benefit classification | ✅ Done | Engine knows auto vs quota | Silver/Gold rules enforced |
| Shipping inline config | ❌ TODO | — | Needs Salla shipping methods API |
| Coupons page | ❌ TODO | — | gift_coupons table ready, needs full CRUD UI |
| Special Offers page | ❌ TODO | — | salla_offer_id on plan, needs full CRUD UI |

**Phase 4-8 verdict**: Backend logic exists. Frontend pages need building per the toggle/card pattern.

---

## Phase 9 — Members page

| Item | Status | Location | Notes |
|------|--------|----------|-------|
| Members API | ✅ Done | `/api/v1/merchant/members` | Filter by tier/status, pagination |
| Member profile | ✅ Done | `/api/v1/merchant/members/{id}` | Full history |
| Members UI | 🟡 Exists | `members.html` | Needs membership-only filter emphasis |

---

## Phase 10 — Billing & Subscription

| Item | Status | Location | Notes |
|------|--------|----------|-------|
| Our SaaS tiers | ✅ Done | `our_plan` enum on Merchant | starter/pro/unlimited |
| Billing UI | 🟡 Exists | `settings.html` | Needs invoice/payment history |
| Salla App Store billing | ❌ TODO | — | Must use Salla billing, not Moyasar |

---

## Phase 11 — Activity Log

| Item | Status | Location | Notes |
|------|--------|----------|-------|
| Activity log API | ✅ Done | `/api/v1/merchant/activity` | Filterable, paginated |
| Activity log UI | ❌ TODO | — | No dedicated page yet |

---

## Phase 12 — Customer-facing experience

| Item | Status | Location | Notes |
|------|--------|----------|-------|
| Plans page | ✅ Done | `customer.html` | ROI calc, tier cards, 3 states |
| Member dashboard | ✅ Done | `member.html` | Badge, shipping, gift, savings, grace |
| Member state API | ✅ Done | `/api/v1/member/state` | For App Snippet |

---

## Phase 13 — Notifications

| Item | Status | Location | Notes |
|------|--------|----------|-------|
| Email templates | 🟡 Stubs | `email_service/service.py` | 3 of 26 email types |
| Email log table | ✅ Done | `email_log` model | Ready for tracking |

---

## Phase 14 — Admin panel

| Item | Status | Location | Notes |
|------|--------|----------|-------|
| Admin users table | ✅ Done | Model exists | admin_users + admin_notes |
| Admin UI | ❌ TODO | — | 0 of 18 screens built |

---

## Phase 15 — QA & hardening

| Item | Status | Location | Notes |
|------|--------|----------|-------|
| Race condition protections | 🟡 Partial | Webhook idempotency done | Others need DB locks |
| E2E testing | ❌ TODO | — | Never browser-tested |
| 61 unit/integration tests | ✅ Done | `tests/` | All passing |

---

## Summary

| Phase | Status | Ready to ship? |
|-------|--------|----------------|
| 0 — Validation | ✅ Code done, manual tests pending | Yes (code) |
| 1 — Foundation | ✅ Complete | Yes |
| 2 — Onboarding | 🟡 Needs UI work | No |
| 3 — Settings | 🟡 Needs restructure | No |
| 4 — Benefits framework | 🟡 Backend done, UI missing | No |
| 5 — Benefit model | ✅ Classification done | Yes |
| 6 — Shipping | ❌ Not built | No |
| 7 — Coupons | ❌ UI not built | No |
| 8 — Special Offers | ❌ UI not built | No |
| 9 — Members | 🟡 Needs polish | No |
| 10 — Billing | 🟡 Wrong payment provider | No |
| 11 — Activity Log | 🟡 API done, UI missing | No |
| 12 — Customer experience | ✅ Pages built | Yes (needs browser test) |
| 13 — Notifications | 🟡 Stubs only | No |
| 14 — Admin | ❌ Not built | No |
| 15 — QA | ❌ Not started | No |
    
# Tasks: Phase 4 — Customer Enrollment, Member Management, Scheduled Jobs

## Data model
- [x] T001 Add `Customer` and `CustomerSubscription` models
- [x] T002 `database/migrate_phase4.py` for existing DBs

## Customer (public)
- [x] T010 `customers/service.py` — enroll, resolve-merchant, validation
- [x] T011 `customers/routes.py` — `GET /api/public/merchants/{store}/plans`, `POST .../enroll`
- [x] T012 Integration tests: public plans + enrollment (valid + invalid email + idempotent + inactive merchant)

## Members (merchant)
- [x] T020 `members/service.py` — list, confirm, cancel
- [x] T021 `members/routes.py` — `GET /members`, `POST /members/{id}/confirm`, `POST /members/{id}/cancel`
- [x] T022 Integration tests: list + status filter + confirm flow + cancel + isolation (cross-merchant 404)

## Dashboard metrics
- [x] T030 `merchant.service.get_dashboard_overview` computes real member_count + monthly_revenue from `CustomerSubscription`
- [x] T031 Integration test asserting metrics move when a member is confirmed

## Scheduler
- [x] T040 `scheduler/runner.py` using APScheduler, safe no-op if library missing or `SCHEDULER_ENABLED=false`
- [x] T041 Wire `refresh_expiring_tokens` (5 min) + `trial_reminders` (daily 09:00) into app lifespan
- [x] T042 Pure-function `notifications/trial_reminder.py` + unit tests (which merchants get picked, language/days routing)
- [x] T043 Added `apscheduler==3.10.4` to `requirements.txt`; `SCHEDULER_ENABLED`, `SCHEDULER_TIMEZONE`, `TRIAL_REMINDER_DAYS` in `.env.example`

## Frontend
- [x] T050 `customer.html` — public enrollment with all five states (loading / empty / error / data / success)
- [x] T051 `members.html` — filterable member list (loading / empty / error / data) + share-link card + confirm/cancel with toasts
- [x] T052 Dashboard: added Members link to nav, metrics card now links to members page and shows real values in localized currency

## Docs
- [x] T060 `backend/README.md` Phase 4 section (endpoints, scheduler env vars, migration)
- [x] T061 `frontend/README.md` new pages + updated states matrix
- [x] T062 `.env.example` Phase 4 vars

---

## Status: COMPLETE

115 tests passing. The end-to-end loop is now real: a merchant installs →
creates plans → shares their enrollment link → customers sign up → merchant
confirms payment → dashboard metrics and member list reflect reality. Token
refresh + trial-expiring reminders run in the background.

# Tasks: Phase R — Realignment to plane.md

## Data model
- [x] T001 Extend `MembershipPlan` with tier + benefit columns + `salla_customer_group_id`
- [x] T002 `database/migrate_phase_r.py` adds the columns idempotently

## Services
- [x] T010 `plans/service.py` accepts + returns the new fields, validates 0 ≤ discount_percent ≤ 100, free_shipping_quota ≥ 0
- [x] T011 `setup_wizard/service.py::configure_program(merchant_id, silver, gold)` — upserts the two plans, flips setup_state, triggers background provisioning
- [x] T012 `salla/provisioning.py` — create customer group for a plan + merchant-wide sweep, idempotent
- [x] T013 Provisioning hook fires in a daemon thread so the wizard commit never blocks on Salla
- [x] T014 `scheduler/job.py::expire_overdue_subscriptions` + daily 02:00 cron in the runner
- [x] T015 `customers/service.py::lookup_membership(store_id, email)` — customer-side read-only summary

## Routes
- [x] T020 `POST /api/merchant/setup/program`
- [x] T021 `GET /api/public/merchants/{store}/membership?email=`

## Frontend
- [x] T030 `wizard.html` — 3-step tier config (Silver → Gold → Review) with full benefit fields
- [x] T031 `plans.html` — tier pill + benefit chips in the list
- [x] T032 `customer.html` — tier badge per plan + benefit chips + bilingual labels
- [x] T033 `member.html` — public email-keyed membership summary, 5 states (form / loading / empty / error / data)
- [x] T034 `members.html` — added "member lookup" shareable link alongside the enrollment link

## Tests (26 new, 141 total)
- [x] T040 Unit: plan service benefit validation (boundaries + bad types) — `tests/unit/test_plan_benefits.py`
- [x] T041 Unit: `configure_program` creates both tiers, upserts on re-run, rejects invalid benefits — `tests/unit/test_configure_program.py`
- [x] T042 Unit: `provision_plan` — persists group id, idempotent, handles 5xx + missing-id, `provision_merchant_program` sweeps all — `tests/unit/test_provisioning.py`
- [x] T043 Unit: `expire_overdue_subscriptions` flips only active+past rows, idempotent — `tests/unit/test_expire_job.py`
- [x] T044 Integration: `POST /api/merchant/setup/program` E2E with plan visibility + rejection paths — `tests/integration/test_program_route.py`
- [x] T045 Integration: `GET .../membership` — valid / unknown email / invalid email / unknown store — `tests/integration/test_member_lookup.py`

## Docs
- [x] T050 `backend/README.md` Phase-R section (endpoints + migration)
- [x] T051 `frontend/README.md` — `member.html` + updated states matrix
- [x] T052 Phase-R tasks marked complete

---

## Status: COMPLETE

141 tests passing. The generic plan model has been realigned to `plane.md`
— Silver + Gold tiers with explicit discount / free shipping / monthly
gift / early access / badge fields, wired end-to-end from the wizard
through to Salla customer-group provisioning and a customer-side
`member.html` self-view.

Deferred (next phase, tracked separately):
- Benefits *execution* — automatic discount application, free-shipping
  coupon generation, monthly-gift issuance (Phase 6 in `plane.md`).
- ROI calculator + coming-soon / already-member state variants on the
  public plans page.
- Real customer login/auth (currently email-as-key for read-only view).
- Special-offer + recurring-subscription-product provisioning in Salla.

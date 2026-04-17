# Phase R Specification: Realign to plane.md Product Model

**Feature**: 006-phase-realignment
**Status**: Open
**Objective**: Reshape the generic `MembershipPlan` into the actual Member Plus
product described in `plane.md` (Silver/Gold tiers with specific benefits),
rework the setup wizard into a program-configuration flow, build the real
Phase 3 (Salla customer-group provisioning), and add the subscription
expire job — so subsequent phases (benefits engine, member dashboard) have
the right foundations.

## Why this exists

Earlier sessions shipped a generic "plans have name/price/duration" model
and a generic 3-step "advance setup_state" wizard. Both work, both are
tested — but they don't match `plane.md`:

- `plane.md` Phase 2 specifies **Silver and Gold tiers** with discount %,
  free-shipping quota, monthly-gift, early-access, badge.
- `plane.md` Phase 3 specifies **Salla resource provisioning** (customer
  groups, special offers, recurring subs). Our previous "Phase 3" was
  hardening + Moyasar + webhook dispatch — valuable, but a different axis.

This phase brings the code back in line with `plane.md` before layering
the benefits engine and customer member dashboard on top.

## Scope

### Data model
- Extend `MembershipPlan` with:
  - `tier` (`'silver' | 'gold' | null` — null remains for legacy/generic plans).
  - `discount_percent` (0–100, nullable).
  - `free_shipping_quota` (int per month, nullable).
  - `monthly_gift_enabled` (bool).
  - `early_access_enabled` (bool).
  - `badge_enabled` (bool).
  - `salla_customer_group_id` (string, nullable) — populated by provisioning.
- `migrate_phase_r.py` adds the columns to existing DBs.

### Setup wizard
- `WizardService.configure_program(merchant_id, silver, gold)` — upserts two
  `MembershipPlan` rows (tier=`silver`, tier=`gold`) with full benefit
  fields, then flips `setup_state → setup_complete`.
- Legacy `advance()` stays for backward compatibility (old tests + API
  consumers). New front-end uses `configure_program`.

### Salla provisioning
- `salla/provisioning.py::provision_plan(session, plan_id)` — if the plan
  doesn't have a `salla_customer_group_id` yet, create one via
  `SallaClient` → `POST /admin/v2/customers/groups` and persist the
  returned id.
- `provision_merchant_program(session, merchant_id)` — run provisioning
  for every plan of the merchant; fire-and-forget from the wizard.

### Scheduler
- `expire_overdue_subscriptions()` — any `CustomerSubscription` whose
  `expires_at <= now` and `status='active'` moves to `expired`. Registered
  daily at 02:00.

### Frontend
- `wizard.html` becomes a 3-step tier-configuration flow (Silver → Gold →
  Review) with all the benefit fields.
- `plans.html` surfaces tier + benefits in the create form and in the
  table.
- `customer.html` shows benefit highlights per plan (discount %, free
  shipping, etc.).
- New `member.html` — a minimal customer-side page `?email=` that lets a
  shopper see their current membership status + benefits.

## Non-goals (this phase)

- Special-offer and recurring-subscription product creation (Salla admin
  API scope — deferred to a dedicated follow-up).
- Automated discount-code / coupon generation on benefit delivery.
- ROI calculator on the hosted plans page.
- Real customer login/auth for `member.html` (we'll use email-as-key for
  read-only view; real auth is Phase 7).

## Deliverables

- Spec + tasks docs
- Model + migration
- Wizard `configure_program` + provisioning module + scheduler expire job
- Reworked `wizard.html`, updated `plans.html` + `customer.html`, new
  `member.html`
- Unit + integration tests
- Updated READMEs

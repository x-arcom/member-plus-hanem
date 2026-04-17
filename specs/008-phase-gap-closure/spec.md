# Phase G Specification: Close Remaining plane.md Gaps

**Feature**: 008-phase-gap-closure
**Status**: Open
**Objective**: Drive the remaining 🟡 rows in the `plane.md` coverage matrix to
✅. No new product direction — tightening what's partial.

## Gaps to close

| plane.md | Gap |
|---|---|
| Phase 3 — Salla Resource Provisioning | special-offer creation alongside customer groups |
| Phase 4 — Public Plans + Interest Flow | coming-soon state, already-member state, interest-registration flow, ROI calculator |
| Phase 5 — Subscription Lifecycle Core | grace period state, renewal action |
| Phase 6 — Benefits Engine | clawback on cancellation, redemption/use tracking |
| Phase 7 — Member Dashboard | savings display, renewal CTA, current-period visibility |

## Scope

### Data
- New `InterestSignup` table: `(id, merchant_id | null, salla_store_id, email, signed_up_at, notified_at)`.
- `CustomerSubscription` gets `grace_ends_at` (nullable datetime).
- `MembershipPlan` gets `salla_special_offer_id` (nullable string).
- `BenefitDelivery.status` gains the value `'revoked'` (no schema change).
- All extensions delivered via `migrate_phase_g.py`.

### Subscription lifecycle (Phase 5 gap)
- `CustomerSubscription.status` now has this progression:
  `pending → active → grace → expired` (plus `cancelled` terminal from any non-expired state).
- `scheduler.job.expire_overdue_subscriptions(now)` now:
  1. `active` past `expires_at` → `grace`, sets `grace_ends_at = expires_at + GRACE_DAYS`.
  2. `grace` past `grace_ends_at` → `expired`.
- `MemberService.renew(subscription_id)`:
  - From `active`/`grace` extends `expires_at += plan.duration_days`, status → `active`, clears `grace_ends_at`.
  - From `expired`/`cancelled` creates a **new** `CustomerSubscription` row (preserving enrollment price is a Phase 8 decision — today renewal uses the current plan price).
- `POST /api/merchant/members/{id}/renew` exposes it.

### Benefit redemption + clawback (Phase 6 gap)
- `POST /api/public/benefits/redeem` `{coupon_code}` → decrements `uses_remaining` if > 0; returns new value + status. Returns 404 for unknown codes; 410 when already depleted.
- `MemberService.cancel()` now calls `benefits.service.revoke_for_subscription(sub_id)` to mark every non-flag-only delivery `status='revoked'` and zero `uses_remaining`.

### Interest registration + public plans states (Phase 4 gap)
- `GET /api/public/merchants/{store}/plans` now returns `store_state` =
  `'available'` when the merchant has ≥1 active plan, else `'coming_soon'`.
- `POST /api/public/merchants/{store}/interest` `{email}` records an
  `InterestSignup` row. Idempotent per `(store, email)`.
- `customer.html` uses both:
  - If `store_state === 'coming_soon'`: show a coming-soon hero + email interest form.
  - Before submitting enrollment: call `/membership?email=…` and, if the email already has a `pending` or `active` subscription for the chosen plan, show an "already enrolled" variant with a link to `member.html`.
- `customer.html` gets an **ROI calculator** — user types their typical monthly spend, we show estimated yearly savings from discount + free shipping (static client-side math, no backend).

### Salla special offer (Phase 3 gap)
- `salla/provisioning.py::provision_special_offer(plan, client_factory=...)` — creates a Salla special offer for a plan (percentage discount bound to the customer group) and stores `salla_special_offer_id`. Same Salla/mock-fallback pattern as customer groups + coupons. Invoked after customer-group creation.

### Member dashboard polish (Phase 7 gap)
- `member.html` shows:
  - a "current period ends on" line when in `active`/`grace`.
  - a **Renew** CTA when status is `grace`/`expired`/`cancelled` (links to the merchant — since customers don't auth here, the CTA says "ask your store to renew" and copies a short reference).
  - a **savings-to-date** stat: sum of `uses_allowed - uses_remaining` * typical order estimate — keep it a simple demonstrative number, not a promise. Computed server-side in the membership lookup.

## Non-goals

- Customer login/auth (still email-keyed on the public member view).
- Proration, credit notes, or partial refunds.
- Push-style launch notifications (the `InterestSignup` table is there; the actual sender is a future phase).

## Deliverables

- `migrate_phase_g.py`
- Model extensions + status transitions + routes above
- Updated frontend pages
- Tests per change
- Updated READMEs + this spec's tasks.md

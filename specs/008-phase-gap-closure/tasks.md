# Tasks: Phase G — Gap Closure

## Data
- [x] T001 `InterestSignup` model
- [x] T002 Add `CustomerSubscription.grace_ends_at` + `MembershipPlan.salla_special_offer_id`
- [x] T003 `migrate_phase_g.py` (idempotent ALTERs + `create_all`)

## Lifecycle (Phase 5 gap)
- [x] T010 `expire_overdue_subscriptions` — active→grace (stamps `grace_ends_at = expires + grace_days`), grace→expired; returns `{expired, grace}`
- [x] T011 `MemberService.renew` + `POST /api/merchant/members/{id}/renew` — extends active/grace, restarts from expired/cancelled

## Benefits (Phase 6 gap)
- [x] T020 `benefits.service.revoke_for_subscription(sub_id)` called from `MemberService.cancel`
- [x] T021 `POST /api/public/benefits/redeem` — decrement `uses_remaining`, 404/410 paths
- [x] T022 `sum_savings_for_subscription` surfaced on the public membership lookup

## Phase 4 gap
- [x] T030 `InterestSignup` upsert + `POST /api/public/merchants/{store}/interest`
- [x] T031 Public plans endpoint returns `store_state`
- [x] T032 `customer.html` — coming-soon / interest-capture branch, already-member branch, ROI calculator, structured plan fields (tier, discount, shipping) surfaced as chips

## Phase 3 gap
- [x] T040 `provision_special_offer(plan)` — Salla `POST /admin/v2/specialoffers`, mock-fallback-friendly; invoked from `provision_merchant_program` after customer-group creation
- [x] T041 Skips with reason `no-discount` / `no-customer-group` when prerequisites aren't met

## Phase 7 gap
- [x] T050 `member.html` — grace pill, grace-ends-at line, savings-to-date hero note, renewal hint
- [x] T051 `members.html` — grace filter, expired filter, renew action per row

## Tests (15 new, 170 total)
- [x] T060 Lifecycle: active→grace, grace→expired, far-future cascade
- [x] T061 Clawback: active/delivered coupons → revoked, flag-only untouched
- [x] T062 Renew: extends active expires_at, creates new row for expired/cancelled, rejects pending
- [x] T063 Redemption: decrement happy path, 404 unknown, 410 depleted
- [x] T064 Interest signup: create, idempotent, invalid-email 400
- [x] T065 Public plans `store_state`: coming_soon → available after launch
- [x] T066 Special offer: created when group + discount present, skipped otherwise

## Docs
- [x] T070 Backend README Phase G section (endpoints, migration, status machine)
- [x] T071 Frontend README updates
- [x] T072 Phase G tasks complete

---

## Status: COMPLETE

170 tests passing. Every row in the `plane.md` coverage matrix is now ✅
except the pieces explicitly deferred (real customer auth; ledger-backed
savings tracking tied to Salla order webhooks; recurring-subscription
product provisioning).

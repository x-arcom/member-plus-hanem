# Tasks: Phase 6 — Benefits Engine

## Data model
- [x] T001 `BenefitDelivery` model
- [x] T002 `database/migrate_phase_6.py`

## Services
- [x] T010 `salla/coupons.py::create_coupon` — SallaClient-backed with Salla-down → mock-code fallback
- [x] T011 `benefits/service.py::generate_on_activation(subscription_id)` — creates rows for every enabled benefit on a plan
- [x] T012 `benefits/service.py::generate_monthly_gifts(now)` — idempotent per `(subscription, period_key=YYYY-MM)`
- [x] T013 `list_for_subscription` / `list_for_merchant` helpers

## Integration
- [x] T020 `MemberService.confirm` launches `generate_on_activation` in a daemon thread
- [x] T021 Scheduler runner registers `monthly_gifts` cron (day=1, hour=3)

## Routes
- [x] T030 Public membership lookup returns `benefits[]` per subscription
- [x] T031 `GET /api/merchant/members/{subscription_id}/benefits` with merchant isolation

## Frontend
- [x] T040 `member.html` — coupon cards with code, uses remaining, expiry, copy button, mock-hint when `status='delivered-mock'`
- [x] T041 `members.html` — new Benefits column + per-row benefit-count pill

## Tests (14 new, 155 total)
- [x] T050 `tests/unit/test_coupons.py` — live success / 4xx fallback / missing-id fallback / no-client fallback
- [x] T051 `tests/unit/test_benefits_service.py` — silver/gold activation shape, idempotency, monthly-gift window
- [x] T052 `tests/integration/test_benefits_api.py` — end-to-end confirm → benefits visible via both endpoints + isolation + auth

## Docs
- [x] T060 Backend README Phase 6 section (migration + endpoints + fallback contract)
- [x] T061 Frontend README updated (member.html coupon cards)
- [x] T062 This tasks.md marked complete

---

## Status: COMPLETE

Benefits are now real: Silver and Gold members actually receive the
coupons their plans promise, visible immediately on `member.html` with a
copy-to-clipboard button, and on the merchant's members list as a count
badge per row. The mock-fallback guarantees the experience degrades
gracefully when the Salla integration is misconfigured or down, without
silently no-op'ing for the merchant.

Deferred (future phases):
- Redemption tracking (decrement `uses_remaining` on webhook)
- Refund / clawback on cancellation mid-cycle
- Enforcement of `early_access_enabled` in Salla (currently a flag row only)
- Member-only pricing beyond the auto-discount customer group

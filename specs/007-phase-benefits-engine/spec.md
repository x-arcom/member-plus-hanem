# Phase 6 Specification: Benefits Engine

**Feature**: 007-phase-benefits-engine
**Status**: Open
**Objective**: Actually deliver the benefits `plane.md` Phase 6 promises. When
a merchant confirms a member's payment, the platform must generate the
coupons + entitlements that plan configured — today nothing happens.

## Scope

### Data
- `BenefitDelivery` — one row per issued benefit (subscription_id, kind,
  coupon_code, uses_allowed, uses_remaining, valid_until, salla_coupon_id,
  status, created_at).

### Benefits covered in this phase
| kind              | trigger                     | Salla action                    | fallback when Salla missing |
|-------------------|-----------------------------|----------------------------------|------------------------------|
| `free_shipping`   | subscription activation     | create free-shipping coupon, N uses = `free_shipping_quota` | mock code `MP-FS-xxxxxxxx` |
| `monthly_gift`    | 1st of month, eligible subs | create single-use % / fixed coupon | mock code `MP-GIFT-xxxxxxxx` |
| `auto_discount`   | subscription activation     | noted only — already attached to the Phase-R customer group | record a `delivered` row with `salla_coupon_id=null` |
| `early_access`    | subscription activation     | feature flag (no coupon yet)     | record a `delivered` row |
| `badge`           | subscription activation     | feature flag (no coupon yet)     | record a `delivered` row |

### Module layout
- `backend/src/benefits/service.py` — `generate_on_activation(subscription_id)`, `generate_monthly_gifts(now)`, `list_for_subscription(id)`.
- `backend/src/salla/coupons.py` — `create_coupon(session, merchant_id, kind, amount, valid_days, reason)` using `SallaClient`, with a mock fallback when Salla responds 4xx/5xx or no client is available.
- `backend/src/database/migrate_phase_6.py` — creates the new table.

### Hooks
- `MemberService.confirm()` calls `benefits.service.generate_on_activation(subscription_id)` in a background thread.
- Scheduler runner adds a monthly-gift tick on the 1st at 03:00 UTC.

### API
- `GET /api/public/merchants/{store}/membership?email=` — already returns subscriptions; now also returns each subscription's `benefits[]`.
- `GET /api/merchant/members/{subscription_id}/benefits` (JWT) — list deliveries per subscription.

### Frontend
- `member.html` — every benefit pill becomes a real card showing the coupon code + uses remaining + expiry (when applicable).
- `members.html` — row gains a small `#badges` column with a count of active benefit deliveries.

## Non-goals

- Actual redemption/usage tracking (decrements happen on webhook in a
  future phase; the `uses_remaining` field is present but frozen to the
  initial value for now).
- Member-only pricing beyond the customer-group auto-discount already
  provisioned in Phase R.
- Refund / clawback when a subscription is cancelled mid-cycle.
- Real Salla coupon endpoints are called best-effort; failures fall back
  to mock codes so merchants never see a silent no-op.

## Functional Requirements

- **FR-001** `BenefitDelivery` rows are created atomically with the
  subscription confirm (via fire-and-forget thread so the confirm response
  is fast).
- **FR-002** Only plan-enabled benefits produce rows: no `monthly_gift`
  delivery if `monthly_gift_enabled=false`.
- **FR-003** Monthly-gift job is idempotent per (subscription, month) —
  re-running the tick on the same day does not duplicate coupons.
- **FR-004** Every delivery returned by the public endpoint omits
  sensitive internals; the `coupon_code` is the only user-visible secret
  and is shown as-is.
- **FR-005** When the Salla client raises, the service falls back to a
  mock coupon code so the experience degrades gracefully; the delivery
  row records `salla_coupon_id=null` and `status='delivered-mock'`.

## Deliverables

- Model + migration
- `benefits` module, `salla/coupons.py`
- Hook into `MemberService.confirm` + monthly tick in scheduler
- Updated lookup endpoint + new merchant endpoint
- Updated `member.html` (coupon cards) and `members.html` (benefit count)
- Unit + integration tests
- Updated READMEs + Phase 6 tasks

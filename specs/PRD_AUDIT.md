# PRD V3.0 vs. Current Implementation — Full Audit

**Date**: 2026-04-17
**PRD**: Member Plus V3.0 (68 pages, READY FOR DEV)
**Current codebase**: Phases 0–4 + R + 6 + G (170 tests, sidebar dashboard rebuild)

---

## Severity Legend

- 🔴 **CRITICAL** — fundamentally wrong, must rebuild/replace
- 🟠 **MAJOR** — significant gap, requires new code or substantial refactor
- 🟡 **MINOR** — needs adjustment but foundation is usable
- ✅ **OK** — matches or close enough

---

## 1. DATABASE SCHEMA (PRD §14 — 11 Tables)

### PRD requires EXACTLY these 11 tables:

| PRD Table | Our Equivalent | Status | Delta |
|-----------|---------------|--------|-------|
| `merchants` | `Merchant` model | 🟠 | Missing: `permanent_access_token`, `recurring_enabled`, `our_plan` (enum starter/pro/unlimited), `member_count` (cached), `setup_step` (0-5 not 0-3). `status` should be enum `trial|active|suspended|cancelled` not `is_active` bool. `salla_store_id` should be BIGINT not String. Tokens encrypted AES-256 (we use Fernet — acceptable). |
| `membership_plans` | `MembershipPlan` | 🟡 | Close. Missing: `gift_name_ar`, `gift_name_en`, `salla_offer_id` (we have it as `salla_special_offer_id`). PRD has `status` enum `active|paused|deactivating|deactivated` — we use `is_active` bool. `display_name_ar/en` naming vs our `name_ar/name_en`. |
| `plan_price_versions` | ❌ NOT BUILT | 🔴 | **Entirely missing.** PRD requires price lock architecture: each member references a specific price version. Multiple versions active simultaneously. Each version = separate Salla product. This is core to price changes without disrupting existing members. |
| `members` | `Customer` + `CustomerSubscription` | 🟠 | Wrong shape. PRD has ONE `members` table combining customer identity + subscription + benefit tracking. We split into `Customer` + `CustomerSubscription`. PRD fields missing: `salla_customer_id` (BIGINT), `salla_subscription_id`, `subscribed_price`, `current_period_end`, `grace_period_ends_at`, `next_renewal_at`, `is_at_risk`, `total_saved_sar`, `free_shipping_used`, `free_shipping_quota`. |
| `gift_coupons` | `BenefitDelivery` (partial) | 🟠 | PRD has a dedicated table with: `gift_type` enum, `gift_description_ar/en`, `attempts`, `month` (UNIQUE with member_id). Our `BenefitDelivery` is more generic — it works but doesn't match the PRD schema. |
| `free_shipping_coupons` | `BenefitDelivery` (partial) | 🟠 | PRD has a SEPARATE table for shipping coupons with `quota`, `used_count` (OUR counter, not Salla's), `status` enum. We merged this into `BenefitDelivery` generically. |
| `webhook_events` | ❌ NOT BUILT | 🔴 | **Missing.** PRD requires EVERY webhook stored BEFORE processing, with `salla_event_id` UNIQUE constraint for idempotency. We process webhooks inline without storing them first. This is the core deduplication mechanism (§16, §21 R-01). |
| `interest_registrations` | `InterestSignup` | 🟡 | Close but different: PRD uses `salla_customer_id` (from Twilight SDK, zero form fields) — we use email (form-based). PRD: zero personal data collected by us. |
| `benefit_events` | `BenefitDelivery` (partial) | 🟠 | PRD has this as a SEPARATE audit table for dispute investigation: `salla_order_id`, `event_type` (discount_applied / shipping_coupon_used / etc.), `amount_saved`, `reason_not_applied`. We don't track per-order benefit events. |
| `activity_log` | ❌ NOT BUILT | 🟠 | Missing. PRD requires a chronological feed of all events (member.joined, benefit.discount_applied, coupon.generated, plan.benefit_changed, etc.) with metadata JSONB. |
| `scheduled_jobs` | ❌ NOT BUILT | 🟠 | Missing as a DB table. PRD tracks job status in DB: `job_type`, `scheduled_for`, `status` (pending/running/completed/failed/skipped), `attempts`, `max_attempts`, `error_message`. We use APScheduler in-memory. |

### Additional PRD tables (from later sections):
| Table | Status |
|-------|--------|
| `admin_users` (§39.3) | ❌ NOT BUILT |
| `admin_notes` (§39.3) | ❌ NOT BUILT |
| `email_log` (§41.7) | ❌ NOT BUILT |

---

## 2. AUTHENTICATION (PRD §20, Appendix A, Appendix B)

| Requirement | PRD Says | We Have | Status |
|-------------|----------|---------|--------|
| Merchant login | NO login screen. Permanent access token in email link → HttpOnly cookie session (8h) | JWT in URL params via `?token=` | 🔴 |
| Token storage | `permanent_access_token` VARCHAR(64) UNIQUE, generated at install, never expires | JWT with expiration | 🔴 |
| Cookie config | `HttpOnly + Secure + SameSite=Strict` | No cookies — JWT in Authorization header | 🔴 |
| Deep linking | `?goto=gift-config` etc. — 7 defined goto values | Not implemented | 🟠 |
| Member auth | Twilight SDK `salla.auth.customer.id` — cross-reference with DB | Email-as-key lookup | 🟠 |
| Webhook verification | `crypto.timingSafeEqual()` on raw body BEFORE JSON parse | HMAC-SHA256 but basic `hmac.compare_digest` | 🟡 |

---

## 3. PAYMENT MODEL (PRD §2.4, §7.1, §12)

| Requirement | PRD Says | We Have | Status |
|-------------|----------|---------|--------|
| Who handles payments | **Salla handles ALL payments.** We NEVER handle money directly. | Moyasar adapter, manual confirm flow | 🔴 |
| Member subscription | Via Salla Recurring Payments API — checkout URL → Salla processes | Our own enrollment + manual confirm | 🔴 |
| Merchant billing | Via Salla App Store billing — we respond to `app.subscription.started` | Our own billing/subscribe endpoint | 🔴 |
| Price lock | Salla subscription params can't be modified once created → new Salla product per price point | Not implemented | 🔴 |

---

## 4. SETUP WIZARD (PRD §8.2, §43.4)

| Requirement | PRD Says | We Have | Status |
|-------------|----------|---------|--------|
| Structure | Welcome (pre-step) + Step 1–4 | 3 steps (Silver → Gold → Review) | 🟠 |
| Welcome screen | Logo, store name, 3-item checklist, 5-min estimate, "Start Setup" CTA | Not implemented | 🟠 |
| Step 1 | Prices & billing cycles per plan. Featured badge toggle. Plan names AR+EN. | Merged into our Silver/Gold steps | 🟡 |
| Step 2 | ALL 6 benefits shown. Automatic (B2, B5, B6 locked on) vs Configurable (B1, B3). Gold > Silver validated. | Only discount + shipping + toggles | 🟠 |
| Step 3 | Monthly Gift: type, value, description AR+EN, live preview panel | Not a separate step | 🟠 |
| Step 4 | Review: summary table + 2 mandatory consent checkboxes (can't skip) | Our review step has no consent checkboxes | 🟡 |
| Smart defaults | All fields pre-filled. Silver: 49 SAR, 10%, 2 uses. Gold: 99 SAR, 15%, 4 uses. | We have defaults but different values (Gold was 25%) | 🟡 |
| Validation | Per-step blocking validation. Gold discount > Silver. Gold shipping >= Silver. | Basic validation only | 🟡 |

---

## 5. THE 6 BENEFITS (PRD §10)

| Benefit | PRD Mechanism | Our Implementation | Status |
|---------|--------------|-------------------|--------|
| B1 — Auto Discount | Salla Special Offer API → auto-applies at checkout | `discount_percent` on plan + provisioned offer | 🟡 |
| B2 — Member-Only Price | Salla Special Offer `offer_type: special_price` per product | ❌ NOT BUILT | 🔴 |
| B3 — Free Shipping | Personal coupon, `include_customer_ids`, manual code entry, monthly quota | Coupon generation exists but not Salla-format | 🟡 |
| B4 — Monthly Gift | 1 use, expires end of month, no rollover, merchant configures type/value/description | Generic gift delivery exists | 🟡 |
| B5 — Early Product Access | Products hidden from public via Salla, visible only to correct tier group | ❌ NOT BUILT | 🔴 |
| B6 — Identity Badge | App Snippet on every store page, tap → salla-sheet mini-dashboard | ❌ NOT BUILT (requires App Snippet) | 🔴 |

---

## 6. BRAND & DESIGN (PRD §43, §42)

| Element | PRD Says | We Have | Status |
|---------|----------|---------|--------|
| Primary color | `#BE52EF` | `#667eea` (completely different blue-purple) | 🔴 |
| Hover color | `#9B35D4` | `#5568d3` | 🔴 |
| Light fill | `#F3E0FD` | `#eef1ff` | 🔴 |
| Gold tier indicator | `#C9A84C` | `#ffc107` (Material amber) | 🟠 |
| Silver tier indicator | `#B0A898` | `#e8eaf6` (Material indigo light) | 🟠 |
| Background | `#FAF8F4` (warm cream) | `#f5f5f5` (cool gray) | 🟠 |
| Success color | `#0F6E56` (green for success ONLY) | Matches approximately | 🟡 |
| Display font | Cormorant Garamond | Segoe UI (system default) | 🔴 |
| UI font (Arabic) | Tajawal | Segoe UI | 🔴 |
| Border radius | 2px buttons, 4px cards | 8px (our `--radius-md`) | 🟠 |
| Design direction | Luxury, NET-A-PORTER, AMEX. Diamond markers. Near-black Gold cards. | Generic SaaS look | 🔴 |
| Logo mark | Flat SVG diamond + white plus, `#BE52EF` fill | 📱 emoji / uploaded 3D PNG (PRD says never use 3D in UI) | 🟠 |

---

## 7. MERCHANT DASHBOARD (PRD §8.4)

| Screen | PRD Requires | We Have | Status |
|--------|-------------|---------|--------|
| Main Overview | Member count by tier, revenue, churn, at-risk count, ROI calculation, time-filtered (7d/30d/3m/12m) | Store name + trial + basic metrics | 🟠 |
| Today's Focus Card | ONE contextual action with priority logic (gift warning > grace expiry > plan limit > zero members) | Not implemented | 🔴 |
| Member List | Searchable, filterable by tier+status. Name, tier, status, subscribed price, renewal date, total savings. | Basic list with filters | 🟡 |
| Member Profile | Full history: all charges, all benefits used, all orders, total savings, message this member | Not implemented | 🔴 |
| Analytics | Revenue trend, member growth, churn timing, tier comparison, benefit effectiveness | Not implemented | 🔴 |
| Gift Management | Configure current/next month gift. Redemption history. Next generation date visible. | Not implemented | 🔴 |
| Activity Log | Chronological feed, filterable, exportable CSV | Not implemented | 🔴 |
| Settings | Plan names, prices, benefits, notifications, branding, billing, data export | Basic settings page | 🟡 |
| Promotion Kit | Plans page link (always visible), social media captions, navigation guide | Not implemented | 🔴 |
| Preview Mode | Preview as Gold/Silver member, preview plans page, preview badge | Not implemented | 🔴 |

---

## 8. WEBHOOKS (PRD §16 — 12 Events)

| Event | PRD Handler | Our Handler | Status |
|-------|------------|-------------|--------|
| `app.store.authorize` | Create merchant, set trial, send welcome email | OAuth callback (close) | 🟡 |
| `app.subscription.started` | Activate plans page if setup done, notify interest registrants | Not fully implemented | 🟠 |
| `app.subscription.canceled` | Full offboarding (§30) | `app.uninstalled` handler (partial) | 🟠 |
| `app.subscription.expired` | Same as canceled | Not handled | 🔴 |
| `subscription.created` | Create member, add to Customer Group, set welcome popup flag | Our enrollment flow (different mechanism) | 🟠 |
| `subscription.charge.succeeded` | Reset quotas, generate gift, update period dates, notify member | Not webhook-driven | 🔴 |
| `subscription.charge.failed` | Start grace period, create expiry job, notify member | Not webhook-driven | 🔴 |
| `subscription.cancelled` | Record cancelled_at, create remove_from_group job for period_end | Partial | 🟠 |
| `subscription.updated` | Sync subscription data | Not handled | 🔴 |
| `order.created` | Log to benefit_events, update total_saved, update last_order | Not handled | 🔴 |
| `order.cancelled` | Restore free shipping credit atomically | Not handled | 🔴 |
| `customer.updated` | Refresh cached data | Not handled | 🔴 |
| **Idempotency** | INSERT webhook_events ON CONFLICT DO NOTHING | Not implemented (no webhook_events table) | 🔴 |

---

## 9. SCHEDULER JOBS (PRD §17 — 5 Jobs)

| Job | PRD Spec | Our Impl | Status |
|-----|----------|----------|--------|
| `generate_monthly_coupons` | 28th of month, 09:00 KSA. Rate limited 10 API/sec. Gift not configured → skip + alert. Per-member 3 retries. | `generate_monthly_gifts` (partial, different timing) | 🟠 |
| `renewal_charge` | Call Salla Charge Subscription API. Pre-checks. Wait for webhook. | Not implemented (Salla handles) | 🟠 |
| `grace_period_expiry` | Created on charge.failed. Cancellable. Remove from group + Salla Cancel + set expired. | `expire_overdue_subscriptions` (partial) | 🟡 |
| `remove_from_group` | Created on subscription.cancelled. Runs at `current_period_end`. Salla Cancel + remove from group. | Not implemented as a deferred job | 🔴 |
| `group_health_check` | Daily 03:00 KSA. Verify all groups exist. Verify member-group membership. At-risk detection (45+ days no order). Suspension detection. | Not implemented | 🔴 |

---

## 10. API CONTRACTS (PRD §18)

| Requirement | PRD Says | We Have | Status |
|-------------|----------|---------|--------|
| Versioning | `/api/v1/...` from day one | `/api/merchant/...` (no versioning) | 🟠 |
| Auth | JWT in HttpOnly cookie. Never trust URL params alone. | JWT in Authorization header from URL | 🔴 |
| Merchant endpoints | 16 defined endpoints with exact query params | ~10 endpoints, different naming | 🟠 |
| Public/Member endpoints | 6 endpoints including `/api/v1/member/state` (lightweight, for App Snippet) | Different shape | 🟠 |

---

## 11. APP SNIPPET (PRD §19 — 7 Injection Points)

| Injection Point | Status |
|-----------------|--------|
| Store header (badge → salla-sheet) | ❌ NOT BUILT |
| Homepage (coming soon widget) | ❌ NOT BUILT |
| Product page (discount preview / member price) | ❌ NOT BUILT |
| Cart page (free shipping banner) | ❌ NOT BUILT |
| Order confirmation (adaptive savings) | ❌ NOT BUILT |
| Profile menu ("My Membership" link) | ❌ NOT BUILT |
| Plans page (Zone 1) | We host this separately | 🟡 |

**Note:** App Snippets are Salla-specific JS injections. They require the Salla Twilight SDK and run inside the merchant's store theme. This is entirely new infrastructure — NOT part of our current frontend.

---

## 12. SECURITY (PRD §20)

| Requirement | Status |
|-------------|--------|
| HMAC-SHA256 with timingSafeEqual before JSON parse | 🟡 Basic HMAC exists |
| JWT via HttpOnly + Secure + SameSite=Strict cookie | 🔴 JWT in URL/header |
| Member auth via Twilight SDK customer.id | 🔴 Not implemented |
| AES-256 token encryption at rest | 🟡 Fernet (acceptable) |
| Data isolation (merchant_id from JWT, never URL params) | 🟡 Close |
| Rate limiting POST /interest: 3/IP/hour | 🔴 Not implemented |
| Never store credit cards, passwords, contact info | ✅ OK |

---

## 13. EMAIL SYSTEM (PRD §23, §41, Appendix A.3)

| Requirement | PRD Says | We Have | Status |
|-------------|----------|---------|--------|
| Language rule | ONE language per email based on `merchant.dashboard_language` | Bilingual toggle | 🟠 |
| Merchant emails | 15+ specific emails with exact AR+EN copy | Welcome + trial reminder + setup complete (3 only) | 🔴 |
| Member notifications | 11 specific notifications | None implemented | 🔴 |
| WhatsApp/SMS | 4 critical triggers | Not implemented | 🔴 |
| Email log table | Full tracking: sent/delivered/opened/bounced/failed | Not implemented | 🔴 |

---

## 14. ADMIN PANEL (PRD §39, §40, §41)

| Component | Status |
|-----------|--------|
| Internal admin dashboard (our ops) — 7 screens | ❌ NOT BUILT |
| Business admin panel (owner view) — 7 screens | ❌ NOT BUILT |
| Notifications center — 4 screens | ❌ NOT BUILT |
| Role-based access (admin/support/devops) | ❌ NOT BUILT |
| Separate subdomain `admin.ourapp.com` | ❌ NOT BUILT |

---

## 15. ADDITIONAL PRD FEATURES NOT BUILT

| Feature | PRD Section | Status |
|---------|------------|--------|
| Price & name change rules (4 scenarios) | §28 | ❌ |
| Plan deactivation (3 scenarios: one plan / all / pause) | §29 | Partial (we have activate/deactivate) |
| Merchant offboarding (7-step) | §30 | Partial |
| Value summary before member cancellation | §31 | ❌ |
| Win-back flow (3 touchpoints, 30-day trigger) | §32 | ❌ |
| Order confirmation adaptive states (5 states) | §33 | ❌ |
| Tier upgrade flow Silver → Gold (3 screens) | §34 | ❌ |
| Milestone celebration cards | §35 | ❌ |
| Promotion kit | §36 | ❌ |
| Preview member experience | §37 | ❌ |
| Complimentary members | §38 | ❌ |
| Race condition protections (6 specific) | §21 | Partial |

---

## SUMMARY — What's Actually Reusable vs. Must Rebuild

### ✅ Keep (foundation is solid)
- FastAPI app structure + lifespan + middleware
- Config loader + env validation + fail-fast
- Health endpoint
- Webhook signature verification (needs upgrade to timingSafeEqual)
- Fernet encryption module (`auth/crypto.py`)
- Token refresh mechanism (`auth/token_refresh.py`)
- SallaClient with 401-retry (`salla/client.py`)
- Docker + docker-compose setup
- Structured JSON logging + request ID middleware
- Test infrastructure (conftest.py, fixtures)
- Design system CSS structure (needs color/font/radius overhaul)

### 🟠 Refactor significantly
- Database models — rename/restructure to match PRD's 11-table schema
- Webhook dispatcher — add webhook_events table for idempotency, handle all 12 events
- Scheduler — move from APScheduler in-memory to DB-tracked jobs
- Membership plans — add plan_price_versions, gift config fields, status enum
- Benefits — split into separate gift_coupons + free_shipping_coupons tables per PRD
- Setup wizard — expand to Welcome + 4 steps per PRD §43.4
- Email system — implement all 26 email types with per-merchant language

### 🔴 Rebuild from scratch
- Authentication — replace JWT-in-URL with permanent access tokens + HttpOnly cookies
- Payment flow — remove Moyasar entirely, wire to Salla Recurring Payments
- Brand/design — new color palette, fonts, border radius per §43
- App Snippet system — entirely new (Salla Twilight SDK injections)
- Admin panel — 3 separate panels, ~18 screens total
- Member-Only Price (B2) and Early Product Access (B5) benefits
- Activity log, benefit_events audit trail, email_log tracking

---

## RECOMMENDED APPROACH

**Phase 1 — Schema & Auth Foundation** (must do first, everything depends on it)
1. Rebuild DB schema to match PRD §14 exactly (11 tables)
2. Implement permanent access token auth (Appendix B)
3. Implement webhook_events idempotency table
4. Update API versioning to `/api/v1/...`

**Phase 2 — Brand & Design Overhaul**
1. Update CSS tokens to PRD §43 colors/fonts/radius
2. Build flat SVG logo mark
3. Rebuild all pages with luxury design direction

**Phase 3 — Core Business Logic**
1. Wire to Salla Recurring Payments (remove Moyasar)
2. Implement plan_price_versions
3. Expand wizard to PRD 4-step structure
4. Implement all 12 webhook handlers
5. Implement all 5 scheduler jobs (DB-tracked)

**Phase 4 — Benefits Engine (all 6)**
1. B2 Member-Only Price
2. B5 Early Product Access
3. Refine B1, B3, B4, B6

**Phase 5 — Dashboard Screens**
1. Today's Focus Card
2. Analytics
3. Gift Management
4. Activity Log
5. Promotion Kit
6. Preview Mode

**Phase 6 — Email & Notification System**
1. All 26 email types with exact copy
2. Email log tracking
3. WhatsApp/SMS critical triggers

**Phase 7 — Admin Panel**
1. Internal ops dashboard
2. Business owner panel
3. Notifications center

**Phase 8 — App Snippet**
1. Salla Twilight SDK integration
2. 7 injection points
3. Member state endpoint

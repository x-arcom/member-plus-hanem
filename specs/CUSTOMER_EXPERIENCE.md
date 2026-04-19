# Member Plus — Customer Experience Architecture

## Customer Journey: 3 Phases

```
TRIAL/COMING SOON          LIVE/JOIN                MEMBER DASHBOARD
──────────────────    →    ──────────────────    →    ──────────────────
Teaser widget              Plans page                 My Membership
Interest registration      ROI calculator             Benefits & codes
"Coming soon" state        Tier comparison             Savings history
                           Subscribe CTA               Renewal info
                           Already-member state        
```

---

## Phase 1: Trial / Coming Soon

### Purpose
When the merchant has installed Member Plus but hasn't launched yet (trial, setup incomplete), customers see a lightweight teaser — NOT the full plans page.

### Component: `coming-soon-widget`

**Placement:** Embedded in store via Salla App Snippet — appears as a floating banner or inline section on the store homepage.

**What it shows:**
- Store logo + "Member Plus" branding
- "برنامج العضوية قيد الإعداد" (Membership program coming soon)
- Single CTA: "أنا مهتم" (I'm interested)

**States:**
| State | What happens |
|-------|-------------|
| Default | Banner visible, button active |
| Loading | Button shows spinner during API call |
| Registered | Button changes to "تم التسجيل ✓", disabled. Message: "سنبلغك فور إطلاق البرنامج" |
| Already registered | Shows "تم التسجيل ✓" immediately |
| Error | Toast with error message, button re-enabled for retry |

**Backend integration:**
- `POST /api/v1/store/{store_id}/interest` with `salla_customer_id`
- Stored in `interest_registrations` table
- Duplicate check: same customer can't register twice
- Merchant dashboard shows interest count

**Merchant feedback loop:**
- Interest count visible in merchant dashboard overview
- Focus card: "X عميل مهتم ببرنامج العضوية — أكمل الإعداد للإطلاق"

**Page:** `customer.html?store={id}` — shows `state-coming-soon` when `coming_soon: true`

---

## Phase 2: Live / Join CTA

### Purpose
Once the merchant is live (setup_completed = true, status = active), customers see the full membership join experience.

### Component: `plans-page`

**Placement:** 
- Dedicated page: `customer.html?store={store_id}`
- Link shared by merchant in store navigation, social media, or product pages
- App Snippet banner on storefront linking to this page

**What it shows:**
1. Store name + "انضم لبرنامج العضوية"
2. ROI Calculator — "كم ستوفر؟" with monthly spend input
3. Silver + Gold tier cards side by side (Gold highlighted as "الأكثر شعبية")
4. Each tier: name, price, billing cycle, benefits list with diamond markers
5. "اشترك الآن" CTA → redirects to Salla native checkout
6. Trust row: "الدفع الآمن عبر سلة · إلغاء في أي وقت"

**User state variants:**
| Customer State | What they see |
|---------------|--------------|
| Non-member (new visitor) | Full plans page with tier comparison + "اشترك الآن" |
| Active member | "أنت عضو بالفعل — اشتراكك نشط" + link to member dashboard |
| Former member | Plans page + banner: "كنت عضواً ووفّرت X ر.س — عُد الآن!" |
| Expired member | Plans page + banner: "انتهى اشتراكك — جدد الآن لاستعادة مزاياك" |

**Page:** `customer.html?store={id}` — shows `state-plans`, `state-already`, or `state-coming-soon`

---

## Phase 3: Customer Membership Dashboard

### Purpose
After joining, the customer has their own "عضويتي" (My Membership) dashboard showing everything about their membership.

### Component: `member-dashboard`

**Placement:** `member.html?store={store_id}&cid={salla_customer_id}`
- Accessed via App Snippet badge on storefront
- Linked from "الذهاب للوحة العضوية" in the already-member state

**Page:** `member.html`

---

## Member Dashboard — Section Structure

### Section 1: Tier Hero Card
**What:** Large gradient card showing membership tier
**Shows:** Tier icon (👑/💎), plan name (الباقة الذهبية), status (عضوية نشطة / ملغاة), member since date
**Variants:**
- Gold: gold gradient background
- Silver: silver gradient background
- Cancelled: muted background with end date

### Section 2: Savings Banner
**What:** Total savings from membership
**Shows:** "X ر.س — إجمالي ما وفّرته بعضويتك"
**Logic:** Sum of all `benefit_events` amount_saved for this member

### Section 3: Benefits Grid (2x2)
**What:** 4 benefit cards showing current status
**Gold plan shows:**
| Card | Value |
|------|-------|
| 🏷️ الخصم التلقائي | 15% |
| 🚚 الشحن المجاني | 2 من 4 متبقي |
| 🎁 الهدية الشهرية | متاحة / مستخدمة |
| ⚡ الوصول المبكر | مفعّل |

**Silver plan shows:**
| Card | Value |
|------|-------|
| 🏷️ الخصم التلقائي | 10% |
| 🚚 الشحن المجاني | 1 من 2 متبقي |
| ⭐ شارة العضوية | مفعّلة |
| 💎 سعر الأعضاء | مفعّل |

### Section 4: Active Shipping Code
**What:** Copyable coupon code for free shipping
**Shows:** Code (FS-H7J9K1), usage counter (2/4), copy button
**Visible:** Only when shipping coupon is active for current month
**Hidden:** When exhausted or no shipping benefit

### Section 5: Gift History (Gold only)
**What:** Monthly gift coupons with codes
**Shows:** Each gift: description, code, status (متاحة/مستخدمة/منتهية), copy button for active ones, expiry date
**Logic:** From `gift_coupons` table, ordered by month desc, limit 6

### Section 6: Savings History
**What:** Recent benefit usage with amounts
**Shows:** Event type (خصم تلقائي, شحن مجاني, هدية شهرية) + amount saved + date
**Logic:** From `benefit_events` table, last 10 events

### Section 7: Renewal Bar
**What:** Next billing date and amount
**Shows:** "التجديد القادم: May 10, 2026 — 99 ر.س"

---

## Snapshot States — All Components

### coming-soon-widget
| State | UI |
|-------|----|
| Loading | Skeleton block |
| Default | Banner + "أنا مهتم" button |
| Registered | "تم التسجيل ✓" + disabled button |
| Error | Toast + retry |

### plans-page
| State | UI |
|-------|----|
| Loading | Skeleton cards |
| Coming soon | Teaser + interest button |
| Plans visible | Tier cards + ROI calculator |
| Already member | Success message + dashboard link |
| Error | Error message + retry |

### member-dashboard
| State | UI |
|-------|----|
| Loading | Skeleton tier hero + benefit cards |
| Active member | Full dashboard with all sections |
| Cancelled member | Tier hero (muted) + renewal CTA |
| Non-member | "لست عضواً" + join link |
| Former member | "كنت عضواً" + win-back message + total saved |
| Error | Error message + retry |

### code-card (shipping / gift)
| State | UI |
|-------|----|
| Active | Green border, code visible, copy button |
| Used/Redeemed | Dimmed (0.5 opacity), no copy button |
| Expired | Dimmed, "منتهية" label |
| Exhausted | Dimmed, "مستنفد" label |

### benefit-card
| State | UI |
|-------|----|
| Active | Normal, value shown |
| Off/Disabled | Dimmed (0.4 opacity), "غير مفعّل" |

---

## Reusable Product Components

| Component | Used in | Purpose |
|-----------|---------|---------|
| `tier-hero` | member.html | Gradient tier header |
| `savings-banner` | member.html | Total savings display |
| `benefit-card` | member.html, customer.html | Single benefit with value |
| `code-card` | member.html | Copyable coupon code with status |
| `tier-card` | customer.html | Plan comparison card with CTA |
| `roi-calculator` | customer.html | Savings estimator |
| `interest-widget` | customer.html (coming soon) | Pre-launch interest capture |
| `trust-row` | customer.html | Payment security message |
| `renewal-bar` | member.html | Next billing info |
| `savings-history` | member.html | Recent benefit events list |

---

## API Endpoints Used

| Endpoint | Page | Purpose |
|----------|------|---------|
| `GET /api/v1/store/{id}/plans` | customer.html | Fetch store plans (or coming_soon flag) |
| `POST /api/v1/store/{id}/interest` | customer.html | Register pre-launch interest |
| `GET /api/v1/member/state` | App Snippet | Lightweight badge check (cached 5 min) |
| `GET /api/v1/member/dashboard` | member.html | Full member data with codes, gifts, savings |

---

## App Snippet (Storefront Badge)

**What:** Injected via Salla App Snippet on every store page
**Purpose:** Show membership badge + link to member dashboard

**For members:**
- Small floating badge: "👑 عضو ذهبي" or "💎 عضو فضي"
- Click → opens member.html

**For non-members:**
- Small floating banner: "انضم للعضوية"
- Click → opens customer.html

**API:** `GET /api/v1/member/state?store_id={id}&salla_customer_id={cid}`
- Cached in SessionStorage for 5 minutes (per PRD)
- Returns: `{is_member, tier, display_name_ar, free_shipping_remaining, total_saved_sar}`

---

## File Map

```
frontend/
  customer.html    → Plans page (join / coming soon / already member)
  member.html      → Customer membership dashboard (عضويتي)
  
  (App Snippet)    → Storefront badge (to be built as Salla widget)
```

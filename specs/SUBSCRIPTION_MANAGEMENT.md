# Subscription Management System — Product Specification

## 1. Feature Overview

A system-wide subscription control and monitoring area within the Member Plus admin panel that provides full visibility into two distinct subscription layers:

- **Layer 1: Merchant Subscriptions** — stores subscribing to our Member Plus app via Salla App Store
- **Layer 2: Member Subscriptions** — end-customers subscribing to merchant membership plans via Salla Recurring Payments

Both layers share similar lifecycle states but serve different stakeholders and have different business implications.

## 2. Purpose

Enable the admin team to:
- Monitor all subscription activity across the entire platform in real-time
- Track revenue health (MRR, churn, growth) at both merchant and member levels
- Identify at-risk subscriptions before they churn
- Investigate payment failures and take corrective action
- Understand the full subscription lifecycle for any merchant or member
- Generate reports for business decisions

## 3. Admin Panel Scope

### 3.1 Subscriptions Overview Dashboard

**Location:** New tab "الاشتراكات" in admin sidebar

**KPI Summary (top row):**

| KPI | Description |
|-----|------------|
| Active Merchants | Currently paying merchants |
| MRR (App) | Monthly recurring revenue from merchant subscriptions |
| Active Members | Total active members across all merchants |
| MRR (Members) | Monthly recurring revenue from member subscriptions |
| Churn Rate | Merchant churn in last 30 days |
| Trial Conversion | % of trial merchants who became paying |
| Failed Payments | Unresolved payment failures (both layers) |
| Net Growth | New subscriptions - cancellations this month |

**Two-tab view:**
- **اشتراكات التجار** — merchant subscription table
- **اشتراكات الأعضاء** — member subscription table

### 3.2 Merchant Subscriptions Table

**Columns:**
| Column | Description |
|--------|------------|
| المتجر | Store name + Salla ID |
| الباقة | Starter / Pro / Unlimited |
| الحالة | Active / Trial / Suspended / Cancelled / Expired |
| تاريخ البدء | Subscription start date |
| التجديد القادم | Next renewal date |
| آخر دفعة | Last successful payment date + amount |
| الأعضاء | Active member count |
| الإجراء | View detail / Suspend / Reactivate |

**Filters:**
- Status: All / Active / Trial / Suspended / Cancelled / Expired
- Plan: All / Starter / Pro / Unlimited
- Date range: Registration date
- Search: Store name, Salla ID

**Sortable by:** Date, status, member count, plan

### 3.3 Member Subscriptions Table

**Columns:**
| Column | Description |
|--------|------------|
| العميل | Customer ID / name |
| المتجر | Merchant store name |
| الباقة | Silver / Gold |
| الحالة | Active / Cancelled / Expired |
| السعر | Monthly subscription price |
| تاريخ البدء | Join date |
| التجديد القادم | Next renewal date |
| إجمالي المدفوع | Total payments made |

**Filters:**
- Status: All / Active / Cancelled / Expired
- Tier: All / Silver / Gold
- Merchant: Dropdown of all merchants
- Date range
- Search: Customer ID, store name

## 4. Merchant Detail Page — Subscription Section

### 4.1 Current Subscription Card
- Current plan (Starter/Pro/Unlimited)
- Status badge (Active/Trial/Suspended/Cancelled)
- Start date
- Next renewal date
- Monthly amount
- Member count / limit

### 4.2 Subscription Timeline
Chronological log of all subscription events:

| Event Type | Description |
|-----------|------------|
| `app.installed` | Merchant installed the app |
| `trial.started` | Trial period began |
| `trial.ending` | Trial ending warning sent |
| `subscription.started` | First payment successful |
| `subscription.renewed` | Monthly renewal successful |
| `payment.failed` | Payment attempt failed |
| `subscription.suspended` | Suspended due to payment failure |
| `plan.upgraded` | Upgraded from Starter → Pro, etc. |
| `plan.downgraded` | Downgraded |
| `subscription.cancelled` | Merchant cancelled |
| `subscription.expired` | Subscription expired |
| `subscription.reactivated` | Re-subscribed after cancellation |

### 4.3 Payment History
Table of all payment transactions:
- Date, amount, status (paid/failed/refunded), plan, invoice reference

### 4.4 Plan Change History
- From plan → To plan, date, reason

## 5. Member Detail Page — Subscription Section

### 5.1 Current Membership Card
- Current tier (Silver/Gold)
- Status (Active/Cancelled/Expired)
- Merchant/store name
- Monthly price
- Join date
- Current period end
- Next renewal date

### 5.2 Subscription Timeline
Chronological log:

| Event Type | Description |
|-----------|------------|
| `member.joined` | Customer subscribed |
| `charge.succeeded` | Monthly payment successful |
| `charge.failed` | Payment failed |
| `member.renewed` | Renewal processed |
| `benefits.activated` | All benefits activated |
| `benefits.reset` | Monthly quotas reset |
| `gift.generated` | Monthly gift created |
| `gift.redeemed` | Gift coupon used |
| `shipping.used` | Free shipping used |
| `member.cancelled` | Member cancelled |
| `member.expired` | Membership expired |
| `tier.upgraded` | Silver → Gold |
| `tier.downgraded` | Gold → Silver |

### 5.3 Payment History
- Date, amount, status, period, payment method

### 5.4 Benefits Usage Summary
- Discount: times applied, total saved
- Shipping: used/quota per month
- Gifts: redeemed/generated per month
- Total savings

## 6. Suggested Statuses

### Merchant Subscription Statuses
| Status | Arabic | Color | Description |
|--------|--------|-------|------------|
| trial | تجربة | Gold | Within free trial period |
| active | نشط | Green | Paying, subscription current |
| suspended | معلّق | Red | Payment failed, grace period |
| cancelled | ملغى | Gray | Merchant cancelled |
| expired | منتهي | Gray | Subscription expired |

### Member Subscription Statuses
| Status | Arabic | Color | Description |
|--------|--------|-------|------------|
| active | نشط | Green | Membership active |
| cancelled | ملغى | Gray | Cancelled, benefits until period end |
| expired | منتهي | Gray | Membership ended |

## 7. Recommended Admin Actions

### On Merchant Subscriptions
| Action | When |
|--------|------|
| Suspend | Payment issues, policy violation |
| Reactivate | After issue resolved |
| Extend Trial | Give more trial days |
| Force Cancel | Emergency cancellation |
| Add Note | Internal annotation |

### On Member Subscriptions
| Action | When |
|--------|------|
| View in merchant context | Navigate to merchant detail |
| View subscription timeline | Full event history |
| Add Note | Internal annotation |

## 8. Optional KPIs / Widgets

### Subscription Health Dashboard
- **Trial → Active conversion rate** (last 30/90 days)
- **Average subscription lifetime** (months)
- **Revenue per merchant** (average)
- **Revenue per member** (average)
- **Payment failure rate** (% of charges that fail)
- **Recovery rate** (% of failed payments that eventually succeed)
- **Net MRR change** (new MRR - churned MRR)

---

## Implementation Priority

### Phase 1 (Now)
- Admin subscriptions tab with merchant + member tables
- Filters and search
- Merchant detail subscription section
- Member detail subscription section

### Phase 2 (Later)
- Subscription health KPIs
- Trial conversion tracking
- Payment failure alerts
- Automated suspension/reactivation
- Revenue forecasting

# Member Plus — Phase Plan V2 (16 Phases)

**Date**: 2026-04-17
**Status**: ACTIVE — replaces all prior phase plans
**Rule**: Platform foundation first, NOT screens first. Each phase fully tested + browser-verified before next.

---

## Global Rules

Every phase must include:
- empty state
- loading / processing state
- error state
- success state where relevant

Also:
- app installation starts inside Salla
- merchant receives an email from our system with a direct dashboard link
- merchant lands in onboarding first
- merchant cannot proceed without required setup
- all setup can be edited later from the dashboard

---

## Phase 0 — Validation, access, and launch blockers

**Goal**: remove anything that can break the product before build starts.

- request required Salla scopes
- test customer groups at scale
- test recurring payments enablement
- test cancel subscription behavior
- set up dev / staging / prod
- OAuth refresh utility
- Salla retry utility
- webhook signature verification
- scheduler monitoring
- legal requirements
- pricing/commission confirmation

**Deliverable**: platform is technically and legally safe to build on

---

## Phase 1 — Core platform foundation

**Goal**: create the app backbone.

- install flow from Salla
- merchant record creation
- trial state
- dashboard access flow
- merchant session handling
- base DB schema
- webhook storage
- scheduled jobs table
- activity log foundation
- API structure
- security rules
- merchant/member/plan status models

**Deliverable**: working backend shell with merchant identity, state, and persistence

---

## Phase 2 — Merchant access and onboarding

**Goal**: let the merchant enter the app correctly and finish the required setup.

- welcome email from our system
- direct dashboard link
- onboarding entry screen
- required setup enforcement
- pricing setup
- billing cycle setup
- benefits selection
- helper copy that settings can be edited later
- save and continue flow
- dashboard access only after minimum setup is complete

**Deliverable**: merchant can install, enter dashboard, and complete onboarding cleanly

---

## Phase 3 — Membership Settings page

**Goal**: build the merchant's main configuration area.

- Membership Settings page
- billing section
- pricing fields
- billing cycle fields
- benefits section
- only required membership settings
- remove non-essential plan-definition fields
- remove old activate/deactivate logic from the old plan area

**Deliverable**: one clean configuration area for the merchant's membership setup

---

## Phase 4 — Benefits framework

**Goal**: build the benefits page as a decision page, not a heavy form page.

Rules:
- every benefit card shows: title, short description, toggle, simple state
- only simple inline configuration is allowed here
- deep management belongs in its own page

Benefits to support:
- Member Coupons
- Member Shipping
- Special Offers

**Deliverable**: merchant understands what each benefit does and can turn it on or off clearly

---

## Phase 5 — Benefit behavior model

**Goal**: classify each benefit correctly so product logic stays clean.

**A) Automatic benefits** — activate immediately, no monthly reset:
- automatic discount
- member price
- early access
- badge

**B) Hard quota benefits** — limited, reset monthly, no rollover:
- free shipping
- monthly gift

**C) Optional vs always-on**:
- Optional = merchant chooses whether to enable
- Always-on = tied to membership core

**Deliverable**: every benefit has a clear product model before UI and engineering continue

---

## Phase 6 — Member Shipping inside Benefits page

**Goal**: inline shipping config inside the benefit card.

- toggle
- short description
- inline shipping methods selector
- states: off / no methods selected / methods selected / fetching / fetch error

**Deliverable**: shipping works as a lightweight inline benefit setup

---

## Phase 7 — Coupons page

**Goal**: full coupon lifecycle in its own page.

Benefits page keeps only: toggle + short description + CTA to open coupon settings.

Coupons page: create / edit / save draft / schedule / activate / deactivate / history.

If benefit is OFF: hide create CTA, show blocked state, keep history visible, CTA goes to Membership Benefits.

**Deliverable**: full coupon lifecycle managed in one place

---

## Phase 8 — Special Offers page

**Goal**: full special offer lifecycle in its own page. Same pattern as coupons.

If benefit is OFF: hide create CTA, show blocked state, keep history visible.

**Deliverable**: full offers lifecycle managed in one place

---

## Phase 9 — Members page

**Goal**: membership customers only (not all store customers).

- active / payment failed / cancelled / expired
- filters
- member table
- renewal visibility
- last activity

**Deliverable**: merchant sees only relevant membership customers

---

## Phase 10 — Billing & Subscription

**Goal**: merchant's subscription to OUR app.

- current plan
- subscription status
- price / billing cycle
- start date / next renewal
- invoices / payment history

**Deliverable**: merchant understands their billing relationship with the app

---

## Phase 11 — Membership Activity Log

**Goal**: operational history.

- member name / event type / membership status / date / details
- examples: subscription started, renewal successful, payment failed, cancelled, expired, coupon issued, benefit enabled

**Deliverable**: merchant can trace what happened across the membership system

---

## Phase 12 — Customer-facing member experience

**Goal**: what the end customer sees.

- join card / membership CTA
- plans page
- welcome moment
- member dashboard
- benefit visibility
- renewal and status messaging
- states: active / non-member / expired / former member

**Deliverable**: customer can understand, join, and use the membership clearly

---

## Phase 13 — Notifications and warnings

**Goal**: all essential communication.

- welcome email / setup reminders / gift warnings / billing warnings
- stop-program warning
- member payment failure / grace-period messages
- blocked-state copy for coupons/offers when feature is off

**Deliverable**: system communicates clearly at every critical step

---

## Phase 14 — Internal admin and operations

**Goal**: internal team control layer.

- admin dashboard / merchant lookup / member lookup
- webhook visibility / scheduler monitor
- failed event retry / notes / ops health

**Deliverable**: team can operate and support the platform safely

---

## Phase 15 — QA, edge cases, and launch hardening

**Goal**: make the product actually launchable.

- race conditions / e2e flow testing / Salla theme testing
- webhook duplication / scheduler retry / benefit conflicts
- offboarding / blocked states
- empty/loading/error/success checks everywhere

**Deliverable**: launch-ready product, not just completed screens

---

## Execution Order

0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14 → 15

**Do NOT skip. Do NOT build screens first, logic later.**

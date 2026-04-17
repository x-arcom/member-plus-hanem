# Phase 2 Implementation Plan

**Branch**: `003-phase-membership-billing` | **Spec**: `spec.md`

## Approach

Phase 2 extends the Phase 1 backend and frontend without reorganising them. New modules live under `backend/src/{plans,setup_wizard,billing}/` and new frontend pages under `frontend/{wizard,plans}.html`. The Merchant model gains one column (`setup_step`) and one foreign key (`subscription_id`). All new routes are JWT-protected and scoped to the authenticated merchant.

Payments are intentionally abstracted behind a `PaymentAdapter` protocol with a `MockPaymentAdapter` implementation; Phase 3 will add a real adapter.

## Module Layout

```
backend/src/
├── plans/              # MembershipPlan CRUD
│   ├── service.py
│   └── routes.py
├── setup_wizard/       # setup_state transitions
│   ├── service.py
│   └── routes.py
├── billing/            # Subscription + mock payment
│   ├── adapter.py      # PaymentAdapter protocol + MockPaymentAdapter
│   ├── service.py
│   └── routes.py
└── database/models.py  # extended with MembershipPlan, Subscription, setup_step
```

## Database Migration Strategy

We keep using SQLAlchemy `Base.metadata.create_all()` (same as Phase 1). The new `setup_step` column defaults to `0`; SQLite's `ALTER TABLE` is not needed for a fresh DB. For an existing DB, a one-shot migration script in `backend/src/database/migrate_phase2.py` adds the column via raw SQL.

## API Surface (new)

```
GET    /api/merchant/setup/state
POST   /api/merchant/setup/advance          { step_data: {...} }

GET    /api/merchant/plans                   ?active_only=true
POST   /api/merchant/plans                   { name_ar, name_en, price, currency, duration_days, benefits, is_active }
GET    /api/merchant/plans/{id}
PATCH  /api/merchant/plans/{id}
DELETE /api/merchant/plans/{id}

GET    /api/merchant/billing/tiers
GET    /api/merchant/billing/subscription
POST   /api/merchant/billing/subscribe       { tier }
POST   /api/merchant/billing/mock-confirm    { subscription_id, success }
```

## Testing Strategy

- **Unit**: Plan service (create/list/update/delete, merchant isolation), wizard service (state transitions, idempotency), billing service (tier lookup, subscribe, mock-confirm, duplicate-active guard).
- **Integration**: Each router tested via the existing `app_client` TestClient fixture — login via demo OAuth → exercise the route.

## Rollout

Phase 2 is backwards-compatible with Phase 1. Existing merchants default to `setup_step=0, setup_state=onboarding`. Dashboard shows a CTA if setup isn't complete.

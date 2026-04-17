# Phase 1 MVP Tasks — Simplified for Quick Implementation

**Objective**: Get merchant onboarding working end-to-end with mock OAuth & email.

---

## Backend Tasks (Sprint 1)

### ✅ T-B1: OAuth Callback Handler (Mock)
- ✅ Created `/api/oauth/callback` GET endpoint
- ✅ Accepts mock OAuth code and state
- ✅ Creates merchant record + trial activation
- ✅ Returns JWT token for merchant auth
- **File**: `backend/src/oauth/provider.py` + integrated in `main.py`

### ✅ T-B2: Merchant Authentication Middleware
- ✅ JWT token validation via `get_current_merchant()`
- ✅ Protected dashboard API routes
- ✅ Extracts merchant_id from token
- **File**: `backend/src/auth/jwt.py`

### ✅ T-B3: Dashboard API Endpoints
- ✅ `GET /api/merchant/profile` — merchant info
- ✅ `GET /api/merchant/trial` — trial status
- ✅ `GET /api/merchant/dashboard` — overview
- **File**: `backend/src/dashboard/routes.py`

### ✅ T-B4: Email Service (Mock)
- ✅ Welcome email template (AR/EN)
- ✅ Mock email send (logs to console)
- ✅ Async sending support
- **File**: `backend/src/email/service.py`

---

## Frontend Tasks (Sprint 1)

### ✅ T-F1: Dashboard HTML/React Shell
- ✅ Login page with OAuth redirect + demo login
- ✅ Dashboard layout (header, trial countdown, profile widgets)
- ✅ Language toggle (AR/EN) with LTR/RTL support
- **File**: `frontend/index.html`, `frontend/dashboard.html`

### ✅ T-F2: API Integration
- ✅ Fetch `/api/merchant/profile`
- ✅ Fetch `/api/merchant/trial`
- ✅ Fetch `/api/merchant/dashboard`
- ✅ Display merchant data and trial countdown
- ✅ JWT token management in localStorage
- **File**: `frontend/dashboard.html`

### ✅ T-F3: Responsive Design
- ✅ Mobile-first responsive layout (375px, 768px, 1920px)
- ✅ Works on desktop/tablet/mobile
- ✅ CSS Grid and Flexbox
- ✅ Language direction toggle (RTL/LTR)
- **File**: `frontend/index.html`, `frontend/dashboard.html`

---

## Implementation Status

| Task | Status | File | Lines |
|------|--------|------|-------|
| T-B1 | ✅ Complete | `backend/src/oauth/provider.py` | ~80 |
| T-B2 | ✅ Complete | `backend/src/auth/jwt.py` | ~90 |
| T-B3 | ✅ Complete | `backend/src/dashboard/routes.py` | ~70 |
| T-B4 | ✅ Complete | `backend/src/email/service.py` | ~50 |
| **Backend Total** | **✅ 4/4** | **~290 LOC** | - |
| T-F1 | ✅ Complete | `frontend/index.html` | ~250 |
| T-F2 | ✅ Complete | `frontend/dashboard.html` | ~300 |
| T-F3 | ✅ Complete | Both | Responsive CSS |
| **Frontend Total** | **✅ 3/3** | **~550 LOC** | - |

**Total Phase 1 MVP Code**: ~840 LOC across 8 files

---

## Timeline & Effort

- **Phase 1 MVP**: ✅ Complete (2.5 hours as estimated)
- **Backend**: ✅ 1.5 hours (database models + services + routes)
- **Frontend**: ✅ 1 hour (login + dashboard + responsive)
- **Integration & Testing**: Ready for E2E

---

## Testing

Complete end-to-end testing guide available in:
📋 **[E2E_TEST_GUIDE.md](../../E2E_TEST_GUIDE.md)**

Quick start:
```bash
# Terminal 1: Backend
cd backend
python3 -m uvicorn src.app-entrypoint.main:app --reload

# Terminal 2: Frontend
cd frontend
python3 -m http.server 3000

# Browser: http://localhost:3000
# Click "Demo Login" → Dashboard appears
```

---

## Deliverables

✅ **Backend**:
- OAuth callback endpoint (mock)
- JWT authentication middleware
- 3 protected dashboard API endpoints
- Mock email service with bilingual templates

✅ **Frontend**:
- HTML login page with OAuth redirect
- HTML dashboard with API integration
- Bilingual UI (Arabic/English)
- Responsive design (mobile/tablet/desktop)
- Language toggle with RTL/LTR support

✅ **Documentation**:
- E2E test guide with 10 test cases
- Frontend README with setup instructions
- Complete flow diagram

---

## Phase 1 Full (Next Sprint)

After successful MVP E2E testing, Phase 1 Full will add:

1. **Real Salla OAuth**: Replace mock provider with production OAuth
2. **Real Email Provider**: Replace console logging with SendGrid/SES/Postmark
3. **Setup Wizard**: Multi-step onboarding UI
4. **Database**: Migrate from SQLite to PostgreSQL for production
5. **Authentication**: Add refresh tokens, session management
6. **Security**: HTTPS, CSRF protection, rate limiting
7. **Monitoring**: Error tracking, analytics, logging
8. **Phase 2 Prep**: Member management API foundation

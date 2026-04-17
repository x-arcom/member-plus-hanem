# Phase 1 Quickstart: Merchant Install and Trial Onboarding

Welcome to Phase 1 development! This guide will get you set up and testing the merchant onboarding flow locally.

---

## Prerequisites

- Python 3.9+
- Git with member-plus repository cloned
- Phase 0 backend running successfully
- Salla OAuth test app credentials (app_id, app_secret)
- Email service account (SendGrid, AWS SES, or similar)
- PostgreSQL or SQLite for local development

---

## Environment Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
pip install sqlalchemy python-dotenv requests cryptography
# For async email jobs:
pip install celery redis  # Or use in-memory queue for local dev
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Phase 0 (from before)
SALLA_API_KEY=test-api-key
SALLA_WEBHOOK_SECRET=test-webhook-secret
DATABASE_URL=sqlite:///./test.db
ENVIRONMENT=development

# Phase 1: OAuth Configuration
SALLA_OAUTH_CLIENT_ID=your-salla-oauth-app-id
SALLA_OAUTH_CLIENT_SECRET=your-salla-oauth-app-secret
SALLA_OAUTH_REDIRECT_URI=http://localhost:8000/api/oauth/callback

# Phase 1: Email Configuration
EMAIL_SERVICE=sendgrid  # or 'ses', 'smtp'
SENDGRID_API_KEY=your-sendgrid-api-key
# Or for SMTP:
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-app-password

# Phase 1: Trial Configuration
TRIAL_DURATION_DAYS=14

# Phase 1: Authentication
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# Phase 1: Database (if using PostgreSQL)
# DATABASE_URL=postgresql://user:password@localhost:5432/memberplus
```

### 3. Initialize Database

Run database migrations:

```bash
# Create tables
python -m alembic upgrade head

# Or manually create tables (SQLite):
sqlite3 test.db < backend/src/database/schema.sql
```

---

## Running Phase 1 Locally

### 1. Start the Backend Server

```bash
cd backend
SALLA_OAUTH_CLIENT_ID=test-client \
SALLA_OAUTH_CLIENT_SECRET=test-secret \
DATABASE_URL=sqlite:///test.db \
python -m uvicorn src.app-entrypoint.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Starting Member Plus Phase 1 backend...
INFO:     ✓ Configuration validated
INFO:     ✓ Database connected
INFO:     ✓ OAuth configured
```

### 2. Start the Frontend (if using React)

In a separate terminal:

```bash
cd frontend
npm install
npm start
```

Frontend will be available at `http://localhost:3000`

---

## Testing Phase 1 Endpoints

### Test 1: Health Check (Phase 0)

```bash
curl -s http://localhost:8000/health | python -m json.tool
```

Expected response:
```json
{
  "status": "healthy",
  "components": {"app": "ok"},
  "details": "Platform foundation is ready"
}
```

### Test 2: OAuth Authorization URL

```bash
curl -s "http://localhost:8000/api/oauth/authorize" | python -m json.tool
```

Expected response (contains Salla OAuth link):
```json
{
  "authorization_url": "https://salla.sa/oauth/authorize?client_id=...&redirect_uri=..."
}
```

### Test 3: Mock OAuth Callback (Simulate Salla Redirect)

For testing without a real Salla app, you can mock the OAuth callback:

```bash
# Get authorization code from Salla (manual step or use mock)
CODE="mock-auth-code-12345"
STATE="mock-state-12345"

curl -X GET "http://localhost:8000/api/oauth/callback?code=$CODE&state=$STATE" \
  -H "Content-Type: application/json"
```

Expected response:
```json
{
  "status": "success",
  "message": "Merchant created and onboarded successfully",
  "merchant_id": "550e8400-e29b-41d4-a716-446655440000",
  "dashboard_url": "http://localhost:3000/dashboard"
}
```

### Test 4: Get Merchant Profile

```bash
MERCHANT_ID="550e8400-e29b-41d4-a716-446655440000"
TOKEN="your-jwt-token-from-oauth-callback"

curl -X GET "http://localhost:8000/api/merchant/profile" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

Expected response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "salla_store_id": "12345",
  "store_name": "My Store",
  "merchant_email": "merchant@example.com",
  "language": "ar"
}
```

### Test 5: Get Trial Status

```bash
curl -X GET "http://localhost:8000/api/merchant/trial" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

Expected response:
```json
{
  "trial_active": true,
  "trial_start_date": "2026-04-16T10:00:00Z",
  "trial_end_date": "2026-04-30T10:00:00Z",
  "remaining_days": 14
}
```

### Test 6: Get Dashboard Overview

```bash
curl -X GET "http://localhost:8000/api/merchant/dashboard" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

Expected response:
```json
{
  "merchant_name": "Ahmed",
  "store_name": "My Store",
  "setup_state": "onboarding",
  "trial_remaining_days": 14,
  "member_count": 0,
  "monthly_revenue": 0
}
```

### Test 7: Verify Welcome Email Sent

Check your email inbox (or SendGrid logs) for welcome email:

**Subject**: Welcome to Member Plus! 🎉

**Content**: Should include:
- Your merchant name
- Your store name
- Trial duration (14 days)
- Link to dashboard
- Next steps (start setup wizard)

---

## Testing Complete Onboarding Flow

### End-to-End Test Script

```bash
#!/bin/bash
# test-phase1-e2e.sh

set -e

echo "🚀 Starting Phase 1 E2E Test..."

# Step 1: Health check
echo "1️⃣ Testing health endpoint..."
curl -s http://localhost:8000/health | python -m json.tool

# Step 2: OAuth authorization URL
echo "2️⃣ Getting OAuth authorization URL..."
AUTH_URL=$(curl -s "http://localhost:8000/api/oauth/authorize" | python -c "import sys, json; print(json.load(sys.stdin)['authorization_url'])")
echo "Authorization URL: $AUTH_URL"

# Step 3: Simulate OAuth callback
echo "3️⃣ Simulating OAuth callback..."
RESPONSE=$(curl -s -X GET "http://localhost:8000/api/oauth/callback?code=mock-code&state=mock-state")
echo "$RESPONSE" | python -m json.tool

# Extract merchant ID and token
MERCHANT_ID=$(echo "$RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['merchant_id'])")
TOKEN=$(echo "$RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin)['token'])")

echo "✅ Merchant created: $MERCHANT_ID"
echo "✅ Token received: ${TOKEN:0:20}..."

# Step 4: Get merchant profile
echo "4️⃣ Getting merchant profile..."
curl -s -X GET "http://localhost:8000/api/merchant/profile" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

# Step 5: Get trial status
echo "5️⃣ Checking trial status..."
curl -s -X GET "http://localhost:8000/api/merchant/trial" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

# Step 6: Get dashboard
echo "6️⃣ Getting dashboard overview..."
curl -s -X GET "http://localhost:8000/api/merchant/dashboard" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool

echo "✅ Phase 1 E2E test complete!"
```

Run the test:

```bash
bash test-phase1-e2e.sh
```

---

## Testing with pytest

### Run Unit Tests

```bash
cd backend
python -m pytest tests/unit/ -v
```

Expected: All tests passing

### Run Integration Tests

```bash
python -m pytest tests/integration/ -v
```

### Run E2E Tests

```bash
python -m pytest tests/integration/test_phase1_e2e.py -v
```

### Run All Tests with Coverage

```bash
python -m pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html  # View coverage report
```

---

## Frontend Testing

### Test Dashboard (React)

If using React frontend at `http://localhost:3000`:

1. Click "Login with Salla"
2. (Redirect to OAuth — use mock for local testing)
3. After OAuth callback, should land on dashboard
4. Dashboard should display:
   - Merchant name and store name
   - Trial countdown (14 days remaining)
   - Language toggle (AR/EN)
   - Placeholder for "Setup Wizard" (Phase 2)

### Test Language Toggle

1. Dashboard loads in Arabic (or English based on preference)
2. Click language toggle button
3. All UI text should switch to other language

### Run Frontend Tests

```bash
cd frontend
npm test
```

---

## Troubleshooting

### Issue: Database Connection Error

```
ERROR: could not connect to database: connection refused
```

**Solution**: Ensure PostgreSQL is running or SQLite file path is correct:

```bash
# Check SQLite file
ls -la test.db

# Or start PostgreSQL
brew services start postgresql
```

### Issue: OAuth Token Expired

```
ERROR: OAuth token expired; refresh failed
```

**Solution**: Token refresh background job may not be running. In development, manually trigger refresh or wait for scheduler to run (Phase 1.2 task T008).

### Issue: Email Not Sending

```
ERROR: Email send failed; Service unavailable
```

**Solution**: Check email service credentials in `.env`:

```bash
# For SendGrid
echo $SENDGRID_API_KEY  # Should not be empty

# For SMTP
python -m smtplib -t [your-email@example.com]
```

### Issue: Merchant Isolation Test Fails

```
FAIL: Merchant A can access Merchant B's profile
```

**Solution**: Check authorization middleware in `backend/src/auth/middleware.py`. Verify token validation and merchant_id extraction:

```python
@require_auth
def profile():
    current_merchant = get_merchant_from_token()
    # Should only return own data, never another merchant's
```

### Issue: Frontend Can't Reach Backend

```
CORS Error: localhost:8000 blocked by CORS policy
```

**Solution**: Add CORS headers to Phase 0 FastAPI setup:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Next Steps

Once Phase 1 is complete and tested:

1. ✅ Merchant can install app from Salla
2. ✅ OAuth authorization works
3. ✅ Trial state is activated
4. ✅ Dashboard is accessible
5. ✅ Welcome email is sent

**Ready for Phase 2: Setup Wizard** — Merchant configures membership program

To start Phase 2, run:

```bash
bash .specify/scripts/bash/create-new-feature.sh 'Phase 2 — Membership Program Setup Wizard'
```

---

## Questions or Issues?

- Check the Phase 1 spec: `specs/002-phase-merchant-install/spec.md`
- Check the implementation plan: `specs/002-phase-merchant-install/plan.md`
- Review the tasks: `specs/002-phase-merchant-install/tasks.md`
- Check backend API docs: `backend/docs/Phase1_API.md`

Good luck! 🚀

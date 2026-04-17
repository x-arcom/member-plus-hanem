# Phase 0 Quickstart

This guide will help you get the Member Plus Phase 0 backend running locally.

## Prerequisites

- Python 3.9+
- pip (Python package manager)

## Setup

### 1. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file in the `backend/` directory with the required variables:

```bash
cat > .env <<'EOF'
SALLA_API_KEY=test-api-key-for-development
SALLA_WEBHOOK_SECRET=test-webhook-secret-for-development
DATABASE_URL=sqlite:///./test.db
ENVIRONMENT=development
EOF
```

> **Note**: For production, use secure secrets managed by your deployment environment.

### 3. Start the server

```bash
cd backend
python src/app-entrypoint/main.py
```

You should see:

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete [GET /health]
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Test Phase 0 Foundation

### Health Check

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "components": {
    "app": "ok"
  },
  "details": "Platform foundation is ready"
}
```

### Root Endpoint

```bash
curl http://localhost:8000/
```

Expected response:

```json
{
  "message": "Member Plus Phase 0 Backend",
  "endpoints": {
    "health": "/health",
    "webhooks": "/webhooks/salla"
  }
}
```

### Webhook Verification

Test the webhook signature verification:

```bash
# Valid signature test
PAYLOAD='{"event":"test"}'
SIGNATURE=$(python3 -c "import hmac, hashlib; print(hmac.new(b'test-webhook-secret-for-development', b'$PAYLOAD', hashlib.sha256).hexdigest())")

curl -X POST http://localhost:8000/webhooks/salla \
  -H "Content-Type: application/json" \
  -H "X-Salla-Signature: $SIGNATURE" \
  -d "$PAYLOAD"
```

Expected response (202 Accepted):

```json
{
  "status": "ok"
}
```

## Next Steps

- Review the architecture in `specs/001-phase-foundation-and/plan.md`
- Complete Phase 0 tasks in `specs/001-phase-foundation-and/tasks.md`
- Prepare Phase 1: Merchant Install and Trial Onboarding

## Troubleshooting

### Missing environment variables

If you see: `Missing required configuration: ...`

Make sure your `.env` file is in the `backend/` directory and contains all required variables from `backend/src/config/README.md`.

### Module import errors

If imports fail, ensure the Python path includes `backend/src/`:

```bash
export PYTHONPATH="${PWD}/backend/src:${PYTHONPATH}"
```

### Port already in use

If port 8000 is taken, modify the startup command:

```bash
python src/app-entrypoint/main.py --port 8001
```

(Requires updating `main.py` to accept command-line arguments.)

# Backend Configuration

Required environment variables for Phase 0:

- `SALLA_API_KEY` — API key for Salla integration
- `SALLA_WEBHOOK_SECRET` — webhook signature secret for request validation
- `DATABASE_URL` — primary database connection string
- `ENVIRONMENT` — runtime environment name (development/staging/production)

Optional Phase 1 OAuth variables:

- `SALLA_CLIENT_ID` — Salla OAuth client ID
- `SALLA_CLIENT_SECRET` — Salla OAuth client secret
- `SALLA_OAUTH_AUTHORIZE_URL` — Salla OAuth authorization URL
- `SALLA_OAUTH_TOKEN_URL` — Salla OAuth token exchange URL
- `SALLA_OAUTH_REDIRECT_URI` — OAuth redirect URI registered with Salla
- `SALLA_STORE_INFO_URL` — Optional Salla store info endpoint for merchant profile lookup

Optional email service variables:

- `EMAIL_HOST` — SMTP host server
- `EMAIL_PORT` — SMTP port
- `EMAIL_USER` — SMTP username
- `EMAIL_PASSWORD` — SMTP password
- `EMAIL_FROM` — From address used for outgoing emails
- `EMAIL_USE_TLS` — Use STARTTLS (true/false)
- `EMAIL_USE_SSL` — Use SMTPS/SSL (true/false)

## Startup behavior

The system should fail fast if any required variable is missing.

If OAuth variables are not configured, the backend falls back to demo OAuth mode for local testing.

## Notes

- Store secrets securely in your deployment environment.
- Do not commit secret values to source control.

### Google Integrations (Calendar)

1. Create OAuth credentials in Google Cloud
- App type: Desktop
- Authorized redirect URI: https://developers.google.com/oauthplayground

2. OAuth Playground
- Settings → Use your own OAuth credentials: ON, paste Client ID/Secret
- Scopes: https://www.googleapis.com/auth/calendar
- Authorize APIs → Exchange authorization code for tokens

3. Seed tokens into vault
- Ensure env vars are set (`INTEGRATION_VAULT_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_CALENDAR_SYNC=true`)
- Run: `python backend/scripts/setup_integrations.py` and choose Google Calendar → paste access/refresh tokens for user `1`

4. Verify
- Create: POST /integrations/google/calendar/test_event/1
- Create custom: POST /integrations/google/calendar/create/1 with JSON body
- Sync: POST /integrations/sync/1
- Automations: GET /automations/metrics

Notes
- Token refresh is automatic; refreshed tokens are persisted to the vault.
- Celery Beat runs periodic sync (`integrations.sync_user_all("1")`).


## Secrets Management

This project treats secrets as runtime configuration provided via environment variables in production. Do not commit secrets and do not rely on `.env` files in production.

### Where secrets live

- Production: managed in a secure vault (e.g., AWS Secrets Manager, GCP Secret Manager, 1Password). They are injected into the process environment by the platform or deployment pipeline.
- Development: `.env` files can be used locally for convenience only. They are not loaded when `ENV=production`.

### How services fetch secrets

- The API process reads required settings from its environment. In development, a `.env` file may be pre-loaded (if present). In production, the app refuses to boot when required secrets are missing.

### Required secrets

- `JWT_SECRET`: HMAC key for signing access tokens.

Extend this list as more components are put behind secret gates (DB creds, S3 keys, etc.).

### Fail-fast behavior

- On startup, when `ENV=production`, the API validates that all required secrets are present and raises a clear error if any are missing. This is also validated in CI.

### Rotation procedure (example)

1. Add the new secret value in your vault with a staged key/version.
2. Update the deployment to use the new secret version (blue/green or rolling).
3. Verify that token issuance and critical flows succeed.
4. Remove the old version after the overlap window.

### Break-glass

- In exceptional incidents, a temporary override can be injected via the environment. Any use must be time-limited and audited.

### Audit notes

- Use your platform’s audit trail (e.g., AWS CloudTrail, 1Password access logs) to track read/access.



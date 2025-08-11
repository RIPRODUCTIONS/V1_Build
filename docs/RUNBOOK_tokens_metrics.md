### Tokens & Metrics Runbook

Auth tokens (dev)
- Obtain: POST /users/register then /users/login; use `access_token` as `Authorization: Bearer <token>`.
- HS256 settings via env: `JWT_SECRET` (required), optional `JWT_ISSUER`, `JWT_AUDIENCE`, `JWT_LEEWAY_SECONDS`.

Life routes
- All /life/* POSTs require bearer token; send an empty JSON body `{}` at minimum.

Metrics
- /metrics exposes Prometheus. Key series: `life_requests_total`, `life_request_latency_seconds_*`.
- Grafana (dev): http://localhost:3001 — import or auto-load the life dashboard.

Local infra
- Start: `make -C platform up` (Prometheus/Grafana/Temporal/Redis/MinIO)
- Stop: `make -C platform down`
- Alerts: edit `platform/infra/alerts.yml` and `platform/infra/prometheus.yml`

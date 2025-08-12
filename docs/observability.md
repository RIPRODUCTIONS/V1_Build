# Observability

Trace issues end-to-end: UI → API → Workers → DB/S3.

## Dashboards (Grafana)

Import JSON dashboards from `grafana/`:

- `api-dashboard.json`: latency p50/p95/p99 via `api_request_latency_seconds_bucket`, error rates via `errors_total{code}`, and `rate_limit_hits_total`.
- `worker-dashboard.json`: Celery retries (e.g., `celery_task_retry_total`) and DB connections.

If your metric names differ, tweak the PromQL expressions after import.

## Alerts (suggested)

- 5xx bursts: `sum(rate(errors_total{code=~"5.."}[5m])) > 1`
- Sustained 429s: `sum(rate(rate_limit_hits_total[5m])) by (route) > 0.1`
- Retry storms: `sum(rate(celery_task_retry_total[5m])) > 0`

## Uptime checks

See `uptime/README.md` for setting up Pingdom/Healthchecks on `/health/live` and `/health/ready`.


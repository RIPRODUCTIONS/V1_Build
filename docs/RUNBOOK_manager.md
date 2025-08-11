Manager Orchestrator Runbook

Prereqs
- Docker Desktop running
- `make` available

Local Infra
- Start: `make -C platform up`
- Stop: `make -C platform down`

Manager Service
- Start only manager: `make -C platform manager-up`
- Stop only manager: `make -C platform manager-down`
- Tail logs: `make -C platform manager-logs`

Health and Metrics
- Health: http://localhost:8011/health
- Metrics: http://localhost:9109/metrics (Prometheus format)
- Prometheus: http://localhost:9090 (job `manager`)
- Grafana: http://localhost:3001 (admin/admin)

Configuration
- Uses `REDIS_URL` from compose (`redis://redis:6379/0`)
- Ports can be overridden with env: `MANAGER_HEALTH_PORT`, `MANAGER_METRICS_PORT`

Correlation IDs
- API middleware sets `X-Correlation-Id` and propagates via `request.state.correlation_id`
- `/life/*` routes include `correlation_id` in payloads
- Manager logs include `correlation_id` in consumed events

RBAC Notes
- When `SECURE_MODE=1`, reads can require scopes (e.g., `life.read`) — enforcement is additive and can be applied via dependencies on routers.


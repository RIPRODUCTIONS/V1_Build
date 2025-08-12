## 1. Clarifying Questions

- What budget ceilings (monthly) apply to infra and LLM spend? ASSUMPTION: Dev <$200/mo.
- Which cloud(s) are preferred (AWS/GCP/Azure) and regions? ASSUMPTION: AWS us-west-2.
- Compliance constraints (PII scope, data retention, encryption at rest in all stores)? ASSUMPTION:
  basic PII, 90-day retention in dev.
- Incident response/on-call expectations? ASSUMPTION: business hours only.
- SSO/IdP requirements? ASSUMPTION: local accounts for now.

## 2. Program Map (tree)

- Life → health, nutrition, home, transport, learning
- Finance → bills, investments
- Safety → security sweep
- Utility → calendar organize, shopping optimize
- Business → marketing launch, sales outreach, ops brief, simulate cycle
- Agents → ideation, relationship openers, agent runtime

## 3. Target Architecture (diagram description + interface catalog)

- Durable workflows: Temporal
- Agent graphs: LangGraph
- Data/ops jobs: Prefect heartbeat (can evolve to Dagster)
- Event bus: Redis/Kafka (Redis local)
- OLTP: Postgres (dev may use sqlite)
- Object store: S3/MinIO
- Telemetry: Prometheus + Grafana + OTEL (optional exporter)
- Interfaces: REST (FastAPI), events (JSON) with idempotency keys

| Interface                     | Type  | Purpose      | Owner    | SLA           | Schema                     | Errors       |
| ----------------------------- | ----- | ------------ | -------- | ------------- | -------------------------- | ------------ |
| /life/\*                      | REST  | Trigger DAGs | Platform | 2xx within 2s | SimpleReq/EnqueuedResponse | 401/403, 5xx |
| events.AutomationRunRequested | event | Start runs   | Platform | N/A           | Pydantic+JSON              | N/A          |

## 4. Canonical Data Model

- Entities: AutomationRun(id, status, intent, created_at), User(id, email)
- Events: AutomationRunRequested { run_id, intent, payload }
- PII classification: email (PII), payload depends on domain
- Retention: 90 days in dev

## 5. Platform Standards

- Runtime: Python 3.11, FastAPI
- Queue/cache: Redis
- DB: Postgres (RDS later), Sqlite in CI
- Object store: S3/MinIO
- LLM: local-first, providers behind router
- Secrets: env vars in dev, SSM/Vault later
- CI/CD: GitHub Actions; platform-only CI for platform/\*\*

## 6. Risk Register

| Risk                     | Impact | Likelihood | Mitigation                   | Tripwire       |
| ------------------------ | ------ | ---------- | ---------------------------- | -------------- |
| Token misuse             | High   | Med        | HS256 gating + leeway checks | >3 401/min     |
| Unbounded metrics labels | Med    | Low        | Fixed label set              | >10k series    |
| Cost overruns            | High   | Med        | Local-first, budgets         | spend >$200/mo |

## 7. 90-Day Plan

- Phase 1 (Weeks 1–4): Orchestration spine, auth, metrics, CI; 3 demo flows live
- Phase 2 (Weeks 5–8): Event bus, object store, 5 high-value automations wrapped as activities;
  dashboards/alerts
- Phase 3 (Weeks 9–12): Data jobs (Prefect/Dagster), evaluations, policy gates, DR drill

Exit criteria: green CI, dashboards, PR checklist, playbooks

## 8. Sprint 1 Backlog (2 weeks)

- PR: merge recovery branch → master (CI green)
- Secrets: set JWT_SECRET, infra envs
- Grafana: import life dashboard, alert on 5xx >0.5%
- Playwright: add e2e for one /life/\* button
- Docs: runbooks for tokens and metrics

## 9. SLOs & Observability

- SLOs: API 99.5% success, p95 latency < 500ms; queue age < 1m
- Dashboards: life_requests_total, latency, 4xx/5xx
- Alerts: 5xx rate >0.5% 5m, latency p95 >1s 10m

## 10. Cost & Capacity Model

- Dev: Docker compose (Redis, Temporal, MinIO, Grafana/Prometheus), <$100/mo cloud if hosted
- Egress negligible; storage <10GB

## 11. Decision Log (ADRs)

- ADR-001: Choose Temporal/LangGraph/Prefect for orchestration spine (durable workflows, agent
  graphs, jobs)

## 12. Open Questions

- Required external integrations (email, calendars, banks)?
- Multi-tenant or single-tenant?
- Data residency or compliance mandates?

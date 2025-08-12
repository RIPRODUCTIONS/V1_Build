# Orchestration Spine (Temporal + LangGraph + Dagster/Prefect) — Bootstrap

This document captures the durable orchestration plan to scale hundreds of automations safely. It is
additive and does not change the existing backend; it provides a parallel spine you can adopt
incrementally.

## Architecture

- Business workflows: Temporal for long-running, retryable, idempotent workflows (supports
  human-in-the-loop)
- Agent runtime: LangGraph to compose/route multi-agent flows with state, retries, cost controls
- Data/ops pipelines: Dagster or Prefect for ETL, feature builds, eval jobs, and batch automations
- Event bus: Kafka/Redpanda (or Redis Streams for small installs)
- Storage: Postgres (OLTP) + S3-compatible object store (e.g., MinIO)
- Observability: OpenTelemetry traces/metrics/logs (collector → Grafana/Tempo/Loki)

## What this gives you

- A safe place to plug each automation: as Temporal activities, LangGraph agents, or Dagster/Prefect
  jobs
- Global observability, retries, timeouts, and versioned rollouts
- Separation of concerns: workflows vs. agent reasoning vs. data jobs

## Day‑0 checklist

- Repos/directories: `platform/orchestration`, `platform/data`, `platform/shared`
- Contracts: define Domain Events (JSON Schema + Pydantic) under `platform/shared`
- Plumbing (optional dev): Postgres, Redis, Kafka/Redpanda, S3 (MinIO), OTel collector
- Security: secrets via env/vault; RBAC scaffold; audit logging

## Master system prompt (for the Orchestrator agent)

```text
SYSTEM ROLE: ORCHESTRATOR (Level 1)
Mission: Safely coordinate hundreds of automations and AI agents as durable, cost-aware workflows. Never guess; always verify with tools, data, and policies.

Core Principles
- Reliability first: all actions must be idempotent, observable, and reversible.
- Least-privilege: only call tools you need; redact secrets in logs.
- Determinism at boundaries: summarize non-deterministic LLM outputs into typed events.

Environment / Primitives
- Workflows: Temporal (startWorkflow, signal, query, continueAsNew).
- Agents: LangGraph graphs (nodes=tools/agents; edges=control logic; persistent state).
- Data Pipelines: Dagster/Prefect jobs (materialize datasets, features, evals).
- Data: Postgres (OLTP), S3 (blobs), Redis (cache), Kafka (domain events).
- Telemetry: OpenTelemetry (trace_id, span_id, log levels), emit on every step.

Inputs
- Goal spec (YAML/JSON): desired outcome, constraints, SLAs, safety rules.
- Current state snapshot: workflow IDs, dataset versions, feature flags.

Outputs
- Signed Domain Events (JSON) that advance state machines.
- ADR notes for any architecture-affecting choice.

Policies
- Timeouts and retries must be explicit.
- Human-in-the-loop when confidence < threshold or when PII/compliance is involved.
- Cost guardrails: keep running token/compute budget; halt if exceeded.

Operating Loop
1) Validate goal → map to {Workflows | Agent Graphs | Data Jobs}.
2) Plan: draft DAG; annotate each node with inputs/outputs, SLAs, rollback strategy.
3) Execute atomically:
   - Start/Signal Temporal workflows for business processes.
   - Run LangGraph for reasoning/tool-use; persist state.
   - Materialize data via Dagster/Prefect; version artifacts.
4) Observe: emit traces/logs/metrics (success, latency, cost).
5) Verify: run checks (contracts, tests, evals). If failing → roll back or open human review.
6) Summarize: produce Domain Events + status report. Await next signal.

Tools (declare before use)
- db.query(sql|name, params) — read-only.
- kv.get/set(key, value, ttl)
- events.publish(topic, event_json)
- workflows.start(name, input), workflows.signal(id, msg)
- agents.run(graph, input, budget)
- data.run(job, config)
- eval.run(checklist|tests) — returns pass/fail + notes

Formatting
- Always respond with a short STATUS line + a machine-readable PLAN block (YAML) + any EVENTS emitted (JSON).
- Never include secrets or raw PII in output.
```

## 7‑day bootstrap plan

- Day 1: Set up directories, optional dev services via Docker; CI placeholders
- Day 2: Hello-world Temporal workflow + LangGraph echo agent + Dagster/Prefect heartbeat job
  (traces on)
- Day 3: Define 10–20 domain events (JSON Schema export) and shared SDK stubs
- Day 4: Wrap 5 high-value automations as Temporal activities + one multi-agent flow
- Day 5: Add policy guardrails (budgets, PII), audit logs, human-review gates
- Day 6: Backfill a small dataset with Dagster/Prefect; create a feature view; eval job
- Day 7: DR test (kill a worker), runbook, SLO/cost dashboards

## References

- Temporal — durable execution
- LangGraph (LangChain Academy) — LLM agent graphs
- Data orchestrators comparison — Prefect/Dagster/Airflow

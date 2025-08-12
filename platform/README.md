### Platform

This folder contains additive orchestration scaffolds and shared assets. It does not change the
running backend.

Fast start:

- `make -C platform up` to bring infra up
- `make -C platform schema` to export JSON schemas under `platform/shared/schemas/`
- `python platform/orchestration/langgraph_demo/app.py` to run the demo
- `python platform/orchestration/prefect_heartbeat/flow.py` to run the heartbeat
- See `platform/orchestration/temporal_worker/README.md` for worker usage

# Platform Spine

This folder holds additive scaffolding for a durable orchestration spine. It does not affect the
running backend.

Directories:

- `orchestration/` — Temporal workflows + LangGraph agent graphs (stubs)
- `data/` — Dagster/Prefect jobs (stubs)
- `shared/` — domain event schemas + tiny SDKs (Python/TS) + schema export

See `docs/ORCHESTRATION_SPINE.md` for the plan.

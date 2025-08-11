### Manager Orchestrator

Purpose: coordinate department tasks using the shared catalog for AI-to-AI scheduling.

Run idea:
- Read `platform/shared/catalog/tasks.json`
- Decide next task per department; emit a simple plan (JSON)
- Future: integrate Temporal to run multi-step workflows

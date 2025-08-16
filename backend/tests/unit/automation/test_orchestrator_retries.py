from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_run_dag_sets_status_and_handles_error(monkeypatch):
    # Patch skills registry to provide a failing step
    import app.automation.orchestrator as orch
    import app.automation.registry as reg
    import app.automation.state as st

    async def _ok(ctx):
        ctx = dict(ctx)
        ctx["a"] = 1
        return ctx

    async def _boom(ctx):  # noqa: ARG001
        raise RuntimeError("fail")

    monkeypatch.setattr(reg, "get_skill", lambda name: (_ok if name == "s1" else _boom))

    # Collect statuses in-memory
    statuses: list[tuple[str, dict]] = []

    async def _set_status(run_id: str, status: str, payload: dict):  # noqa: ARG001
        statuses.append((status, payload))

    # Patch the bound name imported in orchestrator module
    monkeypatch.setattr(orch, "set_status", _set_status)

    await orch.run_dag("r1", ["s1", "s2"], {"init": True})
    # should have transitioned to running then failed
    assert any(s == "running" for s, _ in statuses)
    assert any(s == "failed" for s, _ in statuses)



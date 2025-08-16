from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_run_dag_success_happy_path(monkeypatch):
    import app.automation.orchestrator as orch
    import app.automation.registry as reg

    async def s1(ctx):
        ctx = dict(ctx)
        ctx["s1"] = True
        return ctx

    async def s2(ctx):
        ctx = dict(ctx)
        ctx["s2"] = True
        return ctx

    # map skills on the imported symbol inside orchestrator
    monkeypatch.setattr(orch, "get_skill", lambda name: (s1 if name == "s1" else s2))

    statuses: list[tuple[str, dict]] = []

    async def _set_status(run_id: str, status: str, payload: dict):  # noqa: ARG001
        statuses.append((status, payload))

    monkeypatch.setattr(orch, "set_status", _set_status)

    await orch.run_dag("run-ok", ["s1", "s2"], {"init": True})

    # Should end in succeeded with both steps executed
    assert statuses and statuses[-1][0] == "succeeded"
    assert statuses[-1][1]["executed"] == ["s1", "s2"]
    assert statuses[-1][1]["result"]["s1"] is True and statuses[-1][1]["result"]["s2"] is True


@pytest.mark.asyncio
async def test_no_compensation_in_async_run_dag(monkeypatch):
    import app.automation.orchestrator as orch
    import app.automation.registry as reg

    async def s1(ctx):
        return {**ctx, "s1": True}

    async def s2(ctx):  # noqa: ARG001
        raise RuntimeError("boom")

    monkeypatch.setattr(orch, "get_skill", lambda name: (s1 if name == "s1" else s2))

    called: list[str] = []

    def _get_comp(step: str):  # pragma: no cover - trivial selection
        if step == "s1":
            def comp(ctx):  # noqa: ANN001
                called.append(f"comp:{step}")
            return comp
        return None

    monkeypatch.setattr(orch, "get_comp", _get_comp)

    async def _set_status(run_id: str, status: str, payload: dict):  # noqa: ARG001
        return None

    monkeypatch.setattr(orch, "set_status", _set_status)

    await orch.run_dag("run-fail", ["s1", "s2"], {"init": True})
    # async run_dag does not perform compensation (only the celery task does)
    assert called == []



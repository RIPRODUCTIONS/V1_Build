from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_state_write_and_list_recent(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://invalid:0/0")
    import app.automation.state as st

    await st.record_run_meta("rX", "intent.demo", {"k": 1})
    await st.set_status("rX", "running", {"step": 1})
    await st.set_status("rX", "succeeded", {"result": True})

    got = await st.get_status("rX")
    assert got["status"] == "succeeded"

    recent = await st.list_recent(limit=5)
    assert any(item["run_id"] == "rX" and item["status"] == "succeeded" for item in recent)



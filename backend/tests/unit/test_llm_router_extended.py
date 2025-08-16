import asyncio
from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.services.llm.router import LLMRouter, LLM_REQUEST_DURATION


class _OkProv:
    async def chat(self, prompt: str, system: str | None = None) -> str:  # noqa: ARG002
        await asyncio.sleep(0)
        return f"ok:{prompt}"


class _ErrProv:
    def __init__(self, times: int = 1) -> None:
        self.times = times

    async def chat(self, prompt: str, system: str | None = None) -> str:  # noqa: ARG002
        self.times -= 1
        raise RuntimeError("boom")


def _mk_settings(primary: str = "ollama", fallback: str = "lmstudio", retries: int = 1) -> Settings:
    s = Settings()
    s.LLM_PRIMARY = primary
    s.LLM_FALLBACK = fallback
    s.LLM_RETRIES = retries
    s.LLM_CB_FAIL_THRESHOLD = 1
    s.LLM_CB_RESET_S = 1
    return s


@pytest.mark.asyncio
async def test_llm_router_primary_ok(monkeypatch):
    s = _mk_settings(primary="ollama", fallback="none", retries=0)
    r = LLMRouter(s)
    monkeypatch.setattr(r, "primary", _OkProv())
    # Ensure the circuit is closed so primary is attempted
    monkeypatch.setattr(r, "cb_primary", SimpleNamespace(is_open=False, record_success=lambda: None, record_failure=lambda: None))
    out = await r.chat("hello")
    assert out.startswith("ok:")


@pytest.mark.asyncio
async def test_llm_router_primary_error_fallback_ok(monkeypatch):
    s = _mk_settings(primary="ollama", fallback="lmstudio", retries=0)
    r = LLMRouter(s)
    monkeypatch.setattr(r, "primary", _ErrProv())
    monkeypatch.setattr(r, "fallback", _OkProv())
    out = await r.chat("x")
    assert out.startswith("ok:")


@pytest.mark.asyncio
async def test_llm_router_all_fail_raises(monkeypatch):
    s = _mk_settings(primary="ollama", fallback="lmstudio", retries=0)
    r = LLMRouter(s)
    monkeypatch.setattr(r, "primary", _ErrProv())
    monkeypatch.setattr(r, "fallback", _ErrProv())
    with pytest.raises(RuntimeError):
        await r.chat("x")


def test_llm_request_duration_has_labels():
    # Ensure our patched observe accepts labels dict without raising
    # Use helper to avoid relying on internal prometheus structures
    from app.services.llm.router import _label_observe
    _label_observe(LLM_REQUEST_DURATION, 0.01, {"provider": "test", "outcome": "ok"})
    # If no exception is raised, behavior is acceptable for this unit test
    assert True



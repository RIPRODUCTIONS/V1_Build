# ruff: noqa: I001
import pytest

from app.core.config import Settings
from app.services.llm.router import LLMRouter


@pytest.mark.asyncio
async def test_router_constructs_with_fallback():
    s = Settings(LLM_PRIMARY="openai", LLM_FALLBACK="ollama")
    r = LLMRouter(s)
    assert r.fallback is not None


@pytest.mark.asyncio
async def test_cb_opens_and_fallback(monkeypatch):
    s = Settings(
        LLM_PRIMARY="openai", LLM_FALLBACK="ollama", LLM_RETRIES=0, LLM_CB_FAIL_THRESHOLD=1
    )
    r = LLMRouter(s)

    async def boom(prompt, system=None):
        raise RuntimeError("boom")

    r.primary.chat = boom  # type: ignore

    async def ok(prompt, system=None):
        return "fallback-ok"

    assert r.fallback is not None
    r.fallback.chat = ok  # type: ignore

    out = await r.chat("ping")
    assert out == "fallback-ok"

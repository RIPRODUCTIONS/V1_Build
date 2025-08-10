# ruff: noqa: I001
import asyncio

from app.core.config import Settings
from app.reliability.circuit_breaker import CircuitBreaker
from .providers.anthropic_p import AnthropicProvider
from .providers.openai_p import OpenAIProvider
from .providers.ollama_p import OllamaProvider


class LLMRouter:
    def __init__(self, settings: Settings):
        self.s = settings
        self.cb_primary = CircuitBreaker(settings.LLM_CB_FAIL_THRESHOLD, settings.LLM_CB_RESET_S)

        if self.s.LLM_PRIMARY == "openai":
            self.primary = OpenAIProvider(self.s)
        elif self.s.LLM_PRIMARY == "anthropic":
            self.primary = AnthropicProvider(self.s)
        else:
            raise ValueError("Unsupported LLM_PRIMARY")

        self.fallback = None
        if self.s.LLM_FALLBACK == "ollama":
            self.fallback = OllamaProvider(self.s)

    async def chat(self, prompt: str, system: str | None = None) -> str:
        if not self.cb_primary.is_open:
            for attempt in range(self.s.LLM_RETRIES + 1):
                try:
                    resp = await self.primary.chat(prompt, system)
                    self.cb_primary.record_success()
                    return resp
                except Exception:
                    if attempt >= self.s.LLM_RETRIES:
                        self.cb_primary.record_failure()
                    await asyncio.sleep(0.3 * (attempt + 1))

        if self.fallback:
            return await self.fallback.chat(prompt, system)

        raise RuntimeError("All LLM providers failed (no fallback or circuit open)")


_router_singleton: LLMRouter | None = None


def get_llm_router() -> LLMRouter:
    # Avoid global mutation warnings by using a module-level singleton variable
    if _router_singleton is None:
        # Initialize once
        router = LLMRouter(Settings())
        globals()["_router_singleton"] = router
        return router
    return _router_singleton  # type: ignore[return-value]

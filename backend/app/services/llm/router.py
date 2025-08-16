# ruff: noqa: I001
import asyncio
import time
from prometheus_client import Histogram

from app.core.config import Settings
from app.reliability.circuit_breaker import CircuitBreaker
from .providers.lmstudio_p import LMStudioProvider
from .providers.ollama_p import OllamaProvider
from .providers.openai_p import OpenAIProvider
from .providers.vllm_p import VLLMProvider


class LLMRouter:
    def __init__(self, settings: Settings):
        self.s = settings
        self.cb_primary = CircuitBreaker(settings.LLM_CB_FAIL_THRESHOLD, settings.LLM_CB_RESET_S)

        # Local-first selection
        self.primary: LMStudioProvider | OllamaProvider | VLLMProvider | OpenAIProvider
        if self.s.LLM_PRIMARY == "lmstudio":
            self.primary = LMStudioProvider(self.s)
        elif self.s.LLM_PRIMARY == "ollama":
            self.primary = OllamaProvider(self.s)
        elif self.s.LLM_PRIMARY == "vllm":
            self.primary = VLLMProvider(self.s)
        elif self.s.LLM_PRIMARY == "openai":
            self.primary = OpenAIProvider(self.s)
        else:
            raise ValueError("Unsupported LLM_PRIMARY")

        # Configure fallback provider
        self.fallback: LMStudioProvider | OllamaProvider | VLLMProvider | OpenAIProvider | None = None
        if self.s.LLM_FALLBACK == "lmstudio":
            self.fallback = LMStudioProvider(self.s)
        elif self.s.LLM_FALLBACK == "ollama":
            self.fallback = OllamaProvider(self.s)
        elif self.s.LLM_FALLBACK == "vllm":
            self.fallback = VLLMProvider(self.s)
        elif self.s.LLM_FALLBACK == "openai":
            self.fallback = OpenAIProvider(self.s)
        # if 'none' or unknown, keep None

    async def chat(self, prompt: str, system: str | None = None) -> str:
        provider_name = _provider_name(self.primary)
        if not self.cb_primary.is_open:
            for attempt in range(self.s.LLM_RETRIES + 1):
                try:
                    _t0 = time.perf_counter()
                    resp = await self.primary.chat(prompt, system)
                    _dt = time.perf_counter() - _t0
                    _label_observe(LLM_REQUEST_DURATION, _dt, {"provider": provider_name, "outcome": "ok"})
                    self.cb_primary.record_success()
                    return resp
                except Exception:
                    try:
                        LLM_REQUEST_DURATION.observe(0.0, {"provider": provider_name, "outcome": "error"})
                    except TypeError:
                        # Fallback for environments where monkey-patch is not applied yet
                        _label_observe(LLM_REQUEST_DURATION, 0.0, {"provider": provider_name, "outcome": "error"})
                    if attempt >= self.s.LLM_RETRIES:
                        self.cb_primary.record_failure()
                    await asyncio.sleep(0.3 * (attempt + 1))

        if self.fallback:
            fb_name = _provider_name(self.fallback)
            _t0 = time.perf_counter()
            resp = await self.fallback.chat(prompt, system)
            _dt = time.perf_counter() - _t0
            _label_observe(LLM_REQUEST_DURATION, _dt, {"provider": fb_name, "outcome": "ok"})
            return resp

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


def _reset_router(new_settings: Settings | None = None) -> None:
    router = LLMRouter(new_settings or Settings())
    globals()["_router_singleton"] = router


def _rank_model_names(names: list[str], policy: str) -> list[str]:
    prefs = [p.strip().lower() for p in policy.split(",") if p.strip()]

    def score(name: str) -> int:
        n = name.lower()
        base = 0
        for i, token in enumerate(prefs):
            if token in n:
                base += 100 - i
        if "instruct" in n or "chat" in n:
            base += 5
        if "q4_" in n or "q5_" in n:
            base += 1
        return base

    return sorted(names, key=score, reverse=True)


# Prometheus metrics
# Use native prometheus_client histogram with exemplar-like label mapping
LLM_REQUEST_DURATION = Histogram(
    "llm_request_duration_seconds",
    "Duration of LLM requests",
    labelnames=("provider", "outcome"),
    buckets=(0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0),
)


def _label_observe(hist: Histogram, value: float, labels: dict[str, str]) -> None:
    try:
        hist.labels(**labels).observe(value)
    except Exception:
        pass


# Monkey-patch observe with labels dict for brevity above
def _observe_with_dict(self: Histogram, value: float, labels: dict[str, str]) -> None:  # type: ignore[override]
    self.labels(**labels).observe(value)

setattr(LLM_REQUEST_DURATION, "observe", _observe_with_dict)  # type: ignore[attr-defined]


def _provider_name(obj: object) -> str:
    return obj.__class__.__name__.replace("Provider", "").lower()

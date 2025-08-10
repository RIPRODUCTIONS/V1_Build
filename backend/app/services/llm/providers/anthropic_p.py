# ruff: noqa: I001
from http import HTTPStatus

import aiohttp

from app.core.config import Settings


class AnthropicProvider:
    def __init__(self, settings: Settings):
        self.key = settings.ANTHROPIC_API_KEY
        self.model = settings.ANTHROPIC_MODEL
        self.timeout = settings.LLM_TIMEOUT_S

    async def chat(self, prompt: str, system: str | None = None) -> str:
        if not self.key:
            raise RuntimeError("ANTHROPIC_API_KEY missing")
        headers = {"x-api-key": self.key, "anthropic-version": "2023-06-01"}
        body = {
            "model": self.model,
            "max_tokens": 2048,
            "messages": ([{"role": "system", "content": system}] if system else [])
            + [{"role": "user", "content": prompt}],
        }
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with (
            aiohttp.ClientSession(timeout=timeout) as s,
            s.post("https://api.anthropic.com/v1/messages", json=body, headers=headers) as r,
        ):
            if r.status >= HTTPStatus.BAD_REQUEST:
                raise RuntimeError(f"Anthropic error {r.status}: {await r.text()}")
            data = await r.json()
            return "".join([c.get("text", "") for c in data["content"] if c.get("type") == "text"])

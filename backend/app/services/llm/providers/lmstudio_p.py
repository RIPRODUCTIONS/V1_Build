# ruff: noqa: I001
from http import HTTPStatus
import aiohttp
from app.core.config import Settings


class LMStudioProvider:
    def __init__(self, s: Settings):
        self.base = s.LMSTUDIO_BASE_URL.rstrip("/")
        self.model = s.LMSTUDIO_MODEL
        self.timeout = s.LLM_TIMEOUT_S

    async def chat(self, prompt: str, system: str | None = None) -> str:
        body = {
            "model": self.model,
            "messages": ([{"role": "system", "content": system}] if system else [])
            + [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with (
            aiohttp.ClientSession(timeout=timeout) as sess,
            sess.post(f"{self.base}/chat/completions", json=body) as r,
        ):
            if r.status >= HTTPStatus.BAD_REQUEST:
                raise RuntimeError(f"LMStudio error {r.status}: {await r.text()}")
            data = await r.json()
            return data["choices"][0]["message"]["content"]

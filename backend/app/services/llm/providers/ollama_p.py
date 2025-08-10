# ruff: noqa: I001
from http import HTTPStatus

import aiohttp

from app.core.config import Settings


class OllamaProvider:
    def __init__(self, settings: Settings):
        self.host = settings.OLLAMA_HOST.rstrip("/")
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.LLM_TIMEOUT_S

    async def chat(self, prompt: str, system: str | None = None) -> str:
        payload = {
            "model": self.model,
            "prompt": (f"<<SYS>>{system}\n<</SYS>>\n" if system else "") + prompt,
            "stream": False,
        }
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with (
            aiohttp.ClientSession(timeout=timeout) as s,
            s.post(f"{self.host}/api/generate", json=payload) as r,
        ):
            if r.status >= HTTPStatus.BAD_REQUEST:
                raise RuntimeError(f"Ollama error {r.status}: {await r.text()}")
            data = await r.json()
            return data.get("response", "")

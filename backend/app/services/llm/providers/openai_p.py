# ruff: noqa: I001
from http import HTTPStatus

import aiohttp

from app.core.config import Settings


class OpenAIProvider:
    def __init__(self, settings: Settings):
        self.key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.timeout = settings.LLM_TIMEOUT_S

    async def chat(self, prompt: str, system: str | None = None) -> str:
        if not self.key:
            raise RuntimeError('OPENAI_API_KEY missing')
        payload = {
            'model': self.model,
            'messages': ([{'role': 'system', 'content': system}] if system else [])
            + [{'role': 'user', 'content': prompt}],
            'temperature': 0.2,
        }
        headers = {'Authorization': f'Bearer {self.key}'}
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with (
            aiohttp.ClientSession(timeout=timeout) as s,
            s.post(
                'https://api.openai.com/v1/chat/completions', json=payload, headers=headers
            ) as r,
        ):
            if r.status >= HTTPStatus.BAD_REQUEST:
                raise RuntimeError(f'OpenAI error {r.status}: {await r.text()}')
            data = await r.json()
            return data['choices'][0]['message']['content']

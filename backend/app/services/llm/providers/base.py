from typing import Protocol


class LLMProvider(Protocol):
    async def chat(self, prompt: str, system: str | None = None) -> str: ...

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

Step = dict[str, Any]


class WorkflowEngine:
    def __init__(self, exec_step: Callable[[Step], Any], reflect: Callable[[Step, Any], Step] | None = None):
        self.exec_step = exec_step
        self.reflect = reflect

    async def run_sequential(self, steps: list[Step]) -> list[Any]:
        results: list[Any] = []
        for step in steps:
            result = await self.exec_step(step)
            if self.reflect is not None:
                # Store reflected step for potential future use
                _ = self.reflect(step, result)
            results.append(result)
        return results

    async def run_parallel(self, steps: list[Step], max_concurrency: int = 4) -> list[Any]:
        semaphore = asyncio.Semaphore(max_concurrency)

        async def _run(step: Step):
            async with semaphore:
                result = await self.exec_step(step)
                return self.reflect(step, result) if self.reflect is not None else result

        return await asyncio.gather(*[_run(s) for s in steps])





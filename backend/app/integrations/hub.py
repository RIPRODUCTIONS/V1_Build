from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import random
import time

from .base import IntegrationBase
import os
import logging


@dataclass(slots=True)
class IntegrationHub:
    integrations: Dict[str, IntegrationBase] = field(default_factory=dict)
    last_sync: Dict[str, float] = field(default_factory=dict)
    error_rate: Dict[str, float] = field(default_factory=dict)

    def register(self, key: str, integration: IntegrationBase) -> None:
        self.integrations[key] = integration

    async def auto_discover(self, user_id: str) -> List[str]:
        found: List[str] = []
        for key, integ in self.integrations.items():
            try:
                if await integ.discover(user_id):
                    found.append(key)
            except Exception:
                continue
        return found

    async def sync_all(self, user_id: str) -> Dict[str, dict]:
        results: Dict[str, dict] = {}
        async def _run(key: str, integ: IntegrationBase) -> None:
            try:
                start = time.perf_counter()
                results[key] = await integ.sync(user_id)
                self.last_sync[key] = time.time()
                dur = time.perf_counter() - start
                # naive rolling error metric demo
                self.error_rate[key] = max(0.0, self.error_rate.get(key, 0.0) * 0.9)
            except Exception:
                logging.getLogger(__name__).exception("Integration %s failed", key)
                results[key] = {"status": "error"}
                self.error_rate[key] = min(1.0, self.error_rate.get(key, 0.0) * 0.9 + 0.1)

        # Optionally register mock integration when enabled
        if os.getenv("MOCK_INTEGRATIONS", "false").lower() in {"1", "true", "yes"}:
            try:
                from .mock_provider import MockCalendarIntegration

                self.integrations.setdefault("mock_calendar", MockCalendarIntegration())
            except Exception:
                pass

        await asyncio.gather(*[_run(k, v) for k, v in list(self.integrations.items())])
        return results

    async def poll_with_backoff(self, user_id: str, key: str, base_delay: float = 30.0, max_delay: float = 300.0) -> Optional[dict]:
        integ = self.integrations.get(key)
        if not integ:
            return None
        delay = base_delay
        while True:
            try:
                return await integ.sync(user_id)
            except Exception:
                jitter = random.uniform(0, delay * 0.1)
                await asyncio.sleep(min(max_delay, delay + jitter))
                delay = min(max_delay, delay * 2)




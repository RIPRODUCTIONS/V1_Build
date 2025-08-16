import asyncio
import logging
import os
from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)

ENABLE_SCHEDULER = os.environ.get("ENABLE_SCHEDULER") == "1"


class Scheduler:
    def __init__(self):
        self._tasks: list[asyncio.Task] = []

    def every(self, seconds: int, job: Callable[[], Awaitable[None]]):
        async def runner():
            await asyncio.sleep(1)
            while True:
                try:
                    await job()
                except Exception as e:
                    logger.warning(f"Scheduled job failed: {e}")
                await asyncio.sleep(seconds)

        self._tasks.append(asyncio.create_task(runner()))

    async def stop(self):
        for t in self._tasks:
            t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)






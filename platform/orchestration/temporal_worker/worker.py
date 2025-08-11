from __future__ import annotations

import asyncio
import os

from temporalio.client import Client
from temporalio.worker import Worker

from .activities import heartbeat_activity
from .workflows import HelloWorkflow


async def main() -> None:
    address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
    client = await Client.connect(address)
    task_queue = os.getenv("TEMPORAL_TASK_QUEUE", "demo-task-queue")
    async with Worker(
        client,
        task_queue=task_queue,
        workflows=[HelloWorkflow],
        activities=[heartbeat_activity],
    ):
        print(f"worker started on {task_queue} against {address}")
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())

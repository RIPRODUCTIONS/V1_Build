#!/usr/bin/env python3
import os
import sys
import asyncio
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

logging.basicConfig(level=logging.INFO)

async def main() -> None:
    from app.automations.consumer import StreamConsumer
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    consumer = StreamConsumer(redis_url=redis_url, stream_key=os.getenv("AUTOMATION_EVENT_STREAM", "automation:events"))
    await consumer.start()

if __name__ == "__main__":
    print("Starting consumer...")
    asyncio.run(main())



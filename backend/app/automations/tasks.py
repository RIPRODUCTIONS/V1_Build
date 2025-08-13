from __future__ import annotations

import asyncio
import os

from celery import shared_task

from app.automations.consumer import StreamConsumer
from app.automations.metrics import automation_rule_executions, automation_rule_latency


@shared_task(bind=True, name="automations.consume_event_stream", max_retries=0)
def consume_event_stream(self):
    """Run the Redis Streams consumer in a thread-compatible loop."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    async def _main():
        consumer = StreamConsumer(redis_url)
        await consumer.run()
    asyncio.run(_main())


@shared_task(name="automations.evaluate_rules_for_event")
def evaluate_rules_for_event(event_data: dict):
    from app.db import SessionLocal
    from app.automations.rules_engine import RuleEngine

    db = SessionLocal()
    try:
        engine = RuleEngine(db)
        import asyncio

        results = asyncio.run(engine.evaluate_event(event_data))
        return results
    finally:
        db.close()



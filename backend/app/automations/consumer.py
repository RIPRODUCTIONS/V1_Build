from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

import redis

logger = logging.getLogger(__name__)


STREAM_KEY = os.getenv("AUTOMATION_EVENT_STREAM", "automation:events")
GROUP = os.getenv("AUTOMATION_CONSUMER_GROUP", "automation-workers")
CONSUMER_NAME = os.getenv("HOSTNAME", "worker-1")


class StreamConsumer:
    def __init__(self, redis_url: str, stream_key: str | None = None, consumer_group: str | None = None, consumer_name: str | None = None) -> None:
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.stream_key = stream_key or STREAM_KEY
        self.consumer_group = consumer_group or GROUP
        self.consumer_name = consumer_name or CONSUMER_NAME
        self.running = True

        # Ensure consumer group exists
        try:
            self.redis_client.xgroup_create(self.stream_key, self.consumer_group, id="0", mkstream=True)
            logger.info("Created consumer group %s on %s", self.consumer_group, self.stream_key)
        except redis.ResponseError as e:  # type: ignore[attr-defined]
            if "BUSYGROUP" not in str(e):
                raise
            logger.info("Consumer group %s already exists", self.consumer_group)

    async def start(self) -> None:
        logger.info("Starting consumer on %s", self.stream_key)
        while self.running:
            try:
                messages = self.redis_client.xreadgroup(
                    self.consumer_group,
                    self.consumer_name,
                    {self.stream_key: ">"},
                    count=10,
                    block=1000,
                )
                if not messages:
                    continue
                for _stream, stream_messages in messages:
                    for message_id, data in stream_messages:
                        await self.process_message(message_id, data)
            except Exception as e:  # pragma: no cover
                logger.error("Consumer error: %s", e)
                await asyncio.sleep(5)

    async def process_message(self, message_id: str, data: dict) -> None:
        try:
            logger.info("Processing %s: %s", message_id, data)
            event_json = data.get("e", "{}")
            event_data = json.loads(event_json) if isinstance(event_json, str) else event_json
            logger.info("Parsed event: %s", event_data)

            # Evaluate rules synchronously
            from app.automations.tasks import evaluate_rules_for_event

            result = evaluate_rules_for_event(event_data)
            logger.info("Engine result: %s", result)
            self.redis_client.xack(self.stream_key, self.consumer_group, message_id)
            logger.info("Processed %s: %s", message_id, result)
        except Exception as e:  # pragma: no cover
            logger.error("Failed %s: %s", message_id, e)

    # Back-compat shim and manual control helpers
    async def run(self) -> None:  # pragma: no cover
        await self.start()

    def stop(self) -> None:
        self.running = False



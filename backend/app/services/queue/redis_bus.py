"""
Redis Event Bus Implementation

This module provides a Redis-based event bus for asynchronous messaging.
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


class RedisEventBus:
    """Redis-based event bus for publishing and consuming events."""

    def __init__(self, stream: str, redis_client=None):
        """
        Initialize the Redis event bus.

        Args:
            stream: Redis stream name for events
            redis_client: Redis client instance (optional)
        """
        self.stream = stream
        self._client = redis_client
        self._ensure_client()

    def _ensure_client(self):
        """Ensure Redis client is available."""
        if self._client is None:
            try:
                import redis
                self._client = redis.Redis(host='localhost', port=6379, db=0)
            except ImportError:
                logger.warning("Redis not available, using mock client")
                self._client = MockRedisClient()

    def publish(self, event_data: dict[str, Any]) -> str:
        """
        Publish an event to the Redis stream.

        Args:
            event_data: Event data to publish

        Returns:
            Message ID of the published event
        """
        try:
            # Add timestamp to event data
            event_with_timestamp = {
                **event_data,
                "timestamp": datetime.now(UTC).isoformat(),
                "stream": self.stream
            }

            # Convert to string format for Redis
            fields = {k: json.dumps(v) if not isinstance(v, str) else v
                     for k, v in event_with_timestamp.items()}

            # Publish to Redis stream
            message_id = self._client.xadd(self.stream, fields)
            logger.info(f"Published event to stream {self.stream}: {message_id}")
            return str(message_id)

        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            raise

    def consume(self, group: str, consumer: str, count: int = 10, block: int = 5000):
        """
        Consume events from the Redis stream.

        Args:
            group: Consumer group name
            consumer: Consumer name
            count: Maximum number of messages to read
            block: Block time in milliseconds

        Yields:
            Event data and message ID
        """
        try:
            # Read from stream
            messages = self._client.xreadgroup(
                group, consumer, {self.stream: ">"},
                count=count, block=block
            )

            for _stream, stream_messages in messages:
                for message_id, fields in stream_messages:
                    try:
                        # Parse event data
                        event_data = {}
                        for field, value in fields.items():
                            if isinstance(value, bytes):
                                value = value.decode('utf-8')
                            try:
                                event_data[field.decode('utf-8') if isinstance(field, bytes) else field] = json.loads(value)
                            except json.JSONDecodeError:
                                event_data[field.decode('utf-8') if isinstance(field, bytes) else field] = value

                        yield message_id, event_data

                    except Exception as e:
                        logger.error(f"Failed to parse message {message_id}: {e}")

        except Exception as e:
            logger.error(f"Failed to consume events: {e}")
            raise

    def create_consumer_group(self, group: str, start_id: str = "0"):
        """
        Create a consumer group for the stream.

        Args:
            group: Consumer group name
            start_id: Starting message ID
        """
        try:
            self._client.xgroup_create(self.stream, group, start_id, mkstream=True)
            logger.info(f"Created consumer group {group} for stream {self.stream}")
        except Exception as e:
            logger.warning(f"Consumer group {group} may already exist: {e}")

    def ack_message(self, group: str, message_id: str):
        """
        Acknowledge a message in the consumer group.

        Args:
            group: Consumer group name
            message_id: Message ID to acknowledge
        """
        try:
            self._client.xack(self.stream, group, message_id)
            logger.debug(f"Acknowledged message {message_id} in group {group}")
        except Exception as e:
            logger.error(f"Failed to acknowledge message {message_id}: {e}")


class MockRedisClient:
    """Mock Redis client for testing when Redis is not available."""

    def __init__(self):
        self.streams = {}
        self.message_counter = 0

    def xadd(self, stream: str, fields: dict[str, Any]) -> str:
        """Mock xadd operation."""
        if stream not in self.streams:
            self.streams[stream] = []

        self.message_counter += 1
        message_id = f"{self.message_counter}-0"

        self.streams[stream].append((message_id, fields))
        return message_id

    def xreadgroup(self, group: str, consumer: str, streams: dict[str, str],
                   count: int = 10, block: int = 5000):
        """Mock xreadgroup operation."""
        # Return empty results for mock
        return []

    def xgroup_create(self, stream: str, group: str, start_id: str, mkstream: bool = False):
        """Mock xgroup_create operation."""
        pass

    def xack(self, stream: str, group: str, message_id: str):
        """Mock xack operation."""
        pass

from __future__ import annotations

import hashlib
import json
import os
import time
from collections import defaultdict, deque
from contextlib import suppress
from typing import Any

from app.core.config import get_settings
from app.services.queue.redis_client import get_redis

try:  # optional dependency
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore

# --- In-memory fallback -------------------------------------------------------


class InMemoryBus:
    """Tiny, process-local event bus used when Redis is unavailable."""

    def __init__(self) -> None:
        self._events: defaultdict[str, deque[dict]] = defaultdict(deque)

    def emit(self, topic: str, payload: dict) -> None:
        self._events[topic].append(payload)

    def drain(self, topic: str, max_items: int = 100) -> list[dict]:
        out: list[dict] = []
        q = self._events[topic]
        while q and len(out) < max_items:
            out.append(q.popleft())
        return out


# --- Factory that returns RedisBus when possible ------------------------------


def get_bus():
    """Return the real Redis bus if reachable, otherwise an in-memory bus."""
    r = get_redis()
    if r is None:
        return InMemoryBus()
    # For now, return in-memory bus since we don't have RedisBus class
    return InMemoryBus()


class RedisEventBus:
    """Redis Streams publisher with idempotency guards, DLQ, and consumer group management."""

    def __init__(
        self,
        stream: str = 'events',
        dlq_stream: str = 'automation.dlq',
        consumer_group: str = 'default_group',
    ) -> None:
        self.stream = stream
        self.dlq_stream = dlq_stream
        self.consumer_group = consumer_group
        self._client = None
        url = os.getenv('REDIS_URL', get_settings().REDIS_URL)
        if get_redis() is not None and url:
            with suppress(Exception):
                self._client = redis.Redis.from_url(url, decode_responses=True)
                self._setup_streams()

    def _setup_streams(self) -> None:
        """Setup streams and consumer groups."""
        try:
            # Create main stream if it doesn't exist
            self._client.xadd(self.stream, {'data': 'init'}, maxlen=1, approximate=True)

            # Create DLQ stream if it doesn't exist
            self._client.xadd(self.dlq_stream, {'data': 'init'}, maxlen=1, approximate=True)

            # Setup consumer group for main stream
            try:
                self._client.xgroup_create(self.stream, self.consumer_group, id='0', mkstream=True)
            except redis.ResponseError as e:
                if 'BUSYGROUP' not in str(e):
                    raise

            # Setup consumer group for DLQ
            try:
                self._client.xgroup_create(
                    self.dlq_stream, f'{self.consumer_group}_dlq', id='0', mkstream=True
                )
            except redis.ResponseError as e:
                if 'BUSYGROUP' not in str(e):
                    raise

        except Exception as e:
            print(f'Failed to setup Redis streams: {e}')

    def _generate_idempotency_key(self, event: dict[str, Any]) -> str:
        """Generate idempotency key from event data."""
        # Create a hash from correlation_id and event type
        correlation_id = event.get('correlation_id', 'unknown')
        event_type = event.get('event_type', 'unknown')

        # For events with steps, include step hash
        if 'step_hash' in event:
            step_hash = event['step_hash']
        else:
            # Generate step hash from intent and department
            intent = event.get('intent', '')
            department = event.get('department', '')
            step_hash = hashlib.md5(f'{intent}:{department}'.encode()).hexdigest()

        return f'{correlation_id}:{event_type}:{step_hash}'

    def _check_idempotency(self, idempotency_key: str, ttl_seconds: int = 3600) -> bool:
        """Check if event has already been processed."""
        if not self._client:
            return False

        key = f'idempotency:{idempotency_key}'
        try:
            if hasattr(self._client, 'set'):
                result = self._client.set(key, '1', ex=ttl_seconds, nx=True)
                return bool(result)
            if hasattr(self._client, 'setex'):
                # emulate NX by using a get before setex
                if getattr(self._client, 'get', None) and self._client.get(key):
                    return False
                self._client.setex(key, ttl_seconds, '1')
                return True
        except Exception:
            pass

        # Fallback: in-memory seen set for tests/fakes
        seen = getattr(self, '_seen_keys', None)
        if seen is None:
            seen = set()
            self._seen_keys = seen
        if key in seen:
            return False
        seen.add(key)
        return True

    def publish(
        self,
        event: dict[str, Any],
        max_retries: int = 3,
        enable_idempotency: bool = True,
        idempotency_ttl: int = 3600,
    ) -> str | None:
        """Publish event to Redis Stream with idempotency guard."""
        if not self._client:
            return None

        # Check idempotency if enabled
        if enable_idempotency:
            idempotency_key = self._generate_idempotency_key(event)
            if not self._check_idempotency(idempotency_key, idempotency_ttl):
                print(f'Event already processed (idempotency key: {idempotency_key})')
                return None

        payload = json.dumps(event)
        last_err: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                # Add event to main stream
                message_id = self._client.xadd(
                    self.stream, {'data': payload, 'timestamp': time.time()}
                )
                print(f'Published event {event.get("event_type", "unknown")} with ID: {message_id}')
                return message_id

            except Exception as err:  # noqa: BLE001
                last_err = err
                if attempt < max_retries:
                    time.sleep(min(0.5 * (2**attempt), 2.0))
                else:
                    # Move to DLQ on final failure
                    self._publish_to_dlq(event, str(err))
                    raise RuntimeError(f'failed to publish after retries: {last_err}') from err

    def _publish_to_dlq(self, event: dict[str, Any], error: str) -> None:
        """Publish failed event to Dead Letter Queue."""
        if not self._client:
            return

        try:
            dlq_event = {
                **event,
                'dlq_error': error,
                'dlq_timestamp': time.time(),
                'original_stream': self.stream,
            }

            dlq_payload = json.dumps(dlq_event)
            self._client.xadd(self.dlq_stream, {'data': dlq_payload})
            print(f'Event moved to DLQ: {event.get("event_type", "unknown")} - Error: {error}')

        except Exception as e:
            print(f'Failed to publish to DLQ: {e}')

    def consume_events(
        self, consumer_name: str, count: int = 10, block_ms: int = 5000
    ) -> list[tuple[str, dict[str, Any]]]:
        """Consume events from stream with consumer group."""
        if not self._client:
            return []

        try:
            # Read pending messages first
            pending = self._client.xpending(self.stream, self.consumer_group, '-', '+', count)
            if pending and pending[0] > 0:
                # Process pending messages
                messages = self._client.xreadgroup(
                    self.consumer_group, consumer_name, {self.stream: '0'}, count=count
                )
            else:
                # Read new messages
                messages = self._client.xreadgroup(
                    self.consumer_group,
                    consumer_name,
                    {self.stream: '>'},
                    count=count,
                    block=block_ms,
                )

            events = []
            for _stream, stream_messages in messages:
                for message_id, fields in stream_messages:
                    try:
                        data = json.loads(fields['data'])
                        events.append((message_id, data))
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f'Failed to parse message {message_id}: {e}')
                        # Move malformed message to DLQ
                        self._publish_to_dlq({'raw_message': fields}, f'Parse error: {e}')

            return events

        except Exception as e:
            print(f'Failed to consume events: {e}')
            return []

    def acknowledge_event(self, message_id: str) -> bool:
        """Acknowledge successful processing of an event."""
        if not self._client:
            return False

        try:
            self._client.xack(self.stream, self.consumer_group, message_id)
            return True
        except Exception as e:
            print(f'Failed to acknowledge message {message_id}: {e}')
            return False

    def get_stream_info(self) -> dict[str, Any]:
        """Get information about streams and consumer groups."""
        if not self._client:
            return {}

        try:
            info = {}

            # Main stream info
            info['main_stream'] = {
                'length': self._client.xlen(self.stream),
                'groups': self._client.xinfo_groups(self.stream),
            }

            # DLQ stream info
            info['dlq_stream'] = {
                'length': self._client.xlen(self.dlq_stream),
                'groups': self._client.xinfo_groups(self.dlq_stream),
            }

            # Consumer group info
            try:
                info['consumer_group'] = self._client.xinfo_consumers(
                    self.stream, self.consumer_group
                )
            except Exception:
                info['consumer_group'] = []

            return info

        except Exception as e:
            print(f'Failed to get stream info: {e}')
            return {}

    def clear_dlq(self, max_messages: int = 100) -> int:
        """Clear messages from DLQ (for testing/recovery)."""
        if not self._client:
            return 0

        try:
            # Get DLQ messages
            messages = self._client.xread({self.dlq_stream: '0'}, count=max_messages)
            cleared_count = 0

            for _stream, stream_messages in messages:
                for message_id, _fields in stream_messages:
                    try:
                        self._client.xdel(self.dlq_stream, message_id)
                        cleared_count += 1
                    except Exception as e:
                        print(f'Failed to delete DLQ message {message_id}: {e}')

            return cleared_count

        except Exception as e:
            print(f'Failed to clear DLQ: {e}')
            return 0

    def reprocess_dlq_message(self, message_id: str) -> bool:
        """Reprocess a specific message from DLQ."""
        if not self._client:
            return False

        try:
            # Get message from DLQ
            messages = self._client.xread({self.dlq_stream: '0'}, count=1)

            for _stream, stream_messages in messages:
                for msg_id, fields in stream_messages:
                    if msg_id == message_id:
                        try:
                            data = json.loads(fields['data'])
                            # Remove DLQ-specific fields
                            original_event = {
                                k: v for k, v in data.items() if not k.startswith('dlq_')
                            }

                            # Publish back to main stream
                            self.publish(original_event, enable_idempotency=False)

                            # Remove from DLQ
                            self._client.xdel(self.dlq_stream, message_id)

                            print(f'Reprocessed DLQ message {message_id}')
                            return True

                        except Exception as e:
                            print(f'Failed to reprocess DLQ message {message_id}: {e}')
                            return False

            print(f'Message {message_id} not found in DLQ')
            return False

        except Exception as e:
            print(f'Failed to reprocess DLQ message: {e}')
            return False

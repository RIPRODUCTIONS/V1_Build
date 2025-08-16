from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from enum import Enum

import redis.asyncio as redis
import structlog

from .agent_registry import AgentDomain

logger = structlog.get_logger()


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: int = 60
    success_threshold: int = 3
    timeout_seconds: int = 30


class BackpressureManager:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.circuit_breakers: dict[str, CircuitBreakerConfig] = {}
        self.circuit_states: dict[str, CircuitState] = {}
        self.failure_counts: dict[str, int] = {}
        self.last_failure_time: dict[str, float] = {}
        self.success_counts: dict[str, int] = {}

    def register_circuit_breaker(self, service_name: str, config: CircuitBreakerConfig):
        self.circuit_breakers[service_name] = config
        self.circuit_states[service_name] = CircuitState.CLOSED
        self.failure_counts[service_name] = 0
        self.success_counts[service_name] = 0

    async def execute_with_circuit_breaker(self, service_name: str, operation):
        if service_name not in self.circuit_breakers:
            return await operation()
        config = self.circuit_breakers[service_name]
        state = self.circuit_states[service_name]
        if state == CircuitState.OPEN:
            if time.time() - self.last_failure_time.get(service_name, 0) > config.recovery_timeout:
                self.circuit_states[service_name] = CircuitState.HALF_OPEN
                self.success_counts[service_name] = 0
            else:
                raise Exception(f"Circuit breaker OPEN for {service_name}")
        try:
            result = await asyncio.wait_for(operation(), timeout=config.timeout_seconds)
            await self.record_success(service_name)
            return result
        except Exception:
            await self.record_failure(service_name)
            raise

    async def record_success(self, service_name: str):
        cfg = self.circuit_breakers[service_name]
        state = self.circuit_states[service_name]
        if state == CircuitState.HALF_OPEN:
            self.success_counts[service_name] += 1
            if self.success_counts[service_name] >= cfg.success_threshold:
                self.circuit_states[service_name] = CircuitState.CLOSED
                self.failure_counts[service_name] = 0
                logger.info("circuit_closed", service=service_name)
        elif state == CircuitState.CLOSED:
            self.failure_counts[service_name] = 0

    async def record_failure(self, service_name: str):
        cfg = self.circuit_breakers[service_name]
        state = self.circuit_states[service_name]
        self.failure_counts[service_name] = self.failure_counts.get(service_name, 0) + 1
        self.last_failure_time[service_name] = time.time()
        if state in (CircuitState.CLOSED, CircuitState.HALF_OPEN) and self.failure_counts[service_name] >= cfg.failure_threshold:
            self.circuit_states[service_name] = CircuitState.OPEN
            logger.warning("circuit_open", service=service_name)

    async def get_queue_depth(self, domain: AgentDomain) -> int:
        total = 0
        for p in range(1, 11):
            key = f"queue:default:{domain.value}_queue:p{p}"
            total += await self.redis.zcard(key)
        return total

    async def check_queue_backpressure(self, domain: AgentDomain, max_depth: int = 1000) -> bool:
        current = await self.get_queue_depth(domain)
        if current > max_depth:
            logger.warning("backpressure", domain=domain.value, depth=current, max=max_depth)
            return True
        return False








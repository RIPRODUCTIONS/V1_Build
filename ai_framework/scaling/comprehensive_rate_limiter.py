from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum

import redis.asyncio as redis

from .enhanced_metrics import MetricsCollector


class LimitType(str, Enum):
    AGENT_HOURLY = "agent_hourly"
    TENANT_HOURLY = "tenant_hourly"
    DOMAIN_HOURLY = "domain_hourly"
    API_ENDPOINT = "api_endpoint"
    WEBHOOK_ENDPOINT = "webhook_endpoint"


@dataclass
class RateLimit:
    limit: int
    window_seconds: int
    burst_allowance: int = 0


class ComprehensiveRateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.default_limits: dict[LimitType, RateLimit] = {
            LimitType.AGENT_HOURLY: RateLimit(100, 3600, 10),
            LimitType.TENANT_HOURLY: RateLimit(10000, 3600, 100),
            LimitType.DOMAIN_HOURLY: RateLimit(5000, 3600, 50),
            LimitType.API_ENDPOINT: RateLimit(1000, 3600, 20),
            LimitType.WEBHOOK_ENDPOINT: RateLimit(500, 3600, 10),
        }
        self.tenant_limits: dict[str, dict[LimitType, RateLimit]] = {}

    def get_rate_limit_key(self, limit_type: LimitType, identifier: str) -> str:
        window = int(time.time() // self.default_limits[limit_type].window_seconds)
        return f"rate_limit:{limit_type.value}:{identifier}:{window}"

    async def check_rate_limit(self, limit_type: LimitType, identifier: str, tenant_id: str = "default") -> bool:
        rl = self.get_rate_limit(limit_type, tenant_id)
        key = self.get_rate_limit_key(limit_type, identifier)
        current_raw: bytes | None = await self.redis.get(key)
        current = int(current_raw) if current_raw else 0
        effective = rl.limit + rl.burst_allowance
        if current >= effective:
            MetricsCollector.record_rate_limit_hit(tenant_id, "unknown", identifier, limit_type.value)
            return False
        await self.redis.incr(key)
        await self.redis.expire(key, rl.window_seconds)
        return True

    def get_rate_limit(self, limit_type: LimitType, tenant_id: str) -> RateLimit:
        return self.tenant_limits.get(tenant_id, {}).get(limit_type, self.default_limits[limit_type])

    async def set_tenant_rate_limit(self, tenant_id: str, limit_type: LimitType, rate_limit: RateLimit):
        self.tenant_limits.setdefault(tenant_id, {})[limit_type] = rate_limit

    async def get_current_usage(self, limit_type: LimitType, identifier: str) -> dict[str, int]:
        key = self.get_rate_limit_key(limit_type, identifier)
        current_raw: bytes | None = await self.redis.get(key)
        current = int(current_raw) if current_raw else 0
        rl = self.default_limits[limit_type]
        return {
            "current_count": current,
            "limit": rl.limit,
            "window_seconds": rl.window_seconds,
            "remaining": max(0, rl.limit - current),
            "reset_time": int(time.time()) + rl.window_seconds,
        }








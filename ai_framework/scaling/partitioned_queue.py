from __future__ import annotations

import json
from dataclasses import dataclass

import redis.asyncio as redis

from .agent_registry import AgentDomain


@dataclass
class QueuePartition:
    domain: AgentDomain
    queue_name: str
    priority_levels: int = 10
    max_size: int = 10000
    worker_count: int = 5


class PartitionedQueueManager:
    def __init__(self, redis_client: redis.Redis, tenant_id: str = "default"):
        self.redis = redis_client
        self.tenant_id = tenant_id
        self.partitions: dict[AgentDomain, QueuePartition] = {}
        self.setup_partitions()

    def setup_partitions(self):
        self.partitions = {
            AgentDomain.RESEARCH: QueuePartition(AgentDomain.RESEARCH, "research_queue", worker_count=8, max_size=15000),
            AgentDomain.MARKETING: QueuePartition(AgentDomain.MARKETING, "marketing_queue", worker_count=12, max_size=20000),
            AgentDomain.SALES: QueuePartition(AgentDomain.SALES, "sales_queue", worker_count=12, max_size=20000),
            AgentDomain.FINANCE: QueuePartition(AgentDomain.FINANCE, "finance_queue", worker_count=6, max_size=10000),
            AgentDomain.OPERATIONS: QueuePartition(AgentDomain.OPERATIONS, "operations_queue", worker_count=4, max_size=8000),
            AgentDomain.ANALYTICS: QueuePartition(AgentDomain.ANALYTICS, "analytics_queue", worker_count=4, max_size=8000),
        }

    def get_queue_key(self, domain: AgentDomain, priority: int = 5) -> str:
        partition = self.partitions[domain]
        return f"queue:{self.tenant_id}:{partition.queue_name}:p{priority}"

    def get_dlq_key(self, domain: AgentDomain) -> str:
        partition = self.partitions[domain]
        return f"dlq:{self.tenant_id}:{partition.queue_name}"

    async def enqueue_task(self, task_data: dict, domain: AgentDomain, priority: int = 5):
        queue_key = self.get_queue_key(domain, priority)
        current_size = await self.redis.zcard(queue_key)
        max_size = self.partitions[domain].max_size
        if current_size >= max_size:
            raise Exception(f"Queue {domain} at capacity ({current_size}/{max_size})")
        task_json = json.dumps(task_data)
        await self.redis.zadd(queue_key, {task_json: float(priority)})

    async def get_queue_depths(self) -> dict[AgentDomain, int]:
        depths: dict[AgentDomain, int] = {}
        for domain in self.partitions:
            total = 0
            for p in range(1, 11):
                total += await self.redis.zcard(self.get_queue_key(domain, p))
            depths[domain] = total
        return depths








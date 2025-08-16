from __future__ import annotations

import asyncio
import time
import uuid
from datetime import datetime

try:
    import structlog  # type: ignore
    _logger = structlog.get_logger()
except Exception:
    import logging
    logging.basicConfig(level=logging.INFO)
    _logger = logging.getLogger(__name__)

from .agent_registry import AgentCapability, AgentDomain, AgentRegistry
from .enhanced_metrics import MetricsCollector
from .partitioned_queue import PartitionedQueueManager

logger = _logger


class ContinuousTaskSeeder:
    def __init__(self, queue_manager: PartitionedQueueManager, agent_registry: AgentRegistry):
        self.queue_manager = queue_manager
        self.agent_registry = agent_registry
        self.running = False
        self.seed_schedules: dict[str, dict] = {}
        self.setup_seed_schedules()

    def setup_seed_schedules(self):
        self.seed_schedules = {
            "market_research_continuous": {
                "domain": AgentDomain.RESEARCH,
                "capability": AgentCapability.MARKET_RESEARCH,
                "interval_seconds": 300,
                "batch_size": 10,
                "priority": 8,
                "template": {
                    "action": "market_research",
                    "targets": ["competitors", "industry_trends", "pricing_analysis"],
                    "depth": "standard",
                },
            },
            "content_generation_continuous": {
                "domain": AgentDomain.MARKETING,
                "capability": AgentCapability.CONTENT_CREATION,
                "interval_seconds": 180,
                "batch_size": 15,
                "priority": 7,
                "template": {
                    "action": "content_creation",
                    "content_types": ["blog_posts", "social_media", "email_templates"],
                    "optimization": "seo_focused",
                },
            },
            "lead_qualification_continuous": {
                "domain": AgentDomain.SALES,
                "capability": AgentCapability.LEAD_QUALIFICATION,
                "interval_seconds": 120,
                "batch_size": 20,
                "priority": 9,
                "template": {
                    "action": "lead_qualification",
                    "sources": ["web_forms", "cold_outreach", "referrals"],
                    "scoring_criteria": "comprehensive",
                },
            },
        }

    async def start_continuous_seeding(self):
        self.running = True
        tasks = [asyncio.create_task(self._schedule_loop(name, cfg)) for name, cfg in self.seed_schedules.items()]
        try:
            await asyncio.gather(*tasks)
        finally:
            self.running = False

    async def _schedule_loop(self, schedule_name: str, config: dict):
        while self.running:
            try:
                created = await self._generate_batch(schedule_name, config)
                logger.info("seed_batch", schedule=schedule_name, created=created)
                await asyncio.sleep(config["interval_seconds"])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("seed_error", schedule=schedule_name, error=str(e))
                await asyncio.sleep(60)

    async def _generate_batch(self, schedule_name: str, config: dict) -> int:
        domain: AgentDomain = config["domain"]
        capability: AgentCapability = config["capability"]
        batch_size: int = config["batch_size"]
        priority: int = config["priority"]
        template: dict = config["template"]

        agents = self.agent_registry.get_agents_by_capability(capability)
        if not agents:
            return 0

        depths = await self.queue_manager.get_queue_depths()
        current_depth = depths.get(domain, 0)
        max_depth = self.queue_manager.partitions[domain].max_size
        if current_depth > max_depth * 0.8:
            batch_size = max(1, batch_size // 2)

        created = 0
        batch_id = f"{schedule_name}_{int(time.time())}"
        for i in range(batch_size):
            agent = agents[i % len(agents)]
            task = {
                "task_id": str(uuid.uuid4()),
                "agent_id": agent.agent_id,
                "schedule_name": schedule_name,
                "created_at": datetime.utcnow().isoformat(),
                "priority": priority,
                "max_retries": agent.retry_attempts,
                "timeout_seconds": agent.timeout_seconds,
                **template,
                "batch_id": batch_id,
                "task_index": i,
            }
            try:
                await self.queue_manager.enqueue_task(task, domain, priority)
                created += 1
                MetricsCollector.record_task_completion("default", domain.value, agent.agent_id, 0.0, "created")
            except Exception as e:
                logger.error("enqueue_failed", error=str(e), task_id=task["task_id"])
        return created

    async def stop(self):
        self.running = False



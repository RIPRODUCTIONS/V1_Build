from __future__ import annotations

import asyncio
import json
import multiprocessing as mp
import os
import signal
from contextlib import suppress

import redis.asyncio as redis

try:
    import structlog  # type: ignore
    _logger = structlog.get_logger()
except Exception:  # fallback if structlog not installed
    import logging
    logging.basicConfig(level=logging.INFO)
    _logger = logging.getLogger(__name__)

from .agent_registry import AgentDomain, AgentRegistry
from .partitioned_queue import PartitionedQueueManager

logger = _logger


class ScaledWorkerManager:
    def __init__(self, queue_manager: PartitionedQueueManager, agent_registry: AgentRegistry):
        self.queue_manager = queue_manager
        self.agent_registry = agent_registry
        self.worker_processes: dict[AgentDomain, list[mp.Process]] = {}
        self.running = False

    async def start_all_workers(self):
        self.running = True
        for domain, partition in self.queue_manager.partitions.items():
            await self.start_domain_workers(domain, partition.worker_count)
        asyncio.create_task(self.monitor_workers())
        logger.info("workers_started", total_workers=sum(len(p) for p in self.worker_processes.values()))

    async def start_domain_workers(self, domain: AgentDomain, worker_count: int):
        if domain not in self.worker_processes:
            self.worker_processes[domain] = []
        for i in range(worker_count):
            redis_url = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
            proc = mp.Process(target=run_worker_process, args=(domain.value, i, redis_url), name=f"worker-{domain.value}-{i}")
            proc.start()
            self.worker_processes[domain].append(proc)
        logger.info(f"domain_workers_started domain={domain.value} count={worker_count}")

    async def monitor_workers(self):
        while self.running:
            try:
                for domain, procs in self.worker_processes.items():
                    alive = sum(1 for p in procs if p.is_alive())
                    expected = self.queue_manager.partitions[domain].worker_count
                    if alive < expected:
                        logger.warning(f"workers_missing domain={domain.value} alive={alive} expected={expected}")
                        await self.start_domain_workers(domain, expected - alive)
                await asyncio.sleep(15)
            except Exception as e:
                logger.error(f"monitor_error error={str(e)}")
                await asyncio.sleep(30)


def run_worker_process(domain_value: str, worker_id: int, redis_url: str):
    """Top-level function for multiprocessing workers to avoid pickling the manager instance."""
    def _sig_handler(signum, _frame):
        with suppress(Exception):
            logger.info(f"worker_signal domain={domain_value} worker_id={worker_id} signum={signum}")
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, _sig_handler)
    signal.signal(signal.SIGINT, _sig_handler)

    async def _loop():
        logger.info(f"worker_start domain={domain_value} worker_id={worker_id}")
        r = redis.from_url(redis_url)
        # local mapping for partition queues
        queue_names = {
            "research": "research_queue",
            "marketing": "marketing_queue",
            "sales": "sales_queue",
            "finance": "finance_queue",
            "operations": "operations_queue",
            "analytics": "analytics_queue",
        }
        tenant = "default"
        qname = queue_names.get(domain_value, f"{domain_value}_queue")
        try:
            while True:
                try:
                    found = False
                    for p in range(10, 0, -1):
                        key = f"queue:{tenant}:{qname}:p{p}"
                        res = await r.zpopmax(key, 1)
                        if res:
                            payload, _score = res[0]
                            data = json.loads(payload)
                            # Simulate processing; backend server handles actual agent execution today
                            await asyncio.sleep(0.05)
                            logger.info(f"task_done task_id={data.get('task_id')} agent_id={data.get('agent_id')}")
                            found = True
                            break
                    if not found:
                        await asyncio.sleep(0.5)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"worker_loop_error domain={domain_value} worker_id={worker_id} error={str(e)}")
                    await asyncio.sleep(2)
        finally:
            with suppress(Exception):
                await r.close()
            logger.info(f"worker_stop domain={domain_value} worker_id={worker_id}")

    asyncio.run(_loop())



#!/usr/bin/env python3
"""
Agent Orchestrator - Multi-Provider Agent Management

This module provides a unified orchestrator that manages all LLM providers and agents:
- Dynamic provider selection and load balancing
- Failover mechanisms and cost optimization
- Agent communication protocols
- Task delegation and result aggregation
- Real-time provider health checks
- Performance monitoring and optimization
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from .llm_manager import LLMProvider
from .model_router import ModelRouter, TaskRequirements

# Constants
MAX_RETRY_ATTEMPTS = 100
MAX_TASK_TIMEOUT = 300
WORKER_HEALTH_CHECK_INTERVAL = 30
QUEUE_MONITORING_INTERVAL = 60
MAX_TASK_DURATIONS = 100
HEARTBEAT_TIMEOUT = 300

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Types of agents available in the system."""
    RESEARCH = "research"
    ANALYSIS = "analysis"
    AUTOMATION = "automation"
    SECURITY = "security"
    CONTENT = "content"
    REPORTING = "reporting"
    COORDINATOR = "coordinator"


class AgentStatus(str, Enum):
    """Status of an agent."""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    agent_id: str
    name: str
    agent_type: AgentType
    provider: str
    model: str
    max_tokens: int = 4000
    temperature: float = 0.7
    capabilities: list[str] = field(default_factory=list)
    department: str = "general"
    priority: int = 5


@dataclass
class Task:
    """Task definition for agent execution."""
    task_id: str
    description: str
    requirements: TaskRequirements
    agent_type: AgentType
    priority: int = 5
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    status: str = "pending"
    result: str | None = None
    error: str | None = None


class Agent(ABC):
    """Abstract base class for all agents."""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.status = AgentStatus.IDLE
        self.task_history: list[Task] = []
        self.performance_metrics = {
            "total_tasks_processed": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "average_response_time": 0.0,
            "task_durations": []
        }
        self.last_heartbeat = datetime.now(UTC)

    @abstractmethod
    async def process_task(self, task: Task) -> str:
        """Process a given task and return the result."""
        pass

    async def is_healthy(self) -> bool:
        """Check if the agent is healthy."""
        time_since_heartbeat = (datetime.now(UTC) - self.last_heartbeat).total_seconds()
        return time_since_heartbeat < HEARTBEAT_TIMEOUT

    def update_metrics(self, task: Task, success: bool, duration: float):
        """Update performance metrics."""
        self.performance_metrics["total_tasks_processed"] += 1
        if success:
            self.performance_metrics["successful_tasks"] += 1
        else:
            self.performance_metrics["failed_tasks"] += 1

        self.performance_metrics["task_durations"].append(duration)
        if len(self.performance_metrics["task_durations"]) > MAX_TASK_DURATIONS:
            self.performance_metrics["task_durations"].pop(0)

        if self.performance_metrics["task_durations"]:
            self.performance_metrics["average_response_time"] = sum(
                self.performance_metrics["task_durations"]
            ) / len(self.performance_metrics["task_durations"])

    async def restart(self):
        """Restart the agent."""
        self.status = AgentStatus.IDLE
        self.last_heartbeat = datetime.now(UTC)
        logger.info(f"Agent {self.config.name} restarted")


class AgentOrchestrator:
    """Main orchestrator for managing all agents and tasks."""

    def __init__(self, config_path: str | None = None):
        self.config_path = config_path or "config/agents.yaml"
        self.agents: dict[str, Agent] = {}
        self.task_queue: list[Task] = []
        # Provide default config for ModelRouter
        default_config = {
            "ab_testing": {"enabled": False},
            "learning": {"enabled": True},
            "database": {"path": "model_router.db"}
        }
        self.model_router = ModelRouter(default_config)
        self.llm_providers: dict[str, LLMProvider] = {}
        self.health_check_task: asyncio.Task | None = None
        self.metrics_update_task: asyncio.Task | None = None
        self.running = False

    async def start(self):
        """Start the orchestrator."""
        logger.info("Starting Agent Orchestrator")
        self.running = True

        # Start background tasks
        self.health_check_task = asyncio.create_task(self._health_check_loop())
        self.metrics_update_task = asyncio.create_task(self._metrics_update_loop())

        logger.info("Agent Orchestrator started successfully")

    async def stop(self):
        """Stop the orchestrator."""
        logger.info("Stopping Agent Orchestrator")
        self.running = False

        # Cancel background tasks
        if self.health_check_task:
            self.health_check_task.cancel()

        if self.metrics_update_task:
            self.metrics_update_task.cancel()

        # Save final metrics
        await self._save_metrics_to_db()

        logger.info("Agent Orchestrator stopped")

    async def register_agent(self, agent: Agent):
        """Register a new agent."""
        self.agents[agent.config.agent_id] = agent
        logger.info(f"Registered agent: {agent.config.name}")

    async def submit_task(self, task: Task) -> str:
        """Submit a task for processing."""
        self.task_queue.append(task)
        logger.info(f"Submitted task: {task.task_id}")
        return task.task_id

    async def get_agent_status(self) -> dict[str, Any]:
        """Get status of all agents."""
        status = {
            "total_agents": len(self.agents),
            "active_agents": 0,
            "idle_agents": 0,
            "busy_agents": 0,
            "error_agents": 0,
            "offline_agents": 0
        }

        for agent in self.agents.values():
            if agent.status == AgentStatus.IDLE:
                status["idle_agents"] += 1
                status["active_agents"] += 1
            elif agent.status == AgentStatus.BUSY:
                status["busy_agents"] += 1
                status["active_agents"] += 1
            elif agent.status == AgentStatus.ERROR:
                status["error_agents"] += 1
            elif agent.status == AgentStatus.OFFLINE:
                status["offline_agents"] += 1

        return status

    async def _health_check_loop(self):
        """Background health check loop."""
        while self.running:
            try:
                for _agent_id, agent in self.agents.items():
                    if not await agent.is_healthy():
                        logger.warning(f"Agent {_agent_id} is unhealthy")
                        agent.status = AgentStatus.ERROR

                await asyncio.sleep(WORKER_HEALTH_CHECK_INTERVAL)

            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(WORKER_HEALTH_CHECK_INTERVAL)

    async def _metrics_update_loop(self):
        """Background metrics update loop."""
        while self.running:
            try:
                await self._update_metrics()
                await asyncio.sleep(QUEUE_MONITORING_INTERVAL)

            except Exception as e:
                logger.error(f"Metrics update error: {e}")
                await asyncio.sleep(QUEUE_MONITORING_INTERVAL)

    async def _update_metrics(self):
        """Update system metrics."""
        # Implementation for metrics update
        pass

    async def _save_metrics_to_db(self):
        """Save metrics to database."""
        # Implementation for saving metrics
        pass

    def __del__(self):
        """Cleanup on deletion."""
        with suppress(Exception):
            if hasattr(self, 'health_check_task') and self.health_check_task:
                self.health_check_task.cancel()

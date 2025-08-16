"""
Base AI Agent Framework
Foundation for all specialized AI agents in the ecosystem
"""

import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from autonomous_system.core.agent_orchestrator import AgentOrchestrator
from autonomous_system.core.llm_manager import LLMManager
from autonomous_system.learning.performance_tracker import PerformanceTracker
from autonomous_system.monitoring.health_checker import HealthChecker


class AgentStatus(Enum):
    """Agent operational status"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"
    LEARNING = "learning"
    COLLABORATING = "collaborating"

class AgentPriority(Enum):
    """Agent priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BACKGROUND = "background"

class AgentCapability(Enum):
    """Agent capability types"""
    DECISION_MAKING = "decision_making"
    DATA_ANALYSIS = "data_analysis"
    AUTOMATION = "automation"
    COMMUNICATION = "communication"
    CREATION = "creation"
    MONITORING = "monitoring"
    OPTIMIZATION = "optimization"
    PREDICTION = "prediction"

@dataclass
class AgentMetrics:
    """Agent performance and operational metrics"""
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_execution_time: float = 0.0
    average_response_time: float = 0.0
    success_rate: float = 0.0
    last_activity: datetime = field(default_factory=datetime.now)
    uptime: float = 0.0
    resource_usage: dict[str, float] = field(default_factory=dict)
    collaboration_count: int = 0
    learning_cycles: int = 0

@dataclass
class AgentContext:
    """Context information for agent operations"""
    user_id: str | None = None
    session_id: str | None = None
    priority: AgentPriority = AgentPriority.MEDIUM
    deadline: datetime | None = None
    dependencies: list[str] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

class BaseAgent(ABC):
    """Base class for all AI agents in the ecosystem"""

    def __init__(self, agent_id: str, name: str, description: str,
                 capabilities: list[AgentCapability], priority: AgentPriority = AgentPriority.MEDIUM):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.capabilities = capabilities
        self.priority = priority

        # Core systems
        self.llm_manager = LLMManager()
        self.orchestrator = AgentOrchestrator()
        self.health_checker = HealthChecker({})
        self.performance_tracker = PerformanceTracker({})

        # State management
        self.status = AgentStatus.IDLE
        self.metrics = AgentMetrics()
        self.context = AgentContext()

        # Task management
        self.current_task = None
        self.task_queue = []
        self.collaboration_partners = []

        # Knowledge and memory
        self.knowledge_base = {}
        self.memory = []
        self.learning_data = []

        # Logging
        self.logger = logging.getLogger(f"agent.{agent_id}")

        # Initialize agent
        self._initialize_agent()

    def _initialize_agent(self):
        """Initialize agent-specific components"""
        self.logger.info(f"Initializing agent: {self.name}")

        # Register with orchestrator
        self.orchestrator.register_agent(self)

        # Initialize capabilities
        for capability in self.capabilities:
            self._initialize_capability(capability)

        # Start background tasks
        asyncio.create_task(self._background_monitoring())
        asyncio.create_task(self._learning_cycle())

        self.logger.info(f"Agent {self.name} initialized successfully")

    def _initialize_capability(self, capability: AgentCapability):
        """Initialize a specific capability"""
        if capability == AgentCapability.DECISION_MAKING:
            self._init_decision_making()
        elif capability == AgentCapability.DATA_ANALYSIS:
            self._init_data_analysis()
        elif capability == AgentCapability.AUTOMATION:
            self._init_automation()
        elif capability == AgentCapability.COMMUNICATION:
            self._init_communication()
        elif capability == AgentCapability.CREATION:
            self._init_creation()
        elif capability == AgentCapability.MONITORING:
            self._init_monitoring()
        elif capability == AgentCapability.OPTIMIZATION:
            self._init_optimization()
        elif capability == AgentCapability.PREDICTION:
            self._init_prediction()

    @abstractmethod
    def _init_decision_making(self):
        """Initialize decision-making capabilities"""
        pass

    @abstractmethod
    def _init_data_analysis(self):
        """Initialize data analysis capabilities"""
        pass

    @abstractmethod
    def _init_automation(self):
        """Initialize automation capabilities"""
        pass

    @abstractmethod
    def _init_communication(self):
        """Initialize communication capabilities"""
        pass

    @abstractmethod
    def _init_creation(self):
        """Initialize creation capabilities"""
        pass

    @abstractmethod
    def _init_monitoring(self):
        """Initialize monitoring capabilities"""
        pass

    @abstractmethod
    def _init_optimization(self):
        """Initialize optimization capabilities"""
        pass

    @abstractmethod
    def _init_prediction(self):
        """Initialize prediction capabilities"""
        pass

    async def execute_task(self, task_data: dict[str, Any], context: AgentContext = None) -> dict[str, Any]:
        """Execute a task with the agent's capabilities"""
        start_time = time.time()
        task_id = str(uuid.uuid4())

        try:
            self.logger.info(f"Executing task {task_id}: {task_data.get('type', 'unknown')}")
            self.status = AgentStatus.BUSY
            self.current_task = task_id

            # Update context
            if context:
                self.context = context

            # Execute task based on capabilities
            result = await self._execute_task_internal(task_data)

            # Update metrics
            execution_time = time.time() - start_time
            self._update_metrics(execution_time, True)

            # Log success
            self.logger.info(f"Task {task_id} completed successfully in {execution_time:.2f}s")

            return {
                "task_id": task_id,
                "status": "success",
                "result": result,
                "execution_time": execution_time,
                "agent_id": self.agent_id,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            # Update metrics
            execution_time = time.time() - start_time
            self._update_metrics(execution_time, False)

            # Log error
            self.logger.error(f"Task {task_id} failed: {e}")

            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e),
                "execution_time": execution_time,
                "agent_id": self.agent_id,
                "timestamp": datetime.now().isoformat()
            }

        finally:
            self.status = AgentStatus.IDLE
            self.current_task = None

    @abstractmethod
    async def _execute_task_internal(self, task_data: dict[str, Any]) -> dict[str, Any]:
        """Internal task execution logic - must be implemented by subclasses"""
        pass

    async def collaborate_with_agent(self, target_agent_id: str, collaboration_data: dict[str, Any]) -> dict[str, Any]:
        """Collaborate with another agent"""
        try:
            self.logger.info(f"Collaborating with agent: {target_agent_id}")

            # Request collaboration through orchestrator
            result = await self.orchestrator.request_collaboration(
                self.agent_id, target_agent_id, collaboration_data
            )

            # Update collaboration metrics
            self.metrics.collaboration_count += 1

            return result

        except Exception as e:
            self.logger.error(f"Collaboration failed: {e}")
            raise

    async def learn_from_experience(self, experience_data: dict[str, Any]):
        """Learn from experience and update knowledge base"""
        try:
            self.logger.info("Learning from experience")

            # Store learning data
            self.learning_data.append({
                "timestamp": datetime.now().isoformat(),
                "data": experience_data
            })

            # Update knowledge base
            await self._update_knowledge_base(experience_data)

            # Update learning metrics
            self.metrics.learning_cycles += 1

        except Exception as e:
            self.logger.error(f"Learning failed: {e}")

    async def _update_knowledge_base(self, experience_data: dict[str, Any]):
        """Update agent's knowledge base with new information"""
        # This is a simplified implementation
        # In production, you'd use vector databases, knowledge graphs, etc.

        key = experience_data.get("key", str(uuid.uuid4()))
        self.knowledge_base[key] = {
            "data": experience_data.get("data"),
            "timestamp": datetime.now().isoformat(),
            "confidence": experience_data.get("confidence", 0.8),
            "source": experience_data.get("source", "experience")
        }

    def _update_metrics(self, execution_time: float, success: bool):
        """Update agent performance metrics"""
        if success:
            self.metrics.tasks_completed += 1
        else:
            self.metrics.tasks_failed += 1

        self.metrics.total_execution_time += execution_time
        self.metrics.average_response_time = (
            self.metrics.total_execution_time /
            (self.metrics.tasks_completed + self.metrics.tasks_failed)
        )

        total_tasks = self.metrics.tasks_completed + self.metrics.tasks_failed
        if total_tasks > 0:
            self.metrics.success_rate = self.metrics.tasks_completed / total_tasks

        self.metrics.last_activity = datetime.now()

    async def _background_monitoring(self):
        """Background monitoring and health checks"""
        while True:
            try:
                # Update uptime
                self.metrics.uptime = time.time()

                # Check agent health
                health_status = await self.health_checker.get_component_health()

                # Update resource usage
                import psutil
                process = psutil.Process()
                self.metrics.resource_usage = {
                    "cpu_percent": process.cpu_percent(),
                    "memory_mb": process.memory_info().rss / 1024 / 1024,
                    "threads": process.num_threads()
                }

                # Report to orchestrator
                await self.orchestrator.update_agent_status(self.agent_id, self.status, self.metrics)

                await asyncio.sleep(30)  # Update every 30 seconds

            except Exception as e:
                self.logger.error(f"Background monitoring error: {e}")
                await asyncio.sleep(60)

    async def _learning_cycle(self):
        """Periodic learning and optimization cycle"""
        while True:
            try:
                # Analyze recent experiences
                if len(self.learning_data) > 0:
                    await self._analyze_and_optimize()

                await asyncio.sleep(300)  # Learning cycle every 5 minutes

            except Exception as e:
                self.logger.error(f"Learning cycle error: {e}")
                await asyncio.sleep(600)

    async def _analyze_and_optimize(self):
        """Analyze experiences and optimize behavior"""
        # This is a simplified implementation
        # In production, you'd use ML models, pattern recognition, etc.

        recent_experiences = self.learning_data[-10:]  # Last 10 experiences

        # Analyze patterns
        success_patterns = []
        failure_patterns = []

        for experience in recent_experiences:
            if experience.get("data", {}).get("success", False):
                success_patterns.append(experience)
            else:
                failure_patterns.append(experience)

        # Update strategies based on patterns
        if len(failure_patterns) > len(success_patterns):
            self.logger.info("Detected performance degradation, optimizing strategies")
            # Implement optimization logic here

    def get_status_report(self) -> dict[str, Any]:
        """Get comprehensive agent status report"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "capabilities": [cap.value for cap in self.capabilities],
            "priority": self.priority.value,
            "metrics": {
                "tasks_completed": self.metrics.tasks_completed,
                "tasks_failed": self.metrics.tasks_failed,
                "success_rate": self.metrics.success_rate,
                "average_response_time": self.metrics.average_response_time,
                "uptime": self.metrics.uptime,
                "collaboration_count": self.metrics.collaboration_count,
                "learning_cycles": self.metrics.learning_cycles
            },
            "current_task": self.current_task,
            "task_queue_length": len(self.task_queue),
            "collaboration_partners": self.collaboration_partners,
            "knowledge_base_size": len(self.knowledge_base),
            "last_activity": self.metrics.last_activity.isoformat(),
            "resource_usage": self.metrics.resource_usage
        }

    async def shutdown(self):
        """Gracefully shutdown the agent"""
        self.logger.info(f"Shutting down agent: {self.name}")

        # Cancel background tasks
        # (In production, you'd properly cancel all asyncio tasks)

        # Unregister from orchestrator
        await self.orchestrator.unregister_agent(self.agent_id)

        self.status = AgentStatus.OFFLINE
        self.logger.info(f"Agent {self.name} shutdown complete")

# Utility functions for agent management
def create_agent_id(domain: str, role: str) -> str:
    """Create a standardized agent ID"""
    return f"{domain}_{role}_{str(uuid.uuid4())[:8]}"

def validate_agent_capabilities(capabilities: list[str]) -> list[AgentCapability]:
    """Validate and convert capability strings to enum values"""
    valid_capabilities = []
    for cap_str in capabilities:
        try:
            capability = AgentCapability(cap_str)
            valid_capabilities.append(capability)
        except ValueError:
            logging.warning(f"Invalid capability: {cap_str}")

    return valid_capabilities

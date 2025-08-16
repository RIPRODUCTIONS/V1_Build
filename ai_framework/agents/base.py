"""
Base Agent Class

This module provides the foundational base class for all AI agents in the system.
Each specialized agent inherits from this base class and implements domain-specific logic.
"""

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

# Import will be handled at runtime to avoid circular imports
# from ..core.llm_manager import LLMProvider, LLMRequest, LLMResponse
# from ..core.model_router import ModelRouter, TaskType, TaskComplexity, TaskRequirements

logger = logging.getLogger(__name__)

# Constants to replace magic numbers
MIN_HEARTBEAT_INTERVAL = 5
MIN_CONCURRENT_TASKS = 1
MAX_CONCURRENT_TASKS = 100
DEFAULT_HEARTBEAT_INTERVAL = 30
DEFAULT_MAX_CONCURRENT_TASKS = 10


class AgentType(str, Enum):
    """Types of agents available in the system."""
    # Executive & Strategy
    CEO = "ceo"
    COO = "coo"
    CFO = "cfo"
    CTO = "cto"
    CHRO = "chro"

    # Finance & Money
    ACCOUNTANT = "accountant"
    CONTROLLER = "controller"
    TRADER = "trader"
    PAYMENTS_MANAGER = "payments_manager"
    COLLECTIONS_OFFICER = "collections_officer"
    FRAUD_ANALYST = "fraud_analyst"
    AUDITOR = "auditor"

    # Sales & Customer
    SALES_MANAGER = "sales_manager"
    LEAD_QUALIFIER = "lead_qualifier"
    ACCOUNT_MANAGER = "account_manager"
    CUSTOMER_SUPPORT = "customer_support"
    ONBOARDING_SPECIALIST = "onboarding_specialist"

    # Marketing & Growth
    CMO = "cmo"
    CAMPAIGN_MANAGER = "campaign_manager"
    SOCIAL_MEDIA_MANAGER = "social_media_manager"
    SEO_SPECIALIST = "seo_specialist"
    PR_AGENT = "pr_agent"

    # Operations & Logistics
    SUPPLY_CHAIN_MANAGER = "supply_chain_manager"
    FLEET_MANAGER = "fleet_manager"
    SCHEDULER = "scheduler"
    PROCUREMENT_OFFICER = "procurement_officer"

    # HR & People
    RECRUITER = "recruiter"
    TRAINING_MANAGER = "training_manager"
    PERFORMANCE_COACH = "performance_coach"
    COMPLIANCE_OFFICER = "compliance_officer"

    # Legal & Compliance
    GENERAL_COUNSEL = "general_counsel"
    IP_MANAGER = "ip_manager"
    CONTRACT_NEGOTIATOR = "contract_negotiator"

    # IT & Security
    SYSADMIN = "sysadmin"
    SECURITY_ANALYST = "security_analyst"
    DEVOPS_ENGINEER = "devops_engineer"
    DATA_ENGINEER = "data_engineer"
    CLOUD_OPTIMIZER = "cloud_optimizer"

    # Creative & Content
    GRAPHIC_DESIGNER = "graphic_designer"
    VIDEO_PRODUCER = "video_producer"
    COPYWRITER = "copywriter"
    BRAND_MANAGER = "brand_manager"

    # Personal Life & Productivity
    PERSONAL_ASSISTANT = "personal_assistant"
    TRAVEL_AGENT = "travel_agent"
    HEALTH_COACH = "health_coach"
    HOME_MANAGER = "home_manager"
    LEARNING_MENTOR = "learning_mentor"


class AgentStatus(str, Enum):
    """Status of an agent."""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    STUCK = "stuck" # Added STUCK status


class TaskPriority(str, Enum):
    """Priority levels for tasks."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AgentDepartment(str, Enum):
    """Department/domain classification for agents."""
    EXECUTIVE = "executive"
    FINANCE = "finance"
    SALES = "sales"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    CYBERSECURITY = "cybersecurity"
    HR = "hr"
    LEGAL = "legal"
    IT_SECURITY = "it_security"
    CREATIVE = "creative"
    PERSONAL = "personal"


@dataclass
class AgentConfig:
    """Configuration for an AI agent."""
    name: str
    agent_type: AgentType
    department: AgentDepartment
    capabilities: list[str]
    max_concurrent_tasks: int = 1
    collaboration_enabled: bool = True
    auto_heal_enabled: bool = True
    heartbeat_interval: int = 30  # seconds
    max_memory_gb: float = 1.0
    cost_per_hour: float = 0.0
    priority_level: int = 1

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError("Agent name cannot be empty")

        if not self.capabilities:
            raise ValueError("Agent must have at least one capability")

        if self.max_concurrent_tasks < MIN_CONCURRENT_TASKS:
            raise ValueError(f"Max concurrent tasks must be at least {MIN_CONCURRENT_TASKS}")

        if self.heartbeat_interval < MIN_HEARTBEAT_INTERVAL:
            raise ValueError(f"Heartbeat interval must be at least {MIN_HEARTBEAT_INTERVAL} seconds")


@dataclass
class Task:
    """Task to be executed by an AI agent."""
    task_id: str
    task_type: str
    description: str
    priority: TaskPriority
    requirements: dict[str, Any] = field(default_factory=dict)
    assigned_agent: str | None = None
    status: str = "pending"
    dependencies: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate task after initialization."""
        if not self.task_id:
            raise ValueError("Task ID is required")
        if not self.description:
            raise ValueError("Task description is required")
        if self.priority not in TaskPriority:
            raise ValueError(f"Invalid priority: {self.priority}")


@dataclass
class AgentTask:
    """Task assigned to a specific agent."""
    task: Task
    agent_id: str
    assigned_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    performance_metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMetrics:
    """Performance metrics for an agent."""
    total_tasks_processed: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    total_processing_time: float = 0.0
    avg_task_duration: float = 0.0
    cost_per_hour: float = 0.0
    memory_usage_gb: float = 0.0
    uptime_percentage: float = 100.0
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))


class BaseAgent(ABC):
    """Base class for all AI agents in the framework."""

    def __init__(self, config: AgentConfig, llm_manager=None, model_router=None):
        """Initialize the base agent with proper dependency handling."""
        self.config = config
        self.agent_id = str(uuid.uuid4())
        self.status = AgentStatus.IDLE
        self.current_task: Task | None = None
        self.current_tasks: list[Task] = []
        self.task_history: list[Task] = []
        self.performance_metrics: dict[str, Any] = {}
        self.collaboration_network: list[str] = []
        self.last_heartbeat: datetime = datetime.now(UTC)

        # Initialize dependencies with proper defaults
        self.llm_manager = llm_manager or self._create_default_llm_manager()
        self.model_router = model_router or self._create_default_model_router()

        # Initialize agent-specific components
        self._initialize_agent()

        logger.info(f"Agent {self.__class__.__name__} initialized successfully")

    def _create_default_llm_manager(self):
        """Create a default LLM manager if none provided."""
        class DefaultLLMManager:
            async def get_response(self, request):
                return {"response": "Default response", "provider": "default"}

        return DefaultLLMManager()

    def _create_default_model_router(self):
        """Create a default model router if none provided."""
        class DefaultModelRouter:
            async def route_task(self, task):
                return {"model": "default", "provider": "default"}

        return DefaultModelRouter()

    def _initialize_agent(self):
        """Initialize agent-specific components and domain knowledge."""
        # Default implementation - basic initialization
        try:
            self.status = AgentStatus.IDLE
            self.last_heartbeat = datetime.now(UTC)
            self.performance_metrics = {
                "total_tasks_processed": 0,
                "successful_tasks": 0,
                "failed_tasks": 0,
                "avg_task_duration": 0.0
            }
            logger.info(f"Agent {self.config.name} initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize agent {self.config.name}: {e}")

    async def execute_task(self, task: Task) -> dict[str, Any]:
        """Execute a specific task using the agent's specialized capabilities."""
        # Default implementation - basic task execution
        try:
            logger.info(f"Agent {self.config.name} executing task {task.task_id}")

            # Simulate task execution
            result = {
                "task_id": task.task_id,
                "status": "completed",
                "agent": self.config.name,
                "result": f"Task executed by {self.config.name}",
                "timestamp": datetime.now(UTC).isoformat()
            }

            await self.complete_task(task.task_id, result)
            return result

        except Exception as e:
            error_msg = f"Task execution failed: {e}"
            logger.error(f"Agent {self.config.name} failed to execute task {task.task_id}: {e}")
            await self.complete_task(task.task_id, {}, str(e))
            return {"error": error_msg, "task_id": task.task_id}

    def get_capabilities(self) -> list[str]:
        """Get agent capabilities and skills."""
        # Default implementation - return basic capabilities
        return [self.config.agent_type.value, "basic_operations"]

    def get_department_goals(self) -> list[str]:
        """Get the agent's department-specific goals and objectives."""
        # Default implementation - return basic goals
        return ["efficient_operation", "quality_output", "continuous_improvement"]

    async def can_handle_task(self, task: Task) -> bool:
        """Check if agent can handle a specific task."""
        # Check if agent type matches
        if task.task_type != self.config.agent_type.value:
            return False

        # Check if agent has capacity
        if self.current_task is not None:
            return False

        # Check if agent has required capabilities
        required_capabilities = task.metadata.get("required_capabilities", [])
        if required_capabilities:
            agent_capabilities = set(self.get_capabilities())
            if not all(cap in agent_capabilities for cap in required_capabilities):
                return False

        # Check dependencies
        if task.dependencies:
            for dep_task_id in task.dependencies:
                if not self._is_dependency_completed(dep_task_id):
                    return False

        return True

    async def assign_task(self, task: Task) -> bool:
        """Assign a task to this agent."""
        if not await self.can_handle_task(task):
            return False

        self.current_task = task
        self.status = AgentStatus.BUSY
        return True

    async def complete_task(self, task_id: str, result: dict[str, Any], error: str | None = None):
        """Complete a task and update metrics."""
        if self.current_task and self.current_task.task_id == task_id:
            self.current_task.completed_at = datetime.now(UTC)
            self.current_task.result = result
            self.current_task.error = error
            self.current_task.status = "completed" if not error else "failed"

            # Update performance metrics
            if hasattr(self, 'performance_metrics'):
                self.performance_metrics['total_tasks_processed'] = self.performance_metrics.get('total_tasks_processed', 0) + 1
                if not error:
                    self.performance_metrics['successful_tasks'] = self.performance_metrics.get('successful_tasks', 0) + 1
                else:
                    self.performance_metrics['failed_tasks'] = self.performance_metrics.get('failed_tasks', 0) + 1

            # Move to task history
            self.task_history.append(self.current_task)
            self.current_task = None
            self.status = AgentStatus.IDLE

            logger.info(f"Task {task_id} completed by agent {self.config.name}")
        else:
            logger.warning(f"Task {task_id} not found in current tasks for agent {self.config.name}")

    async def report_error(self, task_id: str, error: str) -> dict[str, Any]:
        """Common error reporting used by several agents."""
        await self.complete_task(task_id, result={}, error=error)
        return {"error": error, "task_id": task_id, "timestamp": datetime.now(UTC).isoformat()}

    async def _learn_from_task(self, task: Task):
        """Learn from completed tasks to improve future performance."""
        if not hasattr(self, 'learning_data'):
            self.learning_data = {}

        if hasattr(task, 'error') and task.error:
            # Learn from failures
            self.learning_data.setdefault("failure_patterns", []).append({
                "task_type": task.task_type,
                "error": task.error,
                "timestamp": datetime.now(UTC)
            })
        else:
            # Learn from successes
            self.learning_data.setdefault("success_patterns", []).append({
                "task_type": task.task_type,
                "result": getattr(task, 'result', {}),
                "timestamp": datetime.now(UTC)
            })

    def _is_dependency_completed(self, dep_task_id: str) -> bool:
        """Check if a dependency task is completed."""
        # For now, assume all dependencies are completed
        # In a real implementation, this would check the task registry
        return True

    async def get_status_report(self) -> dict[str, Any]:
        """Get comprehensive status report for the agent."""
        # Initialize missing attributes if they don't exist
        if not hasattr(self, 'performance_metrics'):
            self.performance_metrics = {}
        if not hasattr(self, 'last_heartbeat'):
            self.last_heartbeat = datetime.now(UTC)

        return {
            "agent_id": self.agent_id,
            "name": self.config.name,
            "type": self.config.agent_type.value,
            "department": self.config.department.value,
            "status": self.status.value,
            "current_task": self.current_task.task_id if self.current_task else None,
            "total_tasks_processed": self.performance_metrics.get('total_tasks_processed', 0),
            "success_rate": (
                self.performance_metrics.get('successful_tasks', 0) /
                max(self.performance_metrics.get('total_tasks_processed', 1), 1)
            ),
            "avg_task_duration": self.performance_metrics.get('avg_task_duration', 0.0),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "capabilities": self.get_capabilities(),
            "department_goals": self.get_department_goals()
        }

    async def collaborate_with_agent(self, other_agent_id: str, task: Task) -> dict[str, Any]:
        """Collaborate with another agent on a task."""
        if not hasattr(self.config, 'collaboration_enabled') or not self.config.collaboration_enabled:
            return {"error": "Collaboration not enabled for this agent"}

        # Add to collaboration network
        if other_agent_id not in self.collaboration_network:
            self.collaboration_network.append(other_agent_id)

        # Implement collaboration logic
        collaboration_result = await self._execute_collaboration(other_agent_id, task)
        return collaboration_result

    async def _execute_collaboration(self, other_agent_id: str, task: Task) -> dict[str, Any]:
        """Execute collaboration logic with another agent."""
        # This is a placeholder - specialized agents will implement their own logic
        return {
            "collaboration_type": "basic",
            "partner_agent": other_agent_id,
            "task_id": task.task_id,
            "status": "collaborating"
        }

    async def shutdown(self):
        """Gracefully shutdown the agent."""
        logger.info(f"Agent {self.config.name} shutting down...")
        self.status = AgentStatus.OFFLINE

        # Save any pending work
        try:
            await self._save_work_state()
        except Exception as e:
            logger.warning(f"Failed to save work state: {e}")

        # Cleanup resources
        try:
            await self._cleanup_resources()
        except Exception as e:
            logger.warning(f"Failed to cleanup resources: {e}")

        logger.info(f"Agent {self.config.name} shutdown complete")

    async def auto_heal(self):
        """Attempt to automatically heal the agent."""
        logger.info(f"Agent {self.config.name} attempting auto-heal...")

        try:
            # Reset status if stuck
            if self.status in [AgentStatus.ERROR, AgentStatus.STUCK]:
                self.status = AgentStatus.IDLE
                logger.info(f"Agent {self.config.name} status reset to IDLE")

            # Clear stuck tasks
            if (self.current_task and
                hasattr(self.current_task, 'status') and
                getattr(self.current_task, 'status', '') == 'stuck'):
                self.current_task = None
                self.status = AgentStatus.IDLE
                logger.info(f"Agent {self.config.name} cleared stuck task")

            # Reset performance metrics if corrupted
            if not isinstance(self.performance_metrics, dict):
                self.performance_metrics = {}
                logger.info(f"Agent {self.config.name} reset corrupted performance metrics")

            return {"status": "healed", "agent": self.config.name}

        except Exception as e:
            logger.error(f"Auto-heal failed for agent {self.config.name}: {e}")
            return {"status": "heal_failed", "error": str(e)}

    async def _save_work_state(self):
        """Save the agent's current work state."""
        try:
            # Default implementation - save basic state
            state_data = {
                "agent_id": self.agent_id,
                "status": self.status.value,
                "current_task": self.current_task.task_id if self.current_task else None,
                "performance_metrics": self.performance_metrics,
                "timestamp": datetime.now(UTC).isoformat()
            }

            # Save to local storage or database
            if hasattr(self, 'state_storage'):
                await self.state_storage.save_state(self.agent_id, state_data)

            logger.debug(f"Work state saved for agent {self.config.name}")
            return state_data
        except Exception as e:
            logger.warning(f"Failed to save work state for agent {self.config.name}: {e}")
            return {}

    async def _cleanup_resources(self):
        """Cleanup agent resources."""
        try:
            # Default implementation - basic cleanup
            if hasattr(self, 'current_task') and self.current_task:
                self.current_task = None

            if hasattr(self, 'task_history'):
                self.task_history.clear()

            if hasattr(self, 'collaboration_network'):
                self.collaboration_network.clear()

            # Reset performance metrics
            if hasattr(self, 'performance_metrics'):
                self.performance_metrics = {}

            logger.debug(f"Resources cleaned up for agent {self.config.name}")
        except Exception as e:
            logger.warning(f"Failed to cleanup resources for agent {self.config.name}: {e}")

    async def heartbeat(self):
        """Send heartbeat to indicate agent is alive."""
        self.last_heartbeat = datetime.now(UTC)
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "timestamp": self.last_heartbeat.isoformat()
        }

"""
Advanced Task Orchestration Engine
Advanced workflow management, dependency resolution, and intelligent scheduling
"""

import asyncio
import heapq
import json
import logging
import sqlite3
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import networkx as nx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"

class TaskDependencyType(Enum):
    """Types of task dependencies"""
    REQUIRES = "requires"  # Task A requires Task B to complete
    BLOCKS = "blocks"      # Task A blocks Task B from starting
    TRIGGERS = "triggers"  # Task A triggers Task B when completed
    OPTIONAL = "optional"  # Task A is optional for Task B

class SchedulingStrategy(Enum):
    """Task scheduling strategies"""
    FIFO = "fifo"                    # First in, first out
    PRIORITY = "priority"            # Priority-based scheduling
    DEADLINE = "deadline"            # Deadline-based scheduling
    RESOURCE_AWARE = "resource_aware" # Resource-aware scheduling
    COST_OPTIMIZED = "cost_optimized" # Cost-optimized scheduling
    LOAD_BALANCED = "load_balanced"   # Load-balanced scheduling

@dataclass
class WorkflowDefinition:
    """Definition of a workflow"""
    workflow_id: str
    name: str
    description: str
    version: str
    tasks: list[dict[str, Any]]
    dependencies: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class WorkflowInstance:
    """Instance of a workflow execution"""
    instance_id: str
    workflow_id: str
    status: WorkflowStatus
    current_tasks: list[str] = field(default_factory=list)
    completed_tasks: list[str] = field(default_factory=list)
    failed_tasks: list[str] = field(default_factory=list)
    start_time: datetime | None = None
    end_time: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class TaskDependency:
    """Task dependency definition"""
    dependency_id: str
    source_task: str
    target_task: str
    dependency_type: TaskDependencyType
    condition: str | None = None  # Optional condition expression
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ResourceRequirement:
    """Resource requirement for a task"""
    cpu_cores: float = 1.0
    memory_gb: float = 1.0
    gpu_count: int = 0
    storage_gb: float = 1.0
    network_bandwidth: float = 1.0
    custom_resources: dict[str, Any] = field(default_factory=dict)

@dataclass
class TaskSchedule:
    """Task scheduling information"""
    task_id: str
    priority: int
    deadline: datetime | None = None
    estimated_duration: timedelta
    resource_requirements: ResourceRequirement
    dependencies: list[str] = field(default_factory=list)
    scheduling_strategy: SchedulingStrategy = SchedulingStrategy.PRIORITY

class AdvancedOrchestrator:
    """Advanced task orchestration engine with workflow management"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.db_path = Path(config.get("database", {}).get("path", "advanced_orchestrator.db"))
        self._init_database()

        # Workflow management
        self.workflows: dict[str, WorkflowDefinition] = {}
        self.workflow_instances: dict[str, WorkflowInstance] = {}
        self.task_dependencies: dict[str, list[TaskDependency]] = defaultdict(list)

        # Task scheduling
        self.task_queue: list[TaskSchedule] = []
        self.running_tasks: dict[str, dict[str, Any]] = {}
        self.completed_tasks: dict[str, dict[str, Any]] = {}

        # Resource management
        self.available_resources = ResourceRequirement(
            cpu_cores=config.get("resources", {}).get("cpu_cores", 8.0),
            memory_gb=config.get("resources", {}).get("memory_gb", 16.0),
            gpu_count=config.get("resources", {}).get("gpu_count", 0),
            storage_gb=config.get("resources", {}).get("storage_gb", 100.0),
            network_bandwidth=config.get("resources", {}).get("network_bandwidth", 1000.0)
        )
        self.allocated_resources = ResourceRequirement()

        # Scheduling configuration
        self.scheduling_strategy = SchedulingStrategy(
            config.get("scheduling", {}).get("strategy", "priority")
        )
        self.max_concurrent_tasks = config.get("scheduling", {}).get("max_concurrent_tasks", 10)
        self.task_timeout = config.get("scheduling", {}).get("task_timeout", 3600)

        # Background tasks
        self.background_tasks = []
        self._start_background_tasks()

        logger.info("Advanced Orchestrator initialized")

    def _init_database(self):
        """Initialize advanced orchestrator database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Workflow definitions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_definitions (
                    workflow_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    version TEXT NOT NULL,
                    tasks TEXT NOT NULL,
                    dependencies TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
            """)

            # Workflow instances
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_instances (
                    instance_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    current_tasks TEXT,
                    completed_tasks TEXT,
                    failed_tasks TEXT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    metadata TEXT,
                    created_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (workflow_id) REFERENCES workflow_definitions (workflow_id)
                )
            """)

            # Task dependencies
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_dependencies (
                    dependency_id TEXT PRIMARY KEY,
                    source_task TEXT NOT NULL,
                    target_task TEXT NOT NULL,
                    dependency_type TEXT NOT NULL,
                    condition TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP NOT NULL
                )
            """)

            # Task execution history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_execution_history (
                    execution_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL,
                    workflow_instance_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    duration REAL,
                    resource_usage TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (workflow_instance_id) REFERENCES workflow_instances (instance_id)
                )
            """)

            conn.commit()
            conn.close()
            logger.info("Advanced orchestrator database initialized")

        except Exception as e:
            logger.error(f"Failed to initialize advanced orchestrator database: {e}")
            raise

    def _start_background_tasks(self):
        """Start background orchestration tasks"""
        self.background_tasks = [
            asyncio.create_task(self._workflow_scheduler()),
            asyncio.create_task(self._resource_monitor()),
            asyncio.create_task(self._dependency_resolver()),
            asyncio.create_task(self._task_monitor())
        ]
        logger.info("Background orchestration tasks started")

    async def register_workflow(self, workflow: WorkflowDefinition) -> bool:
        """Register a new workflow definition"""
        try:
            # Validate workflow
            if not self._validate_workflow(workflow):
                return False

            # Store workflow
            self.workflows[workflow.workflow_id] = workflow

            # Store in database
            await self._store_workflow(workflow)

            # Build dependency graph
            self._build_dependency_graph(workflow)

            logger.info(f"Workflow registered: {workflow.name} ({workflow.workflow_id})")
            return True

        except Exception as e:
            logger.error(f"Failed to register workflow: {e}")
            return False

    def _validate_workflow(self, workflow: WorkflowDefinition) -> bool:
        """Validate workflow definition"""
        try:
            # Check required fields
            if not workflow.workflow_id or not workflow.name or not workflow.tasks:
                logger.error("Workflow missing required fields")
                return False

            # Check for circular dependencies
            if self._has_circular_dependencies(workflow):
                logger.error("Workflow has circular dependencies")
                return False

            # Validate task definitions
            task_ids = {task.get("task_id") for task in workflow.tasks}
            for task in workflow.tasks:
                if not task.get("task_id") or not task.get("name"):
                    logger.error("Task missing required fields")
                    return False

            # Validate dependencies
            for dep in workflow.dependencies:
                if (dep.get("source_task") not in task_ids or
                    dep.get("target_task") not in task_ids):
                    logger.error("Dependency references non-existent task")
                    return False

            return True

        except Exception as e:
            logger.error(f"Workflow validation failed: {e}")
            return False

    def _has_circular_dependencies(self, workflow: WorkflowDefinition) -> bool:
        """Check for circular dependencies in workflow"""
        try:
            # Build dependency graph
            graph = nx.DiGraph()

            # Add nodes
            for task in workflow.tasks:
                graph.add_node(task["task_id"])

            # Add edges
            for dep in workflow.dependencies:
                graph.add_edge(dep["source_task"], dep["target_task"])

            # Check for cycles
            try:
                cycles = list(nx.simple_cycles(graph))
                if cycles:
                    logger.warning(f"Circular dependencies detected: {cycles}")
                    return True
            except nx.NetworkXNoCycle:
                pass

            return False

        except Exception as e:
            logger.error(f"Circular dependency check failed: {e}")
            return True  # Assume circular if check fails

    def _build_dependency_graph(self, workflow: WorkflowDefinition):
        """Build dependency graph for workflow"""
        try:
            workflow_id = workflow.workflow_id

            # Clear existing dependencies
            self.task_dependencies[workflow_id] = []

            # Add dependencies
            for dep_data in workflow.dependencies:
                dependency = TaskDependency(
                    dependency_id=f"{workflow_id}_{dep_data['source_task']}_{dep_data['target_task']}",
                    source_task=dep_data["source_task"],
                    target_task=dep_data["target_task"],
                    dependency_type=TaskDependencyType(dep_data.get("type", "requires")),
                    condition=dep_data.get("condition"),
                    metadata=dep_data.get("metadata", {})
                )
                self.task_dependencies[workflow_id].append(dependency)

            logger.info(f"Dependency graph built for workflow: {workflow.name}")

        except Exception as e:
            logger.error(f"Failed to build dependency graph: {e}")

    async def start_workflow(self, workflow_id: str, metadata: dict[str, Any] = None) -> str | None:
        """Start a workflow instance"""
        try:
            if workflow_id not in self.workflows:
                logger.error(f"Workflow not found: {workflow_id}")
                return None

            workflow = self.workflows[workflow_id]

            # Create workflow instance
            instance_id = f"instance_{workflow_id}_{int(time.time())}"
            instance = WorkflowInstance(
                instance_id=instance_id,
                workflow_id=workflow_id,
                status=WorkflowStatus.PENDING,
                metadata=metadata or {}
            )

            # Store instance
            self.workflow_instances[instance_id] = instance
            await self._store_workflow_instance(instance)

            # Schedule initial tasks
            await self._schedule_workflow_tasks(instance)

            logger.info(f"Workflow started: {workflow.name} ({instance_id})")
            return instance_id

        except Exception as e:
            logger.error(f"Failed to start workflow: {e}")
            return None

    async def _schedule_workflow_tasks(self, instance: WorkflowInstance):
        """Schedule tasks for workflow instance"""
        try:
            workflow = self.workflows[instance.workflow_id]

            # Find tasks that can start (no dependencies or dependencies satisfied)
            for task in workflow.tasks:
                task_id = task["task_id"]

                # Check if task can start
                if await self._can_start_task(instance.instance_id, task_id):
                    # Create task schedule
                    schedule = TaskSchedule(
                        task_id=task_id,
                        priority=task.get("priority", 1),
                        deadline=task.get("deadline"),
                        estimated_duration=timedelta(seconds=task.get("estimated_duration", 300)),
                        resource_requirements=self._parse_resource_requirements(task),
                        dependencies=task.get("dependencies", []),
                        scheduling_strategy=SchedulingStrategy(task.get("scheduling_strategy", "priority"))
                    )

                    # Add to queue
                    heapq.heappush(self.task_queue, (-schedule.priority, time.time(), schedule))

                    # Update instance
                    instance.current_tasks.append(task_id)

            # Update instance status
            if instance.current_tasks:
                instance.status = WorkflowStatus.RUNNING
                instance.start_time = datetime.now()
            else:
                instance.status = WorkflowStatus.COMPLETED
                instance.end_time = datetime.now()

            # Store updated instance
            await self._store_workflow_instance(instance)

        except Exception as e:
            logger.error(f"Failed to schedule workflow tasks: {e}")

    async def _can_start_task(self, instance_id: str, task_id: str) -> bool:
        """Check if a task can start based on dependencies"""
        try:
            workflow = self.workflows[self.workflow_instances[instance_id].workflow_id]

            # Get task dependencies
            task_deps = [
                dep for dep in self.task_dependencies[workflow.workflow_id]
                if dep.target_task == task_id
            ]

            # Check if all dependencies are satisfied
            for dep in task_deps:
                if dep.dependency_type == TaskDependencyType.REQUIRES:
                    # Check if source task is completed
                    if dep.source_task not in self.workflow_instances[instance_id].completed_tasks:
                        return False

                elif dep.dependency_type == TaskDependencyType.BLOCKS:
                    # Check if source task is not running
                    if dep.source_task in self.workflow_instances[instance_id].current_tasks:
                        return False

            return True

        except Exception as e:
            logger.error(f"Failed to check task dependencies: {e}")
            return False

    def _parse_resource_requirements(self, task: dict[str, Any]) -> ResourceRequirement:
        """Parse resource requirements from task definition"""
        try:
            resources = task.get("resources", {})
            return ResourceRequirement(
                cpu_cores=resources.get("cpu_cores", 1.0),
                memory_gb=resources.get("memory_gb", 1.0),
                gpu_count=resources.get("gpu_count", 0),
                storage_gb=resources.get("storage_gb", 1.0),
                network_bandwidth=resources.get("network_bandwidth", 1.0),
                custom_resources=resources.get("custom", {})
            )
        except Exception as e:
            logger.error(f"Failed to parse resource requirements: {e}")
            return ResourceRequirement()

    async def _workflow_scheduler(self):
        """Background task scheduler"""
        while True:
            try:
                if self.task_queue and len(self.running_tasks) < self.max_concurrent_tasks:
                    # Get next task from queue
                    priority, timestamp, schedule = heapq.heappop(self.task_queue)

                    # Check if resources are available
                    if await self._allocate_resources(schedule.resource_requirements):
                        # Start task
                        await self._start_task(schedule)
                    else:
                        # Put back in queue with lower priority
                        heapq.heappush(self.task_queue, (priority + 1, timestamp, schedule))

                await asyncio.sleep(1)  # Check every second

            except Exception as e:
                logger.error(f"Workflow scheduler error: {e}")
                await asyncio.sleep(5)

    async def _allocate_resources(self, requirements: ResourceRequirement) -> bool:
        """Allocate resources for a task"""
        try:
            # Check if resources are available
            if (self.allocated_resources.cpu_cores + requirements.cpu_cores > self.available_resources.cpu_cores or
                self.allocated_resources.memory_gb + requirements.memory_gb > self.available_resources.memory_gb or
                self.allocated_resources.gpu_count + requirements.gpu_count > self.available_resources.gpu_count):
                return False

            # Allocate resources
            self.allocated_resources.cpu_cores += requirements.cpu_cores
            self.allocated_resources.memory_gb += requirements.memory_gb
            self.allocated_resources.gpu_count += requirements.gpu_count
            self.allocated_resources.storage_gb += requirements.storage_gb
            self.allocated_resources.network_bandwidth += requirements.network_bandwidth

            return True

        except Exception as e:
            logger.error(f"Resource allocation failed: {e}")
            return False

    async def _start_task(self, schedule: TaskSchedule):
        """Start a task execution"""
        try:
            # Create task execution record
            execution_id = f"exec_{schedule.task_id}_{int(time.time())}"

            self.running_tasks[execution_id] = {
                "task_id": schedule.task_id,
                "schedule": schedule,
                "start_time": datetime.now(),
                "status": "running"
            }

            # Start task execution (this would integrate with the task executor)
            logger.info(f"Task started: {schedule.task_id}")

        except Exception as e:
            logger.error(f"Failed to start task: {e}")

    async def _resource_monitor(self):
        """Monitor resource usage and cleanup"""
        while True:
            try:
                # Clean up completed tasks
                completed_executions = []
                for exec_id, task_info in self.running_tasks.items():
                    if task_info["status"] == "completed":
                        completed_executions.append(exec_id)

                for exec_id in completed_executions:
                    await self._cleanup_task_resources(exec_id)

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"Resource monitor error: {e}")
                await asyncio.sleep(30)

    async def _cleanup_task_resources(self, execution_id: str):
        """Clean up resources for completed task"""
        try:
            if execution_id in self.running_tasks:
                task_info = self.running_tasks[execution_id]
                schedule = task_info["schedule"]

                # Release resources
                self.allocated_resources.cpu_cores -= schedule.resource_requirements.cpu_cores
                self.allocated_resources.memory_gb -= schedule.resource_requirements.memory_gb
                self.allocated_resources.gpu_count -= schedule.resource_requirements.gpu_count
                self.allocated_resources.storage_gb -= schedule.resource_requirements.storage_gb
                self.allocated_resources.network_bandwidth -= schedule.resource_requirements.network_bandwidth

                # Move to completed tasks
                self.completed_tasks[execution_id] = task_info
                del self.running_tasks[execution_id]

                logger.info(f"Task resources cleaned up: {schedule.task_id}")

        except Exception as e:
            logger.error(f"Failed to cleanup task resources: {e}")

    async def _dependency_resolver(self):
        """Resolve task dependencies and trigger next tasks"""
        while True:
            try:
                # Check all workflow instances
                for instance_id, instance in self.workflow_instances.items():
                    if instance.status == WorkflowStatus.RUNNING:
                        await self._check_workflow_progress(instance)

                await asyncio.sleep(5)  # Check every 5 seconds

            except Exception as e:
                logger.error(f"Dependency resolver error: {e}")
                await asyncio.sleep(10)

    async def _check_workflow_progress(self, instance: WorkflowInstance):
        """Check workflow progress and trigger next tasks"""
        try:
            workflow = self.workflows[instance.workflow_id]

            # Check for newly completed tasks
            for task_id in list(instance.current_tasks):
                if task_id in self.completed_tasks:
                    # Move to completed
                    instance.current_tasks.remove(task_id)
                    instance.completed_tasks.append(task_id)

                    # Check if workflow is complete
                    if len(instance.completed_tasks) == len(workflow.tasks):
                        instance.status = WorkflowStatus.COMPLETED
                        instance.end_time = datetime.now()
                        logger.info(f"Workflow completed: {instance.instance_id}")
                    else:
                        # Schedule next tasks
                        await self._schedule_workflow_tasks(instance)

            # Store updated instance
            await self._store_workflow_instance(instance)

        except Exception as e:
            logger.error(f"Failed to check workflow progress: {e}")

    async def _task_monitor(self):
        """Monitor task execution and handle timeouts"""
        while True:
            try:
                current_time = datetime.now()

                # Check for timed out tasks
                timed_out_tasks = []
                for exec_id, task_info in self.running_tasks.items():
                    start_time = task_info["start_time"]
                    if (current_time - start_time).total_seconds() > self.task_timeout:
                        timed_out_tasks.append(exec_id)

                # Handle timed out tasks
                for exec_id in timed_out_tasks:
                    await self._handle_task_timeout(exec_id)

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Task monitor error: {e}")
                await asyncio.sleep(60)

    async def _handle_task_timeout(self, execution_id: str):
        """Handle task timeout"""
        try:
            if execution_id in self.running_tasks:
                task_info = self.running_tasks[execution_id]
                schedule = task_info["schedule"]

                # Mark task as failed
                task_info["status"] = "timeout"
                task_info["end_time"] = datetime.now()

                # Release resources
                await self._cleanup_task_resources(execution_id)

                # Update workflow instance
                instance_id = task_info.get("workflow_instance_id")
                if instance_id and instance_id in self.workflow_instances:
                    instance = self.workflow_instances[instance_id]
                    instance.failed_tasks.append(schedule.task_id)

                    # Check if workflow should fail
                    if len(instance.failed_tasks) > 0:  # Configure failure threshold
                        instance.status = WorkflowStatus.FAILED
                        instance.end_time = datetime.now()
                        logger.warning(f"Workflow failed due to task timeout: {instance_id}")

                logger.warning(f"Task timed out: {schedule.task_id}")

        except Exception as e:
            logger.error(f"Failed to handle task timeout: {e}")

    # Database operations
    async def _store_workflow(self, workflow: WorkflowDefinition):
        """Store workflow definition in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO workflow_definitions
                (workflow_id, name, description, version, tasks, dependencies, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                workflow.workflow_id,
                workflow.name,
                workflow.description,
                workflow.version,
                json.dumps(workflow.tasks),
                json.dumps(workflow.dependencies),
                json.dumps(workflow.metadata),
                workflow.created_at,
                workflow.updated_at
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to store workflow: {e}")

    async def _store_workflow_instance(self, instance: WorkflowInstance):
        """Store workflow instance in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO workflow_instances
                (instance_id, workflow_id, status, current_tasks, completed_tasks, failed_tasks,
                 start_time, end_time, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                instance.instance_id,
                instance.workflow_id,
                instance.status.value,
                json.dumps(instance.current_tasks),
                json.dumps(instance.completed_tasks),
                json.dumps(instance.failed_tasks),
                instance.start_time,
                instance.end_time,
                json.dumps(instance.metadata),
                instance.created_at
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to store workflow instance: {e}")

    # Public API methods
    async def get_workflow_status(self, instance_id: str) -> dict[str, Any] | None:
        """Get workflow instance status"""
        try:
            if instance_id not in self.workflow_instances:
                return None

            instance = self.workflow_instances[instance_id]
            workflow = self.workflows[instance.workflow_id]

            return {
                "instance_id": instance.instance_id,
                "workflow_name": workflow.name,
                "status": instance.status.value,
                "current_tasks": instance.current_tasks,
                "completed_tasks": instance.completed_tasks,
                "failed_tasks": instance.failed_tasks,
                "progress": len(instance.completed_tasks) / len(workflow.tasks),
                "start_time": instance.start_time.isoformat() if instance.start_time else None,
                "end_time": instance.end_time.isoformat() if instance.end_time else None,
                "metadata": instance.metadata
            }

        except Exception as e:
            logger.error(f"Failed to get workflow status: {e}")
            return None

    async def cancel_workflow(self, instance_id: str) -> bool:
        """Cancel a running workflow"""
        try:
            if instance_id not in self.workflow_instances:
                return False

            instance = self.workflow_instances[instance_id]
            if instance.status not in [WorkflowStatus.PENDING, WorkflowStatus.RUNNING]:
                return False

            # Cancel workflow
            instance.status = WorkflowStatus.CANCELLED
            instance.end_time = datetime.now()

            # Cancel running tasks
            for exec_id, task_info in list(self.running_tasks.items()):
                if task_info.get("workflow_instance_id") == instance_id:
                    await self._cleanup_task_resources(exec_id)

            # Store updated instance
            await self._store_workflow_instance(instance)

            logger.info(f"Workflow cancelled: {instance_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel workflow: {e}")
            return False

    async def get_system_status(self) -> dict[str, Any]:
        """Get orchestrator system status"""
        try:
            return {
                "status": "running",
                "workflows_registered": len(self.workflows),
                "workflows_running": len([i for i in self.workflow_instances.values()
                                        if i.status == WorkflowStatus.RUNNING]),
                "tasks_queued": len(self.task_queue),
                "tasks_running": len(self.running_tasks),
                "tasks_completed": len(self.completed_tasks),
                "resources_allocated": {
                    "cpu_cores": self.allocated_resources.cpu_cores,
                    "memory_gb": self.allocated_resources.memory_gb,
                    "gpu_count": self.allocated_resources.gpu_count,
                    "storage_gb": self.allocated_resources.storage_gb
                },
                "resources_available": {
                    "cpu_cores": self.available_resources.cpu_cores - self.allocated_resources.cpu_cores,
                    "memory_gb": self.available_resources.memory_gb - self.allocated_resources.memory_gb,
                    "gpu_count": self.available_resources.gpu_count - self.allocated_resources.gpu_count,
                    "storage_gb": self.available_resources.storage_gb - self.allocated_resources.storage_gb
                }
            }

        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {"status": "error", "error": str(e)}

    async def shutdown(self):
        """Shutdown the advanced orchestrator"""
        try:
            logger.info("Shutting down Advanced Orchestrator...")

            # Cancel background tasks
            for task in self.background_tasks:
                task.cancel()

            # Wait for tasks to complete
            await asyncio.gather(*self.background_tasks, return_exceptions=True)

            logger.info("Advanced Orchestrator shutdown completed")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

# Example usage
async def main():
    """Example usage of the Advanced Orchestrator"""
    config = {
        "database": {"path": "advanced_orchestrator.db"},
        "resources": {
            "cpu_cores": 8.0,
            "memory_gb": 16.0,
            "gpu_count": 1,
            "storage_gb": 100.0
        },
        "scheduling": {
            "strategy": "priority",
            "max_concurrent_tasks": 5,
            "task_timeout": 1800
        }
    }

    orchestrator = AdvancedOrchestrator(config)

    # Example workflow definition
    workflow = WorkflowDefinition(
        workflow_id="example_workflow",
        name="Example Data Processing Workflow",
        description="Process data through multiple stages",
        version="1.0.0",
        tasks=[
            {
                "task_id": "data_ingestion",
                "name": "Data Ingestion",
                "priority": 1,
                "estimated_duration": 300,
                "resources": {"cpu_cores": 2.0, "memory_gb": 4.0}
            },
            {
                "task_id": "data_processing",
                "name": "Data Processing",
                "priority": 2,
                "estimated_duration": 600,
                "resources": {"cpu_cores": 4.0, "memory_gb": 8.0},
                "dependencies": ["data_ingestion"]
            },
            {
                "task_id": "data_export",
                "name": "Data Export",
                "priority": 3,
                "estimated_duration": 120,
                "resources": {"cpu_cores": 1.0, "memory_gb": 2.0},
                "dependencies": ["data_processing"]
            }
        ],
        dependencies=[
            {
                "source_task": "data_ingestion",
                "target_task": "data_processing",
                "type": "requires"
            },
            {
                "source_task": "data_processing",
                "target_task": "data_export",
                "type": "requires"
            }
        ]
    )

    # Register workflow
    await orchestrator.register_workflow(workflow)

    # Start workflow
    instance_id = await orchestrator.start_workflow("example_workflow")

    if instance_id:
        print(f"Workflow started: {instance_id}")

        # Monitor workflow
        for i in range(30):  # Monitor for 30 seconds
            status = await orchestrator.get_workflow_status(instance_id)
            if status:
                print(f"Progress: {status['progress']:.1%} - Status: {status['status']}")

            if status and status['status'] in ['completed', 'failed', 'cancelled']:
                break

            await asyncio.sleep(1)

    # Shutdown
    await orchestrator.shutdown()

if __name__ == "__main__":
    asyncio.run(main())

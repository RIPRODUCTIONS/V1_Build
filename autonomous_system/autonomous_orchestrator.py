"""
Autonomous System Orchestrator

The main orchestrator that coordinates all components of the autonomous task solving system.
This provides a unified interface for starting, monitoring, and controlling the entire system.
"""

import asyncio
import logging
import signal
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .classification.task_classifier import TaskClassifier
from .discovery.task_detector import DetectedTask, TaskDetector
from .execution.task_executor import AutonomousTaskExecutor
from .intelligence.decision_engine import DecisionEngine, DecisionType
from .orchestration.model_selector import ModelSelector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SystemStatus:
    """Current status of the autonomous system"""
    status: str  # running, stopped, error, initializing
    components: dict[str, str]  # Component name -> status
    metrics: dict[str, Any]  # System performance metrics
    active_tasks: int
    queue_length: int
    uptime: float
    last_heartbeat: datetime
    errors: list[str]

class AutonomousOrchestrator:
    """Main orchestrator for the autonomous task solving system"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.running = False

        # Initialize components
        self.task_detector = None
        self.task_classifier = None
        self.model_selector = None
        self.task_executor = None
        self.decision_engine = None

        # System state
        self.system_status = SystemStatus(
            status="initializing",
            components={},
            metrics={},
            active_tasks=0,
            queue_length=0,
            uptime=0.0,
            last_heartbeat=datetime.now(),
            errors=[]
        )

        # Background tasks
        self.background_tasks = []

        # Setup signal handlers
        self._setup_signal_handlers()

        logger.info("Autonomous Orchestrator initialized")

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown")
            asyncio.create_task(self.shutdown())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def initialize(self):
        """Initialize all system components"""
        try:
            logger.info("Initializing autonomous system components...")

            # Initialize task detector
            self.task_detector = TaskDetector(self.config.get("task_detection", {}))
            self.system_status.components["task_detector"] = "initialized"
            logger.info("Task detector initialized")

            # Initialize task classifier
            self.task_classifier = TaskClassifier(
                self._get_mock_llm_manager(),  # Would be real LLM manager
                self.config.get("task_classification", {})
            )
            self.system_status.components["task_classifier"] = "initialized"
            logger.info("Task classifier initialized")

            # Initialize model selector
            self.model_selector = ModelSelector(
                self._get_mock_llm_manager(),  # Would be real LLM manager
                self._get_mock_cost_tracker(),  # Would be real cost tracker
                self.config.get("model_selection", {})
            )
            self.system_status.components["model_selector"] = "initialized"
            logger.info("Model selector initialized")

            # Initialize task executor
            self.task_executor = AutonomousTaskExecutor(
                self._get_mock_llm_manager(),  # Would be real LLM manager
                self._get_mock_agent_pool(),   # Would be real agent pool
                self._get_mock_tool_manager(), # Would be real tool manager
                self.config.get("task_execution", {})
            )
            self.system_status.components["task_executor"] = "initialized"
            logger.info("Task executor initialized")

            # Initialize decision engine
            self.decision_engine = DecisionEngine(self.config.get("decision_engine", {}))
            self.decision_engine.register_components(
                self.task_detector,
                self.task_classifier,
                self.model_selector,
                self.task_executor
            )
            self.system_status.components["decision_engine"] = "initialized"
            logger.info("Decision engine initialized")

            self.system_status.status = "initialized"
            logger.info("All system components initialized successfully")

        except Exception as e:
            error_msg = f"Failed to initialize system: {e}"
            logger.error(error_msg)
            self.system_status.status = "error"
            self.system_status.errors.append(error_msg)
            raise

    async def start(self):
        """Start the autonomous system"""
        if self.running:
            logger.warning("System is already running")
            return

        try:
            logger.info("Starting autonomous task solving system...")

            # Start all components
            await self._start_components()

            # Start background monitoring
            await self._start_background_monitoring()

            # Start main system loop
            await self._main_system_loop()

        except Exception as e:
            error_msg = f"Failed to start system: {e}"
            logger.error(error_msg)
            self.system_status.status = "error"
            self.system_status.errors.append(error_msg)
            raise

    async def _start_components(self):
        """Start all system components"""
        try:
            # Start task detection
            if self.task_detector:
                detection_task = asyncio.create_task(
                    self.task_detector.start_monitoring()
                )
                self.background_tasks.append(detection_task)
                logger.info("Task detection started")

            # Start task execution engine
            if self.task_executor:
                execution_task = asyncio.create_task(
                    self.task_executor.start_execution_engine()
                )
                self.background_tasks.append(execution_task)
                logger.info("Task execution engine started")

            # Start decision engine background processes
            if self.decision_engine:
                # Decision engine background processes are started in constructor
                logger.info("Decision engine background processes started")

            self.system_status.status = "running"
            self.system_status.last_heartbeat = datetime.now()
            logger.info("All components started successfully")

        except Exception as e:
            logger.error(f"Failed to start components: {e}")
            raise

    async def _start_background_monitoring(self):
        """Start background monitoring tasks"""
        try:
            # System health monitoring
            health_task = asyncio.create_task(self._monitor_system_health())
            self.background_tasks.append(health_task)

            # Performance metrics collection
            metrics_task = asyncio.create_task(self._collect_performance_metrics())
            self.background_tasks.append(metrics_task)

            # Task queue monitoring
            queue_task = asyncio.create_task(self._monitor_task_queue())
            self.background_tasks.append(queue_task)

            # Error monitoring and recovery
            recovery_task = asyncio.create_task(self._monitor_and_recover())
            self.background_tasks.append(recovery_task)

            logger.info("Background monitoring tasks started")

        except Exception as e:
            logger.error(f"Failed to start background monitoring: {e}")
            raise

    async def _main_system_loop(self):
        """Main system loop for continuous operation"""
        logger.info("Entering main system loop")

        try:
            while self.running:
                # Process discovered tasks
                await self._process_discovered_tasks()

                # Make system decisions
                await self._make_system_decisions()

                # Update system status
                await self._update_system_status()

                # Brief pause
                await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Main system loop failed: {e}")
            self.system_status.status = "error"
            self.system_status.errors.append(str(e))
            raise

    async def _process_discovered_tasks(self):
        """Process tasks discovered by the task detector"""
        try:
            if not self.task_detector:
                return

            # Get discovered tasks
            discovered_tasks = await self.task_detector.get_discovered_tasks(limit=10)

            for task in discovered_tasks:
                try:
                    # Classify the task
                    classification = await self.task_classifier.classify_task(task)

                    # Select optimal model
                    model_selection = await self.model_selector.select_optimal_model(
                        classification.__dict__,
                        self._get_task_constraints(task)
                    )

                    # Create workflow
                    workflow = await self._create_workflow_for_task(task, classification, model_selection)

                    # Submit for execution
                    await self._submit_task_for_execution(task, workflow)

                    logger.info(f"Task {task.id} processed and submitted for execution")

                except Exception as e:
                    logger.error(f"Failed to process task {task.id}: {e}")
                    self.system_status.errors.append(f"Task processing failed: {e}")

        except Exception as e:
            logger.error(f"Task processing loop failed: {e}")

    async def _create_workflow_for_task(self, task: DetectedTask, classification,
                                      model_selection) -> Any:
        """Create a workflow for task execution"""
        # This would create a proper WorkflowDefinition
        # For now, return a mock workflow
        from .execution.task_executor import WorkflowDefinition, WorkflowStep

        workflow = WorkflowDefinition(
            workflow_id=f"workflow_{task.id}",
            task_id=task.id,
            steps=[
                WorkflowStep(
                    step_id="step1",
                    step_type="task_execution",
                    agent="general_agent",
                    model=model_selection.selected_model,
                    tools=classification.required_tools,
                    parameters={"task": task.__dict__}
                )
            ],
            estimated_duration=classification.estimated_time_minutes,
            success_criteria=["task_completed", "quality_met"]
        )

        return workflow

    async def _submit_task_for_execution(self, task: DetectedTask, workflow):
        """Submit task for execution"""
        try:
            if self.task_executor:
                # Add to execution queue
                await self.task_executor.execution_queue.put({
                    'task': task,
                    'workflow': workflow
                })
                logger.info(f"Task {task.id} submitted for execution")

        except Exception as e:
            logger.error(f"Failed to submit task {task.id} for execution: {e}")

    async def _make_system_decisions(self):
        """Make system-level decisions for optimization"""
        try:
            if not self.decision_engine:
                return

            # Check if optimization is needed
            if await self._should_optimize_system():
                # Make optimization decision
                decision = await self.decision_engine.make_decision(
                    DecisionType.SYSTEM_OPTIMIZATION,
                    {'trigger': 'periodic_check', 'timestamp': datetime.now()}
                )

                logger.info(f"System optimization decision made: {decision.decision_id}")

        except Exception as e:
            logger.error(f"System decision making failed: {e}")

    async def _should_optimize_system(self) -> bool:
        """Check if system optimization is needed"""
        # Simple heuristic: optimize if error rate is high or performance is low
        if len(self.system_status.errors) > 5:
            return True

        if self.system_status.metrics.get('success_rate', 1.0) < 0.8:
            return True

        return False

    async def _monitor_system_health(self):
        """Monitor overall system health"""
        while self.running:
            try:
                # Check component health
                component_health = await self._check_component_health()

                # Update system status
                if any(status == "error" for status in component_health.values()):
                    self.system_status.status = "error"
                    logger.warning("System health check detected errors")
                else:
                    self.system_status.status = "running"

                # Update heartbeat
                self.system_status.last_heartbeat = datetime.now()

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Health monitoring failed: {e}")
                await asyncio.sleep(30)

    async def _check_component_health(self) -> dict[str, str]:
        """Check health of individual components"""
        health_status = {}

        try:
            # Check task detector
            if self.task_detector:
                health_status["task_detector"] = "healthy" if self.task_detector.running else "error"

            # Check task executor
            if self.task_executor:
                health_status["task_executor"] = "healthy" if hasattr(self.task_executor, 'running') else "error"

            # Check decision engine
            if self.decision_engine:
                health_status["decision_engine"] = "healthy"

        except Exception as e:
            logger.error(f"Component health check failed: {e}")
            health_status["system"] = "error"

        return health_status

    async def _collect_performance_metrics(self):
        """Collect and update performance metrics"""
        while self.running:
            try:
                # Collect metrics from components
                metrics = {}

                if self.task_executor:
                    execution_metrics = self.task_executor.get_execution_metrics()
                    metrics.update(execution_metrics)

                if self.decision_engine:
                    decision_metrics = self.decision_engine.get_decision_metrics()
                    metrics.update(decision_metrics)

                # Calculate derived metrics
                if metrics.get('total_tasks', 0) > 0:
                    success_rate = metrics.get('successful_tasks', 0) / metrics.get('total_tasks', 1)
                    metrics['success_rate'] = success_rate

                # Update system status
                self.system_status.metrics = metrics

                await asyncio.sleep(60)  # Update every minute

            except Exception as e:
                logger.error(f"Performance metrics collection failed: {e}")
                await asyncio.sleep(60)

    async def _monitor_task_queue(self):
        """Monitor task queue and execution status"""
        while self.running:
            try:
                if self.task_executor:
                    # Update queue length
                    self.system_status.queue_length = self.task_executor.execution_queue.qsize()

                    # Update active tasks
                    self.system_status.active_tasks = len(self.task_executor.running_tasks)

                await asyncio.sleep(10)  # Update every 10 seconds

            except Exception as e:
                logger.error(f"Task queue monitoring failed: {e}")
                await asyncio.sleep(10)

    async def _monitor_and_recover(self):
        """Monitor for errors and attempt recovery"""
        while self.running:
            try:
                # Check for critical errors
                if len(self.system_status.errors) > 10:
                    logger.error("Too many errors, attempting system recovery")
                    await self._attempt_system_recovery()

                # Clear old errors
                if len(self.system_status.errors) > 20:
                    self.system_status.errors = self.system_status.errors[-10:]

                await asyncio.sleep(120)  # Check every 2 minutes

            except Exception as e:
                logger.error(f"Error monitoring and recovery failed: {e}")
                await asyncio.sleep(120)

    async def _attempt_system_recovery(self):
        """Attempt to recover the system from errors"""
        try:
            logger.info("Attempting system recovery...")

            # Restart critical components
            if self.task_detector and not self.task_detector.running:
                await self.task_detector.start_monitoring()
                logger.info("Task detector restarted")

            if self.task_executor:
                # Restart execution engine if needed
                logger.info("Task executor recovery attempted")

            # Clear error list
            self.system_status.errors = []

            logger.info("System recovery completed")

        except Exception as e:
            logger.error(f"System recovery failed: {e}")

    async def _update_system_status(self):
        """Update overall system status"""
        try:
            # Update uptime
            if self.system_status.last_heartbeat:
                uptime = (datetime.now() - self.system_status.last_heartbeat).total_seconds()
                self.system_status.uptime = uptime

            # Update component statuses
            if self.task_detector:
                self.system_status.components["task_detector"] = "running" if self.task_detector.running else "stopped"

            if self.task_executor:
                self.system_status.components["task_executor"] = "running"

            if self.decision_engine:
                self.system_status.components["decision_engine"] = "running"

        except Exception as e:
            logger.error(f"System status update failed: {e}")

    async def shutdown(self):
        """Gracefully shutdown the autonomous system"""
        logger.info("Initiating graceful shutdown...")

        self.running = False
        self.system_status.status = "stopping"

        try:
            # Stop task detection
            if self.task_detector:
                await self.task_detector.stop_monitoring()
                logger.info("Task detection stopped")

            # Stop task execution
            if self.task_executor:
                # Task executor will stop when main loop exits
                logger.info("Task execution stopping")

            # Cancel background tasks
            for task in self.background_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            self.system_status.status = "stopped"
            logger.info("Autonomous system shutdown completed")

        except Exception as e:
            logger.error(f"Shutdown failed: {e}")
            self.system_status.status = "error"

    def get_system_status(self) -> SystemStatus:
        """Get current system status"""
        return self.system_status

    async def get_system_metrics(self) -> dict[str, Any]:
        """Get detailed system metrics"""
        metrics = {
            'system_status': self.system_status.__dict__,
            'timestamp': datetime.now().isoformat()
        }

        # Add component-specific metrics
        if self.task_executor:
            metrics['execution_metrics'] = self.task_executor.get_execution_metrics()

        if self.decision_engine:
            metrics['decision_metrics'] = self.decision_engine.get_decision_metrics()

        return metrics

    # Mock component methods for demonstration
    def _get_mock_llm_manager(self):
        """Get mock LLM manager for testing"""
        class MockLLMManager:
            async def generate(self, prompt, provider, model, stream=False):
                return "Mock response"

            async def get_model(self, model_name):
                return f"mock_model_{model_name}"

            async def release_model(self, model):
                pass

            async def get_alternative_models(self, model_name):
                return ["mock_alt_1", "mock_alt_2"]

        return MockLLMManager()

    def _get_mock_cost_tracker(self):
        """Get mock cost tracker for testing"""
        class MockCostTracker:
            pass

        return MockCostTracker()

    def _get_mock_agent_pool(self):
        """Get mock agent pool for testing"""
        class MockAgentPool:
            async def get_agent(self, agent_name):
                return f"mock_agent_{agent_name}"

            async def release_agent(self, agent):
                pass

            async def get_alternative_agents(self, agent_name):
                return ["mock_alt_agent_1", "mock_alt_agent_2"]

        return MockAgentPool()

    def _get_mock_tool_manager(self):
        """Get mock tool manager for testing"""
        class MockToolManager:
            def get_tool(self, tool_name):
                return f"mock_tool_{tool_name}"

            async def release_tool(self, tool):
                pass

        return MockToolManager()

    def _get_task_constraints(self, task: DetectedTask) -> dict[str, Any]:
        """Get constraints for a task"""
        return {
            'max_cost_per_task': 1.0,
            'max_latency_ms': 5000,
            'privacy_sensitive': False,
            'speed_priority': task.priority.value > 7,
            'quality_priority': task.estimated_complexity > 0.7
        }


# Example usage and main entry point
async def main():
    """Main entry point for the autonomous system"""
    # Configuration
    config = {
        "task_detection": {
            "email": {"enabled": True},
            "slack": {"enabled": True},
            "calendar": {"enabled": True},
            "webhook": {"enabled": True},
            "scheduled": {"enabled": True}
        },
        "task_classification": {
            "database": {"path": "task_classifier.db"}
        },
        "model_selection": {
            "database": {"path": "model_selector.db"}
        },
        "task_execution": {
            "max_concurrent_tasks": 10,
            "database": {"path": "task_executor.db"}
        },
        "decision_engine": {
            "database": {"path": "decision_engine.db"}
        }
    }

    # Create orchestrator
    orchestrator = AutonomousOrchestrator(config)

    try:
        # Initialize system
        await orchestrator.initialize()

        # Start system
        await orchestrator.start()

    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"System failed: {e}")
    finally:
        # Shutdown
        await orchestrator.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

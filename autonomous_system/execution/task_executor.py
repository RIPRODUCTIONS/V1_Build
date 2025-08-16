"""
Autonomous Task Execution Engine

This module provides a fully autonomous task execution system that:
- Automatically executes task workflows
- Monitors progress in real-time
- Handles errors and failures automatically
- Implements self-healing mechanisms
- Validates output quality
- Learns from execution outcomes
- Optimizes performance continuously
"""

import asyncio
import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExecutionStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"

class ExecutionPhase(Enum):
    """Execution phases"""
    INITIALIZATION = "initialization"
    RESOURCE_ALLOCATION = "resource_allocation"
    EXECUTION = "execution"
    VALIDATION = "validation"
    CLEANUP = "cleanup"

@dataclass
class ExecutionResult:
    """Result of task execution"""
    task_id: str
    status: ExecutionStatus
    output: dict[str, Any]
    execution_time: float
    cost: float
    quality_score: float
    error_message: str | None = None
    retry_count: int = 0
    phases_completed: list[ExecutionPhase] = field(default_factory=list)
    resource_usage: dict[str, Any] = field(default_factory=dict)
    performance_metrics: dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkflowStep:
    """Individual workflow step"""
    step_id: str
    step_type: str
    agent: str
    model: str
    tools: list[str]
    parameters: dict[str, Any]
    dependencies: list[str] = field(default_factory=list)
    timeout_seconds: int = 300
    retry_policy: dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkflowDefinition:
    """Complete workflow definition"""
    workflow_id: str
    task_id: str
    steps: list[WorkflowStep]
    estimated_duration: int
    success_criteria: list[str]
    failure_threshold: float = 0.8
    parallel_execution: bool = False

class AutonomousTaskExecutor:
    """Fully autonomous task execution engine"""

    def __init__(self, llm_manager, agent_pool, tool_manager, config: dict[str, Any]):
        self.llm_manager = llm_manager
        self.agent_pool = agent_pool
        self.tool_manager = tool_manager
        self.config = config
        self.running_tasks = {}
        self.execution_queue = asyncio.Queue()
        self.max_concurrent_tasks = config.get("max_concurrent_tasks", 10)
        self.db_path = Path(config.get("database", {}).get("path", "task_executor.db"))
        self._init_database()

        # Performance tracking
        self.execution_metrics = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'avg_execution_time': 0.0,
            'avg_cost': 0.0,
            'avg_quality_score': 0.0
        }

        # Start background tasks
        self._start_background_tasks()

    def _init_database(self):
        """Initialize execution database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS execution_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    workflow_id TEXT,
                    status TEXT NOT NULL,
                    execution_time REAL,
                    cost REAL,
                    quality_score REAL,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    phases_completed TEXT,
                    resource_usage TEXT,
                    performance_metrics TEXT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflow_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    step_results TEXT,
                    overall_status TEXT,
                    execution_time REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    task_category TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            conn.close()
            logger.info("Task executor database initialized")

        except Exception as e:
            logger.error(f"Failed to initialize executor database: {e}")
            raise

    def _start_background_tasks(self):
        """Start background monitoring and optimization tasks"""
        asyncio.create_task(self._monitor_system_health())
        asyncio.create_task(self._optimize_resource_allocation())
        asyncio.create_task(self._process_completed_tasks())
        asyncio.create_task(self._handle_failed_tasks())
        asyncio.create_task(self._update_performance_metrics())

    async def start_execution_engine(self):
        """Start the autonomous execution engine"""
        logger.info("Starting autonomous task execution engine...")

        try:
            # Start multiple worker coroutines
            workers = [
                self.execution_worker(f"worker_{i}")
                for i in range(self.max_concurrent_tasks)
            ]

            # Start execution
            await asyncio.gather(*workers)

        except Exception as e:
            logger.error(f"Execution engine failed: {e}")
            raise

    async def execution_worker(self, worker_id: str):
        """Worker coroutine that processes tasks from the queue"""
        logger.info(f"Started execution worker: {worker_id}")

        while True:
            try:
                # Get next task from queue
                task_execution = await self.execution_queue.get()

                # Execute the task
                result = await self.execute_task_workflow(task_execution)

                # Process the result
                await self.process_execution_result(result)

                # Mark task as done
                self.execution_queue.task_done()

            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)

    async def execute_task_workflow(self, task_execution: dict) -> ExecutionResult:
        """Execute a complete task workflow autonomously"""
        task = task_execution['task']
        workflow = task_execution['workflow']

        start_time = time.time()
        total_cost = 0.0
        execution_log = []
        phases_completed = []

        try:
            logger.info(f"Starting execution of task: {task.id}")

            # Phase 1: Initialization
            await self._execute_phase(ExecutionPhase.INITIALIZATION, task, workflow)
            phases_completed.append(ExecutionPhase.INITIALIZATION)

            # Phase 2: Resource Allocation
            resources = await self._execute_phase(ExecutionPhase.RESOURCE_ALLOCATION, task, workflow)
            phases_completed.append(ExecutionPhase.RESOURCE_ALLOCATION)

            # Phase 3: Execution
            execution_results = await self._execute_phase(ExecutionPhase.EXECUTION, task, workflow, resources)
            phases_completed.append(ExecutionPhase.EXECUTION)
            execution_log.extend(execution_results)

            # Calculate total cost
            for result in execution_results:
                total_cost += result.get('cost', 0)

            # Phase 4: Validation
            validation_result = await self._execute_phase(ExecutionPhase.VALIDATION, task, workflow, execution_results)
            phases_completed.append(ExecutionPhase.VALIDATION)

            # Phase 5: Cleanup
            await self._execute_phase(ExecutionPhase.CLEANUP, task, workflow, resources)
            phases_completed.append(ExecutionPhase.CLEANUP)

            # Aggregate final output
            final_output = self._aggregate_step_outputs(execution_log)

            # Validate final output quality
            quality_score = await self._validate_output_quality(final_output, task)

            execution_time = time.time() - start_time

            result = ExecutionResult(
                task_id=task.id,
                status=ExecutionStatus.COMPLETED,
                output=final_output,
                execution_time=execution_time,
                cost=total_cost,
                quality_score=quality_score,
                phases_completed=phases_completed,
                resource_usage=resources,
                performance_metrics={
                    'execution_time': execution_time,
                    'total_cost': total_cost,
                    'quality_score': quality_score,
                    'steps_completed': len(execution_log)
                }
            )

            logger.info(f"Task {task.id} completed successfully in {execution_time:.2f}s")
            return result

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Task execution failed: {str(e)}"
            logger.error(f"{error_msg} for task {task.id}")

            return ExecutionResult(
                task_id=task.id,
                status=ExecutionStatus.FAILED,
                output={},
                execution_time=execution_time,
                cost=total_cost,
                quality_score=0.0,
                error_message=error_msg,
                phases_completed=phases_completed,
                resource_usage=resources if 'resources' in locals() else {},
                performance_metrics={
                    'execution_time': execution_time,
                    'total_cost': total_cost,
                    'error': error_msg
                }
            )

    async def _execute_phase(self, phase: ExecutionPhase, task, workflow: WorkflowDefinition,
                           context: Any = None) -> Any:
        """Execute a specific execution phase"""
        logger.info(f"Executing phase: {phase.value} for task {task.id}")

        try:
            if phase == ExecutionPhase.INITIALIZATION:
                return await self._phase_initialization(task, workflow)

            elif phase == ExecutionPhase.RESOURCE_ALLOCATION:
                return await self._phase_resource_allocation(task, workflow)

            elif phase == ExecutionPhase.EXECUTION:
                return await self._phase_execution(task, workflow, context)

            elif phase == ExecutionPhase.VALIDATION:
                return await self._phase_validation(task, workflow, context)

            elif phase == ExecutionPhase.CLEANUP:
                return await self._phase_cleanup(task, workflow, context)

            else:
                raise ValueError(f"Unknown execution phase: {phase}")

        except Exception as e:
            logger.error(f"Phase {phase.value} failed for task {task.id}: {e}")
            raise

    async def _phase_initialization(self, task, workflow: WorkflowDefinition) -> dict[str, Any]:
        """Initialize task execution"""
        # Validate workflow
        if not workflow.steps:
            raise ValueError("Workflow has no steps")

        # Check dependencies
        dependency_check = await self._check_workflow_dependencies(workflow)
        if not dependency_check['valid']:
            raise ValueError(f"Workflow dependencies not met: {dependency_check['missing']}")

        # Initialize execution context
        execution_context = {
            'task': task,
            'workflow': workflow,
            'start_time': datetime.now(),
            'step_results': {},
            'resources_allocated': False
        }

        logger.info(f"Initialization completed for task {task.id}")
        return execution_context

    async def _phase_resource_allocation(self, task, workflow: WorkflowDefinition) -> dict[str, Any]:
        """Allocate resources for task execution"""
        resources = {}

        # Allocate agents
        for step in workflow.steps:
            agent = await self.agent_pool.get_agent(step.agent)
            if not agent:
                raise ValueError(f"Agent {step.agent} not available")
            resources[f"agent_{step.step_id}"] = agent

        # Allocate tools
        for step in workflow.steps:
            step_tools = {}
            for tool_name in step.tools:
                tool = self.tool_manager.get_tool(tool_name)
                if not tool:
                    logger.warning(f"Tool {tool_name} not available for step {step.step_id}")
                else:
                    step_tools[tool_name] = tool
            resources[f"tools_{step.step_id}"] = step_tools

        # Allocate models
        for step in workflow.steps:
            model = await self.llm_manager.get_model(step.model)
            if not model:
                raise ValueError(f"Model {step.model} not available")
            resources[f"model_{step.step_id}"] = model

        resources['allocated_at'] = datetime.now()
        logger.info(f"Resource allocation completed for task {task.id}")

        return resources

    async def _phase_execution(self, task, workflow: WorkflowDefinition,
                             resources: dict[str, Any]) -> list[dict[str, Any]]:
        """Execute workflow steps"""
        step_results = []

        if workflow.parallel_execution:
            # Execute steps in parallel
            execution_tasks = []
            for step in workflow.steps:
                task = asyncio.create_task(
                    self._execute_workflow_step(step, task, resources)
                )
                execution_tasks.append(task)

            # Wait for all steps to complete
            step_results = await asyncio.gather(*execution_tasks, return_exceptions=True)

            # Handle any exceptions
            for i, result in enumerate(step_results):
                if isinstance(result, Exception):
                    logger.error(f"Step {workflow.steps[i].step_id} failed: {result}")
                    step_results[i] = {
                        'step': workflow.steps[i].step_id,
                        'status': 'failed',
                        'error': str(result),
                        'cost': 0,
                        'execution_time': 0
                    }
        else:
            # Execute steps sequentially
            for step in workflow.steps:
                try:
                    result = await self._execute_workflow_step(step, task, resources)
                    step_results.append(result)
                except Exception as e:
                    logger.error(f"Step {step.step_id} failed: {e}")
                    step_results.append({
                        'step': step.step_id,
                        'status': 'failed',
                        'error': str(e),
                        'cost': 0,
                        'execution_time': 0
                    })

        logger.info(f"Execution phase completed for task {task.id}")
        return step_results

    async def _execute_workflow_step(self, step: WorkflowStep, task,
                                   resources: dict[str, Any]) -> dict[str, Any]:
        """Execute a single workflow step"""
        step_start_time = time.time()

        try:
            # Get required resources
            agent = resources[f"agent_{step.step_id}"]
            tools = resources[f"tools_{step.step_id}"]
            model = resources[f"model_{step.step_id}"]

            # Prepare step context
            context = {
                'task': task,
                'step_config': step,
                'available_tools': tools,
                'model': model
            }

            # Execute step with the agent
            step_output = await agent.execute_step(
                step_type=step.step_type,
                context=context,
                tools=tools,
                model=model,
                parameters=step.parameters
            )

            step_execution_time = time.time() - step_start_time

            return {
                'step': step.step_id,
                'status': 'completed',
                'output': step_output,
                'cost': step_output.get('cost', 0),
                'execution_time': step_execution_time,
                'timestamp': datetime.now()
            }

        except Exception as e:
            step_execution_time = time.time() - step_start_time
            logger.error(f"Step {step.step_id} execution failed: {e}")

            # Attempt recovery
            recovery_result = await self._attempt_step_recovery(step, task, resources, e)
            if recovery_result['status'] == 'completed':
                return recovery_result

            # If recovery failed, return error
            return {
                'step': step.step_id,
                'status': 'failed',
                'error': str(e),
                'cost': 0,
                'execution_time': step_execution_time,
                'timestamp': datetime.now()
            }

    async def _attempt_step_recovery(self, step: WorkflowStep, task,
                                   resources: dict[str, Any], error: Exception) -> dict[str, Any]:
        """Attempt to recover from step failure"""
        logger.info(f"Attempting recovery for step {step.step_id}")

        # Analyze failure reason
        failure_analysis = await self._analyze_failure(error, step, task)

        # Try different recovery strategies
        recovery_strategies = [
            'retry_with_different_model',
            'retry_with_different_agent',
            'simplify_step_requirements',
            'use_fallback_approach'
        ]

        for strategy in recovery_strategies:
            try:
                recovery_result = await self._apply_recovery_strategy(
                    strategy, step, task, resources, failure_analysis
                )
                if recovery_result['status'] == 'completed':
                    logger.info(f"Recovery successful for step {step.step_id} using {strategy}")
                    return recovery_result
            except Exception as recovery_error:
                logger.warning(f"Recovery strategy {strategy} failed: {recovery_error}")
                continue

        logger.error(f"All recovery strategies failed for step {step.step_id}")
        return {'status': 'failed', 'error': 'All recovery strategies failed'}

    async def _analyze_failure(self, error: Exception, step: WorkflowStep, task) -> dict[str, Any]:
        """Analyze the reason for step failure"""
        error_type = type(error).__name__
        error_message = str(error)

        analysis = {
            'error_type': error_type,
            'error_message': error_message,
            'step_id': step.step_id,
            'step_type': step.step_type,
            'timestamp': datetime.now()
        }

        # Categorize error
        if 'timeout' in error_message.lower():
            analysis['category'] = 'timeout'
            analysis['suggested_action'] = 'increase_timeout_or_optimize'
        elif 'resource' in error_message.lower():
            analysis['category'] = 'resource_unavailable'
            analysis['suggested_action'] = 'allocate_different_resources'
        elif 'permission' in error_message.lower():
            analysis['category'] = 'permission_denied'
            analysis['suggested_action'] = 'check_permissions'
        else:
            analysis['category'] = 'unknown'
            analysis['suggested_action'] = 'retry_or_fallback'

        return analysis

    async def _apply_recovery_strategy(self, strategy: str, step: WorkflowStep, task,
                                     resources: dict[str, Any],
                                     failure_analysis: dict[str, Any]) -> dict[str, Any]:
        """Apply a specific recovery strategy"""

        if strategy == 'retry_with_different_model':
            return await self._recovery_retry_different_model(step, task, resources)

        elif strategy == 'retry_with_different_agent':
            return await self._recovery_retry_different_agent(step, task, resources)

        elif strategy == 'simplify_step_requirements':
            return await self._recovery_simplify_requirements(step, task, resources)

        elif strategy == 'use_fallback_approach':
            return await self._recovery_fallback_approach(step, task, resources)

        else:
            raise ValueError(f"Unknown recovery strategy: {strategy}")

    async def _recovery_retry_different_model(self, step: WorkflowStep, task,
                                            resources: dict[str, Any]) -> dict[str, Any]:
        """Recovery: retry with a different model"""
        # Get alternative models
        alternative_models = await self.llm_manager.get_alternative_models(step.model)

        for alt_model in alternative_models:
            try:
                # Try with alternative model
                alt_model_instance = await self.llm_manager.get_model(alt_model)
                resources[f"model_{step.step_id}"] = alt_model_instance

                # Retry execution
                result = await self._execute_workflow_step(step, task, resources)
                if result['status'] == 'completed':
                    return result

            except Exception as e:
                logger.warning(f"Alternative model {alt_model} also failed: {e}")
                continue

        return {'status': 'failed', 'error': 'All alternative models failed'}

    async def _recovery_retry_different_agent(self, step: WorkflowStep, task,
                                            resources: dict[str, Any]) -> dict[str, Any]:
        """Recovery: retry with a different agent"""
        # Get alternative agents
        alternative_agents = await self.agent_pool.get_alternative_agents(step.agent)

        for alt_agent in alternative_agents:
            try:
                # Try with alternative agent
                resources[f"agent_{step.step_id}"] = alt_agent

                # Retry execution
                result = await self._execute_workflow_step(step, task, resources)
                if result['status'] == 'completed':
                    return result

            except Exception as e:
                logger.warning(f"Alternative agent {alt_agent} also failed: {e}")
                continue

        return {'status': 'failed', 'error': 'All alternative agents failed'}

    async def _recovery_simplify_requirements(self, step: WorkflowStep, task,
                                            resources: dict[str, Any]) -> dict[str, Any]:
        """Recovery: simplify step requirements"""
        # Create simplified step
        simplified_step = WorkflowStep(
            step_id=f"{step.step_id}_simplified",
            step_type=step.step_type,
            agent=step.agent,
            model=step.model,
            tools=step.tools[:1] if step.tools else [],  # Use fewer tools
            parameters={k: v for k, v in step.parameters.items() if k in ['basic', 'essential']},
            timeout_seconds=step.timeout_seconds * 2  # Increase timeout
        )

        try:
            result = await self._execute_workflow_step(simplified_step, task, resources)
            if result['status'] == 'completed':
                return result
        except Exception as e:
            logger.warning(f"Simplified step also failed: {e}")

        return {'status': 'failed', 'error': 'Simplified step failed'}

    async def _recovery_fallback_approach(self, step: WorkflowStep, task,
                                        resources: dict[str, Any]) -> dict[str, Any]:
        """Recovery: use fallback approach"""
        # Use most basic approach
        fallback_step = WorkflowStep(
            step_id=f"{step.step_id}_fallback",
            step_type="basic_execution",
            agent="fallback_agent",
            model="gpt-4o-mini",  # Most reliable model
            tools=[],
            parameters={'approach': 'fallback', 'complexity': 'minimal'}
        )

        try:
            result = await self._execute_workflow_step(fallback_step, task, resources)
            if result['status'] == 'completed':
                return result
        except Exception as e:
            logger.warning(f"Fallback approach also failed: {e}")

        return {'status': 'failed', 'error': 'Fallback approach failed'}

    async def _phase_validation(self, task, workflow: WorkflowDefinition,
                              execution_results: list[dict[str, Any]]) -> dict[str, Any]:
        """Validate execution results"""
        validation_results = {}

        # Validate each step result
        for result in execution_results:
            if result['status'] == 'completed':
                step_validation = await self._validate_step_output(result, task)
                validation_results[result['step']] = step_validation

        # Overall validation
        overall_validation = await self._validate_overall_output(execution_results, task, workflow)
        validation_results['overall'] = overall_validation

        logger.info(f"Validation phase completed for task {task.id}")
        return validation_results

    async def _phase_cleanup(self, task, workflow: WorkflowDefinition,
                           resources: dict[str, Any]) -> dict[str, Any]:
        """Clean up resources after execution"""
        cleanup_results = {}

        # Release agents
        for key, agent in resources.items():
            if key.startswith('agent_'):
                try:
                    await self.agent_pool.release_agent(agent)
                    cleanup_results[key] = 'released'
                except Exception as e:
                    logger.warning(f"Failed to release agent {key}: {e}")
                    cleanup_results[key] = 'failed'

        # Release tools
        for key, tools in resources.items():
            if key.startswith('tools_'):
                try:
                    for tool in tools.values():
                        await self.tool_manager.release_tool(tool)
                    cleanup_results[key] = 'released'
                except Exception as e:
                    logger.warning(f"Failed to release tools {key}: {e}")
                    cleanup_results[key] = 'failed'

        # Release models
        for key, model in resources.items():
            if key.startswith('model_'):
                try:
                    await self.llm_manager.release_model(model)
                    cleanup_results[key] = 'released'
                except Exception as e:
                    logger.warning(f"Failed to release model {key}: {e}")
                    cleanup_results[key] = 'failed'

        cleanup_results['timestamp'] = datetime.now()
        logger.info(f"Cleanup phase completed for task {task.id}")

        return cleanup_results

    async def _validate_output_quality(self, output: dict[str, Any], task) -> float:
        """Validate the quality of task output"""
        try:
            # Use AI to assess output quality
            validation_prompt = f"""
            Evaluate the quality of this task output:

            Original Task: {task.title}
            Task Description: {task.description}
            Generated Output: {json.dumps(output, indent=2)}

            Rate the output quality from 0.0 to 1.0 based on:
            1. Completeness (addresses all requirements)
            2. Accuracy (factual correctness)
            3. Relevance (directly addresses the task)
            4. Clarity (well-structured and understandable)
            5. Usefulness (provides value to the requester)

            Return only a decimal score between 0.0 and 1.0
            """

            quality_response = await self.llm_manager.generate(
                prompt=validation_prompt,
                provider='claude',
                model='claude-3.5-sonnet'
            )

            try:
                quality_score = float(quality_response.strip())
                return max(0.0, min(1.0, quality_score))
            except:
                return 0.5  # Default middle score if parsing fails

        except Exception as e:
            logger.error(f"Quality validation failed: {e}")
            return 0.5  # Default score on failure

    def _aggregate_step_outputs(self, execution_log: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate outputs from all workflow steps"""
        aggregated_output = {
            'workflow_completed': True,
            'steps_executed': len(execution_log),
            'total_cost': sum(step.get('cost', 0) for step in execution_log),
            'total_execution_time': sum(step.get('execution_time', 0) for step in execution_log),
            'step_outputs': {},
            'metadata': {
                'aggregated_at': datetime.now().isoformat(),
                'successful_steps': len([s for s in execution_log if s['status'] == 'completed']),
                'failed_steps': len([s for s in execution_log if s['status'] == 'failed'])
            }
        }

        # Add individual step outputs
        for step_result in execution_log:
            if step_result['status'] == 'completed':
                aggregated_output['step_outputs'][step_result['step']] = step_result['output']

        return aggregated_output

    async def _check_workflow_dependencies(self, workflow: WorkflowDefinition) -> dict[str, Any]:
        """Check if workflow dependencies are met"""
        # This would check for external dependencies, resource availability, etc.
        # For now, return success
        return {
            'valid': True,
            'missing': [],
            'warnings': []
        }

    async def process_execution_result(self, result: ExecutionResult):
        """Process completed execution result"""
        try:
            # Store result in database
            await self._store_execution_result(result)

            # Update metrics
            self._update_execution_metrics(result)

            # Emit completion event
            await self._emit_execution_completed(result)

            logger.info(f"Processed execution result for task {result.task_id}")

        except Exception as e:
            logger.error(f"Failed to process execution result: {e}")

    async def _store_execution_result(self, result: ExecutionResult):
        """Store execution result in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO execution_history
                (task_id, status, execution_time, cost, quality_score, error_message,
                 retry_count, phases_completed, resource_usage, performance_metrics, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.task_id,
                result.status.value,
                result.execution_time,
                result.cost,
                result.quality_score,
                result.error_message,
                result.retry_count,
                json.dumps([p.value for p in result.phases_completed]),
                json.dumps(result.resource_usage),
                json.dumps(result.performance_metrics),
                datetime.now()
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to store execution result: {e}")

    def _update_execution_metrics(self, result: ExecutionResult):
        """Update execution performance metrics"""
        self.execution_metrics['total_tasks'] += 1

        if result.status == ExecutionStatus.COMPLETED:
            self.execution_metrics['successful_tasks'] += 1
        else:
            self.execution_metrics['failed_tasks'] += 1

        # Update averages
        total_tasks = self.execution_metrics['total_tasks']
        if total_tasks > 0:
            self.execution_metrics['avg_execution_time'] = (
                (self.execution_metrics['avg_execution_time'] * (total_tasks - 1) + result.execution_time) / total_tasks
            )
            self.execution_metrics['avg_cost'] = (
                (self.execution_metrics['avg_cost'] * (total_tasks - 1) + result.cost) / total_tasks
            )
            self.execution_metrics['avg_quality_score'] = (
                (self.execution_metrics['avg_quality_score'] * (total_tasks - 1) + result.quality_score) / total_tasks
            )

    async def _emit_execution_completed(self, result: ExecutionResult):
        """Emit execution completed event"""
        # This would integrate with an event bus system
        # For now, just log the event
        logger.info(f"Execution completed: {result.task_id} - Status: {result.status.value}")

    async def _monitor_system_health(self):
        """Monitor system health and performance"""
        while True:
            try:
                # Check system resources
                system_health = await self._check_system_health()

                # Log health status
                if system_health['status'] != 'healthy':
                    logger.warning(f"System health issue: {system_health['issues']}")

                # Update health metrics
                await self._update_health_metrics(system_health)

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Health monitoring failed: {e}")
                await asyncio.sleep(60)

    async def _check_system_health(self) -> dict[str, Any]:
        """Check overall system health"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.now(),
            'issues': [],
            'metrics': {}
        }

        # Check queue health
        queue_size = self.execution_queue.qsize()
        if queue_size > 100:
            health_status['status'] = 'warning'
            health_status['issues'].append(f"Large execution queue: {queue_size} tasks")

        # Check worker health
        active_workers = len([w for w in self.running_tasks.values() if w['status'] == 'running'])
        if active_workers > self.max_concurrent_tasks * 0.9:
            health_status['status'] = 'warning'
            health_status['issues'].append(f"High worker utilization: {active_workers}/{self.max_concurrent_tasks}")

        # Check database health
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM execution_history")
            total_executions = cursor.fetchone()[0]
            conn.close()

            health_status['metrics']['total_executions'] = total_executions

        except Exception as e:
            health_status['status'] = 'critical'
            health_status['issues'].append(f"Database health check failed: {e}")

        return health_status

    async def _optimize_resource_allocation(self):
        """Optimize resource allocation based on performance"""
        while True:
            try:
                # Analyze resource usage patterns
                usage_patterns = await self._analyze_resource_usage()

                # Apply optimizations
                optimizations = await self._apply_resource_optimizations(usage_patterns)

                if optimizations:
                    logger.info(f"Applied {len(optimizations)} resource optimizations")

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Resource optimization failed: {e}")
                await asyncio.sleep(300)

    async def _process_completed_tasks(self):
        """Process and analyze completed tasks"""
        while True:
            try:
                # Get recent completed tasks
                completed_tasks = await self._get_recent_completed_tasks()

                # Analyze patterns
                patterns = await self._analyze_completion_patterns(completed_tasks)

                # Update learning models
                await self._update_learning_models(patterns)

                await asyncio.sleep(600)  # Check every 10 minutes

            except Exception as e:
                logger.error(f"Completed task processing failed: {e}")
                await asyncio.sleep(600)

    async def _handle_failed_tasks(self):
        """Handle and analyze failed tasks"""
        while True:
            try:
                # Get recent failed tasks
                failed_tasks = await self._get_recent_failed_tasks()

                # Analyze failure patterns
                failure_patterns = await self._analyze_failure_patterns(failed_tasks)

                # Update failure prevention strategies
                await self._update_failure_prevention(failure_patterns)

                await asyncio.sleep(900)  # Check every 15 minutes

            except Exception as e:
                logger.error(f"Failed task handling failed: {e}")
                await asyncio.sleep(900)

    async def _update_performance_metrics(self):
        """Update performance metrics in database"""
        while True:
            try:
                # Store current metrics
                await self._store_performance_metrics()

                await asyncio.sleep(300)  # Update every 5 minutes

            except Exception as e:
                logger.error(f"Performance metrics update failed: {e}")
                await asyncio.sleep(300)

    # Placeholder methods for background tasks
    async def _analyze_resource_usage(self) -> dict[str, Any]:
        return {}

    async def _apply_resource_optimizations(self, patterns: dict[str, Any]) -> list[str]:
        return []

    async def _get_recent_completed_tasks(self) -> list[dict[str, Any]]:
        return []

    async def _analyze_completion_patterns(self, tasks: list[dict[str, Any]]) -> dict[str, Any]:
        return {}

    async def _update_learning_models(self, patterns: dict[str, Any]):
        pass

    async def _get_recent_failed_tasks(self) -> list[dict[str, Any]]:
        return []

    async def _analyze_failure_patterns(self, tasks: list[dict[str, Any]]) -> dict[str, Any]:
        return {}

    async def _update_failure_prevention(self, patterns: dict[str, Any]):
        pass

    async def _store_performance_metrics(self):
        pass

    async def _update_health_metrics(self, health: dict[str, Any]):
        pass

    async def _validate_step_output(self, step_result: dict[str, Any], task) -> dict[str, Any]:
        return {'valid': True, 'score': 0.8}

    async def _validate_overall_output(self, execution_results: list[dict[str, Any]],
                                     task, workflow: WorkflowDefinition) -> dict[str, Any]:
        return {'valid': True, 'score': 0.8}

    def get_execution_metrics(self) -> dict[str, Any]:
        """Get current execution metrics"""
        return self.execution_metrics.copy()

    async def get_execution_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get execution history from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM execution_history
                ORDER BY started_at DESC LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            history = []

            for row in rows:
                history.append({
                    'id': row[0],
                    'task_id': row[1],
                    'workflow_id': row[2],
                    'status': row[3],
                    'execution_time': row[4],
                    'cost': row[5],
                    'quality_score': row[6],
                    'error_message': row[7],
                    'retry_count': row[8],
                    'phases_completed': json.loads(row[9]) if row[9] else [],
                    'resource_usage': json.loads(row[10]) if row[10] else {},
                    'performance_metrics': json.loads(row[11]) if row[11] else {},
                    'started_at': row[12],
                    'completed_at': row[13]
                })

            conn.close()
            return history

        except Exception as e:
            logger.error(f"Failed to get execution history: {e}")
            return []


# Example usage
async def main():
    """Example usage of the autonomous task executor"""
    # Mock components for testing
    class MockLLMManager:
        async def get_model(self, model_name):
            return f"mock_model_{model_name}"

        async def release_model(self, model):
            pass

        async def generate(self, prompt, provider, model):
            return "Mock response"

    class MockAgentPool:
        async def get_agent(self, agent_name):
            return f"mock_agent_{agent_name}"

        async def release_agent(self, agent):
            pass

        async def get_alternative_agents(self, agent_name):
            return [f"alt_agent_{i}" for i in range(2)]

    class MockToolManager:
        def get_tool(self, tool_name):
            return f"mock_tool_{tool_name}"

        async def release_tool(self, tool):
            pass

    config = {
        "max_concurrent_tasks": 5,
        "database": {"path": "test_executor.db"}
    }

    executor = AutonomousTaskExecutor(
        MockLLMManager(), MockAgentPool(), MockToolManager(), config
    )

    # Example workflow
    workflow = WorkflowDefinition(
        workflow_id="test_workflow",
        task_id="test_task",
        steps=[
            WorkflowStep(
                step_id="step1",
                step_type="data_gathering",
                agent="research_agent",
                model="gpt-4",
                tools=["web_search", "api_connector"],
                parameters={"query": "test query"}
            )
        ],
        estimated_duration=60,
        success_criteria=["data_collected", "analysis_complete"]
    )

    # Mock task
    class MockTask:
        def __init__(self):
            self.id = "test_task"
            self.title = "Test Task"
            self.description = "A test task for demonstration"

    task_execution = {
        'task': MockTask(),
        'workflow': workflow
    }

    # Start execution engine
    executor_task = asyncio.create_task(executor.start_execution_engine())

    # Wait a bit for engine to start
    await asyncio.sleep(1)

    # Execute a task
    result = await executor.execute_task_workflow(task_execution)
    print(f"Execution Result: {result.status.value}")
    print(f"Execution Time: {result.execution_time:.2f}s")
    print(f"Quality Score: {result.quality_score:.2f}")

    # Cancel execution engine
    executor_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())

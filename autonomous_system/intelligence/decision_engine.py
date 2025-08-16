"""
Central Decision Engine for Autonomous Task Solver System

This module provides the core intelligence that orchestrates the entire autonomous system:
- Central decision making for task routing
- Context-aware processing and planning
- Goal-oriented task management
- System adaptation and optimization
- Intelligent resource allocation
- Performance monitoring and learning
"""

import asyncio
import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DecisionType(Enum):
    """Types of decisions the system can make"""
    TASK_ROUTING = "task_routing"
    RESOURCE_ALLOCATION = "resource_allocation"
    MODEL_SELECTION = "model_selection"
    AGENT_ASSIGNMENT = "agent_assignment"
    PRIORITY_ADJUSTMENT = "priority_adjustment"
    SYSTEM_OPTIMIZATION = "system_optimization"
    FAILURE_RECOVERY = "failure_recovery"
    LEARNING_UPDATE = "learning_update"

class DecisionStatus(Enum):
    """Status of a decision"""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class Decision:
    """Represents a decision made by the system"""
    decision_id: str
    decision_type: DecisionType
    context: dict[str, Any]
    reasoning: str
    confidence: float
    alternatives: list[dict[str, Any]]
    selected_action: dict[str, Any]
    status: DecisionStatus
    created_at: datetime
    executed_at: datetime | None = None
    outcome: dict[str, Any] | None = None
    learning_insights: list[str] = field(default_factory=list)

@dataclass
class SystemGoal:
    """System goal for optimization"""
    goal_id: str
    name: str
    description: str
    priority: int
    target_metrics: dict[str, Any]
    current_metrics: dict[str, Any]
    deadline: datetime | None
    status: str = "active"
    progress: float = 0.0

@dataclass
class ContextSnapshot:
    """Snapshot of system context for decision making"""
    timestamp: datetime
    system_load: float
    resource_availability: dict[str, Any]
    active_tasks: int
    queue_length: int
    recent_performance: dict[str, Any]
    error_rates: dict[str, float]
    cost_metrics: dict[str, float]
    quality_metrics: dict[str, float]

class DecisionEngine:
    """Central decision engine for the autonomous system"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.db_path = Path(config.get("database", {}).get("path", "decision_engine.db"))
        self._init_database()

        # System components (will be injected)
        self.task_detector = None
        self.task_classifier = None
        self.model_selector = None
        self.task_executor = None

        # Decision tracking
        self.decisions: dict[str, Decision] = {}
        self.active_goals: dict[str, SystemGoal] = {}
        self.context_history: list[ContextSnapshot] = []

        # Performance tracking
        self.decision_metrics = {
            'total_decisions': 0,
            'successful_decisions': 0,
            'failed_decisions': 0,
            'avg_decision_time': 0.0,
            'avg_confidence': 0.0,
            'learning_cycles': 0
        }

        # Start background processes
        self._start_background_processes()

    def _init_database(self):
        """Initialize decision engine database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS decisions (
                    decision_id TEXT PRIMARY KEY,
                    decision_type TEXT NOT NULL,
                    context TEXT,
                    reasoning TEXT,
                    confidence REAL,
                    alternatives TEXT,
                    selected_action TEXT,
                    status TEXT,
                    created_at TIMESTAMP,
                    executed_at TIMESTAMP,
                    outcome TEXT,
                    learning_insights TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_goals (
                    goal_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    priority INTEGER,
                    target_metrics TEXT,
                    current_metrics TEXT,
                    deadline TEXT,
                    status TEXT,
                    progress REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS context_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP,
                    system_load REAL,
                    resource_availability TEXT,
                    active_tasks INTEGER,
                    queue_length INTEGER,
                    recent_performance TEXT,
                    error_rates TEXT,
                    cost_metrics TEXT,
                    quality_metrics TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS decision_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    decision_type TEXT NOT NULL,
                    success_rate REAL,
                    avg_execution_time REAL,
                    avg_confidence REAL,
                    total_decisions INTEGER,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            conn.close()
            logger.info("Decision engine database initialized")

        except Exception as e:
            logger.error(f"Failed to initialize decision engine database: {e}")
            raise

    def _start_background_processes(self):
        """Start background monitoring and optimization processes"""
        asyncio.create_task(self._monitor_system_context())
        asyncio.create_task(self._optimize_system_performance())
        asyncio.create_task(self._update_learning_models())
        asyncio.create_task(self._manage_system_goals())

    def register_components(self, task_detector, task_classifier, model_selector, task_executor):
        """Register system components for decision making"""
        self.task_detector = task_detector
        self.task_classifier = task_classifier
        self.model_selector = model_selector
        self.task_executor = task_executor
        logger.info("System components registered with decision engine")

    async def make_decision(self, decision_type: DecisionType, context: dict[str, Any]) -> Decision:
        """Make an intelligent decision based on context and goals"""
        start_time = time.time()

        try:
            # Capture current system context
            current_context = await self._capture_system_context()

            # Analyze context and requirements
            analysis = await self._analyze_decision_context(decision_type, context, current_context)

            # Generate decision alternatives
            alternatives = await self._generate_alternatives(decision_type, analysis)

            # Evaluate alternatives
            evaluated_alternatives = await self._evaluate_alternatives(alternatives, analysis)

            # Select best alternative
            selected_action = await self._select_best_alternative(evaluated_alternatives, analysis)

            # Create decision record
            decision = Decision(
                decision_id=f"decision_{int(time.time())}_{decision_type.value}",
                decision_type=decision_type,
                context=context,
                reasoning=selected_action.get('reasoning', 'No reasoning provided'),
                confidence=selected_action.get('confidence', 0.5),
                alternatives=alternatives,
                selected_action=selected_action,
                status=DecisionStatus.PENDING,
                created_at=datetime.now()
            )

            # Store decision
            self.decisions[decision.decision_id] = decision
            await self._store_decision(decision)

            # Execute decision
            outcome = await self._execute_decision(decision)
            decision.outcome = outcome
            decision.status = DecisionStatus.COMPLETED
            decision.executed_at = datetime.now()

            # Update metrics
            decision_time = time.time() - start_time
            self._update_decision_metrics(decision, decision_time)

            # Learn from decision outcome
            await self._learn_from_decision(decision, outcome)

            logger.info(f"Decision {decision.decision_id} completed successfully")
            return decision

        except Exception as e:
            logger.error(f"Decision making failed: {e}")

            # Create failed decision record
            decision = Decision(
                decision_id=f"decision_{int(time.time())}_{decision_type.value}",
                decision_type=decision_type,
                context=context,
                reasoning=f"Decision failed: {str(e)}",
                confidence=0.0,
                alternatives=[],
                selected_action={},
                status=DecisionStatus.FAILED,
                created_at=datetime.now(),
                outcome={'error': str(e)}
            )

            self.decisions[decision.decision_id] = decision
            await self._store_decision(decision)

            return decision

    async def _capture_system_context(self) -> ContextSnapshot:
        """Capture current system context for decision making"""
        try:
            # Get system metrics from components
            system_load = await self._get_system_load()
            resource_availability = await self._get_resource_availability()
            active_tasks = len(self.task_executor.running_tasks) if self.task_executor else 0
            queue_length = self.task_executor.execution_queue.qsize() if self.task_executor else 0

            # Get performance metrics
            recent_performance = await self._get_recent_performance()
            error_rates = await self._get_error_rates()
            cost_metrics = await self._get_cost_metrics()
            quality_metrics = await self._get_quality_metrics()

            context = ContextSnapshot(
                timestamp=datetime.now(),
                system_load=system_load,
                resource_availability=resource_availability,
                active_tasks=active_tasks,
                queue_length=queue_length,
                recent_performance=recent_performance,
                error_rates=error_rates,
                cost_metrics=cost_metrics,
                quality_metrics=quality_metrics
            )

            # Store context snapshot
            self.context_history.append(context)
            await self._store_context_snapshot(context)

            # Keep only recent history
            if len(self.context_history) > 1000:
                self.context_history = self.context_history[-1000:]

            return context

        except Exception as e:
            logger.error(f"Failed to capture system context: {e}")
            # Return default context
            return ContextSnapshot(
                timestamp=datetime.now(),
                system_load=0.5,
                resource_availability={},
                active_tasks=0,
                queue_length=0,
                recent_performance={},
                error_rates={},
                cost_metrics={},
                quality_metrics={}
            )

    async def _analyze_decision_context(self, decision_type: DecisionType,
                                      context: dict[str, Any],
                                      system_context: ContextSnapshot) -> dict[str, Any]:
        """Analyze the context for decision making"""
        analysis = {
            'decision_type': decision_type.value,
            'context': context,
            'system_context': system_context,
            'requirements': {},
            'constraints': {},
            'opportunities': {},
            'risks': {}
        }

        # Analyze based on decision type
        if decision_type == DecisionType.TASK_ROUTING:
            analysis.update(await self._analyze_task_routing_context(context, system_context))
        elif decision_type == DecisionType.RESOURCE_ALLOCATION:
            analysis.update(await self._analyze_resource_allocation_context(context, system_context))
        elif decision_type == DecisionType.MODEL_SELECTION:
            analysis.update(await self._analyze_model_selection_context(context, system_context))
        elif decision_type == DecisionType.AGENT_ASSIGNMENT:
            analysis.update(await self._analyze_agent_assignment_context(context, system_context))
        elif decision_type == DecisionType.SYSTEM_OPTIMIZATION:
            analysis.update(await self._analyze_system_optimization_context(context, system_context))

        return analysis

    async def _analyze_task_routing_context(self, context: dict[str, Any],
                                          system_context: ContextSnapshot) -> dict[str, Any]:
        """Analyze context for task routing decisions"""
        task = context.get('task')

        analysis = {
            'requirements': {
                'priority': task.priority.value if task else 5,
                'complexity': getattr(task, 'estimated_complexity', 0.5),
                'deadline': getattr(task, 'deadline', None),
                'skills_required': getattr(task, 'required_skills', [])
            },
            'constraints': {
                'system_load': system_context.system_load,
                'queue_length': system_context.queue_length,
                'resource_availability': system_context.resource_availability
            },
            'opportunities': {
                'parallel_execution': system_context.system_load < 0.7,
                'fast_track': system_context.queue_length < 10
            },
            'risks': {
                'overload': system_context.system_load > 0.9,
                'queue_overflow': system_context.queue_length > 100,
                'resource_starvation': any(avail < 0.2 for avail in system_context.resource_availability.values())
            }
        }

        return analysis

    async def _analyze_resource_allocation_context(self, context: dict[str, Any],
                                                 system_context: ContextSnapshot) -> dict[str, Any]:
        """Analyze context for resource allocation decisions"""
        analysis = {
            'requirements': {
                'task_complexity': context.get('complexity', 0.5),
                'priority': context.get('priority', 5),
                'estimated_duration': context.get('estimated_duration', 60)
            },
            'constraints': {
                'available_resources': system_context.resource_availability,
                'current_allocations': system_context.active_tasks,
                'budget_limits': context.get('budget_constraints', {})
            },
            'opportunities': {
                'resource_optimization': system_context.system_load < 0.6,
                'cost_reduction': system_context.cost_metrics.get('avg_cost', 0) > 0.5
            },
            'risks': {
                'resource_contention': system_context.system_load > 0.8,
                'cost_overrun': context.get('budget_constraints', {}).get('max_cost', float('inf')) < 1.0
            }
        }

        return analysis

    async def _analyze_model_selection_context(self, context: dict[str, Any],
                                             system_context: ContextSnapshot) -> dict[str, Any]:
        """Analyze context for model selection decisions"""
        analysis = {
            'requirements': {
                'task_category': context.get('category', 'general'),
                'complexity': context.get('complexity', 0.5),
                'privacy_requirements': context.get('privacy_sensitive', False),
                'quality_requirements': context.get('quality_priority', False)
            },
            'constraints': {
                'cost_limits': context.get('max_cost', float('inf')),
                'latency_requirements': context.get('max_latency_ms', float('inf')),
                'model_availability': system_context.resource_availability.get('models', {})
            },
            'opportunities': {
                'local_processing': not context.get('privacy_sensitive', False),
                'cost_optimization': context.get('cost_priority', False),
                'quality_optimization': context.get('quality_priority', False)
            },
            'risks': {
                'model_unavailable': system_context.resource_availability.get('models', {}).get('available', 0) < 1,
                'cost_exceeded': context.get('estimated_cost', 0) > context.get('max_cost', float('inf')),
                'latency_exceeded': context.get('estimated_latency', 0) > context.get('max_latency_ms', float('inf'))
            }
        }

        return analysis

    async def _analyze_agent_assignment_context(self, context: dict[str, Any],
                                              system_context: ContextSnapshot) -> dict[str, Any]:
        """Analyze context for agent assignment decisions"""
        analysis = {
            'requirements': {
                'task_type': context.get('task_type', 'general'),
                'skills_required': context.get('required_skills', []),
                'tools_required': context.get('required_tools', [])
            },
            'constraints': {
                'agent_availability': system_context.resource_availability.get('agents', {}),
                'current_workload': system_context.active_tasks,
                'skill_matches': {}
            },
            'opportunities': {
                'skill_optimization': len(context.get('required_skills', [])) > 0,
                'load_balancing': system_context.system_load > 0.6
            },
            'risks': {
                'agent_unavailable': system_context.resource_availability.get('agents', {}).get('available', 0) < 1,
                'skill_mismatch': len(context.get('required_skills', [])) > 0,
                'overload': system_context.system_load > 0.9
            }
        }

        return analysis

    async def _analyze_system_optimization_context(self, context: dict[str, Any],
                                                 system_context: ContextSnapshot) -> dict[str, Any]:
        """Analyze context for system optimization decisions"""
        analysis = {
            'requirements': {
                'performance_targets': context.get('target_metrics', {}),
                'optimization_goals': context.get('goals', [])
            },
            'constraints': {
                'current_performance': system_context.recent_performance,
                'resource_limits': system_context.resource_availability,
                'cost_limits': system_context.cost_metrics
            },
            'opportunities': {
                'performance_gaps': self._identify_performance_gaps(system_context),
                'resource_optimization': system_context.system_load < 0.5,
                'cost_reduction': system_context.cost_metrics.get('avg_cost', 0) > 0.3
            },
            'risks': {
                'performance_degradation': system_context.recent_performance.get('success_rate', 1.0) < 0.8,
                'resource_starvation': any(avail < 0.1 for avail in system_context.resource_availability.values()),
                'cost_increase': system_context.cost_metrics.get('trend', 'stable') == 'increasing'
            }
        }

        return analysis

    def _identify_performance_gaps(self, system_context: ContextSnapshot) -> list[str]:
        """Identify performance gaps for optimization"""
        gaps = []

        # Check success rate
        success_rate = system_context.recent_performance.get('success_rate', 1.0)
        if success_rate < 0.9:
            gaps.append(f"Low success rate: {success_rate:.2f}")

        # Check error rates
        for error_type, rate in system_context.error_rates.items():
            if rate > 0.1:
                gaps.append(f"High {error_type} error rate: {rate:.2f}")

        # Check cost efficiency
        avg_cost = system_context.cost_metrics.get('avg_cost', 0)
        if avg_cost > 0.5:
            gaps.append(f"High average cost: ${avg_cost:.4f}")

        # Check quality
        avg_quality = system_context.quality_metrics.get('avg_quality', 1.0)
        if avg_quality < 0.8:
            gaps.append(f"Low average quality: {avg_quality:.2f}")

        return gaps

    async def _generate_alternatives(self, decision_type: DecisionType,
                                   analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate alternative actions for the decision"""
        alternatives = []

        if decision_type == DecisionType.TASK_ROUTING:
            alternatives = await self._generate_task_routing_alternatives(analysis)
        elif decision_type == DecisionType.RESOURCE_ALLOCATION:
            alternatives = await self._generate_resource_allocation_alternatives(analysis)
        elif decision_type == DecisionType.MODEL_SELECTION:
            alternatives = await self._generate_model_selection_alternatives(analysis)
        elif decision_type == DecisionType.AGENT_ASSIGNMENT:
            alternatives = await self._generate_agent_assignment_alternatives(analysis)
        elif decision_type == DecisionType.SYSTEM_OPTIMIZATION:
            alternatives = await self._generate_system_optimization_alternatives(analysis)

        return alternatives

    async def _generate_task_routing_alternatives(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate alternatives for task routing"""
        alternatives = []

        # Alternative 1: Direct execution
        alternatives.append({
            'action': 'direct_execution',
            'description': 'Execute task immediately with current resources',
            'expected_outcome': 'Fast execution, moderate resource usage',
            'risks': ['Resource contention if system is busy'],
            'confidence': 0.7
        })

        # Alternative 2: Queued execution
        alternatives.append({
            'action': 'queued_execution',
            'description': 'Add task to queue for later execution',
            'expected_outcome': 'Balanced resource usage, delayed execution',
            'risks': ['Delayed completion, potential deadline miss'],
            'confidence': 0.8
        })

        # Alternative 3: Parallel execution
        if analysis['opportunities'].get('parallel_execution', False):
            alternatives.append({
                'action': 'parallel_execution',
                'description': 'Execute task in parallel with others',
                'expected_outcome': 'Fast execution, higher resource usage',
                'risks': ['Resource contention, potential conflicts'],
                'confidence': 0.6
            })

        # Alternative 4: Deferred execution
        if analysis['risks'].get('overload', False):
            alternatives.append({
                'action': 'deferred_execution',
                'description': 'Defer task until system load decreases',
                'expected_outcome': 'Optimal resource usage, delayed execution',
                'risks': ['Significant delay, potential deadline miss'],
                'confidence': 0.5
            })

        return alternatives

    async def _generate_resource_allocation_alternatives(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate alternatives for resource allocation"""
        alternatives = []

        # Alternative 1: Conservative allocation
        alternatives.append({
            'action': 'conservative_allocation',
            'description': 'Allocate minimum required resources',
            'expected_outcome': 'Low resource usage, moderate performance',
            'risks': ['Potential performance degradation'],
            'confidence': 0.8
        })

        # Alternative 2: Optimal allocation
        alternatives.append({
            'action': 'optimal_allocation',
            'description': 'Allocate resources for optimal performance',
            'expected_outcome': 'High performance, moderate resource usage',
            'risks': ['Higher resource consumption'],
            'confidence': 0.7
        })

        # Alternative 3: Over-allocation
        if analysis['opportunities'].get('resource_optimization', False):
            alternatives.append({
                'action': 'over_allocation',
                'description': 'Allocate extra resources for guaranteed performance',
                'expected_outcome': 'Guaranteed performance, high resource usage',
                'risks': ['Resource waste, higher costs'],
                'confidence': 0.6
            })

        return alternatives

    async def _generate_model_selection_alternatives(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate alternatives for model selection"""
        alternatives = []

        # Alternative 1: Local model
        if analysis['opportunities'].get('local_processing', False):
            alternatives.append({
                'action': 'local_model',
                'description': 'Use local model for processing',
                'expected_outcome': 'Fast processing, no cost, high privacy',
                'risks': ['Lower quality, resource intensive'],
                'confidence': 0.7
            })

        # Alternative 2: Cloud model (cost-optimized)
        if analysis['opportunities'].get('cost_optimization', False):
            alternatives.append({
                'action': 'cost_optimized_cloud',
                'description': 'Use cost-effective cloud model',
                'expected_outcome': 'Balanced cost and quality',
                'risks': ['Moderate cost, potential latency'],
                'confidence': 0.8
            })

        # Alternative 3: Cloud model (quality-optimized)
        if analysis['opportunities'].get('quality_optimization', False):
            alternatives.append({
                'action': 'quality_optimized_cloud',
                'description': 'Use high-quality cloud model',
                'expected_outcome': 'High quality output',
                'risks': ['Higher cost, potential latency'],
                'confidence': 0.9
            })

        return alternatives

    async def _generate_agent_assignment_alternatives(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate alternatives for agent assignment"""
        alternatives = []

        # Alternative 1: Best skill match
        alternatives.append({
            'action': 'best_skill_match',
            'description': 'Assign agent with best skill match',
            'expected_outcome': 'High quality execution',
            'risks': ['Potential workload imbalance'],
            'confidence': 0.8
        })

        # Alternative 2: Load balanced
        if analysis['opportunities'].get('load_balancing', False):
            alternatives.append({
                'action': 'load_balanced',
                'description': 'Assign agent with lowest workload',
                'expected_outcome': 'Balanced workload distribution',
                'risks': ['Potential skill mismatch'],
                'confidence': 0.7
            })

        # Alternative 3: Hybrid approach
        alternatives.append({
            'action': 'hybrid_assignment',
            'description': 'Balance skill match and workload',
            'expected_outcome': 'Good quality with balanced load',
            'risks': ['Suboptimal in both dimensions'],
            'confidence': 0.6
        })

        return alternatives

    async def _generate_system_optimization_alternatives(self, analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate alternatives for system optimization"""
        alternatives = []

        # Alternative 1: Performance optimization
        if analysis['opportunities'].get('performance_gaps'):
            alternatives.append({
                'action': 'performance_optimization',
                'description': 'Focus on improving performance metrics',
                'expected_outcome': 'Better success rates and quality',
                'risks': ['Potential resource increase'],
                'confidence': 0.7
            })

        # Alternative 2: Resource optimization
        if analysis['opportunities'].get('resource_optimization', False):
            alternatives.append({
                'action': 'resource_optimization',
                'description': 'Optimize resource allocation and usage',
                'expected_outcome': 'Lower resource consumption',
                'risks': ['Potential performance impact'],
                'confidence': 0.8
            })

        # Alternative 3: Cost optimization
        if analysis['opportunities'].get('cost_reduction', False):
            alternatives.append({
                'action': 'cost_optimization',
                'description': 'Focus on reducing operational costs',
                'expected_outcome': 'Lower average cost per task',
                'risks': ['Potential quality degradation'],
                'confidence': 0.6
            })

        return alternatives

    async def _evaluate_alternatives(self, alternatives: list[dict[str, Any]],
                                   analysis: dict[str, Any]) -> list[dict[str, Any]]:
        """Evaluate alternatives based on context and goals"""
        evaluated_alternatives = []

        for alternative in alternatives:
            # Calculate score based on multiple factors
            score = await self._calculate_alternative_score(alternative, analysis)

            evaluated_alternative = alternative.copy()
            evaluated_alternative['score'] = score
            evaluated_alternative['reasoning'] = self._generate_alternative_reasoning(alternative, score, analysis)

            evaluated_alternatives.append(evaluated_alternative)

        # Sort by score (descending)
        evaluated_alternatives.sort(key=lambda x: x['score'], reverse=True)

        return evaluated_alternatives

    async def _calculate_alternative_score(self, alternative: dict[str, Any],
                                        analysis: dict[str, Any]) -> float:
        """Calculate score for an alternative"""
        base_score = alternative.get('confidence', 0.5)

        # Adjust based on context
        context_adjustment = 0.0

        # Risk adjustment
        risk_count = len(alternative.get('risks', []))
        context_adjustment -= risk_count * 0.1

        # Opportunity alignment
        if 'parallel_execution' in alternative.get('action', '') and analysis['opportunities'].get('parallel_execution', False):
            context_adjustment += 0.2

        if 'cost_optimization' in alternative.get('action', '') and analysis['opportunities'].get('cost_reduction', False):
            context_adjustment += 0.2

        # Constraint compliance
        if analysis['constraints'].get('budget_limits') and 'cost' in alternative.get('action', '').lower():
            context_adjustment += 0.1

        # Final score
        final_score = max(0.0, min(1.0, base_score + context_adjustment))

        return final_score

    def _generate_alternative_reasoning(self, alternative: dict[str, Any],
                                      score: float, analysis: dict[str, Any]) -> str:
        """Generate reasoning for alternative selection"""
        action = alternative.get('action', '')
        description = alternative.get('description', '')

        reasoning_parts = [f"Selected {action}: {description}"]

        if score > 0.8:
            reasoning_parts.append("High confidence due to excellent context alignment")
        elif score > 0.6:
            reasoning_parts.append("Good confidence with acceptable trade-offs")
        else:
            reasoning_parts.append("Lower confidence due to context constraints")

        # Add specific reasoning based on context
        if analysis['opportunities'].get('parallel_execution', False) and 'parallel' in action.lower():
            reasoning_parts.append("System load allows parallel execution")

        if analysis['risks'].get('overload', False) and 'deferred' in action.lower():
            reasoning_parts.append("System overload risk mitigated by deferral")

        return ". ".join(reasoning_parts)

    async def _select_best_alternative(self, evaluated_alternatives: list[dict[str, Any]],
                                     analysis: dict[str, Any]) -> dict[str, Any]:
        """Select the best alternative based on evaluation"""
        if not evaluated_alternatives:
            raise ValueError("No alternatives available for selection")

        # Select the highest scoring alternative
        best_alternative = evaluated_alternatives[0]

        # Add selection metadata
        best_alternative['selection_timestamp'] = datetime.now()
        best_alternative['selection_reason'] = f"Highest score: {best_alternative['score']:.3f}"
        best_alternative['alternatives_considered'] = len(evaluated_alternatives)

        return best_alternative

    async def _execute_decision(self, decision: Decision) -> dict[str, Any]:
        """Execute the selected decision"""
        try:
            decision.status = DecisionStatus.EXECUTING

            action = decision.selected_action.get('action', '')
            outcome = {}

            if decision.decision_type == DecisionType.TASK_ROUTING:
                outcome = await self._execute_task_routing_decision(action, decision.context)
            elif decision.decision_type == DecisionType.RESOURCE_ALLOCATION:
                outcome = await self._execute_resource_allocation_decision(action, decision.context)
            elif decision.decision_type == DecisionType.MODEL_SELECTION:
                outcome = await self._execute_model_selection_decision(action, decision.context)
            elif decision.decision_type == DecisionType.AGENT_ASSIGNMENT:
                outcome = await self._execute_agent_assignment_decision(action, decision.context)
            elif decision.decision_type == DecisionType.SYSTEM_OPTIMIZATION:
                outcome = await self._execute_system_optimization_decision(action, decision.context)

            outcome['execution_success'] = True
            outcome['execution_timestamp'] = datetime.now()

            return outcome

        except Exception as e:
            logger.error(f"Decision execution failed: {e}")
            return {
                'execution_success': False,
                'error': str(e),
                'execution_timestamp': datetime.now()
            }

    # Placeholder methods for decision execution
    async def _execute_task_routing_decision(self, action: str, context: dict[str, Any]) -> dict[str, Any]:
        return {'action': action, 'status': 'executed'}

    async def _execute_resource_allocation_decision(self, action: str, context: dict[str, Any]) -> dict[str, Any]:
        return {'action': action, 'status': 'executed'}

    async def _execute_model_selection_decision(self, action: str, context: dict[str, Any]) -> dict[str, Any]:
        return {'action': action, 'status': 'executed'}

    async def _execute_agent_assignment_decision(self, action: str, context: dict[str, Any]) -> dict[str, Any]:
        return {'action': action, 'status': 'executed'}

    async def _execute_system_optimization_decision(self, action: str, context: dict[str, Any]) -> dict[str, Any]:
        return {'action': action, 'status': 'executed'}

    # Background process methods
    async def _monitor_system_context(self):
        """Monitor system context continuously"""
        while True:
            try:
                await self._capture_system_context()
                await asyncio.sleep(30)  # Update every 30 seconds
            except Exception as e:
                logger.error(f"Context monitoring failed: {e}")
                await asyncio.sleep(60)

    async def _optimize_system_performance(self):
        """Optimize system performance based on goals"""
        while True:
            try:
                # Check if optimization is needed
                if await self._should_optimize_system():
                    # Make optimization decision
                    await self.make_decision(
                        DecisionType.SYSTEM_OPTIMIZATION,
                        {'trigger': 'periodic_optimization'}
                    )

                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Performance optimization failed: {e}")
                await asyncio.sleep(300)

    async def _update_learning_models(self):
        """Update learning models based on decision outcomes"""
        while True:
            try:
                # Analyze recent decisions
                recent_decisions = await self._get_recent_decisions(limit=100)

                # Update learning models
                await self._update_learning_from_decisions(recent_decisions)

                await asyncio.sleep(600)  # Update every 10 minutes

            except Exception as e:
                logger.error(f"Learning model update failed: {e}")
                await asyncio.sleep(600)

    async def _manage_system_goals(self):
        """Manage and update system goals"""
        while True:
            try:
                # Update goal progress
                await self._update_goal_progress()

                # Create new goals if needed
                await self._create_new_goals()

                await asyncio.sleep(1800)  # Check every 30 minutes

            except Exception as e:
                logger.error(f"Goal management failed: {e}")
                await asyncio.sleep(1800)

    # Placeholder methods for background processes
    async def _should_optimize_system(self) -> bool:
        return False

    async def _get_recent_decisions(self, limit: int) -> list[dict[str, Any]]:
        return []

    async def _update_learning_from_decisions(self, decisions: list[dict[str, Any]]):
        pass

    async def _update_goal_progress(self):
        pass

    async def _create_new_goals(self):
        pass

    # Utility methods
    async def _store_decision(self, decision: Decision):
        """Store decision in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO decisions
                (decision_id, decision_type, context, reasoning, confidence,
                 alternatives, selected_action, status, created_at, executed_at, outcome, learning_insights)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                decision.decision_id,
                decision.decision_type.value,
                json.dumps(decision.context),
                decision.reasoning,
                decision.confidence,
                json.dumps(decision.alternatives),
                json.dumps(decision.selected_action),
                decision.status.value,
                decision.created_at,
                decision.executed_at,
                json.dumps(decision.outcome) if decision.outcome else None,
                json.dumps(decision.learning_insights)
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to store decision: {e}")

    async def _store_context_snapshot(self, context: ContextSnapshot):
        """Store context snapshot in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO context_snapshots
                (timestamp, system_load, resource_availability, active_tasks, queue_length,
                 recent_performance, error_rates, cost_metrics, quality_metrics)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                context.timestamp,
                context.system_load,
                json.dumps(context.resource_availability),
                context.active_tasks,
                context.queue_length,
                json.dumps(context.recent_performance),
                json.dumps(context.error_rates),
                json.dumps(context.cost_metrics),
                json.dumps(context.quality_metrics)
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to store context snapshot: {e}")

    def _update_decision_metrics(self, decision: Decision, decision_time: float):
        """Update decision performance metrics"""
        self.decision_metrics['total_decisions'] += 1

        if decision.status == DecisionStatus.COMPLETED:
            self.decision_metrics['successful_decisions'] += 1
        else:
            self.decision_metrics['failed_decisions'] += 1

        # Update averages
        total_decisions = self.decision_metrics['total_decisions']
        if total_decisions > 0:
            self.decision_metrics['avg_decision_time'] = (
                (self.decision_metrics['avg_decision_time'] * (total_decisions - 1) + decision_time) / total_decisions
            )
            self.decision_metrics['avg_confidence'] = (
                (self.decision_metrics['avg_confidence'] * (total_decisions - 1) + decision.confidence) / total_decisions
            )

    async def _learn_from_decision(self, decision: Decision, outcome: dict[str, Any]):
        """Learn from decision outcome for future improvements"""
        try:
            # Analyze outcome
            success = outcome.get('execution_success', False)

            # Extract learning insights
            insights = []

            if success:
                if decision.confidence > 0.8:
                    insights.append("High confidence decisions tend to succeed")
                else:
                    insights.append("Lower confidence decisions can still succeed with proper execution")
            elif decision.confidence > 0.8:
                insights.append("High confidence doesn't guarantee success - execution matters")
            else:
                insights.append("Low confidence decisions often fail - need better alternatives")

            # Add context-specific insights
            if 'parallel_execution' in decision.selected_action.get('action', ''):
                if success:
                    insights.append("Parallel execution effective for this task type")
                else:
                    insights.append("Parallel execution may cause resource conflicts")

            # Store insights
            decision.learning_insights = insights
            await self._store_decision(decision)

            # Update learning cycle
            self.decision_metrics['learning_cycles'] += 1

            logger.info(f"Learning insights extracted from decision {decision.decision_id}")

        except Exception as e:
            logger.error(f"Failed to learn from decision: {e}")

    # Placeholder methods for system monitoring
    async def _get_system_load(self) -> float:
        return 0.5

    async def _get_resource_availability(self) -> dict[str, Any]:
        return {}

    async def _get_recent_performance(self) -> dict[str, Any]:
        return {}

    async def _get_error_rates(self) -> dict[str, float]:
        return {}

    async def _get_cost_metrics(self) -> dict[str, float]:
        return {}

    async def _get_quality_metrics(self) -> dict[str, float]:
        return {}

    def get_decision_metrics(self) -> dict[str, Any]:
        """Get current decision metrics"""
        return self.decision_metrics.copy()

    async def get_decision_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """Get decision history from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM decisions
                ORDER BY created_at DESC LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            history = []

            for row in rows:
                history.append({
                    'decision_id': row[0],
                    'decision_type': row[1],
                    'context': json.loads(row[2]) if row[2] else {},
                    'reasoning': row[3],
                    'confidence': row[4],
                    'alternatives': json.loads(row[5]) if row[5] else [],
                    'selected_action': json.loads(row[6]) if row[6] else {},
                    'status': row[7],
                    'created_at': row[8],
                    'executed_at': row[9],
                    'outcome': json.loads(row[10]) if row[10] else {},
                    'learning_insights': json.loads(row[11]) if row[11] else []
                })

            conn.close()
            return history

        except Exception as e:
            logger.error(f"Failed to get decision history: {e}")
            return []


# Example usage
async def main():
    """Example usage of the decision engine"""
    config = {
        "database": {"path": "test_decision_engine.db"}
    }

    engine = DecisionEngine(config)

    # Example decision making
    context = {
        'task': type('MockTask', (), {
            'id': 'task_1',
            'priority': type('MockPriority', (), {'value': 8})(),
            'estimated_complexity': 0.7,
            'deadline': datetime.now() + timedelta(hours=2),
            'required_skills': ['research', 'analysis']
        })(),
        'category': 'research',
        'complexity': 0.7,
        'priority': 8
    }

    # Make a task routing decision
    decision = await engine.make_decision(DecisionType.TASK_ROUTING, context)

    print(f"Decision ID: {decision.decision_id}")
    print(f"Decision Type: {decision.decision_type.value}")
    print(f"Selected Action: {decision.selected_action.get('action', 'unknown')}")
    print(f"Confidence: {decision.confidence:.2f}")
    print(f"Reasoning: {decision.reasoning}")
    print(f"Status: {decision.status.value}")

    if decision.outcome:
        print(f"Outcome: {decision.outcome}")


if __name__ == "__main__":
    asyncio.run(main())

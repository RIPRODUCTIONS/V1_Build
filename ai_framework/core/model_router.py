"""
Intelligent Model Router

This module provides intelligent routing for LLM requests based on:
- Task classification and requirements
- Cost-performance optimization
- Model capability matching
- Load balancing across providers
- Fallback mechanisms
- A/B testing for model selection
- Performance learning and optimization
"""

import asyncio
import json
import logging
import random
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .llm_manager import LLMProvider, LLMRequest, LLMResponse

logger = logging.getLogger(__name__)

# Constants to replace magic numbers
HIGH_RELIABILITY_THRESHOLD = 0.95
FAST_RESPONSE_THRESHOLD = 2.0
HIGH_COST_THRESHOLD = 0.01
SLOW_RESPONSE_THRESHOLD = 5.0
LOW_RELIABILITY_THRESHOLD = 0.90
MAX_RECOMMENDATIONS = 5


class TaskType(str, Enum):
    """Classification of different task types."""
    CODING = "coding"
    ANALYSIS = "analysis"
    CREATIVE = "creative"
    RESEARCH = "research"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    QNA = "qna"
    FUNCTION_CALLING = "function_calling"
    STREAMING = "streaming"
    BATCH_PROCESSING = "batch_processing"


class TaskComplexity(str, Enum):
    """Task complexity levels."""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    EXPERT = "expert"


@dataclass
class TaskRequirements:
    """Requirements for a specific task."""
    task_type: TaskType
    complexity: TaskComplexity
    privacy_sensitive: bool = False
    cost_priority: bool = False
    speed_priority: bool = False
    quality_priority: bool = False
    function_calling_required: bool = False
    streaming_required: bool = False
    max_tokens: int = 1000
    temperature: float = 0.7
    specialized_knowledge: list[str] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelCapability:
    """Capabilities of a specific model."""
    provider: LLMProvider
    model_name: str
    task_types: list[TaskType]
    max_complexity: TaskComplexity
    function_calling: bool
    streaming: bool
    max_tokens: int
    cost_per_1k_tokens: float
    avg_latency: float
    success_rate: float
    last_updated: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutingDecision:
    """Result of a routing decision."""
    provider: LLMProvider
    model: str
    confidence: float
    reasoning: str
    alternatives: list[tuple[LLMProvider, str, float]]
    metadata: dict[str, Any] = field(default_factory=dict)


class ModelRouter:
    """Intelligent router for selecting the best model for each task."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.model_capabilities: dict[str, ModelCapability] = {}
        self.performance_history: dict[str, list[dict[str, Any]]] = {}
        self.routing_rules: dict[str, dict[str, Any]] = {}
        self.ab_testing_enabled = config.get("ab_testing", {}).get("enabled", False)
        self.learning_enabled = config.get("learning", {}).get("enabled", True)

        # Initialize routing database
        self.db_path = Path(config.get("database", {}).get("path", "model_router.db"))
        self._init_database()

        # Load model capabilities
        self._load_model_capabilities()

        # Load routing rules
        self._load_routing_rules()

        # Start performance monitoring
        asyncio.create_task(self._monitor_performance())

    def _init_database(self):
        """Initialize the routing database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Performance history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    complexity TEXT NOT NULL,
                    latency REAL NOT NULL,
                    success BOOLEAN NOT NULL,
                    cost REAL NOT NULL,
                    tokens_used INTEGER NOT NULL,
                    user_satisfaction REAL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT
                )
            ''')

            # Routing decisions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS routing_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_type TEXT NOT NULL,
                    complexity TEXT NOT NULL,
                    selected_provider TEXT NOT NULL,
                    selected_model TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    reasoning TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT
                )
            ''')

            # Model capabilities table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_capabilities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    task_types TEXT NOT NULL,
                    max_complexity TEXT NOT NULL,
                    function_calling BOOLEAN NOT NULL,
                    streaming BOOLEAN NOT NULL,
                    max_tokens INTEGER NOT NULL,
                    cost_per_1k_tokens REAL NOT NULL,
                    avg_latency REAL NOT NULL,
                    success_rate REAL NOT NULL,
                    last_updated TEXT NOT NULL,
                    metadata TEXT,
                    UNIQUE(provider, model_name)
                )
            ''')

            conn.commit()
            conn.close()
            logger.info("Model router database initialized")

        except Exception as e:
            logger.error(f"Failed to initialize routing database: {e}")

    def _load_model_capabilities(self):
        """Load model capabilities from database and configuration."""
        try:
            # Load from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('SELECT * FROM model_capabilities')
            rows = cursor.fetchall()

            for row in rows:
                capability = ModelCapability(
                    provider=LLMProvider(row[1]),
                    model_name=row[2],
                    task_types=json.loads(row[3]),
                    max_complexity=TaskComplexity(row[4]),
                    function_calling=bool(row[5]),
                    streaming=bool(row[6]),
                    max_tokens=row[7],
                    cost_per_1k_tokens=row[8],
                    avg_latency=row[9],
                    success_rate=row[10],
                    last_updated=datetime.fromisoformat(row[11]),
                    metadata=json.loads(row[12]) if row[12] else {}
                )

                key = f"{capability.provider.value}:{capability.model_name}"
                self.model_capabilities[key] = capability

            conn.close()

            # Load default capabilities if database is empty
            if not self.model_capabilities:
                self._load_default_capabilities()

            logger.info(f"Loaded {len(self.model_capabilities)} model capabilities")

        except Exception as e:
            logger.error(f"Failed to load model capabilities: {e}")
            self._load_default_capabilities()

    def _load_default_capabilities(self):
        """Load default model capabilities."""
        default_capabilities = [
            # OpenAI models
            ModelCapability(
                provider=LLMProvider.OPENAI,
                model_name="gpt-4",
                task_types=[TaskType.CODING, TaskType.ANALYSIS, TaskType.CREATIVE, TaskType.RESEARCH],
                max_complexity=TaskComplexity.EXPERT,
                function_calling=True,
                streaming=True,
                max_tokens=8192,
                cost_per_1k_tokens=0.03,
                avg_latency=2.5,
                success_rate=0.95,  # High success rate threshold
                last_updated=datetime.now(UTC)
            ),
            ModelCapability(
                provider=LLMProvider.OPENAI,
                model_name="gpt-4-turbo",
                task_types=[TaskType.CODING, TaskType.ANALYSIS, TaskType.CREATIVE, TaskType.RESEARCH],
                max_complexity=TaskComplexity.COMPLEX,
                function_calling=True,
                streaming=True,
                max_tokens=128000,
                cost_per_1k_tokens=0.01,
                avg_latency=1.8,
                success_rate=0.93,
                last_updated=datetime.now(UTC)
            ),
            ModelCapability(
                provider=LLMProvider.OPENAI,
                model_name="gpt-3.5-turbo",
                task_types=[TaskType.CODING, TaskType.ANALYSIS, TaskType.CREATIVE, TaskType.RESEARCH],
                max_complexity=TaskComplexity.MEDIUM,
                function_calling=True,
                streaming=True,
                max_tokens=4096,
                cost_per_1k_tokens=0.002,
                avg_latency=1.2,
                success_rate=0.90,
                last_updated=datetime.now(UTC)
            ),

            # Ollama models
            ModelCapability(
                provider=LLMProvider.OLLAMA,
                model_name="llama3.1:8b",
                task_types=[TaskType.ANALYSIS, TaskType.RESEARCH, TaskType.SUMMARIZATION],
                max_complexity=TaskComplexity.MEDIUM,
                function_calling=False,
                streaming=True,
                max_tokens=4096,
                cost_per_1k_tokens=0.0,
                avg_latency=3.0,
                success_rate=0.85,
                last_updated=datetime.now(UTC)
            ),
            ModelCapability(
                provider=LLMProvider.OLLAMA,
                model_name="llama3.1:70b",
                task_types=[TaskType.CODING, TaskType.ANALYSIS, TaskType.CREATIVE, TaskType.RESEARCH],
                max_complexity=TaskComplexity.COMPLEX,
                function_calling=False,
                streaming=True,
                max_tokens=8192,
                cost_per_1k_tokens=0.0,
                avg_latency=8.0,
                success_rate=0.92,
                last_updated=datetime.now(UTC)
            ),
            ModelCapability(
                provider=LLMProvider.OLLAMA,
                model_name="codellama:13b",
                task_types=[TaskType.CODING, TaskType.ANALYSIS],
                max_complexity=TaskComplexity.COMPLEX,
                function_calling=False,
                streaming=True,
                max_tokens=8192,
                cost_per_1k_tokens=0.0,
                avg_latency=5.0,
                success_rate=0.88,
                last_updated=datetime.now(UTC)
            ),
            ModelCapability(
                provider=LLMProvider.OLLAMA,
                model_name="mistral:7b",
                task_types=[TaskType.ANALYSIS, TaskType.RESEARCH, TaskType.SUMMARIZATION],
                max_complexity=TaskComplexity.MEDIUM,
                function_calling=False,
                streaming=True,
                max_tokens=4096,
                cost_per_1k_tokens=0.0,
                avg_latency=2.5,
                success_rate=0.87,
                last_updated=datetime.now(UTC)
            ),

            # Claude models
            ModelCapability(
                provider=LLMProvider.CLAUDE,
                model_name="claude-3.5-sonnet-20241022",
                task_types=[TaskType.CODING, TaskType.ANALYSIS, TaskType.CREATIVE, TaskType.RESEARCH],
                max_complexity=TaskComplexity.COMPLEX,
                function_calling=True,
                streaming=True,
                max_tokens=4096,
                cost_per_1k_tokens=0.003,
                avg_latency=2.0,
                success_rate=0.94,
                last_updated=datetime.now(UTC)
            ),
            ModelCapability(
                provider=LLMProvider.CLAUDE,
                model_name="claude-3.5-haiku-20240307",
                task_types=[TaskType.ANALYSIS, TaskType.RESEARCH, TaskType.SUMMARIZATION],
                max_complexity=TaskComplexity.MEDIUM,
                function_calling=True,
                streaming=True,
                max_tokens=4096,
                cost_per_1k_tokens=0.00025,
                avg_latency=1.0,
                success_rate=0.89,
                last_updated=datetime.now(UTC)
            )
        ]

        for capability in default_capabilities:
            key = f"{capability.provider.value}:{capability.model_name}"
            self.model_capabilities[key] = capability

        # Save to database
        self._save_model_capabilities()

    def _save_model_capabilities(self):
        """Save model capabilities to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for capability in self.model_capabilities.values():
                cursor.execute('''
                    INSERT OR REPLACE INTO model_capabilities
                    (provider, model_name, task_types, max_complexity, function_calling,
                     streaming, max_tokens, cost_per_1k_tokens, avg_latency, success_rate,
                     last_updated, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    capability.provider.value if hasattr(capability.provider, 'value') else str(capability.provider),
                    capability.model_name,
                    json.dumps([t.value if hasattr(t, 'value') else str(t) for t in capability.task_types]),
                    capability.max_complexity.value if hasattr(capability.max_complexity, 'value') else str(capability.max_complexity),
                    capability.function_calling,
                    capability.streaming,
                    capability.max_tokens,
                    capability.cost_per_1k_tokens,
                    capability.avg_latency,
                    capability.success_rate,
                    capability.last_updated.isoformat(),
                    json.dumps(capability.metadata)
                ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to save model capabilities: {e}")

    def _load_routing_rules(self):
        """Load routing rules from configuration."""
        self.routing_rules = self.config.get("routing_rules", {})

        # Default routing rules if none specified
        if not self.routing_rules:
            self.routing_rules = {
                "default": {
                    "priority": ["openai", "claude", "ollama"],
                    "fallback": "ollama"
                },
                "privacy_sensitive": {
                    "priority": ["ollama", "claude"],
                    "fallback": "ollama"
                },
                "cost_priority": {
                    "priority": ["ollama", "claude", "openai"],
                    "fallback": "ollama"
                },
                "speed_priority": {
                    "priority": ["claude", "openai", "ollama"],
                    "fallback": "claude"
                },
                "quality_priority": {
                    "priority": ["openai", "claude", "ollama"],
                    "fallback": "openai"
                }
            }

    async def route_request(self, request: LLMRequest, requirements: TaskRequirements) -> RoutingDecision:
        """Route a request to the best available model."""
        start_time = time.time()

        try:
            # Analyze task requirements
            task_analysis = self._analyze_task_requirements(requirements)

            # Get candidate models
            candidates = self._get_candidate_models(requirements, task_analysis)

            if not candidates:
                raise ValueError("No suitable models found for the task")

            # Score candidates
            scored_candidates = self._score_candidates(candidates, requirements, task_analysis)

            # Select best model
            best_provider, best_model, best_score = scored_candidates[0]

            # Get alternatives
            alternatives = [(p, m, s) for p, m, s in scored_candidates[1:4]]  # Top 3 alternatives

            # Generate reasoning
            reasoning = self._generate_routing_reasoning(
                best_provider, best_model, best_score, requirements, alternatives
            )

            # Create routing decision
            decision = RoutingDecision(
                provider=best_provider,
                model=best_model,
                confidence=best_score,
                reasoning=reasoning,
                alternatives=alternatives,
                metadata={
                    "task_analysis": task_analysis,
                    "candidates_evaluated": len(candidates),
                    "routing_time": time.time() - start_time
                }
            )

            # Log decision
            self._log_routing_decision(decision, requirements)

            # Update request with selected provider
            request.provider = best_provider
            request.model = best_model

            return decision

        except Exception as e:
            logger.error(f"Routing failed: {e}")
            # Return fallback decision
            return self._get_fallback_decision(requirements)

    def _analyze_task_requirements(self, requirements: TaskRequirements) -> dict[str, Any]:
        """Analyze task requirements for routing decisions."""
        analysis = {
            "complexity_score": self._calculate_complexity_score(requirements.complexity),
            "privacy_score": 1.0 if requirements.privacy_sensitive else 0.0,
            "cost_score": 1.0 if requirements.cost_priority else 0.0,
            "speed_score": 1.0 if requirements.speed_priority else 0.0,
            "quality_score": 1.0 if requirements.quality_priority else 0.0,
            "specialization_score": self._calculate_specialization_score(requirements.specialized_knowledge),
            "constraint_score": self._calculate_constraint_score(requirements.constraints)
        }

        return analysis

    def _calculate_complexity_score(self, complexity: TaskComplexity) -> float:
        """Calculate numerical score for task complexity."""
        complexity_scores = {
            TaskComplexity.SIMPLE: 0.25,
            TaskComplexity.MEDIUM: 0.5,
            TaskComplexity.COMPLEX: 0.75,
            TaskComplexity.EXPERT: 1.0
        }
        return complexity_scores.get(complexity, 0.5)

    def _calculate_specialization_score(self, specializations: list[str]) -> float:
        """Calculate score for specialized knowledge requirements."""
        if not specializations:
            return 0.5
        # Higher score for more specializations (more complex requirements)
        return min(1.0, len(specializations) * 0.2)

    def _calculate_constraint_score(self, constraints: dict[str, Any]) -> float:
        """Calculate score for task constraints."""
        if not constraints:
            return 0.5
        # Higher score for more constraints (more complex requirements)
        return min(1.0, len(constraints) * 0.1)

    def _get_candidate_models(self, requirements: TaskRequirements, analysis: dict[str, Any]) -> list[tuple[LLMProvider, str]]:
        """Get candidate models that meet the requirements."""
        candidates = []

        for _key, capability in self.model_capabilities.items():
            # Check if model supports the task type
            if requirements.task_type not in capability.task_types:
                continue

            # Check complexity requirements
            if not self._meets_complexity_requirements(capability, requirements.complexity):
                continue

            # Check function calling requirements
            if requirements.function_calling_required and not capability.function_calling:
                continue

            # Check streaming requirements
            if requirements.streaming_required and not capability.streaming:
                continue

            # Check token limits
            if requirements.max_tokens > capability.max_tokens:
                continue

            candidates.append((capability.provider, capability.model_name))

        return candidates

    def _meets_complexity_requirements(self, capability: ModelCapability, required_complexity: TaskComplexity) -> bool:
        """Check if model meets complexity requirements."""
        complexity_levels = {
            TaskComplexity.SIMPLE: 0,
            TaskComplexity.MEDIUM: 1,
            TaskComplexity.COMPLEX: 2,
            TaskComplexity.EXPERT: 3
        }

        required_level = complexity_levels.get(required_complexity, 0)
        capability_level = complexity_levels.get(capability.max_complexity, 0)

        return capability_level >= required_level

    def _score_candidates(self, candidates: list[tuple[LLMProvider, str]],
                         requirements: TaskRequirements, analysis: dict[str, Any]) -> list[tuple[LLMProvider, str, float]]:
        """Score candidate models based on requirements and performance."""
        scored_candidates = []

        for provider, model in candidates:
            key = f"{provider.value}:{model}"
            capability = self.model_capabilities[key]

            # Calculate score based on multiple factors
            score = self._calculate_model_score(capability, requirements, analysis)

            scored_candidates.append((provider, model, score))

        # Sort by score (descending)
        scored_candidates.sort(key=lambda x: x[2], reverse=True)

        return scored_candidates

    def _calculate_model_score(self, capability: ModelCapability, requirements: TaskRequirements,
                              analysis: dict[str, Any]) -> float:
        """Calculate comprehensive score for a model."""
        score = 0.0

        # Base capability score (30%)
        capability_score = (
            (1.0 if requirements.task_type in capability.task_types else 0.0) * 0.3 +
            (1.0 if capability.function_calling or not requirements.function_calling_required else 0.0) * 0.2 +
            (1.0 if capability.streaming or not requirements.streaming_required else 0.0) * 0.1
        )
        score += capability_score * 0.3

        # Performance score (25%)
        performance_score = (
            (1.0 - min(capability.avg_latency / 10.0, 1.0)) * 0.5 +  # Lower latency is better
            capability.success_rate * 0.5  # Higher success rate is better
        )
        score += performance_score * 0.25

        # Cost score (20%)
        if requirements.cost_priority:
            cost_score = 1.0 - min(capability.cost_per_1k_tokens / 0.1, 1.0)  # Lower cost is better
        else:
            cost_score = 0.5  # Neutral if cost is not priority
        score += cost_score * 0.2

        # Privacy score (15%)
        if requirements.privacy_sensitive:
            privacy_score = 1.0 if capability.provider == LLMProvider.OLLAMA else 0.3
        else:
            privacy_score = 0.5  # Neutral if privacy is not priority
        score += privacy_score * 0.15

        # Specialization score (10%)
        specialization_score = 0.5  # Default neutral score
        if requirements.specialized_knowledge:
            # Check if model has relevant specializations
            model_specializations = capability.metadata.get("specializations", [])
            if model_specializations:
                matches = sum(1 for spec in requirements.specialized_knowledge
                            if spec.lower() in [s.lower() for s in model_specializations])
                specialization_score = min(1.0, matches / len(requirements.specialized_knowledge))

        score += specialization_score * 0.1

        # Apply A/B testing if enabled
        if self.ab_testing_enabled:
            score = self._apply_ab_testing(score, capability)

        return min(1.0, max(0.0, score))

    def _apply_ab_testing(self, score: float, capability: ModelCapability) -> float:
        """Apply A/B testing adjustments to scores."""
        # Add small random variation for exploration
        variation = random.uniform(-0.05, 0.05)
        return score + variation

    def _generate_routing_reasoning(self, provider: LLMProvider, model: str, score: float,
                                   requirements: TaskRequirements, alternatives: list[tuple[LLMProvider, str, float]]) -> str:
        """Generate human-readable reasoning for the routing decision."""
        reasoning_parts = []

        # Primary reason
        if requirements.privacy_sensitive and provider == LLMProvider.OLLAMA:
            reasoning_parts.append("Selected local Ollama model for privacy-sensitive task")
        elif requirements.cost_priority and provider == LLMProvider.OLLAMA:
            reasoning_parts.append("Selected cost-effective local model")
        elif requirements.quality_priority and provider == LLMProvider.OPENAI:
            reasoning_parts.append("Selected high-quality OpenAI model for best results")
        elif requirements.speed_priority and provider == LLMProvider.CLAUDE:
            reasoning_parts.append("Selected fast Claude model for speed priority")
        else:
            reasoning_parts.append(f"Selected {provider.value} model based on comprehensive scoring")

        # Score information
        reasoning_parts.append(f"Confidence score: {score:.2f}")

        # Alternative options
        if alternatives:
            alt_names = [f"{p.value}:{m}" for p, m, _ in alternatives[:2]]
            reasoning_parts.append(f"Alternatives: {', '.join(alt_names)}")

        # Special requirements
        if requirements.function_calling_required:
            reasoning_parts.append("Function calling capability required and verified")
        if requirements.streaming_required:
            reasoning_parts.append("Streaming capability required and verified")

        return ". ".join(reasoning_parts)

    def _log_routing_decision(self, decision: RoutingDecision, requirements: TaskRequirements):
        """Log routing decision to database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO routing_decisions
                (task_type, complexity, selected_provider, selected_model, confidence, reasoning, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                requirements.task_type.value,
                requirements.complexity.value,
                decision.provider.value,
                decision.model,
                decision.confidence,
                decision.reasoning,
                datetime.now(UTC).isoformat(),
                json.dumps(decision.metadata)
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to log routing decision: {e}")

    def _get_fallback_decision(self, requirements: TaskRequirements) -> RoutingDecision:
        """Get fallback routing decision when normal routing fails."""
        # Try to find any available model
        for _key, capability in self.model_capabilities.items():
            if (requirements.task_type in capability.task_types and
                requirements.max_tokens <= capability.max_tokens):

                return RoutingDecision(
                    provider=capability.provider,
                    model=capability.model_name,
                    confidence=0.3,
                    reasoning="Fallback selection due to routing failure",
                    alternatives=[],
                    metadata={"fallback": True}
                )

        # Ultimate fallback
        return RoutingDecision(
            provider=LLMProvider.OLLAMA,
            model="llama3.1:8b",
            confidence=0.1,
            reasoning="Emergency fallback to local model",
            alternatives=[],
            metadata={"emergency_fallback": True}
        )

    async def _monitor_performance(self):
        """Monitor and update model performance metrics."""
        while True:
            try:
                await self._update_performance_metrics()
                await asyncio.sleep(300)  # Update every 5 minutes
            except Exception as e:
                logger.error(f"Performance monitoring failed: {e}")
                await asyncio.sleep(60)  # Retry in 1 minute

    async def _update_performance_metrics(self):
        """Update performance metrics for all models."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get recent performance data
            cursor.execute('''
                SELECT provider, model, task_type, complexity,
                       AVG(latency) as avg_latency,
                       AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate,
                       AVG(cost) as avg_cost,
                       COUNT(*) as total_requests
                FROM performance_history
                WHERE timestamp > datetime('now', '-1 hour')
                GROUP BY provider, model, task_type, complexity
            ''')

            performance_data = cursor.fetchall()

            # Update model capabilities
            for row in performance_data:
                provider, model, task_type, complexity, avg_latency, success_rate, avg_cost, total_requests = row

                MIN_REQUESTS_FOR_UPDATE = 5  # Only update if we have enough data
                if total_requests >= MIN_REQUESTS_FOR_UPDATE:
                    key = f"{provider}:{model}"
                    if key in self.model_capabilities:
                        capability = self.model_capabilities[key]

                        # Update metrics with exponential moving average
                        alpha = 0.1  # Learning rate
                        capability.avg_latency = (alpha * avg_latency + (1 - alpha) * capability.avg_latency)
                        capability.success_rate = (alpha * success_rate + (1 - alpha) * capability.success_rate)
                        capability.last_updated = datetime.now(UTC)

            conn.close()

            # Save updated capabilities
            self._save_model_capabilities()

        except Exception as e:
            logger.error(f"Failed to update performance metrics: {e}")

    async def record_performance(self, response: LLMResponse, requirements: TaskRequirements, success: bool):
        """Record performance metrics for a completed request."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO performance_history
                (provider, model, task_type, complexity, latency, success, cost, tokens_used, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                response.provider.value,
                response.model,
                requirements.task_type.value,
                requirements.complexity.value,
                response.latency,
                success,
                response.cost,
                response.tokens_used,
                datetime.now(UTC).isoformat()
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to record performance: {e}")

    def get_routing_statistics(self) -> dict[str, Any]:
        """Get routing statistics and insights."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get recent routing decisions
            cursor.execute('''
                SELECT selected_provider, selected_model, confidence, task_type, complexity
                FROM routing_decisions
                WHERE timestamp > datetime('now', '-24 hours')
            ''')

            recent_decisions = cursor.fetchall()

            # Get performance metrics
            cursor.execute('''
                SELECT provider, model, AVG(latency) as avg_latency,
                       AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate,
                       COUNT(*) as total_requests
                FROM performance_history
                WHERE timestamp > datetime('now', '-24 hours')
                GROUP BY provider, model
            ''')

            performance_metrics = cursor.fetchall()

            conn.close()

            # Calculate statistics
            total_decisions = len(recent_decisions)
            avg_confidence = sum(row[2] for row in recent_decisions) / max(total_decisions, 1)

            provider_usage = {}
            for row in recent_decisions:
                provider = row[0]
                provider_usage[provider] = provider_usage.get(provider, 0) + 1

            return {
                "total_decisions_24h": total_decisions,
                "average_confidence": avg_confidence,
                "provider_usage": provider_usage,
                "performance_metrics": [
                    {
                        "provider": row[0],
                        "model": row[1],
                        "avg_latency": row[2],
                        "success_rate": row[3],
                        "total_requests": row[4]
                    }
                    for row in performance_metrics
                ]
            }

        except Exception as e:
            logger.error(f"Failed to get routing statistics: {e}")
            return {}

    def get_model_recommendations(self, task_type: TaskType, complexity: TaskComplexity) -> list[dict[str, Any]]:
        """Get model recommendations for a specific task type and complexity."""
        recommendations = []

        for _key, capability in self.model_capabilities.items():
            if (task_type in capability.task_types and
                self._meets_complexity_requirements(capability, complexity)):

                recommendation = {
                    "provider": capability.provider.value,
                    "model": capability.model_name,
                    "confidence": capability.success_rate,
                    "avg_latency": capability.avg_latency,
                    "cost_per_1k_tokens": capability.cost_per_1k_tokens,
                    "strengths": self._identify_model_strengths(capability, task_type),
                    "considerations": self._identify_model_considerations(capability, task_type)
                }

                recommendations.append(recommendation)

        # Sort by confidence (descending)
        recommendations.sort(key=lambda x: x["confidence"], reverse=True)

        return recommendations[:MAX_RECOMMENDATIONS]  # Top recommendations

    def _identify_model_strengths(self, capability: ModelCapability, task_type: TaskType) -> list[str]:
        """Identify strengths of a model for a specific task type."""
        strengths = []

        if capability.function_calling:
            strengths.append("Native function calling support")

        if capability.streaming:
            strengths.append("Real-time streaming")

        if capability.cost_per_1k_tokens == 0.0:
            strengths.append("Free local processing")

        if capability.success_rate > HIGH_RELIABILITY_THRESHOLD:
            strengths.append("High reliability")

        if capability.avg_latency < FAST_RESPONSE_THRESHOLD:
            strengths.append("Fast response times")

        # Task-specific strengths
        if task_type == TaskType.CODING and "codellama" in capability.model_name.lower():
            strengths.append("Specialized for code generation")

        if task_type == TaskType.CREATIVE and capability.provider == LLMProvider.CLAUDE:
            strengths.append("Strong creative capabilities")

        return strengths

    def _identify_model_considerations(self, capability: ModelCapability, task_type: TaskType) -> list[str]:
        """Identify considerations when using a model for a specific task type."""
        considerations = []

        if capability.provider == LLMProvider.OLLAMA:
            considerations.append("Local processing - requires local resources")

        if capability.cost_per_1k_tokens > HIGH_COST_THRESHOLD:
            considerations.append("Higher cost for large requests")

        if capability.avg_latency > SLOW_RESPONSE_THRESHOLD:
            considerations.append("Slower response times")

        if capability.success_rate < LOW_RELIABILITY_THRESHOLD:
            considerations.append("Lower reliability")

        if not capability.function_calling and task_type == TaskType.FUNCTION_CALLING:
            considerations.append("Function calling not supported")

        return considerations

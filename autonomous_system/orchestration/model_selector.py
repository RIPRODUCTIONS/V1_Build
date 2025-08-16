"""
Intelligent Model & Agent Selection System

This module provides automatic selection of optimal AI models and agents based on:
- Task category and complexity
- Privacy/security requirements
- Cost constraints and budgets
- Performance requirements (speed vs quality)
- Available resources (GPU, memory, API limits)
- Historical performance data
- Current system load
- Deadline urgency
"""

import asyncio
import json
import logging
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelProvider(Enum):
    """AI model providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    OSS20B = "oss20b"
    GOOGLE = "google"
    AZURE = "azure"

class ModelCapability(Enum):
    """Model capabilities"""
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    ANALYSIS = "analysis"
    CREATIVITY = "creativity"
    REASONING = "reasoning"
    MULTIMODAL = "multimodal"
    FUNCTION_CALLING = "function_calling"
    STREAMING = "streaming"

@dataclass
class ModelInfo:
    """Information about an AI model"""
    name: str
    provider: ModelProvider
    capabilities: list[ModelCapability]
    max_tokens: int
    cost_per_1k_tokens: float
    avg_latency_ms: float
    accuracy_score: float
    privacy_level: str  # local, private, public
    gpu_required: bool
    memory_requirement_gb: float
    availability_score: float
    last_updated: datetime

@dataclass
class SelectionCriteria:
    """Criteria for model selection"""
    task_category: str
    complexity: float
    priority: int
    privacy_required: bool
    max_cost: float | None
    speed_priority: bool
    quality_priority: bool
    required_capabilities: list[ModelCapability]
    max_latency_ms: float | None
    gpu_available: bool
    memory_available_gb: float

@dataclass
class ModelSelection:
    """Result of model selection"""
    selected_model: str
    provider: ModelProvider
    confidence_score: float
    reasoning: str
    estimated_cost: float
    estimated_latency_ms: float
    alternative_models: list[str]
    fallback_model: str

class ModelSelector:
    """Intelligent model selection system"""

    def __init__(self, llm_manager, cost_tracker, config: dict[str, Any]):
        self.llm_manager = llm_manager
        self.cost_tracker = cost_tracker
        self.config = config
        self.performance_history = {}
        self.current_loads = {}
        self.model_capabilities = {}
        self.db_path = Path(config.get("database", {}).get("path", "model_selector.db"))
        self._init_database()
        self._load_model_capabilities()

        # Start background monitoring
        asyncio.create_task(self._monitor_system_load())

    def _init_database(self):
        """Initialize model selection database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_capabilities (
                    model_name TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    capabilities TEXT,
                    max_tokens INTEGER,
                    cost_per_1k_tokens REAL,
                    avg_latency_ms REAL,
                    accuracy_score REAL,
                    privacy_level TEXT,
                    gpu_required BOOLEAN,
                    memory_requirement_gb REAL,
                    availability_score REAL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS selection_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    selected_model TEXT NOT NULL,
                    selection_criteria TEXT,
                    confidence_score REAL,
                    actual_performance REAL,
                    cost_actual REAL,
                    latency_actual REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_performance (
                    model_name TEXT NOT NULL,
                    task_category TEXT NOT NULL,
                    success_rate REAL,
                    avg_cost REAL,
                    avg_latency_ms REAL,
                    total_uses INTEGER,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (model_name, task_category)
                )
            """)

            conn.commit()
            conn.close()
            logger.info("Model selector database initialized")

        except Exception as e:
            logger.error(f"Failed to initialize model selector database: {e}")
            raise

    def _load_model_capabilities(self):
        """Load model capabilities from database or defaults"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM model_capabilities")
            rows = cursor.fetchall()

            if rows:
                for row in rows:
                    self.model_capabilities[row[0]] = ModelInfo(
                        name=row[0],
                        provider=ModelProvider(row[1]),
                        capabilities=json.loads(row[2]) if row[2] else [],
                        max_tokens=row[3] or 4096,
                        cost_per_1k_tokens=row[4] or 0.0,
                        avg_latency_ms=row[5] or 1000.0,
                        accuracy_score=row[6] or 0.8,
                        privacy_level=row[7] or "public",
                        gpu_required=bool(row[8]),
                        memory_requirement_gb=row[9] or 0.0,
                        availability_score=row[10] or 1.0,
                        last_updated=datetime.fromisoformat(row[11]) if row[11] else datetime.now()
                    )
            else:
                # Load default capabilities
                self._load_default_capabilities()

            conn.close()

        except Exception as e:
            logger.error(f"Failed to load model capabilities: {e}")
            self._load_default_capabilities()

    def _load_default_capabilities(self):
        """Load default model capabilities"""
        default_models = {
            "gpt-4": ModelInfo(
                name="gpt-4",
                provider=ModelProvider.OPENAI,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.ANALYSIS,
                    ModelCapability.REASONING,
                    ModelCapability.FUNCTION_CALLING
                ],
                max_tokens=8192,
                cost_per_1k_tokens=0.03,
                avg_latency_ms=2000.0,
                accuracy_score=0.95,
                privacy_level="public",
                gpu_required=False,
                memory_requirement_gb=0.0,
                availability_score=0.99,
                last_updated=datetime.now()
            ),
            "gpt-4o-mini": ModelInfo(
                name="gpt-4o-mini",
                provider=ModelProvider.OPENAI,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.ANALYSIS
                ],
                max_tokens=16384,
                cost_per_1k_tokens=0.00015,
                avg_latency_ms=1000.0,
                accuracy_score=0.88,
                privacy_level="public",
                gpu_required=False,
                memory_requirement_gb=0.0,
                availability_score=0.99,
                last_updated=datetime.now()
            ),
            "claude-3.5-sonnet": ModelInfo(
                name="claude-3.5-sonnet",
                provider=ModelProvider.ANTHROPIC,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.ANALYSIS,
                    ModelCapability.REASONING,
                    ModelCapability.FUNCTION_CALLING
                ],
                max_tokens=200000,
                cost_per_1k_tokens=0.003,
                avg_latency_ms=1500.0,
                accuracy_score=0.92,
                privacy_level="public",
                gpu_required=False,
                memory_requirement_gb=0.0,
                availability_score=0.98,
                last_updated=datetime.now()
            ),
            "llama3.1:8b": ModelInfo(
                name="llama3.1:8b",
                provider=ModelProvider.OLLAMA,
                capabilities=[
                    ModelCapability.TEXT_GENERATION,
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.ANALYSIS
                ],
                max_tokens=8192,
                cost_per_1k_tokens=0.0,
                avg_latency_ms=500.0,
                accuracy_score=0.75,
                privacy_level="local",
                gpu_required=True,
                memory_requirement_gb=8.0,
                availability_score=0.95,
                last_updated=datetime.now()
            ),
            "codellama:13b": ModelInfo(
                name="codellama:13b",
                provider=ModelProvider.OLLAMA,
                capabilities=[
                    ModelCapability.CODE_GENERATION,
                    ModelCapability.TEXT_GENERATION
                ],
                max_tokens=8192,
                cost_per_1k_tokens=0.0,
                avg_latency_ms=800.0,
                accuracy_score=0.82,
                privacy_level="local",
                gpu_required=True,
                memory_requirement_gb=13.0,
                availability_score=0.90,
                last_updated=datetime.now()
            )
        }

        self.model_capabilities.update(default_models)
        logger.info(f"Loaded {len(default_models)} default model capabilities")

    async def select_optimal_model(self, task_classification: dict,
                                 constraints: dict = None) -> ModelSelection:
        """Select the optimal model for a given task"""

        start_time = time.time()

        # Create selection criteria
        criteria = self._create_selection_criteria(task_classification, constraints)

        # Get candidate models
        candidates = self._get_candidate_models(criteria)

        if not candidates:
            logger.warning("No suitable models found, using fallback")
            return self._create_fallback_selection(criteria)

        # Score each candidate
        scored_candidates = []
        for model_name in candidates:
            score = await self._score_model_for_task(model_name, criteria)
            scored_candidates.append((model_name, score))

        # Sort by score and select best
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        selected_model = scored_candidates[0][0]

        # Create selection result
        selection = self._create_model_selection(
            selected_model, scored_candidates, criteria
        )

        # Log selection
        await self._log_model_selection(task_classification, selection)

        # Update performance tracking
        await self._update_model_usage(selected_model, criteria.task_category)

        logger.info(f"Selected model {selected_model} with confidence {selection.confidence_score:.2f}")

        return selection

    def _create_selection_criteria(self, task_classification: dict,
                                 constraints: dict) -> SelectionCriteria:
        """Create selection criteria from task classification"""
        constraints = constraints or {}

        return SelectionCriteria(
            task_category=task_classification.get('category', 'general'),
            complexity=task_classification.get('complexity', 0.5),
            priority=task_classification.get('priority', 5),
            privacy_required=constraints.get('privacy_sensitive', False),
            max_cost=constraints.get('max_cost_per_task'),
            speed_priority=constraints.get('speed_priority', False),
            quality_priority=constraints.get('quality_priority', False),
            required_capabilities=self._map_capabilities(task_classification),
            max_latency_ms=constraints.get('max_latency_ms'),
            gpu_available=self._check_gpu_availability(),
            memory_available_gb=self._check_memory_availability()
        )

    def _map_capabilities(self, task_classification: dict) -> list[ModelCapability]:
        """Map task requirements to model capabilities"""
        capabilities = []
        category = task_classification.get('category', 'general')

        if category in ['coding', 'development']:
            capabilities.append(ModelCapability.CODE_GENERATION)

        if category in ['analysis', 'research']:
            capabilities.append(ModelCapability.ANALYSIS)
            capabilities.append(ModelCapability.REASONING)

        if category in ['content_creation', 'writing']:
            capabilities.append(ModelCapability.CREATIVITY)
            capabilities.append(ModelCapability.TEXT_GENERATION)

        if category in ['automation']:
            capabilities.append(ModelCapability.FUNCTION_CALLING)

        # Always include basic text generation
        if ModelCapability.TEXT_GENERATION not in capabilities:
            capabilities.append(ModelCapability.TEXT_GENERATION)

        return capabilities

    def _get_candidate_models(self, criteria: SelectionCriteria) -> list[str]:
        """Get candidate models based on selection criteria"""
        candidates = []

        for model_name, model_info in self.model_capabilities.items():
            if self._is_model_suitable(model_info, criteria):
                candidates.append(model_name)

        return candidates

    def _is_model_suitable(self, model_info: ModelInfo, criteria: SelectionCriteria) -> bool:
        """Check if a model is suitable for the given criteria"""

        # Check required capabilities
        for required_capability in criteria.required_capabilities:
            if required_capability not in model_info.capabilities:
                return False

        # Check privacy requirements
        if criteria.privacy_required and model_info.privacy_level != "local":
            return False

        # Check GPU requirements
        if model_info.gpu_required and not criteria.gpu_available:
            return False

        # Check memory requirements
        if model_info.memory_requirement_gb > criteria.memory_available_gb:
            return False

        # Check cost constraints
        if criteria.max_cost is not None:
            estimated_cost = self._estimate_task_cost(model_info, criteria)
            if estimated_cost > criteria.max_cost:
                return False

        # Check latency constraints
        if criteria.max_latency_ms is not None:
            if model_info.avg_latency_ms > criteria.max_latency_ms:
                return False

        return True

    async def _score_model_for_task(self, model_name: str,
                                  criteria: SelectionCriteria) -> float:
        """Score a model's suitability for a specific task"""
        model_info = self.model_capabilities[model_name]
        score = 0.0

        # Performance score based on historical data
        performance_score = await self._get_historical_performance(model_name, criteria.task_category)
        score += performance_score * 0.3

        # Cost efficiency score
        cost_score = self._calculate_cost_efficiency(model_info, criteria)
        score += cost_score * 0.25

        # Speed score
        speed_score = self._get_speed_score(model_info, criteria)
        score += speed_score * 0.2

        # Availability score
        availability_score = await self._get_availability_score(model_name)
        score += availability_score * 0.15

        # Capability match score
        capability_score = self._get_capability_match(model_info, criteria)
        score += capability_score * 0.1

        # Apply constraint penalties
        if criteria.privacy_required and model_info.privacy_level != "local":
            score *= 0.5  # Heavy penalty for non-local models

        if criteria.max_cost:
            estimated_cost = self._estimate_task_cost(model_info, criteria)
            if estimated_cost > criteria.max_cost:
                score *= 0.1  # Heavy penalty for exceeding budget

        return score

    async def _get_historical_performance(self, model_name: str, task_category: str) -> float:
        """Get historical performance for a model on a specific task category"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT success_rate, avg_cost, avg_latency_ms, total_uses
                FROM model_performance
                WHERE model_name = ? AND task_category = ?
            """, (model_name, task_category))

            row = cursor.fetchone()
            conn.close()

            if row:
                success_rate, avg_cost, avg_latency, total_uses = row

                # Weight by number of uses
                if total_uses > 10:
                    return success_rate
                elif total_uses > 5:
                    return success_rate * 0.8
                else:
                    return 0.5  # Default score for new models

            return 0.5  # Default score

        except Exception as e:
            logger.error(f"Failed to get historical performance: {e}")
            return 0.5

    def _calculate_cost_efficiency(self, model_info: ModelInfo, criteria: SelectionCriteria) -> float:
        """Calculate cost efficiency score"""
        if model_info.cost_per_1k_tokens == 0:
            return 1.0  # Local models are most cost-efficient

        # Lower cost = higher score
        max_cost = 0.01  # $0.01 per 1k tokens
        cost_score = max(0, 1 - (model_info.cost_per_1k_tokens / max_cost))

        return cost_score

    def _get_speed_score(self, model_info: ModelInfo, criteria: SelectionCriteria) -> float:
        """Calculate speed score based on criteria"""
        if criteria.speed_priority:
            # For speed priority, lower latency = higher score
            max_latency = 5000  # 5 seconds
            speed_score = max(0, 1 - (model_info.avg_latency_ms / max_latency))
        else:
            # For quality priority, moderate speed is fine
            speed_score = 0.7 if model_info.avg_latency_ms < 3000 else 0.5

        return speed_score

    async def _get_availability_score(self, model_name: str) -> float:
        """Get current availability score for a model"""
        model_info = self.model_capabilities[model_name]

        # Check current load
        current_load = self.current_loads.get(model_name, 0.0)
        load_score = max(0, 1 - current_load)

        # Combine with base availability
        availability_score = (model_info.availability_score + load_score) / 2

        return availability_score

    def _get_capability_match(self, model_info: ModelInfo, criteria: SelectionCriteria) -> float:
        """Calculate capability match score"""
        required_capabilities = set(criteria.required_capabilities)
        available_capabilities = set(model_info.capabilities)

        if not required_capabilities:
            return 0.5

        match_ratio = len(required_capabilities.intersection(available_capabilities)) / len(required_capabilities)
        return match_ratio

    def _estimate_task_cost(self, model_info: ModelInfo, criteria: SelectionCriteria) -> float:
        """Estimate cost for a task using this model"""
        if model_info.cost_per_1k_tokens == 0:
            return 0.0  # Local models

        # Estimate tokens based on complexity
        estimated_tokens = int(criteria.complexity * 2000)  # Base 2000 tokens
        cost = (estimated_tokens / 1000) * model_info.cost_per_1k_tokens

        return cost

    def _create_model_selection(self, selected_model: str,
                              scored_candidates: list[tuple[str, float]],
                              criteria: SelectionCriteria) -> ModelSelection:
        """Create model selection result"""
        model_info = self.model_capabilities[selected_model]

        # Get alternative models
        alternative_models = [name for name, score in scored_candidates[1:4]]  # Top 3 alternatives

        # Get fallback model
        fallback_model = self._select_fallback_model(criteria)

        # Calculate confidence score
        best_score = scored_candidates[0][1]
        confidence_score = min(1.0, best_score)

        # Estimate cost and latency
        estimated_cost = self._estimate_task_cost(model_info, criteria)
        estimated_latency = model_info.avg_latency_ms

        return ModelSelection(
            selected_model=selected_model,
            provider=model_info.provider,
            confidence_score=confidence_score,
            reasoning=self._generate_selection_reasoning(selected_model, criteria, best_score),
            estimated_cost=estimated_cost,
            estimated_latency_ms=estimated_latency,
            alternative_models=alternative_models,
            fallback_model=fallback_model
        )

    def _select_fallback_model(self, criteria: SelectionCriteria) -> str:
        """Select a fallback model if the primary selection fails"""
        # Prefer local models for fallback
        fallback_candidates = []

        for model_name, model_info in self.model_capabilities.items():
            if (model_info.privacy_level == "local" and
                self._is_model_suitable(model_info, criteria)):
                fallback_candidates.append(model_name)

        if fallback_candidates:
            return fallback_candidates[0]

        # If no local models, use the most reliable cloud model
        return "gpt-4o-mini"

    def _generate_selection_reasoning(self, model_name: str, criteria: SelectionCriteria,
                                    score: float) -> str:
        """Generate human-readable reasoning for model selection"""
        model_info = self.model_capabilities[model_name]

        reasoning_parts = []

        if score > 0.8:
            reasoning_parts.append("Excellent match for task requirements")
        elif score > 0.6:
            reasoning_parts.append("Good match for task requirements")
        else:
            reasoning_parts.append("Adequate match for task requirements")

        if model_info.privacy_level == "local":
            reasoning_parts.append("Local deployment ensures privacy")

        if model_info.cost_per_1k_tokens == 0:
            reasoning_parts.append("Cost-effective local model")

        if criteria.speed_priority and model_info.avg_latency_ms < 1000:
            reasoning_parts.append("Fast response time for speed-critical tasks")

        if criteria.quality_priority and model_info.accuracy_score > 0.9:
            reasoning_parts.append("High accuracy for quality-critical tasks")

        return ". ".join(reasoning_parts)

    def _create_fallback_selection(self, criteria: SelectionCriteria) -> ModelSelection:
        """Create fallback selection when no suitable models found"""
        fallback_model = self._select_fallback_model(criteria)
        model_info = self.model_capabilities[fallback_model]

        return ModelSelection(
            selected_model=fallback_model,
            provider=model_info.provider,
            confidence_score=0.3,
            reasoning="Fallback selection due to constraints",
            estimated_cost=self._estimate_task_cost(model_info, criteria),
            estimated_latency_ms=model_info.avg_latency_ms,
            alternative_models=[],
            fallback_model=fallback_model
        )

    async def _log_model_selection(self, task_classification: dict, selection: ModelSelection):
        """Log model selection for analysis"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO selection_history
                (task_id, selected_model, selection_criteria, confidence_score)
                VALUES (?, ?, ?, ?)
            """, (
                task_classification.get('id', 'unknown'),
                selection.selected_model,
                json.dumps(task_classification),
                selection.confidence_score
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to log model selection: {e}")

    async def _update_model_usage(self, model_name: str, task_category: str):
        """Update model usage statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Update or insert performance record
            cursor.execute("""
                INSERT OR REPLACE INTO model_performance
                (model_name, task_category, total_uses, last_used)
                VALUES (
                    ?, ?,
                    COALESCE((SELECT total_uses FROM model_performance
                              WHERE model_name = ? AND task_category = ?), 0) + 1,
                    CURRENT_TIMESTAMP
                )
            """, (model_name, task_category, model_name, task_category))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to update model usage: {e}")

    def _check_gpu_availability(self) -> bool:
        """Check if GPU is available"""
        # This would integrate with system monitoring
        # For now, assume GPU is available
        return True

    def _check_memory_availability(self) -> float:
        """Check available memory in GB"""
        # This would integrate with system monitoring
        # For now, assume 16GB available
        return 16.0

    async def _monitor_system_load(self):
        """Monitor system load for all models"""
        while True:
            try:
                # Update current loads for all models
                for model_name in self.model_capabilities:
                    load = await self._get_current_model_load(model_name)
                    self.current_loads[model_name] = load

                await asyncio.sleep(30)  # Update every 30 seconds

            except Exception as e:
                logger.error(f"Error monitoring system load: {e}")
                await asyncio.sleep(60)

    async def _get_current_model_load(self, model_name: str) -> float:
        """Get current load for a specific model"""
        # This would integrate with actual system monitoring
        # For now, return random load for demonstration
        import random
        return random.uniform(0.0, 1.0)

    async def get_selection_history(self, limit: int = 100) -> list[dict]:
        """Get model selection history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM selection_history
                ORDER BY timestamp DESC LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            history = []

            for row in rows:
                history.append({
                    'id': row[0],
                    'task_id': row[1],
                    'selected_model': row[2],
                    'selection_criteria': json.loads(row[3]) if row[3] else {},
                    'confidence_score': row[4],
                    'actual_performance': row[5],
                    'cost_actual': row[6],
                    'latency_actual': row[7],
                    'timestamp': row[8]
                })

            conn.close()
            return history

        except Exception as e:
            logger.error(f"Failed to get selection history: {e}")
            return []

    async def update_performance_metrics(self, task_id: str, actual_performance: float,
                                       cost_actual: float, latency_actual: float):
        """Update actual performance metrics for a task"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE selection_history
                SET actual_performance = ?, cost_actual = ?, latency_actual = ?
                WHERE task_id = ?
            """, (actual_performance, cost_actual, latency_actual, task_id))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to update performance metrics: {e}")


# Example usage
async def main():
    """Example usage of the model selector"""
    # Mock LLM manager and cost tracker
    class MockLLMManager:
        pass

    class MockCostTracker:
        pass

    config = {
        "database": {"path": "test_model_selector.db"}
    }

    selector = ModelSelector(MockLLMManager(), MockCostTracker(), config)

    # Example task classification
    task_classification = {
        'id': 'task_1',
        'category': 'coding',
        'complexity': 0.7,
        'priority': 8,
        'required_skills': ['programming', 'debugging'],
        'required_tools': ['code_editor', 'debugger']
    }

    # Example constraints
    constraints = {
        'privacy_sensitive': False,
        'max_cost_per_task': 0.50,
        'speed_priority': True,
        'max_latency_ms': 2000
    }

    selection = await selector.select_optimal_model(task_classification, constraints)
    print(f"Selected Model: {selection.selected_model}")
    print(f"Confidence: {selection.confidence_score:.2f}")
    print(f"Reasoning: {selection.reasoning}")
    print(f"Estimated Cost: ${selection.estimated_cost:.4f}")
    print(f"Estimated Latency: {selection.estimated_latency_ms:.0f}ms")


if __name__ == "__main__":
    asyncio.run(main())

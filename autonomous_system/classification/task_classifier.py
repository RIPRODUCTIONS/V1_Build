"""
AI-Powered Task Classification System

This module provides intelligent task classification using multiple AI models:
- Multi-model consensus classification
- Confidence scoring and validation
- Task complexity assessment
- Resource requirement estimation
- Skill and tool requirement detection
"""

import asyncio
import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskCategory(Enum):
    """Task classification categories"""
    RESEARCH = "research"
    AUTOMATION = "automation"
    CONTENT_CREATION = "content_creation"
    COMMUNICATION = "communication"
    ANALYSIS = "analysis"
    CODING = "coding"
    ADMINISTRATIVE = "administrative"
    SECURITY = "security"
    CUSTOMER_SERVICE = "customer_service"
    MONITORING = "monitoring"

class TaskComplexity(Enum):
    """Task complexity levels"""
    TRIVIAL = 0.1
    SIMPLE = 0.3
    MODERATE = 0.5
    COMPLEX = 0.7
    VERY_COMPLEX = 0.9

@dataclass
class ClassificationResult:
    """Result of task classification"""
    category: TaskCategory
    subcategory: str
    complexity: float
    priority: int
    estimated_time_minutes: int
    required_skills: list[str]
    required_tools: list[str]
    confidence: float
    reasoning: str
    dependencies: list[str] = None
    success_criteria: list[str] = None
    potential_challenges: list[str] = None
    cost_estimate: float = 0.0
    privacy_requirements: str = "public"
    compliance_needs: list[str] = None

class TaskClassifier:
    """Intelligent task classification using multiple AI models"""

    def __init__(self, llm_manager, config: dict[str, Any]):
        self.llm_manager = llm_manager
        self.config = config
        self.classification_models = {
            'primary': 'ollama:llama3.1:8b',      # Fast, local classification
            'validation': 'openai:gpt-4o-mini',   # Validation and consensus
            'complex': 'openai:gpt-4'             # Complex task analysis
        }
        self.db_path = Path(config.get("database", {}).get("path", "task_classifier.db"))
        self._init_database()
        self.performance_history = {}

    def _init_database(self):
        """Initialize classification database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS classification_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT,
                    complexity REAL,
                    confidence REAL,
                    model_used TEXT,
                    classification_time_ms REAL,
                    accuracy_score REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_performance (
                    model_name TEXT PRIMARY KEY,
                    total_classifications INTEGER DEFAULT 0,
                    accuracy_score REAL DEFAULT 0.0,
                    avg_confidence REAL DEFAULT 0.0,
                    avg_classification_time_ms REAL DEFAULT 0.0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            conn.close()
            logger.info("Task classifier database initialized")

        except Exception as e:
            logger.error(f"Failed to initialize classifier database: {e}")
            raise

    async def classify_task(self, task, constraints: dict = None) -> ClassificationResult:
        """Classify task using multiple AI models for accuracy"""

        start_time = datetime.now()

        # Primary classification (fast, local)
        primary_result = await self._primary_classification(task)

        # Validation classification for important tasks
        if primary_result['confidence'] < 0.8 or task.priority.value > 7:
            validation_result = await self._validation_classification(task)
            final_result = self._consensus_classification(primary_result, validation_result)
        else:
            final_result = primary_result

        # Complex analysis for high-priority or complex tasks
        if final_result['complexity'] > 0.7 or task.priority.value > 8:
            complex_analysis = await self._complex_task_analysis(task)
            final_result.update(complex_analysis)

        # Apply constraints
        if constraints:
            final_result = self._apply_constraints(final_result, constraints)

        # Record performance
        classification_time = (datetime.now() - start_time).total_seconds() * 1000
        await self._record_classification_performance(
            task.id, final_result, classification_time
        )

        return ClassificationResult(**final_result)

    async def _primary_classification(self, task) -> dict[str, Any]:
        """Fast classification using local Ollama model"""
        prompt = f"""
        Classify this task quickly and accurately:

        Title: {task.title}
        Description: {task.description}
        Source: {task.source.value}
        Requester: {task.requester}

        Analyze and return JSON:
        {{
            "category": "one of: research, automation, content_creation, communication, analysis, coding, administrative, security, customer_service, monitoring",
            "subcategory": "specific subcategory",
            "complexity": 0.1-1.0,
            "priority": 1-10,
            "estimated_time_minutes": integer,
            "required_skills": ["skill1", "skill2"],
            "required_tools": ["tool1", "tool2"],
            "confidence": 0.1-1.0,
            "reasoning": "brief explanation"
        }}
        """

        try:
            response = await self.llm_manager.generate(
                prompt=prompt,
                provider='ollama',
                model='llama3.1:8b',
                stream=False
            )

            return self._parse_classification_response(response)

        except Exception as e:
            logger.error(f"Primary classification failed: {e}")
            return self._fallback_classification(task)

    async def _validation_classification(self, task) -> dict[str, Any]:
        """Validation using cloud model for accuracy"""
        prompt = f"""
        Validate and refine this task classification:

        Task Details:
        Title: {task.title}
        Description: {task.description}
        Context: {task.context}

        Provide detailed classification with high accuracy:
        {{
            "category": "precise category",
            "subcategory": "detailed subcategory",
            "complexity": "0.1-1.0 with reasoning",
            "priority": "1-10 with justification",
            "estimated_time_minutes": "realistic estimate",
            "required_skills": ["specific skills needed"],
            "required_tools": ["exact tools needed"],
            "dependencies": ["task dependencies"],
            "success_criteria": ["measurable outcomes"],
            "potential_challenges": ["anticipated issues"],
            "confidence": "0.1-1.0"
        }}
        """

        try:
            response = await self.llm_manager.generate(
                prompt=prompt,
                provider='openai',
                model='gpt-4o-mini',
                stream=False
            )

            return self._parse_classification_response(response)

        except Exception as e:
            logger.error(f"Validation classification failed: {e}")
            return self._fallback_classification(task)

    async def _complex_task_analysis(self, task) -> dict[str, Any]:
        """Complex analysis for high-priority tasks"""
        prompt = f"""
        Perform comprehensive analysis of this high-priority task:

        Task: {task.title}
        Description: {task.description}
        Priority: {task.priority.value}

        Provide detailed analysis:
        {{
            "complexity_breakdown": {{
                "technical_complexity": "0.1-1.0",
                "coordination_complexity": "0.1-1.0",
                "resource_complexity": "0.1-1.0"
            }},
            "risk_assessment": ["risk1", "risk2"],
            "resource_requirements": {{
                "human_resources": "number of people",
                "technical_resources": ["resource1", "resource2"],
                "time_resources": "total time needed"
            }},
            "success_metrics": ["metric1", "metric2"],
            "quality_requirements": "quality level needed"
        }}
        """

        try:
            response = await self.llm_manager.generate(
                prompt=prompt,
                provider='openai',
                model='gpt-4',
                stream=False
            )

            return self._parse_complex_analysis(response)

        except Exception as e:
            logger.error(f"Complex analysis failed: {e}")
            return {}

    def _consensus_classification(self, primary: dict, validation: dict) -> dict[str, Any]:
        """Combine multiple classifications for final result"""
        consensus = {}

        # Use validation result if significantly more confident
        if validation['confidence'] > primary['confidence'] + 0.2:
            consensus = validation.copy()
        # Use primary if similar confidence (faster model)
        elif abs(validation['confidence'] - primary['confidence']) < 0.2:
            consensus = primary.copy()
            # Take average of numerical values
            consensus['complexity'] = (primary['complexity'] + validation['complexity']) / 2
            consensus['priority'] = round((primary['priority'] + validation['priority']) / 2)
        else:
            consensus = validation.copy()

        # Combine skill and tool lists
        consensus['required_skills'] = list(set(
            primary.get('required_skills', []) + validation.get('required_skills', [])
        ))
        consensus['required_tools'] = list(set(
            primary.get('required_tools', []) + validation.get('required_tools', [])
        ))

        return consensus

    def _apply_constraints(self, result: dict, constraints: dict) -> dict:
        """Apply constraints to classification result"""
        if 'max_complexity' in constraints:
            result['complexity'] = min(result['complexity'], constraints['max_complexity'])

        if 'max_time' in constraints:
            result['estimated_time_minutes'] = min(
                result['estimated_time_minutes'],
                constraints['max_time']
            )

        if 'required_skills' in constraints:
            result['required_skills'] = list(set(
                result['required_skills'] + constraints['required_skills']
            ))

        if 'privacy_required' in constraints and constraints['privacy_required']:
            result['privacy_requirements'] = 'high'

        return result

    def _fallback_classification(self, task) -> dict[str, Any]:
        """Fallback classification when AI models fail"""
        return {
            "category": "administrative",
            "subcategory": "general",
            "complexity": 0.5,
            "priority": task.priority.value,
            "estimated_time_minutes": 60,
            "required_skills": ["general"],
            "required_tools": ["basic_tools"],
            "confidence": 0.3,
            "reasoning": "Fallback classification due to AI model failure"
        }

    def _parse_classification_response(self, response) -> dict[str, Any]:
        """Parse AI model response into structured format"""
        try:
            # Try to extract JSON from response
            if isinstance(response, str):
                # Look for JSON in the response
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = response[start_idx:end_idx]
                    parsed = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")
            else:
                # Assume response is already parsed
                parsed = response

            # Validate and normalize
            return {
                "category": parsed.get("category", "administrative"),
                "subcategory": parsed.get("subcategory", "general"),
                "complexity": float(parsed.get("complexity", 0.5)),
                "priority": int(parsed.get("priority", 5)),
                "estimated_time_minutes": int(parsed.get("estimated_time_minutes", 60)),
                "required_skills": parsed.get("required_skills", []),
                "required_tools": parsed.get("required_tools", []),
                "confidence": float(parsed.get("confidence", 0.5)),
                "reasoning": parsed.get("reasoning", "No reasoning provided"),
                "dependencies": parsed.get("dependencies", []),
                "success_criteria": parsed.get("success_criteria", []),
                "potential_challenges": parsed.get("potential_challenges", [])
            }

        except Exception as e:
            logger.error(f"Failed to parse classification response: {e}")
            return self._fallback_classification(None)

    def _parse_complex_analysis(self, response) -> dict[str, Any]:
        """Parse complex analysis response"""
        try:
            if isinstance(response, str):
                start_idx = response.find('{')
                end_idx = response.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = response[start_idx:end_idx]
                    return json.loads(json_str)

            return {}

        except Exception as e:
            logger.error(f"Failed to parse complex analysis: {e}")
            return {}

    async def _record_classification_performance(self, task_id: str, result: dict,
                                               classification_time: float):
        """Record classification performance metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO classification_history
                (task_id, category, subcategory, complexity, confidence,
                 model_used, classification_time_ms, accuracy_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id,
                result.get('category', 'unknown'),
                result.get('subcategory', 'unknown'),
                result.get('complexity', 0.5),
                result.get('confidence', 0.5),
                'consensus',  # Model used
                classification_time,
                0.0  # Accuracy score (would be updated later)
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to record classification performance: {e}")

    async def get_classification_history(self, limit: int = 100) -> list[dict]:
        """Get classification history for analysis"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM classification_history
                ORDER BY timestamp DESC LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            history = []

            for row in rows:
                history.append({
                    'id': row[0],
                    'task_id': row[1],
                    'category': row[2],
                    'subcategory': row[3],
                    'complexity': row[4],
                    'confidence': row[5],
                    'model_used': row[6],
                    'classification_time_ms': row[7],
                    'accuracy_score': row[8],
                    'timestamp': row[9]
                })

            conn.close()
            return history

        except Exception as e:
            logger.error(f"Failed to get classification history: {e}")
            return []

    async def update_accuracy_scores(self, task_results: list[dict]):
        """Update accuracy scores based on task outcomes"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for result in task_results:
                task_id = result['task_id']
                accuracy = result.get('accuracy_score', 0.0)

                cursor.execute("""
                    UPDATE classification_history
                    SET accuracy_score = ?
                    WHERE task_id = ?
                """, (accuracy, task_id))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to update accuracy scores: {e}")

    async def get_model_performance(self) -> dict[str, Any]:
        """Get performance metrics for different models"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT model_used,
                       COUNT(*) as total,
                       AVG(confidence) as avg_confidence,
                       AVG(classification_time_ms) as avg_time,
                       AVG(accuracy_score) as avg_accuracy
                FROM classification_history
                GROUP BY model_used
            """)

            performance = {}
            for row in cursor.fetchall():
                performance[row[0]] = {
                    'total_classifications': row[1],
                    'avg_confidence': row[2],
                    'avg_classification_time_ms': row[3],
                    'avg_accuracy': row[4]
                }

            conn.close()
            return performance

        except Exception as e:
            logger.error(f"Failed to get model performance: {e}")
            return {}


class TaskComplexityAnalyzer:
    """Analyzes task complexity using multiple factors"""

    def __init__(self):
        self.complexity_factors = {
            'technical': 0.3,
            'coordination': 0.25,
            'resource': 0.2,
            'time': 0.15,
            'stakeholder': 0.1
        }

    def analyze_complexity(self, task, classification: ClassificationResult) -> float:
        """Analyze overall task complexity"""
        scores = {}

        # Technical complexity
        scores['technical'] = self._assess_technical_complexity(task, classification)

        # Coordination complexity
        scores['coordination'] = self._assess_coordination_complexity(task, classification)

        # Resource complexity
        scores['resource'] = self._assess_resource_complexity(task, classification)

        # Time complexity
        scores['time'] = self._assess_time_complexity(task, classification)

        # Stakeholder complexity
        scores['stakeholder'] = self._assess_stakeholder_complexity(task, classification)

        # Calculate weighted average
        total_complexity = 0.0
        for factor, weight in self.complexity_factors.items():
            total_complexity += scores[factor] * weight

        return min(1.0, total_complexity)

    def _assess_technical_complexity(self, task, classification) -> float:
        """Assess technical complexity of the task"""
        complexity = 0.5

        # Skill requirements
        if len(classification.required_skills) > 5:
            complexity += 0.3
        elif len(classification.required_skills) > 3:
            complexity += 0.2

        # Tool requirements
        if len(classification.required_tools) > 3:
            complexity += 0.2

        # Category-based complexity
        if classification.category in [TaskCategory.CODING, TaskCategory.SECURITY]:
            complexity += 0.2

        return min(1.0, complexity)

    def _assess_coordination_complexity(self, task, classification) -> float:
        """Assess coordination complexity"""
        complexity = 0.3

        # Stakeholder count
        if len(task.stakeholders) > 5:
            complexity += 0.4
        elif len(task.stakeholders) > 2:
            complexity += 0.2

        # Dependencies
        if len(classification.dependencies or []) > 3:
            complexity += 0.3

        # Communication requirements
        if classification.category == TaskCategory.COMMUNICATION:
            complexity += 0.2

        return min(1.0, complexity)

    def _assess_resource_complexity(self, task, classification) -> float:
        """Assess resource complexity"""
        complexity = 0.4

        # Budget constraints
        if task.budget_constraints and task.budget_constraints < 100:
            complexity += 0.3

        # Time constraints
        if task.deadline:
            time_until_deadline = (task.deadline - datetime.now()).total_seconds()
            if time_until_deadline < 3600:  # Less than 1 hour
                complexity += 0.4
            elif time_until_deadline < 86400:  # Less than 1 day
                complexity += 0.2

        return min(1.0, complexity)

    def _assess_time_complexity(self, task, classification) -> float:
        """Assess time complexity"""
        complexity = 0.3

        estimated_time = classification.estimated_time_minutes

        if estimated_time > 480:  # More than 8 hours
            complexity += 0.4
        elif estimated_time > 240:  # More than 4 hours
            complexity += 0.3
        elif estimated_time > 120:  # More than 2 hours
            complexity += 0.2

        return min(1.0, complexity)

    def _assess_stakeholder_complexity(self, task, classification) -> float:
        """Assess stakeholder complexity"""
        complexity = 0.2

        # VIP stakeholders
        vip_stakeholders = [s for s in task.stakeholders if 'ceo' in s.lower() or 'cto' in s.lower()]
        if vip_stakeholders:
            complexity += 0.3

        # External stakeholders
        external_stakeholders = [s for s in task.stakeholders if '@' in s and 'company.com' not in s]
        if external_stakeholders:
            complexity += 0.2

        return min(1.0, complexity)


# Example usage
async def main():
    """Example usage of the task classifier"""
    # Mock LLM manager for testing
    class MockLLMManager:
        async def generate(self, prompt, provider, model, stream=False):
            return '{"category": "research", "subcategory": "data_analysis", "complexity": 0.7, "priority": 8, "estimated_time_minutes": 180, "required_skills": ["research", "analysis"], "required_tools": ["database", "analytics"], "confidence": 0.85, "reasoning": "Task involves data collection and analysis"}'

    config = {
        "database": {"path": "test_classifier.db"}
    }

    classifier = TaskClassifier(MockLLMManager(), config)

    # Mock task
    from autonomous_system.discovery.task_detector import DetectedTask, TaskPriority, TaskSource

    task = DetectedTask(
        id="test_1",
        source=TaskSource.EMAIL,
        title="Analyze Q4 sales data",
        description="Need comprehensive analysis of Q4 sales performance with recommendations",
        priority=TaskPriority.HIGH,
        deadline=None,
        requester="sales@company.com",
        context={},
        raw_data={},
        detected_at=datetime.now(),
        estimated_complexity=0.6,
        required_skills=[],
        dependencies=[],
        tags=[],
        estimated_duration_minutes=120,
        success_criteria=[],
        stakeholders=["sales_team", "management"],
        budget_constraints=None
    )

    result = await classifier.classify_task(task)
    print(f"Classification Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())

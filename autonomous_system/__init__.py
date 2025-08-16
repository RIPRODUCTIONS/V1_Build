"""
Autonomous Task Solver System

A comprehensive, self-running AI automation framework that automatically:
1. Discovers tasks from multiple sources (emails, APIs, webhooks, schedules)
2. Classifies and prioritizes tasks intelligently
3. Selects optimal AI models and agents for each task
4. Executes tasks with minimal human intervention
5. Monitors progress and handles failures automatically
6. Learns from outcomes to improve future decisions
7. Reports results and suggests optimizations

Core Components:
- Task Detection: Multi-source task discovery and monitoring
- Task Classification: AI-powered task categorization and analysis
- Model Selection: Intelligent AI model and agent selection
- Task Execution: Autonomous workflow execution and management
- Decision Engine: Central intelligence for system orchestration
- Learning System: Continuous improvement and optimization
- Monitoring: Real-time system health and performance tracking
"""

__version__ = "1.0.0"
__author__ = "Autonomous System Team"

from .classification.task_classifier import ClassificationResult, TaskCategory, TaskClassifier
from .discovery.task_detector import DetectedTask, TaskDetector, TaskPriority, TaskSource
from .execution.task_executor import AutonomousTaskExecutor, ExecutionResult, WorkflowDefinition
from .intelligence.decision_engine import Decision, DecisionEngine, DecisionType
from .orchestration.model_selector import ModelProvider, ModelSelection, ModelSelector

__all__ = [
    # Core classes
    "TaskDetector",
    "DetectedTask",
    "TaskSource",
    "TaskPriority",
    "TaskClassifier",
    "ClassificationResult",
    "TaskCategory",
    "ModelSelector",
    "ModelSelection",
    "ModelProvider",
    "AutonomousTaskExecutor",
    "ExecutionResult",
    "WorkflowDefinition",
    "DecisionEngine",
    "Decision",
    "DecisionType"
]

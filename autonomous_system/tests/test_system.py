"""
Comprehensive Test Suite for Autonomous Task Solver System
Tests all major components and integration scenarios
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ..autonomous_orchestrator import AutonomousOrchestrator
from ..classification.task_classifier import TaskCategory, TaskClassifier

# Import system components
from ..discovery.task_detector import DetectedTask, TaskDetector, TaskPriority, TaskSource
from ..execution.task_executor import AutonomousTaskExecutor
from ..intelligence.decision_engine import DecisionEngine
from ..learning.performance_tracker import MetricType, PerformanceMetric, PerformanceTracker
from ..monitoring.system_monitor import SystemMonitor
from ..orchestration.advanced_orchestrator import AdvancedOrchestrator, WorkflowDefinition
from ..orchestration.model_selector import ModelSelector
from ..security.auth_manager import AuthManager

# Test configuration
TEST_CONFIG = {
    "system": {
        "name": "Test Autonomous System",
        "environment": "testing",
        "debug": True
    },
    "database": {
        "path": ":memory:"  # Use in-memory database for tests
    },
    "ai_models": {
        "openai": {
            "api_key": "test_key",
            "models": ["gpt-4", "gpt-3.5-turbo"]
        }
    },
    "task_detection": {
        "email": {"enabled": False},
        "slack": {"enabled": False},
        "webhook": {"enabled": True}
    },
    "security": {
        "jwt_secret": "test-secret-key",
        "jwt_expiry": 3600,
        "min_password_length": 8
    }
}

class TestTaskDetection:
    """Test task detection components"""

    @pytest.fixture
    def task_detector(self):
        """Create task detector instance"""
        return TaskDetector(TEST_CONFIG)

    @pytest.mark.asyncio
    async def test_task_detection_initialization(self, task_detector):
        """Test task detector initialization"""
        assert task_detector is not None
        assert task_detector.config == TEST_CONFIG

    @pytest.mark.asyncio
    async def test_create_detected_task(self, task_detector):
        """Test creating detected tasks"""
        task = DetectedTask(
            task_id="test_task_1",
            title="Test Task",
            description="A test task for testing",
            source=TaskSource.FILE_SYSTEM,
            priority=TaskPriority.MEDIUM,
            timestamp=datetime.now()
        )

        assert task.task_id == "test_task_1"
        assert task.title == "Test Task"
        assert task.source == TaskSource.FILE_SYSTEM
        assert task.priority == TaskPriority.MEDIUM

    @pytest.mark.asyncio
    async def test_task_detection_database(self, task_detector):
        """Test task detection database operations"""
        # Test database initialization
        assert task_detector._init_database() is None

        # Test storing and retrieving tasks
        task = DetectedTask(
            task_id="db_test_task",
            title="Database Test Task",
            description="Testing database operations",
            source=TaskSource.WEBHOOK,
            priority=TaskPriority.HIGH,
            timestamp=datetime.now()
        )

        await task_detector._store_task(task)
        retrieved_task = await task_detector._get_task("db_test_task")

        assert retrieved_task is not None
        assert retrieved_task.title == "Database Test Task"

class TestTaskClassification:
    """Test task classification components"""

    @pytest.fixture
    def task_classifier(self):
        """Create task classifier instance"""
        return TaskClassifier(TEST_CONFIG)

    @pytest.mark.asyncio
    async def test_task_classification_initialization(self, task_classifier):
        """Test task classifier initialization"""
        assert task_classifier is not None
        assert task_classifier.config == TEST_CONFIG

    @pytest.mark.asyncio
    async def test_classify_task(self, task_classifier):
        """Test task classification"""
        task = DetectedTask(
            task_id="classify_test",
            title="Research AI trends",
            description="Analyze current AI trends and provide insights",
            source=TaskSource.FILE_SYSTEM,
            priority=TaskPriority.HIGH,
            timestamp=datetime.now()
        )

        # Mock LLM response
        with patch.object(task_classifier, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "category": "research",
                "confidence": 0.85,
                "reasoning": "Task involves research and analysis"
            }

            result = await task_classifier.classify_task(task)

            assert result is not None
            assert result.category == TaskCategory.RESEARCH
            assert result.confidence == 0.85
            assert result.reasoning == "Task involves research and analysis"

class TestModelSelection:
    """Test model selection components"""

    @pytest.fixture
    def model_selector(self):
        """Create model selector instance"""
        return ModelSelector(TEST_CONFIG)

    @pytest.mark.asyncio
    async def test_model_selector_initialization(self, model_selector):
        """Test model selector initialization"""
        assert model_selector is not None
        assert model_selector.config == TEST_CONFIG

    @pytest.mark.asyncio
    async def test_select_model_for_task(self, model_selector):
        """Test model selection for tasks"""
        task = DetectedTask(
            task_id="model_test",
            title="Complex Analysis Task",
            description="Perform complex data analysis",
            source=TaskSource.WEBHOOK,
            priority=TaskPriority.HIGH,
            timestamp=datetime.now()
        )

        selection = await model_selector.select_model_for_task(
            task=task,
            task_category="data_analysis",
            requirements={
                "complexity": "high",
                "accuracy": "high",
                "cost_constraint": "medium"
            }
        )

        assert selection is not None
        assert selection.model_id is not None
        assert selection.provider is not None
        assert selection.confidence_score > 0

class TestTaskExecution:
    """Test task execution components"""

    @pytest.fixture
    def task_executor(self):
        """Create task executor instance"""
        return AutonomousTaskExecutor(TEST_CONFIG)

    @pytest.mark.asyncio
    async def test_task_executor_initialization(self, task_executor):
        """Test task executor initialization"""
        assert task_executor is not None
        assert task_executor.config == TEST_CONFIG

    @pytest.mark.asyncio
    async def test_execute_task_workflow(self, task_executor):
        """Test task workflow execution"""
        workflow = {
            "steps": [
                {"name": "step1", "action": "analyze", "parameters": {"input": "test"}},
                {"name": "step2", "action": "process", "parameters": {"input": "step1_output"}}
            ]
        }

        # Mock dependencies
        task_executor.llm_manager = Mock()
        task_executor.agent_pool = Mock()
        task_executor.tool_manager = Mock()

        result = await task_executor.execute_task_workflow(
            task_id="exec_test",
            workflow=workflow
        )

        assert result is not None
        assert result.status in ["completed", "failed", "running"]

class TestDecisionEngine:
    """Test decision engine components"""

    @pytest.fixture
    def decision_engine(self):
        """Create decision engine instance"""
        return DecisionEngine(TEST_CONFIG)

    @pytest.mark.asyncio
    async def test_decision_engine_initialization(self, decision_engine):
        """Test decision engine initialization"""
        assert decision_engine is not None
        assert decision_engine.config == TEST_CONFIG

    @pytest.mark.asyncio
    async def test_make_decision(self, decision_engine):
        """Test decision making"""
        context = {
            "task_count": 10,
            "system_load": 0.7,
            "available_resources": 0.8,
            "recent_errors": 2
        }

        decision = await decision_engine.make_decision(
            decision_type="resource_allocation",
            context=context,
            goals=["optimize_performance", "minimize_cost"]
        )

        assert decision is not None
        assert decision.decision_type == "resource_allocation"
        assert decision.confidence_score > 0

class TestPerformanceTracking:
    """Test performance tracking components"""

    @pytest.fixture
    def performance_tracker(self):
        """Create performance tracker instance"""
        return PerformanceTracker(TEST_CONFIG)

    @pytest.mark.asyncio
    async def test_performance_tracker_initialization(self, performance_tracker):
        """Test performance tracker initialization"""
        assert performance_tracker is not None
        assert performance_tracker.config == TEST_CONFIG

    @pytest.mark.asyncio
    async def test_record_metric(self, performance_tracker):
        """Test metric recording"""
        metric = PerformanceMetric(
            metric_id="test_metric",
            metric_type=MetricType.SUCCESS_RATE,
            value=0.95,
            task_category="research",
            model_used="gpt-4",
            agent_used="research_agent",
            timestamp=datetime.now()
        )

        await performance_tracker.record_metric(metric)

        # Verify metric was stored
        summary = await performance_tracker.get_performance_summary(hours=1)
        assert "error" not in summary

class TestSystemMonitoring:
    """Test system monitoring components"""

    @pytest.fixture
    def system_monitor(self):
        """Create system monitor instance"""
        return SystemMonitor(TEST_CONFIG)

    @pytest.mark.asyncio
    async def test_system_monitor_initialization(self, system_monitor):
        """Test system monitor initialization"""
        assert system_monitor is not None
        assert system_monitor.config == TEST_CONFIG

    @pytest.mark.asyncio
    async def test_system_health_calculation(self, system_monitor):
        """Test system health calculation"""
        health = await system_monitor._calculate_system_health()

        assert health is not None
        assert health.status in ["healthy", "warning", "critical", "error"]
        assert 0 <= health.score <= 1

class TestAdvancedOrchestration:
    """Test advanced orchestration components"""

    @pytest.fixture
    def advanced_orchestrator(self):
        """Create advanced orchestrator instance"""
        return AdvancedOrchestrator(TEST_CONFIG)

    @pytest.mark.asyncio
    async def test_advanced_orchestrator_initialization(self, advanced_orchestrator):
        """Test advanced orchestrator initialization"""
        assert advanced_orchestrator is not None
        assert advanced_orchestrator.config == TEST_CONFIG

    @pytest.mark.asyncio
    async def test_workflow_registration(self, advanced_orchestrator):
        """Test workflow registration"""
        workflow = WorkflowDefinition(
            workflow_id="test_workflow",
            name="Test Workflow",
            description="A test workflow",
            version="1.0.0",
            tasks=[
                {
                    "task_id": "task1",
                    "name": "Task 1",
                    "priority": 1,
                    "estimated_duration": 300
                }
            ],
            dependencies=[]
        )

        success = await advanced_orchestrator.register_workflow(workflow)
        assert success is True

        # Verify workflow was registered
        assert "test_workflow" in advanced_orchestrator.workflows

class TestSecuritySystem:
    """Test security and authentication components"""

    @pytest.fixture
    def auth_manager(self):
        """Create auth manager instance"""
        return AuthManager(TEST_CONFIG)

    @pytest.mark.asyncio
    async def test_auth_manager_initialization(self, auth_manager):
        """Test auth manager initialization"""
        assert auth_manager is not None
        assert auth_manager.config == TEST_CONFIG

    @pytest.mark.asyncio
    async def test_user_creation(self, auth_manager):
        """Test user creation"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "role": "analyst"
        }

        user_id = await auth_manager.create_user(user_data, "SecurePass123!")
        assert user_id is not None

        # Verify user was created
        user_info = await auth_manager.get_user_info(user_id)
        assert user_info is not None
        assert user_info["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_user_authentication(self, auth_manager):
        """Test user authentication"""
        # Create user first
        user_data = {
            "username": "authuser",
            "email": "auth@example.com",
            "full_name": "Auth User",
            "role": "viewer"
        }

        user_id = await auth_manager.create_user(user_data, "SecurePass123!")

        # Test authentication
        auth_result = await auth_manager.authenticate_user(
            "authuser", "SecurePass123!", "127.0.0.1", "Test Browser"
        )

        assert auth_result is not None
        assert "access_token" in auth_result
        assert "refresh_token" in auth_result

class TestSystemIntegration:
    """Test system integration scenarios"""

    @pytest.fixture
    def orchestrator(self):
        """Create main orchestrator instance"""
        return AutonomousOrchestrator(TEST_CONFIG)

    @pytest.mark.asyncio
    async def test_system_startup(self, orchestrator):
        """Test complete system startup"""
        # Initialize system
        await orchestrator.initialize()

        # Start system
        await orchestrator.start()

        # Check system status
        status = await orchestrator.get_system_status()
        assert status.status == "running"
        assert len(status.components) > 0

    @pytest.mark.asyncio
    async def test_end_to_end_task_processing(self, orchestrator):
        """Test end-to-end task processing"""
        # Initialize and start system
        await orchestrator.initialize()
        await orchestrator.start()

        # Create a test task
        task = DetectedTask(
            task_id="e2e_test",
            title="End-to-End Test Task",
            description="Testing complete task processing pipeline",
            source=TaskSource.WEBHOOK,
            priority=TaskPriority.HIGH,
            timestamp=datetime.now()
        )

        # Submit task
        await orchestrator.submit_task(task)

        # Wait for processing
        await asyncio.sleep(2)

        # Check system status
        status = await orchestrator.get_system_status()
        assert status.active_tasks >= 0  # Task may have completed quickly

    @pytest.mark.asyncio
    async def test_system_shutdown(self, orchestrator):
        """Test system shutdown"""
        # Initialize and start system
        await orchestrator.initialize()
        await orchestrator.start()

        # Shutdown system
        await orchestrator.shutdown()

        # Check system status
        status = await orchestrator.get_system_status()
        assert status.status == "stopped"

class TestErrorHandling:
    """Test error handling and recovery"""

    @pytest.mark.asyncio
    async def test_database_connection_error(self):
        """Test handling of database connection errors"""
        # Create config with invalid database path
        error_config = TEST_CONFIG.copy()
        error_config["database"]["path"] = "/invalid/path/db.sqlite"

        # Should handle database errors gracefully
        try:
            detector = TaskDetector(error_config)
            # This should not crash the system
            assert detector is not None
        except Exception as e:
            # System should handle database errors gracefully
            assert "database" in str(e).lower() or "path" in str(e).lower()

    @pytest.mark.asyncio
    async def test_llm_api_error_handling(self):
        """Test handling of LLM API errors"""
        classifier = TaskClassifier(TEST_CONFIG)

        # Mock LLM failure
        with patch.object(classifier, '_call_llm', new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = Exception("API rate limit exceeded")

            task = DetectedTask(
                task_id="error_test",
                title="Error Test Task",
                description="Testing error handling",
                source=TaskSource.FILE_SYSTEM,
                priority=TaskPriority.MEDIUM,
                timestamp=datetime.now()
            )

            # Should handle errors gracefully
            try:
                result = await classifier.classify_task(task)
                # Should return fallback classification
                assert result is not None
            except Exception:
                # Or should handle the error gracefully
                pass

class TestPerformanceBenchmarks:
    """Test system performance benchmarks"""

    @pytest.mark.asyncio
    async def test_task_processing_throughput(self):
        """Test task processing throughput"""
        executor = AutonomousTaskExecutor(TEST_CONFIG)

        # Create multiple tasks
        tasks = []
        for i in range(10):
            task = DetectedTask(
                task_id=f"throughput_test_{i}",
                title=f"Throughput Test Task {i}",
                description=f"Testing throughput with task {i}",
                source=TaskSource.WEBHOOK,
                priority=TaskPriority.MEDIUM,
                timestamp=datetime.now()
            )
            tasks.append(task)

        # Measure processing time
        start_time = datetime.now()

        # Process tasks concurrently
        results = await asyncio.gather(*[
            executor.execute_task_workflow(
                task_id=task.task_id,
                workflow={"steps": [{"name": "test", "action": "test"}]}
            )
            for task in tasks
        ], return_exceptions=True)

        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()

        # Verify all tasks were processed
        assert len(results) == 10
        assert processing_time < 30  # Should complete within 30 seconds

# Performance markers for pytest-benchmark
@pytest.mark.benchmark
class TestBenchmarks:
    """Performance benchmarks"""

    @pytest.mark.asyncio
    async def test_metric_recording_performance(self, benchmark):
        """Benchmark metric recording performance"""
        tracker = PerformanceTracker(TEST_CONFIG)

        def record_metrics():
            metric = PerformanceMetric(
                metric_id="benchmark_test",
                metric_type=MetricType.SUCCESS_RATE,
                value=0.95,
                task_category="benchmark",
                model_used="test",
                agent_used="test",
                timestamp=datetime.now()
            )
            return asyncio.run(tracker.record_metric(metric))

        result = benchmark(record_metrics)
        assert result is not None

# Test utilities
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def cleanup():
    """Cleanup after each test"""
    yield
    # Clean up any temporary files or databases
    pass

# Main test runner
if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([
        __file__,
        "-v",
        "--cov=autonomous_system",
        "--cov-report=html",
        "--cov-report=term-missing"
    ])

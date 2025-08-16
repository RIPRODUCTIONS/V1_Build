#!/usr/bin/env python3
"""
AI Framework System Test Script

This script tests all components of the AI agent system:
1. Agent initialization
2. Dashboard functionality
3. Agent communication
4. Task execution
5. Emergency protocols

Usage:
    python test_system.py
"""

import asyncio
import logging
import sys
from pathlib import Path

from agents.base import Task, TaskPriority

from core.agent_orchestrator import AgentOrchestrator
from core.master_dashboard import MasterDashboard

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemTester:
    """Test class for the AI Framework system."""

    # Constants to replace magic numbers
    MIN_AGENTS_FOR_COMMUNICATION = 2
    TEST_TASK_ID = "test_collaboration"
    TEST_TASK_TYPE = "test"

    def __init__(self):
        self.dashboard = None
        self.orchestrator = None
        self.test_results = {}

    async def run_all_tests(self):
        """Run all system tests."""
        logger.info("🧪 Starting AI Framework System Tests...")

        try:
            # Test 1: System Initialization
            await self.test_system_initialization()

            # Test 2: Agent Registration
            await self.test_agent_registration()

            # Test 3: Dashboard Functionality
            await self.test_dashboard_functionality()

            # Test 4: Agent Communication
            await self.test_agent_communication()

            # Test 5: Task Execution
            await self.test_task_execution()

            # Test 6: Emergency Protocols
            await self.test_emergency_protocols()

            # Test 7: System Health
            await self.test_system_health()

            # Print test results
            self.print_test_results()

            return True

        except Exception as e:
            logger.error(f"❌ Test suite failed: {str(e)}")
            return False

    async def test_system_initialization(self):
        """Test system initialization."""
        logger.info("🔧 Testing system initialization...")

        try:
            # Initialize orchestrator
            self.orchestrator = AgentOrchestrator()

            # Initialize dashboard
            self.dashboard = MasterDashboard(self.orchestrator)

            # Check if agents were registered
            if len(self.dashboard.agent_registry) > 0:
                self.test_results['initialization'] = 'PASS'
                logger.info(f"✅ System initialized with {len(self.dashboard.agent_registry)} agents")
            else:
                self.test_results['initialization'] = 'FAIL'
                logger.error("❌ No agents registered")

        except Exception as e:
            self.test_results['initialization'] = 'FAIL'
            logger.error(f"❌ Initialization test failed: {str(e)}")

    async def test_agent_registration(self):
        """Test agent registration."""
        logger.info("📝 Testing agent registration...")

        try:
            if not self.dashboard:
                self.test_results['agent_registration'] = 'FAIL'
                return

            # Check if all expected departments have agents
            expected_departments = [
                'executive', 'finance', 'sales', 'marketing',
                'operations', 'hr', 'legal', 'it_security',
                'creative', 'personal'
            ]

            registered_departments = set()
            for agent in self.dashboard.agent_registry.values():
                registered_departments.add(agent.config.department.value)

            missing_departments = set(expected_departments) - registered_departments

            if not missing_departments:
                self.test_results['agent_registration'] = 'PASS'
                logger.info(f"✅ All departments registered: {registered_departments}")
            else:
                self.test_results['agent_registration'] = 'FAIL'
                logger.warning(f"⚠️ Missing departments: {missing_departments}")

        except Exception as e:
            self.test_results['agent_registration'] = 'FAIL'
            logger.error(f"❌ Agent registration test failed: {str(e)}")

    async def test_dashboard_functionality(self):
        """Test dashboard functionality."""
        logger.info("🎛️ Testing dashboard functionality...")

        try:
            if not self.dashboard:
                self.test_results['dashboard_functionality'] = 'FAIL'
                return

            # Test dashboard overview
            overview = await self.dashboard.get_dashboard_overview()

            if overview and 'overview' in overview:
                self.test_results['dashboard_functionality'] = 'PASS'
                logger.info("✅ Dashboard overview working")
            else:
                self.test_results['dashboard_functionality'] = 'FAIL'
                logger.error("❌ Dashboard overview failed")

        except Exception as e:
            self.test_results['dashboard_functionality'] = 'FAIL'
            logger.error(f"❌ Dashboard functionality test failed: {str(e)}")

    async def test_agent_communication(self):
        """Test agent communication."""
        logger.info("💬 Testing agent communication...")

        try:
            if not self.dashboard:
                self.test_results['agent_communication'] = 'FAIL'
                return

            # Find two agents to test communication
            agents = list(self.dashboard.agent_registry.values())
            if len(agents) < self.MIN_AGENTS_FOR_COMMUNICATION:
                self.test_results['agent_communication'] = 'FAIL'
                logger.error(f"❌ Not enough agents for communication test (need {self.MIN_AGENTS_FOR_COMMUNICATION})")
                return

            agent1 = agents[0]
            agent2 = agents[1]

            # Create a test task for collaboration
            test_task = Task(
                task_id=self.TEST_TASK_ID,
                task_type=self.TEST_TASK_TYPE,
                description="Test collaboration",
                priority=TaskPriority.NORMAL,
                requirements={
                    "task_type": self.TEST_TASK_TYPE,
                    "complexity": "simple"
                },
                metadata={}
            )

            # Execute the task
            result = await agent1.collaborate_with_agent(
                agent2.agent_id,
                test_task
            )

            if result and 'error' not in result:
                self.test_results['agent_communication'] = 'PASS'
                logger.info("✅ Agent communication working")
            else:
                self.test_results['agent_communication'] = 'FAIL'
                logger.warning("⚠️ Agent communication test had issues")

        except Exception as e:
            self.test_results['agent_communication'] = 'FAIL'
            logger.error(f"❌ Agent communication test failed: {str(e)}")

    async def test_task_execution(self):
        """Test task execution."""
        logger.info("⚡ Testing task execution...")

        try:
            if not self.dashboard:
                self.test_results['task_execution'] = 'FAIL'
                return

            # Find an agent to test task execution
            agents = list(self.dashboard.agent_registry.values())
            if not agents:
                self.test_results['task_execution'] = 'FAIL'
                logger.error("❌ No agents available for task execution test")
                return

            test_agent = agents[0]

            # Create a test task
            test_task = Task(
                task_id="test_task",
                task_type="strategic_planning",  # Use a valid task type for CEO
                description="Test task execution",
                priority=TaskPriority.NORMAL,
                requirements={
                    "task_type": "strategic_planning",
                    "complexity": "simple"
                },
                metadata={"test": True}
            )

            # Assign the task to the agent first
            await test_agent.assign_task(test_task)

            # Execute the task
            result = await test_agent.execute_task(test_task)

            if result and 'error' not in result:
                self.test_results['task_execution'] = 'PASS'
                logger.info("✅ Task execution working")
            else:
                self.test_results['task_execution'] = 'FAIL'
                logger.error("❌ Task execution failed")

        except Exception as e:
            self.test_results['task_execution'] = 'FAIL'
            logger.error(f"❌ Task execution test failed: {str(e)}")

    async def test_emergency_protocols(self):
        """Test emergency protocols."""
        logger.info("🚨 Testing emergency protocols...")

        try:
            if not self.dashboard:
                self.test_results['emergency_protocols'] = 'FAIL'
                return

            # Test system overload protocol
            result = await self.dashboard.execute_emergency_protocol('system_overload')

            if result and ('status' in result or 'protocol_executed' in result):
                self.test_results['emergency_protocols'] = 'PASS'
                logger.info("✅ Emergency protocols working")
            else:
                self.test_results['emergency_protocols'] = 'FAIL'
                logger.error("❌ Emergency protocols failed")

        except Exception as e:
            self.test_results['emergency_protocols'] = 'FAIL'
            logger.error(f"❌ Emergency protocols test failed: {str(e)}")

    async def test_system_health(self):
        """Test system health."""
        logger.info("🏥 Testing system health...")

        try:
            if not self.dashboard:
                self.test_results['system_health'] = 'FAIL'
                return

            # Get system health
            overview = await self.dashboard.get_dashboard_overview()

            if overview and overview.get('system_health') in ['excellent', 'good']:
                self.test_results['system_health'] = 'PASS'
                logger.info("✅ System health check passed")
            else:
                self.test_results['system_health'] = 'FAIL'
                logger.warning("⚠️ System health check failed")

        except Exception as e:
            self.test_results['system_health'] = 'FAIL'
            logger.error(f"❌ System health test failed: {str(e)}")

    def print_test_results(self):
        """Print test results summary."""
        print("\n" + "="*80)
        print("🧪 AI FRAMEWORK SYSTEM TEST RESULTS")
        print("="*80)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result == 'PASS')
        failed_tests = total_tests - passed_tests

        for test_name, result in self.test_results.items():
            status_icon = "✅" if result == 'PASS' else "❌"
            print(f"{status_icon} {test_name.replace('_', ' ').title()}: {result}")

        print("="*80)
        print(f"📊 Test Summary: {passed_tests}/{total_tests} tests passed")

        if failed_tests == 0:
            print("🎉 All tests passed! The AI Framework is working correctly.")
        else:
            print(f"⚠️ {failed_tests} test(s) failed. Please check the logs above.")

        print("="*80)

    async def cleanup(self):
        """Cleanup test resources."""
        if self.dashboard:
            await self.dashboard.shutdown_all_agents()

async def main():
    """Main test function."""
    tester = SystemTester()

    try:
        success = await tester.run_all_tests()
        return success
    finally:
        await tester.cleanup()

if __name__ == "__main__":
    # Check if we're in the right directory
    if not Path("core").exists() or not Path("agents").exists():
        print("❌ Error: Please run this script from the ai_framework directory")
        print("   Current directory:", Path.cwd())
        print("   Expected structure: ai_framework/core/, ai_framework/agents/")
        sys.exit(1)

    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)


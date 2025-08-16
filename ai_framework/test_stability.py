#!/usr/bin/env python3
"""
AI Framework Stability Test

Comprehensive testing of all system components to ensure stability.
"""

import asyncio
import logging
import sys

from config.agent_configs import get_all_agent_configs
from server import AIFrameworkServer
from workloads.financial_workloads import seed_financial_workloads
from workloads.sales_workloads import seed_sales_workloads

# Import all modules at top level to avoid PLC0415 errors
from core.agent_orchestrator import AgentOrchestrator
from core.master_dashboard import MasterDashboard

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants to replace magic numbers
EXPECTED_AGENT_COUNT = 52
TEST_PORT = 8002

async def test_agent_initialization():
    """Test that all agents can be initialized without errors."""
    logger.info("🧪 Testing agent initialization...")

    try:
        # Initialize orchestrator
        orchestrator = AgentOrchestrator()
        logger.info("✅ Agent Orchestrator initialized")

        # Initialize dashboard
        dashboard = MasterDashboard(orchestrator)
        logger.info("✅ Master Dashboard initialized")

        # Check agent count
        total_agents = len(dashboard.agent_registry)
        logger.info(f"✅ Total agents loaded: {total_agents}")

        if total_agents != EXPECTED_AGENT_COUNT:
            logger.warning(f"⚠️ Expected {EXPECTED_AGENT_COUNT} agents, got {total_agents}")

        return True

    except Exception as e:
        logger.error(f"❌ Agent initialization failed: {str(e)}")
        return False

async def test_agent_configurations():
    """Test that all agent configurations are valid."""
    logger.info("🧪 Testing agent configurations...")

    try:
        configs = get_all_agent_configs()
        logger.info(f"✅ Loaded {len(configs)} agent configurations")

        # Validate each config
        for name, config in configs.items():
            if not config.name or not config.capabilities:
                logger.error(f"❌ Invalid config for {name}")
                return False

        logger.info("✅ All agent configurations are valid")
        return True

    except Exception as e:
        logger.error(f"❌ Configuration validation failed: {str(e)}")
        return False

async def test_dashboard_functionality():
    """Test dashboard functionality."""
    logger.info("🧪 Testing dashboard functionality...")

    try:
        orchestrator = AgentOrchestrator()
        dashboard = MasterDashboard(orchestrator)

        # Test dashboard overview
        await dashboard.get_dashboard_overview()
        logger.info("✅ Dashboard overview generated")

        # Test department status
        await dashboard.get_department_status("executive")
        logger.info("✅ Department status retrieved")

        # Test agent status
        dashboard.get_agent_status(list(dashboard.agent_registry.keys())[0])
        logger.info("✅ Agent status retrieved")

        return True

    except Exception as e:
        logger.error(f"❌ Dashboard functionality failed: {str(e)}")
        return False

async def test_workload_generation():
    """Test workload generation."""
    logger.info("🧪 Testing workload generation...")

    try:
        # Test financial workloads
        financial_tasks = seed_financial_workloads()
        logger.info(f"✅ Generated {len(financial_tasks)} financial tasks")

        # Test sales workloads
        sales_tasks = seed_sales_workloads()
        logger.info(f"✅ Generated {len(sales_tasks)} sales tasks")

        return True

    except Exception as e:
        logger.error(f"❌ Workload generation failed: {str(e)}")
        return False

async def test_api_endpoints():
    """Test API endpoint creation."""
    logger.info("🧪 Testing API endpoint creation...")

    try:
        server = AIFrameworkServer(host="127.0.0.1", port=TEST_PORT, debug=False)

        # Test app creation
        app = server._create_fastapi_app()
        logger.info("✅ FastAPI app created")

        # Check routes
        routes = [route.path for route in app.routes]
        expected_routes = ["/", "/health", "/api/dashboard/overview", "/api/dashboard/departments"]

        for route in expected_routes:
            if route not in routes:
                logger.error(f"❌ Missing route: {route}")
                return False

        logger.info("✅ All expected API routes present")
        return True

    except Exception as e:
        logger.error(f"❌ API endpoint test failed: {str(e)}")
        return False

async def run_all_tests():
    """Run all stability tests."""
    logger.info("🚀 Starting AI Framework Stability Tests...")

    tests = [
        ("Agent Initialization", test_agent_initialization),
        ("Agent Configurations", test_agent_configurations),
        ("Dashboard Functionality", test_dashboard_functionality),
        ("Workload Generation", test_workload_generation),
        ("API Endpoints", test_api_endpoints)
    ]

    results = []

    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")

        try:
            result = await test_func()
            results.append((test_name, result))

            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")

        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {str(e)}")
            results.append((test_name, False))

    # Summary
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")

    logger.info(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All tests passed! System is stable.")
        return True
    else:
        logger.error("💥 Some tests failed. System needs attention.")
        return False

def main():
    """Main entry point."""
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

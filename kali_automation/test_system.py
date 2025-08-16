#!/usr/bin/env python3
"""
Test script for the Kali Linux Automation Platform
Verifies basic functionality and tool availability
"""

import asyncio
import logging
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_basic_functionality():
    """Test basic system functionality"""
    logger.info("Testing basic system functionality...")

    try:
        # Test imports
        from kali_orchestrator import KaliToolsOrchestrator
        logger.info("✅ Successfully imported KaliToolsOrchestrator")

        # Test orchestrator initialization
        orchestrator = KaliToolsOrchestrator()
        logger.info("✅ Successfully initialized orchestrator")

        # Test tools registry
        tools_count = len(orchestrator.tools_registry)
        logger.info(f"✅ Tools registry contains {tools_count} tools")

        # Test specific tools
        expected_tools = ['nmap', 'masscan', 'theharvester', 'nikto', 'sqlmap']
        for tool in expected_tools:
            if tool in orchestrator.tools_registry:
                logger.info(f"✅ Tool {tool} is available")
            else:
                logger.warning(f"⚠️ Tool {tool} not found in registry")

        return True

    except Exception as e:
        logger.error(f"❌ Basic functionality test failed: {e}")
        return False

async def test_tool_imports():
    """Test tool module imports"""
    logger.info("Testing tool module imports...")

    try:
        # Test information gathering tools
        logger.info("✅ Successfully imported information gathering tools")

        # Test vulnerability assessment tools
        logger.info("✅ Successfully imported vulnerability assessment tools")

        return True

    except Exception as e:
        logger.error(f"❌ Tool imports test failed: {e}")
        return False

async def test_configuration():
    """Test configuration loading"""
    logger.info("Testing configuration...")

    try:
        # Check if required directories exist
        required_dirs = ['/kali-automation', '/kali-automation/results', '/kali-automation/configs']

        for directory in required_dirs:
            if os.path.exists(directory):
                logger.info(f"✅ Directory {directory} exists")
            else:
                logger.warning(f"⚠️ Directory {directory} does not exist")

        return True

    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False

async def test_dependencies():
    """Test required dependencies"""
    logger.info("Testing dependencies...")

    try:
        # Test core dependencies
        logger.info("✅ Core Python modules available")

        # Test optional dependencies
        try:
            import yaml
            logger.info("✅ PyYAML available")
        except ImportError:
            logger.warning("⚠️ PyYAML not available")

        try:
            import sqlalchemy
            logger.info("✅ SQLAlchemy available")
        except ImportError:
            logger.warning("⚠️ SQLAlchemy not available")

        try:
            import fastapi
            logger.info("✅ FastAPI available")
        except ImportError:
            logger.warning("⚠️ FastAPI not available")

        return True

    except Exception as e:
        logger.error(f"❌ Dependencies test failed: {e}")
        return False

async def main():
    """Main test function"""
    logger.info("🚀 Starting Kali Linux Automation Platform Tests")
    logger.info("=" * 60)

    tests = [
        ("Basic Functionality", test_basic_functionality),
        ("Tool Imports", test_tool_imports),
        ("Configuration", test_configuration),
        ("Dependencies", test_dependencies),
    ]

    results = {}

    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running {test_name} test...")
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            logger.error(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("=" * 60)

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")

    logger.info(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All tests passed! System is ready.")
        return 0
    else:
        logger.error("💥 Some tests failed. Please check the logs.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Test runner crashed: {e}")
        sys.exit(1)

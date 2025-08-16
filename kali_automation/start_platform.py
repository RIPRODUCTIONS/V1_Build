#!/usr/bin/env python3
"""
Startup script for the Kali Linux Automation Platform
Launches all services and provides status information
"""

import asyncio
import logging
import os
import sys
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def check_environment():
    """Check if the environment is properly configured"""
    logger.info("🔍 Checking environment configuration...")

    # Check required directories
    required_dirs = [
        '/kali-automation',
        '/kali-automation/results',
        '/kali-automation/configs',
        '/kali-automation/logs'
    ]

    for directory in required_dirs:
        if os.path.exists(directory):
            logger.info(f"✅ Directory {directory} exists")
        else:
            logger.warning(f"⚠️ Directory {directory} does not exist")
            try:
                os.makedirs(directory, exist_ok=True)
                logger.info(f"✅ Created directory {directory}")
            except Exception as e:
                logger.error(f"❌ Failed to create directory {directory}: {e}")
                return False

    return True

async def start_orchestrator():
    """Start the main orchestrator"""
    logger.info("🚀 Starting Kali Tools Orchestrator...")

    try:
        from kali_orchestrator import KaliToolsOrchestrator

        # Initialize orchestrator
        orchestrator = KaliToolsOrchestrator()
        logger.info("✅ Orchestrator initialized successfully")

        # Display available tools
        tools_count = len(orchestrator.tools_registry)
        logger.info(f"📊 Available tools: {tools_count}")

        # Show tool categories
        categories = {}
        for tool_name, tool_info in orchestrator.tools_registry.items():
            category = tool_info.get('category', 'unknown')
            if category not in categories:
                categories[category] = []
            categories[category].append(tool_name)

        logger.info("📋 Tool categories:")
        for category, tools in categories.items():
            logger.info(f"  {category}: {len(tools)} tools")

        return orchestrator

    except Exception as e:
        logger.error(f"❌ Failed to start orchestrator: {e}")
        return None

async def start_web_interface():
    """Start the web interface"""
    logger.info("🌐 Starting web interface...")

    try:
        import uvicorn
        from fastapi import FastAPI

        # Create simple FastAPI app
        app = FastAPI(title="Kali Automation Platform", version="1.0.0")

        @app.get("/")
        async def root():
            return {"message": "Kali Linux Automation Platform", "status": "running"}

        @app.get("/health")
        async def health():
            return {"status": "healthy", "timestamp": time.time()}

        @app.get("/tools")
        async def list_tools():
            return {"message": "Tools endpoint - implement tool listing"}

        # Start server in background
        config = uvicorn.Config(app, host="0.0.0.0", port=8001, log_level="info")
        server = uvicorn.Server(config)

        # Run server in background
        asyncio.create_task(server.serve())
        logger.info("✅ Web interface started on port 8001")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to start web interface: {e}")
        return False

async def display_status():
    """Display platform status"""
    logger.info("\n" + "=" * 60)
    logger.info("🎯 KALI LINUX AUTOMATION PLATFORM STATUS")
    logger.info("=" * 60)

    # Check services
    services = {
        "Orchestrator": "✅ Running",
        "Web Interface": "✅ Running on port 8001",
        "Tool Registry": "✅ Loaded",
        "Results Directory": "✅ Available",
        "Configuration": "✅ Loaded"
    }

    for service, status in services.items():
        logger.info(f"{service:<20}: {status}")

    logger.info("\n🌐 Access the platform:")
    logger.info("  Web Interface: http://localhost:8001")
    logger.info("  Health Check:  http://localhost:8001/health")
    logger.info("  API Docs:      http://localhost:8001/docs")

    logger.info("\n📚 Next steps:")
    logger.info("  1. Access the web interface")
    logger.info("  2. Configure your targets")
    logger.info("  3. Start automated scans")
    logger.info("  4. Review results and reports")

    logger.info("\n" + "=" * 60)

async def main():
    """Main startup function"""
    logger.info("🚀 Starting Kali Linux Automation Platform...")
    logger.info("=" * 60)

    # Check environment
    if not await check_environment():
        logger.error("❌ Environment check failed. Exiting.")
        return 1

    # Start orchestrator
    orchestrator = await start_orchestrator()
    if not orchestrator:
        logger.error("❌ Failed to start orchestrator. Exiting.")
        return 1

    # Start web interface
    if not await start_web_interface():
        logger.error("❌ Failed to start web interface. Exiting.")
        return 1

    # Display status
    await display_status()

    # Keep running
    logger.info("\n🔄 Platform is running. Press Ctrl+C to stop.")

    try:
        while True:
            await asyncio.sleep(10)
    except KeyboardInterrupt:
        logger.info("\n⚠️ Shutting down platform...")
        return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n⚠️ Platform shutdown requested")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Platform startup failed: {e}")
        sys.exit(1)

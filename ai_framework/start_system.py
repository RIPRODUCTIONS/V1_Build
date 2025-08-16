#!/usr/bin/env python3
"""
AI Framework Startup Script

This script initializes and starts the complete AI agent system:
1. Initializes all agents
2. Starts the FastAPI backend
3. Serves the frontend dashboard
4. Provides system monitoring

Usage:
    python start_system.py [--port PORT] [--host HOST] [--debug]
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

import uvicorn
from agents.base import Task, TaskPriority
from api.main import app
from config.agent_configs import validate_agent_configs
from workloads import (
    seed_creative_workloads,
    seed_financial_workloads,
    seed_hr_workloads,
    seed_it_workloads,
    seed_legal_workloads,
    seed_marketing_workloads,
    seed_operations_workloads,
    seed_personal_workloads,
    seed_sales_workloads,
)

from core.agent_orchestrator import AgentOrchestrator
from core.master_dashboard import MasterDashboard

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ai_framework.log')
    ]
)

logger = logging.getLogger(__name__)

class AIFrameworkSystem:
    """Main system class that manages the AI Framework."""

    # Constants to replace magic numbers
    LOW_EFFICIENCY_THRESHOLD = 50.0  # percent
    SYSTEM_INFO_WIDTH = 80

    def __init__(self, host: str = "0.0.0.0", port: int = 8001, debug: bool = False):
        self.host = host
        self.port = port
        self.debug = debug
        self.dashboard = None
        self.orchestrator = None

    async def initialize_system(self):
        """Initialize the AI Framework system with proper validation."""
        logger.info("🚀 Initializing AI Framework System...")

        try:
            # Step 1: Validate configurations
            logger.info("🔍 Validating system configurations...")
            if not validate_agent_configs():
                raise Exception("Agent configuration validation failed")
            logger.info("✅ Configuration validation passed")

            # Step 2: Initialize orchestrator
            logger.info("📡 Initializing Agent Orchestrator...")
            self.orchestrator = AgentOrchestrator()  # Now uses proper defaults
            logger.info("✅ Agent Orchestrator initialized")

            # Step 3: Initialize master dashboard
            logger.info("🎛️ Initializing Master Dashboard...")
            self.dashboard = MasterDashboard(self.orchestrator)
            logger.info("✅ Master Dashboard initialized")

            # Step 4: Run system health check
            logger.info("🏥 Running initial system health check...")
            health_ok = await self.run_system_health_check()
            if not health_ok:
                raise Exception("Initial system health check failed")

            # Step 4.1: Seed live workloads
            await self._seed_live_workloads()

            # Step 4.2: Run a sample cross-department finance workflow
            await self._run_finance_workflow()

            # Step 5: Get system overview
            overview = await self.dashboard.get_dashboard_overview()

            logger.info("✅ AI Framework initialized successfully!")
            logger.info(f"📊 Total Agents: {overview['overview']['total_agents']}")
            logger.info(f"🔄 Active Agents: {overview['overview']['active_agents']}")
            logger.info(f"🏢 Departments: {len(overview['departments'])}")

            # Handle overall_efficiency which might be a string or float
            efficiency = overview['overview']['overall_efficiency']
            if isinstance(efficiency, str):
                logger.info(f"📈 Overall Efficiency: {efficiency}")
            else:
                logger.info(f"📈 Overall Efficiency: {efficiency:.1f}%")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize AI Framework: {str(e)}")
            return False

    async def _seed_live_workloads(self):
        """Seed initial workloads across departments to exercise agents."""
        try:
            if not self.dashboard:
                return
            seeds = []
            seeds += seed_financial_workloads()
            seeds += seed_sales_workloads()
            seeds += seed_marketing_workloads()
            seeds += seed_operations_workloads()
            seeds += seed_hr_workloads()
            seeds += seed_legal_workloads()
            seeds += seed_it_workloads()
            seeds += seed_creative_workloads()
            seeds += seed_personal_workloads()

            # Naive fan-out: assign to any agent that supports the task type
            for task in seeds:
                for agent in self.dashboard.agent_registry.values():
                    try:
                        capabilities = agent.get_capabilities()
                        if task.task_type in capabilities:
                            await agent.execute_task(task)
                            break
                    except Exception:
                        continue
            logger.info("📦 Seeded initial live workloads")
        except Exception as e:
            logger.warning(f"Seeding workloads failed: {e}")

    async def _run_finance_workflow(self):
        """Demonstrate CFO -> Accountant -> Auditor collaboration."""
        try:
            if not self.dashboard:
                return
            # Simple helpers to fetch first matching agent by name fragment
            def find_agent_by_label(label_substring: str):
                for agent_id, agent in self.dashboard.agent_registry.items():
                    if label_substring.lower().replace(" ", "_") in agent_id:
                        return agent
                return None

            accountant = find_agent_by_label("accountant")
            auditor = find_agent_by_label("auditor")

            # Run bookkeeping, then audit
            now_meta = {"trigger": "cross_dept_demo"}
            if accountant:
                t1 = Task(
                    task_id="wf_bookkeeping",
                    task_type="bookkeeping",
                    description="Workflow: process bookkeeping before audit",
                    priority=TaskPriority.NORMAL,
                    requirements={},
                    metadata=now_meta,
                )
                await accountant.execute_task(t1)

            if auditor:
                t2 = Task(
                    task_id="wf_compliance_audit",
                    task_type="compliance_audit",
                    description="Workflow: compliance audit after bookkeeping",
                    priority=TaskPriority.NORMAL,
                    requirements={},
                    metadata=now_meta,
                )
                await auditor.execute_task(t2)

            logger.info("🔗 Ran finance cross-department workflow (Accountant → Auditor)")
        except Exception as e:
            logger.warning(f"Finance workflow failed: {e}")

    async def run_system_health_check(self):
        """Run a comprehensive system health check."""
        logger.info("🏥 Running system health check...")

        try:
            if not self.dashboard:
                logger.error("❌ Dashboard not initialized")
                return False

            # Check dashboard status
            overview = await self.dashboard.get_dashboard_overview()

            # Check each department
            for dept_name, dept_data in overview['departments'].items():
                efficiency = dept_data.get('efficiency', 0)
                active_agents = dept_data.get('active_agents', 0)
                total_agents = dept_data.get('agent_count', 0)

                if efficiency < self.LOW_EFFICIENCY_THRESHOLD:
                    logger.warning(f"⚠️ Department {dept_name} has low efficiency: {efficiency:.1f}%")

                if active_agents < total_agents:
                    logger.warning(f"⚠️ Department {dept_name} has inactive agents: {active_agents}/{total_agents}")

            # Check for alerts
            alerts = overview.get('alerts', [])
            if alerts:
                logger.warning(f"⚠️ {len(alerts)} active alerts detected")
                for alert in alerts:
                    logger.warning(f"   - {alert['type']}: {alert['message']}")
            else:
                logger.info("✅ No active alerts")

            logger.info("✅ System health check completed")
            return True

        except Exception as e:
            logger.error(f"❌ Health check failed: {str(e)}")
            return False

    async def start_backend(self):
        """Start the FastAPI backend server."""
        logger.info(f"🌐 Starting FastAPI backend on {self.host}:{self.port}")

        config = uvicorn.Config(
            app=app,
            host=self.host,
            port=self.port,
            log_level="info" if not self.debug else "debug",
            reload=self.debug
        )

        server = uvicorn.Server(config)
        await server.serve()

    def print_system_info(self):
        """Print system information and usage instructions."""
        print("\n" + "="*self.SYSTEM_INFO_WIDTH)
        print("🤖 AI FRAMEWORK SYSTEM STARTED SUCCESSFULLY!")
        print("="*self.SYSTEM_INFO_WIDTH)
        print(f"🌐 Backend API: http://{self.host}:{self.port}")
        print(f"📊 Dashboard: http://{self.host}:{self.port}/frontend/")
        print(f"📚 API Docs: http://{self.host}:{self.port}/docs")
        print(f"🔌 WebSocket: ws://{self.host}:{self.port}/ws")
        print("="*self.SYSTEM_INFO_WIDTH)
        print("📋 Available Endpoints:")
        print("   • GET  /api/dashboard/overview     - System overview")
        print("   • GET  /api/dashboard/departments  - Department status")
        print("   • GET  /api/dashboard/agents       - All agent status")
        print("   • GET  /api/system/health          - System health")
        print("   • POST /api/agents/restart-all     - Restart all agents")
        print("   • POST /api/emergency/{protocol}   - Emergency protocols")
        print("="*self.SYSTEM_INFO_WIDTH)
        print("🎮 Control Commands:")
        print("   • Press Ctrl+C to shutdown the system")
        print("   • Use the web dashboard for real-time monitoring")
        print("   • Check logs in 'ai_framework.log'")
        print("="*self.SYSTEM_INFO_WIDTH)
        print("🚀 Your AI agents are now running autonomously!")
        print("="*self.SYSTEM_INFO_WIDTH + "\n")

    async def run(self):
        """Run the AI Framework system."""
        logger.info("🚀 Starting AI Framework System...")

        # Initialize the system
        success = await self.initialize_system()
        if not success:
            logger.error("❌ System initialization failed")
            return False

        # Print system information
        self.print_system_info()

        # Start the FastAPI backend
        logger.info(f"🌐 Starting FastAPI backend on {self.host}:{self.port}")
        config = uvicorn.Config(
            app=app,
            host=self.host,
            port=self.port,
            log_level="info" if not self.debug else "debug"
        )
        server = uvicorn.Server(config)
        await server.serve()

        return True

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="AI Framework Startup Script")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    # Create system instance
    system = AIFrameworkSystem(
        host=args.host,
        port=args.port,
        debug=args.debug
    )

    try:
        # Initialize the system
        if not await system.initialize_system():
            logger.error("❌ System initialization failed. Exiting.")
            sys.exit(1)

        # Print system information
        system.print_system_info()

        # Start the backend server
        await system.start_backend()

    except KeyboardInterrupt:
        logger.info("\n🛑 Shutdown requested by user...")

        if system.dashboard:
            logger.info("🔄 Shutting down all agents...")
            await system.dashboard.shutdown_all_agents()

        logger.info("✅ AI Framework shutdown complete")

    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Create and start the AI Framework system
    system = AIFrameworkSystem(host="0.0.0.0", port=8001, debug=True)

    try:
        # Run the system
        asyncio.run(system.run())
    except KeyboardInterrupt:
        logger.info("🛑 Shutdown requested by user")
    except Exception as e:
        logger.error(f"❌ System failed: {str(e)}")
        sys.exit(1)

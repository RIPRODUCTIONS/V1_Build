#!/usr/bin/env python3
"""
Quick Start Script for Autonomous Task Solver System
This script demonstrates the system in action with example tasks.
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the autonomous_system package to the path
sys.path.insert(0, str(Path(__file__).parent))

from autonomous_system.autonomous_orchestrator import AutonomousOrchestrator
from autonomous_system.classification.task_classifier import TaskCategory
from autonomous_system.discovery.task_detector import (
    DetectedTask,
    TaskPriority,
    TaskSource,
)
from autonomous_system.learning.performance_tracker import (
    MetricType,
    PerformanceMetric,
    PerformanceTracker,
)
from autonomous_system.monitoring.system_monitor import SystemMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QuickStartDemo:
    """Demonstration of the Autonomous Task Solver System"""

    def __init__(self):
        self.config = self._create_demo_config()
        self.orchestrator = None
        self.performance_tracker = None
        self.system_monitor = None

    def _create_demo_config(self):
        """Create a demo configuration"""
        return {
            "system": {
                "name": "Autonomous Task Solver Demo",
                "environment": "development",
                "debug": True
            },
            "database": {
                "path": "demo_autonomous_system.db"
            },
            "ai_models": {
                "openai": {
                    "api_key": "demo_key",
                    "models": ["gpt-4", "gpt-3.5-turbo"],
                    "default_model": "gpt-3.5-turbo"
                },
                "ollama": {
                    "base_url": "http://localhost:11434",
                    "models": ["llama3.1:8b"],
                    "default_model": "llama3.1:8b"
                }
            },
            "task_detection": {
                "email": {"enabled": False},
                "slack": {"enabled": False},
                "calendar": {"enabled": False},
                "webhook": {"enabled": True, "port": 9001},
                "file_system": {"enabled": True}
            },
            "task_classification": {
                "model": "gpt-3.5-turbo",
                "categories": ["research", "automation", "data_analysis", "content_generation"],
                "confidence_threshold": 0.6
            },
            "model_selection": {
                "criteria_weights": {
                    "cost": 0.3,
                    "performance": 0.4,
                    "privacy": 0.2,
                    "availability": 0.1
                }
            },
            "task_execution": {
                "default_mode": "autonomous",
                "max_concurrent_tasks": 5,
                "timeouts": {
                    "task_startup": 30,
                    "step_execution": 300,
                    "total_execution": 1800
                }
            },
            "performance_tracking": {
                "collection_interval": 30,
                "analysis_interval": 120,
                "learning_rate": 0.1,
                "min_data_points": 5
            },
            "system_monitoring": {
                "monitoring_interval": 15,
                "alert_escalation_delay": 60,
                "thresholds": {
                    "cpu_usage": {"warning": 70.0, "critical": 90.0},
                    "memory_usage": {"warning": 80.0, "critical": 95.0},
                    "disk_usage": {"warning": 85.0, "critical": 95.0}
                }
            }
        }

    async def start_system(self):
        """Start the autonomous system"""
        logger.info("🚀 Starting Autonomous Task Solver System...")

        try:
            # Initialize the orchestrator
            self.orchestrator = AutonomousOrchestrator(self.config)

            # Initialize performance tracking
            self.performance_tracker = PerformanceTracker(self.config)

            # Initialize system monitoring
            self.system_monitor = SystemMonitor(self.config)

            # Start the system
            await self.orchestrator.initialize()
            await self.orchestrator.start()

            logger.info("✅ System started successfully!")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to start system: {e}")
            return False

    async def create_demo_tasks(self):
        """Create some demo tasks for the system to process"""
        logger.info("📝 Creating demo tasks...")

        demo_tasks = [
            {
                "title": "Research AI trends for 2024",
                "description": "Analyze current AI trends and provide insights for strategic planning",
                "source": TaskSource.FILE_SYSTEM,
                "priority": TaskPriority.HIGH,
                "category": TaskCategory.RESEARCH,
                "metadata": {
                    "deadline": (datetime.now() + timedelta(hours=2)).isoformat(),
                    "stakeholder": "CTO",
                    "budget": 50.0
                }
            },
            {
                "title": "Automate daily report generation",
                "description": "Create an automated system to generate daily performance reports",
                "source": TaskSource.WEBHOOK,
                "priority": TaskPriority.MEDIUM,
                "category": TaskCategory.AUTOMATION,
                "metadata": {
                    "deadline": (datetime.now() + timedelta(days=1)).isoformat(),
                    "stakeholder": "Operations Manager",
                    "budget": 100.0
                }
            },
            {
                "title": "Analyze customer feedback data",
                "description": "Process and analyze customer feedback to identify improvement areas",
                "source": TaskSource.FILE_SYSTEM,
                "priority": TaskPriority.HIGH,
                "category": TaskCategory.DATA_ANALYSIS,
                "metadata": {
                    "deadline": (datetime.now() + timedelta(hours=4)).isoformat(),
                    "stakeholder": "Product Manager",
                    "budget": 75.0
                }
            },
            {
                "title": "Generate marketing content",
                "description": "Create engaging marketing content for the new AI product launch",
                "source": TaskSource.WEBHOOK,
                "priority": TaskPriority.MEDIUM,
                "category": TaskCategory.CONTENT_GENERATION,
                "metadata": {
                    "deadline": (datetime.now() + timedelta(days=2)).isoformat(),
                    "stakeholder": "Marketing Director",
                    "budget": 150.0
                }
            }
        ]

        # Create and submit tasks
        for i, task_data in enumerate(demo_tasks, 1):
            task = DetectedTask(
                task_id=f"demo_task_{i}",
                title=task_data["title"],
                description=task_data["description"],
                source=task_data["source"],
                priority=task_data["priority"],
                timestamp=datetime.now(),
                metadata=task_data["metadata"]
            )

            # Submit task to the system
            await self.orchestrator.submit_task(task)
            logger.info(f"📋 Submitted task {i}: {task.title}")

            # Record performance metrics
            await self.performance_tracker.record_metric(
                PerformanceMetric(
                    metric_id=f"task_submission_{i}",
                    metric_type=MetricType.SUCCESS_RATE,
                    value=1.0,
                    task_category=task_data["category"].value,
                    model_used="demo",
                    agent_used="demo_agent",
                    timestamp=datetime.now(),
                    context={"task_id": task.task_id, "source": "demo"},
                    metadata={"priority": task_data["priority"].value}
                )
            )

    async def monitor_system(self, duration_minutes=5):
        """Monitor the system for a specified duration"""
        logger.info(f"📊 Monitoring system for {duration_minutes} minutes...")

        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)

        while datetime.now() < end_time:
            try:
                # Get system status
                status = await self.orchestrator.get_system_status()

                # Get performance summary
                performance_summary = await self.performance_tracker.get_performance_summary(hours=1)

                # Get system monitoring status
                monitor_status = await self.system_monitor.get_system_status()

                # Display status
                print("\n" + "="*60)
                print(f"🕐 System Status at {datetime.now().strftime('%H:%M:%S')}")
                print("="*60)

                print(f"📈 System Status: {status.status}")
                print(f"🔧 Active Components: {len(status.components)}")
                print(f"📋 Active Tasks: {status.active_tasks}")
                print(f"📊 Queue Length: {status.queue_length}")
                print(f"⏱️  Uptime: {status.uptime:.1f} seconds")

                if status.errors:
                    print(f"❌ Errors: {len(status.errors)}")
                    for error in status.errors[:3]:  # Show first 3 errors
                        print(f"   - {error}")

                print("\n📊 Performance Summary:")
                if "error" not in performance_summary:
                    for metric_type, data in performance_summary.get("metrics_by_type", {}).items():
                        print(f"   {metric_type}: {data['average']:.2f} (trend: {data['trend']})")

                print("\n💻 System Health:")
                if monitor_status and "health" in monitor_status and monitor_status["health"]:
                    health = monitor_status["health"]
                    print(f"   Status: {health['status']}")
                    print(f"   Score: {health['score']:.2f}")
                    print(f"   Alerts: {monitor_status['alerts']['total_active']}")

                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error during monitoring: {e}")
                await asyncio.sleep(30)

        logger.info("✅ Monitoring completed")

    async def run_demo(self):
        """Run the complete demo"""
        logger.info("🎬 Starting Autonomous Task Solver Demo...")

        # Start the system
        if not await self.start_system():
            return

        try:
            # Wait for system to fully initialize
            await asyncio.sleep(5)

            # Create demo tasks
            await self.create_demo_tasks()

            # Monitor the system
            await self.monitor_system(duration_minutes=3)

            # Show final results
            await self.show_demo_results()

        except KeyboardInterrupt:
            logger.info("⏹️  Demo interrupted by user")
        except Exception as e:
            logger.error(f"❌ Demo error: {e}")
        finally:
            # Shutdown the system
            await self.shutdown_system()

    async def show_demo_results(self):
        """Show the results of the demo"""
        logger.info("📊 Demo Results Summary...")

        try:
            # Get final system status
            status = await self.orchestrator.get_system_status()

            # Get performance insights
            recommendations = await self.performance_tracker.get_optimization_recommendations()

            # Get system alerts
            alerts = await self.system_monitor.get_alerts(limit=10)

            print("\n" + "🎯" + "="*58)
            print("🎯 DEMO RESULTS SUMMARY")
            print("🎯" + "="*58)

            print("\n📈 System Performance:")
            print(f"   Status: {status.status}")
            print(f"   Tasks Processed: {status.active_tasks + status.queue_length}")
            print(f"   System Uptime: {status.uptime:.1f} seconds")
            print(f"   Components Active: {len(status.components)}")

            print("\n💡 Optimization Recommendations:")
            if recommendations:
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"   {i}. {rec['description']}")
                    print(f"      Impact: {rec['impact_score']:.2f}, Confidence: {rec['confidence']:.2f}")
            else:
                print("   No recommendations available yet")

            print("\n🚨 System Alerts:")
            if alerts:
                for alert in alerts[:3]:
                    print(f"   - [{alert['level']}] {alert['title']}")
            else:
                print("   No active alerts")

            print("\n🎉 Demo completed successfully!")
            print("   The autonomous system is now running and processing tasks.")
            print("   You can continue to monitor it or stop it when ready.")

        except Exception as e:
            logger.error(f"Error showing demo results: {e}")

    async def shutdown_system(self):
        """Shutdown the system gracefully"""
        logger.info("🛑 Shutting down Autonomous Task Solver System...")

        try:
            if self.orchestrator:
                await self.orchestrator.shutdown()
            logger.info("✅ System shutdown completed")
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")

async def main():
    """Main demo function"""
    demo = QuickStartDemo()

    print("🤖" + "="*58)
    print("🤖 AUTONOMOUS TASK SOLVER SYSTEM - QUICK START DEMO")
    print("🤖" + "="*58)
    print()
    print("This demo will:")
    print("1. Start the autonomous system")
    print("2. Create sample tasks")
    print("3. Monitor system performance")
    print("4. Show results and recommendations")
    print()
    print("Press Ctrl+C to stop the demo early")
    print()

    try:
        await demo.run_demo()
    except KeyboardInterrupt:
        print("\n⏹️  Demo stopped by user")
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        return 1

    return 0

if __name__ == "__main__":
    # Run the demo
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

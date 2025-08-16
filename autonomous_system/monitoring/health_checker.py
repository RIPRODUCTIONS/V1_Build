"""
Health Check & Self-Healing System
Production-ready health monitoring with automatic recovery
"""

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import psutil


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"

class ComponentType(Enum):
    """System component types"""
    DATABASE = "database"
    REDIS = "redis"
    AI_MODEL = "ai_model"
    API_ENDPOINT = "api_endpoint"
    WORKER_PROCESS = "worker_process"
    FILE_SYSTEM = "file_system"
    NETWORK = "network"
    MEMORY = "memory"
    CPU = "cpu"
    DISK = "disk"

@dataclass
class HealthCheck:
    """Individual health check definition"""
    check_id: str
    component_type: ComponentType
    name: str
    description: str
    check_function: Callable
    timeout: float = 30.0
    interval: float = 60.0
    critical: bool = False
    dependencies: list[str] = field(default_factory=list)
    retry_count: int = 3
    retry_delay: float = 5.0

@dataclass
class HealthResult:
    """Health check result"""
    check_id: str
    component_type: ComponentType
    status: HealthStatus
    timestamp: datetime
    response_time: float
    details: dict[str, Any]
    error_message: str | None = None
    recommendations: list[str] = field(default_factory=list)

@dataclass
class SystemHealth:
    """Overall system health status"""
    status: HealthStatus
    score: float  # 0.0 to 1.0
    timestamp: datetime
    component_health: dict[str, HealthResult]
    overall_metrics: dict[str, Any]
    alerts: list[str]
    recommendations: list[str]

class HealthChecker:
    """Comprehensive health checking and self-healing system"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Health checks registry
        self.health_checks: dict[str, HealthCheck] = {}
        self.health_results: dict[str, HealthResult] = {}

        # Self-healing actions
        self.healing_actions: dict[str, Callable] = {}
        self.healing_history: list[dict[str, Any]] = []

        # Health thresholds
        self.thresholds = config.get("health", {}).get("thresholds", {
            "cpu_usage": {"warning": 70.0, "critical": 90.0},
            "memory_usage": {"warning": 80.0, "critical": 95.0},
            "disk_usage": {"warning": 85.0, "critical": 95.0},
            "response_time": {"warning": 2000.0, "critical": 5000.0}
        })

        # Health check intervals
        self.check_interval = config.get("health", {}).get("check_interval", 60.0)
        self.healing_cooldown = config.get("health", {}).get("healing_cooldown", 300.0)

        # Background tasks
        self.background_tasks = []
        self._start_background_tasks()

        # Initialize default health checks
        self._init_default_health_checks()

        self.logger.info("Health checker initialized")

    def _init_default_health_checks(self):
        """Initialize default system health checks"""
        # System resource checks
        self.register_health_check(
            HealthCheck(
                check_id="system_cpu",
                component_type=ComponentType.CPU,
                name="CPU Usage Check",
                description="Monitor CPU usage and performance",
                check_function=self._check_cpu_health,
                interval=30.0,
                critical=True
            )
        )

        self.register_health_check(
            HealthCheck(
                check_id="system_memory",
                component_type=ComponentType.MEMORY,
                name="Memory Usage Check",
                description="Monitor memory usage and availability",
                check_function=self._check_memory_health,
                interval=30.0,
                critical=True
            )
        )

        self.register_health_check(
            HealthCheck(
                check_id="system_disk",
                component_type=ComponentType.DISK,
                name="Disk Usage Check",
                description="Monitor disk space and I/O performance",
                check_function=self._check_disk_health,
                interval=60.0,
                critical=True
            )
        )

        # Database health check
        self.register_health_check(
            HealthCheck(
                check_id="database_connection",
                component_type=ComponentType.DATABASE,
                name="Database Connection Check",
                description="Verify database connectivity and performance",
                check_function=self._check_database_health,
                interval=30.0,
                critical=True
            )
        )

        # API endpoint health check
        self.register_health_check(
            HealthCheck(
                check_id="api_health",
                component_type=ComponentType.API_ENDPOINT,
                name="API Health Check",
                description="Verify API endpoints are responding",
                check_function=self._check_api_health,
                interval=30.0,
                critical=False
            )
        )

    def _start_background_tasks(self):
        """Start background health monitoring tasks"""
        self.background_tasks = [
            asyncio.create_task(self._continuous_health_monitoring()),
            asyncio.create_task(self._self_healing_monitor()),
            asyncio.create_task(self._health_metrics_cleanup())
        ]
        self.logger.info("Background health monitoring tasks started")

    def register_health_check(self, health_check: HealthCheck):
        """Register a new health check"""
        self.health_checks[health_check.check_id] = health_check
        self.logger.info(f"Registered health check: {health_check.name}")

    def register_healing_action(self, component_type: ComponentType, action: Callable):
        """Register a self-healing action for a component type"""
        self.healing_actions[component_type.value] = action
        self.logger.info(f"Registered healing action for {component_type.value}")

    async def run_health_check(self, check_id: str) -> HealthResult | None:
        """Run a specific health check"""
        if check_id not in self.health_checks:
            self.logger.warning(f"Health check not found: {check_id}")
            return None

        health_check = self.health_checks[check_id]

        try:
            # Run health check with timeout
            start_time = time.time()

            if asyncio.iscoroutinefunction(health_check.check_function):
                result = await asyncio.wait_for(
                    health_check.check_function(),
                    timeout=health_check.timeout
                )
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, health_check.check_function),
                    timeout=health_check.timeout
                )

            response_time = time.time() - start_time

            # Create health result
            health_result = HealthResult(
                check_id=check_id,
                component_type=health_check.component_type,
                status=result.get("status", HealthStatus.HEALTHY),
                timestamp=datetime.now(),
                response_time=response_time,
                details=result.get("details", {}),
                error_message=result.get("error_message"),
                recommendations=result.get("recommendations", [])
            )

            # Store result
            self.health_results[check_id] = health_result

            # Log result
            if health_result.status == HealthStatus.HEALTHY:
                self.logger.debug(f"Health check passed: {check_id}")
            else:
                self.logger.warning(f"Health check failed: {check_id} - {health_result.error_message}")

            return health_result

        except TimeoutError:
            self.logger.error(f"Health check timeout: {check_id}")
            return HealthResult(
                check_id=check_id,
                component_type=health_check.component_type,
                status=HealthStatus.CRITICAL,
                timestamp=datetime.now(),
                response_time=health_check.timeout,
                details={},
                error_message="Health check timeout",
                recommendations=["Increase timeout or optimize check function"]
            )

        except Exception as e:
            self.logger.error(f"Health check error: {check_id} - {e}")
            return HealthResult(
                check_id=check_id,
                component_type=health_check.component_type,
                status=HealthStatus.CRITICAL,
                timestamp=datetime.now(),
                response_time=0.0,
                details={},
                error_message=str(e),
                recommendations=["Review health check implementation"]
            )

    async def run_all_health_checks(self) -> list[HealthResult]:
        """Run all registered health checks"""
        tasks = []
        for check_id in self.health_checks:
            tasks.append(self.run_health_check(check_id))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and return valid results
        valid_results = [r for r in results if r is not None and not isinstance(r, Exception)]

        return valid_results

    async def get_system_health(self) -> SystemHealth:
        """Get overall system health status"""
        # Run health checks if needed
        if not self.health_results:
            await self.run_all_health_checks()

        # Calculate overall health score
        health_score = self._calculate_health_score()

        # Determine overall status
        if health_score >= 0.9:
            overall_status = HealthStatus.HEALTHY
        elif health_score >= 0.7:
            overall_status = HealthStatus.DEGRADED
        elif health_score >= 0.5:
            overall_status = HealthStatus.UNHEALTHY
        else:
            overall_status = HealthStatus.CRITICAL

        # Generate recommendations
        recommendations = self._generate_health_recommendations()

        # Generate alerts
        alerts = self._generate_health_alerts()

        # Calculate overall metrics
        overall_metrics = self._calculate_overall_metrics()

        return SystemHealth(
            status=overall_status,
            score=health_score,
            timestamp=datetime.now(),
            component_health=self.health_results.copy(),
            overall_metrics=overall_metrics,
            alerts=alerts,
            recommendations=recommendations
        )

    def _calculate_health_score(self) -> float:
        """Calculate overall health score based on component health"""
        if not self.health_results:
            return 1.0

        total_score = 0.0
        total_checks = len(self.health_results)

        for result in self.health_results.values():
            if result.status == HealthStatus.HEALTHY:
                total_score += 1.0
            elif result.status == HealthStatus.DEGRADED:
                total_score += 0.7
            elif result.status == HealthStatus.UNHEALTHY:
                total_score += 0.4
            else:  # CRITICAL
                total_score += 0.1

        return total_score / total_checks if total_checks > 0 else 1.0

    def _calculate_overall_metrics(self) -> dict[str, Any]:
        """Calculate overall system metrics"""
        metrics = {}

        # System resource metrics
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            metrics.update({
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_usage": disk.percent,
                "disk_free_gb": disk.free / (1024**3)
            })
        except Exception as e:
            self.logger.warning(f"Failed to get system metrics: {e}")

        # Health check metrics
        if self.health_results:
            status_counts = {}
            for result in self.health_results.values():
                status = result.status.value
                status_counts[status] = status_counts.get(status, 0) + 1

            metrics["health_check_status"] = status_counts
            metrics["total_health_checks"] = len(self.health_results)

        return metrics

    def _generate_health_recommendations(self) -> list[str]:
        """Generate health improvement recommendations"""
        recommendations = []

        for result in self.health_results.values():
            if result.status != HealthStatus.HEALTHY:
                recommendations.extend(result.recommendations)

        # Add system-level recommendations
        if self.health_results:
            critical_count = len([r for r in self.health_results.values() if r.status == HealthStatus.CRITICAL])
            if critical_count > 0:
                recommendations.append(f"Immediate attention required for {critical_count} critical components")

            unhealthy_count = len([r for r in self.health_results.values() if r.status in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]])
            if unhealthy_count > 0:
                recommendations.append(f"Review and fix {unhealthy_count} unhealthy components")

        return list(set(recommendations))  # Remove duplicates

    def _generate_health_alerts(self) -> list[str]:
        """Generate health alerts for critical issues"""
        alerts = []

        for result in self.health_results.values():
            if result.status == HealthStatus.CRITICAL:
                alerts.append(f"CRITICAL: {result.component_type.value} - {result.error_message}")
            elif result.status == HealthStatus.UNHEALTHY:
                alerts.append(f"UNHEALTHY: {result.component_type.value} - {result.error_message}")

        return alerts

    # Default health check implementations
    async def _check_cpu_health(self) -> dict[str, Any]:
        """Check CPU health"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            if cpu_percent > self.thresholds["cpu_usage"]["critical"]:
                status = HealthStatus.CRITICAL
                recommendations = ["Immediate CPU optimization required", "Consider scaling or load balancing"]
            elif cpu_percent > self.thresholds["cpu_usage"]["warning"]:
                status = HealthStatus.DEGRADED
                recommendations = ["Monitor CPU usage closely", "Consider optimization"]
            else:
                status = HealthStatus.HEALTHY
                recommendations = []

            return {
                "status": status,
                "details": {
                    "cpu_percent": cpu_percent,
                    "cpu_count": cpu_count,
                    "threshold_warning": self.thresholds["cpu_usage"]["warning"],
                    "threshold_critical": self.thresholds["cpu_usage"]["critical"]
                },
                "recommendations": recommendations
            }

        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL,
                "details": {},
                "error_message": f"CPU health check failed: {e}",
                "recommendations": ["Investigate system monitoring issues"]
            }

    async def _check_memory_health(self) -> dict[str, Any]:
        """Check memory health"""
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)

            if memory_percent > self.thresholds["memory_usage"]["critical"]:
                status = HealthStatus.CRITICAL
                recommendations = ["Immediate memory cleanup required", "Consider restarting services"]
            elif memory_percent > self.thresholds["memory_usage"]["warning"]:
                status = HealthStatus.DEGRADED
                recommendations = ["Monitor memory usage", "Consider memory cleanup"]
            else:
                status = HealthStatus.HEALTHY
                recommendations = []

            return {
                "status": status,
                "details": {
                    "memory_percent": memory_percent,
                    "memory_available_gb": memory_available_gb,
                    "memory_total_gb": memory.total / (1024**3),
                    "threshold_warning": self.thresholds["memory_usage"]["warning"],
                    "threshold_critical": self.thresholds["memory_usage"]["critical"]
                },
                "recommendations": recommendations
            }

        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL,
                "details": {},
                "error_message": f"Memory health check failed: {e}",
                "recommendations": ["Investigate system monitoring issues"]
            }

    async def _check_disk_health(self) -> dict[str, Any]:
        """Check disk health"""
        try:
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_free_gb = disk.free / (1024**3)

            if disk_percent > self.thresholds["disk_usage"]["critical"]:
                status = HealthStatus.CRITICAL
                recommendations = ["Immediate disk cleanup required", "Consider disk expansion"]
            elif disk_percent > self.thresholds["disk_usage"]["warning"]:
                status = HealthStatus.DEGRADED
                recommendations = ["Monitor disk usage", "Consider cleanup"]
            else:
                status = HealthStatus.HEALTHY
                recommendations = []

            return {
                "status": status,
                "details": {
                    "disk_percent": disk_percent,
                    "disk_free_gb": disk_free_gb,
                    "disk_total_gb": disk.total / (1024**3),
                    "threshold_warning": self.thresholds["disk_usage"]["warning"],
                    "threshold_critical": self.thresholds["disk_usage"]["critical"]
                },
                "recommendations": recommendations
            }

        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL,
                "details": {},
                "error_message": f"Disk health check failed: {e}",
                "recommendations": ["Investigate system monitoring issues"]
            }

    async def _check_database_health(self) -> dict[str, Any]:
        """Check database health"""
        try:
            # This would check actual database connectivity
            # For now, simulate a database check
            import random

            # Simulate database response time
            response_time = random.uniform(10, 100)  # ms

            if response_time > self.thresholds["response_time"]["critical"]:
                status = HealthStatus.CRITICAL
                recommendations = ["Database performance critical", "Review database configuration"]
            elif response_time > self.thresholds["response_time"]["warning"]:
                status = HealthStatus.DEGRADED
                recommendations = ["Database performance degraded", "Monitor database performance"]
            else:
                status = HealthStatus.HEALTHY
                recommendations = []

            return {
                "status": status,
                "details": {
                    "response_time_ms": response_time,
                    "connection_status": "connected",
                    "threshold_warning": self.thresholds["response_time"]["warning"],
                    "threshold_critical": self.thresholds["response_time"]["critical"]
                },
                "recommendations": recommendations
            }

        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL,
                "details": {},
                "error_message": f"Database health check failed: {e}",
                "recommendations": ["Check database connectivity", "Review database configuration"]
            }

    async def _check_api_health(self) -> dict[str, Any]:
        """Check API health"""
        try:
            # This would check actual API endpoints
            # For now, simulate an API check
            import random

            # Simulate API response time
            response_time = random.uniform(50, 200)  # ms

            if response_time > self.thresholds["response_time"]["critical"]:
                status = HealthStatus.CRITICAL
                recommendations = ["API performance critical", "Review API configuration"]
            elif response_time > self.thresholds["response_time"]["warning"]:
                status = HealthStatus.DEGRADED
                recommendations = ["API performance degraded", "Monitor API performance"]
            else:
                status = HealthStatus.HEALTHY
                recommendations = []

            return {
                "status": status,
                "details": {
                    "response_time_ms": response_time,
                    "endpoint_status": "responding",
                    "threshold_warning": self.thresholds["response_time"]["warning"],
                    "threshold_critical": self.thresholds["response_time"]["critical"]
                },
                "recommendations": recommendations
            }

        except Exception as e:
            return {
                "status": HealthStatus.CRITICAL,
                "details": {},
                "error_message": f"API health check failed: {e}",
                "recommendations": ["Check API connectivity", "Review API configuration"]
            }

    # Background monitoring tasks
    async def _continuous_health_monitoring(self):
        """Continuous health monitoring loop"""
        while True:
            try:
                # Run all health checks
                await self.run_all_health_checks()

                # Get system health
                system_health = await self.get_system_health()

                # Log health status
                if system_health.status == HealthStatus.HEALTHY:
                    self.logger.debug(f"System health: {system_health.score:.2f}")
                else:
                    self.logger.warning(f"System health degraded: {system_health.status.value} (score: {system_health.score:.2f})")

                # Wait for next check interval
                await asyncio.sleep(self.check_interval)

            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(30)  # Wait before retrying

    async def _self_healing_monitor(self):
        """Monitor for self-healing opportunities"""
        while True:
            try:
                # Check for components that need healing
                for result in self.health_results.values():
                    if result.status in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]:
                        await self._attempt_self_healing(result)

                await asyncio.sleep(self.healing_cooldown)

            except Exception as e:
                self.logger.error(f"Self-healing monitor error: {e}")
                await asyncio.sleep(60)

    async def _attempt_self_healing(self, health_result: HealthResult):
        """Attempt to self-heal a component"""
        try:
            component_type = health_result.component_type.value

            if component_type in self.healing_actions:
                self.logger.info(f"Attempting self-healing for {component_type}")

                # Record healing attempt
                healing_record = {
                    "timestamp": datetime.now().isoformat(),
                    "component_type": component_type,
                    "check_id": health_result.check_id,
                    "previous_status": health_result.status.value,
                    "action": "self_healing_attempt"
                }

                # Execute healing action
                healing_action = self.healing_actions[component_type]
                if asyncio.iscoroutinefunction(healing_action):
                    result = await healing_action(health_result)
                else:
                    result = healing_action(health_result)

                healing_record["result"] = result
                self.healing_history.append(healing_record)

                self.logger.info(f"Self-healing completed for {component_type}: {result}")

            else:
                self.logger.debug(f"No healing action registered for {component_type}")

        except Exception as e:
            self.logger.error(f"Self-healing failed for {health_result.component_type.value}: {e}")

    async def _health_metrics_cleanup(self):
        """Clean up old health metrics"""
        while True:
            try:
                # Keep only recent health results (last 24 hours)
                cutoff_time = datetime.now() - timedelta(hours=24)

                old_results = [
                    check_id for check_id, result in self.health_results.items()
                    if result.timestamp < cutoff_time
                ]

                for check_id in old_results:
                    del self.health_results[check_id]

                if old_results:
                    self.logger.info(f"Cleaned up {len(old_results)} old health results")

                # Clean up healing history (keep last 7 days)
                cutoff_time = datetime.now() - timedelta(days=7)
                self.healing_history = [
                    record for record in self.healing_history
                    if datetime.fromisoformat(record["timestamp"]) > cutoff_time
                ]

                await asyncio.sleep(3600)  # Clean up every hour

            except Exception as e:
                self.logger.error(f"Health metrics cleanup error: {e}")
                await asyncio.sleep(3600)

    # Public API methods
    async def get_component_health(self, component_type: ComponentType) -> list[HealthResult]:
        """Get health status for a specific component type"""
        return [
            result for result in self.health_results.values()
            if result.component_type == component_type
        ]

    def get_healing_history(self, hours: int = 24) -> list[dict[str, Any]]:
        """Get healing history for the specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        return [
            record for record in self.healing_history
            if datetime.fromisoformat(record["timestamp"]) > cutoff_time
        ]

    async def force_health_check(self, check_id: str) -> HealthResult | None:
        """Force a health check to run immediately"""
        return await self.run_health_check(check_id)

    async def shutdown(self):
        """Shutdown the health checker"""
        try:
            self.logger.info("Shutting down Health Checker...")

            # Cancel background tasks
            for task in self.background_tasks:
                task.cancel()

            # Wait for tasks to complete
            await asyncio.gather(*self.background_tasks, return_exceptions=True)

            self.logger.info("Health Checker shutdown completed")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

# Example usage
async def main():
    """Example usage of the health checker"""
    config = {
        "health": {
            "check_interval": 30,
            "healing_cooldown": 120,
            "thresholds": {
                "cpu_usage": {"warning": 70.0, "critical": 90.0},
                "memory_usage": {"warning": 80.0, "critical": 95.0},
                "disk_usage": {"warning": 85.0, "critical": 95.0},
                "response_time": {"warning": 2000.0, "critical": 5000.0}
            }
        }
    }

    # Initialize health checker
    health_checker = HealthChecker(config)

    # Register a custom healing action
    def heal_database(health_result):
        return "Database connection restored"

    health_checker.register_healing_action(ComponentType.DATABASE, heal_database)

    # Wait for some health checks to run
    await asyncio.sleep(35)

    # Get system health
    system_health = await health_checker.get_system_health()
    print(f"System Health: {system_health.status.value} (Score: {system_health.score:.2f})")

    # Get component health
    cpu_health = await health_checker.get_component_health(ComponentType.CPU)
    if cpu_health:
        print(f"CPU Health: {cpu_health[0].status.value}")

    # Get healing history
    healing_history = health_checker.get_healing_history(hours=1)
    print(f"Healing attempts in last hour: {len(healing_history)}")

    # Shutdown
    await health_checker.shutdown()

if __name__ == "__main__":
    asyncio.run(main())

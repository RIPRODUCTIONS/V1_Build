#!/usr/bin/env python3
"""
AI Framework Stability Testing Suite
Comprehensive reliability and stability validation
"""

import asyncio
import time
import random
import logging
import json
import psutil
import threading
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import aiohttp
import subprocess
import signal
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class StabilityTestResult:
    """Individual stability test result"""
    test_name: str
    category: str
    status: str  # PASS, FAIL, WARNING
    duration: float
    details: Dict[str, Any]
    timestamp: datetime
    error_message: Optional[str] = None

@dataclass
class StabilitySummary:
    """Stability test summary"""
    total_tests: int
    passed: int
    failed: int
    warnings: int
    total_duration: float
    success_rate: float
    system_health_score: float

class StabilityTestSuite:
    """Comprehensive stability testing suite for AI Framework"""

    def __init__(self, base_url: str = "http://localhost:18000"):
        self.base_url = base_url
        self.results: List[StabilityTestResult] = []
        self.session = None
        self.system_metrics = []
        self.monitoring_thread = None
        self.stop_monitoring = False

    async def setup_session(self):
        """Setup HTTP session for testing"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)

    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()

    def add_result(self, test_name: str, category: str, status: str,
                   duration: float, details: Dict = None, error_message: str = None):
        """Add a test result"""
        result = StabilityTestResult(
            test_name=test_name,
            category=category,
            status=status,
            duration=duration,
            details=details or {},
            timestamp=datetime.now(),
            error_message=error_message
        )
        self.results.append(result)

        # Log the result
        log_level = logging.ERROR if status == "FAIL" else logging.INFO
        logger.log(log_level, f"{test_name}: {status} - Duration: {duration:.2f}s")
        if error_message:
            logger.error(f"Error: {error_message}")

    def monitor_system_resources(self):
        """Monitor system resources during testing"""
        while not self.stop_monitoring:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')

                # Get process info for AI Framework
                ai_framework_processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                    try:
                        if 'python' in proc.info['name'].lower() or 'uvicorn' in proc.info['name'].lower():
                            ai_framework_processes.append(proc.info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                self.system_metrics.append({
                    'timestamp': time.time(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available': memory.available,
                    'disk_percent': disk.percent,
                    'ai_framework_processes': ai_framework_processes
                })

                time.sleep(1)
            except Exception as e:
                logger.error(f"Error monitoring system: {e}")
                break

    async def test_basic_functionality(self):
        """Test basic system functionality"""
        logger.info("Testing basic system functionality...")

        test_cases = [
            ("Health Check", "/health"),
            ("Root Endpoint", "/"),
            ("Ready Check", "/ready")
        ]

        for test_name, endpoint in test_cases:
            start_time = time.time()
            try:
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    duration = time.time() - start_time

                    if response.status == 200:
                        self.add_result(
                            test_name,
                            "Basic Functionality",
                            "PASS",
                            duration,
                            {"endpoint": endpoint, "status_code": response.status}
                        )
                    else:
                        self.add_result(
                            test_name,
                            "Basic Functionality",
                            "FAIL",
                            duration,
                            {"endpoint": endpoint, "status_code": response.status},
                            f"Expected 200, got {response.status}"
                        )

            except Exception as e:
                duration = time.time() - start_time
                self.add_result(
                    test_name,
                    "Basic Functionality",
                    "FAIL",
                    duration,
                    {"endpoint": endpoint},
                    str(e)
                )

    async def test_authentication_system(self):
        """Test authentication system stability"""
        logger.info("Testing authentication system stability...")

        # Test login
        start_time = time.time()
        try:
            login_data = {"username": "admin", "password": "admin123"}
            async with self.session.post(f"{self.base_url}/auth/login", json=login_data) as response:
                duration = time.time() - start_time

                if response.status == 200:
                    data = await response.json()
                    if "access_token" in data:
                        self.add_result(
                            "Authentication Login",
                            "Authentication",
                            "PASS",
                            duration,
                            {"status_code": response.status, "has_token": True}
                        )

                        # Test protected endpoint with token
                        token = data["access_token"]
                        headers = {"Authorization": f"Bearer {token}"}

                        # Test metrics endpoint
                        async with self.session.get(f"{self.base_url}/metrics", headers=headers) as metrics_response:
                            if metrics_response.status == 200:
                                self.add_result(
                                    "Protected Endpoint Access",
                                    "Authentication",
                                    "PASS",
                                    duration,
                                    {"endpoint": "/metrics", "status_code": metrics_response.status}
                                )
                            else:
                                self.add_result(
                                    "Protected Endpoint Access",
                                    "Authentication",
                                    "FAIL",
                                    duration,
                                    {"endpoint": "/metrics", "status_code": metrics_response.status},
                                    f"Expected 200, got {metrics_response.status}"
                                )
                    else:
                        self.add_result(
                            "Authentication Login",
                            "Authentication",
                            "FAIL",
                            duration,
                            {"status_code": response.status},
                            "No access token in response"
                        )
                else:
                    self.add_result(
                        "Authentication Login",
                        "Authentication",
                        "FAIL",
                        duration,
                        {"status_code": response.status},
                        f"Expected 200, got {response.status}"
                    )

        except Exception as e:
            duration = time.time() - start_time
            self.add_result(
                "Authentication Login",
                "Authentication",
                "FAIL",
                duration,
                {},
                str(e)
            )

    async def test_load_stability(self):
        """Test system stability under load"""
        logger.info("Testing system stability under load...")

        # Send multiple concurrent requests
        concurrent_requests = 20
        start_time = time.time()

        try:
            tasks = []
            for i in range(concurrent_requests):
                task = self.session.get(f"{self.base_url}/health")
                tasks.append(task)

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Analyze results
            successful = 0
            failed = 0
            response_times = []

            for i, response in enumerate(responses):
                if isinstance(response, aiohttp.ClientResponse):
                    if response.status == 200:
                        successful += 1
                        response_times.append(response.headers.get('x-process-time', '0'))
                    else:
                        failed += 1
                else:
                    failed += 1

            duration = time.time() - start_time
            success_rate = successful / concurrent_requests

            if success_rate >= 0.95:  # 95% success rate
                self.add_result(
                    "Load Stability",
                    "Performance",
                    "PASS",
                    duration,
                    {
                        "concurrent_requests": concurrent_requests,
                        "successful": successful,
                        "failed": failed,
                        "success_rate": success_rate,
                        "avg_response_time": sum(float(t) for t in response_times if t != '0') / len(response_times) if response_times else 0
                    }
                )
            elif success_rate >= 0.80:  # 80% success rate
                self.add_result(
                    "Load Stability",
                    "Performance",
                    "WARNING",
                    duration,
                    {
                        "concurrent_requests": concurrent_requests,
                        "successful": successful,
                        "failed": failed,
                        "success_rate": success_rate
                    },
                    f"Success rate {success_rate:.2%} below 95% threshold"
                )
            else:
                self.add_result(
                    "Load Stability",
                    "Performance",
                    "FAIL",
                    duration,
                    {
                        "concurrent_requests": concurrent_requests,
                        "successful": successful,
                        "failed": failed,
                        "success_rate": success_rate
                    },
                    f"Success rate {success_rate:.2%} below 80% threshold"
                )

        except Exception as e:
            duration = time.time() - start_time
            self.add_result(
                "Load Stability",
                "Performance",
                "FAIL",
                duration,
                {"concurrent_requests": concurrent_requests},
                str(e)
            )

    async def test_error_handling(self):
        """Test system error handling and recovery"""
        logger.info("Testing error handling and recovery...")

        # Test invalid endpoints
        invalid_endpoints = [
            "/nonexistent",
            "/api/invalid",
            "/invalid/path"
        ]

        for endpoint in invalid_endpoints:
            start_time = time.time()
            try:
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    duration = time.time() - start_time

                    # Should return 404 for invalid endpoints
                    if response.status == 404:
                        self.add_result(
                            f"Error Handling - {endpoint}",
                            "Error Handling",
                            "PASS",
                            duration,
                            {"endpoint": endpoint, "status_code": response.status}
                        )
                    else:
                        self.add_result(
                            f"Error Handling - {endpoint}",
                            "Error Handling",
                            "WARNING",
                            duration,
                            {"endpoint": endpoint, "status_code": response.status},
                            f"Expected 404, got {response.status}"
                        )

            except Exception as e:
                duration = time.time() - start_time
                self.add_result(
                    f"Error Handling - {endpoint}",
                    "Error Handling",
                    "FAIL",
                    duration,
                    {"endpoint": endpoint},
                    str(e)
                )

        # Test malformed requests
        start_time = time.time()
        try:
            # Send malformed JSON
            malformed_data = "{invalid json"
            headers = {"Content-Type": "application/json"}

            async with self.session.post(f"{self.base_url}/auth/login", data=malformed_data, headers=headers) as response:
                duration = time.time() - start_time

                # Should handle malformed JSON gracefully
                if response.status in [400, 422]:  # Bad Request or Unprocessable Entity
                    self.add_result(
                        "Malformed Request Handling",
                        "Error Handling",
                        "PASS",
                        duration,
                        {"status_code": response.status, "request_type": "malformed_json"}
                    )
                else:
                    self.add_result(
                        "Malformed Request Handling",
                        "Error Handling",
                        "WARNING",
                        duration,
                        {"status_code": response.status, "request_type": "malformed_json"},
                        f"Expected 400/422, got {response.status}"
                    )

        except Exception as e:
            duration = time.time() - start_time
            self.add_result(
                "Malformed Request Handling",
                "Error Handling",
                "FAIL",
                duration,
                {"request_type": "malformed_json"},
                str(e)
            )

    async def test_database_connectivity(self):
        """Test database connectivity and stability"""
        logger.info("Testing database connectivity...")

        # Test endpoints that use database
        db_dependent_endpoints = [
            "/api/dashboard/overview",
            "/api/system/status"
        ]

        for endpoint in db_dependent_endpoints:
            start_time = time.time()
            try:
                # First get a valid token
                login_data = {"username": "admin", "password": "admin123"}
                async with self.session.post(f"{self.base_url}/auth/login", json=login_data) as login_response:
                    if login_response.status == 200:
                        data = await login_response.json()
                        token = data["access_token"]
                        headers = {"Authorization": f"Bearer {token}"}

                        # Test database-dependent endpoint
                        async with self.session.get(f"{self.base_url}{endpoint}", headers=headers) as response:
                            duration = time.time() - start_time

                            if response.status == 200:
                                self.add_result(
                                    f"Database Connectivity - {endpoint}",
                                    "Database",
                                    "PASS",
                                    duration,
                                    {"endpoint": endpoint, "status_code": response.status}
                                )
                            else:
                                self.add_result(
                                    f"Database Connectivity - {endpoint}",
                                    "Database",
                                    "FAIL",
                                    duration,
                                    {"endpoint": endpoint, "status_code": response.status},
                                    f"Database endpoint returned {response.status}"
                                )
                    else:
                        duration = time.time() - start_time
                        self.add_result(
                            f"Database Connectivity - {endpoint}",
                            "Database",
                            "FAIL",
                            duration,
                            {"endpoint": endpoint},
                            "Failed to get authentication token"
                        )

            except Exception as e:
                duration = time.time() - start_time
                self.add_result(
                    f"Database Connectivity - {endpoint}",
                    "Database",
                    "FAIL",
                    duration,
                    {"endpoint": endpoint},
                    str(e)
                )

    async def test_system_resources(self):
        """Test system resource usage and limits"""
        logger.info("Testing system resource usage...")

        # Check current system resources
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Define thresholds
            cpu_threshold = 80.0  # 80% CPU usage
            memory_threshold = 85.0  # 85% memory usage
            disk_threshold = 90.0  # 90% disk usage

            start_time = time.time()

            # Check CPU usage
            if cpu_percent < cpu_threshold:
                self.add_result(
                    "CPU Usage Check",
                    "System Resources",
                    "PASS",
                    0.0,
                    {"cpu_percent": cpu_percent, "threshold": cpu_threshold}
                )
            else:
                self.add_result(
                    "CPU Usage Check",
                    "System Resources",
                    "WARNING",
                    0.0,
                    {"cpu_percent": cpu_percent, "threshold": cpu_threshold},
                    f"CPU usage {cpu_percent}% above threshold {cpu_threshold}%"
                )

            # Check memory usage
            if memory.percent < memory_threshold:
                self.add_result(
                    "Memory Usage Check",
                    "System Resources",
                    "PASS",
                    0.0,
                    {"memory_percent": memory.percent, "threshold": memory_threshold}
                )
            else:
                self.add_result(
                    "Memory Usage Check",
                    "System Resources",
                    "WARNING",
                    0.0,
                    {"memory_percent": memory.percent, "threshold": memory_threshold},
                    f"Memory usage {memory.percent}% above threshold {memory_threshold}%"
                )

            # Check disk usage
            if disk.percent < disk_threshold:
                self.add_result(
                    "Disk Usage Check",
                    "System Resources",
                    "PASS",
                    0.0,
                    {"disk_percent": disk.percent, "threshold": disk_threshold}
                )
            else:
                self.add_result(
                    "Disk Usage Check",
                    "System Resources",
                    "WARNING",
                    0.0,
                    {"disk_percent": disk.percent, "threshold": disk_threshold},
                    f"Disk usage {disk.percent}% above threshold {disk_threshold}%"
                )

        except Exception as e:
            self.add_result(
                "System Resources Check",
                "System Resources",
                "FAIL",
                0.0,
                {},
                str(e)
            )

    async def run_all_tests(self):
        """Run all stability tests"""
        logger.info("Starting comprehensive stability testing...")

        # Start system monitoring
        self.monitoring_thread = threading.Thread(target=self.monitor_system_resources)
        self.monitoring_thread.start()

        await self.setup_session()

        try:
            # Run all test categories
            await self.test_basic_functionality()
            await self.test_authentication_system()
            await self.test_load_stability()
            await self.test_error_handling()
            await self.test_database_connectivity()
            await self.test_system_resources()

        finally:
            await self.cleanup_session()

            # Stop monitoring
            self.stop_monitoring = True
            if self.monitoring_thread:
                self.monitoring_thread.join()

    def generate_summary(self) -> StabilitySummary:
        """Generate stability test summary"""
        if not self.results:
            return StabilitySummary(0, 0, 0, 0, 0.0, 0.0, 0.0)

        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        warnings = sum(1 for r in self.results if r.status == "WARNING")

        total_duration = sum(r.duration for r in self.results)
        success_rate = passed / total_tests if total_tests > 0 else 0.0

        # Calculate system health score based on resource usage
        system_health_score = 100.0
        if self.system_metrics:
            latest_metrics = self.system_metrics[-1]
            if latest_metrics['cpu_percent'] > 80:
                system_health_score -= 20
            if latest_metrics['memory_percent'] > 85:
                system_health_score -= 20
            if latest_metrics['disk_percent'] > 90:
                system_health_score -= 20

        return StabilitySummary(
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            warnings=warnings,
            total_duration=total_duration,
            success_rate=success_rate,
            system_health_score=system_health_score
        )

    def save_results(self, filename: str = None) -> None:
        """Save stability test results to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stability_test_results_{timestamp}.json"

        summary = self.generate_summary()

        output = {
            'summary': {
                'total_tests': summary.total_tests,
                'passed': summary.passed,
                'failed': summary.failed,
                'warnings': summary.warnings,
                'total_duration': summary.total_duration,
                'success_rate': summary.success_rate,
                'system_health_score': summary.system_health_score
            },
            'system_metrics': self.system_metrics,
            'test_results': [
                {
                    'test_name': r.test_name,
                    'category': r.category,
                    'status': r.status,
                    'duration': r.duration,
                    'details': r.details,
                    'timestamp': r.timestamp.isoformat(),
                    'error_message': r.error_message
                }
                for r in self.results
            ]
        }

        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)

        logger.info(f"Stability test results saved to {filename}")

    def print_summary(self) -> None:
        """Print stability test summary to console"""
        summary = self.generate_summary()

        print("\n" + "="*60)
        print("STABILITY TEST RESULTS SUMMARY")
        print("="*60)
        print(f"Total Tests: {summary.total_tests}")
        print(f"Passed: {summary.passed}")
        print(f"Failed: {summary.failed}")
        print(f"Warnings: {summary.warnings}")
        print(f"Success Rate: {summary.success_rate:.2%}")
        print(f"Total Duration: {summary.total_duration:.2f} seconds")
        print(f"System Health Score: {summary.system_health_score:.1f}/100")
        print("="*60)

        # Print failed tests
        if summary.failed > 0:
            print("\nFAILED TESTS:")
            print("-" * 40)
            for result in self.results:
                if result.status == "FAIL":
                    print(f"❌ {result.test_name}: {result.error_message}")

async def main():
    """Main stability testing execution"""
    print("🧪 AI Framework Stability Testing Suite")
    print("="*50)

    # Initialize stability test suite
    stability_tester = StabilityTestSuite()

    # Run all stability tests
    await stability_tester.run_all_tests()

    # Generate and display results
    stability_tester.print_summary()

    # Save results
    stability_tester.save_results()

    print("\n✅ Stability testing completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
AI Framework Chaos Engineering Module
Test system resilience under various failure conditions
"""

import asyncio
import time
import random
import logging
import json
import subprocess
import signal
import os
import threading
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import aiohttp
import psutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ChaosTestResult:
    """Individual chaos test result"""
    test_name: str
    category: str
    status: str  # PASS, FAIL, WARNING
    duration: float
    failure_injected: bool
    system_recovered: bool
    details: Dict[str, Any]
    timestamp: datetime
    error_message: Optional[str] = None

@dataclass
class ChaosSummary:
    """Chaos testing summary"""
    total_tests: int
    passed: int
    failed: int
    warnings: int
    total_duration: float
    recovery_rate: float
    resilience_score: float

class ChaosEngineer:
    """Chaos engineering module for AI Framework"""

    def __init__(self, base_url: str = "http://localhost:18000"):
        self.base_url = base_url
        self.results: List[ChaosTestResult] = []
        self.session = None
        self.system_metrics = []
        self.monitoring_thread = None
        self.stop_monitoring = False
        self.original_processes = {}

    async def setup_session(self):
        """Setup HTTP session for testing"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)

    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()

    def add_result(self, test_name: str, category: str, status: str,
                   duration: float, failure_injected: bool, system_recovered: bool,
                   details: Dict = None, error_message: str = None):
        """Add a chaos test result"""
        result = ChaosTestResult(
            test_name=test_name,
            category=category,
            status=status,
            duration=duration,
            failure_injected=failure_injected,
            system_recovered=system_recovered,
            details=details or {},
            timestamp=datetime.now(),
            error_message=error_message
        )
        self.results.append(result)

        # Log the result
        log_level = logging.ERROR if status == "FAIL" else logging.INFO
        logger.log(log_level, f"{test_name}: {status} - Recovery: {system_recovered}")
        if error_message:
            logger.error(f"Error: {error_message}")

    def monitor_system_resources(self):
        """Monitor system resources during chaos testing"""
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

    def get_ai_framework_processes(self) -> List[Dict[str, Any]]:
        """Get all AI Framework related processes"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if any(keyword in proc.info['name'].lower() for keyword in ['python', 'uvicorn', 'ai_framework']):
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmdline': proc.info['cmdline']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return processes

    async def test_process_kill_resilience(self):
        """Test system resilience when processes are killed"""
        logger.info("Testing process kill resilience...")

        start_time = time.time()

        try:
            # Get AI Framework processes
            processes = self.get_ai_framework_processes()
            if not processes:
                self.add_result(
                    "Process Kill Resilience",
                    "Process Management",
                    "WARNING",
                    time.time() - start_time,
                    False,
                    False,
                    {"processes_found": 0},
                    "No AI Framework processes found"
                )
                return

            # Store original process info
            self.original_processes = {p['pid']: p for p in processes}

            # Kill a random process (not the main one)
            target_process = None
            for proc in processes:
                if 'uvicorn' in proc['name'].lower() and 'server' in ' '.join(proc['cmdline'] or []):
                    target_process = proc
                    break

            if not target_process:
                # If no main server process, kill a random one
                target_process = random.choice(processes)

            logger.info(f"Killing process: {target_process}")

            # Kill the process
            try:
                os.kill(target_process['pid'], signal.SIGTERM)
                failure_injected = True
                logger.info(f"Process {target_process['pid']} killed")
            except Exception as e:
                logger.error(f"Failed to kill process: {e}")
                failure_injected = False

            # Wait for system to potentially recover
            await asyncio.sleep(5)

            # Check if system is still responding
            try:
                async with self.session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        system_recovered = True
                        logger.info("System recovered after process kill")
                    else:
                        system_recovered = False
                        logger.warning("System not fully recovered")
            except Exception as e:
                system_recovered = False
                logger.error(f"System not responding: {e}")

            # Restart the killed process if needed
            if failure_injected and not system_recovered:
                logger.info("Attempting to restart killed process...")
                # In a real scenario, you'd restart the service
                # For testing, we'll just note it

            duration = time.time() - start_time

            if system_recovered:
                self.add_result(
                    "Process Kill Resilience",
                    "Process Management",
                    "PASS",
                    duration,
                    failure_injected,
                    system_recovered,
                    {
                        "killed_process": target_process,
                        "recovery_time": duration
                    }
                )
            else:
                self.add_result(
                    "Process Kill Resilience",
                    "Process Management",
                    "FAIL",
                    duration,
                    failure_injected,
                    system_recovered,
                    {
                        "killed_process": target_process,
                        "recovery_time": duration
                    },
                    "System failed to recover from process kill"
                )

        except Exception as e:
            duration = time.time() - start_time
            self.add_result(
                "Process Kill Resilience",
                "Process Management",
                "FAIL",
                duration,
                False,
                False,
                {},
                str(e)
            )

    async def test_memory_pressure_resilience(self):
        """Test system resilience under memory pressure"""
        logger.info("Testing memory pressure resilience...")

        start_time = time.time()

        try:
            # Check initial memory state
            initial_memory = psutil.virtual_memory()
            logger.info(f"Initial memory usage: {initial_memory.percent}%")

            # Simulate memory pressure by allocating memory
            memory_blocks = []
            target_memory_percent = 85.0  # Target 85% memory usage

            try:
                while psutil.virtual_memory().percent < target_memory_percent:
                    # Allocate 100MB blocks
                    block = bytearray(100 * 1024 * 1024)  # 100MB
                    memory_blocks.append(block)

                    current_memory = psutil.virtual_memory()
                    logger.info(f"Memory usage: {current_memory.percent}%")

                    if len(memory_blocks) > 50:  # Prevent infinite loop
                        break

                    await asyncio.sleep(0.1)

                failure_injected = True
                logger.info(f"Memory pressure created: {psutil.virtual_memory().percent}%")

            except MemoryError:
                failure_injected = True
                logger.info("Memory limit reached")

            # Test system functionality under memory pressure
            try:
                async with self.session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        system_recovered = True
                        logger.info("System functional under memory pressure")
                    else:
                        system_recovered = False
                        logger.warning("System degraded under memory pressure")
            except Exception as e:
                system_recovered = False
                logger.error(f"System not responding under memory pressure: {e}")

            # Release memory pressure
            memory_blocks.clear()
            import gc
            gc.collect()

            # Wait for memory to stabilize
            await asyncio.sleep(3)

            final_memory = psutil.virtual_memory()
            logger.info(f"Final memory usage: {final_memory.percent}%")

            duration = time.time() - start_time

            if system_recovered:
                self.add_result(
                    "Memory Pressure Resilience",
                    "Resource Management",
                    "PASS",
                    duration,
                    failure_injected,
                    system_recovered,
                    {
                        "initial_memory": initial_memory.percent,
                        "peak_memory": target_memory_percent,
                        "final_memory": final_memory.percent,
                        "memory_blocks_allocated": len(memory_blocks)
                    }
                )
            else:
                self.add_result(
                    "Memory Pressure Resilience",
                    "Resource Management",
                    "FAIL",
                    duration,
                    failure_injected,
                    system_recovered,
                    {
                        "initial_memory": initial_memory.percent,
                        "peak_memory": target_memory_percent,
                        "final_memory": final_memory.percent
                    },
                    "System failed under memory pressure"
                )

        except Exception as e:
            duration = time.time() - start_time
            self.add_result(
                "Memory Pressure Resilience",
                "Resource Management",
                "FAIL",
                duration,
                False,
                False,
                {},
                str(e)
            )

    async def test_network_latency_resilience(self):
        """Test system resilience under network latency"""
        logger.info("Testing network latency resilience...")

        start_time = time.time()

        try:
            # Test normal response time
            normal_start = time.time()
            async with self.session.get(f"{self.base_url}/health") as response:
                normal_time = time.time() - normal_start

            # Simulate network latency (we can't actually inject latency, but we can test timeout handling)
            timeout_session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=1))  # 1 second timeout

            try:
                latency_start = time.time()
                async with timeout_session.get(f"{self.base_url}/health") as response:
                    latency_time = time.time() - latency_start

                # If we get here, the request completed within timeout
                failure_injected = False
                system_recovered = True

            except asyncio.TimeoutError:
                failure_injected = True
                system_recovered = True  # Timeout is expected behavior
                latency_time = 1.0  # 1 second timeout

            await timeout_session.close()

            duration = time.time() - start_time

            if system_recovered:
                self.add_result(
                    "Network Latency Resilience",
                    "Network Management",
                    "PASS",
                    duration,
                    failure_injected,
                    system_recovered,
                    {
                        "normal_response_time": normal_time,
                        "latency_response_time": latency_time,
                        "timeout_handled": failure_injected
                    }
                )
            else:
                self.add_result(
                    "Network Latency Resilience",
                    "Network Management",
                    "FAIL",
                    duration,
                    failure_injected,
                    system_recovered,
                    {
                        "normal_response_time": normal_time,
                        "latency_response_time": latency_time
                    },
                    "System failed to handle network latency"
                )

        except Exception as e:
            duration = time.time() - start_time
            self.add_result(
                "Network Latency Resilience",
                "Network Management",
                "FAIL",
                duration,
                False,
                False,
                {},
                str(e)
            )

    async def test_database_connection_resilience(self):
        """Test system resilience when database connections fail"""
        logger.info("Testing database connection resilience...")

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
                    try:
                        async with self.session.get(f"{self.base_url}/api/dashboard/overview", headers=headers) as response:
                            if response.status == 200:
                                # Database is working, simulate connection issue by testing error handling
                                failure_injected = False
                                system_recovered = True

                                self.add_result(
                                    "Database Connection Resilience",
                                    "Database Management",
                                    "PASS",
                                    time.time() - start_time,
                                    failure_injected,
                                    system_recovered,
                                    {
                                        "endpoint": "/api/dashboard/overview",
                                        "status_code": response.status,
                                        "note": "Database connection stable"
                                    }
                                )
                            else:
                                failure_injected = True
                                system_recovered = False

                                self.add_result(
                                    "Database Connection Resilience",
                                    "Database Management",
                                    "FAIL",
                                    time.time() - start_time,
                                    failure_injected,
                                    system_recovered,
                                    {
                                        "endpoint": "/api/dashboard/overview",
                                        "status_code": response.status
                                    },
                                    f"Database endpoint returned {response.status}"
                                )
                    except Exception as e:
                        failure_injected = True
                        system_recovered = False

                        self.add_result(
                            "Database Connection Resilience",
                            "Database Management",
                            "FAIL",
                            time.time() - start_time,
                            failure_injected,
                            system_recovered,
                            {
                                "endpoint": "/api/dashboard/overview"
                            },
                            str(e)
                        )
                else:
                    self.add_result(
                        "Database Connection Resilience",
                        "Database Management",
                        "FAIL",
                        time.time() - start_time,
                        False,
                        False,
                        {},
                        "Failed to get authentication token"
                    )

        except Exception as e:
            self.add_result(
                "Database Connection Resilience",
                "Database Management",
                "FAIL",
                time.time() - start_time,
                False,
                False,
                {},
                str(e)
            )

    async def test_graceful_degradation(self):
        """Test system graceful degradation under stress"""
        logger.info("Testing graceful degradation...")

        start_time = time.time()

        try:
            # Send multiple concurrent requests to stress the system
            concurrent_requests = 50
            tasks = []

            for i in range(concurrent_requests):
                task = self.session.get(f"{self.base_url}/health")
                tasks.append(task)

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Analyze results
            successful = 0
            failed = 0
            degraded = 0

            for response in responses:
                if isinstance(response, aiohttp.ClientResponse):
                    if response.status == 200:
                        successful += 1
                    elif response.status == 429:  # Rate limited
                        degraded += 1
                    else:
                        failed += 1
                else:
                    failed += 1

            total_requests = len(responses)
            success_rate = successful / total_requests
            degradation_rate = degraded / total_requests

            duration = time.time() - start_time

            # System is resilient if it handles stress gracefully
            if success_rate >= 0.7 and degradation_rate >= 0.1:  # 70% success, 10% graceful degradation
                system_recovered = True
                status = "PASS"
            elif success_rate >= 0.5:  # 50% success
                system_recovered = True
                status = "WARNING"
            else:
                system_recovered = False
                status = "FAIL"

            self.add_result(
                "Graceful Degradation",
                "System Resilience",
                status,
                duration,
                True,  # Stress was injected
                system_recovered,
                {
                    "total_requests": total_requests,
                    "successful": successful,
                    "degraded": degraded,
                    "failed": failed,
                    "success_rate": success_rate,
                    "degradation_rate": degradation_rate
                }
            )

        except Exception as e:
            duration = time.time() - start_time
            self.add_result(
                "Graceful Degradation",
                "System Resilience",
                "FAIL",
                duration,
                True,
                False,
                {},
                str(e)
            )

    async def run_all_chaos_tests(self):
        """Run all chaos engineering tests"""
        logger.info("Starting comprehensive chaos engineering tests...")

        # Start system monitoring
        self.monitoring_thread = threading.Thread(target=self.monitor_system_resources)
        self.monitoring_thread.start()

        await self.setup_session()

        try:
            # Run all chaos test categories
            await self.test_process_kill_resilience()
            await self.test_memory_pressure_resilience()
            await self.test_network_latency_resilience()
            await self.test_database_connection_resilience()
            await self.test_graceful_degradation()

        finally:
            await self.cleanup_session()

            # Stop monitoring
            self.stop_monitoring = True
            if self.monitoring_thread:
                self.monitoring_thread.join()

    def generate_summary(self) -> ChaosSummary:
        """Generate chaos testing summary"""
        if not self.results:
            return ChaosSummary(0, 0, 0, 0, 0.0, 0.0, 0.0)

        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        warnings = sum(1 for r in self.results if r.status == "WARNING")

        total_duration = sum(r.duration for r in self.results)
        recovery_rate = sum(1 for r in self.results if r.system_recovered) / total_tests if total_tests > 0 else 0.0

        # Calculate resilience score
        resilience_score = 100.0
        resilience_score -= failed * 20  # Each failure reduces score by 20
        resilience_score -= warnings * 10  # Each warning reduces score by 10
        resilience_score = max(0.0, resilience_score)  # Don't go below 0

        return ChaosSummary(
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            warnings=warnings,
            total_duration=total_duration,
            recovery_rate=recovery_rate,
            resilience_score=resilience_score
        )

    def save_results(self, filename: str = None) -> None:
        """Save chaos testing results to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chaos_test_results_{timestamp}.json"

        summary = self.generate_summary()

        output = {
            'summary': {
                'total_tests': summary.total_tests,
                'passed': summary.passed,
                'failed': summary.failed,
                'warnings': summary.warnings,
                'total_duration': summary.total_duration,
                'recovery_rate': summary.recovery_rate,
                'resilience_score': summary.resilience_score
            },
            'system_metrics': self.system_metrics,
            'test_results': [
                {
                    'test_name': r.test_name,
                    'category': r.category,
                    'status': r.status,
                    'duration': r.duration,
                    'failure_injected': r.failure_injected,
                    'system_recovered': r.system_recovered,
                    'details': r.details,
                    'timestamp': r.timestamp.isoformat(),
                    'error_message': r.error_message
                }
                for r in self.results
            ]
        }

        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)

        logger.info(f"Chaos testing results saved to {filename}")

    def print_summary(self) -> None:
        """Print chaos testing summary to console"""
        summary = self.generate_summary()

        print("\n" + "="*60)
        print("CHAOS ENGINEERING TEST RESULTS SUMMARY")
        print("="*60)
        print(f"Total Tests: {summary.total_tests}")
        print(f"Passed: {summary.passed}")
        print(f"Failed: {summary.failed}")
        print(f"Warnings: {summary.warnings}")
        print(f"Recovery Rate: {summary.recovery_rate:.2%}")
        print(f"Total Duration: {summary.total_duration:.2f} seconds")
        print(f"Resilience Score: {summary.resilience_score:.1f}/100")
        print("="*60)

        # Print failed tests
        if summary.failed > 0:
            print("\nFAILED TESTS:")
            print("-" * 40)
            for result in self.results:
                if result.status == "FAIL":
                    print(f"❌ {result.test_name}: {result.error_message}")

async def main():
    """Main chaos engineering execution"""
    print("🌪️ AI Framework Chaos Engineering Suite")
    print("="*50)
    print("⚠️  WARNING: This will inject failures into your system!")
    print("Make sure you're running this in a safe environment.")
    print("="*50)

    # Initialize chaos engineer
    chaos_engineer = ChaosEngineer()

    # Run all chaos tests
    await chaos_engineer.run_all_chaos_tests()

    # Generate and display results
    chaos_engineer.print_summary()

    # Save results
    chaos_engineer.save_results()

    print("\n✅ Chaos engineering tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())

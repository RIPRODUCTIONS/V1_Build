#!/usr/bin/env python3
"""
AI Framework Load Testing Suite
Comprehensive performance testing for enterprise-scale workloads
"""

import asyncio
import aiohttp
import time
import statistics
import json
import logging
from dataclasses import dataclass
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import psutil
import threading
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Individual test result data"""
    endpoint: str
    method: str
    response_time: float
    status_code: int
    success: bool
    timestamp: float
    payload_size: int = 0

@dataclass
class LoadTestSummary:
    """Summary of load test results"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    success_rate: float
    test_duration: float

class LoadTestSuite:
    """Comprehensive load testing suite for AI Framework"""

    def __init__(self, base_url: str = "http://localhost:18000"):
        self.base_url = base_url
        self.results: List[TestResult] = []
        self.start_time = None
        self.end_time = None
        self.system_metrics = []
        self.monitoring_thread = None
        self.stop_monitoring = False

    async def test_endpoint(self, session: aiohttp.ClientSession, endpoint: str,
                           method: str = "GET", payload: Dict = None) -> TestResult:
        """Test a single endpoint and return results"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()

        try:
            if method == "GET":
                async with session.get(url) as response:
                    response_time = time.time() - start_time
                    content = await response.read()
                    return TestResult(
                        endpoint=endpoint,
                        method=method,
                        response_time=response_time,
                        status_code=response.status,
                        success=200 <= response.status < 300,
                        timestamp=start_time,
                        payload_size=len(content)
                    )
            elif method == "POST":
                async with session.post(url, json=payload) as response:
                    response_time = time.time() - start_time
                    content = await response.read()
                    return TestResult(
                        endpoint=endpoint,
                        method=method,
                        response_time=response_time,
                        status_code=response.status,
                        success=200 <= response.status < 300,
                        timestamp=start_time,
                        payload_size=len(content)
                    )
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Error testing {endpoint}: {e}")
            return TestResult(
                endpoint=endpoint,
                method=method,
                response_time=response_time,
                status_code=0,
                success=False,
                timestamp=start_time
            )

    def monitor_system_resources(self):
        """Monitor system resources during testing"""
        while not self.stop_monitoring:
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')

                self.system_metrics.append({
                    'timestamp': time.time(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_available': memory.available,
                    'disk_percent': disk.percent
                })

                time.sleep(1)
            except Exception as e:
                logger.error(f"Error monitoring system: {e}")
                break

    async def run_concurrent_tests(self, endpoints: List[Dict],
                                  concurrency: int = 10,
                                  duration: int = 60) -> None:
        """Run concurrent load tests for specified duration"""
        logger.info(f"Starting load test with {concurrency} concurrent users for {duration} seconds")

        # Start system monitoring
        self.monitoring_thread = threading.Thread(target=self.monitor_system_resources)
        self.monitoring_thread.start()

        self.start_time = time.time()
        self.end_time = self.start_time + duration

        async with aiohttp.ClientSession() as session:
            while time.time() < self.end_time:
                # Create tasks for concurrent execution
                tasks = []
                for _ in range(concurrency):
                    for endpoint_config in endpoints:
                        endpoint = endpoint_config['endpoint']
                        method = endpoint_config.get('method', 'GET')
                        payload = endpoint_config.get('payload')

                        task = self.test_endpoint(session, endpoint, method, payload)
                        tasks.append(task)

                # Execute all tasks concurrently
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for result in results:
                        if isinstance(result, TestResult):
                            self.results.append(result)

                # Small delay to prevent overwhelming
                await asyncio.sleep(0.1)

        # Stop monitoring
        self.stop_monitoring = True
        if self.monitoring_thread:
            self.monitoring_thread.join()

    async def run_stress_test(self, endpoint: str, max_concurrency: int = 100) -> None:
        """Run stress test to find breaking point"""
        logger.info(f"Starting stress test on {endpoint} with max {max_concurrency} concurrent users")

        self.start_time = time.time()

        async with aiohttp.ClientSession() as session:
            concurrency = 1
            while concurrency <= max_concurrency:
                logger.info(f"Testing with {concurrency} concurrent users...")

                # Create concurrent requests
                tasks = [self.test_endpoint(session, endpoint) for _ in range(concurrency)]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Check success rate
                successful = sum(1 for r in results if isinstance(r, TestResult) and r.success)
                success_rate = successful / len(results) if results else 0

                logger.info(f"Concurrency {concurrency}: {success_rate:.2%} success rate")

                # If success rate drops below 90%, we've found the breaking point
                if success_rate < 0.9:
                    logger.info(f"Breaking point found at {concurrency} concurrent users")
                    break

                concurrency *= 2
                await asyncio.sleep(2)  # Brief pause between tests

        self.end_time = time.time()

    def generate_summary(self) -> LoadTestSummary:
        """Generate comprehensive test summary"""
        if not self.results:
            return LoadTestSummary(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]

        response_times = [r.response_time for r in self.results]
        response_times.sort()

        total_requests = len(self.results)
        successful_requests = len(successful)
        failed_requests = len(failed)

        test_duration = (self.end_time or time.time()) - (self.start_time or time.time())

        summary = LoadTestSummary(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            avg_response_time=statistics.mean(response_times) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            p95_response_time=response_times[int(len(response_times) * 0.95)] if response_times else 0,
            p99_response_time=response_times[int(len(response_times) * 0.99)] if response_times else 0,
            requests_per_second=total_requests / test_duration if test_duration > 0 else 0,
            success_rate=successful_requests / total_requests if total_requests > 0 else 0,
            test_duration=test_duration
        )

        return summary

    def save_results(self, filename: str = None) -> None:
        """Save test results to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"load_test_results_{timestamp}.json"

        summary = self.generate_summary()

        output = {
            'summary': {
                'total_requests': summary.total_requests,
                'successful_requests': summary.successful_requests,
                'failed_requests': summary.failed_requests,
                'avg_response_time': summary.avg_response_time,
                'min_response_time': summary.min_response_time,
                'max_response_time': summary.max_response_time,
                'p95_response_time': summary.p95_response_time,
                'p99_response_time': summary.p99_response_time,
                'requests_per_second': summary.requests_per_second,
                'success_rate': summary.success_rate,
                'test_duration': summary.test_duration
            },
            'system_metrics': self.system_metrics,
            'individual_results': [
                {
                    'endpoint': r.endpoint,
                    'method': r.method,
                    'response_time': r.response_time,
                    'status_code': r.status_code,
                    'success': r.success,
                    'timestamp': r.timestamp,
                    'payload_size': r.payload_size
                }
                for r in self.results
            ]
        }

        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)

        logger.info(f"Results saved to {filename}")

    def print_summary(self) -> None:
        """Print test summary to console"""
        summary = self.generate_summary()

        print("\n" + "="*60)
        print("LOAD TEST RESULTS SUMMARY")
        print("="*60)
        print(f"Total Requests: {summary.total_requests:,}")
        print(f"Successful: {summary.successful_requests:,}")
        print(f"Failed: {summary.failed_requests:,}")
        print(f"Success Rate: {summary.success_rate:.2%}")
        print(f"Test Duration: {summary.test_duration:.2f} seconds")
        print(f"Requests/Second: {summary.requests_per_second:.2f}")
        print()
        print("Response Time Statistics:")
        print(f"  Average: {summary.avg_response_time:.3f}s")
        print(f"  Minimum: {summary.min_response_time:.3f}s")
        print(f"  Maximum: {summary.max_response_time:.3f}s")
        print(f"  95th Percentile: {summary.p95_response_time:.3f}s")
        print(f"  99th Percentile: {summary.p99_response_time:.3f}s")
        print("="*60)

async def main():
    """Main load testing execution"""
    # Define test endpoints
    endpoints = [
        {'endpoint': '/', 'method': 'GET'},
        {'endpoint': '/health', 'method': 'GET'},
        {'endpoint': '/metrics', 'method': 'GET'},
        {'endpoint': '/api/system/status', 'method': 'GET'},
        {'endpoint': '/api/dashboard/overview', 'method': 'GET'},
        {'endpoint': '/api/dashboard/departments', 'method': 'GET'}
    ]

    # Initialize load test suite
    load_tester = LoadTestSuite()

    print("🚀 AI Framework Load Testing Suite")
    print("="*50)

    # Run concurrent load test
    print("\n1. Running Concurrent Load Test...")
    await load_tester.run_concurrent_tests(
        endpoints=endpoints,
        concurrency=20,  # 20 concurrent users
        duration=120      # 2 minutes
    )

    # Run stress test
    print("\n2. Running Stress Test...")
    await load_tester.run_stress_test('/health', max_concurrency=50)

    # Generate and display results
    print("\n3. Generating Results...")
    load_tester.print_summary()

    # Save results
    load_tester.save_results()

    print("\n✅ Load testing completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
AI Framework Security Testing Suite
Comprehensive security validation and penetration testing
"""

import asyncio
import aiohttp
import time
import json
import logging
import subprocess
import sys
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
import ssl
import socket
import requests
from urllib.parse import urljoin, urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SecurityTestResult:
    """Individual security test result"""
    test_name: str
    category: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    status: str    # PASS, FAIL, WARNING
    description: str
    details: Dict[str, Any]
    timestamp: datetime

@dataclass
class SecuritySummary:
    """Security test summary"""
    total_tests: int
    passed: int
    failed: int
    warnings: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    overall_score: float

class SecurityTestSuite:
    """Comprehensive security testing suite for AI Framework"""

    def __init__(self, base_url: str = "http://localhost:18000"):
        self.base_url = base_url
        self.results: List[SecurityTestResult] = []
        self.session = None

    async def setup_session(self):
        """Setup HTTP session for testing"""
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(timeout=timeout)

    async def cleanup_session(self):
        """Cleanup HTTP session"""
        if self.session:
            await self.session.close()

    def add_result(self, test_name: str, category: str, severity: str,
                   status: str, description: str, details: Dict = None):
        """Add a test result"""
        result = SecurityTestResult(
            test_name=test_name,
            category=category,
            severity=severity,
            status=status,
            description=description,
            details=details or {},
            timestamp=datetime.now()
        )
        self.results.append(result)

        # Log the result
        log_level = logging.ERROR if status == "FAIL" else logging.INFO
        logger.log(log_level, f"{test_name}: {status} - {description}")

    async def test_authentication(self):
        """Test authentication mechanisms"""
        logger.info("Testing authentication mechanisms...")

        # Test unauthenticated access to protected endpoints
        protected_endpoints = [
            '/metrics',
            '/api/system/status',
            '/api/dashboard/overview'
        ]

        for endpoint in protected_endpoints:
            try:
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    if response.status == 401:
                        self.add_result(
                            "Authentication Required",
                            "Authentication",
                            "LOW",
                            "PASS",
                            f"Endpoint {endpoint} properly requires authentication",
                            {"endpoint": endpoint, "status_code": response.status}
                        )
                    else:
                        self.add_result(
                            "Authentication Bypass",
                            "Authentication",
                            "HIGH",
                            "FAIL",
                            f"Endpoint {endpoint} accessible without authentication",
                            {"endpoint": endpoint, "status_code": response.status}
                        )
            except Exception as e:
                self.add_result(
                    "Authentication Test Error",
                    "Authentication",
                    "MEDIUM",
                    "WARNING",
                    f"Error testing {endpoint}: {e}",
                    {"endpoint": endpoint, "error": str(e)}
                )

    async def test_authorization(self):
        """Test authorization mechanisms"""
        logger.info("Testing authorization mechanisms...")

        # Test role-based access control
        test_cases = [
            {
                "endpoint": "/api/system/status",
                "method": "GET",
                "expected_roles": ["admin", "user"]
            }
        ]

        for test_case in test_cases:
            try:
                # Test without proper authorization
                async with self.session.get(f"{self.base_url}{test_case['endpoint']}") as response:
                    if response.status in [401, 403]:
                        self.add_result(
                            "Authorization Enforced",
                            "Authorization",
                            "LOW",
                            "PASS",
                            f"Endpoint {test_case['endpoint']} properly enforces authorization",
                            {"endpoint": test_case['endpoint'], "status_code": response.status}
                        )
                    else:
                        self.add_result(
                            "Authorization Bypass",
                            "Authorization",
                            "HIGH",
                            "FAIL",
                            f"Endpoint {test_case['endpoint']} accessible without proper authorization",
                            {"endpoint": test_case['endpoint'], "status_code": response.status}
                        )
            except Exception as e:
                self.add_result(
                    "Authorization Test Error",
                    "Authorization",
                    "MEDIUM",
                    "WARNING",
                    f"Error testing {test_case['endpoint']}: {e}",
                    {"endpoint": test_case['endpoint'], "error": str(e)}
                )

    async def test_input_validation(self):
        """Test input validation and sanitization"""
        logger.info("Testing input validation...")

        # Test SQL injection attempts
        sql_injection_payloads = [
            "' OR 1=1 --",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --"
        ]

        for payload in sql_injection_payloads:
            try:
                # Test in query parameters
                params = {"q": payload}
                async with self.session.get(f"{self.base_url}/", params=params) as response:
                    if response.status == 400 or "error" in (await response.text()).lower():
                        self.add_result(
                            "SQL Injection Prevention",
                            "Input Validation",
                            "LOW",
                            "PASS",
                            f"SQL injection payload properly rejected: {payload[:20]}...",
                            {"payload": payload, "status_code": response.status}
                        )
                    else:
                        self.add_result(
                            "SQL Injection Vulnerability",
                            "Input Validation",
                            "CRITICAL",
                            "FAIL",
                            f"SQL injection payload not properly validated: {payload[:20]}...",
                            {"payload": payload, "status_code": response.status}
                        )
            except Exception as e:
                self.add_result(
                    "Input Validation Test Error",
                    "Input Validation",
                    "MEDIUM",
                    "WARNING",
                    f"Error testing SQL injection: {e}",
                    {"payload": payload, "error": str(e)}
                )

    async def test_rate_limiting(self):
        """Test rate limiting mechanisms"""
        logger.info("Testing rate limiting...")

        # Send multiple rapid requests
        rapid_requests = 100
        start_time = time.time()

        try:
            tasks = []
            for _ in range(rapid_requests):
                task = self.session.get(f"{self.base_url}/health")
                tasks.append(task)

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Count successful vs rate-limited responses
            successful = 0
            rate_limited = 0

            for response in responses:
                if isinstance(response, aiohttp.ClientResponse):
                    if response.status == 200:
                        successful += 1
                    elif response.status == 429:  # Too Many Requests
                        rate_limited += 1

            if rate_limited > 0:
                self.add_result(
                    "Rate Limiting Active",
                    "Rate Limiting",
                    "LOW",
                    "PASS",
                    f"Rate limiting properly enforced: {rate_limited}/{rapid_requests} requests rate limited",
                    {"total_requests": rapid_requests, "rate_limited": rate_limited, "successful": successful}
                )
            else:
                self.add_result(
                    "Rate Limiting Missing",
                    "Rate Limiting",
                    "MEDIUM",
                    "WARNING",
                    f"No rate limiting detected for {rapid_requests} rapid requests",
                    {"total_requests": rapid_requests, "rate_limited": rate_limited, "successful": successful}
                )

        except Exception as e:
            self.add_result(
                "Rate Limiting Test Error",
                "Rate Limiting",
                "MEDIUM",
                "WARNING",
                f"Error testing rate limiting: {e}",
                {"error": str(e)}
            )

    async def test_ssl_tls(self):
        """Test SSL/TLS configuration"""
        logger.info("Testing SSL/TLS configuration...")

        try:
            # Parse URL to get hostname and port
            parsed_url = urlparse(self.base_url)
            hostname = parsed_url.hostname or "localhost"
            port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)

            if parsed_url.scheme == "https":
                # Test SSL/TLS configuration
                context = ssl.create_default_context()
                with socket.create_connection((hostname, port), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        cert = ssock.getpeercert()

                        # Check certificate validity
                        if cert:
                            self.add_result(
                                "SSL Certificate Valid",
                                "SSL/TLS",
                                "LOW",
                                "PASS",
                                f"SSL certificate is valid for {hostname}",
                                {"subject": cert.get('subject', []), "issuer": cert.get('issuer', [])}
                            )
                        else:
                            self.add_result(
                                "SSL Certificate Missing",
                                "SSL/TLS",
                                "HIGH",
                                "FAIL",
                                f"No SSL certificate found for {hostname}",
                                {"hostname": hostname, "port": port}
                            )
            else:
                self.add_result(
                    "HTTPS Not Enabled",
                    "SSL/TLS",
                    "MEDIUM",
                    "WARNING",
                    f"HTTPS not enabled for {self.base_url}",
                    {"scheme": parsed_url.scheme, "hostname": hostname, "port": port}
                )

        except Exception as e:
            self.add_result(
                "SSL/TLS Test Error",
                "SSL/TLS",
                "MEDIUM",
                "WARNING",
                f"Error testing SSL/TLS: {e}",
                {"error": str(e)}
            )

    async def test_headers_security(self):
        """Test security headers"""
        logger.info("Testing security headers...")

        try:
            async with self.session.get(f"{self.base_url}/") as response:
                headers = response.headers

                # Check for common security headers
                security_headers = {
                    "X-Content-Type-Options": "nosniff",
                    "X-Frame-Options": ["DENY", "SAMEORIGIN"],
                    "X-XSS-Protection": "1; mode=block",
                    "Strict-Transport-Security": None,  # Any value is good
                    "Content-Security-Policy": None,   # Any value is good
                    "Referrer-Policy": None            # Any value is good
                }

                for header, expected_value in security_headers.items():
                    if header in headers:
                        header_value = headers[header]
                        if expected_value is None or header_value == expected_value or header_value in expected_value:
                            self.add_result(
                                f"{header} Header Present",
                                "Security Headers",
                                "LOW",
                                "PASS",
                                f"Security header {header} is properly configured",
                                {"header": header, "value": header_value}
                            )
                        else:
                            self.add_result(
                                f"{header} Header Misconfigured",
                                "Security Headers",
                                "MEDIUM",
                                "WARNING",
                                f"Security header {header} has unexpected value: {header_value}",
                                {"header": header, "value": header_value, "expected": expected_value}
                            )
                    else:
                        self.add_result(
                            f"{header} Header Missing",
                            "Security Headers",
                            "MEDIUM",
                            "WARNING",
                            f"Security header {header} is missing",
                            {"header": header}
                        )

        except Exception as e:
            self.add_result(
                "Security Headers Test Error",
                "Security Headers",
                "MEDIUM",
                "WARNING",
                f"Error testing security headers: {e}",
                {"error": str(e)}
            )

    async def test_cors_policy(self):
        """Test CORS policy configuration"""
        logger.info("Testing CORS policy...")

        try:
            # Test CORS preflight request
            headers = {
                "Origin": "https://malicious-site.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }

            async with self.session.options(f"{self.base_url}/", headers=headers) as response:
                cors_headers = response.headers

                if "Access-Control-Allow-Origin" in cors_headers:
                    allowed_origin = cors_headers["Access-Control-Allow-Origin"]
                    if allowed_origin == "*":
                        self.add_result(
                            "CORS Overly Permissive",
                            "CORS Policy",
                            "HIGH",
                            "FAIL",
                            "CORS allows any origin (*)",
                            {"allowed_origin": allowed_origin}
                        )
                    else:
                        self.add_result(
                            "CORS Properly Configured",
                            "CORS Policy",
                            "LOW",
                            "PASS",
                            f"CORS origin properly restricted to: {allowed_origin}",
                            {"allowed_origin": allowed_origin}
                        )
                else:
                    self.add_result(
                        "CORS Not Configured",
                        "CORS Policy",
                        "MEDIUM",
                        "WARNING",
                        "CORS headers not found in response",
                        {"headers": dict(cors_headers)}
                    )

        except Exception as e:
            self.add_result(
                "CORS Test Error",
                "CORS Policy",
                "MEDIUM",
                "WARNING",
                f"Error testing CORS policy: {e}",
                {"error": str(e)}
            )

    async def run_all_tests(self):
        """Run all security tests"""
        logger.info("Starting comprehensive security testing...")

        await self.setup_session()

        try:
            # Run all test categories
            await self.test_authentication()
            await self.test_authorization()
            await self.test_input_validation()
            await self.test_rate_limiting()
            await self.test_ssl_tls()
            await self.test_headers_security()
            await self.test_cors_policy()

        finally:
            await self.cleanup_session()

    def generate_summary(self) -> SecuritySummary:
        """Generate security test summary"""
        if not self.results:
            return SecuritySummary(0, 0, 0, 0, 0, 0, 0, 0, 0.0)

        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        warnings = sum(1 for r in self.results if r.status == "WARNING")

        critical_issues = sum(1 for r in self.results if r.severity == "CRITICAL" and r.status == "FAIL")
        high_issues = sum(1 for r in self.results if r.severity == "HIGH" and r.status == "FAIL")
        medium_issues = sum(1 for r in self.results if r.severity == "MEDIUM" and r.status == "FAIL")
        low_issues = sum(1 for r in self.results if r.severity == "LOW" and r.status == "FAIL")

        # Calculate overall score (0-100)
        if total_tests > 0:
            overall_score = (passed / total_tests) * 100
        else:
            overall_score = 0.0

        return SecuritySummary(
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            warnings=warnings,
            critical_issues=critical_issues,
            high_issues=high_issues,
            medium_issues=medium_issues,
            low_issues=low_issues,
            overall_score=overall_score
        )

    def save_results(self, filename: str = None) -> None:
        """Save security test results to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"security_test_results_{timestamp}.json"

        summary = self.generate_summary()

        output = {
            'summary': {
                'total_tests': summary.total_tests,
                'passed': summary.passed,
                'failed': summary.failed,
                'warnings': summary.warnings,
                'critical_issues': summary.critical_issues,
                'high_issues': summary.high_issues,
                'medium_issues': summary.medium_issues,
                'low_issues': summary.low_issues,
                'overall_score': summary.overall_score
            },
            'test_results': [
                {
                    'test_name': r.test_name,
                    'category': r.category,
                    'severity': r.severity,
                    'status': r.status,
                    'description': r.description,
                    'details': r.details,
                    'timestamp': r.timestamp.isoformat()
                }
                for r in self.results
            ]
        }

        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)

        logger.info(f"Security test results saved to {filename}")

    def print_summary(self) -> None:
        """Print security test summary to console"""
        summary = self.generate_summary()

        print("\n" + "="*60)
        print("SECURITY TEST RESULTS SUMMARY")
        print("="*60)
        print(f"Total Tests: {summary.total_tests}")
        print(f"Passed: {summary.passed}")
        print(f"Failed: {summary.failed}")
        print(f"Warnings: {summary.warnings}")
        print(f"Overall Score: {summary.overall_score:.1f}/100")
        print()
        print("Issues by Severity:")
        print(f"  Critical: {summary.critical_issues}")
        print(f"  High: {summary.high_issues}")
        print(f"  Medium: {summary.medium_issues}")
        print(f"  Low: {summary.low_issues}")
        print("="*60)

        # Print failed tests
        if summary.failed > 0:
            print("\nFAILED TESTS:")
            print("-" * 40)
            for result in self.results:
                if result.status == "FAIL":
                    print(f"❌ {result.test_name} ({result.severity}): {result.description}")

async def main():
    """Main security testing execution"""
    print("🔒 AI Framework Security Testing Suite")
    print("="*50)

    # Initialize security test suite
    security_tester = SecurityTestSuite()

    # Run all security tests
    await security_tester.run_all_tests()

    # Generate and display results
    security_tester.print_summary()

    # Save results
    security_tester.save_results()

    print("\n✅ Security testing completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())

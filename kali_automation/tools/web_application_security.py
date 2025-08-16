#!/usr/bin/env python3
"""
Web Application Security Tools for Kali Linux Automation.

This module provides automated web application security testing capabilities
using various tools available in Kali Linux.
"""

import asyncio
import json
import logging
import subprocess
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class WebSecurityError(Exception):
    """Base exception for web application security operations."""
    pass


class ScanError(WebSecurityError):
    """Exception raised when web security scanning fails."""
    pass


class ReportError(WebSecurityError):
    """Exception raised when report generation fails."""
    pass


class ConfigurationError(WebSecurityError):
    """Exception raised when tool configuration is invalid."""
    pass


class BaseWebSecurityTool(ABC):
    """Base class for all web application security tools."""

    def __init__(self, name: str, description: str, category: str):
        self.name = name
        self.description = description
        self.category = category
        self.required_packages = []
        self.optional_packages = []
        self.config = {}
        self.scan_profiles = {}
        self.output_formats = []

    @abstractmethod
    async def execute(self, target: str, options: dict[str, Any]) -> dict[str, Any]:
        """Execute the web security testing tool."""
        pass

    def validate_target(self, target: str) -> bool:
        """Validate target URL format."""
        try:
            result = urlparse(target)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    def validate_options(self, options: dict[str, Any]) -> bool:
        """Validate scan options."""
        return isinstance(options, dict)

    def get_help(self) -> str:
        """Get tool help information."""
        return f"{self.name}: {self.description}"

    def check_dependencies(self) -> bool:
        """Check if required packages are installed."""
        for package in self.required_packages:
            try:
                subprocess.run([package, '--version'],
                             capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.warning(f"Required package {package} not found")
                return False
        return True

    def get_scan_profiles(self) -> dict[str, str]:
        """Get available scan profiles."""
        return self.scan_profiles.copy()

    def get_output_formats(self) -> list[str]:
        """Get supported output formats."""
        return self.output_formats.copy()


class OWASPZAPAutomation(BaseWebSecurityTool):
    """Automated OWASP ZAP web application security testing."""

    def __init__(self):
        super().__init__(
            name="zap",
            description="OWASP ZAP web application security scanner",
            category="web_application_security"
        )
        self.required_packages = ["zaproxy"]
        self.scan_profiles = {
            "quick": "Quick scan with basic checks",
            "full": "Full scan with all checks",
            "passive": "Passive scan only",
            "active": "Active scan with spidering",
            "api": "API security testing"
        }
        self.output_formats = ["xml", "html", "json", "md"]
        self.zap_api_url = "http://localhost:8080"

    async def execute(self, target: str, options: dict[str, Any]) -> dict[str, Any]:
        """Execute OWASP ZAP security scan."""
        if not self.validate_target(target):
            return {"error": "Invalid target URL"}

        if not self.validate_options(options):
            return {"error": "Invalid options"}

        if not self.check_dependencies():
            return {"error": "OWASP ZAP not available"}

        scan_profile = options.get("scan_profile", "quick")
        output_format = options.get("output_format", "xml")
        max_duration = options.get("max_duration", 3600)  # 1 hour default

        try:
            # Start ZAP daemon
            await self._start_zap_daemon()

            # Create new context
            context_id = await self._create_context(target)

            # Configure scan settings
            await self._configure_scan_settings(context_id, scan_profile)

            # Start spidering
            spider_results = await self._spider_target(target, context_id)

            # Start active scanning
            scan_results = await self._active_scan(target, context_id, max_duration)

            # Generate report
            report = await self._generate_report(target, context_id, output_format)

            # Clean up
            await self._cleanup_context(context_id)

            return {
                "success": True,
                "target": target,
                "scan_profile": scan_profile,
                "spider_results": spider_results,
                "scan_results": scan_results,
                "report": report,
                "timestamp": datetime.now(UTC).isoformat()
            }

        except Exception as e:
            logger.error(f"OWASP ZAP scan failed: {e}")
            return {"success": False, "error": str(e)}

    async def _start_zap_daemon(self):
        """Start ZAP daemon process."""
        try:
            # Start ZAP daemon in background
            cmd = [
                "zaproxy", "--daemon", "--port", "8080",
                "--host", "0.0.0.0", "--api-key", "kali_automation"
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait for ZAP to start
            await asyncio.sleep(10)

            # Test if ZAP is running
            test_cmd = ["curl", "-s", f"{self.zap_api_url}/JSON/core/view/version"]
            result = subprocess.run(test_cmd, check=False, capture_output=True, text=True)

            if result.returncode != 0:
                raise ScanError("Failed to start ZAP daemon")

        except Exception as e:
            raise ScanError(f"Failed to start ZAP daemon: {e}")

    async def _create_context(self, target: str) -> str:
        """Create new ZAP context for the target."""
        try:
            domain = urlparse(target).netloc

            cmd = [
                "curl", "-s", "-X", "POST",
                f"{self.zap_api_url}/JSON/context/action/newContext",
                "-d", f"contextName=AutoScan_{domain}"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            response = json.loads(result.stdout)

            if "contextId" in response:
                return response["contextId"]
            else:
                # Get context ID by name
                cmd = [
                    "curl", "-s", f"{self.zap_api_url}/JSON/context/view/contextList"
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                contexts = json.loads(result.stdout)

                for context in contexts["contexts"]:
                    if context["name"] == f"AutoScan_{domain}":
                        return context["id"]

                raise ScanError("Failed to create ZAP context")

        except Exception as e:
            raise ScanError(f"Failed to create ZAP context: {e}")

    async def _configure_scan_settings(self, context_id: str, scan_profile: str):
        """Configure scan settings based on profile."""
        try:
            if scan_profile == "full":
                # Enable all scan policies
                cmd = [
                    "curl", "-s", "-X", "POST",
                    f"{self.zap_api_url}/JSON/pscan/action/enableAllScanners"
                ]
                subprocess.run(cmd, capture_output=True, check=True)

                cmd = [
                    "curl", "-s", "-X", "POST",
                    f"{self.zap_api_url}/JSON/ascan/action/enableAllScanners"
                ]
                subprocess.run(cmd, capture_output=True, check=True)

            elif scan_profile == "passive":
                # Enable only passive scanners
                cmd = [
                    "curl", "-s", "-X", "POST",
                    f"{self.zap_api_url}/JSON/pscan/action/enableAllScanners"
                ]
                subprocess.run(cmd, capture_output=True, check=True)

                cmd = [
                    "curl", "-s", "-X", "POST",
                    f"{self.zap_api_url}/JSON/ascan/action/disableAllScanners"
                ]
                subprocess.run(cmd, capture_output=True, check=True)

        except Exception as e:
            logger.warning(f"Failed to configure scan settings: {e}")

    async def _spider_target(self, target: str, context_id: str) -> dict[str, Any]:
        """Spider the target website to discover URLs."""
        try:
            cmd = [
                "curl", "-s", "-X", "POST",
                f"{self.zap_api_url}/JSON/spider/action/scan",
                "-d", f"url={target}&contextId={context_id}&maxChildren=50"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            response = json.loads(result.stdout)

            if "scan" in response:
                scan_id = response["scan"]

                # Monitor spider progress
                spider_results = await self._monitor_spider(scan_id)
                return spider_results
            else:
                raise ScanError("Failed to start spider scan")

        except Exception as e:
            raise ScanError(f"Failed to spider target: {e}")

    async def _monitor_spider(self, scan_id: str) -> dict[str, Any]:
        """Monitor spider scan progress."""
        try:
            max_wait_time = 1800  # 30 minutes max
            wait_interval = 10  # Check every 10 seconds
            elapsed_time = 0

            while elapsed_time < max_wait_time:
                cmd = [
                    "curl", "-s", f"{self.zap_api_url}/JSON/spider/view/status?scanId={scan_id}"
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                response = json.loads(result.stdout)

                if "status" in response:
                    status = response["status"]

                    if status == "100":
                        # Get spider results
                        return await self._get_spider_results(scan_id)
                    elif status == "-1":
                        raise ScanError("Spider scan failed")

                await asyncio.sleep(wait_interval)
                elapsed_time += wait_interval

            raise ScanError("Spider scan timeout")

        except Exception as e:
            raise ScanError(f"Failed to monitor spider: {e}")

    async def _get_spider_results(self, scan_id: str) -> dict[str, Any]:
        """Get spider scan results."""
        try:
            cmd = [
                "curl", "-s", f"{self.zap_api_url}/JSON/spider/view/results?scanId={scan_id}"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            response = json.loads(result.stdout)

            return {
                "scan_id": scan_id,
                "urls_found": len(response.get("results", [])),
                "results": response.get("results", []),
                "status": "completed"
            }

        except Exception as e:
            raise ScanError(f"Failed to get spider results: {e}")

    async def _active_scan(self, target: str, context_id: str, max_duration: int) -> dict[str, Any]:
        """Perform active security scanning."""
        try:
            cmd = [
                "curl", "-s", "-X", "POST",
                f"{self.zap_api_url}/JSON/ascan/action/scan",
                "-d", f"url={target}&contextId={context_id}&scanPolicyName=Default Policy"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            response = json.loads(result.stdout)

            if "scan" in response:
                scan_id = response["scan"]

                # Monitor active scan progress
                scan_results = await self._monitor_active_scan(scan_id, max_duration)
                return scan_results
            else:
                raise ScanError("Failed to start active scan")

        except Exception as e:
            raise ScanError(f"Failed to start active scan: {e}")

    async def _monitor_active_scan(self, scan_id: str, max_duration: int) -> dict[str, Any]:
        """Monitor active scan progress."""
        try:
            wait_interval = 30  # Check every 30 seconds
            elapsed_time = 0

            while elapsed_time < max_duration:
                cmd = [
                    "curl", "-s", f"{self.zap_api_url}/JSON/ascan/view/status?scanId={scan_id}"
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                response = json.loads(result.stdout)

                if "status" in response:
                    status = response["status"]

                    if status == "100":
                        # Get scan results
                        return await self._get_active_scan_results(scan_id)
                    elif status == "-1":
                        raise ScanError("Active scan failed")

                await asyncio.sleep(wait_interval)
                elapsed_time += wait_interval

            raise ScanError("Active scan timeout")

        except Exception as e:
            raise ScanError(f"Failed to monitor active scan: {e}")

    async def _get_active_scan_results(self, scan_id: str) -> dict[str, Any]:
        """Get active scan results."""
        try:
            # Get alerts
            cmd = [
                "curl", "-s", f"{self.zap_api_url}/JSON/core/view/alerts"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            alerts = json.loads(result.stdout)

            # Get scan progress
            cmd = [
                "curl", "-s", f"{self.zap_api_url}/JSON/ascan/view/scanProgress?scanId={scan_id}"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            progress = json.loads(result.stdout)

            return {
                "scan_id": scan_id,
                "alerts": alerts.get("alerts", []),
                "progress": progress,
                "status": "completed"
            }

        except Exception as e:
            raise ScanError(f"Failed to get active scan results: {e}")

    async def _generate_report(self, target: str, context_id: str, output_format: str) -> dict[str, Any]:
        """Generate security scan report."""
        try:
            # Generate report using ZAP API
            cmd = [
                "curl", "-s", "-X", "POST",
                f"{self.zap_api_url}/JSON/reports/action/generate",
                "-d", f"title=Security_Scan_{urlparse(target).netloc}&template=traditional-html&theme=dark&description=Automated security scan&contexts={context_id}&sites={target}&reportFileName=zap_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html&reportDir=/tmp"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            response = json.loads(result.stdout)

            if "report" in response:
                report_path = response["report"]

                # Read report content
                with open(report_path) as f:
                    report_content = f.read()

                return {
                    "format": output_format,
                    "file_path": report_path,
                    "content": report_content,
                    "timestamp": datetime.now(UTC).isoformat()
                }
            else:
                raise ReportError("Failed to generate ZAP report")

        except Exception as e:
            raise ReportError(f"Failed to generate report: {e}")

    async def _cleanup_context(self, context_id: str):
        """Clean up ZAP context."""
        try:
            cmd = [
                "curl", "-s", "-X", "POST",
                f"{self.zap_api_url}/JSON/context/action/removeContext",
                "-d", f"contextId={context_id}"
            ]

            subprocess.run(cmd, capture_output=True, check=True)

        except Exception as e:
            logger.warning(f"Failed to cleanup context: {e}")


class NiktoAutomation(BaseWebSecurityTool):
    """Automated Nikto web server security scanner."""

    def __init__(self):
        super().__init__(
            name="nikto",
            description="Web server security scanner",
            category="web_application_security"
        )
        self.required_packages = ["nikto"]
        self.scan_profiles = {
            "basic": "Basic scan with common checks",
            "full": "Full scan with all plugins",
            "malware": "Malware detection scan",
            "cgi": "CGI script testing",
            "ssl": "SSL/TLS security testing"
        }
        self.output_formats = ["txt", "xml", "csv", "html"]

    async def execute(self, target: str, options: dict[str, Any]) -> dict[str, Any]:
        """Execute Nikto security scan."""
        if not self.validate_target(target):
            return {"error": "Invalid target URL"}

        if not self.validate_options(options):
            return {"error": "Invalid options"}

        if not self.check_dependencies():
            return {"error": "Nikto not available"}

        scan_profile = options.get("scan_profile", "basic")
        output_format = options.get("output_format", "txt")
        port = options.get("port")

        try:
            # Build Nikto command
            output_file = f"nikto_{urlparse(target).netloc}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            cmd = ["nikto", "-h", target]

            # Add profile-specific options
            if scan_profile == "full":
                cmd.extend(["-C", "all"])
            elif scan_profile == "malware":
                cmd.extend(["-C", "malware"])
            elif scan_profile == "cgi":
                cmd.extend(["-C", "cgi"])
            elif scan_profile == "ssl":
                cmd.extend(["-ssl"])

            # Add port if specified
            if port:
                cmd.extend(["-p", str(port)])

            # Add output format
            if output_format == "xml":
                cmd.extend(["-Format", "xml", "-o", f"{output_file}.xml"])
            elif output_format == "csv":
                cmd.extend(["-Format", "csv", "-o", f"{output_file}.csv"])
            elif output_format == "html":
                cmd.extend(["-Format", "htm", "-o", f"{output_file}.html"])
            else:
                cmd.extend(["-o", f"{output_file}.txt"])

            # Add additional options
            cmd.extend(["-Tuning", "123457890abcx", "-timeout", "10"])

            logger.info(f"Executing Nikto scan: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                # Parse results
                scan_results = await self._parse_nikto_results(stdout.decode(), output_file, output_format)

                return {
                    "success": True,
                    "target": target,
                    "scan_profile": scan_profile,
                    "scan_results": scan_results,
                    "output_file": f"{output_file}.{output_format}",
                    "command": " ".join(cmd),
                    "timestamp": datetime.now(UTC).isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": stderr.decode(),
                    "command": " ".join(cmd)
                }

        except Exception as e:
            logger.error(f"Nikto scan failed: {e}")
            return {"success": False, "error": str(e)}

    async def _parse_nikto_results(self, output: str, output_file: str, output_format: str) -> dict[str, Any]:
        """Parse Nikto scan results."""
        try:
            results = {
                "vulnerabilities": [],
                "summary": {
                    "total_issues": 0,
                    "high_risk": 0,
                    "medium_risk": 0,
                    "low_risk": 0
                },
                "server_info": {},
                "scan_details": {}
            }

            lines = output.split('\n')

            for line in lines:
                line = line.strip()

                if not line:
                    continue

                # Extract server information
                if "Server:" in line:
                    results["server_info"]["server"] = line.split("Server:")[1].strip()
                elif "OSVDB-" in line:
                    # Extract vulnerability information
                    vuln_info = self._extract_vulnerability_info(line)
                    if vuln_info:
                        results["vulnerabilities"].append(vuln_info)
                        results["summary"]["total_issues"] += 1

                        # Categorize by risk level
                        if "high" in vuln_info.get("risk", "").lower():
                            results["summary"]["high_risk"] += 1
                        elif "medium" in vuln_info.get("risk", "").lower():
                            results["summary"]["medium_risk"] += 1
                        else:
                            results["summary"]["low_risk"] += 1

            return results

        except Exception as e:
            logger.error(f"Failed to parse Nikto results: {e}")
            return {"error": f"Failed to parse results: {e}"}

    def _extract_vulnerability_info(self, line: str) -> dict[str, Any] | None:
        """Extract vulnerability information from Nikto output line."""
        try:
            # Parse OSVDB line format
            if "OSVDB-" in line:
                parts = line.split()

                vuln_info = {
                    "osvdb_id": "",
                    "description": "",
                    "risk": "low",
                    "details": line
                }

                for part in parts:
                    if part.startswith("OSVDB-"):
                        vuln_info["osvdb_id"] = part
                    elif "high" in part.lower():
                        vuln_info["risk"] = "high"
                    elif "medium" in part.lower():
                        vuln_info["risk"] = "medium"

                # Extract description
                if ":" in line:
                    description = line.split(":", 1)[1].strip()
                    vuln_info["description"] = description

                return vuln_info

            return None

        except Exception:
            return None


class BurpSuiteAutomation(BaseWebSecurityTool):
    """Automated Burp Suite web application security testing."""

    def __init__(self):
        super().__init__(
            name="burpsuite",
            description="Professional web application security testing platform",
            category="web_application_security"
        )
        self.required_packages = ["burpsuite"]
        self.scan_profiles = {
            "crawl": "Crawl and audit",
            "audit": "Audit only",
            "full": "Full scan with all checks",
            "api": "API security testing",
            "mobile": "Mobile application testing"
        }
        self.output_formats = ["xml", "html", "json"]

    async def execute(self, target: str, options: dict[str, Any]) -> dict[str, Any]:
        """Execute Burp Suite security scan."""
        if not self.validate_target(target):
            return {"error": "Invalid target URL"}

        if not self.validate_options(options):
            return {"error": "Invalid options"}

        if not self.check_dependencies():
            return {"error": "Burp Suite not available"}

        scan_profile = options.get("scan_profile", "crawl")
        output_format = options.get("output_format", "xml")

        try:
            # Create Burp project
            project_file = f"burp_project_{urlparse(target).netloc}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.burp"

            # Start Burp Suite in headless mode
            cmd = [
                "burpsuite", "--unpause-spider-and-scanner",
                "--project-file", project_file,
                "--config-file", "/tmp/burp_config.json"
            ]

            # Create configuration file
            config = self._create_burp_config(target, scan_profile)
            with open("/tmp/burp_config.json", "w") as f:
                json.dump(config, f)

            logger.info(f"Executing Burp Suite scan: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait for Burp to start and complete scan
            await asyncio.sleep(300)  # 5 minutes for basic scan

            # Stop Burp process
            process.terminate()
            await process.wait()

            # Generate report
            report = await self._generate_burp_report(project_file, output_format)

            return {
                "success": True,
                "target": target,
                "scan_profile": scan_profile,
                "project_file": project_file,
                "report": report,
                "command": " ".join(cmd),
                "timestamp": datetime.now(UTC).isoformat()
            }

        except Exception as e:
            logger.error(f"Burp Suite scan failed: {e}")
            return {"success": False, "error": str(e)}

    def _create_burp_config(self, target: str, scan_profile: str) -> dict[str, Any]:
        """Create Burp Suite configuration."""
        return {
            "project_options": {
                "connections": {
                    "upstream_proxy": {
                        "use_user_options": False
                    }
                }
            },
            "spider": {
                "request_headers": {
                    "User-Agent": "Kali Automation Spider"
                },
                "check_robots_txt": True,
                "process_forms": True
            },
            "scanner": {
                "scan_definition": {
                    "urls": [target],
                    "exclude_urls": []
                },
                "scan_issues": {
                    "include_passive": True,
                    "include_active": scan_profile != "crawl"
                }
            }
        }

    async def _generate_burp_report(self, project_file: str, output_format: str) -> dict[str, Any]:
        """Generate Burp Suite scan report."""
        try:
            # Use Burp command line to generate report
            output_file = f"burp_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            cmd = [
                "burpsuite", "--project-file", project_file,
                "--report", output_format, "--output", output_file
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return {
                    "format": output_format,
                    "output_file": f"{output_file}.{output_format}",
                    "timestamp": datetime.now(UTC).isoformat()
                }
            else:
                raise ReportError(f"Failed to generate Burp report: {stderr.decode()}")

        except Exception as e:
            raise ReportError(f"Failed to generate Burp report: {e}")


class WebApplicationSecurityTools:
    """Manager class for web application security tools."""

    def __init__(self):
        self.tools = {
            "zap": OWASPZAPAutomation(),
            "nikto": NiktoAutomation(),
            "burpsuite": BurpSuiteAutomation()
        }

    def get_available_tools(self) -> list[str]:
        """Get list of available web security tools."""
        return list(self.tools.keys())

    def get_tool_info(self, tool_name: str) -> dict[str, Any] | None:
        """Get information about a specific tool."""
        if tool_name in self.tools:
            tool = self.tools[tool_name]
            return {
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "scan_profiles": tool.get_scan_profiles(),
                "output_formats": tool.get_output_formats()
            }
        return None

    async def execute_web_security_scan(self, tool_name: str, target: str,
                                      options: dict[str, Any]) -> dict[str, Any]:
        """Execute web security scan with specified tool."""
        if tool_name not in self.tools:
            return {"error": f"Tool {tool_name} not available"}

        tool = self.tools[tool_name]
        return await tool.execute(target, options)

    async def execute_comprehensive_web_security_assessment(self, target: str,
                                                          options: dict[str, Any]) -> dict[str, Any]:
        """Execute comprehensive web security assessment using multiple tools."""
        results = {}
        failed_tools = []

        for tool_name, tool in self.tools.items():
            try:
                logger.info(f"Executing {tool_name} web security scan on {target}")
                result = await tool.execute(target, options)
                results[tool_name] = result

                if not result.get("success", False):
                    failed_tools.append(tool_name)

            except Exception as e:
                logger.error(f"Tool {tool_name} failed: {e}")
                results[tool_name] = {"success": False, "error": str(e)}
                failed_tools.append(tool_name)

        # Generate comprehensive report
        comprehensive_report = self._generate_comprehensive_report(results, target)

        return {
            "success": len(failed_tools) == 0,
            "target": target,
            "tool_results": results,
            "failed_tools": failed_tools,
            "comprehensive_report": comprehensive_report,
            "timestamp": datetime.now(UTC).isoformat()
        }

    def _generate_comprehensive_report(self, results: dict[str, Any], target: str) -> dict[str, Any]:
        """Generate comprehensive web security assessment report."""
        total_vulnerabilities = 0
        high_risk_vulnerabilities = 0
        medium_risk_vulnerabilities = 0
        low_risk_vulnerabilities = 0

        # Aggregate vulnerability counts
        for tool_name, result in results.items():
            if result.get("success", False):
                scan_results = result.get("scan_results", {})

                if "vulnerabilities" in scan_results:
                    vulns = scan_results["vulnerabilities"]
                    total_vulnerabilities += len(vulns)

                    # Categorize by risk level
                    for vuln in vulns:
                        risk = vuln.get("risk", "").lower()
                        if "high" in risk:
                            high_risk_vulnerabilities += 1
                        elif "medium" in risk:
                            medium_risk_vulnerabilities += 1
                        else:
                            low_risk_vulnerabilities += 1

        return {
            "target": target,
            "summary": {
                "total_vulnerabilities": total_vulnerabilities,
                "high_risk_vulnerabilities": high_risk_vulnerabilities,
                "medium_risk_vulnerabilities": medium_risk_vulnerabilities,
                "low_risk_vulnerabilities": low_risk_vulnerabilities
            },
            "risk_assessment": self._assess_web_security_risk(high_risk_vulnerabilities,
                                                            medium_risk_vulnerabilities),
            "recommendations": self._generate_web_security_recommendations(high_risk_vulnerabilities,
                                                                        medium_risk_vulnerabilities),
            "generated_at": datetime.now(UTC).isoformat()
        }

    def _assess_web_security_risk(self, high: int, medium: int) -> str:
        """Assess web security risk level."""
        if high > 5:
            return "CRITICAL"
        elif high > 0:
            return "HIGH"
        elif medium > 10:
            return "MEDIUM"
        elif medium > 0:
            return "LOW"
        else:
            return "MINIMAL"

    def _generate_web_security_recommendations(self, high: int, medium: int) -> list[str]:
        """Generate web security recommendations."""
        recommendations = []

        if high > 0:
            recommendations.append("Immediate action required: High-risk vulnerabilities detected")
            recommendations.append("Implement web application firewall (WAF)")
            recommendations.append("Review and fix authentication mechanisms")

        if medium > 0:
            recommendations.append("Address medium-risk vulnerabilities within 1 week")
            recommendations.append("Implement input validation and sanitization")
            recommendations.append("Enable security headers (HSTS, CSP, etc.)")

        recommendations.append("Implement secure coding practices")
        recommendations.append("Regular security testing and code reviews")
        recommendations.append("Keep web applications and frameworks updated")

        return recommendations


# Example usage and testing
async def main():
    """Example usage of web application security tools."""
    tools = WebApplicationSecurityTools()

    # Get available tools
    print("Available tools:", tools.get_available_tools())

    # Execute single tool scan
    result = await tools.execute_web_security_scan(
        "nikto",
        "https://example.com",
        {"scan_profile": "basic", "output_format": "txt"}
    )
    print("Single tool result:", result)

    # Execute comprehensive assessment
    comprehensive = await tools.execute_comprehensive_web_security_assessment(
        "https://example.com",
        {"scan_profile": "basic", "output_format": "xml"}
    )
    print("Comprehensive assessment:", comprehensive)


if __name__ == "__main__":
    asyncio.run(main())

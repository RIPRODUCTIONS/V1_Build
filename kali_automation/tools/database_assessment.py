#!/usr/bin/env python3
"""
Database Assessment Tools for Kali Linux Automation.

This module provides automated database security testing capabilities
using various tools available in Kali Linux.
"""

import asyncio
import logging
import re
import subprocess
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class DatabaseAssessmentError(Exception):
    """Base exception for database assessment operations."""
    pass


class ScanError(DatabaseAssessmentError):
    """Exception raised when database scanning fails."""
    pass


class ReportError(DatabaseAssessmentError):
    """Exception raised when report generation fails."""
    pass


class ConfigurationError(DatabaseAssessmentError):
    """Exception raised when tool configuration is invalid."""
    pass


class BaseDatabaseTool(ABC):
    """Base class for all database assessment tools."""

    def __init__(self, name: str, description: str, category: str):
        self.name = name
        self.description = description
        self.category = category
        self.required_packages = []
        self.optional_packages = []
        self.config = {}
        self.scan_profiles = {}
        self.output_formats = []
        self.supported_databases = []

    @abstractmethod
    async def execute(self, target: str, options: dict[str, Any]) -> dict[str, Any]:
        """Execute the database assessment tool."""
        pass

    def validate_target(self, target: str) -> bool:
        """Validate target format."""
        return bool(target and len(target.strip()) > 0)

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

    def get_supported_databases(self) -> list[str]:
        """Get supported database types."""
        return self.supported_databases.copy()


class SQLMapAutomation(BaseDatabaseTool):
    """Automated SQLMap SQL injection testing."""

    def __init__(self):
        super().__init__(
            name="sqlmap",
            description="Automated SQL injection and database takeover tool",
            category="database_assessment"
        )
        self.required_packages = ["sqlmap"]
        self.scan_profiles = {
            "basic": "Basic SQL injection detection",
            "full": "Full database enumeration and takeover",
            "blind": "Blind SQL injection testing",
            "time": "Time-based SQL injection testing",
            "union": "Union-based SQL injection testing",
            "error": "Error-based SQL injection testing"
        }
        self.output_formats = ["txt", "csv", "html", "xml", "json"]
        self.supported_databases = ["mysql", "postgresql", "oracle", "sqlserver", "sqlite", "access", "firebird", "sybase", "sap", "maxdb", "db2", "hsqldb", "informix", "ingres", "frontbase", "prestosql"]

    async def execute(self, target: str, options: dict[str, Any]) -> dict[str, Any]:
        """Execute SQLMap security scan."""
        if not self.validate_target(target):
            return {"error": "Invalid target"}

        if not self.validate_options(options):
            return {"error": "Invalid options"}

        if not self.check_dependencies():
            return {"error": "SQLMap not available"}

        scan_profile = options.get("scan_profile", "basic")
        output_format = options.get("output_format", "txt")
        database_type = options.get("database_type")
        risk_level = options.get("risk_level", 1)
        thread_level = options.get("thread_level", 1)

        try:
            # Build SQLMap command
            output_file = f"sqlmap_{urlparse(target).netloc.replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            cmd = ["sqlmap", "-u", target, "--batch", "--random-agent"]

            # Add profile-specific options
            if scan_profile == "full":
                cmd.extend(["--dbs", "--tables", "--dump", "--schema", "--count"])
            elif scan_profile == "blind":
                cmd.extend(["--technique=B", "--time-sec=10"])
            elif scan_profile == "time":
                cmd.extend(["--technique=T", "--time-sec=10"])
            elif scan_profile == "union":
                cmd.extend(["--technique=U"])
            elif scan_profile == "error":
                cmd.extend(["--technique=E"])

            # Add database type if specified
            if database_type and database_type in self.supported_databases:
                cmd.extend(["--dbms", database_type])

            # Add risk and thread levels
            cmd.extend(["--risk", str(risk_level), "--threads", str(thread_level)])

            # Add output format
            if output_format == "csv":
                cmd.extend(["--output-dir", "/tmp", "--csv-del", ","])
            elif output_format == "html":
                cmd.extend(["--output-dir", "/tmp", "--html"])
            elif output_format == "xml":
                cmd.extend(["--output-dir", "/tmp", "--xml"])
            elif output_format == "json":
                cmd.extend(["--output-dir", "/tmp", "--json"])
            else:
                cmd.extend(["--output-dir", "/tmp"])

            # Add additional options for better results
            cmd.extend(["--level", "5", "--timeout", "30", "--retries", "3"])

            logger.info(f"Executing SQLMap scan: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                # Parse results
                scan_results = await self._parse_sqlmap_results(stdout.decode(), stderr.decode(), output_file, output_format)

                return {
                    "success": True,
                    "target": target,
                    "scan_profile": scan_profile,
                    "scan_results": scan_results,
                    "output_file": output_file,
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
            logger.error(f"SQLMap scan failed: {e}")
            return {"success": False, "error": str(e)}

    async def _parse_sqlmap_results(self, stdout: str, stderr: str, output_file: str, output_format: str) -> dict[str, Any]:
        """Parse SQLMap scan results."""
        try:
            results = {
                "injections_found": [],
                "databases": [],
                "tables": [],
                "columns": [],
                "data_dumped": [],
                "summary": {
                    "total_injections": 0,
                    "databases_found": 0,
                    "tables_found": 0,
                    "columns_found": 0,
                    "data_records": 0
                },
                "scan_details": {}
            }

            # Parse stdout for injection points and results
            lines = stdout.split('\n')

            for line in lines:
                line = line.strip()

                if not line:
                    continue

                # Extract injection information
                if "injectable" in line.lower():
                    injection_info = self._extract_injection_info(line)
                    if injection_info:
                        results["injections_found"].append(injection_info)
                        results["summary"]["total_injections"] += 1

                # Extract database information
                elif "available databases" in line.lower():
                    db_info = self._extract_database_info(line)
                    if db_info:
                        results["databases"].append(db_info)
                        results["summary"]["databases_found"] += 1

                # Extract table information
                elif "available tables" in line.lower():
                    table_info = self._extract_table_info(line)
                    if table_info:
                        results["tables"].append(table_info)
                        results["summary"]["tables_found"] += 1

            # Parse stderr for additional information
            stderr_lines = stderr.split('\n')
            for line in stderr_lines:
                line = line.strip()

                if not line:
                    continue

                # Extract additional scan details
                if "technique" in line.lower():
                    results["scan_details"]["technique"] = line

            return results

        except Exception as e:
            logger.error(f"Failed to parse SQLMap results: {e}")
            return {"error": f"Failed to parse results: {e}"}

    def _extract_injection_info(self, line: str) -> dict[str, Any] | None:
        """Extract SQL injection information from line."""
        try:
            # Parse injection point information
            if "injectable" in line.lower():
                parts = line.split()

                injection_info = {
                    "parameter": "",
                    "type": "",
                    "title": "",
                    "payload": "",
                    "details": line
                }

                # Extract parameter name
                for i, part in enumerate(parts):
                    if "parameter:" in part.lower():
                        if i + 1 < len(parts):
                            injection_info["parameter"] = parts[i + 1]
                        break

                # Extract injection type
                if "boolean-based" in line.lower():
                    injection_info["type"] = "boolean-based"
                elif "time-based" in line.lower():
                    injection_info["type"] = "time-based"
                elif "union-based" in line.lower():
                    injection_info["type"] = "union-based"
                elif "error-based" in line.lower():
                    injection_info["type"] = "error-based"

                return injection_info

            return None

        except Exception:
            return None

    def _extract_database_info(self, line: str) -> dict[str, Any] | None:
        """Extract database information from line."""
        try:
            if "available databases" in line.lower():
                # Extract database names
                db_names = re.findall(r'\[(.*?)\]', line)
                return {
                    "databases": db_names,
                    "count": len(db_names)
                }
            return None

        except Exception:
            return None

    def _extract_table_info(self, line: str) -> dict[str, Any] | None:
        """Extract table information from line."""
        try:
            if "available tables" in line.lower():
                # Extract table names
                table_names = re.findall(r'\[(.*?)\]', line)
                return {
                    "tables": table_names,
                    "count": len(table_names)
                }
            return None

        except Exception:
            return None


class SQLNinjaAutomation(BaseDatabaseTool):
    """Automated SQLNinja SQL injection testing."""

    def __init__(self):
        super().__init__(
            name="sqlninja",
            description="SQL Server injection and takeover tool",
            category="database_assessment"
        )
        self.required_packages = ["sqlninja"]
        self.scan_profiles = {
            "basic": "Basic SQL injection detection",
            "fingerprint": "Database fingerprinting",
            "escalation": "Privilege escalation",
            "backdoor": "Backdoor installation",
            "shell": "Command shell access"
        }
        self.output_formats = ["txt", "log"]
        self.supported_databases = ["mssql", "sqlserver"]

    async def execute(self, target: str, options: dict[str, Any]) -> dict[str, Any]:
        """Execute SQLNinja security scan."""
        if not self.validate_target(target):
            return {"error": "Invalid target"}

        if not self.validate_options(options):
            return {"error": "Invalid options"}

        if not self.check_dependencies():
            return {"error": "SQLNinja not available"}

        scan_profile = options.get("scan_profile", "basic")
        output_format = options.get("output_format", "txt")
        port = options.get("port", 1433)

        try:
            # Build SQLNinja command
            output_file = f"sqlninja_{urlparse(target).netloc.replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            cmd = ["sqlninja", "-m", target, "-p", str(port)]

            # Add profile-specific options
            if scan_profile == "fingerprint":
                cmd.extend(["-f"])
            elif scan_profile == "escalation":
                cmd.extend(["-e"])
            elif scan_profile == "backdoor":
                cmd.extend(["-b"])
            elif scan_profile == "shell":
                cmd.extend(["-s"])

            # Add output options
            cmd.extend(["-o", f"{output_file}.{output_format}"])

            logger.info(f"Executing SQLNinja scan: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                # Parse results
                scan_results = await self._parse_sqlninja_results(stdout.decode(), stderr.decode(), output_file, output_format)

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
            logger.error(f"SQLNinja scan failed: {e}")
            return {"success": False, "error": str(e)}

    async def _parse_sqlninja_results(self, stdout: str, stderr: str, output_file: str, output_format: str) -> dict[str, Any]:
        """Parse SQLNinja scan results."""
        try:
            results = {
                "injections_found": [],
                "database_info": {},
                "privilege_info": {},
                "scan_details": {},
                "summary": {
                    "total_injections": 0,
                    "databases_found": 0,
                    "privileges_escalated": False
                }
            }

            # Parse stdout for injection results
            lines = stdout.split('\n')

            for line in lines:
                line = line.strip()

                if not line:
                    continue

                # Extract injection information
                if "injection" in line.lower():
                    injection_info = self._extract_sqlninja_injection_info(line)
                    if injection_info:
                        results["injections_found"].append(injection_info)
                        results["summary"]["total_injections"] += 1

                # Extract database information
                elif "database" in line.lower():
                    db_info = self._extract_sqlninja_db_info(line)
                    if db_info:
                        results["database_info"].update(db_info)
                        results["summary"]["databases_found"] += 1

            # Parse stderr for additional information
            stderr_lines = stderr.split('\n')
            for line in stderr_lines:
                line = line.strip()

                if not line:
                    continue

                # Extract scan details
                if "error" in line.lower() or "warning" in line.lower():
                    results["scan_details"]["errors"] = results["scan_details"].get("errors", []) + [line]

            return results

        except Exception as e:
            logger.error(f"Failed to parse SQLNinja results: {e}")
            return {"error": f"Failed to parse results: {e}"}

    def _extract_sqlninja_injection_info(self, line: str) -> dict[str, Any] | None:
        """Extract SQLNinja injection information from line."""
        try:
            if "injection" in line.lower():
                return {
                    "type": "sql_injection",
                    "details": line,
                    "timestamp": datetime.now(UTC).isoformat()
                }
            return None

        except Exception:
            return None

    def _extract_sqlninja_db_info(self, line: str) -> dict[str, Any] | None:
        """Extract SQLNinja database information from line."""
        try:
            if "database" in line.lower():
                return {
                    "database_info": line,
                    "timestamp": datetime.now(UTC).isoformat()
                }
            return None

        except Exception:
            return None


class NoSQLMapAutomation(BaseDatabaseTool):
    """Automated NoSQLMap NoSQL injection testing."""

    def __init__(self):
        super().__init__(
            name="nosqlmap",
            description="NoSQL injection and database takeover tool",
            category="database_assessment"
        )
        self.required_packages = ["nosqlmap"]
        self.scan_profiles = {
            "basic": "Basic NoSQL injection detection",
            "full": "Full database enumeration",
            "authentication": "Authentication bypass testing",
            "data_extraction": "Data extraction testing"
        }
        self.output_formats = ["txt", "json"]
        self.supported_databases = ["mongodb", "couchdb", "redis", "cassandra", "hbase", "neo4j"]

    async def execute(self, target: str, options: dict[str, Any]) -> dict[str, Any]:
        """Execute NoSQLMap security scan."""
        if not self.validate_target(target):
            return {"error": "Invalid target"}

        if not self.validate_options(options):
            return {"error": "Invalid options"}

        if not self.check_dependencies():
            return {"error": "NoSQLMap not available"}

        scan_profile = options.get("scan_profile", "basic")
        output_format = options.get("output_format", "txt")
        database_type = options.get("database_type", "mongodb")

        try:
            # Build NoSQLMap command
            output_file = f"nosqlmap_{urlparse(target).netloc.replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            cmd = ["nosqlmap", "-u", target, "--batch"]

            # Add profile-specific options
            if scan_profile == "full":
                cmd.extend(["--dbs", "--tables", "--dump"])
            elif scan_profile == "authentication":
                cmd.extend(["--auth-bypass"])
            elif scan_profile == "data_extraction":
                cmd.extend(["--extract"])

            # Add database type
            if database_type in self.supported_databases:
                cmd.extend(["--dbms", database_type])

            # Add output options
            if output_format == "json":
                cmd.extend(["--output", f"{output_file}.json"])
            else:
                cmd.extend(["--output", f"{output_file}.txt"])

            logger.info(f"Executing NoSQLMap scan: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                # Parse results
                scan_results = await self._parse_nosqlmap_results(stdout.decode(), stderr.decode(), output_file, output_format)

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
            logger.error(f"NoSQLMap scan failed: {e}")
            return {"success": False, "error": str(e)}

    async def _parse_nosqlmap_results(self, stdout: str, stderr: str, output_file: str, output_format: str) -> dict[str, Any]:
        """Parse NoSQLMap scan results."""
        try:
            results = {
                "injections_found": [],
                "databases": [],
                "collections": [],
                "scan_details": {},
                "summary": {
                    "total_injections": 0,
                    "databases_found": 0,
                    "collections_found": 0
                }
            }

            # Parse stdout for injection results
            lines = stdout.split('\n')

            for line in lines:
                line = line.strip()

                if not line:
                    continue

                # Extract injection information
                if "injection" in line.lower():
                    injection_info = self._extract_nosqlmap_injection_info(line)
                    if injection_info:
                        results["injections_found"].append(injection_info)
                        results["summary"]["total_injections"] += 1

                # Extract database information
                elif "database" in line.lower():
                    db_info = self._extract_nosqlmap_db_info(line)
                    if db_info:
                        results["databases"].append(db_info)
                        results["summary"]["databases_found"] += 1

            return results

        except Exception as e:
            logger.error(f"Failed to parse NoSQLMap results: {e}")
            return {"error": f"Failed to parse results: {e}"}

    def _extract_nosqlmap_injection_info(self, line: str) -> dict[str, Any] | None:
        """Extract NoSQLMap injection information from line."""
        try:
            if "injection" in line.lower():
                return {
                    "type": "nosql_injection",
                    "details": line,
                    "timestamp": datetime.now(UTC).isoformat()
                }
            return None

        except Exception:
            return None

    def _extract_nosqlmap_db_info(self, line: str) -> dict[str, Any] | None:
        """Extract NoSQLMap database information from line."""
        try:
            if "database" in line.lower():
                return {
                    "database_info": line,
                    "timestamp": datetime.now(UTC).isoformat()
                }
            return None

        except Exception:
            return None


class DatabaseAssessmentTools:
    """Manager class for database assessment tools."""

    def __init__(self):
        self.tools = {
            "sqlmap": SQLMapAutomation(),
            "sqlninja": SQLNinjaAutomation(),
            "nosqlmap": NoSQLMapAutomation()
        }

    def get_available_tools(self) -> list[str]:
        """Get list of available database assessment tools."""
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
                "output_formats": tool.get_output_formats(),
                "supported_databases": tool.get_supported_databases()
            }
        return None

    async def execute_database_assessment(self, tool_name: str, target: str,
                                        options: dict[str, Any]) -> dict[str, Any]:
        """Execute database assessment with specified tool."""
        if tool_name not in self.tools:
            return {"error": f"Tool {tool_name} not available"}

        tool = self.tools[tool_name]
        return await tool.execute(target, options)

    async def execute_comprehensive_database_assessment(self, target: str,
                                                      options: dict[str, Any]) -> dict[str, Any]:
        """Execute comprehensive database assessment using multiple tools."""
        results = {}
        failed_tools = []

        for tool_name, tool in self.tools.items():
            try:
                logger.info(f"Executing {tool_name} database assessment on {target}")
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
        """Generate comprehensive database assessment report."""
        total_injections = 0
        databases_found = 0
        tables_found = 0
        data_records = 0

        # Aggregate results
        for tool_name, result in results.items():
            if result.get("success", False):
                scan_results = result.get("scan_results", {})

                if "summary" in scan_results:
                    summary = scan_results["summary"]
                    total_injections += summary.get("total_injections", 0)
                    databases_found += summary.get("databases_found", 0)
                    tables_found += summary.get("tables_found", 0)
                    data_records += summary.get("data_records", 0)

        return {
            "target": target,
            "summary": {
                "total_injections": total_injections,
                "databases_found": databases_found,
                "tables_found": tables_found,
                "data_records": data_records
            },
            "risk_assessment": self._assess_database_security_risk(total_injections, databases_found),
            "recommendations": self._generate_database_security_recommendations(total_injections, databases_found),
            "generated_at": datetime.now(UTC).isoformat()
        }

    def _assess_database_security_risk(self, injections: int, databases: int) -> str:
        """Assess database security risk level."""
        if injections > 5:
            return "CRITICAL"
        elif injections > 0:
            return "HIGH"
        elif databases > 0:
            return "MEDIUM"
        else:
            return "MINIMAL"

    def _generate_database_security_recommendations(self, injections: int, databases: int) -> list[str]:
        """Generate database security recommendations."""
        recommendations = []

        if injections > 0:
            recommendations.append("Immediate action required: SQL injection vulnerabilities detected")
            recommendations.append("Implement parameterized queries and prepared statements")
            recommendations.append("Use input validation and sanitization")
            recommendations.append("Implement web application firewall (WAF)")

        if databases > 0:
            recommendations.append("Review database access controls and permissions")
            recommendations.append("Implement least privilege principle")
            recommendations.append("Enable database auditing and logging")

        recommendations.append("Regular security testing and vulnerability assessments")
        recommendations.append("Keep database systems and applications updated")
        recommendations.append("Implement secure coding practices")
        recommendations.append("Use encryption for sensitive data")

        return recommendations


# Example usage and testing
async def main():
    """Example usage of database assessment tools."""
    tools = DatabaseAssessmentTools()

    # Get available tools
    print("Available tools:", tools.get_available_tools())

    # Execute single tool scan
    result = await tools.execute_database_assessment(
        "sqlmap",
        "http://example.com/page.php?id=1",
        {"scan_profile": "basic", "output_format": "txt"}
    )
    print("Single tool result:", result)

    # Execute comprehensive assessment
    comprehensive = await tools.execute_comprehensive_database_assessment(
        "http://example.com/page.php?id=1",
        {"scan_profile": "basic", "output_format": "txt"}
    )
    print("Comprehensive assessment:", comprehensive)


if __name__ == "__main__":
    asyncio.run(main())

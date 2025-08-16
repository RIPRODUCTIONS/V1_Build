#!/usr/bin/env python3
"""
Password Attack Tools for Kali Linux Automation.

This module provides automated password cracking and brute force capabilities
using various tools available in Kali Linux.
"""

import asyncio
import logging
import re
import subprocess
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class PasswordAttackError(Exception):
    """Base exception for password attack operations."""
    pass


class CrackingError(PasswordAttackError):
    """Exception raised when password cracking fails."""
    pass


class HashError(PasswordAttackError):
    """Exception raised when hash operations fail."""
    pass


class ConfigurationError(PasswordAttackError):
    """Exception raised when tool configuration is invalid."""
    pass


class BasePasswordTool(ABC):
    """Base class for all password attack tools."""

    def __init__(self, name: str, description: str, category: str):
        self.name = name
        self.description = description
        self.category = category
        self.required_packages = []
        self.optional_packages = []
        self.config = {}
        self.attack_modes = {}
        self.output_formats = []
        self.supported_hash_types = []

    @abstractmethod
    async def execute(self, target: str, options: dict[str, Any]) -> dict[str, Any]:
        """Execute the password attack tool."""
        pass

    def validate_target(self, target: str) -> bool:
        """Validate target format."""
        return bool(target and len(target.strip()) > 0)

    def validate_options(self, options: dict[str, Any]) -> bool:
        """Validate attack options."""
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

    def get_attack_modes(self) -> dict[str, str]:
        """Get available attack modes."""
        return self.attack_modes.copy()

    def get_output_formats(self) -> list[str]:
        """Get supported output formats."""
        return self.output_formats.copy()

    def get_supported_hash_types(self) -> list[str]:
        """Get supported hash types."""
        return self.supported_hash_types.copy()


class JohnTheRipperAutomation(BasePasswordTool):
    """Automated John the Ripper password cracking."""

    def __init__(self):
        super().__init__(
            name="john",
            description="Fast password cracker for various hash types",
            category="password_attacks"
        )
        self.required_packages = ["john"]
        self.attack_modes = {
            "wordlist": "Dictionary-based attack",
            "incremental": "Incremental brute force attack",
            "mask": "Mask-based attack",
            "single": "Single crack mode",
            "external": "External mode with custom rules"
        }
        self.output_formats = ["txt", "pot", "show"]
        self.supported_hash_types = ["md5", "sha1", "sha256", "sha512", "ntlm", "lm", "bcrypt", "sha256crypt", "sha512crypt", "md5crypt", "des"]

    async def execute(self, target: str, options: dict[str, Any]) -> dict[str, Any]:
        """Execute John the Ripper password cracking."""
        if not self.validate_target(target):
            return {"error": "Invalid target"}

        if not self.validate_options(options):
            return {"error": "Invalid options"}

        if not self.check_dependencies():
            return {"error": "John the Ripper not available"}

        attack_mode = options.get("attack_mode", "wordlist")
        wordlist = options.get("wordlist", "/usr/share/wordlists/rockyou.txt")
        hash_file = options.get("hash_file")
        hash_string = options.get("hash_string")
        output_format = options.get("output_format", "txt")

        try:
            # Create hash file if hash string provided
            if hash_string and not hash_file:
                hash_file = await self._create_hash_file(hash_string)
            elif not hash_file:
                return {"error": "Either hash_file or hash_string must be provided"}

            # Build John command
            output_file = f"john_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            cmd = ["john", "--format=auto", hash_file]

            # Add attack mode specific options
            if attack_mode == "wordlist":
                if Path(wordlist).exists():
                    cmd.extend(["--wordlist", wordlist])
                else:
                    logger.warning(f"Wordlist {wordlist} not found, using default")
            elif attack_mode == "incremental":
                cmd.extend(["--incremental"])
            elif attack_mode == "mask":
                mask = options.get("mask", "?a?a?a?a?a?a?a?a")
                cmd.extend(["--mask", mask])
            elif attack_mode == "single":
                cmd.extend(["--single"])
            elif attack_mode == "external":
                rules_file = options.get("rules_file", "/etc/john/john.conf")
                if Path(rules_file).exists():
                    cmd.extend(["--rules", rules_file])

            # Add output options
            cmd.extend(["--pot", f"{output_file}.pot", "--show"])

            # Add performance options
            cmd.extend(["--fork", "4", "--memory", "4096"])

            logger.info(f"Executing John the Ripper: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                # Parse results
                crack_results = await self._parse_john_results(stdout.decode(), stderr.decode(), output_file)

                return {
                    "success": True,
                    "target": target,
                    "attack_mode": attack_mode,
                    "crack_results": crack_results,
                    "output_files": {
                        "pot": f"{output_file}.pot",
                        "show": f"{output_file}.show"
                    },
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
            logger.error(f"John the Ripper attack failed: {e}")
            return {"success": False, "error": str(e)}

    async def _create_hash_file(self, hash_string: str) -> str:
        """Create a temporary hash file from hash string."""
        try:
            hash_file = f"/tmp/hash_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

            with open(hash_file, 'w') as f:
                f.write(hash_string + '\n')

            return hash_file

        except Exception as e:
            raise HashError(f"Failed to create hash file: {e}")

    async def _parse_john_results(self, stdout: str, stderr: str, output_file: str) -> dict[str, Any]:
        """Parse John the Ripper results."""
        try:
            results = {
                "cracked_passwords": [],
                "hash_types": [],
                "performance_stats": {},
                "summary": {
                    "total_hashes": 0,
                    "cracked_hashes": 0,
                    "success_rate": 0.0
                }
            }

            # Parse stdout for cracked passwords
            lines = stdout.split('\n')

            for line in lines:
                line = line.strip()

                if not line:
                    continue

                # Extract cracked password information
                if ":" in line and not line.startswith("#"):
                    password_info = self._extract_password_info(line)
                    if password_info:
                        results["cracked_passwords"].append(password_info)
                        results["summary"]["cracked_hashes"] += 1

                # Extract hash type information
                elif "Loaded" in line and "password hash" in line:
                    hash_type = self._extract_hash_type(line)
                    if hash_type:
                        results["hash_types"].append(hash_type)

            # Parse stderr for performance information
            stderr_lines = stderr.split('\n')
            for line in stderr_lines:
                line = line.strip()

                if not line:
                    continue

                # Extract performance stats
                if "c/s" in line:
                    performance = self._extract_performance_stats(line)
                    if performance:
                        results["performance_stats"].update(performance)

            # Calculate success rate
            if results["summary"]["total_hashes"] > 0:
                results["summary"]["success_rate"] = (
                    results["summary"]["cracked_hashes"] /
                    results["summary"]["total_hashes"]
                ) * 100

            return results

        except Exception as e:
            logger.error(f"Failed to parse John results: {e}")
            return {"error": f"Failed to parse results: {e}"}

    def _extract_password_info(self, line: str) -> dict[str, Any] | None:
        """Extract password information from John output line."""
        try:
            if ":" in line:
                parts = line.split(":")

                if len(parts) >= 2:
                    return {
                        "username": parts[0],
                        "password": parts[1],
                        "hash": parts[2] if len(parts) > 2 else "",
                        "timestamp": datetime.now(UTC).isoformat()
                    }

            return None

        except Exception:
            return None

    def _extract_hash_type(self, line: str) -> str | None:
        """Extract hash type from John output line."""
        try:
            if "Loaded" in line and "password hash" in line:
                # Extract hash type from line like "Loaded 1 password hash (md5crypt)"
                match = re.search(r'\(([^)]+)\)', line)
                if match:
                    return match.group(1)

            return None

        except Exception:
            return None

    def _extract_performance_stats(self, line: str) -> dict[str, Any] | None:
        """Extract performance statistics from John output line."""
        try:
            if "c/s" in line:
                # Extract current speed
                match = re.search(r'(\d+(?:\.\d+)?)\s*c/s', line)
                if match:
                    return {"current_speed": float(match.group(1))}

            return None

        except Exception:
            return None


class HashcatAutomation(BasePasswordTool):
    """Automated Hashcat password cracking."""

    def __init__(self):
        super().__init__(
            name="hashcat",
            description="Advanced password recovery utility",
            category="password_attacks"
        )
        self.required_packages = ["hashcat"]
        self.attack_modes = {
            "wordlist": "Dictionary-based attack (0)",
            "combinator": "Combinator attack (1)",
            "mask": "Mask-based attack (3)",
            "hybrid_wordlist_mask": "Hybrid wordlist + mask (6)",
            "hybrid_mask_wordlist": "Hybrid mask + wordlist (7)",
            "rule": "Rule-based attack (0 with rules)"
        }
        self.output_formats = ["txt", "pot", "out"]
        self.supported_hash_types = ["md5", "sha1", "sha256", "sha512", "ntlm", "lm", "bcrypt", "sha256crypt", "sha512crypt", "md5crypt", "des", "raw-md5", "raw-sha1", "raw-sha256", "raw-sha512"]

    async def execute(self, target: str, options: dict[str, Any]) -> dict[str, Any]:
        """Execute Hashcat password cracking."""
        if not self.validate_target(target):
            return {"error": "Invalid target"}

        if not self.validate_options(options):
            return {"error": "Invalid options"}

        if not self.check_dependencies():
            return {"error": "Hashcat not available"}

        attack_mode = options.get("attack_mode", "wordlist")
        hash_type = options.get("hash_type", "0")  # Auto-detect
        wordlist = options.get("wordlist", "/usr/share/wordlists/rockyou.txt")
        hash_file = options.get("hash_file")
        hash_string = options.get("hash_string")
        output_format = options.get("output_format", "txt")
        device = options.get("device", "1,2,3")  # GPU devices

        try:
            # Create hash file if hash string provided
            if hash_string and not hash_file:
                hash_file = await self._create_hashcat_hash_file(hash_string)
            elif not hash_file:
                return {"error": "Either hash_file or hash_string must be provided"}

            # Build Hashcat command
            output_file = f"hashcat_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            cmd = ["hashcat", "-m", str(hash_type), hash_file]

            # Add attack mode
            if attack_mode == "wordlist":
                cmd.extend(["-a", "0"])
                if Path(wordlist).exists():
                    cmd.extend([wordlist])
                else:
                    logger.warning(f"Wordlist {wordlist} not found, using default")
            elif attack_mode == "combinator":
                cmd.extend(["-a", "1"])
                wordlist1 = options.get("wordlist1", wordlist)
                wordlist2 = options.get("wordlist2", wordlist)
                cmd.extend([wordlist1, wordlist2])
            elif attack_mode == "mask":
                cmd.extend(["-a", "3"])
                mask = options.get("mask", "?a?a?a?a?a?a?a?a")
                cmd.extend([mask])
            elif attack_mode == "hybrid_wordlist_mask":
                cmd.extend(["-a", "6"])
                if Path(wordlist).exists():
                    cmd.extend([wordlist])
                mask = options.get("mask", "?a?a?a?a")
                cmd.extend([mask])
            elif attack_mode == "hybrid_mask_wordlist":
                cmd.extend(["-a", "7"])
                mask = options.get("mask", "?a?a?a?a")
                cmd.extend([mask])
                if Path(wordlist).exists():
                    cmd.extend([wordlist])
            elif attack_mode == "rule":
                cmd.extend(["-a", "0"])
                if Path(wordlist).exists():
                    cmd.extend([wordlist])
                rules_file = options.get("rules_file", "/usr/share/hashcat/rules/best64.rule")
                if Path(rules_file).exists():
                    cmd.extend(["-r", rules_file])

            # Add output options
            cmd.extend(["-o", f"{output_file}.{output_format}"])

            # Add performance options
            cmd.extend(["-d", device, "-w", "3"])  # Workload profile

            # Add additional options
            cmd.extend(["--force", "--status", "--status-timer", "10"])

            logger.info(f"Executing Hashcat: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                # Parse results
                crack_results = await self._parse_hashcat_results(stdout.decode(), stderr.decode(), output_file, output_format)

                return {
                    "success": True,
                    "target": target,
                    "attack_mode": attack_mode,
                    "crack_results": crack_results,
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
            logger.error(f"Hashcat attack failed: {e}")
            return {"success": False, "error": str(e)}

    async def _create_hashcat_hash_file(self, hash_string: str) -> str:
        """Create a temporary hash file for Hashcat."""
        try:
            hash_file = f"/tmp/hashcat_hash_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

            with open(hash_file, 'w') as f:
                f.write(hash_string + '\n')

            return hash_file

        except Exception as e:
            raise HashError(f"Failed to create hash file: {e}")

    async def _parse_hashcat_results(self, stdout: str, stderr: str, output_file: str, output_format: str) -> dict[str, Any]:
        """Parse Hashcat results."""
        try:
            results = {
                "cracked_passwords": [],
                "hash_types": [],
                "performance_stats": {},
                "summary": {
                    "total_hashes": 0,
                    "cracked_hashes": 0,
                    "success_rate": 0.0
                }
            }

            # Parse stdout for results
            lines = stdout.split('\n')

            for line in lines:
                line = line.strip()

                if not line:
                    continue

                # Extract hash type information
                if "Hash.Mode" in line:
                    hash_type = self._extract_hashcat_hash_type(line)
                    if hash_type:
                        results["hash_types"].append(hash_type)

            # Parse stderr for performance and results
            stderr_lines = stderr.split('\n')
            for line in stderr_lines:
                line = line.strip()

                if not line:
                    continue

                # Extract performance stats
                if "Speed.#1" in line:
                    performance = self._extract_hashcat_performance(line)
                    if performance:
                        results["performance_stats"].update(performance)

                # Extract status information
                elif "Recovered" in line:
                    status = self._extract_hashcat_status(line)
                    if status:
                        results["summary"].update(status)

            return results

        except Exception as e:
            logger.error(f"Failed to parse Hashcat results: {e}")
            return {"error": f"Failed to parse results: {e}"}

    def _extract_hashcat_hash_type(self, line: str) -> str | None:
        """Extract hash type from Hashcat output line."""
        try:
            if "Hash.Mode" in line:
                # Extract hash mode from line like "Hash.Mode........: 0 (MD5)"
                match = re.search(r'Hash\.Mode[^:]*:\s*(\d+)\s*\(([^)]+)\)', line)
                if match:
                    return f"{match.group(1)} ({match.group(2)})"

            return None

        except Exception:
            return None

    def _extract_hashcat_performance(self, line: str) -> dict[str, Any] | None:
        """Extract performance statistics from Hashcat output line."""
        try:
            if "Speed.#1" in line:
                # Extract speed from line like "Speed.#1.........: 12345.6 MH/s"
                match = re.search(r'Speed\.#1[^:]*:\s*([\d.]+)\s*([KMGT]?H/s)', line)
                if match:
                    return {"speed": f"{match.group(1)} {match.group(2)}"}

            return None

        except Exception:
            return None

    def _extract_hashcat_status(self, line: str) -> dict[str, Any] | None:
        """Extract status information from Hashcat output line."""
        try:
            if "Recovered" in line:
                # Extract recovery stats from line like "Recovered........: 1/1 (100.00%) Digests"
                match = re.search(r'Recovered[^:]*:\s*(\d+)/(\d+)\s*\(([\d.]+)%\)', line)
                if match:
                    return {
                        "cracked_hashes": int(match.group(1)),
                        "total_hashes": int(match.group(2)),
                        "success_rate": float(match.group(3))
                    }

            return None

        except Exception:
            return None


class HydraAutomation(BasePasswordTool):
    """Automated Hydra network service brute force."""

    def __init__(self):
        super().__init__(
            name="hydra",
            description="Network logon cracker for various services",
            category="password_attacks"
        )
        self.required_packages = ["hydra"]
        self.attack_modes = {
            "wordlist": "Dictionary-based attack",
            "combinator": "Username/password combination attack",
            "incremental": "Incremental brute force attack"
        }
        self.output_formats = ["txt", "json"]
        self.supported_services = ["ssh", "ftp", "telnet", "http", "https", "smb", "rdp", "vnc", "pop3", "imap", "smtp", "mysql", "postgresql", "oracle", "mssql"]

    async def execute(self, target: str, options: dict[str, Any]) -> dict[str, Any]:
        """Execute Hydra brute force attack."""
        if not self.validate_target(target):
            return {"error": "Invalid target"}

        if not self.validate_options(options):
            return {"error": "Invalid options"}

        if not self.check_dependencies():
            return {"error": "Hydra not available"}

        attack_mode = options.get("attack_mode", "wordlist")
        service = options.get("service", "ssh")
        username = options.get("username", "admin")
        wordlist = options.get("wordlist", "/usr/share/wordlists/rockyou.txt")
        port = options.get("port")
        output_format = options.get("output_format", "txt")

        try:
            # Build Hydra command
            output_file = f"hydra_{urlparse(target).netloc.replace('.', '_')}_{service}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            cmd = ["hydra"]

            # Add target and service
            if port:
                cmd.extend(["-s", str(port)])

            cmd.extend([target, service])

            # Add attack mode specific options
            if attack_mode == "wordlist":
                if Path(wordlist).exists():
                    cmd.extend(["-P", wordlist])
                else:
                    logger.warning(f"Wordlist {wordlist} not found, using default")

                if username:
                    cmd.extend(["-l", username])
                else:
                    cmd.extend(["-L", "/usr/share/wordlists/usernames.txt"])

            elif attack_mode == "combinator":
                username_list = options.get("username_list", "/usr/share/wordlists/usernames.txt")
                password_list = options.get("password_list", wordlist)

                if Path(username_list).exists() and Path(password_list).exists():
                    cmd.extend(["-L", username_list, "-P", password_list])
                else:
                    logger.warning("Username or password list not found, using default")

            elif attack_mode == "incremental":
                cmd.extend(["-x", "1:8:a1"])  # 1-8 character alphanumeric

            # Add output options
            if output_format == "json":
                cmd.extend(["-o", f"{output_file}.json", "-f"])
            else:
                cmd.extend(["-o", f"{output_file}.txt", "-f"])

            # Add performance options
            cmd.extend(["-t", "4", "-W", "3"])  # Threads and wait time

            logger.info(f"Executing Hydra: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                # Parse results
                attack_results = await self._parse_hydra_results(stdout.decode(), stderr.decode(), output_file, output_format)

                return {
                    "success": True,
                    "target": target,
                    "service": service,
                    "attack_mode": attack_mode,
                    "attack_results": attack_results,
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
            logger.error(f"Hydra attack failed: {e}")
            return {"success": False, "error": str(e)}

    async def _parse_hydra_results(self, stdout: str, stderr: str, output_file: str, output_format: str) -> dict[str, Any]:
        """Parse Hydra results."""
        try:
            results = {
                "credentials_found": [],
                "services_tested": [],
                "performance_stats": {},
                "summary": {
                    "total_attempts": 0,
                    "successful_logins": 0,
                    "success_rate": 0.0
                }
            }

            # Parse stdout for results
            lines = stdout.split('\n')

            for line in lines:
                line = line.strip()

                if not line:
                    continue

                # Extract successful login information
                if "login:" in line.lower() and "password:" in line.lower():
                    credential_info = self._extract_credential_info(line)
                    if credential_info:
                        results["credentials_found"].append(credential_info)
                        results["summary"]["successful_logins"] += 1

            # Parse stderr for additional information
            stderr_lines = stderr.split('\n')
            for line in stderr_lines:
                line = line.strip()

                if not line:
                    continue

                # Extract performance stats
                if "attempts" in line.lower():
                    attempts = self._extract_attempts_info(line)
                    if attempts:
                        results["summary"]["total_attempts"] = attempts

            # Calculate success rate
            if results["summary"]["total_attempts"] > 0:
                results["summary"]["success_rate"] = (
                    results["summary"]["successful_logins"] /
                    results["summary"]["total_attempts"]
                ) * 100

            return results

        except Exception as e:
            logger.error(f"Failed to parse Hydra results: {e}")
            return {"error": f"Failed to parse results: {e}"}

    def _extract_credential_info(self, line: str) -> dict[str, Any] | None:
        """Extract credential information from Hydra output line."""
        try:
            if "login:" in line.lower() and "password:" in line.lower():
                # Parse line like "[22][ssh] host: 192.168.1.1   login: admin   password: password123"
                parts = line.split()

                credential_info = {
                    "service": "",
                    "host": "",
                    "username": "",
                    "password": "",
                    "timestamp": datetime.now(UTC).isoformat()
                }

                for i, part in enumerate(parts):
                    if part == "login:" and i + 1 < len(parts):
                        credential_info["username"] = parts[i + 1]
                    elif part == "password:" and i + 1 < len(parts):
                        credential_info["password"] = parts[i + 1]
                    elif "[" in part and "]" in part:
                        credential_info["service"] = part.strip("[]")
                    elif "." in part and part.count(".") == 3:
                        credential_info["host"] = part

                return credential_info

            return None

        except Exception:
            return None

    def _extract_attempts_info(self, line: str) -> int | None:
        """Extract attempts information from Hydra output line."""
        try:
            if "attempts" in line.lower():
                # Extract number from line like "1 of 1 target completed, 1 valid password found"
                match = re.search(r'(\d+)\s+of\s+(\d+)\s+target', line)
                if match:
                    return int(match.group(2))

            return None

        except Exception:
            return None


class PasswordAttackTools:
    """Manager class for password attack tools."""

    def __init__(self):
        self.tools = {
            "john": JohnTheRipperAutomation(),
            "hashcat": HashcatAutomation(),
            "hydra": HydraAutomation()
        }

    def get_available_tools(self) -> list[str]:
        """Get list of available password attack tools."""
        return list(self.tools.keys())

    def get_tool_info(self, tool_name: str) -> dict[str, Any] | None:
        """Get information about a specific tool."""
        if tool_name in self.tools:
            tool = self.tools[tool_name]
            return {
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "attack_modes": tool.get_attack_modes(),
                "output_formats": tool.get_output_formats(),
                "supported_hash_types": tool.get_supported_hash_types()
            }
        return None

    async def execute_password_attack(self, tool_name: str, target: str,
                                    options: dict[str, Any]) -> dict[str, Any]:
        """Execute password attack with specified tool."""
        if tool_name not in self.tools:
            return {"error": f"Tool {tool_name} not available"}

        tool = self.tools[tool_name]
        return await tool.execute(target, options)

    async def execute_comprehensive_password_assessment(self, target: str,
                                                      options: dict[str, Any]) -> dict[str, Any]:
        """Execute comprehensive password assessment using multiple tools."""
        results = {}
        failed_tools = []

        for tool_name, tool in self.tools.items():
            try:
                logger.info(f"Executing {tool_name} password attack on {target}")
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
        """Generate comprehensive password assessment report."""
        total_hashes = 0
        cracked_hashes = 0
        successful_logins = 0
        total_attempts = 0

        # Aggregate results
        for tool_name, result in results.items():
            if result.get("success", False):
                if "crack_results" in result:
                    crack_results = result["crack_results"]
                    if "summary" in crack_results:
                        summary = crack_results["summary"]
                        total_hashes += summary.get("total_hashes", 0)
                        cracked_hashes += summary.get("cracked_hashes", 0)

                elif "attack_results" in result:
                    attack_results = result["attack_results"]
                    if "summary" in attack_results:
                        summary = attack_results["summary"]
                        successful_logins += summary.get("successful_logins", 0)
                        total_attempts += summary.get("total_attempts", 0)

        return {
            "target": target,
            "summary": {
                "total_hashes": total_hashes,
                "cracked_hashes": cracked_hashes,
                "successful_logins": successful_logins,
                "total_attempts": total_attempts
            },
            "risk_assessment": self._assess_password_security_risk(cracked_hashes, successful_logins),
            "recommendations": self._generate_password_security_recommendations(cracked_hashes, successful_logins),
            "generated_at": datetime.now(UTC).isoformat()
        }

    def _assess_password_security_risk(self, cracked: int, logins: int) -> str:
        """Assess password security risk level."""
        if cracked > 10 or logins > 5:
            return "CRITICAL"
        elif cracked > 0 or logins > 0:
            return "HIGH"
        else:
            return "MINIMAL"

    def _generate_password_security_recommendations(self, cracked: int, logins: int) -> list[str]:
        """Generate password security recommendations."""
        recommendations = []

        if cracked > 0:
            recommendations.append("Immediate action required: Passwords have been cracked")
            recommendations.append("Implement strong password policies")
            recommendations.append("Use password managers for complex passwords")
            recommendations.append("Enable multi-factor authentication (MFA)")

        if logins > 0:
            recommendations.append("Network service brute force attacks detected")
            recommendations.append("Implement account lockout policies")
            recommendations.append("Use strong authentication mechanisms")
            recommendations.append("Monitor failed login attempts")

        recommendations.append("Regular password audits and testing")
        recommendations.append("Implement password expiration policies")
        recommendations.append("Use salted and hashed password storage")
        recommendations.append("Regular security awareness training")

        return recommendations


# Example usage and testing
async def main():
    """Example usage of password attack tools."""
    tools = PasswordAttackTools()

    # Get available tools
    print("Available tools:", tools.get_available_tools())

    # Execute single tool attack
    result = await tools.execute_password_attack(
        "john",
        "hash_file.txt",
        {"attack_mode": "wordlist", "wordlist": "/usr/share/wordlists/rockyou.txt"}
    )
    print("Single tool result:", result)

    # Execute comprehensive assessment
    comprehensive = await tools.execute_comprehensive_password_assessment(
        "hash_file.txt",
        {"attack_mode": "wordlist", "wordlist": "/usr/share/wordlists/rockyou.txt"}
    )
    print("Comprehensive assessment:", comprehensive)


if __name__ == "__main__":
    asyncio.run(main())

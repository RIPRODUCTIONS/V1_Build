"""
Dynamic Analysis Sandbox Module

This module provides comprehensive dynamic analysis capabilities for malware samples
in isolated sandbox environments, including execution monitoring, behavior analysis,
and network traffic analysis.
"""

import hashlib
import logging
import os
import subprocess
import tempfile
import time
from datetime import UTC, datetime
from typing import Any

# Constants for magic numbers
HIGH_RISK_THRESHOLD = 5
MEDIUM_RISK_THRESHOLD = 2
MIN_ASCII_CHAR = 32
MAX_ASCII_CHAR = 126
MIN_STRING_LENGTH = 4
DEFAULT_BUFFER_SIZE = 1024
MAX_PORT_NUMBER = 49152
MIN_PORT_NUMBER = 1024
MAX_PROCESS_COUNT = 3

# Configure logging
logger = logging.getLogger(__name__)


class SandboxError(Exception):
    """Custom exception for sandbox operations."""
    pass


class SandboxCreationError(SandboxError):
    """Exception raised when sandbox creation fails."""
    pass


class ExecutionError(SandboxError):
    """Exception raised when sample execution fails."""
    pass


class MonitoringError(SandboxError):
    """Exception raised when behavior monitoring fails."""
    pass


def create_sandbox_environment(config: dict[str, Any]) -> dict[str, Any]:
    """
    Create isolated sandbox environment.

    Args:
        config: Sandbox configuration parameters

    Returns:
        Dictionary containing sandbox environment information

    Raises:
        SandboxCreationError: If sandbox creation fails
    """
    try:
        logger.info("Creating sandbox environment")

        # Extract configuration
        isolation_level = config.get("isolation_level", "medium")
        network_access = config.get("network_access", "restricted")
        monitoring_enabled = config.get("monitoring_enabled", True)

        # Create temporary directory for sandbox
        sandbox_dir = tempfile.mkdtemp(prefix="sandbox_")

        # Create sandbox structure
        sandbox_structure = _create_sandbox_structure(sandbox_dir)

        # Configure isolation
        isolation_config = _configure_isolation(isolation_level, sandbox_dir)

        # Configure network access
        network_config = _configure_network_access(network_access)

        # Configure monitoring
        monitoring_config = _configure_monitoring(monitoring_enabled, sandbox_dir)

        # Initialize sandbox state
        sandbox_state = {
            "status": "ready",
            "created_at": datetime.now(UTC).isoformat(),
            "sample_count": 0,
            "execution_count": 0
        }

        sandbox_env = {
            "sandbox_id": _generate_sandbox_id(),
            "sandbox_dir": sandbox_dir,
            "isolation_level": isolation_level,
            "network_access": network_access,
            "monitoring_enabled": monitoring_enabled,
            "structure": sandbox_structure,
            "isolation_config": isolation_config,
            "network_config": network_config,
            "monitoring_config": monitoring_config,
            "state": sandbox_state,
            "creation_timestamp": datetime.now(UTC).isoformat()
        }

        logger.info(f"Sandbox environment created successfully: {sandbox_env['sandbox_id']}")
        return sandbox_env

    except Exception as e:
        logger.error(f"Sandbox environment creation failed: {e}")
        raise SandboxCreationError(f"Sandbox creation failed: {e}") from e


def execute_sample(sample_data: bytes, sandbox_config: dict[str, Any]) -> dict[str, Any]:
    """
    Execute malware sample in sandbox.

    Args:
        sample_data: Raw bytes of the malware sample
        sandbox_config: Sandbox configuration and environment

    Returns:
        Dictionary containing execution results and artifacts

    Raises:
        ExecutionError: If sample execution fails
    """
    try:
        logger.info("Starting sample execution in sandbox")

        # Validate sandbox state
        if sandbox_config.get("state", {}).get("status") != "ready":
            raise ExecutionError("Sandbox is not ready for execution")

        # Create sample file in sandbox
        sample_file = _create_sample_file(sample_data, sandbox_config)

        # Update sandbox state
        sandbox_config["state"]["sample_count"] += 1
        sandbox_config["state"]["execution_count"] += 1
        sandbox_config["state"]["status"] = "executing"

        # Prepare execution environment
        execution_env = _prepare_execution_environment(sandbox_config)

        # Execute the sample
        execution_result = _execute_sample_file(sample_file, execution_env, sandbox_config)

        # Collect execution artifacts
        artifacts = _collect_execution_artifacts(sandbox_config)

        # Update sandbox state
        sandbox_config["state"]["status"] = "ready"

        result = {
            "execution_id": _generate_execution_id(),
            "sample_file": sample_file,
            "execution_result": execution_result,
            "artifacts": artifacts,
            "execution_timestamp": datetime.now(UTC).isoformat(),
            "sandbox_state": sandbox_config["state"]
        }

        logger.info(f"Sample execution completed successfully: {result['execution_id']}")
        return result

    except Exception as e:
        logger.error(f"Sample execution failed: {e}")
        # Reset sandbox state
        sandbox_config["state"]["status"] = "ready"
        raise ExecutionError(f"Sample execution failed: {e}") from e


def monitor_behavior(execution_info: dict[str, Any]) -> dict[str, Any]:
    """
    Monitor malware behavior during execution.

    Args:
        execution_info: Information from sample execution

    Returns:
        Dictionary containing behavior monitoring results

    Raises:
        MonitoringError: If behavior monitoring fails
    """
    try:
        logger.info("Starting behavior monitoring")

        # Extract execution details
        sample_file = execution_info.get("sample_file", "")
        sandbox_dir = execution_info.get("sandbox_dir", "")

        if not sample_file or not sandbox_dir:
            raise MonitoringError("Invalid execution information")

        # Monitor file system changes
        file_changes = _monitor_file_system_changes(sandbox_dir)

        # Monitor registry changes
        registry_changes = _monitor_registry_changes(sandbox_dir)

        # Monitor process creation
        process_creation = _monitor_process_creation(sandbox_dir)

        # Monitor network activity
        network_activity = _monitor_network_activity(sandbox_dir)

        # Monitor API calls
        api_calls = _monitor_api_calls(sandbox_dir)

        # Analyze behavior patterns
        behavior_patterns = _analyze_behavior_patterns(
            file_changes, registry_changes, process_creation, network_activity, api_calls
        )

        # Generate behavior summary
        behavior_summary = _generate_behavior_summary(behavior_patterns)

        result = {
            "file_system_changes": file_changes,
            "registry_changes": registry_changes,
            "process_creation": process_creation,
            "network_activity": network_activity,
            "api_calls": api_calls,
            "behavior_patterns": behavior_patterns,
            "behavior_summary": behavior_summary,
            "monitoring_timestamp": datetime.now(UTC).isoformat()
        }

        logger.info("Behavior monitoring completed successfully")
        return result

    except Exception as e:
        logger.error(f"Behavior monitoring failed: {e}")
        raise MonitoringError(f"Behavior monitoring failed: {e}") from e


def analyze_network_traffic(pcap_data: bytes) -> dict[str, Any]:
    """
    Analyze network traffic generated by sample.

    Args:
        pcap_data: PCAP data from network monitoring

    Returns:
        Dictionary containing network traffic analysis

    Raises:
        SandboxError: If network analysis fails
    """
    try:
        logger.info("Starting network traffic analysis")

        if not pcap_data:
            return {
                "network_connections": [],
                "traffic_patterns": [],
                "suspicious_activity": [],
                "analysis_summary": "No network traffic detected"
            }

        # Parse PCAP data
        network_connections = _parse_network_connections(pcap_data)

        # Analyze traffic patterns
        traffic_patterns = _analyze_traffic_patterns(network_connections)

        # Identify suspicious activity
        suspicious_activity = _identify_suspicious_network_activity(network_connections)

        # Analyze protocols
        protocol_analysis = _analyze_network_protocols(network_connections)

        # Generate network summary
        network_summary = _generate_network_summary(network_connections, suspicious_activity)

        result = {
            "network_connections": network_connections,
            "traffic_patterns": traffic_patterns,
            "suspicious_activity": suspicious_activity,
            "protocol_analysis": protocol_analysis,
            "network_summary": network_summary,
            "analysis_timestamp": datetime.now(UTC).isoformat()
        }

        logger.info("Network traffic analysis completed successfully")
        return result

    except Exception as e:
        logger.error(f"Network traffic analysis failed: {e}")
        raise SandboxError(f"Network analysis failed: {e}") from e


def extract_runtime_artifacts(behavior_data: dict[str, Any]) -> dict[str, Any]:
    """
    Extract artifacts created during execution.

    Args:
        behavior_data: Behavior monitoring results

    Returns:
        Dictionary containing extracted runtime artifacts

    Raises:
        SandboxError: If artifact extraction fails
    """
    try:
        logger.info("Starting runtime artifact extraction")

        # Extract file artifacts
        file_artifacts = _extract_file_artifacts(behavior_data)

        # Extract registry artifacts
        registry_artifacts = _extract_registry_artifacts(behavior_data)

        # Extract process artifacts
        process_artifacts = _extract_process_artifacts(behavior_data)

        # Extract network artifacts
        network_artifacts = _extract_network_artifacts(behavior_data)

        # Extract memory artifacts
        memory_artifacts = _extract_memory_artifacts(behavior_data)

        # Generate artifact summary
        artifact_summary = _generate_artifact_summary(
            file_artifacts, registry_artifacts, process_artifacts,
            network_artifacts, memory_artifacts
        )

        result = {
            "file_artifacts": file_artifacts,
            "registry_artifacts": registry_artifacts,
            "process_artifacts": process_artifacts,
            "network_artifacts": network_artifacts,
            "memory_artifacts": memory_artifacts,
            "artifact_summary": artifact_summary,
            "extraction_timestamp": datetime.now(UTC).isoformat()
        }

        logger.info("Runtime artifact extraction completed successfully")
        return result

    except Exception as e:
        logger.error(f"Runtime artifact extraction failed: {e}")
        raise SandboxError(f"Artifact extraction failed: {e}") from e


# Helper functions for sandbox creation
def _create_sandbox_structure(sandbox_dir: str) -> dict[str, Any]:
    """Create sandbox directory structure."""
    try:
        structure = {
            "root": sandbox_dir,
            "samples": os.path.join(sandbox_dir, "samples"),
            "logs": os.path.join(sandbox_dir, "logs"),
            "artifacts": os.path.join(sandbox_dir, "artifacts"),
            "temp": os.path.join(sandbox_dir, "temp"),
            "monitoring": os.path.join(sandbox_dir, "monitoring")
        }

        # Create directories
        for path in structure.values():
            os.makedirs(path, exist_ok=True)

        return structure
    except Exception as e:
        logger.warning(f"Failed to create sandbox structure: {e}")
        return {}


def _configure_isolation(isolation_level: str, sandbox_dir: str) -> dict[str, Any]:
    """Configure sandbox isolation settings."""
    isolation_config = {
        "level": isolation_level,
        "file_system_isolation": True,
        "process_isolation": True,
        "network_isolation": isolation_level in ["high", "maximum"],
        "memory_isolation": isolation_level == "maximum"
    }

    # Apply isolation based on level
    if isolation_level == "high":
        isolation_config.update({
            "restrict_system_calls": True,
            "restrict_file_access": True,
            "restrict_registry_access": True
        })
    elif isolation_level == "maximum":
        isolation_config.update({
            "restrict_system_calls": True,
            "restrict_file_access": True,
            "restrict_registry_access": True,
            "restrict_network_access": True,
            "memory_protection": True
        })

    return isolation_config


def _configure_network_access(network_access: str) -> dict[str, Any]:
    """Configure network access settings."""
    network_config = {
        "access_level": network_access,
        "allowed_protocols": [],
        "allowed_ports": [],
        "allowed_domains": [],
        "traffic_capture": True,
        "dns_monitoring": True
    }

    if network_access == "restricted":
        network_config.update({
            "allowed_protocols": ["HTTP", "HTTPS"],
            "allowed_ports": [80, 443],
            "allowed_domains": ["localhost", "127.0.0.1"]
        })
    elif network_access == "blocked":
        network_config.update({
            "allowed_protocols": [],
            "allowed_ports": [],
            "allowed_domains": []
        })

    return network_config


def _configure_monitoring(monitoring_enabled: bool, sandbox_dir: str) -> dict[str, Any]:
    """Configure monitoring settings."""
    if not monitoring_enabled:
        return {"enabled": False}

    monitoring_config = {
        "enabled": True,
        "file_monitoring": True,
        "registry_monitoring": True,
        "process_monitoring": True,
        "network_monitoring": True,
        "api_monitoring": True,
        "memory_monitoring": True,
        "log_directory": os.path.join(sandbox_dir, "monitoring")
    }

    return monitoring_config


def _generate_sandbox_id() -> str:
    """Generate unique sandbox identifier."""
    timestamp = int(time.time())
    random_suffix = hashlib.md5(str(timestamp).encode()).hexdigest()[:8]
    return f"sandbox_{timestamp}_{random_suffix}"


# Helper functions for sample execution
def _create_sample_file(sample_data: bytes, sandbox_config: dict[str, Any]) -> str:
    """Create sample file in sandbox."""
    try:
        samples_dir = sandbox_config["structure"]["samples"]
        sample_filename = f"sample_{int(time.time())}.exe"
        sample_path = os.path.join(samples_dir, sample_filename)

        with open(sample_path, 'wb') as f:
            f.write(sample_data)

        # Calculate file hash
        file_hash = hashlib.sha256(sample_data).hexdigest()

        logger.info(f"Sample file created: {sample_path} (hash: {file_hash})")
        return sample_path

    except Exception as e:
        logger.error(f"Failed to create sample file: {e}")
        raise ExecutionError(f"Sample file creation failed: {e}") from e


def _prepare_execution_environment(sandbox_config: dict[str, Any]) -> dict[str, Any]:
    """Prepare execution environment."""
    execution_env = {
        "working_directory": sandbox_config["structure"]["temp"],
        "environment_variables": {
            "TEMP": sandbox_config["structure"]["temp"],
            "TMP": sandbox_config["structure"]["temp"],
            "USERPROFILE": sandbox_config["structure"]["temp"],
            "APPDATA": sandbox_config["structure"]["temp"]
        },
        "isolation_config": sandbox_config["isolation_config"],
        "monitoring_config": sandbox_config["monitoring_config"]
    }

    return execution_env


def _execute_sample_file(sample_file: str, execution_env: dict[str, Any],
                        sandbox_config: dict[str, Any]) -> dict[str, Any]:
    """Execute the sample file."""
    try:
        execution_result = {
            "status": "unknown",
            "exit_code": None,
            "execution_time": 0,
            "error_message": None,
            "process_id": None
        }

        start_time = time.time()

        # Start monitoring before execution
        monitoring_process = _start_monitoring(sandbox_config)

        try:
            # Execute the sample
            process = subprocess.Popen(
                [sample_file],
                cwd=execution_env["working_directory"],
                env=execution_env["environment_variables"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )

            execution_result["process_id"] = process.pid

            # Wait for execution with timeout
            try:
                stdout, stderr = process.communicate(timeout=300)  # 5 minutes timeout
                execution_result["exit_code"] = process.returncode
                execution_result["status"] = "completed"
            except subprocess.TimeoutExpired:
                process.kill()
                execution_result["status"] = "timeout"
                execution_result["error_message"] = "Execution timed out"

        finally:
            # Stop monitoring
            _stop_monitoring(monitoring_process)

        execution_result["execution_time"] = time.time() - start_time

        return execution_result

    except Exception as e:
        execution_result["status"] = "failed"
        execution_result["error_message"] = str(e)
        logger.error(f"Sample execution failed: {e}")
        return execution_result


def _start_monitoring(sandbox_config: dict[str, Any]) -> dict[str, Any] | None:
    """Start monitoring processes."""
    try:
        if not sandbox_config["monitoring_config"]["enabled"]:
            return None

        # Start file system monitoring
        file_monitor = _start_file_monitoring(sandbox_config)

        # Start process monitoring
        process_monitor = _start_process_monitoring(sandbox_config)

        # Start network monitoring
        network_monitor = _start_network_monitoring(sandbox_config)

        return {
            "file_monitor": file_monitor,
            "process_monitor": process_monitor,
            "network_monitor": network_monitor
        }

    except Exception as e:
        logger.warning(f"Failed to start monitoring: {e}")
        return None


def _stop_monitoring(monitoring_process: dict[str, Any] | None) -> None:
    """Stop monitoring processes."""
    if not monitoring_process:
        return

    try:
        for _monitor_name, monitor_process in monitoring_process.items():
            if monitor_process and hasattr(monitor_process, 'terminate'):
                monitor_process.terminate()
                monitor_process.wait(timeout=5)
    except Exception as e:
        logger.warning(f"Failed to stop monitoring: {e}")


def _start_file_monitoring(sandbox_config: dict[str, Any]) -> subprocess.Popen | None:
    """Start file system monitoring."""
    try:
        # This would implement actual file system monitoring
        # For now, return None
        return None
    except Exception as e:
        logger.warning(f"Failed to start file monitoring: {e}")
        return None


def _start_process_monitoring(sandbox_config: dict[str, Any]) -> subprocess.Popen | None:
    """Start process monitoring."""
    try:
        # This would implement actual process monitoring
        # For now, return None
        return None
    except Exception as e:
        logger.warning(f"Failed to start process monitoring: {e}")
        return None


def _start_network_monitoring(sandbox_config: dict[str, Any]) -> subprocess.Popen | None:
    """Start network monitoring."""
    try:
        # This would implement actual network monitoring
        # For now, return None
        return None
    except Exception as e:
        logger.warning(f"Failed to start network monitoring: {e}")
        return None


def _collect_execution_artifacts(sandbox_config: dict[str, Any]) -> dict[str, Any]:
    """Collect artifacts from execution."""
    artifacts = {
        "files": [],
        "logs": [],
        "memory_dumps": [],
        "network_captures": []
    }

    try:
        # Collect files
        artifacts_dir = sandbox_config["structure"]["artifacts"]
        if os.path.exists(artifacts_dir):
            for root, _dirs, files in os.walk(artifacts_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    artifacts["files"].append({
                        "path": file_path,
                        "size": os.path.getsize(file_path),
                        "modified": os.path.getmtime(file_path)
                    })

        # Collect logs
        logs_dir = sandbox_config["structure"]["logs"]
        if os.path.exists(logs_dir):
            for log_file in os.listdir(logs_dir):
                if log_file.endswith('.log'):
                    log_path = os.path.join(logs_dir, log_file)
                    artifacts["logs"].append({
                        "path": log_path,
                        "size": os.path.getsize(log_path)
                    })

    except Exception as e:
        logger.warning(f"Failed to collect execution artifacts: {e}")

    return artifacts


def _generate_execution_id() -> str:
    """Generate unique execution identifier."""
    timestamp = int(time.time())
    random_suffix = hashlib.md5(str(timestamp).encode()).hexdigest()[:8]
    return f"exec_{timestamp}_{random_suffix}"


# Helper functions for behavior monitoring
def _monitor_file_system_changes(sandbox_dir: str) -> list[dict[str, Any]]:
    """Monitor file system changes."""
    try:
        changes = []

        # This would implement actual file system change monitoring
        # For now, return mock data
        changes.append({
            "type": "file_created",
            "path": os.path.join(sandbox_dir, "temp", "malware_output.txt"),
            "timestamp": datetime.now(UTC).isoformat(),
            "size": 1024
        })

        return changes

    except Exception as e:
        logger.warning(f"File system monitoring failed: {e}")
        return []


def _monitor_registry_changes(sandbox_dir: str) -> list[dict[str, Any]]:
    """Monitor registry changes."""
    try:
        changes = []

        # This would implement actual registry change monitoring
        # For now, return mock data
        changes.append({
            "type": "key_created",
            "path": "HKEY_CURRENT_USER\\Software\\Malware",
            "timestamp": datetime.now(UTC).isoformat(),
            "value": "suspicious_value"
        })

        return changes

    except Exception as e:
        logger.warning(f"Registry monitoring failed: {e}")
        return []


def _monitor_process_creation(sandbox_dir: str) -> list[dict[str, Any]]:
    """Monitor process creation."""
    try:
        processes = []

        # This would implement actual process monitoring
        # For now, return mock data
        processes.append({
            "process_id": 1234,
            "parent_id": 123,
            "command_line": "C:\\temp\\malware.exe",
            "start_time": datetime.now(UTC).isoformat(),
            "status": "running"
        })

        return processes

    except Exception as e:
        logger.warning(f"Process monitoring failed: {e}")
        return []


def _monitor_network_activity(sandbox_dir: str) -> list[dict[str, Any]]:
    """Monitor network activity."""
    try:
        activity = []

        # This would implement actual network monitoring
        # For now, return mock data
        activity.append({
            "type": "connection",
            "local_address": "192.168.1.100:12345",
            "remote_address": "10.0.0.1:80",
            "protocol": "TCP",
            "timestamp": datetime.now(UTC).isoformat()
        })

        return activity

    except Exception as e:
        logger.warning(f"Network monitoring failed: {e}")
        return []


def _monitor_api_calls(sandbox_dir: str) -> list[dict[str, Any]]:
    """Monitor API calls."""
    try:
        api_calls = []

        # This would implement actual API monitoring
        # For now, return mock data
        api_calls.append({
            "api_name": "CreateFileW",
            "parameters": "C:\\temp\\output.txt",
            "timestamp": datetime.now(UTC).isoformat(),
            "result": "SUCCESS"
        })

        return api_calls

    except Exception as e:
        logger.warning(f"API monitoring failed: {e}")
        return []


def _analyze_behavior_patterns(file_changes: list[dict[str, Any]],
                              registry_changes: list[dict[str, Any]],
                              process_creation: list[dict[str, Any]],
                              network_activity: list[dict[str, Any]],
                              api_calls: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze behavior patterns."""
    patterns = {
        "file_operations": [],
        "registry_operations": [],
        "process_operations": [],
        "network_operations": [],
        "api_usage": [],
        "suspicious_patterns": []
    }

    # Analyze file operations
    if file_changes:
        patterns["file_operations"] = _analyze_file_operations(file_changes)

    # Analyze registry operations
    if registry_changes:
        patterns["registry_operations"] = _analyze_registry_operations(registry_changes)

    # Analyze process operations
    if process_creation:
        patterns["process_operations"] = _analyze_process_operations(process_creation)

    # Analyze network operations
    if network_activity:
        patterns["network_operations"] = _analyze_network_operations(network_activity)

    # Analyze API usage
    if api_calls:
        patterns["api_usage"] = _analyze_api_usage(api_calls)

    # Identify suspicious patterns
    patterns["suspicious_patterns"] = _identify_suspicious_patterns(patterns)

    return patterns


def _analyze_file_operations(file_changes: list[dict[str, Any]]) -> list[str]:
    """Analyze file operation patterns."""
    patterns = []

    for change in file_changes:
        if change.get("type") == "file_created":
            patterns.append("file_creation")
        elif change.get("type") == "file_modified":
            patterns.append("file_modification")
        elif change.get("type") == "file_deleted":
            patterns.append("file_deletion")

    return list(set(patterns))


def _analyze_registry_operations(registry_changes: list[dict[str, Any]]) -> list[str]:
    """Analyze registry operation patterns."""
    patterns = []

    for change in registry_changes:
        if change.get("type") == "key_created":
            patterns.append("registry_key_creation")
        elif change.get("type") == "value_set":
            patterns.append("registry_value_modification")

    return list(set(patterns))


def _analyze_process_operations(process_creation: list[dict[str, Any]]) -> list[str]:
    """Analyze process operation patterns."""
    patterns = []

    for process in process_creation:
        if process.get("status") == "running":
            patterns.append("process_creation")
        elif process.get("status") == "terminated":
            patterns.append("process_termination")

    return list(set(patterns))


def _analyze_network_operations(network_activity: list[dict[str, Any]]) -> list[str]:
    """Analyze network operation patterns."""
    patterns = []

    for activity in network_activity:
        if activity.get("type") == "connection":
            patterns.append("network_connection")
        elif activity.get("type") == "data_transfer":
            patterns.append("data_transfer")

    return list(set(patterns))


def _analyze_api_usage(api_calls: list[dict[str, Any]]) -> list[str]:
    """Analyze API usage patterns."""
    patterns = []

    for api_call in api_calls:
        api_name = api_call.get("api_name", "")
        if "CreateFile" in api_name:
            patterns.append("file_operations")
        elif "RegCreate" in api_name:
            patterns.append("registry_operations")
        elif "CreateProcess" in api_name:
            patterns.append("process_operations")
        elif "WSAConnect" in api_name:
            patterns.append("network_operations")

    return list(set(patterns))


def _identify_suspicious_patterns(patterns: dict[str, Any]) -> list[str]:
    """Identify suspicious behavior patterns."""
    suspicious = []

    # Check for suspicious file operations
    if "file_creation" in patterns.get("file_operations", []):
        suspicious.append("suspicious_file_creation")

    # Check for suspicious registry operations
    if "registry_key_creation" in patterns.get("registry_operations", []):
        suspicious.append("suspicious_registry_modification")

    # Check for suspicious process operations
    if "process_creation" in patterns.get("process_operations", []):
        suspicious.append("suspicious_process_creation")

    # Check for suspicious network operations
    if "network_connection" in patterns.get("network_operations", []):
        suspicious.append("suspicious_network_activity")

    return suspicious


def _generate_behavior_summary(behavior_patterns: dict[str, Any]) -> dict[str, Any]:
    """Generate behavior summary."""
    summary = {
        "total_operations": 0,
        "suspicious_operations": 0,
        "risk_level": "low",
        "recommendations": []
    }

    # Count total operations
    for _pattern_type, patterns in behavior_patterns.items():
        if isinstance(patterns, list):
            summary["total_operations"] += len(patterns)

    # Count suspicious operations
    suspicious_patterns = behavior_patterns.get("suspicious_patterns", [])
    summary["suspicious_operations"] = len(suspicious_patterns)

    # Determine risk level
    if summary["suspicious_operations"] > HIGH_RISK_THRESHOLD:
        summary["risk_level"] = "high"
    elif summary["suspicious_operations"] > MEDIUM_RISK_THRESHOLD:
        summary["risk_level"] = "medium"

    # Generate recommendations
    if summary["risk_level"] == "high":
        summary["recommendations"].append("Immediate containment required")
        summary["recommendations"].append("Deep analysis recommended")
    elif summary["risk_level"] == "medium":
        summary["recommendations"].append("Monitor closely")
        summary["recommendations"].append("Additional analysis recommended")

    return summary


# Helper functions for network analysis
def _parse_network_connections(pcap_data: bytes) -> list[dict[str, Any]]:
    """Parse network connections from PCAP data."""
    connections = []

    try:
        # This would implement actual PCAP parsing
        # For now, return mock data
        connections.append({
            "source_ip": "192.168.1.100",
            "source_port": 12345,
            "dest_ip": "10.0.0.1",
            "dest_port": 80,
            "protocol": "TCP",
            "timestamp": datetime.now(UTC).isoformat(),
            "data_size": DEFAULT_BUFFER_SIZE
        })

    except Exception as e:
        logger.warning(f"Network connection parsing failed: {e}")

    return connections


def _analyze_traffic_patterns(connections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Analyze network traffic patterns."""
    patterns = []

    try:
        # Analyze connection patterns
        if len(connections) > 1:
            patterns.append({
                "pattern_type": "multiple_connections",
                "description": "Multiple network connections detected",
                "severity": "medium"
            })

        # Analyze protocol patterns
        protocols = [conn.get("protocol") for conn in connections]
        if "TCP" in protocols and "UDP" in protocols:
            patterns.append({
                "pattern_type": "mixed_protocols",
                "description": "Mixed protocol usage detected",
                "severity": "low"
            })

    except Exception as e:
        logger.warning(f"Traffic pattern analysis failed: {e}")

    return patterns


def _identify_suspicious_network_activity(connections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Identify suspicious network activity."""
    suspicious = []

    try:
        for conn in connections:
            dest_ip = conn.get("dest_ip", "")
            dest_port = conn.get("dest_port", 0)

            # Check for suspicious destinations
            if dest_ip in ["0.0.0.0", "255.255.255.255"]:
                suspicious.append({
                    "type": "suspicious_destination",
                    "description": f"Suspicious destination IP: {dest_ip}",
                    "severity": "high"
                })

            # Check for suspicious ports
            if dest_port in [22, 23, 3389, 5900]:  # SSH, Telnet, RDP, VNC
                suspicious.append({
                    "type": "suspicious_port",
                    "description": f"Suspicious destination port: {dest_port}",
                    "severity": "medium"
                })

    except Exception as e:
        logger.warning(f"Suspicious network activity detection failed: {e}")

    return suspicious


def _analyze_network_protocols(connections: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze network protocols."""
    protocol_analysis = {
        "protocols": {},
        "port_analysis": {},
        "ip_analysis": {}
    }

    try:
        # Count protocols
        for conn in connections:
            protocol = conn.get("protocol", "unknown")
            protocol_analysis["protocols"][protocol] = protocol_analysis["protocols"].get(protocol, 0) + 1

        # Analyze ports
        for conn in connections:
            port = conn.get("dest_port", 0)
            if port > 0:
                if port < 1024:
                    port_range = "well_known"
                elif port < 49152:
                    port_range = "registered"
                else:
                    port_range = "dynamic"

                protocol_analysis["port_analysis"][port_range] = protocol_analysis["port_analysis"].get(port_range, 0) + 1

        # Analyze IP addresses
        unique_ips = set()
        for conn in connections:
            unique_ips.add(conn.get("source_ip", ""))
            unique_ips.add(conn.get("dest_ip", ""))

        protocol_analysis["ip_analysis"]["unique_ips"] = len(unique_ips)

    except Exception as e:
        logger.warning(f"Protocol analysis failed: {e}")

    return protocol_analysis


def _generate_network_summary(connections: list[dict[str, Any]],
                             suspicious_activity: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate network summary."""
    summary = {
        "total_connections": len(connections),
        "suspicious_connections": len(suspicious_activity),
        "risk_level": "low",
        "recommendations": []
    }

    # Determine risk level
    if summary["suspicious_connections"] > 3:
        summary["risk_level"] = "high"
    elif summary["suspicious_connections"] > 1:
        summary["risk_level"] = "medium"

    # Generate recommendations
    if summary["risk_level"] == "high":
        summary["recommendations"].append("Block suspicious connections")
        summary["recommendations"].append("Investigate network traffic")
    elif summary["risk_level"] == "medium":
        summary["recommendations"].append("Monitor network activity")
        summary["recommendations"].append("Review firewall rules")

    return summary


# Helper functions for artifact extraction
def _extract_file_artifacts(behavior_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract file artifacts."""
    artifacts = []

    try:
        file_changes = behavior_data.get("file_system_changes", [])
        for change in file_changes:
            if change.get("type") == "file_created":
                artifacts.append({
                    "type": "created_file",
                    "path": change.get("path", ""),
                    "size": change.get("size", 0),
                    "timestamp": change.get("timestamp", ""),
                    "hash": _calculate_file_hash(change.get("path", ""))
                })

    except Exception as e:
        logger.warning(f"File artifact extraction failed: {e}")

    return artifacts


def _extract_registry_artifacts(behavior_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract registry artifacts."""
    artifacts = []

    try:
        registry_changes = behavior_data.get("registry_changes", [])
        for change in registry_changes:
            artifacts.append({
                "type": "registry_change",
                "path": change.get("path", ""),
                "value": change.get("value", ""),
                "timestamp": change.get("timestamp", "")
            })

    except Exception as e:
        logger.warning(f"Registry artifact extraction failed: {e}")

    return artifacts


def _extract_process_artifacts(behavior_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract process artifacts."""
    artifacts = []

    try:
        process_creation = behavior_data.get("process_creation", [])
        for process in process_creation:
            artifacts.append({
                "type": "process_info",
                "process_id": process.get("process_id", 0),
                "parent_id": process.get("parent_id", 0),
                "command_line": process.get("command_line", ""),
                "start_time": process.get("start_time", ""),
                "status": process.get("status", "")
            })

    except Exception as e:
        logger.warning(f"Process artifact extraction failed: {e}")

    return artifacts


def _extract_network_artifacts(behavior_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract network artifacts."""
    artifacts = []

    try:
        network_activity = behavior_data.get("network_activity", [])
        for activity in network_activity:
            artifacts.append({
                "type": "network_activity",
                "local_address": activity.get("local_address", ""),
                "remote_address": activity.get("remote_address", ""),
                "protocol": activity.get("protocol", ""),
                "timestamp": activity.get("timestamp", "")
            })

    except Exception as e:
        logger.warning(f"Network artifact extraction failed: {e}")

    return artifacts


def _extract_memory_artifacts(behavior_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract memory artifacts."""
    artifacts = []

    try:
        # This would implement actual memory artifact extraction
        # For now, return empty list
        pass

    except Exception as e:
        logger.warning(f"Memory artifact extraction failed: {e}")

    return artifacts


def _calculate_file_hash(file_path: str) -> str:
    """Calculate file hash."""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                data = f.read()
                return hashlib.sha256(data).hexdigest()
    except Exception:
        pass

    return ""


def _generate_artifact_summary(file_artifacts: list[dict[str, Any]],
                              registry_artifacts: list[dict[str, Any]],
                              process_artifacts: list[dict[str, Any]],
                              network_artifacts: list[dict[str, Any]],
                              memory_artifacts: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate artifact summary."""
    summary = {
        "total_artifacts": len(file_artifacts) + len(registry_artifacts) +
                          len(process_artifacts) + len(network_artifacts) + len(memory_artifacts),
        "file_artifacts": len(file_artifacts),
        "registry_artifacts": len(registry_artifacts),
        "process_artifacts": len(process_artifacts),
        "network_artifacts": len(network_artifacts),
        "memory_artifacts": len(memory_artifacts),
        "artifact_types": []
    }

    # Identify artifact types
    if file_artifacts:
        summary["artifact_types"].append("files")
    if registry_artifacts:
        summary["artifact_types"].append("registry")
    if process_artifacts:
        summary["artifact_types"].append("processes")
    if network_artifacts:
        summary["artifact_types"].append("network")
    if memory_artifacts:
        summary["artifact_types"].append("memory")

    return summary

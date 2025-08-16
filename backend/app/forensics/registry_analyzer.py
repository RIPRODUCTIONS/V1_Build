import hashlib
import logging
import os
import struct
from datetime import UTC, datetime
from typing import Any

# Constants for magic numbers
DEFAULT_TIMEOUT_SECONDS = 30
MAX_HIVE_SIZE_MB = 100
DEFAULT_CHUNK_SIZE = 1024
MAX_KEY_LENGTH = 255
MAX_VALUE_LENGTH = 16384

logger = logging.getLogger(__name__)

class RegistryAnalysisError(Exception):
    """Custom exception for registry analysis errors."""
    pass

class HiveParsingError(RegistryAnalysisError):
    """Exception raised when registry hive parsing fails."""
    pass

class ChangeAnalysisError(RegistryAnalysisError):
    """Exception raised when registry change analysis fails."""
    pass

class UserActivityError(RegistryAnalysisError):
    """Exception raised when user activity extraction fails."""
    pass

def parse_registry_hives(hive_files: list[str], analysis_params: dict[str, Any]) -> dict[str, Any]:
    """
    Parse Windows registry hive files for analysis.
    Args:
        hive_files: List of paths to registry hive files
        analysis_params: Analysis parameters
    Returns:
        Dictionary containing parsed registry data and metadata
    Raises:
        HiveParsingError: If registry hive parsing fails
    """
    try:
        logger.info(f"Starting registry hive parsing for {len(hive_files)} files")
        parsed_hives = {}
        hive_metadata = {}

        for hive_file in hive_files:
            if not _validate_hive_file(hive_file):
                logger.warning(f"Invalid hive file: {hive_file}")
                continue

            try:
                hive_data = _parse_single_hive(hive_file, analysis_params)
                hive_name = _extract_hive_name(hive_file)
                parsed_hives[hive_name] = hive_data
                hive_metadata[hive_name] = _extract_hive_metadata(hive_file)
            except Exception as e:
                logger.error(f"Failed to parse hive {hive_file}: {e}")
                continue

        registry_summary = _generate_registry_summary(parsed_hives)

        result = {
            "hive_files": hive_files,
            "parsed_hives": parsed_hives,
            "hive_metadata": hive_metadata,
            "registry_summary": registry_summary,
            "analysis_timestamp": datetime.now(UTC).isoformat()
        }

        logger.info(f"Successfully parsed {len(parsed_hives)} registry hives")
        return result

    except Exception as e:
        logger.error(f"Registry hive parsing failed: {e}")
        raise HiveParsingError(f"Registry parsing failed: {e}") from e

def analyze_registry_changes(registry_data: dict[str, Any], baseline_data: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Analyze changes in registry data compared to baseline.
    Args:
        registry_data: Current registry data
        baseline_data: Baseline registry data for comparison
    Returns:
        Dictionary containing change analysis results
    Raises:
        ChangeAnalysisError: If change analysis fails
    """
    try:
        logger.info("Starting registry change analysis")

        if not baseline_data:
            logger.info("No baseline data provided, analyzing current state only")
            current_analysis = _analyze_current_registry_state(registry_data)
            return {
                "baseline_comparison": False,
                "current_state_analysis": current_analysis,
                "change_summary": "No baseline for comparison",
                "analysis_timestamp": datetime.now(UTC).isoformat()
            }

        # Compare current state with baseline
        changes = _identify_registry_changes(registry_data, baseline_data)
        change_categories = _categorize_changes(changes)
        risk_assessment = _assess_change_risks(changes)

        result = {
            "baseline_comparison": True,
            "changes_detected": changes,
            "change_categories": change_categories,
            "risk_assessment": risk_assessment,
            "change_summary": _generate_change_summary(changes),
            "analysis_timestamp": datetime.now(UTC).isoformat()
        }

        logger.info(f"Registry change analysis completed: {len(changes)} changes detected")
        return result

    except Exception as e:
        logger.error(f"Registry change analysis failed: {e}")
        raise ChangeAnalysisError(f"Change analysis failed: {e}") from e

def extract_user_activity(registry_data: dict[str, Any], user_context: dict[str, Any]) -> dict[str, Any]:
    """
    Extract user activity patterns from registry data.
    Args:
        registry_data: Parsed registry data
        user_context: User context information
    Returns:
        Dictionary containing extracted user activity data
    Raises:
        UserActivityError: If user activity extraction fails
    """
    try:
        logger.info("Starting user activity extraction from registry")

        # Extract various types of user activity
        login_activity = _extract_login_activity(registry_data)
        application_usage = _extract_application_usage(registry_data)
        file_access_patterns = _extract_file_access_patterns(registry_data)
        network_activity = _extract_network_activity(registry_data)
        system_interactions = _extract_system_interactions(registry_data)

        # Correlate activities with user context
        correlated_activity = _correlate_user_activities(
            login_activity, application_usage, file_access_patterns,
            network_activity, system_interactions, user_context
        )

        # Generate activity timeline
        activity_timeline = _generate_activity_timeline(correlated_activity)

        result = {
            "login_activity": login_activity,
            "application_usage": application_usage,
            "file_access_patterns": file_access_patterns,
            "network_activity": network_activity,
            "system_interactions": system_interactions,
            "correlated_activity": correlated_activity,
            "activity_timeline": activity_timeline,
            "user_behavior_profile": _generate_user_behavior_profile(correlated_activity),
            "extraction_timestamp": datetime.now(UTC).isoformat()
        }

        logger.info("User activity extraction completed successfully")
        return result

    except Exception as e:
        logger.error(f"User activity extraction failed: {e}")
        raise UserActivityError(f"Activity extraction failed: {e}") from e

def _validate_hive_file(hive_file: str) -> bool:
    """Validate registry hive file format and accessibility."""
    try:
        if not os.path.exists(hive_file):
            return False

        # Check file size (registry hives are typically several MB)
        file_size = os.path.getsize(hive_file)
        if file_size < DEFAULT_CHUNK_SIZE:  # Less than 1KB is suspicious
            return False

        # Check file permissions
        return os.access(hive_file, os.R_OK)
    except Exception:
        return False

def _parse_single_hive(hive_file: str, analysis_params: dict[str, Any]) -> dict[str, Any]:
    """Parse a single registry hive file."""
    try:
        with open(hive_file, 'rb') as f:
            hive_content = f.read()

        # Parse hive header
        hive_header = _parse_hive_header(hive_content)

        # Extract key structures based on analysis parameters
        keys_to_extract = analysis_params.get('keys_to_extract', [])
        if not keys_to_extract:
            keys_to_extract = _get_default_registry_keys()

        extracted_keys = {}
        for key_path in keys_to_extract:
            try:
                key_data = _extract_registry_key(hive_content, key_path)
                if key_data:
                    extracted_keys[key_path] = key_data
            except Exception as e:
                logger.warning(f"Failed to extract key {key_path}: {e}")
                continue

        return {
            "hive_header": hive_header,
            "extracted_keys": extracted_keys,
            "total_keys_extracted": len(extracted_keys),
            "hive_size": len(hive_content),
            "parse_timestamp": datetime.now(UTC).isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to parse hive {hive_file}: {e}")
        raise HiveParsingError(f"Hive parsing failed: {e}") from e

def _parse_hive_header(hive_content: bytes) -> dict[str, Any]:
    """Parse registry hive header structure."""
    try:
        if len(hive_content) < 4096:  # Minimum hive size
            return {"error": "Hive content too small"}

        # Parse hive signature and basic structure
        signature = hive_content[:4].decode('ascii', errors='ignore')
        sequence1 = struct.unpack('<I', hive_content[4:8])[0]
        sequence2 = struct.unpack('<I', hive_content[8:12])[0]
        timestamp = struct.unpack('<Q', hive_content[12:20])[0]

        return {
            "signature": signature,
            "sequence1": sequence1,
            "sequence2": sequence2,
            "timestamp": timestamp,
            "timestamp_readable": datetime.fromtimestamp(timestamp, tz=UTC).isoformat() if timestamp > 0 else "Unknown"
        }
    except Exception as e:
        return {"error": f"Header parsing failed: {str(e)}"}

def _extract_registry_key(hive_content: bytes, key_path: str) -> dict[str, Any] | None:
    """Extract specific registry key data."""
    try:
        # This is a simplified implementation
        # In a real implementation, you would parse the actual registry structure

        # Mock extraction for demonstration
        key_data = {
            "key_path": key_path,
            "key_name": key_path.split('\\')[-1],
            "subkeys": [],
            "values": [],
            "last_modified": datetime.now(UTC).isoformat(),
            "access_count": 0
        }

        # Add some mock subkeys and values
        if "Software" in key_path:
            key_data["subkeys"] = ["Microsoft", "Adobe", "Mozilla"]
            key_data["values"] = [
                {"name": "InstallDate", "type": "REG_DWORD", "data": "0x12345678"},
                {"name": "Version", "type": "REG_SZ", "data": "1.0.0"}
            ]
        elif "System" in key_path:
            key_data["subkeys"] = ["CurrentControlSet", "Control", "Services"]
            key_data["values"] = [
                {"name": "ComputerName", "type": "REG_SZ", "data": "WORKSTATION-01"},
                {"name": "ProductName", "type": "REG_SZ", "data": "Windows 10 Pro"}
            ]

        return key_data

    except Exception as e:
        logger.warning(f"Failed to extract key {key_path}: {e}")
        return None

def _get_default_registry_keys() -> list[str]:
    """Get default registry keys to extract for analysis."""
    return [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System",
        r"SYSTEM\CurrentControlSet\Services",
        r"SYSTEM\CurrentControlSet\Control\Session Manager\AppCompatCache",
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\RunMRU",
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\OpenSavePidlMRU",
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\LastVisitedPidlMRU",
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs",
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\WordWheelQuery"
    ]

def _extract_hive_name(hive_file: str) -> str:
    """Extract hive name from file path."""
    filename = os.path.basename(hive_file)
    if filename.lower().startswith('sam'):
        return "SAM"
    elif filename.lower().startswith('security'):
        return "SECURITY"
    elif filename.lower().startswith('software'):
        return "SOFTWARE"
    elif filename.lower().startswith('system'):
        return "SYSTEM"
    elif filename.lower().startswith('ntuser'):
        return "NTUSER"
    else:
        return filename.split('.')[0].upper()

def _extract_hive_metadata(hive_file: str) -> dict[str, Any]:
    """Extract metadata from hive file."""
    try:
        stat_info = os.stat(hive_file)
        return {
            "file_path": hive_file,
            "file_size": stat_info.st_size,
            "created_time": datetime.fromtimestamp(stat_info.st_ctime, tz=UTC).isoformat(),
            "modified_time": datetime.fromtimestamp(stat_info.st_mtime, tz=UTC).isoformat(),
            "accessed_time": datetime.fromtimestamp(stat_info.st_atime, tz=UTC).isoformat(),
            "file_hash": _calculate_file_hash(hive_file)
        }
    except Exception as e:
        return {"error": f"Metadata extraction failed: {str(e)}"}

def _calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of file."""
    try:
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception:
        return "hash_calculation_failed"

def _generate_registry_summary(parsed_hives: dict[str, Any]) -> dict[str, Any]:
    """Generate summary of parsed registry data."""
    total_keys = sum(hive.get('total_keys_extracted', 0) for hive in parsed_hives.values())
    total_size = sum(hive.get('hive_size', 0) for hive in parsed_hives.values())

    return {
        "total_hives_parsed": len(parsed_hives),
        "total_keys_extracted": total_keys,
        "total_data_size": total_size,
        "hive_types": list(parsed_hives.keys()),
        "parse_status": "completed"
    }

def _analyze_current_registry_state(registry_data: dict[str, Any]) -> dict[str, Any]:
    """Analyze current registry state without baseline comparison."""
    return {
        "analysis_type": "current_state_only",
        "total_hives": len(registry_data.get('parsed_hives', {})),
        "total_keys": sum(hive.get('total_keys_extracted', 0) for hive in registry_data.get('parsed_hives', {}).values()),
        "analysis_summary": "Current registry state analyzed"
    }

def _identify_registry_changes(current_data: dict[str, Any], baseline_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Identify changes between current and baseline registry data."""
    changes = []

    # This is a simplified comparison
    # In a real implementation, you would do deep comparison of registry structures

    current_hives = current_data.get('parsed_hives', {})
    baseline_hives = baseline_data.get('parsed_hives', {})

    for hive_name in current_hives:
        if hive_name not in baseline_hives:
            changes.append({
                "type": "new_hive",
                "hive_name": hive_name,
                "description": f"New registry hive detected: {hive_name}"
            })
        else:
            # Compare key counts
            current_keys = current_hives[hive_name].get('total_keys_extracted', 0)
            baseline_keys = baseline_hives[hive_name].get('total_keys_extracted', 0)

            if current_keys != baseline_keys:
                changes.append({
                    "type": "key_count_change",
                    "hive_name": hive_name,
                    "baseline_count": baseline_keys,
                    "current_count": current_keys,
                    "difference": current_keys - baseline_keys
                })

    return changes

def _categorize_changes(changes: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Categorize registry changes by type."""
    categories = {
        "new_hives": [],
        "key_changes": [],
        "value_changes": [],
        "permission_changes": [],
        "other_changes": []
    }

    for change in changes:
        change_type = change.get('type', 'unknown')
        if change_type == 'new_hive':
            categories["new_hives"].append(change)
        elif change_type in ['key_count_change', 'key_addition', 'key_deletion']:
            categories["key_changes"].append(change)
        elif change_type in ['value_modification', 'value_addition', 'value_deletion']:
            categories["value_changes"].append(change)
        elif change_type == 'permission_change':
            categories["permission_changes"].append(change)
        else:
            categories["other_changes"].append(change)

    return categories

def _assess_change_risks(changes: list[dict[str, Any]]) -> dict[str, Any]:
    """Assess risk level of registry changes."""
    risk_scores = {
        "low": 0,
        "medium": 0,
        "high": 0,
        "critical": 0
    }

    for change in changes:
        risk_level = _calculate_change_risk(change)
        risk_scores[risk_level] += 1

    total_changes = len(changes)
    overall_risk = _calculate_overall_risk(risk_scores, total_changes)

    return {
        "risk_breakdown": risk_scores,
        "overall_risk": overall_risk,
        "total_changes": total_changes,
        "risk_assessment": _generate_risk_assessment(risk_scores, overall_risk)
    }

def _calculate_change_risk(change: dict[str, Any]) -> str:
    """Calculate risk level for a specific change."""
    change_type = change.get('type', 'unknown')

    high_risk_types = ['new_hive', 'permission_change']
    medium_risk_types = ['key_count_change', 'value_modification']
    low_risk_types = ['key_addition', 'value_addition']

    if change_type in high_risk_types:
        return "high"
    elif change_type in medium_risk_types:
        return "medium"
    elif change_type in low_risk_types:
        return "low"
    else:
        return "medium"

def _calculate_overall_risk(risk_scores: dict[str, int], total_changes: int) -> str:
    """Calculate overall risk level based on risk scores."""
    if total_changes == 0:
        return "none"

    # Weighted risk calculation
    weighted_score = (
        risk_scores["critical"] * 4 +
        risk_scores["high"] * 3 +
        risk_scores["medium"] * 2 +
        risk_scores["low"] * 1
    ) / total_changes

    if weighted_score >= 3.5:
        return "critical"
    elif weighted_score >= 2.5:
        return "high"
    elif weighted_score >= 1.5:
        return "medium"
    else:
        return "low"

def _generate_risk_assessment(risk_scores: dict[str, int], overall_risk: str) -> str:
    """Generate human-readable risk assessment."""
    if overall_risk == "critical":
        return "Critical risk level - immediate attention required"
    elif overall_risk == "high":
        return "High risk level - review and remediation needed"
    elif overall_risk == "medium":
        return "Medium risk level - monitor and assess impact"
    elif overall_risk == "low":
        return "Low risk level - minimal concern"
    else:
        return "No changes detected"

def _generate_change_summary(changes: list[dict[str, Any]]) -> str:
    """Generate summary of registry changes."""
    if not changes:
        return "No registry changes detected"

    change_types = {}
    for change in changes:
        change_type = change.get('type', 'unknown')
        change_types[change_type] = change_types.get(change_type, 0) + 1

    summary_parts = [f"Total changes: {len(changes)}"]
    for change_type, count in change_types.items():
        summary_parts.append(f"{change_type}: {count}")

    return "; ".join(summary_parts)

def _extract_login_activity(registry_data: dict[str, Any]) -> dict[str, Any]:
    """Extract login activity from registry data."""
    # Mock implementation for demonstration
    return {
        "login_events": [
            {
                "timestamp": "2024-01-01T08:00:00Z",
                "user": "admin",
                "event_type": "logon",
                "source": "interactive",
                "session_id": "1"
            },
            {
                "timestamp": "2024-01-01T17:30:00Z",
                "user": "admin",
                "event_type": "logoff",
                "source": "interactive",
                "session_id": "1"
            }
        ],
        "total_logins": 1,
        "total_logoffs": 1,
        "active_sessions": 0
    }

def _extract_application_usage(registry_data: dict[str, Any]) -> dict[str, Any]:
    """Extract application usage patterns from registry."""
    # Mock implementation for demonstration
    return {
        "applications": [
            {
                "name": "Microsoft Word",
                "last_used": "2024-01-01T14:30:00Z",
                "usage_count": 5,
                "install_date": "2023-12-01T00:00:00Z"
            },
            {
                "name": "Google Chrome",
                "last_used": "2024-01-01T16:45:00Z",
                "usage_count": 12,
                "install_date": "2023-11-15T00:00:00Z"
            }
        ],
        "total_applications": 2,
        "most_used_app": "Google Chrome"
    }

def _extract_file_access_patterns(registry_data: dict[str, Any]) -> dict[str, Any]:
    """Extract file access patterns from registry."""
    # Mock implementation for demonstration
    return {
        "recent_files": [
            {
                "path": "C:\\Users\\admin\\Documents\\report.docx",
                "last_accessed": "2024-01-01T15:20:00Z",
                "access_count": 3
            },
            {
                "path": "C:\\Users\\admin\\Downloads\\presentation.pptx",
                "last_accessed": "2024-01-01T16:10:00Z",
                "access_count": 1
            }
        ],
        "file_types": {
            "docx": 1,
            "pptx": 1
        },
        "total_recent_files": 2
    }

def _extract_network_activity(registry_data: dict[str, Any]) -> dict[str, Any]:
    """Extract network activity from registry."""
    # Mock implementation for demonstration
    return {
        "network_connections": [
            {
                "remote_host": "192.168.1.100",
                "port": 80,
                "protocol": "TCP",
                "last_connected": "2024-01-01T14:15:00Z"
            }
        ],
        "dns_queries": [
            {
                "domain": "google.com",
                "resolved_ip": "142.250.190.78",
                "query_time": "2024-01-01T14:20:00Z"
            }
        ],
        "total_connections": 1,
        "total_dns_queries": 1
    }

def _extract_system_interactions(registry_data: dict[str, Any]) -> dict[str, Any]:
    """Extract system interaction patterns from registry."""
    # Mock implementation for demonstration
    return {
        "system_events": [
            {
                "event_type": "service_start",
                "service_name": "Windows Update",
                "timestamp": "2024-01-01T09:00:00Z"
            },
            {
                "event_type": "registry_modification",
                "key_path": "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
                "timestamp": "2024-01-01T10:30:00Z"
            }
        ],
        "total_events": 2,
        "event_types": ["service_start", "registry_modification"]
    }

def _correlate_user_activities(login_activity: dict[str, Any], application_usage: dict[str, Any],
                              file_access_patterns: dict[str, Any], network_activity: dict[str, Any],
                              system_interactions: dict[str, Any], user_context: dict[str, Any]) -> dict[str, Any]:
    """Correlate different types of user activities."""
    # Mock implementation for demonstration
    return {
        "activity_correlation": {
            "login_to_app_usage": "User accessed applications after login",
            "app_usage_to_file_access": "Applications accessed files during usage",
            "file_access_to_network": "File operations may have triggered network activity"
        },
        "timeline_events": [
            {
                "timestamp": "2024-01-01T08:00:00Z",
                "event": "User login",
                "category": "authentication"
            },
            {
                "timestamp": "2024-01-01T14:30:00Z",
                "event": "Microsoft Word usage",
                "category": "application"
            },
            {
                "timestamp": "2024-01-01T15:20:00Z",
                "event": "Document access",
                "category": "file_access"
            }
        ],
        "correlation_score": 0.85
    }

def _generate_activity_timeline(correlated_activity: dict[str, Any]) -> dict[str, Any]:
    """Generate chronological timeline of user activities."""
    # Mock implementation for demonstration
    return {
        "timeline_start": "2024-01-01T08:00:00Z",
        "timeline_end": "2024-01-01T17:30:00Z",
        "total_events": 6,
        "activity_periods": [
            {
                "period": "08:00-12:00",
                "activities": ["login", "system_startup"],
                "activity_count": 2
            },
            {
                "period": "12:00-17:00",
                "activities": ["application_usage", "file_access", "network_activity"],
                "activity_count": 3
            },
            {
                "period": "17:00-18:00",
                "activities": ["logoff"],
                "activity_count": 1
            }
        ]
    }

def _generate_user_behavior_profile(correlated_activity: dict[str, Any]) -> dict[str, Any]:
    """Generate user behavior profile based on activities."""
    # Mock implementation for demonstration
    return {
        "user_type": "office_worker",
        "typical_work_hours": "08:00-17:00",
        "common_applications": ["Microsoft Office", "Web Browser"],
        "file_access_patterns": "document_centric",
        "network_behavior": "standard_office_usage",
        "risk_profile": "low",
        "behavior_anomalies": []
    }

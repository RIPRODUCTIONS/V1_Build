"""
Static Malware Analyzer Module

This module provides comprehensive static analysis capabilities for malware samples,
including PE structure analysis, string extraction, pattern scanning, and file hash calculation.
"""

import hashlib
import logging
import os
import re
import struct
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)


class StaticAnalysisError(Exception):
    """Custom exception for static analysis errors."""
    pass


class FileFormatError(StaticAnalysisError):
    """Exception raised when file format is not supported."""
    pass


class AnalysisError(StaticAnalysisError):
    """Exception raised when analysis fails."""
    pass


def analyze_pe_structure(sample_data: bytes) -> Dict[str, Any]:
    """
    Analyze PE file structure and metadata.

    Args:
        sample_data: Raw bytes of the PE file

    Returns:
        Dictionary containing PE structure analysis results

    Raises:
        FileFormatError: If file is not a valid PE file
        AnalysisError: If analysis fails
    """
    try:
    logger.info("Starting PE structure analysis")

        # Validate PE header
        if not _is_valid_pe_file(sample_data):
            raise FileFormatError("File is not a valid PE file")

        # Parse DOS header
        dos_header = _parse_dos_header(sample_data)

        # Parse PE header
        pe_header = _parse_pe_header(sample_data, dos_header)

        # Parse optional header
        optional_header = _parse_optional_header(sample_data, pe_header)

        # Parse section headers
        section_headers = _parse_section_headers(sample_data, pe_header)

        # Parse import table
        import_table = _parse_import_table(sample_data, pe_header, optional_header)

        # Parse export table
        export_table = _parse_export_table(sample_data, pe_header, optional_header)

        # Parse resource table
        resource_table = _parse_resource_table(sample_data, pe_header, optional_header)

        # Analyze PE characteristics
        characteristics = _analyze_pe_characteristics(pe_header, optional_header)

        result = {
            "dos_header": dos_header,
            "pe_header": pe_header,
            "optional_header": optional_header,
            "section_headers": section_headers,
            "import_table": import_table,
            "export_table": export_table,
            "resource_table": resource_table,
            "characteristics": characteristics,
            "analysis_timestamp": _get_timestamp(),
            "file_size": len(sample_data)
        }

        logger.info("PE structure analysis completed successfully")
        return result

    except Exception as e:
        logger.error(f"PE structure analysis failed: {e}")
        raise AnalysisError(f"PE analysis failed: {e}")


def extract_strings(sample_data: bytes) -> List[str]:
    """
    Extract printable strings from binary.

    Args:
        sample_data: Raw bytes of the file

    Returns:
        List of extracted strings

    Raises:
        AnalysisError: If string extraction fails
    """
    try:
    logger.info("Starting string extraction")

        strings = []
        min_length = 4  # Minimum string length

        # Extract ASCII strings
        ascii_strings = _extract_ascii_strings(sample_data, min_length)
        strings.extend(ascii_strings)

        # Extract Unicode strings
        unicode_strings = _extract_unicode_strings(sample_data, min_length)
        strings.extend(unicode_strings)

        # Filter and clean strings
        filtered_strings = _filter_strings(strings)

        # Remove duplicates while preserving order
        unique_strings = list(dict.fromkeys(filtered_strings))

        logger.info(f"String extraction completed. Found {len(unique_strings)} unique strings")
        return unique_strings

    except Exception as e:
        logger.error(f"String extraction failed: {e}")
        raise AnalysisError(f"String extraction failed: {e}")


def scan_for_patterns(sample_data: bytes) -> Dict[str, Any]:
    """
    Scan for suspicious patterns and YARA rules.

    Args:
        sample_data: Raw bytes of the file

    Returns:
        Dictionary containing pattern scan results

    Raises:
        AnalysisError: If pattern scanning fails
    """
    try:
    logger.info("Starting pattern scanning")

        patterns = {
            "suspicious_patterns": [],
            "yara_matches": [],
            "entropy_analysis": {},
            "encryption_indicators": [],
            "packer_indicators": [],
            "malware_families": []
        }

        # Scan for suspicious patterns
        suspicious = _scan_suspicious_patterns(sample_data)
        patterns["suspicious_patterns"] = suspicious

        # Apply YARA rules
        yara_matches = _apply_yara_rules(sample_data)
        patterns["yara_matches"] = yara_matches

        # Analyze entropy
        entropy_analysis = _analyze_entropy(sample_data)
        patterns["entropy_analysis"] = entropy_analysis

        # Detect encryption indicators
        encryption_indicators = _detect_encryption(sample_data)
        patterns["encryption_indicators"] = encryption_indicators

        # Detect packer indicators
        packer_indicators = _detect_packers(sample_data)
        patterns["packer_indicators"] = packer_indicators

        # Identify malware families
        malware_families = _identify_malware_families(patterns)
        patterns["malware_families"] = malware_families

        logger.info("Pattern scanning completed successfully")
        return patterns

    except Exception as e:
        logger.error(f"Pattern scanning failed: {e}")
        raise AnalysisError(f"Pattern scanning failed: {e}")


def calculate_file_hashes(sample_data: bytes) -> Dict[str, str]:
    """
    Calculate various file hashes.

    Args:
        sample_data: Raw bytes of the file

    Returns:
        Dictionary containing different hash values

    Raises:
        AnalysisError: If hash calculation fails
    """
    try:
        logger.info("Starting hash calculation")

        hashes = {}

        # Calculate MD5
        md5_hash = hashlib.md5(sample_data).hexdigest()
        hashes["md5"] = md5_hash

        # Calculate SHA1
        sha1_hash = hashlib.sha1(sample_data).hexdigest()
        hashes["sha1"] = sha1_hash

        # Calculate SHA256
        sha256_hash = hashlib.sha256(sample_data).hexdigest()
        hashes["sha256"] = sha256_hash

        # Calculate SHA512
        sha512_hash = hashlib.sha512(sample_data).hexdigest()
        hashes["sha512"] = sha512_hash

        # Calculate SSDeep (fuzzy hash)
        ssdeep_hash = _calculate_ssdeep(sample_data)
        if ssdeep_hash:
            hashes["ssdeep"] = ssdeep_hash

        # Calculate TLSH (trend micro locality sensitive hash)
        tlsh_hash = _calculate_tlsh(sample_data)
        if tlsh_hash:
            hashes["tlsh"] = tlsh_hash

        logger.info("Hash calculation completed successfully")
        return hashes

    except Exception as e:
        logger.error(f"Hash calculation failed: {e}")
        raise AnalysisError(f"Hash calculation failed: {e}")


def analyze_imports_exports(pe_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze PE imports and exports.

    Args:
        pe_data: PE structure analysis results

    Returns:
        Dictionary containing import/export analysis

    Raises:
        AnalysisError: If analysis fails
    """
    try:
    logger.info("Starting import/export analysis")

        analysis = {
            "import_analysis": {},
            "export_analysis": {},
            "suspicious_imports": [],
            "suspicious_exports": [],
            "api_usage_patterns": [],
            "risk_assessment": {}
        }

        # Analyze imports
        import_table = pe_data.get("import_table", {})
        if import_table:
            analysis["import_analysis"] = _analyze_imports(import_table)
            analysis["suspicious_imports"] = _identify_suspicious_imports(import_table)
            analysis["api_usage_patterns"] = _analyze_api_usage(import_table)

        # Analyze exports
        export_table = pe_data.get("export_table", {})
        if export_table:
            analysis["export_analysis"] = _analyze_exports(export_table)
            analysis["suspicious_exports"] = _identify_suspicious_exports(export_table)

        # Assess risk
        analysis["risk_assessment"] = _assess_import_export_risk(analysis)

        logger.info("Import/export analysis completed successfully")
        return analysis

    except Exception as e:
        logger.error(f"Import/export analysis failed: {e}")
        raise AnalysisError(f"Import/export analysis failed: {e}")


# Helper functions for PE analysis
def _is_valid_pe_file(data: bytes) -> bool:
    """Check if file is a valid PE file."""
    if len(data) < 64:
        return False

    # Check DOS header signature
    if data[:2] != b'MZ':
        return False

    # Check PE header offset
    try:
        pe_offset = struct.unpack('<I', data[60:64])[0]
        if pe_offset >= len(data) - 4:
            return False

        # Check PE signature
        if data[pe_offset:pe_offset + 4] != b'PE\x00\x00':
            return False

        return True
    except (struct.error, IndexError):
        return False


def _parse_dos_header(data: bytes) -> Dict[str, Any]:
    """Parse DOS header."""
    try:
        dos_header = {
            "signature": data[:2].hex().upper(),
            "last_page_size": struct.unpack('<H', data[2:4])[0],
            "pages_in_file": struct.unpack('<H', data[4:6])[0],
            "relocations": struct.unpack('<H', data[6:8])[0],
            "header_paragraphs": struct.unpack('<H', data[8:10])[0],
            "min_extra_paragraphs": struct.unpack('<H', data[10:12])[0],
            "max_extra_paragraphs": struct.unpack('<H', data[12:14])[0],
            "initial_ss": struct.unpack('<H', data[14:16])[0],
            "initial_sp": struct.unpack('<H', data[16:18])[0],
            "checksum": struct.unpack('<H', data[18:20])[0],
            "initial_ip": struct.unpack('<H', data[20:22])[0],
            "initial_cs": struct.unpack('<H', data[22:24])[0],
            "reloc_table_offset": struct.unpack('<H', data[24:26])[0],
            "overlay_number": struct.unpack('<H', data[26:28])[0],
            "pe_header_offset": struct.unpack('<I', data[60:64])[0]
        }
        return dos_header
    except struct.error as e:
        logger.warning(f"Failed to parse DOS header: {e}")
        return {}


def _parse_pe_header(data: bytes, dos_header: Dict[str, Any]) -> Dict[str, Any]:
    """Parse PE header."""
    try:
        pe_offset = dos_header.get("pe_header_offset", 0)
        if pe_offset >= len(data) - 24:
            return {}

        pe_header = {
            "signature": data[pe_offset:pe_offset + 4].hex().upper(),
            "machine": struct.unpack('<H', data[pe_offset + 4:pe_offset + 6])[0],
            "number_of_sections": struct.unpack('<H', data[pe_offset + 6:pe_offset + 8])[0],
            "time_date_stamp": struct.unpack('<I', data[pe_offset + 8:pe_offset + 12])[0],
            "pointer_to_symbol_table": struct.unpack('<I', data[pe_offset + 12:pe_offset + 16])[0],
            "number_of_symbols": struct.unpack('<I', data[pe_offset + 16:pe_offset + 20])[0],
            "size_of_optional_header": struct.unpack('<H', data[pe_offset + 20:pe_offset + 22])[0],
            "characteristics": struct.unpack('<H', data[pe_offset + 22:pe_offset + 24])[0]
        }
        return pe_header
    except struct.error as e:
        logger.warning(f"Failed to parse PE header: {e}")
        return {}


def _parse_optional_header(data: bytes, pe_header: Dict[str, Any]) -> Dict[str, Any]:
    """Parse optional header."""
    try:
        pe_offset = pe_header.get("pe_header_offset", 0)
        optional_size = pe_header.get("size_of_optional_header", 0)

        if optional_size == 0 or pe_offset + 24 + optional_size > len(data):
            return {}

        optional_start = pe_offset + 24
        optional_data = data[optional_start:optional_start + optional_size]

        optional_header = {
            "magic": struct.unpack('<H', optional_data[:2])[0],
            "major_linker_version": optional_data[2],
            "minor_linker_version": optional_data[3],
            "size_of_code": struct.unpack('<I', optional_data[4:8])[0],
            "size_of_initialized_data": struct.unpack('<I', optional_data[8:12])[0],
            "size_of_uninitialized_data": struct.unpack('<I', optional_data[12:16])[0],
            "address_of_entry_point": struct.unpack('<I', optional_data[16:20])[0],
            "base_of_code": struct.unpack('<I', optional_data[20:24])[0]
        }

        # Parse additional fields for PE32+ files
        if optional_header["magic"] == 0x20b:  # PE32+
            if len(optional_data) >= 32:
                optional_header["base_of_data"] = struct.unpack('<I', optional_data[24:28])[0]
                optional_header["image_base"] = struct.unpack('<Q', optional_data[28:36])[0]
        else:  # PE32
            if len(optional_data) >= 28:
                optional_header["base_of_data"] = struct.unpack('<I', optional_data[24:28])[0]
                optional_header["image_base"] = struct.unpack('<I', optional_data[28:32])[0]

        return optional_header
    except struct.error as e:
        logger.warning(f"Failed to parse optional header: {e}")
        return {}


def _parse_section_headers(data: bytes, pe_header: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse section headers."""
    try:
        sections = []
        num_sections = pe_header.get("number_of_sections", 0)
        pe_offset = pe_header.get("pe_header_offset", 0)
        optional_size = pe_header.get("size_of_optional_header", 0)

        section_start = pe_offset + 24 + optional_size

        for i in range(num_sections):
            if section_start + i * 40 + 40 > len(data):
                break

            section_data = data[section_start + i * 40:section_start + i * 40 + 40]

            section = {
                "name": section_data[:8].decode('ascii', errors='ignore').rstrip('\x00'),
                "virtual_size": struct.unpack('<I', section_data[8:12])[0],
                "virtual_address": struct.unpack('<I', section_data[12:16])[0],
                "size_of_raw_data": struct.unpack('<I', section_data[16:20])[0],
                "pointer_to_raw_data": struct.unpack('<I', section_data[20:24])[0],
                "pointer_to_relocations": struct.unpack('<I', section_data[24:28])[0],
                "pointer_to_line_numbers": struct.unpack('<I', section_data[28:32])[0],
                "number_of_relocations": struct.unpack('<H', section_data[32:34])[0],
                "number_of_line_numbers": struct.unpack('<H', section_data[34:36])[0],
                "characteristics": struct.unpack('<I', section_data[36:40])[0]
            }
            sections.append(section)

        return sections
    except struct.error as e:
        logger.warning(f"Failed to parse section headers: {e}")
        return []


def _parse_import_table(data: bytes, pe_header: Dict[str, Any], optional_header: Dict[str, Any]) -> Dict[str, Any]:
    """Parse import table."""
    try:
        # This is a simplified import table parser
        # In a real implementation, you would need to handle the complex structure
        return {
            "imports": [],
            "total_imports": 0,
            "dlls": []
        }
    except Exception as e:
        logger.warning(f"Failed to parse import table: {e}")
        return {}


def _parse_export_table(data: bytes, pe_header: Dict[str, Any], optional_header: Dict[str, Any]) -> Dict[str, Any]:
    """Parse export table."""
    try:
        # This is a simplified export table parser
        return {
            "exports": [],
            "total_exports": 0,
            "export_name": ""
        }
    except Exception as e:
        logger.warning(f"Failed to parse export table: {e}")
        return {}


def _parse_resource_table(data: bytes, pe_header: Dict[str, Any], optional_header: Dict[str, Any]) -> Dict[str, Any]:
    """Parse resource table."""
    try:
        # This is a simplified resource table parser
        return {
            "resources": [],
            "total_resources": 0
        }
    except Exception as e:
        logger.warning(f"Failed to parse resource table: {e}")
        return {}


def _analyze_pe_characteristics(pe_header: Dict[str, Any], optional_header: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze PE characteristics."""
    characteristics = {
        "is_dll": False,
        "is_executable": False,
        "is_system_file": False,
        "has_debug_info": False,
        "is_stripped": False
    }

    if pe_header:
        char = pe_header.get("characteristics", 0)
        characteristics["is_dll"] = bool(char & 0x2000)
        characteristics["is_executable"] = bool(char & 0x0002)
        characteristics["is_system_file"] = bool(char & 0x4000)
        characteristics["has_debug_info"] = bool(char & 0x0020)
        characteristics["is_stripped"] = not bool(char & 0x0020)

    return characteristics


# Helper functions for string extraction
def _extract_ascii_strings(data: bytes, min_length: int) -> List[str]:
    """Extract ASCII strings from binary data."""
    strings = []
    current_string = ""

    for byte in data:
        if 32 <= byte <= 126:  # Printable ASCII
            current_string += chr(byte)
        else:
            if len(current_string) >= min_length:
                strings.append(current_string)
            current_string = ""

    # Don't forget the last string
    if len(current_string) >= min_length:
        strings.append(current_string)

    return strings


def _extract_unicode_strings(data: bytes, min_length: int) -> List[str]:
    """Extract Unicode strings from binary data."""
    strings = []

    # Look for UTF-16LE strings
    for i in range(0, len(data) - 1, 2):
        if i + 1 < len(data):
            char = data[i] | (data[i + 1] << 8)
            if 32 <= char <= 126:  # Printable ASCII in Unicode
                # Try to extract a string starting from this position
                unicode_string = _extract_unicode_string_from_position(data, i, min_length)
                if unicode_string:
                    strings.append(unicode_string)

    return strings


def _extract_unicode_string_from_position(data: bytes, start_pos: int, min_length: int) -> Optional[str]:
    """Extract Unicode string starting from a specific position."""
    try:
        string_chars = []
        pos = start_pos

        while pos + 1 < len(data):
            char = data[pos] | (data[pos + 1] << 8)
            if 32 <= char <= 126:  # Printable ASCII
                string_chars.append(chr(char))
                pos += 2
                        else:
                            break

        result = "".join(string_chars)
        return result if len(result) >= min_length else None
    except Exception:
        return None


def _filter_strings(strings: List[str]) -> List[str]:
    """Filter and clean extracted strings."""
    filtered = []

    for string in strings:
        # Remove strings that are mostly non-alphanumeric
        alphanumeric_ratio = sum(1 for c in string if c.isalnum()) / len(string)
        if alphanumeric_ratio < 0.3:
            continue

        # Remove very long strings (likely false positives)
        if len(string) > 1000:
            continue

        # Remove strings that are just repeated characters
        if len(set(string)) < 3:
            continue

        filtered.append(string)

    return filtered


# Helper functions for pattern scanning
def _scan_suspicious_patterns(data: bytes) -> List[Dict[str, Any]]:
    """Scan for suspicious patterns in binary data."""
    patterns = []

    # Common malware patterns
    malware_patterns = [
        (b"cmd.exe", "Command shell execution"),
        (b"powershell", "PowerShell execution"),
        (b"regsvr32", "DLL registration"),
        (b"rundll32", "DLL execution"),
        (b"schtasks", "Scheduled task creation"),
        (b"net user", "User account manipulation"),
        (b"wmic", "WMI command execution"),
        (b"certutil", "Certificate utility abuse"),
        (b"bitsadmin", "Background Intelligent Transfer Service"),
        (b"mshta", "HTML application execution")
    ]

    for pattern, description in malware_patterns:
        if pattern in data:
            patterns.append({
                "pattern": pattern.decode('ascii', errors='ignore'),
                "description": description,
                "severity": "medium"
            })

    # Look for suspicious URLs
    url_pattern = rb'https?://[^\s\x00]+'
    urls = re.findall(url_pattern, data)
    for url in urls:
        try:
            url_str = url.decode('ascii', errors='ignore')
            if _is_suspicious_url(url_str):
                patterns.append({
                    "pattern": url_str,
                    "description": "Suspicious URL",
                    "severity": "high"
                })
        except Exception:
            continue

    return patterns


def _is_suspicious_url(url: str) -> bool:
    """Check if URL is suspicious."""
    suspicious_domains = [
        "malware.com", "evil.com", "hack.com", "phish.com",
        "malicious.net", "suspicious.org", "dangerous.info"
    ]

    return any(domain in url.lower() for domain in suspicious_domains)


def _apply_yara_rules(data: bytes) -> List[Dict[str, Any]]:
    """Apply YARA rules to the sample."""
    # This would integrate with actual YARA engine
    # For now, return mock results
    return [
        {
            "rule_name": "Suspicious_Behavior",
            "rule_description": "Detects suspicious behavior patterns",
            "matched_strings": ["cmd.exe", "powershell"],
            "confidence": 0.8
        }
    ]


def _analyze_entropy(data: bytes) -> Dict[str, Any]:
    """Analyze entropy of different sections."""
    try:
        # Calculate overall entropy
        overall_entropy = _calculate_entropy(data)

        # Analyze entropy by chunks
        chunk_size = 1024
        entropy_chunks = []

        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            if len(chunk) >= 64:  # Minimum size for meaningful entropy
                chunk_entropy = _calculate_entropy(chunk)
                entropy_chunks.append(chunk_entropy)

        return {
            "overall_entropy": overall_entropy,
            "average_chunk_entropy": sum(entropy_chunks) / len(entropy_chunks) if entropy_chunks else 0,
            "entropy_distribution": {
                "low_entropy": sum(1 for e in entropy_chunks if e < 4.0),
                "medium_entropy": sum(1 for e in entropy_chunks if 4.0 <= e <= 6.0),
                "high_entropy": sum(1 for e in entropy_chunks if e > 6.0)
            }
        }
    except Exception as e:
        logger.warning(f"Entropy analysis failed: {e}")
        return {}


def _calculate_entropy(data: bytes) -> float:
    """Calculate Shannon entropy of data."""
    if not data:
        return 0.0

    # Count byte frequencies
    byte_counts = [0] * 256
    for byte in data:
        byte_counts[byte] += 1

    # Calculate entropy
    entropy = 0.0
    data_length = len(data)

    for count in byte_counts:
        if count > 0:
            probability = count / data_length
            entropy -= probability * (probability.bit_length() - 1)

    return entropy


def _detect_encryption(data: bytes) -> List[str]:
    """Detect encryption indicators."""
    indicators = []

    # High entropy is often an indicator of encryption
    entropy = _calculate_entropy(data)
    if entropy > 7.5:
        indicators.append("high_entropy_encryption")

    # Look for encryption-related strings
    encryption_patterns = [
        b"AES", b"RSA", b"DES", b"MD5", b"SHA", b"encrypt", b"decrypt",
        b"cipher", b"key", b"password", b"hash"
    ]

    for pattern in encryption_patterns:
        if pattern in data:
            indicators.append(f"encryption_pattern_{pattern.decode('ascii', errors='ignore').lower()}")

    return indicators


def _detect_packers(data: bytes) -> List[str]:
    """Detect packer indicators."""
    indicators = []

    # Common packer signatures
    packer_signatures = [
        (b"UPX", "UPX packer"),
        (b"ASPack", "ASPack packer"),
        (b"PECompact", "PECompact packer"),
        (b"Armadillo", "Armadillo packer"),
        (b"Themida", "Themida packer"),
        (b"VMProtect", "VMProtect packer")
    ]

    for signature, description in packer_signatures:
        if signature in data:
            indicators.append(description)

    # Check for suspicious section names
    suspicious_sections = [b".upx", b".aspack", b".packed", b".encrypted"]
    for section in suspicious_sections:
        if section in data:
            indicators.append(f"suspicious_section_{section.decode('ascii', errors='ignore')}")

    return indicators


def _identify_malware_families(patterns: Dict[str, Any]) -> List[str]:
    """Identify potential malware families based on patterns."""
    families = []

    # Simple family identification based on patterns
    if any("cmd.exe" in p.get("pattern", "") for p in patterns.get("suspicious_patterns", [])):
        families.append("Command_Execution_Trojan")

    if any("powershell" in p.get("pattern", "") for p in patterns.get("suspicious_patterns", [])):
        families.append("PowerShell_Malware")

    if patterns.get("packer_indicators"):
        families.append("Packed_Malware")

    if patterns.get("encryption_indicators"):
        families.append("Encrypted_Malware")

    return families


# Helper functions for hash calculation
def _calculate_ssdeep(data: bytes) -> Optional[str]:
    """Calculate SSDeep fuzzy hash."""
    try:
        # This would integrate with actual SSDeep library
        # For now, return None
        return None
    except Exception:
        return None


def _calculate_tlsh(data: bytes) -> Optional[str]:
    """Calculate TLSH hash."""
    try:
        # This would integrate with actual TLSH library
        # For now, return None
        return None
    except Exception:
        return None


# Helper functions for import/export analysis
def _analyze_imports(import_table: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze import table."""
    return {
        "total_imports": import_table.get("total_imports", 0),
        "dll_count": len(import_table.get("dlls", [])),
        "api_categories": _categorize_apis(import_table)
    }


def _analyze_exports(export_table: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze export table."""
    return {
        "total_exports": export_table.get("total_exports", 0),
        "export_name": export_table.get("export_name", ""),
        "export_types": _categorize_exports(export_table)
    }


def _identify_suspicious_imports(import_table: Dict[str, Any]) -> List[str]:
    """Identify suspicious imports."""
    suspicious_apis = [
        "CreateRemoteThread", "WriteProcessMemory", "VirtualAllocEx",
        "SetWindowsHookEx", "SetTimer", "CreateTimerQueueTimer",
        "RegCreateKey", "RegSetValue", "WSAConnect", "connect"
    ]

    found_suspicious = []
    imports = import_table.get("imports", [])

    for api in suspicious_apis:
        if any(api.lower() in imp.lower() for imp in imports):
            found_suspicious.append(api)

    return found_suspicious


def _identify_suspicious_exports(export_table: Dict[str, Any]) -> List[str]:
    """Identify suspicious exports."""
    suspicious_exports = [
        "DllRegisterServer", "DllUnregisterServer", "DllInstall",
        "Start", "Stop", "ServiceMain"
    ]

    found_suspicious = []
    exports = export_table.get("exports", [])

    for export in suspicious_exports:
        if any(export.lower() in exp.lower() for exp in exports):
            found_suspicious.append(export)

    return found_suspicious


def _analyze_api_usage(import_table: Dict[str, Any]) -> List[str]:
    """Analyze API usage patterns."""
    patterns = []
    imports = import_table.get("imports", [])

    # Check for process injection patterns
    if any("CreateRemoteThread" in imp for imp in imports):
        patterns.append("process_injection")

    # Check for persistence patterns
    if any("RegCreateKey" in imp for imp in imports):
        patterns.append("registry_persistence")

    # Check for network patterns
    if any("WSAConnect" in imp for imp in imports):
        patterns.append("network_communication")

    return patterns


def _categorize_apis(import_table: Dict[str, Any]) -> Dict[str, int]:
    """Categorize APIs by function."""
    categories = {
        "process_management": 0,
        "memory_management": 0,
        "file_system": 0,
        "registry": 0,
        "network": 0,
        "system_services": 0
    }

    imports = import_table.get("imports", [])

    for imp in imports:
        imp_lower = imp.lower()
        if any(api in imp_lower for api in ["createprocess", "openprocess", "terminateprocess"]):
            categories["process_management"] += 1
        elif any(api in imp_lower for api in ["virtualalloc", "writeprocessmemory", "readprocessmemory"]):
            categories["memory_management"] += 1
        elif any(api in imp_lower for api in ["createfile", "readfile", "writefile"]):
            categories["file_system"] += 1
        elif any(api in imp_lower for api in ["regcreatekey", "regsetvalue", "regqueryvalue"]):
            categories["registry"] += 1
        elif any(api in imp_lower for api in ["wsaconnect", "connect", "send", "recv"]):
            categories["network"] += 1
        elif any(api in imp_lower for api in ["getsystemtime", "sleep", "gettickcount"]):
            categories["system_services"] += 1

    return categories


def _categorize_exports(export_table: Dict[str, Any]) -> Dict[str, int]:
    """Categorize exports by function."""
    categories = {
        "dll_functions": 0,
        "service_functions": 0,
        "custom_functions": 0
    }

    exports = export_table.get("exports", [])

    for exp in exports:
        exp_lower = exp.lower()
        if any(func in exp_lower for func in ["dllregisterserver", "dllunregisterserver"]):
            categories["dll_functions"] += 1
        elif any(func in exp_lower for func in ["start", "stop", "servicemain"]):
            categories["service_functions"] += 1
        else:
            categories["custom_functions"] += 1

    return categories


def _assess_import_export_risk(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Assess risk based on import/export analysis."""
    risk_score = 0
    risk_factors = []

    # Assess based on suspicious imports
    suspicious_imports = analysis.get("suspicious_imports", [])
    if suspicious_imports:
        risk_score += len(suspicious_imports) * 0.2
        risk_factors.extend(suspicious_imports)

    # Assess based on suspicious exports
    suspicious_exports = analysis.get("suspicious_exports", [])
    if suspicious_exports:
        risk_score += len(suspicious_exports) * 0.15
        risk_factors.extend(suspicious_exports)

    # Assess based on API usage patterns
    api_patterns = analysis.get("api_usage_patterns", [])
    if "process_injection" in api_patterns:
        risk_score += 0.3
        risk_factors.append("process_injection_capability")

    if "registry_persistence" in api_patterns:
        risk_score += 0.25
        risk_factors.append("persistence_capability")

    if "network_communication" in api_patterns:
        risk_score += 0.2
        risk_factors.append("network_communication")

    # Normalize risk score
    risk_score = min(risk_score, 1.0)

    # Determine risk level
    if risk_score >= 0.7:
        risk_level = "high"
    elif risk_score >= 0.4:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "recommendations": _generate_risk_recommendations(risk_level, risk_factors)
    }


def _generate_risk_recommendations(risk_level: str, risk_factors: List[str]) -> List[str]:
    """Generate risk mitigation recommendations."""
    recommendations = []

    if risk_level == "high":
        recommendations.append("Immediate containment and analysis required")
        recommendations.append("Isolate from network and other systems")
        recommendations.append("Perform deep behavioral analysis")

    if risk_level in ["medium", "high"]:
        recommendations.append("Monitor system behavior closely")
        recommendations.append("Review network connections")
        recommendations.append("Check for persistence mechanisms")

    if "process_injection_capability" in risk_factors:
        recommendations.append("Monitor for unusual process creation")
        recommendations.append("Review process tree relationships")

    if "persistence_capability" in risk_factors:
        recommendations.append("Check registry for suspicious entries")
        recommendations.append("Review startup programs and services")

    if "network_communication" in risk_factors:
        recommendations.append("Monitor network traffic")
        recommendations.append("Review firewall rules")

    return recommendations


def _get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()

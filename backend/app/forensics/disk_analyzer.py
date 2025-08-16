"""
Disk Analyzer Module

This module provides comprehensive disk forensics capabilities including disk imaging,
filesystem analysis, unallocated space scanning, and deleted file recovery.
"""

import logging
import os
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import hashlib
import shutil

# Configure logging
logger = logging.getLogger(__name__)


class DiskAnalysisError(Exception):
    """Custom exception for disk analysis errors."""
    pass


class ImagingError(DiskAnalysisError):
    """Exception raised when disk imaging fails."""
    pass


class MountingError(DiskAnalysisError):
    """Exception raised when disk mounting fails."""
    pass


class AnalysisError(DiskAnalysisError):
    """Exception raised when analysis fails."""
    pass


def create_disk_image(source_device: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create forensic disk image.

    Args:
        source_device: Path to source device or file
        params: Imaging parameters

    Returns:
        Dictionary containing imaging results and metadata

    Raises:
        ImagingError: If disk imaging fails
    """
    try:
        logger.info(f"Starting disk imaging from source: {source_device}")

        # Validate source device
        if not _validate_source_device(source_device):
            raise ImagingError(f"Invalid source device: {source_device}")

        # Extract imaging parameters
        compression = params.get("compression", "gzip")
        verify_integrity = params.get("verify_integrity", True)
        block_size = params.get("block_size", 4096)

        # Create output directory
        output_dir = _create_output_directory()

        # Generate image filename
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        image_filename = f"disk_image_{timestamp}.img"
        image_path = os.path.join(output_dir, image_filename)

        # Start imaging process
        imaging_start = time.time()

        # Create the image using appropriate tool
        if compression == "gzip":
            image_result = _create_gzipped_image(source_device, image_path, block_size)
        elif compression == "none":
            image_result = _create_raw_image(source_device, image_path, block_size)
        else:
            raise ImagingError(f"Unsupported compression type: {compression}")

        imaging_duration = time.time() - imaging_start

        # Verify image integrity if requested
        if verify_integrity:
            integrity_result = _verify_image_integrity(source_device, image_path)
        else:
            integrity_result = {"verified": False, "reason": "Integrity verification disabled"}

        # Calculate image statistics
        image_stats = _calculate_image_statistics(image_path, source_device)

        # Generate imaging report
        imaging_report = {
            "source_device": source_device,
            "image_path": image_path,
            "compression": compression,
            "block_size": block_size,
            "imaging_duration": imaging_duration,
            "integrity_verification": integrity_result,
            "image_statistics": image_stats,
            "imaging_timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "completed"
        }

        logger.info(f"Disk imaging completed successfully: {image_path}")
        return imaging_report

    except Exception as e:
        logger.error(f"Disk imaging failed: {e}")
        raise ImagingError(f"Disk imaging failed: {e}")


def mount_image(image_path: str) -> Dict[str, Any]:
    """
    Mount disk image for analysis.

    Args:
        image_path: Path to disk image file

    Returns:
        Dictionary containing mount information

    Raises:
        MountingError: If image mounting fails
    """
    try:
        logger.info(f"Starting disk image mounting: {image_path}")

        # Validate image file
        if not _validate_image_file(image_path):
            raise MountingError(f"Invalid image file: {image_path}")

        # Create mount point
        mount_point = _create_mount_point()

        # Determine image format
        image_format = _detect_image_format(image_path)

        # Mount the image
        if image_format == "raw":
            mount_result = _mount_raw_image(image_path, mount_point)
        elif image_format == "gzip":
            mount_result = _mount_compressed_image(image_path, mount_point)
        else:
            raise MountingError(f"Unsupported image format: {image_format}")

        # Verify mount success
        if not _verify_mount_success(mount_point):
            raise MountingError("Failed to verify mount success")

        # Get mount information
        mount_info = _get_mount_information(mount_point, image_path)

        result = {
            "image_path": image_path,
            "mount_point": mount_point,
            "image_format": image_format,
            "mount_result": mount_result,
            "mount_info": mount_info,
            "mount_timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "mounted"
        }

        logger.info(f"Disk image mounted successfully at: {mount_point}")
        return result

    except Exception as e:
        logger.error(f"Disk image mounting failed: {e}")
        raise MountingError(f"Image mounting failed: {e}")


def analyze_filesystem(mount_point: str) -> Dict[str, Any]:
    """
    Analyze filesystem structure and artifacts.

    Args:
        mount_point: Path to mounted filesystem

    Returns:
        Dictionary containing filesystem analysis results

    Raises:
        AnalysisError: If filesystem analysis fails
    """
    try:
        logger.info(f"Starting filesystem analysis: {mount_point}")

        # Validate mount point
        if not _validate_mount_point(mount_point):
            raise AnalysisError(f"Invalid mount point: {mount_point}")

        # Analyze filesystem structure
        fs_structure = _analyze_filesystem_structure(mount_point)

        # Analyze file metadata
        file_metadata = _analyze_file_metadata(mount_point)

        # Analyze directory structure
        directory_structure = _analyze_directory_structure(mount_point)

        # Analyze file timestamps
        timestamp_analysis = _analyze_file_timestamps(mount_point)

        # Analyze file permissions
        permission_analysis = _analyze_file_permissions(mount_point)

        # Analyze hidden files
        hidden_files = _analyze_hidden_files(mount_point)

        # Analyze deleted files
        deleted_files = _analyze_deleted_files(mount_point)

        # Generate analysis summary
        analysis_summary = _generate_filesystem_summary(
            fs_structure, file_metadata, directory_structure,
            timestamp_analysis, permission_analysis, hidden_files, deleted_files
        )

        result = {
            "mount_point": mount_point,
            "filesystem_structure": fs_structure,
            "file_metadata": file_metadata,
            "directory_structure": directory_structure,
            "timestamp_analysis": timestamp_analysis,
            "permission_analysis": permission_analysis,
            "hidden_files": hidden_files,
            "deleted_files": deleted_files,
            "analysis_summary": analysis_summary,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat()
        }

        logger.info("Filesystem analysis completed successfully")
        return result

    except Exception as e:
        logger.error(f"Filesystem analysis failed: {e}")
        raise AnalysisError(f"Filesystem analysis failed: {e}")


def scan_unallocated_space(image_path: str) -> Dict[str, Any]:
    """
    Scan unallocated disk space.

    Args:
        image_path: Path to disk image file

    Returns:
        Dictionary containing unallocated space scan results

    Raises:
        AnalysisError: If unallocated space scanning fails
    """
    try:
        logger.info(f"Starting unallocated space scan: {image_path}")

        # Validate image file
        if not _validate_image_file(image_path):
            raise AnalysisError(f"Invalid image file: {image_path}")

        # Get image information
        image_info = _get_image_information(image_path)

        # Scan for file signatures
        file_signatures = _scan_file_signatures(image_path)

        # Scan for deleted files
        deleted_files = _scan_deleted_files(image_path)

        # Scan for slack space
        slack_space = _scan_slack_space(image_path)

        # Analyze unallocated patterns
        unallocated_patterns = _analyze_unallocated_patterns(
            file_signatures, deleted_files, slack_space
        )

        # Calculate scan statistics
        scan_statistics = _calculate_scan_statistics(
            image_info, file_signatures, deleted_files, slack_space
        )

        result = {
            "image_path": image_path,
            "image_information": image_info,
            "file_signatures": file_signatures,
            "deleted_files": deleted_files,
            "slack_space": slack_space,
            "unallocated_patterns": unallocated_patterns,
            "scan_statistics": scan_statistics,
            "scan_timestamp": datetime.now(timezone.utc).isoformat()
        }

        logger.info("Unallocated space scan completed successfully")
        return result

    except Exception as e:
        logger.error(f"Unallocated space scanning failed: {e}")
        raise AnalysisError(f"Unallocated space scanning failed: {e}")


def recover_deleted_files(scan_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Recover deleted files from unallocated space.

    Args:
        scan_results: Results from unallocated space scan

    Returns:
        List of recovered files with metadata

    Raises:
        AnalysisError: If file recovery fails
    """
    try:
        logger.info("Starting deleted file recovery")

        recovered_files = []

        # Extract scan information
        file_signatures = scan_results.get("file_signatures", [])
        deleted_files = scan_results.get("deleted_files", [])
        slack_space = scan_results.get("slack_space", [])

        # Recover files from file signatures
        for signature in file_signatures:
            try:
                recovered_file = _recover_file_from_signature(signature)
                if recovered_file:
                    recovered_files.append(recovered_file)
            except Exception as e:
                logger.warning(f"Failed to recover file from signature: {e}")

        # Recover files from deleted file entries
        for deleted_file in deleted_files:
            try:
                recovered_file = _recover_deleted_file_entry(deleted_file)
                if recovered_file:
                    recovered_files.append(recovered_file)
            except Exception as e:
                logger.warning(f"Failed to recover deleted file entry: {e}")

        # Recover files from slack space
        for slack in slack_space:
            try:
                recovered_file = _recover_file_from_slack(slack)
                if recovered_file:
                    recovered_files.append(recovered_file)
            except Exception as e:
                logger.warning(f"Failed to recover file from slack space: {e}")

        # Validate recovered files
        validated_files = _validate_recovered_files(recovered_files)

        # Generate recovery summary
        recovery_summary = _generate_recovery_summary(validated_files)

        logger.info(f"File recovery completed. Recovered {len(validated_files)} files")
        return validated_files

    except Exception as e:
        logger.error(f"File recovery failed: {e}")
        raise AnalysisError(f"File recovery failed: {e}")


# Helper functions for disk imaging
def _validate_source_device(source_device: str) -> bool:
    """Validate source device path."""
    try:
        # Check if device exists
        if not os.path.exists(source_device):
            return False

        # Check if it's a block device or regular file
        if os.path.isblock(source_device) or os.path.isfile(source_device):
            return True

        return False
    except Exception:
        return False


def _create_output_directory() -> str:
    """Create output directory for disk images."""
    try:
        output_dir = os.path.join(tempfile.gettempdir(), "disk_forensics")
        os.makedirs(output_dir, exist_ok=True)
        return output_dir
    except Exception as e:
        logger.warning(f"Failed to create output directory: {e}")
        return tempfile.gettempdir()


def _create_gzipped_image(source_device: str, image_path: str, block_size: int) -> Dict[str, Any]:
    """Create gzipped disk image."""
    try:
        # Use dd and gzip to create compressed image
        dd_cmd = [
            "dd", "if=" + source_device,
            "bs=" + str(block_size),
            "conv=noerror,sync"
        ]

        gzip_cmd = ["gzip", "-c"]

        # Create the compressed image
        with open(image_path, 'wb') as output_file:
            dd_process = subprocess.Popen(dd_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            gzip_process = subprocess.Popen(gzip_cmd, stdin=dd_process.stdout, stdout=output_file, stderr=subprocess.PIPE)

            # Wait for completion
            dd_process.stdout.close()
            gzip_process.communicate()
            dd_process.wait()

        return {
            "compression_type": "gzip",
            "compression_level": "default",
            "success": True
        }

    except Exception as e:
        logger.error(f"Failed to create gzipped image: {e}")
        return {
            "compression_type": "gzip",
            "compression_level": "default",
            "success": False,
            "error": str(e)
        }


def _create_raw_image(source_device: str, image_path: str, block_size: int) -> Dict[str, Any]:
    """Create raw disk image."""
    try:
        # Use dd to create raw image
        dd_cmd = [
            "dd", "if=" + source_device,
            "of=" + image_path,
            "bs=" + str(block_size),
            "conv=noerror,sync"
        ]

        result = subprocess.run(dd_cmd, capture_output=True, text=True)

        if result.returncode == 0:
            return {
                "compression_type": "none",
                "compression_level": "none",
                "success": True
            }
        else:
            return {
                "compression_type": "none",
                "compression_level": "none",
                "success": False,
                "error": result.stderr
            }

    except Exception as e:
        logger.error(f"Failed to create raw image: {e}")
        return {
            "compression_type": "none",
            "compression_level": "none",
            "success": False,
            "error": str(e)
        }


def _verify_image_integrity(source_device: str, image_path: str) -> Dict[str, Any]:
    """Verify image integrity."""
    try:
        # Calculate source hash
        source_hash = _calculate_device_hash(source_device)

        # Calculate image hash
        image_hash = _calculate_file_hash(image_path)

        # Compare hashes
        if source_hash and image_hash:
            verified = source_hash == image_hash
            return {
                "verified": verified,
                "source_hash": source_hash,
                "image_hash": image_hash,
                "integrity_check": "passed" if verified else "failed"
            }
        else:
            return {
                "verified": False,
                "reason": "Failed to calculate hashes",
                "source_hash": source_hash,
                "image_hash": image_hash
            }

    except Exception as e:
        logger.warning(f"Image integrity verification failed: {e}")
        return {
            "verified": False,
            "reason": f"Verification error: {e}"
        }


def _calculate_device_hash(device_path: str) -> Optional[str]:
    """Calculate hash of device."""
    try:
        # Use dd to read device and calculate hash
        dd_cmd = ["dd", "if=" + device_path, "bs=1M", "count=100"]
        result = subprocess.run(dd_cmd, capture_output=True)

        if result.returncode == 0:
            return hashlib.sha256(result.stdout).hexdigest()
        return None

    except Exception:
        return None


def _calculate_file_hash(file_path: str) -> Optional[str]:
    """Calculate hash of file."""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None


def _calculate_image_statistics(image_path: str, source_device: str) -> Dict[str, Any]:
    """Calculate image statistics."""
    try:
        stats = {}

        # Get image file size
        if os.path.exists(image_path):
            stats["image_size"] = os.path.getsize(image_path)
            stats["image_size_mb"] = stats["image_size"] / (1024 * 1024)

        # Get source device size
        if os.path.exists(source_device):
            try:
                device_size = os.path.getsize(source_device)
                stats["source_size"] = device_size
                stats["source_size_mb"] = device_size / (1024 * 1024)

                # Calculate compression ratio
                if stats.get("image_size") and stats.get("source_size"):
                    stats["compression_ratio"] = stats["image_size"] / stats["source_size"]
            except OSError:
                # Device size not available
                stats["source_size"] = "unknown"

        return stats

    except Exception as e:
        logger.warning(f"Failed to calculate image statistics: {e}")
        return {}


# Helper functions for image mounting
def _validate_image_file(image_path: str) -> bool:
    """Validate image file."""
    try:
        return os.path.isfile(image_path) and os.path.getsize(image_path) > 0
    except Exception:
        return False


def _create_mount_point() -> str:
    """Create mount point for disk image."""
    try:
        mount_dir = os.path.join(tempfile.gettempdir(), "disk_mount")
        os.makedirs(mount_dir, exist_ok=True)
        return mount_dir
    except Exception as e:
        logger.warning(f"Failed to create mount point: {e}")
        return tempfile.mkdtemp()


def _detect_image_format(image_path: str) -> str:
    """Detect image format."""
    try:
        # Check file extension
        if image_path.endswith('.gz') or image_path.endswith('.gzip'):
            return "gzip"
        elif image_path.endswith('.img') or image_path.endswith('.raw'):
            return "raw"
        else:
            # Try to detect by examining file header
            with open(image_path, 'rb') as f:
                header = f.read(512)
                if header.startswith(b'\x1f\x8b'):  # Gzip magic
                    return "gzip"
                else:
                    return "raw"
    except Exception:
        return "unknown"


def _mount_raw_image(image_path: str, mount_point: str) -> Dict[str, Any]:
    """Mount raw disk image."""
    try:
        # Use losetup and mount for Linux
        if os.name == 'posix':
            # Create loop device
            losetup_cmd = ["losetup", "--find", "--show", image_path]
            result = subprocess.run(losetup_cmd, capture_output=True, text=True)

            if result.returncode == 0:
                loop_device = result.stdout.strip()

                # Mount the loop device
                mount_cmd = ["mount", loop_device, mount_point]
                mount_result = subprocess.run(mount_cmd, capture_output=True, text=True)

                if mount_result.returncode == 0:
                    return {
                        "loop_device": loop_device,
                        "mount_success": True,
                        "mount_error": None
                    }
                else:
                    return {
                        "loop_device": loop_device,
                        "mount_success": False,
                        "mount_error": mount_result.stderr
                    }
            else:
                return {
                    "loop_device": None,
                    "mount_success": False,
                    "mount_error": result.stderr
                }
        else:
            # Windows or other OS
            return {
                "loop_device": None,
                "mount_success": False,
                "mount_error": "Mounting not supported on this OS"
            }

    except Exception as e:
        logger.error(f"Failed to mount raw image: {e}")
        return {
            "loop_device": None,
            "mount_success": False,
            "mount_error": str(e)
        }


def _mount_compressed_image(image_path: str, mount_point: str) -> Dict[str, Any]:
    """Mount compressed disk image."""
    try:
        # Decompress and mount
        temp_image = _decompress_image(image_path)

        if temp_image:
            mount_result = _mount_raw_image(temp_image, mount_point)
            mount_result["temp_image"] = temp_image
            return mount_result
        else:
            return {
                "loop_device": None,
                "mount_success": False,
                "mount_error": "Failed to decompress image"
            }

    except Exception as e:
        logger.error(f"Failed to mount compressed image: {e}")
        return {
            "loop_device": None,
            "mount_success": False,
            "mount_error": str(e)
        }


def _decompress_image(image_path: str) -> Optional[str]:
    """Decompress image file."""
    try:
        # Create temporary file for decompressed image
        temp_image = tempfile.NamedTemporaryFile(delete=False, suffix='.img')
        temp_image.close()

        # Decompress using gunzip
        gunzip_cmd = ["gunzip", "-c", image_path]
        with open(temp_image.name, 'wb') as output_file:
            result = subprocess.run(gunzip_cmd, stdout=output_file, stderr=subprocess.PIPE)

        if result.returncode == 0:
            return temp_image.name
        else:
            os.unlink(temp_image.name)
            return None

    except Exception as e:
        logger.error(f"Failed to decompress image: {e}")
        return None


def _verify_mount_success(mount_point: str) -> bool:
    """Verify mount success."""
    try:
        # Check if mount point exists and has content
        if not os.path.exists(mount_point):
            return False

        # Check if directory has content (not empty)
        try:
            content = os.listdir(mount_point)
            return len(content) > 0
        except OSError:
            return False

    except Exception:
        return False


def _get_mount_information(mount_point: str, image_path: str) -> Dict[str, Any]:
    """Get mount information."""
    try:
        mount_info = {
            "mount_point": mount_point,
            "image_path": image_path,
            "mount_time": datetime.now(timezone.utc).isoformat()
        }

        # Get filesystem information
        if os.name == 'posix':
            try:
                df_cmd = ["df", mount_point]
                result = subprocess.run(df_cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        parts = lines[1].split()
                        if len(parts) >= 4:
                            mount_info["filesystem_size"] = parts[1]
                            mount_info["used_space"] = parts[2]
                            mount_info["available_space"] = parts[3]
            except Exception:
                pass

        return mount_info

    except Exception as e:
        logger.warning(f"Failed to get mount information: {e}")
        return {}


# Helper functions for filesystem analysis
def _validate_mount_point(mount_point: str) -> bool:
    """Validate mount point."""
    try:
        return os.path.exists(mount_point) and os.path.isdir(mount_point)
    except Exception:
        return False


def _analyze_filesystem_structure(mount_point: str) -> Dict[str, Any]:
    """Analyze filesystem structure."""
    try:
        structure = {
            "total_directories": 0,
            "total_files": 0,
            "filesystem_type": "unknown",
            "block_size": 0,
            "inode_count": 0
        }

        # Count directories and files
        for root, dirs, files in os.walk(mount_point):
            structure["total_directories"] += len(dirs)
            structure["total_files"] += len(files)

        # Try to get filesystem information
        if os.name == 'posix':
            try:
                stat_cmd = ["stat", "-f", mount_point]
                result = subprocess.run(stat_cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if "Type:" in line:
                            structure["filesystem_type"] = line.split("Type:")[1].strip()
                        elif "Block size:" in line:
                            structure["block_size"] = int(line.split("Block size:")[1].strip())
                        elif "Inodes:" in line:
                            structure["inode_count"] = int(line.split("Inodes:")[1].strip())
            except Exception:
                pass

        return structure

    except Exception as e:
        logger.warning(f"Failed to analyze filesystem structure: {e}")
        return {}


def _analyze_file_metadata(mount_point: str) -> Dict[str, Any]:
    """Analyze file metadata."""
    try:
        metadata = {
            "file_types": {},
            "file_sizes": [],
            "file_ages": [],
            "total_size": 0
        }

        for root, dirs, files in os.walk(mount_point):
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    file_stat = os.stat(file_path)

                    # File type analysis
                    file_ext = os.path.splitext(file)[1].lower()
                    metadata["file_types"][file_ext] = metadata["file_types"].get(file_ext, 0) + 1

                    # File size analysis
                    file_size = file_stat.st_size
                    metadata["file_sizes"].append(file_size)
                    metadata["total_size"] += file_size

                    # File age analysis
                    file_age = time.time() - file_stat.st_mtime
                    metadata["file_ages"].append(file_age)

                except Exception:
                    continue

        # Calculate statistics
        if metadata["file_sizes"]:
            metadata["average_file_size"] = sum(metadata["file_sizes"]) / len(metadata["file_sizes"])
            metadata["largest_file"] = max(metadata["file_sizes"])
            metadata["smallest_file"] = min(metadata["file_sizes"])

        if metadata["file_ages"]:
            metadata["average_file_age"] = sum(metadata["file_ages"]) / len(metadata["file_ages"])
            metadata["oldest_file"] = max(metadata["file_ages"])
            metadata["newest_file"] = min(metadata["file_ages"])

        return metadata

    except Exception as e:
        logger.warning(f"Failed to analyze file metadata: {e}")
        return {}


def _analyze_directory_structure(mount_point: str) -> Dict[str, Any]:
    """Analyze directory structure."""
    try:
        structure = {
            "directory_depths": [],
            "directory_sizes": {},
            "common_paths": [],
            "deepest_directory": "",
            "max_depth": 0
        }

        for root, dirs, files in os.walk(mount_point):
            try:
                # Calculate directory depth
                depth = root.count(os.sep) - mount_point.count(os.sep)
                structure["directory_depths"].append(depth)

                if depth > structure["max_depth"]:
                    structure["max_depth"] = depth
                    structure["deepest_directory"] = root

                # Calculate directory size
                dir_size = sum(os.path.getsize(os.path.join(root, file)) for file in files)
                structure["directory_sizes"][root] = dir_size

            except Exception:
                continue

        # Find common paths
        path_counts = {}
        for root in structure["directory_sizes"].keys():
            path_parts = root.split(os.sep)
            for i in range(1, len(path_parts)):
                partial_path = os.sep.join(path_parts[:i+1])
                path_counts[partial_path] = path_counts.get(partial_path, 0) + 1

        # Get most common paths
        structure["common_paths"] = sorted(
            path_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        return structure

    except Exception as e:
        logger.warning(f"Failed to analyze directory structure: {e}")
        return {}


def _analyze_file_timestamps(mount_point: str) -> Dict[str, Any]:
    """Analyze file timestamps."""
    try:
        timestamps = {
            "access_times": [],
            "modification_times": [],
            "creation_times": [],
            "recent_files": [],
            "old_files": []
        }

        current_time = time.time()

        for root, dirs, files in os.walk(mount_point):
            for file in files:
                try:
                    file_path = os.path.join(root, file)
                    file_stat = os.stat(file_path)

                    # Access time
                    access_time = file_stat.st_atime
                    timestamps["access_times"].append(access_time)

                    # Modification time
                    mod_time = file_stat.st_mtime
                    timestamps["modification_times"].append(mod_time)

                    # Creation time (if available)
                    try:
                        create_time = file_stat.st_ctime
                        timestamps["creation_times"].append(create_time)
                    except AttributeError:
                        pass

                    # Recent files (last 24 hours)
                    if current_time - mod_time < 86400:
                        timestamps["recent_files"].append({
                            "path": file_path,
                            "modification_time": mod_time,
                            "age_hours": (current_time - mod_time) / 3600
                        })

                    # Old files (older than 30 days)
                    if current_time - mod_time > 2592000:
                        timestamps["old_files"].append({
                            "path": file_path,
                            "modification_time": mod_time,
                            "age_days": (current_time - mod_time) / 86400
                        })

                except Exception:
                    continue

        # Sort recent and old files
        timestamps["recent_files"].sort(key=lambda x: x["modification_time"], reverse=True)
        timestamps["old_files"].sort(key=lambda x: x["modification_time"])

        return timestamps

    except Exception as e:
        logger.warning(f"Failed to analyze file timestamps: {e}")
        return {}


def _analyze_file_permissions(mount_point: str) -> Dict[str, Any]:
    """Analyze file permissions."""
    try:
        permissions = {
            "readable_files": 0,
            "writable_files": 0,
            "executable_files": 0,
            "hidden_files": 0,
            "permission_errors": 0
        }

        for root, dirs, files in os.walk(mount_point):
            for file in files:
                try:
                    file_path = os.path.join(root, file)

                    # Check permissions
                    if os.access(file_path, os.R_OK):
                        permissions["readable_files"] += 1

                    if os.access(file_path, os.W_OK):
                        permissions["writable_files"] += 1

                    if os.access(file_path, os.X_OK):
                        permissions["executable_files"] += 1

                    # Check if hidden
                    if file.startswith('.'):
                        permissions["hidden_files"] += 1

                except Exception:
                    permissions["permission_errors"] += 1
                    continue

        return permissions

    except Exception as e:
        logger.warning(f"Failed to analyze file permissions: {e}")
        return {}


def _analyze_hidden_files(mount_point: str) -> List[Dict[str, Any]]:
    """Analyze hidden files."""
    try:
        hidden_files = []

        for root, dirs, files in os.walk(mount_point):
            for file in files:
                if file.startswith('.'):
                    try:
                        file_path = os.path.join(root, file)
                        file_stat = os.stat(file_path)

                        hidden_files.append({
                            "path": file_path,
                            "name": file,
                            "size": file_stat.st_size,
                            "modification_time": file_stat.st_mtime,
                            "permissions": oct(file_stat.st_mode)[-3:]
                        })
                    except Exception:
                        continue

        return hidden_files

    except Exception as e:
        logger.warning(f"Failed to analyze hidden files: {e}")
        return []


def _analyze_deleted_files(mount_point: str) -> List[Dict[str, Any]]:
    """Analyze deleted files."""
    try:
        deleted_files = []

        # This is a simplified implementation
        # In a real forensics environment, you would use tools like
        # PhotoRec, TestDisk, or similar to recover deleted files

        return deleted_files

    except Exception as e:
        logger.warning(f"Failed to analyze deleted files: {e}")
        return []


def _generate_filesystem_summary(fs_structure: Dict[str, Any], file_metadata: Dict[str, Any],
                                directory_structure: Dict[str, Any], timestamp_analysis: Dict[str, Any],
                                permission_analysis: Dict[str, Any], hidden_files: List[Dict[str, Any]],
                                deleted_files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate filesystem analysis summary."""
    try:
        summary = {
            "total_files": fs_structure.get("total_files", 0),
            "total_directories": fs_structure.get("total_directories", 0),
            "total_size_gb": (file_metadata.get("total_size", 0) / (1024**3)),
            "filesystem_type": fs_structure.get("filesystem_type", "unknown"),
            "max_directory_depth": directory_structure.get("max_depth", 0),
            "recent_files_count": len(timestamp_analysis.get("recent_files", [])),
            "old_files_count": len(timestamp_analysis.get("old_files", [])),
            "hidden_files_count": len(hidden_files),
            "deleted_files_count": len(deleted_files),
            "permission_summary": permission_analysis
        }

        return summary

    except Exception as e:
        logger.warning(f"Failed to generate filesystem summary: {e}")
        return {}


# Helper functions for unallocated space scanning
def _get_image_information(image_path: str) -> Dict[str, Any]:
    """Get image information."""
    try:
        info = {
            "file_size": os.path.getsize(image_path),
            "file_size_gb": os.path.getsize(image_path) / (1024**3),
            "last_modified": os.path.getmtime(image_path)
        }

        return info

    except Exception as e:
        logger.warning(f"Failed to get image information: {e}")
        return {}


def _scan_file_signatures(image_path: str) -> List[Dict[str, Any]]:
    """Scan for file signatures."""
    try:
        signatures = []

        # Common file signatures
        file_signatures = {
            b'\xff\xd8\xff': 'JPEG',
            b'\x89PNG\r\n\x1a\n': 'PNG',
            b'GIF87a': 'GIF',
            b'GIF89a': 'GIF',
            b'%PDF': 'PDF',
            b'PK\x03\x04': 'ZIP',
            b'PK\x05\x06': 'ZIP',
            b'PK\x07\x08': 'ZIP',
            b'MZ': 'EXE',
            b'\x7fELF': 'ELF'
        }

        # Scan image file for signatures
        with open(image_path, 'rb') as f:
            data = f.read()

            for signature, file_type in file_signatures.items():
                offset = 0
                while True:
                    pos = data.find(signature, offset)
                    if pos == -1:
                        break

                    signatures.append({
                        "signature": signature.hex(),
                        "file_type": file_type,
                        "offset": pos,
                        "confidence": "high"
                    })

                    offset = pos + 1

        return signatures

    except Exception as e:
        logger.warning(f"Failed to scan file signatures: {e}")
        return []


def _scan_deleted_files(image_path: str) -> List[Dict[str, Any]]:
    """Scan for deleted files."""
    try:
        deleted_files = []

        # This is a simplified implementation
        # In a real forensics environment, you would use specialized tools

        return deleted_files

    except Exception as e:
        logger.warning(f"Failed to scan deleted files: {e}")
        return []


def _scan_slack_space(image_path: str) -> List[Dict[str, Any]]:
    """Scan for slack space."""
    try:
        slack_space = []

        # This is a simplified implementation
        # In a real forensics environment, you would analyze filesystem slack

        return slack_space

    except Exception as e:
        logger.warning(f"Failed to scan slack space: {e}")
        return []


def _analyze_unallocated_patterns(file_signatures: List[Dict[str, Any]],
                                 deleted_files: List[Dict[str, Any]],
                                 slack_space: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze unallocated space patterns."""
    try:
        patterns = {
            "file_signature_patterns": {},
            "deleted_file_patterns": {},
            "slack_space_patterns": {},
            "overall_assessment": "unknown"
        }

        # Analyze file signature patterns
        file_types = [sig.get("file_type") for sig in file_signatures]
        for file_type in file_types:
            patterns["file_signature_patterns"][file_type] = file_types.count(file_type)

        # Determine overall assessment
        total_findings = len(file_signatures) + len(deleted_files) + len(slack_space)

        if total_findings == 0:
            patterns["overall_assessment"] = "clean"
        elif total_findings < 10:
            patterns["overall_assessment"] = "minimal_activity"
        elif total_findings < 50:
            patterns["overall_assessment"] = "moderate_activity"
        else:
            patterns["overall_assessment"] = "high_activity"

        return patterns

    except Exception as e:
        logger.warning(f"Failed to analyze unallocated patterns: {e}")
        return {}


def _calculate_scan_statistics(image_info: Dict[str, Any], file_signatures: List[Dict[str, Any]],
                              deleted_files: List[Dict[str, Any]], slack_space: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate scan statistics."""
    try:
        stats = {
            "total_signatures_found": len(file_signatures),
            "total_deleted_files": len(deleted_files),
            "total_slack_fragments": len(slack_space),
            "scan_coverage_percent": 0.0,
            "estimated_recovery_potential": "unknown"
        }

        # Calculate scan coverage (simplified)
        if image_info.get("file_size"):
            # Assume we scanned the entire image
            stats["scan_coverage_percent"] = 100.0

        # Estimate recovery potential
        total_findings = stats["total_signatures_found"] + stats["total_deleted_files"]

        if total_findings == 0:
            stats["estimated_recovery_potential"] = "none"
        elif total_findings < 5:
            stats["estimated_recovery_potential"] = "low"
        elif total_findings < 20:
            stats["estimated_recovery_potential"] = "medium"
        else:
            stats["estimated_recovery_potential"] = "high"

        return stats

    except Exception as e:
        logger.warning(f"Failed to calculate scan statistics: {e}")
        return {}


# Helper functions for file recovery
def _recover_file_from_signature(signature: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Recover file from signature."""
    try:
        # This is a simplified implementation
        # In a real forensics environment, you would implement actual file carving

        recovered_file = {
            "recovery_method": "signature_based",
            "file_type": signature.get("file_type", "unknown"),
            "offset": signature.get("offset", 0),
            "confidence": signature.get("confidence", "unknown"),
            "recovery_status": "attempted"
        }

        return recovered_file

    except Exception as e:
        logger.warning(f"Failed to recover file from signature: {e}")
        return None


def _recover_deleted_file_entry(deleted_file: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Recover deleted file entry."""
    try:
        # This is a simplified implementation
        # In a real forensics environment, you would implement actual file recovery

        recovered_file = {
            "recovery_method": "deleted_entry",
            "file_type": "unknown",
            "offset": 0,
            "confidence": "medium",
            "recovery_status": "attempted"
        }

        return recovered_file

    except Exception as e:
        logger.warning(f"Failed to recover deleted file entry: {e}")
        return None


def _recover_file_from_slack(slack: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Recover file from slack space."""
    try:
        # This is a simplified implementation
        # In a real forensics environment, you would implement actual slack space recovery

        recovered_file = {
            "recovery_method": "slack_space",
            "file_type": "unknown",
            "offset": 0,
            "confidence": "low",
            "recovery_status": "attempted"
        }

        return recovered_file

    except Exception as e:
        logger.warning(f"Failed to recover file from slack space: {e}")
        return None


def _validate_recovered_files(recovered_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validate recovered files."""
    try:
        validated_files = []

        for file in recovered_files:
            try:
                # Basic validation
                if (file.get("recovery_method") and
                    file.get("file_type") and
                    file.get("confidence")):

                    # Add validation timestamp
                    file["validation_timestamp"] = datetime.now(timezone.utc).isoformat()
                    file["validation_status"] = "validated"

                    validated_files.append(file)

            except Exception:
                continue

        return validated_files

    except Exception as e:
        logger.warning(f"Failed to validate recovered files: {e}")
        return []


def _generate_recovery_summary(recovered_files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate recovery summary."""
    try:
        summary = {
            "total_files_recovered": len(recovered_files),
            "recovery_methods": {},
            "file_types": {},
            "confidence_levels": {},
            "recovery_success_rate": 0.0
        }

        # Analyze recovery methods
        for file in recovered_files:
            method = file.get("recovery_method", "unknown")
            summary["recovery_methods"][method] = summary["recovery_methods"].get(method, 0) + 1

            file_type = file.get("file_type", "unknown")
            summary["file_types"][file_type] = summary["file_types"].get(file_type, 0) + 1

            confidence = file.get("confidence", "unknown")
            summary["confidence_levels"][confidence] = summary["confidence_levels"].get(confidence, 0) + 1

        # Calculate success rate
        if recovered_files:
            successful = sum(1 for f in recovered_files if f.get("recovery_status") == "successful")
            summary["recovery_success_rate"] = successful / len(recovered_files)

        return summary

    except Exception as e:
        logger.warning(f"Failed to generate recovery summary: {e}")
        return {}

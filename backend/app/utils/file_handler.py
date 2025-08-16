#!/usr/bin/env python3
"""
Secure file handling utilities for evidence storage and malware quarantine.
Implements secure upload, quarantine, storage, and deletion operations.
"""

import hashlib
import json
import logging
import os
import shutil
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet

# Try to import magic, fallback to basic file type detection if not available
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("python-magic not available, using basic file type detection")

logger = logging.getLogger(__name__)

class FileHandlerError(Exception):
    """Base exception for file handling operations"""
    pass

class UploadError(FileHandlerError):
    """Exception raised during file upload operations"""
    pass

class QuarantineError(FileHandlerError):
    """Exception raised during malware quarantine operations"""
    pass

class StorageError(FileHandlerError):
    """Exception raised during evidence storage operations"""
    pass

class IntegrityError(FileHandlerError):
    """Exception raised during file integrity checks"""
    pass

class DeletionError(FileHandlerError):
    """Exception raised during secure file deletion operations"""
    pass

def get_file_type_info(file_path: Path) -> tuple[str, str]:
    """
    Get MIME type and file type information.

    Args:
        file_path: Path to the file

    Returns:
        Tuple of (mime_type, file_type)
    """
    if MAGIC_AVAILABLE:
        try:
            mime_type = magic.from_file(str(file_path), mime=True)
            file_type = magic.from_file(str(file_path))
            return mime_type, file_type
        except Exception as e:
            logger.warning(f"Magic file type detection failed: {e}")

    # Fallback to basic file type detection
    extension = file_path.suffix.lower()

    # Basic MIME type mapping
    mime_mapping = {
        '.txt': 'text/plain',
        '.py': 'text/x-python',
        '.js': 'application/javascript',
        '.html': 'text/html',
        '.css': 'text/css',
        '.json': 'application/json',
        '.xml': 'application/xml',
        '.pdf': 'application/pdf',
        '.zip': 'application/zip',
        '.tar': 'application/x-tar',
        '.gz': 'application/gzip',
        '.exe': 'application/x-executable',
        '.dll': 'application/x-executable',
        '.bat': 'text/x-batch',
        '.cmd': 'text/x-batch',
        '.ps1': 'text/x-powershell',
        '.vbs': 'text/x-vbscript',
        '.jar': 'application/x-java-archive',
        '.msi': 'application/x-msi',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.ico': 'image/x-icon'
    }

    mime_type = mime_mapping.get(extension, 'application/octet-stream')
    file_type = f"{extension.upper()[1:]} file" if extension else "Unknown file type"

    return mime_type, file_type

def secure_file_upload(
    file_path: str | Path,
    destination_dir: str | Path,
    encryption_key: bytes | None = None,
    quarantine_suspicious: bool = True
) -> dict[str, Any]:
    """
    Securely upload a file with integrity checks and optional encryption.

    Args:
        file_path: Path to the file to upload
        destination_dir: Directory to upload to
        encryption_key: Optional encryption key
        quarantine_suspicious: Whether to quarantine suspicious files

    Returns:
        Upload result with metadata

    Raises:
        UploadError: If upload fails
    """
    try:
        file_path = Path(file_path)
        destination_dir = Path(destination_dir)

        if not file_path.exists():
            raise UploadError(f"Source file not found: {file_path}")

        # Create destination directory
        destination_dir.mkdir(parents=True, exist_ok=True)

        # Calculate file hash for integrity
        file_hash = calculate_file_hash(file_path)

        # Check file type
        mime_type, file_type = get_file_type_info(file_path)

        # Check for suspicious file types
        suspicious_extensions = {'.exe', '.dll', '.bat', '.cmd', '.ps1', '.vbs', '.js', '.jar', '.msi'}
        suspicious_mime_types = {
            'application/x-executable', 'application/x-dosexec', 'application/x-msdownload',
            'application/x-msi', 'application/x-java-archive', 'text/x-python'
        }

        is_suspicious = (
            file_path.suffix.lower() in suspicious_extensions or
            mime_type in suspicious_mime_types
        )

        # Quarantine if suspicious and quarantine is enabled
        if is_suspicious and quarantine_suspicious:
            logger.warning(f"Suspicious file detected: {file_path}")
            quarantine_result = quarantine_malware(file_path)
            return {
                'success': True,
                'status': 'quarantined',
                'original_path': str(file_path),
                'quarantine_path': quarantine_result['quarantine_path'],
                'hash': file_hash,
                'mime_type': mime_type,
                'file_type': file_type,
                'is_suspicious': True,
                'quarantine_reason': 'Suspicious file type detected',
                'timestamp': datetime.now(UTC).isoformat()
            }

        # Generate unique filename
        timestamp = int(time.time())
        unique_filename = f"{timestamp}_{file_path.name}"
        destination_path = destination_dir / unique_filename

        # Copy file to destination
        shutil.copy2(file_path, destination_path)

        # Encrypt if key provided
        encrypted_path = None
        if encryption_key:
            encrypted_path = destination_path.with_suffix(destination_path.suffix + '.encrypted')
            encrypt_file(destination_path, encrypted_path, encryption_key)
            # Remove unencrypted copy
            destination_path.unlink()
            destination_path = encrypted_path

        # Verify integrity of copied file
        if not verify_file_integrity(destination_path, file_hash):
            raise UploadError("File integrity check failed after upload")

        # Create metadata
        metadata = {
            'original_filename': file_path.name,
            'uploaded_filename': destination_path.name,
            'original_path': str(file_path),
            'destination_path': str(destination_path),
            'file_size': file_path.stat().st_size,
            'hash': file_hash,
            'mime_type': mime_type,
            'file_type': file_type,
            'is_suspicious': is_suspicious,
            'encrypted': encryption_key is not None,
            'upload_timestamp': datetime.now(UTC).isoformat(),
            'permissions': oct(file_path.stat().st_mode)[-3:]
        }

        # Save metadata
        metadata_path = destination_path.with_suffix('.metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)

        logger.info(f"File uploaded successfully: {file_path} -> {destination_path}")

        return {
            'success': True,
            'status': 'uploaded',
            'destination_path': str(destination_path),
            'metadata_path': str(metadata_path),
            'hash': file_hash,
            'metadata': metadata
        }

    except Exception as e:
        logger.error(f"File upload failed for {file_path}: {e}")
        raise UploadError(f"Upload failed: {e}") from e

def quarantine_malware(
    file_path: str | Path,
    quarantine_dir: str | Path | None = None
) -> dict[str, Any]:
    """
    Quarantine a suspicious or malicious file for analysis.

    Args:
        file_path: Path to the file to quarantine
        quarantine_dir: Quarantine directory (default: /opt/kali-automation/quarantine)

    Returns:
        Quarantine result with metadata

    Raises:
        QuarantineError: If quarantine fails
    """
    try:
        file_path = Path(file_path)

        if not file_path.exists():
            raise QuarantineError(f"File not found: {file_path}")

        # Set quarantine directory
        if quarantine_dir is None:
            quarantine_dir = Path("/opt/kali-automation/quarantine")
        else:
            quarantine_dir = Path(quarantine_dir)

        quarantine_dir.mkdir(parents=True, exist_ok=True)

        # Create quarantine subdirectories
        suspicious_dir = quarantine_dir / "suspicious"
        malicious_dir = quarantine_dir / "malicious"
        analysis_dir = quarantine_dir / "analysis"

        for dir_path in [suspicious_dir, malicious_dir, analysis_dir]:
            dir_path.mkdir(exist_ok=True)

        # Calculate file hash
        file_hash = calculate_file_hash(file_path)

        # Check file with YARA rules for malware detection
        malware_detected = scan_file_with_yara(file_path)

        # Determine quarantine location
        if malware_detected:
            target_dir = malicious_dir
            quarantine_reason = "Malware detected by YARA rules"
        else:
            target_dir = suspicious_dir
            quarantine_reason = "Suspicious file type or behavior"

        # Generate quarantine filename
        timestamp = int(time.time())
        quarantine_filename = f"quarantine_{timestamp}_{file_path.name}"
        quarantine_path = target_dir / quarantine_filename

        # Move file to quarantine
        shutil.move(str(file_path), str(quarantine_path))

        # Create quarantine metadata
        quarantine_metadata = {
            'original_path': str(file_path),
            'quarantine_path': str(quarantine_path),
            'quarantine_timestamp': datetime.now(UTC).isoformat(),
            'file_hash': file_hash,
            'file_size': quarantine_path.stat().st_size,
            'quarantine_reason': quarantine_reason,
            'malware_detected': malware_detected,
            'yara_rules_matched': malware_detected.get('rules_matched', []) if malware_detected else [],
            'original_permissions': oct(quarantine_path.stat().st_mode)[-3:],
            'quarantine_id': f"Q{timestamp}"
        }

        # Save quarantine metadata
        metadata_path = quarantine_path.with_suffix('.quarantine.json')
        with open(metadata_path, 'w') as f:
            json.dump(quarantine_metadata, f, indent=2, default=str)

        # Create analysis copy
        analysis_path = analysis_dir / f"analysis_{timestamp}_{file_path.name}"
        shutil.copy2(quarantine_path, analysis_path)

        logger.info(f"File quarantined successfully: {file_path} -> {quarantine_path}")

        return {
            'success': True,
            'quarantine_path': str(quarantine_path),
            'analysis_path': str(analysis_path),
            'metadata_path': str(metadata_path),
            'quarantine_id': quarantine_metadata['quarantine_id'],
            'quarantine_reason': quarantine_reason,
            'malware_detected': malware_detected,
            'metadata': quarantine_metadata
        }

    except Exception as e:
        logger.error(f"File quarantine failed for {file_path}: {e}")
        raise QuarantineError(f"Quarantine failed: {e}") from e

def evidence_storage(
    evidence_data: str | bytes | dict[str, Any] | Path,
    evidence_type: str,
    case_id: str,
    storage_dir: str | Path | None = None
) -> dict[str, Any]:
    """
    Store evidence with proper chain of custody and metadata.

    Args:
        evidence_data: Evidence to store
        evidence_type: Type of evidence (disk_image, memory_dump, network_capture, etc.)
        case_id: Case identifier
        storage_dir: Storage directory (default: /opt/kali-automation/evidence)

    Returns:
        Storage result with metadata

    Raises:
        StorageError: If storage fails
    """
    try:
        # Set storage directory
        if storage_dir is None:
            storage_dir = Path("/opt/kali-automation/evidence")
        else:
            storage_dir = Path(storage_dir)

        # Create case directory
        case_dir = storage_dir / case_id
        case_dir.mkdir(parents=True, exist_ok=True)

        # Create evidence type subdirectory
        evidence_dir = case_dir / evidence_type
        evidence_dir.mkdir(exist_ok=True)

        # Generate evidence ID
        timestamp = int(time.time())
        evidence_id = f"{evidence_type}_{timestamp}"

        # Handle different evidence data types
        if isinstance(evidence_data, Path):
            # File path - copy to evidence directory
            if evidence_data.exists():
                evidence_filename = f"{evidence_id}_{evidence_data.name}"
                evidence_path = evidence_dir / evidence_filename
                shutil.copy2(evidence_data, evidence_path)
                file_size = evidence_path.stat().st_size
                original_path = str(evidence_data)
            else:
                raise StorageError(f"Evidence file not found: {evidence_data}")

        elif isinstance(evidence_data, dict):
            # Dictionary data - save as JSON
            evidence_filename = f"{evidence_id}.json"
            evidence_path = evidence_dir / evidence_filename
            with open(evidence_path, 'w') as f:
                json.dump(evidence_data, f, indent=2, default=str)
            file_size = evidence_path.stat().st_size
            original_path = None

        elif isinstance(evidence_data, (str, bytes)):
            # String or bytes data - save as file
            extension = '.txt' if isinstance(evidence_data, str) else '.bin'
            evidence_filename = f"{evidence_id}{extension}"
            evidence_path = evidence_dir / evidence_filename

            if isinstance(evidence_data, str):
                with open(evidence_path, 'w', encoding='utf-8') as f:
                    f.write(evidence_data)
            else:
                with open(evidence_path, 'wb') as f:
                    f.write(evidence_data)

            file_size = evidence_path.stat().st_size
            original_path = None
        else:
            raise StorageError(f"Unsupported evidence data type: {type(evidence_data)}")

        # Calculate hash for integrity
        evidence_hash = calculate_file_hash(evidence_path)

        # Create evidence metadata
        evidence_metadata = {
            'evidence_id': evidence_id,
            'case_id': case_id,
            'evidence_type': evidence_type,
            'evidence_path': str(evidence_path),
            'original_path': original_path,
            'file_size': file_size,
            'hash': evidence_hash,
            'storage_timestamp': datetime.now(UTC).isoformat(),
            'stored_by': os.getenv('USER', 'unknown'),
            'permissions': oct(evidence_path.stat().st_mode)[-3:],
            'mime_type': get_file_type_info(evidence_path)[0] if evidence_path.exists() else None
        }

        # Save evidence metadata
        metadata_path = evidence_path.with_suffix('.metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(evidence_metadata, f, indent=2, default=str)

        # Create chain of custody entry
        custody_entry = {
            'evidence_id': evidence_id,
            'action': 'stored',
            'timestamp': evidence_metadata['storage_timestamp'],
            'location': str(evidence_path),
            'hash': evidence_hash,
            'user': evidence_metadata['stored_by']
        }

        custody_file = case_dir / "chain_of_custody.json"
        custody_chain = []

        if custody_file.exists():
            with open(custody_file) as f:
                custody_chain = json.load(f)

        custody_chain.append(custody_entry)

        with open(custody_file, 'w') as f:
            json.dump(custody_chain, f, indent=2, default=str)

        logger.info(f"Evidence stored successfully: {evidence_id} in {evidence_path}")

        return {
            'success': True,
            'evidence_id': evidence_id,
            'evidence_path': str(evidence_path),
            'metadata_path': str(metadata_path),
            'custody_file': str(custody_file),
            'hash': evidence_hash,
            'metadata': evidence_metadata
        }

    except Exception as e:
        logger.error(f"Evidence storage failed: {e}")
        raise StorageError(f"Evidence storage failed: {e}") from e

def file_integrity_check(
    file_path: str | Path,
    expected_hash: str | None = None,
    algorithm: str = "sha256"
) -> dict[str, Any]:
    """
    Perform comprehensive file integrity checks.

    Args:
        file_path: Path to the file to check
        expected_hash: Expected hash value (optional)
        algorithm: Hash algorithm to use

    Returns:
        Integrity check results

    Raises:
        IntegrityError: If integrity check fails
    """
    try:
        file_path = Path(file_path)

        if not file_path.exists():
            raise IntegrityError(f"File not found: {file_path}")

        # Calculate current hash
        current_hash = calculate_file_hash(file_path, algorithm)

        # Get file metadata
        stat_info = file_path.stat()
        file_metadata = {
            'file_path': str(file_path),
            'file_size': stat_info.st_size,
            'created_time': datetime.fromtimestamp(stat_info.st_ctime, tz=UTC).isoformat(),
            'modified_time': datetime.fromtimestamp(stat_info.st_mtime, tz=UTC).isoformat(),
            'accessed_time': datetime.fromtimestamp(stat_info.st_atime, tz=UTC).isoformat(),
            'permissions': oct(stat_info.st_mode)[-3:],
            'owner': stat_info.st_uid,
            'group': stat_info.st_gid
        }

        # Check file type
        mime_type, file_type = get_file_type_info(file_path)

        # Verify hash if expected hash provided
        hash_verification = None
        if expected_hash:
            hash_verification = {
                'expected': expected_hash.lower(),
                'calculated': current_hash.lower(),
                'match': current_hash.lower() == expected_hash.lower()
            }

        # Check for file corruption indicators
        corruption_indicators = []

        # Check if file is readable
        try:
            with open(file_path, 'rb') as f:
                f.read(1024)  # Read first 1KB
        except Exception as e:
            corruption_indicators.append(f"File read error: {e}")

        # Check file size consistency
        if stat_info.st_size == 0:
            corruption_indicators.append("File size is zero")

        # Check for common corruption patterns
        if file_path.suffix.lower() in {'.zip', '.rar', '.7z'}:
            try:
                import zipfile
                if file_path.suffix.lower() == '.zip':
                    with zipfile.ZipFile(file_path, 'r') as zf:
                        zf.testzip()
            except Exception as e:
                corruption_indicators.append(f"Archive corruption detected: {e}")

        integrity_result = {
            'file_path': str(file_path),
            'current_hash': current_hash,
            'hash_algorithm': algorithm,
            'hash_verification': hash_verification,
            'file_metadata': file_metadata,
            'mime_type': mime_type,
            'file_type': file_type,
            'corruption_indicators': corruption_indicators,
            'integrity_status': 'good' if not corruption_indicators else 'corrupted',
            'check_timestamp': datetime.now(UTC).isoformat()
        }

        if corruption_indicators:
            logger.warning(f"File integrity issues detected for {file_path}: {corruption_indicators}")
        else:
            logger.info(f"File integrity check passed for {file_path}")

        return integrity_result

    except Exception as e:
        logger.error(f"File integrity check failed for {file_path}: {e}")
        raise IntegrityError(f"Integrity check failed: {e}") from e

def secure_file_deletion(
    file_path: str | Path,
    method: str = "secure",
    passes: int = 3
) -> dict[str, Any]:
    """
    Securely delete a file using various methods.

    Args:
        file_path: Path to the file to delete
        method: Deletion method (simple, secure, military)
        passes: Number of overwrite passes for secure deletion

    Returns:
        Deletion result

    Raises:
        DeletionError: If deletion fails
    """
    try:
        file_path = Path(file_path)

        if not file_path.exists():
            raise DeletionError(f"File not found: {file_path}")

        # Get file info before deletion
        file_size = file_path.stat().st_size
        file_hash = calculate_file_hash(file_path) if file_size > 0 else None

        deletion_metadata = {
            'file_path': str(file_path),
            'file_size': file_size,
            'original_hash': file_hash,
            'deletion_method': method,
            'deletion_timestamp': datetime.now(UTC).isoformat(),
            'deleted_by': os.getenv('USER', 'unknown')
        }

        if method == "simple":
            # Simple deletion - just remove the file
            file_path.unlink()
            deletion_metadata['method_description'] = "Simple file deletion"

        elif method == "secure":
            # Secure deletion - overwrite with random data before deletion
            secure_overwrite(file_path, passes)
            file_path.unlink()
            deletion_metadata['method_description'] = f"Secure deletion with {passes} overwrite passes"

        elif method == "military":
            # Military-grade deletion - multiple overwrite passes with specific patterns
            military_overwrite(file_path, passes)
            file_path.unlink()
            deletion_metadata['method_description'] = f"Military-grade deletion with {passes} overwrite passes"

        else:
            raise DeletionError(f"Unsupported deletion method: {method}")

        # Verify deletion
        if file_path.exists():
            raise DeletionError(f"File still exists after deletion: {file_path}")

        # Log deletion metadata
        log_deletion(deletion_metadata)

        logger.info(f"File securely deleted: {file_path} using {method} method")

        return {
            'success': True,
            'deleted_file': str(file_path),
            'deletion_method': method,
            'deletion_timestamp': deletion_metadata['deletion_timestamp'],
            'metadata': deletion_metadata
        }

    except Exception as e:
        logger.error(f"Secure file deletion failed for {file_path}: {e}")
        raise DeletionError(f"Secure deletion failed: {e}") from e

# Helper functions

def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Calculate hash of a file using specified algorithm."""
    valid_algorithms = {
        'md5': hashlib.md5,
        'sha1': hashlib.sha1,
        'sha256': hashlib.sha256,
        'sha512': hashlib.sha512
    }

    if algorithm not in valid_algorithms:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    hash_func = valid_algorithms[algorithm]
    hash_obj = hash_func()

    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            hash_obj.update(chunk)

    return hash_obj.hexdigest()

def verify_file_integrity(file_path: Path, expected_hash: str) -> bool:
    """Verify file integrity by comparing calculated hash with expected hash."""
    try:
        calculated_hash = calculate_file_hash(file_path)
        return calculated_hash.lower() == expected_hash.lower()
    except Exception:
        return False

def scan_file_with_yara(file_path: Path) -> dict[str, Any] | None:
    """Scan file with YARA rules for malware detection."""
    try:
        # This is a simplified implementation
        # In production, you would load actual YARA rules
        suspicious_patterns = [
            b'MZ',  # PE header
            b'This program cannot be run in DOS mode',
            b'CreateFile',
            b'RegCreateKey',
            b'InternetOpen'
        ]

        with open(file_path, 'rb') as f:
            content = f.read()

        matches = []
        for pattern in suspicious_patterns:
            if pattern in content:
                matches.append(pattern.decode('utf-8', errors='ignore'))

        if matches:
            return {
                'malware_detected': True,
                'rules_matched': matches,
                'confidence': 'medium'
            }

        return None

    except Exception as e:
        logger.warning(f"YARA scan failed for {file_path}: {e}")
        return None

def encrypt_file(input_path: Path, output_path: Path, key: bytes) -> None:
    """Encrypt a file using Fernet encryption."""
    cipher = Fernet(key)

    with open(input_path, 'rb') as f_in:
        with open(output_path, 'wb') as f_out:
            while chunk := f_in.read(8192):
                encrypted_chunk = cipher.encrypt(chunk)
                f_out.write(encrypted_chunk)

def secure_overwrite(file_path: Path, passes: int) -> None:
    """Overwrite file with random data before deletion."""
    file_size = file_path.stat().st_size

    for i in range(passes):
        with open(file_path, 'wb') as f:
            # Write random data
            f.write(os.urandom(file_size))
            f.flush()
            os.fsync(f.fileno())

        # Write zeros
        with open(file_path, 'wb') as f:
            f.write(b'\x00' * file_size)
            f.flush()
            os.fsync(f.fileno())

        # Write ones
        with open(file_path, 'wb') as f:
            f.write(b'\xff' * file_size)
            f.flush()
            os.fsync(f.fileno())

def military_overwrite(file_path: Path, passes: int) -> None:
    """Military-grade file overwrite with specific patterns."""
    file_size = file_path.stat().st_size

    patterns = [
        b'\x00',      # Zeros
        b'\xff',      # Ones
        b'\x55',      # Alternating 0101
        b'\xaa',      # Alternating 1010
        b'\x92\x49',  # Random pattern
        b'\x24\x92',  # Random pattern
        b'\x49\x24',  # Random pattern
        b'\x6d\xb6'   # Random pattern
    ]

    for i in range(passes):
        pattern = patterns[i % len(patterns)]
        with open(file_path, 'wb') as f:
            # Write pattern repeatedly
            while f.tell() < file_size:
                f.write(pattern)
            f.flush()
            os.fsync(f.fileno())

def log_deletion(deletion_metadata: dict[str, Any]) -> None:
    """Log file deletion for audit purposes."""
    log_dir = Path("/opt/kali-automation/logs/deletions")
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"deletion_log_{datetime.now().strftime('%Y%m%d')}.json"

    log_entries = []
    if log_file.exists():
        with open(log_file) as f:
            log_entries = json.load(f)

    log_entries.append(deletion_metadata)

    with open(log_file, 'w') as f:
        json.dump(log_entries, f, indent=2, default=str)

def secure_file_operation(
    operation: str,
    file_path: str | Path,
    **kwargs
) -> dict[str, Any]:
    """
    Perform secure file operations with proper error handling and logging.

    Args:
        operation: Operation to perform (upload, delete, move, copy, verify)
        file_path: Path to the file
        **kwargs: Additional arguments for the operation

    Returns:
        Operation result

    Raises:
        FileHandlerError: If operation fails
    """
    try:
        file_path = Path(file_path)

        if operation == "upload":
            destination_dir = kwargs.get('destination_dir', '/tmp')
            encryption_key = kwargs.get('encryption_key')
            quarantine_suspicious = kwargs.get('quarantine_suspicious', True)
            return secure_file_upload(file_path, destination_dir, encryption_key, quarantine_suspicious)

        elif operation == "delete":
            method = kwargs.get('method', 'secure')
            passes = kwargs.get('passes', 3)
            return secure_file_deletion(file_path, method, passes)

        elif operation == "move":
            destination = Path(kwargs.get('destination'))
            if not destination.parent.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)

            # Calculate hash before move
            original_hash = calculate_file_hash(file_path)

            # Move file
            shutil.move(str(file_path), str(destination))

            # Verify integrity after move
            if not verify_file_integrity(destination, original_hash):
                raise FileHandlerError("File integrity check failed after move")

            return {
                'success': True,
                'operation': 'move',
                'original_path': str(file_path),
                'destination_path': str(destination),
                'hash': original_hash,
                'timestamp': datetime.now(UTC).isoformat()
            }

        elif operation == "copy":
            destination = Path(kwargs.get('destination'))
            if not destination.parent.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)

            # Calculate hash before copy
            original_hash = calculate_file_hash(file_path)

            # Copy file
            shutil.copy2(file_path, destination)

            # Verify integrity after copy
            if not verify_file_integrity(destination, original_hash):
                raise FileHandlerError("File integrity check failed after copy")

            return {
                'success': True,
                'operation': 'copy',
                'original_path': str(file_path),
                'destination_path': str(destination),
                'hash': original_hash,
                'timestamp': datetime.now(UTC).isoformat()
            }

        elif operation == "verify":
            expected_hash = kwargs.get('expected_hash')
            algorithm = kwargs.get('algorithm', 'sha256')
            return file_integrity_check(file_path, expected_hash, algorithm)

        else:
            raise FileHandlerError(f"Unsupported operation: {operation}")

    except Exception as e:
        logger.error(f"Secure file operation '{operation}' failed for {file_path}: {e}")
        raise FileHandlerError(f"File operation failed: {e}") from e

def cleanup_temp_files(
    temp_dir: str | Path | None = None,
    max_age_hours: int = 24,
    file_patterns: list[str] | None = None
) -> dict[str, Any]:
    """
    Clean up temporary files based on age and patterns.

    Args:
        temp_dir: Directory to clean (default: system temp directory)
        max_age_hours: Maximum age of files to keep in hours
        file_patterns: File patterns to match (e.g., ['*.tmp', '*.log'])

    Returns:
        Cleanup result with statistics
    """
    try:
        if temp_dir is None:
            temp_dir = Path(tempfile.gettempdir())
        else:
            temp_dir = Path(temp_dir)

        if not temp_dir.exists():
            return {
                'success': True,
                'temp_dir': str(temp_dir),
                'files_removed': 0,
                'bytes_freed': 0,
                'errors': []
            }

        # Set default file patterns if none provided
        if file_patterns is None:
            file_patterns = ['*.tmp', '*.log', '*.cache', '*.temp', '*.bak']

        cutoff_time = datetime.now(UTC).timestamp() - (max_age_hours * 3600)

        files_removed = 0
        bytes_freed = 0
        errors = []

        # Process each pattern
        for pattern in file_patterns:
            try:
                for file_path in temp_dir.glob(pattern):
                    try:
                        # Check file age
                        if file_path.stat().st_mtime < cutoff_time:
                            file_size = file_path.stat().st_size

                            # Securely delete the file
                            secure_file_deletion(file_path, method="simple")

                            files_removed += 1
                            bytes_freed += file_size

                    except Exception as e:
                        errors.append(f"Failed to process {file_path}: {e}")

            except Exception as e:
                errors.append(f"Failed to process pattern {pattern}: {e}")

        # Also check for files without extensions that might be temporary
        try:
            for file_path in temp_dir.iterdir():
                if file_path.is_file() and not file_path.suffix:
                    try:
                        # Check if it's a temporary file by name
                        if any(temp_indicator in file_path.name.lower() for temp_indicator in ['temp', 'tmp', 'cache', 'bak']):
                            if file_path.stat().st_mtime < cutoff_time:
                                file_size = file_path.stat().st_size
                                secure_file_deletion(file_path, method="simple")
                                files_removed += 1
                                bytes_freed += file_size
                    except Exception as e:
                        errors.append(f"Failed to process {file_path}: {e}")
        except Exception as e:
            errors.append(f"Failed to process extensionless files: {e}")

        result = {
            'success': True,
            'temp_dir': str(temp_dir),
            'files_removed': files_removed,
            'bytes_freed': bytes_freed,
            'max_age_hours': max_age_hours,
            'patterns_processed': file_patterns,
            'errors': errors,
            'cleanup_timestamp': datetime.now(UTC).isoformat()
        }

        if errors:
            logger.warning(f"Cleanup completed with {len(errors)} errors: {errors}")
        else:
            logger.info(f"Cleanup completed successfully: {files_removed} files removed, {bytes_freed} bytes freed")

        return result

    except Exception as e:
        logger.error(f"Cleanup operation failed: {e}")
        return {
            'success': False,
            'temp_dir': str(temp_dir) if temp_dir else 'unknown',
            'files_removed': 0,
            'bytes_freed': 0,
            'errors': [str(e)],
            'cleanup_timestamp': datetime.now(UTC).isoformat()
        }

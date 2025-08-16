"""
Utility modules for the cybersecurity automation platform.
"""

from .crypto import (
    calculate_file_hash,
    chain_of_custody_hash,
    digital_signature,
    encrypt_sensitive_data,
    hash_evidence,
    key_management,
    verify_file_integrity,
)
from .file_handler import (
    cleanup_temp_files,
    evidence_storage,
    file_integrity_check,
    quarantine_malware,
    secure_file_deletion,
    secure_file_operation,
    secure_file_upload,
)

__all__ = [
    # Crypto functions
    'calculate_file_hash',
    'verify_file_integrity',
    'hash_evidence',
    'encrypt_sensitive_data',
    'digital_signature',
    'key_management',
    'chain_of_custody_hash',

    # File handler functions
    'secure_file_upload',
    'quarantine_malware',
    'evidence_storage',
    'file_integrity_check',
    'secure_file_deletion',
    'secure_file_operation',
    'cleanup_temp_files'
]

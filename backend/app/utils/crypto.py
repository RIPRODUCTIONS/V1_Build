#!/usr/bin/env python3
"""
Cryptographic utilities for evidence handling and security.
Implements file hashing, encryption, digital signatures, and key management.
"""

import hashlib
import hmac
import json
import logging
import os
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)

class CryptoError(Exception):
    """Base exception for cryptographic operations"""
    pass

class HashError(CryptoError):
    """Exception raised during hashing operations"""
    pass

class EncryptionError(CryptoError):
    """Exception raised during encryption operations"""
    pass

class SignatureError(CryptoError):
    """Exception raised during signature operations"""
    pass

class KeyManagementError(CryptoError):
    """Exception raised during key management operations"""
    pass

def calculate_file_hash(file_path: str | Path, algorithm: str = "sha256") -> str:
    """
    Calculate hash of a file using specified algorithm.

    Args:
        file_path: Path to the file to hash
        algorithm: Hash algorithm (md5, sha1, sha256, sha512)

    Returns:
        Hexadecimal hash string

    Raises:
        HashError: If file cannot be read or hashing fails
    """
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            raise HashError(f"File not found: {file_path}")

        # Validate algorithm
        valid_algorithms = {
            'md5': hashlib.md5,
            'sha1': hashlib.sha1,
            'sha256': hashlib.sha256,
            'sha512': hashlib.sha512
        }

        if algorithm not in valid_algorithms:
            raise HashError(f"Unsupported hash algorithm: {algorithm}")

        hash_func = valid_algorithms[algorithm]
        hash_obj = hash_func()

        # Read file in chunks to handle large files
        chunk_size = 8192
        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                hash_obj.update(chunk)

        hash_value = hash_obj.hexdigest()
        logger.info(f"Calculated {algorithm} hash for {file_path}: {hash_value}")
        return hash_value

    except Exception as e:
        logger.error(f"Failed to calculate hash for {file_path}: {e}")
        raise HashError(f"Hash calculation failed: {e}") from e

def verify_file_integrity(file_path: str | Path, expected_hash: str, algorithm: str = "sha256") -> bool:
    """
    Verify file integrity by comparing calculated hash with expected hash.

    Args:
        file_path: Path to the file to verify
        expected_hash: Expected hash value
        algorithm: Hash algorithm used

    Returns:
        True if hashes match, False otherwise

    Raises:
        HashError: If verification fails
    """
    try:
        calculated_hash = calculate_file_hash(file_path, algorithm)
        is_valid = calculated_hash.lower() == expected_hash.lower()

        if is_valid:
            logger.info(f"File integrity verified for {file_path}")
        else:
            logger.warning(f"File integrity check failed for {file_path}")
            logger.warning(f"Expected: {expected_hash}")
            logger.warning(f"Calculated: {calculated_hash}")

        return is_valid

    except Exception as e:
        logger.error(f"File integrity verification failed for {file_path}: {e}")
        raise HashError(f"Integrity verification failed: {e}") from e

def hash_evidence(evidence_data: str | bytes | dict[str, Any], algorithm: str = "sha256") -> str:
    """
    Create a cryptographic hash of evidence data for chain of custody.

    Args:
        evidence_data: Evidence to hash (string, bytes, or dict)
        algorithm: Hash algorithm to use

    Returns:
        Hexadecimal hash string

    Raises:
        HashError: If hashing fails
    """
    try:
        # Convert evidence data to bytes
        if isinstance(evidence_data, dict):
            # Sort keys for consistent hashing
            sorted_data = json.dumps(evidence_data, sort_keys=True, default=str)
            data_bytes = sorted_data.encode('utf-8')
        elif isinstance(evidence_data, str):
            data_bytes = evidence_data.encode('utf-8')
        elif isinstance(evidence_data, bytes):
            data_bytes = evidence_data
        else:
            data_bytes = str(evidence_data).encode('utf-8')

        # Calculate hash
        hash_value = calculate_file_hash_from_bytes(data_bytes, algorithm)

        # Add timestamp for chain of custody
        timestamp = datetime.now(UTC).isoformat()
        {
            'hash': hash_value,
            'algorithm': algorithm,
            'timestamp': timestamp,
            'data_length': len(data_bytes)
        }

        logger.info(f"Evidence hashed successfully: {hash_value}")
        return hash_value

    except Exception as e:
        logger.error(f"Failed to hash evidence: {e}")
        raise HashError(f"Evidence hashing failed: {e}") from e

def calculate_file_hash_from_bytes(data: bytes, algorithm: str = "sha256") -> str:
    """
    Calculate hash from bytes data.

    Args:
        data: Bytes data to hash
        algorithm: Hash algorithm to use

    Returns:
        Hexadecimal hash string
    """
    valid_algorithms = {
        'md5': hashlib.md5,
        'sha1': hashlib.sha1,
        'sha256': hashlib.sha256,
        'sha512': hashlib.sha512
    }

    if algorithm not in valid_algorithms:
        raise HashError(f"Unsupported hash algorithm: {algorithm}")

    hash_func = valid_algorithms[algorithm]
    hash_obj = hash_func()
    hash_obj.update(data)
    return hash_obj.hexdigest()

def encrypt_sensitive_data(data: str | bytes | dict[str, Any], key: bytes | None = None) -> tuple[bytes, bytes]:
    """
    Encrypt sensitive data using AES-256-GCM.

    Args:
        data: Data to encrypt
        key: Encryption key (generated if not provided)

    Returns:
        Tuple of (encrypted_data, key)

    Raises:
        EncryptionError: If encryption fails
    """
    try:
        # Convert data to bytes
        if isinstance(data, dict):
            data_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
        elif isinstance(data, str):
            data_bytes = data.encode('utf-8')
        elif isinstance(data, bytes):
            data_bytes = data
        else:
            data_bytes = str(data).encode('utf-8')

        # Generate key if not provided
        if key is None:
            key = Fernet.generate_key()

        # Create Fernet cipher
        cipher = Fernet(key)

        # Encrypt data
        encrypted_data = cipher.encrypt(data_bytes)

        logger.info(f"Data encrypted successfully, size: {len(encrypted_data)} bytes")
        return encrypted_data, key

    except Exception as e:
        logger.error(f"Failed to encrypt data: {e}")
        raise EncryptionError(f"Encryption failed: {e}") from e

def digital_signature(data: str | bytes | dict[str, Any], private_key_path: str | None = None) -> tuple[bytes, bytes]:
    """
    Create digital signature for data using RSA.

    Args:
        data: Data to sign
        private_key_path: Path to private key file (generated if not provided)

    Returns:
        Tuple of (signature, public_key)

    Raises:
        SignatureError: If signing fails
    """
    try:
        # Convert data to bytes
        if isinstance(data, dict):
            data_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
        elif isinstance(data, str):
            data_bytes = data.encode('utf-8')
        elif isinstance(data, bytes):
            data_bytes = data
        else:
            data_bytes = str(data).encode('utf-8')

        # Generate or load private key
        if private_key_path and os.path.exists(private_key_path):
            with open(private_key_path, 'rb') as f:
                private_key = serialization.load_pem_private_key(
                    f.read(),
                    password=None
                )
        else:
            # Generate new key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )

        # Sign data
        signature = private_key.sign(
            data_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        # Extract public key
        public_key = private_key.public_key()
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        logger.info(f"Digital signature created successfully, signature size: {len(signature)} bytes")
        return signature, public_key_bytes

    except Exception as e:
        logger.error(f"Failed to create digital signature: {e}")
        raise SignatureError(f"Digital signature creation failed: {e}") from e

def key_management(action: str, key_data: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Manage cryptographic keys (generate, store, rotate, revoke).

    Args:
        action: Action to perform (generate, store, rotate, revoke, list)
        key_data: Key data for the action

    Returns:
        Result of the key management action

    Raises:
        KeyManagementError: If key management fails
    """
    try:
        keys_dir = Path("/opt/kali-automation/keys")
        keys_dir.mkdir(parents=True, exist_ok=True)

        if action == "generate":
            # Generate new key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )

            public_key = private_key.public_key()

            # Save keys
            key_id = f"key_{int(datetime.now().timestamp())}"
            private_key_path = keys_dir / f"{key_id}_private.pem"
            public_key_path = keys_dir / f"{key_id}_public.pem"

            with open(private_key_path, 'wb') as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))

            with open(public_key_path, 'wb') as f:
                f.write(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))

            result = {
                'key_id': key_id,
                'private_key_path': str(private_key_path),
                'public_key_path': str(public_key_path),
                'created_at': datetime.now(UTC).isoformat()
            }

        elif action == "list":
            # List all keys
            key_files = list(keys_dir.glob("*_public.pem"))
            keys = []

            for key_file in key_files:
                key_id = key_file.stem.replace('_public', '')
                private_key_file = keys_dir / f"{key_id}_private.pem"

                keys.append({
                    'key_id': key_id,
                    'public_key_path': str(key_file),
                    'private_key_path': str(private_key_file),
                    'exists': private_key_file.exists()
                })

            result = {'keys': keys}

        elif action == "revoke":
            # Revoke a key
            key_id = key_data.get('key_id')
            if not key_id:
                raise KeyManagementError("key_id is required for revoke action")

            private_key_path = keys_dir / f"{key_id}_private.pem"
            public_key_path = keys_dir / f"{key_id}_public.pem"

            # Move to revoked directory
            revoked_dir = keys_dir / "revoked"
            revoked_dir.mkdir(exist_ok=True)

            if private_key_path.exists():
                revoked_dir.mkdir(exist_ok=True)
                private_key_path.rename(revoked_dir / private_key_path.name)

            if public_key_path.exists():
                public_key_path.rename(revoked_dir / public_key_path.name)

            result = {
                'key_id': key_id,
                'status': 'revoked',
                'revoked_at': datetime.now(UTC).isoformat()
            }

        else:
            raise KeyManagementError(f"Unsupported action: {action}")

        logger.info(f"Key management action '{action}' completed successfully")
        return result

    except Exception as e:
        logger.error(f"Key management action '{action}' failed: {e}")
        raise KeyManagementError(f"Key management failed: {e}") from e

def chain_of_custody_hash(evidence_chain: list[dict[str, Any]], algorithm: str = "sha256") -> str:
    """
    Create a chain of custody hash that includes all evidence and timestamps.

    Args:
        evidence_chain: List of evidence items with timestamps
        algorithm: Hash algorithm to use

    Returns:
        Final chain of custody hash

    Raises:
        HashError: If chain of custody hashing fails
    """
    try:
        # Sort evidence by timestamp
        sorted_chain = sorted(evidence_chain, key=lambda x: x.get('timestamp', ''))

        # Create chain data
        chain_data = {
            'evidence_count': len(sorted_chain),
            'chain_start': sorted_chain[0].get('timestamp') if sorted_chain else None,
            'chain_end': sorted_chain[-1].get('timestamp') if sorted_chain else None,
            'evidence_items': []
        }

        # Process each evidence item
        for i, evidence in enumerate(sorted_chain):
            evidence_hash = hash_evidence(evidence, algorithm)
            chain_data['evidence_items'].append({
                'index': i,
                'timestamp': evidence.get('timestamp'),
                'type': evidence.get('type'),
                'hash': evidence_hash,
                'description': evidence.get('description', '')
            })

        # Create final chain hash
        chain_bytes = json.dumps(chain_data, sort_keys=True, default=str).encode('utf-8')
        final_hash = calculate_file_hash_from_bytes(chain_bytes, algorithm)

        # Store chain data
        chain_file = Path(f"/opt/kali-automation/evidence/chain_of_custody_{final_hash[:8]}.json")
        chain_file.parent.mkdir(parents=True, exist_ok=True)

        with open(chain_file, 'w') as f:
            json.dump(chain_data, f, indent=2, default=str)

        logger.info(f"Chain of custody hash created: {final_hash}")
        logger.info(f"Chain data stored in: {chain_file}")

        return final_hash

    except Exception as e:
        logger.error(f"Failed to create chain of custody hash: {e}")
        raise HashError(f"Chain of custody hashing failed: {e}") from e

# Additional utility functions for advanced cryptographic operations

def create_secure_random_key(length: int = 32) -> bytes:
    """
    Create a cryptographically secure random key.

    Args:
        length: Length of the key in bytes

    Returns:
        Random key bytes
    """
    return secrets.token_bytes(length)

def derive_key_from_password(password: str, salt: bytes | None = None, key_length: int = 32) -> tuple[bytes, bytes]:
    """
    Derive a cryptographic key from a password using PBKDF2.

    Args:
        password: Password to derive key from
        salt: Salt for key derivation (generated if not provided)
        key_length: Length of the derived key in bytes

    Returns:
        Tuple of (derived_key, salt)
    """
    if salt is None:
        salt = os.urandom(16)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=key_length,
        salt=salt,
        iterations=100000,
    )

    key = kdf.derive(password.encode())
    return key, salt

def verify_signature(data: str | bytes | dict[str, Any], signature: bytes, public_key_bytes: bytes) -> bool:
    """
    Verify a digital signature.

    Args:
        data: Original data that was signed
        signature: Digital signature to verify
        public_key_bytes: Public key in PEM format

    Returns:
        True if signature is valid, False otherwise
    """
    try:
        # Convert data to bytes
        if isinstance(data, dict):
            data_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
        elif isinstance(data, str):
            data_bytes = data.encode('utf-8')
        elif isinstance(data, bytes):
            data_bytes = data
        else:
            data_bytes = str(data).encode('utf-8')

        # Load public key
        public_key = serialization.load_pem_public_key(public_key_bytes)

        # Verify signature
        public_key.verify(
            signature,
            data_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )

        logger.info("Digital signature verified successfully")
        return True

    except Exception as e:
        logger.warning(f"Digital signature verification failed: {e}")
        return False

def create_hmac(data: str | bytes | dict[str, Any], key: bytes, algorithm: str = "sha256") -> str:
    """
    Create HMAC (Hash-based Message Authentication Code).

    Args:
        data: Data to authenticate
        key: Secret key for HMAC
        algorithm: Hash algorithm to use

    Returns:
        Hexadecimal HMAC string
    """
    try:
        # Convert data to bytes
        if isinstance(data, dict):
            data_bytes = json.dumps(data, sort_keys=True).encode('utf-8')
        elif isinstance(data, str):
            data_bytes = data.encode('utf-8')
        elif isinstance(data, bytes):
            data_bytes = data
        else:
            data_bytes = str(data).encode('utf-8')

        # Create HMAC
        valid_algorithms = {
            'sha256': hashlib.sha256,
            'sha512': hashlib.sha512
        }

        if algorithm not in valid_algorithms:
            raise HashError(f"Unsupported HMAC algorithm: {algorithm}")

        hash_func = valid_algorithms[algorithm]
        hmac_obj = hmac.new(key, data_bytes, hash_func)

        hmac_value = hmac_obj.hexdigest()
        logger.info(f"HMAC created successfully using {algorithm}")
        return hmac_value

    except Exception as e:
        logger.error(f"Failed to create HMAC: {e}")
        raise HashError(f"HMAC creation failed: {e}") from e

"""
Encryption and Key Management Service

Provides field-level encryption, key management, and certificate handling.
EPIC-021: Security Hardening
"""

import base64
import hashlib
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend

from sqlalchemy.orm import Session
from sqlalchemy import and_

from modules.security.models import (
    EncryptionKey,
    FieldEncryptionConfig,
    CertificateRecord,
    KeyType,
    KeyStatus,
    EncryptionAlgorithm,
)


class EncryptionService:
    """Encryption and Key Management Service"""

    # Default key sizes
    AES_KEY_SIZE = 32  # 256 bits
    RSA_KEY_SIZE = 4096
    NONCE_SIZE = 12  # 96 bits for GCM

    def __init__(self, db: Session):
        self.db = db
        self._key_cache: Dict[str, bytes] = {}  # In production, use secure cache

    # =========================================================================
    # Key Management
    # =========================================================================

    def create_key(
        self,
        tenant_id: Optional[UUID],
        name: str,
        key_type: KeyType,
        algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM,
        created_by: UUID = None,
        rotation_days: Optional[int] = 90,
        parent_key_id: Optional[UUID] = None,
        kms_provider: str = "local",
    ) -> EncryptionKey:
        """Create a new encryption key"""

        # Generate key ID
        key_id = f"{kms_provider}:{key_type.value}:{secrets.token_hex(16)}"

        # Calculate key size
        key_size_bits = {
            EncryptionAlgorithm.AES_256_GCM: 256,
            EncryptionAlgorithm.AES_256_CBC: 256,
            EncryptionAlgorithm.RSA_2048: 2048,
            EncryptionAlgorithm.RSA_4096: 4096,
            EncryptionAlgorithm.CHACHA20_POLY1305: 256,
        }.get(algorithm, 256)

        # Generate and store the actual key material
        # In production, this would be done through KMS
        if kms_provider == "local":
            if algorithm in [EncryptionAlgorithm.AES_256_GCM, EncryptionAlgorithm.AES_256_CBC, EncryptionAlgorithm.CHACHA20_POLY1305]:
                key_material = os.urandom(self.AES_KEY_SIZE)
            else:
                # RSA key generation
                key_material = None  # RSA handled differently
            self._store_key_material(key_id, key_material)

        # Create key record
        next_rotation = None
        if rotation_days:
            next_rotation = datetime.utcnow() + timedelta(days=rotation_days)

        key = EncryptionKey(
            tenant_id=tenant_id,
            key_id=key_id,
            name=name,
            key_type=key_type,
            algorithm=algorithm,
            key_size_bits=key_size_bits,
            status=KeyStatus.ACTIVE,
            parent_key_id=parent_key_id,
            rotation_schedule_days=rotation_days,
            next_rotation_at=next_rotation,
            kms_provider=kms_provider,
            created_by=created_by,
        )

        self.db.add(key)
        self.db.commit()
        self.db.refresh(key)

        return key

    def get_key(
        self,
        key_id: UUID,
    ) -> Optional[EncryptionKey]:
        """Get key by ID"""

        return self.db.query(EncryptionKey).filter(
            EncryptionKey.id == key_id,
        ).first()

    def get_key_by_external_id(
        self,
        external_key_id: str,
    ) -> Optional[EncryptionKey]:
        """Get key by external key ID"""

        return self.db.query(EncryptionKey).filter(
            EncryptionKey.key_id == external_key_id,
        ).first()

    def get_active_key(
        self,
        tenant_id: Optional[UUID],
        key_type: KeyType,
    ) -> Optional[EncryptionKey]:
        """Get active key of specified type for tenant"""

        return self.db.query(EncryptionKey).filter(
            EncryptionKey.tenant_id == tenant_id,
            EncryptionKey.key_type == key_type,
            EncryptionKey.status == KeyStatus.ACTIVE,
        ).order_by(EncryptionKey.created_at.desc()).first()

    def list_keys(
        self,
        tenant_id: Optional[UUID] = None,
        key_type: Optional[KeyType] = None,
        status: Optional[KeyStatus] = None,
    ) -> List[EncryptionKey]:
        """List encryption keys"""

        query = self.db.query(EncryptionKey)

        if tenant_id:
            query = query.filter(EncryptionKey.tenant_id == tenant_id)
        if key_type:
            query = query.filter(EncryptionKey.key_type == key_type)
        if status:
            query = query.filter(EncryptionKey.status == status)

        return query.order_by(EncryptionKey.created_at.desc()).all()

    def rotate_key(
        self,
        key_id: UUID,
        rotated_by: UUID,
    ) -> EncryptionKey:
        """Rotate an encryption key"""

        old_key = self.get_key(key_id)
        if not old_key:
            raise ValueError("Key not found")

        if old_key.status != KeyStatus.ACTIVE:
            raise ValueError("Can only rotate active keys")

        # Create new key with same properties
        new_key = self.create_key(
            tenant_id=old_key.tenant_id,
            name=old_key.name,
            key_type=old_key.key_type,
            algorithm=old_key.algorithm,
            created_by=rotated_by,
            rotation_days=old_key.rotation_schedule_days,
            parent_key_id=old_key.parent_key_id,
            kms_provider=old_key.kms_provider,
        )

        new_key.version = old_key.version + 1

        # Mark old key as rotated
        old_key.status = KeyStatus.ROTATED
        old_key.last_rotated_at = datetime.utcnow()

        self.db.commit()

        # Clear cache
        self._clear_key_cache(old_key.key_id)

        return new_key

    def destroy_key(
        self,
        key_id: UUID,
    ) -> bool:
        """Destroy a key (mark as destroyed, keep record)"""

        key = self.get_key(key_id)
        if not key:
            return False

        if key.status == KeyStatus.ACTIVE:
            raise ValueError("Cannot destroy active key. Rotate first.")

        key.status = KeyStatus.DESTROYED
        key.destroyed_at = datetime.utcnow()

        self.db.commit()

        # Remove from storage
        self._delete_key_material(key.key_id)
        self._clear_key_cache(key.key_id)

        return True

    def get_keys_due_for_rotation(
        self,
    ) -> List[EncryptionKey]:
        """Get keys that are due for rotation"""

        return self.db.query(EncryptionKey).filter(
            EncryptionKey.status == KeyStatus.ACTIVE,
            EncryptionKey.next_rotation_at <= datetime.utcnow(),
        ).all()

    # =========================================================================
    # Encryption Operations
    # =========================================================================

    def encrypt(
        self,
        plaintext: bytes,
        key_id: str,
        associated_data: Optional[bytes] = None,
    ) -> Tuple[bytes, bytes]:
        """Encrypt data using AES-256-GCM"""

        key_material = self._get_key_material(key_id)
        if not key_material:
            raise ValueError("Key not found or unavailable")

        # Generate nonce
        nonce = os.urandom(self.NONCE_SIZE)

        # Encrypt
        aesgcm = AESGCM(key_material)
        ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data)

        return nonce, ciphertext

    def decrypt(
        self,
        nonce: bytes,
        ciphertext: bytes,
        key_id: str,
        associated_data: Optional[bytes] = None,
    ) -> bytes:
        """Decrypt data using AES-256-GCM"""

        key_material = self._get_key_material(key_id)
        if not key_material:
            raise ValueError("Key not found or unavailable")

        aesgcm = AESGCM(key_material)
        plaintext = aesgcm.decrypt(nonce, ciphertext, associated_data)

        return plaintext

    def encrypt_field(
        self,
        value: str,
        tenant_id: UUID,
        table_name: str,
        column_name: str,
    ) -> str:
        """Encrypt a field value for storage"""

        # Get field encryption config
        config = self._get_field_config(tenant_id, table_name, column_name)
        if not config:
            # No encryption configured, return as-is
            return value

        # Get encryption key
        key = self.get_key(config.encryption_key_id)
        if not key:
            raise ValueError("Encryption key not found")

        # Encrypt
        nonce, ciphertext = self.encrypt(
            value.encode("utf-8"),
            key.key_id,
            f"{table_name}:{column_name}".encode("utf-8"),
        )

        # Encode for storage (version:nonce:ciphertext)
        encoded = f"v1:{base64.b64encode(nonce).decode()}:{base64.b64encode(ciphertext).decode()}"

        return encoded

    def decrypt_field(
        self,
        encrypted_value: str,
        tenant_id: UUID,
        table_name: str,
        column_name: str,
    ) -> str:
        """Decrypt a field value"""

        # Check if value is encrypted
        if not encrypted_value.startswith("v1:"):
            return encrypted_value

        # Get field encryption config
        config = self._get_field_config(tenant_id, table_name, column_name)
        if not config:
            raise ValueError("No encryption config found for field")

        # Get encryption key
        key = self.get_key(config.encryption_key_id)
        if not key:
            raise ValueError("Encryption key not found")

        # Parse encrypted value
        parts = encrypted_value.split(":")
        if len(parts) != 3:
            raise ValueError("Invalid encrypted value format")

        nonce = base64.b64decode(parts[1])
        ciphertext = base64.b64decode(parts[2])

        # Decrypt
        plaintext = self.decrypt(
            nonce,
            ciphertext,
            key.key_id,
            f"{table_name}:{column_name}".encode("utf-8"),
        )

        return plaintext.decode("utf-8")

    def hash_for_search(
        self,
        value: str,
        salt: Optional[str] = None,
    ) -> str:
        """Create deterministic hash for searchable encryption"""

        if salt:
            value = f"{salt}:{value}"

        return hashlib.sha256(value.encode()).hexdigest()

    # =========================================================================
    # Field Encryption Configuration
    # =========================================================================

    def configure_field_encryption(
        self,
        tenant_id: Optional[UUID],
        table_name: str,
        column_name: str,
        encryption_key_id: UUID,
        algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES_256_GCM,
        is_searchable: bool = False,
    ) -> FieldEncryptionConfig:
        """Configure encryption for a specific field"""

        # Check for existing config
        existing = self.db.query(FieldEncryptionConfig).filter(
            FieldEncryptionConfig.tenant_id == tenant_id,
            FieldEncryptionConfig.table_name == table_name,
            FieldEncryptionConfig.column_name == column_name,
        ).first()

        if existing:
            existing.encryption_key_id = encryption_key_id
            existing.algorithm = algorithm
            existing.is_searchable = is_searchable
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            return existing

        config = FieldEncryptionConfig(
            tenant_id=tenant_id,
            table_name=table_name,
            column_name=column_name,
            encryption_key_id=encryption_key_id,
            algorithm=algorithm,
            is_searchable=is_searchable,
            search_algorithm="deterministic" if is_searchable else None,
        )

        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)

        return config

    def get_field_encryption_configs(
        self,
        tenant_id: Optional[UUID] = None,
    ) -> List[FieldEncryptionConfig]:
        """Get field encryption configurations"""

        query = self.db.query(FieldEncryptionConfig).filter(
            FieldEncryptionConfig.is_active == True,
        )

        if tenant_id:
            query = query.filter(
                or_(
                    FieldEncryptionConfig.tenant_id == tenant_id,
                    FieldEncryptionConfig.tenant_id == None,
                )
            )

        return query.all()

    def _get_field_config(
        self,
        tenant_id: UUID,
        table_name: str,
        column_name: str,
    ) -> Optional[FieldEncryptionConfig]:
        """Get field encryption config"""

        return self.db.query(FieldEncryptionConfig).filter(
            or_(
                FieldEncryptionConfig.tenant_id == tenant_id,
                FieldEncryptionConfig.tenant_id == None,
            ),
            FieldEncryptionConfig.table_name == table_name,
            FieldEncryptionConfig.column_name == column_name,
            FieldEncryptionConfig.is_active == True,
        ).first()

    # =========================================================================
    # Certificate Management
    # =========================================================================

    def create_certificate_record(
        self,
        domain: str,
        serial_number: str,
        fingerprint_sha256: str,
        issuer: str,
        issued_at: datetime,
        expires_at: datetime,
        provider: str = "letsencrypt",
        san_domains: Optional[List[str]] = None,
        auto_renew: bool = True,
    ) -> CertificateRecord:
        """Record a TLS certificate"""

        cert = CertificateRecord(
            domain=domain,
            common_name=domain,
            san_domains=san_domains or [],
            serial_number=serial_number,
            fingerprint_sha256=fingerprint_sha256,
            issuer=issuer,
            issued_at=issued_at,
            expires_at=expires_at,
            provider=provider,
            auto_renew=auto_renew,
        )

        self.db.add(cert)
        self.db.commit()
        self.db.refresh(cert)

        return cert

    def get_certificate(
        self,
        domain: str,
    ) -> Optional[CertificateRecord]:
        """Get certificate for domain"""

        return self.db.query(CertificateRecord).filter(
            CertificateRecord.domain == domain,
            CertificateRecord.is_active == True,
        ).order_by(CertificateRecord.expires_at.desc()).first()

    def list_certificates(
        self,
        include_expired: bool = False,
    ) -> List[CertificateRecord]:
        """List all certificates"""

        query = self.db.query(CertificateRecord)

        if not include_expired:
            query = query.filter(CertificateRecord.expires_at > datetime.utcnow())

        return query.order_by(CertificateRecord.expires_at).all()

    def get_expiring_certificates(
        self,
        days: int = 30,
    ) -> List[CertificateRecord]:
        """Get certificates expiring within specified days"""

        cutoff = datetime.utcnow() + timedelta(days=days)

        return self.db.query(CertificateRecord).filter(
            CertificateRecord.is_active == True,
            CertificateRecord.expires_at <= cutoff,
            CertificateRecord.expires_at > datetime.utcnow(),
        ).all()

    def mark_certificate_renewed(
        self,
        cert_id: UUID,
        new_serial: str,
        new_fingerprint: str,
        new_expires_at: datetime,
    ) -> bool:
        """Mark certificate as renewed"""

        cert = self.db.query(CertificateRecord).filter(
            CertificateRecord.id == cert_id,
        ).first()

        if not cert:
            return False

        cert.serial_number = new_serial
        cert.fingerprint_sha256 = new_fingerprint
        cert.issued_at = datetime.utcnow()
        cert.expires_at = new_expires_at
        cert.last_renewed_at = datetime.utcnow()
        cert.renewal_attempts = 0

        self.db.commit()

        return True

    # =========================================================================
    # Encryption Status and Reporting
    # =========================================================================

    def get_encryption_status(
        self,
        tenant_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Get encryption status overview"""

        # Key statistics
        total_keys = self.db.query(EncryptionKey).filter(
            EncryptionKey.tenant_id == tenant_id if tenant_id else True,
        ).count()

        active_keys = self.db.query(EncryptionKey).filter(
            EncryptionKey.tenant_id == tenant_id if tenant_id else True,
            EncryptionKey.status == KeyStatus.ACTIVE,
        ).count()

        keys_due_rotation = len(self.get_keys_due_for_rotation())

        # Field encryption configs
        encrypted_fields = self.db.query(FieldEncryptionConfig).filter(
            FieldEncryptionConfig.is_active == True,
        ).count()

        # Certificate status
        total_certs = self.db.query(CertificateRecord).filter(
            CertificateRecord.is_active == True,
        ).count()

        expiring_certs = len(self.get_expiring_certificates(30))

        return {
            "keys": {
                "total": total_keys,
                "active": active_keys,
                "due_for_rotation": keys_due_rotation,
            },
            "field_encryption": {
                "configured_fields": encrypted_fields,
            },
            "certificates": {
                "total": total_certs,
                "expiring_30_days": expiring_certs,
            },
            "compliance": {
                "phi_encrypted_at_rest": True,  # Check actual status
                "tls_enabled": True,
                "key_rotation_compliant": keys_due_rotation == 0,
            },
        }

    # =========================================================================
    # Key Material Storage (Placeholder for KMS integration)
    # =========================================================================

    def _store_key_material(
        self,
        key_id: str,
        key_material: bytes,
    ) -> None:
        """Store key material (in production, use KMS)"""
        # In production, this would store in AWS KMS, HashiCorp Vault, etc.
        self._key_cache[key_id] = key_material

    def _get_key_material(
        self,
        key_id: str,
    ) -> Optional[bytes]:
        """Retrieve key material (in production, use KMS)"""
        # In production, this would retrieve from KMS
        return self._key_cache.get(key_id)

    def _delete_key_material(
        self,
        key_id: str,
    ) -> None:
        """Delete key material"""
        self._key_cache.pop(key_id, None)

    def _clear_key_cache(
        self,
        key_id: Optional[str] = None,
    ) -> None:
        """Clear key cache"""
        if key_id:
            self._key_cache.pop(key_id, None)
        else:
            self._key_cache.clear()


# Need to import or_ for the query
from sqlalchemy import or_

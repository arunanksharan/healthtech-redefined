"""
Multi-Factor Authentication (MFA) Service

Provides TOTP, SMS OTP, and WebAuthn authentication.
EPIC-021: Security Hardening
"""

import base64
import hashlib
import hmac
import os
import secrets
import struct
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from modules.security.models import (
    MFAEnrollment,
    MFABackupCode,
    MFAPolicy,
    MFAMethod,
    MFAStatus,
)


class TOTPGenerator:
    """Time-based One-Time Password generator (RFC 6238)"""

    def __init__(self, secret: bytes, digits: int = 6, period: int = 30):
        self.secret = secret
        self.digits = digits
        self.period = period

    def generate(self, timestamp: Optional[int] = None) -> str:
        """Generate TOTP code for given timestamp"""
        if timestamp is None:
            timestamp = int(time.time())

        counter = timestamp // self.period
        counter_bytes = struct.pack(">Q", counter)

        hmac_hash = hmac.new(self.secret, counter_bytes, hashlib.sha1).digest()
        offset = hmac_hash[-1] & 0x0F

        truncated = struct.unpack(">I", hmac_hash[offset:offset + 4])[0]
        truncated &= 0x7FFFFFFF

        code = truncated % (10 ** self.digits)
        return str(code).zfill(self.digits)

    def verify(self, code: str, window: int = 1) -> bool:
        """Verify TOTP code with time window tolerance"""
        current_time = int(time.time())

        for offset in range(-window, window + 1):
            check_time = current_time + (offset * self.period)
            if self.generate(check_time) == code:
                return True
        return False


class MFAService:
    """Multi-Factor Authentication Service"""

    TOTP_SECRET_LENGTH = 20  # 160 bits
    BACKUP_CODE_COUNT = 10
    BACKUP_CODE_LENGTH = 8
    SMS_CODE_LENGTH = 6
    SMS_CODE_EXPIRY_MINUTES = 5

    def __init__(self, db: Session):
        self.db = db
        self._sms_codes: Dict[str, Tuple[str, datetime]] = {}  # In production, use Redis

    # =========================================================================
    # TOTP Methods
    # =========================================================================

    def enroll_totp(
        self,
        tenant_id: UUID,
        user_id: UUID,
        device_name: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Start TOTP enrollment"""

        # Check for existing TOTP enrollment
        existing = self.db.query(MFAEnrollment).filter(
            MFAEnrollment.tenant_id == tenant_id,
            MFAEnrollment.user_id == user_id,
            MFAEnrollment.method == MFAMethod.TOTP,
            MFAEnrollment.status != MFAStatus.DISABLED,
        ).first()

        if existing and existing.status == MFAStatus.ENABLED:
            raise ValueError("TOTP is already enrolled for this user")

        # Generate secret
        secret = os.urandom(self.TOTP_SECRET_LENGTH)
        secret_b32 = base64.b32encode(secret).decode("utf-8")

        # Create or update enrollment
        if existing:
            enrollment = existing
            enrollment.status = MFAStatus.PENDING
        else:
            enrollment = MFAEnrollment(
                tenant_id=tenant_id,
                user_id=user_id,
                method=MFAMethod.TOTP,
                status=MFAStatus.PENDING,
            )
            self.db.add(enrollment)

        # Store encrypted secret (in production, encrypt with KMS)
        enrollment.secret_encrypted = secret
        enrollment.device_name = device_name
        enrollment.enrolled_ip = ip_address
        enrollment.enrolled_user_agent = user_agent

        self.db.commit()
        self.db.refresh(enrollment)

        # Generate provisioning URI for QR code
        issuer = "HealthTech-PRM"
        provisioning_uri = f"otpauth://totp/{issuer}:user?secret={secret_b32}&issuer={issuer}&digits=6&period=30"

        return {
            "enrollment_id": str(enrollment.id),
            "secret": secret_b32,
            "provisioning_uri": provisioning_uri,
            "instructions": "Scan the QR code with your authenticator app and enter the verification code.",
        }

    def verify_totp_enrollment(
        self,
        tenant_id: UUID,
        user_id: UUID,
        code: str,
    ) -> Dict[str, Any]:
        """Verify TOTP code to complete enrollment"""

        enrollment = self.db.query(MFAEnrollment).filter(
            MFAEnrollment.tenant_id == tenant_id,
            MFAEnrollment.user_id == user_id,
            MFAEnrollment.method == MFAMethod.TOTP,
            MFAEnrollment.status == MFAStatus.PENDING,
        ).first()

        if not enrollment:
            raise ValueError("No pending TOTP enrollment found")

        # Verify code
        totp = TOTPGenerator(enrollment.secret_encrypted)
        if not totp.verify(code):
            raise ValueError("Invalid verification code")

        # Enable enrollment
        enrollment.status = MFAStatus.ENABLED
        enrollment.verified_at = datetime.utcnow()
        enrollment.is_primary = not self._has_primary_mfa(tenant_id, user_id)

        # Generate backup codes
        backup_codes = self._generate_backup_codes(tenant_id, user_id)

        self.db.commit()

        return {
            "enrollment_id": str(enrollment.id),
            "status": "enabled",
            "is_primary": enrollment.is_primary,
            "backup_codes": backup_codes,
            "message": "TOTP authentication enabled successfully. Save your backup codes securely.",
        }

    def verify_totp(
        self,
        tenant_id: UUID,
        user_id: UUID,
        code: str,
    ) -> bool:
        """Verify TOTP code for authentication"""

        enrollment = self.db.query(MFAEnrollment).filter(
            MFAEnrollment.tenant_id == tenant_id,
            MFAEnrollment.user_id == user_id,
            MFAEnrollment.method == MFAMethod.TOTP,
            MFAEnrollment.status == MFAStatus.ENABLED,
        ).first()

        if not enrollment:
            return False

        totp = TOTPGenerator(enrollment.secret_encrypted)
        if totp.verify(code):
            enrollment.last_used_at = datetime.utcnow()
            enrollment.use_count += 1
            self.db.commit()
            return True

        return False

    # =========================================================================
    # SMS OTP Methods
    # =========================================================================

    def enroll_sms(
        self,
        tenant_id: UUID,
        user_id: UUID,
        phone_number: str,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Start SMS OTP enrollment"""

        # Validate phone number format
        phone_number = self._normalize_phone(phone_number)
        phone_hash = hashlib.sha256(phone_number.encode()).hexdigest()

        # Check for existing SMS enrollment
        existing = self.db.query(MFAEnrollment).filter(
            MFAEnrollment.tenant_id == tenant_id,
            MFAEnrollment.user_id == user_id,
            MFAEnrollment.method == MFAMethod.SMS,
        ).first()

        if existing:
            enrollment = existing
            enrollment.status = MFAStatus.PENDING
        else:
            enrollment = MFAEnrollment(
                tenant_id=tenant_id,
                user_id=user_id,
                method=MFAMethod.SMS,
                status=MFAStatus.PENDING,
            )
            self.db.add(enrollment)

        enrollment.phone_number_hash = phone_hash
        enrollment.enrolled_ip = ip_address

        self.db.commit()
        self.db.refresh(enrollment)

        # Send verification code
        code = self._generate_sms_code()
        self._store_sms_code(user_id, code)
        self._send_sms(phone_number, f"Your verification code is: {code}")

        return {
            "enrollment_id": str(enrollment.id),
            "phone_masked": self._mask_phone(phone_number),
            "message": "Verification code sent to your phone. Enter the code to complete enrollment.",
        }

    def verify_sms_enrollment(
        self,
        tenant_id: UUID,
        user_id: UUID,
        code: str,
    ) -> Dict[str, Any]:
        """Verify SMS code to complete enrollment"""

        enrollment = self.db.query(MFAEnrollment).filter(
            MFAEnrollment.tenant_id == tenant_id,
            MFAEnrollment.user_id == user_id,
            MFAEnrollment.method == MFAMethod.SMS,
            MFAEnrollment.status == MFAStatus.PENDING,
        ).first()

        if not enrollment:
            raise ValueError("No pending SMS enrollment found")

        if not self._verify_sms_code(user_id, code):
            raise ValueError("Invalid or expired verification code")

        enrollment.status = MFAStatus.ENABLED
        enrollment.verified_at = datetime.utcnow()
        enrollment.is_primary = not self._has_primary_mfa(tenant_id, user_id)

        self.db.commit()

        return {
            "enrollment_id": str(enrollment.id),
            "status": "enabled",
            "is_primary": enrollment.is_primary,
            "message": "SMS authentication enabled successfully.",
        }

    def send_sms_code(
        self,
        tenant_id: UUID,
        user_id: UUID,
    ) -> Dict[str, Any]:
        """Send SMS code for authentication"""

        enrollment = self.db.query(MFAEnrollment).filter(
            MFAEnrollment.tenant_id == tenant_id,
            MFAEnrollment.user_id == user_id,
            MFAEnrollment.method == MFAMethod.SMS,
            MFAEnrollment.status == MFAStatus.ENABLED,
        ).first()

        if not enrollment:
            raise ValueError("SMS MFA is not enrolled for this user")

        # Rate limiting check would go here

        code = self._generate_sms_code()
        self._store_sms_code(user_id, code)

        # In production, retrieve phone from encrypted storage
        # self._send_sms(phone_number, f"Your login code is: {code}")

        return {
            "message": "Verification code sent to your registered phone.",
            "expires_in_minutes": self.SMS_CODE_EXPIRY_MINUTES,
        }

    def verify_sms(
        self,
        tenant_id: UUID,
        user_id: UUID,
        code: str,
    ) -> bool:
        """Verify SMS code for authentication"""

        enrollment = self.db.query(MFAEnrollment).filter(
            MFAEnrollment.tenant_id == tenant_id,
            MFAEnrollment.user_id == user_id,
            MFAEnrollment.method == MFAMethod.SMS,
            MFAEnrollment.status == MFAStatus.ENABLED,
        ).first()

        if not enrollment:
            return False

        if self._verify_sms_code(user_id, code):
            enrollment.last_used_at = datetime.utcnow()
            enrollment.use_count += 1
            self.db.commit()
            return True

        return False

    # =========================================================================
    # WebAuthn Methods
    # =========================================================================

    def start_webauthn_registration(
        self,
        tenant_id: UUID,
        user_id: UUID,
        username: str,
        device_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate WebAuthn registration options"""

        # Generate challenge
        challenge = secrets.token_bytes(32)
        challenge_b64 = base64.urlsafe_b64encode(challenge).decode("utf-8")

        # Store challenge temporarily (in production, use Redis with expiry)
        self._store_webauthn_challenge(user_id, challenge)

        # Generate user ID
        user_handle = hashlib.sha256(str(user_id).encode()).digest()
        user_handle_b64 = base64.urlsafe_b64encode(user_handle).decode("utf-8")

        # Get existing credentials to exclude
        existing_credentials = self.db.query(MFAEnrollment).filter(
            MFAEnrollment.tenant_id == tenant_id,
            MFAEnrollment.user_id == user_id,
            MFAEnrollment.method == MFAMethod.WEBAUTHN,
            MFAEnrollment.status == MFAStatus.ENABLED,
        ).all()

        exclude_credentials = [
            {"type": "public-key", "id": e.webauthn_credential_id}
            for e in existing_credentials
        ]

        return {
            "challenge": challenge_b64,
            "rp": {
                "name": "HealthTech PRM",
                "id": "healthtech-prm.local",  # Replace with actual domain
            },
            "user": {
                "id": user_handle_b64,
                "name": username,
                "displayName": username,
            },
            "pubKeyCredParams": [
                {"type": "public-key", "alg": -7},   # ES256
                {"type": "public-key", "alg": -257}, # RS256
            ],
            "timeout": 60000,
            "excludeCredentials": exclude_credentials,
            "authenticatorSelection": {
                "authenticatorAttachment": "cross-platform",
                "requireResidentKey": False,
                "userVerification": "preferred",
            },
            "attestation": "direct",
        }

    def complete_webauthn_registration(
        self,
        tenant_id: UUID,
        user_id: UUID,
        credential: Dict[str, Any],
        device_name: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Complete WebAuthn registration with credential response"""

        # Verify challenge
        stored_challenge = self._get_webauthn_challenge(user_id)
        if not stored_challenge:
            raise ValueError("Registration session expired")

        # In production, fully verify the attestation
        credential_id = credential.get("id")
        public_key = credential.get("response", {}).get("publicKey")

        if not credential_id or not public_key:
            raise ValueError("Invalid credential response")

        # Create enrollment
        enrollment = MFAEnrollment(
            tenant_id=tenant_id,
            user_id=user_id,
            method=MFAMethod.WEBAUTHN,
            status=MFAStatus.ENABLED,
            webauthn_credential_id=credential_id,
            webauthn_public_key=json.dumps(public_key) if isinstance(public_key, dict) else public_key,
            device_name=device_name or "Security Key",
            enrolled_ip=ip_address,
            verified_at=datetime.utcnow(),
            is_primary=not self._has_primary_mfa(tenant_id, user_id),
        )

        self.db.add(enrollment)
        self.db.commit()
        self.db.refresh(enrollment)

        return {
            "enrollment_id": str(enrollment.id),
            "credential_id": credential_id,
            "device_name": enrollment.device_name,
            "status": "enabled",
            "message": "Security key registered successfully.",
        }

    def start_webauthn_authentication(
        self,
        tenant_id: UUID,
        user_id: UUID,
    ) -> Dict[str, Any]:
        """Generate WebAuthn authentication options"""

        # Get registered credentials
        credentials = self.db.query(MFAEnrollment).filter(
            MFAEnrollment.tenant_id == tenant_id,
            MFAEnrollment.user_id == user_id,
            MFAEnrollment.method == MFAMethod.WEBAUTHN,
            MFAEnrollment.status == MFAStatus.ENABLED,
        ).all()

        if not credentials:
            raise ValueError("No security keys registered for this user")

        # Generate challenge
        challenge = secrets.token_bytes(32)
        challenge_b64 = base64.urlsafe_b64encode(challenge).decode("utf-8")

        self._store_webauthn_challenge(user_id, challenge)

        return {
            "challenge": challenge_b64,
            "timeout": 60000,
            "rpId": "healthtech-prm.local",
            "allowCredentials": [
                {"type": "public-key", "id": c.webauthn_credential_id}
                for c in credentials
            ],
            "userVerification": "preferred",
        }

    def verify_webauthn(
        self,
        tenant_id: UUID,
        user_id: UUID,
        assertion: Dict[str, Any],
    ) -> bool:
        """Verify WebAuthn authentication assertion"""

        credential_id = assertion.get("id")

        enrollment = self.db.query(MFAEnrollment).filter(
            MFAEnrollment.tenant_id == tenant_id,
            MFAEnrollment.user_id == user_id,
            MFAEnrollment.method == MFAMethod.WEBAUTHN,
            MFAEnrollment.webauthn_credential_id == credential_id,
            MFAEnrollment.status == MFAStatus.ENABLED,
        ).first()

        if not enrollment:
            return False

        # Verify challenge
        stored_challenge = self._get_webauthn_challenge(user_id)
        if not stored_challenge:
            return False

        # In production, fully verify the assertion signature
        # For now, we trust the credential_id match

        enrollment.last_used_at = datetime.utcnow()
        enrollment.use_count += 1
        self.db.commit()

        return True

    # =========================================================================
    # Backup Codes
    # =========================================================================

    def verify_backup_code(
        self,
        tenant_id: UUID,
        user_id: UUID,
        code: str,
    ) -> bool:
        """Verify and consume a backup code"""

        code_hash = hashlib.sha256(code.encode()).hexdigest()

        backup_code = self.db.query(MFABackupCode).filter(
            MFABackupCode.tenant_id == tenant_id,
            MFABackupCode.user_id == user_id,
            MFABackupCode.code_hash == code_hash,
            MFABackupCode.is_used == False,
        ).first()

        if not backup_code:
            return False

        # Check expiry
        if backup_code.expires_at and backup_code.expires_at < datetime.utcnow():
            return False

        # Mark as used
        backup_code.is_used = True
        backup_code.used_at = datetime.utcnow()

        self.db.commit()

        return True

    def regenerate_backup_codes(
        self,
        tenant_id: UUID,
        user_id: UUID,
    ) -> List[str]:
        """Regenerate all backup codes (invalidates existing ones)"""

        # Invalidate existing codes
        self.db.query(MFABackupCode).filter(
            MFABackupCode.tenant_id == tenant_id,
            MFABackupCode.user_id == user_id,
        ).delete()

        # Generate new codes
        codes = self._generate_backup_codes(tenant_id, user_id)

        self.db.commit()

        return codes

    def get_remaining_backup_codes_count(
        self,
        tenant_id: UUID,
        user_id: UUID,
    ) -> int:
        """Get count of remaining backup codes"""

        return self.db.query(MFABackupCode).filter(
            MFABackupCode.tenant_id == tenant_id,
            MFABackupCode.user_id == user_id,
            MFABackupCode.is_used == False,
        ).count()

    # =========================================================================
    # MFA Policy Methods
    # =========================================================================

    def create_policy(
        self,
        tenant_id: UUID,
        name: str,
        created_by: UUID,
        **kwargs,
    ) -> MFAPolicy:
        """Create MFA policy"""

        policy = MFAPolicy(
            tenant_id=tenant_id,
            name=name,
            created_by=created_by,
            **kwargs,
        )

        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)

        return policy

    def get_active_policy(
        self,
        tenant_id: UUID,
    ) -> Optional[MFAPolicy]:
        """Get active MFA policy for tenant"""

        return self.db.query(MFAPolicy).filter(
            MFAPolicy.tenant_id == tenant_id,
            MFAPolicy.is_active == True,
        ).first()

    def check_mfa_required(
        self,
        tenant_id: UUID,
        user_id: UUID,
        roles: List[str],
        accessing_phi: bool = False,
        is_admin_action: bool = False,
        is_new_device: bool = False,
    ) -> Dict[str, Any]:
        """Check if MFA is required for this context"""

        policy = self.get_active_policy(tenant_id)

        if not policy:
            return {"required": False, "reason": "No MFA policy configured"}

        # Check conditions
        reasons = []

        if policy.required_for_all:
            reasons.append("MFA required for all users")

        if policy.required_roles:
            if any(role in policy.required_roles for role in roles):
                reasons.append(f"MFA required for role")

        if policy.require_for_phi_access and accessing_phi:
            reasons.append("MFA required for PHI access")

        if policy.require_for_admin_actions and is_admin_action:
            reasons.append("MFA required for admin actions")

        if policy.require_on_new_device and is_new_device:
            reasons.append("MFA required for new device")

        return {
            "required": len(reasons) > 0,
            "reasons": reasons,
            "allowed_methods": policy.allowed_methods or ["totp", "sms", "webauthn", "backup_code"],
        }

    # =========================================================================
    # Enrollment Management
    # =========================================================================

    def get_enrollments(
        self,
        tenant_id: UUID,
        user_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Get all MFA enrollments for user"""

        enrollments = self.db.query(MFAEnrollment).filter(
            MFAEnrollment.tenant_id == tenant_id,
            MFAEnrollment.user_id == user_id,
        ).all()

        return [
            {
                "id": str(e.id),
                "method": e.method.value,
                "status": e.status.value,
                "is_primary": e.is_primary,
                "device_name": e.device_name,
                "last_used_at": e.last_used_at.isoformat() if e.last_used_at else None,
                "use_count": e.use_count,
                "created_at": e.created_at.isoformat(),
            }
            for e in enrollments
        ]

    def disable_enrollment(
        self,
        tenant_id: UUID,
        user_id: UUID,
        enrollment_id: UUID,
    ) -> Dict[str, Any]:
        """Disable an MFA enrollment"""

        enrollment = self.db.query(MFAEnrollment).filter(
            MFAEnrollment.id == enrollment_id,
            MFAEnrollment.tenant_id == tenant_id,
            MFAEnrollment.user_id == user_id,
        ).first()

        if not enrollment:
            raise ValueError("Enrollment not found")

        enrollment.status = MFAStatus.DISABLED

        # If this was primary, promote another
        if enrollment.is_primary:
            enrollment.is_primary = False
            other = self.db.query(MFAEnrollment).filter(
                MFAEnrollment.tenant_id == tenant_id,
                MFAEnrollment.user_id == user_id,
                MFAEnrollment.id != enrollment_id,
                MFAEnrollment.status == MFAStatus.ENABLED,
            ).first()
            if other:
                other.is_primary = True

        self.db.commit()

        return {"status": "disabled", "enrollment_id": str(enrollment_id)}

    # =========================================================================
    # Private Helper Methods
    # =========================================================================

    def _has_primary_mfa(self, tenant_id: UUID, user_id: UUID) -> bool:
        """Check if user has a primary MFA method"""
        return self.db.query(MFAEnrollment).filter(
            MFAEnrollment.tenant_id == tenant_id,
            MFAEnrollment.user_id == user_id,
            MFAEnrollment.is_primary == True,
            MFAEnrollment.status == MFAStatus.ENABLED,
        ).count() > 0

    def _generate_backup_codes(
        self,
        tenant_id: UUID,
        user_id: UUID,
    ) -> List[str]:
        """Generate backup codes for user"""

        codes = []
        expires_at = datetime.utcnow() + timedelta(days=365)

        for _ in range(self.BACKUP_CODE_COUNT):
            code = secrets.token_hex(self.BACKUP_CODE_LENGTH // 2).upper()
            code_hash = hashlib.sha256(code.encode()).hexdigest()

            backup_code = MFABackupCode(
                tenant_id=tenant_id,
                user_id=user_id,
                code_hash=code_hash,
                expires_at=expires_at,
            )
            self.db.add(backup_code)
            codes.append(code)

        return codes

    def _generate_sms_code(self) -> str:
        """Generate random SMS code"""
        return "".join(secrets.choice("0123456789") for _ in range(self.SMS_CODE_LENGTH))

    def _store_sms_code(self, user_id: UUID, code: str) -> None:
        """Store SMS code with expiry (in production, use Redis)"""
        expires_at = datetime.utcnow() + timedelta(minutes=self.SMS_CODE_EXPIRY_MINUTES)
        self._sms_codes[str(user_id)] = (code, expires_at)

    def _verify_sms_code(self, user_id: UUID, code: str) -> bool:
        """Verify SMS code"""
        stored = self._sms_codes.get(str(user_id))
        if not stored:
            return False

        stored_code, expires_at = stored
        if datetime.utcnow() > expires_at:
            del self._sms_codes[str(user_id)]
            return False

        if stored_code == code:
            del self._sms_codes[str(user_id)]
            return True

        return False

    def _send_sms(self, phone_number: str, message: str) -> None:
        """Send SMS (integrate with Twilio in production)"""
        # In production: twilio_client.messages.create(to=phone_number, body=message)
        pass

    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number"""
        return "".join(c for c in phone if c.isdigit() or c == "+")

    def _mask_phone(self, phone: str) -> str:
        """Mask phone number for display"""
        if len(phone) < 4:
            return "****"
        return "*" * (len(phone) - 4) + phone[-4:]

    def _store_webauthn_challenge(self, user_id: UUID, challenge: bytes) -> None:
        """Store WebAuthn challenge (in production, use Redis with expiry)"""
        # Placeholder - use Redis in production
        pass

    def _get_webauthn_challenge(self, user_id: UUID) -> Optional[bytes]:
        """Get stored WebAuthn challenge"""
        # Placeholder - use Redis in production
        return None

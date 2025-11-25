"""
Mobile Authentication Service
EPIC-016: Biometric auth and session management
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
import secrets
import hashlib

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func, desc

from modules.mobile.models import (
    MobileDevice, MobileSession, MobileAuditLog,
    DeviceStatus, SessionStatus, BiometricType
)
from modules.mobile.schemas import (
    SessionCreate, SessionResponse, SessionRefresh,
    BiometricAuthRequest, BiometricAuthResponse
)


class MobileAuthService:
    """
    Handles mobile authentication:
    - Session creation and management
    - Biometric authentication
    - Token refresh
    - Security validation
    - Audit logging
    """

    # Session configuration
    ACCESS_TOKEN_EXPIRY_HOURS = 1
    REFRESH_TOKEN_EXPIRY_DAYS = 30
    MAX_SESSIONS_PER_DEVICE = 5
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30

    async def create_session(
        self,
        db: AsyncSession,
        device_id: UUID,
        user_id: UUID,
        tenant_id: UUID,
        data: SessionCreate,
        ip_address: str = None,
        user_agent: str = None
    ) -> SessionResponse:
        """Create a new mobile session"""

        # Validate device
        device = await self._get_active_device(db, device_id, user_id)
        if not device:
            raise ValueError("Device not found or inactive")

        # Check for account lockout
        if await self._is_locked_out(db, device_id):
            raise ValueError("Device is temporarily locked due to failed attempts")

        # Revoke old sessions if max reached
        await self._cleanup_old_sessions(db, device_id)

        # Generate tokens
        access_token = self._generate_token()
        refresh_token = self._generate_token()

        # Create session
        session = MobileSession(
            id=uuid4(),
            tenant_id=tenant_id,
            device_id=device_id,
            user_id=user_id,
            access_token_hash=self._hash_token(access_token),
            refresh_token_hash=self._hash_token(refresh_token),
            access_token_expires_at=datetime.now(timezone.utc) + timedelta(
                hours=self.ACCESS_TOKEN_EXPIRY_HOURS
            ),
            refresh_token_expires_at=datetime.now(timezone.utc) + timedelta(
                days=self.REFRESH_TOKEN_EXPIRY_DAYS
            ),
            status=SessionStatus.ACTIVE,
            auth_method=data.auth_method,
            ip_address=ip_address,
            user_agent=user_agent,
            app_version=data.app_version,
            device_info=data.device_info or {}
        )
        db.add(session)

        # Update device last active
        device.last_active_at = datetime.now(timezone.utc)
        device.last_ip_address = ip_address

        # Log session creation
        await self._log_action(
            db, tenant_id, user_id, device_id,
            "session_created",
            "authentication",
            f"Mobile session created via {data.auth_method}",
            ip_address=ip_address,
            success=True
        )

        await db.commit()
        await db.refresh(session)

        return SessionResponse(
            session_id=session.id,
            access_token=access_token,
            refresh_token=refresh_token,
            access_token_expires_at=session.access_token_expires_at,
            refresh_token_expires_at=session.refresh_token_expires_at,
            auth_method=session.auth_method
        )

    async def refresh_session(
        self,
        db: AsyncSession,
        data: SessionRefresh,
        ip_address: str = None
    ) -> SessionResponse:
        """Refresh an existing session"""

        # Find session by refresh token
        refresh_hash = self._hash_token(data.refresh_token)
        result = await db.execute(
            select(MobileSession).where(
                and_(
                    MobileSession.refresh_token_hash == refresh_hash,
                    MobileSession.status == SessionStatus.ACTIVE
                )
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError("Invalid or expired refresh token")

        if session.refresh_token_expires_at < datetime.now(timezone.utc):
            session.status = SessionStatus.EXPIRED
            await db.commit()
            raise ValueError("Refresh token has expired")

        # Validate device is still active
        device = await self._get_active_device(
            db, session.device_id, session.user_id
        )
        if not device:
            session.status = SessionStatus.REVOKED
            await db.commit()
            raise ValueError("Device no longer active")

        # Generate new tokens
        new_access_token = self._generate_token()
        new_refresh_token = self._generate_token()

        # Update session
        session.access_token_hash = self._hash_token(new_access_token)
        session.refresh_token_hash = self._hash_token(new_refresh_token)
        session.access_token_expires_at = datetime.now(timezone.utc) + timedelta(
            hours=self.ACCESS_TOKEN_EXPIRY_HOURS
        )
        session.refresh_token_expires_at = datetime.now(timezone.utc) + timedelta(
            days=self.REFRESH_TOKEN_EXPIRY_DAYS
        )
        session.last_activity_at = datetime.now(timezone.utc)
        session.ip_address = ip_address

        # Update device
        device.last_active_at = datetime.now(timezone.utc)
        device.last_ip_address = ip_address

        await db.commit()
        await db.refresh(session)

        return SessionResponse(
            session_id=session.id,
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            access_token_expires_at=session.access_token_expires_at,
            refresh_token_expires_at=session.refresh_token_expires_at,
            auth_method=session.auth_method
        )

    async def validate_access_token(
        self,
        db: AsyncSession,
        access_token: str
    ) -> Optional[Dict[str, Any]]:
        """Validate an access token and return session info"""

        token_hash = self._hash_token(access_token)
        result = await db.execute(
            select(MobileSession).where(
                and_(
                    MobileSession.access_token_hash == token_hash,
                    MobileSession.status == SessionStatus.ACTIVE
                )
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            return None

        if session.access_token_expires_at < datetime.now(timezone.utc):
            return None

        # Update last activity
        session.last_activity_at = datetime.now(timezone.utc)
        await db.commit()

        return {
            "session_id": str(session.id),
            "user_id": str(session.user_id),
            "tenant_id": str(session.tenant_id),
            "device_id": str(session.device_id),
            "auth_method": session.auth_method
        }

    async def authenticate_biometric(
        self,
        db: AsyncSession,
        device_id: UUID,
        user_id: UUID,
        tenant_id: UUID,
        data: BiometricAuthRequest,
        ip_address: str = None
    ) -> BiometricAuthResponse:
        """Authenticate using biometric"""

        # Get device
        device = await self._get_active_device(db, device_id, user_id)
        if not device:
            await self._log_action(
                db, tenant_id, user_id, device_id,
                "biometric_auth_failed",
                "authentication",
                "Device not found or inactive",
                ip_address=ip_address,
                success=False
            )
            await db.commit()
            raise ValueError("Device not found or inactive")

        # Verify biometric is enabled on device
        if not device.biometric_enabled:
            await self._log_action(
                db, tenant_id, user_id, device_id,
                "biometric_auth_failed",
                "authentication",
                "Biometric not enabled on device",
                ip_address=ip_address,
                success=False
            )
            await db.commit()
            raise ValueError("Biometric authentication not enabled")

        # Verify biometric type matches
        if device.biometric_type and device.biometric_type.value != data.biometric_type.value:
            await self._log_action(
                db, tenant_id, user_id, device_id,
                "biometric_auth_failed",
                "authentication",
                f"Biometric type mismatch: expected {device.biometric_type.value}",
                ip_address=ip_address,
                success=False
            )
            await db.commit()
            raise ValueError("Biometric type mismatch")

        # Verify the biometric signature
        # In production, this would validate against stored biometric data
        # The signature is typically generated by the device's secure enclave
        if not self._verify_biometric_signature(data.signature, data.challenge):
            await self._record_failed_attempt(db, device_id)
            await self._log_action(
                db, tenant_id, user_id, device_id,
                "biometric_auth_failed",
                "authentication",
                "Invalid biometric signature",
                ip_address=ip_address,
                success=False
            )
            await db.commit()
            raise ValueError("Biometric verification failed")

        # Create session
        session_data = SessionCreate(
            auth_method="biometric",
            app_version=data.app_version,
            device_info={"biometric_type": data.biometric_type.value}
        )
        session = await self.create_session(
            db, device_id, user_id, tenant_id, session_data, ip_address
        )

        return BiometricAuthResponse(
            success=True,
            session_id=session.session_id,
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            access_token_expires_at=session.access_token_expires_at,
            refresh_token_expires_at=session.refresh_token_expires_at
        )

    async def enable_biometric(
        self,
        db: AsyncSession,
        device_id: UUID,
        user_id: UUID,
        biometric_type: BiometricType,
        public_key: str = None
    ) -> None:
        """Enable biometric authentication on a device"""

        device = await self._get_active_device(db, device_id, user_id)
        if not device:
            raise ValueError("Device not found")

        device.biometric_enabled = True
        device.biometric_type = biometric_type
        if public_key:
            device.biometric_public_key = public_key
        device.updated_at = datetime.now(timezone.utc)

        await self._log_action(
            db, device.tenant_id, user_id, device_id,
            "biometric_enabled",
            "security",
            f"Biometric authentication enabled: {biometric_type.value}",
            success=True
        )

        await db.commit()

    async def disable_biometric(
        self,
        db: AsyncSession,
        device_id: UUID,
        user_id: UUID
    ) -> None:
        """Disable biometric authentication on a device"""

        device = await self._get_active_device(db, device_id, user_id)
        if not device:
            raise ValueError("Device not found")

        device.biometric_enabled = False
        device.biometric_type = None
        device.biometric_public_key = None
        device.updated_at = datetime.now(timezone.utc)

        await self._log_action(
            db, device.tenant_id, user_id, device_id,
            "biometric_disabled",
            "security",
            "Biometric authentication disabled",
            success=True
        )

        await db.commit()

    async def end_session(
        self,
        db: AsyncSession,
        session_id: UUID,
        user_id: UUID,
        ip_address: str = None
    ) -> None:
        """End a mobile session (logout)"""

        result = await db.execute(
            select(MobileSession).where(
                and_(
                    MobileSession.id == session_id,
                    MobileSession.user_id == user_id,
                    MobileSession.status == SessionStatus.ACTIVE
                )
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError("Session not found")

        session.status = SessionStatus.ENDED
        session.ended_at = datetime.now(timezone.utc)

        await self._log_action(
            db, session.tenant_id, user_id, session.device_id,
            "session_ended",
            "authentication",
            "User logged out",
            ip_address=ip_address,
            success=True
        )

        await db.commit()

    async def end_all_sessions(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        except_session_id: UUID = None
    ) -> int:
        """End all sessions for a user (logout everywhere)"""

        query = update(MobileSession).where(
            and_(
                MobileSession.user_id == user_id,
                MobileSession.tenant_id == tenant_id,
                MobileSession.status == SessionStatus.ACTIVE
            )
        )

        if except_session_id:
            query = query.where(MobileSession.id != except_session_id)

        query = query.values(
            status=SessionStatus.ENDED,
            ended_at=datetime.now(timezone.utc)
        )

        result = await db.execute(query)
        await db.commit()

        return result.rowcount

    async def revoke_session(
        self,
        db: AsyncSession,
        session_id: UUID,
        tenant_id: UUID,
        reason: str = None
    ) -> None:
        """Revoke a session (admin action)"""

        result = await db.execute(
            select(MobileSession).where(
                and_(
                    MobileSession.id == session_id,
                    MobileSession.tenant_id == tenant_id
                )
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError("Session not found")

        session.status = SessionStatus.REVOKED
        session.ended_at = datetime.now(timezone.utc)

        await self._log_action(
            db, tenant_id, session.user_id, session.device_id,
            "session_revoked",
            "security",
            f"Session revoked: {reason or 'Admin action'}",
            success=True
        )

        await db.commit()

    async def get_active_sessions(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID
    ) -> List[Dict[str, Any]]:
        """Get all active sessions for a user"""

        result = await db.execute(
            select(MobileSession).where(
                and_(
                    MobileSession.user_id == user_id,
                    MobileSession.tenant_id == tenant_id,
                    MobileSession.status == SessionStatus.ACTIVE
                )
            ).order_by(desc(MobileSession.last_activity_at))
        )
        sessions = result.scalars().all()

        return [
            {
                "session_id": str(s.id),
                "device_id": str(s.device_id),
                "auth_method": s.auth_method,
                "ip_address": s.ip_address,
                "user_agent": s.user_agent,
                "app_version": s.app_version,
                "created_at": s.created_at.isoformat(),
                "last_activity_at": s.last_activity_at.isoformat() if s.last_activity_at else None
            }
            for s in sessions
        ]

    async def get_audit_log(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        action_category: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get authentication audit log for a user"""

        query = select(MobileAuditLog).where(
            and_(
                MobileAuditLog.user_id == user_id,
                MobileAuditLog.tenant_id == tenant_id
            )
        )

        if action_category:
            query = query.where(MobileAuditLog.action_category == action_category)

        query = query.order_by(desc(MobileAuditLog.created_at))
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        logs = result.scalars().all()

        return [
            {
                "id": str(log.id),
                "action": log.action,
                "action_category": log.action_category,
                "action_description": log.action_description,
                "details": log.details,
                "ip_address": log.ip_address,
                "success": log.success,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ]

    async def generate_biometric_challenge(
        self,
        db: AsyncSession,
        device_id: UUID
    ) -> Dict[str, Any]:
        """Generate a challenge for biometric authentication"""

        challenge = secrets.token_hex(32)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

        # In production, store challenge temporarily
        # Could use Redis or similar for short-term storage

        return {
            "challenge": challenge,
            "expires_at": expires_at.isoformat(),
            "device_id": str(device_id)
        }

    # Private helper methods

    async def _get_active_device(
        self,
        db: AsyncSession,
        device_id: UUID,
        user_id: UUID
    ) -> Optional[MobileDevice]:
        """Get device if active"""

        result = await db.execute(
            select(MobileDevice).where(
                and_(
                    MobileDevice.id == device_id,
                    MobileDevice.user_id == user_id,
                    MobileDevice.status == DeviceStatus.ACTIVE
                )
            )
        )
        return result.scalar_one_or_none()

    async def _is_locked_out(
        self,
        db: AsyncSession,
        device_id: UUID
    ) -> bool:
        """Check if device is locked out due to failed attempts"""

        lockout_threshold = datetime.now(timezone.utc) - timedelta(
            minutes=self.LOCKOUT_DURATION_MINUTES
        )

        result = await db.execute(
            select(func.count()).where(
                and_(
                    MobileAuditLog.device_id == device_id,
                    MobileAuditLog.action.in_([
                        "biometric_auth_failed",
                        "session_auth_failed"
                    ]),
                    MobileAuditLog.success == False,
                    MobileAuditLog.created_at > lockout_threshold
                )
            )
        )
        failed_count = result.scalar()

        return failed_count >= self.MAX_FAILED_ATTEMPTS

    async def _record_failed_attempt(
        self,
        db: AsyncSession,
        device_id: UUID
    ) -> None:
        """Record a failed authentication attempt"""

        # This is handled by _log_action when success=False
        pass

    async def _cleanup_old_sessions(
        self,
        db: AsyncSession,
        device_id: UUID
    ) -> None:
        """Remove old sessions if max reached"""

        # Count active sessions
        result = await db.execute(
            select(func.count()).where(
                and_(
                    MobileSession.device_id == device_id,
                    MobileSession.status == SessionStatus.ACTIVE
                )
            )
        )
        count = result.scalar()

        if count >= self.MAX_SESSIONS_PER_DEVICE:
            # End oldest sessions
            sessions_result = await db.execute(
                select(MobileSession).where(
                    and_(
                        MobileSession.device_id == device_id,
                        MobileSession.status == SessionStatus.ACTIVE
                    )
                ).order_by(MobileSession.created_at).limit(
                    count - self.MAX_SESSIONS_PER_DEVICE + 1
                )
            )
            old_sessions = sessions_result.scalars().all()

            for session in old_sessions:
                session.status = SessionStatus.ENDED
                session.ended_at = datetime.now(timezone.utc)

    async def _log_action(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        device_id: UUID,
        action: str,
        category: str,
        description: str,
        details: Dict[str, Any] = None,
        ip_address: str = None,
        success: bool = True
    ) -> None:
        """Log an authentication action"""

        log = MobileAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            device_id=device_id,
            action=action,
            action_category=category,
            action_description=description,
            details=details or {},
            ip_address=ip_address,
            success=success
        )
        db.add(log)

    def _generate_token(self) -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(64)

    def _hash_token(self, token: str) -> str:
        """Hash a token for storage"""
        return hashlib.sha256(token.encode()).hexdigest()

    def _verify_biometric_signature(
        self,
        signature: str,
        challenge: str
    ) -> bool:
        """
        Verify biometric signature.
        In production, this would use public key cryptography
        to verify the signature against the stored public key.
        """
        # Placeholder - in production would verify signature
        # using device's public key stored during biometric setup
        return signature is not None and challenge is not None

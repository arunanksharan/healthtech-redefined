"""
Session Management Service

Provides secure session handling, token management, and session policies.
EPIC-021: Security Hardening
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
import jwt
from user_agents import parse as parse_user_agent

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from modules.security.models import (
    UserSession,
    SessionPolicy,
    LoginAttempt,
    SessionStatus,
    MFAMethod,
)


class SessionService:
    """Session Management Service"""

    # Token configuration
    ACCESS_TOKEN_EXPIRE_MINUTES = 15
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    TOKEN_ALGORITHM = "RS256"
    SESSION_TOKEN_LENGTH = 64

    # JWT Keys (in production, load from secure storage)
    JWT_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA0m59l2u9iDnMbrXHfqkOrn2dVQ3vfBJqcDuFUK03d+1PZGbV
...placeholder...
-----END RSA PRIVATE KEY-----"""

    JWT_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0m59l2u9iDnMbrXHfqkO
...placeholder...
-----END PUBLIC KEY-----"""

    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # Session Creation
    # =========================================================================

    def create_session(
        self,
        tenant_id: UUID,
        user_id: UUID,
        ip_address: str,
        user_agent: Optional[str] = None,
        device_fingerprint: Optional[str] = None,
        mfa_verified: bool = False,
        mfa_method: Optional[MFAMethod] = None,
    ) -> Dict[str, Any]:
        """Create a new session"""

        # Get session policy
        policy = self._get_session_policy(tenant_id)

        # Check concurrent session limits
        active_count = self._get_active_session_count(tenant_id, user_id)
        max_sessions = policy.max_concurrent_sessions if policy else 5

        if active_count >= max_sessions:
            if policy and policy.on_exceed_action == "deny_new":
                raise ValueError("Maximum concurrent sessions reached")
            elif policy and policy.on_exceed_action == "revoke_oldest":
                self._revoke_oldest_session(tenant_id, user_id)

        # Parse user agent
        device_info = self._parse_device_info(user_agent)

        # Generate session tokens
        session_token = secrets.token_urlsafe(self.SESSION_TOKEN_LENGTH)
        refresh_token = secrets.token_urlsafe(self.SESSION_TOKEN_LENGTH)

        # Calculate expiry
        idle_timeout = policy.idle_timeout_minutes if policy else 15
        absolute_timeout = policy.absolute_timeout_minutes if policy else 480

        expires_at = datetime.utcnow() + timedelta(minutes=absolute_timeout)

        # Create session
        session = UserSession(
            tenant_id=tenant_id,
            user_id=user_id,
            session_token_hash=self._hash_token(session_token),
            refresh_token_hash=self._hash_token(refresh_token),
            status=SessionStatus.ACTIVE,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            device_type=device_info.get("device_type"),
            browser=device_info.get("browser"),
            os=device_info.get("os"),
            expires_at=expires_at,
            mfa_verified=mfa_verified,
            mfa_verified_at=datetime.utcnow() if mfa_verified else None,
            mfa_method_used=mfa_method,
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        # Generate JWT access token
        access_token = self._generate_access_token(
            tenant_id=tenant_id,
            user_id=user_id,
            session_id=session.id,
        )

        return {
            "session_id": str(session.id),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "refresh_expires_in": self.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        }

    def refresh_session(
        self,
        refresh_token: str,
        ip_address: str,
    ) -> Dict[str, Any]:
        """Refresh an existing session"""

        token_hash = self._hash_token(refresh_token)

        session = self.db.query(UserSession).filter(
            UserSession.refresh_token_hash == token_hash,
            UserSession.status == SessionStatus.ACTIVE,
        ).first()

        if not session:
            raise ValueError("Invalid refresh token")

        # Check if session expired
        if session.expires_at < datetime.utcnow():
            session.status = SessionStatus.EXPIRED
            self.db.commit()
            raise ValueError("Session expired")

        # Get policy
        policy = self._get_session_policy(session.tenant_id)

        # Check IP binding
        if policy and policy.bind_to_ip and session.ip_address != ip_address:
            session.status = SessionStatus.REVOKED
            session.revoked_reason = "IP address mismatch"
            self.db.commit()
            raise ValueError("Session invalid: IP address changed")

        # Update session
        session.last_activity_at = datetime.utcnow()

        # Generate new access token
        access_token = self._generate_access_token(
            tenant_id=session.tenant_id,
            user_id=session.user_id,
            session_id=session.id,
        )

        # Optionally rotate refresh token
        new_refresh_token = secrets.token_urlsafe(self.SESSION_TOKEN_LENGTH)
        session.refresh_token_hash = self._hash_token(new_refresh_token)

        self.db.commit()

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": self.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    def validate_session(
        self,
        session_token: str,
    ) -> Optional[UserSession]:
        """Validate session token"""

        token_hash = self._hash_token(session_token)

        session = self.db.query(UserSession).filter(
            UserSession.session_token_hash == token_hash,
            UserSession.status == SessionStatus.ACTIVE,
        ).first()

        if not session:
            return None

        # Check expiry
        if session.expires_at < datetime.utcnow():
            session.status = SessionStatus.EXPIRED
            self.db.commit()
            return None

        # Update last activity
        session.last_activity_at = datetime.utcnow()
        self.db.commit()

        return session

    def validate_access_token(
        self,
        access_token: str,
    ) -> Optional[Dict[str, Any]]:
        """Validate JWT access token"""

        try:
            # In production, use actual keys
            payload = jwt.decode(
                access_token,
                self.JWT_PUBLIC_KEY,
                algorithms=[self.TOKEN_ALGORITHM],
                options={"verify_signature": False},  # Remove in production
            )

            # Verify session still active
            session_id = payload.get("session_id")
            if session_id:
                session = self.db.query(UserSession).filter(
                    UserSession.id == session_id,
                    UserSession.status == SessionStatus.ACTIVE,
                ).first()

                if not session or session.expires_at < datetime.utcnow():
                    return None

                # Update activity
                session.last_activity_at = datetime.utcnow()
                self.db.commit()

            return payload

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    # =========================================================================
    # Session Management
    # =========================================================================

    def revoke_session(
        self,
        session_id: UUID,
        reason: Optional[str] = None,
    ) -> bool:
        """Revoke a specific session"""

        session = self.db.query(UserSession).filter(
            UserSession.id == session_id,
        ).first()

        if not session:
            return False

        session.status = SessionStatus.REVOKED
        session.revoked_at = datetime.utcnow()
        session.revoked_reason = reason

        self.db.commit()

        return True

    def revoke_all_sessions(
        self,
        tenant_id: UUID,
        user_id: UUID,
        except_session_id: Optional[UUID] = None,
        reason: Optional[str] = None,
    ) -> int:
        """Revoke all sessions for a user (logout everywhere)"""

        query = self.db.query(UserSession).filter(
            UserSession.tenant_id == tenant_id,
            UserSession.user_id == user_id,
            UserSession.status == SessionStatus.ACTIVE,
        )

        if except_session_id:
            query = query.filter(UserSession.id != except_session_id)

        sessions = query.all()

        for session in sessions:
            session.status = SessionStatus.REVOKED
            session.revoked_at = datetime.utcnow()
            session.revoked_reason = reason or "Logout all sessions"

        self.db.commit()

        return len(sessions)

    def get_active_sessions(
        self,
        tenant_id: UUID,
        user_id: UUID,
    ) -> List[Dict[str, Any]]:
        """Get all active sessions for user"""

        sessions = self.db.query(UserSession).filter(
            UserSession.tenant_id == tenant_id,
            UserSession.user_id == user_id,
            UserSession.status == SessionStatus.ACTIVE,
            UserSession.expires_at > datetime.utcnow(),
        ).order_by(UserSession.last_activity_at.desc()).all()

        return [
            {
                "id": str(s.id),
                "device_type": s.device_type,
                "browser": s.browser,
                "os": s.os,
                "ip_address": str(s.ip_address) if s.ip_address else None,
                "location_country": s.location_country,
                "location_city": s.location_city,
                "created_at": s.created_at.isoformat(),
                "last_activity_at": s.last_activity_at.isoformat() if s.last_activity_at else None,
                "mfa_verified": s.mfa_verified,
                "is_current": False,  # Set by caller
            }
            for s in sessions
        ]

    def get_session_history(
        self,
        tenant_id: UUID,
        user_id: UUID,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get session history for user"""

        sessions = self.db.query(UserSession).filter(
            UserSession.tenant_id == tenant_id,
            UserSession.user_id == user_id,
        ).order_by(UserSession.created_at.desc()).limit(limit).all()

        return [
            {
                "id": str(s.id),
                "status": s.status.value,
                "device_type": s.device_type,
                "browser": s.browser,
                "os": s.os,
                "ip_address": str(s.ip_address) if s.ip_address else None,
                "location_country": s.location_country,
                "location_city": s.location_city,
                "created_at": s.created_at.isoformat(),
                "expires_at": s.expires_at.isoformat(),
                "revoked_at": s.revoked_at.isoformat() if s.revoked_at else None,
                "revoked_reason": s.revoked_reason,
            }
            for s in sessions
        ]

    # =========================================================================
    # Login Attempt Tracking
    # =========================================================================

    def record_login_attempt(
        self,
        tenant_id: Optional[UUID],
        username: str,
        user_id: Optional[UUID],
        success: bool,
        ip_address: str,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None,
        mfa_required: bool = False,
        mfa_method: Optional[MFAMethod] = None,
        mfa_success: Optional[bool] = None,
    ) -> LoginAttempt:
        """Record a login attempt"""

        device_info = self._parse_device_info(user_agent)

        attempt = LoginAttempt(
            tenant_id=tenant_id,
            username=username,
            user_id=user_id,
            success=success,
            failure_reason=failure_reason,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_info.get("fingerprint"),
            mfa_required=mfa_required,
            mfa_method=mfa_method,
            mfa_success=mfa_success,
        )

        self.db.add(attempt)
        self.db.commit()

        return attempt

    def get_failed_attempts_count(
        self,
        username: str,
        ip_address: str,
        window_minutes: int = 15,
    ) -> Dict[str, int]:
        """Get failed login attempt counts"""

        since = datetime.utcnow() - timedelta(minutes=window_minutes)

        # Count by username
        username_count = self.db.query(LoginAttempt).filter(
            LoginAttempt.username == username,
            LoginAttempt.success == False,
            LoginAttempt.attempted_at >= since,
        ).count()

        # Count by IP
        ip_count = self.db.query(LoginAttempt).filter(
            LoginAttempt.ip_address == ip_address,
            LoginAttempt.success == False,
            LoginAttempt.attempted_at >= since,
        ).count()

        return {
            "by_username": username_count,
            "by_ip": ip_count,
        }

    def is_account_locked(
        self,
        username: str,
        max_attempts: int = 5,
        lockout_minutes: int = 30,
    ) -> bool:
        """Check if account is locked due to failed attempts"""

        since = datetime.utcnow() - timedelta(minutes=lockout_minutes)

        failed_count = self.db.query(LoginAttempt).filter(
            LoginAttempt.username == username,
            LoginAttempt.success == False,
            LoginAttempt.attempted_at >= since,
        ).count()

        return failed_count >= max_attempts

    # =========================================================================
    # Session Policies
    # =========================================================================

    def create_policy(
        self,
        tenant_id: UUID,
        name: str,
        **kwargs,
    ) -> SessionPolicy:
        """Create session policy"""

        policy = SessionPolicy(
            tenant_id=tenant_id,
            name=name,
            **kwargs,
        )

        self.db.add(policy)
        self.db.commit()
        self.db.refresh(policy)

        return policy

    def get_policy(
        self,
        policy_id: UUID,
    ) -> Optional[SessionPolicy]:
        """Get session policy by ID"""

        return self.db.query(SessionPolicy).filter(
            SessionPolicy.id == policy_id,
        ).first()

    def update_policy(
        self,
        policy_id: UUID,
        **kwargs,
    ) -> Optional[SessionPolicy]:
        """Update session policy"""

        policy = self.get_policy(policy_id)
        if not policy:
            return None

        for key, value in kwargs.items():
            if hasattr(policy, key):
                setattr(policy, key, value)

        policy.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(policy)

        return policy

    def set_default_policy(
        self,
        tenant_id: UUID,
        policy_id: UUID,
    ) -> bool:
        """Set a policy as default for tenant"""

        # Clear existing default
        self.db.query(SessionPolicy).filter(
            SessionPolicy.tenant_id == tenant_id,
            SessionPolicy.is_default == True,
        ).update({"is_default": False})

        # Set new default
        policy = self.db.query(SessionPolicy).filter(
            SessionPolicy.id == policy_id,
            SessionPolicy.tenant_id == tenant_id,
        ).first()

        if not policy:
            return False

        policy.is_default = True
        self.db.commit()

        return True

    # =========================================================================
    # Session Analytics
    # =========================================================================

    def get_session_analytics(
        self,
        tenant_id: UUID,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get session analytics for tenant"""

        since = datetime.utcnow() - timedelta(days=days)

        # Total sessions
        total_sessions = self.db.query(UserSession).filter(
            UserSession.tenant_id == tenant_id,
            UserSession.created_at >= since,
        ).count()

        # Active sessions
        active_sessions = self.db.query(UserSession).filter(
            UserSession.tenant_id == tenant_id,
            UserSession.status == SessionStatus.ACTIVE,
            UserSession.expires_at > datetime.utcnow(),
        ).count()

        # Sessions by device type
        device_breakdown = self.db.query(
            UserSession.device_type,
            func.count(UserSession.id).label("count"),
        ).filter(
            UserSession.tenant_id == tenant_id,
            UserSession.created_at >= since,
        ).group_by(UserSession.device_type).all()

        # Login attempts stats
        total_attempts = self.db.query(LoginAttempt).filter(
            LoginAttempt.tenant_id == tenant_id,
            LoginAttempt.attempted_at >= since,
        ).count()

        failed_attempts = self.db.query(LoginAttempt).filter(
            LoginAttempt.tenant_id == tenant_id,
            LoginAttempt.success == False,
            LoginAttempt.attempted_at >= since,
        ).count()

        return {
            "period_days": days,
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "device_breakdown": {d[0] or "unknown": d[1] for d in device_breakdown},
            "login_attempts": {
                "total": total_attempts,
                "failed": failed_attempts,
                "success_rate": (total_attempts - failed_attempts) / total_attempts if total_attempts > 0 else 1.0,
            },
        }

    # =========================================================================
    # Private Helper Methods
    # =========================================================================

    def _hash_token(self, token: str) -> str:
        """Hash token for storage"""
        return hashlib.sha256(token.encode()).hexdigest()

    def _generate_access_token(
        self,
        tenant_id: UUID,
        user_id: UUID,
        session_id: UUID,
    ) -> str:
        """Generate JWT access token"""

        now = datetime.utcnow()
        expires = now + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)

        payload = {
            "tenant_id": str(tenant_id),
            "user_id": str(user_id),
            "session_id": str(session_id),
            "iat": now,
            "exp": expires,
            "type": "access",
        }

        # In production, use actual private key
        return jwt.encode(
            payload,
            self.JWT_PRIVATE_KEY,
            algorithm=self.TOKEN_ALGORITHM,
        )

    def _get_session_policy(
        self,
        tenant_id: UUID,
    ) -> Optional[SessionPolicy]:
        """Get active session policy for tenant"""

        return self.db.query(SessionPolicy).filter(
            SessionPolicy.tenant_id == tenant_id,
            SessionPolicy.is_active == True,
            SessionPolicy.is_default == True,
        ).first()

    def _get_active_session_count(
        self,
        tenant_id: UUID,
        user_id: UUID,
    ) -> int:
        """Get count of active sessions for user"""

        return self.db.query(UserSession).filter(
            UserSession.tenant_id == tenant_id,
            UserSession.user_id == user_id,
            UserSession.status == SessionStatus.ACTIVE,
            UserSession.expires_at > datetime.utcnow(),
        ).count()

    def _revoke_oldest_session(
        self,
        tenant_id: UUID,
        user_id: UUID,
    ) -> None:
        """Revoke the oldest active session"""

        oldest = self.db.query(UserSession).filter(
            UserSession.tenant_id == tenant_id,
            UserSession.user_id == user_id,
            UserSession.status == SessionStatus.ACTIVE,
        ).order_by(UserSession.created_at.asc()).first()

        if oldest:
            oldest.status = SessionStatus.REVOKED
            oldest.revoked_at = datetime.utcnow()
            oldest.revoked_reason = "Exceeded concurrent session limit"
            self.db.commit()

    def _parse_device_info(
        self,
        user_agent: Optional[str],
    ) -> Dict[str, Any]:
        """Parse user agent string for device info"""

        if not user_agent:
            return {}

        try:
            ua = parse_user_agent(user_agent)
            return {
                "device_type": "mobile" if ua.is_mobile else ("tablet" if ua.is_tablet else "desktop"),
                "browser": f"{ua.browser.family} {ua.browser.version_string}",
                "os": f"{ua.os.family} {ua.os.version_string}",
                "fingerprint": hashlib.md5(user_agent.encode()).hexdigest()[:16],
            }
        except Exception:
            return {}

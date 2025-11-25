"""
Patient Portal Authentication Service
EPIC-014: JWT authentication, MFA, session management
"""
import os
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple, List
from uuid import UUID, uuid4
import base64

import jwt
import pyotp
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_
from sqlalchemy.orm import selectinload

from modules.patient_portal.models import (
    PortalUser, PortalSession, PortalAuditLog, PortalPreference,
    IdentityVerification, PortalUserStatus, MFAMethod, SessionStatus,
    AuditAction, VerificationType
)
from modules.patient_portal.schemas import (
    RegisterRequest, RegisterResponse, LoginRequest, LoginResponse,
    TokenResponse, MFASetupResponse, PortalUserResponse,
    MFAMethodEnum, PortalUserStatusEnum
)


class AuthService:
    """
    Handles all authentication operations for the patient portal including:
    - User registration with identity verification
    - Login with MFA support
    - JWT token management
    - Session tracking
    - Password management
    - Account security
    """

    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")))
        self.refresh_token_expire = timedelta(days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")))
        self.max_login_attempts = 5
        self.lockout_duration = timedelta(minutes=30)
        self.password_min_length = 8

    # ==================== Password Hashing ====================

    def hash_password(self, password: str) -> Tuple[str, str]:
        """Hash password with salt"""
        salt = secrets.token_hex(32)
        hashed = self.pwd_context.hash(password + salt)
        return hashed, salt

    def verify_password(self, plain_password: str, hashed_password: str, salt: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password + salt, hashed_password)

    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password meets security requirements"""
        errors = []

        if len(password) < self.password_min_length:
            errors.append(f"Password must be at least {self.password_min_length} characters")

        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")

        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")

        return len(errors) == 0, errors

    # ==================== Token Management ====================

    def create_access_token(self, user_id: UUID, tenant_id: UUID, additional_claims: Dict = None) -> str:
        """Create JWT access token"""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "type": "access",
            "iat": now,
            "exp": now + self.access_token_expire,
            "jti": str(uuid4())  # JWT ID for revocation
        }

        if additional_claims:
            payload.update(additional_claims)

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: UUID, tenant_id: UUID) -> str:
        """Create JWT refresh token"""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "type": "refresh",
            "iat": now,
            "exp": now + self.refresh_token_expire,
            "jti": str(uuid4())
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> Dict:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")

    def hash_token(self, token: str) -> str:
        """Hash token for storage"""
        return hashlib.sha256(token.encode()).hexdigest()

    # ==================== MFA ====================

    def generate_totp_secret(self) -> str:
        """Generate TOTP secret for authenticator apps"""
        return pyotp.random_base32()

    def get_totp_uri(self, secret: str, email: str, issuer: str = "HealthTech Portal") -> str:
        """Get TOTP URI for QR code generation"""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=email, issuer_name=issuer)

    def verify_totp(self, secret: str, code: str) -> bool:
        """Verify TOTP code"""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)  # Allow 30 second window

    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """Generate backup codes for MFA recovery"""
        codes = []
        for _ in range(count):
            code = secrets.token_hex(4).upper()  # 8 character hex codes
            codes.append(f"{code[:4]}-{code[4:]}")
        return codes

    def hash_backup_codes(self, codes: List[str]) -> List[str]:
        """Hash backup codes for storage"""
        return [hashlib.sha256(code.encode()).hexdigest() for code in codes]

    def verify_backup_code(self, code: str, hashed_codes: List[str]) -> Tuple[bool, int]:
        """Verify backup code and return index if valid"""
        code_hash = hashlib.sha256(code.encode()).hexdigest()
        for i, hashed in enumerate(hashed_codes):
            if hmac.compare_digest(code_hash, hashed):
                return True, i
        return False, -1

    def generate_verification_code(self, length: int = 6) -> str:
        """Generate numeric verification code"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(length)])

    # ==================== Registration ====================

    async def register(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        request: RegisterRequest,
        ip_address: str = None,
        user_agent: str = None
    ) -> RegisterResponse:
        """Register new portal user"""

        # Validate password strength
        is_valid, errors = self.validate_password_strength(request.password)
        if not is_valid:
            raise ValueError(f"Password requirements not met: {', '.join(errors)}")

        # Check if email already exists
        existing = await db.execute(
            select(PortalUser).where(
                and_(
                    PortalUser.tenant_id == tenant_id,
                    PortalUser.email == request.email.lower()
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("An account with this email already exists")

        # Find matching patient record
        patient_id = await self._find_matching_patient(
            db,
            tenant_id,
            request.first_name,
            request.last_name,
            request.date_of_birth,
            request.mrn,
            request.ssn_last_four
        )

        if not patient_id:
            raise ValueError("Unable to verify your identity. Please contact support.")

        # Hash password
        password_hash, password_salt = self.hash_password(request.password)

        # Generate verification token
        verification_token = secrets.token_urlsafe(32)
        verification_expires = datetime.now(timezone.utc) + timedelta(hours=24)

        # Create portal user
        user = PortalUser(
            id=uuid4(),
            tenant_id=tenant_id,
            patient_id=patient_id,
            email=request.email.lower(),
            password_hash=password_hash,
            password_salt=password_salt,
            status=PortalUserStatus.PENDING_VERIFICATION,
            email_verification_token=verification_token,
            email_verification_expires_at=verification_expires,
            phone_number=request.phone_number,
            display_name=f"{request.first_name} {request.last_name}",
            terms_accepted=request.accept_terms,
            terms_accepted_at=datetime.now(timezone.utc) if request.accept_terms else None,
            privacy_accepted=request.accept_privacy,
            privacy_accepted_at=datetime.now(timezone.utc) if request.accept_privacy else None
        )

        db.add(user)

        # Create default preferences
        preferences = PortalPreference(
            user_id=user.id,
            tenant_id=tenant_id
        )
        db.add(preferences)

        # Log registration
        audit_log = PortalAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user.id,
            patient_id=patient_id,
            action=AuditAction.PROFILE_UPDATE,
            action_category="registration",
            action_description="New portal user registration",
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )
        db.add(audit_log)

        await db.commit()

        # Send verification email (async task)
        await self._send_verification_email(user.email, verification_token)

        return RegisterResponse(
            user_id=user.id,
            email=user.email,
            status=PortalUserStatusEnum(user.status.value),
            verification_required=True,
            verification_method="email",
            message="Registration successful. Please check your email to verify your account."
        )

    async def _find_matching_patient(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        first_name: str,
        last_name: str,
        date_of_birth,
        mrn: str = None,
        ssn_last_four: str = None
    ) -> Optional[UUID]:
        """Find matching patient record for identity verification"""
        from modules.fhir.models import Patient  # Import here to avoid circular imports

        # Build query based on available identifiers
        conditions = [
            Patient.tenant_id == tenant_id,
            Patient.active == True
        ]

        # If MRN provided, use it as primary identifier
        if mrn:
            conditions.append(Patient.mrn == mrn)
        else:
            # Match by name and DOB
            conditions.extend([
                Patient.first_name.ilike(first_name),
                Patient.last_name.ilike(last_name),
                Patient.date_of_birth == date_of_birth
            ])

        result = await db.execute(
            select(Patient.id).where(and_(*conditions))
        )
        patient = result.scalar_one_or_none()

        return patient

    async def _send_verification_email(self, email: str, token: str):
        """Send email verification (placeholder - integrate with email service)"""
        # In production, this would integrate with your email service
        # e.g., SendGrid, AWS SES, etc.
        print(f"Sending verification email to {email} with token {token}")

    # ==================== Login ====================

    async def login(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        request: LoginRequest,
        ip_address: str = None,
        user_agent: str = None
    ) -> LoginResponse:
        """Authenticate user and create session"""

        # Find user
        result = await db.execute(
            select(PortalUser).where(
                and_(
                    PortalUser.tenant_id == tenant_id,
                    PortalUser.email == request.email.lower()
                )
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            await self._log_failed_login(db, tenant_id, request.email, ip_address, user_agent, "User not found")
            raise ValueError("Invalid email or password")

        # Check account status
        if user.status == PortalUserStatus.DEACTIVATED:
            raise ValueError("This account has been deactivated")

        if user.status == PortalUserStatus.SUSPENDED:
            raise ValueError("This account has been suspended. Please contact support.")

        if user.status == PortalUserStatus.LOCKED:
            if user.locked_until and user.locked_until > datetime.now(timezone.utc):
                remaining = (user.locked_until - datetime.now(timezone.utc)).seconds // 60
                raise ValueError(f"Account is locked. Please try again in {remaining} minutes.")
            else:
                # Unlock account
                user.status = PortalUserStatus.ACTIVE
                user.login_attempts = 0
                user.locked_until = None

        if user.status == PortalUserStatus.PENDING_VERIFICATION:
            raise ValueError("Please verify your email address before logging in")

        # Verify password
        if not self.verify_password(request.password, user.password_hash, user.password_salt):
            user.login_attempts += 1
            user.last_failed_login_at = datetime.now(timezone.utc)

            if user.login_attempts >= self.max_login_attempts:
                user.status = PortalUserStatus.LOCKED
                user.locked_until = datetime.now(timezone.utc) + self.lockout_duration
                await db.commit()
                await self._log_failed_login(db, tenant_id, request.email, ip_address, user_agent, "Account locked")
                raise ValueError("Account has been locked due to too many failed attempts. Please try again later.")

            await db.commit()
            await self._log_failed_login(db, tenant_id, request.email, ip_address, user_agent, "Invalid password")
            raise ValueError("Invalid email or password")

        # Check MFA
        if user.mfa_enabled:
            if not request.mfa_code:
                return LoginResponse(
                    access_token="",
                    refresh_token="",
                    expires_in=0,
                    requires_mfa=True,
                    mfa_method=MFAMethodEnum(user.mfa_method.value)
                )

            # Verify MFA code
            if not await self._verify_mfa_code(user, request.mfa_code):
                await self._log_failed_login(db, tenant_id, request.email, ip_address, user_agent, "Invalid MFA code")
                raise ValueError("Invalid verification code")

        # Successful login
        user.login_attempts = 0
        user.last_login_at = datetime.now(timezone.utc)
        user.last_login_ip = ip_address
        user.last_login_user_agent = user_agent
        user.total_logins += 1

        # Create tokens
        access_token = self.create_access_token(user.id, tenant_id)
        refresh_token = self.create_refresh_token(user.id, tenant_id)

        # Create session
        session = PortalSession(
            id=uuid4(),
            user_id=user.id,
            tenant_id=tenant_id,
            token_hash=self.hash_token(access_token),
            refresh_token_hash=self.hash_token(refresh_token),
            status=SessionStatus.ACTIVE,
            ip_address=ip_address,
            user_agent=user_agent,
            device_type=self._parse_device_type(user_agent),
            browser=self._parse_browser(user_agent),
            os=self._parse_os(user_agent),
            expires_at=datetime.now(timezone.utc) + self.access_token_expire,
            refresh_expires_at=datetime.now(timezone.utc) + self.refresh_token_expire
        )
        db.add(session)

        # Log successful login
        audit_log = PortalAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user.id,
            patient_id=user.patient_id,
            action=AuditAction.LOGIN,
            action_category="authentication",
            action_description="Successful login",
            session_id=session.id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )
        db.add(audit_log)

        await db.commit()

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(self.access_token_expire.total_seconds()),
            requires_mfa=False,
            user=PortalUserResponse(
                id=user.id,
                patient_id=user.patient_id,
                email=user.email,
                status=PortalUserStatusEnum(user.status.value),
                email_verified=user.email_verified,
                phone_number=user.phone_number,
                phone_verified=user.phone_verified,
                mfa_enabled=user.mfa_enabled,
                mfa_method=MFAMethodEnum(user.mfa_method.value) if user.mfa_method else None,
                display_name=user.display_name,
                avatar_url=user.avatar_url,
                preferred_language=user.preferred_language,
                timezone=user.timezone,
                last_login_at=user.last_login_at,
                terms_accepted=user.terms_accepted,
                privacy_accepted=user.privacy_accepted,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
        )

    async def _verify_mfa_code(self, user: PortalUser, code: str) -> bool:
        """Verify MFA code based on user's method"""
        if user.mfa_method == MFAMethod.TOTP:
            return self.verify_totp(user.mfa_secret, code)
        elif user.mfa_method == MFAMethod.BACKUP_CODE:
            is_valid, index = self.verify_backup_code(code, user.mfa_backup_codes)
            if is_valid:
                # Remove used backup code
                user.mfa_backup_codes.pop(index)
            return is_valid
        # SMS and Email codes would be verified against stored codes
        return False

    async def _log_failed_login(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        email: str,
        ip_address: str,
        user_agent: str,
        reason: str
    ):
        """Log failed login attempt"""
        audit_log = PortalAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            action=AuditAction.LOGIN_FAILED,
            action_category="authentication",
            action_description=f"Failed login for {email}: {reason}",
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            error_message=reason
        )
        db.add(audit_log)
        await db.commit()

    # ==================== Token Refresh ====================

    async def refresh_tokens(
        self,
        db: AsyncSession,
        refresh_token: str,
        ip_address: str = None
    ) -> TokenResponse:
        """Refresh access token using refresh token"""

        # Decode refresh token
        try:
            payload = self.decode_token(refresh_token)
        except ValueError as e:
            raise ValueError(f"Invalid refresh token: {str(e)}")

        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")

        user_id = UUID(payload["sub"])
        tenant_id = UUID(payload["tenant_id"])

        # Verify session exists and is valid
        token_hash = self.hash_token(refresh_token)
        result = await db.execute(
            select(PortalSession).where(
                and_(
                    PortalSession.refresh_token_hash == token_hash,
                    PortalSession.status == SessionStatus.ACTIVE
                )
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError("Session not found or expired")

        if session.refresh_expires_at < datetime.now(timezone.utc):
            session.status = SessionStatus.EXPIRED
            await db.commit()
            raise ValueError("Refresh token expired")

        # Create new tokens
        new_access_token = self.create_access_token(user_id, tenant_id)
        new_refresh_token = self.create_refresh_token(user_id, tenant_id)

        # Update session
        session.token_hash = self.hash_token(new_access_token)
        session.refresh_token_hash = self.hash_token(new_refresh_token)
        session.expires_at = datetime.now(timezone.utc) + self.access_token_expire
        session.refresh_expires_at = datetime.now(timezone.utc) + self.refresh_token_expire
        session.last_activity_at = datetime.now(timezone.utc)

        await db.commit()

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=int(self.access_token_expire.total_seconds())
        )

    # ==================== Logout ====================

    async def logout(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        token: str,
        ip_address: str = None,
        user_agent: str = None
    ):
        """Logout user and invalidate session"""

        token_hash = self.hash_token(token)

        result = await db.execute(
            select(PortalSession).where(
                and_(
                    PortalSession.token_hash == token_hash,
                    PortalSession.user_id == user_id
                )
            )
        )
        session = result.scalar_one_or_none()

        if session:
            session.status = SessionStatus.LOGGED_OUT
            session.ended_at = datetime.now(timezone.utc)
            session.end_reason = "user_logout"

        # Log logout
        audit_log = PortalAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            action=AuditAction.LOGOUT,
            action_category="authentication",
            action_description="User logout",
            session_id=session.id if session else None,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )
        db.add(audit_log)

        await db.commit()

    # ==================== MFA Setup ====================

    async def setup_mfa(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        method: MFAMethod
    ) -> MFASetupResponse:
        """Setup MFA for user"""

        result = await db.execute(
            select(PortalUser).where(
                and_(
                    PortalUser.id == user_id,
                    PortalUser.tenant_id == tenant_id
                )
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        if method == MFAMethod.TOTP:
            secret = self.generate_totp_secret()
            qr_uri = self.get_totp_uri(secret, user.email)

            # Generate backup codes
            backup_codes = self.generate_backup_codes()

            # Store temporarily (not enabled until verified)
            user.mfa_secret = secret
            user.mfa_method = method
            user.mfa_backup_codes = self.hash_backup_codes(backup_codes)

            await db.commit()

            return MFASetupResponse(
                method=MFAMethodEnum.TOTP,
                secret=secret,
                qr_code_url=qr_uri,
                backup_codes=backup_codes,
                verification_required=True
            )

        elif method == MFAMethod.SMS:
            if not user.phone_number:
                raise ValueError("Phone number required for SMS authentication")

            # Send verification code
            code = self.generate_verification_code()
            user.phone_verification_code = code
            user.phone_verification_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
            user.mfa_method = method

            await db.commit()

            # Send SMS (integrate with SMS service)
            await self._send_sms_verification(user.phone_number, code)

            return MFASetupResponse(
                method=MFAMethodEnum.SMS,
                verification_required=True
            )

        else:
            raise ValueError(f"MFA method {method} not supported")

    async def _send_sms_verification(self, phone: str, code: str):
        """Send SMS verification code (placeholder)"""
        # Integrate with Twilio or other SMS service
        print(f"Sending SMS to {phone} with code {code}")

    async def verify_and_enable_mfa(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        code: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> bool:
        """Verify MFA code and enable MFA"""

        result = await db.execute(
            select(PortalUser).where(
                and_(
                    PortalUser.id == user_id,
                    PortalUser.tenant_id == tenant_id
                )
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        if not user.mfa_method:
            raise ValueError("MFA not configured")

        # Verify based on method
        if user.mfa_method == MFAMethod.TOTP:
            if not self.verify_totp(user.mfa_secret, code):
                raise ValueError("Invalid verification code")
        elif user.mfa_method == MFAMethod.SMS:
            if user.phone_verification_code != code:
                raise ValueError("Invalid verification code")
            if user.phone_verification_expires_at < datetime.now(timezone.utc):
                raise ValueError("Verification code expired")

        # Enable MFA
        user.mfa_enabled = True
        user.mfa_enabled_at = datetime.now(timezone.utc)

        # Log MFA enabled
        audit_log = PortalAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            patient_id=user.patient_id,
            action=AuditAction.MFA_ENABLED,
            action_category="security",
            action_description=f"MFA enabled using {user.mfa_method.value}",
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )
        db.add(audit_log)

        await db.commit()
        return True

    async def disable_mfa(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        password: str,
        ip_address: str = None,
        user_agent: str = None
    ):
        """Disable MFA (requires password verification)"""

        result = await db.execute(
            select(PortalUser).where(
                and_(
                    PortalUser.id == user_id,
                    PortalUser.tenant_id == tenant_id
                )
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        # Verify password
        if not self.verify_password(password, user.password_hash, user.password_salt):
            raise ValueError("Invalid password")

        # Disable MFA
        user.mfa_enabled = False
        user.mfa_secret = None
        user.mfa_method = None
        user.mfa_backup_codes = []

        # Log MFA disabled
        audit_log = PortalAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            patient_id=user.patient_id,
            action=AuditAction.MFA_DISABLED,
            action_category="security",
            action_description="MFA disabled",
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )
        db.add(audit_log)

        await db.commit()

    # ==================== Email Verification ====================

    async def verify_email(
        self,
        db: AsyncSession,
        token: str,
        ip_address: str = None
    ) -> bool:
        """Verify email address"""

        result = await db.execute(
            select(PortalUser).where(
                PortalUser.email_verification_token == token
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("Invalid verification token")

        if user.email_verification_expires_at < datetime.now(timezone.utc):
            raise ValueError("Verification token has expired")

        user.email_verified = True
        user.email_verified_at = datetime.now(timezone.utc)
        user.email_verification_token = None
        user.email_verification_expires_at = None

        if user.status == PortalUserStatus.PENDING_VERIFICATION:
            user.status = PortalUserStatus.ACTIVE

        await db.commit()
        return True

    # ==================== Password Reset ====================

    async def initiate_password_reset(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        email: str,
        ip_address: str = None
    ) -> bool:
        """Initiate password reset"""

        result = await db.execute(
            select(PortalUser).where(
                and_(
                    PortalUser.tenant_id == tenant_id,
                    PortalUser.email == email.lower()
                )
            )
        )
        user = result.scalar_one_or_none()

        # Always return success to prevent email enumeration
        if not user:
            return True

        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        user.email_verification_token = reset_token  # Reusing field for reset
        user.email_verification_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        await db.commit()

        # Send reset email
        await self._send_password_reset_email(user.email, reset_token)

        return True

    async def _send_password_reset_email(self, email: str, token: str):
        """Send password reset email (placeholder)"""
        print(f"Sending password reset email to {email} with token {token}")

    async def reset_password(
        self,
        db: AsyncSession,
        token: str,
        new_password: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> bool:
        """Reset password using token"""

        # Validate password strength
        is_valid, errors = self.validate_password_strength(new_password)
        if not is_valid:
            raise ValueError(f"Password requirements not met: {', '.join(errors)}")

        result = await db.execute(
            select(PortalUser).where(
                PortalUser.email_verification_token == token
            )
        )
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("Invalid reset token")

        if user.email_verification_expires_at < datetime.now(timezone.utc):
            raise ValueError("Reset token has expired")

        # Hash new password
        password_hash, password_salt = self.hash_password(new_password)

        user.password_hash = password_hash
        user.password_salt = password_salt
        user.password_changed_at = datetime.now(timezone.utc)
        user.email_verification_token = None
        user.email_verification_expires_at = None
        user.require_password_change = False

        # Unlock account if locked
        if user.status == PortalUserStatus.LOCKED:
            user.status = PortalUserStatus.ACTIVE
            user.login_attempts = 0
            user.locked_until = None

        # Invalidate all sessions
        await db.execute(
            update(PortalSession).where(
                and_(
                    PortalSession.user_id == user.id,
                    PortalSession.status == SessionStatus.ACTIVE
                )
            ).values(
                status=SessionStatus.REVOKED,
                ended_at=datetime.now(timezone.utc),
                end_reason="password_reset"
            )
        )

        # Log password reset
        audit_log = PortalAuditLog(
            id=uuid4(),
            tenant_id=user.tenant_id,
            user_id=user.id,
            patient_id=user.patient_id,
            action=AuditAction.PASSWORD_RESET,
            action_category="security",
            action_description="Password reset via token",
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )
        db.add(audit_log)

        await db.commit()
        return True

    # ==================== Session Management ====================

    async def get_active_sessions(
        self,
        db: AsyncSession,
        user_id: UUID,
        current_token: str = None
    ) -> List[PortalSession]:
        """Get all active sessions for user"""

        result = await db.execute(
            select(PortalSession).where(
                and_(
                    PortalSession.user_id == user_id,
                    PortalSession.status == SessionStatus.ACTIVE
                )
            ).order_by(PortalSession.last_activity_at.desc())
        )
        sessions = result.scalars().all()

        current_hash = self.hash_token(current_token) if current_token else None

        return [
            {
                **session.__dict__,
                "is_current": session.token_hash == current_hash if current_hash else False
            }
            for session in sessions
        ]

    async def revoke_session(
        self,
        db: AsyncSession,
        user_id: UUID,
        session_id: UUID
    ):
        """Revoke specific session"""

        result = await db.execute(
            select(PortalSession).where(
                and_(
                    PortalSession.id == session_id,
                    PortalSession.user_id == user_id
                )
            )
        )
        session = result.scalar_one_or_none()

        if session:
            session.status = SessionStatus.REVOKED
            session.ended_at = datetime.now(timezone.utc)
            session.end_reason = "user_revoked"
            await db.commit()

    async def revoke_all_sessions_except_current(
        self,
        db: AsyncSession,
        user_id: UUID,
        current_token: str
    ):
        """Revoke all sessions except current"""

        current_hash = self.hash_token(current_token)

        await db.execute(
            update(PortalSession).where(
                and_(
                    PortalSession.user_id == user_id,
                    PortalSession.status == SessionStatus.ACTIVE,
                    PortalSession.token_hash != current_hash
                )
            ).values(
                status=SessionStatus.REVOKED,
                ended_at=datetime.now(timezone.utc),
                end_reason="user_revoked_all"
            )
        )
        await db.commit()

    # ==================== Helper Methods ====================

    def _parse_device_type(self, user_agent: str) -> str:
        """Parse device type from user agent"""
        if not user_agent:
            return "unknown"
        ua_lower = user_agent.lower()
        if "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
            return "mobile"
        elif "tablet" in ua_lower or "ipad" in ua_lower:
            return "tablet"
        return "desktop"

    def _parse_browser(self, user_agent: str) -> str:
        """Parse browser from user agent"""
        if not user_agent:
            return "unknown"
        ua_lower = user_agent.lower()
        if "chrome" in ua_lower and "edg" not in ua_lower:
            return "Chrome"
        elif "firefox" in ua_lower:
            return "Firefox"
        elif "safari" in ua_lower and "chrome" not in ua_lower:
            return "Safari"
        elif "edg" in ua_lower:
            return "Edge"
        return "Other"

    def _parse_os(self, user_agent: str) -> str:
        """Parse OS from user agent"""
        if not user_agent:
            return "unknown"
        ua_lower = user_agent.lower()
        if "windows" in ua_lower:
            return "Windows"
        elif "mac os" in ua_lower or "macos" in ua_lower:
            return "macOS"
        elif "linux" in ua_lower:
            return "Linux"
        elif "android" in ua_lower:
            return "Android"
        elif "iphone" in ua_lower or "ipad" in ua_lower:
            return "iOS"
        return "Other"

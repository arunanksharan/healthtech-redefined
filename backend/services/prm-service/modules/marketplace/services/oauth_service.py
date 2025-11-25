"""
OAuth Service
EPIC-018: OAuth 2.0 Authorization Server with SMART on FHIR support
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
import secrets
import hashlib
import base64
import jwt
import re

from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from modules.marketplace.models import (
    OAuthApplication, OAuthToken, OAuthConsent, APIKey,
    DeveloperOrganization, DeveloperAuditLog,
    AppType, AppStatus, TokenType, GrantType, APIKeyStatus
)
from modules.marketplace.schemas import (
    OAuthAppCreate, OAuthAppUpdate, OAuthAppResponse, OAuthAppWithSecret,
    OAuthAppListResponse, ClientSecretRotateResponse,
    APIKeyCreate, APIKeyResponse, APIKeyWithSecret, APIKeyListResponse,
    AuthorizationRequest, AuthorizationResponse,
    TokenRequest, TokenResponse, TokenIntrospectionResponse,
    ConsentGrant, ConsentResponse, ConsentListResponse,
    SMARTConfiguration, SMARTLaunchContext
)


class OAuthService:
    """
    OAuth 2.0 Authorization Server with SMART on FHIR support.

    Handles:
    - OAuth application registration
    - Authorization code flow
    - Client credentials flow
    - Token management
    - SMART on FHIR launch contexts
    - Consent management
    """

    def __init__(self):
        # In production, these would be loaded from config
        self.issuer = "https://api.prm.healthcare"
        self.jwt_algorithm = "RS256"
        self.jwt_secret = "your-secret-key"  # Would use RSA keys in production
        self.authorization_code_ttl = 600  # 10 minutes
        self.default_access_token_ttl = 3600  # 1 hour
        self.default_refresh_token_ttl = 2592000  # 30 days

    # ========================================================================
    # FHIR Scopes Definition
    # ========================================================================

    FHIR_SCOPES = {
        # Patient-level access
        "patient/Patient.read": "Read patient demographics",
        "patient/Patient.write": "Update patient demographics",
        "patient/Observation.read": "Read patient observations",
        "patient/Observation.write": "Create observations",
        "patient/Condition.read": "Read patient conditions",
        "patient/Condition.write": "Create/update conditions",
        "patient/MedicationRequest.read": "Read medications",
        "patient/MedicationRequest.write": "Prescribe medications",
        "patient/Appointment.read": "Read appointments",
        "patient/Appointment.write": "Manage appointments",
        "patient/Encounter.read": "Read encounters",
        "patient/DiagnosticReport.read": "Read diagnostic reports",
        "patient/DocumentReference.read": "Read documents",

        # User-level access (provider context)
        "user/Patient.read": "Read any patient as provider",
        "user/Patient.write": "Update any patient",
        "user/Encounter.read": "Read any encounter",
        "user/Encounter.write": "Create encounters",

        # System-level access (backend services)
        "system/Patient.read": "Bulk patient access",
        "system/*.read": "Full read access",
        "system/*.write": "Full write access",

        # PRM-specific scopes
        "prm/ai.triage": "Access AI triage agent",
        "prm/ai.scribe": "Access ambient scribe",
        "prm/analytics.read": "Read analytics data",
        "prm/messaging.send": "Send patient messages",
        "prm/appointments.manage": "Full appointment management",
        "prm/billing.read": "Read billing data",
        "prm/billing.write": "Create charges",

        # OpenID Connect
        "openid": "OpenID Connect authentication",
        "profile": "User profile information",
        "email": "User email address",
        "fhirUser": "FHIR user resource",
        "launch": "SMART launch context",
        "launch/patient": "Patient launch context",
        "launch/encounter": "Encounter launch context",
        "offline_access": "Refresh token access",
    }

    # ========================================================================
    # Application Management
    # ========================================================================

    async def create_application(
        self,
        db: AsyncSession,
        organization_id: UUID,
        data: OAuthAppCreate,
        user_id: UUID
    ) -> OAuthAppWithSecret:
        """Create a new OAuth application."""
        # Generate slug
        slug = self._generate_slug(data.name)
        existing = await db.execute(
            select(OAuthApplication).where(OAuthApplication.slug == slug)
        )
        if existing.scalar_one_or_none():
            slug = f"{slug}-{secrets.token_hex(3)}"

        # Generate credentials
        client_id = f"prm_{secrets.token_urlsafe(24)}"
        client_secret = secrets.token_urlsafe(48)
        secret_hash = hashlib.sha256(client_secret.encode()).hexdigest()

        # Determine grant types based on app type
        grant_types = ["authorization_code", "refresh_token"]
        if data.app_type == AppTypeSchema.BACKEND:
            grant_types.append("client_credentials")

        app = OAuthApplication(
            organization_id=organization_id,
            name=data.name,
            slug=slug,
            description=data.description,
            app_type=AppType(data.app_type.value),
            status=AppStatus.DRAFT,
            client_id=client_id,
            client_secret_hash=secret_hash,
            client_secret_prefix=client_secret[:8],
            redirect_uris=data.redirect_uris,
            allowed_grant_types=grant_types,
            allowed_scopes=data.allowed_scopes,
            is_smart_on_fhir=data.is_smart_on_fhir,
            launch_uri=data.launch_uri,
            homepage_url=data.homepage_url,
            privacy_policy_url=data.privacy_policy_url,
            terms_of_service_url=data.terms_of_service_url,
            support_url=data.support_url,
            logo_url=data.logo_url,
            require_pkce=data.app_type in [AppTypeSchema.SPA, AppTypeSchema.NATIVE]
        )

        db.add(app)

        # Log audit
        audit_log = DeveloperAuditLog(
            organization_id=organization_id,
            user_id=user_id,
            application_id=app.id,
            action="application.created",
            entity_type="application",
            entity_id=app.id,
            details={"name": data.name, "app_type": data.app_type.value}
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(app)

        response = OAuthAppWithSecret(
            **self._to_app_response(app).model_dump(),
            client_secret=client_secret
        )

        return response

    async def get_application(
        self,
        db: AsyncSession,
        application_id: UUID,
        organization_id: UUID
    ) -> OAuthAppResponse:
        """Get application by ID."""
        app = await self._get_application(db, application_id, organization_id)
        return self._to_app_response(app)

    async def get_application_by_client_id(
        self,
        db: AsyncSession,
        client_id: str
    ) -> OAuthAppResponse:
        """Get application by client ID."""
        query = select(OAuthApplication).where(
            OAuthApplication.client_id == client_id
        )
        result = await db.execute(query)
        app = result.scalar_one_or_none()

        if not app:
            raise ValueError("Application not found")

        return self._to_app_response(app)

    async def update_application(
        self,
        db: AsyncSession,
        application_id: UUID,
        organization_id: UUID,
        data: OAuthAppUpdate,
        user_id: UUID
    ) -> OAuthAppResponse:
        """Update application."""
        app = await self._get_application(db, application_id, organization_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(app, field):
                setattr(app, field, value)

        # Log audit
        audit_log = DeveloperAuditLog(
            organization_id=organization_id,
            user_id=user_id,
            application_id=application_id,
            action="application.updated",
            entity_type="application",
            entity_id=application_id,
            details={"updated_fields": list(update_data.keys())}
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(app)

        return self._to_app_response(app)

    async def rotate_client_secret(
        self,
        db: AsyncSession,
        application_id: UUID,
        organization_id: UUID,
        user_id: UUID
    ) -> ClientSecretRotateResponse:
        """Rotate client secret."""
        app = await self._get_application(db, application_id, organization_id)

        # Generate new secret
        client_secret = secrets.token_urlsafe(48)
        secret_hash = hashlib.sha256(client_secret.encode()).hexdigest()

        app.client_secret_hash = secret_hash
        app.client_secret_prefix = client_secret[:8]

        # Log audit
        audit_log = DeveloperAuditLog(
            organization_id=organization_id,
            user_id=user_id,
            application_id=application_id,
            action="application.secret_rotated",
            entity_type="application",
            entity_id=application_id,
            details={}
        )
        db.add(audit_log)

        await db.commit()

        return ClientSecretRotateResponse(
            client_id=app.client_id,
            client_secret=client_secret,
            client_secret_prefix=client_secret[:8],
            rotated_at=datetime.utcnow()
        )

    async def list_applications(
        self,
        db: AsyncSession,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 50
    ) -> OAuthAppListResponse:
        """List applications for organization."""
        # Count total
        count_query = select(func.count(OAuthApplication.id)).where(
            OAuthApplication.organization_id == organization_id
        )
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Get applications
        query = select(OAuthApplication).where(
            OAuthApplication.organization_id == organization_id
        ).order_by(OAuthApplication.created_at.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        applications = result.scalars().all()

        return OAuthAppListResponse(
            items=[self._to_app_response(app) for app in applications],
            total=total
        )

    # ========================================================================
    # API Key Management
    # ========================================================================

    async def create_api_key(
        self,
        db: AsyncSession,
        application_id: UUID,
        organization_id: UUID,
        data: APIKeyCreate,
        user_id: UUID
    ) -> APIKeyWithSecret:
        """Create a new API key."""
        app = await self._get_application(db, application_id, organization_id)

        # Generate key
        prefix = "prm_test_" if data.is_test_key else "prm_live_"
        key_value = f"{prefix}{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(key_value.encode()).hexdigest()

        api_key = APIKey(
            application_id=application_id,
            name=data.name,
            key_prefix=key_value[:12],
            key_hash=key_hash,
            status=APIKeyStatus.ACTIVE,
            scopes=data.scopes,
            is_test_key=data.is_test_key,
            rate_limit_per_minute=data.rate_limit_per_minute,
            rate_limit_per_day=data.rate_limit_per_day,
            monthly_quota=data.monthly_quota,
            ip_allowlist=data.ip_allowlist,
            expires_at=data.expires_at,
            created_by=user_id
        )

        db.add(api_key)

        # Log audit
        audit_log = DeveloperAuditLog(
            organization_id=organization_id,
            user_id=user_id,
            application_id=application_id,
            action="api_key.created",
            entity_type="api_key",
            entity_id=api_key.id,
            details={"name": data.name, "is_test": data.is_test_key}
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(api_key)

        return APIKeyWithSecret(
            **self._to_api_key_response(api_key).model_dump(),
            key=key_value
        )

    async def revoke_api_key(
        self,
        db: AsyncSession,
        api_key_id: UUID,
        application_id: UUID,
        organization_id: UUID,
        user_id: UUID
    ) -> None:
        """Revoke an API key."""
        # Verify application ownership
        await self._get_application(db, application_id, organization_id)

        query = select(APIKey).where(
            and_(
                APIKey.id == api_key_id,
                APIKey.application_id == application_id
            )
        )
        result = await db.execute(query)
        api_key = result.scalar_one_or_none()

        if not api_key:
            raise ValueError("API key not found")

        api_key.status = APIKeyStatus.REVOKED
        api_key.revoked_at = datetime.utcnow()

        # Log audit
        audit_log = DeveloperAuditLog(
            organization_id=organization_id,
            user_id=user_id,
            application_id=application_id,
            action="api_key.revoked",
            entity_type="api_key",
            entity_id=api_key_id,
            details={"name": api_key.name}
        )
        db.add(audit_log)

        await db.commit()

    async def list_api_keys(
        self,
        db: AsyncSession,
        application_id: UUID,
        organization_id: UUID
    ) -> APIKeyListResponse:
        """List API keys for application."""
        await self._get_application(db, application_id, organization_id)

        query = select(APIKey).where(
            APIKey.application_id == application_id
        ).order_by(APIKey.created_at.desc())

        result = await db.execute(query)
        keys = result.scalars().all()

        return APIKeyListResponse(
            items=[self._to_api_key_response(k) for k in keys],
            total=len(keys)
        )

    async def validate_api_key(
        self,
        db: AsyncSession,
        api_key: str
    ) -> Optional[Dict[str, Any]]:
        """Validate an API key and return associated data."""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        query = select(APIKey).where(
            and_(
                APIKey.key_hash == key_hash,
                APIKey.status == APIKeyStatus.ACTIVE
            )
        )
        result = await db.execute(query)
        key = result.scalar_one_or_none()

        if not key:
            return None

        # Check expiration
        if key.expires_at and key.expires_at < datetime.utcnow():
            return None

        # Update last used
        key.last_used_at = datetime.utcnow()
        key.total_requests += 1
        await db.commit()

        return {
            "api_key_id": key.id,
            "application_id": key.application_id,
            "scopes": key.scopes,
            "is_test_key": key.is_test_key,
            "rate_limit_per_minute": key.rate_limit_per_minute,
            "rate_limit_per_day": key.rate_limit_per_day
        }

    # ========================================================================
    # OAuth Authorization Flow
    # ========================================================================

    async def create_authorization_code(
        self,
        db: AsyncSession,
        request: AuthorizationRequest,
        tenant_id: UUID,
        user_id: UUID,
        patient_id: Optional[UUID] = None
    ) -> AuthorizationResponse:
        """Create authorization code for OAuth flow."""
        # Validate client
        app = await self._get_app_by_client_id(db, request.client_id)

        # Validate redirect URI
        if request.redirect_uri not in app.redirect_uris:
            raise ValueError("Invalid redirect URI")

        # Validate scopes
        requested_scopes = request.scope.split() if request.scope else []
        for scope in requested_scopes:
            if scope not in app.allowed_scopes and scope not in self.FHIR_SCOPES:
                raise ValueError(f"Invalid scope: {scope}")

        # PKCE validation for public clients
        if app.require_pkce and not request.code_challenge:
            raise ValueError("PKCE code_challenge required")

        # Generate authorization code
        code = secrets.token_urlsafe(32)
        code_hash = hashlib.sha256(code.encode()).hexdigest()

        # Build launch context for SMART
        launch_context = {}
        if patient_id:
            launch_context["patient"] = str(patient_id)
        if request.launch:
            # Decode EHR launch token and extract context
            launch_context["launch"] = request.launch

        token = OAuthToken(
            application_id=app.id,
            tenant_id=tenant_id,
            token_type=TokenType.AUTHORIZATION_CODE,
            token_hash=code_hash,
            token_prefix=code[:8],
            user_id=user_id,
            patient_id=patient_id,
            grant_type=GrantType.AUTHORIZATION_CODE,
            scopes=requested_scopes,
            launch_context=launch_context,
            expires_at=datetime.utcnow() + timedelta(seconds=self.authorization_code_ttl),
            code_challenge=request.code_challenge,
            code_challenge_method=request.code_challenge_method or "S256"
        )

        db.add(token)
        await db.commit()

        return AuthorizationResponse(
            code=code,
            state=request.state,
            redirect_uri=request.redirect_uri
        )

    async def exchange_authorization_code(
        self,
        db: AsyncSession,
        request: TokenRequest
    ) -> TokenResponse:
        """Exchange authorization code for tokens."""
        # Validate client
        app = await self._get_app_by_client_id(db, request.client_id)

        # Verify client secret for confidential clients
        if app.app_type not in [AppType.SPA, AppType.NATIVE]:
            if not request.client_secret:
                raise ValueError("Client secret required")
            secret_hash = hashlib.sha256(request.client_secret.encode()).hexdigest()
            if secret_hash != app.client_secret_hash:
                raise ValueError("Invalid client secret")

        # Find authorization code
        code_hash = hashlib.sha256(request.code.encode()).hexdigest()
        query = select(OAuthToken).where(
            and_(
                OAuthToken.token_hash == code_hash,
                OAuthToken.token_type == TokenType.AUTHORIZATION_CODE,
                OAuthToken.application_id == app.id,
                OAuthToken.is_revoked == False
            )
        )
        result = await db.execute(query)
        auth_code = result.scalar_one_or_none()

        if not auth_code:
            raise ValueError("Invalid authorization code")

        if auth_code.expires_at < datetime.utcnow():
            raise ValueError("Authorization code expired")

        # PKCE verification
        if auth_code.code_challenge:
            if not request.code_verifier:
                raise ValueError("Code verifier required")

            if auth_code.code_challenge_method == "S256":
                verifier_hash = base64.urlsafe_b64encode(
                    hashlib.sha256(request.code_verifier.encode()).digest()
                ).rstrip(b'=').decode()
            else:
                verifier_hash = request.code_verifier

            if verifier_hash != auth_code.code_challenge:
                raise ValueError("Invalid code verifier")

        # Revoke the authorization code
        auth_code.is_revoked = True
        auth_code.revoked_at = datetime.utcnow()

        # Generate access token
        access_token = await self._create_access_token(
            db, app, auth_code.tenant_id, auth_code.user_id,
            auth_code.scopes, auth_code.patient_id, auth_code.launch_context
        )

        # Generate refresh token if offline_access scope requested
        refresh_token = None
        if "offline_access" in auth_code.scopes:
            refresh_token = await self._create_refresh_token(
                db, app, auth_code.tenant_id, auth_code.user_id,
                auth_code.scopes, auth_code.patient_id, access_token.id
            )

        await db.commit()

        # Build response
        return TokenResponse(
            access_token=self._encode_jwt_token(access_token, app),
            token_type="Bearer",
            expires_in=app.access_token_ttl,
            refresh_token=self._encode_jwt_token(refresh_token, app) if refresh_token else None,
            scope=" ".join(auth_code.scopes),
            patient=auth_code.launch_context.get("patient"),
            encounter=auth_code.launch_context.get("encounter")
        )

    async def refresh_access_token(
        self,
        db: AsyncSession,
        request: TokenRequest
    ) -> TokenResponse:
        """Refresh an access token."""
        # Decode and validate refresh token
        try:
            payload = jwt.decode(
                request.refresh_token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm]
            )
        except jwt.InvalidTokenError:
            raise ValueError("Invalid refresh token")

        token_id = UUID(payload.get("jti"))

        # Find refresh token
        query = select(OAuthToken).where(
            and_(
                OAuthToken.id == token_id,
                OAuthToken.token_type == TokenType.REFRESH,
                OAuthToken.is_revoked == False
            )
        )
        result = await db.execute(query)
        refresh_token = result.scalar_one_or_none()

        if not refresh_token:
            raise ValueError("Invalid refresh token")

        if refresh_token.expires_at < datetime.utcnow():
            raise ValueError("Refresh token expired")

        # Get application
        app = await self._get_app_by_id(db, refresh_token.application_id)

        # Create new access token
        new_access = await self._create_access_token(
            db, app, refresh_token.tenant_id, refresh_token.user_id,
            refresh_token.scopes, refresh_token.patient_id, refresh_token.launch_context
        )

        # Rotate refresh token
        refresh_token.is_revoked = True
        new_refresh = await self._create_refresh_token(
            db, app, refresh_token.tenant_id, refresh_token.user_id,
            refresh_token.scopes, refresh_token.patient_id, new_access.id
        )

        await db.commit()

        return TokenResponse(
            access_token=self._encode_jwt_token(new_access, app),
            token_type="Bearer",
            expires_in=app.access_token_ttl,
            refresh_token=self._encode_jwt_token(new_refresh, app),
            scope=" ".join(refresh_token.scopes),
            patient=refresh_token.launch_context.get("patient")
        )

    async def client_credentials_grant(
        self,
        db: AsyncSession,
        request: TokenRequest
    ) -> TokenResponse:
        """Handle client credentials grant for M2M auth."""
        # Validate client
        app = await self._get_app_by_client_id(db, request.client_id)

        if "client_credentials" not in app.allowed_grant_types:
            raise ValueError("Client credentials grant not allowed")

        # Verify client secret
        if not request.client_secret:
            raise ValueError("Client secret required")
        secret_hash = hashlib.sha256(request.client_secret.encode()).hexdigest()
        if secret_hash != app.client_secret_hash:
            raise ValueError("Invalid client secret")

        # Validate scopes
        requested_scopes = request.scope.split() if request.scope else app.default_scopes
        for scope in requested_scopes:
            if scope not in app.allowed_scopes:
                raise ValueError(f"Invalid scope: {scope}")

        # Create access token (no user context)
        access_token = await self._create_access_token(
            db, app, app.organization_id, None, requested_scopes
        )

        await db.commit()

        return TokenResponse(
            access_token=self._encode_jwt_token(access_token, app),
            token_type="Bearer",
            expires_in=app.access_token_ttl,
            scope=" ".join(requested_scopes)
        )

    async def revoke_token(
        self,
        db: AsyncSession,
        token: str,
        client_id: str
    ) -> None:
        """Revoke a token."""
        try:
            payload = jwt.decode(
                token, self.jwt_secret, algorithms=[self.jwt_algorithm]
            )
            token_id = UUID(payload.get("jti"))
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")

        # Verify client owns the token
        query = select(OAuthToken).where(OAuthToken.id == token_id)
        result = await db.execute(query)
        db_token = result.scalar_one_or_none()

        if not db_token:
            return  # Token doesn't exist, consider it revoked

        app = await self._get_app_by_id(db, db_token.application_id)
        if app.client_id != client_id:
            raise ValueError("Token does not belong to client")

        db_token.is_revoked = True
        db_token.revoked_at = datetime.utcnow()
        await db.commit()

    async def introspect_token(
        self,
        db: AsyncSession,
        token: str
    ) -> TokenIntrospectionResponse:
        """Introspect a token."""
        try:
            payload = jwt.decode(
                token, self.jwt_secret, algorithms=[self.jwt_algorithm]
            )
        except jwt.ExpiredSignatureError:
            return TokenIntrospectionResponse(active=False)
        except jwt.InvalidTokenError:
            return TokenIntrospectionResponse(active=False)

        token_id = UUID(payload.get("jti"))

        # Check if revoked
        query = select(OAuthToken).where(OAuthToken.id == token_id)
        result = await db.execute(query)
        db_token = result.scalar_one_or_none()

        if not db_token or db_token.is_revoked:
            return TokenIntrospectionResponse(active=False)

        return TokenIntrospectionResponse(
            active=True,
            scope=" ".join(db_token.scopes),
            client_id=payload.get("client_id"),
            exp=payload.get("exp"),
            iat=payload.get("iat"),
            sub=payload.get("sub"),
            aud=payload.get("aud"),
            iss=payload.get("iss"),
            tenant_id=str(db_token.tenant_id),
            patient_id=str(db_token.patient_id) if db_token.patient_id else None
        )

    # ========================================================================
    # Consent Management
    # ========================================================================

    async def grant_consent(
        self,
        db: AsyncSession,
        application_id: UUID,
        tenant_id: UUID,
        user_id: UUID,
        data: ConsentGrant
    ) -> ConsentResponse:
        """Grant consent for application."""
        app = await self._get_app_by_id(db, application_id)

        # Check for existing consent
        existing_query = select(OAuthConsent).where(
            and_(
                OAuthConsent.application_id == application_id,
                OAuthConsent.tenant_id == tenant_id,
                OAuthConsent.user_id == user_id,
                OAuthConsent.patient_id == data.patient_id if data.patient_id else OAuthConsent.patient_id.is_(None)
            )
        )
        existing = await db.execute(existing_query)
        consent = existing.scalar_one_or_none()

        if consent:
            # Update existing consent
            consent.granted_scopes = list(set(consent.granted_scopes + data.scopes))
            consent.is_active = True
            consent.revoked_at = None
        else:
            # Create new consent
            consent = OAuthConsent(
                application_id=application_id,
                tenant_id=tenant_id,
                user_id=user_id,
                patient_id=data.patient_id,
                granted_scopes=data.scopes,
                is_active=True
            )
            db.add(consent)

        await db.commit()
        await db.refresh(consent)

        return ConsentResponse(
            id=consent.id,
            application_id=consent.application_id,
            application_name=app.name,
            tenant_id=consent.tenant_id,
            user_id=consent.user_id,
            patient_id=consent.patient_id,
            granted_scopes=consent.granted_scopes,
            is_active=consent.is_active,
            granted_at=consent.granted_at,
            expires_at=consent.expires_at
        )

    async def revoke_consent(
        self,
        db: AsyncSession,
        consent_id: UUID,
        user_id: UUID
    ) -> None:
        """Revoke consent."""
        query = select(OAuthConsent).where(
            and_(
                OAuthConsent.id == consent_id,
                OAuthConsent.user_id == user_id
            )
        )
        result = await db.execute(query)
        consent = result.scalar_one_or_none()

        if not consent:
            raise ValueError("Consent not found")

        consent.is_active = False
        consent.revoked_at = datetime.utcnow()

        # Revoke all tokens for this consent
        await db.execute(
            update(OAuthToken).where(
                and_(
                    OAuthToken.application_id == consent.application_id,
                    OAuthToken.tenant_id == consent.tenant_id,
                    OAuthToken.user_id == user_id
                )
            ).values(is_revoked=True, revoked_at=datetime.utcnow())
        )

        await db.commit()

    async def list_user_consents(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID
    ) -> ConsentListResponse:
        """List consents for a user."""
        query = select(OAuthConsent, OAuthApplication).join(
            OAuthApplication, OAuthConsent.application_id == OAuthApplication.id
        ).where(
            and_(
                OAuthConsent.tenant_id == tenant_id,
                OAuthConsent.user_id == user_id
            )
        ).order_by(OAuthConsent.granted_at.desc())

        result = await db.execute(query)
        rows = result.all()

        items = [
            ConsentResponse(
                id=consent.id,
                application_id=consent.application_id,
                application_name=app.name,
                tenant_id=consent.tenant_id,
                user_id=consent.user_id,
                patient_id=consent.patient_id,
                granted_scopes=consent.granted_scopes,
                is_active=consent.is_active,
                granted_at=consent.granted_at,
                expires_at=consent.expires_at
            )
            for consent, app in rows
        ]

        return ConsentListResponse(items=items, total=len(items))

    # ========================================================================
    # SMART on FHIR
    # ========================================================================

    async def get_smart_configuration(
        self,
        base_url: str
    ) -> SMARTConfiguration:
        """Get SMART on FHIR well-known configuration."""
        return SMARTConfiguration(
            issuer=self.issuer,
            authorization_endpoint=f"{base_url}/oauth/authorize",
            token_endpoint=f"{base_url}/oauth/token",
            token_endpoint_auth_methods_supported=[
                "client_secret_basic",
                "client_secret_post",
                "private_key_jwt"
            ],
            registration_endpoint=f"{base_url}/oauth/register",
            scopes_supported=list(self.FHIR_SCOPES.keys()),
            response_types_supported=["code"],
            capabilities=[
                "launch-ehr",
                "launch-standalone",
                "client-public",
                "client-confidential-symmetric",
                "sso-openid-connect",
                "context-ehr-patient",
                "context-ehr-encounter",
                "context-standalone-patient",
                "permission-offline",
                "permission-patient",
                "permission-user"
            ],
            code_challenge_methods_supported=["S256"]
        )

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def _get_application(
        self,
        db: AsyncSession,
        application_id: UUID,
        organization_id: UUID
    ) -> OAuthApplication:
        """Get application with organization validation."""
        query = select(OAuthApplication).where(
            and_(
                OAuthApplication.id == application_id,
                OAuthApplication.organization_id == organization_id
            )
        )
        result = await db.execute(query)
        app = result.scalar_one_or_none()

        if not app:
            raise ValueError("Application not found")

        return app

    async def _get_app_by_client_id(
        self,
        db: AsyncSession,
        client_id: str
    ) -> OAuthApplication:
        """Get application by client ID."""
        query = select(OAuthApplication).where(
            OAuthApplication.client_id == client_id
        )
        result = await db.execute(query)
        app = result.scalar_one_or_none()

        if not app:
            raise ValueError("Invalid client_id")

        return app

    async def _get_app_by_id(
        self,
        db: AsyncSession,
        application_id: UUID
    ) -> OAuthApplication:
        """Get application by ID."""
        query = select(OAuthApplication).where(
            OAuthApplication.id == application_id
        )
        result = await db.execute(query)
        app = result.scalar_one_or_none()

        if not app:
            raise ValueError("Application not found")

        return app

    async def _create_access_token(
        self,
        db: AsyncSession,
        app: OAuthApplication,
        tenant_id: UUID,
        user_id: Optional[UUID],
        scopes: List[str],
        patient_id: Optional[UUID] = None,
        launch_context: Optional[Dict] = None
    ) -> OAuthToken:
        """Create access token record."""
        token = OAuthToken(
            application_id=app.id,
            tenant_id=tenant_id,
            token_type=TokenType.ACCESS,
            token_hash=secrets.token_hex(32),
            user_id=user_id,
            patient_id=patient_id,
            scopes=scopes,
            launch_context=launch_context or {},
            expires_at=datetime.utcnow() + timedelta(seconds=app.access_token_ttl)
        )
        db.add(token)
        await db.flush()
        return token

    async def _create_refresh_token(
        self,
        db: AsyncSession,
        app: OAuthApplication,
        tenant_id: UUID,
        user_id: Optional[UUID],
        scopes: List[str],
        patient_id: Optional[UUID],
        access_token_id: UUID
    ) -> OAuthToken:
        """Create refresh token record."""
        token = OAuthToken(
            application_id=app.id,
            tenant_id=tenant_id,
            token_type=TokenType.REFRESH,
            token_hash=secrets.token_hex(32),
            user_id=user_id,
            patient_id=patient_id,
            scopes=scopes,
            parent_token_id=access_token_id,
            expires_at=datetime.utcnow() + timedelta(seconds=app.refresh_token_ttl)
        )
        db.add(token)
        await db.flush()
        return token

    def _encode_jwt_token(
        self,
        token: OAuthToken,
        app: OAuthApplication
    ) -> str:
        """Encode token as JWT."""
        payload = {
            "jti": str(token.id),
            "iss": self.issuer,
            "aud": app.client_id,
            "sub": str(token.user_id) if token.user_id else str(token.application_id),
            "client_id": app.client_id,
            "scope": " ".join(token.scopes),
            "iat": datetime.utcnow().timestamp(),
            "exp": token.expires_at.timestamp(),
            "tenant_id": str(token.tenant_id)
        }

        if token.patient_id:
            payload["patient"] = str(token.patient_id)

        if token.launch_context:
            payload.update(token.launch_context)

        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def _generate_slug(self, name: str) -> str:
        """Generate URL-safe slug."""
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')[:100]

    def _to_app_response(self, app: OAuthApplication) -> OAuthAppResponse:
        """Convert application to response model."""
        return OAuthAppResponse(
            id=app.id,
            organization_id=app.organization_id,
            name=app.name,
            slug=app.slug,
            description=app.description,
            app_type=app.app_type.value,
            status=app.status.value,
            client_id=app.client_id,
            redirect_uris=app.redirect_uris or [],
            allowed_grant_types=app.allowed_grant_types or [],
            allowed_scopes=app.allowed_scopes or [],
            default_scopes=app.default_scopes or [],
            is_smart_on_fhir=app.is_smart_on_fhir,
            launch_uri=app.launch_uri,
            homepage_url=app.homepage_url,
            logo_url=app.logo_url,
            icon_url=app.icon_url,
            access_token_ttl=app.access_token_ttl,
            refresh_token_ttl=app.refresh_token_ttl,
            require_pkce=app.require_pkce,
            created_at=app.created_at,
            updated_at=app.updated_at
        )

    def _to_api_key_response(self, key: APIKey) -> APIKeyResponse:
        """Convert API key to response model."""
        return APIKeyResponse(
            id=key.id,
            application_id=key.application_id,
            name=key.name,
            key_prefix=key.key_prefix,
            status=key.status.value,
            scopes=key.scopes or [],
            is_test_key=key.is_test_key,
            rate_limit_per_minute=key.rate_limit_per_minute,
            rate_limit_per_day=key.rate_limit_per_day,
            monthly_quota=key.monthly_quota,
            last_used_at=key.last_used_at,
            total_requests=key.total_requests,
            expires_at=key.expires_at,
            created_at=key.created_at
        )


# Import for type hints
from modules.marketplace.schemas import AppTypeSchema

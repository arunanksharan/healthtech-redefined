"""
API Marketplace Router
Provides endpoints for developer portal, OAuth, marketplace, and publishing.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db

from .models import AppCategory
from .schemas import (
    APIKeyCreate,
    APIKeyResponse,
    APIKeyWithSecret,
    APIUsageLogCreate,
    APIUsageLogResponse,
    APIUsageSummary,
    AppInstallationCreate,
    AppInstallationResponse,
    AppInstallationUpdate,
    AppReviewCreate,
    AppReviewResponse,
    AppReviewUpdate,
    AppSearchFilters,
    AppSubmissionCreate,
    AppSubmissionResponse,
    AppVersionCreate,
    AppVersionResponse,
    AuthorizationRequest,
    AuthorizationResponse,
    ClientCredentialsRequest,
    CodeSample,
    ConsentCreate,
    ConsentResponse,
    DeveloperDashboard,
    DeveloperOrgCreate,
    DeveloperOrgResponse,
    DeveloperOrgUpdate,
    OAuthAppCreate,
    OAuthAppResponse,
    OAuthAppUpdate,
    OAuthAppWithSecret,
    PaginatedResponse,
    PublisherDashboard,
    RefreshTokenRequest,
    ReviewDecision,
    SandboxCreate,
    SandboxResponse,
    SandboxWithCredentials,
    SDKDocumentation,
    SDKLanguage,
    SMARTConfiguration,
    SubmissionReviewCreate,
    TeamMemberInvite,
    TeamMemberResponse,
    TokenExchangeRequest,
    TokenResponse,
    UsageAnalytics,
    VersionRollout,
    WebhookCreate,
    WebhookResponse,
    WebhookUpdate,
)
from .services import (
    APIGatewayService,
    DeveloperService,
    MarketplaceService,
    OAuthService,
    PublisherService,
    SDKGeneratorService,
)

router = APIRouter(prefix="/marketplace", tags=["API Marketplace"])

# Service instances
developer_service = DeveloperService()
oauth_service = OAuthService()
gateway_service = APIGatewayService()
marketplace_service = MarketplaceService()
publisher_service = PublisherService()
sdk_service = SDKGeneratorService()


# =============================================================================
# Developer Portal Endpoints
# =============================================================================

@router.post(
    "/developers/register",
    response_model=DeveloperOrgResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a developer organization"
)
async def register_developer(
    data: DeveloperOrgCreate,
    db: AsyncSession = Depends(get_db),
    x_user_id: UUID = Header(..., description="Current user ID")
):
    """Register a new developer organization for API access."""
    try:
        return await developer_service.register_organization(db, data, x_user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/developers/{organization_id}",
    response_model=DeveloperOrgResponse,
    summary="Get developer organization details"
)
async def get_developer_organization(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    x_user_id: UUID = Header(..., description="Current user ID")
):
    """Get details of a developer organization."""
    try:
        return await developer_service.get_organization(db, organization_id, x_user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put(
    "/developers/{organization_id}",
    response_model=DeveloperOrgResponse,
    summary="Update developer organization"
)
async def update_developer_organization(
    organization_id: UUID,
    data: DeveloperOrgUpdate,
    db: AsyncSession = Depends(get_db),
    x_user_id: UUID = Header(..., description="Current user ID")
):
    """Update a developer organization."""
    try:
        return await developer_service.update_organization(
            db, organization_id, data, x_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/developers/{organization_id}/dashboard",
    response_model=DeveloperDashboard,
    summary="Get developer dashboard"
)
async def get_developer_dashboard(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    x_user_id: UUID = Header(..., description="Current user ID")
):
    """Get developer dashboard with statistics and applications."""
    try:
        return await developer_service.get_dashboard(db, organization_id, x_user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Team Management
@router.post(
    "/developers/{organization_id}/members",
    response_model=TeamMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite team member"
)
async def invite_team_member(
    organization_id: UUID,
    data: TeamMemberInvite,
    db: AsyncSession = Depends(get_db),
    x_user_id: UUID = Header(..., description="Current user ID")
):
    """Invite a new member to the developer organization."""
    try:
        return await developer_service.invite_member(
            db, organization_id, data, x_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/developers/invitations/{token}/accept",
    response_model=TeamMemberResponse,
    summary="Accept team invitation"
)
async def accept_invitation(
    token: str,
    db: AsyncSession = Depends(get_db),
    x_user_id: UUID = Header(..., description="Current user ID")
):
    """Accept a team invitation."""
    try:
        return await developer_service.accept_invitation(db, token, x_user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/developers/{organization_id}/members",
    response_model=list[TeamMemberResponse],
    summary="List team members"
)
async def list_team_members(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    x_user_id: UUID = Header(..., description="Current user ID")
):
    """List all members of a developer organization."""
    try:
        return await developer_service.list_members(db, organization_id, x_user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
    "/developers/{organization_id}/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove team member"
)
async def remove_team_member(
    organization_id: UUID,
    member_id: UUID,
    db: AsyncSession = Depends(get_db),
    x_user_id: UUID = Header(..., description="Current user ID")
):
    """Remove a member from the developer organization."""
    try:
        await developer_service.remove_member(
            db, organization_id, member_id, x_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Sandbox Management
@router.post(
    "/developers/{organization_id}/sandboxes",
    response_model=SandboxWithCredentials,
    status_code=status.HTTP_201_CREATED,
    summary="Create sandbox environment"
)
async def create_sandbox(
    organization_id: UUID,
    data: SandboxCreate,
    db: AsyncSession = Depends(get_db),
    x_user_id: UUID = Header(..., description="Current user ID")
):
    """Create a new sandbox environment for testing."""
    try:
        return await developer_service.create_sandbox(
            db, organization_id, data, x_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/developers/{organization_id}/sandboxes",
    response_model=list[SandboxResponse],
    summary="List sandbox environments"
)
async def list_sandboxes(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    x_user_id: UUID = Header(..., description="Current user ID")
):
    """List all sandbox environments for the organization."""
    try:
        return await developer_service.list_sandboxes(db, organization_id, x_user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/developers/{organization_id}/sandboxes/{sandbox_id}/reset",
    response_model=SandboxWithCredentials,
    summary="Reset sandbox environment"
)
async def reset_sandbox(
    organization_id: UUID,
    sandbox_id: UUID,
    db: AsyncSession = Depends(get_db),
    x_user_id: UUID = Header(..., description="Current user ID")
):
    """Reset sandbox to initial state with fresh test data."""
    try:
        return await developer_service.reset_sandbox(
            db, organization_id, sandbox_id, x_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# OAuth 2.0 & SMART on FHIR Endpoints
# =============================================================================

@router.post(
    "/oauth/applications",
    response_model=OAuthAppWithSecret,
    status_code=status.HTTP_201_CREATED,
    summary="Create OAuth application"
)
async def create_oauth_application(
    data: OAuthAppCreate,
    db: AsyncSession = Depends(get_db),
    x_user_id: UUID = Header(..., description="Current user ID"),
    x_organization_id: UUID = Header(..., description="Developer organization ID")
):
    """Create a new OAuth application."""
    try:
        return await oauth_service.create_application(
            db, x_organization_id, data, x_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/oauth/applications/{application_id}",
    response_model=OAuthAppResponse,
    summary="Get OAuth application"
)
async def get_oauth_application(
    application_id: UUID,
    db: AsyncSession = Depends(get_db),
    x_user_id: UUID = Header(..., description="Current user ID"),
    x_organization_id: UUID = Header(..., description="Developer organization ID")
):
    """Get OAuth application details."""
    try:
        return await oauth_service.get_application(
            db, application_id, x_organization_id, x_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put(
    "/oauth/applications/{application_id}",
    response_model=OAuthAppResponse,
    summary="Update OAuth application"
)
async def update_oauth_application(
    application_id: UUID,
    data: OAuthAppUpdate,
    db: AsyncSession = Depends(get_db),
    x_user_id: UUID = Header(..., description="Current user ID"),
    x_organization_id: UUID = Header(..., description="Developer organization ID")
):
    """Update an OAuth application."""
    try:
        return await oauth_service.update_application(
            db, application_id, x_organization_id, data, x_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/oauth/applications/{application_id}/rotate-secret",
    response_model=OAuthAppWithSecret,
    summary="Rotate client secret"
)
async def rotate_client_secret(
    application_id: UUID,
    db: AsyncSession = Depends(get_db),
    x_user_id: UUID = Header(..., description="Current user ID"),
    x_organization_id: UUID = Header(..., description="Developer organization ID")
):
    """Rotate the client secret for an OAuth application."""
    try:
        return await oauth_service.rotate_client_secret(
            db, application_id, x_organization_id, x_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# API Keys
@router.post(
    "/oauth/applications/{application_id}/api-keys",
    response_model=APIKeyWithSecret,
    status_code=status.HTTP_201_CREATED,
    summary="Create API key"
)
async def create_api_key(
    application_id: UUID,
    data: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
    x_user_id: UUID = Header(..., description="Current user ID"),
    x_organization_id: UUID = Header(..., description="Developer organization ID")
):
    """Create a new API key for the application."""
    try:
        return await oauth_service.create_api_key(
            db, application_id, x_organization_id, data, x_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/oauth/applications/{application_id}/api-keys",
    response_model=list[APIKeyResponse],
    summary="List API keys"
)
async def list_api_keys(
    application_id: UUID,
    db: AsyncSession = Depends(get_db),
    x_user_id: UUID = Header(..., description="Current user ID"),
    x_organization_id: UUID = Header(..., description="Developer organization ID")
):
    """List all API keys for an application."""
    try:
        return await oauth_service.list_api_keys(
            db, application_id, x_organization_id, x_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
    "/oauth/api-keys/{api_key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke API key"
)
async def revoke_api_key(
    api_key_id: UUID,
    db: AsyncSession = Depends(get_db),
    x_user_id: UUID = Header(..., description="Current user ID"),
    x_organization_id: UUID = Header(..., description="Developer organization ID")
):
    """Revoke an API key."""
    try:
        await oauth_service.revoke_api_key(
            db, api_key_id, x_organization_id, x_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# OAuth Authorization Flow
@router.get(
    "/oauth/authorize",
    summary="OAuth authorization endpoint"
)
async def authorize(
    request: Request,
    client_id: str = Query(...),
    response_type: str = Query(...),
    redirect_uri: str = Query(...),
    scope: str = Query(...),
    state: str = Query(...),
    code_challenge: Optional[str] = Query(None),
    code_challenge_method: Optional[str] = Query(None),
    launch: Optional[str] = Query(None),
    aud: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    x_tenant_id: UUID = Header(..., description="Tenant ID"),
    x_user_id: UUID = Header(..., description="User ID"),
    x_patient_id: Optional[UUID] = Header(None, description="Patient context")
):
    """
    OAuth 2.0 Authorization endpoint.
    Supports Authorization Code flow with PKCE and SMART on FHIR.
    """
    try:
        auth_request = AuthorizationRequest(
            client_id=client_id,
            response_type=response_type,
            redirect_uri=redirect_uri,
            scope=scope,
            state=state,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            launch=launch,
            aud=aud
        )
        return await oauth_service.create_authorization_code(
            db, auth_request, x_tenant_id, x_user_id, x_patient_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/oauth/token",
    response_model=TokenResponse,
    summary="OAuth token endpoint"
)
async def token(
    grant_type: str = Query(...),
    code: Optional[str] = Query(None),
    redirect_uri: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None),
    client_secret: Optional[str] = Query(None),
    code_verifier: Optional[str] = Query(None),
    refresh_token: Optional[str] = Query(None),
    scope: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    OAuth 2.0 Token endpoint.
    Supports authorization_code, refresh_token, and client_credentials grants.
    """
    try:
        if grant_type == "authorization_code":
            request = TokenExchangeRequest(
                grant_type=grant_type,
                code=code,
                redirect_uri=redirect_uri,
                client_id=client_id,
                client_secret=client_secret,
                code_verifier=code_verifier
            )
            return await oauth_service.exchange_authorization_code(db, request)

        elif grant_type == "refresh_token":
            request = RefreshTokenRequest(
                grant_type=grant_type,
                refresh_token=refresh_token,
                client_id=client_id,
                client_secret=client_secret,
                scope=scope
            )
            return await oauth_service.refresh_access_token(db, request)

        elif grant_type == "client_credentials":
            request = ClientCredentialsRequest(
                grant_type=grant_type,
                client_id=client_id,
                client_secret=client_secret,
                scope=scope
            )
            return await oauth_service.client_credentials_grant(db, request)

        else:
            raise HTTPException(status_code=400, detail="Unsupported grant type")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/oauth/token/revoke",
    status_code=status.HTTP_200_OK,
    summary="Revoke token"
)
async def revoke_token(
    token: str = Query(...),
    token_type_hint: Optional[str] = Query(None),
    client_id: str = Query(...),
    client_secret: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Revoke an access or refresh token."""
    try:
        await oauth_service.revoke_token(db, token, client_id, client_secret)
        return {"revoked": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Consent Management
@router.post(
    "/oauth/applications/{application_id}/consent",
    response_model=ConsentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Grant consent"
)
async def grant_consent(
    application_id: UUID,
    data: ConsentCreate,
    db: AsyncSession = Depends(get_db),
    x_tenant_id: UUID = Header(..., description="Tenant ID"),
    x_user_id: UUID = Header(..., description="User ID")
):
    """Grant consent for an application to access data."""
    try:
        return await oauth_service.grant_consent(
            db, application_id, x_tenant_id, x_user_id, data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/oauth/applications/{application_id}/consent",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke consent"
)
async def revoke_consent(
    application_id: UUID,
    db: AsyncSession = Depends(get_db),
    x_tenant_id: UUID = Header(..., description="Tenant ID"),
    x_user_id: UUID = Header(..., description="User ID")
):
    """Revoke consent for an application."""
    try:
        await oauth_service.revoke_consent(db, application_id, x_tenant_id, x_user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# SMART on FHIR
@router.get(
    "/.well-known/smart-configuration",
    response_model=SMARTConfiguration,
    summary="SMART Configuration"
)
async def smart_configuration(request: Request):
    """Get SMART on FHIR configuration for discovery."""
    base_url = str(request.base_url).rstrip("/")
    return await oauth_service.get_smart_configuration(base_url)


@router.get(
    "/oauth/scopes",
    response_model=dict[str, str],
    summary="List available scopes"
)
async def list_scopes():
    """List all available OAuth scopes."""
    return oauth_service.list_available_scopes()


# Webhooks
@router.post(
    "/oauth/applications/{application_id}/webhooks",
    response_model=WebhookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create webhook"
)
async def create_webhook(
    application_id: UUID,
    data: WebhookCreate,
    db: AsyncSession = Depends(get_db),
    x_user_id: UUID = Header(..., description="Current user ID"),
    x_organization_id: UUID = Header(..., description="Developer organization ID")
):
    """Create a webhook endpoint for event notifications."""
    try:
        return await oauth_service.create_webhook(
            db, application_id, x_organization_id, data, x_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/oauth/applications/{application_id}/webhooks",
    response_model=list[WebhookResponse],
    summary="List webhooks"
)
async def list_webhooks(
    application_id: UUID,
    db: AsyncSession = Depends(get_db),
    x_user_id: UUID = Header(..., description="Current user ID"),
    x_organization_id: UUID = Header(..., description="Developer organization ID")
):
    """List all webhooks for an application."""
    try:
        return await oauth_service.list_webhooks(
            db, application_id, x_organization_id, x_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put(
    "/oauth/webhooks/{webhook_id}",
    response_model=WebhookResponse,
    summary="Update webhook"
)
async def update_webhook(
    webhook_id: UUID,
    data: WebhookUpdate,
    db: AsyncSession = Depends(get_db),
    x_user_id: UUID = Header(..., description="Current user ID"),
    x_organization_id: UUID = Header(..., description="Developer organization ID")
):
    """Update a webhook endpoint."""
    try:
        return await oauth_service.update_webhook(
            db, webhook_id, x_organization_id, data, x_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/oauth/webhooks/{webhook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete webhook"
)
async def delete_webhook(
    webhook_id: UUID,
    db: AsyncSession = Depends(get_db),
    x_user_id: UUID = Header(..., description="Current user ID"),
    x_organization_id: UUID = Header(..., description="Developer organization ID")
):
    """Delete a webhook endpoint."""
    try:
        await oauth_service.delete_webhook(db, webhook_id, x_organization_id, x_user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# API Gateway & Usage Endpoints
# =============================================================================

@router.get(
    "/gateway/rate-limit",
    response_model=dict,
    summary="Check rate limit status"
)
async def check_rate_limit(
    db: AsyncSession = Depends(get_db),
    x_application_id: UUID = Header(..., description="Application ID"),
    x_api_key_id: Optional[UUID] = Header(None, description="API Key ID")
):
    """Check current rate limit status for an application."""
    status = await gateway_service.get_rate_limit_status(
        db, x_application_id, x_api_key_id
    )
    return {
        "requests_remaining": status.requests_remaining,
        "requests_limit": status.requests_limit,
        "window_reset_at": status.window_reset_at.isoformat(),
        "quota_remaining": status.quota_remaining,
        "quota_limit": status.quota_limit
    }


@router.post(
    "/gateway/usage",
    response_model=APIUsageLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log API usage"
)
async def log_usage(
    data: APIUsageLogCreate,
    db: AsyncSession = Depends(get_db),
    x_application_id: UUID = Header(..., description="Application ID")
):
    """Log an API request for analytics."""
    return await gateway_service.log_request(db, x_application_id, data)


@router.get(
    "/gateway/usage/summary",
    response_model=APIUsageSummary,
    summary="Get usage summary"
)
async def get_usage_summary(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    x_application_id: UUID = Header(..., description="Application ID")
):
    """Get API usage summary for an application."""
    return await gateway_service.get_usage_summary(
        db, x_application_id, start_date, end_date
    )


@router.get(
    "/gateway/usage/analytics",
    response_model=UsageAnalytics,
    summary="Get usage analytics"
)
async def get_usage_analytics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    granularity: str = Query("hour", description="Time granularity"),
    db: AsyncSession = Depends(get_db),
    x_application_id: UUID = Header(..., description="Application ID")
):
    """Get detailed usage analytics with time series data."""
    return await gateway_service.get_usage_analytics(
        db, x_application_id, start_date, end_date, granularity
    )


# =============================================================================
# Marketplace Catalog Endpoints
# =============================================================================

@router.get(
    "/apps",
    response_model=PaginatedResponse,
    summary="Search marketplace apps"
)
async def search_apps(
    query: Optional[str] = Query(None, description="Search query"),
    category: Optional[AppCategory] = Query(None),
    is_free: Optional[bool] = Query(None),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    is_featured: Optional[bool] = Query(None),
    smart_on_fhir_only: Optional[bool] = Query(None),
    sort_by: Optional[str] = Query("popularity"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Search and filter marketplace applications."""
    filters = AppSearchFilters(
        query=query,
        category=category,
        is_free=is_free,
        min_rating=min_rating,
        is_featured=is_featured,
        smart_on_fhir_only=smart_on_fhir_only,
        sort_by=sort_by
    )
    return await marketplace_service.search_apps(db, filters, page, page_size)


@router.get(
    "/apps/featured",
    response_model=list,
    summary="Get featured apps"
)
async def get_featured_apps(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get featured applications for the marketplace homepage."""
    return await marketplace_service.get_featured_apps(db, limit)


@router.get(
    "/apps/categories/{category}",
    response_model=PaginatedResponse,
    summary="Get apps by category"
)
async def get_apps_by_category(
    category: AppCategory,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get applications filtered by category."""
    return await marketplace_service.get_apps_by_category(
        db, category, page, page_size
    )


@router.get(
    "/apps/{app_id}",
    response_model=dict,
    summary="Get app details"
)
async def get_app_detail(
    app_id: UUID,
    db: AsyncSession = Depends(get_db),
    x_tenant_id: Optional[UUID] = Header(None, description="Tenant ID for install status")
):
    """Get detailed information about a marketplace application."""
    result = await marketplace_service.get_app_detail(db, app_id, x_tenant_id)
    if not result:
        raise HTTPException(status_code=404, detail="App not found")
    return result


@router.get(
    "/apps/{app_id}/similar",
    response_model=list,
    summary="Get similar apps"
)
async def get_similar_apps(
    app_id: UUID,
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db)
):
    """Get similar applications based on category and tags."""
    return await marketplace_service.get_similar_apps(db, app_id, limit)


# App Installation
@router.post(
    "/apps/{app_id}/install",
    response_model=AppInstallationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Install app"
)
async def install_app(
    app_id: UUID,
    data: AppInstallationCreate,
    db: AsyncSession = Depends(get_db),
    x_tenant_id: UUID = Header(..., description="Tenant ID"),
    x_user_id: UUID = Header(..., description="User ID")
):
    """Install a marketplace application for a tenant."""
    try:
        return await marketplace_service.install_app(
            db, app_id, x_tenant_id, x_user_id, data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/installations/{installation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Uninstall app"
)
async def uninstall_app(
    installation_id: UUID,
    db: AsyncSession = Depends(get_db),
    x_tenant_id: UUID = Header(..., description="Tenant ID"),
    x_user_id: UUID = Header(..., description="User ID")
):
    """Uninstall an application from a tenant."""
    try:
        await marketplace_service.uninstall_app(
            db, installation_id, x_tenant_id, x_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/installations/{installation_id}",
    response_model=AppInstallationResponse,
    summary="Update installation"
)
async def update_installation(
    installation_id: UUID,
    data: AppInstallationUpdate,
    db: AsyncSession = Depends(get_db),
    x_tenant_id: UUID = Header(..., description="Tenant ID"),
    x_user_id: UUID = Header(..., description="User ID")
):
    """Update installation configuration or scopes."""
    try:
        return await marketplace_service.update_installation(
            db, installation_id, x_tenant_id, x_user_id, data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/installations",
    response_model=list,
    summary="List tenant installations"
)
async def list_installations(
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    x_tenant_id: UUID = Header(..., description="Tenant ID")
):
    """List all app installations for a tenant."""
    return await marketplace_service.get_tenant_installations(
        db, x_tenant_id, include_inactive
    )


# App Reviews
@router.post(
    "/apps/{app_id}/reviews",
    response_model=AppReviewResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create review"
)
async def create_review(
    app_id: UUID,
    data: AppReviewCreate,
    db: AsyncSession = Depends(get_db),
    x_tenant_id: UUID = Header(..., description="Tenant ID"),
    x_user_id: UUID = Header(..., description="User ID")
):
    """Create a review for a marketplace application."""
    try:
        return await marketplace_service.create_review(
            db, app_id, x_tenant_id, x_user_id, data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/apps/{app_id}/reviews",
    response_model=PaginatedResponse,
    summary="Get app reviews"
)
async def get_app_reviews(
    app_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("newest"),
    db: AsyncSession = Depends(get_db)
):
    """Get reviews for a marketplace application."""
    return await marketplace_service.get_app_reviews(
        db, app_id, page, page_size, sort_by
    )


@router.put(
    "/reviews/{review_id}",
    response_model=AppReviewResponse,
    summary="Update review"
)
async def update_review(
    review_id: UUID,
    data: AppReviewUpdate,
    db: AsyncSession = Depends(get_db),
    x_user_id: UUID = Header(..., description="User ID")
):
    """Update an existing review."""
    try:
        return await marketplace_service.update_review(db, review_id, x_user_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/reviews/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete review"
)
async def delete_review(
    review_id: UUID,
    db: AsyncSession = Depends(get_db),
    x_user_id: UUID = Header(..., description="User ID")
):
    """Delete a review."""
    try:
        await marketplace_service.delete_review(db, review_id, x_user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/reviews/{review_id}/helpful",
    status_code=status.HTTP_200_OK,
    summary="Mark review helpful"
)
async def mark_review_helpful(
    review_id: UUID,
    db: AsyncSession = Depends(get_db),
    x_user_id: UUID = Header(..., description="User ID")
):
    """Mark a review as helpful."""
    try:
        await marketplace_service.mark_review_helpful(db, review_id, x_user_id)
        return {"marked": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/reviews/{review_id}/respond",
    response_model=AppReviewResponse,
    summary="Respond to review"
)
async def respond_to_review(
    review_id: UUID,
    response_text: str = Query(...),
    db: AsyncSession = Depends(get_db),
    x_organization_id: UUID = Header(..., description="Developer organization ID")
):
    """Add developer response to a review."""
    try:
        return await marketplace_service.respond_to_review(
            db, review_id, x_organization_id, response_text
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Publisher Endpoints
# =============================================================================

@router.post(
    "/publisher/apps",
    response_model=AppSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create app submission"
)
async def create_app_submission(
    data: AppSubmissionCreate,
    db: AsyncSession = Depends(get_db),
    x_organization_id: UUID = Header(..., description="Developer organization ID"),
    x_user_id: UUID = Header(..., description="User ID")
):
    """Create a new app submission for marketplace review."""
    try:
        return await publisher_service.create_submission(
            db, x_organization_id, x_user_id, data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/publisher/apps/{app_id}/submit",
    response_model=AppSubmissionResponse,
    summary="Submit app for review"
)
async def submit_app_for_review(
    app_id: UUID,
    db: AsyncSession = Depends(get_db),
    x_organization_id: UUID = Header(..., description="Developer organization ID"),
    x_user_id: UUID = Header(..., description="User ID")
):
    """Submit an app for marketplace review."""
    try:
        return await publisher_service.submit_for_review(
            db, app_id, x_organization_id, x_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/publisher/apps/{app_id}/review",
    response_model=AppSubmissionResponse,
    summary="Review app submission (admin)"
)
async def review_app_submission(
    app_id: UUID,
    decision: ReviewDecision = Query(...),
    review_notes: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    x_reviewer_id: UUID = Header(..., description="Reviewer user ID")
):
    """Review and approve/reject an app submission (admin only)."""
    try:
        data = SubmissionReviewCreate(
            decision=decision,
            review_notes=review_notes
        )
        return await publisher_service.review_submission(
            db, app_id, x_reviewer_id, data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/publisher/apps/{app_id}/versions",
    response_model=AppVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create app version"
)
async def create_app_version(
    app_id: UUID,
    data: AppVersionCreate,
    db: AsyncSession = Depends(get_db),
    x_organization_id: UUID = Header(..., description="Developer organization ID"),
    x_user_id: UUID = Header(..., description="User ID")
):
    """Create a new version for an existing app."""
    try:
        return await publisher_service.create_version(
            db, app_id, x_organization_id, x_user_id, data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/publisher/apps/{app_id}/versions",
    response_model=list[AppVersionResponse],
    summary="List app versions"
)
async def list_app_versions(
    app_id: UUID,
    db: AsyncSession = Depends(get_db),
    x_organization_id: UUID = Header(..., description="Developer organization ID"),
    x_user_id: UUID = Header(..., description="User ID")
):
    """List all versions for an app."""
    try:
        return await publisher_service.get_app_versions(
            db, app_id, x_organization_id, x_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/publisher/apps/{app_id}/versions/{version_id}/submit",
    response_model=AppVersionResponse,
    summary="Submit version for review"
)
async def submit_version_for_review(
    app_id: UUID,
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
    x_organization_id: UUID = Header(..., description="Developer organization ID"),
    x_user_id: UUID = Header(..., description="User ID")
):
    """Submit a version for review."""
    try:
        return await publisher_service.submit_version_for_review(
            db, app_id, version_id, x_organization_id, x_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/publisher/apps/{app_id}/versions/{version_id}/publish",
    response_model=AppVersionResponse,
    summary="Publish version (admin)"
)
async def publish_version(
    app_id: UUID,
    version_id: UUID,
    initial_percentage: int = Query(100, ge=0, le=100),
    db: AsyncSession = Depends(get_db),
    x_reviewer_id: UUID = Header(..., description="Reviewer user ID")
):
    """Publish a version (admin only). Supports staged rollouts."""
    try:
        rollout = VersionRollout(initial_percentage=initial_percentage)
        return await publisher_service.publish_version(
            db, app_id, version_id, x_reviewer_id, rollout
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/publisher/apps/{app_id}/versions/{version_id}/rollout",
    response_model=AppVersionResponse,
    summary="Update rollout percentage"
)
async def update_rollout_percentage(
    app_id: UUID,
    version_id: UUID,
    percentage: int = Query(..., ge=0, le=100),
    db: AsyncSession = Depends(get_db),
    x_organization_id: UUID = Header(..., description="Developer organization ID"),
    x_user_id: UUID = Header(..., description="User ID")
):
    """Update the rollout percentage for a staged release."""
    try:
        return await publisher_service.update_rollout(
            db, app_id, version_id, x_organization_id, x_user_id, percentage
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/publisher/apps/{app_id}/versions/{version_id}/deprecate",
    response_model=AppVersionResponse,
    summary="Deprecate version"
)
async def deprecate_version(
    app_id: UUID,
    version_id: UUID,
    message: str = Query(..., description="Deprecation message"),
    sunset_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
    x_organization_id: UUID = Header(..., description="Developer organization ID"),
    x_user_id: UUID = Header(..., description="User ID")
):
    """Deprecate a published version."""
    try:
        return await publisher_service.deprecate_version(
            db, app_id, version_id, x_organization_id, x_user_id,
            message, sunset_date
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/publisher/apps/{app_id}/unpublish",
    response_model=dict,
    summary="Unpublish app"
)
async def unpublish_app(
    app_id: UUID,
    reason: str = Query(..., description="Reason for unpublishing"),
    db: AsyncSession = Depends(get_db),
    x_organization_id: UUID = Header(..., description="Developer organization ID"),
    x_user_id: UUID = Header(..., description="User ID")
):
    """Unpublish an app from the marketplace."""
    try:
        return await publisher_service.unpublish_app(
            db, app_id, x_organization_id, x_user_id, reason
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/publisher/dashboard",
    response_model=PublisherDashboard,
    summary="Get publisher dashboard"
)
async def get_publisher_dashboard(
    db: AsyncSession = Depends(get_db),
    x_organization_id: UUID = Header(..., description="Developer organization ID"),
    x_user_id: UUID = Header(..., description="User ID")
):
    """Get publisher dashboard with app statistics."""
    try:
        return await publisher_service.get_publisher_dashboard(
            db, x_organization_id, x_user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# =============================================================================
# SDK & Documentation Endpoints
# =============================================================================

@router.get(
    "/sdk/docs/{language}",
    response_model=SDKDocumentation,
    summary="Get SDK documentation"
)
async def get_sdk_documentation(language: SDKLanguage):
    """Get SDK documentation for a specific language."""
    docs = sdk_service.get_sdk_documentation(language)
    if not docs:
        raise HTTPException(status_code=404, detail="SDK documentation not found")
    return docs


@router.get(
    "/sdk/samples/auth",
    response_model=list[CodeSample],
    summary="Get authentication samples"
)
async def get_auth_samples(
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    scopes: str = Query(..., description="Space-separated scopes"),
    language: Optional[SDKLanguage] = Query(None)
):
    """Get OAuth authentication code samples."""
    return sdk_service.generate_authentication_samples(
        client_id, redirect_uri, scopes.split(), language
    )


@router.get(
    "/sdk/samples/fhir",
    response_model=list[CodeSample],
    summary="Get FHIR operation samples"
)
async def get_fhir_samples(
    resource_type: str = Query(..., description="FHIR resource type"),
    operation: str = Query(..., description="Operation: read, search, create, update, delete"),
    resource_id: Optional[str] = Query(None),
    language: Optional[SDKLanguage] = Query(None)
):
    """Get FHIR operation code samples."""
    return sdk_service.generate_fhir_samples(
        resource_type, operation, resource_id, language=language
    )


@router.get(
    "/sdk/samples/webhook",
    response_model=list[CodeSample],
    summary="Get webhook handler samples"
)
async def get_webhook_samples(
    event_types: str = Query(..., description="Comma-separated event types"),
    language: Optional[SDKLanguage] = Query(None)
):
    """Get webhook handling code samples."""
    return sdk_service.generate_webhook_samples(
        event_types.split(","), language
    )


@router.get(
    "/sdk/samples/smart",
    response_model=list[CodeSample],
    summary="Get SMART on FHIR launch samples"
)
async def get_smart_launch_samples(
    client_id: str = Query(...),
    scopes: str = Query(..., description="Space-separated scopes"),
    launch_type: str = Query("standalone", description="ehr or standalone"),
    language: Optional[SDKLanguage] = Query(None)
):
    """Get SMART on FHIR launch code samples."""
    return sdk_service.generate_smart_launch_samples(
        client_id, scopes.split(), launch_type, language
    )


@router.get(
    "/sdk/samples/api",
    response_model=list[CodeSample],
    summary="Get API call samples"
)
async def get_api_call_samples(
    endpoint: str = Query(..., description="API endpoint"),
    method: str = Query("GET", description="HTTP method"),
    resource_type: str = Query("Resource", description="Resource type name"),
    language: Optional[SDKLanguage] = Query(None)
):
    """Get generic API call code samples."""
    return sdk_service.generate_api_call_samples(
        endpoint, method, resource_type, language=language
    )

"""
Developer Service
EPIC-018: Developer registration, team management, and sandbox provisioning
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
import secrets
import hashlib
import re

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from modules.marketplace.models import (
    DeveloperOrganization, DeveloperMember, SandboxEnvironment,
    OAuthApplication, DeveloperAuditLog,
    DeveloperStatus, DeveloperRole, SandboxStatus
)
from modules.marketplace.schemas import (
    DeveloperOrgCreate, DeveloperOrgUpdate, DeveloperOrgResponse,
    DeveloperOrgListResponse, TeamMemberInvite, TeamMemberUpdate,
    TeamMemberResponse, TeamMemberListResponse,
    SandboxCreate, SandboxResponse, SandboxWithCredentials,
    DeveloperDashboard, DeveloperStats
)


class DeveloperService:
    """
    Service for developer organization management.

    Handles:
    - Developer registration and verification
    - Team member management
    - Sandbox environment provisioning
    - Developer dashboard and statistics
    """

    def __init__(self):
        self.default_sandbox_expiry_days = 90
        self.max_sandbox_api_calls = 1000

    # ========================================================================
    # Organization Management
    # ========================================================================

    async def register_organization(
        self,
        db: AsyncSession,
        data: DeveloperOrgCreate,
        user_id: UUID
    ) -> DeveloperOrgResponse:
        """Register a new developer organization."""
        # Generate slug from name
        slug = self._generate_slug(data.name)

        # Check if slug exists
        existing = await db.execute(
            select(DeveloperOrganization).where(
                DeveloperOrganization.slug == slug
            )
        )
        if existing.scalar_one_or_none():
            # Append random suffix
            slug = f"{slug}-{secrets.token_hex(3)}"

        # Create organization
        organization = DeveloperOrganization(
            name=data.name,
            slug=slug,
            email=data.email,
            website=data.website,
            description=data.description,
            contact_name=data.contact_name,
            contact_email=data.contact_email,
            contact_phone=data.contact_phone,
            address_line1=data.address_line1,
            address_line2=data.address_line2,
            city=data.city,
            state=data.state,
            postal_code=data.postal_code,
            country=data.country,
            status=DeveloperStatus.PENDING
        )

        db.add(organization)
        await db.flush()

        # Add creator as owner
        owner_member = DeveloperMember(
            organization_id=organization.id,
            user_id=user_id,
            email=data.email,
            name=data.contact_name,
            role=DeveloperRole.OWNER,
            is_active=True,
            accepted_at=datetime.utcnow()
        )
        db.add(owner_member)

        # Create default sandbox
        await self._create_default_sandbox(db, organization.id)

        # Log audit
        audit_log = DeveloperAuditLog(
            organization_id=organization.id,
            user_id=user_id,
            action="organization.created",
            entity_type="organization",
            entity_id=organization.id,
            details={"name": data.name, "email": data.email}
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(organization)

        return self._to_org_response(organization)

    async def get_organization(
        self,
        db: AsyncSession,
        organization_id: UUID
    ) -> DeveloperOrgResponse:
        """Get organization by ID."""
        org = await self._get_organization(db, organization_id)
        return self._to_org_response(org)

    async def get_organization_by_slug(
        self,
        db: AsyncSession,
        slug: str
    ) -> DeveloperOrgResponse:
        """Get organization by slug."""
        query = select(DeveloperOrganization).where(
            DeveloperOrganization.slug == slug
        )
        result = await db.execute(query)
        org = result.scalar_one_or_none()

        if not org:
            raise ValueError("Organization not found")

        return self._to_org_response(org)

    async def update_organization(
        self,
        db: AsyncSession,
        organization_id: UUID,
        data: DeveloperOrgUpdate,
        user_id: UUID
    ) -> DeveloperOrgResponse:
        """Update organization details."""
        org = await self._get_organization(db, organization_id)

        # Check permission
        await self._check_permission(db, organization_id, user_id, [DeveloperRole.OWNER, DeveloperRole.ADMIN])

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(org, field):
                setattr(org, field, value)

        # Log audit
        audit_log = DeveloperAuditLog(
            organization_id=organization_id,
            user_id=user_id,
            action="organization.updated",
            entity_type="organization",
            entity_id=organization_id,
            details={"updated_fields": list(update_data.keys())}
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(org)

        return self._to_org_response(org)

    async def accept_terms(
        self,
        db: AsyncSession,
        organization_id: UUID,
        terms_version: str,
        user_id: UUID
    ) -> DeveloperOrgResponse:
        """Accept developer terms and conditions."""
        org = await self._get_organization(db, organization_id)

        org.agreed_to_terms = True
        org.terms_accepted_at = datetime.utcnow()
        org.terms_version = terms_version

        # Activate organization if pending
        if org.status == DeveloperStatus.PENDING:
            org.status = DeveloperStatus.ACTIVE

        # Log audit
        audit_log = DeveloperAuditLog(
            organization_id=organization_id,
            user_id=user_id,
            action="terms.accepted",
            entity_type="organization",
            entity_id=organization_id,
            details={"terms_version": terms_version}
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(org)

        return self._to_org_response(org)

    async def list_user_organizations(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> DeveloperOrgListResponse:
        """List organizations for a user."""
        # Get member records for user
        member_query = select(DeveloperMember.organization_id).where(
            and_(
                DeveloperMember.user_id == user_id,
                DeveloperMember.is_active == True
            )
        )
        member_result = await db.execute(member_query)
        org_ids = [row[0] for row in member_result.all()]

        if not org_ids:
            return DeveloperOrgListResponse(items=[], total=0)

        # Get organizations
        org_query = select(DeveloperOrganization).where(
            DeveloperOrganization.id.in_(org_ids)
        ).order_by(DeveloperOrganization.name)

        result = await db.execute(org_query)
        organizations = result.scalars().all()

        return DeveloperOrgListResponse(
            items=[self._to_org_response(org) for org in organizations],
            total=len(organizations)
        )

    # ========================================================================
    # Team Member Management
    # ========================================================================

    async def invite_member(
        self,
        db: AsyncSession,
        organization_id: UUID,
        data: TeamMemberInvite,
        inviter_id: UUID
    ) -> TeamMemberResponse:
        """Invite a new team member."""
        # Check permission
        await self._check_permission(
            db, organization_id, inviter_id,
            [DeveloperRole.OWNER, DeveloperRole.ADMIN]
        )

        # Check if already a member
        existing = await db.execute(
            select(DeveloperMember).where(
                and_(
                    DeveloperMember.organization_id == organization_id,
                    DeveloperMember.email == data.email
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("User is already a member")

        # Generate invitation token
        invitation_token = secrets.token_urlsafe(32)

        member = DeveloperMember(
            organization_id=organization_id,
            user_id=uuid4(),  # Placeholder until accepted
            email=data.email,
            name=data.name,
            role=DeveloperRole(data.role.value),
            is_active=False,
            invited_by=inviter_id,
            invited_at=datetime.utcnow(),
            invitation_token=invitation_token
        )

        db.add(member)

        # Log audit
        audit_log = DeveloperAuditLog(
            organization_id=organization_id,
            user_id=inviter_id,
            action="member.invited",
            entity_type="member",
            entity_id=member.id,
            details={"email": data.email, "role": data.role.value}
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(member)

        # TODO: Send invitation email

        return self._to_member_response(member)

    async def accept_invitation(
        self,
        db: AsyncSession,
        invitation_token: str,
        user_id: UUID
    ) -> TeamMemberResponse:
        """Accept a team invitation."""
        query = select(DeveloperMember).where(
            DeveloperMember.invitation_token == invitation_token
        )
        result = await db.execute(query)
        member = result.scalar_one_or_none()

        if not member:
            raise ValueError("Invalid invitation token")

        if member.accepted_at:
            raise ValueError("Invitation already accepted")

        member.user_id = user_id
        member.is_active = True
        member.accepted_at = datetime.utcnow()
        member.invitation_token = None

        # Log audit
        audit_log = DeveloperAuditLog(
            organization_id=member.organization_id,
            user_id=user_id,
            action="member.joined",
            entity_type="member",
            entity_id=member.id,
            details={"email": member.email}
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(member)

        return self._to_member_response(member)

    async def update_member(
        self,
        db: AsyncSession,
        organization_id: UUID,
        member_id: UUID,
        data: TeamMemberUpdate,
        updater_id: UUID
    ) -> TeamMemberResponse:
        """Update team member."""
        # Check permission
        await self._check_permission(
            db, organization_id, updater_id,
            [DeveloperRole.OWNER, DeveloperRole.ADMIN]
        )

        # Get member
        query = select(DeveloperMember).where(
            and_(
                DeveloperMember.id == member_id,
                DeveloperMember.organization_id == organization_id
            )
        )
        result = await db.execute(query)
        member = result.scalar_one_or_none()

        if not member:
            raise ValueError("Member not found")

        # Can't modify owner unless you're the owner
        if member.role == DeveloperRole.OWNER:
            updater_member = await self._get_member(db, organization_id, updater_id)
            if updater_member.role != DeveloperRole.OWNER:
                raise ValueError("Only owner can modify owner role")

        # Update fields
        if data.name is not None:
            member.name = data.name
        if data.role is not None:
            member.role = DeveloperRole(data.role.value)
        if data.is_active is not None:
            member.is_active = data.is_active

        # Log audit
        audit_log = DeveloperAuditLog(
            organization_id=organization_id,
            user_id=updater_id,
            action="member.updated",
            entity_type="member",
            entity_id=member_id,
            details=data.model_dump(exclude_unset=True)
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(member)

        return self._to_member_response(member)

    async def remove_member(
        self,
        db: AsyncSession,
        organization_id: UUID,
        member_id: UUID,
        remover_id: UUID
    ) -> None:
        """Remove team member."""
        # Check permission
        await self._check_permission(
            db, organization_id, remover_id,
            [DeveloperRole.OWNER, DeveloperRole.ADMIN]
        )

        # Get member
        query = select(DeveloperMember).where(
            and_(
                DeveloperMember.id == member_id,
                DeveloperMember.organization_id == organization_id
            )
        )
        result = await db.execute(query)
        member = result.scalar_one_or_none()

        if not member:
            raise ValueError("Member not found")

        # Can't remove owner
        if member.role == DeveloperRole.OWNER:
            raise ValueError("Cannot remove organization owner")

        # Log audit before deletion
        audit_log = DeveloperAuditLog(
            organization_id=organization_id,
            user_id=remover_id,
            action="member.removed",
            entity_type="member",
            entity_id=member_id,
            details={"email": member.email, "role": member.role.value}
        )
        db.add(audit_log)

        await db.delete(member)
        await db.commit()

    async def list_members(
        self,
        db: AsyncSession,
        organization_id: UUID
    ) -> TeamMemberListResponse:
        """List team members."""
        query = select(DeveloperMember).where(
            DeveloperMember.organization_id == organization_id
        ).order_by(DeveloperMember.created_at)

        result = await db.execute(query)
        members = result.scalars().all()

        return TeamMemberListResponse(
            members=[self._to_member_response(m) for m in members],
            total=len(members)
        )

    # ========================================================================
    # Sandbox Management
    # ========================================================================

    async def create_sandbox(
        self,
        db: AsyncSession,
        organization_id: UUID,
        data: SandboxCreate,
        user_id: UUID
    ) -> SandboxWithCredentials:
        """Create a new sandbox environment."""
        # Check permission
        await self._check_permission(
            db, organization_id, user_id,
            [DeveloperRole.OWNER, DeveloperRole.ADMIN, DeveloperRole.DEVELOPER]
        )

        # Generate sandbox tenant ID
        sandbox_tenant_id = uuid4()

        # Generate test API key
        test_api_key = f"prm_test_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(test_api_key.encode()).hexdigest()

        sandbox = SandboxEnvironment(
            organization_id=organization_id,
            name=data.name,
            status=SandboxStatus.PROVISIONING,
            sandbox_tenant_id=sandbox_tenant_id,
            has_sample_data=data.has_sample_data,
            sample_data_config=data.sample_data_config or {},
            test_api_key_prefix=test_api_key[:12],
            test_api_key_hash=key_hash,
            max_api_calls_per_day=self.max_sandbox_api_calls,
            expires_at=datetime.utcnow() + timedelta(days=self.default_sandbox_expiry_days)
        )

        db.add(sandbox)

        # Log audit
        audit_log = DeveloperAuditLog(
            organization_id=organization_id,
            user_id=user_id,
            action="sandbox.created",
            entity_type="sandbox",
            entity_id=sandbox.id,
            details={"name": data.name}
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(sandbox)

        # Provision sandbox (would be async in production)
        sandbox.status = SandboxStatus.ACTIVE
        await db.commit()

        response = SandboxWithCredentials(
            id=sandbox.id,
            organization_id=sandbox.organization_id,
            name=sandbox.name,
            status=sandbox.status.value,
            sandbox_tenant_id=sandbox.sandbox_tenant_id,
            has_sample_data=sandbox.has_sample_data,
            max_api_calls_per_day=sandbox.max_api_calls_per_day,
            max_records=sandbox.max_records,
            api_calls_today=sandbox.api_calls_today,
            total_api_calls=sandbox.total_api_calls,
            created_at=sandbox.created_at,
            expires_at=sandbox.expires_at,
            last_used_at=sandbox.last_used_at,
            test_api_key=test_api_key
        )

        return response

    async def get_sandbox(
        self,
        db: AsyncSession,
        organization_id: UUID,
        sandbox_id: UUID
    ) -> SandboxResponse:
        """Get sandbox by ID."""
        query = select(SandboxEnvironment).where(
            and_(
                SandboxEnvironment.id == sandbox_id,
                SandboxEnvironment.organization_id == organization_id
            )
        )
        result = await db.execute(query)
        sandbox = result.scalar_one_or_none()

        if not sandbox:
            raise ValueError("Sandbox not found")

        return self._to_sandbox_response(sandbox)

    async def reset_sandbox(
        self,
        db: AsyncSession,
        organization_id: UUID,
        sandbox_id: UUID,
        user_id: UUID
    ) -> SandboxWithCredentials:
        """Reset sandbox to fresh state."""
        # Check permission
        await self._check_permission(
            db, organization_id, user_id,
            [DeveloperRole.OWNER, DeveloperRole.ADMIN, DeveloperRole.DEVELOPER]
        )

        query = select(SandboxEnvironment).where(
            and_(
                SandboxEnvironment.id == sandbox_id,
                SandboxEnvironment.organization_id == organization_id
            )
        )
        result = await db.execute(query)
        sandbox = result.scalar_one_or_none()

        if not sandbox:
            raise ValueError("Sandbox not found")

        # Generate new test API key
        test_api_key = f"prm_test_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(test_api_key.encode()).hexdigest()

        sandbox.status = SandboxStatus.RESETTING
        sandbox.test_api_key_prefix = test_api_key[:12]
        sandbox.test_api_key_hash = key_hash
        sandbox.api_calls_today = 0
        sandbox.last_reset_at = datetime.utcnow()

        # Log audit
        audit_log = DeveloperAuditLog(
            organization_id=organization_id,
            user_id=user_id,
            action="sandbox.reset",
            entity_type="sandbox",
            entity_id=sandbox_id,
            details={}
        )
        db.add(audit_log)

        await db.commit()

        # Complete reset (would be async in production)
        sandbox.status = SandboxStatus.ACTIVE
        await db.commit()
        await db.refresh(sandbox)

        return SandboxWithCredentials(
            id=sandbox.id,
            organization_id=sandbox.organization_id,
            name=sandbox.name,
            status=sandbox.status.value,
            sandbox_tenant_id=sandbox.sandbox_tenant_id,
            has_sample_data=sandbox.has_sample_data,
            max_api_calls_per_day=sandbox.max_api_calls_per_day,
            max_records=sandbox.max_records,
            api_calls_today=sandbox.api_calls_today,
            total_api_calls=sandbox.total_api_calls,
            created_at=sandbox.created_at,
            expires_at=sandbox.expires_at,
            last_used_at=sandbox.last_used_at,
            test_api_key=test_api_key
        )

    async def list_sandboxes(
        self,
        db: AsyncSession,
        organization_id: UUID
    ) -> List[SandboxResponse]:
        """List sandboxes for organization."""
        query = select(SandboxEnvironment).where(
            SandboxEnvironment.organization_id == organization_id
        ).order_by(SandboxEnvironment.created_at)

        result = await db.execute(query)
        sandboxes = result.scalars().all()

        return [self._to_sandbox_response(s) for s in sandboxes]

    # ========================================================================
    # Dashboard & Statistics
    # ========================================================================

    async def get_dashboard(
        self,
        db: AsyncSession,
        organization_id: UUID,
        user_id: UUID
    ) -> DeveloperDashboard:
        """Get developer dashboard data."""
        org = await self._get_organization(db, organization_id)

        # Get applications
        apps_query = select(OAuthApplication).where(
            OAuthApplication.organization_id == organization_id
        ).order_by(OAuthApplication.created_at.desc()).limit(10)
        apps_result = await db.execute(apps_query)
        applications = apps_result.scalars().all()

        # Get sandbox status
        sandbox_query = select(SandboxEnvironment).where(
            SandboxEnvironment.organization_id == organization_id
        ).order_by(SandboxEnvironment.created_at.desc()).limit(1)
        sandbox_result = await db.execute(sandbox_query)
        sandbox = sandbox_result.scalar_one_or_none()

        # Get recent audit logs
        audit_query = select(DeveloperAuditLog).where(
            DeveloperAuditLog.organization_id == organization_id
        ).order_by(DeveloperAuditLog.created_at.desc()).limit(10)
        audit_result = await db.execute(audit_query)
        recent_logs = audit_result.scalars().all()

        # Calculate API calls (placeholder - would query usage logs)
        total_api_calls_today = 0
        total_api_calls_month = 0

        # Count active installations
        from modules.marketplace.models import AppInstallation, InstallationStatus
        install_count_query = select(func.count(AppInstallation.id)).where(
            and_(
                AppInstallation.application_id.in_([a.id for a in applications]),
                AppInstallation.status == InstallationStatus.ACTIVE
            )
        )
        install_result = await db.execute(install_count_query)
        active_installations = install_result.scalar() or 0

        return DeveloperDashboard(
            organization=self._to_org_response(org),
            applications=[self._to_app_response(a) for a in applications],
            total_api_calls_today=total_api_calls_today,
            total_api_calls_month=total_api_calls_month,
            active_installations=active_installations,
            sandbox_status=sandbox.status.value if sandbox else None,
            recent_activity=[
                {
                    "action": log.action,
                    "entity_type": log.entity_type,
                    "created_at": log.created_at.isoformat()
                }
                for log in recent_logs
            ]
        )

    async def get_statistics(
        self,
        db: AsyncSession,
        organization_id: UUID
    ) -> DeveloperStats:
        """Get developer statistics."""
        # Count applications
        app_count_query = select(func.count(OAuthApplication.id)).where(
            OAuthApplication.organization_id == organization_id
        )
        app_result = await db.execute(app_count_query)
        total_applications = app_result.scalar() or 0

        # Count API keys
        from modules.marketplace.models import APIKey
        key_count_query = select(func.count(APIKey.id)).join(OAuthApplication).where(
            OAuthApplication.organization_id == organization_id
        )
        key_result = await db.execute(key_count_query)
        total_api_keys = key_result.scalar() or 0

        # Count installations
        from modules.marketplace.models import AppInstallation
        install_count_query = select(func.count(AppInstallation.id)).join(OAuthApplication).where(
            OAuthApplication.organization_id == organization_id
        )
        install_result = await db.execute(install_count_query)
        total_installations = install_result.scalar() or 0

        return DeveloperStats(
            total_applications=total_applications,
            total_api_keys=total_api_keys,
            total_installations=total_installations,
            total_api_calls=0,  # Placeholder
            api_calls_trend=[],  # Would query time series data
            top_endpoints=[],  # Would query usage logs
            error_rate=0.0  # Would calculate from logs
        )

    # ========================================================================
    # Helper Methods
    # ========================================================================

    async def _get_organization(
        self,
        db: AsyncSession,
        organization_id: UUID
    ) -> DeveloperOrganization:
        """Get organization by ID with validation."""
        query = select(DeveloperOrganization).where(
            DeveloperOrganization.id == organization_id
        )
        result = await db.execute(query)
        org = result.scalar_one_or_none()

        if not org:
            raise ValueError("Organization not found")

        return org

    async def _get_member(
        self,
        db: AsyncSession,
        organization_id: UUID,
        user_id: UUID
    ) -> DeveloperMember:
        """Get member by user ID."""
        query = select(DeveloperMember).where(
            and_(
                DeveloperMember.organization_id == organization_id,
                DeveloperMember.user_id == user_id,
                DeveloperMember.is_active == True
            )
        )
        result = await db.execute(query)
        member = result.scalar_one_or_none()

        if not member:
            raise ValueError("User is not a member of this organization")

        return member

    async def _check_permission(
        self,
        db: AsyncSession,
        organization_id: UUID,
        user_id: UUID,
        required_roles: List[DeveloperRole]
    ) -> None:
        """Check if user has required role."""
        member = await self._get_member(db, organization_id, user_id)

        if member.role not in required_roles:
            raise ValueError("Insufficient permissions")

    async def _create_default_sandbox(
        self,
        db: AsyncSession,
        organization_id: UUID
    ) -> None:
        """Create default sandbox for new organization."""
        test_api_key = f"prm_test_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(test_api_key.encode()).hexdigest()

        sandbox = SandboxEnvironment(
            organization_id=organization_id,
            name="Default Sandbox",
            status=SandboxStatus.ACTIVE,
            sandbox_tenant_id=uuid4(),
            has_sample_data=True,
            test_api_key_prefix=test_api_key[:12],
            test_api_key_hash=key_hash,
            max_api_calls_per_day=self.max_sandbox_api_calls,
            expires_at=datetime.utcnow() + timedelta(days=self.default_sandbox_expiry_days)
        )

        db.add(sandbox)

    def _generate_slug(self, name: str) -> str:
        """Generate URL-safe slug from name."""
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')
        return slug[:100]

    def _to_org_response(self, org: DeveloperOrganization) -> DeveloperOrgResponse:
        """Convert organization to response model."""
        return DeveloperOrgResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            email=org.email,
            website=org.website,
            description=org.description,
            logo_url=org.logo_url,
            contact_name=org.contact_name,
            status=org.status.value,
            verified_at=org.verified_at,
            agreed_to_terms=org.agreed_to_terms,
            created_at=org.created_at
        )

    def _to_member_response(self, member: DeveloperMember) -> TeamMemberResponse:
        """Convert member to response model."""
        return TeamMemberResponse(
            id=member.id,
            organization_id=member.organization_id,
            user_id=member.user_id if member.accepted_at else None,
            email=member.email,
            name=member.name,
            role=member.role.value,
            is_active=member.is_active,
            invited_at=member.invited_at,
            accepted_at=member.accepted_at,
            last_login_at=member.last_login_at,
            two_factor_enabled=member.two_factor_enabled,
            created_at=member.created_at
        )

    def _to_sandbox_response(self, sandbox: SandboxEnvironment) -> SandboxResponse:
        """Convert sandbox to response model."""
        return SandboxResponse(
            id=sandbox.id,
            organization_id=sandbox.organization_id,
            name=sandbox.name,
            status=sandbox.status.value,
            sandbox_tenant_id=sandbox.sandbox_tenant_id,
            has_sample_data=sandbox.has_sample_data,
            max_api_calls_per_day=sandbox.max_api_calls_per_day,
            max_records=sandbox.max_records,
            api_calls_today=sandbox.api_calls_today,
            total_api_calls=sandbox.total_api_calls,
            created_at=sandbox.created_at,
            expires_at=sandbox.expires_at,
            last_used_at=sandbox.last_used_at
        )

    def _to_app_response(self, app: OAuthApplication):
        """Convert OAuth app to response model."""
        from modules.marketplace.schemas import OAuthAppResponse
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

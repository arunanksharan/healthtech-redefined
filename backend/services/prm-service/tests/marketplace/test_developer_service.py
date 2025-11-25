"""
Unit tests for DeveloperService
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from modules.marketplace.services.developer_service import DeveloperService
from modules.marketplace.models import (
    DeveloperOrganization,
    DeveloperMember,
    DeveloperRole,
    DeveloperStatus,
    SandboxEnvironment,
    SandboxStatus,
)
from modules.marketplace.schemas import (
    DeveloperOrgCreate,
    DeveloperOrgUpdate,
    TeamMemberInvite,
    SandboxCreate,
)


@pytest.fixture
def developer_service():
    return DeveloperService()


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def sample_org_create():
    return DeveloperOrgCreate(
        name="Test Developer Org",
        email="dev@test.com",
        website="https://test.com",
        description="Test organization for development"
    )


@pytest.fixture
def sample_organization():
    org = MagicMock(spec=DeveloperOrganization)
    org.id = uuid4()
    org.name = "Test Developer Org"
    org.slug = "test-developer-org"
    org.email = "dev@test.com"
    org.website = "https://test.com"
    org.status = DeveloperStatus.PENDING
    org.created_at = datetime.utcnow()
    org.updated_at = datetime.utcnow()
    return org


@pytest.fixture
def sample_member():
    member = MagicMock(spec=DeveloperMember)
    member.id = uuid4()
    member.developer_organization_id = uuid4()
    member.user_id = uuid4()
    member.role = DeveloperRole.OWNER
    member.email = "owner@test.com"
    member.joined_at = datetime.utcnow()
    return member


class TestDeveloperServiceRegistration:
    """Tests for developer organization registration."""

    @pytest.mark.asyncio
    async def test_register_organization_success(
        self, developer_service, mock_db, sample_org_create
    ):
        """Test successful organization registration."""
        user_id = uuid4()

        # Mock no existing org with same slug
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await developer_service.register_organization(
            mock_db, sample_org_create, user_id
        )

        assert result is not None
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_register_organization_duplicate_slug(
        self, developer_service, mock_db, sample_org_create, sample_organization
    ):
        """Test registration fails with duplicate slug."""
        user_id = uuid4()

        # Mock existing org with same slug
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_organization
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="already exists"):
            await developer_service.register_organization(
                mock_db, sample_org_create, user_id
            )


class TestDeveloperServiceTeamManagement:
    """Tests for team member management."""

    @pytest.mark.asyncio
    async def test_invite_member_success(
        self, developer_service, mock_db, sample_organization, sample_member
    ):
        """Test successful team member invitation."""
        inviter_id = uuid4()
        invite_data = TeamMemberInvite(
            email="newmember@test.com",
            role=DeveloperRole.DEVELOPER
        )

        # Mock organization lookup
        org_result = AsyncMock()
        org_result.scalar_one_or_none.return_value = sample_organization

        # Mock member lookup (inviter exists, invitee doesn't)
        member_result = AsyncMock()
        member_result.scalar_one_or_none.side_effect = [sample_member, None]

        mock_db.execute.side_effect = [org_result, member_result, member_result]

        result = await developer_service.invite_member(
            mock_db, sample_organization.id, invite_data, inviter_id
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_invite_member_not_authorized(
        self, developer_service, mock_db, sample_organization
    ):
        """Test invitation fails when inviter is not authorized."""
        inviter_id = uuid4()
        invite_data = TeamMemberInvite(
            email="newmember@test.com",
            role=DeveloperRole.DEVELOPER
        )

        # Mock organization lookup
        org_result = AsyncMock()
        org_result.scalar_one_or_none.return_value = sample_organization

        # Mock no member found (inviter not a member)
        member_result = AsyncMock()
        member_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [org_result, member_result]

        with pytest.raises(ValueError, match="Not authorized"):
            await developer_service.invite_member(
                mock_db, sample_organization.id, invite_data, inviter_id
            )

    @pytest.mark.asyncio
    async def test_accept_invitation_success(
        self, developer_service, mock_db
    ):
        """Test successful invitation acceptance."""
        user_id = uuid4()
        invitation_token = "valid_token_123"

        # Mock pending member with invitation
        pending_member = MagicMock(spec=DeveloperMember)
        pending_member.id = uuid4()
        pending_member.invitation_token = invitation_token
        pending_member.invitation_expires_at = datetime.utcnow() + timedelta(days=1)
        pending_member.user_id = None
        pending_member.role = DeveloperRole.DEVELOPER

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = pending_member
        mock_db.execute.return_value = mock_result

        result = await developer_service.accept_invitation(
            mock_db, invitation_token, user_id
        )

        assert pending_member.user_id == user_id
        assert pending_member.joined_at is not None
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_accept_invitation_expired(
        self, developer_service, mock_db
    ):
        """Test invitation acceptance fails when expired."""
        user_id = uuid4()
        invitation_token = "expired_token"

        # Mock expired invitation
        expired_member = MagicMock(spec=DeveloperMember)
        expired_member.invitation_token = invitation_token
        expired_member.invitation_expires_at = datetime.utcnow() - timedelta(days=1)
        expired_member.user_id = None

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = expired_member
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="expired"):
            await developer_service.accept_invitation(
                mock_db, invitation_token, user_id
            )


class TestDeveloperServiceSandbox:
    """Tests for sandbox environment management."""

    @pytest.mark.asyncio
    async def test_create_sandbox_success(
        self, developer_service, mock_db, sample_organization, sample_member
    ):
        """Test successful sandbox creation."""
        user_id = sample_member.user_id
        sandbox_data = SandboxCreate(
            name="Test Sandbox",
            description="Sandbox for testing"
        )

        # Mock organization and member lookups
        org_result = AsyncMock()
        org_result.scalar_one_or_none.return_value = sample_organization

        member_result = AsyncMock()
        member_result.scalar_one_or_none.return_value = sample_member

        # Mock sandbox count check (under limit)
        count_result = AsyncMock()
        count_result.scalar.return_value = 2

        mock_db.execute.side_effect = [org_result, member_result, count_result]

        result = await developer_service.create_sandbox(
            mock_db, sample_organization.id, sandbox_data, user_id
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_create_sandbox_limit_exceeded(
        self, developer_service, mock_db, sample_organization, sample_member
    ):
        """Test sandbox creation fails when limit exceeded."""
        user_id = sample_member.user_id
        sandbox_data = SandboxCreate(
            name="Test Sandbox",
            description="Sandbox for testing"
        )

        # Mock organization and member lookups
        org_result = AsyncMock()
        org_result.scalar_one_or_none.return_value = sample_organization

        member_result = AsyncMock()
        member_result.scalar_one_or_none.return_value = sample_member

        # Mock sandbox count at limit
        count_result = AsyncMock()
        count_result.scalar.return_value = 5  # At limit

        mock_db.execute.side_effect = [org_result, member_result, count_result]

        with pytest.raises(ValueError, match="limit"):
            await developer_service.create_sandbox(
                mock_db, sample_organization.id, sandbox_data, user_id
            )

    @pytest.mark.asyncio
    async def test_reset_sandbox_success(
        self, developer_service, mock_db, sample_organization, sample_member
    ):
        """Test successful sandbox reset."""
        user_id = sample_member.user_id
        sandbox_id = uuid4()

        # Mock sandbox
        sandbox = MagicMock(spec=SandboxEnvironment)
        sandbox.id = sandbox_id
        sandbox.developer_organization_id = sample_organization.id
        sandbox.status = SandboxStatus.ACTIVE
        sandbox.api_key_hash = "old_hash"

        # Mock lookups
        org_result = AsyncMock()
        org_result.scalar_one_or_none.return_value = sample_organization

        member_result = AsyncMock()
        member_result.scalar_one_or_none.return_value = sample_member

        sandbox_result = AsyncMock()
        sandbox_result.scalar_one_or_none.return_value = sandbox

        mock_db.execute.side_effect = [org_result, member_result, sandbox_result]

        result = await developer_service.reset_sandbox(
            mock_db, sample_organization.id, sandbox_id, user_id
        )

        assert sandbox.api_key_hash != "old_hash"
        assert mock_db.commit.called


class TestDeveloperServiceDashboard:
    """Tests for developer dashboard."""

    @pytest.mark.asyncio
    async def test_get_dashboard_success(
        self, developer_service, mock_db, sample_organization, sample_member
    ):
        """Test successful dashboard retrieval."""
        user_id = sample_member.user_id

        # Setup mock organization with relationships
        sample_organization.members = [sample_member]
        sample_organization.applications = []
        sample_organization.sandboxes = []

        # Mock lookups
        org_result = AsyncMock()
        org_result.scalar_one_or_none.return_value = sample_organization

        member_result = AsyncMock()
        member_result.scalar_one_or_none.return_value = sample_member

        mock_db.execute.side_effect = [org_result, member_result]

        result = await developer_service.get_dashboard(
            mock_db, sample_organization.id, user_id
        )

        assert result is not None
        assert result.organization_id == sample_organization.id

    @pytest.mark.asyncio
    async def test_get_dashboard_not_authorized(
        self, developer_service, mock_db, sample_organization
    ):
        """Test dashboard access denied for non-members."""
        user_id = uuid4()

        # Mock organization lookup
        org_result = AsyncMock()
        org_result.scalar_one_or_none.return_value = sample_organization

        # Mock no member found
        member_result = AsyncMock()
        member_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [org_result, member_result]

        with pytest.raises(ValueError, match="Not authorized"):
            await developer_service.get_dashboard(
                mock_db, sample_organization.id, user_id
            )

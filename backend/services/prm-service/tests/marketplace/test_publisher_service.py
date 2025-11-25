"""
Unit tests for PublisherService
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from modules.marketplace.services.publisher_service import PublisherService
from modules.marketplace.models import (
    MarketplaceApp,
    AppVersion,
    AppCategory,
    AppStatus,
    DeveloperOrganization,
    DeveloperMember,
    DeveloperRole,
    DeveloperStatus,
    OAuthApplication,
)
from modules.marketplace.schemas import (
    AppSubmissionCreate,
    AppVersionCreate,
    SubmissionReviewCreate,
    ReviewDecision,
    VersionRollout,
)


@pytest.fixture
def publisher_service():
    return PublisherService()


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def sample_organization():
    org = MagicMock(spec=DeveloperOrganization)
    org.id = uuid4()
    org.name = "Test Developer Org"
    org.status = DeveloperStatus.APPROVED
    return org


@pytest.fixture
def sample_member():
    member = MagicMock(spec=DeveloperMember)
    member.id = uuid4()
    member.developer_organization_id = uuid4()
    member.user_id = uuid4()
    member.role = DeveloperRole.OWNER
    return member


@pytest.fixture
def sample_oauth_app():
    app = MagicMock(spec=OAuthApplication)
    app.id = uuid4()
    app.developer_organization_id = uuid4()
    return app


@pytest.fixture
def sample_marketplace_app():
    app = MagicMock(spec=MarketplaceApp)
    app.id = uuid4()
    app.oauth_application_id = uuid4()
    app.developer_organization_id = uuid4()
    app.name = "Test Healthcare App"
    app.slug = "test-healthcare-app"
    app.description = "A comprehensive healthcare integration app for clinics."
    app.short_description = "Healthcare integration"
    app.icon_url = "https://cdn.test.com/icon.png"
    app.privacy_policy_url = "https://test.com/privacy"
    app.support_email = "support@test.com"
    app.category = AppCategory.EHR_INTEGRATION
    app.status = AppStatus.DRAFT
    app.versions = []
    app.install_count = 0
    app.average_rating = Decimal("0")
    app.review_count = 0
    return app


@pytest.fixture
def sample_version():
    version = MagicMock(spec=AppVersion)
    version.id = uuid4()
    version.marketplace_app_id = uuid4()
    version.version = "1.0.0"
    version.release_notes = "Initial release"
    version.status = AppStatus.DRAFT
    version.is_current = True
    version.rollout_percentage = 100
    version.submitted_at = datetime.utcnow()
    version.published_at = None
    return version


class TestAppSubmission:
    """Tests for app submission."""

    @pytest.mark.asyncio
    async def test_create_submission_success(
        self, publisher_service, mock_db, sample_organization, sample_member, sample_oauth_app
    ):
        """Test successful app submission creation."""
        organization_id = sample_organization.id
        user_id = sample_member.user_id
        sample_oauth_app.developer_organization_id = organization_id

        submission_data = AppSubmissionCreate(
            oauth_application_id=sample_oauth_app.id,
            name="New Healthcare App",
            description="A comprehensive healthcare app for patient management and clinical workflows.",
            short_description="Patient management app",
            icon_url="https://cdn.test.com/icon.png",
            category=AppCategory.PRACTICE_MANAGEMENT,
            support_email="support@newapp.com",
            privacy_policy_url="https://newapp.com/privacy",
            version="1.0.0",
            release_notes="Initial release with core features"
        )

        # Mock member lookup
        member_result = AsyncMock()
        member_result.scalar_one_or_none.return_value = sample_member

        # Mock org lookup
        org_result = AsyncMock()
        org_result.scalar_one_or_none.return_value = sample_organization

        # Mock OAuth app lookup
        oauth_result = AsyncMock()
        oauth_result.scalar_one_or_none.return_value = sample_oauth_app

        # Mock no existing slug
        slug_result = AsyncMock()
        slug_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [member_result, org_result, oauth_result, org_result, slug_result]

        result = await publisher_service.create_submission(
            mock_db, organization_id, user_id, submission_data
        )

        assert result is not None
        assert mock_db.add.called

    @pytest.mark.asyncio
    async def test_submit_for_review_success(
        self, publisher_service, mock_db, sample_marketplace_app, sample_organization, sample_member
    ):
        """Test successful submission for review."""
        organization_id = sample_organization.id
        user_id = sample_member.user_id
        sample_marketplace_app.developer_organization_id = organization_id

        # Setup versions
        version = MagicMock(spec=AppVersion)
        version.is_current = True
        version.status = AppStatus.DRAFT
        sample_marketplace_app.versions = [version]

        # Mock lookups
        member_result = AsyncMock()
        member_result.scalar_one_or_none.return_value = sample_member

        org_result = AsyncMock()
        org_result.scalar_one_or_none.return_value = sample_organization

        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_marketplace_app

        mock_db.execute.side_effect = [member_result, org_result, app_result]

        result = await publisher_service.submit_for_review(
            mock_db, sample_marketplace_app.id, organization_id, user_id
        )

        assert result is not None
        assert sample_marketplace_app.status == AppStatus.PENDING_REVIEW

    @pytest.mark.asyncio
    async def test_submit_for_review_validation_fails(
        self, publisher_service, mock_db, sample_organization, sample_member
    ):
        """Test submission fails validation."""
        organization_id = sample_organization.id
        user_id = sample_member.user_id

        # Create invalid app (missing required fields)
        invalid_app = MagicMock(spec=MarketplaceApp)
        invalid_app.id = uuid4()
        invalid_app.developer_organization_id = organization_id
        invalid_app.name = "X"  # Too short
        invalid_app.description = "Short"  # Too short
        invalid_app.short_description = None
        invalid_app.icon_url = None
        invalid_app.privacy_policy_url = None
        invalid_app.support_email = None
        invalid_app.status = AppStatus.DRAFT
        invalid_app.versions = []

        # Mock lookups
        member_result = AsyncMock()
        member_result.scalar_one_or_none.return_value = sample_member

        org_result = AsyncMock()
        org_result.scalar_one_or_none.return_value = sample_organization

        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = invalid_app

        mock_db.execute.side_effect = [member_result, org_result, app_result]

        with pytest.raises(ValueError, match="validation failed"):
            await publisher_service.submit_for_review(
                mock_db, invalid_app.id, organization_id, user_id
            )


class TestSubmissionReview:
    """Tests for submission review process."""

    @pytest.mark.asyncio
    async def test_review_submission_approve(
        self, publisher_service, mock_db, sample_marketplace_app, sample_version
    ):
        """Test approving a submission."""
        reviewer_id = uuid4()
        sample_marketplace_app.status = AppStatus.PENDING_REVIEW
        sample_version.status = AppStatus.PENDING_REVIEW
        sample_marketplace_app.versions = [sample_version]

        decision = SubmissionReviewCreate(
            decision=ReviewDecision.APPROVED,
            review_notes="App meets all requirements."
        )

        # Mock app lookup
        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_marketplace_app
        mock_db.execute.return_value = app_result

        result = await publisher_service.review_submission(
            mock_db, sample_marketplace_app.id, reviewer_id, decision
        )

        assert result is not None
        assert sample_marketplace_app.status == AppStatus.PUBLISHED

    @pytest.mark.asyncio
    async def test_review_submission_reject(
        self, publisher_service, mock_db, sample_marketplace_app, sample_version
    ):
        """Test rejecting a submission."""
        reviewer_id = uuid4()
        sample_marketplace_app.status = AppStatus.PENDING_REVIEW
        sample_version.status = AppStatus.PENDING_REVIEW
        sample_marketplace_app.versions = [sample_version]

        decision = SubmissionReviewCreate(
            decision=ReviewDecision.REJECTED,
            review_notes="Missing security documentation."
        )

        # Mock app lookup
        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_marketplace_app
        mock_db.execute.return_value = app_result

        result = await publisher_service.review_submission(
            mock_db, sample_marketplace_app.id, reviewer_id, decision
        )

        assert result is not None
        assert sample_marketplace_app.status == AppStatus.REJECTED


class TestVersionManagement:
    """Tests for version management."""

    @pytest.mark.asyncio
    async def test_create_version_success(
        self, publisher_service, mock_db, sample_marketplace_app, sample_organization, sample_member
    ):
        """Test successful version creation."""
        organization_id = sample_organization.id
        user_id = sample_member.user_id
        sample_marketplace_app.developer_organization_id = organization_id
        sample_marketplace_app.versions = []

        version_data = AppVersionCreate(
            version="2.0.0",
            release_notes="Major update with new features",
            breaking_changes=["API v1 deprecated"],
            deprecations=["Old endpoint /v1/patients"]
        )

        # Mock lookups
        member_result = AsyncMock()
        member_result.scalar_one_or_none.return_value = sample_member

        org_result = AsyncMock()
        org_result.scalar_one_or_none.return_value = sample_organization

        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_marketplace_app

        mock_db.execute.side_effect = [member_result, org_result, app_result]

        result = await publisher_service.create_version(
            mock_db, sample_marketplace_app.id, organization_id, user_id, version_data
        )

        assert result is not None
        assert mock_db.add.called

    @pytest.mark.asyncio
    async def test_create_version_invalid_semver(
        self, publisher_service, mock_db, sample_marketplace_app, sample_organization, sample_member
    ):
        """Test version creation fails with invalid semver."""
        organization_id = sample_organization.id
        user_id = sample_member.user_id
        sample_marketplace_app.developer_organization_id = organization_id

        version_data = AppVersionCreate(
            version="invalid.version",  # Invalid semver
            release_notes="Test"
        )

        # Mock lookups
        member_result = AsyncMock()
        member_result.scalar_one_or_none.return_value = sample_member

        org_result = AsyncMock()
        org_result.scalar_one_or_none.return_value = sample_organization

        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_marketplace_app

        mock_db.execute.side_effect = [member_result, org_result, app_result]

        with pytest.raises(ValueError, match="Invalid version"):
            await publisher_service.create_version(
                mock_db, sample_marketplace_app.id, organization_id, user_id, version_data
            )

    @pytest.mark.asyncio
    async def test_publish_version_full_rollout(
        self, publisher_service, mock_db, sample_marketplace_app, sample_version
    ):
        """Test publishing version with full rollout."""
        reviewer_id = uuid4()
        sample_version.status = AppStatus.PENDING_REVIEW
        sample_marketplace_app.versions = [sample_version]

        # Mock lookups
        version_result = AsyncMock()
        version_result.scalar_one_or_none.return_value = sample_version

        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_marketplace_app

        mock_db.execute.side_effect = [version_result, app_result]

        result = await publisher_service.publish_version(
            mock_db, sample_marketplace_app.id, sample_version.id, reviewer_id
        )

        assert result is not None
        assert sample_version.status == AppStatus.PUBLISHED
        assert sample_version.is_current is True

    @pytest.mark.asyncio
    async def test_publish_version_staged_rollout(
        self, publisher_service, mock_db, sample_marketplace_app, sample_version
    ):
        """Test publishing version with staged rollout."""
        reviewer_id = uuid4()
        sample_version.status = AppStatus.PENDING_REVIEW
        sample_marketplace_app.versions = [sample_version]

        rollout = VersionRollout(initial_percentage=25)

        # Mock lookups
        version_result = AsyncMock()
        version_result.scalar_one_or_none.return_value = sample_version

        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_marketplace_app

        mock_db.execute.side_effect = [version_result, app_result]

        result = await publisher_service.publish_version(
            mock_db, sample_marketplace_app.id, sample_version.id, reviewer_id, rollout
        )

        assert result is not None
        assert sample_version.rollout_percentage == 25
        # Should not be current until 100%
        assert sample_version.is_current is False

    @pytest.mark.asyncio
    async def test_update_rollout_to_full(
        self, publisher_service, mock_db, sample_marketplace_app, sample_version, sample_organization, sample_member
    ):
        """Test updating rollout to 100%."""
        organization_id = sample_organization.id
        user_id = sample_member.user_id
        sample_marketplace_app.developer_organization_id = organization_id
        sample_version.status = AppStatus.PUBLISHED
        sample_version.rollout_percentage = 50
        sample_version.is_current = False
        sample_marketplace_app.versions = [sample_version]

        # Mock lookups
        member_result = AsyncMock()
        member_result.scalar_one_or_none.return_value = sample_member

        org_result = AsyncMock()
        org_result.scalar_one_or_none.return_value = sample_organization

        version_result = AsyncMock()
        version_result.scalar_one_or_none.return_value = sample_version

        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_marketplace_app

        mock_db.execute.side_effect = [member_result, org_result, version_result, app_result]

        result = await publisher_service.update_rollout(
            mock_db, sample_marketplace_app.id, sample_version.id, organization_id, user_id, 100
        )

        assert result is not None
        assert sample_version.rollout_percentage == 100
        assert sample_version.is_current is True


class TestVersionDeprecation:
    """Tests for version deprecation."""

    @pytest.mark.asyncio
    async def test_deprecate_version_success(
        self, publisher_service, mock_db, sample_marketplace_app, sample_version, sample_organization, sample_member
    ):
        """Test successful version deprecation."""
        organization_id = sample_organization.id
        user_id = sample_member.user_id
        sample_marketplace_app.developer_organization_id = organization_id
        sample_version.status = AppStatus.PUBLISHED
        sample_version.is_current = False
        sample_marketplace_app.versions = [sample_version]

        sunset_date = datetime.utcnow() + timedelta(days=90)

        # Mock lookups
        member_result = AsyncMock()
        member_result.scalar_one_or_none.return_value = sample_member

        org_result = AsyncMock()
        org_result.scalar_one_or_none.return_value = sample_organization

        version_result = AsyncMock()
        version_result.scalar_one_or_none.return_value = sample_version

        mock_db.execute.side_effect = [member_result, org_result, version_result]

        result = await publisher_service.deprecate_version(
            mock_db, sample_marketplace_app.id, sample_version.id,
            organization_id, user_id,
            "This version has known security issues. Please upgrade.",
            sunset_date
        )

        assert result is not None
        assert sample_version.status == AppStatus.DEPRECATED


class TestPublisherDashboard:
    """Tests for publisher dashboard."""

    @pytest.mark.asyncio
    async def test_get_publisher_dashboard_success(
        self, publisher_service, mock_db, sample_marketplace_app, sample_organization, sample_member
    ):
        """Test successful dashboard retrieval."""
        organization_id = sample_organization.id
        user_id = sample_member.user_id

        # Setup apps
        sample_marketplace_app.developer_organization_id = organization_id
        sample_marketplace_app.status = AppStatus.PUBLISHED
        sample_marketplace_app.versions = []

        # Mock lookups
        member_result = AsyncMock()
        member_result.scalar_one_or_none.return_value = sample_member

        org_result = AsyncMock()
        org_result.scalar_one_or_none.return_value = sample_organization

        apps_result = MagicMock()
        apps_result.scalars.return_value.all.return_value = [sample_marketplace_app]

        mock_db.execute.side_effect = [member_result, org_result, apps_result]

        result = await publisher_service.get_publisher_dashboard(
            mock_db, organization_id, user_id
        )

        assert result is not None
        assert result.total_apps >= 1
        assert result.published_apps >= 0


class TestUnpublishApp:
    """Tests for app unpublishing."""

    @pytest.mark.asyncio
    async def test_unpublish_app_success(
        self, publisher_service, mock_db, sample_marketplace_app, sample_organization, sample_member
    ):
        """Test successful app unpublishing."""
        organization_id = sample_organization.id
        user_id = sample_member.user_id
        sample_marketplace_app.developer_organization_id = organization_id
        sample_marketplace_app.status = AppStatus.PUBLISHED

        # Mock lookups
        member_result = AsyncMock()
        member_result.scalar_one_or_none.return_value = sample_member

        org_result = AsyncMock()
        org_result.scalar_one_or_none.return_value = sample_organization

        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_marketplace_app

        mock_db.execute.side_effect = [member_result, org_result, app_result]

        result = await publisher_service.unpublish_app(
            mock_db, sample_marketplace_app.id, organization_id, user_id,
            "Discontinuing product support"
        )

        assert result is not None
        assert sample_marketplace_app.status == AppStatus.SUSPENDED

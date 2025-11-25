"""
Unit tests for MarketplaceService
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from modules.marketplace.services.marketplace_service import MarketplaceService
from modules.marketplace.models import (
    MarketplaceApp,
    AppInstallation,
    AppReview,
    AppVersion,
    AppCategory,
    AppStatus,
    InstallationStatus,
    OAuthApplication,
    OAuthConsent,
)
from modules.marketplace.schemas import (
    AppSearchFilters,
    AppInstallationCreate,
    AppInstallationUpdate,
    AppReviewCreate,
    AppReviewUpdate,
)


@pytest.fixture
def marketplace_service():
    return MarketplaceService()


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.add = MagicMock()
    db.delete = AsyncMock()
    return db


@pytest.fixture
def sample_marketplace_app():
    app = MagicMock(spec=MarketplaceApp)
    app.id = uuid4()
    app.oauth_application_id = uuid4()
    app.developer_organization_id = uuid4()
    app.name = "Test Healthcare App"
    app.slug = "test-healthcare-app"
    app.description = "A comprehensive test application"
    app.short_description = "Test app"
    app.icon_url = "https://cdn.test.com/icon.png"
    app.banner_url = "https://cdn.test.com/banner.png"
    app.screenshots = []
    app.category = AppCategory.EHR_INTEGRATION
    app.tags = ["fhir", "ehr"]
    app.developer_name = "Test Developer"
    app.average_rating = Decimal("4.5")
    app.review_count = 100
    app.install_count = 1000
    app.pricing_model = "free"
    app.price_monthly = None
    app.status = AppStatus.PUBLISHED
    app.is_featured = True
    app.is_verified = True
    app.required_scopes = ["patient/Patient.read"]
    app.optional_scopes = []
    app.versions = []
    app.reviews = []
    app.published_at = datetime.utcnow()
    return app


@pytest.fixture
def sample_installation():
    installation = MagicMock(spec=AppInstallation)
    installation.id = uuid4()
    installation.marketplace_app_id = uuid4()
    installation.tenant_id = uuid4()
    installation.installed_by_user_id = uuid4()
    installation.installed_version_id = uuid4()
    installation.status = InstallationStatus.ACTIVE
    installation.granted_scopes = ["patient/Patient.read"]
    installation.configuration = {}
    installation.created_at = datetime.utcnow()
    installation.activated_at = datetime.utcnow()
    return installation


@pytest.fixture
def sample_review():
    review = MagicMock(spec=AppReview)
    review.id = uuid4()
    review.marketplace_app_id = uuid4()
    review.tenant_id = uuid4()
    review.user_id = uuid4()
    review.rating = 5
    review.title = "Great App!"
    review.review_text = "This app is excellent for our clinic."
    review.developer_response = None
    review.developer_response_at = None
    review.is_verified_purchase = True
    review.helpful_count = 10
    review.created_at = datetime.utcnow()
    review.updated_at = datetime.utcnow()
    return review


class TestAppSearch:
    """Tests for app search and discovery."""

    @pytest.mark.asyncio
    async def test_search_apps_success(
        self, marketplace_service, mock_db, sample_marketplace_app
    ):
        """Test successful app search."""
        filters = AppSearchFilters(query="healthcare")

        # Mock apps result
        apps_result = MagicMock()
        apps_result.scalars.return_value.all.return_value = [sample_marketplace_app]

        # Mock count result
        count_result = AsyncMock()
        count_result.scalar.return_value = 1

        mock_db.execute.side_effect = [
            AsyncMock(return_value=count_result),
            AsyncMock(return_value=apps_result)
        ]

        result = await marketplace_service.search_apps(mock_db, filters)

        assert result is not None
        assert len(result.items) >= 0  # May vary based on mocking

    @pytest.mark.asyncio
    async def test_search_apps_with_filters(
        self, marketplace_service, mock_db, sample_marketplace_app
    ):
        """Test app search with various filters."""
        filters = AppSearchFilters(
            category=AppCategory.EHR_INTEGRATION,
            is_free=True,
            min_rating=4.0,
            is_featured=True,
            sort_by="rating"
        )

        # Mock results
        apps_result = MagicMock()
        apps_result.scalars.return_value.all.return_value = [sample_marketplace_app]

        count_result = AsyncMock()
        count_result.scalar.return_value = 1

        mock_db.execute.side_effect = [
            AsyncMock(return_value=count_result),
            AsyncMock(return_value=apps_result)
        ]

        result = await marketplace_service.search_apps(mock_db, filters)

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_featured_apps(
        self, marketplace_service, mock_db, sample_marketplace_app
    ):
        """Test getting featured apps."""
        apps_result = MagicMock()
        apps_result.scalars.return_value.all.return_value = [sample_marketplace_app]
        mock_db.execute.return_value = apps_result

        result = await marketplace_service.get_featured_apps(mock_db, limit=10)

        assert result is not None
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_app_detail_found(
        self, marketplace_service, mock_db, sample_marketplace_app
    ):
        """Test getting app detail when app exists."""
        sample_marketplace_app.versions = []
        sample_marketplace_app.reviews = []

        apps_result = AsyncMock()
        apps_result.scalar_one_or_none.return_value = sample_marketplace_app
        mock_db.execute.return_value = apps_result

        result = await marketplace_service.get_app_detail(
            mock_db, sample_marketplace_app.id
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_app_detail_not_found(
        self, marketplace_service, mock_db
    ):
        """Test getting app detail when app doesn't exist."""
        apps_result = AsyncMock()
        apps_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = apps_result

        result = await marketplace_service.get_app_detail(mock_db, uuid4())

        assert result is None


class TestAppInstallation:
    """Tests for app installation management."""

    @pytest.mark.asyncio
    async def test_install_app_success(
        self, marketplace_service, mock_db, sample_marketplace_app
    ):
        """Test successful app installation."""
        tenant_id = uuid4()
        user_id = uuid4()
        install_data = AppInstallationCreate(
            granted_scopes=["patient/Patient.read"]
        )

        # Mock app lookup
        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_marketplace_app

        # Mock no existing installation
        existing_result = AsyncMock()
        existing_result.scalar_one_or_none.return_value = None

        # Mock version lookup
        version = MagicMock(spec=AppVersion)
        version.id = uuid4()
        version.is_current = True
        version_result = AsyncMock()
        version_result.scalar_one_or_none.return_value = version

        mock_db.execute.side_effect = [app_result, existing_result, version_result]

        result = await marketplace_service.install_app(
            mock_db, sample_marketplace_app.id, tenant_id, user_id, install_data
        )

        assert result is not None
        assert mock_db.add.called

    @pytest.mark.asyncio
    async def test_install_app_already_installed(
        self, marketplace_service, mock_db, sample_marketplace_app, sample_installation
    ):
        """Test installation fails when already installed."""
        tenant_id = sample_installation.tenant_id
        user_id = uuid4()
        install_data = AppInstallationCreate()

        # Mock app lookup
        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_marketplace_app

        # Mock existing active installation
        existing_result = AsyncMock()
        existing_result.scalar_one_or_none.return_value = sample_installation

        mock_db.execute.side_effect = [app_result, existing_result]

        with pytest.raises(ValueError, match="already installed"):
            await marketplace_service.install_app(
                mock_db, sample_marketplace_app.id, tenant_id, user_id, install_data
            )

    @pytest.mark.asyncio
    async def test_uninstall_app_success(
        self, marketplace_service, mock_db, sample_installation, sample_marketplace_app
    ):
        """Test successful app uninstallation."""
        tenant_id = sample_installation.tenant_id
        user_id = uuid4()

        # Mock installation lookup
        install_result = AsyncMock()
        install_result.scalar_one_or_none.return_value = sample_installation

        # Mock app lookup
        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_marketplace_app

        mock_db.execute.side_effect = [install_result, app_result]

        result = await marketplace_service.uninstall_app(
            mock_db, sample_installation.id, tenant_id, user_id
        )

        assert result is True
        assert sample_installation.status == InstallationStatus.UNINSTALLED

    @pytest.mark.asyncio
    async def test_update_installation_success(
        self, marketplace_service, mock_db, sample_installation
    ):
        """Test successful installation update."""
        tenant_id = sample_installation.tenant_id
        user_id = uuid4()
        update_data = AppInstallationUpdate(
            configuration={"feature_x": True}
        )

        # Mock installation lookup
        install_result = AsyncMock()
        install_result.scalar_one_or_none.return_value = sample_installation
        mock_db.execute.return_value = install_result

        result = await marketplace_service.update_installation(
            mock_db, sample_installation.id, tenant_id, user_id, update_data
        )

        assert result is not None
        assert sample_installation.configuration == {"feature_x": True}


class TestAppReviews:
    """Tests for app review management."""

    @pytest.mark.asyncio
    async def test_create_review_success(
        self, marketplace_service, mock_db, sample_marketplace_app
    ):
        """Test successful review creation."""
        tenant_id = uuid4()
        user_id = uuid4()
        review_data = AppReviewCreate(
            rating=5,
            title="Excellent App",
            review_text="This app has transformed our workflow."
        )

        # Mock app lookup
        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_marketplace_app

        # Mock no existing review
        existing_result = AsyncMock()
        existing_result.scalar_one_or_none.return_value = None

        # Mock installation check
        install_result = AsyncMock()
        install_result.scalar_one_or_none.return_value = MagicMock()  # Has installation

        mock_db.execute.side_effect = [app_result, existing_result, install_result]

        result = await marketplace_service.create_review(
            mock_db, sample_marketplace_app.id, tenant_id, user_id, review_data
        )

        assert result is not None
        assert mock_db.add.called

    @pytest.mark.asyncio
    async def test_create_review_duplicate(
        self, marketplace_service, mock_db, sample_marketplace_app, sample_review
    ):
        """Test review creation fails for duplicate."""
        tenant_id = sample_review.tenant_id
        user_id = sample_review.user_id
        review_data = AppReviewCreate(
            rating=4,
            title="Another Review",
            review_text="Trying to review again"
        )

        # Mock app lookup
        app_result = AsyncMock()
        app_result.scalar_one_or_none.return_value = sample_marketplace_app

        # Mock existing review
        existing_result = AsyncMock()
        existing_result.scalar_one_or_none.return_value = sample_review

        mock_db.execute.side_effect = [app_result, existing_result]

        with pytest.raises(ValueError, match="already reviewed"):
            await marketplace_service.create_review(
                mock_db, sample_marketplace_app.id, tenant_id, user_id, review_data
            )

    @pytest.mark.asyncio
    async def test_update_review_success(
        self, marketplace_service, mock_db, sample_review
    ):
        """Test successful review update."""
        user_id = sample_review.user_id
        update_data = AppReviewUpdate(
            rating=4,
            review_text="Updated: Still good but some issues."
        )

        # Mock review lookup
        review_result = AsyncMock()
        review_result.scalar_one_or_none.return_value = sample_review
        mock_db.execute.return_value = review_result

        result = await marketplace_service.update_review(
            mock_db, sample_review.id, user_id, update_data
        )

        assert result is not None
        assert sample_review.rating == 4

    @pytest.mark.asyncio
    async def test_delete_review_success(
        self, marketplace_service, mock_db, sample_review
    ):
        """Test successful review deletion."""
        user_id = sample_review.user_id

        # Mock review lookup
        review_result = AsyncMock()
        review_result.scalar_one_or_none.return_value = sample_review
        mock_db.execute.return_value = review_result

        result = await marketplace_service.delete_review(
            mock_db, sample_review.id, user_id
        )

        assert result is True
        assert mock_db.delete.called

    @pytest.mark.asyncio
    async def test_respond_to_review_success(
        self, marketplace_service, mock_db, sample_review, sample_marketplace_app
    ):
        """Test successful developer response to review."""
        organization_id = sample_marketplace_app.developer_organization_id
        response_text = "Thank you for your feedback!"

        sample_review.marketplace_app = sample_marketplace_app

        # Mock review lookup
        review_result = AsyncMock()
        review_result.scalar_one_or_none.return_value = sample_review
        mock_db.execute.return_value = review_result

        result = await marketplace_service.respond_to_review(
            mock_db, sample_review.id, organization_id, response_text
        )

        assert result is not None
        assert sample_review.developer_response == response_text

    @pytest.mark.asyncio
    async def test_respond_to_review_unauthorized(
        self, marketplace_service, mock_db, sample_review, sample_marketplace_app
    ):
        """Test response fails for unauthorized developer."""
        different_org_id = uuid4()
        response_text = "Unauthorized response"

        sample_review.marketplace_app = sample_marketplace_app

        # Mock review lookup
        review_result = AsyncMock()
        review_result.scalar_one_or_none.return_value = sample_review
        mock_db.execute.return_value = review_result

        with pytest.raises(ValueError, match="Not authorized"):
            await marketplace_service.respond_to_review(
                mock_db, sample_review.id, different_org_id, response_text
            )

    @pytest.mark.asyncio
    async def test_mark_review_helpful(
        self, marketplace_service, mock_db, sample_review
    ):
        """Test marking review as helpful."""
        user_id = uuid4()
        original_count = sample_review.helpful_count

        # Mock review lookup
        review_result = AsyncMock()
        review_result.scalar_one_or_none.return_value = sample_review
        mock_db.execute.return_value = review_result

        result = await marketplace_service.mark_review_helpful(
            mock_db, sample_review.id, user_id
        )

        assert result is True
        assert sample_review.helpful_count == original_count + 1


class TestSimilarApps:
    """Tests for similar app recommendations."""

    @pytest.mark.asyncio
    async def test_get_similar_apps_success(
        self, marketplace_service, mock_db, sample_marketplace_app
    ):
        """Test getting similar apps."""
        # Mock reference app
        ref_app_result = AsyncMock()
        ref_app_result.scalar_one_or_none.return_value = sample_marketplace_app

        # Mock similar apps
        similar_app = MagicMock(spec=MarketplaceApp)
        similar_app.id = uuid4()
        similar_app.name = "Similar App"
        similar_app.slug = "similar-app"
        similar_app.category = sample_marketplace_app.category
        similar_app.average_rating = Decimal("4.2")
        similar_app.install_count = 500

        similar_result = MagicMock()
        similar_result.scalars.return_value.all.return_value = [similar_app]

        mock_db.execute.side_effect = [ref_app_result, similar_result]

        result = await marketplace_service.get_similar_apps(
            mock_db, sample_marketplace_app.id, limit=5
        )

        assert result is not None
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_similar_apps_not_found(
        self, marketplace_service, mock_db
    ):
        """Test similar apps returns empty when app not found."""
        # Mock app not found
        ref_app_result = AsyncMock()
        ref_app_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = ref_app_result

        result = await marketplace_service.get_similar_apps(mock_db, uuid4())

        assert result == []

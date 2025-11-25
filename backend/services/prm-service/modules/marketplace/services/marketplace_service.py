"""
Marketplace Service
Handles app catalog, installations, reviews, and discovery.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import (
    AppCategory,
    AppInstallation,
    AppReview,
    AppStatus,
    AppVersion,
    DeveloperAuditLog,
    DeveloperOrganization,
    InstallationStatus,
    MarketplaceApp,
    OAuthApplication,
    OAuthConsent,
)
from ..schemas import (
    AppCatalogResponse,
    AppDetailResponse,
    AppInstallationCreate,
    AppInstallationResponse,
    AppInstallationUpdate,
    AppReviewCreate,
    AppReviewResponse,
    AppReviewUpdate,
    AppSearchFilters,
    ConsentCreate,
    FeaturedAppResponse,
    InstalledAppResponse,
    PaginatedResponse,
)


class MarketplaceService:
    """
    Marketplace Service providing app catalog, installations,
    reviews, and discovery features.
    """

    async def search_apps(
        self,
        db: AsyncSession,
        filters: AppSearchFilters,
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedResponse[AppCatalogResponse]:
        """
        Search and filter marketplace apps.
        """
        query = select(MarketplaceApp).where(
            MarketplaceApp.status == AppStatus.PUBLISHED
        )

        # Apply filters
        if filters.query:
            search_term = f"%{filters.query}%"
            query = query.where(
                or_(
                    MarketplaceApp.name.ilike(search_term),
                    MarketplaceApp.description.ilike(search_term),
                    MarketplaceApp.short_description.ilike(search_term)
                )
            )

        if filters.category:
            query = query.where(MarketplaceApp.category == filters.category)

        if filters.developer_id:
            query = query.where(
                MarketplaceApp.developer_organization_id == filters.developer_id
            )

        if filters.is_free is not None:
            if filters.is_free:
                query = query.where(
                    or_(
                        MarketplaceApp.pricing_model == "free",
                        MarketplaceApp.price_monthly.is_(None),
                        MarketplaceApp.price_monthly == 0
                    )
                )
            else:
                query = query.where(
                    and_(
                        MarketplaceApp.pricing_model != "free",
                        MarketplaceApp.price_monthly > 0
                    )
                )

        if filters.min_rating:
            query = query.where(
                MarketplaceApp.average_rating >= filters.min_rating
            )

        if filters.is_featured:
            query = query.where(MarketplaceApp.is_featured == True)

        if filters.smart_on_fhir_only:
            # Join with OAuth application to check SMART support
            query = query.join(
                OAuthApplication,
                MarketplaceApp.oauth_application_id == OAuthApplication.id
            ).where(OAuthApplication.is_smart_on_fhir == True)

        # Sorting
        sort_map = {
            "popularity": MarketplaceApp.install_count.desc(),
            "rating": MarketplaceApp.average_rating.desc(),
            "newest": MarketplaceApp.published_at.desc(),
            "name": MarketplaceApp.name.asc(),
            "price_low": MarketplaceApp.price_monthly.asc().nullsfirst(),
            "price_high": MarketplaceApp.price_monthly.desc().nullslast()
        }
        sort_order = sort_map.get(
            filters.sort_by or "popularity",
            MarketplaceApp.install_count.desc()
        )
        query = query.order_by(sort_order)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await db.execute(query)
        apps = result.scalars().all()

        # Transform to response
        items = [
            AppCatalogResponse(
                id=app.id,
                name=app.name,
                slug=app.slug,
                short_description=app.short_description,
                icon_url=app.icon_url,
                category=app.category,
                developer_name=app.developer_name,
                average_rating=float(app.average_rating or 0),
                review_count=app.review_count or 0,
                install_count=app.install_count or 0,
                pricing_model=app.pricing_model,
                price_monthly=float(app.price_monthly) if app.price_monthly else None,
                is_featured=app.is_featured,
                is_verified=app.is_verified
            )
            for app in apps
        ]

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

    async def get_app_detail(
        self,
        db: AsyncSession,
        app_id: UUID,
        tenant_id: Optional[UUID] = None
    ) -> Optional[AppDetailResponse]:
        """
        Get detailed information about a marketplace app.
        """
        result = await db.execute(
            select(MarketplaceApp).options(
                selectinload(MarketplaceApp.versions),
                selectinload(MarketplaceApp.reviews)
            ).where(MarketplaceApp.id == app_id)
        )
        app = result.scalar_one_or_none()

        if not app:
            return None

        # Check if installed for this tenant
        is_installed = False
        installation = None
        if tenant_id:
            install_result = await db.execute(
                select(AppInstallation).where(
                    and_(
                        AppInstallation.marketplace_app_id == app_id,
                        AppInstallation.tenant_id == tenant_id,
                        AppInstallation.status == InstallationStatus.ACTIVE
                    )
                )
            )
            installation = install_result.scalar_one_or_none()
            is_installed = installation is not None

        # Get current version
        current_version = None
        for v in app.versions:
            if v.is_current:
                current_version = v
                break

        # Get recent reviews
        recent_reviews = sorted(
            app.reviews,
            key=lambda r: r.created_at,
            reverse=True
        )[:5]

        return AppDetailResponse(
            id=app.id,
            name=app.name,
            slug=app.slug,
            description=app.description,
            short_description=app.short_description,
            icon_url=app.icon_url,
            banner_url=app.banner_url,
            screenshots=app.screenshots or [],
            category=app.category,
            tags=app.tags or [],
            developer_organization_id=app.developer_organization_id,
            developer_name=app.developer_name,
            support_email=app.support_email,
            support_url=app.support_url,
            documentation_url=app.documentation_url,
            privacy_policy_url=app.privacy_policy_url,
            terms_of_service_url=app.terms_of_service_url,
            average_rating=float(app.average_rating or 0),
            review_count=app.review_count or 0,
            install_count=app.install_count or 0,
            pricing_model=app.pricing_model,
            price_monthly=float(app.price_monthly) if app.price_monthly else None,
            price_yearly=float(app.price_yearly) if app.price_yearly else None,
            price_one_time=float(app.price_one_time) if app.price_one_time else None,
            free_trial_days=app.free_trial_days,
            required_scopes=app.required_scopes or [],
            optional_scopes=app.optional_scopes or [],
            is_featured=app.is_featured,
            is_verified=app.is_verified,
            current_version=current_version.version if current_version else None,
            version_release_notes=current_version.release_notes if current_version else None,
            published_at=app.published_at,
            is_installed=is_installed,
            installation_id=installation.id if installation else None,
            recent_reviews=[
                AppReviewResponse(
                    id=r.id,
                    marketplace_app_id=r.marketplace_app_id,
                    tenant_id=r.tenant_id,
                    user_id=r.user_id,
                    rating=r.rating,
                    title=r.title,
                    review_text=r.review_text,
                    developer_response=r.developer_response,
                    developer_response_at=r.developer_response_at,
                    is_verified_purchase=r.is_verified_purchase,
                    helpful_count=r.helpful_count or 0,
                    created_at=r.created_at,
                    updated_at=r.updated_at
                )
                for r in recent_reviews
            ]
        )

    async def get_featured_apps(
        self,
        db: AsyncSession,
        limit: int = 10
    ) -> list[FeaturedAppResponse]:
        """
        Get featured apps for the marketplace homepage.
        """
        result = await db.execute(
            select(MarketplaceApp).where(
                and_(
                    MarketplaceApp.status == AppStatus.PUBLISHED,
                    MarketplaceApp.is_featured == True
                )
            ).order_by(
                MarketplaceApp.featured_order.asc().nullslast(),
                MarketplaceApp.install_count.desc()
            ).limit(limit)
        )
        apps = result.scalars().all()

        return [
            FeaturedAppResponse(
                id=app.id,
                name=app.name,
                slug=app.slug,
                short_description=app.short_description,
                icon_url=app.icon_url,
                banner_url=app.banner_url,
                category=app.category,
                developer_name=app.developer_name,
                average_rating=float(app.average_rating or 0),
                install_count=app.install_count or 0,
                featured_tagline=app.featured_tagline
            )
            for app in apps
        ]

    async def get_apps_by_category(
        self,
        db: AsyncSession,
        category: AppCategory,
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedResponse[AppCatalogResponse]:
        """
        Get apps filtered by category.
        """
        filters = AppSearchFilters(category=category)
        return await self.search_apps(db, filters, page, page_size)

    async def install_app(
        self,
        db: AsyncSession,
        app_id: UUID,
        tenant_id: UUID,
        user_id: UUID,
        data: AppInstallationCreate
    ) -> AppInstallationResponse:
        """
        Install a marketplace app for a tenant.
        """
        # Check if app exists and is published
        app_result = await db.execute(
            select(MarketplaceApp).where(
                and_(
                    MarketplaceApp.id == app_id,
                    MarketplaceApp.status == AppStatus.PUBLISHED
                )
            )
        )
        app = app_result.scalar_one_or_none()

        if not app:
            raise ValueError("App not found or not available")

        # Check if already installed
        existing_result = await db.execute(
            select(AppInstallation).where(
                and_(
                    AppInstallation.marketplace_app_id == app_id,
                    AppInstallation.tenant_id == tenant_id,
                    AppInstallation.status.in_([
                        InstallationStatus.ACTIVE,
                        InstallationStatus.PENDING
                    ])
                )
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            raise ValueError("App is already installed for this tenant")

        # Get current version
        version_result = await db.execute(
            select(AppVersion).where(
                and_(
                    AppVersion.marketplace_app_id == app_id,
                    AppVersion.is_current == True
                )
            )
        )
        current_version = version_result.scalar_one_or_none()

        # Create installation
        installation = AppInstallation(
            id=uuid4(),
            marketplace_app_id=app_id,
            tenant_id=tenant_id,
            installed_by_user_id=user_id,
            installed_version_id=current_version.id if current_version else None,
            status=InstallationStatus.PENDING,
            granted_scopes=data.granted_scopes or app.required_scopes or [],
            configuration=data.configuration or {}
        )

        db.add(installation)

        # Create OAuth consent record
        if app.oauth_application_id:
            consent = OAuthConsent(
                id=uuid4(),
                application_id=app.oauth_application_id,
                tenant_id=tenant_id,
                user_id=user_id,
                granted_scopes=data.granted_scopes or app.required_scopes or [],
                consent_type="installation",
                granted_at=datetime.utcnow()
            )
            db.add(consent)

        # Update install count
        app.install_count = (app.install_count or 0) + 1

        # Audit log
        audit = DeveloperAuditLog(
            id=uuid4(),
            developer_organization_id=app.developer_organization_id,
            action="app_installed",
            resource_type="app_installation",
            resource_id=str(installation.id),
            details={
                "app_id": str(app_id),
                "tenant_id": str(tenant_id),
                "version": current_version.version if current_version else None
            },
            timestamp=datetime.utcnow()
        )
        db.add(audit)

        await db.commit()
        await db.refresh(installation)

        # Activate installation (in real impl, this might involve provisioning)
        installation.status = InstallationStatus.ACTIVE
        installation.activated_at = datetime.utcnow()
        await db.commit()

        return AppInstallationResponse(
            id=installation.id,
            marketplace_app_id=installation.marketplace_app_id,
            tenant_id=installation.tenant_id,
            installed_by_user_id=installation.installed_by_user_id,
            installed_version_id=installation.installed_version_id,
            status=installation.status,
            granted_scopes=installation.granted_scopes,
            configuration=installation.configuration,
            installed_at=installation.created_at,
            activated_at=installation.activated_at
        )

    async def uninstall_app(
        self,
        db: AsyncSession,
        installation_id: UUID,
        tenant_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Uninstall an app from a tenant.
        """
        result = await db.execute(
            select(AppInstallation).where(
                and_(
                    AppInstallation.id == installation_id,
                    AppInstallation.tenant_id == tenant_id
                )
            )
        )
        installation = result.scalar_one_or_none()

        if not installation:
            raise ValueError("Installation not found")

        # Get app for audit
        app_result = await db.execute(
            select(MarketplaceApp).where(
                MarketplaceApp.id == installation.marketplace_app_id
            )
        )
        app = app_result.scalar_one_or_none()

        # Update status
        installation.status = InstallationStatus.UNINSTALLED
        installation.uninstalled_at = datetime.utcnow()
        installation.uninstalled_by_user_id = user_id

        # Decrement install count
        if app:
            app.install_count = max(0, (app.install_count or 0) - 1)

            # Audit log
            audit = DeveloperAuditLog(
                id=uuid4(),
                developer_organization_id=app.developer_organization_id,
                action="app_uninstalled",
                resource_type="app_installation",
                resource_id=str(installation_id),
                details={
                    "app_id": str(app.id),
                    "tenant_id": str(tenant_id)
                },
                timestamp=datetime.utcnow()
            )
            db.add(audit)

        # Revoke consent
        if app and app.oauth_application_id:
            await db.execute(
                update(OAuthConsent).where(
                    and_(
                        OAuthConsent.application_id == app.oauth_application_id,
                        OAuthConsent.tenant_id == tenant_id
                    )
                ).values(
                    revoked_at=datetime.utcnow(),
                    revoked_by_user_id=user_id
                )
            )

        await db.commit()
        return True

    async def update_installation(
        self,
        db: AsyncSession,
        installation_id: UUID,
        tenant_id: UUID,
        user_id: UUID,
        data: AppInstallationUpdate
    ) -> AppInstallationResponse:
        """
        Update installation configuration or granted scopes.
        """
        result = await db.execute(
            select(AppInstallation).where(
                and_(
                    AppInstallation.id == installation_id,
                    AppInstallation.tenant_id == tenant_id,
                    AppInstallation.status == InstallationStatus.ACTIVE
                )
            )
        )
        installation = result.scalar_one_or_none()

        if not installation:
            raise ValueError("Installation not found or not active")

        if data.configuration is not None:
            installation.configuration = data.configuration

        if data.granted_scopes is not None:
            installation.granted_scopes = data.granted_scopes

            # Update OAuth consent
            app_result = await db.execute(
                select(MarketplaceApp).where(
                    MarketplaceApp.id == installation.marketplace_app_id
                )
            )
            app = app_result.scalar_one_or_none()

            if app and app.oauth_application_id:
                await db.execute(
                    update(OAuthConsent).where(
                        and_(
                            OAuthConsent.application_id == app.oauth_application_id,
                            OAuthConsent.tenant_id == tenant_id
                        )
                    ).values(granted_scopes=data.granted_scopes)
                )

        await db.commit()
        await db.refresh(installation)

        return AppInstallationResponse(
            id=installation.id,
            marketplace_app_id=installation.marketplace_app_id,
            tenant_id=installation.tenant_id,
            installed_by_user_id=installation.installed_by_user_id,
            installed_version_id=installation.installed_version_id,
            status=installation.status,
            granted_scopes=installation.granted_scopes,
            configuration=installation.configuration,
            installed_at=installation.created_at,
            activated_at=installation.activated_at
        )

    async def get_tenant_installations(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        include_inactive: bool = False
    ) -> list[InstalledAppResponse]:
        """
        Get all app installations for a tenant.
        """
        query = select(AppInstallation).options(
            selectinload(AppInstallation.marketplace_app)
        ).where(AppInstallation.tenant_id == tenant_id)

        if not include_inactive:
            query = query.where(
                AppInstallation.status == InstallationStatus.ACTIVE
            )

        result = await db.execute(query)
        installations = result.scalars().all()

        return [
            InstalledAppResponse(
                installation_id=inst.id,
                app_id=inst.marketplace_app_id,
                app_name=inst.marketplace_app.name if inst.marketplace_app else "Unknown",
                app_icon_url=inst.marketplace_app.icon_url if inst.marketplace_app else None,
                app_category=inst.marketplace_app.category if inst.marketplace_app else None,
                status=inst.status,
                granted_scopes=inst.granted_scopes,
                installed_at=inst.created_at,
                installed_by_user_id=inst.installed_by_user_id,
                current_version=inst.installed_version.version if inst.installed_version else None,
                update_available=False  # Would check against latest version
            )
            for inst in installations
        ]

    async def create_review(
        self,
        db: AsyncSession,
        app_id: UUID,
        tenant_id: UUID,
        user_id: UUID,
        data: AppReviewCreate
    ) -> AppReviewResponse:
        """
        Create a review for a marketplace app.
        """
        # Check if app exists
        app_result = await db.execute(
            select(MarketplaceApp).where(MarketplaceApp.id == app_id)
        )
        app = app_result.scalar_one_or_none()

        if not app:
            raise ValueError("App not found")

        # Check if user has already reviewed
        existing_result = await db.execute(
            select(AppReview).where(
                and_(
                    AppReview.marketplace_app_id == app_id,
                    AppReview.user_id == user_id
                )
            )
        )
        existing = existing_result.scalar_one_or_none()

        if existing:
            raise ValueError("You have already reviewed this app")

        # Check if it's a verified purchase (has installation)
        install_result = await db.execute(
            select(AppInstallation).where(
                and_(
                    AppInstallation.marketplace_app_id == app_id,
                    AppInstallation.tenant_id == tenant_id
                )
            )
        )
        installation = install_result.scalar_one_or_none()
        is_verified = installation is not None

        # Create review
        review = AppReview(
            id=uuid4(),
            marketplace_app_id=app_id,
            tenant_id=tenant_id,
            user_id=user_id,
            rating=data.rating,
            title=data.title,
            review_text=data.review_text,
            is_verified_purchase=is_verified,
            helpful_count=0
        )

        db.add(review)

        # Update app rating
        await self._update_app_rating(db, app_id)

        await db.commit()
        await db.refresh(review)

        return AppReviewResponse(
            id=review.id,
            marketplace_app_id=review.marketplace_app_id,
            tenant_id=review.tenant_id,
            user_id=review.user_id,
            rating=review.rating,
            title=review.title,
            review_text=review.review_text,
            developer_response=review.developer_response,
            developer_response_at=review.developer_response_at,
            is_verified_purchase=review.is_verified_purchase,
            helpful_count=review.helpful_count or 0,
            created_at=review.created_at,
            updated_at=review.updated_at
        )

    async def update_review(
        self,
        db: AsyncSession,
        review_id: UUID,
        user_id: UUID,
        data: AppReviewUpdate
    ) -> AppReviewResponse:
        """
        Update an existing review.
        """
        result = await db.execute(
            select(AppReview).where(
                and_(
                    AppReview.id == review_id,
                    AppReview.user_id == user_id
                )
            )
        )
        review = result.scalar_one_or_none()

        if not review:
            raise ValueError("Review not found or not owned by user")

        if data.rating is not None:
            review.rating = data.rating
        if data.title is not None:
            review.title = data.title
        if data.review_text is not None:
            review.review_text = data.review_text

        review.updated_at = datetime.utcnow()

        # Update app rating
        await self._update_app_rating(db, review.marketplace_app_id)

        await db.commit()
        await db.refresh(review)

        return AppReviewResponse(
            id=review.id,
            marketplace_app_id=review.marketplace_app_id,
            tenant_id=review.tenant_id,
            user_id=review.user_id,
            rating=review.rating,
            title=review.title,
            review_text=review.review_text,
            developer_response=review.developer_response,
            developer_response_at=review.developer_response_at,
            is_verified_purchase=review.is_verified_purchase,
            helpful_count=review.helpful_count or 0,
            created_at=review.created_at,
            updated_at=review.updated_at
        )

    async def delete_review(
        self,
        db: AsyncSession,
        review_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Delete a review.
        """
        result = await db.execute(
            select(AppReview).where(
                and_(
                    AppReview.id == review_id,
                    AppReview.user_id == user_id
                )
            )
        )
        review = result.scalar_one_or_none()

        if not review:
            raise ValueError("Review not found or not owned by user")

        app_id = review.marketplace_app_id

        await db.delete(review)

        # Update app rating
        await self._update_app_rating(db, app_id)

        await db.commit()
        return True

    async def respond_to_review(
        self,
        db: AsyncSession,
        review_id: UUID,
        developer_organization_id: UUID,
        response_text: str
    ) -> AppReviewResponse:
        """
        Add developer response to a review.
        """
        result = await db.execute(
            select(AppReview).options(
                selectinload(AppReview.marketplace_app)
            ).where(AppReview.id == review_id)
        )
        review = result.scalar_one_or_none()

        if not review:
            raise ValueError("Review not found")

        # Verify developer owns the app
        if review.marketplace_app.developer_organization_id != developer_organization_id:
            raise ValueError("Not authorized to respond to this review")

        review.developer_response = response_text
        review.developer_response_at = datetime.utcnow()

        await db.commit()
        await db.refresh(review)

        return AppReviewResponse(
            id=review.id,
            marketplace_app_id=review.marketplace_app_id,
            tenant_id=review.tenant_id,
            user_id=review.user_id,
            rating=review.rating,
            title=review.title,
            review_text=review.review_text,
            developer_response=review.developer_response,
            developer_response_at=review.developer_response_at,
            is_verified_purchase=review.is_verified_purchase,
            helpful_count=review.helpful_count or 0,
            created_at=review.created_at,
            updated_at=review.updated_at
        )

    async def get_app_reviews(
        self,
        db: AsyncSession,
        app_id: UUID,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "newest"
    ) -> PaginatedResponse[AppReviewResponse]:
        """
        Get reviews for an app.
        """
        query = select(AppReview).where(
            AppReview.marketplace_app_id == app_id
        )

        # Sorting
        sort_map = {
            "newest": AppReview.created_at.desc(),
            "oldest": AppReview.created_at.asc(),
            "highest": AppReview.rating.desc(),
            "lowest": AppReview.rating.asc(),
            "helpful": AppReview.helpful_count.desc().nullslast()
        }
        sort_order = sort_map.get(sort_by, AppReview.created_at.desc())
        query = query.order_by(sort_order)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await db.execute(query)
        reviews = result.scalars().all()

        items = [
            AppReviewResponse(
                id=r.id,
                marketplace_app_id=r.marketplace_app_id,
                tenant_id=r.tenant_id,
                user_id=r.user_id,
                rating=r.rating,
                title=r.title,
                review_text=r.review_text,
                developer_response=r.developer_response,
                developer_response_at=r.developer_response_at,
                is_verified_purchase=r.is_verified_purchase,
                helpful_count=r.helpful_count or 0,
                created_at=r.created_at,
                updated_at=r.updated_at
            )
            for r in reviews
        ]

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )

    async def mark_review_helpful(
        self,
        db: AsyncSession,
        review_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Mark a review as helpful.
        """
        result = await db.execute(
            select(AppReview).where(AppReview.id == review_id)
        )
        review = result.scalar_one_or_none()

        if not review:
            raise ValueError("Review not found")

        # Increment helpful count
        review.helpful_count = (review.helpful_count or 0) + 1

        await db.commit()
        return True

    async def get_similar_apps(
        self,
        db: AsyncSession,
        app_id: UUID,
        limit: int = 5
    ) -> list[AppCatalogResponse]:
        """
        Get similar apps based on category and tags.
        """
        # Get the reference app
        app_result = await db.execute(
            select(MarketplaceApp).where(MarketplaceApp.id == app_id)
        )
        app = app_result.scalar_one_or_none()

        if not app:
            return []

        # Find similar apps
        query = select(MarketplaceApp).where(
            and_(
                MarketplaceApp.id != app_id,
                MarketplaceApp.status == AppStatus.PUBLISHED,
                MarketplaceApp.category == app.category
            )
        ).order_by(
            MarketplaceApp.average_rating.desc(),
            MarketplaceApp.install_count.desc()
        ).limit(limit)

        result = await db.execute(query)
        apps = result.scalars().all()

        return [
            AppCatalogResponse(
                id=a.id,
                name=a.name,
                slug=a.slug,
                short_description=a.short_description,
                icon_url=a.icon_url,
                category=a.category,
                developer_name=a.developer_name,
                average_rating=float(a.average_rating or 0),
                review_count=a.review_count or 0,
                install_count=a.install_count or 0,
                pricing_model=a.pricing_model,
                price_monthly=float(a.price_monthly) if a.price_monthly else None,
                is_featured=a.is_featured,
                is_verified=a.is_verified
            )
            for a in apps
        ]

    async def _update_app_rating(
        self,
        db: AsyncSession,
        app_id: UUID
    ) -> None:
        """
        Recalculate and update app rating.
        """
        result = await db.execute(
            select(
                func.avg(AppReview.rating),
                func.count(AppReview.id)
            ).where(AppReview.marketplace_app_id == app_id)
        )
        row = result.fetchone()
        avg_rating = row[0] or 0
        review_count = row[1] or 0

        await db.execute(
            update(MarketplaceApp).where(
                MarketplaceApp.id == app_id
            ).values(
                average_rating=Decimal(str(round(avg_rating, 1))),
                review_count=review_count
            )
        )

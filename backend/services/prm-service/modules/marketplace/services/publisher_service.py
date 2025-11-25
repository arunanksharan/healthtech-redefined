"""
Publisher Service
Handles app submissions, versioning, review process, and publishing.
"""

import re
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
    AppStatus,
    AppVersion,
    DeveloperAuditLog,
    DeveloperMember,
    DeveloperOrganization,
    DeveloperRole,
    DeveloperStatus,
    InstallationStatus,
    MarketplaceApp,
    OAuthApplication,
)
from ..schemas import (
    AppSubmissionCreate,
    AppSubmissionResponse,
    AppVersionCreate,
    AppVersionResponse,
    PublishedAppResponse,
    PublisherDashboard,
    ReviewDecision,
    SubmissionReviewCreate,
    VersionRollout,
)


class PublisherService:
    """
    Publisher Service for managing app submissions, versions,
    and the publication review process.
    """

    async def create_submission(
        self,
        db: AsyncSession,
        organization_id: UUID,
        user_id: UUID,
        data: AppSubmissionCreate
    ) -> AppSubmissionResponse:
        """
        Create a new app submission for marketplace review.
        """
        # Verify organization and user access
        await self._verify_publisher_access(db, organization_id, user_id)

        # Verify OAuth application exists
        app_result = await db.execute(
            select(OAuthApplication).where(
                and_(
                    OAuthApplication.id == data.oauth_application_id,
                    OAuthApplication.developer_organization_id == organization_id
                )
            )
        )
        oauth_app = app_result.scalar_one_or_none()

        if not oauth_app:
            raise ValueError("OAuth application not found or not owned by organization")

        # Generate slug from name
        slug = self._generate_slug(data.name)

        # Check slug uniqueness
        existing_result = await db.execute(
            select(MarketplaceApp).where(MarketplaceApp.slug == slug)
        )
        if existing_result.scalar_one_or_none():
            slug = f"{slug}-{uuid4().hex[:8]}"

        # Get developer organization for name
        org_result = await db.execute(
            select(DeveloperOrganization).where(
                DeveloperOrganization.id == organization_id
            )
        )
        org = org_result.scalar_one_or_none()

        # Create marketplace app entry
        marketplace_app = MarketplaceApp(
            id=uuid4(),
            oauth_application_id=data.oauth_application_id,
            developer_organization_id=organization_id,
            name=data.name,
            slug=slug,
            description=data.description,
            short_description=data.short_description,
            icon_url=data.icon_url,
            banner_url=data.banner_url,
            screenshots=data.screenshots or [],
            category=data.category,
            tags=data.tags or [],
            developer_name=org.name if org else "Unknown Developer",
            support_email=data.support_email,
            support_url=data.support_url,
            documentation_url=data.documentation_url,
            privacy_policy_url=data.privacy_policy_url,
            terms_of_service_url=data.terms_of_service_url,
            pricing_model=data.pricing_model or "free",
            price_monthly=data.price_monthly,
            price_yearly=data.price_yearly,
            price_one_time=data.price_one_time,
            free_trial_days=data.free_trial_days,
            required_scopes=data.required_scopes or [],
            optional_scopes=data.optional_scopes or [],
            webhook_url=data.webhook_url,
            status=AppStatus.DRAFT
        )

        db.add(marketplace_app)

        # Create initial version
        version = AppVersion(
            id=uuid4(),
            marketplace_app_id=marketplace_app.id,
            version=data.version or "1.0.0",
            release_notes=data.release_notes or "Initial release",
            changelog=data.changelog,
            min_api_version=data.min_api_version,
            max_api_version=data.max_api_version,
            status=AppStatus.DRAFT,
            is_current=True,
            submitted_at=datetime.utcnow(),
            submitted_by_user_id=user_id
        )

        db.add(version)

        # Audit log
        audit = DeveloperAuditLog(
            id=uuid4(),
            developer_organization_id=organization_id,
            user_id=user_id,
            action="app_submission_created",
            resource_type="marketplace_app",
            resource_id=str(marketplace_app.id),
            details={
                "app_name": data.name,
                "version": version.version
            },
            timestamp=datetime.utcnow()
        )
        db.add(audit)

        await db.commit()
        await db.refresh(marketplace_app)
        await db.refresh(version)

        return AppSubmissionResponse(
            id=marketplace_app.id,
            oauth_application_id=marketplace_app.oauth_application_id,
            name=marketplace_app.name,
            slug=marketplace_app.slug,
            description=marketplace_app.description,
            short_description=marketplace_app.short_description,
            category=marketplace_app.category,
            status=marketplace_app.status,
            current_version=version.version,
            version_id=version.id,
            submitted_at=version.submitted_at,
            submitted_by_user_id=version.submitted_by_user_id,
            review_status=None,
            review_notes=None
        )

    async def submit_for_review(
        self,
        db: AsyncSession,
        app_id: UUID,
        organization_id: UUID,
        user_id: UUID
    ) -> AppSubmissionResponse:
        """
        Submit an app for marketplace review.
        """
        await self._verify_publisher_access(db, organization_id, user_id)

        result = await db.execute(
            select(MarketplaceApp).options(
                selectinload(MarketplaceApp.versions)
            ).where(
                and_(
                    MarketplaceApp.id == app_id,
                    MarketplaceApp.developer_organization_id == organization_id
                )
            )
        )
        app = result.scalar_one_or_none()

        if not app:
            raise ValueError("App not found or not owned by organization")

        if app.status not in [AppStatus.DRAFT, AppStatus.REJECTED]:
            raise ValueError(f"App cannot be submitted from status: {app.status}")

        # Validate submission requirements
        self._validate_submission(app)

        # Update status
        app.status = AppStatus.PENDING_REVIEW

        # Update current version
        current_version = None
        for v in app.versions:
            if v.is_current:
                v.status = AppStatus.PENDING_REVIEW
                v.submitted_at = datetime.utcnow()
                v.submitted_by_user_id = user_id
                current_version = v
                break

        # Audit log
        audit = DeveloperAuditLog(
            id=uuid4(),
            developer_organization_id=organization_id,
            user_id=user_id,
            action="app_submitted_for_review",
            resource_type="marketplace_app",
            resource_id=str(app.id),
            details={"version": current_version.version if current_version else None},
            timestamp=datetime.utcnow()
        )
        db.add(audit)

        await db.commit()
        await db.refresh(app)

        return AppSubmissionResponse(
            id=app.id,
            oauth_application_id=app.oauth_application_id,
            name=app.name,
            slug=app.slug,
            description=app.description,
            short_description=app.short_description,
            category=app.category,
            status=app.status,
            current_version=current_version.version if current_version else None,
            version_id=current_version.id if current_version else None,
            submitted_at=current_version.submitted_at if current_version else None,
            submitted_by_user_id=current_version.submitted_by_user_id if current_version else None,
            review_status=None,
            review_notes=None
        )

    async def review_submission(
        self,
        db: AsyncSession,
        app_id: UUID,
        reviewer_id: UUID,
        decision: SubmissionReviewCreate
    ) -> AppSubmissionResponse:
        """
        Review and approve/reject an app submission.
        This is typically done by platform administrators.
        """
        result = await db.execute(
            select(MarketplaceApp).options(
                selectinload(MarketplaceApp.versions)
            ).where(
                and_(
                    MarketplaceApp.id == app_id,
                    MarketplaceApp.status == AppStatus.PENDING_REVIEW
                )
            )
        )
        app = result.scalar_one_or_none()

        if not app:
            raise ValueError("App not found or not pending review")

        current_version = None
        for v in app.versions:
            if v.is_current:
                current_version = v
                break

        if decision.decision == ReviewDecision.APPROVED:
            app.status = AppStatus.PUBLISHED
            app.published_at = datetime.utcnow()
            if current_version:
                current_version.status = AppStatus.PUBLISHED
                current_version.published_at = datetime.utcnow()
                current_version.reviewed_by_user_id = reviewer_id
                current_version.reviewed_at = datetime.utcnow()
        else:
            app.status = AppStatus.REJECTED
            if current_version:
                current_version.status = AppStatus.REJECTED
                current_version.review_notes = decision.review_notes
                current_version.reviewed_by_user_id = reviewer_id
                current_version.reviewed_at = datetime.utcnow()

        # Audit log
        audit = DeveloperAuditLog(
            id=uuid4(),
            developer_organization_id=app.developer_organization_id,
            user_id=reviewer_id,
            action=f"app_review_{decision.decision.value}",
            resource_type="marketplace_app",
            resource_id=str(app.id),
            details={
                "decision": decision.decision.value,
                "notes": decision.review_notes
            },
            timestamp=datetime.utcnow()
        )
        db.add(audit)

        await db.commit()
        await db.refresh(app)

        return AppSubmissionResponse(
            id=app.id,
            oauth_application_id=app.oauth_application_id,
            name=app.name,
            slug=app.slug,
            description=app.description,
            short_description=app.short_description,
            category=app.category,
            status=app.status,
            current_version=current_version.version if current_version else None,
            version_id=current_version.id if current_version else None,
            submitted_at=current_version.submitted_at if current_version else None,
            submitted_by_user_id=current_version.submitted_by_user_id if current_version else None,
            review_status=decision.decision.value,
            review_notes=decision.review_notes
        )

    async def create_version(
        self,
        db: AsyncSession,
        app_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        data: AppVersionCreate
    ) -> AppVersionResponse:
        """
        Create a new version for an existing app.
        """
        await self._verify_publisher_access(db, organization_id, user_id)

        result = await db.execute(
            select(MarketplaceApp).options(
                selectinload(MarketplaceApp.versions)
            ).where(
                and_(
                    MarketplaceApp.id == app_id,
                    MarketplaceApp.developer_organization_id == organization_id
                )
            )
        )
        app = result.scalar_one_or_none()

        if not app:
            raise ValueError("App not found or not owned by organization")

        # Validate version number
        if not self._is_valid_semver(data.version):
            raise ValueError("Invalid version format. Use semantic versioning (e.g., 1.2.3)")

        # Check version doesn't already exist
        for v in app.versions:
            if v.version == data.version:
                raise ValueError(f"Version {data.version} already exists")

        # Create new version (not current yet - needs to be published)
        version = AppVersion(
            id=uuid4(),
            marketplace_app_id=app_id,
            version=data.version,
            release_notes=data.release_notes,
            changelog=data.changelog,
            min_api_version=data.min_api_version,
            max_api_version=data.max_api_version,
            breaking_changes=data.breaking_changes or [],
            deprecations=data.deprecations or [],
            status=AppStatus.DRAFT,
            is_current=False,
            submitted_at=datetime.utcnow(),
            submitted_by_user_id=user_id
        )

        db.add(version)

        # Audit log
        audit = DeveloperAuditLog(
            id=uuid4(),
            developer_organization_id=organization_id,
            user_id=user_id,
            action="app_version_created",
            resource_type="app_version",
            resource_id=str(version.id),
            details={
                "app_id": str(app_id),
                "version": data.version
            },
            timestamp=datetime.utcnow()
        )
        db.add(audit)

        await db.commit()
        await db.refresh(version)

        return AppVersionResponse(
            id=version.id,
            marketplace_app_id=version.marketplace_app_id,
            version=version.version,
            release_notes=version.release_notes,
            changelog=version.changelog,
            min_api_version=version.min_api_version,
            max_api_version=version.max_api_version,
            breaking_changes=version.breaking_changes,
            deprecations=version.deprecations,
            status=version.status,
            is_current=version.is_current,
            submitted_at=version.submitted_at,
            published_at=version.published_at,
            rollout_percentage=version.rollout_percentage
        )

    async def submit_version_for_review(
        self,
        db: AsyncSession,
        app_id: UUID,
        version_id: UUID,
        organization_id: UUID,
        user_id: UUID
    ) -> AppVersionResponse:
        """
        Submit a specific version for review.
        """
        await self._verify_publisher_access(db, organization_id, user_id)

        result = await db.execute(
            select(AppVersion).where(
                and_(
                    AppVersion.id == version_id,
                    AppVersion.marketplace_app_id == app_id
                )
            )
        )
        version = result.scalar_one_or_none()

        if not version:
            raise ValueError("Version not found")

        # Verify app ownership
        app_result = await db.execute(
            select(MarketplaceApp).where(
                and_(
                    MarketplaceApp.id == app_id,
                    MarketplaceApp.developer_organization_id == organization_id
                )
            )
        )
        app = app_result.scalar_one_or_none()

        if not app:
            raise ValueError("App not found or not owned by organization")

        if version.status not in [AppStatus.DRAFT, AppStatus.REJECTED]:
            raise ValueError(f"Version cannot be submitted from status: {version.status}")

        version.status = AppStatus.PENDING_REVIEW
        version.submitted_at = datetime.utcnow()
        version.submitted_by_user_id = user_id

        # Audit log
        audit = DeveloperAuditLog(
            id=uuid4(),
            developer_organization_id=organization_id,
            user_id=user_id,
            action="version_submitted_for_review",
            resource_type="app_version",
            resource_id=str(version.id),
            details={"version": version.version},
            timestamp=datetime.utcnow()
        )
        db.add(audit)

        await db.commit()
        await db.refresh(version)

        return AppVersionResponse(
            id=version.id,
            marketplace_app_id=version.marketplace_app_id,
            version=version.version,
            release_notes=version.release_notes,
            changelog=version.changelog,
            min_api_version=version.min_api_version,
            max_api_version=version.max_api_version,
            breaking_changes=version.breaking_changes,
            deprecations=version.deprecations,
            status=version.status,
            is_current=version.is_current,
            submitted_at=version.submitted_at,
            published_at=version.published_at,
            rollout_percentage=version.rollout_percentage
        )

    async def publish_version(
        self,
        db: AsyncSession,
        app_id: UUID,
        version_id: UUID,
        reviewer_id: UUID,
        rollout: Optional[VersionRollout] = None
    ) -> AppVersionResponse:
        """
        Publish an approved version, making it current.
        Supports staged rollouts.
        """
        result = await db.execute(
            select(AppVersion).where(
                and_(
                    AppVersion.id == version_id,
                    AppVersion.marketplace_app_id == app_id,
                    AppVersion.status == AppStatus.PENDING_REVIEW
                )
            )
        )
        version = result.scalar_one_or_none()

        if not version:
            raise ValueError("Version not found or not pending review")

        # Get app
        app_result = await db.execute(
            select(MarketplaceApp).options(
                selectinload(MarketplaceApp.versions)
            ).where(MarketplaceApp.id == app_id)
        )
        app = app_result.scalar_one_or_none()

        # Determine rollout strategy
        rollout_percentage = 100
        if rollout:
            rollout_percentage = rollout.initial_percentage

        # If full rollout, make this version current
        if rollout_percentage == 100:
            # Unset current flag on all other versions
            for v in app.versions:
                if v.is_current:
                    v.is_current = False
            version.is_current = True

        version.status = AppStatus.PUBLISHED
        version.published_at = datetime.utcnow()
        version.reviewed_by_user_id = reviewer_id
        version.reviewed_at = datetime.utcnow()
        version.rollout_percentage = rollout_percentage

        # Ensure app is published
        if app.status != AppStatus.PUBLISHED:
            app.status = AppStatus.PUBLISHED
            app.published_at = datetime.utcnow()

        # Audit log
        audit = DeveloperAuditLog(
            id=uuid4(),
            developer_organization_id=app.developer_organization_id,
            user_id=reviewer_id,
            action="version_published",
            resource_type="app_version",
            resource_id=str(version.id),
            details={
                "version": version.version,
                "rollout_percentage": rollout_percentage
            },
            timestamp=datetime.utcnow()
        )
        db.add(audit)

        await db.commit()
        await db.refresh(version)

        return AppVersionResponse(
            id=version.id,
            marketplace_app_id=version.marketplace_app_id,
            version=version.version,
            release_notes=version.release_notes,
            changelog=version.changelog,
            min_api_version=version.min_api_version,
            max_api_version=version.max_api_version,
            breaking_changes=version.breaking_changes,
            deprecations=version.deprecations,
            status=version.status,
            is_current=version.is_current,
            submitted_at=version.submitted_at,
            published_at=version.published_at,
            rollout_percentage=version.rollout_percentage
        )

    async def update_rollout(
        self,
        db: AsyncSession,
        app_id: UUID,
        version_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        new_percentage: int
    ) -> AppVersionResponse:
        """
        Update the rollout percentage for a staged release.
        """
        await self._verify_publisher_access(db, organization_id, user_id)

        result = await db.execute(
            select(AppVersion).where(
                and_(
                    AppVersion.id == version_id,
                    AppVersion.marketplace_app_id == app_id,
                    AppVersion.status == AppStatus.PUBLISHED
                )
            )
        )
        version = result.scalar_one_or_none()

        if not version:
            raise ValueError("Version not found or not published")

        # Verify app ownership
        app_result = await db.execute(
            select(MarketplaceApp).options(
                selectinload(MarketplaceApp.versions)
            ).where(
                and_(
                    MarketplaceApp.id == app_id,
                    MarketplaceApp.developer_organization_id == organization_id
                )
            )
        )
        app = app_result.scalar_one_or_none()

        if not app:
            raise ValueError("App not found or not owned by organization")

        if new_percentage < 0 or new_percentage > 100:
            raise ValueError("Rollout percentage must be between 0 and 100")

        old_percentage = version.rollout_percentage
        version.rollout_percentage = new_percentage

        # If reaching 100%, make this version current
        if new_percentage == 100 and not version.is_current:
            for v in app.versions:
                if v.is_current:
                    v.is_current = False
            version.is_current = True

        # Audit log
        audit = DeveloperAuditLog(
            id=uuid4(),
            developer_organization_id=organization_id,
            user_id=user_id,
            action="rollout_updated",
            resource_type="app_version",
            resource_id=str(version.id),
            details={
                "version": version.version,
                "old_percentage": old_percentage,
                "new_percentage": new_percentage
            },
            timestamp=datetime.utcnow()
        )
        db.add(audit)

        await db.commit()
        await db.refresh(version)

        return AppVersionResponse(
            id=version.id,
            marketplace_app_id=version.marketplace_app_id,
            version=version.version,
            release_notes=version.release_notes,
            changelog=version.changelog,
            min_api_version=version.min_api_version,
            max_api_version=version.max_api_version,
            breaking_changes=version.breaking_changes,
            deprecations=version.deprecations,
            status=version.status,
            is_current=version.is_current,
            submitted_at=version.submitted_at,
            published_at=version.published_at,
            rollout_percentage=version.rollout_percentage
        )

    async def deprecate_version(
        self,
        db: AsyncSession,
        app_id: UUID,
        version_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        deprecation_message: str,
        sunset_date: Optional[datetime] = None
    ) -> AppVersionResponse:
        """
        Deprecate a published version.
        """
        await self._verify_publisher_access(db, organization_id, user_id)

        result = await db.execute(
            select(AppVersion).where(
                and_(
                    AppVersion.id == version_id,
                    AppVersion.marketplace_app_id == app_id,
                    AppVersion.status == AppStatus.PUBLISHED
                )
            )
        )
        version = result.scalar_one_or_none()

        if not version:
            raise ValueError("Version not found or not published")

        version.status = AppStatus.DEPRECATED
        version.deprecated_at = datetime.utcnow()
        version.deprecation_message = deprecation_message
        version.sunset_date = sunset_date

        # If this was current, we need to find next best version
        if version.is_current:
            version.is_current = False

            # Find latest non-deprecated published version
            app_result = await db.execute(
                select(MarketplaceApp).options(
                    selectinload(MarketplaceApp.versions)
                ).where(MarketplaceApp.id == app_id)
            )
            app = app_result.scalar_one_or_none()

            best_version = None
            for v in app.versions:
                if v.status == AppStatus.PUBLISHED and v.id != version_id:
                    if not best_version or self._compare_versions(
                        v.version, best_version.version
                    ) > 0:
                        best_version = v

            if best_version:
                best_version.is_current = True

        # Audit log
        audit = DeveloperAuditLog(
            id=uuid4(),
            developer_organization_id=organization_id,
            user_id=user_id,
            action="version_deprecated",
            resource_type="app_version",
            resource_id=str(version.id),
            details={
                "version": version.version,
                "message": deprecation_message,
                "sunset_date": sunset_date.isoformat() if sunset_date else None
            },
            timestamp=datetime.utcnow()
        )
        db.add(audit)

        await db.commit()
        await db.refresh(version)

        return AppVersionResponse(
            id=version.id,
            marketplace_app_id=version.marketplace_app_id,
            version=version.version,
            release_notes=version.release_notes,
            changelog=version.changelog,
            min_api_version=version.min_api_version,
            max_api_version=version.max_api_version,
            breaking_changes=version.breaking_changes,
            deprecations=version.deprecations,
            status=version.status,
            is_current=version.is_current,
            submitted_at=version.submitted_at,
            published_at=version.published_at,
            rollout_percentage=version.rollout_percentage,
            deprecated_at=version.deprecated_at,
            deprecation_message=version.deprecation_message,
            sunset_date=version.sunset_date
        )

    async def unpublish_app(
        self,
        db: AsyncSession,
        app_id: UUID,
        organization_id: UUID,
        user_id: UUID,
        reason: str
    ) -> PublishedAppResponse:
        """
        Unpublish an app from the marketplace.
        """
        await self._verify_publisher_access(db, organization_id, user_id)

        result = await db.execute(
            select(MarketplaceApp).where(
                and_(
                    MarketplaceApp.id == app_id,
                    MarketplaceApp.developer_organization_id == organization_id
                )
            )
        )
        app = result.scalar_one_or_none()

        if not app:
            raise ValueError("App not found or not owned by organization")

        if app.status != AppStatus.PUBLISHED:
            raise ValueError("App is not currently published")

        app.status = AppStatus.SUSPENDED
        app.suspended_at = datetime.utcnow()
        app.suspension_reason = reason

        # Audit log
        audit = DeveloperAuditLog(
            id=uuid4(),
            developer_organization_id=organization_id,
            user_id=user_id,
            action="app_unpublished",
            resource_type="marketplace_app",
            resource_id=str(app.id),
            details={"reason": reason},
            timestamp=datetime.utcnow()
        )
        db.add(audit)

        await db.commit()
        await db.refresh(app)

        return PublishedAppResponse(
            id=app.id,
            name=app.name,
            slug=app.slug,
            status=app.status,
            published_at=app.published_at,
            install_count=app.install_count or 0,
            average_rating=float(app.average_rating or 0),
            review_count=app.review_count or 0
        )

    async def get_publisher_dashboard(
        self,
        db: AsyncSession,
        organization_id: UUID,
        user_id: UUID
    ) -> PublisherDashboard:
        """
        Get publisher dashboard with app statistics.
        """
        await self._verify_publisher_access(db, organization_id, user_id)

        # Get all apps for organization
        apps_result = await db.execute(
            select(MarketplaceApp).options(
                selectinload(MarketplaceApp.versions)
            ).where(
                MarketplaceApp.developer_organization_id == organization_id
            )
        )
        apps = apps_result.scalars().all()

        # Calculate statistics
        total_apps = len(apps)
        published_apps = len([a for a in apps if a.status == AppStatus.PUBLISHED])
        pending_review = len([a for a in apps if a.status == AppStatus.PENDING_REVIEW])
        draft_apps = len([a for a in apps if a.status == AppStatus.DRAFT])

        total_installs = sum(a.install_count or 0 for a in apps)
        total_reviews = sum(a.review_count or 0 for a in apps)

        # Calculate average rating across all apps
        rated_apps = [a for a in apps if a.average_rating and a.review_count]
        avg_rating = (
            sum(float(a.average_rating) * a.review_count for a in rated_apps) /
            sum(a.review_count for a in rated_apps)
            if rated_apps else 0
        )

        # Get app summaries
        app_summaries = [
            PublishedAppResponse(
                id=a.id,
                name=a.name,
                slug=a.slug,
                status=a.status,
                published_at=a.published_at,
                install_count=a.install_count or 0,
                average_rating=float(a.average_rating or 0),
                review_count=a.review_count or 0
            )
            for a in apps
        ]

        return PublisherDashboard(
            organization_id=organization_id,
            total_apps=total_apps,
            published_apps=published_apps,
            pending_review=pending_review,
            draft_apps=draft_apps,
            total_installs=total_installs,
            total_reviews=total_reviews,
            average_rating=round(avg_rating, 1),
            apps=app_summaries
        )

    async def get_app_versions(
        self,
        db: AsyncSession,
        app_id: UUID,
        organization_id: UUID,
        user_id: UUID
    ) -> list[AppVersionResponse]:
        """
        Get all versions for an app.
        """
        await self._verify_publisher_access(db, organization_id, user_id)

        result = await db.execute(
            select(MarketplaceApp).options(
                selectinload(MarketplaceApp.versions)
            ).where(
                and_(
                    MarketplaceApp.id == app_id,
                    MarketplaceApp.developer_organization_id == organization_id
                )
            )
        )
        app = result.scalar_one_or_none()

        if not app:
            raise ValueError("App not found or not owned by organization")

        # Sort versions by semantic version
        sorted_versions = sorted(
            app.versions,
            key=lambda v: self._parse_version(v.version),
            reverse=True
        )

        return [
            AppVersionResponse(
                id=v.id,
                marketplace_app_id=v.marketplace_app_id,
                version=v.version,
                release_notes=v.release_notes,
                changelog=v.changelog,
                min_api_version=v.min_api_version,
                max_api_version=v.max_api_version,
                breaking_changes=v.breaking_changes,
                deprecations=v.deprecations,
                status=v.status,
                is_current=v.is_current,
                submitted_at=v.submitted_at,
                published_at=v.published_at,
                rollout_percentage=v.rollout_percentage,
                deprecated_at=v.deprecated_at,
                deprecation_message=v.deprecation_message,
                sunset_date=v.sunset_date
            )
            for v in sorted_versions
        ]

    async def _verify_publisher_access(
        self,
        db: AsyncSession,
        organization_id: UUID,
        user_id: UUID
    ) -> None:
        """Verify user has publisher access to organization."""
        result = await db.execute(
            select(DeveloperMember).where(
                and_(
                    DeveloperMember.developer_organization_id == organization_id,
                    DeveloperMember.user_id == user_id,
                    DeveloperMember.role.in_([
                        DeveloperRole.OWNER,
                        DeveloperRole.ADMIN,
                        DeveloperRole.DEVELOPER
                    ])
                )
            )
        )
        member = result.scalar_one_or_none()

        if not member:
            raise ValueError("Not authorized to publish for this organization")

        # Verify organization is approved
        org_result = await db.execute(
            select(DeveloperOrganization).where(
                and_(
                    DeveloperOrganization.id == organization_id,
                    DeveloperOrganization.status == DeveloperStatus.APPROVED
                )
            )
        )
        org = org_result.scalar_one_or_none()

        if not org:
            raise ValueError("Organization not approved for publishing")

    def _validate_submission(self, app: MarketplaceApp) -> None:
        """Validate app meets submission requirements."""
        errors = []

        if not app.name or len(app.name) < 3:
            errors.append("App name must be at least 3 characters")

        if not app.description or len(app.description) < 50:
            errors.append("Description must be at least 50 characters")

        if not app.short_description:
            errors.append("Short description is required")

        if not app.icon_url:
            errors.append("App icon is required")

        if not app.privacy_policy_url:
            errors.append("Privacy policy URL is required")

        if not app.support_email:
            errors.append("Support email is required")

        if errors:
            raise ValueError(f"Submission validation failed: {'; '.join(errors)}")

    def _generate_slug(self, name: str) -> str:
        """Generate URL-safe slug from name."""
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')[:100]

    def _is_valid_semver(self, version: str) -> bool:
        """Check if version follows semantic versioning."""
        pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*)?(\+[a-zA-Z0-9]+(\.[a-zA-Z0-9]+)*)?$'
        return bool(re.match(pattern, version))

    def _parse_version(self, version: str) -> tuple[int, int, int]:
        """Parse version string into comparable tuple."""
        try:
            parts = version.split('-')[0].split('+')[0].split('.')
            return (int(parts[0]), int(parts[1]), int(parts[2]))
        except (IndexError, ValueError):
            return (0, 0, 0)

    def _compare_versions(self, v1: str, v2: str) -> int:
        """Compare two version strings. Returns 1 if v1 > v2, -1 if v1 < v2, 0 if equal."""
        p1 = self._parse_version(v1)
        p2 = self._parse_version(v2)
        if p1 > p2:
            return 1
        elif p1 < p2:
            return -1
        return 0

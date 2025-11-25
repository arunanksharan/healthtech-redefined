"""
Deployment Service

Service for managing deployments, rollbacks, environment promotions, and feature flags.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    Deployment, EnvironmentPromotion, FeatureFlag, DatabaseMigration,
    DeploymentStatus, DeploymentStrategy, FeatureFlagStatus, EnvironmentType
)
from ..schemas import (
    DeploymentCreate, DeploymentUpdate, EnvironmentPromotionCreate,
    FeatureFlagCreate, FeatureFlagUpdate, DatabaseMigrationCreate,
    DeploymentSummary, DeploymentResponse
)


class DeploymentService:
    """Service for deployment management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Deployments
    # =========================================================================

    async def _generate_deployment_number(self, tenant_id: UUID) -> str:
        """Generate unique deployment number."""
        result = await self.db.execute(
            select(func.count(Deployment.id)).where(
                Deployment.tenant_id == tenant_id
            )
        )
        count = result.scalar() or 0
        return f"DEPLOY-{count + 1:04d}"

    async def create_deployment(
        self,
        tenant_id: UUID,
        data: DeploymentCreate,
        created_by: Optional[UUID] = None
    ) -> Deployment:
        """Create a new deployment."""
        deployment_number = await self._generate_deployment_number(tenant_id)

        deployment = Deployment(
            tenant_id=tenant_id,
            deployment_number=deployment_number,
            service_name=data.service_name,
            version=data.version,
            previous_version=data.previous_version,
            commit_sha=data.commit_sha,
            environment=data.environment,
            strategy=data.strategy,
            replicas=data.replicas,
            config_changes=data.config_changes or {},
            scheduled_at=data.scheduled_at,
            requires_approval=data.requires_approval,
            docker_image=data.docker_image,
            helm_chart_version=data.helm_chart_version,
            release_notes=data.release_notes,
            deployment_notes=data.deployment_notes,
            created_by=created_by
        )
        self.db.add(deployment)
        await self.db.commit()
        await self.db.refresh(deployment)
        return deployment

    async def get_deployment(
        self,
        tenant_id: UUID,
        deployment_id: UUID
    ) -> Optional[Deployment]:
        """Get deployment by ID."""
        result = await self.db.execute(
            select(Deployment).where(
                and_(
                    Deployment.tenant_id == tenant_id,
                    Deployment.id == deployment_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_deployments(
        self,
        tenant_id: UUID,
        service_name: Optional[str] = None,
        environment: Optional[EnvironmentType] = None,
        status: Optional[DeploymentStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Deployment]:
        """List deployments."""
        query = select(Deployment).where(Deployment.tenant_id == tenant_id)

        if service_name:
            query = query.where(Deployment.service_name == service_name)
        if environment:
            query = query.where(Deployment.environment == environment)
        if status:
            query = query.where(Deployment.status == status)

        query = query.order_by(Deployment.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def start_deployment(
        self,
        tenant_id: UUID,
        deployment_id: UUID
    ) -> Optional[Deployment]:
        """Start a deployment."""
        deployment = await self.get_deployment(tenant_id, deployment_id)
        if deployment:
            deployment.status = DeploymentStatus.IN_PROGRESS
            deployment.started_at = datetime.utcnow()
            deployment.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(deployment)
        return deployment

    async def complete_deployment(
        self,
        tenant_id: UUID,
        deployment_id: UUID,
        success: bool,
        health_check_passed: Optional[bool] = None
    ) -> Optional[Deployment]:
        """Complete a deployment."""
        deployment = await self.get_deployment(tenant_id, deployment_id)
        if deployment:
            deployment.status = DeploymentStatus.SUCCEEDED if success else DeploymentStatus.FAILED
            deployment.completed_at = datetime.utcnow()
            deployment.health_check_passed = health_check_passed

            if deployment.started_at:
                delta = datetime.utcnow() - deployment.started_at
                deployment.duration_seconds = int(delta.total_seconds())

            deployment.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(deployment)
        return deployment

    async def approve_deployment(
        self,
        tenant_id: UUID,
        deployment_id: UUID,
        approved_by: UUID
    ) -> Optional[Deployment]:
        """Approve a deployment."""
        deployment = await self.get_deployment(tenant_id, deployment_id)
        if deployment:
            deployment.approved_by = approved_by
            deployment.approved_at = datetime.utcnow()
            deployment.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(deployment)
        return deployment

    async def rollback_deployment(
        self,
        tenant_id: UUID,
        deployment_id: UUID,
        reason: str,
        created_by: Optional[UUID] = None
    ) -> Optional[Deployment]:
        """Rollback a deployment."""
        deployment = await self.get_deployment(tenant_id, deployment_id)
        if deployment and deployment.previous_version:
            # Mark original deployment as rolled back
            deployment.rolled_back = True
            deployment.rollback_reason = reason
            deployment.status = DeploymentStatus.ROLLED_BACK
            deployment.updated_at = datetime.utcnow()

            # Create rollback deployment
            rollback_data = DeploymentCreate(
                service_name=deployment.service_name,
                version=deployment.previous_version,
                previous_version=deployment.version,
                commit_sha=None,
                environment=deployment.environment,
                strategy=deployment.strategy,
                replicas=deployment.replicas,
                release_notes=f"Rollback from {deployment.version} - {reason}"
            )
            rollback = await self.create_deployment(tenant_id, rollback_data, created_by)

            deployment.rollback_deployment_id = rollback.id

            await self.db.commit()
            await self.db.refresh(deployment)
            return rollback
        return None

    async def get_latest_deployment(
        self,
        tenant_id: UUID,
        service_name: str,
        environment: EnvironmentType
    ) -> Optional[Deployment]:
        """Get the latest successful deployment for a service."""
        result = await self.db.execute(
            select(Deployment).where(
                and_(
                    Deployment.tenant_id == tenant_id,
                    Deployment.service_name == service_name,
                    Deployment.environment == environment,
                    Deployment.status == DeploymentStatus.SUCCEEDED
                )
            ).order_by(Deployment.completed_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    # =========================================================================
    # Environment Promotions
    # =========================================================================

    async def create_promotion(
        self,
        tenant_id: UUID,
        data: EnvironmentPromotionCreate,
        created_by: Optional[UUID] = None
    ) -> EnvironmentPromotion:
        """Create a new environment promotion request."""
        promotion = EnvironmentPromotion(
            tenant_id=tenant_id,
            service_name=data.service_name,
            version=data.version,
            source_environment=data.source_environment,
            target_environment=data.target_environment,
            approval_required=data.approval_required,
            created_by=created_by
        )
        self.db.add(promotion)
        await self.db.commit()
        await self.db.refresh(promotion)
        return promotion

    async def get_promotion(
        self,
        tenant_id: UUID,
        promotion_id: UUID
    ) -> Optional[EnvironmentPromotion]:
        """Get promotion by ID."""
        result = await self.db.execute(
            select(EnvironmentPromotion).where(
                and_(
                    EnvironmentPromotion.tenant_id == tenant_id,
                    EnvironmentPromotion.id == promotion_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_promotions(
        self,
        tenant_id: UUID,
        status: Optional[DeploymentStatus] = None,
        pending_only: bool = False
    ) -> List[EnvironmentPromotion]:
        """List environment promotions."""
        query = select(EnvironmentPromotion).where(
            EnvironmentPromotion.tenant_id == tenant_id
        )
        if status:
            query = query.where(EnvironmentPromotion.status == status)
        if pending_only:
            query = query.where(EnvironmentPromotion.status == DeploymentStatus.PENDING)
        query = query.order_by(EnvironmentPromotion.requested_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def approve_promotion(
        self,
        tenant_id: UUID,
        promotion_id: UUID,
        approved_by: UUID
    ) -> Optional[EnvironmentPromotion]:
        """Approve an environment promotion."""
        promotion = await self.get_promotion(tenant_id, promotion_id)
        if promotion:
            promotion.approved_by = approved_by
            promotion.approved_at = datetime.utcnow()
            promotion.status = DeploymentStatus.IN_PROGRESS
            promotion.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(promotion)
        return promotion

    async def reject_promotion(
        self,
        tenant_id: UUID,
        promotion_id: UUID,
        reason: str
    ) -> Optional[EnvironmentPromotion]:
        """Reject an environment promotion."""
        promotion = await self.get_promotion(tenant_id, promotion_id)
        if promotion:
            promotion.status = DeploymentStatus.FAILED
            promotion.rejection_reason = reason
            promotion.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(promotion)
        return promotion

    async def complete_promotion(
        self,
        tenant_id: UUID,
        promotion_id: UUID,
        deployment_id: UUID
    ) -> Optional[EnvironmentPromotion]:
        """Complete an environment promotion."""
        promotion = await self.get_promotion(tenant_id, promotion_id)
        if promotion:
            promotion.status = DeploymentStatus.SUCCEEDED
            promotion.deployment_id = deployment_id
            promotion.promoted_at = datetime.utcnow()
            promotion.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(promotion)
        return promotion

    # =========================================================================
    # Feature Flags
    # =========================================================================

    async def create_feature_flag(
        self,
        tenant_id: UUID,
        data: FeatureFlagCreate,
        created_by: Optional[UUID] = None
    ) -> FeatureFlag:
        """Create a new feature flag."""
        flag = FeatureFlag(
            tenant_id=tenant_id,
            key=data.key,
            name=data.name,
            description=data.description,
            status=data.status,
            environment=data.environment,
            percentage_rollout=data.percentage_rollout,
            targeted_users=data.targeted_users or [],
            targeted_tenants=data.targeted_tenants or [],
            variants=data.variants or [],
            default_variant=data.default_variant,
            rules=data.rules or [],
            owner_team=data.owner_team,
            expires_at=data.expires_at,
            created_by=created_by
        )
        self.db.add(flag)
        await self.db.commit()
        await self.db.refresh(flag)
        return flag

    async def get_feature_flag(
        self,
        tenant_id: UUID,
        flag_id: UUID
    ) -> Optional[FeatureFlag]:
        """Get feature flag by ID."""
        result = await self.db.execute(
            select(FeatureFlag).where(
                and_(
                    FeatureFlag.tenant_id == tenant_id,
                    FeatureFlag.id == flag_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_feature_flag_by_key(
        self,
        tenant_id: UUID,
        key: str
    ) -> Optional[FeatureFlag]:
        """Get feature flag by key."""
        result = await self.db.execute(
            select(FeatureFlag).where(
                and_(
                    FeatureFlag.tenant_id == tenant_id,
                    FeatureFlag.key == key,
                    FeatureFlag.archived == False
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_feature_flags(
        self,
        tenant_id: UUID,
        status: Optional[FeatureFlagStatus] = None,
        environment: Optional[EnvironmentType] = None,
        include_archived: bool = False
    ) -> List[FeatureFlag]:
        """List feature flags."""
        query = select(FeatureFlag).where(FeatureFlag.tenant_id == tenant_id)

        if status:
            query = query.where(FeatureFlag.status == status)
        if environment:
            query = query.where(FeatureFlag.environment == environment)
        if not include_archived:
            query = query.where(FeatureFlag.archived == False)

        query = query.order_by(FeatureFlag.name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_feature_flag(
        self,
        tenant_id: UUID,
        flag_id: UUID,
        data: FeatureFlagUpdate
    ) -> Optional[FeatureFlag]:
        """Update a feature flag."""
        flag = await self.get_feature_flag(tenant_id, flag_id)
        if flag:
            if data.status is not None:
                flag.status = data.status
            if data.percentage_rollout is not None:
                flag.percentage_rollout = data.percentage_rollout
            if data.targeted_users is not None:
                flag.targeted_users = data.targeted_users
            if data.targeted_tenants is not None:
                flag.targeted_tenants = data.targeted_tenants
            if data.rules is not None:
                flag.rules = data.rules
            if data.archived is not None:
                flag.archived = data.archived

            flag.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(flag)
        return flag

    async def evaluate_feature_flag(
        self,
        tenant_id: UUID,
        key: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Evaluate a feature flag for a user."""
        flag = await self.get_feature_flag_by_key(tenant_id, key)
        if not flag:
            return False

        # Update evaluation stats
        flag.last_evaluated_at = datetime.utcnow()
        flag.evaluation_count += 1
        await self.db.commit()

        # Disabled flags
        if flag.status == FeatureFlagStatus.DISABLED:
            return False

        # Enabled flags
        if flag.status == FeatureFlagStatus.ENABLED:
            return True

        # User targeting
        if flag.status == FeatureFlagStatus.USER_TARGETING and user_id:
            return user_id in (flag.targeted_users or [])

        # Percentage rollout
        if flag.status == FeatureFlagStatus.PERCENTAGE_ROLLOUT:
            if flag.percentage_rollout >= 100:
                return True
            if flag.percentage_rollout <= 0:
                return False
            # Simple hash-based rollout
            if user_id:
                hash_val = hash(f"{key}:{user_id}") % 100
                return hash_val < flag.percentage_rollout
            return False

        return False

    # =========================================================================
    # Database Migrations
    # =========================================================================

    async def create_migration_record(
        self,
        tenant_id: UUID,
        data: DatabaseMigrationCreate,
        executed_by: Optional[UUID] = None
    ) -> DatabaseMigration:
        """Create a migration record."""
        migration = DatabaseMigration(
            tenant_id=tenant_id,
            migration_id=data.migration_id,
            migration_name=data.migration_name,
            database_name=data.database_name,
            environment=data.environment,
            up_sql=data.up_sql,
            down_sql=data.down_sql,
            executed_by=executed_by
        )
        self.db.add(migration)
        await self.db.commit()
        await self.db.refresh(migration)
        return migration

    async def get_migration(
        self,
        tenant_id: UUID,
        migration_id: UUID
    ) -> Optional[DatabaseMigration]:
        """Get migration by ID."""
        result = await self.db.execute(
            select(DatabaseMigration).where(
                and_(
                    DatabaseMigration.tenant_id == tenant_id,
                    DatabaseMigration.id == migration_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_migrations(
        self,
        tenant_id: UUID,
        environment: Optional[EnvironmentType] = None,
        database_name: Optional[str] = None
    ) -> List[DatabaseMigration]:
        """List database migrations."""
        query = select(DatabaseMigration).where(
            DatabaseMigration.tenant_id == tenant_id
        )
        if environment:
            query = query.where(DatabaseMigration.environment == environment)
        if database_name:
            query = query.where(DatabaseMigration.database_name == database_name)
        query = query.order_by(DatabaseMigration.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def start_migration(
        self,
        tenant_id: UUID,
        migration_id: UUID
    ) -> Optional[DatabaseMigration]:
        """Start a migration."""
        migration = await self.get_migration(tenant_id, migration_id)
        if migration:
            migration.status = DeploymentStatus.IN_PROGRESS
            migration.started_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(migration)
        return migration

    async def complete_migration(
        self,
        tenant_id: UUID,
        migration_id: UUID,
        success: bool,
        error_message: Optional[str] = None
    ) -> Optional[DatabaseMigration]:
        """Complete a migration."""
        migration = await self.get_migration(tenant_id, migration_id)
        if migration:
            migration.status = DeploymentStatus.SUCCEEDED if success else DeploymentStatus.FAILED
            migration.completed_at = datetime.utcnow()
            migration.error_message = error_message

            if migration.started_at:
                delta = datetime.utcnow() - migration.started_at
                migration.duration_seconds = int(delta.total_seconds())

            await self.db.commit()
            await self.db.refresh(migration)
        return migration

    # =========================================================================
    # Summary
    # =========================================================================

    async def get_deployment_summary(
        self,
        tenant_id: UUID
    ) -> DeploymentSummary:
        """Get deployment summary."""
        # Total deployments
        total_result = await self.db.execute(
            select(func.count(Deployment.id)).where(
                Deployment.tenant_id == tenant_id
            )
        )
        total_deployments = total_result.scalar() or 0

        # By status
        status_result = await self.db.execute(
            select(
                Deployment.status,
                func.count(Deployment.id)
            ).where(
                Deployment.tenant_id == tenant_id
            ).group_by(Deployment.status)
        )
        deployments_by_status = {str(row[0].value): row[1] for row in status_result.all()}

        # By environment
        env_result = await self.db.execute(
            select(
                Deployment.environment,
                func.count(Deployment.id)
            ).where(
                Deployment.tenant_id == tenant_id
            ).group_by(Deployment.environment)
        )
        deployments_by_environment = {str(row[0].value): row[1] for row in env_result.all()}

        # Recent deployments
        recent_result = await self.db.execute(
            select(Deployment).where(
                Deployment.tenant_id == tenant_id
            ).order_by(Deployment.created_at.desc()).limit(5)
        )
        recent_deployments = [
            DeploymentResponse.model_validate(d) for d in recent_result.scalars().all()
        ]

        # Enabled feature flags
        flags_result = await self.db.execute(
            select(func.count(FeatureFlag.id)).where(
                and_(
                    FeatureFlag.tenant_id == tenant_id,
                    FeatureFlag.status == FeatureFlagStatus.ENABLED,
                    FeatureFlag.archived == False
                )
            )
        )
        feature_flags_enabled = flags_result.scalar() or 0

        # Pending promotions
        promotions_result = await self.db.execute(
            select(func.count(EnvironmentPromotion.id)).where(
                and_(
                    EnvironmentPromotion.tenant_id == tenant_id,
                    EnvironmentPromotion.status == DeploymentStatus.PENDING
                )
            )
        )
        pending_promotions = promotions_result.scalar() or 0

        # Average deployment duration
        avg_duration_result = await self.db.execute(
            select(func.avg(Deployment.duration_seconds)).where(
                and_(
                    Deployment.tenant_id == tenant_id,
                    Deployment.duration_seconds.isnot(None),
                    Deployment.status == DeploymentStatus.SUCCEEDED
                )
            )
        )
        avg_deployment_duration_seconds = avg_duration_result.scalar()

        return DeploymentSummary(
            total_deployments=total_deployments,
            deployments_by_status=deployments_by_status,
            deployments_by_environment=deployments_by_environment,
            recent_deployments=recent_deployments,
            feature_flags_enabled=feature_flags_enabled,
            pending_promotions=pending_promotions,
            avg_deployment_duration_seconds=avg_deployment_duration_seconds
        )

"""
Infrastructure Service

Service for managing production infrastructure resources, auto-scaling, and networking.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    InfrastructureResource, AutoScalingConfig, NetworkConfig,
    ResourceType, ResourceStatus, CloudProvider, EnvironmentType
)
from ..schemas import (
    InfrastructureResourceCreate, AutoScalingConfigCreate, NetworkConfigCreate,
    InfrastructureSummary
)


class InfrastructureService:
    """Service for infrastructure management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Infrastructure Resource Management
    # =========================================================================

    async def create_resource(
        self,
        tenant_id: UUID,
        data: InfrastructureResourceCreate,
        created_by: Optional[UUID] = None
    ) -> InfrastructureResource:
        """Create a new infrastructure resource."""
        resource = InfrastructureResource(
            tenant_id=tenant_id,
            name=data.name,
            resource_type=data.resource_type,
            cloud_provider=data.cloud_provider,
            environment=data.environment,
            region=data.region,
            availability_zone=data.availability_zone,
            resource_id=data.resource_id,
            resource_arn=data.resource_arn,
            instance_type=data.instance_type,
            cpu_cores=data.cpu_cores,
            memory_gb=data.memory_gb,
            storage_gb=data.storage_gb,
            private_ip=data.private_ip,
            public_ip=data.public_ip,
            dns_name=data.dns_name,
            tags=data.tags or {},
            metadata=data.metadata or {},
            hourly_cost=data.hourly_cost or 0.0,
            monthly_cost=(data.hourly_cost or 0.0) * 24 * 30,
            terraform_resource=data.terraform_resource,
            terraform_state_key=data.terraform_state_key,
            created_by=created_by
        )
        self.db.add(resource)
        await self.db.commit()
        await self.db.refresh(resource)
        return resource

    async def get_resource(
        self,
        tenant_id: UUID,
        resource_id: UUID
    ) -> Optional[InfrastructureResource]:
        """Get a resource by ID."""
        result = await self.db.execute(
            select(InfrastructureResource).where(
                and_(
                    InfrastructureResource.tenant_id == tenant_id,
                    InfrastructureResource.id == resource_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_resources(
        self,
        tenant_id: UUID,
        environment: Optional[EnvironmentType] = None,
        resource_type: Optional[ResourceType] = None,
        status: Optional[ResourceStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[InfrastructureResource]:
        """List infrastructure resources with filtering."""
        query = select(InfrastructureResource).where(
            InfrastructureResource.tenant_id == tenant_id
        )

        if environment:
            query = query.where(InfrastructureResource.environment == environment)
        if resource_type:
            query = query.where(InfrastructureResource.resource_type == resource_type)
        if status:
            query = query.where(InfrastructureResource.status == status)

        query = query.order_by(InfrastructureResource.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_resource_status(
        self,
        tenant_id: UUID,
        resource_id: UUID,
        status: ResourceStatus
    ) -> Optional[InfrastructureResource]:
        """Update resource status."""
        resource = await self.get_resource(tenant_id, resource_id)
        if resource:
            resource.status = status
            resource.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(resource)
        return resource

    async def update_resource_cost(
        self,
        tenant_id: UUID,
        resource_id: UUID,
        hourly_cost: float
    ) -> Optional[InfrastructureResource]:
        """Update resource cost."""
        resource = await self.get_resource(tenant_id, resource_id)
        if resource:
            resource.hourly_cost = hourly_cost
            resource.monthly_cost = hourly_cost * 24 * 30
            resource.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(resource)
        return resource

    async def terminate_resource(
        self,
        tenant_id: UUID,
        resource_id: UUID
    ) -> Optional[InfrastructureResource]:
        """Mark resource as terminated."""
        return await self.update_resource_status(
            tenant_id, resource_id, ResourceStatus.TERMINATED
        )

    # =========================================================================
    # Auto-Scaling Configuration
    # =========================================================================

    async def create_auto_scaling_config(
        self,
        tenant_id: UUID,
        data: AutoScalingConfigCreate
    ) -> AutoScalingConfig:
        """Create auto-scaling configuration."""
        config = AutoScalingConfig(
            tenant_id=tenant_id,
            resource_id=data.resource_id,
            name=data.name,
            enabled=data.enabled,
            min_instances=data.min_instances,
            max_instances=data.max_instances,
            desired_instances=data.desired_instances,
            scale_up_cpu_threshold=data.scale_up_cpu_threshold,
            scale_down_cpu_threshold=data.scale_down_cpu_threshold,
            scale_up_memory_threshold=data.scale_up_memory_threshold,
            scale_down_memory_threshold=data.scale_down_memory_threshold,
            scale_up_cooldown=data.scale_up_cooldown,
            scale_down_cooldown=data.scale_down_cooldown,
            custom_metrics=data.custom_metrics or [],
            predictive_scaling_enabled=data.predictive_scaling_enabled,
            predictive_scaling_mode=data.predictive_scaling_mode
        )
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def get_auto_scaling_config(
        self,
        tenant_id: UUID,
        config_id: UUID
    ) -> Optional[AutoScalingConfig]:
        """Get auto-scaling config by ID."""
        result = await self.db.execute(
            select(AutoScalingConfig).where(
                and_(
                    AutoScalingConfig.tenant_id == tenant_id,
                    AutoScalingConfig.id == config_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_auto_scaling_configs(
        self,
        tenant_id: UUID,
        enabled_only: bool = False
    ) -> List[AutoScalingConfig]:
        """List auto-scaling configurations."""
        query = select(AutoScalingConfig).where(
            AutoScalingConfig.tenant_id == tenant_id
        )
        if enabled_only:
            query = query.where(AutoScalingConfig.enabled == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_auto_scaling_thresholds(
        self,
        tenant_id: UUID,
        config_id: UUID,
        scale_up_cpu: Optional[float] = None,
        scale_down_cpu: Optional[float] = None,
        scale_up_memory: Optional[float] = None,
        scale_down_memory: Optional[float] = None
    ) -> Optional[AutoScalingConfig]:
        """Update auto-scaling thresholds."""
        config = await self.get_auto_scaling_config(tenant_id, config_id)
        if config:
            if scale_up_cpu is not None:
                config.scale_up_cpu_threshold = scale_up_cpu
            if scale_down_cpu is not None:
                config.scale_down_cpu_threshold = scale_down_cpu
            if scale_up_memory is not None:
                config.scale_up_memory_threshold = scale_up_memory
            if scale_down_memory is not None:
                config.scale_down_memory_threshold = scale_down_memory
            config.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(config)
        return config

    # =========================================================================
    # Network Configuration
    # =========================================================================

    async def create_network_config(
        self,
        tenant_id: UUID,
        data: NetworkConfigCreate
    ) -> NetworkConfig:
        """Create network configuration."""
        config = NetworkConfig(
            tenant_id=tenant_id,
            name=data.name,
            environment=data.environment,
            vpc_id=data.vpc_id,
            vpc_cidr=data.vpc_cidr,
            public_subnets=data.public_subnets or [],
            private_subnets=data.private_subnets or [],
            database_subnets=data.database_subnets or [],
            security_groups=data.security_groups or [],
            load_balancer_arn=data.load_balancer_arn,
            load_balancer_dns=data.load_balancer_dns,
            service_mesh_enabled=data.service_mesh_enabled,
            service_mesh_type=data.service_mesh_type,
            dns_zone_id=data.dns_zone_id,
            domain_name=data.domain_name,
            waf_enabled=data.waf_enabled,
            waf_rules=data.waf_rules or [],
            ddos_protection_enabled=data.ddos_protection_enabled
        )
        self.db.add(config)
        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def get_network_config(
        self,
        tenant_id: UUID,
        config_id: UUID
    ) -> Optional[NetworkConfig]:
        """Get network config by ID."""
        result = await self.db.execute(
            select(NetworkConfig).where(
                and_(
                    NetworkConfig.tenant_id == tenant_id,
                    NetworkConfig.id == config_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_network_config_by_environment(
        self,
        tenant_id: UUID,
        environment: EnvironmentType
    ) -> Optional[NetworkConfig]:
        """Get network config for an environment."""
        result = await self.db.execute(
            select(NetworkConfig).where(
                and_(
                    NetworkConfig.tenant_id == tenant_id,
                    NetworkConfig.environment == environment
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_network_configs(
        self,
        tenant_id: UUID
    ) -> List[NetworkConfig]:
        """List network configurations."""
        result = await self.db.execute(
            select(NetworkConfig).where(NetworkConfig.tenant_id == tenant_id)
        )
        return list(result.scalars().all())

    # =========================================================================
    # Summary and Statistics
    # =========================================================================

    async def get_infrastructure_summary(
        self,
        tenant_id: UUID
    ) -> InfrastructureSummary:
        """Get infrastructure summary."""
        # Total resources
        total_result = await self.db.execute(
            select(func.count(InfrastructureResource.id)).where(
                InfrastructureResource.tenant_id == tenant_id
            )
        )
        total_resources = total_result.scalar() or 0

        # Resources by type
        type_result = await self.db.execute(
            select(
                InfrastructureResource.resource_type,
                func.count(InfrastructureResource.id)
            ).where(
                InfrastructureResource.tenant_id == tenant_id
            ).group_by(InfrastructureResource.resource_type)
        )
        resources_by_type = {str(row[0].value): row[1] for row in type_result.all()}

        # Resources by status
        status_result = await self.db.execute(
            select(
                InfrastructureResource.status,
                func.count(InfrastructureResource.id)
            ).where(
                InfrastructureResource.tenant_id == tenant_id
            ).group_by(InfrastructureResource.status)
        )
        resources_by_status = {str(row[0].value): row[1] for row in status_result.all()}

        # Resources by environment
        env_result = await self.db.execute(
            select(
                InfrastructureResource.environment,
                func.count(InfrastructureResource.id)
            ).where(
                InfrastructureResource.tenant_id == tenant_id
            ).group_by(InfrastructureResource.environment)
        )
        resources_by_environment = {str(row[0].value): row[1] for row in env_result.all()}

        # Total monthly cost
        cost_result = await self.db.execute(
            select(func.sum(InfrastructureResource.monthly_cost)).where(
                and_(
                    InfrastructureResource.tenant_id == tenant_id,
                    InfrastructureResource.status != ResourceStatus.TERMINATED
                )
            )
        )
        total_monthly_cost = cost_result.scalar() or 0.0

        # Check multi-AZ
        az_result = await self.db.execute(
            select(func.count(func.distinct(InfrastructureResource.availability_zone))).where(
                and_(
                    InfrastructureResource.tenant_id == tenant_id,
                    InfrastructureResource.environment == EnvironmentType.PRODUCTION,
                    InfrastructureResource.availability_zone.isnot(None)
                )
            )
        )
        distinct_azs = az_result.scalar() or 0
        multi_az_enabled = distinct_azs > 1

        # Auto-scaling configs count
        as_result = await self.db.execute(
            select(func.count(AutoScalingConfig.id)).where(
                and_(
                    AutoScalingConfig.tenant_id == tenant_id,
                    AutoScalingConfig.enabled == True
                )
            )
        )
        auto_scaling_configs = as_result.scalar() or 0

        return InfrastructureSummary(
            total_resources=total_resources,
            resources_by_type=resources_by_type,
            resources_by_status=resources_by_status,
            resources_by_environment=resources_by_environment,
            total_monthly_cost=total_monthly_cost,
            multi_az_enabled=multi_az_enabled,
            auto_scaling_configs=auto_scaling_configs
        )

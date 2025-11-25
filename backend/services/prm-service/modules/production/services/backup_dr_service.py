"""
Backup & Disaster Recovery Service

Service for managing backups, restore operations, DR plans, and DR drills.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    Backup, RestoreOperation, DisasterRecoveryPlan, DRDrill,
    BackupType, BackupStatus, DRScenario, DrillStatus, EnvironmentType
)
from ..schemas import (
    BackupCreate, RestoreOperationCreate, DisasterRecoveryPlanCreate,
    DRDrillCreate, DRDrillUpdate, BackupDRSummary
)


class BackupDRService:
    """Service for backup and disaster recovery management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Backup Management
    # =========================================================================

    async def _generate_backup_id(self, tenant_id: UUID) -> str:
        """Generate unique backup ID."""
        date_str = datetime.utcnow().strftime("%Y%m%d")
        result = await self.db.execute(
            select(func.count(Backup.id)).where(
                and_(
                    Backup.tenant_id == tenant_id,
                    Backup.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
                )
            )
        )
        count = result.scalar() or 0
        return f"BKP-{date_str}-{count + 1:03d}"

    async def create_backup(
        self,
        tenant_id: UUID,
        data: BackupCreate,
        created_by: Optional[UUID] = None
    ) -> Backup:
        """Create a new backup."""
        backup_id = await self._generate_backup_id(tenant_id)

        backup = Backup(
            tenant_id=tenant_id,
            backup_id=backup_id,
            backup_type=data.backup_type,
            source_database=data.source_database,
            source_region=data.source_region,
            source_environment=data.source_environment,
            storage_location=data.storage_location,
            storage_region=data.storage_region,
            cross_region_copy=data.cross_region_copy,
            cross_region_location=data.cross_region_location,
            encrypted=data.encrypted,
            encryption_key_id=data.encryption_key_id,
            retention_days=data.retention_days,
            expires_at=datetime.utcnow() + timedelta(days=data.retention_days),
            pitr_enabled=data.pitr_enabled,
            metadata=data.metadata or {},
            tags=data.tags or {},
            created_by=created_by
        )
        self.db.add(backup)
        await self.db.commit()
        await self.db.refresh(backup)
        return backup

    async def get_backup(
        self,
        tenant_id: UUID,
        backup_id: UUID
    ) -> Optional[Backup]:
        """Get backup by ID."""
        result = await self.db.execute(
            select(Backup).where(
                and_(
                    Backup.tenant_id == tenant_id,
                    Backup.id == backup_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_backups(
        self,
        tenant_id: UUID,
        source_database: Optional[str] = None,
        environment: Optional[EnvironmentType] = None,
        status: Optional[BackupStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Backup]:
        """List backups."""
        query = select(Backup).where(Backup.tenant_id == tenant_id)

        if source_database:
            query = query.where(Backup.source_database == source_database)
        if environment:
            query = query.where(Backup.source_environment == environment)
        if status:
            query = query.where(Backup.status == status)

        query = query.order_by(Backup.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def start_backup(
        self,
        tenant_id: UUID,
        backup_id: UUID
    ) -> Optional[Backup]:
        """Start a backup operation."""
        backup = await self.get_backup(tenant_id, backup_id)
        if backup:
            backup.status = BackupStatus.IN_PROGRESS
            backup.started_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(backup)
        return backup

    async def complete_backup(
        self,
        tenant_id: UUID,
        backup_id: UUID,
        success: bool,
        size_bytes: Optional[float] = None
    ) -> Optional[Backup]:
        """Complete a backup operation."""
        backup = await self.get_backup(tenant_id, backup_id)
        if backup:
            backup.status = BackupStatus.COMPLETED if success else BackupStatus.FAILED
            backup.completed_at = datetime.utcnow()
            backup.size_bytes = size_bytes

            if backup.started_at:
                delta = datetime.utcnow() - backup.started_at
                backup.duration_seconds = int(delta.total_seconds())

            await self.db.commit()
            await self.db.refresh(backup)
        return backup

    async def verify_backup(
        self,
        tenant_id: UUID,
        backup_id: UUID,
        verification_result: Dict[str, Any]
    ) -> Optional[Backup]:
        """Mark backup as verified."""
        backup = await self.get_backup(tenant_id, backup_id)
        if backup:
            backup.verified = True
            backup.verified_at = datetime.utcnow()
            backup.verification_result = verification_result
            backup.status = BackupStatus.VERIFIED
            await self.db.commit()
            await self.db.refresh(backup)
        return backup

    async def get_latest_backup(
        self,
        tenant_id: UUID,
        source_database: str,
        environment: EnvironmentType
    ) -> Optional[Backup]:
        """Get the latest verified backup."""
        result = await self.db.execute(
            select(Backup).where(
                and_(
                    Backup.tenant_id == tenant_id,
                    Backup.source_database == source_database,
                    Backup.source_environment == environment,
                    Backup.status.in_([BackupStatus.COMPLETED, BackupStatus.VERIFIED])
                )
            ).order_by(Backup.completed_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def expire_old_backups(
        self,
        tenant_id: UUID
    ) -> int:
        """Mark expired backups as expired."""
        result = await self.db.execute(
            select(Backup).where(
                and_(
                    Backup.tenant_id == tenant_id,
                    Backup.expires_at < datetime.utcnow(),
                    Backup.status.notin_([BackupStatus.EXPIRED])
                )
            )
        )
        backups = list(result.scalars().all())
        count = 0
        for backup in backups:
            backup.status = BackupStatus.EXPIRED
            count += 1
        await self.db.commit()
        return count

    # =========================================================================
    # Restore Operations
    # =========================================================================

    async def _generate_restore_id(self, tenant_id: UUID) -> str:
        """Generate unique restore ID."""
        date_str = datetime.utcnow().strftime("%Y%m%d")
        result = await self.db.execute(
            select(func.count(RestoreOperation.id)).where(
                and_(
                    RestoreOperation.tenant_id == tenant_id,
                    RestoreOperation.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
                )
            )
        )
        count = result.scalar() or 0
        return f"RST-{date_str}-{count + 1:03d}"

    async def create_restore(
        self,
        tenant_id: UUID,
        data: RestoreOperationCreate,
        initiated_by: Optional[UUID] = None
    ) -> RestoreOperation:
        """Create a restore operation."""
        restore_id = await self._generate_restore_id(tenant_id)

        restore = RestoreOperation(
            tenant_id=tenant_id,
            backup_id=data.backup_id,
            restore_id=restore_id,
            target_database=data.target_database,
            target_environment=data.target_environment,
            restore_to_point_in_time=data.restore_to_point_in_time,
            initiated_by=initiated_by
        )
        self.db.add(restore)
        await self.db.commit()
        await self.db.refresh(restore)
        return restore

    async def get_restore(
        self,
        tenant_id: UUID,
        restore_id: UUID
    ) -> Optional[RestoreOperation]:
        """Get restore operation by ID."""
        result = await self.db.execute(
            select(RestoreOperation).where(
                and_(
                    RestoreOperation.tenant_id == tenant_id,
                    RestoreOperation.id == restore_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_restores(
        self,
        tenant_id: UUID,
        status: Optional[BackupStatus] = None
    ) -> List[RestoreOperation]:
        """List restore operations."""
        query = select(RestoreOperation).where(
            RestoreOperation.tenant_id == tenant_id
        )
        if status:
            query = query.where(RestoreOperation.status == status)
        query = query.order_by(RestoreOperation.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def start_restore(
        self,
        tenant_id: UUID,
        restore_id: UUID
    ) -> Optional[RestoreOperation]:
        """Start a restore operation."""
        restore = await self.get_restore(tenant_id, restore_id)
        if restore:
            restore.status = BackupStatus.IN_PROGRESS
            restore.started_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(restore)
        return restore

    async def complete_restore(
        self,
        tenant_id: UUID,
        restore_id: UUID,
        success: bool,
        error_message: Optional[str] = None,
        verification_details: Optional[Dict[str, Any]] = None
    ) -> Optional[RestoreOperation]:
        """Complete a restore operation."""
        restore = await self.get_restore(tenant_id, restore_id)
        if restore:
            restore.status = BackupStatus.COMPLETED if success else BackupStatus.FAILED
            restore.completed_at = datetime.utcnow()
            restore.error_message = error_message
            restore.data_verification_passed = success
            restore.verification_details = verification_details

            if restore.started_at:
                delta = datetime.utcnow() - restore.started_at
                restore.duration_seconds = int(delta.total_seconds())

            await self.db.commit()
            await self.db.refresh(restore)
        return restore

    # =========================================================================
    # Disaster Recovery Plans
    # =========================================================================

    async def create_dr_plan(
        self,
        tenant_id: UUID,
        data: DisasterRecoveryPlanCreate,
        created_by: Optional[UUID] = None
    ) -> DisasterRecoveryPlan:
        """Create a DR plan."""
        plan = DisasterRecoveryPlan(
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            scenario=data.scenario,
            rto_hours=data.rto_hours,
            rpo_hours=data.rpo_hours,
            recovery_steps=data.recovery_steps,
            communication_plan=data.communication_plan,
            escalation_contacts=data.escalation_contacts or [],
            primary_region=data.primary_region,
            dr_region=data.dr_region,
            affected_services=data.affected_services or [],
            test_frequency_days=data.test_frequency_days,
            next_test_date=datetime.utcnow() + timedelta(days=data.test_frequency_days),
            created_by=created_by
        )
        self.db.add(plan)
        await self.db.commit()
        await self.db.refresh(plan)
        return plan

    async def get_dr_plan(
        self,
        tenant_id: UUID,
        plan_id: UUID
    ) -> Optional[DisasterRecoveryPlan]:
        """Get DR plan by ID."""
        result = await self.db.execute(
            select(DisasterRecoveryPlan).where(
                and_(
                    DisasterRecoveryPlan.tenant_id == tenant_id,
                    DisasterRecoveryPlan.id == plan_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_dr_plans(
        self,
        tenant_id: UUID,
        scenario: Optional[DRScenario] = None,
        active_only: bool = False
    ) -> List[DisasterRecoveryPlan]:
        """List DR plans."""
        query = select(DisasterRecoveryPlan).where(
            DisasterRecoveryPlan.tenant_id == tenant_id
        )
        if scenario:
            query = query.where(DisasterRecoveryPlan.scenario == scenario)
        if active_only:
            query = query.where(DisasterRecoveryPlan.is_active == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_dr_plan(
        self,
        tenant_id: UUID,
        plan_id: UUID,
        recovery_steps: Optional[List[Dict[str, Any]]] = None,
        rto_hours: Optional[float] = None,
        rpo_hours: Optional[float] = None
    ) -> Optional[DisasterRecoveryPlan]:
        """Update a DR plan."""
        plan = await self.get_dr_plan(tenant_id, plan_id)
        if plan:
            if recovery_steps is not None:
                plan.recovery_steps = recovery_steps
            if rto_hours is not None:
                plan.rto_hours = rto_hours
            if rpo_hours is not None:
                plan.rpo_hours = rpo_hours

            plan.version += 1
            plan.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(plan)
        return plan

    async def get_plans_needing_test(
        self,
        tenant_id: UUID
    ) -> List[DisasterRecoveryPlan]:
        """Get DR plans that need testing."""
        result = await self.db.execute(
            select(DisasterRecoveryPlan).where(
                and_(
                    DisasterRecoveryPlan.tenant_id == tenant_id,
                    DisasterRecoveryPlan.is_active == True,
                    DisasterRecoveryPlan.next_test_date <= datetime.utcnow()
                )
            )
        )
        return list(result.scalars().all())

    # =========================================================================
    # DR Drills
    # =========================================================================

    async def _generate_drill_id(self, tenant_id: UUID) -> str:
        """Generate unique drill ID."""
        date_str = datetime.utcnow().strftime("%Y%m%d")
        result = await self.db.execute(
            select(func.count(DRDrill.id)).where(
                and_(
                    DRDrill.tenant_id == tenant_id,
                    DRDrill.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
                )
            )
        )
        count = result.scalar() or 0
        return f"DRILL-{date_str}-{count + 1:03d}"

    async def create_dr_drill(
        self,
        tenant_id: UUID,
        data: DRDrillCreate
    ) -> DRDrill:
        """Create a DR drill."""
        drill_id = await self._generate_drill_id(tenant_id)

        drill = DRDrill(
            tenant_id=tenant_id,
            dr_plan_id=data.dr_plan_id,
            drill_id=drill_id,
            scheduled_at=data.scheduled_at,
            participants=data.participants or [],
            coordinator=data.coordinator
        )
        self.db.add(drill)
        await self.db.commit()
        await self.db.refresh(drill)
        return drill

    async def get_dr_drill(
        self,
        tenant_id: UUID,
        drill_id: UUID
    ) -> Optional[DRDrill]:
        """Get DR drill by ID."""
        result = await self.db.execute(
            select(DRDrill).where(
                and_(
                    DRDrill.tenant_id == tenant_id,
                    DRDrill.id == drill_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_dr_drills(
        self,
        tenant_id: UUID,
        dr_plan_id: Optional[UUID] = None,
        status: Optional[DrillStatus] = None
    ) -> List[DRDrill]:
        """List DR drills."""
        query = select(DRDrill).where(DRDrill.tenant_id == tenant_id)
        if dr_plan_id:
            query = query.where(DRDrill.dr_plan_id == dr_plan_id)
        if status:
            query = query.where(DRDrill.status == status)
        query = query.order_by(DRDrill.scheduled_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def start_dr_drill(
        self,
        tenant_id: UUID,
        drill_id: UUID
    ) -> Optional[DRDrill]:
        """Start a DR drill."""
        drill = await self.get_dr_drill(tenant_id, drill_id)
        if drill:
            drill.status = DrillStatus.IN_PROGRESS
            drill.started_at = datetime.utcnow()
            drill.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(drill)
        return drill

    async def update_dr_drill(
        self,
        tenant_id: UUID,
        drill_id: UUID,
        data: DRDrillUpdate
    ) -> Optional[DRDrill]:
        """Update DR drill."""
        drill = await self.get_dr_drill(tenant_id, drill_id)
        if drill:
            if data.status is not None:
                drill.status = data.status
                if data.status == DrillStatus.COMPLETED:
                    drill.completed_at = datetime.utcnow()
            if data.steps_completed is not None:
                drill.steps_completed = data.steps_completed
            if data.issues_encountered is not None:
                drill.issues_encountered = data.issues_encountered
            if data.rto_achieved_minutes is not None:
                drill.rto_achieved_minutes = data.rto_achieved_minutes
            if data.rpo_achieved_minutes is not None:
                drill.rpo_achieved_minutes = data.rpo_achieved_minutes
            if data.lessons_learned is not None:
                drill.lessons_learned = data.lessons_learned
            if data.action_items is not None:
                drill.action_items = data.action_items
            if data.drill_report_url is not None:
                drill.drill_report_url = data.drill_report_url

            drill.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(drill)
        return drill

    async def complete_dr_drill(
        self,
        tenant_id: UUID,
        drill_id: UUID,
        rto_achieved_minutes: float,
        rpo_achieved_minutes: float,
        lessons_learned: str,
        action_items: List[Dict[str, Any]]
    ) -> Optional[DRDrill]:
        """Complete a DR drill with results."""
        drill = await self.get_dr_drill(tenant_id, drill_id)
        if drill:
            drill.status = DrillStatus.COMPLETED
            drill.completed_at = datetime.utcnow()
            drill.rto_achieved_minutes = rto_achieved_minutes
            drill.rpo_achieved_minutes = rpo_achieved_minutes
            drill.lessons_learned = lessons_learned
            drill.action_items = action_items

            # Check against targets
            dr_plan = await self.get_dr_plan(tenant_id, drill.dr_plan_id)
            if dr_plan:
                drill.rto_target_met = rto_achieved_minutes <= (dr_plan.rto_hours * 60)
                drill.rpo_target_met = rpo_achieved_minutes <= (dr_plan.rpo_hours * 60)
                drill.success = drill.rto_target_met and drill.rpo_target_met

                # Update DR plan test info
                dr_plan.last_tested_at = datetime.utcnow()
                dr_plan.last_test_result = "passed" if drill.success else "failed"
                dr_plan.next_test_date = datetime.utcnow() + timedelta(days=dr_plan.test_frequency_days)

            drill.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(drill)
        return drill

    # =========================================================================
    # Summary
    # =========================================================================

    async def get_backup_dr_summary(
        self,
        tenant_id: UUID
    ) -> BackupDRSummary:
        """Get backup and DR summary."""
        # Total backups
        total_backups_result = await self.db.execute(
            select(func.count(Backup.id)).where(Backup.tenant_id == tenant_id)
        )
        total_backups = total_backups_result.scalar() or 0

        # Backups by status
        status_result = await self.db.execute(
            select(
                Backup.status,
                func.count(Backup.id)
            ).where(
                Backup.tenant_id == tenant_id
            ).group_by(Backup.status)
        )
        backups_by_status = {str(row[0].value): row[1] for row in status_result.all()}

        # Latest backup
        latest_backup = await self.db.execute(
            select(Backup.completed_at).where(
                and_(
                    Backup.tenant_id == tenant_id,
                    Backup.status.in_([BackupStatus.COMPLETED, BackupStatus.VERIFIED])
                )
            ).order_by(Backup.completed_at.desc()).limit(1)
        )
        latest_backup_at = latest_backup.scalar()

        # Any verified backup recently
        verified_result = await self.db.execute(
            select(func.count(Backup.id)).where(
                and_(
                    Backup.tenant_id == tenant_id,
                    Backup.verified == True,
                    Backup.verified_at >= datetime.utcnow() - timedelta(days=7)
                )
            )
        )
        backup_verified = (verified_result.scalar() or 0) > 0

        # DR Plans
        dr_plans_result = await self.db.execute(
            select(func.count(DisasterRecoveryPlan.id)).where(
                and_(
                    DisasterRecoveryPlan.tenant_id == tenant_id,
                    DisasterRecoveryPlan.is_active == True
                )
            )
        )
        total_dr_plans = dr_plans_result.scalar() or 0

        # DR Plans tested
        tested_result = await self.db.execute(
            select(func.count(DisasterRecoveryPlan.id)).where(
                and_(
                    DisasterRecoveryPlan.tenant_id == tenant_id,
                    DisasterRecoveryPlan.is_active == True,
                    DisasterRecoveryPlan.last_tested_at.isnot(None)
                )
            )
        )
        dr_plans_tested = tested_result.scalar() or 0

        # Next DR drill
        next_drill_result = await self.db.execute(
            select(DRDrill.scheduled_at).where(
                and_(
                    DRDrill.tenant_id == tenant_id,
                    DRDrill.status == DrillStatus.SCHEDULED,
                    DRDrill.scheduled_at >= datetime.utcnow()
                )
            ).order_by(DRDrill.scheduled_at).limit(1)
        )
        next_dr_drill = next_drill_result.scalar()

        # Get average RTO/RPO from active plans
        rto_rpo_result = await self.db.execute(
            select(
                func.avg(DisasterRecoveryPlan.rto_hours),
                func.avg(DisasterRecoveryPlan.rpo_hours)
            ).where(
                and_(
                    DisasterRecoveryPlan.tenant_id == tenant_id,
                    DisasterRecoveryPlan.is_active == True
                )
            )
        )
        row = rto_rpo_result.one_or_none()
        rto_hours = row[0] if row else None
        rpo_hours = row[1] if row else None

        return BackupDRSummary(
            total_backups=total_backups,
            backups_by_status=backups_by_status,
            latest_backup_at=latest_backup_at,
            backup_verified=backup_verified,
            total_dr_plans=total_dr_plans,
            dr_plans_tested=dr_plans_tested,
            next_dr_drill=next_dr_drill,
            rto_hours=rto_hours,
            rpo_hours=rpo_hours
        )

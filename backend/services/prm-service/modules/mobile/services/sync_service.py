"""
Mobile Sync Service
EPIC-016: Delta sync and offline data management
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
import hashlib
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func, desc

from modules.mobile.models import (
    MobileDevice, SyncCheckpoint, SyncQueue, SyncConflict,
    SyncEntityType, SyncOperationType, SyncStatus
)
from modules.mobile.schemas import (
    SyncRequest, SyncChange, SyncResponse, SyncPush,
    SyncPushResult, SyncConflictResolve, SyncStatusResponse
)


class MobileSyncService:
    """
    Handles mobile data synchronization:
    - Delta sync for efficient data transfer
    - Offline queue management
    - Conflict detection and resolution
    - Entity-based sync checkpoints
    """

    # Entity type to model/table mapping
    ENTITY_MODELS = {
        SyncEntityType.PATIENT: "Patient",
        SyncEntityType.APPOINTMENT: "Appointment",
        SyncEntityType.MEDICATION: "Medication",
        SyncEntityType.OBSERVATION: "Observation",
        SyncEntityType.CONDITION: "Condition",
        SyncEntityType.DOCUMENT: "DocumentReference",
        SyncEntityType.MESSAGE: "SecureMessage",
        SyncEntityType.CARE_PLAN: "CarePlan",
        SyncEntityType.TASK: "Task",
        SyncEntityType.NOTIFICATION: "PushNotification",
        SyncEntityType.PREFERENCE: "NotificationPreference"
    }

    async def pull_changes(
        self,
        db: AsyncSession,
        device_id: UUID,
        user_id: UUID,
        tenant_id: UUID,
        data: SyncRequest
    ) -> SyncResponse:
        """
        Pull changes from server since last sync checkpoint.
        Implements delta sync - only returns changed records.
        """

        changes = []
        new_checkpoints = {}

        for entity_type in data.entity_types:
            entity_enum = SyncEntityType(entity_type.value)

            # Get last checkpoint for this entity type
            checkpoint = await self._get_checkpoint(
                db, device_id, entity_enum
            )
            last_sync = checkpoint.last_sync_at if checkpoint else None

            # Get changes since checkpoint
            entity_changes = await self._get_entity_changes(
                db, tenant_id, user_id, entity_enum, last_sync, data.limit
            )

            for change in entity_changes:
                changes.append(SyncChange(
                    entity_type=entity_type,
                    entity_id=change["id"],
                    operation=change["operation"],
                    data=change["data"],
                    version=change["version"],
                    timestamp=change["timestamp"]
                ))

            # Track new checkpoint time
            if entity_changes:
                new_checkpoints[entity_type.value] = max(
                    c["timestamp"] for c in entity_changes
                )
            else:
                new_checkpoints[entity_type.value] = datetime.now(timezone.utc)

        # Check for pending conflicts
        conflicts = await self._get_pending_conflicts(db, device_id)

        return SyncResponse(
            changes=changes,
            has_more=len(changes) >= data.limit,
            sync_token=self._generate_sync_token(new_checkpoints),
            server_time=datetime.now(timezone.utc),
            conflicts=[{
                "id": str(c.id),
                "entity_type": c.entity_type.value,
                "entity_id": str(c.entity_id),
                "client_data": c.client_data,
                "server_data": c.server_data
            } for c in conflicts]
        )

    async def push_changes(
        self,
        db: AsyncSession,
        device_id: UUID,
        user_id: UUID,
        tenant_id: UUID,
        data: SyncPush
    ) -> SyncPushResult:
        """
        Push local changes from device to server.
        Handles conflict detection and resolution.
        """

        successful = []
        failed = []
        conflicts = []

        for change in data.changes:
            try:
                result = await self._process_change(
                    db, tenant_id, user_id, device_id, change
                )

                if result["status"] == "success":
                    successful.append(str(change.entity_id))
                elif result["status"] == "conflict":
                    conflicts.append({
                        "entity_type": change.entity_type.value,
                        "entity_id": str(change.entity_id),
                        "client_version": change.version,
                        "server_version": result["server_version"],
                        "server_data": result["server_data"]
                    })
                else:
                    failed.append({
                        "entity_id": str(change.entity_id),
                        "error": result.get("error", "Unknown error")
                    })
            except Exception as e:
                failed.append({
                    "entity_id": str(change.entity_id),
                    "error": str(e)
                })

        await db.commit()

        return SyncPushResult(
            successful=successful,
            failed=failed,
            conflicts=conflicts,
            server_time=datetime.now(timezone.utc)
        )

    async def resolve_conflict(
        self,
        db: AsyncSession,
        conflict_id: UUID,
        device_id: UUID,
        data: SyncConflictResolve
    ) -> Dict[str, Any]:
        """Resolve a sync conflict"""

        result = await db.execute(
            select(SyncConflict).where(
                and_(
                    SyncConflict.id == conflict_id,
                    SyncConflict.device_id == device_id,
                    SyncConflict.status == SyncStatus.PENDING
                )
            )
        )
        conflict = result.scalar_one_or_none()

        if not conflict:
            raise ValueError("Conflict not found or already resolved")

        if data.resolution == "client":
            # Apply client version
            await self._apply_entity_change(
                db,
                conflict.tenant_id,
                conflict.entity_type,
                conflict.entity_id,
                SyncOperationType.UPDATE,
                conflict.client_data
            )
            conflict.resolved_with = "client"
        elif data.resolution == "server":
            # Keep server version (no action needed)
            conflict.resolved_with = "server"
        elif data.resolution == "merge":
            # Apply merged data
            await self._apply_entity_change(
                db,
                conflict.tenant_id,
                conflict.entity_type,
                conflict.entity_id,
                SyncOperationType.UPDATE,
                data.merged_data
            )
            conflict.resolved_with = "merge"
            conflict.resolved_data = data.merged_data

        conflict.status = SyncStatus.COMPLETED
        conflict.resolved_at = datetime.now(timezone.utc)

        await db.commit()

        return {
            "conflict_id": str(conflict_id),
            "status": "resolved",
            "resolution": data.resolution
        }

    async def get_sync_status(
        self,
        db: AsyncSession,
        device_id: UUID,
        user_id: UUID
    ) -> SyncStatusResponse:
        """Get current sync status for a device"""

        # Get all checkpoints
        result = await db.execute(
            select(SyncCheckpoint).where(
                SyncCheckpoint.device_id == device_id
            )
        )
        checkpoints = result.scalars().all()

        # Get pending queue items
        queue_result = await db.execute(
            select(func.count()).where(
                and_(
                    SyncQueue.device_id == device_id,
                    SyncQueue.status == SyncStatus.PENDING
                )
            )
        )
        pending_count = queue_result.scalar()

        # Get pending conflicts
        conflict_result = await db.execute(
            select(func.count()).where(
                and_(
                    SyncConflict.device_id == device_id,
                    SyncConflict.status == SyncStatus.PENDING
                )
            )
        )
        conflict_count = conflict_result.scalar()

        # Last sync time (most recent checkpoint)
        last_sync = None
        if checkpoints:
            last_sync = max(c.last_sync_at for c in checkpoints if c.last_sync_at)

        return SyncStatusResponse(
            is_synced=pending_count == 0 and conflict_count == 0,
            pending_changes=pending_count,
            pending_conflicts=conflict_count,
            last_sync_at=last_sync,
            checkpoints={
                c.entity_type.value: {
                    "last_sync_at": c.last_sync_at.isoformat() if c.last_sync_at else None,
                    "sync_version": c.sync_version
                } for c in checkpoints
            }
        )

    async def queue_offline_change(
        self,
        db: AsyncSession,
        device_id: UUID,
        user_id: UUID,
        tenant_id: UUID,
        entity_type: SyncEntityType,
        entity_id: UUID,
        operation: SyncOperationType,
        data: Dict[str, Any]
    ) -> UUID:
        """Queue a change made offline for later sync"""

        queue_item = SyncQueue(
            id=uuid4(),
            tenant_id=tenant_id,
            device_id=device_id,
            entity_type=entity_type,
            entity_id=entity_id,
            operation=operation,
            data=data,
            status=SyncStatus.PENDING,
            client_timestamp=data.get("_client_timestamp", datetime.now(timezone.utc))
        )
        db.add(queue_item)
        await db.commit()

        return queue_item.id

    async def process_offline_queue(
        self,
        db: AsyncSession,
        device_id: UUID,
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """Process pending items in the offline queue"""

        result = await db.execute(
            select(SyncQueue).where(
                and_(
                    SyncQueue.device_id == device_id,
                    SyncQueue.status == SyncStatus.PENDING
                )
            ).order_by(SyncQueue.client_timestamp).limit(batch_size)
        )
        queue_items = result.scalars().all()

        processed = 0
        failed = 0
        conflicts = 0

        for item in queue_items:
            try:
                # Check for conflicts
                if item.operation in [SyncOperationType.UPDATE, SyncOperationType.DELETE]:
                    has_conflict = await self._check_conflict(
                        db, item.entity_type, item.entity_id, item.client_timestamp
                    )

                    if has_conflict:
                        # Create conflict record
                        await self._create_conflict(db, item)
                        item.status = SyncStatus.CONFLICT
                        conflicts += 1
                        continue

                # Apply change
                success = await self._apply_entity_change(
                    db,
                    item.tenant_id,
                    item.entity_type,
                    item.entity_id,
                    item.operation,
                    item.data
                )

                if success:
                    item.status = SyncStatus.COMPLETED
                    item.processed_at = datetime.now(timezone.utc)
                    processed += 1
                else:
                    item.status = SyncStatus.FAILED
                    item.error_message = "Failed to apply change"
                    item.retry_count += 1
                    failed += 1

            except Exception as e:
                item.status = SyncStatus.FAILED
                item.error_message = str(e)
                item.retry_count += 1
                failed += 1

        await db.commit()

        return {
            "processed": processed,
            "failed": failed,
            "conflicts": conflicts,
            "remaining": await self._get_queue_count(db, device_id)
        }

    async def update_checkpoint(
        self,
        db: AsyncSession,
        device_id: UUID,
        entity_type: SyncEntityType,
        sync_time: datetime,
        sync_version: int = None
    ) -> None:
        """Update sync checkpoint for an entity type"""

        result = await db.execute(
            select(SyncCheckpoint).where(
                and_(
                    SyncCheckpoint.device_id == device_id,
                    SyncCheckpoint.entity_type == entity_type
                )
            )
        )
        checkpoint = result.scalar_one_or_none()

        if checkpoint:
            checkpoint.last_sync_at = sync_time
            if sync_version:
                checkpoint.sync_version = sync_version
        else:
            checkpoint = SyncCheckpoint(
                id=uuid4(),
                device_id=device_id,
                entity_type=entity_type,
                last_sync_at=sync_time,
                sync_version=sync_version or 1
            )
            db.add(checkpoint)

        await db.commit()

    async def reset_sync(
        self,
        db: AsyncSession,
        device_id: UUID,
        entity_types: List[SyncEntityType] = None
    ) -> None:
        """Reset sync state for a device (full re-sync required)"""

        # Delete checkpoints
        query = delete(SyncCheckpoint).where(
            SyncCheckpoint.device_id == device_id
        )
        if entity_types:
            query = query.where(SyncCheckpoint.entity_type.in_(entity_types))
        await db.execute(query)

        # Clear queue
        queue_query = delete(SyncQueue).where(
            SyncQueue.device_id == device_id
        )
        if entity_types:
            queue_query = queue_query.where(SyncQueue.entity_type.in_(entity_types))
        await db.execute(queue_query)

        # Clear conflicts
        conflict_query = delete(SyncConflict).where(
            SyncConflict.device_id == device_id
        )
        if entity_types:
            conflict_query = conflict_query.where(SyncConflict.entity_type.in_(entity_types))
        await db.execute(conflict_query)

        await db.commit()

    async def get_full_sync_data(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        entity_types: List[SyncEntityType],
        page: int = 1,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """Get full data for initial sync (no delta)"""

        data = {}
        total_records = 0

        for entity_type in entity_types:
            records = await self._get_all_entity_data(
                db, tenant_id, user_id, entity_type, page, page_size
            )
            data[entity_type.value] = records
            total_records += len(records)

        return {
            "data": data,
            "page": page,
            "page_size": page_size,
            "total_records": total_records,
            "sync_token": self._generate_sync_token({
                et.value: datetime.now(timezone.utc) for et in entity_types
            })
        }

    # Private helper methods

    async def _get_checkpoint(
        self,
        db: AsyncSession,
        device_id: UUID,
        entity_type: SyncEntityType
    ) -> Optional[SyncCheckpoint]:
        """Get checkpoint for entity type"""

        result = await db.execute(
            select(SyncCheckpoint).where(
                and_(
                    SyncCheckpoint.device_id == device_id,
                    SyncCheckpoint.entity_type == entity_type
                )
            )
        )
        return result.scalar_one_or_none()

    async def _get_entity_changes(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        entity_type: SyncEntityType,
        since: Optional[datetime],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Get changes for an entity type since a timestamp.
        This would query the actual entity tables.
        """

        # This is a simplified implementation.
        # In production, this would query actual entity tables
        # and track changes via updated_at timestamps or change logs.

        changes = []

        # Example: For appointments, would query Appointment table
        # and return records where updated_at > since

        # Placeholder - would be implemented per entity type
        # based on actual FHIR resource models

        return changes

    async def _get_all_entity_data(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        entity_type: SyncEntityType,
        page: int,
        page_size: int
    ) -> List[Dict[str, Any]]:
        """Get all data for an entity type (full sync)"""

        # Would query actual entity tables
        # Placeholder implementation
        return []

    async def _process_change(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        device_id: UUID,
        change: SyncChange
    ) -> Dict[str, Any]:
        """Process a single change from client"""

        entity_type = SyncEntityType(change.entity_type.value)
        operation = SyncOperationType(change.operation.value)

        # Check for version conflict on updates
        if operation == SyncOperationType.UPDATE:
            server_version = await self._get_entity_version(
                db, entity_type, change.entity_id
            )

            if server_version and server_version > change.version:
                # Conflict detected
                server_data = await self._get_entity_data(
                    db, entity_type, change.entity_id
                )

                # Create conflict record
                conflict = SyncConflict(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    device_id=device_id,
                    entity_type=entity_type,
                    entity_id=change.entity_id,
                    client_version=change.version,
                    server_version=server_version,
                    client_data=change.data,
                    server_data=server_data,
                    status=SyncStatus.PENDING
                )
                db.add(conflict)

                return {
                    "status": "conflict",
                    "server_version": server_version,
                    "server_data": server_data
                }

        # Apply the change
        success = await self._apply_entity_change(
            db, tenant_id, entity_type, change.entity_id, operation, change.data
        )

        if success:
            return {"status": "success"}
        else:
            return {"status": "failed", "error": "Failed to apply change"}

    async def _apply_entity_change(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        entity_type: SyncEntityType,
        entity_id: UUID,
        operation: SyncOperationType,
        data: Dict[str, Any]
    ) -> bool:
        """Apply a change to an entity"""

        # This would interact with actual entity services
        # Placeholder - would be implemented per entity type

        return True

    async def _get_entity_version(
        self,
        db: AsyncSession,
        entity_type: SyncEntityType,
        entity_id: UUID
    ) -> Optional[int]:
        """Get current version of an entity"""

        # Would query entity table for version/meta.versionId
        return None

    async def _get_entity_data(
        self,
        db: AsyncSession,
        entity_type: SyncEntityType,
        entity_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Get current data for an entity"""

        # Would query entity table
        return None

    async def _check_conflict(
        self,
        db: AsyncSession,
        entity_type: SyncEntityType,
        entity_id: UUID,
        client_timestamp: datetime
    ) -> bool:
        """Check if there's a conflict with server data"""

        # Would compare server updated_at with client_timestamp
        return False

    async def _create_conflict(
        self,
        db: AsyncSession,
        queue_item: SyncQueue
    ) -> None:
        """Create a conflict record from a queue item"""

        server_data = await self._get_entity_data(
            db, queue_item.entity_type, queue_item.entity_id
        )

        conflict = SyncConflict(
            id=uuid4(),
            tenant_id=queue_item.tenant_id,
            device_id=queue_item.device_id,
            entity_type=queue_item.entity_type,
            entity_id=queue_item.entity_id,
            client_data=queue_item.data,
            server_data=server_data,
            status=SyncStatus.PENDING
        )
        db.add(conflict)

    async def _get_pending_conflicts(
        self,
        db: AsyncSession,
        device_id: UUID
    ) -> List[SyncConflict]:
        """Get pending conflicts for a device"""

        result = await db.execute(
            select(SyncConflict).where(
                and_(
                    SyncConflict.device_id == device_id,
                    SyncConflict.status == SyncStatus.PENDING
                )
            )
        )
        return result.scalars().all()

    async def _get_queue_count(
        self,
        db: AsyncSession,
        device_id: UUID
    ) -> int:
        """Get count of pending queue items"""

        result = await db.execute(
            select(func.count()).where(
                and_(
                    SyncQueue.device_id == device_id,
                    SyncQueue.status == SyncStatus.PENDING
                )
            )
        )
        return result.scalar()

    def _generate_sync_token(
        self,
        checkpoints: Dict[str, datetime]
    ) -> str:
        """Generate a sync token from checkpoints"""

        data = json.dumps({
            k: v.isoformat() if isinstance(v, datetime) else str(v)
            for k, v in checkpoints.items()
        }, sort_keys=True)

        return hashlib.sha256(data.encode()).hexdigest()[:32]

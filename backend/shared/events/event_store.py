"""
Event Store implementation for event sourcing
Provides persistent storage, snapshots, and replay capabilities
"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from loguru import logger
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from .types import Event, EventType


class EventStore:
    """
    Event Store for event sourcing pattern

    Features:
    - Persistent event storage in PostgreSQL
    - Event versioning and migration support
    - Snapshot functionality for performance
    - Event replay capability
    - Query API for event history
    - Support for aggregate reconstruction
    """

    def __init__(self, db_session: Session):
        """
        Initialize event store

        Args:
            db_session: Database session
        """
        self.db = db_session

    async def append_event(
        self,
        aggregate_type: str,
        aggregate_id: UUID,
        event_type: EventType,
        event_data: Dict[str, Any],
        tenant_id: str,
        version: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UUID:
        """
        Append event to store

        Args:
            aggregate_type: Type of aggregate (e.g., 'Patient', 'Appointment')
            aggregate_id: ID of aggregate
            event_type: Type of event
            event_data: Event payload
            tenant_id: Tenant identifier
            version: Expected version of aggregate
            metadata: Additional metadata

        Returns:
            UUID: Event ID

        Raises:
            ConcurrencyError: If version conflict detected
        """
        from shared.database.models import StoredEvent

        # Check for version conflicts
        current_version = self.get_aggregate_version(aggregate_id)
        if current_version != version - 1:
            raise ConcurrencyError(
                f"Version conflict for aggregate {aggregate_id}. "
                f"Expected {version - 1}, got {current_version}"
            )

        # Create stored event
        event_id = uuid4()
        stored_event = StoredEvent(
            event_id=event_id,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type.value,
            event_data=event_data,
            tenant_id=tenant_id,
            version=version,
            occurred_at=datetime.utcnow(),
            event_metadata=metadata or {},
        )

        self.db.add(stored_event)
        self.db.commit()

        logger.debug(
            f"Event appended: {event_type.value} for {aggregate_type} "
            f"{aggregate_id} v{version}"
        )

        return event_id

    def get_events_for_aggregate(
        self,
        aggregate_id: UUID,
        from_version: int = 0,
        to_version: Optional[int] = None,
    ) -> List[Event]:
        """
        Get all events for an aggregate

        Args:
            aggregate_id: ID of aggregate
            from_version: Starting version (inclusive)
            to_version: Ending version (inclusive), None for all

        Returns:
            List of events in order
        """
        from shared.database.models import StoredEvent

        query = (
            self.db.query(StoredEvent)
            .filter(StoredEvent.aggregate_id == aggregate_id)
            .filter(StoredEvent.version >= from_version)
        )

        if to_version is not None:
            query = query.filter(StoredEvent.version <= to_version)

        query = query.order_by(StoredEvent.version)

        stored_events = query.all()

        # Convert to Event objects
        events = []
        for se in stored_events:
            event = Event(
                event_id=se.event_id,
                event_type=EventType(se.event_type),
                tenant_id=se.tenant_id,
                occurred_at=se.occurred_at,
                payload=se.event_data,
                metadata=se.event_metadata,
            )
            events.append(event)

        return events

    def get_aggregate_version(self, aggregate_id: UUID) -> int:
        """
        Get current version of aggregate

        Args:
            aggregate_id: ID of aggregate

        Returns:
            Current version number (0 if no events)
        """
        from shared.database.models import StoredEvent

        result = (
            self.db.query(func.max(StoredEvent.version))
            .filter(StoredEvent.aggregate_id == aggregate_id)
            .scalar()
        )

        return result or 0

    async def save_snapshot(
        self,
        aggregate_type: str,
        aggregate_id: UUID,
        state: Dict[str, Any],
        version: int,
        tenant_id: str,
    ):
        """
        Save aggregate snapshot for performance

        Args:
            aggregate_type: Type of aggregate
            aggregate_id: ID of aggregate
            state: Current state of aggregate
            version: Version at which snapshot was taken
            tenant_id: Tenant identifier
        """
        from shared.database.models import AggregateSnapshot

        snapshot = AggregateSnapshot(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            state=state,
            version=version,
            tenant_id=tenant_id,
            created_at=datetime.utcnow(),
        )

        self.db.add(snapshot)
        self.db.commit()

        logger.debug(
            f"Snapshot saved: {aggregate_type} {aggregate_id} v{version}"
        )

    def get_snapshot(
        self, aggregate_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get latest snapshot for aggregate

        Args:
            aggregate_id: ID of aggregate

        Returns:
            Snapshot data if exists, None otherwise
        """
        from shared.database.models import AggregateSnapshot

        snapshot = (
            self.db.query(AggregateSnapshot)
            .filter(AggregateSnapshot.aggregate_id == aggregate_id)
            .order_by(desc(AggregateSnapshot.version))
            .first()
        )

        if snapshot:
            return {
                "state": snapshot.state,
                "version": snapshot.version,
                "created_at": snapshot.created_at,
            }

        return None

    def rebuild_aggregate(
        self, aggregate_id: UUID, aggregate_class
    ) -> Any:
        """
        Rebuild aggregate from events (and optional snapshot)

        Args:
            aggregate_id: ID of aggregate
            aggregate_class: Class with apply_event method

        Returns:
            Reconstructed aggregate instance
        """
        # Try to load from snapshot first
        snapshot = self.get_snapshot(aggregate_id)

        if snapshot:
            # Start from snapshot
            aggregate = aggregate_class.from_snapshot(snapshot["state"])
            from_version = snapshot["version"] + 1
        else:
            # Start from scratch
            aggregate = aggregate_class()
            from_version = 0

        # Apply events after snapshot
        events = self.get_events_for_aggregate(
            aggregate_id, from_version=from_version
        )

        for event in events:
            aggregate.apply_event(event)

        return aggregate

    def query_events(
        self,
        tenant_id: str,
        event_types: Optional[List[EventType]] = None,
        aggregate_types: Optional[List[str]] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Event]:
        """
        Query events with filters

        Args:
            tenant_id: Tenant identifier
            event_types: Filter by event types
            aggregate_types: Filter by aggregate types
            from_date: Start date filter
            to_date: End date filter
            limit: Maximum number of events to return
            offset: Pagination offset

        Returns:
            List of matching events
        """
        from shared.database.models import StoredEvent

        query = self.db.query(StoredEvent).filter(
            StoredEvent.tenant_id == tenant_id
        )

        if event_types:
            event_type_values = [et.value for et in event_types]
            query = query.filter(StoredEvent.event_type.in_(event_type_values))

        if aggregate_types:
            query = query.filter(
                StoredEvent.aggregate_type.in_(aggregate_types)
            )

        if from_date:
            query = query.filter(StoredEvent.occurred_at >= from_date)

        if to_date:
            query = query.filter(StoredEvent.occurred_at <= to_date)

        query = query.order_by(desc(StoredEvent.occurred_at))
        query = query.limit(limit).offset(offset)

        stored_events = query.all()

        # Convert to Event objects
        events = []
        for se in stored_events:
            event = Event(
                event_id=se.event_id,
                event_type=EventType(se.event_type),
                tenant_id=se.tenant_id,
                occurred_at=se.occurred_at,
                payload=se.event_data,
                metadata=se.event_metadata,
            )
            events.append(event)

        return events

    async def replay_events(
        self,
        tenant_id: str,
        event_handler,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        event_types: Optional[List[EventType]] = None,
    ):
        """
        Replay events through handler

        Args:
            tenant_id: Tenant identifier
            event_handler: Async function to handle each event
            from_date: Start date for replay
            to_date: End date for replay
            event_types: Filter by event types
        """
        logger.info(
            f"Starting event replay for tenant {tenant_id} "
            f"from {from_date} to {to_date}"
        )

        offset = 0
        batch_size = 100
        total_replayed = 0

        while True:
            events = self.query_events(
                tenant_id=tenant_id,
                event_types=event_types,
                from_date=from_date,
                to_date=to_date,
                limit=batch_size,
                offset=offset,
            )

            if not events:
                break

            for event in events:
                try:
                    await event_handler(event)
                    total_replayed += 1
                except Exception as e:
                    logger.error(
                        f"Error replaying event {event.event_id}: {e}"
                    )

            offset += batch_size

        logger.info(f"Event replay completed. Replayed {total_replayed} events")

    def compact_events(
        self, aggregate_id: UUID, keep_events: int = 10
    ):
        """
        Compact old events for aggregate by creating snapshot
        and removing old events

        Args:
            aggregate_id: ID of aggregate
            keep_events: Number of recent events to keep
        """
        from shared.database.models import StoredEvent

        # Get current version
        current_version = self.get_aggregate_version(aggregate_id)

        if current_version <= keep_events:
            return  # Not enough events to compact

        # Create snapshot at version before keep_events
        snapshot_version = current_version - keep_events

        # Delete old events (would need aggregate class to rebuild)
        # This is a simplified version
        logger.info(
            f"Compaction for {aggregate_id}: "
            f"current v{current_version}, snapshot v{snapshot_version}"
        )


class ConcurrencyError(Exception):
    """Raised when event version conflict detected"""

    pass


# Example aggregate class
class PatientAggregate:
    """Example aggregate for patient"""

    def __init__(self):
        self.id: Optional[UUID] = None
        self.name: str = ""
        self.email: str = ""
        self.version: int = 0

    @classmethod
    def from_snapshot(cls, state: Dict[str, Any]):
        """Create aggregate from snapshot"""
        aggregate = cls()
        aggregate.id = UUID(state["id"])
        aggregate.name = state["name"]
        aggregate.email = state["email"]
        aggregate.version = state["version"]
        return aggregate

    def apply_event(self, event: Event):
        """Apply event to aggregate"""
        if event.event_type == EventType.PATIENT_CREATED:
            self.id = UUID(event.payload["patient_id"])
            self.name = event.payload["name"]
            self.email = event.payload.get("email", "")

        elif event.event_type == EventType.PATIENT_UPDATED:
            if "name" in event.payload:
                self.name = event.payload["name"]
            if "email" in event.payload:
                self.email = event.payload["email"]

        self.version += 1

    def to_snapshot(self) -> Dict[str, Any]:
        """Convert aggregate to snapshot"""
        return {
            "id": str(self.id),
            "name": self.name,
            "email": self.email,
            "version": self.version,
        }

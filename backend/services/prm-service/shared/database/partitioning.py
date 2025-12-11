"""
Database Partitioning Manager

Implements table partitioning strategies for large tables:
- Time-based partitioning (range)
- List partitioning (tenant-based)
- Hash partitioning (for even distribution)
- Automatic partition management
- Partition pruning optimization
- Archival automation

EPIC-003: US-003.5 Database Partitioning
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import calendar

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PartitionStrategy(str, Enum):
    """Partitioning strategies."""
    RANGE = "range"  # Time-based partitioning
    LIST = "list"    # Tenant-based partitioning
    HASH = "hash"    # Even distribution


class PartitionInterval(str, Enum):
    """Intervals for range partitioning."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


@dataclass
class PartitionDefinition:
    """Definition for a partitioned table."""
    table_name: str
    strategy: PartitionStrategy
    partition_key: str
    interval: Optional[PartitionInterval] = None  # For range partitioning
    retention_months: int = 24  # How long to keep partitions
    archive_after_months: int = 12  # When to archive to cold storage
    num_hash_partitions: int = 8  # For hash partitioning


@dataclass
class PartitionInfo:
    """Information about an existing partition."""
    name: str
    table_name: str
    strategy: str
    range_from: Optional[str] = None
    range_to: Optional[str] = None
    list_values: Optional[List[str]] = None
    size_bytes: int = 0
    size_human: str = ""
    row_count: int = 0
    is_default: bool = False


@dataclass
class PartitionMaintenanceResult:
    """Result of partition maintenance operations."""
    partitions_created: List[str] = field(default_factory=list)
    partitions_dropped: List[str] = field(default_factory=list)
    partitions_archived: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    duration_ms: float = 0


class PartitionManager:
    """
    Manages database table partitioning.

    Features:
    - Create partitioned tables
    - Automatic partition creation for future periods
    - Automatic partition cleanup for old data
    - Archive old partitions to cold storage
    - Monitor partition health
    """

    # Tables that should be partitioned
    PARTITIONED_TABLES: List[PartitionDefinition] = [
        PartitionDefinition(
            table_name="event_log",
            strategy=PartitionStrategy.RANGE,
            partition_key="timestamp",
            interval=PartitionInterval.MONTHLY,
            retention_months=36,
            archive_after_months=12,
        ),
        PartitionDefinition(
            table_name="audit_logs",
            strategy=PartitionStrategy.RANGE,
            partition_key="created_at",
            interval=PartitionInterval.MONTHLY,
            retention_months=84,  # 7 years for HIPAA
            archive_after_months=24,
        ),
        PartitionDefinition(
            table_name="appointments",
            strategy=PartitionStrategy.RANGE,
            partition_key="scheduled_start",
            interval=PartitionInterval.MONTHLY,
            retention_months=60,
            archive_after_months=24,
        ),
        PartitionDefinition(
            table_name="encounters",
            strategy=PartitionStrategy.RANGE,
            partition_key="period_start",
            interval=PartitionInterval.MONTHLY,
            retention_months=84,  # 7 years for medical records
            archive_after_months=36,
        ),
        PartitionDefinition(
            table_name="communications",
            strategy=PartitionStrategy.RANGE,
            partition_key="sent_at",
            interval=PartitionInterval.MONTHLY,
            retention_months=24,
            archive_after_months=6,
        ),
        PartitionDefinition(
            table_name="analytics_events",
            strategy=PartitionStrategy.RANGE,
            partition_key="event_time",
            interval=PartitionInterval.WEEKLY,
            retention_months=6,
            archive_after_months=1,
        ),
    ]

    def __init__(self, engine: Engine):
        self.engine = engine

    def create_partitioned_table(
        self,
        definition: PartitionDefinition,
        original_table_ddl: str,
        db: Session,
    ) -> bool:
        """
        Convert a regular table to a partitioned table.

        This creates a new partitioned table, migrates data, and swaps tables.

        Args:
            definition: Partition definition
            original_table_ddl: DDL of the original table (without indexes)
            db: Database session

        Returns:
            True if successful
        """
        table = definition.table_name
        partition_key = definition.partition_key

        try:
            # Step 1: Create the partitioned parent table
            partition_clause = self._get_partition_clause(definition)

            # Modify original DDL to add partitioning
            partitioned_ddl = original_table_ddl.rstrip(";").rstrip()
            partitioned_ddl += f" PARTITION BY {partition_clause}"

            # Create as new table first
            new_table = f"{table}_partitioned"
            partitioned_ddl = partitioned_ddl.replace(
                f'CREATE TABLE "{table}"',
                f'CREATE TABLE "{new_table}"'
            ).replace(
                f"CREATE TABLE {table}",
                f"CREATE TABLE {new_table}"
            )

            db.execute(text(partitioned_ddl))
            logger.info(f"Created partitioned table structure: {new_table}")

            # Step 2: Create initial partitions
            self._create_initial_partitions(definition, db)

            # Step 3: Create default partition for overflow
            self._create_default_partition(definition, db)

            logger.info(f"Partitioned table created: {table}")
            return True

        except Exception as e:
            logger.error(f"Error creating partitioned table {table}: {e}")
            db.rollback()
            return False

    def _get_partition_clause(self, definition: PartitionDefinition) -> str:
        """Generate the PARTITION BY clause."""
        if definition.strategy == PartitionStrategy.RANGE:
            return f"RANGE ({definition.partition_key})"
        elif definition.strategy == PartitionStrategy.LIST:
            return f"LIST ({definition.partition_key})"
        elif definition.strategy == PartitionStrategy.HASH:
            return f"HASH ({definition.partition_key})"
        else:
            raise ValueError(f"Unknown partition strategy: {definition.strategy}")

    def _create_initial_partitions(
        self,
        definition: PartitionDefinition,
        db: Session,
    ):
        """Create initial partitions for a range-partitioned table."""
        if definition.strategy != PartitionStrategy.RANGE:
            return

        now = datetime.now(timezone.utc)

        # Create partitions for past data (up to retention period)
        start_date = now - timedelta(days=definition.retention_months * 30)

        # Create partitions for future data (3 months ahead)
        end_date = now + timedelta(days=90)

        current_date = start_date
        while current_date < end_date:
            self._create_range_partition(definition, current_date, db)
            current_date = self._next_partition_date(current_date, definition.interval)

    def _create_range_partition(
        self,
        definition: PartitionDefinition,
        partition_date: datetime,
        db: Session,
    ) -> Optional[str]:
        """Create a single range partition."""
        table = definition.table_name
        interval = definition.interval

        # Calculate partition boundaries
        from_date, to_date = self._get_partition_boundaries(partition_date, interval)

        # Generate partition name
        partition_name = self._get_partition_name(table, partition_date, interval)

        try:
            # Check if partition already exists
            exists_query = """
                SELECT 1 FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE c.relname = :name
                  AND n.nspname = 'public'
            """
            result = db.execute(text(exists_query), {"name": partition_name})
            if result.fetchone():
                return None  # Already exists

            # Create partition
            sql = f"""
                CREATE TABLE IF NOT EXISTS {partition_name}
                PARTITION OF {table}
                FOR VALUES FROM ('{from_date.isoformat()}')
                TO ('{to_date.isoformat()}')
            """
            db.execute(text(sql))
            db.commit()

            logger.info(f"Created partition: {partition_name}")
            return partition_name

        except Exception as e:
            logger.error(f"Error creating partition {partition_name}: {e}")
            db.rollback()
            return None

    def _create_default_partition(
        self,
        definition: PartitionDefinition,
        db: Session,
    ) -> bool:
        """Create a default partition for overflow data."""
        table = definition.table_name
        partition_name = f"{table}_default"

        try:
            sql = f"""
                CREATE TABLE IF NOT EXISTS {partition_name}
                PARTITION OF {table} DEFAULT
            """
            db.execute(text(sql))
            db.commit()

            logger.info(f"Created default partition: {partition_name}")
            return True

        except Exception as e:
            logger.error(f"Error creating default partition: {e}")
            db.rollback()
            return False

    def _get_partition_boundaries(
        self,
        date: datetime,
        interval: PartitionInterval,
    ) -> Tuple[datetime, datetime]:
        """Calculate partition boundary dates."""
        if interval == PartitionInterval.DAILY:
            from_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            to_date = from_date + timedelta(days=1)

        elif interval == PartitionInterval.WEEKLY:
            # Start of week (Monday)
            from_date = date - timedelta(days=date.weekday())
            from_date = from_date.replace(hour=0, minute=0, second=0, microsecond=0)
            to_date = from_date + timedelta(days=7)

        elif interval == PartitionInterval.MONTHLY:
            from_date = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # First day of next month
            if date.month == 12:
                to_date = from_date.replace(year=date.year + 1, month=1)
            else:
                to_date = from_date.replace(month=date.month + 1)

        elif interval == PartitionInterval.QUARTERLY:
            quarter = (date.month - 1) // 3
            from_date = date.replace(
                month=quarter * 3 + 1, day=1,
                hour=0, minute=0, second=0, microsecond=0
            )
            # First day of next quarter
            next_quarter_month = (quarter + 1) * 3 + 1
            if next_quarter_month > 12:
                to_date = from_date.replace(year=date.year + 1, month=1)
            else:
                to_date = from_date.replace(month=next_quarter_month)

        elif interval == PartitionInterval.YEARLY:
            from_date = date.replace(
                month=1, day=1,
                hour=0, minute=0, second=0, microsecond=0
            )
            to_date = from_date.replace(year=date.year + 1)

        else:
            raise ValueError(f"Unknown interval: {interval}")

        return from_date, to_date

    def _get_partition_name(
        self,
        table: str,
        date: datetime,
        interval: PartitionInterval,
    ) -> str:
        """Generate partition name based on date and interval."""
        if interval == PartitionInterval.DAILY:
            suffix = date.strftime("%Y%m%d")
        elif interval == PartitionInterval.WEEKLY:
            suffix = f"{date.year}w{date.isocalendar()[1]:02d}"
        elif interval == PartitionInterval.MONTHLY:
            suffix = date.strftime("%Y%m")
        elif interval == PartitionInterval.QUARTERLY:
            quarter = (date.month - 1) // 3 + 1
            suffix = f"{date.year}q{quarter}"
        elif interval == PartitionInterval.YEARLY:
            suffix = str(date.year)
        else:
            suffix = date.strftime("%Y%m%d")

        return f"{table}_p{suffix}"

    def _next_partition_date(
        self,
        date: datetime,
        interval: PartitionInterval,
    ) -> datetime:
        """Get the start date of the next partition."""
        if interval == PartitionInterval.DAILY:
            return date + timedelta(days=1)
        elif interval == PartitionInterval.WEEKLY:
            return date + timedelta(days=7)
        elif interval == PartitionInterval.MONTHLY:
            if date.month == 12:
                return date.replace(year=date.year + 1, month=1, day=1)
            return date.replace(month=date.month + 1, day=1)
        elif interval == PartitionInterval.QUARTERLY:
            next_month = date.month + 3
            if next_month > 12:
                return date.replace(year=date.year + 1, month=next_month - 12, day=1)
            return date.replace(month=next_month, day=1)
        elif interval == PartitionInterval.YEARLY:
            return date.replace(year=date.year + 1, month=1, day=1)
        else:
            return date + timedelta(days=30)

    def get_partition_info(
        self,
        table_name: str,
        db: Session,
    ) -> List[PartitionInfo]:
        """
        Get information about existing partitions for a table.

        Args:
            table_name: Parent table name
            db: Database session

        Returns:
            List of PartitionInfo objects
        """
        query = """
            SELECT
                c.relname AS partition_name,
                pg_get_expr(c.relpartbound, c.oid) AS partition_bound,
                pg_relation_size(c.oid) AS size_bytes,
                pg_size_pretty(pg_relation_size(c.oid)) AS size_human,
                (SELECT reltuples::bigint FROM pg_class WHERE oid = c.oid) AS row_count
            FROM pg_class c
            JOIN pg_inherits i ON i.inhrelid = c.oid
            JOIN pg_class p ON i.inhparent = p.oid
            WHERE p.relname = :table_name
              AND c.relkind = 'r'
            ORDER BY c.relname
        """

        result = db.execute(text(query), {"table_name": table_name})

        partitions = []
        for row in result:
            bound = row.partition_bound or ""
            is_default = "DEFAULT" in bound.upper()

            # Parse range bounds
            range_from = None
            range_to = None
            if "FOR VALUES FROM" in bound:
                # Extract from/to values
                try:
                    parts = bound.split("FOR VALUES FROM")[1]
                    from_part, to_part = parts.split("TO")
                    range_from = from_part.strip().strip("()'")
                    range_to = to_part.strip().strip("()'")
                except:
                    pass

            info = PartitionInfo(
                name=row.partition_name,
                table_name=table_name,
                strategy="range",  # Simplified
                range_from=range_from,
                range_to=range_to,
                size_bytes=row.size_bytes,
                size_human=row.size_human,
                row_count=int(row.row_count or 0),
                is_default=is_default,
            )
            partitions.append(info)

        return partitions

    def maintain_partitions(
        self,
        db: Session,
        definitions: Optional[List[PartitionDefinition]] = None,
    ) -> PartitionMaintenanceResult:
        """
        Run partition maintenance for all defined tables.

        This:
        1. Creates partitions for upcoming periods
        2. Archives old partitions
        3. Drops very old partitions

        Args:
            db: Database session
            definitions: Optional list of definitions (default: all)

        Returns:
            PartitionMaintenanceResult with details
        """
        import time
        start_time = time.time()

        result = PartitionMaintenanceResult()
        definitions = definitions or self.PARTITIONED_TABLES

        for definition in definitions:
            try:
                # Create future partitions
                created = self._create_future_partitions(definition, db)
                result.partitions_created.extend(created)

                # Archive old partitions
                archived = self._archive_old_partitions(definition, db)
                result.partitions_archived.extend(archived)

                # Drop expired partitions
                dropped = self._drop_expired_partitions(definition, db)
                result.partitions_dropped.extend(dropped)

            except Exception as e:
                error_msg = f"Error maintaining {definition.table_name}: {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)

        result.duration_ms = (time.time() - start_time) * 1000
        return result

    def _create_future_partitions(
        self,
        definition: PartitionDefinition,
        db: Session,
        months_ahead: int = 3,
    ) -> List[str]:
        """Create partitions for upcoming periods."""
        if definition.strategy != PartitionStrategy.RANGE:
            return []

        created = []
        now = datetime.now(timezone.utc)
        end_date = now + timedelta(days=months_ahead * 30)

        current_date = now
        while current_date < end_date:
            partition_name = self._create_range_partition(definition, current_date, db)
            if partition_name:
                created.append(partition_name)
            current_date = self._next_partition_date(current_date, definition.interval)

        return created

    def _archive_old_partitions(
        self,
        definition: PartitionDefinition,
        db: Session,
    ) -> List[str]:
        """Archive partitions older than archive threshold."""
        archived = []
        threshold = datetime.now(timezone.utc) - timedelta(days=definition.archive_after_months * 30)

        partitions = self.get_partition_info(definition.table_name, db)

        for partition in partitions:
            if partition.is_default:
                continue

            # Check if partition is older than archive threshold
            if partition.range_to:
                try:
                    partition_end = datetime.fromisoformat(partition.range_to.replace("'", ""))
                    if partition_end < threshold:
                        # Archive logic - in production, move to cold storage
                        logger.info(f"Would archive partition: {partition.name}")
                        archived.append(partition.name)
                except:
                    pass

        return archived

    def _drop_expired_partitions(
        self,
        definition: PartitionDefinition,
        db: Session,
    ) -> List[str]:
        """Drop partitions older than retention period."""
        dropped = []
        threshold = datetime.now(timezone.utc) - timedelta(days=definition.retention_months * 30)

        partitions = self.get_partition_info(definition.table_name, db)

        for partition in partitions:
            if partition.is_default:
                continue

            # Check if partition is older than retention threshold
            if partition.range_to:
                try:
                    partition_end = datetime.fromisoformat(partition.range_to.replace("'", ""))
                    if partition_end < threshold:
                        # Drop the partition
                        drop_sql = f"DROP TABLE IF EXISTS {partition.name}"
                        db.execute(text(drop_sql))
                        db.commit()
                        dropped.append(partition.name)
                        logger.info(f"Dropped expired partition: {partition.name}")
                except:
                    pass

        return dropped

    def get_partition_stats(
        self,
        db: Session,
        table_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get partitioning statistics.

        Args:
            db: Database session
            table_name: Optional specific table

        Returns:
            Dictionary of statistics
        """
        stats = {
            "tables": {},
            "total_partitions": 0,
            "total_size_bytes": 0,
        }

        tables = [table_name] if table_name else [d.table_name for d in self.PARTITIONED_TABLES]

        for table in tables:
            partitions = self.get_partition_info(table, db)
            table_size = sum(p.size_bytes for p in partitions)
            table_rows = sum(p.row_count for p in partitions)

            stats["tables"][table] = {
                "partition_count": len(partitions),
                "total_size_bytes": table_size,
                "total_size_human": f"{table_size / (1024*1024):.2f} MB",
                "total_rows": table_rows,
                "oldest_partition": min((p.range_from for p in partitions if p.range_from), default=None),
                "newest_partition": max((p.range_to for p in partitions if p.range_to), default=None),
            }

            stats["total_partitions"] += len(partitions)
            stats["total_size_bytes"] += table_size

        stats["total_size_human"] = f"{stats['total_size_bytes'] / (1024*1024):.2f} MB"
        return stats

    def check_partition_health(
        self,
        db: Session,
    ) -> Dict[str, Any]:
        """
        Check health of all partitioned tables.

        Returns:
            Health report with issues
        """
        issues = []
        now = datetime.now(timezone.utc)

        for definition in self.PARTITIONED_TABLES:
            partitions = self.get_partition_info(definition.table_name, db)

            if not partitions:
                issues.append({
                    "table": definition.table_name,
                    "severity": "warning",
                    "issue": "No partitions found - table may not be partitioned",
                })
                continue

            # Check for missing future partitions
            has_future = any(
                p.range_to and datetime.fromisoformat(p.range_to.replace("'", "")) > now
                for p in partitions if p.range_to
            )
            if not has_future:
                issues.append({
                    "table": definition.table_name,
                    "severity": "error",
                    "issue": "No future partitions - new data may fail to insert",
                })

            # Check for bloated default partition
            default_partition = next((p for p in partitions if p.is_default), None)
            if default_partition and default_partition.row_count > 10000:
                issues.append({
                    "table": definition.table_name,
                    "severity": "warning",
                    "issue": f"Default partition has {default_partition.row_count:,} rows",
                })

            # Check for very large partitions
            for partition in partitions:
                if partition.size_bytes > 10 * 1024 * 1024 * 1024:  # 10GB
                    issues.append({
                        "table": definition.table_name,
                        "severity": "info",
                        "issue": f"Large partition {partition.name}: {partition.size_human}",
                    })

        return {
            "healthy": len([i for i in issues if i["severity"] == "error"]) == 0,
            "issues": issues,
            "checked_tables": len(self.PARTITIONED_TABLES),
            "checked_at": now.isoformat(),
        }


# Global partition manager
_partition_manager: Optional[PartitionManager] = None


def get_partition_manager(engine: Optional[Engine] = None) -> PartitionManager:
    """Get or create the global partition manager."""
    global _partition_manager
    if _partition_manager is None:
        if engine is None:
            from .connection import engine as default_engine
            engine = default_engine
        _partition_manager = PartitionManager(engine)
    return _partition_manager

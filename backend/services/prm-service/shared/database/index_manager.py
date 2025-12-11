"""
Index Manager

Comprehensive database index management including:
- Index creation and optimization
- Index usage monitoring
- Unused index detection
- Index maintenance automation
- Query plan analysis

EPIC-003: US-003.1 Index Optimization
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class IndexType(str, Enum):
    """Types of database indexes."""
    BTREE = "btree"
    HASH = "hash"
    GIN = "gin"  # For JSONB and full-text
    GIST = "gist"  # For geometric/range types
    BRIN = "brin"  # For large sequential data
    GIN_TRGM = "gin_trgm"  # For trigram similarity


@dataclass
class IndexDefinition:
    """Definition for creating an index."""
    name: str
    table: str
    columns: List[str]
    index_type: IndexType = IndexType.BTREE
    unique: bool = False
    partial_condition: Optional[str] = None  # WHERE clause for partial index
    include_columns: Optional[List[str]] = None  # INCLUDE for covering indexes
    concurrent: bool = True  # CREATE INDEX CONCURRENTLY
    if_not_exists: bool = True


@dataclass
class IndexStats:
    """Statistics for an index."""
    name: str
    table: str
    size_bytes: int
    size_human: str
    scans: int
    tuples_read: int
    tuples_fetched: int
    last_used: Optional[datetime] = None
    is_valid: bool = True
    is_unique: bool = False
    definition: str = ""


@dataclass
class IndexRecommendation:
    """Recommendation for index optimization."""
    action: str  # create, drop, rebuild
    index_name: str
    table: str
    reason: str
    estimated_improvement: str
    sql: str
    priority: int = 1  # 1 = highest


@dataclass
class QueryPlanAnalysis:
    """Analysis of a query execution plan."""
    query: str
    plan: str
    total_cost: float
    actual_time_ms: float
    rows_estimated: int
    rows_actual: int
    seq_scans: int
    index_scans: int
    recommendations: List[str] = field(default_factory=list)


class IndexManager:
    """
    Manages database indexes for optimal performance.

    Features:
    - Index creation with best practices
    - Index usage monitoring
    - Unused index detection
    - Index maintenance scheduling
    - Query plan analysis for index recommendations
    """

    # Comprehensive index definitions for healthcare schema
    HEALTHCARE_INDEXES: List[IndexDefinition] = [
        # Patient indexes
        IndexDefinition(
            name="idx_patients_tenant_id",
            table="patients",
            columns=["tenant_id"],
        ),
        IndexDefinition(
            name="idx_patients_phone_primary",
            table="patients",
            columns=["phone_primary"],
        ),
        IndexDefinition(
            name="idx_patients_email_primary",
            table="patients",
            columns=["email_primary"],
        ),
        IndexDefinition(
            name="idx_patients_name_search",
            table="patients",
            columns=["last_name", "first_name"],
            include_columns=["phone_primary", "email_primary", "date_of_birth"],
        ),
        IndexDefinition(
            name="idx_patients_dob",
            table="patients",
            columns=["date_of_birth"],
        ),
        IndexDefinition(
            name="idx_patients_tenant_active",
            table="patients",
            columns=["tenant_id", "created_at"],
            partial_condition="is_deceased = false",
        ),
        IndexDefinition(
            name="idx_patients_fhir_gin",
            table="patients",
            columns=["fhir_resource"],
            index_type=IndexType.GIN,
        ),

        # Appointment indexes
        IndexDefinition(
            name="idx_appointments_patient_id",
            table="appointments",
            columns=["patient_id"],
        ),
        IndexDefinition(
            name="idx_appointments_practitioner_id",
            table="appointments",
            columns=["practitioner_id"],
        ),
        IndexDefinition(
            name="idx_appointments_scheduled",
            table="appointments",
            columns=["scheduled_start", "scheduled_end"],
        ),
        IndexDefinition(
            name="idx_appointments_tenant_date",
            table="appointments",
            columns=["tenant_id", "scheduled_start"],
        ),
        IndexDefinition(
            name="idx_appointments_status_active",
            table="appointments",
            columns=["status", "scheduled_start"],
            partial_condition="status IN ('scheduled', 'confirmed', 'arrived')",
        ),

        # Encounter indexes
        IndexDefinition(
            name="idx_encounters_patient_id",
            table="encounters",
            columns=["patient_id"],
        ),
        IndexDefinition(
            name="idx_encounters_tenant_period",
            table="encounters",
            columns=["tenant_id", "period_start"],
        ),
        IndexDefinition(
            name="idx_encounters_status",
            table="encounters",
            columns=["status"],
        ),

        # Event log indexes for audit trail
        IndexDefinition(
            name="idx_event_log_tenant_timestamp",
            table="event_log",
            columns=["tenant_id", "timestamp"],
        ),
        IndexDefinition(
            name="idx_event_log_aggregate",
            table="event_log",
            columns=["aggregate_type", "aggregate_id"],
        ),
        IndexDefinition(
            name="idx_event_log_event_type",
            table="event_log",
            columns=["event_type"],
        ),

        # FHIR resource indexes
        IndexDefinition(
            name="idx_fhir_resources_type_id",
            table="fhir_resources",
            columns=["resource_type", "resource_id"],
        ),
        IndexDefinition(
            name="idx_fhir_resources_tenant",
            table="fhir_resources",
            columns=["tenant_id", "resource_type"],
        ),
        IndexDefinition(
            name="idx_fhir_resources_data_gin",
            table="fhir_resources",
            columns=["resource_data"],
            index_type=IndexType.GIN,
        ),

        # User/Auth indexes
        IndexDefinition(
            name="idx_users_email",
            table="users",
            columns=["email"],
            unique=True,
        ),
        IndexDefinition(
            name="idx_users_tenant_active",
            table="users",
            columns=["tenant_id"],
            partial_condition="is_active = true",
        ),

        # Practitioner indexes
        IndexDefinition(
            name="idx_practitioners_tenant",
            table="practitioners",
            columns=["tenant_id"],
        ),
        IndexDefinition(
            name="idx_practitioners_speciality",
            table="practitioners",
            columns=["speciality"],
        ),
        IndexDefinition(
            name="idx_practitioners_name",
            table="practitioners",
            columns=["last_name", "first_name"],
        ),

        # Organization/Location indexes
        IndexDefinition(
            name="idx_organizations_tenant",
            table="organizations",
            columns=["tenant_id"],
        ),
        IndexDefinition(
            name="idx_locations_organization",
            table="locations",
            columns=["organization_id"],
        ),

        # Consent indexes
        IndexDefinition(
            name="idx_consents_patient",
            table="consents",
            columns=["patient_id"],
        ),
        IndexDefinition(
            name="idx_consents_status",
            table="consents",
            columns=["status"],
            partial_condition="status = 'active'",
        ),
    ]

    def __init__(self, engine: Engine):
        self.engine = engine
        self._stats_cache: Dict[str, IndexStats] = {}
        self._last_stats_refresh: Optional[datetime] = None

    def create_index(
        self,
        definition: IndexDefinition,
        db: Optional[Session] = None,
    ) -> bool:
        """
        Create an index based on definition.

        Args:
            definition: Index definition
            db: Optional session to use

        Returns:
            True if created successfully
        """
        try:
            # Build CREATE INDEX statement
            sql_parts = ["CREATE"]
            if definition.unique:
                sql_parts.append("UNIQUE")
            sql_parts.append("INDEX")
            if definition.concurrent:
                sql_parts.append("CONCURRENTLY")
            if definition.if_not_exists:
                sql_parts.append("IF NOT EXISTS")

            sql_parts.append(definition.name)
            sql_parts.append("ON")
            sql_parts.append(definition.table)

            # Index type
            if definition.index_type != IndexType.BTREE:
                sql_parts.append(f"USING {definition.index_type.value}")

            # Columns
            sql_parts.append(f"({', '.join(definition.columns)})")

            # Include columns (covering index)
            if definition.include_columns:
                sql_parts.append(f"INCLUDE ({', '.join(definition.include_columns)})")

            # Partial index condition
            if definition.partial_condition:
                sql_parts.append(f"WHERE {definition.partial_condition}")

            sql = " ".join(sql_parts)

            # Execute
            if db:
                db.execute(text(sql))
                db.commit()
            else:
                with self.engine.connect() as conn:
                    # CONCURRENTLY cannot run in transaction
                    if definition.concurrent:
                        conn.execution_options(isolation_level="AUTOCOMMIT")
                    conn.execute(text(sql))

            logger.info(f"Created index: {definition.name}")
            return True

        except Exception as e:
            logger.error(f"Error creating index {definition.name}: {e}")
            return False

    def create_all_indexes(self, db: Optional[Session] = None) -> Dict[str, bool]:
        """
        Create all healthcare indexes.

        Returns:
            Dictionary of index_name -> success status
        """
        results = {}
        for index_def in self.HEALTHCARE_INDEXES:
            results[index_def.name] = self.create_index(index_def, db)
        return results

    def drop_index(
        self,
        index_name: str,
        concurrent: bool = True,
        if_exists: bool = True,
        db: Optional[Session] = None,
    ) -> bool:
        """Drop an index."""
        try:
            sql_parts = ["DROP INDEX"]
            if concurrent:
                sql_parts.append("CONCURRENTLY")
            if if_exists:
                sql_parts.append("IF EXISTS")
            sql_parts.append(index_name)

            sql = " ".join(sql_parts)

            if db:
                db.execute(text(sql))
                db.commit()
            else:
                with self.engine.connect() as conn:
                    if concurrent:
                        conn.execution_options(isolation_level="AUTOCOMMIT")
                    conn.execute(text(sql))

            logger.info(f"Dropped index: {index_name}")
            return True

        except Exception as e:
            logger.error(f"Error dropping index {index_name}: {e}")
            return False

    def get_index_stats(
        self,
        db: Session,
        table_name: Optional[str] = None,
        refresh: bool = False,
    ) -> List[IndexStats]:
        """
        Get index usage statistics.

        Args:
            db: Database session
            table_name: Optional table to filter
            refresh: Force refresh of cached stats

        Returns:
            List of IndexStats
        """
        # Use cache if available and fresh
        cache_age = 300  # 5 minutes
        if (
            not refresh
            and self._last_stats_refresh
            and (datetime.now(timezone.utc) - self._last_stats_refresh).seconds < cache_age
        ):
            if table_name:
                return [s for s in self._stats_cache.values() if s.table == table_name]
            return list(self._stats_cache.values())

        query = """
        SELECT
            i.indexrelname AS index_name,
            t.relname AS table_name,
            pg_relation_size(i.indexrelid) AS size_bytes,
            pg_size_pretty(pg_relation_size(i.indexrelid)) AS size_human,
            COALESCE(s.idx_scan, 0) AS scans,
            COALESCE(s.idx_tup_read, 0) AS tuples_read,
            COALESCE(s.idx_tup_fetch, 0) AS tuples_fetched,
            ix.indisunique AS is_unique,
            ix.indisvalid AS is_valid,
            pg_get_indexdef(i.indexrelid) AS definition
        FROM pg_stat_user_indexes i
        JOIN pg_index ix ON i.indexrelid = ix.indexrelid
        JOIN pg_class t ON i.relid = t.oid
        LEFT JOIN pg_stat_user_indexes s ON i.indexrelid = s.indexrelid
        """

        if table_name:
            query += f" WHERE t.relname = '{table_name}'"

        query += " ORDER BY size_bytes DESC"

        result = db.execute(text(query))

        stats = []
        for row in result:
            stat = IndexStats(
                name=row.index_name,
                table=row.table_name,
                size_bytes=row.size_bytes,
                size_human=row.size_human,
                scans=row.scans,
                tuples_read=row.tuples_read,
                tuples_fetched=row.tuples_fetched,
                is_unique=row.is_unique,
                is_valid=row.is_valid,
                definition=row.definition,
            )
            stats.append(stat)
            self._stats_cache[stat.name] = stat

        self._last_stats_refresh = datetime.now(timezone.utc)
        return stats

    def find_unused_indexes(
        self,
        db: Session,
        min_size_bytes: int = 1024 * 1024,  # 1MB
        min_age_days: int = 7,
    ) -> List[IndexRecommendation]:
        """
        Find indexes that are not being used.

        Args:
            db: Database session
            min_size_bytes: Minimum index size to consider
            min_age_days: Minimum age of index

        Returns:
            List of recommendations to drop unused indexes
        """
        query = """
        SELECT
            s.indexrelname AS index_name,
            s.relname AS table_name,
            pg_relation_size(s.indexrelid) AS size_bytes,
            pg_size_pretty(pg_relation_size(s.indexrelid)) AS size_human,
            COALESCE(s.idx_scan, 0) AS scans,
            pg_get_indexdef(s.indexrelid) AS definition
        FROM pg_stat_user_indexes s
        JOIN pg_index i ON s.indexrelid = i.indexrelid
        WHERE s.idx_scan = 0
          AND NOT i.indisunique
          AND NOT i.indisprimary
          AND pg_relation_size(s.indexrelid) > :min_size
          AND s.indexrelid NOT IN (
              SELECT conindid FROM pg_constraint WHERE contype IN ('p', 'u', 'x')
          )
        ORDER BY pg_relation_size(s.indexrelid) DESC
        """

        result = db.execute(text(query), {"min_size": min_size_bytes})

        recommendations = []
        for row in result:
            rec = IndexRecommendation(
                action="drop",
                index_name=row.index_name,
                table=row.table_name,
                reason=f"Index has 0 scans and uses {row.size_human}",
                estimated_improvement=f"Free {row.size_human} of disk space",
                sql=f"DROP INDEX CONCURRENTLY IF EXISTS {row.index_name};",
                priority=2 if row.size_bytes > 10 * 1024 * 1024 else 3,  # Higher priority for larger indexes
            )
            recommendations.append(rec)

        return recommendations

    def find_duplicate_indexes(self, db: Session) -> List[IndexRecommendation]:
        """
        Find duplicate or overlapping indexes.

        Returns:
            List of recommendations to consolidate indexes
        """
        query = """
        WITH index_cols AS (
            SELECT
                i.indexrelid,
                i.indrelid,
                t.relname AS table_name,
                c.relname AS index_name,
                pg_get_indexdef(i.indexrelid) AS definition,
                array_agg(a.attname ORDER BY array_position(i.indkey, a.attnum)) AS columns,
                pg_relation_size(i.indexrelid) AS size_bytes
            FROM pg_index i
            JOIN pg_class c ON i.indexrelid = c.oid
            JOIN pg_class t ON i.indrelid = t.oid
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(i.indkey)
            WHERE t.relkind = 'r'
              AND c.relkind = 'i'
            GROUP BY i.indexrelid, i.indrelid, t.relname, c.relname
        )
        SELECT
            ic1.index_name AS index1,
            ic2.index_name AS index2,
            ic1.table_name,
            ic1.columns AS columns1,
            ic2.columns AS columns2,
            ic1.size_bytes AS size1,
            ic2.size_bytes AS size2,
            pg_size_pretty(ic1.size_bytes + ic2.size_bytes) AS combined_size
        FROM index_cols ic1
        JOIN index_cols ic2 ON ic1.indrelid = ic2.indrelid
          AND ic1.indexrelid < ic2.indexrelid
          AND ic1.columns = ic2.columns
        ORDER BY ic1.size_bytes + ic2.size_bytes DESC
        """

        result = db.execute(text(query))

        recommendations = []
        for row in result:
            # Keep the larger index (likely has more columns or is more useful)
            drop_index = row.index1 if row.size1 < row.size2 else row.index2
            keep_index = row.index2 if row.size1 < row.size2 else row.index1

            rec = IndexRecommendation(
                action="drop",
                index_name=drop_index,
                table=row.table_name,
                reason=f"Duplicate of {keep_index} - same columns: {row.columns1}",
                estimated_improvement=f"Free disk space, combined size: {row.combined_size}",
                sql=f"DROP INDEX CONCURRENTLY IF EXISTS {drop_index};",
                priority=1,
            )
            recommendations.append(rec)

        return recommendations

    def find_missing_indexes(self, db: Session) -> List[IndexRecommendation]:
        """
        Find missing indexes based on sequential scans.

        Returns:
            List of recommendations for new indexes
        """
        query = """
        SELECT
            t.relname AS table_name,
            s.seq_scan AS sequential_scans,
            s.seq_tup_read AS rows_read,
            s.idx_scan AS index_scans,
            pg_size_pretty(pg_relation_size(t.oid)) AS table_size
        FROM pg_stat_user_tables s
        JOIN pg_class t ON s.relid = t.oid
        WHERE s.seq_scan > 1000
          AND s.seq_tup_read > 100000
          AND (s.idx_scan IS NULL OR s.idx_scan < s.seq_scan)
        ORDER BY s.seq_tup_read DESC
        LIMIT 20
        """

        result = db.execute(text(query))

        recommendations = []
        for row in result:
            rec = IndexRecommendation(
                action="investigate",
                index_name=f"idx_{row.table_name}_*",
                table=row.table_name,
                reason=(
                    f"High sequential scans: {row.sequential_scans:,} scans, "
                    f"{row.rows_read:,} rows read"
                ),
                estimated_improvement="Potentially significant query performance improvement",
                sql=f"-- Analyze queries on {row.table_name} and create appropriate indexes",
                priority=1 if row.rows_read > 1000000 else 2,
            )
            recommendations.append(rec)

        return recommendations

    def find_missing_fk_indexes(self, db: Session) -> List[IndexRecommendation]:
        """
        Find foreign keys without indexes.

        Returns:
            List of recommendations for FK indexes
        """
        query = """
        SELECT
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND NOT EXISTS (
              SELECT 1 FROM pg_indexes
              WHERE tablename = tc.table_name
                AND indexdef LIKE '%' || kcu.column_name || '%'
          )
        """

        result = db.execute(text(query))

        recommendations = []
        for row in result:
            index_name = f"idx_{row.table_name}_{row.column_name}"
            rec = IndexRecommendation(
                action="create",
                index_name=index_name,
                table=row.table_name,
                reason=f"Foreign key to {row.foreign_table} without index",
                estimated_improvement="Faster JOIN operations and DELETE cascades",
                sql=f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {index_name} ON {row.table_name}({row.column_name});",
                priority=1,
            )
            recommendations.append(rec)

        return recommendations

    def analyze_query_plan(
        self,
        db: Session,
        query: str,
    ) -> QueryPlanAnalysis:
        """
        Analyze a query's execution plan.

        Args:
            db: Database session
            query: SQL query to analyze

        Returns:
            QueryPlanAnalysis with insights
        """
        explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"

        try:
            result = db.execute(text(explain_query))
            plan_json = result.fetchone()[0]

            plan = plan_json[0]["Plan"]

            analysis = QueryPlanAnalysis(
                query=query,
                plan=str(plan_json),
                total_cost=plan.get("Total Cost", 0),
                actual_time_ms=plan.get("Actual Total Time", 0),
                rows_estimated=plan.get("Plan Rows", 0),
                rows_actual=plan.get("Actual Rows", 0),
                seq_scans=0,
                index_scans=0,
            )

            # Count scan types and generate recommendations
            recommendations = []
            self._analyze_plan_node(plan, analysis, recommendations)
            analysis.recommendations = recommendations

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing query plan: {e}")
            return QueryPlanAnalysis(
                query=query,
                plan=str(e),
                total_cost=0,
                actual_time_ms=0,
                rows_estimated=0,
                rows_actual=0,
                seq_scans=0,
                index_scans=0,
                recommendations=[f"Error analyzing: {e}"],
            )

    def _analyze_plan_node(
        self,
        node: Dict[str, Any],
        analysis: QueryPlanAnalysis,
        recommendations: List[str],
    ):
        """Recursively analyze plan nodes."""
        node_type = node.get("Node Type", "")

        if node_type == "Seq Scan":
            analysis.seq_scans += 1
            table = node.get("Relation Name", "unknown")
            rows = node.get("Actual Rows", 0)
            if rows > 1000:
                recommendations.append(
                    f"Sequential scan on {table} returned {rows:,} rows - consider adding an index"
                )

        elif node_type in ["Index Scan", "Index Only Scan", "Bitmap Index Scan"]:
            analysis.index_scans += 1

        # Check for row estimate accuracy
        estimated = node.get("Plan Rows", 0)
        actual = node.get("Actual Rows", 0)
        if estimated > 0 and actual > 0:
            ratio = actual / estimated
            if ratio > 10 or ratio < 0.1:
                recommendations.append(
                    f"Row estimate off by {ratio:.1f}x - consider running ANALYZE"
                )

        # Process child nodes
        for child in node.get("Plans", []):
            self._analyze_plan_node(child, analysis, recommendations)

    def reindex_table(
        self,
        table_name: str,
        concurrent: bool = True,
        db: Optional[Session] = None,
    ) -> bool:
        """
        Reindex a table to rebuild fragmented indexes.

        Args:
            table_name: Table to reindex
            concurrent: Use REINDEX CONCURRENTLY
            db: Optional session

        Returns:
            True if successful
        """
        try:
            sql = f"REINDEX TABLE {'CONCURRENTLY ' if concurrent else ''}{table_name}"

            if db:
                db.execute(text(sql))
                db.commit()
            else:
                with self.engine.connect() as conn:
                    if concurrent:
                        conn.execution_options(isolation_level="AUTOCOMMIT")
                    conn.execute(text(sql))

            logger.info(f"Reindexed table: {table_name}")
            return True

        except Exception as e:
            logger.error(f"Error reindexing {table_name}: {e}")
            return False

    def update_statistics(
        self,
        table_name: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> bool:
        """
        Update table statistics for the query planner.

        Args:
            table_name: Optional specific table (None = all tables)
            db: Optional session

        Returns:
            True if successful
        """
        try:
            sql = f"ANALYZE {table_name}" if table_name else "ANALYZE"

            if db:
                db.execute(text(sql))
                db.commit()
            else:
                with self.engine.connect() as conn:
                    conn.execute(text(sql))

            logger.info(f"Updated statistics: {table_name or 'all tables'}")
            return True

        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
            return False

    def get_all_recommendations(self, db: Session) -> Dict[str, List[IndexRecommendation]]:
        """
        Get all index optimization recommendations.

        Returns:
            Dictionary categorized by recommendation type
        """
        return {
            "unused_indexes": self.find_unused_indexes(db),
            "duplicate_indexes": self.find_duplicate_indexes(db),
            "missing_indexes": self.find_missing_indexes(db),
            "missing_fk_indexes": self.find_missing_fk_indexes(db),
        }

    def get_index_health_report(self, db: Session) -> Dict[str, Any]:
        """
        Generate a comprehensive index health report.

        Returns:
            Dictionary with index health metrics
        """
        stats = self.get_index_stats(db, refresh=True)

        total_size = sum(s.size_bytes for s in stats)
        unused_indexes = [s for s in stats if s.scans == 0 and not s.is_unique]
        invalid_indexes = [s for s in stats if not s.is_valid]

        recommendations = self.get_all_recommendations(db)
        total_recommendations = sum(len(v) for v in recommendations.values())

        return {
            "summary": {
                "total_indexes": len(stats),
                "total_size_bytes": total_size,
                "total_size_human": f"{total_size / (1024*1024):.2f} MB",
                "unused_indexes": len(unused_indexes),
                "invalid_indexes": len(invalid_indexes),
                "total_recommendations": total_recommendations,
            },
            "health_score": self._calculate_health_score(stats, recommendations),
            "top_indexes_by_size": [
                {"name": s.name, "table": s.table, "size": s.size_human, "scans": s.scans}
                for s in sorted(stats, key=lambda x: x.size_bytes, reverse=True)[:10]
            ],
            "unused_indexes": [
                {"name": s.name, "table": s.table, "size": s.size_human}
                for s in unused_indexes[:10]
            ],
            "recommendations": {
                k: [{"index": r.index_name, "action": r.action, "reason": r.reason}
                    for r in v[:5]]
                for k, v in recommendations.items()
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _calculate_health_score(
        self,
        stats: List[IndexStats],
        recommendations: Dict[str, List[IndexRecommendation]],
    ) -> int:
        """Calculate index health score (0-100)."""
        score = 100

        # Deduct for unused indexes
        unused_count = len([s for s in stats if s.scans == 0 and not s.is_unique])
        score -= min(20, unused_count * 2)

        # Deduct for invalid indexes
        invalid_count = len([s for s in stats if not s.is_valid])
        score -= invalid_count * 10

        # Deduct for missing FK indexes
        score -= len(recommendations.get("missing_fk_indexes", [])) * 5

        # Deduct for duplicates
        score -= len(recommendations.get("duplicate_indexes", [])) * 3

        return max(0, score)


# Global index manager (initialized with engine)
_index_manager: Optional[IndexManager] = None


def get_index_manager(engine: Optional[Engine] = None) -> IndexManager:
    """Get or create the global index manager."""
    global _index_manager
    if _index_manager is None:
        if engine is None:
            from .connection import engine as default_engine
            engine = default_engine
        _index_manager = IndexManager(engine)
    return _index_manager

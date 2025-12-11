"""
Database Performance Monitoring

Comprehensive monitoring for database performance including:
- Query performance metrics
- Connection pool metrics
- Cache metrics
- Index health
- Partition health
- Replication lag monitoring
- Alert generation

EPIC-003: Database Performance Monitoring
"""

import asyncio
import os
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(str, Enum):
    """Types of metrics."""
    QUERY = "query"
    POOL = "pool"
    CACHE = "cache"
    INDEX = "index"
    PARTITION = "partition"
    REPLICATION = "replication"


@dataclass
class Alert:
    """Database performance alert."""
    alert_id: str
    severity: AlertSeverity
    metric_type: MetricType
    title: str
    message: str
    value: Any
    threshold: Any
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged: bool = False


@dataclass
class MetricThresholds:
    """Thresholds for generating alerts."""
    # Query performance
    slow_query_threshold_ms: float = 100
    very_slow_query_threshold_ms: float = 1000
    max_queries_per_second: int = 1000

    # Connection pool
    pool_utilization_warning: float = 0.7
    pool_utilization_critical: float = 0.9
    max_wait_time_ms: float = 100
    max_checkout_time_ms: float = 5000

    # Cache
    cache_hit_ratio_warning: float = 0.7
    cache_hit_ratio_critical: float = 0.5
    cache_memory_warning_mb: int = 200

    # Index
    unused_index_threshold_scans: int = 100
    index_bloat_threshold_percent: float = 20

    # Replication
    replication_lag_warning_seconds: float = 2.0
    replication_lag_critical_seconds: float = 10.0


@dataclass
class PerformanceSnapshot:
    """Point-in-time performance snapshot."""
    timestamp: datetime
    query_stats: Dict[str, Any]
    pool_stats: Dict[str, Any]
    cache_stats: Dict[str, Any]
    index_stats: Dict[str, Any]
    partition_stats: Dict[str, Any]
    replication_stats: Dict[str, Any]
    active_alerts: List[Alert]
    health_score: int


class DatabaseMonitor:
    """
    Central database performance monitoring.

    Collects metrics from all database subsystems and generates
    alerts when thresholds are exceeded.
    """

    def __init__(
        self,
        engine: Engine,
        thresholds: Optional[MetricThresholds] = None,
        check_interval_seconds: int = 60,
    ):
        self.engine = engine
        self.thresholds = thresholds or MetricThresholds()
        self.check_interval = check_interval_seconds

        # Metrics storage
        self._snapshots: List[PerformanceSnapshot] = []
        self._max_snapshots = 1440  # 24 hours at 1-minute intervals
        self._alerts: List[Alert] = []
        self._max_alerts = 1000

        # Callbacks
        self._alert_callbacks: List[Callable[[Alert], None]] = []

        # Monitoring state
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Alert counter for unique IDs
        self._alert_counter = 0

    def start(self):
        """Start the monitoring thread."""
        if self._running:
            return

        self._running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="database-monitor",
        )
        self._monitor_thread.start()
        logger.info("Database monitor started")

    def stop(self):
        """Stop the monitoring thread."""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=10)
        logger.info("Database monitor stopped")

    def register_alert_callback(self, callback: Callable[[Alert], None]):
        """Register a callback for alerts."""
        self._alert_callbacks.append(callback)

    def _monitor_loop(self):
        """Background monitoring loop."""
        while self._running:
            try:
                snapshot = self._collect_metrics()
                self._store_snapshot(snapshot)
                self._check_thresholds(snapshot)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

            time.sleep(self.check_interval)

    def _collect_metrics(self) -> PerformanceSnapshot:
        """Collect all performance metrics."""
        from sqlalchemy.orm import Session

        with Session(self.engine) as db:
            query_stats = self._collect_query_stats(db)
            pool_stats = self._collect_pool_stats()
            cache_stats = self._collect_cache_stats()
            index_stats = self._collect_index_stats(db)
            partition_stats = self._collect_partition_stats(db)
            replication_stats = self._collect_replication_stats(db)

        # Calculate health score
        health_score = self._calculate_health_score(
            query_stats, pool_stats, cache_stats, index_stats, replication_stats
        )

        with self._lock:
            active_alerts = [a for a in self._alerts if not a.acknowledged]

        return PerformanceSnapshot(
            timestamp=datetime.now(timezone.utc),
            query_stats=query_stats,
            pool_stats=pool_stats,
            cache_stats=cache_stats,
            index_stats=index_stats,
            partition_stats=partition_stats,
            replication_stats=replication_stats,
            active_alerts=active_alerts,
            health_score=health_score,
        )

    def _collect_query_stats(self, db: Session) -> Dict[str, Any]:
        """Collect query performance statistics."""
        try:
            # Get pg_stat_statements if available
            query = """
                SELECT
                    COUNT(*) as total_queries,
                    SUM(calls) as total_calls,
                    AVG(mean_exec_time) as avg_exec_time_ms,
                    MAX(max_exec_time) as max_exec_time_ms,
                    SUM(rows) as total_rows
                FROM pg_stat_statements
                WHERE dbid = (SELECT oid FROM pg_database WHERE datname = current_database())
            """

            try:
                result = db.execute(text(query))
                row = result.fetchone()
                if row:
                    return {
                        "total_queries": row.total_queries or 0,
                        "total_calls": row.total_calls or 0,
                        "avg_exec_time_ms": float(row.avg_exec_time_ms or 0),
                        "max_exec_time_ms": float(row.max_exec_time_ms or 0),
                        "total_rows": row.total_rows or 0,
                    }
            except:
                pass  # pg_stat_statements not available

            # Fallback to basic stats
            query = """
                SELECT
                    SUM(seq_scan) as seq_scans,
                    SUM(idx_scan) as idx_scans,
                    SUM(n_tup_ins) as inserts,
                    SUM(n_tup_upd) as updates,
                    SUM(n_tup_del) as deletes
                FROM pg_stat_user_tables
            """
            result = db.execute(text(query))
            row = result.fetchone()

            return {
                "seq_scans": row.seq_scans or 0,
                "idx_scans": row.idx_scans or 0,
                "inserts": row.inserts or 0,
                "updates": row.updates or 0,
                "deletes": row.deletes or 0,
            }

        except Exception as e:
            logger.error(f"Error collecting query stats: {e}")
            return {}

    def _collect_pool_stats(self) -> Dict[str, Any]:
        """Collect connection pool statistics."""
        try:
            pool = self.engine.pool

            checked_out = pool.checkedout()
            pool_size = pool.size()
            overflow = pool.overflow()

            utilization = checked_out / pool_size if pool_size > 0 else 0

            return {
                "pool_size": pool_size,
                "checked_out": checked_out,
                "overflow": overflow,
                "checked_in": pool.checkedin(),
                "utilization": utilization,
            }

        except Exception as e:
            logger.error(f"Error collecting pool stats: {e}")
            return {}

    def _collect_cache_stats(self) -> Dict[str, Any]:
        """Collect cache statistics."""
        try:
            from .cache import cache_manager

            stats = cache_manager.get_stats()
            return {
                "hits": stats.get("hits", 0),
                "misses": stats.get("misses", 0),
                "hit_ratio": stats.get("hit_ratio", 0),
                "sets": stats.get("sets", 0),
                "deletes": stats.get("deletes", 0),
                "errors": stats.get("errors", 0),
                "local_cache_size": stats.get("local_cache_size", 0),
            }

        except Exception as e:
            logger.debug(f"Cache stats not available: {e}")
            return {}

    def _collect_index_stats(self, db: Session) -> Dict[str, Any]:
        """Collect index statistics."""
        try:
            query = """
                SELECT
                    COUNT(*) as total_indexes,
                    SUM(pg_relation_size(indexrelid)) as total_size,
                    COUNT(*) FILTER (WHERE idx_scan = 0) as unused_indexes
                FROM pg_stat_user_indexes
            """
            result = db.execute(text(query))
            row = result.fetchone()

            return {
                "total_indexes": row.total_indexes or 0,
                "total_size_bytes": row.total_size or 0,
                "total_size_mb": (row.total_size or 0) / (1024 * 1024),
                "unused_indexes": row.unused_indexes or 0,
            }

        except Exception as e:
            logger.error(f"Error collecting index stats: {e}")
            return {}

    def _collect_partition_stats(self, db: Session) -> Dict[str, Any]:
        """Collect partitioning statistics."""
        try:
            query = """
                SELECT
                    COUNT(DISTINCT inhparent) as partitioned_tables,
                    COUNT(*) as total_partitions
                FROM pg_inherits
            """
            result = db.execute(text(query))
            row = result.fetchone()

            return {
                "partitioned_tables": row.partitioned_tables or 0,
                "total_partitions": row.total_partitions or 0,
            }

        except Exception as e:
            logger.error(f"Error collecting partition stats: {e}")
            return {}

    def _collect_replication_stats(self, db: Session) -> Dict[str, Any]:
        """Collect replication statistics."""
        try:
            # Check if this is a replica
            query = """
                SELECT
                    pg_is_in_recovery() as is_replica,
                    CASE
                        WHEN pg_is_in_recovery() THEN
                            EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp()))
                        ELSE 0
                    END as lag_seconds
            """
            result = db.execute(text(query))
            row = result.fetchone()

            # Get replication slot info for primary
            slots_query = """
                SELECT
                    slot_name,
                    active,
                    pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) as lag_bytes
                FROM pg_replication_slots
            """

            slots = []
            try:
                slots_result = db.execute(text(slots_query))
                for slot_row in slots_result:
                    slots.append({
                        "name": slot_row.slot_name,
                        "active": slot_row.active,
                        "lag_bytes": slot_row.lag_bytes or 0,
                    })
            except:
                pass  # May not have replication slots

            return {
                "is_replica": row.is_replica if row else False,
                "lag_seconds": float(row.lag_seconds or 0) if row else 0,
                "replication_slots": slots,
            }

        except Exception as e:
            logger.error(f"Error collecting replication stats: {e}")
            return {}

    def _calculate_health_score(
        self,
        query_stats: Dict,
        pool_stats: Dict,
        cache_stats: Dict,
        index_stats: Dict,
        replication_stats: Dict,
    ) -> int:
        """Calculate overall health score (0-100)."""
        score = 100

        # Pool utilization impact
        utilization = pool_stats.get("utilization", 0)
        if utilization > self.thresholds.pool_utilization_critical:
            score -= 30
        elif utilization > self.thresholds.pool_utilization_warning:
            score -= 15

        # Cache hit ratio impact
        hit_ratio = cache_stats.get("hit_ratio", 1.0)
        if hit_ratio < self.thresholds.cache_hit_ratio_critical:
            score -= 20
        elif hit_ratio < self.thresholds.cache_hit_ratio_warning:
            score -= 10

        # Unused indexes impact
        unused = index_stats.get("unused_indexes", 0)
        score -= min(10, unused)

        # Replication lag impact
        lag = replication_stats.get("lag_seconds", 0)
        if lag > self.thresholds.replication_lag_critical_seconds:
            score -= 25
        elif lag > self.thresholds.replication_lag_warning_seconds:
            score -= 10

        return max(0, score)

    def _store_snapshot(self, snapshot: PerformanceSnapshot):
        """Store a performance snapshot."""
        with self._lock:
            self._snapshots.append(snapshot)
            if len(self._snapshots) > self._max_snapshots:
                self._snapshots = self._snapshots[-self._max_snapshots:]

    def _check_thresholds(self, snapshot: PerformanceSnapshot):
        """Check metrics against thresholds and generate alerts."""
        # Pool utilization
        utilization = snapshot.pool_stats.get("utilization", 0)
        if utilization > self.thresholds.pool_utilization_critical:
            self._create_alert(
                AlertSeverity.CRITICAL,
                MetricType.POOL,
                "Critical pool utilization",
                f"Connection pool is at {utilization*100:.1f}% capacity",
                utilization,
                self.thresholds.pool_utilization_critical,
            )
        elif utilization > self.thresholds.pool_utilization_warning:
            self._create_alert(
                AlertSeverity.WARNING,
                MetricType.POOL,
                "High pool utilization",
                f"Connection pool is at {utilization*100:.1f}% capacity",
                utilization,
                self.thresholds.pool_utilization_warning,
            )

        # Cache hit ratio
        hit_ratio = snapshot.cache_stats.get("hit_ratio", 1.0)
        if hit_ratio < self.thresholds.cache_hit_ratio_critical:
            self._create_alert(
                AlertSeverity.ERROR,
                MetricType.CACHE,
                "Critical cache hit ratio",
                f"Cache hit ratio is {hit_ratio*100:.1f}%",
                hit_ratio,
                self.thresholds.cache_hit_ratio_critical,
            )
        elif hit_ratio < self.thresholds.cache_hit_ratio_warning:
            self._create_alert(
                AlertSeverity.WARNING,
                MetricType.CACHE,
                "Low cache hit ratio",
                f"Cache hit ratio is {hit_ratio*100:.1f}%",
                hit_ratio,
                self.thresholds.cache_hit_ratio_warning,
            )

        # Replication lag
        lag = snapshot.replication_stats.get("lag_seconds", 0)
        if lag > self.thresholds.replication_lag_critical_seconds:
            self._create_alert(
                AlertSeverity.CRITICAL,
                MetricType.REPLICATION,
                "Critical replication lag",
                f"Replication lag is {lag:.1f} seconds",
                lag,
                self.thresholds.replication_lag_critical_seconds,
            )
        elif lag > self.thresholds.replication_lag_warning_seconds:
            self._create_alert(
                AlertSeverity.WARNING,
                MetricType.REPLICATION,
                "High replication lag",
                f"Replication lag is {lag:.1f} seconds",
                lag,
                self.thresholds.replication_lag_warning_seconds,
            )

    def _create_alert(
        self,
        severity: AlertSeverity,
        metric_type: MetricType,
        title: str,
        message: str,
        value: Any,
        threshold: Any,
    ):
        """Create and store an alert."""
        with self._lock:
            self._alert_counter += 1
            alert = Alert(
                alert_id=f"alert-{self._alert_counter}",
                severity=severity,
                metric_type=metric_type,
                title=title,
                message=message,
                value=value,
                threshold=threshold,
            )

            # Check for duplicate recent alerts
            recent_cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
            duplicate = any(
                a.title == title and a.timestamp > recent_cutoff
                for a in self._alerts
            )

            if not duplicate:
                self._alerts.append(alert)
                if len(self._alerts) > self._max_alerts:
                    self._alerts = self._alerts[-self._max_alerts:]

                # Notify callbacks
                for callback in self._alert_callbacks:
                    try:
                        callback(alert)
                    except Exception as e:
                        logger.error(f"Alert callback error: {e}")

                logger.log(
                    logging.ERROR if severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL] else logging.WARNING,
                    f"Database alert: {title} - {message}"
                )

    def get_latest_snapshot(self) -> Optional[PerformanceSnapshot]:
        """Get the most recent performance snapshot."""
        with self._lock:
            return self._snapshots[-1] if self._snapshots else None

    def get_snapshots(
        self,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[PerformanceSnapshot]:
        """Get performance snapshots."""
        with self._lock:
            snapshots = self._snapshots

            if since:
                snapshots = [s for s in snapshots if s.timestamp >= since]

            return snapshots[-limit:]

    def get_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 100,
    ) -> List[Alert]:
        """Get alerts with optional filtering."""
        with self._lock:
            alerts = self._alerts

            if severity:
                alerts = [a for a in alerts if a.severity == severity]

            if acknowledged is not None:
                alerts = [a for a in alerts if a.acknowledged == acknowledged]

            return alerts[-limit:]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        with self._lock:
            for alert in self._alerts:
                if alert.alert_id == alert_id:
                    alert.acknowledged = True
                    return True
            return False

    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get data for monitoring dashboard.

        Returns comprehensive metrics for dashboard display.
        """
        snapshot = self.get_latest_snapshot()

        if not snapshot:
            return {"error": "No data available"}

        # Get trend data (last hour)
        hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        recent_snapshots = self.get_snapshots(since=hour_ago)

        # Calculate trends
        pool_utilization_trend = [
            {"time": s.timestamp.isoformat(), "value": s.pool_stats.get("utilization", 0) * 100}
            for s in recent_snapshots
        ]

        cache_hit_trend = [
            {"time": s.timestamp.isoformat(), "value": s.cache_stats.get("hit_ratio", 0) * 100}
            for s in recent_snapshots
        ]

        health_trend = [
            {"time": s.timestamp.isoformat(), "value": s.health_score}
            for s in recent_snapshots
        ]

        return {
            "health_score": snapshot.health_score,
            "timestamp": snapshot.timestamp.isoformat(),
            "summary": {
                "query_stats": snapshot.query_stats,
                "pool_stats": snapshot.pool_stats,
                "cache_stats": snapshot.cache_stats,
                "index_stats": snapshot.index_stats,
                "partition_stats": snapshot.partition_stats,
                "replication_stats": snapshot.replication_stats,
            },
            "alerts": {
                "total": len(snapshot.active_alerts),
                "critical": len([a for a in snapshot.active_alerts if a.severity == AlertSeverity.CRITICAL]),
                "warning": len([a for a in snapshot.active_alerts if a.severity == AlertSeverity.WARNING]),
                "recent": [
                    {"title": a.title, "severity": a.severity.value, "message": a.message}
                    for a in snapshot.active_alerts[:5]
                ],
            },
            "trends": {
                "pool_utilization": pool_utilization_trend[-60:],  # Last 60 points
                "cache_hit_ratio": cache_hit_trend[-60:],
                "health_score": health_trend[-60:],
            },
        }


# Global monitor instance
_monitor: Optional[DatabaseMonitor] = None


def get_database_monitor(engine: Optional[Engine] = None) -> DatabaseMonitor:
    """Get or create the global database monitor."""
    global _monitor
    if _monitor is None:
        if engine is None:
            from .connection import engine as default_engine
            engine = default_engine
        _monitor = DatabaseMonitor(engine)
        _monitor.start()
    return _monitor

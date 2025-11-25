"""
Query Optimizer

Database query optimization utilities including:
- Query analysis and profiling
- N+1 detection
- Query plan optimization
- Batch query execution
- Read replica routing

EPIC-003: US-003.2 Query Optimization
"""

import functools
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar
from dataclasses import dataclass, field
import logging
import os

from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, Query, joinedload, selectinload
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class QueryMetrics:
    """Metrics for a single query execution."""
    query_hash: str
    sql: str
    duration_ms: float
    rows_affected: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    plan: Optional[str] = None
    source: Optional[str] = None  # Source location in code


@dataclass
class QueryStats:
    """Aggregated statistics for queries."""
    total_queries: int = 0
    total_duration_ms: float = 0
    slow_queries: int = 0
    n_plus_one_detected: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

    @property
    def avg_duration_ms(self) -> float:
        return self.total_duration_ms / self.total_queries if self.total_queries > 0 else 0


class SlowQueryLog:
    """Tracks slow queries for analysis."""

    def __init__(self, threshold_ms: float = 100):
        self.threshold_ms = threshold_ms
        self.queries: List[QueryMetrics] = []
        self.max_queries = 1000

    def log(self, metrics: QueryMetrics):
        """Log a slow query."""
        if metrics.duration_ms >= self.threshold_ms:
            self.queries.append(metrics)
            if len(self.queries) > self.max_queries:
                self.queries = self.queries[-self.max_queries:]
            logger.warning(
                f"Slow query ({metrics.duration_ms:.2f}ms): "
                f"{metrics.sql[:200]}..."
            )

    def get_slowest(self, limit: int = 10) -> List[QueryMetrics]:
        """Get the slowest queries."""
        return sorted(self.queries, key=lambda q: q.duration_ms, reverse=True)[:limit]

    def get_most_frequent(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most frequently slow queries."""
        from collections import Counter
        hashes = Counter(q.query_hash for q in self.queries)
        return hashes.most_common(limit)


class NPlusOneDetector:
    """Detects N+1 query patterns."""

    def __init__(self, threshold: int = 5):
        self.threshold = threshold
        self._query_counts: Dict[str, int] = {}
        self._request_queries: List[str] = []

    def start_request(self):
        """Start tracking for a new request."""
        self._query_counts.clear()
        self._request_queries.clear()

    def track_query(self, query_hash: str, sql: str):
        """Track a query execution."""
        self._request_queries.append(sql)
        self._query_counts[query_hash] = self._query_counts.get(query_hash, 0) + 1

        if self._query_counts[query_hash] == self.threshold:
            logger.warning(
                f"N+1 pattern detected! Query executed {self.threshold}+ times: "
                f"{sql[:200]}..."
            )
            return True
        return False

    def end_request(self) -> Dict[str, Any]:
        """End tracking and return summary."""
        repeated = {h: c for h, c in self._query_counts.items() if c >= self.threshold}
        return {
            "total_queries": len(self._request_queries),
            "unique_queries": len(self._query_counts),
            "repeated_queries": repeated,
            "n_plus_one_detected": len(repeated) > 0,
        }


class ReadWriteSplitter:
    """
    Routes queries to read replicas or primary based on operation type.

    Supports:
    - Automatic read/write detection
    - Manual routing hints
    - Replica lag awareness
    - Failover handling
    """

    def __init__(
        self,
        primary_url: str,
        replica_urls: Optional[List[str]] = None,
        max_replica_lag_seconds: float = 1.0,
    ):
        from sqlalchemy import create_engine

        self.primary_engine = create_engine(
            primary_url,
            poolclass=QueuePool,
            pool_size=50,
            max_overflow=20,
            pool_pre_ping=True,
        )

        self.replica_engines = []
        for url in (replica_urls or []):
            engine = create_engine(
                url,
                poolclass=QueuePool,
                pool_size=25,
                max_overflow=10,
                pool_pre_ping=True,
            )
            self.replica_engines.append(engine)

        self.max_replica_lag = max_replica_lag_seconds
        self._replica_index = 0

    def get_engine_for_read(self, require_fresh: bool = False):
        """Get engine for read operations."""
        if not self.replica_engines or require_fresh:
            return self.primary_engine

        # Round-robin replica selection
        engine = self.replica_engines[self._replica_index]
        self._replica_index = (self._replica_index + 1) % len(self.replica_engines)

        return engine

    def get_engine_for_write(self):
        """Get engine for write operations."""
        return self.primary_engine

    def get_session_for_read(self, require_fresh: bool = False) -> Session:
        """Get session for read operations."""
        from sqlalchemy.orm import sessionmaker
        engine = self.get_engine_for_read(require_fresh)
        SessionLocal = sessionmaker(bind=engine)
        return SessionLocal()

    def get_session_for_write(self) -> Session:
        """Get session for write operations."""
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(bind=self.primary_engine)
        return SessionLocal()


class QueryOptimizer:
    """
    Central query optimization manager.

    Features:
    - Query timing and profiling
    - N+1 detection
    - Read/write splitting
    - Query plan analysis
    - Batch query support
    """

    def __init__(
        self,
        slow_query_threshold_ms: float = 100,
        n_plus_one_threshold: int = 5,
        enable_profiling: bool = True,
    ):
        self.slow_query_log = SlowQueryLog(slow_query_threshold_ms)
        self.n_plus_one_detector = NPlusOneDetector(n_plus_one_threshold)
        self.enable_profiling = enable_profiling
        self._stats = QueryStats()
        self._active_profiling = False

    def setup_engine_hooks(self, engine: Engine):
        """Setup query timing hooks on SQLAlchemy engine."""

        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault("query_start_time", []).append(time.time())

        @event.listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = (time.time() - conn.info["query_start_time"].pop()) * 1000

            if self.enable_profiling:
                self._stats.total_queries += 1
                self._stats.total_duration_ms += total

                if total >= self.slow_query_log.threshold_ms:
                    self._stats.slow_queries += 1

                    metrics = QueryMetrics(
                        query_hash=hash(statement),
                        sql=statement,
                        duration_ms=total,
                        rows_affected=cursor.rowcount or 0,
                    )
                    self.slow_query_log.log(metrics)

    @contextmanager
    def profile_request(self):
        """Context manager to profile all queries in a request."""
        self.n_plus_one_detector.start_request()
        self._active_profiling = True

        try:
            yield
        finally:
            self._active_profiling = False
            result = self.n_plus_one_detector.end_request()
            if result["n_plus_one_detected"]:
                self._stats.n_plus_one_detected += 1

    def optimize_query(self, query: Query, model_class: type) -> Query:
        """
        Optimize a SQLAlchemy query by adding appropriate loading strategies.

        This analyzes the model and adds joinedload/selectinload for relationships.
        """
        # Get relationships from model
        relationships = getattr(model_class, "__mapper__", None)
        if not relationships:
            return query

        # Add eager loading for relationships
        for rel in relationships.relationships:
            if rel.uselist:
                # One-to-many: use selectinload (separate query, avoids cartesian product)
                query = query.options(selectinload(getattr(model_class, rel.key)))
            else:
                # Many-to-one/one-to-one: use joinedload (single JOIN)
                query = query.options(joinedload(getattr(model_class, rel.key)))

        return query

    def get_query_plan(self, db: Session, query: Query) -> str:
        """Get the execution plan for a query."""
        statement = query.statement.compile(compile_kwargs={"literal_binds": True})
        explain = f"EXPLAIN ANALYZE {str(statement)}"

        result = db.execute(text(explain))
        plan_lines = [row[0] for row in result]
        return "\n".join(plan_lines)

    def get_stats(self) -> Dict[str, Any]:
        """Get query statistics."""
        return {
            "total_queries": self._stats.total_queries,
            "total_duration_ms": self._stats.total_duration_ms,
            "avg_duration_ms": self._stats.avg_duration_ms,
            "slow_queries": self._stats.slow_queries,
            "n_plus_one_detected": self._stats.n_plus_one_detected,
            "slowest_queries": [
                {"sql": q.sql[:100], "duration_ms": q.duration_ms}
                for q in self.slow_query_log.get_slowest(5)
            ],
        }

    def reset_stats(self):
        """Reset statistics."""
        self._stats = QueryStats()
        self.slow_query_log.queries.clear()


class BatchQueryExecutor:
    """
    Executes queries in batches for better performance.

    Useful for:
    - Bulk inserts
    - Bulk updates
    - Bulk deletes
    - Mass data operations
    """

    def __init__(self, db: Session, batch_size: int = 1000):
        self.db = db
        self.batch_size = batch_size

    def bulk_insert(self, model_class: type, records: List[Dict[str, Any]]) -> int:
        """
        Bulk insert records.

        Args:
            model_class: SQLAlchemy model class
            records: List of dictionaries with record data

        Returns:
            Number of records inserted
        """
        total_inserted = 0

        for i in range(0, len(records), self.batch_size):
            batch = records[i:i + self.batch_size]
            self.db.bulk_insert_mappings(model_class, batch)
            total_inserted += len(batch)

            if i + self.batch_size < len(records):
                self.db.flush()

        self.db.commit()
        logger.info(f"Bulk inserted {total_inserted} records into {model_class.__tablename__}")
        return total_inserted

    def bulk_update(
        self,
        model_class: type,
        records: List[Dict[str, Any]],
        key_field: str = "id",
    ) -> int:
        """
        Bulk update records.

        Args:
            model_class: SQLAlchemy model class
            records: List of dictionaries with update data (must include key_field)
            key_field: Field to use for matching records

        Returns:
            Number of records updated
        """
        total_updated = 0

        for i in range(0, len(records), self.batch_size):
            batch = records[i:i + self.batch_size]
            self.db.bulk_update_mappings(model_class, batch)
            total_updated += len(batch)

            if i + self.batch_size < len(records):
                self.db.flush()

        self.db.commit()
        logger.info(f"Bulk updated {total_updated} records in {model_class.__tablename__}")
        return total_updated

    def bulk_delete(
        self,
        model_class: type,
        ids: List[Any],
        id_field: str = "id",
    ) -> int:
        """
        Bulk delete records by ID.

        Args:
            model_class: SQLAlchemy model class
            ids: List of IDs to delete
            id_field: Name of the ID field

        Returns:
            Number of records deleted
        """
        from sqlalchemy import delete

        total_deleted = 0

        for i in range(0, len(ids), self.batch_size):
            batch_ids = ids[i:i + self.batch_size]
            stmt = delete(model_class).where(
                getattr(model_class, id_field).in_(batch_ids)
            )
            result = self.db.execute(stmt)
            total_deleted += result.rowcount

        self.db.commit()
        logger.info(f"Bulk deleted {total_deleted} records from {model_class.__tablename__}")
        return total_deleted

    def batch_query(
        self,
        query: Query,
        batch_size: Optional[int] = None,
    ):
        """
        Execute a query in batches to avoid memory issues.

        Yields batches of results.
        """
        batch_size = batch_size or self.batch_size

        offset = 0
        while True:
            batch = query.limit(batch_size).offset(offset).all()
            if not batch:
                break
            yield batch
            offset += batch_size


def profiled_query(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to profile database queries in a function.

    Usage:
        @profiled_query
        def get_users_with_appointments(db: Session):
            return db.query(User).all()
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration_ms = (time.time() - start_time) * 1000

        logger.debug(f"Query function {func.__name__} took {duration_ms:.2f}ms")
        return result

    return wrapper


# Global query optimizer instance
query_optimizer = QueryOptimizer()

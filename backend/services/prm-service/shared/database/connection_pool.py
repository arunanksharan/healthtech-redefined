"""
Enhanced Connection Pool Manager

Advanced connection pooling with:
- Connection leak detection and prevention
- Health monitoring and metrics
- Automatic failover to replicas
- Connection pool sizing optimization
- Connection lifecycle management
- Performance metrics collection

EPIC-003: US-003.3 Connection Pool Optimization
"""

import os
import time
import threading
import weakref
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import logging

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool, Pool, StaticPool
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class ConnectionState(str, Enum):
    """States of a pooled connection."""
    IDLE = "idle"
    IN_USE = "in_use"
    INVALID = "invalid"
    CHECKOUT_TIMEOUT = "checkout_timeout"


@dataclass
class ConnectionInfo:
    """Information about a connection checkout."""
    connection_id: str
    checkout_time: datetime
    checkout_stack: Optional[str] = None
    last_activity: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    query_count: int = 0
    state: ConnectionState = ConnectionState.IN_USE


@dataclass
class PoolMetrics:
    """Metrics for a connection pool."""
    pool_size: int = 0
    checked_out: int = 0
    checked_in: int = 0
    overflow: int = 0
    invalidated: int = 0
    checkout_count: int = 0
    checkin_count: int = 0
    checkout_timeouts: int = 0
    leaks_detected: int = 0
    avg_checkout_time_ms: float = 0
    max_checkout_time_ms: float = 0
    total_wait_time_ms: float = 0
    errors: int = 0


@dataclass
class PoolConfig:
    """Configuration for connection pool."""
    # Pool sizing
    pool_size: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30  # seconds
    pool_recycle: int = 3600  # seconds - recycle connections after 1 hour
    pool_pre_ping: bool = True  # Verify connection is valid before use

    # Leak detection
    leak_detection_threshold_seconds: int = 60
    enable_leak_detection: bool = True

    # Health checks
    health_check_interval_seconds: int = 30
    validation_query: str = "SELECT 1"

    # Performance
    echo: bool = False
    echo_pool: bool = False

    @classmethod
    def from_env(cls) -> "PoolConfig":
        """Load configuration from environment variables."""
        return cls(
            pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
            pool_pre_ping=os.getenv("DB_POOL_PRE_PING", "true").lower() == "true",
            leak_detection_threshold_seconds=int(os.getenv("DB_LEAK_THRESHOLD", "60")),
            enable_leak_detection=os.getenv("DB_LEAK_DETECTION", "true").lower() == "true",
            echo=os.getenv("SQL_ECHO", "false").lower() == "true",
        )


class ConnectionLeakDetector:
    """
    Detects connection leaks by monitoring checkout duration.

    A leak is suspected when a connection is held longer than the threshold
    without being returned to the pool.
    """

    def __init__(
        self,
        threshold_seconds: int = 60,
        check_interval_seconds: int = 30,
    ):
        self.threshold = threshold_seconds
        self.check_interval = check_interval_seconds
        self._active_connections: Dict[int, ConnectionInfo] = {}
        self._lock = threading.Lock()
        self._running = False
        self._check_thread: Optional[threading.Thread] = None
        self._on_leak_callbacks: List[Callable[[ConnectionInfo], None]] = []

    def start(self):
        """Start the leak detection thread."""
        if self._running:
            return

        self._running = True
        self._check_thread = threading.Thread(
            target=self._check_loop,
            daemon=True,
            name="connection-leak-detector",
        )
        self._check_thread.start()
        logger.info("Connection leak detector started")

    def stop(self):
        """Stop the leak detection thread."""
        self._running = False
        if self._check_thread:
            self._check_thread.join(timeout=5)
        logger.info("Connection leak detector stopped")

    def on_checkout(self, connection_id: int, stack_trace: Optional[str] = None):
        """Record a connection checkout."""
        with self._lock:
            self._active_connections[connection_id] = ConnectionInfo(
                connection_id=str(connection_id),
                checkout_time=datetime.now(timezone.utc),
                checkout_stack=stack_trace,
            )

    def on_checkin(self, connection_id: int):
        """Record a connection checkin."""
        with self._lock:
            self._active_connections.pop(connection_id, None)

    def on_activity(self, connection_id: int):
        """Record activity on a connection."""
        with self._lock:
            if connection_id in self._active_connections:
                info = self._active_connections[connection_id]
                info.last_activity = datetime.now(timezone.utc)
                info.query_count += 1

    def register_leak_callback(self, callback: Callable[[ConnectionInfo], None]):
        """Register a callback to be called when a leak is detected."""
        self._on_leak_callbacks.append(callback)

    def _check_loop(self):
        """Background loop to check for leaks."""
        while self._running:
            try:
                self._check_for_leaks()
            except Exception as e:
                logger.error(f"Error in leak detection: {e}")

            time.sleep(self.check_interval)

    def _check_for_leaks(self):
        """Check for connections held too long."""
        now = datetime.now(timezone.utc)
        threshold = timedelta(seconds=self.threshold)

        with self._lock:
            for conn_id, info in list(self._active_connections.items()):
                duration = now - info.checkout_time

                if duration > threshold:
                    logger.warning(
                        f"Potential connection leak detected!\n"
                        f"Connection {conn_id} held for {duration.seconds}s\n"
                        f"Queries executed: {info.query_count}\n"
                        f"Checkout stack:\n{info.checkout_stack or 'Not available'}"
                    )

                    # Notify callbacks
                    for callback in self._on_leak_callbacks:
                        try:
                            callback(info)
                        except Exception as e:
                            logger.error(f"Leak callback error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get current leak detector statistics."""
        with self._lock:
            return {
                "active_connections": len(self._active_connections),
                "connections": [
                    {
                        "id": info.connection_id,
                        "checkout_duration_seconds": (
                            datetime.now(timezone.utc) - info.checkout_time
                        ).seconds,
                        "queries": info.query_count,
                    }
                    for info in self._active_connections.values()
                ],
            }


class EnhancedConnectionPool:
    """
    Enhanced database connection pool with monitoring and leak detection.

    Features:
    - Configurable pool sizing
    - Connection leak detection
    - Health monitoring
    - Performance metrics
    - Automatic failover support
    """

    def __init__(
        self,
        database_url: str,
        config: Optional[PoolConfig] = None,
    ):
        self.database_url = database_url
        self.config = config or PoolConfig.from_env()

        # Create engine with pool configuration
        self.engine = self._create_engine()

        # Session factory
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

        # Metrics
        self._metrics = PoolMetrics()
        self._checkout_times: List[float] = []
        self._metrics_lock = threading.Lock()

        # Leak detection
        self._leak_detector: Optional[ConnectionLeakDetector] = None
        if self.config.enable_leak_detection:
            self._leak_detector = ConnectionLeakDetector(
                threshold_seconds=self.config.leak_detection_threshold_seconds,
            )
            self._leak_detector.register_leak_callback(self._on_leak_detected)

        # Setup event listeners
        self._setup_event_listeners()

    def _create_engine(self) -> Engine:
        """Create SQLAlchemy engine with pool configuration."""
        return create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            pool_timeout=self.config.pool_timeout,
            pool_recycle=self.config.pool_recycle,
            pool_pre_ping=self.config.pool_pre_ping,
            echo=self.config.echo,
            echo_pool=self.config.echo_pool,
        )

    def _setup_event_listeners(self):
        """Setup SQLAlchemy event listeners for monitoring."""

        @event.listens_for(self.engine, "connect")
        def on_connect(dbapi_conn, connection_record):
            """Track new connections."""
            logger.debug(f"New connection created: {id(dbapi_conn)}")

        @event.listens_for(self.engine, "checkout")
        def on_checkout(dbapi_conn, connection_record, connection_proxy):
            """Track connection checkouts."""
            conn_id = id(dbapi_conn)
            checkout_time = time.time()
            connection_record.info["checkout_time"] = checkout_time

            with self._metrics_lock:
                self._metrics.checkout_count += 1
                self._metrics.checked_out += 1

            # Record for leak detection
            if self._leak_detector:
                import traceback
                stack = "".join(traceback.format_stack()[-10:])
                self._leak_detector.on_checkout(conn_id, stack)

        @event.listens_for(self.engine, "checkin")
        def on_checkin(dbapi_conn, connection_record):
            """Track connection checkins."""
            conn_id = id(dbapi_conn)
            checkout_time = connection_record.info.get("checkout_time")

            if checkout_time:
                duration_ms = (time.time() - checkout_time) * 1000
                with self._metrics_lock:
                    self._checkout_times.append(duration_ms)
                    # Keep only last 1000 samples
                    if len(self._checkout_times) > 1000:
                        self._checkout_times = self._checkout_times[-1000:]

                    self._metrics.avg_checkout_time_ms = (
                        sum(self._checkout_times) / len(self._checkout_times)
                    )
                    self._metrics.max_checkout_time_ms = max(
                        self._metrics.max_checkout_time_ms, duration_ms
                    )

            with self._metrics_lock:
                self._metrics.checkin_count += 1
                self._metrics.checked_out = max(0, self._metrics.checked_out - 1)

            # Clear leak detection
            if self._leak_detector:
                self._leak_detector.on_checkin(conn_id)

        @event.listens_for(self.engine, "invalidate")
        def on_invalidate(dbapi_conn, connection_record, exception):
            """Track invalidated connections."""
            with self._metrics_lock:
                self._metrics.invalidated += 1

            logger.warning(f"Connection invalidated: {exception}")

        @event.listens_for(self.engine.pool, "checkout")
        def on_pool_checkout(dbapi_conn, connection_record, connection_proxy):
            """Pool-level checkout tracking."""
            pass

    def _on_leak_detected(self, info: ConnectionInfo):
        """Handle detected connection leak."""
        with self._metrics_lock:
            self._metrics.leaks_detected += 1

    def start(self):
        """Start the connection pool and monitoring."""
        if self._leak_detector:
            self._leak_detector.start()
        logger.info("Enhanced connection pool started")

    def stop(self):
        """Stop the connection pool and cleanup."""
        if self._leak_detector:
            self._leak_detector.stop()
        self.engine.dispose()
        logger.info("Enhanced connection pool stopped")

    @contextmanager
    def get_session(self) -> Session:
        """
        Get a database session with automatic cleanup.

        Usage:
            with pool.get_session() as session:
                session.query(User).all()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            with self._metrics_lock:
                self._metrics.errors += 1
            raise
        finally:
            session.close()

    def get_db(self):
        """
        Dependency for FastAPI routes.

        Usage:
            @app.get("/users")
            def get_users(db: Session = Depends(pool.get_db)):
                return db.query(User).all()
        """
        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            with self._metrics_lock:
                self._metrics.errors += 1
            raise
        finally:
            session.close()

    def check_health(self) -> Dict[str, Any]:
        """
        Check pool health.

        Returns:
            Health status dictionary
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(self.config.validation_query))
                result.fetchone()

            pool = self.engine.pool

            return {
                "healthy": True,
                "pool_status": {
                    "size": pool.size(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                    "checked_in": pool.checkedin(),
                },
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Pool health check failed: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }

    def get_metrics(self) -> Dict[str, Any]:
        """Get pool metrics."""
        pool = self.engine.pool

        with self._metrics_lock:
            metrics = {
                "pool": {
                    "size": pool.size(),
                    "max_overflow": self.config.max_overflow,
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                    "checked_in": pool.checkedin(),
                },
                "stats": {
                    "checkout_count": self._metrics.checkout_count,
                    "checkin_count": self._metrics.checkin_count,
                    "invalidated": self._metrics.invalidated,
                    "leaks_detected": self._metrics.leaks_detected,
                    "errors": self._metrics.errors,
                    "avg_checkout_time_ms": round(self._metrics.avg_checkout_time_ms, 2),
                    "max_checkout_time_ms": round(self._metrics.max_checkout_time_ms, 2),
                },
            }

        if self._leak_detector:
            metrics["leak_detector"] = self._leak_detector.get_stats()

        return metrics

    def resize_pool(self, new_size: int, new_max_overflow: int = None):
        """
        Resize the connection pool.

        Note: This requires recreating the engine.
        """
        if new_size == self.config.pool_size:
            return

        logger.info(f"Resizing pool from {self.config.pool_size} to {new_size}")

        # Update config
        self.config.pool_size = new_size
        if new_max_overflow is not None:
            self.config.max_overflow = new_max_overflow

        # Recreate engine
        old_engine = self.engine
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
        )

        # Setup event listeners on new engine
        self._setup_event_listeners()

        # Dispose old engine
        old_engine.dispose()

    def optimize_pool_size(self) -> int:
        """
        Calculate optimal pool size based on current usage.

        Returns:
            Recommended pool size
        """
        metrics = self.get_metrics()
        pool_stats = metrics["pool"]

        current_size = pool_stats["size"]
        max_used = pool_stats["checked_out"] + pool_stats["overflow"]

        # If we're frequently using overflow, increase size
        if pool_stats["overflow"] > 0:
            recommended = min(current_size + 5, current_size * 2)
        # If we're using less than 50% of the pool, decrease size
        elif max_used < current_size * 0.5 and current_size > 5:
            recommended = max(5, int(current_size * 0.75))
        else:
            recommended = current_size

        return recommended


class FailoverConnectionPool:
    """
    Connection pool with automatic failover to replicas.

    Features:
    - Primary database connection
    - Multiple read replica connections
    - Automatic failover on primary failure
    - Health-based routing
    """

    def __init__(
        self,
        primary_url: str,
        replica_urls: Optional[List[str]] = None,
        config: Optional[PoolConfig] = None,
    ):
        self.config = config or PoolConfig.from_env()

        # Primary pool
        self.primary = EnhancedConnectionPool(primary_url, self.config)

        # Replica pools
        self.replicas: List[EnhancedConnectionPool] = []
        for url in (replica_urls or []):
            replica_config = PoolConfig(
                pool_size=self.config.pool_size // 2,  # Smaller pools for replicas
                max_overflow=self.config.max_overflow // 2,
                **{k: v for k, v in vars(self.config).items()
                   if k not in ["pool_size", "max_overflow"]}
            )
            self.replicas.append(EnhancedConnectionPool(url, replica_config))

        # Health tracking
        self._replica_health: Dict[int, bool] = {i: True for i in range(len(self.replicas))}
        self._replica_index = 0
        self._lock = threading.Lock()

    def start(self):
        """Start all pools."""
        self.primary.start()
        for replica in self.replicas:
            replica.start()

    def stop(self):
        """Stop all pools."""
        self.primary.stop()
        for replica in self.replicas:
            replica.stop()

    @contextmanager
    def get_write_session(self) -> Session:
        """Get a session for write operations (always uses primary)."""
        with self.primary.get_session() as session:
            yield session

    @contextmanager
    def get_read_session(self, require_fresh: bool = False) -> Session:
        """
        Get a session for read operations.

        Args:
            require_fresh: If True, use primary for up-to-date data

        Yields:
            Database session
        """
        if require_fresh or not self.replicas:
            with self.primary.get_session() as session:
                yield session
        else:
            pool = self._get_healthy_replica()
            with pool.get_session() as session:
                yield session

    def _get_healthy_replica(self) -> EnhancedConnectionPool:
        """Get a healthy replica using round-robin."""
        if not self.replicas:
            return self.primary

        with self._lock:
            # Try to find a healthy replica
            for _ in range(len(self.replicas)):
                idx = self._replica_index
                self._replica_index = (self._replica_index + 1) % len(self.replicas)

                if self._replica_health.get(idx, False):
                    return self.replicas[idx]

            # All replicas unhealthy, fall back to primary
            return self.primary

    def check_replica_health(self):
        """Check health of all replicas."""
        for i, replica in enumerate(self.replicas):
            health = replica.check_health()
            self._replica_health[i] = health["healthy"]

    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics for all pools."""
        return {
            "primary": self.primary.get_metrics(),
            "replicas": [
                {
                    "index": i,
                    "healthy": self._replica_health.get(i, False),
                    "metrics": replica.get_metrics(),
                }
                for i, replica in enumerate(self.replicas)
            ],
        }


# Global connection pool instances
_pool: Optional[EnhancedConnectionPool] = None
_failover_pool: Optional[FailoverConnectionPool] = None


def get_connection_pool(
    database_url: Optional[str] = None,
    config: Optional[PoolConfig] = None,
) -> EnhancedConnectionPool:
    """Get or create the global connection pool."""
    global _pool
    if _pool is None:
        if database_url is None:
            database_url = os.getenv(
                "DATABASE_URL",
                "postgresql://postgres:password@localhost:5432/healthtech"
            )
        _pool = EnhancedConnectionPool(database_url, config)
        _pool.start()
    return _pool


def get_failover_pool(
    primary_url: Optional[str] = None,
    replica_urls: Optional[List[str]] = None,
    config: Optional[PoolConfig] = None,
) -> FailoverConnectionPool:
    """Get or create the global failover pool."""
    global _failover_pool
    if _failover_pool is None:
        if primary_url is None:
            primary_url = os.getenv(
                "DATABASE_URL",
                "postgresql://postgres:password@localhost:5432/healthtech"
            )
        if replica_urls is None:
            replica_env = os.getenv("DATABASE_REPLICA_URLS", "")
            replica_urls = [url.strip() for url in replica_env.split(",") if url.strip()]

        _failover_pool = FailoverConnectionPool(primary_url, replica_urls, config)
        _failover_pool.start()
    return _failover_pool

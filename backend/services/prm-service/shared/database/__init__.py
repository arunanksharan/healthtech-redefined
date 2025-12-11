"""
Database Package

Comprehensive database functionality including:
- Connection management and pooling
- ORM models and schema
- Caching layer (Redis)
- Query optimization
- Multi-tenant support
- Index management
- Table partitioning
- Read replica support
- Performance monitoring

EPIC-003: Database & Performance Optimization
"""

# Core connection and session management
from .connection import (
    engine,
    SessionLocal,
    get_db,
    get_db_session,
    init_db,
    drop_db,
    check_db_connection,
    get_db_info,
)

# ORM Models
from .models import (
    Base,
    Tenant,
    Patient,
    PatientIdentifier,
    Practitioner,
    Organization,
    Location,
)

# Caching
from .cache import (
    CacheManager,
    CacheConfig,
    CacheStats,
    CacheSerializer,
    CacheWarmer,
    WarmingTask,
    cache_manager,
    cache_warmer,
    cached,
)

# Query optimization
from .query_optimizer import (
    QueryOptimizer,
    QueryMetrics,
    QueryStats,
    SlowQueryLog,
    NPlusOneDetector,
    ReadWriteSplitter,
    BatchQueryExecutor,
    query_optimizer,
    profiled_query,
)

# Multi-tenancy
from .tenant_context import (
    TenantContext,
    TenantContextManager,
    TenantLimits,
    TenantSettings,
    TenantBranding,
    TenantTier,
    TenantStatus,
    TenantResolver,
    TenantService,
    get_current_tenant,
    set_tenant,
    get_tenant_context,
    set_tenant_context,
    clear_tenant_context,
    setup_tenant_rls,
    setup_session_tenant_hooks,
    tenant_scoped,
    tenant_resolver,
)

# Index management
from .index_manager import (
    IndexManager,
    IndexDefinition,
    IndexStats,
    IndexType,
    IndexRecommendation,
    QueryPlanAnalysis,
    get_index_manager,
)

# Partitioning
from .partitioning import (
    PartitionManager,
    PartitionDefinition,
    PartitionInfo,
    PartitionStrategy,
    PartitionInterval,
    PartitionMaintenanceResult,
    get_partition_manager,
)

# Enhanced connection pooling
from .connection_pool import (
    EnhancedConnectionPool,
    FailoverConnectionPool,
    PoolConfig,
    PoolMetrics,
    ConnectionInfo,
    ConnectionState,
    ConnectionLeakDetector,
    get_connection_pool,
    get_failover_pool,
)

# Monitoring
from .monitoring import (
    DatabaseMonitor,
    Alert,
    AlertSeverity,
    MetricType,
    MetricThresholds,
    PerformanceSnapshot,
    get_database_monitor,
)

# EPIC-004: Enhanced Tenant Service
from .tenant_service import (
    TenantServiceImpl,
    TenantCreate,
    TenantUpdate,
    ApiKeyCreate,
    DataExportRequest,
    UsageStats,
    TenantResponse,
)

# EPIC-004: Rate Limiting
from .rate_limiter import (
    SlidingWindowRateLimiter,
    TokenBucketRateLimiter,
    QuotaManager,
    TenantRateLimiter,
    QuotaType,
    RateLimitWindow,
    RateLimitConfig,
    QuotaConfig,
    RateLimitResult,
    QuotaResult,
)

# EPIC-004: Usage Tracking
from .usage_tracker import (
    UsageTracker,
    UsageMetric,
    UsageEvent,
    UsageSummary,
    BillingMetricsCollector,
    init_usage_tracker,
    shutdown_usage_tracker,
)

# EPIC-004: Audit Service
from .audit_service import (
    AuditService,
    AuditAction,
    AuditCategory,
    AuditEntry,
    audited,
)

# EPIC-004: Data Export/Import
from .data_export import (
    DataExporter,
    DataImporter,
    TenantMigrator,
    ExportConfig,
    ImportConfig,
    ExportFormat,
    ExportStatus,
    ImportStatus,
    ExportResult,
    ImportResult,
)

# EPIC-004: Tenant Monitoring
from .tenant_monitoring import (
    TenantMonitor,
    TenantHealthMetrics,
    SLAMetrics,
    HealthStatus,
    AlertType,
    Alert as TenantAlert,
    AlertSeverity as TenantAlertSeverity,
)

__all__ = [
    # Connection
    "engine",
    "SessionLocal",
    "get_db",
    "get_db_session",
    "init_db",
    "drop_db",
    "check_db_connection",
    "get_db_info",
    # Models
    "Base",
    "Tenant",
    "Patient",
    "PatientIdentifier",
    "Practitioner",
    "Organization",
    "Location",
    # Cache
    "CacheManager",
    "CacheConfig",
    "CacheStats",
    "CacheSerializer",
    "CacheWarmer",
    "WarmingTask",
    "cache_manager",
    "cache_warmer",
    "cached",
    # Query Optimizer
    "QueryOptimizer",
    "QueryMetrics",
    "QueryStats",
    "SlowQueryLog",
    "NPlusOneDetector",
    "ReadWriteSplitter",
    "BatchQueryExecutor",
    "query_optimizer",
    "profiled_query",
    # Tenant
    "TenantContext",
    "TenantContextManager",
    "TenantLimits",
    "TenantSettings",
    "TenantBranding",
    "TenantTier",
    "TenantStatus",
    "TenantResolver",
    "TenantService",
    "get_current_tenant",
    "set_tenant",
    "get_tenant_context",
    "set_tenant_context",
    "clear_tenant_context",
    "setup_tenant_rls",
    "setup_session_tenant_hooks",
    "tenant_scoped",
    "tenant_resolver",
    # Index Manager
    "IndexManager",
    "IndexDefinition",
    "IndexStats",
    "IndexType",
    "IndexRecommendation",
    "QueryPlanAnalysis",
    "get_index_manager",
    # Partitioning
    "PartitionManager",
    "PartitionDefinition",
    "PartitionInfo",
    "PartitionStrategy",
    "PartitionInterval",
    "PartitionMaintenanceResult",
    "get_partition_manager",
    # Connection Pool
    "EnhancedConnectionPool",
    "FailoverConnectionPool",
    "PoolConfig",
    "PoolMetrics",
    "ConnectionInfo",
    "ConnectionState",
    "ConnectionLeakDetector",
    "get_connection_pool",
    "get_failover_pool",
    # Monitoring
    "DatabaseMonitor",
    "Alert",
    "AlertSeverity",
    "MetricType",
    "MetricThresholds",
    "PerformanceSnapshot",
    "get_database_monitor",
    # EPIC-004: Enhanced Tenant Service
    "TenantServiceImpl",
    "TenantCreate",
    "TenantUpdate",
    "ApiKeyCreate",
    "DataExportRequest",
    "UsageStats",
    "TenantResponse",
    # EPIC-004: Rate Limiting
    "SlidingWindowRateLimiter",
    "TokenBucketRateLimiter",
    "QuotaManager",
    "TenantRateLimiter",
    "QuotaType",
    "RateLimitWindow",
    "RateLimitConfig",
    "QuotaConfig",
    "RateLimitResult",
    "QuotaResult",
    # EPIC-004: Usage Tracking
    "UsageTracker",
    "UsageMetric",
    "UsageEvent",
    "UsageSummary",
    "BillingMetricsCollector",
    "init_usage_tracker",
    "shutdown_usage_tracker",
    # EPIC-004: Audit Service
    "AuditService",
    "AuditAction",
    "AuditCategory",
    "AuditEntry",
    "audited",
    # EPIC-004: Data Export/Import
    "DataExporter",
    "DataImporter",
    "TenantMigrator",
    "ExportConfig",
    "ImportConfig",
    "ExportFormat",
    "ExportStatus",
    "ImportStatus",
    "ExportResult",
    "ImportResult",
    # EPIC-004: Tenant Monitoring
    "TenantMonitor",
    "TenantHealthMetrics",
    "SLAMetrics",
    "HealthStatus",
    "AlertType",
    "TenantAlert",
    "TenantAlertSeverity",
]

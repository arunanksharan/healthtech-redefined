"""
Production Readiness Models

SQLAlchemy models for EPIC-024: Production Readiness
Including infrastructure management, monitoring, alerting, deployments,
backup/DR, runbooks, and go-live preparation.
"""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY, JSONB
from sqlalchemy.orm import relationship

from shared.database import Base


# =============================================================================
# Enums
# =============================================================================

class ResourceType(str, Enum):
    """Types of infrastructure resources."""
    COMPUTE = "compute"
    DATABASE = "database"
    CACHE = "cache"
    MESSAGING = "messaging"
    STORAGE = "storage"
    CDN = "cdn"
    LOAD_BALANCER = "load_balancer"
    DNS = "dns"
    WAF = "waf"
    VPN = "vpn"


class ResourceStatus(str, Enum):
    """Infrastructure resource status."""
    PROVISIONING = "provisioning"
    RUNNING = "running"
    UPDATING = "updating"
    DEGRADED = "degraded"
    FAILED = "failed"
    TERMINATED = "terminated"
    MAINTENANCE = "maintenance"


class CloudProvider(str, Enum):
    """Cloud provider options."""
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    ON_PREMISE = "on_premise"


class EnvironmentType(str, Enum):
    """Deployment environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    DR = "dr"


class MetricType(str, Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class MetricCategory(str, Enum):
    """Metric categories."""
    INFRASTRUCTURE = "infrastructure"
    APPLICATION = "application"
    BUSINESS = "business"
    SECURITY = "security"
    COMPLIANCE = "compliance"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    P1_CRITICAL = "p1_critical"
    P2_HIGH = "p2_high"
    P3_MEDIUM = "p3_medium"
    P4_LOW = "p4_low"
    P5_INFO = "p5_info"


class AlertStatus(str, Enum):
    """Alert status."""
    FIRING = "firing"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"
    ESCALATED = "escalated"


class IncidentStatus(str, Enum):
    """Incident status."""
    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    POSTMORTEM = "postmortem"
    CLOSED = "closed"


class DeploymentStatus(str, Enum):
    """Deployment status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


class DeploymentStrategy(str, Enum):
    """Deployment strategy types."""
    ROLLING = "rolling"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    RECREATE = "recreate"


class FeatureFlagStatus(str, Enum):
    """Feature flag status."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    PERCENTAGE_ROLLOUT = "percentage_rollout"
    USER_TARGETING = "user_targeting"


class BackupType(str, Enum):
    """Backup types."""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    SNAPSHOT = "snapshot"
    WAL = "wal"


class BackupStatus(str, Enum):
    """Backup status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    VERIFIED = "verified"
    EXPIRED = "expired"


class DRScenario(str, Enum):
    """Disaster recovery scenarios."""
    DATABASE_FAILURE = "database_failure"
    REGION_OUTAGE = "region_outage"
    SERVICE_FAILURE = "service_failure"
    SECURITY_BREACH = "security_breach"
    DATA_CORRUPTION = "data_corruption"
    NETWORK_FAILURE = "network_failure"


class DrillStatus(str, Enum):
    """DR drill status."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunbookType(str, Enum):
    """Runbook types."""
    DEPLOYMENT = "deployment"
    INCIDENT_RESPONSE = "incident_response"
    MAINTENANCE = "maintenance"
    SCALING = "scaling"
    BACKUP = "backup"
    RECOVERY = "recovery"
    SECURITY = "security"


class ChecklistCategory(str, Enum):
    """Go-live checklist categories."""
    INFRASTRUCTURE = "infrastructure"
    MONITORING = "monitoring"
    SECURITY = "security"
    OPERATIONS = "operations"
    BUSINESS = "business"
    DOCUMENTATION = "documentation"
    TESTING = "testing"


class ChecklistItemStatus(str, Enum):
    """Checklist item status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    NOT_APPLICABLE = "not_applicable"


class HealthCheckType(str, Enum):
    """Health check types."""
    LIVENESS = "liveness"
    READINESS = "readiness"
    STARTUP = "startup"
    DEPENDENCY = "dependency"


class HealthStatus(str, Enum):
    """Health status."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


# =============================================================================
# Infrastructure Models
# =============================================================================

class InfrastructureResource(Base):
    """Infrastructure resource tracking."""
    __tablename__ = "production_infrastructure_resources"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    resource_type = Column(SQLEnum(ResourceType), nullable=False)
    status = Column(SQLEnum(ResourceStatus), default=ResourceStatus.PROVISIONING)

    cloud_provider = Column(SQLEnum(CloudProvider), nullable=False)
    environment = Column(SQLEnum(EnvironmentType), nullable=False)
    region = Column(String(100), nullable=False)
    availability_zone = Column(String(100))

    # Resource identifiers
    resource_id = Column(String(255))  # Cloud provider resource ID
    resource_arn = Column(String(500))  # AWS ARN or equivalent

    # Configuration
    instance_type = Column(String(100))
    cpu_cores = Column(Integer)
    memory_gb = Column(Float)
    storage_gb = Column(Float)

    # Networking
    private_ip = Column(String(50))
    public_ip = Column(String(50))
    dns_name = Column(String(255))

    # Tags and metadata
    tags = Column(JSONB, default=dict)
    metadata = Column(JSONB, default=dict)

    # Cost tracking
    hourly_cost = Column(Float, default=0.0)
    monthly_cost = Column(Float, default=0.0)

    # IaC reference
    terraform_resource = Column(String(255))
    terraform_state_key = Column(String(255))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(PGUUID(as_uuid=True))

    __table_args__ = (
        Index('ix_prod_resource_tenant_env', 'tenant_id', 'environment'),
        Index('ix_prod_resource_type_status', 'resource_type', 'status'),
    )


class AutoScalingConfig(Base):
    """Auto-scaling configuration for resources."""
    __tablename__ = "production_auto_scaling_configs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    resource_id = Column(PGUUID(as_uuid=True), ForeignKey("production_infrastructure_resources.id"))

    name = Column(String(255), nullable=False)
    enabled = Column(Boolean, default=True)

    min_instances = Column(Integer, default=1)
    max_instances = Column(Integer, default=10)
    desired_instances = Column(Integer, default=2)

    # Scaling triggers
    scale_up_cpu_threshold = Column(Float, default=70.0)
    scale_down_cpu_threshold = Column(Float, default=30.0)
    scale_up_memory_threshold = Column(Float, default=80.0)
    scale_down_memory_threshold = Column(Float, default=40.0)

    # Cooldown periods (seconds)
    scale_up_cooldown = Column(Integer, default=300)
    scale_down_cooldown = Column(Integer, default=600)

    # Custom metrics
    custom_metrics = Column(JSONB, default=list)

    # Predictive scaling
    predictive_scaling_enabled = Column(Boolean, default=False)
    predictive_scaling_mode = Column(String(50))  # forecast_only, forecast_and_scale

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NetworkConfig(Base):
    """Network configuration."""
    __tablename__ = "production_network_configs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    environment = Column(SQLEnum(EnvironmentType), nullable=False)

    # VPC configuration
    vpc_id = Column(String(100))
    vpc_cidr = Column(String(20))

    # Subnets
    public_subnets = Column(ARRAY(String), default=list)
    private_subnets = Column(ARRAY(String), default=list)
    database_subnets = Column(ARRAY(String), default=list)

    # Security groups
    security_groups = Column(JSONB, default=list)

    # Load balancer
    load_balancer_arn = Column(String(500))
    load_balancer_dns = Column(String(255))

    # Service mesh
    service_mesh_enabled = Column(Boolean, default=False)
    service_mesh_type = Column(String(50))  # istio, linkerd

    # DNS configuration
    dns_zone_id = Column(String(100))
    domain_name = Column(String(255))

    # WAF and DDoS
    waf_enabled = Column(Boolean, default=False)
    waf_rules = Column(JSONB, default=list)
    ddos_protection_enabled = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# =============================================================================
# Monitoring Models
# =============================================================================

class MetricDefinition(Base):
    """Custom metric definitions."""
    __tablename__ = "production_metric_definitions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text)

    metric_type = Column(SQLEnum(MetricType), nullable=False)
    category = Column(SQLEnum(MetricCategory), nullable=False)

    # Prometheus configuration
    prometheus_query = Column(Text)
    labels = Column(ARRAY(String), default=list)

    # Unit and display
    unit = Column(String(50))  # ms, percent, count, bytes
    display_name = Column(String(255))

    # Thresholds
    warning_threshold = Column(Float)
    critical_threshold = Column(Float)

    # Aggregation
    aggregation_method = Column(String(50))  # avg, sum, max, min, p50, p95, p99
    aggregation_interval = Column(String(20))  # 1m, 5m, 1h

    enabled = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'name', name='uq_metric_tenant_name'),
    )


class Dashboard(Base):
    """Monitoring dashboards."""
    __tablename__ = "production_dashboards"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Dashboard type
    dashboard_type = Column(String(100))  # service, infrastructure, business, slo

    # Grafana configuration
    grafana_uid = Column(String(100))
    grafana_url = Column(String(500))
    grafana_json = Column(JSONB)  # Dashboard JSON definition

    # Panels
    panels = Column(JSONB, default=list)

    # Access control
    is_public = Column(Boolean, default=False)
    allowed_roles = Column(ARRAY(String), default=list)

    # Refresh settings
    auto_refresh_interval = Column(String(20))  # 5s, 1m, 5m
    time_range = Column(String(50))  # last_1h, last_24h, last_7d

    # Ownership
    owner_id = Column(PGUUID(as_uuid=True))

    starred = Column(Boolean, default=False)
    folder = Column(String(100))
    tags = Column(ARRAY(String), default=list)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HealthCheck(Base):
    """Service health check configuration."""
    __tablename__ = "production_health_checks"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    service_name = Column(String(255), nullable=False)
    check_type = Column(SQLEnum(HealthCheckType), nullable=False)

    # Endpoint configuration
    endpoint = Column(String(500), nullable=False)
    method = Column(String(10), default="GET")
    expected_status_code = Column(Integer, default=200)
    expected_response = Column(JSONB)  # Expected JSON response body

    # Timing
    interval_seconds = Column(Integer, default=30)
    timeout_seconds = Column(Integer, default=10)

    # Thresholds
    success_threshold = Column(Integer, default=1)
    failure_threshold = Column(Integer, default=3)

    # Current status
    current_status = Column(SQLEnum(HealthStatus), default=HealthStatus.UNKNOWN)
    last_check_at = Column(DateTime)
    last_success_at = Column(DateTime)
    last_failure_at = Column(DateTime)
    consecutive_failures = Column(Integer, default=0)

    # Dependencies
    dependencies = Column(JSONB, default=list)  # Other services this depends on

    enabled = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_prod_health_service_type', 'service_name', 'check_type'),
    )


class SLODefinition(Base):
    """Service Level Objective definitions."""
    __tablename__ = "production_slo_definitions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text)

    service_name = Column(String(255), nullable=False)

    # SLO targets
    target_percentage = Column(Float, nullable=False)  # e.g., 99.9
    window_days = Column(Integer, default=30)  # Rolling window

    # Error budget
    error_budget_minutes = Column(Float)  # Calculated based on target
    error_budget_remaining = Column(Float)
    error_budget_consumed_percent = Column(Float, default=0.0)

    # SLI configuration
    sli_query = Column(Text)  # Prometheus query for SLI
    sli_type = Column(String(50))  # availability, latency, throughput

    # Burn rate alerting
    burn_rate_alert_enabled = Column(Boolean, default=True)
    fast_burn_threshold = Column(Float, default=14.4)  # 2% budget in 1 hour
    slow_burn_threshold = Column(Float, default=1.0)

    # Current status
    current_sli_value = Column(Float)
    slo_met = Column(Boolean)
    last_calculated_at = Column(DateTime)

    enabled = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tenant_id', 'name', name='uq_slo_tenant_name'),
    )


class SLIRecord(Base):
    """Historical SLI measurements."""
    __tablename__ = "production_sli_records"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    slo_id = Column(PGUUID(as_uuid=True), ForeignKey("production_slo_definitions.id"))

    timestamp = Column(DateTime, nullable=False)

    good_events = Column(Integer, default=0)
    total_events = Column(Integer, default=0)
    sli_value = Column(Float)  # good_events / total_events * 100

    # Context
    window_start = Column(DateTime)
    window_end = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('ix_prod_sli_slo_timestamp', 'slo_id', 'timestamp'),
    )


# =============================================================================
# Alerting Models
# =============================================================================

class AlertRule(Base):
    """Alert rule definitions."""
    __tablename__ = "production_alert_rules"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text)

    severity = Column(SQLEnum(AlertSeverity), nullable=False)

    # Alert condition
    prometheus_query = Column(Text, nullable=False)
    threshold_operator = Column(String(10))  # >, <, >=, <=, ==, !=
    threshold_value = Column(Float)

    # Timing
    for_duration = Column(String(20))  # How long condition must be true: 5m, 10m
    evaluation_interval = Column(String(20), default="1m")

    # Notification
    notification_channels = Column(ARRAY(String), default=list)  # slack, pagerduty, email

    # Runbook
    runbook_url = Column(String(500))
    runbook_id = Column(PGUUID(as_uuid=True), ForeignKey("production_runbooks.id"))

    # Labels and annotations
    labels = Column(JSONB, default=dict)
    annotations = Column(JSONB, default=dict)

    # Grouping
    group_by = Column(ARRAY(String), default=list)
    inhibit_rules = Column(JSONB, default=list)

    # Status
    enabled = Column(Boolean, default=True)
    silenced_until = Column(DateTime)

    # Statistics
    last_triggered_at = Column(DateTime)
    trigger_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(PGUUID(as_uuid=True))


class AlertIncident(Base):
    """Alert incidents."""
    __tablename__ = "production_alert_incidents"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    alert_rule_id = Column(PGUUID(as_uuid=True), ForeignKey("production_alert_rules.id"))

    incident_number = Column(String(50), unique=True)  # INC-001
    title = Column(String(500), nullable=False)
    description = Column(Text)

    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    status = Column(SQLEnum(IncidentStatus), default=IncidentStatus.TRIGGERED)

    # Timeline
    triggered_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    closed_at = Column(DateTime)

    # Assignment
    assigned_to = Column(PGUUID(as_uuid=True))
    escalation_level = Column(Integer, default=0)

    # Impact
    affected_services = Column(ARRAY(String), default=list)
    affected_users = Column(Integer, default=0)
    customer_impact = Column(Text)

    # Communication
    status_page_updated = Column(Boolean, default=False)
    communication_sent = Column(Boolean, default=False)

    # Resolution
    root_cause = Column(Text)
    resolution_summary = Column(Text)
    postmortem_url = Column(String(500))

    # Metrics
    time_to_acknowledge_seconds = Column(Integer)
    time_to_resolve_seconds = Column(Integer)

    # External references
    pagerduty_incident_id = Column(String(100))
    jira_ticket_id = Column(String(50))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_prod_incident_status_severity', 'status', 'severity'),
        Index('ix_prod_incident_tenant_triggered', 'tenant_id', 'triggered_at'),
    )


class OnCallSchedule(Base):
    """On-call rotation schedule."""
    __tablename__ = "production_on_call_schedules"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Team
    team_name = Column(String(255), nullable=False)
    members = Column(ARRAY(PGUUID(as_uuid=True)), default=list)

    # Rotation settings
    rotation_type = Column(String(50))  # daily, weekly, custom
    rotation_start_day = Column(Integer)  # 0=Monday, 6=Sunday
    rotation_start_hour = Column(Integer, default=9)
    handoff_time = Column(String(10), default="09:00")
    timezone = Column(String(50), default="UTC")

    # Current on-call
    current_primary = Column(PGUUID(as_uuid=True))
    current_secondary = Column(PGUUID(as_uuid=True))
    next_rotation_at = Column(DateTime)

    # External integration
    pagerduty_schedule_id = Column(String(100))
    opsgenie_schedule_id = Column(String(100))

    enabled = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EscalationPolicy(Base):
    """Alert escalation policies."""
    __tablename__ = "production_escalation_policies"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Escalation levels
    # Each level: {level: 1, delay_minutes: 5, targets: [schedule_id, user_id]}
    escalation_levels = Column(JSONB, default=list)

    # Settings
    repeat_enabled = Column(Boolean, default=False)
    repeat_limit = Column(Integer, default=3)

    # Acknowledgment requirements
    require_acknowledgment = Column(Boolean, default=True)
    acknowledgment_timeout_minutes = Column(Integer, default=30)

    # External integration
    pagerduty_policy_id = Column(String(100))
    opsgenie_policy_id = Column(String(100))

    enabled = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# =============================================================================
# Deployment Models
# =============================================================================

class Deployment(Base):
    """Deployment records."""
    __tablename__ = "production_deployments"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    deployment_number = Column(String(50))  # DEPLOY-001
    service_name = Column(String(255), nullable=False)

    # Version info
    version = Column(String(100), nullable=False)
    previous_version = Column(String(100))
    commit_sha = Column(String(40))

    # Environment
    environment = Column(SQLEnum(EnvironmentType), nullable=False)

    # Strategy
    strategy = Column(SQLEnum(DeploymentStrategy), default=DeploymentStrategy.ROLLING)
    status = Column(SQLEnum(DeploymentStatus), default=DeploymentStatus.PENDING)

    # Configuration
    replicas = Column(Integer, default=2)
    config_changes = Column(JSONB, default=dict)  # Environment variable changes

    # Timeline
    scheduled_at = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Health
    health_check_passed = Column(Boolean)
    health_check_attempts = Column(Integer, default=0)

    # Rollback info
    rolled_back = Column(Boolean, default=False)
    rollback_reason = Column(Text)
    rollback_deployment_id = Column(PGUUID(as_uuid=True))

    # Approval
    requires_approval = Column(Boolean, default=False)
    approved_by = Column(PGUUID(as_uuid=True))
    approved_at = Column(DateTime)

    # Artifacts
    docker_image = Column(String(500))
    helm_chart_version = Column(String(50))

    # Notes
    release_notes = Column(Text)
    deployment_notes = Column(Text)

    # Metrics
    duration_seconds = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(PGUUID(as_uuid=True))

    __table_args__ = (
        Index('ix_prod_deploy_service_env', 'service_name', 'environment'),
        Index('ix_prod_deploy_status_started', 'status', 'started_at'),
    )


class EnvironmentPromotion(Base):
    """Environment promotion records."""
    __tablename__ = "production_environment_promotions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    service_name = Column(String(255), nullable=False)
    version = Column(String(100), nullable=False)

    source_environment = Column(SQLEnum(EnvironmentType), nullable=False)
    target_environment = Column(SQLEnum(EnvironmentType), nullable=False)

    # Status
    status = Column(SQLEnum(DeploymentStatus), default=DeploymentStatus.PENDING)

    # Approval workflow
    approval_required = Column(Boolean, default=True)
    approved_by = Column(PGUUID(as_uuid=True))
    approved_at = Column(DateTime)
    rejection_reason = Column(Text)

    # Pre-promotion checks
    tests_passed = Column(Boolean)
    security_scan_passed = Column(Boolean)
    pre_checks_result = Column(JSONB)

    # Deployment reference
    deployment_id = Column(PGUUID(as_uuid=True), ForeignKey("production_deployments.id"))

    # Timeline
    requested_at = Column(DateTime, default=datetime.utcnow)
    promoted_at = Column(DateTime)

    created_by = Column(PGUUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FeatureFlag(Base):
    """Feature flag management."""
    __tablename__ = "production_feature_flags"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    key = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    status = Column(SQLEnum(FeatureFlagStatus), default=FeatureFlagStatus.DISABLED)

    # Targeting
    environment = Column(SQLEnum(EnvironmentType))
    percentage_rollout = Column(Float, default=0.0)  # 0-100
    targeted_users = Column(ARRAY(String), default=list)
    targeted_tenants = Column(ARRAY(PGUUID(as_uuid=True)), default=list)

    # Variants (for A/B testing)
    variants = Column(JSONB, default=list)
    default_variant = Column(String(100))

    # Rules
    rules = Column(JSONB, default=list)  # Conditional rules

    # Stale flag detection
    last_evaluated_at = Column(DateTime)
    evaluation_count = Column(Integer, default=0)

    # Ownership
    owner_id = Column(PGUUID(as_uuid=True))
    owner_team = Column(String(255))

    # External integration
    launchdarkly_key = Column(String(255))
    unleash_name = Column(String(255))

    # Lifecycle
    expires_at = Column(DateTime)
    archived = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(PGUUID(as_uuid=True))

    __table_args__ = (
        UniqueConstraint('tenant_id', 'key', name='uq_feature_flag_tenant_key'),
    )


class DatabaseMigration(Base):
    """Database migration tracking."""
    __tablename__ = "production_database_migrations"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    migration_id = Column(String(255), nullable=False)  # Alembic revision
    migration_name = Column(String(500))

    database_name = Column(String(255), nullable=False)
    environment = Column(SQLEnum(EnvironmentType), nullable=False)

    # Status
    status = Column(SQLEnum(DeploymentStatus), default=DeploymentStatus.PENDING)

    # Execution
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)

    # Rollback
    rollback_available = Column(Boolean, default=True)
    rolled_back = Column(Boolean, default=False)
    rollback_at = Column(DateTime)

    # Error tracking
    error_message = Column(Text)
    error_details = Column(JSONB)

    # SQL
    up_sql = Column(Text)
    down_sql = Column(Text)

    # Verification
    pre_migration_checksum = Column(String(64))
    post_migration_checksum = Column(String(64))

    created_at = Column(DateTime, default=datetime.utcnow)
    executed_by = Column(PGUUID(as_uuid=True))


# =============================================================================
# Backup & DR Models
# =============================================================================

class Backup(Base):
    """Backup records."""
    __tablename__ = "production_backups"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    backup_id = Column(String(100), unique=True)  # BKP-20241125-001

    backup_type = Column(SQLEnum(BackupType), nullable=False)
    status = Column(SQLEnum(BackupStatus), default=BackupStatus.PENDING)

    # Source
    source_database = Column(String(255), nullable=False)
    source_region = Column(String(100))
    source_environment = Column(SQLEnum(EnvironmentType), nullable=False)

    # Storage
    storage_location = Column(String(500))  # S3 path, etc.
    storage_region = Column(String(100))
    cross_region_copy = Column(Boolean, default=False)
    cross_region_location = Column(String(500))

    # Size and timing
    size_bytes = Column(Float)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)

    # Encryption
    encrypted = Column(Boolean, default=True)
    encryption_key_id = Column(String(255))

    # Retention
    retention_days = Column(Integer, default=30)
    expires_at = Column(DateTime)

    # Verification
    verified = Column(Boolean, default=False)
    verified_at = Column(DateTime)
    verification_result = Column(JSONB)

    # Point-in-time recovery
    pitr_enabled = Column(Boolean, default=False)
    earliest_restore_time = Column(DateTime)
    latest_restore_time = Column(DateTime)

    # Metadata
    metadata = Column(JSONB, default=dict)
    tags = Column(JSONB, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(PGUUID(as_uuid=True))

    __table_args__ = (
        Index('ix_prod_backup_status_env', 'status', 'source_environment'),
        Index('ix_prod_backup_tenant_created', 'tenant_id', 'created_at'),
    )


class RestoreOperation(Base):
    """Database restore operations."""
    __tablename__ = "production_restore_operations"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    backup_id = Column(PGUUID(as_uuid=True), ForeignKey("production_backups.id"))

    restore_id = Column(String(100), unique=True)  # RST-20241125-001

    status = Column(SQLEnum(BackupStatus), default=BackupStatus.PENDING)

    # Target
    target_database = Column(String(255), nullable=False)
    target_environment = Column(SQLEnum(EnvironmentType), nullable=False)

    # Point-in-time
    restore_to_point_in_time = Column(DateTime)

    # Timeline
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)

    # Verification
    data_verification_passed = Column(Boolean)
    verification_details = Column(JSONB)

    # Error tracking
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    initiated_by = Column(PGUUID(as_uuid=True))


class DisasterRecoveryPlan(Base):
    """Disaster recovery plan definitions."""
    __tablename__ = "production_dr_plans"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text)

    scenario = Column(SQLEnum(DRScenario), nullable=False)

    # Targets
    rto_hours = Column(Float, nullable=False)  # Recovery Time Objective
    rpo_hours = Column(Float, nullable=False)  # Recovery Point Objective

    # Steps
    # Each step: {order: 1, name: "...", description: "...", owner: "...", estimated_minutes: 30}
    recovery_steps = Column(JSONB, default=list)

    # Communication
    communication_plan = Column(JSONB)  # Who to notify at each stage
    escalation_contacts = Column(JSONB, default=list)

    # Resources
    primary_region = Column(String(100))
    dr_region = Column(String(100))
    affected_services = Column(ARRAY(String), default=list)

    # Testing
    last_tested_at = Column(DateTime)
    last_test_result = Column(String(50))
    next_test_date = Column(DateTime)
    test_frequency_days = Column(Integer, default=90)

    # Status
    is_active = Column(Boolean, default=True)
    version = Column(Integer, default=1)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(PGUUID(as_uuid=True))


class DRDrill(Base):
    """Disaster recovery drill records."""
    __tablename__ = "production_dr_drills"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    dr_plan_id = Column(PGUUID(as_uuid=True), ForeignKey("production_dr_plans.id"))

    drill_id = Column(String(100), unique=True)  # DRILL-20241125-001

    status = Column(SQLEnum(DrillStatus), default=DrillStatus.SCHEDULED)

    # Schedule
    scheduled_at = Column(DateTime, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Participants
    participants = Column(ARRAY(PGUUID(as_uuid=True)), default=list)
    coordinator = Column(PGUUID(as_uuid=True))

    # Execution
    steps_completed = Column(JSONB, default=list)
    issues_encountered = Column(JSONB, default=list)

    # Results
    rto_achieved_minutes = Column(Float)
    rpo_achieved_minutes = Column(Float)
    rto_target_met = Column(Boolean)
    rpo_target_met = Column(Boolean)

    # Assessment
    success = Column(Boolean)
    lessons_learned = Column(Text)
    action_items = Column(JSONB, default=list)

    # Documentation
    drill_report_url = Column(String(500))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# =============================================================================
# Runbook Models
# =============================================================================

class Runbook(Base):
    """Operational runbooks."""
    __tablename__ = "production_runbooks"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    title = Column(String(500), nullable=False)
    description = Column(Text)

    runbook_type = Column(SQLEnum(RunbookType), nullable=False)

    # Content
    # Steps: [{order: 1, title: "...", content: "...", expected_outcome: "...", commands: [...]}]
    steps = Column(JSONB, default=list)

    # Prerequisites
    prerequisites = Column(JSONB, default=list)
    required_access = Column(ARRAY(String), default=list)

    # Associated alerts
    associated_alerts = Column(ARRAY(PGUUID(as_uuid=True)), default=list)

    # Services
    affected_services = Column(ARRAY(String), default=list)

    # Automation
    automated_steps = Column(JSONB, default=list)  # Steps that can be automated
    automation_script_url = Column(String(500))

    # Metadata
    estimated_duration_minutes = Column(Integer)
    difficulty_level = Column(String(20))  # easy, medium, hard

    # Version control
    version = Column(Integer, default=1)
    last_reviewed_at = Column(DateTime)
    next_review_date = Column(DateTime)

    # Ownership
    owner_id = Column(PGUUID(as_uuid=True))
    owner_team = Column(String(255))

    # Usage tracking
    times_used = Column(Integer, default=0)
    last_used_at = Column(DateTime)

    tags = Column(ARRAY(String), default=list)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(PGUUID(as_uuid=True))


class IncidentPlaybook(Base):
    """Incident-specific playbooks."""
    __tablename__ = "production_incident_playbooks"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    title = Column(String(500), nullable=False)
    description = Column(Text)

    severity = Column(SQLEnum(AlertSeverity), nullable=False)

    # Symptoms
    symptoms = Column(JSONB, default=list)  # What to look for

    # Diagnosis steps
    diagnosis_steps = Column(JSONB, default=list)

    # Mitigation
    immediate_actions = Column(JSONB, default=list)
    long_term_fixes = Column(JSONB, default=list)

    # Communication
    communication_template = Column(Text)
    stakeholders_to_notify = Column(JSONB, default=list)

    # Related
    related_runbooks = Column(ARRAY(PGUUID(as_uuid=True)), default=list)
    related_alerts = Column(ARRAY(PGUUID(as_uuid=True)), default=list)

    # History
    times_used = Column(Integer, default=0)
    avg_resolution_minutes = Column(Float)

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(PGUUID(as_uuid=True))


# =============================================================================
# Go-Live Models
# =============================================================================

class GoLiveChecklist(Base):
    """Go-live checklist."""
    __tablename__ = "production_go_live_checklists"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Target
    target_go_live_date = Column(DateTime)
    environment = Column(SQLEnum(EnvironmentType), default=EnvironmentType.PRODUCTION)

    # Progress
    total_items = Column(Integer, default=0)
    completed_items = Column(Integer, default=0)
    blocked_items = Column(Integer, default=0)
    completion_percentage = Column(Float, default=0.0)

    # Status
    is_ready = Column(Boolean, default=False)
    blockers = Column(JSONB, default=list)

    # Sign-offs required
    required_approvers = Column(ARRAY(PGUUID(as_uuid=True)), default=list)
    approvals_received = Column(JSONB, default=list)

    # Timeline
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    actual_go_live_at = Column(DateTime)

    # Documentation
    release_notes_url = Column(String(500))
    rollback_plan_url = Column(String(500))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(PGUUID(as_uuid=True))


class GoLiveChecklistItem(Base):
    """Individual go-live checklist items."""
    __tablename__ = "production_go_live_checklist_items"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    checklist_id = Column(PGUUID(as_uuid=True), ForeignKey("production_go_live_checklists.id"))

    title = Column(String(500), nullable=False)
    description = Column(Text)

    category = Column(SQLEnum(ChecklistCategory), nullable=False)
    status = Column(SQLEnum(ChecklistItemStatus), default=ChecklistItemStatus.PENDING)

    # Priority
    is_critical = Column(Boolean, default=False)
    is_blocker = Column(Boolean, default=False)

    # Assignment
    assigned_to = Column(PGUUID(as_uuid=True))
    owner_team = Column(String(255))

    # Verification
    verification_method = Column(Text)  # How to verify this item
    evidence_url = Column(String(500))  # Link to evidence

    # Dependencies
    depends_on = Column(ARRAY(PGUUID(as_uuid=True)), default=list)

    # Timeline
    due_date = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Notes
    notes = Column(Text)
    blocker_reason = Column(Text)

    # Order
    display_order = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_prod_checklist_item_category', 'checklist_id', 'category'),
    )


class StatusPageComponent(Base):
    """Status page components."""
    __tablename__ = "production_status_page_components"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Status
    status = Column(SQLEnum(HealthStatus), default=HealthStatus.HEALTHY)

    # Grouping
    group_name = Column(String(255))
    display_order = Column(Integer, default=0)

    # Health check reference
    health_check_id = Column(PGUUID(as_uuid=True), ForeignKey("production_health_checks.id"))

    # Display settings
    show_on_public_page = Column(Boolean, default=True)
    show_uptime = Column(Boolean, default=True)

    # External integration
    statuspage_component_id = Column(String(100))  # Atlassian Statuspage

    # Metrics
    uptime_percentage = Column(Float)
    last_incident_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StatusPageIncident(Base):
    """Status page incident updates."""
    __tablename__ = "production_status_page_incidents"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    alert_incident_id = Column(PGUUID(as_uuid=True), ForeignKey("production_alert_incidents.id"))

    title = Column(String(500), nullable=False)
    status = Column(String(50))  # investigating, identified, monitoring, resolved

    # Impact
    impact = Column(String(50))  # none, minor, major, critical
    affected_components = Column(ARRAY(PGUUID(as_uuid=True)), default=list)

    # Updates
    # Each: {timestamp: "...", status: "...", message: "..."}
    updates = Column(JSONB, default=list)

    # Timeline
    started_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)

    # External
    statuspage_incident_id = Column(String(100))

    # Visibility
    is_public = Column(Boolean, default=True)
    scheduled_maintenance = Column(Boolean, default=False)
    scheduled_start = Column(DateTime)
    scheduled_end = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

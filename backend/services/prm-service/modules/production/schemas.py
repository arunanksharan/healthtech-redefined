"""
Production Readiness Schemas

Pydantic schemas for EPIC-024: Production Readiness API request/response validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field

from .models import (
    ResourceType, ResourceStatus, CloudProvider, EnvironmentType,
    MetricType, MetricCategory, AlertSeverity, AlertStatus, IncidentStatus,
    DeploymentStatus, DeploymentStrategy, FeatureFlagStatus,
    BackupType, BackupStatus, DRScenario, DrillStatus,
    RunbookType, ChecklistCategory, ChecklistItemStatus,
    HealthCheckType, HealthStatus
)


# =============================================================================
# Infrastructure Schemas
# =============================================================================

class InfrastructureResourceCreate(BaseModel):
    """Create infrastructure resource."""
    name: str
    resource_type: ResourceType
    cloud_provider: CloudProvider
    environment: EnvironmentType
    region: str
    availability_zone: Optional[str] = None
    resource_id: Optional[str] = None
    resource_arn: Optional[str] = None
    instance_type: Optional[str] = None
    cpu_cores: Optional[int] = None
    memory_gb: Optional[float] = None
    storage_gb: Optional[float] = None
    private_ip: Optional[str] = None
    public_ip: Optional[str] = None
    dns_name: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    hourly_cost: Optional[float] = 0.0
    terraform_resource: Optional[str] = None
    terraform_state_key: Optional[str] = None


class InfrastructureResourceResponse(BaseModel):
    """Infrastructure resource response."""
    id: UUID
    tenant_id: UUID
    name: str
    resource_type: ResourceType
    status: ResourceStatus
    cloud_provider: CloudProvider
    environment: EnvironmentType
    region: str
    availability_zone: Optional[str]
    resource_id: Optional[str]
    resource_arn: Optional[str]
    instance_type: Optional[str]
    cpu_cores: Optional[int]
    memory_gb: Optional[float]
    storage_gb: Optional[float]
    private_ip: Optional[str]
    public_ip: Optional[str]
    dns_name: Optional[str]
    tags: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    hourly_cost: float
    monthly_cost: float
    terraform_resource: Optional[str]
    terraform_state_key: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AutoScalingConfigCreate(BaseModel):
    """Create auto-scaling configuration."""
    resource_id: Optional[UUID] = None
    name: str
    enabled: bool = True
    min_instances: int = 1
    max_instances: int = 10
    desired_instances: int = 2
    scale_up_cpu_threshold: float = 70.0
    scale_down_cpu_threshold: float = 30.0
    scale_up_memory_threshold: float = 80.0
    scale_down_memory_threshold: float = 40.0
    scale_up_cooldown: int = 300
    scale_down_cooldown: int = 600
    custom_metrics: Optional[List[Dict[str, Any]]] = None
    predictive_scaling_enabled: bool = False
    predictive_scaling_mode: Optional[str] = None


class AutoScalingConfigResponse(BaseModel):
    """Auto-scaling configuration response."""
    id: UUID
    tenant_id: UUID
    resource_id: Optional[UUID]
    name: str
    enabled: bool
    min_instances: int
    max_instances: int
    desired_instances: int
    scale_up_cpu_threshold: float
    scale_down_cpu_threshold: float
    scale_up_memory_threshold: float
    scale_down_memory_threshold: float
    scale_up_cooldown: int
    scale_down_cooldown: int
    custom_metrics: Optional[List[Dict[str, Any]]]
    predictive_scaling_enabled: bool
    predictive_scaling_mode: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NetworkConfigCreate(BaseModel):
    """Create network configuration."""
    name: str
    environment: EnvironmentType
    vpc_id: Optional[str] = None
    vpc_cidr: Optional[str] = None
    public_subnets: Optional[List[str]] = None
    private_subnets: Optional[List[str]] = None
    database_subnets: Optional[List[str]] = None
    security_groups: Optional[List[Dict[str, Any]]] = None
    load_balancer_arn: Optional[str] = None
    load_balancer_dns: Optional[str] = None
    service_mesh_enabled: bool = False
    service_mesh_type: Optional[str] = None
    dns_zone_id: Optional[str] = None
    domain_name: Optional[str] = None
    waf_enabled: bool = False
    waf_rules: Optional[List[Dict[str, Any]]] = None
    ddos_protection_enabled: bool = False


class NetworkConfigResponse(BaseModel):
    """Network configuration response."""
    id: UUID
    tenant_id: UUID
    name: str
    environment: EnvironmentType
    vpc_id: Optional[str]
    vpc_cidr: Optional[str]
    public_subnets: Optional[List[str]]
    private_subnets: Optional[List[str]]
    database_subnets: Optional[List[str]]
    security_groups: Optional[List[Dict[str, Any]]]
    load_balancer_arn: Optional[str]
    load_balancer_dns: Optional[str]
    service_mesh_enabled: bool
    service_mesh_type: Optional[str]
    dns_zone_id: Optional[str]
    domain_name: Optional[str]
    waf_enabled: bool
    waf_rules: Optional[List[Dict[str, Any]]]
    ddos_protection_enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Monitoring Schemas
# =============================================================================

class MetricDefinitionCreate(BaseModel):
    """Create metric definition."""
    name: str
    description: Optional[str] = None
    metric_type: MetricType
    category: MetricCategory
    prometheus_query: Optional[str] = None
    labels: Optional[List[str]] = None
    unit: Optional[str] = None
    display_name: Optional[str] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    aggregation_method: Optional[str] = None
    aggregation_interval: Optional[str] = None
    enabled: bool = True


class MetricDefinitionResponse(BaseModel):
    """Metric definition response."""
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    metric_type: MetricType
    category: MetricCategory
    prometheus_query: Optional[str]
    labels: Optional[List[str]]
    unit: Optional[str]
    display_name: Optional[str]
    warning_threshold: Optional[float]
    critical_threshold: Optional[float]
    aggregation_method: Optional[str]
    aggregation_interval: Optional[str]
    enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DashboardCreate(BaseModel):
    """Create dashboard."""
    name: str
    description: Optional[str] = None
    dashboard_type: Optional[str] = None
    grafana_uid: Optional[str] = None
    grafana_url: Optional[str] = None
    grafana_json: Optional[Dict[str, Any]] = None
    panels: Optional[List[Dict[str, Any]]] = None
    is_public: bool = False
    allowed_roles: Optional[List[str]] = None
    auto_refresh_interval: Optional[str] = None
    time_range: Optional[str] = None
    folder: Optional[str] = None
    tags: Optional[List[str]] = None


class DashboardResponse(BaseModel):
    """Dashboard response."""
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    dashboard_type: Optional[str]
    grafana_uid: Optional[str]
    grafana_url: Optional[str]
    grafana_json: Optional[Dict[str, Any]]
    panels: Optional[List[Dict[str, Any]]]
    is_public: bool
    allowed_roles: Optional[List[str]]
    auto_refresh_interval: Optional[str]
    time_range: Optional[str]
    owner_id: Optional[UUID]
    starred: bool
    folder: Optional[str]
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HealthCheckCreate(BaseModel):
    """Create health check."""
    service_name: str
    check_type: HealthCheckType
    endpoint: str
    method: str = "GET"
    expected_status_code: int = 200
    expected_response: Optional[Dict[str, Any]] = None
    interval_seconds: int = 30
    timeout_seconds: int = 10
    success_threshold: int = 1
    failure_threshold: int = 3
    dependencies: Optional[List[Dict[str, Any]]] = None
    enabled: bool = True


class HealthCheckResponse(BaseModel):
    """Health check response."""
    id: UUID
    tenant_id: UUID
    service_name: str
    check_type: HealthCheckType
    endpoint: str
    method: str
    expected_status_code: int
    expected_response: Optional[Dict[str, Any]]
    interval_seconds: int
    timeout_seconds: int
    success_threshold: int
    failure_threshold: int
    current_status: HealthStatus
    last_check_at: Optional[datetime]
    last_success_at: Optional[datetime]
    last_failure_at: Optional[datetime]
    consecutive_failures: int
    dependencies: Optional[List[Dict[str, Any]]]
    enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SLODefinitionCreate(BaseModel):
    """Create SLO definition."""
    name: str
    description: Optional[str] = None
    service_name: str
    target_percentage: float
    window_days: int = 30
    sli_query: Optional[str] = None
    sli_type: Optional[str] = None
    burn_rate_alert_enabled: bool = True
    fast_burn_threshold: float = 14.4
    slow_burn_threshold: float = 1.0
    enabled: bool = True


class SLODefinitionResponse(BaseModel):
    """SLO definition response."""
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    service_name: str
    target_percentage: float
    window_days: int
    error_budget_minutes: Optional[float]
    error_budget_remaining: Optional[float]
    error_budget_consumed_percent: float
    sli_query: Optional[str]
    sli_type: Optional[str]
    burn_rate_alert_enabled: bool
    fast_burn_threshold: float
    slow_burn_threshold: float
    current_sli_value: Optional[float]
    slo_met: Optional[bool]
    last_calculated_at: Optional[datetime]
    enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SLIRecordCreate(BaseModel):
    """Create SLI record."""
    slo_id: UUID
    timestamp: datetime
    good_events: int
    total_events: int
    window_start: Optional[datetime] = None
    window_end: Optional[datetime] = None


class SLIRecordResponse(BaseModel):
    """SLI record response."""
    id: UUID
    tenant_id: UUID
    slo_id: UUID
    timestamp: datetime
    good_events: int
    total_events: int
    sli_value: Optional[float]
    window_start: Optional[datetime]
    window_end: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Alerting Schemas
# =============================================================================

class AlertRuleCreate(BaseModel):
    """Create alert rule."""
    name: str
    description: Optional[str] = None
    severity: AlertSeverity
    prometheus_query: str
    threshold_operator: Optional[str] = None
    threshold_value: Optional[float] = None
    for_duration: Optional[str] = None
    evaluation_interval: str = "1m"
    notification_channels: Optional[List[str]] = None
    runbook_url: Optional[str] = None
    runbook_id: Optional[UUID] = None
    labels: Optional[Dict[str, Any]] = None
    annotations: Optional[Dict[str, Any]] = None
    group_by: Optional[List[str]] = None
    inhibit_rules: Optional[List[Dict[str, Any]]] = None
    enabled: bool = True


class AlertRuleResponse(BaseModel):
    """Alert rule response."""
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    severity: AlertSeverity
    prometheus_query: str
    threshold_operator: Optional[str]
    threshold_value: Optional[float]
    for_duration: Optional[str]
    evaluation_interval: str
    notification_channels: Optional[List[str]]
    runbook_url: Optional[str]
    runbook_id: Optional[UUID]
    labels: Optional[Dict[str, Any]]
    annotations: Optional[Dict[str, Any]]
    group_by: Optional[List[str]]
    inhibit_rules: Optional[List[Dict[str, Any]]]
    enabled: bool
    silenced_until: Optional[datetime]
    last_triggered_at: Optional[datetime]
    trigger_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertIncidentCreate(BaseModel):
    """Create alert incident."""
    alert_rule_id: Optional[UUID] = None
    title: str
    description: Optional[str] = None
    severity: AlertSeverity
    affected_services: Optional[List[str]] = None
    affected_users: int = 0
    customer_impact: Optional[str] = None


class AlertIncidentResponse(BaseModel):
    """Alert incident response."""
    id: UUID
    tenant_id: UUID
    alert_rule_id: Optional[UUID]
    incident_number: Optional[str]
    title: str
    description: Optional[str]
    severity: AlertSeverity
    status: IncidentStatus
    triggered_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    assigned_to: Optional[UUID]
    escalation_level: int
    affected_services: Optional[List[str]]
    affected_users: int
    customer_impact: Optional[str]
    status_page_updated: bool
    communication_sent: bool
    root_cause: Optional[str]
    resolution_summary: Optional[str]
    postmortem_url: Optional[str]
    time_to_acknowledge_seconds: Optional[int]
    time_to_resolve_seconds: Optional[int]
    pagerduty_incident_id: Optional[str]
    jira_ticket_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertIncidentUpdate(BaseModel):
    """Update alert incident."""
    status: Optional[IncidentStatus] = None
    assigned_to: Optional[UUID] = None
    root_cause: Optional[str] = None
    resolution_summary: Optional[str] = None
    postmortem_url: Optional[str] = None


class OnCallScheduleCreate(BaseModel):
    """Create on-call schedule."""
    name: str
    description: Optional[str] = None
    team_name: str
    members: Optional[List[UUID]] = None
    rotation_type: Optional[str] = None
    rotation_start_day: Optional[int] = None
    rotation_start_hour: int = 9
    handoff_time: str = "09:00"
    timezone: str = "UTC"
    pagerduty_schedule_id: Optional[str] = None
    opsgenie_schedule_id: Optional[str] = None
    enabled: bool = True


class OnCallScheduleResponse(BaseModel):
    """On-call schedule response."""
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    team_name: str
    members: Optional[List[UUID]]
    rotation_type: Optional[str]
    rotation_start_day: Optional[int]
    rotation_start_hour: int
    handoff_time: str
    timezone: str
    current_primary: Optional[UUID]
    current_secondary: Optional[UUID]
    next_rotation_at: Optional[datetime]
    pagerduty_schedule_id: Optional[str]
    opsgenie_schedule_id: Optional[str]
    enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EscalationPolicyCreate(BaseModel):
    """Create escalation policy."""
    name: str
    description: Optional[str] = None
    escalation_levels: List[Dict[str, Any]]
    repeat_enabled: bool = False
    repeat_limit: int = 3
    require_acknowledgment: bool = True
    acknowledgment_timeout_minutes: int = 30
    pagerduty_policy_id: Optional[str] = None
    opsgenie_policy_id: Optional[str] = None
    enabled: bool = True


class EscalationPolicyResponse(BaseModel):
    """Escalation policy response."""
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    escalation_levels: List[Dict[str, Any]]
    repeat_enabled: bool
    repeat_limit: int
    require_acknowledgment: bool
    acknowledgment_timeout_minutes: int
    pagerduty_policy_id: Optional[str]
    opsgenie_policy_id: Optional[str]
    enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Deployment Schemas
# =============================================================================

class DeploymentCreate(BaseModel):
    """Create deployment."""
    service_name: str
    version: str
    previous_version: Optional[str] = None
    commit_sha: Optional[str] = None
    environment: EnvironmentType
    strategy: DeploymentStrategy = DeploymentStrategy.ROLLING
    replicas: int = 2
    config_changes: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None
    requires_approval: bool = False
    docker_image: Optional[str] = None
    helm_chart_version: Optional[str] = None
    release_notes: Optional[str] = None
    deployment_notes: Optional[str] = None


class DeploymentResponse(BaseModel):
    """Deployment response."""
    id: UUID
    tenant_id: UUID
    deployment_number: Optional[str]
    service_name: str
    version: str
    previous_version: Optional[str]
    commit_sha: Optional[str]
    environment: EnvironmentType
    strategy: DeploymentStrategy
    status: DeploymentStatus
    replicas: int
    config_changes: Optional[Dict[str, Any]]
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    health_check_passed: Optional[bool]
    health_check_attempts: int
    rolled_back: bool
    rollback_reason: Optional[str]
    rollback_deployment_id: Optional[UUID]
    requires_approval: bool
    approved_by: Optional[UUID]
    approved_at: Optional[datetime]
    docker_image: Optional[str]
    helm_chart_version: Optional[str]
    release_notes: Optional[str]
    deployment_notes: Optional[str]
    duration_seconds: Optional[int]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]

    class Config:
        from_attributes = True


class DeploymentUpdate(BaseModel):
    """Update deployment."""
    status: Optional[DeploymentStatus] = None
    health_check_passed: Optional[bool] = None
    rollback_reason: Optional[str] = None


class EnvironmentPromotionCreate(BaseModel):
    """Create environment promotion."""
    service_name: str
    version: str
    source_environment: EnvironmentType
    target_environment: EnvironmentType
    approval_required: bool = True


class EnvironmentPromotionResponse(BaseModel):
    """Environment promotion response."""
    id: UUID
    tenant_id: UUID
    service_name: str
    version: str
    source_environment: EnvironmentType
    target_environment: EnvironmentType
    status: DeploymentStatus
    approval_required: bool
    approved_by: Optional[UUID]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]
    tests_passed: Optional[bool]
    security_scan_passed: Optional[bool]
    pre_checks_result: Optional[Dict[str, Any]]
    deployment_id: Optional[UUID]
    requested_at: datetime
    promoted_at: Optional[datetime]
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FeatureFlagCreate(BaseModel):
    """Create feature flag."""
    key: str
    name: str
    description: Optional[str] = None
    status: FeatureFlagStatus = FeatureFlagStatus.DISABLED
    environment: Optional[EnvironmentType] = None
    percentage_rollout: float = 0.0
    targeted_users: Optional[List[str]] = None
    targeted_tenants: Optional[List[UUID]] = None
    variants: Optional[List[Dict[str, Any]]] = None
    default_variant: Optional[str] = None
    rules: Optional[List[Dict[str, Any]]] = None
    owner_team: Optional[str] = None
    expires_at: Optional[datetime] = None


class FeatureFlagResponse(BaseModel):
    """Feature flag response."""
    id: UUID
    tenant_id: UUID
    key: str
    name: str
    description: Optional[str]
    status: FeatureFlagStatus
    environment: Optional[EnvironmentType]
    percentage_rollout: float
    targeted_users: Optional[List[str]]
    targeted_tenants: Optional[List[UUID]]
    variants: Optional[List[Dict[str, Any]]]
    default_variant: Optional[str]
    rules: Optional[List[Dict[str, Any]]]
    last_evaluated_at: Optional[datetime]
    evaluation_count: int
    owner_id: Optional[UUID]
    owner_team: Optional[str]
    launchdarkly_key: Optional[str]
    unleash_name: Optional[str]
    expires_at: Optional[datetime]
    archived: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]

    class Config:
        from_attributes = True


class FeatureFlagUpdate(BaseModel):
    """Update feature flag."""
    status: Optional[FeatureFlagStatus] = None
    percentage_rollout: Optional[float] = None
    targeted_users: Optional[List[str]] = None
    targeted_tenants: Optional[List[UUID]] = None
    rules: Optional[List[Dict[str, Any]]] = None
    archived: Optional[bool] = None


class DatabaseMigrationCreate(BaseModel):
    """Create database migration record."""
    migration_id: str
    migration_name: Optional[str] = None
    database_name: str
    environment: EnvironmentType
    up_sql: Optional[str] = None
    down_sql: Optional[str] = None


class DatabaseMigrationResponse(BaseModel):
    """Database migration response."""
    id: UUID
    tenant_id: UUID
    migration_id: str
    migration_name: Optional[str]
    database_name: str
    environment: EnvironmentType
    status: DeploymentStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    rollback_available: bool
    rolled_back: bool
    rollback_at: Optional[datetime]
    error_message: Optional[str]
    error_details: Optional[Dict[str, Any]]
    up_sql: Optional[str]
    down_sql: Optional[str]
    pre_migration_checksum: Optional[str]
    post_migration_checksum: Optional[str]
    created_at: datetime
    executed_by: Optional[UUID]

    class Config:
        from_attributes = True


# =============================================================================
# Backup & DR Schemas
# =============================================================================

class BackupCreate(BaseModel):
    """Create backup."""
    backup_type: BackupType
    source_database: str
    source_region: Optional[str] = None
    source_environment: EnvironmentType
    storage_location: Optional[str] = None
    storage_region: Optional[str] = None
    cross_region_copy: bool = False
    cross_region_location: Optional[str] = None
    encrypted: bool = True
    encryption_key_id: Optional[str] = None
    retention_days: int = 30
    pitr_enabled: bool = False
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[Dict[str, Any]] = None


class BackupResponse(BaseModel):
    """Backup response."""
    id: UUID
    tenant_id: UUID
    backup_id: Optional[str]
    backup_type: BackupType
    status: BackupStatus
    source_database: str
    source_region: Optional[str]
    source_environment: EnvironmentType
    storage_location: Optional[str]
    storage_region: Optional[str]
    cross_region_copy: bool
    cross_region_location: Optional[str]
    size_bytes: Optional[float]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    encrypted: bool
    encryption_key_id: Optional[str]
    retention_days: int
    expires_at: Optional[datetime]
    verified: bool
    verified_at: Optional[datetime]
    verification_result: Optional[Dict[str, Any]]
    pitr_enabled: bool
    earliest_restore_time: Optional[datetime]
    latest_restore_time: Optional[datetime]
    metadata: Optional[Dict[str, Any]]
    tags: Optional[Dict[str, Any]]
    created_at: datetime
    created_by: Optional[UUID]

    class Config:
        from_attributes = True


class RestoreOperationCreate(BaseModel):
    """Create restore operation."""
    backup_id: UUID
    target_database: str
    target_environment: EnvironmentType
    restore_to_point_in_time: Optional[datetime] = None


class RestoreOperationResponse(BaseModel):
    """Restore operation response."""
    id: UUID
    tenant_id: UUID
    backup_id: UUID
    restore_id: Optional[str]
    status: BackupStatus
    target_database: str
    target_environment: EnvironmentType
    restore_to_point_in_time: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    data_verification_passed: Optional[bool]
    verification_details: Optional[Dict[str, Any]]
    error_message: Optional[str]
    retry_count: int
    created_at: datetime
    initiated_by: Optional[UUID]

    class Config:
        from_attributes = True


class DisasterRecoveryPlanCreate(BaseModel):
    """Create DR plan."""
    name: str
    description: Optional[str] = None
    scenario: DRScenario
    rto_hours: float
    rpo_hours: float
    recovery_steps: List[Dict[str, Any]]
    communication_plan: Optional[Dict[str, Any]] = None
    escalation_contacts: Optional[List[Dict[str, Any]]] = None
    primary_region: Optional[str] = None
    dr_region: Optional[str] = None
    affected_services: Optional[List[str]] = None
    test_frequency_days: int = 90


class DisasterRecoveryPlanResponse(BaseModel):
    """DR plan response."""
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    scenario: DRScenario
    rto_hours: float
    rpo_hours: float
    recovery_steps: List[Dict[str, Any]]
    communication_plan: Optional[Dict[str, Any]]
    escalation_contacts: Optional[List[Dict[str, Any]]]
    primary_region: Optional[str]
    dr_region: Optional[str]
    affected_services: Optional[List[str]]
    last_tested_at: Optional[datetime]
    last_test_result: Optional[str]
    next_test_date: Optional[datetime]
    test_frequency_days: int
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]

    class Config:
        from_attributes = True


class DRDrillCreate(BaseModel):
    """Create DR drill."""
    dr_plan_id: UUID
    scheduled_at: datetime
    participants: Optional[List[UUID]] = None
    coordinator: Optional[UUID] = None


class DRDrillResponse(BaseModel):
    """DR drill response."""
    id: UUID
    tenant_id: UUID
    dr_plan_id: UUID
    drill_id: Optional[str]
    status: DrillStatus
    scheduled_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    participants: Optional[List[UUID]]
    coordinator: Optional[UUID]
    steps_completed: Optional[List[Dict[str, Any]]]
    issues_encountered: Optional[List[Dict[str, Any]]]
    rto_achieved_minutes: Optional[float]
    rpo_achieved_minutes: Optional[float]
    rto_target_met: Optional[bool]
    rpo_target_met: Optional[bool]
    success: Optional[bool]
    lessons_learned: Optional[str]
    action_items: Optional[List[Dict[str, Any]]]
    drill_report_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DRDrillUpdate(BaseModel):
    """Update DR drill."""
    status: Optional[DrillStatus] = None
    steps_completed: Optional[List[Dict[str, Any]]] = None
    issues_encountered: Optional[List[Dict[str, Any]]] = None
    rto_achieved_minutes: Optional[float] = None
    rpo_achieved_minutes: Optional[float] = None
    lessons_learned: Optional[str] = None
    action_items: Optional[List[Dict[str, Any]]] = None
    drill_report_url: Optional[str] = None


# =============================================================================
# Runbook Schemas
# =============================================================================

class RunbookCreate(BaseModel):
    """Create runbook."""
    title: str
    description: Optional[str] = None
    runbook_type: RunbookType
    steps: List[Dict[str, Any]]
    prerequisites: Optional[List[Dict[str, Any]]] = None
    required_access: Optional[List[str]] = None
    associated_alerts: Optional[List[UUID]] = None
    affected_services: Optional[List[str]] = None
    automated_steps: Optional[List[Dict[str, Any]]] = None
    automation_script_url: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    difficulty_level: Optional[str] = None
    owner_team: Optional[str] = None
    tags: Optional[List[str]] = None


class RunbookResponse(BaseModel):
    """Runbook response."""
    id: UUID
    tenant_id: UUID
    title: str
    description: Optional[str]
    runbook_type: RunbookType
    steps: List[Dict[str, Any]]
    prerequisites: Optional[List[Dict[str, Any]]]
    required_access: Optional[List[str]]
    associated_alerts: Optional[List[UUID]]
    affected_services: Optional[List[str]]
    automated_steps: Optional[List[Dict[str, Any]]]
    automation_script_url: Optional[str]
    estimated_duration_minutes: Optional[int]
    difficulty_level: Optional[str]
    version: int
    last_reviewed_at: Optional[datetime]
    next_review_date: Optional[datetime]
    owner_id: Optional[UUID]
    owner_team: Optional[str]
    times_used: int
    last_used_at: Optional[datetime]
    tags: Optional[List[str]]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]

    class Config:
        from_attributes = True


class RunbookUpdate(BaseModel):
    """Update runbook."""
    title: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None
    prerequisites: Optional[List[Dict[str, Any]]] = None
    required_access: Optional[List[str]] = None
    affected_services: Optional[List[str]] = None
    estimated_duration_minutes: Optional[int] = None
    is_active: Optional[bool] = None


class IncidentPlaybookCreate(BaseModel):
    """Create incident playbook."""
    title: str
    description: Optional[str] = None
    severity: AlertSeverity
    symptoms: List[Dict[str, Any]]
    diagnosis_steps: List[Dict[str, Any]]
    immediate_actions: List[Dict[str, Any]]
    long_term_fixes: Optional[List[Dict[str, Any]]] = None
    communication_template: Optional[str] = None
    stakeholders_to_notify: Optional[List[Dict[str, Any]]] = None
    related_runbooks: Optional[List[UUID]] = None
    related_alerts: Optional[List[UUID]] = None


class IncidentPlaybookResponse(BaseModel):
    """Incident playbook response."""
    id: UUID
    tenant_id: UUID
    title: str
    description: Optional[str]
    severity: AlertSeverity
    symptoms: List[Dict[str, Any]]
    diagnosis_steps: List[Dict[str, Any]]
    immediate_actions: List[Dict[str, Any]]
    long_term_fixes: Optional[List[Dict[str, Any]]]
    communication_template: Optional[str]
    stakeholders_to_notify: Optional[List[Dict[str, Any]]]
    related_runbooks: Optional[List[UUID]]
    related_alerts: Optional[List[UUID]]
    times_used: int
    avg_resolution_minutes: Optional[float]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]

    class Config:
        from_attributes = True


# =============================================================================
# Go-Live Schemas
# =============================================================================

class GoLiveChecklistCreate(BaseModel):
    """Create go-live checklist."""
    name: str
    description: Optional[str] = None
    target_go_live_date: Optional[datetime] = None
    environment: EnvironmentType = EnvironmentType.PRODUCTION
    required_approvers: Optional[List[UUID]] = None
    release_notes_url: Optional[str] = None
    rollback_plan_url: Optional[str] = None


class GoLiveChecklistResponse(BaseModel):
    """Go-live checklist response."""
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    target_go_live_date: Optional[datetime]
    environment: EnvironmentType
    total_items: int
    completed_items: int
    blocked_items: int
    completion_percentage: float
    is_ready: bool
    blockers: Optional[List[Dict[str, Any]]]
    required_approvers: Optional[List[UUID]]
    approvals_received: Optional[List[Dict[str, Any]]]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    actual_go_live_at: Optional[datetime]
    release_notes_url: Optional[str]
    rollback_plan_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]

    class Config:
        from_attributes = True


class GoLiveChecklistItemCreate(BaseModel):
    """Create go-live checklist item."""
    checklist_id: UUID
    title: str
    description: Optional[str] = None
    category: ChecklistCategory
    is_critical: bool = False
    is_blocker: bool = False
    assigned_to: Optional[UUID] = None
    owner_team: Optional[str] = None
    verification_method: Optional[str] = None
    depends_on: Optional[List[UUID]] = None
    due_date: Optional[datetime] = None
    display_order: int = 0


class GoLiveChecklistItemResponse(BaseModel):
    """Go-live checklist item response."""
    id: UUID
    checklist_id: UUID
    title: str
    description: Optional[str]
    category: ChecklistCategory
    status: ChecklistItemStatus
    is_critical: bool
    is_blocker: bool
    assigned_to: Optional[UUID]
    owner_team: Optional[str]
    verification_method: Optional[str]
    evidence_url: Optional[str]
    depends_on: Optional[List[UUID]]
    due_date: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    notes: Optional[str]
    blocker_reason: Optional[str]
    display_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GoLiveChecklistItemUpdate(BaseModel):
    """Update go-live checklist item."""
    status: Optional[ChecklistItemStatus] = None
    assigned_to: Optional[UUID] = None
    evidence_url: Optional[str] = None
    notes: Optional[str] = None
    blocker_reason: Optional[str] = None


class StatusPageComponentCreate(BaseModel):
    """Create status page component."""
    name: str
    description: Optional[str] = None
    group_name: Optional[str] = None
    display_order: int = 0
    health_check_id: Optional[UUID] = None
    show_on_public_page: bool = True
    show_uptime: bool = True
    statuspage_component_id: Optional[str] = None


class StatusPageComponentResponse(BaseModel):
    """Status page component response."""
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    status: HealthStatus
    group_name: Optional[str]
    display_order: int
    health_check_id: Optional[UUID]
    show_on_public_page: bool
    show_uptime: bool
    statuspage_component_id: Optional[str]
    uptime_percentage: Optional[float]
    last_incident_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StatusPageIncidentCreate(BaseModel):
    """Create status page incident."""
    alert_incident_id: Optional[UUID] = None
    title: str
    status: str = "investigating"
    impact: str = "none"
    affected_components: Optional[List[UUID]] = None
    is_public: bool = True
    scheduled_maintenance: bool = False
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None


class StatusPageIncidentResponse(BaseModel):
    """Status page incident response."""
    id: UUID
    tenant_id: UUID
    alert_incident_id: Optional[UUID]
    title: str
    status: Optional[str]
    impact: Optional[str]
    affected_components: Optional[List[UUID]]
    updates: Optional[List[Dict[str, Any]]]
    started_at: datetime
    resolved_at: Optional[datetime]
    statuspage_incident_id: Optional[str]
    is_public: bool
    scheduled_maintenance: bool
    scheduled_start: Optional[datetime]
    scheduled_end: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StatusPageIncidentUpdate(BaseModel):
    """Update status page incident."""
    status: Optional[str] = None
    impact: Optional[str] = None
    message: Optional[str] = None  # New update message


# =============================================================================
# Dashboard/Summary Schemas
# =============================================================================

class InfrastructureSummary(BaseModel):
    """Infrastructure summary."""
    total_resources: int
    resources_by_type: Dict[str, int]
    resources_by_status: Dict[str, int]
    resources_by_environment: Dict[str, int]
    total_monthly_cost: float
    multi_az_enabled: bool
    auto_scaling_configs: int


class MonitoringSummary(BaseModel):
    """Monitoring summary."""
    total_metrics: int
    total_dashboards: int
    total_health_checks: int
    healthy_services: int
    unhealthy_services: int
    degraded_services: int
    total_slos: int
    slos_met: int
    slos_at_risk: int


class AlertingSummary(BaseModel):
    """Alerting summary."""
    total_alert_rules: int
    enabled_alert_rules: int
    active_incidents: int
    incidents_by_severity: Dict[str, int]
    incidents_by_status: Dict[str, int]
    mttr_minutes: Optional[float]
    mttd_minutes: Optional[float]
    on_call_schedules: int


class DeploymentSummary(BaseModel):
    """Deployment summary."""
    total_deployments: int
    deployments_by_status: Dict[str, int]
    deployments_by_environment: Dict[str, int]
    recent_deployments: List[DeploymentResponse]
    feature_flags_enabled: int
    pending_promotions: int
    avg_deployment_duration_seconds: Optional[float]


class BackupDRSummary(BaseModel):
    """Backup and DR summary."""
    total_backups: int
    backups_by_status: Dict[str, int]
    latest_backup_at: Optional[datetime]
    backup_verified: bool
    total_dr_plans: int
    dr_plans_tested: int
    next_dr_drill: Optional[datetime]
    rto_hours: Optional[float]
    rpo_hours: Optional[float]


class OperationalReadinessSummary(BaseModel):
    """Operational readiness summary."""
    total_runbooks: int
    total_playbooks: int
    runbooks_by_type: Dict[str, int]
    runbooks_recently_used: int


class GoLiveReadinessSummary(BaseModel):
    """Go-live readiness summary."""
    total_checklists: int
    ready_checklists: int
    checklist_items_completed: int
    checklist_items_pending: int
    checklist_items_blocked: int
    critical_items_pending: int
    blockers: List[str]


class ProductionReadinessDashboard(BaseModel):
    """Complete production readiness dashboard."""
    infrastructure: InfrastructureSummary
    monitoring: MonitoringSummary
    alerting: AlertingSummary
    deployments: DeploymentSummary
    backup_dr: BackupDRSummary
    operations: OperationalReadinessSummary
    go_live: GoLiveReadinessSummary
    overall_readiness_score: float  # 0-100
    critical_issues: List[str]
    recommendations: List[str]

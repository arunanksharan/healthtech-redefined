"""
Production Readiness Module

Comprehensive production readiness infrastructure for EPIC-024: Production Readiness.
Including infrastructure management, monitoring & observability, alerting,
deployments, backup/DR, runbooks, and go-live preparation.
"""

from .models import (
    # Enums
    ResourceType,
    ResourceStatus,
    CloudProvider,
    EnvironmentType,
    MetricType,
    MetricCategory,
    AlertSeverity,
    AlertStatus,
    IncidentStatus,
    DeploymentStatus,
    DeploymentStrategy,
    FeatureFlagStatus,
    BackupType,
    BackupStatus,
    DRScenario,
    DrillStatus,
    RunbookType,
    ChecklistCategory,
    ChecklistItemStatus,
    HealthCheckType,
    HealthStatus,
    # Infrastructure Models
    InfrastructureResource,
    AutoScalingConfig,
    NetworkConfig,
    # Monitoring Models
    MetricDefinition,
    Dashboard,
    HealthCheck,
    SLODefinition,
    SLIRecord,
    # Alerting Models
    AlertRule,
    AlertIncident,
    OnCallSchedule,
    EscalationPolicy,
    # Deployment Models
    Deployment,
    EnvironmentPromotion,
    FeatureFlag,
    DatabaseMigration,
    # Backup & DR Models
    Backup,
    RestoreOperation,
    DisasterRecoveryPlan,
    DRDrill,
    # Runbook Models
    Runbook,
    IncidentPlaybook,
    # Go-Live Models
    GoLiveChecklist,
    GoLiveChecklistItem,
    StatusPageComponent,
    StatusPageIncident,
)

from .router import router

from .services import (
    InfrastructureService,
    MonitoringService,
    AlertingService,
    DeploymentService,
    BackupDRService,
    RunbookService,
    GoLiveService,
)

__all__ = [
    # Router
    "router",
    # Enums
    "ResourceType",
    "ResourceStatus",
    "CloudProvider",
    "EnvironmentType",
    "MetricType",
    "MetricCategory",
    "AlertSeverity",
    "AlertStatus",
    "IncidentStatus",
    "DeploymentStatus",
    "DeploymentStrategy",
    "FeatureFlagStatus",
    "BackupType",
    "BackupStatus",
    "DRScenario",
    "DrillStatus",
    "RunbookType",
    "ChecklistCategory",
    "ChecklistItemStatus",
    "HealthCheckType",
    "HealthStatus",
    # Infrastructure Models
    "InfrastructureResource",
    "AutoScalingConfig",
    "NetworkConfig",
    # Monitoring Models
    "MetricDefinition",
    "Dashboard",
    "HealthCheck",
    "SLODefinition",
    "SLIRecord",
    # Alerting Models
    "AlertRule",
    "AlertIncident",
    "OnCallSchedule",
    "EscalationPolicy",
    # Deployment Models
    "Deployment",
    "EnvironmentPromotion",
    "FeatureFlag",
    "DatabaseMigration",
    # Backup & DR Models
    "Backup",
    "RestoreOperation",
    "DisasterRecoveryPlan",
    "DRDrill",
    # Runbook Models
    "Runbook",
    "IncidentPlaybook",
    # Go-Live Models
    "GoLiveChecklist",
    "GoLiveChecklistItem",
    "StatusPageComponent",
    "StatusPageIncident",
    # Services
    "InfrastructureService",
    "MonitoringService",
    "AlertingService",
    "DeploymentService",
    "BackupDRService",
    "RunbookService",
    "GoLiveService",
]

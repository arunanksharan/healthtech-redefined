"""
Production Readiness Router

FastAPI router for EPIC-024: Production Readiness API endpoints.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db

from .models import (
    ResourceType, ResourceStatus, EnvironmentType,
    MetricCategory, HealthCheckType, AlertSeverity, IncidentStatus,
    DeploymentStatus, FeatureFlagStatus, BackupStatus, DRScenario, DrillStatus,
    RunbookType, ChecklistCategory, ChecklistItemStatus, HealthStatus
)
from .schemas import (
    # Infrastructure
    InfrastructureResourceCreate, InfrastructureResourceResponse,
    AutoScalingConfigCreate, AutoScalingConfigResponse,
    NetworkConfigCreate, NetworkConfigResponse, InfrastructureSummary,
    # Monitoring
    MetricDefinitionCreate, MetricDefinitionResponse,
    DashboardCreate, DashboardResponse,
    HealthCheckCreate, HealthCheckResponse,
    SLODefinitionCreate, SLODefinitionResponse,
    SLIRecordCreate, SLIRecordResponse, MonitoringSummary,
    # Alerting
    AlertRuleCreate, AlertRuleResponse,
    AlertIncidentCreate, AlertIncidentResponse, AlertIncidentUpdate,
    OnCallScheduleCreate, OnCallScheduleResponse,
    EscalationPolicyCreate, EscalationPolicyResponse, AlertingSummary,
    # Deployment
    DeploymentCreate, DeploymentResponse, DeploymentUpdate,
    EnvironmentPromotionCreate, EnvironmentPromotionResponse,
    FeatureFlagCreate, FeatureFlagResponse, FeatureFlagUpdate,
    DatabaseMigrationCreate, DatabaseMigrationResponse, DeploymentSummary,
    # Backup & DR
    BackupCreate, BackupResponse,
    RestoreOperationCreate, RestoreOperationResponse,
    DisasterRecoveryPlanCreate, DisasterRecoveryPlanResponse,
    DRDrillCreate, DRDrillResponse, DRDrillUpdate, BackupDRSummary,
    # Runbooks
    RunbookCreate, RunbookResponse, RunbookUpdate,
    IncidentPlaybookCreate, IncidentPlaybookResponse, OperationalReadinessSummary,
    # Go-Live
    GoLiveChecklistCreate, GoLiveChecklistResponse,
    GoLiveChecklistItemCreate, GoLiveChecklistItemResponse, GoLiveChecklistItemUpdate,
    StatusPageComponentCreate, StatusPageComponentResponse,
    StatusPageIncidentCreate, StatusPageIncidentResponse, StatusPageIncidentUpdate,
    GoLiveReadinessSummary,
    # Dashboard
    ProductionReadinessDashboard
)
from .services import (
    InfrastructureService, MonitoringService, AlertingService,
    DeploymentService, BackupDRService, RunbookService, GoLiveService
)

router = APIRouter(prefix="/production", tags=["Production Readiness"])


# Placeholder for tenant extraction from auth
async def get_current_tenant_id() -> UUID:
    from uuid import uuid4
    return uuid4()


async def get_current_user_id() -> UUID:
    from uuid import uuid4
    return uuid4()


# =============================================================================
# Infrastructure Endpoints
# =============================================================================

@router.post("/infrastructure/resources", response_model=InfrastructureResourceResponse)
async def create_infrastructure_resource(
    data: InfrastructureResourceCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Create a new infrastructure resource."""
    service = InfrastructureService(db)
    return await service.create_resource(tenant_id, data, user_id)


@router.get("/infrastructure/resources", response_model=List[InfrastructureResourceResponse])
async def list_infrastructure_resources(
    environment: Optional[EnvironmentType] = None,
    resource_type: Optional[ResourceType] = None,
    status: Optional[ResourceStatus] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """List infrastructure resources."""
    service = InfrastructureService(db)
    return await service.list_resources(tenant_id, environment, resource_type, status, limit, offset)


@router.get("/infrastructure/resources/{resource_id}", response_model=InfrastructureResourceResponse)
async def get_infrastructure_resource(
    resource_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Get an infrastructure resource."""
    service = InfrastructureService(db)
    resource = await service.get_resource(tenant_id, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource


@router.post("/infrastructure/resources/{resource_id}/terminate", response_model=InfrastructureResourceResponse)
async def terminate_infrastructure_resource(
    resource_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Terminate an infrastructure resource."""
    service = InfrastructureService(db)
    resource = await service.terminate_resource(tenant_id, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource


@router.post("/infrastructure/auto-scaling", response_model=AutoScalingConfigResponse)
async def create_auto_scaling_config(
    data: AutoScalingConfigCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Create auto-scaling configuration."""
    service = InfrastructureService(db)
    return await service.create_auto_scaling_config(tenant_id, data)


@router.get("/infrastructure/auto-scaling", response_model=List[AutoScalingConfigResponse])
async def list_auto_scaling_configs(
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """List auto-scaling configurations."""
    service = InfrastructureService(db)
    return await service.list_auto_scaling_configs(tenant_id, enabled_only)


@router.post("/infrastructure/network", response_model=NetworkConfigResponse)
async def create_network_config(
    data: NetworkConfigCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Create network configuration."""
    service = InfrastructureService(db)
    return await service.create_network_config(tenant_id, data)


@router.get("/infrastructure/network", response_model=List[NetworkConfigResponse])
async def list_network_configs(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """List network configurations."""
    service = InfrastructureService(db)
    return await service.list_network_configs(tenant_id)


@router.get("/infrastructure/summary", response_model=InfrastructureSummary)
async def get_infrastructure_summary(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Get infrastructure summary."""
    service = InfrastructureService(db)
    return await service.get_infrastructure_summary(tenant_id)


# =============================================================================
# Monitoring Endpoints
# =============================================================================

@router.post("/monitoring/metrics", response_model=MetricDefinitionResponse)
async def create_metric_definition(
    data: MetricDefinitionCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Create a metric definition."""
    service = MonitoringService(db)
    return await service.create_metric(tenant_id, data)


@router.get("/monitoring/metrics", response_model=List[MetricDefinitionResponse])
async def list_metric_definitions(
    category: Optional[MetricCategory] = None,
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """List metric definitions."""
    service = MonitoringService(db)
    return await service.list_metrics(tenant_id, category, enabled_only)


@router.post("/monitoring/dashboards", response_model=DashboardResponse)
async def create_dashboard(
    data: DashboardCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Create a dashboard."""
    service = MonitoringService(db)
    return await service.create_dashboard(tenant_id, data, user_id)


@router.get("/monitoring/dashboards", response_model=List[DashboardResponse])
async def list_dashboards(
    dashboard_type: Optional[str] = None,
    folder: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """List dashboards."""
    service = MonitoringService(db)
    return await service.list_dashboards(tenant_id, dashboard_type, folder)


@router.get("/monitoring/dashboards/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Get a dashboard."""
    service = MonitoringService(db)
    dashboard = await service.get_dashboard(tenant_id, dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.post("/monitoring/health-checks", response_model=HealthCheckResponse)
async def create_health_check(
    data: HealthCheckCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Create a health check."""
    service = MonitoringService(db)
    return await service.create_health_check(tenant_id, data)


@router.get("/monitoring/health-checks", response_model=List[HealthCheckResponse])
async def list_health_checks(
    service_name: Optional[str] = None,
    check_type: Optional[HealthCheckType] = None,
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """List health checks."""
    svc = MonitoringService(db)
    return await svc.list_health_checks(tenant_id, service_name, check_type, enabled_only)


@router.post("/monitoring/slos", response_model=SLODefinitionResponse)
async def create_slo(
    data: SLODefinitionCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Create an SLO definition."""
    service = MonitoringService(db)
    return await service.create_slo(tenant_id, data)


@router.get("/monitoring/slos", response_model=List[SLODefinitionResponse])
async def list_slos(
    service_name: Optional[str] = None,
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """List SLO definitions."""
    service = MonitoringService(db)
    return await service.list_slos(tenant_id, service_name, enabled_only)


@router.post("/monitoring/slis", response_model=SLIRecordResponse)
async def record_sli(
    data: SLIRecordCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Record an SLI measurement."""
    service = MonitoringService(db)
    return await service.record_sli(tenant_id, data)


@router.get("/monitoring/slos/{slo_id}/history", response_model=List[SLIRecordResponse])
async def get_sli_history(
    slo_id: UUID,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Get SLI history for an SLO."""
    service = MonitoringService(db)
    return await service.get_sli_history(tenant_id, slo_id, days)


@router.get("/monitoring/summary", response_model=MonitoringSummary)
async def get_monitoring_summary(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Get monitoring summary."""
    service = MonitoringService(db)
    return await service.get_monitoring_summary(tenant_id)


# =============================================================================
# Alerting Endpoints
# =============================================================================

@router.post("/alerting/rules", response_model=AlertRuleResponse)
async def create_alert_rule(
    data: AlertRuleCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Create an alert rule."""
    service = AlertingService(db)
    return await service.create_alert_rule(tenant_id, data, user_id)


@router.get("/alerting/rules", response_model=List[AlertRuleResponse])
async def list_alert_rules(
    severity: Optional[AlertSeverity] = None,
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """List alert rules."""
    service = AlertingService(db)
    return await service.list_alert_rules(tenant_id, severity, enabled_only)


@router.post("/alerting/rules/{rule_id}/silence")
async def silence_alert_rule(
    rule_id: UUID,
    duration_hours: int = 1,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Silence an alert rule."""
    service = AlertingService(db)
    rule = await service.silence_alert_rule(tenant_id, rule_id, duration_hours)
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    return {"message": f"Alert silenced for {duration_hours} hours"}


@router.post("/alerting/incidents", response_model=AlertIncidentResponse)
async def create_incident(
    data: AlertIncidentCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Create an incident."""
    service = AlertingService(db)
    return await service.create_incident(tenant_id, data)


@router.get("/alerting/incidents", response_model=List[AlertIncidentResponse])
async def list_incidents(
    status: Optional[IncidentStatus] = None,
    severity: Optional[AlertSeverity] = None,
    active_only: bool = False,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """List incidents."""
    service = AlertingService(db)
    return await service.list_incidents(tenant_id, status, severity, active_only, limit, offset)


@router.get("/alerting/incidents/{incident_id}", response_model=AlertIncidentResponse)
async def get_incident(
    incident_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Get an incident."""
    service = AlertingService(db)
    incident = await service.get_incident(tenant_id, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/alerting/incidents/{incident_id}/acknowledge", response_model=AlertIncidentResponse)
async def acknowledge_incident(
    incident_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Acknowledge an incident."""
    service = AlertingService(db)
    incident = await service.acknowledge_incident(tenant_id, incident_id, user_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.patch("/alerting/incidents/{incident_id}", response_model=AlertIncidentResponse)
async def update_incident(
    incident_id: UUID,
    data: AlertIncidentUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Update an incident."""
    service = AlertingService(db)
    incident = await service.update_incident(tenant_id, incident_id, data)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/alerting/on-call-schedules", response_model=OnCallScheduleResponse)
async def create_on_call_schedule(
    data: OnCallScheduleCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Create an on-call schedule."""
    service = AlertingService(db)
    return await service.create_on_call_schedule(tenant_id, data)


@router.get("/alerting/on-call-schedules", response_model=List[OnCallScheduleResponse])
async def list_on_call_schedules(
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """List on-call schedules."""
    service = AlertingService(db)
    return await service.list_on_call_schedules(tenant_id, enabled_only)


@router.post("/alerting/escalation-policies", response_model=EscalationPolicyResponse)
async def create_escalation_policy(
    data: EscalationPolicyCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Create an escalation policy."""
    service = AlertingService(db)
    return await service.create_escalation_policy(tenant_id, data)


@router.get("/alerting/escalation-policies", response_model=List[EscalationPolicyResponse])
async def list_escalation_policies(
    enabled_only: bool = False,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """List escalation policies."""
    service = AlertingService(db)
    return await service.list_escalation_policies(tenant_id, enabled_only)


@router.get("/alerting/summary", response_model=AlertingSummary)
async def get_alerting_summary(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Get alerting summary."""
    service = AlertingService(db)
    return await service.get_alerting_summary(tenant_id)


# =============================================================================
# Deployment Endpoints
# =============================================================================

@router.post("/deployments", response_model=DeploymentResponse)
async def create_deployment(
    data: DeploymentCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Create a deployment."""
    service = DeploymentService(db)
    return await service.create_deployment(tenant_id, data, user_id)


@router.get("/deployments", response_model=List[DeploymentResponse])
async def list_deployments(
    service_name: Optional[str] = None,
    environment: Optional[EnvironmentType] = None,
    status: Optional[DeploymentStatus] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """List deployments."""
    svc = DeploymentService(db)
    return await svc.list_deployments(tenant_id, service_name, environment, status, limit, offset)


@router.get("/deployments/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Get a deployment."""
    service = DeploymentService(db)
    deployment = await service.get_deployment(tenant_id, deployment_id)
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return deployment


@router.post("/deployments/{deployment_id}/start", response_model=DeploymentResponse)
async def start_deployment(
    deployment_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Start a deployment."""
    service = DeploymentService(db)
    deployment = await service.start_deployment(tenant_id, deployment_id)
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return deployment


@router.post("/deployments/{deployment_id}/approve", response_model=DeploymentResponse)
async def approve_deployment(
    deployment_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Approve a deployment."""
    service = DeploymentService(db)
    deployment = await service.approve_deployment(tenant_id, deployment_id, user_id)
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return deployment


@router.post("/deployments/{deployment_id}/rollback", response_model=DeploymentResponse)
async def rollback_deployment(
    deployment_id: UUID,
    reason: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Rollback a deployment."""
    service = DeploymentService(db)
    rollback = await service.rollback_deployment(tenant_id, deployment_id, reason, user_id)
    if not rollback:
        raise HTTPException(status_code=404, detail="Deployment not found or no previous version")
    return rollback


@router.post("/promotions", response_model=EnvironmentPromotionResponse)
async def create_promotion(
    data: EnvironmentPromotionCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Create an environment promotion."""
    service = DeploymentService(db)
    return await service.create_promotion(tenant_id, data, user_id)


@router.get("/promotions", response_model=List[EnvironmentPromotionResponse])
async def list_promotions(
    status: Optional[DeploymentStatus] = None,
    pending_only: bool = False,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """List environment promotions."""
    service = DeploymentService(db)
    return await service.list_promotions(tenant_id, status, pending_only)


@router.post("/promotions/{promotion_id}/approve", response_model=EnvironmentPromotionResponse)
async def approve_promotion(
    promotion_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Approve a promotion."""
    service = DeploymentService(db)
    promotion = await service.approve_promotion(tenant_id, promotion_id, user_id)
    if not promotion:
        raise HTTPException(status_code=404, detail="Promotion not found")
    return promotion


@router.post("/feature-flags", response_model=FeatureFlagResponse)
async def create_feature_flag(
    data: FeatureFlagCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Create a feature flag."""
    service = DeploymentService(db)
    return await service.create_feature_flag(tenant_id, data, user_id)


@router.get("/feature-flags", response_model=List[FeatureFlagResponse])
async def list_feature_flags(
    status: Optional[FeatureFlagStatus] = None,
    environment: Optional[EnvironmentType] = None,
    include_archived: bool = False,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """List feature flags."""
    service = DeploymentService(db)
    return await service.list_feature_flags(tenant_id, status, environment, include_archived)


@router.patch("/feature-flags/{flag_id}", response_model=FeatureFlagResponse)
async def update_feature_flag(
    flag_id: UUID,
    data: FeatureFlagUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Update a feature flag."""
    service = DeploymentService(db)
    flag = await service.update_feature_flag(tenant_id, flag_id, data)
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    return flag


@router.post("/feature-flags/{key}/evaluate")
async def evaluate_feature_flag(
    key: str,
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Evaluate a feature flag."""
    service = DeploymentService(db)
    result = await service.evaluate_feature_flag(tenant_id, key, user_id)
    return {"key": key, "enabled": result}


@router.get("/deployments/summary", response_model=DeploymentSummary)
async def get_deployment_summary(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Get deployment summary."""
    service = DeploymentService(db)
    return await service.get_deployment_summary(tenant_id)


# =============================================================================
# Backup & DR Endpoints
# =============================================================================

@router.post("/backups", response_model=BackupResponse)
async def create_backup(
    data: BackupCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Create a backup."""
    service = BackupDRService(db)
    return await service.create_backup(tenant_id, data, user_id)


@router.get("/backups", response_model=List[BackupResponse])
async def list_backups(
    source_database: Optional[str] = None,
    environment: Optional[EnvironmentType] = None,
    status: Optional[BackupStatus] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """List backups."""
    service = BackupDRService(db)
    return await service.list_backups(tenant_id, source_database, environment, status, limit, offset)


@router.get("/backups/{backup_id}", response_model=BackupResponse)
async def get_backup(
    backup_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Get a backup."""
    service = BackupDRService(db)
    backup = await service.get_backup(tenant_id, backup_id)
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    return backup


@router.post("/backups/{backup_id}/verify", response_model=BackupResponse)
async def verify_backup(
    backup_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Verify a backup."""
    service = BackupDRService(db)
    backup = await service.verify_backup(tenant_id, backup_id, {"verified": True})
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    return backup


@router.post("/restores", response_model=RestoreOperationResponse)
async def create_restore(
    data: RestoreOperationCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Create a restore operation."""
    service = BackupDRService(db)
    return await service.create_restore(tenant_id, data, user_id)


@router.get("/restores", response_model=List[RestoreOperationResponse])
async def list_restores(
    status: Optional[BackupStatus] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """List restore operations."""
    service = BackupDRService(db)
    return await service.list_restores(tenant_id, status)


@router.post("/dr-plans", response_model=DisasterRecoveryPlanResponse)
async def create_dr_plan(
    data: DisasterRecoveryPlanCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Create a DR plan."""
    service = BackupDRService(db)
    return await service.create_dr_plan(tenant_id, data, user_id)


@router.get("/dr-plans", response_model=List[DisasterRecoveryPlanResponse])
async def list_dr_plans(
    scenario: Optional[DRScenario] = None,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """List DR plans."""
    service = BackupDRService(db)
    return await service.list_dr_plans(tenant_id, scenario, active_only)


@router.get("/dr-plans/{plan_id}", response_model=DisasterRecoveryPlanResponse)
async def get_dr_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Get a DR plan."""
    service = BackupDRService(db)
    plan = await service.get_dr_plan(tenant_id, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="DR plan not found")
    return plan


@router.post("/dr-drills", response_model=DRDrillResponse)
async def create_dr_drill(
    data: DRDrillCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Create a DR drill."""
    service = BackupDRService(db)
    return await service.create_dr_drill(tenant_id, data)


@router.get("/dr-drills", response_model=List[DRDrillResponse])
async def list_dr_drills(
    dr_plan_id: Optional[UUID] = None,
    status: Optional[DrillStatus] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """List DR drills."""
    service = BackupDRService(db)
    return await service.list_dr_drills(tenant_id, dr_plan_id, status)


@router.patch("/dr-drills/{drill_id}", response_model=DRDrillResponse)
async def update_dr_drill(
    drill_id: UUID,
    data: DRDrillUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Update a DR drill."""
    service = BackupDRService(db)
    drill = await service.update_dr_drill(tenant_id, drill_id, data)
    if not drill:
        raise HTTPException(status_code=404, detail="DR drill not found")
    return drill


@router.get("/backup-dr/summary", response_model=BackupDRSummary)
async def get_backup_dr_summary(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Get backup and DR summary."""
    service = BackupDRService(db)
    return await service.get_backup_dr_summary(tenant_id)


# =============================================================================
# Runbook Endpoints
# =============================================================================

@router.post("/runbooks", response_model=RunbookResponse)
async def create_runbook(
    data: RunbookCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Create a runbook."""
    service = RunbookService(db)
    return await service.create_runbook(tenant_id, data, user_id)


@router.get("/runbooks", response_model=List[RunbookResponse])
async def list_runbooks(
    runbook_type: Optional[RunbookType] = None,
    affected_service: Optional[str] = None,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """List runbooks."""
    service = RunbookService(db)
    return await service.list_runbooks(tenant_id, runbook_type, affected_service, active_only)


@router.get("/runbooks/{runbook_id}", response_model=RunbookResponse)
async def get_runbook(
    runbook_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Get a runbook."""
    service = RunbookService(db)
    runbook = await service.get_runbook(tenant_id, runbook_id)
    if not runbook:
        raise HTTPException(status_code=404, detail="Runbook not found")
    return runbook


@router.patch("/runbooks/{runbook_id}", response_model=RunbookResponse)
async def update_runbook(
    runbook_id: UUID,
    data: RunbookUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Update a runbook."""
    service = RunbookService(db)
    runbook = await service.update_runbook(tenant_id, runbook_id, data)
    if not runbook:
        raise HTTPException(status_code=404, detail="Runbook not found")
    return runbook


@router.post("/runbooks/{runbook_id}/use", response_model=RunbookResponse)
async def record_runbook_usage(
    runbook_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Record runbook usage."""
    service = RunbookService(db)
    runbook = await service.record_runbook_usage(tenant_id, runbook_id)
    if not runbook:
        raise HTTPException(status_code=404, detail="Runbook not found")
    return runbook


@router.get("/runbooks/search/{query}", response_model=List[RunbookResponse])
async def search_runbooks(
    query: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Search runbooks."""
    service = RunbookService(db)
    return await service.search_runbooks(tenant_id, query)


@router.post("/playbooks", response_model=IncidentPlaybookResponse)
async def create_playbook(
    data: IncidentPlaybookCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Create an incident playbook."""
    service = RunbookService(db)
    return await service.create_playbook(tenant_id, data, user_id)


@router.get("/playbooks", response_model=List[IncidentPlaybookResponse])
async def list_playbooks(
    severity: Optional[AlertSeverity] = None,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """List incident playbooks."""
    service = RunbookService(db)
    return await service.list_playbooks(tenant_id, severity, active_only)


@router.get("/operations/summary", response_model=OperationalReadinessSummary)
async def get_operations_summary(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Get operational readiness summary."""
    service = RunbookService(db)
    return await service.get_operational_readiness_summary(tenant_id)


# =============================================================================
# Go-Live Endpoints
# =============================================================================

@router.post("/go-live/checklists", response_model=GoLiveChecklistResponse)
async def create_go_live_checklist(
    data: GoLiveChecklistCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Create a go-live checklist."""
    service = GoLiveService(db)
    return await service.create_checklist(tenant_id, data, user_id)


@router.get("/go-live/checklists", response_model=List[GoLiveChecklistResponse])
async def list_go_live_checklists(
    environment: Optional[EnvironmentType] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """List go-live checklists."""
    service = GoLiveService(db)
    return await service.list_checklists(tenant_id, environment)


@router.get("/go-live/checklists/{checklist_id}", response_model=GoLiveChecklistResponse)
async def get_go_live_checklist(
    checklist_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Get a go-live checklist."""
    service = GoLiveService(db)
    checklist = await service.get_checklist(tenant_id, checklist_id)
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")
    return checklist


@router.post("/go-live/checklists/{checklist_id}/start", response_model=GoLiveChecklistResponse)
async def start_go_live_checklist(
    checklist_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Start a go-live checklist."""
    service = GoLiveService(db)
    checklist = await service.start_checklist(tenant_id, checklist_id)
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")
    return checklist


@router.post("/go-live/checklists/{checklist_id}/approve", response_model=GoLiveChecklistResponse)
async def approve_go_live_checklist(
    checklist_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Approve a go-live checklist."""
    service = GoLiveService(db)
    checklist = await service.approve_checklist(tenant_id, checklist_id, user_id)
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")
    return checklist


@router.post("/go-live/checklists/{checklist_id}/launch", response_model=GoLiveChecklistResponse)
async def mark_go_live(
    checklist_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Mark checklist as launched."""
    service = GoLiveService(db)
    checklist = await service.mark_go_live(tenant_id, checklist_id)
    if not checklist:
        raise HTTPException(status_code=400, detail="Checklist not ready or not found")
    return checklist


@router.post("/go-live/items", response_model=GoLiveChecklistItemResponse)
async def create_checklist_item(
    data: GoLiveChecklistItemCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Create a checklist item."""
    service = GoLiveService(db)
    return await service.create_checklist_item(tenant_id, data)


@router.get("/go-live/checklists/{checklist_id}/items", response_model=List[GoLiveChecklistItemResponse])
async def list_checklist_items(
    checklist_id: UUID,
    category: Optional[ChecklistCategory] = None,
    status: Optional[ChecklistItemStatus] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """List checklist items."""
    service = GoLiveService(db)
    return await service.list_checklist_items(tenant_id, checklist_id, category, status)


@router.patch("/go-live/items/{item_id}", response_model=GoLiveChecklistItemResponse)
async def update_checklist_item(
    item_id: UUID,
    data: GoLiveChecklistItemUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Update a checklist item."""
    service = GoLiveService(db)
    item = await service.update_checklist_item(tenant_id, item_id, data)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post("/go-live/items/{item_id}/complete", response_model=GoLiveChecklistItemResponse)
async def complete_checklist_item(
    item_id: UUID,
    evidence_url: Optional[str] = None,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Complete a checklist item."""
    service = GoLiveService(db)
    item = await service.complete_checklist_item(tenant_id, item_id, evidence_url, notes)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.post("/status-page/components", response_model=StatusPageComponentResponse)
async def create_status_component(
    data: StatusPageComponentCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Create a status page component."""
    service = GoLiveService(db)
    return await service.create_status_component(tenant_id, data)


@router.get("/status-page/components", response_model=List[StatusPageComponentResponse])
async def list_status_components(
    public_only: bool = False,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """List status page components."""
    service = GoLiveService(db)
    return await service.list_status_components(tenant_id, public_only)


@router.post("/status-page/incidents", response_model=StatusPageIncidentResponse)
async def create_status_incident(
    data: StatusPageIncidentCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Create a status page incident."""
    service = GoLiveService(db)
    return await service.create_status_incident(tenant_id, data)


@router.get("/status-page/incidents", response_model=List[StatusPageIncidentResponse])
async def list_status_incidents(
    public_only: bool = False,
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """List status page incidents."""
    service = GoLiveService(db)
    return await service.list_status_incidents(tenant_id, public_only, active_only)


@router.patch("/status-page/incidents/{incident_id}", response_model=StatusPageIncidentResponse)
async def update_status_incident(
    incident_id: UUID,
    data: StatusPageIncidentUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Update a status page incident."""
    service = GoLiveService(db)
    incident = await service.update_status_incident(tenant_id, incident_id, data)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.get("/go-live/summary", response_model=GoLiveReadinessSummary)
async def get_go_live_summary(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Get go-live readiness summary."""
    service = GoLiveService(db)
    return await service.get_go_live_readiness_summary(tenant_id)


# =============================================================================
# Dashboard Endpoint
# =============================================================================

@router.get("/dashboard", response_model=ProductionReadinessDashboard)
async def get_production_readiness_dashboard(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id)
):
    """Get comprehensive production readiness dashboard."""
    infra_svc = InfrastructureService(db)
    monitor_svc = MonitoringService(db)
    alert_svc = AlertingService(db)
    deploy_svc = DeploymentService(db)
    backup_svc = BackupDRService(db)
    runbook_svc = RunbookService(db)
    golive_svc = GoLiveService(db)

    infrastructure = await infra_svc.get_infrastructure_summary(tenant_id)
    monitoring = await monitor_svc.get_monitoring_summary(tenant_id)
    alerting = await alert_svc.get_alerting_summary(tenant_id)
    deployments = await deploy_svc.get_deployment_summary(tenant_id)
    backup_dr = await backup_svc.get_backup_dr_summary(tenant_id)
    operations = await runbook_svc.get_operational_readiness_summary(tenant_id)
    go_live = await golive_svc.get_go_live_readiness_summary(tenant_id)

    # Calculate overall readiness score (simple weighted average)
    scores = []

    # Infrastructure score (20%)
    if infrastructure.total_resources > 0:
        running = infrastructure.resources_by_status.get("running", 0)
        infra_score = (running / infrastructure.total_resources) * 100
    else:
        infra_score = 0
    scores.append(infra_score * 0.20)

    # Monitoring score (15%)
    if monitoring.total_health_checks > 0:
        healthy = monitoring.healthy_services
        total_services = healthy + monitoring.unhealthy_services + monitoring.degraded_services
        monitor_score = (healthy / total_services * 100) if total_services > 0 else 0
    else:
        monitor_score = 0
    scores.append(monitor_score * 0.15)

    # Alerting score (15%)
    alert_score = 100 if alerting.active_incidents == 0 else max(0, 100 - alerting.active_incidents * 10)
    scores.append(alert_score * 0.15)

    # Deployment score (15%)
    deploy_score = 100 if deployments.pending_promotions == 0 else max(0, 100 - deployments.pending_promotions * 20)
    scores.append(deploy_score * 0.15)

    # Backup/DR score (15%)
    backup_score = 100 if backup_dr.backup_verified and backup_dr.dr_plans_tested > 0 else 50
    scores.append(backup_score * 0.15)

    # Operations score (10%)
    ops_score = min(100, operations.total_runbooks * 10) if operations.total_runbooks > 0 else 0
    scores.append(ops_score * 0.10)

    # Go-live score (10%)
    if go_live.total_checklists > 0:
        total_items = go_live.checklist_items_completed + go_live.checklist_items_pending + go_live.checklist_items_blocked
        golive_score = (go_live.checklist_items_completed / total_items * 100) if total_items > 0 else 0
    else:
        golive_score = 0
    scores.append(golive_score * 0.10)

    overall_readiness_score = sum(scores)

    # Identify critical issues
    critical_issues = []
    if monitoring.unhealthy_services > 0:
        critical_issues.append(f"{monitoring.unhealthy_services} unhealthy service(s)")
    if alerting.active_incidents > 0:
        critical_issues.append(f"{alerting.active_incidents} active incident(s)")
    if go_live.critical_items_pending > 0:
        critical_issues.append(f"{go_live.critical_items_pending} critical checklist items pending")
    if go_live.checklist_items_blocked > 0:
        critical_issues.append(f"{go_live.checklist_items_blocked} blocked checklist items")

    # Recommendations
    recommendations = []
    if not backup_dr.backup_verified:
        recommendations.append("Verify recent backup integrity")
    if backup_dr.dr_plans_tested == 0:
        recommendations.append("Conduct DR drill for all plans")
    if operations.total_runbooks < 5:
        recommendations.append("Create more operational runbooks")
    if monitoring.slos_at_risk > 0:
        recommendations.append(f"Address {monitoring.slos_at_risk} SLO(s) at risk")
    if infrastructure.auto_scaling_configs == 0:
        recommendations.append("Configure auto-scaling for production resources")

    return ProductionReadinessDashboard(
        infrastructure=infrastructure,
        monitoring=monitoring,
        alerting=alerting,
        deployments=deployments,
        backup_dr=backup_dr,
        operations=operations,
        go_live=go_live,
        overall_readiness_score=round(overall_readiness_score, 2),
        critical_issues=critical_issues,
        recommendations=recommendations
    )

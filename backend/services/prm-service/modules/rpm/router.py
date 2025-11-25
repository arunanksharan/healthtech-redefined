"""
Remote Patient Monitoring (RPM) API Router

FastAPI router for RPM endpoints:
- Device management
- Reading ingestion
- Alert management
- Care protocols
- Enrollment management
- Billing
- Patient engagement
- Analytics
- Third-party integrations

EPIC-019: Remote Patient Monitoring
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Body, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db

from .schemas import (
    # Device
    DeviceCreate, DeviceUpdate, DeviceResponse,
    DeviceAssignmentCreate, DeviceAssignmentUpdate, DeviceAssignmentResponse,
    # Reading
    ReadingCreate, ReadingBatchCreate, ReadingUpdate, ReadingResponse,
    ReadingBatchResponse, ReadingFilters,
    BloodPressureReading, GlucoseReading, WeightReading, OxygenSaturationReading,
    # Alert
    AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse,
    PatientAlertRuleCreate, PatientAlertRuleUpdate, PatientAlertRuleResponse,
    AlertResponse, AlertAcknowledge, AlertResolve, AlertEscalate, AlertFilters,
    # Protocol
    ProtocolCreate, ProtocolUpdate, ProtocolResponse,
    ProtocolTriggerCreate, ProtocolActionCreate,
    TriggerResponse, ActionResponse, ProtocolExecutionResponse,
    # Enrollment
    EnrollmentCreate, EnrollmentUpdate, EnrollmentResponse, EnrollmentFilters,
    # Billing
    MonitoringPeriodResponse, ClinicalTimeEntryCreate, ClinicalTimeEntryResponse,
    BillingEventCreate, BillingEventResponse, BillingSummary,
    # Engagement
    PatientReminderCreate, PatientReminderUpdate, PatientReminderResponse,
    PatientGoalCreate, PatientGoalUpdate, PatientGoalResponse,
    EducationalContentCreate, EducationalContentResponse, ContentEngagementCreate,
    # Analytics
    TrendAnalysisResponse, PopulationMetricsResponse, DataQualityResponse,
    # Dashboard
    PatientRPMDashboard, ProviderRPMDashboard, RPMProgramMetrics,
    # Webhook
    WithingsWebhookPayload, AppleHealthExportPayload, GoogleFitDataPayload,
    # Common
    PaginatedResponse,
    # Enums
    DeviceType, DeviceStatus, DeviceVendor, ReadingType, ReadingStatus,
    AlertSeverity, AlertStatus, AlertType, ProtocolStatus, EnrollmentStatus,
    BillingCodeType
)
from .services import (
    DeviceService, ReadingService, AlertService, ProtocolService,
    EnrollmentService, BillingService, EngagementService,
    AnalyticsService, IntegrationService
)

router = APIRouter(prefix="/rpm", tags=["Remote Patient Monitoring"])

# Service instances
device_service = DeviceService()
reading_service = ReadingService()
alert_service = AlertService()
protocol_service = ProtocolService()
enrollment_service = EnrollmentService()
billing_service = BillingService()
engagement_service = EngagementService()
analytics_service = AnalyticsService()
integration_service = IntegrationService()


# Dependency for tenant ID (would come from auth in production)
async def get_tenant_id() -> UUID:
    return UUID("00000000-0000-0000-0000-000000000001")


async def get_current_user_id() -> UUID:
    return UUID("00000000-0000-0000-0000-000000000002")


# =============================================================================
# DEVICE ENDPOINTS
# =============================================================================

@router.post("/devices", response_model=DeviceResponse, status_code=201)
async def register_device(
    device_data: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Register a new RPM device."""
    try:
        device = await device_service.register_device(db, tenant_id, device_data)
        return device
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/devices", response_model=PaginatedResponse)
async def list_devices(
    device_type: Optional[DeviceType] = None,
    vendor: Optional[DeviceVendor] = None,
    status: Optional[DeviceStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """List registered devices."""
    devices, total = await device_service.list_devices(
        db, tenant_id, device_type, vendor, status, skip, limit
    )
    return PaginatedResponse(
        items=[DeviceResponse.from_orm(d) for d in devices],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/devices/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get device by ID."""
    device = await device_service.get_device(db, device_id, tenant_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.patch("/devices/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: UUID,
    update_data: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Update device information."""
    device = await device_service.update_device(db, device_id, tenant_id, update_data)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.post("/devices/{device_id}/deactivate", status_code=204)
async def deactivate_device(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Deactivate a device."""
    success = await device_service.deactivate_device(db, device_id, tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Device not found")


# Device Assignments
@router.post("/devices/assignments", response_model=DeviceAssignmentResponse, status_code=201)
async def assign_device(
    assignment_data: DeviceAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Assign a device to a patient."""
    try:
        assignment = await device_service.assign_device(
            db, tenant_id, user_id, assignment_data
        )
        return assignment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/patients/{patient_id}/devices", response_model=List[DeviceAssignmentResponse])
async def get_patient_devices(
    patient_id: UUID,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get all device assignments for a patient."""
    assignments = await device_service.get_patient_assignments(
        db, tenant_id, patient_id, active_only
    )
    return assignments


@router.patch("/devices/assignments/{assignment_id}", response_model=DeviceAssignmentResponse)
async def update_assignment(
    assignment_id: UUID,
    update_data: DeviceAssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Update device assignment."""
    assignment = await device_service.update_assignment(
        db, assignment_id, tenant_id, update_data
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


@router.post("/devices/assignments/{assignment_id}/unassign", status_code=204)
async def unassign_device(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Unassign a device from a patient."""
    success = await device_service.unassign_device(
        db, assignment_id, tenant_id, user_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Assignment not found")


# =============================================================================
# READING ENDPOINTS
# =============================================================================

@router.post("/readings", response_model=ReadingResponse, status_code=201)
async def create_reading(
    reading_data: ReadingCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Create a single device reading."""
    reading = await reading_service.create_reading(db, tenant_id, reading_data)

    # Evaluate alerts in background
    background_tasks.add_task(
        alert_service.evaluate_reading, db, tenant_id, reading
    )

    return reading


@router.post("/readings/batch", response_model=ReadingBatchResponse, status_code=201)
async def create_batch_readings(
    batch_data: ReadingBatchCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Create multiple readings in batch."""
    result = await reading_service.create_batch_readings(db, tenant_id, batch_data)
    return result


@router.post("/readings/blood-pressure", response_model=List[ReadingResponse], status_code=201)
async def create_blood_pressure_reading(
    bp_data: BloodPressureReading,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Create blood pressure reading (convenience endpoint)."""
    readings = await reading_service.create_blood_pressure_reading(
        db, tenant_id, bp_data
    )
    return readings


@router.post("/readings/glucose", response_model=ReadingResponse, status_code=201)
async def create_glucose_reading(
    glucose_data: GlucoseReading,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Create glucose reading (convenience endpoint)."""
    reading = await reading_service.create_glucose_reading(db, tenant_id, glucose_data)
    return reading


@router.post("/readings/weight", response_model=ReadingResponse, status_code=201)
async def create_weight_reading(
    weight_data: WeightReading,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Create weight reading (convenience endpoint)."""
    reading = await reading_service.create_weight_reading(db, tenant_id, weight_data)
    return reading


@router.post("/readings/spo2", response_model=List[ReadingResponse], status_code=201)
async def create_spo2_reading(
    spo2_data: OxygenSaturationReading,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Create SpO2 reading (convenience endpoint)."""
    readings = await reading_service.create_spo2_reading(db, tenant_id, spo2_data)
    return readings


@router.get("/readings", response_model=PaginatedResponse)
async def list_readings(
    patient_id: Optional[UUID] = None,
    device_id: Optional[UUID] = None,
    enrollment_id: Optional[UUID] = None,
    reading_type: Optional[ReadingType] = None,
    status: Optional[ReadingStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    is_manual: Optional[bool] = None,
    is_valid: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """List readings with filters."""
    filters = ReadingFilters(
        patient_id=patient_id,
        device_id=device_id,
        enrollment_id=enrollment_id,
        reading_type=reading_type,
        status=status,
        start_date=start_date,
        end_date=end_date,
        is_manual=is_manual,
        is_valid=is_valid
    )
    readings, total = await reading_service.list_readings(
        db, tenant_id, filters, skip, limit
    )
    return PaginatedResponse(
        items=[ReadingResponse.from_orm(r) for r in readings],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/patients/{patient_id}/readings", response_model=List[ReadingResponse])
async def get_patient_readings(
    patient_id: UUID,
    reading_type: Optional[ReadingType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get readings for a specific patient."""
    readings = await reading_service.get_patient_readings(
        db, tenant_id, patient_id, reading_type, start_date, end_date, limit
    )
    return readings


@router.get("/readings/{reading_id}", response_model=ReadingResponse)
async def get_reading(
    reading_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get reading by ID."""
    reading = await reading_service.get_reading(db, reading_id, tenant_id)
    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")
    return reading


@router.patch("/readings/{reading_id}", response_model=ReadingResponse)
async def update_reading(
    reading_id: UUID,
    update_data: ReadingUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Update reading status."""
    reading = await reading_service.update_reading(
        db, reading_id, tenant_id, update_data
    )
    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")
    return reading


@router.post("/readings/{reading_id}/validate", response_model=ReadingResponse)
async def validate_reading(
    reading_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Mark reading as validated."""
    reading = await reading_service.validate_reading(
        db, reading_id, tenant_id, user_id
    )
    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")
    return reading


# =============================================================================
# ALERT ENDPOINTS
# =============================================================================

@router.post("/alert-rules", response_model=AlertRuleResponse, status_code=201)
async def create_alert_rule(
    rule_data: AlertRuleCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Create a new alert rule."""
    rule = await alert_service.create_alert_rule(db, tenant_id, user_id, rule_data)
    return rule


@router.get("/alert-rules", response_model=PaginatedResponse)
async def list_alert_rules(
    reading_type: Optional[ReadingType] = None,
    active_only: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """List alert rules."""
    rules, total = await alert_service.list_alert_rules(
        db, tenant_id, reading_type, active_only, skip, limit
    )
    return PaginatedResponse(
        items=[AlertRuleResponse.from_orm(r) for r in rules],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/alert-rules/{rule_id}", response_model=AlertRuleResponse)
async def get_alert_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get alert rule by ID."""
    rule = await alert_service.get_alert_rule(db, rule_id, tenant_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    return rule


@router.patch("/alert-rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: UUID,
    update_data: AlertRuleUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Update alert rule."""
    rule = await alert_service.update_alert_rule(db, rule_id, tenant_id, update_data)
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    return rule


@router.delete("/alert-rules/{rule_id}", status_code=204)
async def delete_alert_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Delete (deactivate) alert rule."""
    success = await alert_service.delete_alert_rule(db, rule_id, tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert rule not found")


# Patient-specific rules
@router.post("/patients/{patient_id}/alert-rules", response_model=PatientAlertRuleResponse, status_code=201)
async def create_patient_alert_rule(
    patient_id: UUID,
    rule_data: PatientAlertRuleCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Create patient-specific alert rule override."""
    rule_data.patient_id = patient_id
    try:
        rule = await alert_service.create_patient_rule(db, tenant_id, rule_data)
        return rule
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/patients/{patient_id}/alert-rules", response_model=List[PatientAlertRuleResponse])
async def get_patient_alert_rules(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get patient-specific alert rules."""
    rules = await alert_service.get_patient_rules(db, tenant_id, patient_id)
    return rules


# Alerts
@router.get("/alerts", response_model=PaginatedResponse)
async def list_alerts(
    patient_id: Optional[UUID] = None,
    enrollment_id: Optional[UUID] = None,
    severity: Optional[AlertSeverity] = None,
    status: Optional[AlertStatus] = None,
    alert_type: Optional[AlertType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """List alerts with filters."""
    filters = AlertFilters(
        patient_id=patient_id,
        enrollment_id=enrollment_id,
        severity=severity,
        status=status,
        alert_type=alert_type,
        start_date=start_date,
        end_date=end_date
    )
    alerts, total = await alert_service.list_alerts(
        db, tenant_id, filters, skip, limit
    )
    return PaginatedResponse(
        items=[AlertResponse.from_orm(a) for a in alerts],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/alerts/active", response_model=List[AlertResponse])
async def get_active_alerts(
    patient_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get all active (unresolved) alerts."""
    alerts = await alert_service.get_active_alerts(db, tenant_id, patient_id)
    return alerts


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get alert by ID."""
    alert = await alert_service.get_alert(db, alert_id, tenant_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: UUID,
    ack_data: AlertAcknowledge,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Acknowledge an alert."""
    try:
        alert = await alert_service.acknowledge_alert(
            db, alert_id, tenant_id, user_id, ack_data
        )
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        return alert
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/alerts/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: UUID,
    resolve_data: AlertResolve,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Resolve an alert."""
    alert = await alert_service.resolve_alert(
        db, alert_id, tenant_id, user_id, resolve_data
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.post("/alerts/{alert_id}/escalate", response_model=AlertResponse)
async def escalate_alert(
    alert_id: UUID,
    escalate_data: AlertEscalate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Escalate an alert."""
    alert = await alert_service.escalate_alert(
        db, alert_id, tenant_id, escalate_data
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


# =============================================================================
# PROTOCOL ENDPOINTS
# =============================================================================

@router.post("/protocols", response_model=ProtocolResponse, status_code=201)
async def create_protocol(
    protocol_data: ProtocolCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Create a new care protocol."""
    protocol = await protocol_service.create_protocol(
        db, tenant_id, user_id, protocol_data
    )
    return protocol


@router.get("/protocols", response_model=PaginatedResponse)
async def list_protocols(
    condition: Optional[str] = None,
    status: Optional[ProtocolStatus] = None,
    template_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """List care protocols."""
    protocols, total = await protocol_service.list_protocols(
        db, tenant_id, condition, status, template_only, skip, limit
    )
    return PaginatedResponse(
        items=[ProtocolResponse.from_orm(p) for p in protocols],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/protocols/{protocol_id}", response_model=ProtocolResponse)
async def get_protocol(
    protocol_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get protocol by ID."""
    protocol = await protocol_service.get_protocol(db, protocol_id, tenant_id)
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    return protocol


@router.patch("/protocols/{protocol_id}", response_model=ProtocolResponse)
async def update_protocol(
    protocol_id: UUID,
    update_data: ProtocolUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Update protocol."""
    protocol = await protocol_service.update_protocol(
        db, protocol_id, tenant_id, update_data
    )
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    return protocol


@router.post("/protocols/{protocol_id}/activate", response_model=ProtocolResponse)
async def activate_protocol(
    protocol_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Activate a protocol."""
    try:
        protocol = await protocol_service.activate_protocol(
            db, protocol_id, tenant_id, user_id
        )
        if not protocol:
            raise HTTPException(status_code=404, detail="Protocol not found")
        return protocol
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/protocols/{protocol_id}/copy", response_model=ProtocolResponse, status_code=201)
async def copy_protocol(
    protocol_id: UUID,
    new_name: str = Query(..., min_length=1, max_length=200),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Copy a protocol."""
    protocol = await protocol_service.copy_protocol(
        db, protocol_id, tenant_id, user_id, new_name
    )
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")
    return protocol


# Protocol triggers and actions
@router.post("/protocols/{protocol_id}/triggers", response_model=TriggerResponse, status_code=201)
async def add_trigger(
    protocol_id: UUID,
    trigger_data: ProtocolTriggerCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Add a trigger to a protocol."""
    trigger = await protocol_service.add_trigger(
        db, protocol_id, tenant_id, trigger_data
    )
    if not trigger:
        raise HTTPException(status_code=404, detail="Protocol not found")
    return trigger


@router.post("/triggers/{trigger_id}/actions", response_model=ActionResponse, status_code=201)
async def add_action(
    trigger_id: UUID,
    action_data: ProtocolActionCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Add an action to a trigger."""
    action = await protocol_service.add_action(db, trigger_id, tenant_id, action_data)
    if not action:
        raise HTTPException(status_code=404, detail="Trigger not found")
    return action


# =============================================================================
# ENROLLMENT ENDPOINTS
# =============================================================================

@router.post("/enrollments", response_model=EnrollmentResponse, status_code=201)
async def create_enrollment(
    enrollment_data: EnrollmentCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Create a new RPM enrollment."""
    try:
        enrollment = await enrollment_service.create_enrollment(
            db, tenant_id, user_id, enrollment_data
        )
        return enrollment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/enrollments", response_model=PaginatedResponse)
async def list_enrollments(
    patient_id: Optional[UUID] = None,
    provider_id: Optional[UUID] = None,
    condition: Optional[str] = None,
    status: Optional[EnrollmentStatus] = None,
    protocol_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """List enrollments."""
    filters = EnrollmentFilters(
        patient_id=patient_id,
        provider_id=provider_id,
        condition=condition,
        status=status,
        protocol_id=protocol_id
    )
    enrollments, total = await enrollment_service.list_enrollments(
        db, tenant_id, filters, skip, limit
    )
    return PaginatedResponse(
        items=[EnrollmentResponse.from_orm(e) for e in enrollments],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/enrollments/{enrollment_id}", response_model=EnrollmentResponse)
async def get_enrollment(
    enrollment_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get enrollment by ID."""
    enrollment = await enrollment_service.get_enrollment(
        db, enrollment_id, tenant_id
    )
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return enrollment


@router.get("/patients/{patient_id}/enrollment", response_model=EnrollmentResponse)
async def get_patient_enrollment(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get patient's current enrollment."""
    enrollment = await enrollment_service.get_patient_enrollment(
        db, tenant_id, patient_id
    )
    if not enrollment:
        raise HTTPException(status_code=404, detail="No active enrollment found")
    return enrollment


@router.patch("/enrollments/{enrollment_id}", response_model=EnrollmentResponse)
async def update_enrollment(
    enrollment_id: UUID,
    update_data: EnrollmentUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Update enrollment."""
    enrollment = await enrollment_service.update_enrollment(
        db, enrollment_id, tenant_id, update_data
    )
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return enrollment


@router.post("/enrollments/{enrollment_id}/activate", response_model=EnrollmentResponse)
async def activate_enrollment(
    enrollment_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Activate an enrollment."""
    try:
        enrollment = await enrollment_service.activate_enrollment(
            db, enrollment_id, tenant_id
        )
        if not enrollment:
            raise HTTPException(status_code=404, detail="Enrollment not found")
        return enrollment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/enrollments/{enrollment_id}/consent", response_model=EnrollmentResponse)
async def record_consent(
    enrollment_id: UUID,
    consent_date: date = Body(...),
    consent_document_id: Optional[UUID] = Body(None),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Record patient consent."""
    enrollment = await enrollment_service.record_consent(
        db, enrollment_id, tenant_id, consent_date, consent_document_id
    )
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return enrollment


@router.post("/enrollments/{enrollment_id}/discharge", response_model=EnrollmentResponse)
async def discharge_enrollment(
    enrollment_id: UUID,
    reason: str = Body(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Discharge patient from RPM program."""
    enrollment = await enrollment_service.discharge_enrollment(
        db, enrollment_id, tenant_id, reason
    )
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    return enrollment


# =============================================================================
# BILLING ENDPOINTS
# =============================================================================

@router.get("/enrollments/{enrollment_id}/monitoring-period", response_model=MonitoringPeriodResponse)
async def get_current_monitoring_period(
    enrollment_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get current monitoring period for enrollment."""
    period = await billing_service.get_current_period(db, tenant_id, enrollment_id)
    if not period:
        raise HTTPException(status_code=404, detail="No monitoring period found")
    return period


@router.post("/billing/time-entries", response_model=ClinicalTimeEntryResponse, status_code=201)
async def log_clinical_time(
    entry_data: ClinicalTimeEntryCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Log clinical time for billing."""
    try:
        entry = await billing_service.log_clinical_time(
            db, tenant_id, user_id, entry_data
        )
        return entry
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/billing/time-entries", response_model=List[ClinicalTimeEntryResponse])
async def get_time_entries(
    enrollment_id: Optional[UUID] = None,
    period_id: Optional[UUID] = None,
    provider_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get clinical time entries."""
    entries = await billing_service.get_time_entries(
        db, tenant_id, enrollment_id, period_id, provider_id, start_date, end_date
    )
    return entries


@router.post("/billing/generate", response_model=List[BillingEventResponse])
async def generate_billing_events(
    period_month: int = Query(..., description="Period month in YYYYMM format"),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Generate billing events for a period."""
    events = await billing_service.generate_billing_events(
        db, tenant_id, period_month
    )
    return events


@router.get("/billing/events", response_model=PaginatedResponse)
async def get_billing_events(
    enrollment_id: Optional[UUID] = None,
    patient_id: Optional[UUID] = None,
    cpt_code: Optional[BillingCodeType] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get billing events."""
    events, total = await billing_service.get_billing_events(
        db, tenant_id, enrollment_id, patient_id, cpt_code, status,
        start_date, end_date, skip, limit
    )
    return PaginatedResponse(
        items=[BillingEventResponse.from_orm(e) for e in events],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/billing/summary", response_model=BillingSummary)
async def get_billing_summary(
    period_month: int = Query(..., description="Period month in YYYYMM format"),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get billing summary for a period."""
    summary = await billing_service.get_billing_summary(db, tenant_id, period_month)
    return summary


# =============================================================================
# ENGAGEMENT ENDPOINTS
# =============================================================================

# Reminders
@router.post("/reminders", response_model=PatientReminderResponse, status_code=201)
async def create_reminder(
    reminder_data: PatientReminderCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Create a patient reminder."""
    reminder = await engagement_service.create_reminder(db, tenant_id, reminder_data)
    return reminder


@router.get("/patients/{patient_id}/reminders", response_model=List[PatientReminderResponse])
async def get_patient_reminders(
    patient_id: UUID,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get reminders for a patient."""
    reminders = await engagement_service.get_patient_reminders(
        db, tenant_id, patient_id, active_only
    )
    return reminders


@router.patch("/reminders/{reminder_id}", response_model=PatientReminderResponse)
async def update_reminder(
    reminder_id: UUID,
    update_data: PatientReminderUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Update a reminder."""
    reminder = await engagement_service.update_reminder(
        db, reminder_id, tenant_id, update_data
    )
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return reminder


# Goals
@router.post("/goals", response_model=PatientGoalResponse, status_code=201)
async def create_goal(
    goal_data: PatientGoalCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Create a patient goal."""
    goal = await engagement_service.create_goal(
        db, tenant_id, user_id, "provider", goal_data
    )
    return goal


@router.get("/patients/{patient_id}/goals", response_model=List[PatientGoalResponse])
async def get_patient_goals(
    patient_id: UUID,
    reading_type: Optional[ReadingType] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get goals for a patient."""
    goals = await engagement_service.get_patient_goals(
        db, tenant_id, patient_id, reading_type, active_only
    )
    return goals


@router.patch("/goals/{goal_id}", response_model=PatientGoalResponse)
async def update_goal(
    goal_id: UUID,
    update_data: PatientGoalUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Update a goal."""
    goal = await engagement_service.update_goal(db, goal_id, tenant_id, update_data)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


# Educational Content
@router.post("/content", response_model=EducationalContentResponse, status_code=201)
async def create_content(
    content_data: EducationalContentCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Create educational content."""
    content = await engagement_service.create_content(
        db, tenant_id, user_id, content_data
    )
    return content


@router.get("/content", response_model=PaginatedResponse)
async def list_content(
    condition: Optional[str] = None,
    content_type: Optional[str] = None,
    featured_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """List educational content."""
    content, total = await engagement_service.list_content(
        db, tenant_id, condition, content_type, featured_only, skip, limit
    )
    return PaginatedResponse(
        items=[EducationalContentResponse.from_orm(c) for c in content],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        pages=(total + limit - 1) // limit
    )


@router.get("/patients/{patient_id}/recommended-content", response_model=List[EducationalContentResponse])
async def get_recommended_content(
    patient_id: UUID,
    condition: Optional[str] = None,
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get recommended content for a patient."""
    content = await engagement_service.get_recommended_content(
        db, tenant_id, patient_id, condition, limit
    )
    return content


@router.post("/content/{content_id}/engagement")
async def record_content_engagement(
    content_id: UUID,
    engagement_data: ContentEngagementCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Record content engagement."""
    engagement_data.content_id = content_id
    engagement = await engagement_service.record_engagement(
        db, tenant_id, user_id, engagement_data
    )
    return {"success": True}


# =============================================================================
# ANALYTICS ENDPOINTS
# =============================================================================

@router.get("/patients/{patient_id}/trends/{reading_type}", response_model=TrendAnalysisResponse)
async def get_patient_trend(
    patient_id: UUID,
    reading_type: ReadingType,
    period_days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get trend analysis for a patient."""
    trend = await analytics_service.analyze_patient_trends(
        db, tenant_id, patient_id, reading_type, period_days
    )
    return trend


@router.get("/analytics/population", response_model=PopulationMetricsResponse)
async def get_population_metrics(
    metric_date: date = Query(default=None),
    condition: Optional[str] = None,
    reading_type: Optional[ReadingType] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get population health metrics."""
    if not metric_date:
        metric_date = date.today()

    metrics = await analytics_service.calculate_population_metrics(
        db, tenant_id, metric_date, condition, reading_type
    )
    return metrics


@router.get("/patients/{patient_id}/data-quality", response_model=List[DataQualityResponse])
async def get_data_quality(
    patient_id: UUID,
    start_date: date,
    end_date: date,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get data quality metrics for a patient."""
    metrics = await analytics_service.get_data_quality(
        db, tenant_id, patient_id, start_date, end_date
    )
    return metrics


# =============================================================================
# WEBHOOK ENDPOINTS (Third-party integrations)
# =============================================================================

@router.post("/webhooks/withings")
async def withings_webhook(
    payload: WithingsWebhookPayload,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Handle Withings webhook notifications."""
    readings = await integration_service.handle_withings_webhook(
        db, tenant_id, payload
    )
    return {"processed": len(readings)}


@router.post("/integrations/apple-health")
async def process_apple_health(
    payload: AppleHealthExportPayload,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Process Apple Health data export."""
    readings = await integration_service.process_apple_health_export(
        db, tenant_id, payload
    )
    return {"processed": len(readings)}


@router.post("/integrations/google-fit")
async def process_google_fit(
    payload: GoogleFitDataPayload,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Process Google Fit data."""
    readings = await integration_service.process_google_fit_data(
        db, tenant_id, payload
    )
    return {"processed": len(readings)}


@router.get("/integrations/{patient_id}/status")
async def get_integration_status(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get integration status for a patient."""
    status = await integration_service.get_integration_status(
        db, tenant_id, patient_id
    )
    return status


# =============================================================================
# DASHBOARD ENDPOINTS
# =============================================================================

@router.get("/dashboard/patient/{patient_id}", response_model=PatientRPMDashboard)
async def get_patient_dashboard(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get patient RPM dashboard data."""
    # Aggregate data from multiple services
    enrollment = await enrollment_service.get_patient_enrollment(
        db, tenant_id, patient_id
    )
    devices = await device_service.get_patient_assignments(
        db, tenant_id, patient_id, active_only=True
    )
    readings = await reading_service.get_patient_readings(
        db, tenant_id, patient_id, limit=20
    )
    alerts = await alert_service.get_active_alerts(db, tenant_id, patient_id)
    goals = await engagement_service.get_patient_goals(
        db, tenant_id, patient_id, active_only=True
    )
    content = await engagement_service.get_recommended_content(
        db, tenant_id, patient_id, limit=3
    )

    # Calculate compliance (simplified)
    compliance_rate = 0.0
    days_with_readings = 0
    if enrollment:
        period = await billing_service.get_current_period(
            db, tenant_id, enrollment.id
        )
        if period:
            days_with_readings = period.days_with_readings
            compliance_rate = period.days_with_readings / 30 * 100

    return PatientRPMDashboard(
        patient_id=patient_id,
        enrollment=EnrollmentResponse.from_orm(enrollment) if enrollment else None,
        active_devices=[DeviceAssignmentResponse.from_orm(d) for d in devices],
        recent_readings=[ReadingResponse.from_orm(r) for r in readings],
        active_alerts=[AlertResponse.from_orm(a) for a in alerts],
        goals=[PatientGoalResponse.from_orm(g) for g in goals],
        compliance_rate=compliance_rate,
        days_with_readings_this_month=days_with_readings,
        next_reminder=None,
        trend_summary={},
        recommended_content=[EducationalContentResponse.from_orm(c) for c in content]
    )


@router.get("/dashboard/provider", response_model=ProviderRPMDashboard)
async def get_provider_dashboard(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """Get provider RPM dashboard data."""
    # Get enrollment statistics
    stats = await enrollment_service.get_enrollment_statistics(db, tenant_id)

    # Get critical alerts
    critical_alerts = await alert_service.get_active_alerts(db, tenant_id)
    critical_alerts = [a for a in critical_alerts if a.severity == AlertSeverity.CRITICAL][:10]

    # Get pending executions
    pending = await protocol_service.get_pending_executions(db, tenant_id)

    # Get billing eligibility
    today = date.today()
    period_month = today.year * 100 + today.month
    billing_summary = await billing_service.get_billing_summary(
        db, tenant_id, period_month
    )

    return ProviderRPMDashboard(
        total_enrolled_patients=stats.get("total_enrollments", 0),
        active_patients=stats.get("active_count", 0),
        patients_needing_attention=len(await enrollment_service.get_patients_needing_attention(
            db, tenant_id, days_threshold=3
        )),
        critical_alerts=[AlertResponse.from_orm(a) for a in critical_alerts],
        pending_approvals=len([e for e in pending if e.status == "pending_approval"]),
        billing_eligible_this_month={
            "99453": billing_summary.patients_eligible_99453,
            "99454": billing_summary.patients_eligible_99454,
            "99457": billing_summary.patients_eligible_99457,
            "99458": billing_summary.patients_eligible_99458
        },
        compliance_overview=stats.get("by_condition", {}),
        recent_readings_count=0,
        protocol_executions_pending=len(pending)
    )


@router.get("/dashboard/program", response_model=RPMProgramMetrics)
async def get_program_metrics(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id)
):
    """Get overall RPM program metrics."""
    stats = await enrollment_service.get_enrollment_statistics(db, tenant_id)

    today = date.today()
    period_month = today.year * 100 + today.month
    billing_summary = await billing_service.get_billing_summary(
        db, tenant_id, period_month
    )

    # Get device counts
    devices, total_devices = await device_service.list_devices(
        db, tenant_id, limit=1
    )
    active_devices, _ = await device_service.list_devices(
        db, tenant_id, status=DeviceStatus.ACTIVE, limit=1
    )

    # Get alert statistics
    alert_stats = await alert_service.get_alert_statistics(
        db, tenant_id,
        datetime.combine(today, datetime.min.time()),
        datetime.combine(today, datetime.max.time())
    )

    return RPMProgramMetrics(
        total_enrollments=stats.get("total_enrollments", 0),
        active_enrollments=stats.get("active_count", 0),
        total_devices=total_devices,
        active_devices=len(active_devices) if active_devices else 0,
        readings_today=0,
        readings_this_month=0,
        alerts_triggered_today=alert_stats.get("total_alerts", 0),
        alerts_resolved_today=alert_stats.get("by_status", {}).get("resolved", 0),
        avg_compliance_rate=0.0,
        billing_summary=billing_summary,
        condition_breakdown=stats.get("by_condition", {}),
        top_performing_protocols=[]
    )

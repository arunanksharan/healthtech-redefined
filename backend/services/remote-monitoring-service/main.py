"""
Remote Monitoring Service
FastAPI service for home health device management and remote patient monitoring
Port: 8022
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID
import json

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, and_, or_, func
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import IntegrityError

from shared.database.models import (
    RemoteDevice,
    DeviceBinding,
    RemoteMeasurement,
    RemoteAlert,
    Patient,
    User,
    Tenant
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    RemoteDeviceCreate,
    RemoteDeviceUpdate,
    RemoteDeviceResponse,
    RemoteDeviceListResponse,
    DeviceBindingCreate,
    DeviceBindingUpdate,
    DeviceBindingResponse,
    DeviceBindingListResponse,
    RemoteMeasurementCreate,
    RemoteMeasurementResponse,
    RemoteMeasurementListResponse,
    RemoteAlertResponse,
    RemoteAlertListResponse,
    RemoteAlertAcknowledge,
    RemoteAlertResolve,
    PatientMonitoringDashboard,
    PatientMeasurementSummary
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# FastAPI app
app = FastAPI(
    title="Remote Monitoring Service",
    description="Home health device management and remote patient monitoring",
    version="0.1.0"
)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== Remote Device Endpoints ====================

@app.post(
    "/api/v1/remote/devices",
    response_model=RemoteDeviceResponse,
    status_code=201,
    tags=["Remote Devices"]
)
async def register_device(
    device_data: RemoteDeviceCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Register a new remote monitoring device.

    - **device_type**: BP_CUFF, GLUCOMETER, CGM, PULSE_OXIMETER, etc.
    - **device_identifier**: Unique device serial number
    """
    # Check if device identifier already exists
    existing = db.query(RemoteDevice).filter(
        and_(
            RemoteDevice.tenant_id == device_data.tenant_id,
            RemoteDevice.device_identifier == device_data.device_identifier
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Device with identifier '{device_data.device_identifier}' already registered"
        )

    # Create device
    device = RemoteDevice(
        tenant_id=device_data.tenant_id,
        device_type=device_data.device_type,
        manufacturer=device_data.manufacturer,
        model_name=device_data.model_name,
        device_identifier=device_data.device_identifier,
        vendor_system_id=device_data.vendor_system_id,
        calibration_date=device_data.calibration_date,
        firmware_version=device_data.firmware_version,
        metadata=device_data.metadata
    )

    db.add(device)

    try:
        db.commit()
        db.refresh(device)

        # Publish event
        await publish_event(
            EventType.REMOTE_DEVICE_REGISTERED,
            {
                "device_id": str(device.id),
                "device_type": device.device_type,
                "manufacturer": device.manufacturer,
                "device_identifier": device.device_identifier
            }
        )

        logger.info(f"Remote device registered: {device.device_identifier}")
        return device

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")


@app.get(
    "/api/v1/remote/devices",
    response_model=RemoteDeviceListResponse,
    tags=["Remote Devices"]
)
async def list_devices(
    tenant_id: Optional[UUID] = Query(None),
    device_type: Optional[str] = Query(None),
    manufacturer: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List remote devices with filtering."""
    query = db.query(RemoteDevice)

    if tenant_id:
        query = query.filter(RemoteDevice.tenant_id == tenant_id)

    if device_type:
        query = query.filter(RemoteDevice.device_type == device_type.upper())

    if manufacturer:
        query = query.filter(RemoteDevice.manufacturer.ilike(f"%{manufacturer}%"))

    total = query.count()
    offset = (page - 1) * page_size
    devices = query.order_by(RemoteDevice.created_at.desc()).offset(offset).limit(page_size).all()

    return RemoteDeviceListResponse(
        total=total,
        devices=devices,
        page=page,
        page_size=page_size,
        has_next=offset + page_size < total,
        has_previous=page > 1
    )


@app.get(
    "/api/v1/remote/devices/{device_id}",
    response_model=RemoteDeviceResponse,
    tags=["Remote Devices"]
)
async def get_device(
    device_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a remote device by ID."""
    device = db.query(RemoteDevice).filter(RemoteDevice.id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return device


@app.patch(
    "/api/v1/remote/devices/{device_id}",
    response_model=RemoteDeviceResponse,
    tags=["Remote Devices"]
)
async def update_device(
    device_id: UUID,
    update_data: RemoteDeviceUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Update device calibration, firmware, or metadata."""
    device = db.query(RemoteDevice).filter(RemoteDevice.id == device_id).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(device, field, value)

    device.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(device)

    logger.info(f"Device updated: {device.device_identifier}")
    return device


# ==================== Device Binding Endpoints ====================

@app.post(
    "/api/v1/remote/bindings",
    response_model=DeviceBindingResponse,
    status_code=201,
    tags=["Device Bindings"]
)
async def bind_device_to_patient(
    binding_data: DeviceBindingCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Bind a remote device to a patient for monitoring.

    - **care_program_code**: HF_HOME_MONITORING, DM2_REMOTE, etc.
    - **alert_thresholds**: Automated alert thresholds
    """
    # Validate device exists
    device = db.query(RemoteDevice).filter(
        RemoteDevice.id == binding_data.remote_device_id
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Validate patient exists
    patient = db.query(Patient).filter(Patient.id == binding_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Check if device is already actively bound
    existing_binding = db.query(DeviceBinding).filter(
        and_(
            DeviceBinding.remote_device_id == binding_data.remote_device_id,
            DeviceBinding.binding_status == "active"
        )
    ).first()

    if existing_binding:
        raise HTTPException(
            status_code=400,
            detail=f"Device is already actively bound to patient {existing_binding.patient_id}"
        )

    # Create binding
    binding = DeviceBinding(
        remote_device_id=binding_data.remote_device_id,
        patient_id=binding_data.patient_id,
        care_program_code=binding_data.care_program_code,
        measurement_frequency=binding_data.measurement_frequency,
        alert_thresholds=binding_data.alert_thresholds,
        binding_status="active",
        bound_at=datetime.utcnow(),
        notes=binding_data.notes
    )

    db.add(binding)
    db.commit()
    db.refresh(binding)

    # Publish event
    await publish_event(
        EventType.DEVICE_BOUND,
        {
            "binding_id": str(binding.id),
            "device_id": str(device.id),
            "device_type": device.device_type,
            "patient_id": str(binding.patient_id),
            "care_program": binding.care_program_code
        }
    )

    logger.info(f"Device bound: {device.device_identifier} to patient {binding.patient_id}")
    return binding


@app.get(
    "/api/v1/remote/bindings",
    response_model=DeviceBindingListResponse,
    tags=["Device Bindings"]
)
async def list_bindings(
    patient_id: Optional[UUID] = Query(None),
    device_id: Optional[UUID] = Query(None),
    binding_status: Optional[str] = Query(None),
    care_program_code: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List device bindings with filtering."""
    query = db.query(DeviceBinding)

    if patient_id:
        query = query.filter(DeviceBinding.patient_id == patient_id)

    if device_id:
        query = query.filter(DeviceBinding.remote_device_id == device_id)

    if binding_status:
        query = query.filter(DeviceBinding.binding_status == binding_status.lower())

    if care_program_code:
        query = query.filter(DeviceBinding.care_program_code == care_program_code)

    total = query.count()
    offset = (page - 1) * page_size
    bindings = query.order_by(DeviceBinding.bound_at.desc()).offset(offset).limit(page_size).all()

    return DeviceBindingListResponse(
        total=total,
        bindings=bindings,
        page=page,
        page_size=page_size,
        has_next=offset + page_size < total,
        has_previous=page > 1
    )


@app.get(
    "/api/v1/remote/bindings/{binding_id}",
    response_model=DeviceBindingResponse,
    tags=["Device Bindings"]
)
async def get_binding(
    binding_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a device binding by ID."""
    binding = db.query(DeviceBinding).filter(DeviceBinding.id == binding_id).first()

    if not binding:
        raise HTTPException(status_code=404, detail="Device binding not found")

    return binding


@app.patch(
    "/api/v1/remote/bindings/{binding_id}",
    response_model=DeviceBindingResponse,
    tags=["Device Bindings"]
)
async def update_binding(
    binding_id: UUID,
    update_data: DeviceBindingUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Update device binding (thresholds, frequency, status)."""
    binding = db.query(DeviceBinding).filter(DeviceBinding.id == binding_id).first()

    if not binding:
        raise HTTPException(status_code=404, detail="Device binding not found")

    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(binding, field, value)

    binding.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(binding)

    logger.info(f"Device binding updated: {binding_id}")
    return binding


@app.post(
    "/api/v1/remote/bindings/{binding_id}/unbind",
    response_model=DeviceBindingResponse,
    tags=["Device Bindings"]
)
async def unbind_device(
    binding_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Unbind a device from a patient."""
    binding = db.query(DeviceBinding).filter(DeviceBinding.id == binding_id).first()

    if not binding:
        raise HTTPException(status_code=404, detail="Device binding not found")

    if binding.binding_status == "discontinued":
        raise HTTPException(status_code=400, detail="Device binding already discontinued")

    binding.binding_status = "discontinued"
    binding.unbound_at = datetime.utcnow()
    binding.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(binding)

    # Publish event
    await publish_event(
        EventType.DEVICE_UNBOUND,
        {
            "binding_id": str(binding.id),
            "patient_id": str(binding.patient_id),
            "device_id": str(binding.remote_device_id)
        }
    )

    logger.info(f"Device unbound: {binding_id}")
    return binding


# ==================== Remote Measurement Endpoints ====================

@app.post(
    "/api/v1/remote/measurements",
    response_model=RemoteMeasurementResponse,
    status_code=201,
    tags=["Measurements"]
)
async def ingest_measurement(
    measurement_data: RemoteMeasurementCreate,
    db: Session = Depends(get_db)
):
    """
    Ingest a measurement from a remote device.

    Automatically evaluates alert thresholds and creates FHIR Observation.
    """
    # Validate binding exists and is active
    binding = db.query(DeviceBinding).filter(
        DeviceBinding.id == measurement_data.device_binding_id
    ).first()

    if not binding:
        raise HTTPException(status_code=404, detail="Device binding not found")

    if binding.binding_status != "active":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot ingest measurement for binding in '{binding.binding_status}' status"
        )

    # Create measurement
    measurement = RemoteMeasurement(
        device_binding_id=measurement_data.device_binding_id,
        measurement_type=measurement_data.measurement_type,
        measured_at=measurement_data.measured_at,
        payload=measurement_data.payload,
        device_metadata=measurement_data.device_metadata,
        ingested_at=datetime.utcnow()
    )

    db.add(measurement)
    db.commit()
    db.refresh(measurement)

    # Create FHIR Observation
    fhir_observation = create_fhir_observation(measurement, binding)
    measurement.fhir_observation_id = fhir_observation.get("id")
    db.commit()

    # Evaluate alert thresholds
    alerts = await evaluate_alert_thresholds(measurement, binding, db)

    # Publish event
    await publish_event(
        EventType.REMOTE_MEASUREMENT_INGESTED,
        {
            "measurement_id": str(measurement.id),
            "patient_id": str(binding.patient_id),
            "device_binding_id": str(binding.id),
            "measurement_type": measurement.measurement_type,
            "measured_at": measurement.measured_at.isoformat(),
            "alerts_triggered": len(alerts)
        }
    )

    logger.info(
        f"Measurement ingested: {measurement.measurement_type} for patient {binding.patient_id}, "
        f"{len(alerts)} alerts triggered"
    )
    return measurement


@app.get(
    "/api/v1/remote/measurements",
    response_model=RemoteMeasurementListResponse,
    tags=["Measurements"]
)
async def list_measurements(
    device_binding_id: Optional[UUID] = Query(None),
    patient_id: Optional[UUID] = Query(None),
    measurement_type: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List remote measurements with filtering."""
    query = db.query(RemoteMeasurement)

    if device_binding_id:
        query = query.filter(RemoteMeasurement.device_binding_id == device_binding_id)

    if patient_id:
        # Join with DeviceBinding to filter by patient
        query = query.join(DeviceBinding).filter(DeviceBinding.patient_id == patient_id)

    if measurement_type:
        query = query.filter(RemoteMeasurement.measurement_type == measurement_type.upper())

    if from_date:
        query = query.filter(RemoteMeasurement.measured_at >= from_date)

    if to_date:
        query = query.filter(RemoteMeasurement.measured_at <= to_date)

    total = query.count()
    offset = (page - 1) * page_size
    measurements = query.order_by(
        RemoteMeasurement.measured_at.desc()
    ).offset(offset).limit(page_size).all()

    return RemoteMeasurementListResponse(
        total=total,
        measurements=measurements,
        page=page,
        page_size=page_size,
        has_next=offset + page_size < total,
        has_previous=page > 1
    )


# ==================== Remote Alert Endpoints ====================

@app.get(
    "/api/v1/remote/alerts",
    response_model=RemoteAlertListResponse,
    tags=["Alerts"]
)
async def list_alerts(
    patient_id: Optional[UUID] = Query(None),
    device_binding_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None, description="open, acknowledged, resolved"),
    severity: Optional[str] = Query(None, description="info, warning, critical"),
    from_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List remote monitoring alerts with filtering."""
    query = db.query(RemoteAlert)

    if device_binding_id:
        query = query.filter(RemoteAlert.device_binding_id == device_binding_id)

    if patient_id:
        # Join with DeviceBinding
        query = query.join(DeviceBinding).filter(DeviceBinding.patient_id == patient_id)

    if status:
        query = query.filter(RemoteAlert.status == status.lower())

    if severity:
        query = query.filter(RemoteAlert.severity == severity.lower())

    if from_date:
        query = query.filter(RemoteAlert.triggered_at >= from_date)

    total = query.count()
    offset = (page - 1) * page_size
    alerts = query.order_by(
        RemoteAlert.triggered_at.desc()
    ).offset(offset).limit(page_size).all()

    return RemoteAlertListResponse(
        total=total,
        alerts=alerts,
        page=page,
        page_size=page_size,
        has_next=offset + page_size < total,
        has_previous=page > 1
    )


@app.post(
    "/api/v1/remote/alerts/{alert_id}/acknowledge",
    response_model=RemoteAlertResponse,
    tags=["Alerts"]
)
async def acknowledge_alert(
    alert_id: UUID,
    ack_data: RemoteAlertAcknowledge,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Acknowledge a remote monitoring alert."""
    alert = db.query(RemoteAlert).filter(RemoteAlert.id == alert_id).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if alert.status != "open":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot acknowledge alert in '{alert.status}' status"
        )

    alert.status = "acknowledged"
    alert.acknowledged_at = datetime.utcnow()
    alert.acknowledged_by_user_id = current_user_id
    if ack_data.notes:
        alert.resolution_notes = ack_data.notes

    db.commit()
    db.refresh(alert)

    logger.info(f"Alert acknowledged: {alert_id} by user {current_user_id}")
    return alert


@app.post(
    "/api/v1/remote/alerts/{alert_id}/resolve",
    response_model=RemoteAlertResponse,
    tags=["Alerts"]
)
async def resolve_alert(
    alert_id: UUID,
    resolve_data: RemoteAlertResolve,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Resolve a remote monitoring alert with resolution notes."""
    alert = db.query(RemoteAlert).filter(RemoteAlert.id == alert_id).first()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if alert.status == "resolved":
        raise HTTPException(status_code=400, detail="Alert already resolved")

    alert.status = "resolved"
    alert.resolved_at = datetime.utcnow()
    alert.resolution_notes = resolve_data.resolution_notes
    alert.linked_task_id = resolve_data.linked_task_id

    db.commit()
    db.refresh(alert)

    # Publish event
    await publish_event(
        EventType.REMOTE_ALERT_RESOLVED,
        {
            "alert_id": str(alert.id),
            "severity": alert.severity,
            "resolved_at": alert.resolved_at.isoformat()
        }
    )

    logger.info(f"Alert resolved: {alert_id}")
    return alert


# ==================== Analytics/Dashboard Endpoints ====================

@app.get(
    "/api/v1/remote/patients/{patient_id}/dashboard",
    response_model=PatientMonitoringDashboard,
    tags=["Analytics"]
)
async def get_patient_dashboard(
    patient_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive monitoring dashboard for a patient.

    Includes active devices, recent measurements, active alerts, and adherence.
    """
    # Validate patient
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Get active device bindings
    active_bindings = db.query(DeviceBinding).filter(
        and_(
            DeviceBinding.patient_id == patient_id,
            DeviceBinding.binding_status == "active"
        )
    ).all()

    # Get recent measurements (last 7 days)
    recent_cutoff = datetime.utcnow() - timedelta(days=7)
    recent_measurements = db.query(RemoteMeasurement).join(DeviceBinding).filter(
        and_(
            DeviceBinding.patient_id == patient_id,
            RemoteMeasurement.measured_at >= recent_cutoff
        )
    ).order_by(RemoteMeasurement.measured_at.desc()).limit(50).all()

    # Get active alerts
    active_alerts = db.query(RemoteAlert).join(DeviceBinding).filter(
        and_(
            DeviceBinding.patient_id == patient_id,
            RemoteAlert.status.in_(["open", "acknowledged"])
        )
    ).order_by(RemoteAlert.triggered_at.desc()).all()

    # Build measurement summaries
    measurement_summaries = []
    for binding in active_bindings:
        # Get measurements for this binding
        measurements = db.query(RemoteMeasurement).filter(
            RemoteMeasurement.device_binding_id == binding.id
        ).order_by(RemoteMeasurement.measured_at.desc()).limit(30).all()

        if measurements:
            latest = measurements[0]
            summary = PatientMeasurementSummary(
                patient_id=patient_id,
                device_binding_id=binding.id,
                measurement_type=latest.measurement_type,
                total_measurements=len(measurements),
                latest_measurement=latest,
                date_range={
                    "first": measurements[-1].measured_at,
                    "last": latest.measured_at
                },
                statistics=calculate_measurement_statistics(measurements)
            )
            measurement_summaries.append(summary)

    # Calculate adherence score
    adherence_score = calculate_adherence_score(active_bindings, recent_measurements)

    return PatientMonitoringDashboard(
        patient_id=patient_id,
        active_devices=active_bindings,
        recent_measurements=recent_measurements[:10],
        active_alerts=active_alerts,
        measurement_summaries=measurement_summaries,
        adherence_score=adherence_score
    )


# ==================== Helper Functions ====================

async def evaluate_alert_thresholds(
    measurement: RemoteMeasurement,
    binding: DeviceBinding,
    db: Session
) -> List[RemoteAlert]:
    """
    Evaluate measurement against alert thresholds.
    Create alerts for violations.
    """
    alerts = []

    if not binding.alert_thresholds:
        return alerts

    thresholds = binding.alert_thresholds
    payload = measurement.payload

    # Check BP thresholds
    if measurement.measurement_type == "BP":
        if "systolic_bp" in thresholds and "systolic" in payload:
            systolic = payload["systolic"]
            sys_threshold = thresholds["systolic_bp"]

            if systolic > sys_threshold.get("max", 999):
                alert = create_alert(
                    binding,
                    measurement,
                    "threshold",
                    "warning",
                    "High Systolic BP",
                    f"Systolic BP {systolic} exceeds threshold {sys_threshold['max']}",
                    {"systolic": systolic, "threshold": sys_threshold["max"]},
                    db
                )
                alerts.append(alert)

            elif systolic < sys_threshold.get("min", 0):
                alert = create_alert(
                    binding,
                    measurement,
                    "threshold",
                    "warning",
                    "Low Systolic BP",
                    f"Systolic BP {systolic} below threshold {sys_threshold['min']}",
                    {"systolic": systolic, "threshold": sys_threshold["min"]},
                    db
                )
                alerts.append(alert)

    # Check glucose thresholds
    elif measurement.measurement_type == "GLUCOSE":
        if "glucose" in thresholds and "value" in payload:
            glucose = payload["value"]
            glucose_threshold = thresholds["glucose"]

            if glucose > glucose_threshold.get("max", 999):
                alert = create_alert(
                    binding,
                    measurement,
                    "threshold",
                    "critical" if glucose > 300 else "warning",
                    "High Blood Glucose",
                    f"Blood glucose {glucose} exceeds threshold {glucose_threshold['max']}",
                    {"glucose": glucose, "threshold": glucose_threshold["max"]},
                    db
                )
                alerts.append(alert)

    # Check weight changes
    elif measurement.measurement_type == "WEIGHT":
        # Get previous weight
        prev_measurement = db.query(RemoteMeasurement).filter(
            and_(
                RemoteMeasurement.device_binding_id == binding.id,
                RemoteMeasurement.measurement_type == "WEIGHT",
                RemoteMeasurement.id != measurement.id
            )
        ).order_by(RemoteMeasurement.measured_at.desc()).first()

        if prev_measurement and "rapid_weight_gain" in thresholds:
            current_weight = payload.get("value", 0)
            prev_weight = prev_measurement.payload.get("value", 0)
            weight_change = current_weight - prev_weight

            threshold_kg = thresholds["rapid_weight_gain"].get("threshold_kg", 2)
            if weight_change > threshold_kg:
                alert = create_alert(
                    binding,
                    measurement,
                    "trend",
                    "warning",
                    "Rapid Weight Gain",
                    f"Weight increased by {weight_change:.1f} kg",
                    {"current": current_weight, "previous": prev_weight, "change": weight_change},
                    db
                )
                alerts.append(alert)

    return alerts


def create_alert(
    binding: DeviceBinding,
    measurement: RemoteMeasurement,
    alert_type: str,
    severity: str,
    title: str,
    description: str,
    alert_data: dict,
    db: Session
) -> RemoteAlert:
    """Create and persist a remote alert."""
    alert = RemoteAlert(
        device_binding_id=binding.id,
        measurement_id=measurement.id,
        alert_type=alert_type,
        severity=severity,
        title=title,
        description=description,
        alert_data=alert_data,
        status="open",
        triggered_at=datetime.utcnow()
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    logger.warning(f"Alert created: {title} for patient {binding.patient_id}")
    return alert


def create_fhir_observation(measurement: RemoteMeasurement, binding: DeviceBinding) -> dict:
    """Create FHIR R4 Observation for measurement."""
    # Build LOINC code based on measurement type
    loinc_codes = {
        "BP": "85354-9",  # Blood pressure panel
        "GLUCOSE": "2339-0",  # Glucose
        "WEIGHT": "29463-7",  # Body weight
        "SPO2": "59408-5",  # Oxygen saturation
        "HR": "8867-4",  # Heart rate
        "TEMP": "8310-5"  # Body temperature
    }

    fhir_obs = {
        "resourceType": "Observation",
        "id": f"remote-{measurement.id}",
        "status": "final",
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": "vital-signs"
            }]
        }],
        "code": {
            "coding": [{
                "system": "http://loinc.org",
                "code": loinc_codes.get(measurement.measurement_type, "unknown")
            }],
            "text": measurement.measurement_type
        },
        "subject": {
            "reference": f"Patient/{binding.patient_id}"
        },
        "effectiveDateTime": measurement.measured_at.isoformat(),
        "issued": measurement.ingested_at.isoformat(),
        "valueQuantity": measurement.payload,
        "device": {
            "reference": f"Device/{binding.remote_device_id}"
        }
    }

    # TODO: POST to FHIR service
    return {"id": f"Observation-{measurement.id}"}


def calculate_measurement_statistics(measurements: List[RemoteMeasurement]) -> dict:
    """Calculate statistics for measurements."""
    if not measurements:
        return {}

    # For BP measurements
    if measurements[0].measurement_type == "BP":
        systolic_values = [m.payload.get("systolic", 0) for m in measurements if "systolic" in m.payload]
        diastolic_values = [m.payload.get("diastolic", 0) for m in measurements if "diastolic" in m.payload]

        return {
            "systolic": {
                "min": min(systolic_values) if systolic_values else 0,
                "max": max(systolic_values) if systolic_values else 0,
                "avg": sum(systolic_values) / len(systolic_values) if systolic_values else 0
            },
            "diastolic": {
                "min": min(diastolic_values) if diastolic_values else 0,
                "max": max(diastolic_values) if diastolic_values else 0,
                "avg": sum(diastolic_values) / len(diastolic_values) if diastolic_values else 0
            }
        }

    # For other measurements with single value
    values = [m.payload.get("value", 0) for m in measurements if "value" in m.payload]
    if values:
        return {
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values)
        }

    return {}


def calculate_adherence_score(
    bindings: List[DeviceBinding],
    recent_measurements: List[RemoteMeasurement]
) -> float:
    """
    Calculate adherence score (0-100) based on expected vs actual measurements.
    """
    if not bindings:
        return 0.0

    total_expected = 0
    total_actual = len(recent_measurements)

    # Calculate expected measurements based on frequency
    frequency_map = {
        "daily": 7,  # 7 in last week
        "twice_daily": 14,
        "weekly": 1
    }

    for binding in bindings:
        freq = binding.measurement_frequency or "daily"
        total_expected += frequency_map.get(freq, 7)

    if total_expected == 0:
        return 100.0

    score = (total_actual / total_expected) * 100
    return min(100.0, score)


# Health check
@app.get("/health", tags=["System"])
async def health_check():
    """Service health check endpoint."""
    return {
        "service": "remote-monitoring-service",
        "status": "healthy",
        "version": "0.1.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8022)

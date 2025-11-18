"""
Ops Command Center API Service - Port 8073
Provides unified API for operational snapshots and command center views
Real-time operational layer for integrated clinical + financial command
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, desc, and_, or_
from sqlalchemy.orm import Session, sessionmaker, joinedload

from shared.database.models import (
    HospitalUnit, UnitSnapshot, BedSnapshot, ORStatusSnapshot, EDStatusSnapshot,
    LabWorkloadSnapshot, ImagingWorkloadSnapshot, RCMWorkloadSnapshot,
    OpsAlert, OpsAlertRule, OpsPlaybook, OpsPlaybookStep, OpsKPI
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    HospitalOverviewResponse, RCMStatusResponse, TopAlert,
    UnitSnapshotResponse, BedSnapshotResponse, ORStatusSnapshotResponse,
    EDStatusSnapshotResponse, LabWorkloadSnapshotResponse, ImagingWorkloadSnapshotResponse,
    RCMWorkloadSnapshotResponse, OpsAlertResponse, OpsAlertUpdateRequest,
    OpsPlaybookResponse, OpsPlaybookStepResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Ops Command Center API Service", version="0.1.0")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Hospital Overview Endpoint
@app.get("/api/v1/ops/overview", response_model=HospitalOverviewResponse, tags=["Overview"])
async def get_hospital_overview(
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """
    Get complete hospital operational overview snapshot
    Includes occupancy, ED crowding, OR utilization, lab/imaging backlogs, RCM status, and top alerts
    """
    current_time = datetime.utcnow()

    # Get latest unit snapshots for overall occupancy
    ward_snapshots = db.query(UnitSnapshot).join(HospitalUnit).filter(
        HospitalUnit.tenant_id == tenant_id,
        HospitalUnit.unit_type == 'ward',
        UnitSnapshot.snapshot_time >= current_time - timedelta(minutes=15)
    ).all()

    icu_snapshots = db.query(UnitSnapshot).join(HospitalUnit).filter(
        HospitalUnit.tenant_id == tenant_id,
        HospitalUnit.unit_type == 'icu',
        UnitSnapshot.snapshot_time >= current_time - timedelta(minutes=15)
    ).all()

    # Calculate hospital occupancy
    total_beds = sum(s.total_beds or 0 for s in ward_snapshots + icu_snapshots)
    occupied_beds = sum(s.occupied_beds or 0 for s in ward_snapshots + icu_snapshots)
    hospital_occupancy = (occupied_beds / total_beds) if total_beds > 0 else 0

    # Calculate ICU occupancy
    icu_total_beds = sum(s.total_beds or 0 for s in icu_snapshots)
    icu_occupied_beds = sum(s.occupied_beds or 0 for s in icu_snapshots)
    icu_occupancy = (icu_occupied_beds / icu_total_beds) if icu_total_beds > 0 else 0

    # Get ED crowding index
    ed_snapshot = db.query(EDStatusSnapshot).join(HospitalUnit).filter(
        HospitalUnit.tenant_id == tenant_id,
        HospitalUnit.unit_type == 'ed'
    ).order_by(desc(EDStatusSnapshot.snapshot_time)).first()

    ed_crowding_index = 0
    if ed_snapshot and ed_snapshot.total_in_ed:
        # Simple crowding index: (total in ED) / (ED capacity estimate)
        ed_crowding_index = ed_snapshot.total_in_ed / 50  # Assuming 50 as normal capacity

    # Get OR utilization
    or_snapshots = db.query(ORStatusSnapshot).join(HospitalUnit).filter(
        HospitalUnit.tenant_id == tenant_id,
        ORStatusSnapshot.snapshot_time >= current_time - timedelta(hours=1)
    ).all()

    or_utilization = sum(s.utilization_rate_today or 0 for s in or_snapshots) / len(or_snapshots) if or_snapshots else 0

    # Get lab pending critical
    lab_snapshot = db.query(LabWorkloadSnapshot).join(HospitalUnit).filter(
        HospitalUnit.tenant_id == tenant_id
    ).order_by(desc(LabWorkloadSnapshot.snapshot_time)).first()

    lab_pending_critical = lab_snapshot.critical_pending or 0 if lab_snapshot else 0

    # Get imaging pending urgent
    imaging_snapshot = db.query(ImagingWorkloadSnapshot).join(HospitalUnit).filter(
        HospitalUnit.tenant_id == tenant_id
    ).order_by(desc(ImagingWorkloadSnapshot.snapshot_time)).first()

    imaging_pending_urgent = imaging_snapshot.pending_urgent or 0 if imaging_snapshot else 0

    # Get RCM status
    rcm_snapshot = db.query(RCMWorkloadSnapshot).filter(
        RCMWorkloadSnapshot.tenant_id == tenant_id
    ).order_by(desc(RCMWorkloadSnapshot.snapshot_time)).first()

    rcm_status = RCMStatusResponse(
        preauth_pending=rcm_snapshot.preauth_pending or 0 if rcm_snapshot else 0,
        preauth_sla_risk=rcm_snapshot.preauth_sla_breach_risk or 0 if rcm_snapshot else 0,
        claims_to_submit=rcm_snapshot.claims_to_submit or 0 if rcm_snapshot else 0,
        denials_high_value=rcm_snapshot.denials_high_value or 0 if rcm_snapshot else 0,
        ar_total=rcm_snapshot.ar_total if rcm_snapshot else 0
    )

    # Get top alerts
    top_alerts_data = db.query(OpsAlert).filter(
        OpsAlert.tenant_id == tenant_id,
        OpsAlert.status == 'open',
        OpsAlert.severity.in_(['critical', 'warning'])
    ).order_by(
        desc(OpsAlert.severity),
        desc(OpsAlert.triggered_at)
    ).limit(5).all()

    top_alerts = [
        TopAlert(
            alert_id=alert.id,
            domain=alert.domain,
            severity=alert.severity,
            description=alert.description or f"{alert.metric_name}: {alert.metric_value}",
            triggered_at=alert.triggered_at
        )
        for alert in top_alerts_data
    ]

    return HospitalOverviewResponse(
        timestamp=current_time,
        hospital_occupancy=hospital_occupancy,
        icu_occupancy=icu_occupancy,
        ed_crowding_index=ed_crowding_index,
        or_utilization_today=or_utilization,
        lab_pending_critical=lab_pending_critical,
        imaging_pending_urgent=imaging_pending_urgent,
        rcm=rcm_status,
        top_alerts=top_alerts
    )


# Bed Management Endpoint
@app.get("/api/v1/ops/bed-management", response_model=List[UnitSnapshotResponse], tags=["Bed Management"])
async def get_bed_management_view(
    tenant_id: UUID = Query(...),
    unit_type: Optional[str] = Query(None, description="Filter by unit type (ward, icu)"),
    db: Session = Depends(get_db)
):
    """Get bed management view with latest unit snapshots"""
    current_time = datetime.utcnow()

    # Get latest snapshot for each unit
    query = db.query(
        UnitSnapshot, HospitalUnit
    ).join(HospitalUnit).filter(
        HospitalUnit.tenant_id == tenant_id,
        UnitSnapshot.snapshot_time >= current_time - timedelta(minutes=15)
    )

    if unit_type:
        query = query.filter(HospitalUnit.unit_type == unit_type)

    results = query.all()

    snapshots = []
    for snapshot, unit in results:
        snapshots.append(UnitSnapshotResponse(
            id=snapshot.id,
            unit_id=unit.id,
            unit_code=unit.code,
            unit_name=unit.name,
            unit_type=unit.unit_type,
            snapshot_time=snapshot.snapshot_time,
            total_beds=snapshot.total_beds,
            occupied_beds=snapshot.occupied_beds,
            reserved_beds=snapshot.reserved_beds,
            blocked_beds=snapshot.blocked_beds,
            occupancy_rate=snapshot.occupancy_rate,
            acuity_index=snapshot.acuity_index,
            ed_waiting_count=snapshot.ed_waiting_count,
            ed_waiting_longer_than_30m=snapshot.ed_waiting_longer_than_30m
        ))

    return snapshots


# OR Status Endpoint
@app.get("/api/v1/ops/or-status", response_model=List[ORStatusSnapshotResponse], tags=["OR Status"])
async def get_or_status(
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Get OR status with latest snapshots for all OR rooms"""
    current_time = datetime.utcnow()

    snapshots = db.query(ORStatusSnapshot).join(HospitalUnit).filter(
        HospitalUnit.tenant_id == tenant_id,
        ORStatusSnapshot.snapshot_time >= current_time - timedelta(minutes=15)
    ).order_by(desc(ORStatusSnapshot.snapshot_time)).all()

    return snapshots


# ED Status Endpoint
@app.get("/api/v1/ops/ed-status", response_model=List[EDStatusSnapshotResponse], tags=["ED Status"])
async def get_ed_status(
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Get ED status with latest snapshots"""
    current_time = datetime.utcnow()

    snapshots = db.query(EDStatusSnapshot).join(HospitalUnit).filter(
        HospitalUnit.tenant_id == tenant_id,
        EDStatusSnapshot.snapshot_time >= current_time - timedelta(minutes=15)
    ).order_by(desc(EDStatusSnapshot.snapshot_time)).all()

    return snapshots


# Lab Status Endpoint
@app.get("/api/v1/ops/lab-status", response_model=List[LabWorkloadSnapshotResponse], tags=["Lab Status"])
async def get_lab_status(
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Get lab workload status"""
    current_time = datetime.utcnow()

    snapshots = db.query(LabWorkloadSnapshot).join(HospitalUnit).filter(
        HospitalUnit.tenant_id == tenant_id,
        LabWorkloadSnapshot.snapshot_time >= current_time - timedelta(minutes=15)
    ).order_by(desc(LabWorkloadSnapshot.snapshot_time)).all()

    return snapshots


# Imaging Status Endpoint
@app.get("/api/v1/ops/imaging-status", response_model=List[ImagingWorkloadSnapshotResponse], tags=["Imaging Status"])
async def get_imaging_status(
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Get imaging workload status"""
    current_time = datetime.utcnow()

    snapshots = db.query(ImagingWorkloadSnapshot).join(HospitalUnit).filter(
        HospitalUnit.tenant_id == tenant_id,
        ImagingWorkloadSnapshot.snapshot_time >= current_time - timedelta(minutes=15)
    ).order_by(desc(ImagingWorkloadSnapshot.snapshot_time)).all()

    return snapshots


# RCM Status Endpoint
@app.get("/api/v1/ops/rcm-status", response_model=RCMWorkloadSnapshotResponse, tags=["RCM Status"])
async def get_rcm_status(
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Get RCM workload status"""
    snapshot = db.query(RCMWorkloadSnapshot).filter(
        RCMWorkloadSnapshot.tenant_id == tenant_id
    ).order_by(desc(RCMWorkloadSnapshot.snapshot_time)).first()

    if not snapshot:
        raise HTTPException(status_code=404, detail="No RCM snapshot found")

    return snapshot


# Alerts Endpoints
@app.get("/api/v1/ops/alerts", response_model=List[OpsAlertResponse], tags=["Alerts"])
async def list_alerts(
    tenant_id: UUID = Query(...),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List operational alerts with filters"""
    query = db.query(OpsAlert).filter(OpsAlert.tenant_id == tenant_id)

    if status:
        query = query.filter(OpsAlert.status == status)
    if severity:
        query = query.filter(OpsAlert.severity == severity)
    if domain:
        query = query.filter(OpsAlert.domain == domain)

    return query.order_by(desc(OpsAlert.triggered_at)).all()


@app.get("/api/v1/ops/alerts/{alert_id}", response_model=OpsAlertResponse, tags=["Alerts"])
async def get_alert(alert_id: UUID, db: Session = Depends(get_db)):
    """Get alert details"""
    alert = db.query(OpsAlert).filter(OpsAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@app.patch("/api/v1/ops/alerts/{alert_id}", response_model=OpsAlertResponse, tags=["Alerts"])
async def update_alert(
    alert_id: UUID,
    update_data: OpsAlertUpdateRequest,
    db: Session = Depends(get_db)
):
    """Update alert (acknowledge, assign, resolve)"""
    alert = db.query(OpsAlert).filter(OpsAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    old_status = alert.status

    if update_data.status is not None:
        alert.status = update_data.status
        if update_data.status == 'resolved':
            alert.resolved_at = datetime.utcnow()

    if update_data.assigned_user_id is not None:
        alert.assigned_user_id = update_data.assigned_user_id

    if update_data.assigned_team is not None:
        alert.assigned_team = update_data.assigned_team

    alert.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)

    # Publish events
    if old_status != alert.status:
        if alert.status == 'acked':
            await publish_event(EventType.OPS_ALERT_ACKNOWLEDGED, {"alert_id": str(alert.id)})
        elif alert.status == 'resolved':
            await publish_event(EventType.OPS_ALERT_RESOLVED, {"alert_id": str(alert.id)})

    if update_data.assigned_user_id is not None:
        await publish_event(EventType.OPS_ALERT_ASSIGNED, {
            "alert_id": str(alert.id),
            "assigned_user_id": str(alert.assigned_user_id)
        })

    logger.info(f"Alert updated: {alert_id}")
    return alert


# Playbook Endpoints
@app.get("/api/v1/ops/playbooks", response_model=List[OpsPlaybookResponse], tags=["Playbooks"])
async def list_playbooks(
    tenant_id: UUID = Query(...),
    alert_rule_id: Optional[UUID] = Query(None),
    domain: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List operational playbooks"""
    query = db.query(OpsPlaybook).filter(
        OpsPlaybook.tenant_id == tenant_id,
        OpsPlaybook.is_active == True
    ).options(joinedload(OpsPlaybook.playbook_steps))

    if alert_rule_id:
        query = query.filter(OpsPlaybook.trigger_alert_rule_id == alert_rule_id)
    if domain:
        query = query.filter(OpsPlaybook.domain == domain)

    playbooks = query.all()

    # Convert to response format with steps
    results = []
    for playbook in playbooks:
        steps = [
            OpsPlaybookStepResponse(
                id=step.id,
                step_order=step.step_order,
                title=step.title,
                instructions=step.instructions,
                responsible_role=step.responsible_role,
                expected_completion_minutes=step.expected_completion_minutes
            )
            for step in sorted(playbook.playbook_steps, key=lambda s: s.step_order)
        ]

        results.append(OpsPlaybookResponse(
            id=playbook.id,
            name=playbook.name,
            domain=playbook.domain,
            trigger_alert_rule_id=playbook.trigger_alert_rule_id,
            description=playbook.description,
            is_active=playbook.is_active,
            steps=steps
        ))

    return results


@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "ops-command-center-api-service", "status": "healthy", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8073)

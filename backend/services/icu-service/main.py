"""
ICU Service API
Manages Early Warning Scores (NEWS2, MEWS, SOFA) and ICU alerts
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging
import os

from shared.database.connection import get_db
from shared.database.models import (
    EWSScore, ICUAlert, Patient, Admission, Encounter,
    NursingObservation, Ward, BedAssignment, Bed
)
from shared.events.publisher import publish_event
from shared.events.types import EventType
from .schemas import (
    EWSCalculateRequest, EWSScoreResponse, EWSScoreListResponse,
    ICUAlertCreate, ICUAlertUpdate, ICUAlertResponse, ICUAlertListResponse,
    ICUDashboardStats
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="ICU Service",
    description="Manages Early Warning Scores and ICU alerts",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== EWS Calculation Functions ====================

def calculate_news2_score(vitals: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate NEWS2 (National Early Warning Score 2) from vitals

    Returns:
        dict with score_value, risk_level, and score_breakdown
    """
    score = 0
    breakdown = {}

    # Respiratory Rate (breaths/min)
    rr = vitals.get("respiratory_rate")
    if rr is not None:
        if rr <= 8:
            rr_score = 3
        elif rr <= 11:
            rr_score = 1
        elif rr <= 20:
            rr_score = 0
        elif rr <= 24:
            rr_score = 2
        else:  # >= 25
            rr_score = 3
        score += rr_score
        breakdown["respiratory_rate"] = {"value": rr, "score": rr_score}

    # SpO2 (%)
    spo2 = vitals.get("spo2")
    if spo2 is not None:
        if spo2 <= 91:
            spo2_score = 3
        elif spo2 <= 93:
            spo2_score = 2
        elif spo2 <= 95:
            spo2_score = 1
        else:  # >= 96
            spo2_score = 0
        score += spo2_score
        breakdown["spo2"] = {"value": spo2, "score": spo2_score}

    # Air or Oxygen (simplified - assume room air)
    # In full implementation, track if patient is on supplemental O2
    air_or_o2 = vitals.get("on_oxygen", False)
    if air_or_o2:
        air_score = 2
    else:
        air_score = 0
    score += air_score
    breakdown["air_or_oxygen"] = {"on_oxygen": air_or_o2, "score": air_score}

    # Systolic Blood Pressure (mmHg)
    bp_systolic = vitals.get("bp_systolic")
    if bp_systolic is not None:
        if bp_systolic <= 90:
            bp_score = 3
        elif bp_systolic <= 100:
            bp_score = 2
        elif bp_systolic <= 110:
            bp_score = 1
        elif bp_systolic <= 219:
            bp_score = 0
        else:  # >= 220
            bp_score = 3
        score += bp_score
        breakdown["bp_systolic"] = {"value": bp_systolic, "score": bp_score}

    # Heart Rate (beats/min)
    hr = vitals.get("heart_rate")
    if hr is not None:
        if hr <= 40:
            hr_score = 3
        elif hr <= 50:
            hr_score = 1
        elif hr <= 90:
            hr_score = 0
        elif hr <= 110:
            hr_score = 1
        elif hr <= 130:
            hr_score = 2
        else:  # >= 131
            hr_score = 3
        score += hr_score
        breakdown["heart_rate"] = {"value": hr, "score": hr_score}

    # Level of Consciousness
    consciousness = vitals.get("consciousness_level", "alert").lower()
    if consciousness in ["alert", "a"]:
        consciousness_score = 0
    else:  # CVPU (Confusion, Voice, Pain, Unresponsive)
        consciousness_score = 3
    score += consciousness_score
    breakdown["consciousness"] = {"value": consciousness, "score": consciousness_score}

    # Temperature (Celsius)
    temp = vitals.get("temperature")
    if temp is not None:
        if temp <= 35.0:
            temp_score = 3
        elif temp <= 36.0:
            temp_score = 1
        elif temp <= 38.0:
            temp_score = 0
        elif temp <= 39.0:
            temp_score = 1
        else:  # >= 39.1
            temp_score = 2
        score += temp_score
        breakdown["temperature"] = {"value": temp, "score": temp_score}

    # Determine risk level
    if score <= 4:
        risk_level = "low"
    elif score <= 6:
        risk_level = "medium"
    elif score <= 10:
        risk_level = "high"
    else:
        risk_level = "critical"

    return {
        "score_value": score,
        "risk_level": risk_level,
        "score_breakdown": breakdown
    }


def calculate_mews_score(vitals: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate MEWS (Modified Early Warning Score)
    Simplified implementation
    """
    # Similar logic to NEWS2 but with different thresholds
    # For Phase 3, we'll use NEWS2 primarily
    return calculate_news2_score(vitals)


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "icu-service",
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== EWS Score Endpoints ====================

@app.post("/api/v1/icu/ews/calculate", response_model=EWSScoreResponse, status_code=201)
async def calculate_ews(
    ews_request: EWSCalculateRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate Early Warning Score from vitals

    Supported score types:
    - NEWS2: National Early Warning Score 2 (UK)
    - MEWS: Modified Early Warning Score
    - SOFA: Sequential Organ Failure Assessment (future)
    """
    try:
        # Validate admission exists
        admission = db.query(Admission).filter(
            Admission.id == ews_request.admission_id,
            Admission.tenant_id == ews_request.tenant_id
        ).first()

        if not admission:
            raise HTTPException(status_code=404, detail="Admission not found")

        # Calculate score based on type
        if ews_request.score_type == "NEWS2":
            result = calculate_news2_score(ews_request.vitals)
        elif ews_request.score_type == "MEWS":
            result = calculate_mews_score(ews_request.vitals)
        else:
            raise HTTPException(status_code=400, detail=f"Score type {ews_request.score_type} not yet implemented")

        # Create EWS score record
        ews_score = EWSScore(
            tenant_id=ews_request.tenant_id,
            admission_id=ews_request.admission_id,
            encounter_id=ews_request.encounter_id,
            patient_id=ews_request.patient_id,
            score_type=ews_request.score_type,
            score_value=result["score_value"],
            risk_level=result["risk_level"],
            calculated_at=ews_request.calculated_at or datetime.utcnow()
        )

        # Store source observation and breakdown
        source_data = {}
        if ews_request.source_observation_id:
            source_data["observation_ids"] = [str(ews_request.source_observation_id)]

        source_data["score_breakdown"] = result["score_breakdown"]
        source_data["vitals_snapshot"] = ews_request.vitals

        ews_score.source_observation_ids = source_data

        db.add(ews_score)
        db.commit()
        db.refresh(ews_score)

        # Create alert if high risk
        if result["risk_level"] in ["high", "critical"]:
            await create_ews_alert(db, ews_score, ews_request)

        logger.info(
            f"Calculated {ews_request.score_type} score of {result['score_value']} "
            f"({result['risk_level']}) for patient {ews_request.patient_id}"
        )

        return ews_score

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error calculating EWS: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def create_ews_alert(
    db: Session,
    ews_score: EWSScore,
    ews_request: EWSCalculateRequest
):
    """Create an alert for high/critical EWS score"""
    severity = "critical" if ews_score.risk_level == "critical" else "warning"

    message = (
        f"{ews_score.score_type} score of {ews_score.score_value} - "
        f"{ews_score.risk_level.capitalize()} risk"
    )

    alert = ICUAlert(
        tenant_id=ews_score.tenant_id,
        admission_id=ews_score.admission_id,
        encounter_id=ews_score.encounter_id,
        patient_id=ews_score.patient_id,
        alert_type="ews_high",
        message=message,
        severity=severity,
        status="open",
        triggered_at=datetime.utcnow(),
        meta_data={
            "ews_score_id": str(ews_score.id),
            "score_type": ews_score.score_type,
            "score_value": ews_score.score_value,
            "risk_level": ews_score.risk_level
        }
    )

    db.add(alert)
    db.commit()

    # Publish event
    await publish_event(
        EventType.ICU_ALERT_CREATED,
        {
            "alert_id": str(alert.id),
            "tenant_id": str(alert.tenant_id),
            "patient_id": str(alert.patient_id),
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "message": alert.message,
            "ews_score": ews_score.score_value
        }
    )


@app.get("/api/v1/icu/ews/{ews_id}", response_model=EWSScoreResponse)
async def get_ews_score(
    ews_id: UUID,
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Get EWS score by ID"""
    ews_score = db.query(EWSScore).filter(
        EWSScore.id == ews_id,
        EWSScore.tenant_id == tenant_id
    ).first()

    if not ews_score:
        raise HTTPException(status_code=404, detail="EWS score not found")

    return ews_score


@app.get("/api/v1/icu/ews", response_model=EWSScoreListResponse)
async def list_ews_scores(
    tenant_id: UUID = Query(...),
    patient_id: Optional[UUID] = Query(None),
    admission_id: Optional[UUID] = Query(None),
    score_type: Optional[str] = Query(None, description="NEWS2, MEWS, SOFA"),
    risk_level: Optional[str] = Query(None, description="low, medium, high, critical"),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List EWS scores with filtering

    Filters:
    - patient_id: Filter by patient
    - admission_id: Filter by admission
    - score_type: Filter by score type (NEWS2, MEWS, SOFA)
    - risk_level: Filter by risk level
    - from_date / to_date: Filter by calculated_at range
    """
    query = db.query(EWSScore).filter(EWSScore.tenant_id == tenant_id)

    # Apply filters
    if patient_id:
        query = query.filter(EWSScore.patient_id == patient_id)

    if admission_id:
        query = query.filter(EWSScore.admission_id == admission_id)

    if score_type:
        query = query.filter(EWSScore.score_type == score_type.upper())

    if risk_level:
        query = query.filter(EWSScore.risk_level == risk_level.lower())

    if from_date:
        query = query.filter(EWSScore.calculated_at >= from_date)

    if to_date:
        query = query.filter(EWSScore.calculated_at <= to_date)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    scores = query.order_by(EWSScore.calculated_at.desc()).offset(offset).limit(page_size).all()

    # Calculate pagination metadata
    has_next = (offset + page_size) < total
    has_previous = page > 1

    return EWSScoreListResponse(
        total=total,
        scores=scores,
        page=page,
        page_size=page_size,
        has_next=has_next,
        has_previous=has_previous
    )


# ==================== ICU Alert Endpoints ====================

@app.post("/api/v1/icu/alerts", response_model=ICUAlertResponse, status_code=201)
async def create_icu_alert(
    alert_data: ICUAlertCreate,
    db: Session = Depends(get_db)
):
    """
    Create an ICU alert

    Alert types:
    - ews_high: High EWS score
    - vitals_trend: Concerning trend in vitals
    - device_alarm: Device/monitor alarm
    - manual: Manually created by staff
    """
    try:
        # Validate admission exists
        admission = db.query(Admission).filter(
            Admission.id == alert_data.admission_id,
            Admission.tenant_id == alert_data.tenant_id
        ).first()

        if not admission:
            raise HTTPException(status_code=404, detail="Admission not found")

        # Create alert
        alert = ICUAlert(
            tenant_id=alert_data.tenant_id,
            admission_id=alert_data.admission_id,
            encounter_id=alert_data.encounter_id,
            patient_id=alert_data.patient_id,
            alert_type=alert_data.alert_type.lower(),
            message=alert_data.message,
            severity=alert_data.severity.lower(),
            status="open",
            triggered_at=alert_data.triggered_at or datetime.utcnow(),
            meta_data=alert_data.metadata or {}
        )

        db.add(alert)
        db.commit()
        db.refresh(alert)

        # Publish event
        await publish_event(
            EventType.ICU_ALERT_CREATED,
            {
                "alert_id": str(alert.id),
                "tenant_id": str(alert.tenant_id),
                "patient_id": str(alert.patient_id),
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message
            }
        )

        logger.info(f"Created ICU alert {alert.id} for patient {alert.patient_id}")
        return alert

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating ICU alert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/icu/alerts/{alert_id}", response_model=ICUAlertResponse)
async def get_icu_alert(
    alert_id: UUID,
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Get ICU alert by ID"""
    alert = db.query(ICUAlert).filter(
        ICUAlert.id == alert_id,
        ICUAlert.tenant_id == tenant_id
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="ICU alert not found")

    return alert


@app.get("/api/v1/icu/alerts", response_model=ICUAlertListResponse)
async def list_icu_alerts(
    tenant_id: UUID = Query(...),
    ward_id: Optional[UUID] = Query(None),
    patient_id: Optional[UUID] = Query(None),
    admission_id: Optional[UUID] = Query(None),
    alert_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None, description="info, warning, critical"),
    status: Optional[str] = Query(None, description="open, acknowledged, resolved"),
    active_only: bool = Query(False, description="Only show open/acknowledged alerts"),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List ICU alerts with filtering

    Filters:
    - ward_id: Filter by ward (via bed assignment)
    - patient_id: Filter by patient
    - admission_id: Filter by admission
    - alert_type: Filter by alert type
    - severity: Filter by severity
    - status: Filter by status
    - active_only: Only show open/acknowledged alerts
    - from_date / to_date: Filter by triggered_at range
    """
    query = db.query(ICUAlert).filter(ICUAlert.tenant_id == tenant_id)

    # Filter by ward (join through bed assignments)
    if ward_id:
        query = query.join(
            BedAssignment,
            and_(
                BedAssignment.admission_id == ICUAlert.admission_id,
                BedAssignment.status == "active"
            )
        ).join(Bed).filter(Bed.ward_id == ward_id)

    # Apply other filters
    if patient_id:
        query = query.filter(ICUAlert.patient_id == patient_id)

    if admission_id:
        query = query.filter(ICUAlert.admission_id == admission_id)

    if alert_type:
        query = query.filter(ICUAlert.alert_type == alert_type.lower())

    if severity:
        query = query.filter(ICUAlert.severity == severity.lower())

    if status:
        query = query.filter(ICUAlert.status == status.lower())

    if active_only:
        query = query.filter(ICUAlert.status.in_(["open", "acknowledged"]))

    if from_date:
        query = query.filter(ICUAlert.triggered_at >= from_date)

    if to_date:
        query = query.filter(ICUAlert.triggered_at <= to_date)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    alerts = query.order_by(
        ICUAlert.severity.desc(),
        ICUAlert.triggered_at.desc()
    ).offset(offset).limit(page_size).all()

    # Calculate pagination metadata
    has_next = (offset + page_size) < total
    has_previous = page > 1

    return ICUAlertListResponse(
        total=total,
        alerts=alerts,
        page=page,
        page_size=page_size,
        has_next=has_next,
        has_previous=has_previous
    )


@app.patch("/api/v1/icu/alerts/{alert_id}", response_model=ICUAlertResponse)
async def update_icu_alert(
    alert_id: UUID,
    update_data: ICUAlertUpdate,
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """
    Update ICU alert

    Typically used to:
    - Acknowledge alert (status=acknowledged)
    - Resolve alert (status=resolved)
    - Add notes
    """
    try:
        alert = db.query(ICUAlert).filter(
            ICUAlert.id == alert_id,
            ICUAlert.tenant_id == tenant_id
        ).first()

        if not alert:
            raise HTTPException(status_code=404, detail="ICU alert not found")

        # Update status with timestamps
        if update_data.status:
            old_status = alert.status
            alert.status = update_data.status.lower()

            if update_data.status == "acknowledged" and old_status == "open":
                alert.acknowledged_at = datetime.utcnow()
                alert.acknowledged_by_user_id = update_data.acknowledged_by_user_id

            elif update_data.status == "resolved":
                alert.resolved_at = datetime.utcnow()
                if not alert.acknowledged_at:
                    alert.acknowledged_at = datetime.utcnow()
                    alert.acknowledged_by_user_id = update_data.acknowledged_by_user_id

        # Store notes in metadata
        if update_data.notes:
            if not alert.meta_data:
                alert.meta_data = {}
            if "notes" not in alert.meta_data:
                alert.meta_data["notes"] = []
            alert.meta_data["notes"].append({
                "text": update_data.notes,
                "user_id": str(update_data.acknowledged_by_user_id) if update_data.acknowledged_by_user_id else None,
                "timestamp": datetime.utcnow().isoformat()
            })

        alert.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(alert)

        logger.info(f"Updated ICU alert {alert.id} to status {alert.status}")
        return alert

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating ICU alert: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Dashboard Endpoints ====================

@app.get("/api/v1/icu/dashboard/stats", response_model=ICUDashboardStats)
async def get_icu_dashboard_stats(
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """
    Get ICU dashboard statistics

    Returns:
    - Total ICU/HDU patients
    - Active alerts by severity
    - High/medium risk patient counts
    - Average NEWS2 score
    """
    # Count ICU/HDU patients (active admissions in ICU/HDU wards)
    icu_patients = db.query(Admission).join(
        BedAssignment,
        and_(
            BedAssignment.admission_id == Admission.id,
            BedAssignment.status == "active"
        )
    ).join(Bed).join(Ward).filter(
        Admission.tenant_id == tenant_id,
        Admission.status == "admitted",
        Ward.type == "icu"
    ).count()

    hdu_patients = db.query(Admission).join(
        BedAssignment,
        and_(
            BedAssignment.admission_id == Admission.id,
            BedAssignment.status == "active"
        )
    ).join(Bed).join(Ward).filter(
        Admission.tenant_id == tenant_id,
        Admission.status == "admitted",
        Ward.type == "hdu"
    ).count()

    # Active alerts by severity
    active_critical_alerts = db.query(ICUAlert).filter(
        ICUAlert.tenant_id == tenant_id,
        ICUAlert.status.in_(["open", "acknowledged"]),
        ICUAlert.severity == "critical"
    ).count()

    active_warning_alerts = db.query(ICUAlert).filter(
        ICUAlert.tenant_id == tenant_id,
        ICUAlert.status.in_(["open", "acknowledged"]),
        ICUAlert.severity == "warning"
    ).count()

    # High/medium risk patients (latest EWS score)
    # Get latest score for each patient
    from sqlalchemy import distinct
    from sqlalchemy.sql import func as sql_func

    # Subquery for latest score per patient
    latest_scores_subq = db.query(
        EWSScore.patient_id,
        sql_func.max(EWSScore.calculated_at).label("max_calc_at")
    ).filter(
        EWSScore.tenant_id == tenant_id
    ).group_by(EWSScore.patient_id).subquery()

    latest_scores = db.query(EWSScore).join(
        latest_scores_subq,
        and_(
            EWSScore.patient_id == latest_scores_subq.c.patient_id,
            EWSScore.calculated_at == latest_scores_subq.c.max_calc_at
        )
    ).all()

    high_risk_patients = sum(1 for score in latest_scores if score.risk_level in ["high", "critical"])
    medium_risk_patients = sum(1 for score in latest_scores if score.risk_level == "medium")

    # Average NEWS2 score (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(days=1)
    news2_scores = db.query(EWSScore).filter(
        EWSScore.tenant_id == tenant_id,
        EWSScore.score_type == "NEWS2",
        EWSScore.calculated_at >= yesterday
    ).all()

    avg_news2 = None
    if news2_scores:
        avg_news2 = sum(score.score_value for score in news2_scores) / len(news2_scores)

    return ICUDashboardStats(
        total_icu_patients=icu_patients,
        total_hdu_patients=hdu_patients,
        active_critical_alerts=active_critical_alerts,
        active_warning_alerts=active_warning_alerts,
        high_risk_patients=high_risk_patients,
        medium_risk_patients=medium_risk_patients,
        average_news2_score=avg_news2
    )


# ==================== Root ====================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "icu-service",
        "version": "1.0.0",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8013))
    uvicorn.run(app, host="0.0.0.0", port=port)

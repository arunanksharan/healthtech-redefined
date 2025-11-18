"""
Radiology Reporting Service - Port 8034
Manages radiology report creation, templates, signing, and addenda
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, and_
from sqlalchemy.orm import Session, sessionmaker

from shared.database.models import (
    RadiologyReportTemplate, RadiologyReport, RadiologyReportAddendum,
    ImagingStudy, Patient, Practitioner, Tenant
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    RadiologyReportTemplateCreate, RadiologyReportTemplateResponse,
    RadiologyReportCreate, RadiologyReportUpdate, RadiologyReportResponse,
    ReportSignRequest,
    RadiologyReportAddendumCreate, RadiologyReportAddendumResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Radiology Reporting Service", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Radiology Report Template Endpoints
@app.post("/api/v1/radiology/templates", response_model=RadiologyReportTemplateResponse, status_code=201, tags=["Templates"])
async def create_report_template(
    template_data: RadiologyReportTemplateCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create radiology report template"""
    existing = db.query(RadiologyReportTemplate).filter(and_(
        RadiologyReportTemplate.tenant_id == template_data.tenant_id,
        RadiologyReportTemplate.code == template_data.code
    )).first()
    if existing:
        raise HTTPException(status_code=400, detail="Template code already exists")

    template = RadiologyReportTemplate(
        tenant_id=template_data.tenant_id,
        code=template_data.code,
        name=template_data.name,
        modality_code=template_data.modality_code,
        body_part=template_data.body_part,
        description=template_data.description,
        template_type=template_data.template_type,
        schema=template_data.schema,
        default_text=template_data.default_text
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    logger.info(f"Report template created: {template.code}")
    return template

@app.get("/api/v1/radiology/templates", response_model=List[RadiologyReportTemplateResponse], tags=["Templates"])
async def list_report_templates(
    tenant_id: Optional[UUID] = Query(None),
    modality_code: Optional[str] = Query(None),
    body_part: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List radiology report templates"""
    query = db.query(RadiologyReportTemplate)
    if tenant_id:
        query = query.filter(RadiologyReportTemplate.tenant_id == tenant_id)
    if modality_code:
        query = query.filter(RadiologyReportTemplate.modality_code == modality_code)
    if body_part:
        query = query.filter(RadiologyReportTemplate.body_part == body_part)
    if is_active is not None:
        query = query.filter(RadiologyReportTemplate.is_active == is_active)
    return query.all()

@app.get("/api/v1/radiology/templates/{template_id}", response_model=RadiologyReportTemplateResponse, tags=["Templates"])
async def get_report_template(template_id: UUID, db: Session = Depends(get_db)):
    """Get report template details"""
    template = db.query(RadiologyReportTemplate).filter(RadiologyReportTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

# Radiology Report Endpoints
@app.post("/api/v1/radiology/reports", response_model=RadiologyReportResponse, status_code=201, tags=["Reports"])
async def create_radiology_report(
    report_data: RadiologyReportCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create radiology report (draft)"""
    # Verify imaging study exists
    study = db.query(ImagingStudy).filter(ImagingStudy.id == report_data.imaging_study_id).first()
    if not study:
        raise HTTPException(status_code=404, detail="Imaging study not found")

    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == report_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Check if report already exists
    existing = db.query(RadiologyReport).filter(
        RadiologyReport.imaging_study_id == report_data.imaging_study_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Report already exists for this study")

    report = RadiologyReport(
        tenant_id=patient.tenant_id,
        imaging_study_id=report_data.imaging_study_id,
        imaging_order_id=report_data.imaging_order_id,
        patient_id=report_data.patient_id,
        radiologist_id=report_data.radiologist_id or current_user_id,
        template_id=report_data.template_id,
        status='draft',
        clinical_history=report_data.clinical_history,
        technique=report_data.technique,
        findings=report_data.findings,
        impression=report_data.impression,
        structured_data=report_data.structured_data
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    await publish_event(EventType.RADIOLOGY_REPORT_CREATED, {
        "report_id": str(report.id),
        "imaging_study_id": str(report.imaging_study_id),
        "patient_id": str(report.patient_id),
        "radiologist_id": str(report.radiologist_id) if report.radiologist_id else None,
        "status": report.status
    })

    logger.info(f"Radiology report created: {report.id}")
    return report

@app.get("/api/v1/radiology/reports", response_model=List[RadiologyReportResponse], tags=["Reports"])
async def list_radiology_reports(
    patient_id: Optional[UUID] = Query(None),
    radiologist_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """List radiology reports with filters"""
    query = db.query(RadiologyReport)
    if patient_id:
        query = query.filter(RadiologyReport.patient_id == patient_id)
    if radiologist_id:
        query = query.filter(RadiologyReport.radiologist_id == radiologist_id)
    if status:
        query = query.filter(RadiologyReport.status == status)
    if from_date:
        query = query.filter(RadiologyReport.created_at >= from_date)
    if to_date:
        query = query.filter(RadiologyReport.created_at <= to_date)
    return query.order_by(RadiologyReport.created_at.desc()).all()

@app.get("/api/v1/radiology/reports/{report_id}", response_model=RadiologyReportResponse, tags=["Reports"])
async def get_radiology_report(report_id: UUID, db: Session = Depends(get_db)):
    """Get radiology report details"""
    report = db.query(RadiologyReport).filter(RadiologyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@app.patch("/api/v1/radiology/reports/{report_id}", response_model=RadiologyReportResponse, tags=["Reports"])
async def update_radiology_report(
    report_id: UUID,
    report_data: RadiologyReportUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Update radiology report (save edits)"""
    report = db.query(RadiologyReport).filter(RadiologyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.status not in ['draft', 'preliminary']:
        raise HTTPException(status_code=400, detail="Cannot update a final or cancelled report")

    update_data = report_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(report, field, value)

    report.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(report)

    logger.info(f"Radiology report updated: {report_id}")
    return report

@app.post("/api/v1/radiology/reports/{report_id}/sign", response_model=RadiologyReportResponse, tags=["Reports"])
async def sign_radiology_report(
    report_id: UUID,
    sign_request: ReportSignRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Sign radiology report (mark as preliminary or final)"""
    report = db.query(RadiologyReport).filter(RadiologyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.status not in ['draft', 'preliminary']:
        raise HTTPException(status_code=400, detail="Report cannot be signed in current status")

    report.status = 'final' if sign_request.final else 'preliminary'
    report.signed_at = datetime.utcnow()
    report.signed_by_radiologist_id = current_user_id
    report.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(report)

    await publish_event(EventType.RADIOLOGY_REPORT_SIGNED, {
        "report_id": str(report.id),
        "imaging_study_id": str(report.imaging_study_id),
        "patient_id": str(report.patient_id),
        "signed_by_radiologist_id": str(current_user_id) if current_user_id else None,
        "status": report.status,
        "critical_result": report.critical_result
    })

    # If critical result, publish critical alert
    if report.critical_result:
        await publish_event(EventType.RADIOLOGY_CRITICAL_RESULT, {
            "report_id": str(report.id),
            "patient_id": str(report.patient_id),
            "impression": report.impression
        })

    logger.info(f"Radiology report signed: {report_id} - {report.status}")
    return report

# Report Addendum Endpoints
@app.post("/api/v1/radiology/reports/{report_id}/addenda", response_model=RadiologyReportAddendumResponse, status_code=201, tags=["Addenda"])
async def create_report_addendum(
    report_id: UUID,
    addendum_data: RadiologyReportAddendumCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create report addendum"""
    # Verify report exists
    report = db.query(RadiologyReport).filter(RadiologyReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Ensure addendum belongs to the report
    if addendum_data.radiology_report_id != report_id:
        raise HTTPException(status_code=400, detail="Report ID mismatch")

    addendum = RadiologyReportAddendum(
        radiology_report_id=addendum_data.radiology_report_id,
        added_by_radiologist_id=addendum_data.added_by_radiologist_id or current_user_id,
        content=addendum_data.content
    )
    db.add(addendum)
    db.commit()
    db.refresh(addendum)

    # Update report status to corrected if it was final
    if report.status == 'final':
        report.status = 'corrected'
        report.updated_at = datetime.utcnow()
        db.commit()

    await publish_event(EventType.RADIOLOGY_REPORT_ADDENDUM_ADDED, {
        "addendum_id": str(addendum.id),
        "report_id": str(report.id),
        "patient_id": str(report.patient_id)
    })

    logger.info(f"Report addendum added: {addendum.id} for report {report_id}")
    return addendum

@app.get("/api/v1/radiology/reports/{report_id}/addenda", response_model=List[RadiologyReportAddendumResponse], tags=["Addenda"])
async def list_report_addenda(report_id: UUID, db: Session = Depends(get_db)):
    """List all addenda for a report"""
    return db.query(RadiologyReportAddendum).filter(
        RadiologyReportAddendum.radiology_report_id == report_id
    ).order_by(RadiologyReportAddendum.created_at).all()

@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "radiology-reporting-service", "status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8034)

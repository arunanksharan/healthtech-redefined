"""
AP Pathology Service - Port 8040
Manages anatomic pathology cases, specimens, and synoptic reporting
"""
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from shared.database.models import (
    APCase, APReport, APReportTemplate, APReportSynopticValue,
    Patient, Practitioner, Tenant
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    APReportTemplateCreate, APReportTemplateResponse,
    APCaseCreate, APCaseUpdate, APCaseResponse,
    APReportCreate, APReportUpdate, APReportSignRequest, APReportResponse,
    APReportSynopticValueResponse
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="AP Pathology Service", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_case_number(tenant_id: UUID, year: int):
    """Generate sequential case number like AP-2025-000123"""
    # In production, this would use a sequence or counter per tenant
    import secrets
    return f"AP-{year}-{secrets.token_hex(3).upper()}"

# AP Report Template Endpoints
@app.post("/api/v1/ap-templates", response_model=APReportTemplateResponse, status_code=201, tags=["Report Templates"])
async def create_report_template(
    template_data: APReportTemplateCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create an anatomic pathology report template"""
    existing = db.query(APReportTemplate).filter(
        APReportTemplate.code == template_data.code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Template code already exists")

    template = APReportTemplate(
        tenant_id=template_data.tenant_id,
        code=template_data.code,
        name=template_data.name,
        description=template_data.description,
        site=template_data.site,
        schema=template_data.schema,
        default_narrative=template_data.default_narrative
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    logger.info(f"AP report template created: {template.code}")
    return template

@app.get("/api/v1/ap-templates", response_model=List[APReportTemplateResponse], tags=["Report Templates"])
async def list_report_templates(
    site: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List AP report templates"""
    query = db.query(APReportTemplate)
    if site:
        query = query.filter(APReportTemplate.site == site)
    if is_active is not None:
        query = query.filter(APReportTemplate.is_active == is_active)
    return query.all()

@app.get("/api/v1/ap-templates/{id}", response_model=APReportTemplateResponse, tags=["Report Templates"])
async def get_report_template(id: UUID, db: Session = Depends(get_db)):
    """Get AP report template details"""
    template = db.query(APReportTemplate).filter(APReportTemplate.id == id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Report template not found")
    return template

# AP Case Endpoints
@app.post("/api/v1/ap-cases", response_model=APCaseResponse, status_code=201, tags=["AP Cases"])
async def create_ap_case(
    case_data: APCaseCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create anatomic pathology case (from OR/biopsy order)"""
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == case_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    case_number = generate_case_number(patient.tenant_id, datetime.utcnow().year)

    ap_case = APCase(
        tenant_id=patient.tenant_id,
        case_number=case_number,
        patient_id=case_data.patient_id,
        encounter_id=case_data.encounter_id,
        referring_practitioner_id=case_data.referring_practitioner_id,
        referring_department_id=case_data.referring_department_id,
        received_date=datetime.utcnow(),
        status='accessioned',
        clinical_history=case_data.clinical_history,
        pathologist_id=case_data.pathologist_id
    )
    db.add(ap_case)
    db.commit()
    db.refresh(ap_case)

    await publish_event(EventType.AP_CASE_CREATED, {
        "ap_case_id": str(ap_case.id),
        "case_number": ap_case.case_number,
        "patient_id": str(ap_case.patient_id)
    })

    logger.info(f"AP case created: {ap_case.case_number}")
    return ap_case

@app.get("/api/v1/ap-cases", response_model=List[APCaseResponse], tags=["AP Cases"])
async def list_ap_cases(
    patient_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    pathologist_id: Optional[UUID] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List AP cases with filters"""
    query = db.query(APCase)
    if patient_id:
        query = query.filter(APCase.patient_id == patient_id)
    if status:
        query = query.filter(APCase.status == status)
    if pathologist_id:
        query = query.filter(APCase.pathologist_id == pathologist_id)
    if from_date:
        query = query.filter(APCase.received_date >= from_date)
    if to_date:
        query = query.filter(APCase.received_date <= to_date)
    return query.order_by(APCase.received_date.desc()).all()

@app.get("/api/v1/ap-cases/{case_id}", response_model=APCaseResponse, tags=["AP Cases"])
async def get_ap_case(case_id: UUID, db: Session = Depends(get_db)):
    """Get AP case details"""
    ap_case = db.query(APCase).filter(APCase.id == case_id).first()
    if not ap_case:
        raise HTTPException(status_code=404, detail="AP case not found")
    return ap_case

@app.patch("/api/v1/ap-cases/{case_id}", response_model=APCaseResponse, tags=["AP Cases"])
async def update_ap_case(
    case_id: UUID,
    update_data: APCaseUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Update AP case status and details"""
    ap_case = db.query(APCase).filter(APCase.id == case_id).first()
    if not ap_case:
        raise HTTPException(status_code=404, detail="AP case not found")

    if update_data.status:
        ap_case.status = update_data.status
    if update_data.diagnosis_summary:
        ap_case.diagnosis_summary = update_data.diagnosis_summary
    if update_data.pathologist_id:
        ap_case.pathologist_id = update_data.pathologist_id

    db.commit()
    db.refresh(ap_case)

    logger.info(f"AP case updated: {case_id}")
    return ap_case

# AP Report Endpoints
@app.post("/api/v1/ap-reports", response_model=APReportResponse, status_code=201, tags=["AP Reports"])
async def create_ap_report(
    report_data: APReportCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Create draft pathology report with optional template"""
    # Verify case exists
    ap_case = db.query(APCase).filter(APCase.id == report_data.ap_case_id).first()
    if not ap_case:
        raise HTTPException(status_code=404, detail="AP case not found")

    ap_report = APReport(
        ap_case_id=report_data.ap_case_id,
        template_id=report_data.template_id,
        status='draft',
        gross_description=report_data.gross_description,
        microscopic_description=report_data.microscopic_description,
        diagnosis_text=report_data.diagnosis_text,
        comments=report_data.comments
    )
    db.add(ap_report)
    db.flush()  # Get report ID

    # Add synoptic values
    if report_data.synoptic_values:
        for value_data in report_data.synoptic_values:
            synoptic_value = APReportSynopticValue(
                ap_report_id=ap_report.id,
                field_code=value_data.field_code,
                value_text=value_data.value_text,
                value_code=value_data.value_code
            )
            db.add(synoptic_value)

    db.commit()
    db.refresh(ap_report)

    await publish_event(EventType.AP_REPORT_CREATED, {
        "ap_report_id": str(ap_report.id),
        "ap_case_id": str(ap_report.ap_case_id),
        "patient_id": str(ap_case.patient_id)
    })

    logger.info(f"AP report created: {ap_report.id} for case {ap_case.case_number}")
    return ap_report

@app.get("/api/v1/ap-reports/{report_id}", response_model=APReportResponse, tags=["AP Reports"])
async def get_ap_report(report_id: UUID, db: Session = Depends(get_db)):
    """Get AP report details"""
    ap_report = db.query(APReport).filter(APReport.id == report_id).first()
    if not ap_report:
        raise HTTPException(status_code=404, detail="AP report not found")
    return ap_report

@app.patch("/api/v1/ap-reports/{report_id}", response_model=APReportResponse, tags=["AP Reports"])
async def update_ap_report(
    report_id: UUID,
    update_data: APReportUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Update pathology report narrative and synoptic values"""
    ap_report = db.query(APReport).filter(APReport.id == report_id).first()
    if not ap_report:
        raise HTTPException(status_code=404, detail="AP report not found")

    if ap_report.status not in ['draft', 'preliminary']:
        raise HTTPException(status_code=400, detail="Cannot modify finalized report")

    if update_data.gross_description:
        ap_report.gross_description = update_data.gross_description
    if update_data.microscopic_description:
        ap_report.microscopic_description = update_data.microscopic_description
    if update_data.diagnosis_text:
        ap_report.diagnosis_text = update_data.diagnosis_text
    if update_data.comments:
        ap_report.comments = update_data.comments

    # Update synoptic values
    if update_data.synoptic_values is not None:
        # Delete existing synoptic values
        db.query(APReportSynopticValue).filter(
            APReportSynopticValue.ap_report_id == report_id
        ).delete()

        # Add new synoptic values
        for value_data in update_data.synoptic_values:
            synoptic_value = APReportSynopticValue(
                ap_report_id=ap_report.id,
                field_code=value_data.field_code,
                value_text=value_data.value_text,
                value_code=value_data.value_code
            )
            db.add(synoptic_value)

    db.commit()
    db.refresh(ap_report)

    await publish_event(EventType.AP_REPORT_UPDATED, {
        "ap_report_id": str(ap_report.id),
        "ap_case_id": str(ap_report.ap_case_id)
    })

    logger.info(f"AP report updated: {report_id}")
    return ap_report

@app.post("/api/v1/ap-reports/{report_id}/sign", response_model=APReportResponse, tags=["AP Reports"])
async def sign_ap_report(
    report_id: UUID,
    sign_request: APReportSignRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Sign pathology report (mark as final)"""
    ap_report = db.query(APReport).filter(APReport.id == report_id).first()
    if not ap_report:
        raise HTTPException(status_code=404, detail="AP report not found")

    if ap_report.status == 'final':
        raise HTTPException(status_code=400, detail="Report already finalized")

    ap_report.status = 'final' if sign_request.final else 'preliminary'
    ap_report.signed_at = datetime.utcnow()
    ap_report.signed_by_pathologist_id = current_user_id

    db.commit()
    db.refresh(ap_report)

    await publish_event(EventType.AP_REPORT_SIGNED, {
        "ap_report_id": str(ap_report.id),
        "ap_case_id": str(ap_report.ap_case_id),
        "status": ap_report.status
    })

    logger.info(f"AP report signed: {report_id} - status: {ap_report.status}")
    return ap_report

@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "ap-pathology-service", "status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8040)

"""
Diagnostic Reports Router
API endpoints for lab results, imaging reports
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from loguru import logger

from shared.database.connection import get_db
from shared.database.fhir_models import FHIRResource

from .schemas import (
    ReportCreate,
    ReportResponse,
    ReportListResponse,
    ReportCode
)


router = APIRouter(prefix="/diagnostic-reports", tags=["Diagnostic Reports"])

RESOURCE_TYPE = "DiagnosticReport"


def _build_fhir_diagnostic_report(data: ReportCreate, fhir_id: str) -> dict:
    """Build FHIR DiagnosticReport resource from create data"""
    resource = {
        "resourceType": "DiagnosticReport",
        "id": fhir_id,
        "status": data.status,
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                "code": data.category,
                "display": "Laboratory" if data.category == "LAB" else "Radiology"
            }]
        }],
        "code": {
            "coding": [{
                "system": data.code.system,
                "code": data.code.code,
                "display": data.code.display
            }]
        },
        "subject": {"reference": f"Patient/{data.patient_id}"},
    }

    if data.encounter_id:
        resource["encounter"] = {"reference": f"Encounter/{data.encounter_id}"}

    if data.performer_id:
        resource["performer"] = [{"reference": f"Practitioner/{data.performer_id}"}]

    if data.effective_datetime:
        resource["effectiveDateTime"] = data.effective_datetime.isoformat()

    resource["issued"] = (data.issued or datetime.utcnow()).isoformat()

    if data.conclusion:
        resource["conclusion"] = data.conclusion

    if data.result_ids:
        resource["result"] = [
            {"reference": f"Observation/{obs_id}"} for obs_id in data.result_ids
        ]

    if data.presented_form_url:
        resource["presentedForm"] = [{
            "contentType": "application/pdf",
            "url": data.presented_form_url
        }]

    if data.note:
        # Store in extension since FHIR DiagnosticReport doesn't have a note field
        resource["extension"] = [{
            "url": "http://healthtech.local/fhir/StructureDefinition/report-note",
            "valueString": data.note
        }]

    return resource


def _parse_report_response(resource: FHIRResource) -> ReportResponse:
    """Parse FHIRResource into ReportResponse"""
    data = resource.resource_data

    # Extract code
    code_data = data.get("code", {}).get("coding", [{}])[0]
    code = ReportCode(
        system=code_data.get("system", ""),
        code=code_data.get("code", ""),
        display=code_data.get("display")
    )

    # Extract category
    category = "LAB"
    if "category" in data and data["category"]:
        category = data["category"][0].get("coding", [{}])[0].get("code", "LAB")

    # Extract patient_id
    patient_id = None
    if "subject" in data:
        ref = data["subject"].get("reference", "")
        if ref.startswith("Patient/"):
            try:
                patient_id = UUID(ref.replace("Patient/", ""))
            except ValueError:
                pass

    # Extract encounter_id
    encounter_id = None
    if "encounter" in data:
        ref = data["encounter"].get("reference", "")
        if ref.startswith("Encounter/"):
            try:
                encounter_id = UUID(ref.replace("Encounter/", ""))
            except ValueError:
                pass

    # Extract performer_id
    performer_id = None
    if "performer" in data and data["performer"]:
        ref = data["performer"][0].get("reference", "")
        if ref.startswith("Practitioner/"):
            try:
                performer_id = UUID(ref.replace("Practitioner/", ""))
            except ValueError:
                pass

    # Extract result_ids
    result_ids = []
    if "result" in data:
        for r in data["result"]:
            ref = r.get("reference", "")
            if ref.startswith("Observation/"):
                try:
                    result_ids.append(UUID(ref.replace("Observation/", "")))
                except ValueError:
                    pass

    # Extract datetimes
    effective = None
    if "effectiveDateTime" in data:
        try:
            effective = datetime.fromisoformat(data["effectiveDateTime"].replace("Z", "+00:00"))
        except ValueError:
            pass

    issued = None
    if "issued" in data:
        try:
            issued = datetime.fromisoformat(data["issued"].replace("Z", "+00:00"))
        except ValueError:
            pass

    # Extract presented form URL
    presented_form_url = None
    if "presentedForm" in data and data["presentedForm"]:
        presented_form_url = data["presentedForm"][0].get("url")

    # Extract note from extension
    note = None
    if "extension" in data:
        for ext in data["extension"]:
            if ext.get("url", "").endswith("report-note"):
                note = ext.get("valueString")
                break

    return ReportResponse(
        id=resource.id,
        fhir_id=resource.fhir_id,
        tenant_id=resource.tenant_id,
        resource_type=RESOURCE_TYPE,
        patient_id=patient_id,
        encounter_id=encounter_id,
        performer_id=performer_id,
        status=data.get("status", "final"),
        category=category,
        code=code,
        effective_datetime=effective,
        issued=issued,
        conclusion=data.get("conclusion"),
        result_ids=result_ids,
        presented_form_url=presented_form_url,
        note=note,
        created_at=resource.created_at,
        updated_at=resource.last_updated
    )


@router.get("", response_model=ReportListResponse)
async def list_diagnostic_reports(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    patient_id: Optional[UUID] = Query(None, description="Filter by patient"),
    category: Optional[str] = Query(None, description="Filter by category (LAB, RAD)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """
    List diagnostic reports (lab results, imaging)

    Categories: LAB (Laboratory), RAD (Radiology)
    Status: registered, partial, preliminary, final, amended
    """
    query = db.query(FHIRResource).filter(
        FHIRResource.resource_type == RESOURCE_TYPE,
        FHIRResource.deleted == False
    )

    if tenant_id:
        query = query.filter(FHIRResource.tenant_id == tenant_id)

    if patient_id:
        query = query.filter(
            FHIRResource.resource_data["subject"]["reference"].astext == f"Patient/{patient_id}"
        )

    if category:
        query = query.filter(
            FHIRResource.resource_data["category"][0]["coding"][0]["code"].astext == category
        )

    if status:
        query = query.filter(
            FHIRResource.resource_data["status"].astext == status
        )

    total = query.count()
    offset = (page - 1) * page_size
    reports = query.order_by(FHIRResource.last_updated.desc()).offset(offset).limit(page_size).all()

    return ReportListResponse(
        items=[_parse_report_response(rep) for rep in reports],
        total=total,
        page=page,
        page_size=page_size,
        has_next=offset + len(reports) < total,
        has_previous=page > 1
    )


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_diagnostic_report(
    report_data: ReportCreate,
    db: Session = Depends(get_db)
):
    """Create a new diagnostic report"""
    fhir_id = f"dr-{uuid4()}"
    resource_data = _build_fhir_diagnostic_report(report_data, fhir_id)

    report = FHIRResource(
        id=uuid4(),
        tenant_id=report_data.tenant_id,
        resource_type=RESOURCE_TYPE,
        fhir_id=fhir_id,
        version_id=1,
        resource_data=resource_data,
        search_tokens={
            "patient": [str(report_data.patient_id)],
            "category": [report_data.category],
            "status": [report_data.status],
            "code": [report_data.code.code]
        },
        created_at=datetime.utcnow(),
        last_updated=datetime.utcnow()
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    logger.info(f"Created diagnostic report: {report.id}")
    return _parse_report_response(report)


@router.get("/{report_id}", response_model=ReportResponse)
async def get_diagnostic_report(
    report_id: UUID,
    db: Session = Depends(get_db)
):
    """Get diagnostic report by ID"""
    report = db.query(FHIRResource).filter(
        FHIRResource.id == report_id,
        FHIRResource.resource_type == RESOURCE_TYPE,
        FHIRResource.deleted == False
    ).first()

    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diagnostic report not found")

    return _parse_report_response(report)

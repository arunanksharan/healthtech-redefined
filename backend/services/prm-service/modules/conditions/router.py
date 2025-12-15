"""
Conditions Router
API endpoints for patient conditions/diagnoses
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
    ConditionCreate,
    ConditionUpdate,
    ConditionResponse,
    ConditionListResponse,
    ConditionCode
)


router = APIRouter(prefix="/conditions", tags=["Conditions"])

RESOURCE_TYPE = "Condition"


def _build_fhir_condition(data: ConditionCreate, fhir_id: str) -> dict:
    """Build FHIR Condition resource from create data"""
    resource = {
        "resourceType": "Condition",
        "id": fhir_id,
        "clinicalStatus": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                "code": data.clinical_status
            }]
        },
        "verificationStatus": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                "code": data.verification_status
            }]
        },
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                "code": data.category
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

    if data.severity:
        resource["severity"] = {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": data.severity
            }]
        }

    if data.encounter_id:
        resource["encounter"] = {"reference": f"Encounter/{data.encounter_id}"}

    if data.recorder_id:
        resource["recorder"] = {"reference": f"Practitioner/{data.recorder_id}"}

    if data.onset_datetime:
        resource["onsetDateTime"] = data.onset_datetime.isoformat()

    if data.abatement_datetime:
        resource["abatementDateTime"] = data.abatement_datetime.isoformat()

    if data.note:
        resource["note"] = [{"text": data.note}]

    return resource


def _parse_condition_response(resource: FHIRResource) -> ConditionResponse:
    """Parse FHIRResource into ConditionResponse"""
    data = resource.resource_data

    # Extract code
    code_data = data.get("code", {}).get("coding", [{}])[0]
    code = ConditionCode(
        system=code_data.get("system", ""),
        code=code_data.get("code", ""),
        display=code_data.get("display")
    )

    # Extract statuses
    clinical_status = "active"
    if "clinicalStatus" in data:
        clinical_status = data["clinicalStatus"].get("coding", [{}])[0].get("code", "active")

    verification_status = "confirmed"
    if "verificationStatus" in data:
        verification_status = data["verificationStatus"].get("coding", [{}])[0].get("code", "confirmed")

    # Extract category
    category = "encounter-diagnosis"
    if "category" in data and data["category"]:
        category = data["category"][0].get("coding", [{}])[0].get("code", "encounter-diagnosis")

    # Extract severity
    severity = None
    if "severity" in data:
        severity = data["severity"].get("coding", [{}])[0].get("code")

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

    # Extract note
    note = None
    if "note" in data and data["note"]:
        note = data["note"][0].get("text")

    # Extract datetimes
    onset = None
    if "onsetDateTime" in data:
        try:
            onset = datetime.fromisoformat(data["onsetDateTime"].replace("Z", "+00:00"))
        except ValueError:
            pass

    abatement = None
    if "abatementDateTime" in data:
        try:
            abatement = datetime.fromisoformat(data["abatementDateTime"].replace("Z", "+00:00"))
        except ValueError:
            pass

    return ConditionResponse(
        id=resource.id,
        fhir_id=resource.fhir_id,
        tenant_id=resource.tenant_id,
        resource_type=RESOURCE_TYPE,
        patient_id=patient_id,
        encounter_id=encounter_id,
        clinical_status=clinical_status,
        verification_status=verification_status,
        category=category,
        severity=severity,
        code=code,
        onset_datetime=onset,
        abatement_datetime=abatement,
        note=note,
        created_at=resource.created_at,
        updated_at=resource.last_updated
    )


@router.get("", response_model=ConditionListResponse)
async def list_conditions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    patient_id: Optional[UUID] = Query(None, description="Filter by patient"),
    clinical_status: Optional[str] = Query(None, description="Filter by clinical status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    """
    List patient conditions/diagnoses

    Clinical status: active, recurrence, relapse, inactive, remission, resolved
    Category: problem-list-item, encounter-diagnosis
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

    if clinical_status:
        query = query.filter(
            FHIRResource.resource_data["clinicalStatus"]["coding"][0]["code"].astext == clinical_status
        )

    if category:
        query = query.filter(
            FHIRResource.resource_data["category"][0]["coding"][0]["code"].astext == category
        )

    total = query.count()
    offset = (page - 1) * page_size
    conditions = query.order_by(FHIRResource.last_updated.desc()).offset(offset).limit(page_size).all()

    return ConditionListResponse(
        items=[_parse_condition_response(cond) for cond in conditions],
        total=total,
        page=page,
        page_size=page_size,
        has_next=offset + len(conditions) < total,
        has_previous=page > 1
    )


@router.post("", response_model=ConditionResponse, status_code=status.HTTP_201_CREATED)
async def create_condition(
    cond_data: ConditionCreate,
    db: Session = Depends(get_db)
):
    """Record a new patient condition/diagnosis"""
    fhir_id = f"cond-{uuid4()}"
    resource_data = _build_fhir_condition(cond_data, fhir_id)

    condition = FHIRResource(
        id=uuid4(),
        tenant_id=cond_data.tenant_id,
        resource_type=RESOURCE_TYPE,
        fhir_id=fhir_id,
        version_id=1,
        resource_data=resource_data,
        search_tokens={
            "patient": [str(cond_data.patient_id)],
            "clinical-status": [cond_data.clinical_status],
            "code": [cond_data.code.code]
        },
        created_at=datetime.utcnow(),
        last_updated=datetime.utcnow()
    )

    db.add(condition)
    db.commit()
    db.refresh(condition)

    logger.info(f"Created condition: {condition.id}")
    return _parse_condition_response(condition)


@router.put("/{condition_id}", response_model=ConditionResponse)
async def update_condition(
    condition_id: UUID,
    update_data: ConditionUpdate,
    db: Session = Depends(get_db)
):
    """Update or resolve a condition"""
    condition = db.query(FHIRResource).filter(
        FHIRResource.id == condition_id,
        FHIRResource.resource_type == RESOURCE_TYPE,
        FHIRResource.deleted == False
    ).first()

    if not condition:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Condition not found")

    # Update resource_data
    resource_data = condition.resource_data.copy()

    if update_data.clinical_status:
        resource_data["clinicalStatus"] = {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                "code": update_data.clinical_status
            }]
        }

    if update_data.verification_status:
        resource_data["verificationStatus"] = {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                "code": update_data.verification_status
            }]
        }

    if update_data.severity:
        resource_data["severity"] = {
            "coding": [{"system": "http://snomed.info/sct", "code": update_data.severity}]
        }

    if update_data.abatement_datetime:
        resource_data["abatementDateTime"] = update_data.abatement_datetime.isoformat()

    if update_data.note:
        resource_data["note"] = [{"text": update_data.note}]

    condition.resource_data = resource_data
    condition.version_id += 1
    condition.last_updated = datetime.utcnow()

    db.commit()
    db.refresh(condition)

    logger.info(f"Updated condition: {condition_id}")
    return _parse_condition_response(condition)

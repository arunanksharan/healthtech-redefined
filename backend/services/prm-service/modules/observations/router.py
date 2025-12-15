"""
Observations Router
API endpoints for clinical observations (vitals, lab results)
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
    ObservationCreate,
    ObservationResponse,
    ObservationListResponse,
    ObservationCode,
    ObservationValue
)


router = APIRouter(prefix="/observations", tags=["Observations"])

RESOURCE_TYPE = "Observation"


def _build_fhir_observation(data: ObservationCreate, fhir_id: str) -> dict:
    """Build FHIR Observation resource from create data"""
    resource = {
        "resourceType": "Observation",
        "id": fhir_id,
        "status": data.status,
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                "code": data.category,
                "display": data.category.replace("-", " ").title()
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

    if data.value:
        if data.value.value is not None:
            resource["valueQuantity"] = {
                "value": data.value.value,
                "unit": data.value.unit,
                "system": data.value.system or "http://unitsofmeasure.org",
                "code": data.value.code
            }
        elif data.value.value_string:
            resource["valueString"] = data.value.value_string

    if data.encounter_id:
        resource["encounter"] = {"reference": f"Encounter/{data.encounter_id}"}

    if data.practitioner_id:
        resource["performer"] = [{"reference": f"Practitioner/{data.practitioner_id}"}]

    if data.effective_datetime:
        resource["effectiveDateTime"] = data.effective_datetime.isoformat()

    if data.interpretation:
        resource["interpretation"] = [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                "code": data.interpretation
            }]
        }]

    if data.note:
        resource["note"] = [{"text": data.note}]

    return resource


def _parse_observation_response(resource: FHIRResource) -> ObservationResponse:
    """Parse FHIRResource into ObservationResponse"""
    data = resource.resource
    # Note: resource.resource instead of resource.resource_data if using models.py definition?
    # models.py says 'resource = Column(JSONB, nullable=False)'
    # fhir_models.py said 'resource_data = Column(JSONB...)'
    # Let's check models.py again for exact column name for json data.
    
    # In Step 12121:
    # 597:     resource = Column(JSONB, nullable=False)
    # So the column is named 'resource'.
    
    # Extract code
    code_data = data.get("code", {}).get("coding", [{}])[0]
    code = ObservationCode(
        system=code_data.get("system", ""),
        code=code_data.get("code", ""),
        display=code_data.get("display")
    )

    # Extract value
    value = None
    if "valueQuantity" in data:
        vq = data["valueQuantity"]
        value = ObservationValue(
            value=vq.get("value"),
            unit=vq.get("unit"),
            system=vq.get("system"),
            code=vq.get("code")
        )
    elif "valueString" in data:
        value = ObservationValue(value_string=data["valueString"])

    # Extract category
    category = "vital-signs"
    if "category" in data and data["category"]:
        cat_coding = data["category"][0].get("coding", [{}])[0]
        category = cat_coding.get("code", "vital-signs")

    # Extract patient_id
    patient_id = None
    if "subject" in data:
        ref = data["subject"].get("reference", "")
        if ref.startswith("Patient/"):
            try:
                patient_id = UUID(ref.replace("Patient/", ""))
            except ValueError:
                pass

    # Extract interpretation
    interpretation = None
    if "interpretation" in data and data["interpretation"]:
        interp_coding = data["interpretation"][0].get("coding", [{}])[0]
        interpretation = interp_coding.get("code")

    # Extract note
    note = None
    if "note" in data and data["note"]:
        note = data["note"][0].get("text")

    # Extract effective datetime
    effective = None
    if "effectiveDateTime" in data:
        try:
            effective = datetime.fromisoformat(data["effectiveDateTime"].replace("Z", "+00:00"))
        except ValueError:
            pass

    return ObservationResponse(
        id=resource.id,
        fhir_id=resource.resource_id,
        tenant_id=resource.tenant_id,
        resource_type=RESOURCE_TYPE,
        patient_id=patient_id,
        status=data.get("status", "final"),
        category=category,
        code=code,
        value=value,
        effective_datetime=effective,
        interpretation=interpretation,
        note=note,
        created_at=resource.created_at,
        updated_at=resource.updated_at
    )


@router.get("", response_model=ObservationListResponse)
async def list_observations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    patient_id: Optional[UUID] = Query(None, description="Filter by patient"),
    category: Optional[str] = Query(None, description="Filter by category"),
    code: Optional[str] = Query(None, description="Filter by LOINC code"),
    db: Session = Depends(get_db)
):
    """
    List clinical observations with pagination and filters

    Categories: vital-signs, laboratory, imaging, procedure, survey
    """
    query = db.query(FHIRResource).filter(
        FHIRResource.resource_type == RESOURCE_TYPE,
        # FHIRResource.deleted is not present in models.py
    )

    if tenant_id:
        query = query.filter(FHIRResource.tenant_id == tenant_id)

    if patient_id:
        query = query.filter(
            FHIRResource.resource["subject"]["reference"].astext == f"Patient/{patient_id}"
        )

    if category:
        query = query.filter(
            FHIRResource.resource["category"][0]["coding"][0]["code"].astext == category
        )

    if code:
        query = query.filter(
            FHIRResource.resource["code"]["coding"][0]["code"].astext == code
        )

    total = query.count()
    offset = (page - 1) * page_size
    observations = query.order_by(FHIRResource.updated_at.desc()).offset(offset).limit(page_size).all()

    return ObservationListResponse(
        items=[_parse_observation_response(obs) for obs in observations],
        total=total,
        page=page,
        page_size=page_size,
        has_next=offset + len(observations) < total,
        has_previous=page > 1
    )


@router.post("", response_model=ObservationResponse, status_code=status.HTTP_201_CREATED)
async def create_observation(
    obs_data: ObservationCreate,
    db: Session = Depends(get_db)
):
    """Create a new clinical observation"""
    fhir_id = f"obs-{uuid4()}"
    resource_data = _build_fhir_observation(obs_data, fhir_id)

    observation = FHIRResource(
        id=uuid4(),
        tenant_id=obs_data.tenant_id,
        resource_type=RESOURCE_TYPE,
        resource_id=fhir_id,
        version=1,
        is_current=True,
        resource=resource_data,
        meta_data={
            "search_tokens": {
                "patient": [str(obs_data.patient_id)],
                "category": [obs_data.category],
                "code": [obs_data.code.code]
            }
        }
    )

    db.add(observation)
    db.commit()
    db.refresh(observation)

    logger.info(f"Created observation: {observation.id}")
    return _parse_observation_response(observation)


@router.get("/{observation_id}", response_model=ObservationResponse)
async def get_observation(
    observation_id: UUID,
    db: Session = Depends(get_db)
):
    """Get observation by ID"""
    observation = db.query(FHIRResource).filter(
        FHIRResource.id == observation_id,
        FHIRResource.resource_type == RESOURCE_TYPE,
    ).first()

    if not observation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Observation not found")

    return _parse_observation_response(observation)

"""
Medications Router
API endpoints for medication requests/prescriptions
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
    MedicationCreate,
    MedicationResponse,
    MedicationListResponse,
    MedicationCode,
    Dosage
)


router = APIRouter(prefix="/medications", tags=["Medications"])

RESOURCE_TYPE = "MedicationRequest"


def _build_fhir_medication_request(data: MedicationCreate, fhir_id: str) -> dict:
    """Build FHIR MedicationRequest resource from create data"""
    resource = {
        "resourceType": "MedicationRequest",
        "id": fhir_id,
        "status": data.status,
        "intent": data.intent,
        "medicationCodeableConcept": {
            "coding": [{
                "system": data.medication.system,
                "code": data.medication.code,
                "display": data.medication.display
            }]
        },
        "subject": {"reference": f"Patient/{data.patient_id}"},
    }

    if data.encounter_id:
        resource["encounter"] = {"reference": f"Encounter/{data.encounter_id}"}

    if data.requester_id:
        resource["requester"] = {"reference": f"Practitioner/{data.requester_id}"}

    if data.authored_on:
        resource["authoredOn"] = data.authored_on.isoformat()
    else:
        resource["authoredOn"] = datetime.utcnow().isoformat()

    if data.dosage:
        dosage_inst = {"text": data.dosage.text} if data.dosage.text else {}
        if data.dosage.timing:
            dosage_inst["timing"] = {"code": {"text": data.dosage.timing}}
        if data.dosage.route:
            dosage_inst["route"] = {"text": data.dosage.route}
        if data.dosage.dose_value is not None:
            dosage_inst["doseAndRate"] = [{
                "doseQuantity": {
                    "value": data.dosage.dose_value,
                    "unit": data.dosage.dose_unit or "mg"
                }
            }]
        resource["dosageInstruction"] = [dosage_inst]

    if data.quantity or data.days_supply:
        resource["dispenseRequest"] = {}
        if data.quantity:
            resource["dispenseRequest"]["quantity"] = {"value": data.quantity}
        if data.days_supply:
            resource["dispenseRequest"]["expectedSupplyDuration"] = {
                "value": data.days_supply,
                "unit": "days"
            }
        if data.refills is not None:
            resource["dispenseRequest"]["numberOfRepeatsAllowed"] = data.refills

    if data.note:
        resource["note"] = [{"text": data.note}]

    return resource


def _parse_medication_response(resource: FHIRResource) -> MedicationResponse:
    """Parse FHIRResource into MedicationResponse"""
    data = resource.resource_data

    # Extract medication code
    med_data = data.get("medicationCodeableConcept", {}).get("coding", [{}])[0]
    medication = MedicationCode(
        system=med_data.get("system", ""),
        code=med_data.get("code", ""),
        display=med_data.get("display")
    )

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

    # Extract requester_id
    requester_id = None
    if "requester" in data:
        ref = data["requester"].get("reference", "")
        if ref.startswith("Practitioner/"):
            try:
                requester_id = UUID(ref.replace("Practitioner/", ""))
            except ValueError:
                pass

    # Extract dosage
    dosage = None
    if "dosageInstruction" in data and data["dosageInstruction"]:
        di = data["dosageInstruction"][0]
        dosage = Dosage(
            text=di.get("text"),
            timing=di.get("timing", {}).get("code", {}).get("text"),
            route=di.get("route", {}).get("text")
        )
        if "doseAndRate" in di and di["doseAndRate"]:
            dq = di["doseAndRate"][0].get("doseQuantity", {})
            dosage.dose_value = dq.get("value")
            dosage.dose_unit = dq.get("unit")

    # Extract dispense info
    quantity = None
    days_supply = None
    refills = None
    if "dispenseRequest" in data:
        dr = data["dispenseRequest"]
        if "quantity" in dr:
            quantity = dr["quantity"].get("value")
        if "expectedSupplyDuration" in dr:
            days_supply = dr["expectedSupplyDuration"].get("value")
        refills = dr.get("numberOfRepeatsAllowed")

    # Extract authored_on
    authored_on = None
    if "authoredOn" in data:
        try:
            authored_on = datetime.fromisoformat(data["authoredOn"].replace("Z", "+00:00"))
        except ValueError:
            pass

    # Extract note
    note = None
    if "note" in data and data["note"]:
        note = data["note"][0].get("text")

    return MedicationResponse(
        id=resource.id,
        fhir_id=resource.fhir_id,
        tenant_id=resource.tenant_id,
        resource_type=RESOURCE_TYPE,
        patient_id=patient_id,
        encounter_id=encounter_id,
        requester_id=requester_id,
        status=data.get("status", "active"),
        intent=data.get("intent", "order"),
        medication=medication,
        dosage=dosage,
        quantity=quantity,
        days_supply=days_supply,
        refills=refills,
        authored_on=authored_on,
        note=note,
        created_at=resource.created_at,
        updated_at=resource.last_updated
    )


@router.get("", response_model=MedicationListResponse)
async def list_medications(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    patient_id: Optional[UUID] = Query(None, description="Filter by patient"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """
    List medication requests/prescriptions

    Status: active, on-hold, cancelled, completed, stopped
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

    if status:
        query = query.filter(
            FHIRResource.resource_data["status"].astext == status
        )

    total = query.count()
    offset = (page - 1) * page_size
    medications = query.order_by(FHIRResource.last_updated.desc()).offset(offset).limit(page_size).all()

    return MedicationListResponse(
        items=[_parse_medication_response(med) for med in medications],
        total=total,
        page=page,
        page_size=page_size,
        has_next=offset + len(medications) < total,
        has_previous=page > 1
    )


@router.post("", response_model=MedicationResponse, status_code=status.HTTP_201_CREATED)
async def create_medication(
    med_data: MedicationCreate,
    db: Session = Depends(get_db)
):
    """Prescribe a new medication"""
    fhir_id = f"medrx-{uuid4()}"
    resource_data = _build_fhir_medication_request(med_data, fhir_id)

    medication = FHIRResource(
        id=uuid4(),
        tenant_id=med_data.tenant_id,
        resource_type=RESOURCE_TYPE,
        fhir_id=fhir_id,
        version_id=1,
        resource_data=resource_data,
        search_tokens={
            "patient": [str(med_data.patient_id)],
            "status": [med_data.status],
            "medication": [med_data.medication.code]
        },
        created_at=datetime.utcnow(),
        last_updated=datetime.utcnow()
    )

    db.add(medication)
    db.commit()
    db.refresh(medication)

    logger.info(f"Created medication request: {medication.id}")
    return _parse_medication_response(medication)


@router.get("/{medication_id}", response_model=MedicationResponse)
async def get_medication(
    medication_id: UUID,
    db: Session = Depends(get_db)
):
    """Get medication prescription by ID"""
    medication = db.query(FHIRResource).filter(
        FHIRResource.id == medication_id,
        FHIRResource.resource_type == RESOURCE_TYPE,
        FHIRResource.deleted == False
    ).first()

    if not medication:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")

    return _parse_medication_response(medication)

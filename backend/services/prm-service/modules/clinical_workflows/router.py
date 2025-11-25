"""
Clinical Workflows Router

EPIC-006: Clinical Workflows API Endpoints
Comprehensive REST API for clinical workflow operations.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, Query, status, BackgroundTasks, Body
from sqlalchemy.orm import Session
from sqlalchemy import desc
from loguru import logger

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from shared.database.connection import get_db

from .models import (
    Prescription, LabOrder, LabResult, ImagingOrder, ImagingStudy,
    Referral, ClinicalNote, NoteTemplate, SmartPhrase,
    CarePlan, CareGoal, CareIntervention,
    ClinicalAlert, CDSRule, VitalSign, DischargeRecord,
)
from .schemas import (
    # Prescription schemas
    PrescriptionCreate, PrescriptionUpdate, PrescriptionResponse,
    PrescriptionListResponse, SignPrescriptionRequest, SendToPharmacyRequest,
    DrugSearchRequest, DrugInfo, InteractionCheckRequest, InteractionCheckResponse,
    # Lab schemas
    LabOrderCreate, LabOrderResponse, LabOrderListResponse, LabResultResponse,
    RecordSpecimenRequest, LabResultTrendResponse,
    # Imaging schemas
    ImagingOrderCreate, ImagingOrderResponse, ImagingOrderListResponse,
    ImagingStudyResponse, RadiologyReportResponse,
    # Referral schemas
    ReferralCreate, ReferralResponse, ReferralListResponse,
    ReferralMessageCreate, ReferralDocumentResponse, ProviderSearchRequest, ProviderResponse,
    # Documentation schemas
    ClinicalNoteCreate, ClinicalNoteUpdate, ClinicalNoteResponse, ClinicalNoteListResponse,
    SignNoteRequest, AddAddendumRequest,
    NoteTemplateCreate, NoteTemplateResponse, SmartPhraseCreate, SmartPhraseResponse,
    CodeSuggestionResponse,
    # Care Plan schemas
    CarePlanCreate, CarePlanResponse, CarePlanListResponse,
    CareGoalCreate, CareGoalResponse, GoalProgressCreate,
    CareInterventionCreate, CareInterventionResponse, CareTeamMemberCreate,
    # CDS schemas
    EvaluateAlertsRequest, ClinicalAlertResponse, ClinicalAlertListResponse,
    AcknowledgeAlertRequest, OverrideAlertRequest,
    CDSRuleCreate, CDSRuleResponse, PreventiveCareRecommendationResponse,
    # Vital Signs schemas
    VitalSignCreate, VitalSignResponse, VitalSignListResponse,
    VitalSignsBatchCreate, EarlyWarningScoreResponse, VitalTrendResponse,
    # Discharge schemas
    DischargeRecordCreate, DischargeRecordResponse, UpdateChecklistRequest,
    # Enums
    PrescriptionStatus, LabOrderStatus, ImagingOrderStatus, ReferralStatus,
    NoteStatus, CarePlanStatus, OrderPriority,
)
from .service import (
    prescription_service, lab_order_service, imaging_service,
    referral_service, documentation_service, care_plan_service,
    decision_support_service, vital_signs_service, discharge_service,
)

router = APIRouter(prefix="/api/v1/clinical", tags=["Clinical Workflows"])


# ==================== Health Check ====================

@router.get("/health")
async def clinical_health():
    """Clinical workflows health check."""
    return {
        "status": "healthy",
        "module": "clinical_workflows",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ==================== E-Prescribing (US-006.1) ====================

@router.post(
    "/prescriptions",
    response_model=PrescriptionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Prescriptions"],
)
async def create_prescription(
    data: PrescriptionCreate,
    db: Session = Depends(get_db),
):
    """Create a new prescription."""
    try:
        prescription = await prescription_service.create_prescription(db, data)
        return prescription
    except Exception as e:
        logger.error(f"Error creating prescription: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/prescriptions",
    response_model=PrescriptionListResponse,
    tags=["Prescriptions"],
)
async def list_prescriptions(
    tenant_id: UUID = Query(...),
    patient_id: Optional[UUID] = Query(None),
    prescriber_id: Optional[UUID] = Query(None),
    status: Optional[PrescriptionStatus] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List prescriptions with filters."""
    query = db.query(Prescription).filter(Prescription.tenant_id == tenant_id)

    if patient_id:
        query = query.filter(Prescription.patient_id == patient_id)
    if prescriber_id:
        query = query.filter(Prescription.prescriber_id == prescriber_id)
    if status:
        query = query.filter(Prescription.status == status.value)

    total = query.count()
    prescriptions = query.order_by(desc(Prescription.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return PrescriptionListResponse(
        total=total,
        prescriptions=prescriptions,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
        has_previous=page > 1,
    )


@router.get(
    "/prescriptions/{prescription_id}",
    response_model=PrescriptionResponse,
    tags=["Prescriptions"],
)
async def get_prescription(
    prescription_id: UUID,
    db: Session = Depends(get_db),
):
    """Get prescription by ID."""
    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id
    ).first()

    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    return prescription


@router.post(
    "/prescriptions/{prescription_id}/interactions/check",
    response_model=InteractionCheckResponse,
    tags=["Prescriptions"],
)
async def check_drug_interactions(
    prescription_id: UUID,
    request: InteractionCheckRequest,
    db: Session = Depends(get_db),
):
    """Check drug interactions for a prescription."""
    prescription = db.query(Prescription).filter(
        Prescription.id == prescription_id
    ).first()

    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    result = await prescription_service.check_interactions(
        db,
        prescription.tenant_id,
        request.patient_id,
        request.rxnorm_code,
        request.current_medications,
    )

    # Update prescription flags
    prescription.interactions_checked = True
    prescription.allergies_checked = True
    db.commit()

    return result


@router.post(
    "/prescriptions/{prescription_id}/sign",
    response_model=PrescriptionResponse,
    tags=["Prescriptions"],
)
async def sign_prescription(
    prescription_id: UUID,
    request: SignPrescriptionRequest,
    db: Session = Depends(get_db),
):
    """Sign and finalize a prescription."""
    try:
        prescription = await prescription_service.sign_prescription(
            db, prescription_id, request.signer_id
        )
        return prescription
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/prescriptions/{prescription_id}/send",
    response_model=PrescriptionResponse,
    tags=["Prescriptions"],
)
async def send_to_pharmacy(
    prescription_id: UUID,
    request: SendToPharmacyRequest,
    db: Session = Depends(get_db),
):
    """Send prescription to pharmacy via e-prescribing network."""
    try:
        prescription = await prescription_service.send_to_pharmacy(
            db, prescription_id, request.pharmacy_id, request.pharmacy_ncpdp
        )
        return prescription
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/medications/search",
    response_model=List[DrugInfo],
    tags=["Prescriptions"],
)
async def search_drugs(request: DrugSearchRequest):
    """Search drug database."""
    # Mock implementation - in production, integrate with RxNorm API
    results = []
    query = request.query.lower()

    for code, info in prescription_service.DRUG_DATABASE.items():
        if query in info["name"].lower() or query in info["generic"].lower():
            results.append(DrugInfo(
                rxnorm_code=code,
                name=info["name"],
                generic_name=info["generic"],
                brand_names=[],
                drug_class=info.get("class"),
                schedule=info.get("schedule"),
            ))

    return results[:request.limit]


# ==================== Laboratory Orders (US-006.2) ====================

@router.post(
    "/lab-orders",
    response_model=LabOrderResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Lab Orders"],
)
async def create_lab_order(
    data: LabOrderCreate,
    db: Session = Depends(get_db),
):
    """Create a new lab order."""
    order = await lab_order_service.create_order(db, data)
    return order


@router.get(
    "/lab-orders",
    response_model=LabOrderListResponse,
    tags=["Lab Orders"],
)
async def list_lab_orders(
    tenant_id: UUID = Query(...),
    patient_id: Optional[UUID] = Query(None),
    status: Optional[LabOrderStatus] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List lab orders with filters."""
    query = db.query(LabOrder).filter(LabOrder.tenant_id == tenant_id)

    if patient_id:
        query = query.filter(LabOrder.patient_id == patient_id)
    if status:
        query = query.filter(LabOrder.status == status.value)

    total = query.count()
    orders = query.order_by(desc(LabOrder.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return LabOrderListResponse(
        total=total,
        orders=orders,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
        has_previous=page > 1,
    )


@router.get(
    "/lab-orders/{order_id}",
    response_model=LabOrderResponse,
    tags=["Lab Orders"],
)
async def get_lab_order(
    order_id: UUID,
    db: Session = Depends(get_db),
):
    """Get lab order by ID."""
    order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Lab order not found")
    return order


@router.post(
    "/lab-orders/{order_id}/submit",
    response_model=LabOrderResponse,
    tags=["Lab Orders"],
)
async def submit_lab_order(
    order_id: UUID,
    db: Session = Depends(get_db),
):
    """Submit lab order to performing lab."""
    try:
        order = await lab_order_service.submit_order(db, order_id)
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/lab-orders/{order_id}/specimen",
    response_model=LabOrderResponse,
    tags=["Lab Orders"],
)
async def record_specimen_collection(
    order_id: UUID,
    request: RecordSpecimenRequest,
    db: Session = Depends(get_db),
):
    """Record specimen collection for lab order."""
    try:
        order = await lab_order_service.record_specimen_collection(
            db, order_id, request.collected_by, request.collection_time
        )
        return order
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/lab-orders/{order_id}/results",
    response_model=List[LabResultResponse],
    tags=["Lab Orders"],
)
async def get_lab_results(
    order_id: UUID,
    db: Session = Depends(get_db),
):
    """Get results for a lab order."""
    results = db.query(LabResult).filter(LabResult.order_id == order_id).all()
    return results


@router.get(
    "/lab-results/trends/{patient_id}",
    response_model=LabResultTrendResponse,
    tags=["Lab Orders"],
)
async def get_lab_result_trends(
    patient_id: UUID,
    tenant_id: UUID = Query(...),
    loinc_code: str = Query(...),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Get historical trends for a lab test."""
    values = await lab_order_service.get_result_trends(
        db, tenant_id, patient_id, loinc_code, limit
    )

    # Get test name from first result
    test_name = ""
    result = db.query(LabResult).filter(
        LabResult.loinc_code == loinc_code
    ).first()
    if result:
        test_name = result.test_name

    return LabResultTrendResponse(
        loinc_code=loinc_code,
        test_name=test_name,
        unit=values[0]["unit"] if values else "",
        values=values,
    )


# ==================== Imaging (US-006.3) ====================

@router.post(
    "/imaging-orders",
    response_model=ImagingOrderResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Imaging"],
)
async def create_imaging_order(
    data: ImagingOrderCreate,
    db: Session = Depends(get_db),
):
    """Create an imaging order."""
    order = await imaging_service.create_order(db, data)
    return order


@router.get(
    "/imaging-orders",
    response_model=ImagingOrderListResponse,
    tags=["Imaging"],
)
async def list_imaging_orders(
    tenant_id: UUID = Query(...),
    patient_id: Optional[UUID] = Query(None),
    status: Optional[ImagingOrderStatus] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List imaging orders with filters."""
    query = db.query(ImagingOrder).filter(ImagingOrder.tenant_id == tenant_id)

    if patient_id:
        query = query.filter(ImagingOrder.patient_id == patient_id)
    if status:
        query = query.filter(ImagingOrder.status == status.value)

    total = query.count()
    orders = query.order_by(desc(ImagingOrder.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return ImagingOrderListResponse(
        total=total,
        orders=orders,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
        has_previous=page > 1,
    )


@router.get(
    "/imaging-orders/{order_id}",
    response_model=ImagingOrderResponse,
    tags=["Imaging"],
)
async def get_imaging_order(
    order_id: UUID,
    db: Session = Depends(get_db),
):
    """Get imaging order by ID."""
    order = db.query(ImagingOrder).filter(ImagingOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Imaging order not found")
    return order


@router.get(
    "/imaging-studies/{patient_id}",
    response_model=List[ImagingStudyResponse],
    tags=["Imaging"],
)
async def get_patient_imaging_studies(
    patient_id: UUID,
    tenant_id: UUID = Query(...),
    modality: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get imaging studies for a patient."""
    query = db.query(ImagingStudy).filter(
        ImagingStudy.tenant_id == tenant_id,
        ImagingStudy.patient_id == patient_id,
    )

    if modality:
        query = query.filter(ImagingStudy.modality == modality)

    studies = query.order_by(desc(ImagingStudy.study_datetime)).limit(limit).all()
    return studies


@router.get(
    "/imaging/cumulative-dose/{patient_id}",
    tags=["Imaging"],
)
async def get_cumulative_radiation_dose(
    patient_id: UUID,
    tenant_id: UUID = Query(...),
    months: int = Query(12, ge=1, le=60),
    db: Session = Depends(get_db),
):
    """Get cumulative radiation dose for patient."""
    return await imaging_service.get_cumulative_dose(db, tenant_id, patient_id, months)


# ==================== Referrals (US-006.4) ====================

@router.post(
    "/referrals",
    response_model=ReferralResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Referrals"],
)
async def create_referral(
    data: ReferralCreate,
    db: Session = Depends(get_db),
):
    """Create a new referral."""
    referral = await referral_service.create_referral(db, data)
    return referral


@router.get(
    "/referrals",
    response_model=ReferralListResponse,
    tags=["Referrals"],
)
async def list_referrals(
    tenant_id: UUID = Query(...),
    patient_id: Optional[UUID] = Query(None),
    referring_provider_id: Optional[UUID] = Query(None),
    status: Optional[ReferralStatus] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List referrals with filters."""
    query = db.query(Referral).filter(Referral.tenant_id == tenant_id)

    if patient_id:
        query = query.filter(Referral.patient_id == patient_id)
    if referring_provider_id:
        query = query.filter(Referral.referring_provider_id == referring_provider_id)
    if status:
        query = query.filter(Referral.status == status.value)

    total = query.count()
    referrals = query.order_by(desc(Referral.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return ReferralListResponse(
        total=total,
        referrals=referrals,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
        has_previous=page > 1,
    )


@router.get(
    "/referrals/{referral_id}",
    response_model=ReferralResponse,
    tags=["Referrals"],
)
async def get_referral(
    referral_id: UUID,
    db: Session = Depends(get_db),
):
    """Get referral by ID."""
    referral = db.query(Referral).filter(Referral.id == referral_id).first()
    if not referral:
        raise HTTPException(status_code=404, detail="Referral not found")
    return referral


@router.post(
    "/referrals/{referral_id}/submit",
    response_model=ReferralResponse,
    tags=["Referrals"],
)
async def submit_referral(
    referral_id: UUID,
    db: Session = Depends(get_db),
):
    """Submit referral to receiving provider."""
    try:
        referral = await referral_service.submit_referral(db, referral_id)
        return referral
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/referrals/{referral_id}/complete",
    response_model=ReferralResponse,
    tags=["Referrals"],
)
async def complete_referral(
    referral_id: UUID,
    consultation_notes: str = Body(...),
    recommendations: Optional[str] = Body(None),
    follow_up_needed: bool = Body(False),
    db: Session = Depends(get_db),
):
    """Complete referral with consultation response."""
    try:
        referral = await referral_service.complete_referral(
            db, referral_id, consultation_notes, recommendations, follow_up_needed
        )
        return referral
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== Clinical Documentation (US-006.5) ====================

@router.post(
    "/clinical-notes",
    response_model=ClinicalNoteResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Documentation"],
)
async def create_clinical_note(
    data: ClinicalNoteCreate,
    db: Session = Depends(get_db),
):
    """Create a clinical note."""
    note = await documentation_service.create_note(db, data)
    return note


@router.get(
    "/clinical-notes",
    response_model=ClinicalNoteListResponse,
    tags=["Documentation"],
)
async def list_clinical_notes(
    tenant_id: UUID = Query(...),
    patient_id: Optional[UUID] = Query(None),
    encounter_id: Optional[UUID] = Query(None),
    note_type: Optional[str] = Query(None),
    status: Optional[NoteStatus] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List clinical notes with filters."""
    query = db.query(ClinicalNote).filter(ClinicalNote.tenant_id == tenant_id)

    if patient_id:
        query = query.filter(ClinicalNote.patient_id == patient_id)
    if encounter_id:
        query = query.filter(ClinicalNote.encounter_id == encounter_id)
    if note_type:
        query = query.filter(ClinicalNote.note_type == note_type)
    if status:
        query = query.filter(ClinicalNote.status == status.value)

    total = query.count()
    notes = query.order_by(desc(ClinicalNote.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return ClinicalNoteListResponse(
        total=total,
        notes=notes,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
        has_previous=page > 1,
    )


@router.get(
    "/clinical-notes/{note_id}",
    response_model=ClinicalNoteResponse,
    tags=["Documentation"],
)
async def get_clinical_note(
    note_id: UUID,
    db: Session = Depends(get_db),
):
    """Get clinical note by ID."""
    note = db.query(ClinicalNote).filter(ClinicalNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Clinical note not found")
    return note


@router.patch(
    "/clinical-notes/{note_id}",
    response_model=ClinicalNoteResponse,
    tags=["Documentation"],
)
async def update_clinical_note(
    note_id: UUID,
    data: ClinicalNoteUpdate,
    db: Session = Depends(get_db),
):
    """Update a clinical note."""
    note = db.query(ClinicalNote).filter(ClinicalNote.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Clinical note not found")

    if note.status in ["signed", "cosigned"]:
        raise HTTPException(status_code=400, detail="Cannot update signed notes")

    if data.title is not None:
        note.title = data.title
    if data.content is not None:
        note.content = data.content
    if data.structured_content is not None:
        note.structured_content = data.structured_content.dict()
    if data.diagnosis_codes is not None:
        note.diagnosis_codes = data.diagnosis_codes
    if data.procedure_codes is not None:
        note.procedure_codes = data.procedure_codes

    note.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(note)

    return note


@router.post(
    "/clinical-notes/{note_id}/sign",
    response_model=ClinicalNoteResponse,
    tags=["Documentation"],
)
async def sign_clinical_note(
    note_id: UUID,
    request: SignNoteRequest,
    db: Session = Depends(get_db),
):
    """Sign a clinical note."""
    try:
        note = await documentation_service.sign_note(db, note_id, request.signer_id)
        return note
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/clinical-notes/{note_id}/addendum",
    response_model=ClinicalNoteResponse,
    tags=["Documentation"],
)
async def add_addendum(
    note_id: UUID,
    request: AddAddendumRequest,
    db: Session = Depends(get_db),
):
    """Add addendum to a signed note."""
    try:
        note = await documentation_service.add_addendum(
            db, note_id, request.author_id, request.content
        )
        return note
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/clinical-notes/suggest-codes",
    response_model=List[CodeSuggestionResponse],
    tags=["Documentation"],
)
async def suggest_codes(
    content: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    """AI-powered code suggestions from note content."""
    suggestions = await documentation_service.suggest_codes(db, content)
    return suggestions


@router.get(
    "/note-templates",
    response_model=List[NoteTemplateResponse],
    tags=["Documentation"],
)
async def list_note_templates(
    tenant_id: UUID = Query(...),
    note_type: Optional[str] = Query(None),
    specialty: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List note templates."""
    query = db.query(NoteTemplate).filter(
        NoteTemplate.tenant_id == tenant_id,
        NoteTemplate.is_active == True,
    )

    if note_type:
        query = query.filter(NoteTemplate.note_type == note_type)
    if specialty:
        query = query.filter(NoteTemplate.specialty == specialty)

    return query.all()


@router.post(
    "/note-templates",
    response_model=NoteTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Documentation"],
)
async def create_note_template(
    data: NoteTemplateCreate,
    db: Session = Depends(get_db),
):
    """Create a note template."""
    from uuid import uuid4

    template = NoteTemplate(
        id=uuid4(),
        tenant_id=data.tenant_id,
        name=data.name,
        note_type=data.note_type.value,
        specialty=data.specialty,
        sections=data.sections,
        default_content=data.default_content,
    )

    db.add(template)
    db.commit()
    db.refresh(template)

    return template


@router.get(
    "/smart-phrases",
    response_model=List[SmartPhraseResponse],
    tags=["Documentation"],
)
async def list_smart_phrases(
    tenant_id: UUID = Query(...),
    owner_id: Optional[UUID] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """List smart phrases/macros."""
    from sqlalchemy import or_

    query = db.query(SmartPhrase).filter(
        SmartPhrase.tenant_id == tenant_id,
        SmartPhrase.is_active == True,
    )

    # Include shared phrases and owner's phrases
    if owner_id:
        query = query.filter(
            or_(SmartPhrase.owner_id == None, SmartPhrase.owner_id == owner_id)
        )
    else:
        query = query.filter(SmartPhrase.owner_id == None)

    if category:
        query = query.filter(SmartPhrase.category == category)

    return query.all()


# ==================== Care Plans (US-006.7) ====================

@router.post(
    "/care-plans",
    response_model=CarePlanResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Care Plans"],
)
async def create_care_plan(
    data: CarePlanCreate,
    db: Session = Depends(get_db),
):
    """Create a care plan with goals and interventions."""
    plan = await care_plan_service.create_care_plan(db, data)
    return plan


@router.get(
    "/care-plans",
    response_model=CarePlanListResponse,
    tags=["Care Plans"],
)
async def list_care_plans(
    tenant_id: UUID = Query(...),
    patient_id: Optional[UUID] = Query(None),
    status: Optional[CarePlanStatus] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List care plans with filters."""
    query = db.query(CarePlan).filter(CarePlan.tenant_id == tenant_id)

    if patient_id:
        query = query.filter(CarePlan.patient_id == patient_id)
    if status:
        query = query.filter(CarePlan.status == status.value)

    total = query.count()
    plans = query.order_by(desc(CarePlan.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return CarePlanListResponse(
        total=total,
        care_plans=plans,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
        has_previous=page > 1,
    )


@router.get(
    "/care-plans/{plan_id}",
    response_model=CarePlanResponse,
    tags=["Care Plans"],
)
async def get_care_plan(
    plan_id: UUID,
    db: Session = Depends(get_db),
):
    """Get care plan by ID."""
    plan = db.query(CarePlan).filter(CarePlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Care plan not found")
    return plan


@router.post(
    "/care-plans/{plan_id}/activate",
    response_model=CarePlanResponse,
    tags=["Care Plans"],
)
async def activate_care_plan(
    plan_id: UUID,
    db: Session = Depends(get_db),
):
    """Activate a care plan."""
    try:
        plan = await care_plan_service.activate_care_plan(db, plan_id)
        return plan
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/care-plans/{plan_id}/goals",
    response_model=List[CareGoalResponse],
    tags=["Care Plans"],
)
async def get_care_plan_goals(
    plan_id: UUID,
    db: Session = Depends(get_db),
):
    """Get goals for a care plan."""
    goals = db.query(CareGoal).filter(CareGoal.care_plan_id == plan_id).all()
    return goals


@router.post(
    "/care-plans/{plan_id}/goals/{goal_id}/progress",
    tags=["Care Plans"],
)
async def record_goal_progress(
    plan_id: UUID,
    goal_id: UUID,
    data: GoalProgressCreate,
    db: Session = Depends(get_db),
):
    """Record progress toward a care goal."""
    try:
        progress = await care_plan_service.record_goal_progress(
            db, goal_id, data.measure, data.value,
            data.recorded_by, data.unit, data.notes
        )
        return {"progress_id": str(progress.id), "achievement_status": progress.achievement_status}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/care-plans/{plan_id}/interventions",
    response_model=List[CareInterventionResponse],
    tags=["Care Plans"],
)
async def get_care_plan_interventions(
    plan_id: UUID,
    db: Session = Depends(get_db),
):
    """Get interventions for a care plan."""
    interventions = db.query(CareIntervention).filter(
        CareIntervention.care_plan_id == plan_id
    ).all()
    return interventions


# ==================== Clinical Decision Support (US-006.9) ====================

@router.post(
    "/alerts/evaluate",
    response_model=List[ClinicalAlertResponse],
    tags=["Decision Support"],
)
async def evaluate_alerts(
    request: EvaluateAlertsRequest,
    tenant_id: UUID = Query(...),
    db: Session = Depends(get_db),
):
    """Evaluate CDS rules and generate alerts for patient."""
    alerts = await decision_support_service.evaluate_alerts(
        db, tenant_id, request.patient_id, request.context
    )
    return alerts


@router.get(
    "/alerts",
    response_model=ClinicalAlertListResponse,
    tags=["Decision Support"],
)
async def list_alerts(
    tenant_id: UUID = Query(...),
    patient_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List clinical alerts."""
    query = db.query(ClinicalAlert).filter(ClinicalAlert.tenant_id == tenant_id)

    if patient_id:
        query = query.filter(ClinicalAlert.patient_id == patient_id)
    if status:
        query = query.filter(ClinicalAlert.status == status)
    if severity:
        query = query.filter(ClinicalAlert.severity == severity)

    total = query.count()
    alerts = query.order_by(desc(ClinicalAlert.created_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return ClinicalAlertListResponse(
        total=total,
        alerts=alerts,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
        has_previous=page > 1,
    )


@router.post(
    "/alerts/{alert_id}/acknowledge",
    response_model=ClinicalAlertResponse,
    tags=["Decision Support"],
)
async def acknowledge_alert(
    alert_id: UUID,
    request: AcknowledgeAlertRequest,
    db: Session = Depends(get_db),
):
    """Acknowledge a clinical alert."""
    try:
        alert = await decision_support_service.acknowledge_alert(
            db, alert_id, request.user_id
        )
        return alert
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/alerts/{alert_id}/override",
    response_model=ClinicalAlertResponse,
    tags=["Decision Support"],
)
async def override_alert(
    alert_id: UUID,
    request: OverrideAlertRequest,
    db: Session = Depends(get_db),
):
    """Override a clinical alert with reason."""
    try:
        alert = await decision_support_service.override_alert(
            db, alert_id, request.user_id, request.reason
        )
        return alert
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/cds-rules",
    response_model=CDSRuleResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Decision Support"],
)
async def create_cds_rule(
    data: CDSRuleCreate,
    db: Session = Depends(get_db),
):
    """Create a CDS rule."""
    from uuid import uuid4

    rule = CDSRule(
        id=uuid4(),
        tenant_id=data.tenant_id,
        name=data.name,
        description=data.description,
        category=data.category.value,
        conditions=data.conditions,
        alert_severity=data.alert_severity.value,
        alert_title_template=data.alert_title_template,
        alert_message_template=data.alert_message_template,
        suggested_actions=data.suggested_actions,
    )

    db.add(rule)
    db.commit()
    db.refresh(rule)

    return rule


@router.get(
    "/cds-rules",
    response_model=List[CDSRuleResponse],
    tags=["Decision Support"],
)
async def list_cds_rules(
    tenant_id: UUID = Query(...),
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """List CDS rules."""
    query = db.query(CDSRule).filter(CDSRule.tenant_id == tenant_id)

    if category:
        query = query.filter(CDSRule.category == category)
    if is_active is not None:
        query = query.filter(CDSRule.is_active == is_active)

    return query.order_by(CDSRule.priority).all()


# ==================== Vital Signs (US-006.10) ====================

@router.post(
    "/vital-signs",
    response_model=VitalSignResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Vital Signs"],
)
async def record_vital_sign(
    data: VitalSignCreate,
    db: Session = Depends(get_db),
):
    """Record a vital sign measurement."""
    vital = await vital_signs_service.record_vital_sign(db, data)
    return vital


@router.post(
    "/vital-signs/batch",
    response_model=List[VitalSignResponse],
    status_code=status.HTTP_201_CREATED,
    tags=["Vital Signs"],
)
async def record_vital_signs_batch(
    data: VitalSignsBatchCreate,
    db: Session = Depends(get_db),
):
    """Record multiple vital signs at once."""
    from .schemas import VitalType

    vitals = []
    for v in data.vitals:
        vital_data = VitalSignCreate(
            tenant_id=data.tenant_id,
            patient_id=data.patient_id,
            encounter_id=data.encounter_id,
            vital_type=VitalType(v["vital_type"]),
            value=v.get("value"),
            value_string=v.get("value_string"),
            unit=v.get("unit", ""),
            systolic=v.get("systolic"),
            diastolic=v.get("diastolic"),
            recorded_by=data.recorded_by,
            method=v.get("method"),
            position=v.get("position"),
        )
        vital = await vital_signs_service.record_vital_sign(db, vital_data)
        vitals.append(vital)

    return vitals


@router.get(
    "/vital-signs",
    response_model=VitalSignListResponse,
    tags=["Vital Signs"],
)
async def list_vital_signs(
    tenant_id: UUID = Query(...),
    patient_id: UUID = Query(...),
    encounter_id: Optional[UUID] = Query(None),
    vital_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List vital signs for a patient."""
    query = db.query(VitalSign).filter(
        VitalSign.tenant_id == tenant_id,
        VitalSign.patient_id == patient_id,
    )

    if encounter_id:
        query = query.filter(VitalSign.encounter_id == encounter_id)
    if vital_type:
        query = query.filter(VitalSign.vital_type == vital_type)

    total = query.count()
    vitals = query.order_by(desc(VitalSign.recorded_at)).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return VitalSignListResponse(
        total=total,
        vital_signs=vitals,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
        has_previous=page > 1,
    )


@router.get(
    "/vital-signs/trends/{patient_id}",
    response_model=VitalTrendResponse,
    tags=["Vital Signs"],
)
async def get_vital_trends(
    patient_id: UUID,
    tenant_id: UUID = Query(...),
    vital_type: str = Query(...),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get vital sign trends for a patient."""
    values = await vital_signs_service.get_vital_trends(
        db, tenant_id, patient_id, vital_type, limit
    )

    # Get unit from first vital
    unit = ""
    vital = db.query(VitalSign).filter(
        VitalSign.patient_id == patient_id,
        VitalSign.vital_type == vital_type,
    ).first()
    if vital:
        unit = vital.unit or ""

    return VitalTrendResponse(
        vital_type=vital_type,
        unit=unit,
        values=values,
    )


@router.post(
    "/vital-signs/early-warning-score/{patient_id}",
    response_model=EarlyWarningScoreResponse,
    tags=["Vital Signs"],
)
async def calculate_early_warning_score(
    patient_id: UUID,
    tenant_id: UUID = Query(...),
    encounter_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
):
    """Calculate early warning score (NEWS) for patient."""
    ews = await vital_signs_service.calculate_early_warning_score(
        db, tenant_id, patient_id, encounter_id
    )
    return ews


# ==================== Discharge Management (US-006.8) ====================

@router.post(
    "/discharge",
    response_model=DischargeRecordResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Discharge"],
)
async def create_discharge_record(
    data: DischargeRecordCreate,
    db: Session = Depends(get_db),
):
    """Create a discharge record."""
    record = await discharge_service.create_discharge_record(db, data)
    return record


@router.get(
    "/discharge/{record_id}",
    response_model=DischargeRecordResponse,
    tags=["Discharge"],
)
async def get_discharge_record(
    record_id: UUID,
    db: Session = Depends(get_db),
):
    """Get discharge record by ID."""
    record = db.query(DischargeRecord).filter(DischargeRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Discharge record not found")
    return record


@router.patch(
    "/discharge/{record_id}/checklist",
    response_model=DischargeRecordResponse,
    tags=["Discharge"],
)
async def update_discharge_checklist(
    record_id: UUID,
    request: UpdateChecklistRequest,
    db: Session = Depends(get_db),
):
    """Update a discharge checklist item."""
    try:
        record = await discharge_service.update_checklist_item(
            db, record_id, request.item_id, request.is_completed,
            request.completed_by, request.notes
        )
        return record
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/discharge/{record_id}/complete",
    response_model=DischargeRecordResponse,
    tags=["Discharge"],
)
async def complete_discharge(
    record_id: UUID,
    completed_by: UUID = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    """Complete the discharge process."""
    try:
        record = await discharge_service.complete_discharge(db, record_id, completed_by)
        return record
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

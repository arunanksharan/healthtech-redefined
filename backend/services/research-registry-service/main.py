"""
Research Registry Service - Port 8026
Disease registries, enrollments, and longitudinal data tracking
"""
import logging
from datetime import datetime, date
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import Session, sessionmaker

from shared.database.models import (
    Registry, RegistryCriteria, RegistryEnrollment,
    RegistryDataElement, RegistryDataValue, Patient, Tenant
)
from shared.events.types import EventType
from shared.events.publisher import publish_event
from schemas import (
    RegistryCreate, RegistryUpdate, RegistryResponse,
    RegistryCriteriaCreate, RegistryCriteriaResponse,
    RegistryEnrollmentCreate, RegistryEnrollmentUpdate, RegistryEnrollmentResponse,
    RegistryDataElementCreate, RegistryDataElementResponse,
    RegistryDataValueCreate, RegistryDataValueResponse,
    RegistryDataRefreshRequest
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://user:password@localhost:5432/healthtech"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(title="Research Registry Service", version="0.1.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Registry Endpoints
@app.post("/api/v1/registries", response_model=RegistryResponse, status_code=201, tags=["Registries"])
async def create_registry(registry_data: RegistryCreate, db: Session = Depends(get_db), current_user_id: UUID = None):
    """Create a new disease/condition registry"""
    # Check for duplicate code
    existing = db.query(Registry).filter(and_(
        Registry.tenant_id == registry_data.tenant_id,
        Registry.code == registry_data.code
    )).first()
    if existing:
        raise HTTPException(status_code=400, detail="Registry code already exists")

    registry = Registry(
        tenant_id=registry_data.tenant_id,
        code=registry_data.code,
        name=registry_data.name,
        description=registry_data.description,
        category=registry_data.category,
        status=registry_data.status,
        inclusion_criteria=registry_data.inclusion_criteria,
        exclusion_criteria=registry_data.exclusion_criteria
    )
    db.add(registry)
    db.commit()
    db.refresh(registry)

    await publish_event(EventType.REGISTRY_CREATED, {
        "registry_id": str(registry.id),
        "code": registry.code,
        "name": registry.name,
        "category": registry.category
    })

    logger.info(f"Registry created: {registry.code}")
    return registry

@app.get("/api/v1/registries", response_model=List[RegistryResponse], tags=["Registries"])
async def list_registries(
    tenant_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List all registries with optional filters"""
    query = db.query(Registry)
    if tenant_id:
        query = query.filter(Registry.tenant_id == tenant_id)
    if status:
        query = query.filter(Registry.status == status)
    if category:
        query = query.filter(Registry.category == category)
    return query.order_by(Registry.created_at.desc()).all()

@app.get("/api/v1/registries/{registry_id}", response_model=RegistryResponse, tags=["Registries"])
async def get_registry(registry_id: UUID, db: Session = Depends(get_db)):
    """Get registry details"""
    registry = db.query(Registry).filter(Registry.id == registry_id).first()
    if not registry:
        raise HTTPException(status_code=404, detail="Registry not found")
    return registry

@app.put("/api/v1/registries/{registry_id}", response_model=RegistryResponse, tags=["Registries"])
async def update_registry(
    registry_id: UUID,
    registry_data: RegistryUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Update registry details"""
    registry = db.query(Registry).filter(Registry.id == registry_id).first()
    if not registry:
        raise HTTPException(status_code=404, detail="Registry not found")

    update_data = registry_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(registry, field, value)

    registry.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(registry)

    await publish_event(EventType.REGISTRY_UPDATED, {
        "registry_id": str(registry.id),
        "code": registry.code,
        "updated_fields": list(update_data.keys())
    })

    logger.info(f"Registry updated: {registry.code}")
    return registry

# Registry Criteria Endpoints
@app.post("/api/v1/registries/{registry_id}/criteria", response_model=RegistryCriteriaResponse, status_code=201, tags=["Registry Criteria"])
async def add_registry_criterion(
    registry_id: UUID,
    criteria_data: RegistryCriteriaCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Add inclusion/exclusion criterion to registry"""
    # Verify registry exists
    registry = db.query(Registry).filter(Registry.id == registry_id).first()
    if not registry:
        raise HTTPException(status_code=404, detail="Registry not found")

    # Ensure criterion belongs to the registry
    if criteria_data.registry_id != registry_id:
        raise HTTPException(status_code=400, detail="Registry ID mismatch")

    criterion = RegistryCriteria(
        registry_id=criteria_data.registry_id,
        criterion_type=criteria_data.criterion_type,
        category=criteria_data.category,
        logic_expression=criteria_data.logic_expression,
        description=criteria_data.description
    )
    db.add(criterion)
    db.commit()
    db.refresh(criterion)

    logger.info(f"Registry criterion added: {registry.code} - {criterion.category}")
    return criterion

@app.get("/api/v1/registries/{registry_id}/criteria", response_model=List[RegistryCriteriaResponse], tags=["Registry Criteria"])
async def list_registry_criteria(
    registry_id: UUID,
    criterion_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List all criteria for a registry"""
    query = db.query(RegistryCriteria).filter(RegistryCriteria.registry_id == registry_id)
    if criterion_type:
        query = query.filter(RegistryCriteria.criterion_type == criterion_type)
    return query.all()

# Registry Enrollment Endpoints
@app.post("/api/v1/registries/enrollments", response_model=RegistryEnrollmentResponse, status_code=201, tags=["Enrollments"])
async def create_enrollment(
    enrollment_data: RegistryEnrollmentCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Enroll a patient in a registry"""
    # Verify registry exists
    registry = db.query(Registry).filter(Registry.id == enrollment_data.registry_id).first()
    if not registry:
        raise HTTPException(status_code=404, detail="Registry not found")

    # Verify patient exists
    patient = db.query(Patient).filter(Patient.id == enrollment_data.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Check for duplicate enrollment
    existing = db.query(RegistryEnrollment).filter(and_(
        RegistryEnrollment.registry_id == enrollment_data.registry_id,
        RegistryEnrollment.patient_id == enrollment_data.patient_id,
        RegistryEnrollment.status == 'enrolled'
    )).first()
    if existing:
        raise HTTPException(status_code=400, detail="Patient already enrolled in this registry")

    enrollment = RegistryEnrollment(
        registry_id=enrollment_data.registry_id,
        patient_id=enrollment_data.patient_id,
        enrollment_date=enrollment_data.enrollment_date,
        status='enrolled',
        consent_record_id=enrollment_data.consent_record_id,
        enrollment_source=enrollment_data.enrollment_source
    )
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)

    await publish_event(EventType.REGISTRY_ENROLLMENT_CREATED, {
        "enrollment_id": str(enrollment.id),
        "registry_id": str(registry.id),
        "registry_code": registry.code,
        "patient_id": str(enrollment.patient_id),
        "enrollment_source": enrollment.enrollment_source
    })

    logger.info(f"Patient enrolled in registry: {registry.code}")
    return enrollment

@app.get("/api/v1/registries/enrollments", response_model=List[RegistryEnrollmentResponse], tags=["Enrollments"])
async def list_enrollments(
    registry_id: Optional[UUID] = Query(None),
    patient_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List registry enrollments with filters"""
    query = db.query(RegistryEnrollment)
    if registry_id:
        query = query.filter(RegistryEnrollment.registry_id == registry_id)
    if patient_id:
        query = query.filter(RegistryEnrollment.patient_id == patient_id)
    if status:
        query = query.filter(RegistryEnrollment.status == status)
    return query.order_by(RegistryEnrollment.enrollment_date.desc()).all()

@app.put("/api/v1/registries/enrollments/{enrollment_id}", response_model=RegistryEnrollmentResponse, tags=["Enrollments"])
async def update_enrollment(
    enrollment_id: UUID,
    enrollment_data: RegistryEnrollmentUpdate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Update enrollment (typically for withdrawal)"""
    enrollment = db.query(RegistryEnrollment).filter(RegistryEnrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    update_data = enrollment_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(enrollment, field, value)

    db.commit()
    db.refresh(enrollment)

    # Publish withdrawal event if status changed to withdrawn
    if enrollment.status == 'withdrawn':
        await publish_event(EventType.REGISTRY_ENROLLMENT_WITHDRAWN, {
            "enrollment_id": str(enrollment.id),
            "registry_id": str(enrollment.registry_id),
            "patient_id": str(enrollment.patient_id),
            "withdrawal_reason": enrollment.withdrawal_reason
        })

    logger.info(f"Enrollment updated: {enrollment_id}")
    return enrollment

# Registry Data Elements Endpoints
@app.post("/api/v1/registries/{registry_id}/data-elements", response_model=RegistryDataElementResponse, status_code=201, tags=["Data Elements"])
async def add_data_element(
    registry_id: UUID,
    element_data: RegistryDataElementCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Add data element to registry"""
    # Verify registry exists
    registry = db.query(Registry).filter(Registry.id == registry_id).first()
    if not registry:
        raise HTTPException(status_code=404, detail="Registry not found")

    # Ensure element belongs to the registry
    if element_data.registry_id != registry_id:
        raise HTTPException(status_code=400, detail="Registry ID mismatch")

    # Check for duplicate code
    existing = db.query(RegistryDataElement).filter(and_(
        RegistryDataElement.registry_id == registry_id,
        RegistryDataElement.code == element_data.code
    )).first()
    if existing:
        raise HTTPException(status_code=400, detail="Data element code already exists")

    element = RegistryDataElement(
        registry_id=element_data.registry_id,
        code=element_data.code,
        name=element_data.name,
        data_type=element_data.data_type,
        unit=element_data.unit,
        collection_frequency=element_data.collection_frequency,
        source_path=element_data.source_path
    )
    db.add(element)
    db.commit()
    db.refresh(element)

    logger.info(f"Data element added to registry: {registry.code} - {element.code}")
    return element

@app.get("/api/v1/registries/{registry_id}/data-elements", response_model=List[RegistryDataElementResponse], tags=["Data Elements"])
async def list_data_elements(registry_id: UUID, db: Session = Depends(get_db)):
    """List all data elements for a registry"""
    return db.query(RegistryDataElement).filter(
        RegistryDataElement.registry_id == registry_id
    ).order_by(RegistryDataElement.code).all()

# Registry Data Values Endpoints
@app.post("/api/v1/registries/data-values", response_model=RegistryDataValueResponse, status_code=201, tags=["Data Values"])
async def record_data_value(
    value_data: RegistryDataValueCreate,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """Record a data value for an enrollment"""
    # Verify enrollment exists
    enrollment = db.query(RegistryEnrollment).filter(
        RegistryEnrollment.id == value_data.registry_enrollment_id
    ).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    # Verify data element exists
    element = db.query(RegistryDataElement).filter(
        RegistryDataElement.id == value_data.data_element_id
    ).first()
    if not element:
        raise HTTPException(status_code=404, detail="Data element not found")

    # Ensure element belongs to the same registry
    if element.registry_id != enrollment.registry_id:
        raise HTTPException(status_code=400, detail="Data element does not belong to enrollment's registry")

    value = RegistryDataValue(
        registry_enrollment_id=value_data.registry_enrollment_id,
        data_element_id=value_data.data_element_id,
        as_of_date=value_data.as_of_date,
        value_string=value_data.value_string,
        value_number=value_data.value_number,
        value_date=value_data.value_date,
        value_code=value_data.value_code,
        source_reference=value_data.source_reference
    )
    db.add(value)
    db.commit()
    db.refresh(value)

    logger.info(f"Data value recorded: {element.code} for enrollment {enrollment.id}")
    return value

# Registry Data Refresh
@app.post("/api/v1/registries/{registry_id}/refresh", status_code=202, tags=["Data Management"])
async def refresh_registry_data(
    registry_id: UUID,
    refresh_request: RegistryDataRefreshRequest,
    db: Session = Depends(get_db),
    current_user_id: UUID = None
):
    """
    Trigger registry data refresh from source systems
    This would typically queue a background job to pull data from FHIR/analytics
    """
    # Verify registry exists
    registry = db.query(Registry).filter(Registry.id == registry_id).first()
    if not registry:
        raise HTTPException(status_code=404, detail="Registry not found")

    await publish_event(EventType.REGISTRY_DATA_REFRESHED, {
        "registry_id": str(registry.id),
        "registry_code": registry.code,
        "requested_by": str(current_user_id) if current_user_id else None,
        "filters": {
            "enrollment_ids": [str(e) for e in refresh_request.enrollment_ids] if refresh_request.enrollment_ids else None,
            "data_element_codes": refresh_request.data_element_codes,
            "start_date": refresh_request.start_date.isoformat() if refresh_request.start_date else None,
            "end_date": refresh_request.end_date.isoformat() if refresh_request.end_date else None
        }
    })

    logger.info(f"Registry data refresh queued: {registry.code}")
    return {
        "message": "Registry data refresh queued",
        "registry_id": str(registry.id),
        "registry_code": registry.code
    }

@app.get("/health", tags=["System"])
async def health_check():
    return {"service": "research-registry-service", "status": "healthy", "version": "0.1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8026)

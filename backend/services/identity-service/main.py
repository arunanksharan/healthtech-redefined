"""
Identity Service - Patient, Practitioner, Organization Management
FastAPI application with complete CRUD operations and FHIR support
"""
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from sqlalchemy.orm import Session

# Import shared modules
import sys
sys.path.insert(0, '/app')

from shared.database.connection import get_db, check_db_connection
from shared.database.models import (
    Patient, PatientIdentifier, Practitioner,
    Organization, Location, Tenant
)
from shared.events.publisher import publish_event
from shared.events.types import EventType

from .schemas import (
    PatientCreate, PatientUpdate, PatientResponse, PatientSearchResponse,
    PractitionerCreate, PractitionerUpdate, PractitionerResponse,
    OrganizationCreate, OrganizationUpdate, OrganizationResponse,
    LocationCreate, LocationUpdate, LocationResponse,
    IdentifierInput, MergeRequest, HealthResponse
)
from .fhir_converter import to_fhir_patient, to_fhir_practitioner


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Identity Service...")

    # Check database connection
    if not check_db_connection():
        logger.error("Failed to connect to database")
        raise RuntimeError("Database connection failed")

    logger.info("Identity Service started successfully")
    yield

    # Shutdown
    logger.info("Shutting down Identity Service...")


# Initialize FastAPI app
app = FastAPI(
    title="Identity Service",
    description="Patient, Practitioner, and Organization Management",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    db_healthy = check_db_connection()
    return HealthResponse(
        status="healthy" if db_healthy else "unhealthy",
        service="identity-service",
        version="1.0.0",
        database=db_healthy
    )


# ============================================================================
# PATIENT ENDPOINTS
# ============================================================================

@app.post(
    "/api/v1/patients",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Patients"]
)
async def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new patient

    - Validates unique identifiers
    - Creates FHIR Patient resource
    - Publishes Patient.Created event
    """
    try:
        # Check for duplicate identifiers
        if patient_data.identifiers:
            for identifier in patient_data.identifiers:
                existing = db.query(PatientIdentifier).filter(
                    PatientIdentifier.system == identifier.system,
                    PatientIdentifier.value == identifier.value
                ).first()

                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Identifier {identifier.system}:{identifier.value} already exists"
                    )

        # Create patient record
        db_patient = Patient(
            tenant_id=patient_data.tenant_id,
            first_name=patient_data.first_name,
            last_name=patient_data.last_name,
            middle_name=patient_data.middle_name,
            date_of_birth=patient_data.date_of_birth,
            gender=patient_data.gender,
            phone_primary=patient_data.phone_primary,
            phone_secondary=patient_data.phone_secondary,
            email_primary=patient_data.email_primary,
            email_secondary=patient_data.email_secondary,
            marital_status=patient_data.marital_status,
            blood_group=patient_data.blood_group,
            language_preferred=patient_data.language_preferred,
        )

        # Add address if provided
        if patient_data.address:
            db_patient.address_line1 = patient_data.address.line1
            db_patient.address_line2 = patient_data.address.line2
            db_patient.city = patient_data.address.city
            db_patient.state = patient_data.address.state
            db_patient.postal_code = patient_data.address.postal_code
            db_patient.country = patient_data.address.country

        # Generate FHIR representation
        db_patient.fhir_resource = to_fhir_patient(db_patient)

        db.add(db_patient)
        db.flush()

        # Add identifiers
        if patient_data.identifiers:
            for identifier in patient_data.identifiers:
                db_identifier = PatientIdentifier(
                    patient_id=db_patient.id,
                    system=identifier.system,
                    value=identifier.value,
                    is_primary=identifier.is_primary,
                )
                db.add(db_identifier)

        db.commit()
        db.refresh(db_patient)

        # Publish event
        await publish_event(
            event_type=EventType.PATIENT_CREATED,
            tenant_id=str(db_patient.tenant_id),
            payload={
                "patient_id": str(db_patient.id),
                "name": f"{db_patient.first_name} {db_patient.last_name}",
                "identifiers": [
                    {"system": i.system, "value": i.value}
                    for i in db_patient.identifiers
                ],
                "date_of_birth": db_patient.date_of_birth.isoformat() if db_patient.date_of_birth else None,
            },
            source_service="identity-service"
        )

        logger.info(f"Patient created: {db_patient.id}")
        return PatientResponse.model_validate(db_patient)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating patient: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create patient: {str(e)}"
        )


@app.get(
    "/api/v1/patients/{patient_id}",
    response_model=PatientResponse,
    tags=["Patients"]
)
async def get_patient(
    patient_id: UUID,
    db: Session = Depends(get_db)
):
    """Get patient by ID"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    return PatientResponse.model_validate(patient)


@app.get(
    "/api/v1/patients",
    response_model=PatientSearchResponse,
    tags=["Patients"]
)
async def search_patients(
    search: Optional[str] = Query(None, description="Search by name or phone"),
    identifier_system: Optional[str] = Query(None, description="Identifier system (e.g., MRN, ABHA)"),
    identifier_value: Optional[str] = Query(None, description="Identifier value"),
    date_of_birth: Optional[str] = Query(None, description="Date of birth (YYYY-MM-DD)"),
    gender: Optional[str] = Query(None, description="Gender"),
    limit: int = Query(20, le=100, description="Maximum results to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    Search patients with various filters

    Supports:
    - Text search on name and phone
    - Identifier search (system + value)
    - Date of birth filtering
    - Gender filtering
    - Pagination
    """
    query = db.query(Patient)

    # Text search
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Patient.first_name.ilike(search_term)) |
            (Patient.last_name.ilike(search_term)) |
            (Patient.phone_primary.like(search_term))
        )

    # Identifier search
    if identifier_system and identifier_value:
        query = query.join(PatientIdentifier).filter(
            PatientIdentifier.system == identifier_system,
            PatientIdentifier.value == identifier_value
        )

    # Date of birth filter
    if date_of_birth:
        query = query.filter(Patient.date_of_birth == date_of_birth)

    # Gender filter
    if gender:
        query = query.filter(Patient.gender == gender)

    # Get total count
    total = query.count()

    # Apply pagination
    patients = query.offset(offset).limit(limit).all()

    return PatientSearchResponse(
        total=total,
        offset=offset,
        limit=limit,
        patients=[PatientResponse.model_validate(p) for p in patients]
    )


@app.patch(
    "/api/v1/patients/{patient_id}",
    response_model=PatientResponse,
    tags=["Patients"]
)
async def update_patient(
    patient_id: UUID,
    patient_update: PatientUpdate,
    db: Session = Depends(get_db)
):
    """Update patient information"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    try:
        # Update fields
        update_data = patient_update.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(patient, field) and value is not None:
                setattr(patient, field, value)

        patient.updated_at = datetime.utcnow()
        patient.fhir_resource = to_fhir_patient(patient)

        db.commit()
        db.refresh(patient)

        # Publish event
        await publish_event(
            event_type=EventType.PATIENT_UPDATED,
            tenant_id=str(patient.tenant_id),
            payload={"patient_id": str(patient.id)},
            source_service="identity-service"
        )

        logger.info(f"Patient updated: {patient.id}")
        return PatientResponse.model_validate(patient)

    except Exception as e:
        db.rollback()
        logger.error(f"Error updating patient: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update patient: {str(e)}"
        )


@app.post(
    "/api/v1/patients/{patient_id}/identifiers",
    status_code=status.HTTP_201_CREATED,
    tags=["Patients"]
)
async def add_patient_identifier(
    patient_id: UUID,
    identifier: IdentifierInput,
    db: Session = Depends(get_db)
):
    """Add an identifier to a patient"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    # Check for duplicate
    existing = db.query(PatientIdentifier).filter(
        PatientIdentifier.system == identifier.system,
        PatientIdentifier.value == identifier.value
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Identifier {identifier.system}:{identifier.value} already exists"
        )

    db_identifier = PatientIdentifier(
        patient_id=patient_id,
        system=identifier.system,
        value=identifier.value,
        is_primary=identifier.is_primary,
    )

    db.add(db_identifier)
    db.commit()

    return {"message": "Identifier added successfully"}


@app.post(
    "/api/v1/patients/merge",
    tags=["Patients"]
)
async def merge_patients(
    merge_request: MergeRequest,
    db: Session = Depends(get_db)
):
    """
    Merge multiple patient records into one

    - Moves all identifiers to target patient
    - Marks source patients as merged
    - Publishes merge event
    """
    target_patient = db.query(Patient).filter(
        Patient.id == merge_request.target_patient_id
    ).first()

    if not target_patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target patient not found"
        )

    try:
        merged_ids = []

        for source_id in merge_request.source_patient_ids:
            source_patient = db.query(Patient).filter(Patient.id == source_id).first()

            if not source_patient:
                logger.warning(f"Source patient {source_id} not found, skipping")
                continue

            # Move identifiers
            db.query(PatientIdentifier).filter(
                PatientIdentifier.patient_id == source_id
            ).update({"patient_id": merge_request.target_patient_id})

            # Mark as merged (using deceased flag for now)
            source_patient.is_deceased = True
            source_patient.metadata = {
                **source_patient.metadata,
                "merged_into": str(merge_request.target_patient_id),
                "merged_at": datetime.utcnow().isoformat(),
                "merge_reason": merge_request.reason
            }

            merged_ids.append(str(source_id))

        db.commit()

        # Publish event
        await publish_event(
            event_type=EventType.PATIENT_MERGED,
            tenant_id=str(target_patient.tenant_id),
            payload={
                "target_patient_id": str(merge_request.target_patient_id),
                "source_patient_ids": merged_ids,
                "reason": merge_request.reason
            },
            source_service="identity-service"
        )

        logger.info(f"Patients merged into {merge_request.target_patient_id}")
        return {
            "status": "success",
            "target_patient_id": str(merge_request.target_patient_id),
            "merged_count": len(merged_ids)
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error merging patients: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to merge patients: {str(e)}"
        )


# ============================================================================
# PRACTITIONER ENDPOINTS
# ============================================================================

@app.post(
    "/api/v1/practitioners",
    response_model=PractitionerResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Practitioners"]
)
async def create_practitioner(
    practitioner_data: PractitionerCreate,
    db: Session = Depends(get_db)
):
    """Create a new practitioner (doctor, nurse, etc.)"""
    try:
        db_practitioner = Practitioner(**practitioner_data.model_dump())
        db_practitioner.fhir_resource = to_fhir_practitioner(db_practitioner)

        db.add(db_practitioner)
        db.commit()
        db.refresh(db_practitioner)

        await publish_event(
            event_type=EventType.PRACTITIONER_CREATED,
            tenant_id=str(db_practitioner.tenant_id),
            payload={"practitioner_id": str(db_practitioner.id)},
            source_service="identity-service"
        )

        logger.info(f"Practitioner created: {db_practitioner.id}")
        return PractitionerResponse.model_validate(db_practitioner)

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating practitioner: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create practitioner: {str(e)}"
        )


@app.get(
    "/api/v1/practitioners",
    response_model=List[PractitionerResponse],
    tags=["Practitioners"]
)
async def list_practitioners(
    specialty: Optional[str] = Query(None, description="Filter by specialty"),
    is_active: bool = Query(True, description="Filter by active status"),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db)
):
    """List practitioners with filters"""
    query = db.query(Practitioner).filter(Practitioner.is_active == is_active)

    if specialty:
        query = query.filter(Practitioner.speciality == specialty)

    practitioners = query.limit(limit).all()
    return [PractitionerResponse.model_validate(p) for p in practitioners]


@app.get(
    "/api/v1/practitioners/{practitioner_id}",
    response_model=PractitionerResponse,
    tags=["Practitioners"]
)
async def get_practitioner(
    practitioner_id: UUID,
    db: Session = Depends(get_db)
):
    """Get practitioner by ID"""
    practitioner = db.query(Practitioner).filter(
        Practitioner.id == practitioner_id
    ).first()

    if not practitioner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practitioner not found"
        )

    return PractitionerResponse.model_validate(practitioner)


# ============================================================================
# ORGANIZATION ENDPOINTS
# ============================================================================

@app.post(
    "/api/v1/organizations",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Organizations"]
)
async def create_organization(
    organization_data: OrganizationCreate,
    db: Session = Depends(get_db)
):
    """Create a new organization (hospital, clinic, lab, etc.)"""
    db_organization = Organization(**organization_data.model_dump())
    db.add(db_organization)
    db.commit()
    db.refresh(db_organization)

    return OrganizationResponse.model_validate(db_organization)


@app.get(
    "/api/v1/organizations",
    response_model=List[OrganizationResponse],
    tags=["Organizations"]
)
async def list_organizations(
    type: Optional[str] = Query(None, description="Organization type"),
    is_active: bool = Query(True),
    db: Session = Depends(get_db)
):
    """List organizations"""
    query = db.query(Organization).filter(Organization.is_active == is_active)

    if type:
        query = query.filter(Organization.type == type)

    organizations = query.all()
    return [OrganizationResponse.model_validate(o) for o in organizations]


# ============================================================================
# LOCATION ENDPOINTS
# ============================================================================

@app.post(
    "/api/v1/locations",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Locations"]
)
async def create_location(
    location_data: LocationCreate,
    db: Session = Depends(get_db)
):
    """Create a new location (ward, room, department, etc.)"""
    db_location = Location(**location_data.model_dump())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)

    return LocationResponse.model_validate(db_location)


@app.get(
    "/api/v1/locations",
    response_model=List[LocationResponse],
    tags=["Locations"]
)
async def list_locations(
    organization_id: Optional[UUID] = Query(None),
    type: Optional[str] = Query(None),
    is_active: bool = Query(True),
    db: Session = Depends(get_db)
):
    """List locations"""
    query = db.query(Location).filter(Location.is_active == is_active)

    if organization_id:
        query = query.filter(Location.organization_id == organization_id)
    if type:
        query = query.filter(Location.type == type)

    locations = query.all()
    return [LocationResponse.model_validate(loc) for loc in locations]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

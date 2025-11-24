# Phase 1: Core Platform & FHIR Backbone - Detailed Implementation Guide

## Overview
Phase 1 establishes the foundational platform with identity management, FHIR clinical data store, consent framework, and event-driven architecture. This phase takes 8-12 weeks and provides the "kernel" on which all other functionality is built.

## Project Structure

```
healthtech-platform/
├── backend/
│   ├── services/
│   │   ├── identity-service/
│   │   ├── fhir-service/
│   │   ├── consent-service/
│   │   ├── auth-service/
│   │   └── admin-service/
│   ├── shared/
│   │   ├── database/
│   │   ├── events/
│   │   ├── models/
│   │   └── utils/
│   └── tests/
├── frontend/
│   ├── apps/
│   │   └── admin-console/
│   └── packages/
│       ├── ui-components/
│       └── api-client/
└── infrastructure/
    ├── docker/
    ├── migrations/
    └── scripts/
```

---

## Backend Implementation

### 1. Database Setup

#### File: `backend/shared/database/models.py`

```python
"""
Core database models and configuration
"""
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, JSON, ForeignKey, Index, Date, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

# ============= IDENTITY MODELS =============

class Tenant(Base):
    __tablename__ = 'tenants'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    domain = Column(String(255))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class Patient(Base):
    __tablename__ = 'patients'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)

    # Demographics
    first_name = Column(String(100))
    last_name = Column(String(100))
    middle_name = Column(String(100))
    date_of_birth = Column(Date)
    gender = Column(String(20))  # male, female, other, unknown

    # Contact
    phone_primary = Column(String(20))
    email_primary = Column(String(255))

    # Address
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100))

    # Status
    is_deceased = Column(Boolean, default=False)
    deceased_date = Column(DateTime(timezone=True))

    # FHIR
    fhir_resource = Column(JSON, nullable=False, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    identifiers = relationship("PatientIdentifier", back_populates="patient", cascade="all, delete-orphan")
    consents = relationship("Consent", back_populates="patient", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('idx_patients_tenant', 'tenant_id'),
        Index('idx_patients_phone', 'phone_primary'),
        Index('idx_patients_name', 'first_name', 'last_name'),
    )

class PatientIdentifier(Base):
    __tablename__ = 'patient_identifiers'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey('patients.id', ondelete='CASCADE'), nullable=False)
    system = Column(String(100), nullable=False)  # ABHA, MRN, NATIONAL_ID
    value = Column(String(255), nullable=False)
    is_primary = Column(Boolean, default=False)

    # Relationships
    patient = relationship("Patient", back_populates="identifiers")

    # Indexes
    __table_args__ = (
        Index('uniq_patient_identifier', 'system', 'value', unique=True),
        Index('idx_patient_identifiers_patient', 'patient_id'),
    )

class Practitioner(Base):
    __tablename__ = 'practitioners'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)

    # Demographics
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100))
    gender = Column(String(20))

    # Professional
    qualification = Column(String(255))
    speciality = Column(String(100))
    license_number = Column(String(100))

    # Contact
    phone_primary = Column(String(20))
    email_primary = Column(String(255))

    # FHIR
    fhir_resource = Column(JSON, nullable=False, default=dict)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class Organization(Base):
    __tablename__ = 'organizations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)

    name = Column(String(255), nullable=False)
    type = Column(String(100))  # hospital, clinic, lab, pharmacy

    # Contact
    phone = Column(String(20))
    email = Column(String(255))
    website = Column(String(255))

    # Address
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100))

    # FHIR
    fhir_resource = Column(JSON, nullable=False, default=dict)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

class Location(Base):
    __tablename__ = 'locations'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey('organizations.id'))

    name = Column(String(255), nullable=False)
    type = Column(String(100))  # ward, room, bed, clinic, department

    # Physical location
    building = Column(String(100))
    floor = Column(String(50))
    room = Column(String(50))

    # FHIR
    fhir_resource = Column(JSON, nullable=False, default=dict)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

# ============= CONSENT MODELS =============

class Consent(Base):
    __tablename__ = 'consents'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey('patients.id'), nullable=False)

    status = Column(String(20), nullable=False, default='active')  # active, inactive, draft
    category = Column(String(50))  # treatment, research, marketing

    # Scope
    purpose = Column(String(100))
    data_types = Column(JSON, default=list)  # ['clinical', 'demographic', 'billing']

    # Period
    valid_from = Column(DateTime(timezone=True))
    valid_until = Column(DateTime(timezone=True))

    # Source
    channel = Column(String(50))  # web, whatsapp, phone, in_clinic
    note = Column(Text)

    # FHIR
    consent_fhir = Column(JSON, nullable=False, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="consents")

    # Indexes
    __table_args__ = (
        Index('idx_consents_patient', 'patient_id', 'status'),
    )

# ============= AUTH MODELS =============

class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)

    email = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))

    # Link to practitioner if applicable
    practitioner_id = Column(UUID(as_uuid=True), ForeignKey('practitioners.id'))

    # Status
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    # Timestamps
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index('uniq_users_email_tenant', 'tenant_id', 'email', unique=True),
    )

class Role(Base):
    __tablename__ = 'roles'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)

    name = Column(String(100), nullable=False)
    description = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")

class Permission(Base):
    __tablename__ = 'permissions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    resource = Column(String(100), nullable=False)  # patient, appointment, order
    action = Column(String(50), nullable=False)  # read, write, delete
    scope = Column(String(50))  # own, department, all

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

class UserRole(Base):
    __tablename__ = 'user_roles'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id', ondelete='CASCADE'), nullable=False)

    # Relationships
    user = relationship("User", back_populates="roles")
    role = relationship("Role")

class RolePermission(Base):
    __tablename__ = 'role_permissions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id', ondelete='CASCADE'), nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey('permissions.id', ondelete='CASCADE'), nullable=False)

    # Relationships
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission")

# ============= FHIR MODELS =============

class FHIRResource(Base):
    __tablename__ = 'fhir_resources'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)

    resource_type = Column(String(50), nullable=False)  # Encounter, EpisodeOfCare, etc
    resource_id = Column(String(100), nullable=False)  # FHIR logical ID
    version = Column(Integer, nullable=False, default=1)
    is_current = Column(Boolean, nullable=False, default=True)

    # The actual FHIR resource
    resource = Column(JSON, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_fhir_resources_tenant_type', 'tenant_id', 'resource_type'),
        Index('idx_fhir_resources_id_type', 'resource_type', 'resource_id', 'is_current'),
    )

# ============= EVENT LOG =============

class EventLog(Base):
    __tablename__ = 'event_log'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('tenants.id'), nullable=False)

    event_type = Column(String(100), nullable=False)  # Patient.Created, Consent.Updated
    event_payload = Column(JSON, nullable=False)

    occurred_at = Column(DateTime(timezone=True), nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    processed_by_warehouse = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_event_log_type_time', 'event_type', 'occurred_at'),
    )
```

#### File: `backend/shared/database/connection.py`

```python
"""
Database connection management
"""
import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from typing import Generator

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/healthtech"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # For development; use QueuePool in production
    echo=os.getenv("SQL_ECHO", "false").lower() == "true"
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 2. Identity Service Implementation

#### File: `backend/services/identity-service/main.py`

```python
"""
Identity Service - Patient, Practitioner, Organization management
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from shared.database.connection import get_db
from shared.database.models import Patient, PatientIdentifier, Practitioner, Organization, Location
from .schemas import (
    PatientCreate, PatientUpdate, PatientResponse,
    PractitionerCreate, PractitionerResponse,
    OrganizationCreate, OrganizationResponse,
    IdentifierInput
)
from .fhir_converter import to_fhir_patient, from_fhir_patient
from shared.events.publisher import EventPublisher

app = FastAPI(title="Identity Service", version="1.0.0")
event_publisher = EventPublisher()

# ============= PATIENT ENDPOINTS =============

@app.post("/api/v1/identity/patients", response_model=PatientResponse)
async def create_patient(
    patient: PatientCreate,
    db: Session = Depends(get_db)
):
    """Create a new patient"""
    # Check for duplicate identifiers
    if patient.identifiers:
        for identifier in patient.identifiers:
            existing = db.query(PatientIdentifier).filter(
                PatientIdentifier.system == identifier.system,
                PatientIdentifier.value == identifier.value
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail=f"Identifier {identifier.system}:{identifier.value} already exists")

    # Create patient record
    db_patient = Patient(
        tenant_id=patient.tenant_id,
        first_name=patient.first_name,
        last_name=patient.last_name,
        middle_name=patient.middle_name,
        date_of_birth=patient.date_of_birth,
        gender=patient.gender,
        phone_primary=patient.phone_primary,
        email_primary=patient.email_primary,
        address_line1=patient.address.line1 if patient.address else None,
        address_line2=patient.address.line2 if patient.address else None,
        city=patient.address.city if patient.address else None,
        state=patient.address.state if patient.address else None,
        postal_code=patient.address.postal_code if patient.address else None,
        country=patient.address.country if patient.address else None
    )

    # Generate FHIR representation
    db_patient.fhir_resource = to_fhir_patient(db_patient)

    db.add(db_patient)
    db.flush()

    # Add identifiers
    if patient.identifiers:
        for identifier in patient.identifiers:
            db_identifier = PatientIdentifier(
                patient_id=db_patient.id,
                system=identifier.system,
                value=identifier.value,
                is_primary=identifier.is_primary
            )
            db.add(db_identifier)

    db.commit()
    db.refresh(db_patient)

    # Publish event
    await event_publisher.publish(
        event_type="Patient.Created",
        tenant_id=str(db_patient.tenant_id),
        payload={
            "patient_id": str(db_patient.id),
            "identifiers": [
                {"system": i.system, "value": i.value}
                for i in db_patient.identifiers
            ]
        }
    )

    return PatientResponse.from_orm(db_patient)

@app.get("/api/v1/identity/patients/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    db: Session = Depends(get_db)
):
    """Get patient by ID"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientResponse.from_orm(patient)

@app.get("/api/v1/identity/patients", response_model=List[PatientResponse])
async def search_patients(
    search: Optional[str] = Query(None, description="Search by name or phone"),
    identifier_system: Optional[str] = None,
    identifier_value: Optional[str] = None,
    limit: int = Query(10, le=100),
    db: Session = Depends(get_db)
):
    """Search patients"""
    query = db.query(Patient)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Patient.first_name.ilike(search_term)) |
            (Patient.last_name.ilike(search_term)) |
            (Patient.phone_primary.like(search_term))
        )

    if identifier_system and identifier_value:
        query = query.join(PatientIdentifier).filter(
            PatientIdentifier.system == identifier_system,
            PatientIdentifier.value == identifier_value
        )

    patients = query.limit(limit).all()
    return [PatientResponse.from_orm(p) for p in patients]

@app.patch("/api/v1/identity/patients/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: str,
    patient_update: PatientUpdate,
    db: Session = Depends(get_db)
):
    """Update patient information"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Update fields
    update_data = patient_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(patient, field):
            setattr(patient, field, value)

    patient.updated_at = datetime.utcnow()
    patient.fhir_resource = to_fhir_patient(patient)

    db.commit()
    db.refresh(patient)

    # Publish event
    await event_publisher.publish(
        event_type="Patient.Updated",
        tenant_id=str(patient.tenant_id),
        payload={"patient_id": str(patient.id)}
    )

    return PatientResponse.from_orm(patient)

@app.post("/api/v1/identity/patients/{patient_id}/merge")
async def merge_patients(
    patient_id: str,
    source_patient_ids: List[str],
    merge_reason: str,
    db: Session = Depends(get_db)
):
    """Merge multiple patient records"""
    target_patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not target_patient:
        raise HTTPException(status_code=404, detail="Target patient not found")

    for source_id in source_patient_ids:
        source_patient = db.query(Patient).filter(Patient.id == source_id).first()
        if not source_patient:
            continue

        # Move identifiers
        db.query(PatientIdentifier).filter(
            PatientIdentifier.patient_id == source_id
        ).update({"patient_id": patient_id})

        # Mark source as merged (could also delete)
        source_patient.is_deceased = True  # Using as a flag for now

    db.commit()

    # Publish event
    await event_publisher.publish(
        event_type="Patient.Merged",
        tenant_id=str(target_patient.tenant_id),
        payload={
            "target_patient_id": patient_id,
            "source_patient_ids": source_patient_ids,
            "reason": merge_reason
        }
    )

    return {"status": "success", "merged_into": patient_id}

# ============= PRACTITIONER ENDPOINTS =============

@app.post("/api/v1/identity/practitioners", response_model=PractitionerResponse)
async def create_practitioner(
    practitioner: PractitionerCreate,
    db: Session = Depends(get_db)
):
    """Create a new practitioner"""
    db_practitioner = Practitioner(**practitioner.dict())
    db.add(db_practitioner)
    db.commit()
    db.refresh(db_practitioner)

    await event_publisher.publish(
        event_type="Practitioner.Created",
        tenant_id=str(db_practitioner.tenant_id),
        payload={"practitioner_id": str(db_practitioner.id)}
    )

    return PractitionerResponse.from_orm(db_practitioner)

@app.get("/api/v1/identity/practitioners", response_model=List[PractitionerResponse])
async def list_practitioners(
    specialty: Optional[str] = None,
    is_active: bool = True,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db)
):
    """List practitioners"""
    query = db.query(Practitioner).filter(Practitioner.is_active == is_active)

    if specialty:
        query = query.filter(Practitioner.speciality == specialty)

    practitioners = query.limit(limit).all()
    return [PractitionerResponse.from_orm(p) for p in practitioners]

# ============= ORGANIZATION ENDPOINTS =============

@app.post("/api/v1/identity/organizations", response_model=OrganizationResponse)
async def create_organization(
    organization: OrganizationCreate,
    db: Session = Depends(get_db)
):
    """Create a new organization"""
    db_organization = Organization(**organization.dict())
    db.add(db_organization)
    db.commit()
    db.refresh(db_organization)

    return OrganizationResponse.from_orm(db_organization)

@app.get("/api/v1/identity/organizations", response_model=List[OrganizationResponse])
async def list_organizations(
    type: Optional[str] = None,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """List organizations"""
    query = db.query(Organization).filter(Organization.is_active == is_active)

    if type:
        query = query.filter(Organization.type == type)

    organizations = query.all()
    return [OrganizationResponse.from_orm(o) for o in organizations]

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "identity-service"}
```

#### File: `backend/services/identity-service/schemas.py`

```python
"""
Pydantic schemas for Identity Service
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID

# ============= PATIENT SCHEMAS =============

class AddressInput(BaseModel):
    line1: Optional[str]
    line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    country: Optional[str] = "India"

class IdentifierInput(BaseModel):
    system: str  # ABHA, MRN, NATIONAL_ID
    value: str
    is_primary: bool = False

class PatientCreate(BaseModel):
    tenant_id: UUID
    first_name: str
    last_name: str
    middle_name: Optional[str]
    date_of_birth: date
    gender: str  # male, female, other, unknown

    phone_primary: Optional[str]
    email_primary: Optional[EmailStr]

    address: Optional[AddressInput]
    identifiers: Optional[List[IdentifierInput]]

    @validator('gender')
    def validate_gender(cls, v):
        allowed = ['male', 'female', 'other', 'unknown']
        if v not in allowed:
            raise ValueError(f"Gender must be one of {allowed}")
        return v

class PatientUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    middle_name: Optional[str]
    phone_primary: Optional[str]
    email_primary: Optional[EmailStr]

    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    country: Optional[str]

class PatientResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    first_name: Optional[str]
    last_name: Optional[str]
    middle_name: Optional[str]
    date_of_birth: Optional[date]
    gender: Optional[str]

    phone_primary: Optional[str]
    email_primary: Optional[str]

    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    country: Optional[str]

    is_deceased: bool
    deceased_date: Optional[datetime]

    created_at: datetime
    updated_at: datetime

    identifiers: List[dict] = []

    class Config:
        orm_mode = True

# ============= PRACTITIONER SCHEMAS =============

class PractitionerCreate(BaseModel):
    tenant_id: UUID
    first_name: str
    last_name: str
    middle_name: Optional[str]
    gender: Optional[str]

    qualification: Optional[str]
    speciality: Optional[str]
    license_number: Optional[str]

    phone_primary: Optional[str]
    email_primary: Optional[EmailStr]

class PractitionerResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    first_name: str
    last_name: str
    middle_name: Optional[str]
    gender: Optional[str]

    qualification: Optional[str]
    speciality: Optional[str]
    license_number: Optional[str]

    phone_primary: Optional[str]
    email_primary: Optional[str]

    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# ============= ORGANIZATION SCHEMAS =============

class OrganizationCreate(BaseModel):
    tenant_id: UUID
    name: str
    type: Optional[str]  # hospital, clinic, lab, pharmacy

    phone: Optional[str]
    email: Optional[EmailStr]
    website: Optional[str]

    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    country: Optional[str]

class OrganizationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    type: Optional[str]

    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]

    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    country: Optional[str]

    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
```

### 3. FHIR Service Implementation

#### File: `backend/services/fhir-service/main.py`

```python
"""
FHIR Service - FHIR R4 resource management
"""
from fastapi import FastAPI, HTTPException, Depends, Path
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
import json
from datetime import datetime

from shared.database.connection import get_db
from shared.database.models import FHIRResource
from .fhir_validator import validate_fhir_resource
from shared.events.publisher import EventPublisher

app = FastAPI(title="FHIR Service", version="1.0.0")
event_publisher = EventPublisher()

SUPPORTED_RESOURCE_TYPES = [
    "Patient", "Practitioner", "Organization", "Location",
    "Encounter", "EpisodeOfCare", "Consent", "Condition",
    "Observation", "MedicationRequest", "ServiceRequest",
    "DiagnosticReport", "CarePlan", "Task", "Communication"
]

@app.post("/fhir/R4/{resource_type}")
async def create_resource(
    resource_type: str = Path(..., description="FHIR resource type"),
    resource: Dict = None,
    db: Session = Depends(get_db)
):
    """Create a new FHIR resource"""
    if resource_type not in SUPPORTED_RESOURCE_TYPES:
        raise HTTPException(status_code=400, detail=f"Resource type {resource_type} not supported")

    # Validate FHIR resource
    validation_errors = validate_fhir_resource(resource_type, resource)
    if validation_errors:
        raise HTTPException(status_code=400, detail={"errors": validation_errors})

    # Generate resource ID if not provided
    if "id" not in resource:
        resource["id"] = str(uuid.uuid4())

    # Add metadata
    resource["meta"] = resource.get("meta", {})
    resource["meta"]["versionId"] = "1"
    resource["meta"]["lastUpdated"] = datetime.utcnow().isoformat()

    # Store resource
    db_resource = FHIRResource(
        tenant_id=resource.get("meta", {}).get("tenant_id", "default"),
        resource_type=resource_type,
        resource_id=resource["id"],
        version=1,
        is_current=True,
        resource=resource
    )

    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)

    # Publish event
    await event_publisher.publish(
        event_type=f"{resource_type}.Created",
        tenant_id=str(db_resource.tenant_id),
        payload={
            "resource_type": resource_type,
            "resource_id": resource["id"]
        }
    )

    return resource

@app.get("/fhir/R4/{resource_type}/{resource_id}")
async def get_resource(
    resource_type: str = Path(..., description="FHIR resource type"),
    resource_id: str = Path(..., description="Resource ID"),
    db: Session = Depends(get_db)
):
    """Get a FHIR resource by ID"""
    if resource_type not in SUPPORTED_RESOURCE_TYPES:
        raise HTTPException(status_code=400, detail=f"Resource type {resource_type} not supported")

    resource = db.query(FHIRResource).filter(
        FHIRResource.resource_type == resource_type,
        FHIRResource.resource_id == resource_id,
        FHIRResource.is_current == True
    ).first()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    return resource.resource

@app.put("/fhir/R4/{resource_type}/{resource_id}")
async def update_resource(
    resource_type: str = Path(..., description="FHIR resource type"),
    resource_id: str = Path(..., description="Resource ID"),
    resource: Dict = None,
    db: Session = Depends(get_db)
):
    """Update a FHIR resource"""
    if resource_type not in SUPPORTED_RESOURCE_TYPES:
        raise HTTPException(status_code=400, detail=f"Resource type {resource_type} not supported")

    # Get existing resource
    existing = db.query(FHIRResource).filter(
        FHIRResource.resource_type == resource_type,
        FHIRResource.resource_id == resource_id,
        FHIRResource.is_current == True
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Resource not found")

    # Validate updated resource
    validation_errors = validate_fhir_resource(resource_type, resource)
    if validation_errors:
        raise HTTPException(status_code=400, detail={"errors": validation_errors})

    # Mark old version as not current
    existing.is_current = False

    # Create new version
    new_version = existing.version + 1
    resource["id"] = resource_id
    resource["meta"] = resource.get("meta", {})
    resource["meta"]["versionId"] = str(new_version)
    resource["meta"]["lastUpdated"] = datetime.utcnow().isoformat()

    db_resource = FHIRResource(
        tenant_id=existing.tenant_id,
        resource_type=resource_type,
        resource_id=resource_id,
        version=new_version,
        is_current=True,
        resource=resource
    )

    db.add(db_resource)
    db.commit()

    # Publish event
    await event_publisher.publish(
        event_type=f"{resource_type}.Updated",
        tenant_id=str(existing.tenant_id),
        payload={
            "resource_type": resource_type,
            "resource_id": resource_id,
            "version": new_version
        }
    )

    return resource

@app.delete("/fhir/R4/{resource_type}/{resource_id}")
async def delete_resource(
    resource_type: str = Path(..., description="FHIR resource type"),
    resource_id: str = Path(..., description="Resource ID"),
    db: Session = Depends(get_db)
):
    """Delete a FHIR resource (soft delete)"""
    if resource_type not in SUPPORTED_RESOURCE_TYPES:
        raise HTTPException(status_code=400, detail=f"Resource type {resource_type} not supported")

    resource = db.query(FHIRResource).filter(
        FHIRResource.resource_type == resource_type,
        FHIRResource.resource_id == resource_id,
        FHIRResource.is_current == True
    ).first()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    # Soft delete by marking as not current
    resource.is_current = False
    db.commit()

    # Publish event
    await event_publisher.publish(
        event_type=f"{resource_type}.Deleted",
        tenant_id=str(resource.tenant_id),
        payload={
            "resource_type": resource_type,
            "resource_id": resource_id
        }
    )

    return {"status": "deleted"}

@app.get("/fhir/R4/{resource_type}")
async def search_resources(
    resource_type: str = Path(..., description="FHIR resource type"),
    patient: Optional[str] = None,
    encounter: Optional[str] = None,
    date: Optional[str] = None,
    _count: int = 50,
    db: Session = Depends(get_db)
):
    """Search FHIR resources"""
    if resource_type not in SUPPORTED_RESOURCE_TYPES:
        raise HTTPException(status_code=400, detail=f"Resource type {resource_type} not supported")

    query = db.query(FHIRResource).filter(
        FHIRResource.resource_type == resource_type,
        FHIRResource.is_current == True
    )

    # Apply filters based on resource content
    # This is simplified - real FHIR search is more complex
    if patient:
        query = query.filter(
            FHIRResource.resource.op("->")("subject").op("->>")("reference").like(f"%Patient/{patient}%")
        )

    if encounter:
        query = query.filter(
            FHIRResource.resource.op("->")("encounter").op("->>")("reference").like(f"%Encounter/{encounter}%")
        )

    resources = query.limit(_count).all()

    # Create FHIR Bundle response
    bundle = {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(resources),
        "entry": [
            {
                "resource": r.resource,
                "fullUrl": f"/fhir/R4/{r.resource_type}/{r.resource_id}"
            }
            for r in resources
        ]
    }

    return bundle

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "fhir-service"}
```

### 4. Consent Service Implementation

#### File: `backend/services/consent-service/main.py`

```python
"""
Consent Service - Patient consent management
"""
from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID

from shared.database.connection import get_db
from shared.database.models import Consent
from .schemas import ConsentCreate, ConsentUpdate, ConsentResponse, ConsentValidation
from shared.events.publisher import EventPublisher

app = FastAPI(title="Consent Service", version="1.0.0")
event_publisher = EventPublisher()

@app.post("/api/v1/consents", response_model=ConsentResponse)
async def create_consent(
    consent: ConsentCreate,
    db: Session = Depends(get_db)
):
    """Create a new consent"""
    # Set validity period if not specified
    if not consent.valid_from:
        consent.valid_from = datetime.utcnow()
    if not consent.valid_until:
        consent.valid_until = datetime.utcnow() + timedelta(days=365)  # 1 year default

    db_consent = Consent(
        tenant_id=consent.tenant_id,
        patient_id=consent.patient_id,
        status=consent.status or "active",
        category=consent.category,
        purpose=consent.purpose,
        data_types=consent.data_types,
        valid_from=consent.valid_from,
        valid_until=consent.valid_until,
        channel=consent.channel,
        note=consent.note
    )

    # Create FHIR Consent resource
    db_consent.consent_fhir = {
        "resourceType": "Consent",
        "status": db_consent.status,
        "category": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/consentcategorycodes",
                "code": consent.category
            }]
        }],
        "patient": {
            "reference": f"Patient/{consent.patient_id}"
        },
        "dateTime": datetime.utcnow().isoformat(),
        "provision": {
            "type": "permit",
            "period": {
                "start": consent.valid_from.isoformat(),
                "end": consent.valid_until.isoformat()
            },
            "purpose": [{
                "code": consent.purpose
            }],
            "data": [
                {"meaning": "instance", "reference": {"display": dt}}
                for dt in consent.data_types
            ] if consent.data_types else None
        }
    }

    db.add(db_consent)
    db.commit()
    db.refresh(db_consent)

    # Publish event
    await event_publisher.publish(
        event_type="Consent.Created",
        tenant_id=str(db_consent.tenant_id),
        payload={
            "consent_id": str(db_consent.id),
            "patient_id": str(db_consent.patient_id),
            "category": db_consent.category,
            "purpose": db_consent.purpose
        }
    )

    return ConsentResponse.from_orm(db_consent)

@app.get("/api/v1/consents/{consent_id}", response_model=ConsentResponse)
async def get_consent(
    consent_id: UUID,
    db: Session = Depends(get_db)
):
    """Get consent by ID"""
    consent = db.query(Consent).filter(Consent.id == consent_id).first()
    if not consent:
        raise HTTPException(status_code=404, detail="Consent not found")
    return ConsentResponse.from_orm(consent)

@app.get("/api/v1/consents", response_model=List[ConsentResponse])
async def list_consents(
    patient_id: Optional[UUID] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List consents with filters"""
    query = db.query(Consent)

    if patient_id:
        query = query.filter(Consent.patient_id == patient_id)
    if status:
        query = query.filter(Consent.status == status)
    if category:
        query = query.filter(Consent.category == category)

    consents = query.all()
    return [ConsentResponse.from_orm(c) for c in consents]

@app.patch("/api/v1/consents/{consent_id}", response_model=ConsentResponse)
async def update_consent(
    consent_id: UUID,
    consent_update: ConsentUpdate,
    db: Session = Depends(get_db)
):
    """Update consent status or validity"""
    consent = db.query(Consent).filter(Consent.id == consent_id).first()
    if not consent:
        raise HTTPException(status_code=404, detail="Consent not found")

    # Update fields
    if consent_update.status:
        consent.status = consent_update.status
    if consent_update.valid_until:
        consent.valid_until = consent_update.valid_until
    if consent_update.note:
        consent.note = consent_update.note

    consent.updated_at = datetime.utcnow()

    # Update FHIR representation
    consent.consent_fhir["status"] = consent.status
    if consent_update.valid_until:
        consent.consent_fhir["provision"]["period"]["end"] = consent_update.valid_until.isoformat()

    db.commit()
    db.refresh(consent)

    # Publish event
    await event_publisher.publish(
        event_type="Consent.Updated",
        tenant_id=str(consent.tenant_id),
        payload={
            "consent_id": str(consent.id),
            "patient_id": str(consent.patient_id),
            "status": consent.status
        }
    )

    return ConsentResponse.from_orm(consent)

@app.post("/api/v1/consents/validate", response_model=ConsentValidation)
async def validate_consent(
    patient_id: UUID,
    purpose: str,
    data_categories: List[str],
    channel: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Check if a planned use of patient data is allowed by existing consents"""
    # Find active consents for patient
    consents = db.query(Consent).filter(
        Consent.patient_id == patient_id,
        Consent.status == "active",
        Consent.valid_from <= datetime.utcnow(),
        Consent.valid_until >= datetime.utcnow()
    ).all()

    # Check if any consent covers the requested use
    allowed = False
    applicable_consent_ids = []
    reason = "No active consent found"

    for consent in consents:
        # Check purpose match
        if consent.purpose != purpose and consent.purpose != "all":
            continue

        # Check data categories
        if consent.data_types:
            if not all(cat in consent.data_types for cat in data_categories):
                continue

        # Check channel if specified
        if channel and consent.channel and consent.channel != channel:
            continue

        allowed = True
        applicable_consent_ids.append(str(consent.id))
        reason = "Consent found covering requested use"
        break

    if not allowed and not consents:
        reason = "No active consents found for patient"
    elif not allowed:
        reason = f"No consent found for purpose '{purpose}' with data categories {data_categories}"

    return ConsentValidation(
        allowed=allowed,
        reason=reason,
        applicable_consent_ids=applicable_consent_ids
    )

@app.post("/api/v1/consents/{consent_id}/withdraw")
async def withdraw_consent(
    consent_id: UUID,
    reason: str,
    db: Session = Depends(get_db)
):
    """Withdraw a consent"""
    consent = db.query(Consent).filter(Consent.id == consent_id).first()
    if not consent:
        raise HTTPException(status_code=404, detail="Consent not found")

    consent.status = "inactive"
    consent.note = f"Withdrawn: {reason}"
    consent.updated_at = datetime.utcnow()

    db.commit()

    # Publish event
    await event_publisher.publish(
        event_type="Consent.Withdrawn",
        tenant_id=str(consent.tenant_id),
        payload={
            "consent_id": str(consent.id),
            "patient_id": str(consent.patient_id),
            "reason": reason
        }
    )

    return {"status": "withdrawn", "consent_id": str(consent_id)}

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "consent-service"}
```

### 5. Auth Service Implementation

#### File: `backend/services/auth-service/main.py`

```python
"""
Auth Service - Authentication and authorization
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from shared.database.connection import get_db
from shared.database.models import User, Role, Permission, UserRole, RolePermission
from .schemas import UserCreate, UserResponse, Token, TokenData, RoleCreate, RoleResponse
import os

app = FastAPI(title="Auth Service", version="1.0.0")

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ============= UTILITY FUNCTIONS =============

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
    return user

def check_permission(user: User, resource: str, action: str, db: Session) -> bool:
    """Check if user has permission for resource and action"""
    # Get user's permissions through roles
    permissions = db.query(Permission).join(
        RolePermission, Permission.id == RolePermission.permission_id
    ).join(
        Role, RolePermission.role_id == Role.id
    ).join(
        UserRole, Role.id == UserRole.role_id
    ).filter(
        UserRole.user_id == user.id,
        Permission.resource == resource,
        Permission.action == action
    ).all()

    return len(permissions) > 0

# ============= AUTH ENDPOINTS =============

@app.post("/api/v1/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login and get access token"""
    # Parse email from username field (format: email@domain|tenant_code)
    parts = form_data.username.split("|")
    email = parts[0]
    tenant_code = parts[1] if len(parts) > 1 else None

    # Find user
    query = db.query(User).filter(User.email == email)
    if tenant_code:
        # Join with tenant to filter by code
        from shared.database.models import Tenant
        query = query.join(Tenant, User.tenant_id == Tenant.id).filter(Tenant.code == tenant_code)

    user = query.first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Create tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id),
            "email": user.email
        },
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id)
        }
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@app.post("/api/v1/auth/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        user_id: str = payload.get("sub")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    # Create new access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id),
            "email": user.email
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,  # Return same refresh token
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@app.get("/api/v1/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse.from_orm(current_user)

@app.get("/api/v1/auth/me/permissions")
async def get_user_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's permissions"""
    permissions = db.query(Permission).join(
        RolePermission, Permission.id == RolePermission.permission_id
    ).join(
        Role, RolePermission.role_id == Role.id
    ).join(
        UserRole, Role.id == UserRole.role_id
    ).filter(
        UserRole.user_id == current_user.id
    ).all()

    return [
        {
            "resource": p.resource,
            "action": p.action,
            "scope": p.scope
        }
        for p in permissions
    ]

# ============= USER MANAGEMENT ENDPOINTS =============

@app.post("/api/v1/auth/users", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new user (requires admin permission)"""
    # Check permission
    if not current_user.is_superuser and not check_permission(current_user, "user", "create", db):
        raise HTTPException(status_code=403, detail="Not authorized to create users")

    # Check if user exists
    existing = db.query(User).filter(
        User.tenant_id == user.tenant_id,
        User.email == user.email
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    # Create user
    db_user = User(
        tenant_id=user.tenant_id,
        email=user.email,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name,
        practitioner_id=user.practitioner_id,
        is_active=user.is_active
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Assign default role if specified
    if user.role_ids:
        for role_id in user.role_ids:
            user_role = UserRole(user_id=db_user.id, role_id=role_id)
            db.add(user_role)
        db.commit()

    return UserResponse.from_orm(db_user)

@app.get("/api/v1/auth/users", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List users in tenant"""
    users = db.query(User).filter(User.tenant_id == current_user.tenant_id).all()
    return [UserResponse.from_orm(u) for u in users]

# ============= ROLE MANAGEMENT ENDPOINTS =============

@app.post("/api/v1/auth/roles", response_model=RoleResponse)
async def create_role(
    role: RoleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new role"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only superusers can create roles")

    db_role = Role(
        tenant_id=role.tenant_id,
        name=role.name,
        description=role.description
    )

    db.add(db_role)
    db.commit()
    db.refresh(db_role)

    # Add permissions to role
    if role.permission_ids:
        for perm_id in role.permission_ids:
            role_perm = RolePermission(role_id=db_role.id, permission_id=perm_id)
            db.add(role_perm)
        db.commit()

    return RoleResponse.from_orm(db_role)

@app.get("/api/v1/auth/roles", response_model=List[RoleResponse])
async def list_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List available roles"""
    roles = db.query(Role).filter(Role.tenant_id == current_user.tenant_id).all()
    return [RoleResponse.from_orm(r) for r in roles]

@app.post("/api/v1/auth/users/{user_id}/roles")
async def assign_role_to_user(
    user_id: UUID,
    role_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Assign a role to a user"""
    if not current_user.is_superuser and not check_permission(current_user, "user", "update", db):
        raise HTTPException(status_code=403, detail="Not authorized to assign roles")

    # Check if assignment exists
    existing = db.query(UserRole).filter(
        UserRole.user_id == user_id,
        UserRole.role_id == role_id
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Role already assigned to user")

    user_role = UserRole(user_id=user_id, role_id=role_id)
    db.add(user_role)
    db.commit()

    return {"status": "success", "message": "Role assigned"}

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "auth-service"}
```

---

## Frontend Implementation

### 1. Admin Console Setup

#### File: `frontend/apps/admin-console/app/layout.tsx`

```tsx
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from './providers'
import { MainNav } from '@/components/layout/main-nav'
import { UserNav } from '@/components/layout/user-nav'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'HealthTech Admin Console',
  description: 'AI-Native Healthcare Platform Administration',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>
          <div className="flex min-h-screen flex-col">
            <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
              <div className="container flex h-14 items-center">
                <MainNav />
                <div className="flex flex-1 items-center justify-end space-x-4">
                  <UserNav />
                </div>
              </div>
            </header>
            <main className="flex-1">{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  )
}
```

#### File: `frontend/apps/admin-console/app/providers.tsx`

```tsx
'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { SessionProvider } from 'next-auth/react'
import { ThemeProvider } from '@/components/theme-provider'
import { Toaster } from '@/components/ui/toaster'
import { useState } from 'react'

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000, // 1 minute
            refetchOnWindowFocus: false,
          },
        },
      })
  )

  return (
    <SessionProvider>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {children}
          <Toaster />
        </ThemeProvider>
      </QueryClientProvider>
    </SessionProvider>
  )
}
```

### 2. Patient Management UI

#### File: `frontend/apps/admin-console/app/patients/page.tsx`

```tsx
'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { PatientDialog } from '@/components/patients/patient-dialog'
import { PatientDetails } from '@/components/patients/patient-details'
import { api } from '@/lib/api'
import { Patient } from '@/types/patient'
import { Plus, Search } from 'lucide-react'

export default function PatientsPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null)
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false)
  const queryClient = useQueryClient()

  // Fetch patients
  const { data: patients, isLoading } = useQuery({
    queryKey: ['patients', searchTerm],
    queryFn: () => api.patients.search({ search: searchTerm }),
  })

  // Create patient mutation
  const createPatientMutation = useMutation({
    mutationFn: api.patients.create,
    onSuccess: () => {
      queryClient.invalidateQueries(['patients'])
      setIsCreateDialogOpen(false)
    },
  })

  return (
    <div className="container mx-auto py-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Patients</h1>
          <p className="text-muted-foreground">
            Manage patient records and identities
          </p>
        </div>
        <Button onClick={() => setIsCreateDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Patient
        </Button>
      </div>

      <div className="mb-4 flex items-center space-x-2">
        <div className="relative flex-1">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search by name, phone, or identifier..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-8"
          />
        </div>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Date of Birth</TableHead>
              <TableHead>Gender</TableHead>
              <TableHead>Phone</TableHead>
              <TableHead>Identifiers</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center">
                  Loading...
                </TableCell>
              </TableRow>
            ) : patients?.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center">
                  No patients found
                </TableCell>
              </TableRow>
            ) : (
              patients?.map((patient) => (
                <TableRow key={patient.id}>
                  <TableCell className="font-medium">
                    {patient.first_name} {patient.last_name}
                  </TableCell>
                  <TableCell>{patient.date_of_birth}</TableCell>
                  <TableCell className="capitalize">{patient.gender}</TableCell>
                  <TableCell>{patient.phone_primary}</TableCell>
                  <TableCell>
                    {patient.identifiers?.map((id) => (
                      <span
                        key={`${id.system}-${id.value}`}
                        className="mr-2 inline-block rounded bg-secondary px-2 py-1 text-xs"
                      >
                        {id.system}: {id.value}
                      </span>
                    ))}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedPatient(patient)}
                    >
                      View
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Create Patient Dialog */}
      <PatientDialog
        open={isCreateDialogOpen}
        onOpenChange={setIsCreateDialogOpen}
        onSubmit={(data) => createPatientMutation.mutate(data)}
        isLoading={createPatientMutation.isLoading}
      />

      {/* Patient Details Sheet */}
      {selectedPatient && (
        <PatientDetails
          patient={selectedPatient}
          open={!!selectedPatient}
          onOpenChange={(open) => !open && setSelectedPatient(null)}
        />
      )}
    </div>
  )
}
```

---

## Event System Implementation

#### File: `backend/shared/events/publisher.py`

```python
"""
Event publishing system using Kafka
"""
import json
import os
from typing import Dict, Any
from datetime import datetime
from confluent_kafka import Producer
import logging

logger = logging.getLogger(__name__)

class EventPublisher:
    def __init__(self):
        self.producer = None
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.topic_prefix = os.getenv("KAFKA_TOPIC_PREFIX", "healthtech")
        self._init_producer()

    def _init_producer(self):
        """Initialize Kafka producer"""
        try:
            conf = {
                'bootstrap.servers': self.bootstrap_servers,
                'client.id': 'healthtech-producer',
                'acks': 'all',
                'retries': 3,
                'max.in.flight.requests.per.connection': 1
            }
            self.producer = Producer(conf)
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            # Fallback to logging events if Kafka is not available
            self.producer = None

    async def publish(self, event_type: str, tenant_id: str, payload: Dict[str, Any]):
        """Publish an event to Kafka"""
        event = {
            "event_type": event_type,
            "event_id": str(uuid.uuid4()),
            "occurred_at": datetime.utcnow().isoformat(),
            "tenant_id": tenant_id,
            "payload": payload
        }

        # Determine topic based on event type
        topic = self._get_topic(event_type)

        if self.producer:
            try:
                self.producer.produce(
                    topic=topic,
                    key=tenant_id.encode('utf-8'),
                    value=json.dumps(event).encode('utf-8'),
                    callback=self._delivery_report
                )
                self.producer.poll(0)
            except Exception as e:
                logger.error(f"Failed to publish event: {e}")
                # Fallback to database event log
                await self._log_event_to_db(event)
        else:
            # Kafka not available, log to database
            await self._log_event_to_db(event)

    def _get_topic(self, event_type: str) -> str:
        """Get Kafka topic for event type"""
        # Map event types to topics
        domain = event_type.split('.')[0].lower()
        return f"{self.topic_prefix}.{domain}.events"

    def _delivery_report(self, err, msg):
        """Callback for Kafka delivery reports"""
        if err is not None:
            logger.error(f'Event delivery failed: {err}')
        else:
            logger.debug(f'Event delivered to {msg.topic()} [{msg.partition()}]')

    async def _log_event_to_db(self, event: Dict[str, Any]):
        """Fallback to log events to database when Kafka is unavailable"""
        from shared.database.connection import get_db_session
        from shared.database.models import EventLog

        with get_db_session() as db:
            db_event = EventLog(
                tenant_id=event["tenant_id"],
                event_type=event["event_type"],
                event_payload=event["payload"],
                occurred_at=datetime.fromisoformat(event["occurred_at"]),
                published_at=datetime.utcnow()
            )
            db.add(db_event)

    def flush(self):
        """Flush any pending events"""
        if self.producer:
            self.producer.flush()
```

---

## Database Migrations

#### File: `backend/migrations/alembic.ini`

```ini
[alembic]
script_location = migrations
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql://postgres:password@localhost:5432/healthtech

[post_write_hooks]
hooks = black
black.type = console_scripts
black.entrypoint = black
black.options = -l 88

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

#### File: `backend/migrations/env.py`

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.database.models import Base
from shared.database.connection import DATABASE_URL

config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

---

## Docker Setup

#### File: `docker-compose.yml`

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: healthtech
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  zookeeper:
    image: confluentinc/cp-zookeeper:7.4.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  kafka:
    image: confluentinc/cp-kafka:7.4.0
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

  identity-service:
    build:
      context: ./backend
      dockerfile: services/identity-service/Dockerfile
    environment:
      DATABASE_URL: postgresql://postgres:password@postgres:5432/healthtech
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
    ports:
      - "8001:8000"
    depends_on:
      - postgres
      - kafka

  fhir-service:
    build:
      context: ./backend
      dockerfile: services/fhir-service/Dockerfile
    environment:
      DATABASE_URL: postgresql://postgres:password@postgres:5432/healthtech
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
    ports:
      - "8002:8000"
    depends_on:
      - postgres
      - kafka

  consent-service:
    build:
      context: ./backend
      dockerfile: services/consent-service/Dockerfile
    environment:
      DATABASE_URL: postgresql://postgres:password@postgres:5432/healthtech
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
    ports:
      - "8003:8000"
    depends_on:
      - postgres
      - kafka

  auth-service:
    build:
      context: ./backend
      dockerfile: services/auth-service/Dockerfile
    environment:
      DATABASE_URL: postgresql://postgres:password@postgres:5432/healthtech
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
      JWT_SECRET_KEY: your-secret-key-change-in-production
    ports:
      - "8004:8000"
    depends_on:
      - postgres
      - kafka

volumes:
  postgres_data:
```

---

## Testing Setup

#### File: `backend/tests/test_identity_service.py`

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.database.models import Base
from services.identity_service.main import app
from shared.database.connection import get_db

# Test database
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:password@localhost:5432/healthtech_test"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_create_patient():
    response = client.post(
        "/api/v1/identity/patients",
        json={
            "tenant_id": "00000000-0000-0000-0000-000000000000",
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-01",
            "gender": "male",
            "phone_primary": "9876543210",
            "identifiers": [
                {"system": "MRN", "value": "MRN001", "is_primary": True}
            ]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"

def test_search_patients():
    response = client.get("/api/v1/identity/patients?search=John")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_patient():
    # First create a patient
    create_response = client.post(
        "/api/v1/identity/patients",
        json={
            "tenant_id": "00000000-0000-0000-0000-000000000000",
            "first_name": "Jane",
            "last_name": "Smith",
            "date_of_birth": "1985-05-15",
            "gender": "female"
        }
    )
    patient_id = create_response.json()["id"]

    # Then get the patient
    response = client.get(f"/api/v1/identity/patients/{patient_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == patient_id
    assert data["first_name"] == "Jane"
```

---

## Summary

This Phase 1 implementation guide provides:

1. **Complete database schema** with all required tables
2. **Four core services** with full API implementations:
   - Identity Service (Patient/Practitioner management)
   - FHIR Service (Clinical data store)
   - Consent Service (Privacy management)
   - Auth Service (Authentication/Authorization)

3. **Event-driven architecture** with Kafka integration
4. **Frontend foundation** with Next.js admin console
5. **Docker setup** for easy development
6. **Testing framework** with examples

### Next Steps:

1. **Initialize the database**:
   ```bash
   cd backend
   alembic init migrations
   alembic revision --autogenerate -m "Initial migration"
   alembic upgrade head
   ```

2. **Start services**:
   ```bash
   docker-compose up
   ```

3. **Run tests**:
   ```bash
   pytest backend/tests
   ```

4. **Start frontend**:
   ```bash
   cd frontend/apps/admin-console
   npm install
   npm run dev
   ```

5. **Create initial data**:
   - Create tenant
   - Create admin user
   - Set up basic roles and permissions

This completes Phase 1 foundation. Move to Phase 2 for implementing outpatient workflows and agent capabilities.
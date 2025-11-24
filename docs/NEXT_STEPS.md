# Next Steps - Implementation Guide

## 🚀 Immediate Actions Required

### 1. Complete Identity Service Implementation (2-3 hours)

Create the following files in `backend/services/identity-service/`:

#### a. `__init__.py`
```python
"""Identity Service - Patient and Practitioner Management"""
__version__ = "1.0.0"
```

#### b. `main.py`
Copy the complete implementation from `IMPLEMENTATION_GUIDE_PHASE_1.md` (lines 84-295)
- Patient CRUD endpoints
- Practitioner management
- Organization management
- Patient identifier handling
- Patient merging functionality

#### c. `schemas.py`
Copy Pydantic schemas from `IMPLEMENTATION_GUIDE_PHASE_1.md` (lines 297-396)
- PatientCreate, PatientUpdate, PatientResponse
- PractitionerCreate, PractitionerResponse
- OrganizationCreate, OrganizationResponse
- IdentifierInput

#### d. `fhir_converter.py`
```python
"""FHIR conversion utilities for Identity resources"""
from datetime import date
from typing import Dict, Any

def to_fhir_patient(patient) -> Dict[str, Any]:
    """Convert Patient model to FHIR Patient resource"""
    fhir_patient = {
        "resourceType": "Patient",
        "id": str(patient.id),
        "active": not patient.is_deceased,
        "name": [{
            "use": "official",
            "family": patient.last_name,
            "given": [patient.first_name],
        }],
        "telecom": [],
        "gender": patient.gender,
        "birthDate": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
    }

    if patient.phone_primary:
        fhir_patient["telecom"].append({
            "system": "phone",
            "value": patient.phone_primary,
            "use": "mobile"
        })

    if patient.email_primary:
        fhir_patient["telecom"].append({
            "system": "email",
            "value": patient.email_primary
        })

    if patient.address_line1:
        fhir_patient["address"] = [{
            "use": "home",
            "line": [patient.address_line1, patient.address_line2] if patient.address_line2 else [patient.address_line1],
            "city": patient.city,
            "state": patient.state,
            "postalCode": patient.postal_code,
            "country": patient.country
        }]

    return fhir_patient
```

### 2. Setup Database Migrations (30 minutes)

```bash
cd backend

# Initialize Alembic
alembic init migrations

# Update alembic.ini with database URL
# Edit migrations/env.py to import Base from shared.database.models

# Create initial migration
alembic revision --autogenerate -m "Initial schema - Phase 1"

# Apply migration
alembic upgrade head
```

### 3. Create Shared Pydantic Models (1 hour)

Create `backend/shared/models/base.py`:
```python
"""Base Pydantic models for API contracts"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }

class TimestampedSchema(BaseSchema):
    """Schema with timestamp fields"""
    created_at: datetime
    updated_at: datetime

class TenantedSchema(BaseSchema):
    """Schema with tenant_id"""
    tenant_id: UUID
```

### 4. Implement Remaining Phase 1 Services (6-8 hours)

#### a. FHIR Service
- Copy implementation from `IMPLEMENTATION_GUIDE_PHASE_1.md`
- Create FHIR validation logic
- Implement resource versioning

#### b. Consent Service
- Copy implementation from guide
- Implement consent validation endpoint
- Add consent expiry checking

#### c. Auth Service
- Implement JWT token generation
- Create password hashing utilities
- Implement permission checking
- Add refresh token logic

### 5. Initialize Frontend Admin Console (2-3 hours)

```bash
cd frontend/apps

# Create Next.js app
npx create-next-app@latest admin-console \
  --typescript \
  --tailwind \
  --app \
  --src-dir \
  --import-alias "@/*"

cd admin-console

# Install dependencies
npm install \
  @radix-ui/react-* \
  zustand \
  @tanstack/react-query \
  next-auth \
  zod \
  react-hook-form

# Initialize Shadcn UI
npx shadcn-ui@latest init
```

Create:
- `app/layout.tsx` - Main layout
- `app/providers.tsx` - Context providers
- `app/patients/page.tsx` - Patient management
- `lib/api.ts` - API client
- `components/patients/` - Patient components

### 6. Setup Local Development Environment (1 hour)

```bash
# Start infrastructure
docker-compose up -d postgres redis kafka zookeeper

# Wait for services to be healthy
docker-compose ps

# Run migrations
cd backend
alembic upgrade head

# Seed initial data
python scripts/seed_data.py

# Start backend services
docker-compose up identity-service fhir-service consent-service auth-service

# In another terminal, start frontend
cd frontend/apps/admin-console
npm run dev
```

### 7. Create Initial Test Suite (2-3 hours)

Create `backend/tests/conftest.py`:
```python
"""Pytest configuration and fixtures"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.database.models import Base

@pytest.fixture(scope="session")
def engine():
    return create_engine("postgresql://postgres:password@localhost:5432/healthtech_test")

@pytest.fixture(scope="session")
def tables(engine):
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(engine, tables):
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
```

## 📋 Implementation Checklist

### Week 1: Core Services
- [ ] Complete Identity Service implementation
- [ ] Complete FHIR Service implementation
- [ ] Complete Consent Service implementation
- [ ] Complete Auth Service implementation
- [ ] Setup Alembic migrations
- [ ] Create seed data scripts
- [ ] Write unit tests for core models

### Week 2: Frontend & Integration
- [ ] Initialize Admin Console app
- [ ] Implement authentication flow
- [ ] Build patient management UI
- [ ] Create API client package
- [ ] Setup Shadcn UI components
- [ ] Write integration tests
- [ ] Create API documentation

### Week 3: Polish & Deploy
- [ ] Add monitoring and logging
- [ ] Create deployment scripts
- [ ] Write deployment documentation
- [ ] Setup CI/CD pipeline
- [ ] Load testing
- [ ] Security audit
- [ ] Create demo data

## 🔧 Development Commands

```bash
# Backend
cd backend
source venv/bin/activate
uvicorn services.identity_service.main:app --reload

# Frontend
cd frontend/apps/admin-console
npm run dev

# Tests
cd backend
pytest -v

# Migrations
alembic revision --autogenerate -m "Description"
alembic upgrade head

# Docker
docker-compose up -d
docker-compose logs -f identity-service
docker-compose down

# Database
docker exec -it healthtech-postgres psql -U postgres -d healthtech
```

## 📚 Key Reference Files

1. **Database Models**: `backend/shared/database/models.py`
2. **Event System**: `backend/shared/events/publisher.py`
3. **Implementation Guide**: `IMPLEMENTATION_GUIDE_PHASE_1.md`
4. **API Documentation**: See OpenAPI at http://localhost:8001/docs
5. **Architecture**: `IMPLEMENTATION_GUIDE_MASTER_ARCHITECTURE.md`

## ⚠️ Important Notes

1. **Security**: Change JWT_SECRET_KEY before production
2. **Database**: Use strong passwords in production
3. **CORS**: Configure properly for frontend domain
4. **Logging**: Setup centralized logging for production
5. **Monitoring**: Enable Prometheus metrics
6. **Backups**: Setup automated database backups
7. **SSL**: Use HTTPS in production

## 🎯 Success Criteria for Phase 1

- [ ] All 4 microservices running and healthy
- [ ] Admin console accessible at http://localhost:3000
- [ ] Can create and search patients
- [ ] Can manage consents
- [ ] Authentication working with JWT
- [ ] Events publishing to Kafka
- [ ] All unit tests passing
- [ ] API documentation available

---

**Estimated Total Time**: 15-20 hours
**Target Completion**: End of Week 1

Once Phase 1 is complete, proceed to Phase 2 for OPD and PRM implementation.

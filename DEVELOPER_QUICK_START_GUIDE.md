# Developer Quick Start Guide - AI-Native Healthcare Platform

## Overview
This guide provides step-by-step instructions for developers and coding assistants (like Cursor) to implement the AI-native healthcare platform. Follow these instructions sequentially for best results.

---

## Prerequisites

### Required Software
- **Python** 3.11+
- **Node.js** 18+
- **PostgreSQL** 15+
- **Docker** & Docker Compose
- **Git**
- **VS Code** or **Cursor** IDE

### API Keys (obtain before starting)
- **OpenAI** or **Anthropic** API key for LLM functionality
- **WhatsApp Business API** credentials (Phase 2)
- **SMS provider** API credentials (Phase 2)

---

## Project Setup Instructions

### Step 1: Initialize Project Structure

```bash
# Create main project directory
mkdir healthtech-platform && cd healthtech-platform

# Create backend structure
mkdir -p backend/{services,shared,tests,migrations}
mkdir -p backend/services/{identity-service,fhir-service,consent-service,auth-service,admin-service}
mkdir -p backend/shared/{database,events,models,utils,schemas}

# Create frontend structure
mkdir -p frontend/{apps,packages}
mkdir -p frontend/packages/{ui-components,api-client,shared-types}

# Create infrastructure
mkdir -p infrastructure/{docker,k8s,scripts,terraform}

# Create documentation
mkdir -p docs/{api,architecture,guides,decisions}
```

### Step 2: Backend Base Setup

```bash
cd backend

# Create Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Create requirements.txt
cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
httpx==0.25.1
redis==5.0.1
celery==5.3.4
confluent-kafka==2.3.0
pytest==7.4.3
pytest-asyncio==0.21.1
python-dotenv==1.0.0
EOF

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Database Setup

```bash
# Start PostgreSQL using Docker
docker run -d \
  --name healthtech-postgres \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=healthtech \
  -p 5432:5432 \
  -v healthtech_pgdata:/var/lib/postgresql/data \
  postgres:15

# Create .env file
cat > backend/.env << EOF
DATABASE_URL=postgresql://postgres:password@localhost:5432/healthtech
JWT_SECRET_KEY=your-secret-key-change-in-production
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
REDIS_URL=redis://localhost:6379
ENV=development
EOF
```

### Step 4: Frontend Base Setup

```bash
cd ../frontend

# Initialize package.json for monorepo
npm init -y

# Install workspace dependencies
npm install -D \
  @types/node \
  @types/react \
  typescript \
  eslint \
  prettier \
  turbo

# Create admin console app
npx create-next-app@latest apps/admin-console \
  --typescript \
  --tailwind \
  --app \
  --src-dir \
  --import-alias "@/*"

cd apps/admin-console

# Install UI and utility packages
npm install \
  @radix-ui/react-alert-dialog \
  @radix-ui/react-dialog \
  @radix-ui/react-dropdown-menu \
  @radix-ui/react-label \
  @radix-ui/react-select \
  @radix-ui/react-separator \
  @radix-ui/react-slot \
  @radix-ui/react-tabs \
  @radix-ui/react-toast \
  class-variance-authority \
  clsx \
  tailwind-merge \
  zustand \
  @tanstack/react-query \
  next-auth \
  react-hook-form \
  @hookform/resolvers \
  zod \
  date-fns \
  recharts \
  lucide-react
```

---

## Phase-by-Phase Implementation

## Phase 1: Core Platform (Weeks 1-8)

### Week 1-2: Database & Models

1. **Create database models** (`backend/shared/database/models.py`)
   - Copy the complete models from `IMPLEMENTATION_GUIDE_PHASE_1.md`
   - Includes: Tenant, Patient, Practitioner, Organization, Location, Consent, User, Role, Permission, FHIRResource

2. **Setup Alembic migrations**
   ```bash
   cd backend
   alembic init migrations
   # Update alembic.ini with database URL
   alembic revision --autogenerate -m "Initial schema"
   alembic upgrade head
   ```

3. **Create seed data script** (`backend/scripts/seed_data.py`)
   ```python
   # Create default tenant
   # Create admin user
   # Create basic roles (admin, doctor, nurse, receptionist)
   # Create permissions
   ```

### Week 3-4: Identity Service

1. **Implement Identity Service**
   - Location: `backend/services/identity-service/`
   - Files to create:
     - `main.py` - FastAPI app with patient/practitioner endpoints
     - `schemas.py` - Pydantic models
     - `fhir_converter.py` - FHIR conversion utilities
     - `Dockerfile` - Container configuration

2. **Key endpoints to implement:**
   - `POST /patients` - Create patient
   - `GET /patients/{id}` - Get patient
   - `GET /patients` - Search patients
   - `PATCH /patients/{id}` - Update patient
   - `POST /patients/{id}/merge` - Merge patients
   - Similar endpoints for practitioners, organizations

### Week 5-6: FHIR & Consent Services

1. **Implement FHIR Service**
   - Generic FHIR resource CRUD
   - Support for core resource types
   - FHIR validation

2. **Implement Consent Service**
   - Consent creation and management
   - Consent validation endpoint
   - Privacy preference tracking

### Week 7-8: Auth Service & Admin Console

1. **Implement Auth Service**
   - JWT token generation
   - User authentication
   - Role-based access control
   - Permission checking

2. **Build Admin Console**
   - Login/authentication flow
   - Patient management UI
   - User management UI
   - Consent viewer
   - FHIR resource browser

---

## Phase 2: Outpatient & PRM (Weeks 9-20)

### Week 9-10: Scheduling Service

1. **Database tables:**
   - `provider_schedules`
   - `time_slots`
   - `appointments`

2. **Key features:**
   - Provider schedule templates
   - Slot generation
   - Appointment booking/rescheduling
   - Availability checking

### Week 11-12: Encounter Service

1. **Database tables:**
   - `encounters`
   - Link to appointments

2. **Features:**
   - OPD encounter creation
   - Encounter status management
   - Link to FHIR resources

### Week 13-14: PRM Service

1. **Database tables:**
   - `journeys`
   - `journey_stages`
   - `journey_instances`
   - `communications`
   - `tickets`

2. **Features:**
   - Journey definition
   - Patient journey tracking
   - Multi-channel communications
   - Event-driven stage transitions

### Week 15-16: Scribe Service & AI Integration

1. **Implement LLM integration:**
   - Transcript to SOAP conversion
   - Clinical note generation
   - Problem/diagnosis extraction
   - Order suggestions

2. **Create LLM tools:**
   - `search_patient`
   - `book_appointment`
   - `draft_clinical_note`

### Week 17-18: Patient & Doctor Portals

1. **Patient Portal:**
   - Appointment booking
   - Medical records view
   - Journey status

2. **Doctor Portal:**
   - Patient worklist
   - Consultation screen
   - AI-assisted note taking

### Week 19-20: Integration & Testing

1. **End-to-end workflows:**
   - Patient registration → Appointment → Consultation → Follow-up
   - Multi-channel patient communications
   - Journey orchestration

---

## Phase 3: Inpatient Operations (Weeks 21-36)

### Core Services to Implement:
1. **Bed Management Service** - Ward/bed allocation
2. **Admission Service** - IPD admissions
3. **Nursing Service** - Tasks and observations
4. **Orders Service** - Lab/imaging/medication orders
5. **ICU Service** - Early warning scores

### Key Features:
- Real-time bed management
- Nursing task boards
- Vital signs recording
- Order management
- ICU monitoring dashboards

---

## Phase 4: Intelligence Layer (Weeks 37-48)

### Core Services to Implement:
1. **Outcomes Service** - Track clinical outcomes
2. **Quality Metrics Service** - QI projects
3. **Risk Stratification Service** - ML models
4. **Analytics Hub** - Data warehouse integration
5. **Voice Collaboration Service** - Real-time transcription
6. **Governance Service** - AI audit trails

---

## File-by-File Implementation Checklist

### Phase 1 Core Files

#### Backend Files
```
✅ backend/shared/database/models.py - Complete database schema
✅ backend/shared/database/connection.py - Database connection management
✅ backend/shared/events/publisher.py - Event publishing system
✅ backend/services/identity-service/main.py - Identity service API
✅ backend/services/identity-service/schemas.py - Pydantic schemas
✅ backend/services/fhir-service/main.py - FHIR service API
✅ backend/services/consent-service/main.py - Consent service API
✅ backend/services/auth-service/main.py - Authentication service
✅ backend/migrations/alembic.ini - Migration configuration
✅ backend/migrations/env.py - Migration environment
```

#### Frontend Files
```
✅ frontend/apps/admin-console/app/layout.tsx - Main layout
✅ frontend/apps/admin-console/app/providers.tsx - Context providers
✅ frontend/apps/admin-console/app/patients/page.tsx - Patient management
✅ frontend/apps/admin-console/components/patients/patient-dialog.tsx
✅ frontend/apps/admin-console/components/patients/patient-details.tsx
✅ frontend/apps/admin-console/lib/api.ts - API client
```

---

## Development Best Practices

### 1. Code Organization
- **One service per folder** with its own main.py
- **Shared code** in backend/shared/
- **Consistent naming** for files and functions
- **Type hints** everywhere in Python
- **TypeScript** for all frontend code

### 2. API Design
- **RESTful conventions** for CRUD operations
- **Consistent error responses**
- **Pagination** for list endpoints
- **Filtering** support where needed
- **API versioning** (/api/v1/)

### 3. Database Guidelines
- **Use UUIDs** for all primary keys
- **Soft deletes** where appropriate
- **Audit fields** (created_at, updated_at)
- **Indexes** on frequently queried columns
- **JSONB** for FHIR resources

### 4. Security Practices
- **JWT tokens** for authentication
- **RBAC/ABAC** for authorization
- **Input validation** with Pydantic
- **SQL injection prevention** via ORM
- **CORS configuration** for frontend

### 5. Testing Strategy
- **Unit tests** for business logic
- **Integration tests** for API endpoints
- **E2E tests** for critical workflows
- **Load testing** before production
- **Security testing** for auth flows

### 6. LLM Integration Guidelines
- **Tool-based approach** - LLMs call defined tools
- **Safety classifications** for each tool
- **Audit logging** for all LLM actions
- **Human approval** for critical actions
- **Version tracking** for prompts and models

---

## Common Implementation Patterns

### 1. Service Structure
```python
# Every service follows this pattern
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from shared.database.connection import get_db
from shared.events.publisher import EventPublisher

app = FastAPI(title="Service Name")
event_publisher = EventPublisher()

@app.post("/api/v1/resource")
async def create_resource(data: Schema, db: Session = Depends(get_db)):
    # Validate
    # Create in DB
    # Publish event
    # Return response
    pass
```

### 2. Frontend API Calls
```typescript
// Consistent API client pattern
export const api = {
  patients: {
    create: (data: PatientCreate) =>
      fetch('/api/v1/patients', { method: 'POST', body: JSON.stringify(data) }),
    get: (id: string) =>
      fetch(`/api/v1/patients/${id}`),
    search: (params: SearchParams) =>
      fetch(`/api/v1/patients?${new URLSearchParams(params)}`)
  }
}
```

### 3. Event Publishing
```python
# Consistent event structure
await event_publisher.publish(
    event_type="Domain.Action",  # e.g., "Patient.Created"
    tenant_id=str(tenant_id),
    payload={
        "resource_id": str(resource_id),
        # Additional context
    }
)
```

---

## Troubleshooting Guide

### Common Issues & Solutions

1. **Database connection errors**
   - Check PostgreSQL is running
   - Verify DATABASE_URL in .env
   - Check network/firewall settings

2. **Import errors in Python**
   - Ensure virtual environment is activated
   - Check PYTHONPATH includes project root
   - Verify all dependencies installed

3. **Frontend build errors**
   - Clear node_modules and reinstall
   - Check Node version (should be 18+)
   - Verify all required packages installed

4. **Kafka connection issues**
   - Ensure Kafka/Zookeeper running
   - Check KAFKA_BOOTSTRAP_SERVERS
   - Fallback to database event log

5. **Authentication failures**
   - Verify JWT_SECRET_KEY is set
   - Check token expiration
   - Ensure user is active

---

## Deployment Checklist

### Before deploying to production:

- [ ] All services containerized with Dockerfile
- [ ] docker-compose.yml for local development
- [ ] Kubernetes manifests for production
- [ ] Environment variables properly configured
- [ ] Database migrations tested and ready
- [ ] API documentation generated
- [ ] Security audit completed
- [ ] Load testing performed
- [ ] Monitoring and logging configured
- [ ] Backup and recovery procedures documented
- [ ] HIPAA compliance verified
- [ ] SSL certificates configured
- [ ] Rate limiting implemented
- [ ] Error handling comprehensive
- [ ] Rollback procedures defined

---

## Resources & Documentation

### Key Technologies
- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://www.sqlalchemy.org/
- **Next.js**: https://nextjs.org/
- **FHIR R4**: https://www.hl7.org/fhir/
- **PostgreSQL JSONB**: https://www.postgresql.org/docs/current/datatype-json.html

### Healthcare Standards
- **FHIR Resources**: https://www.hl7.org/fhir/resourcelist.html
- **SNOMED CT**: https://www.snomed.org/
- **LOINC**: https://loinc.org/
- **ICD-10**: https://www.who.int/standards/classifications/classification-of-diseases

### AI/LLM Resources
- **LangChain**: https://python.langchain.com/
- **OpenAI API**: https://platform.openai.com/
- **Anthropic Claude**: https://www.anthropic.com/

---

## Getting Help

### For implementation questions:
1. Review the detailed phase guides
2. Check the troubleshooting section
3. Consult the API documentation
4. Review similar service implementations
5. Test in isolation before integrating

### Architecture decisions:
- Refer to `IMPLEMENTATION_GUIDE_MASTER_ARCHITECTURE.md`
- Follow established patterns
- Maintain consistency across services
- Document any deviations

---

This guide provides everything needed to implement the AI-native healthcare platform. Start with Phase 1 and progress sequentially. Each phase builds on the previous one, so complete implementation and testing before moving forward.
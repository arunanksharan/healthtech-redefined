# Phase 2 Implementation Status

**Date**: 2025-01-15
**Phase**: Phase 2 - OPD Workflows & Agentic PRM
**Status**: Database Models Complete, Services In Progress

---

## ✅ Completed

### Phase 2 Database Models (100%)

All Phase 2 models have been added to `backend/shared/database/models.py`:

#### Scheduling & Appointments
- `ProviderSchedule` - Recurring provider availability templates
- `TimeSlot` - Materialized appointment slots
- `Appointment` - Patient appointments with status tracking

#### Encounters
- `Encounter` - Clinical OPD encounters linked to appointments

#### PRM (Patient Relationship Management)
- `Journey` - Journey definitions (care programs)
- `JourneyStage` - Stages within journeys
- `JourneyInstance` - Patient journey instances
- `JourneyInstanceStageStatus` - Stage progress tracking
- `Communication` - Patient communications (WhatsApp, SMS, Email)
- `Ticket` - Support tickets

**Total New Models**: 10
**Total New Indexes**: 15+
**Relationships Added**: 15+

---

## 🚧 In Progress

### Services to Implement

#### 1. Scheduling Service (Port 8005)
**Priority**: High
**Estimated Lines**: 800+

**Endpoints Needed**:
```
Provider Schedules:
POST   /api/v1/scheduling/schedules
GET    /api/v1/scheduling/schedules
PATCH  /api/v1/scheduling/schedules/{id}

Slots:
POST   /api/v1/scheduling/schedules/{schedule_id}/materialize
GET    /api/v1/scheduling/slots

Appointments:
POST   /api/v1/scheduling/appointments
GET    /api/v1/scheduling/appointments/{id}
GET    /api/v1/scheduling/appointments
PATCH  /api/v1/scheduling/appointments/{id}
POST   /api/v1/scheduling/appointments/{id}/check-in
POST   /api/v1/scheduling/appointments/{id}/no-show
POST   /api/v1/scheduling/appointments/{id}/complete
```

**Key Features**:
- Provider schedule templates
- Slot materialization for date ranges
- Appointment booking with capacity validation
- Status management (booked → checked_in → completed)
- Event publishing for PRM integration

---

#### 2. Encounter Service (Port 8006)
**Priority**: High
**Estimated Lines**: 600+

**Endpoints Needed**:
```
Encounters:
POST   /api/v1/encounters
GET    /api/v1/encounters/{id}
GET    /api/v1/encounters
PATCH  /api/v1/encounters/{id}
POST   /api/v1/encounters/{id}/complete
```

**Key Features**:
- Create encounters from appointments
- FHIR Encounter resource generation
- Link to patient timeline
- Status transitions (planned → in-progress → completed)
- Event publishing

---

#### 3. PRM Service (Port 8007)
**Priority**: High
**Estimated Lines**: 1,200+

**Endpoints Needed**:
```
Journeys:
POST   /api/v1/prm/journeys
GET    /api/v1/prm/journeys
GET    /api/v1/prm/journeys/{id}
PATCH  /api/v1/prm/journeys/{id}

Journey Stages:
POST   /api/v1/prm/journeys/{journey_id}/stages
GET    /api/v1/prm/journeys/{journey_id}/stages

Journey Instances:
POST   /api/v1/prm/journey-instances
GET    /api/v1/prm/journey-instances
GET    /api/v1/prm/journey-instances/{id}
POST   /api/v1/prm/journey-instances/{id}/advance
PATCH  /api/v1/prm/journey-instances/{id}

Communications:
POST   /api/v1/prm/communications
GET    /api/v1/prm/communications

Tickets:
POST   /api/v1/prm/tickets
GET    /api/v1/prm/tickets
PATCH  /api/v1/prm/tickets/{id}
```

**Key Features**:
- Journey definition management
- Patient journey orchestration
- Event-driven stage transitions
- Multi-channel communications (WhatsApp, SMS, Email)
- Ticket management
- Event consumers for appointment/encounter events

---

#### 4. Scribe Service (Port 8008)
**Priority**: Medium
**Estimated Lines**: 400+

**Endpoints Needed**:
```
Scribe:
POST   /api/v1/scribe/draft-note
POST   /api/v1/scribe/validate-note
```

**Key Features**:
- AI-powered SOAP note generation
- FHIR bundle creation from transcript
- Problem extraction with SNOMED/ICD codes
- Order suggestions (labs, imaging, medications)
- Stateless design (no DB writes, just transformations)

---

## 📊 Implementation Statistics (Projected)

```
Services to Implement:    4
API Endpoints:            40+
Lines of Code:            3,000+
Event Types:              15+ new
LLM Tools:                12+
```

---

## 🔄 Next Steps

### Immediate Tasks (Priority Order)

1. **Database Migration** (15 min)
   ```bash
   cd backend
   alembic revision --autogenerate -m "Phase 2 schema"
   alembic upgrade head
   ```

2. **Scheduling Service** (3-4 hours)
   - Create service structure
   - Implement provider schedule CRUD
   - Slot materialization logic
   - Appointment booking with validation
   - Event publishing

3. **Encounter Service** (2-3 hours)
   - Create service structure
   - Encounter CRUD linked to appointments
   - FHIR resource generation
   - Status management

4. **PRM Service** (4-5 hours)
   - Journey management
   - Journey instance orchestration
   - Event consumer setup
   - Communication integration
   - Ticket management

5. **Scribe Service** (2-3 hours)
   - LLM integration setup
   - SOAP note generation prompts
   - FHIR resource drafting
   - Validation logic

### Migration Strategy

Since this is a significant schema addition, here's the recommended approach:

```bash
# 1. Activate virtual environment
cd backend
source venv/bin/activate

# 2. Generate migration
alembic revision --autogenerate -m "Phase 2: Add scheduling, encounters, and PRM models"

# 3. Review migration file
# Check alembic/versions/<revision>_phase_2_add_scheduling.py

# 4. Apply migration
alembic upgrade head

# 5. Verify
python -c "from shared.database.models import *; print('All models imported successfully')"
```

---

## 🎯 Success Criteria for Phase 2

When complete, the system should support:

1. **OPD Scheduling**
   - Doctors can define their weekly schedules
   - Slots are automatically materialized
   - Patients can book/reschedule/cancel appointments
   - Real-time capacity tracking

2. **Clinical Encounters**
   - Encounters created from appointments
   - FHIR-compliant encounter records
   - Linked to patient timeline

3. **Patient Journeys**
   - Automated journey creation on appointment booking
   - Stage-based progression
   - Automated communications
   - Event-driven orchestration

4. **AI Clinical Notes**
   - Text transcripts → structured SOAP notes
   - FHIR resource drafts
   - Problem and order extraction

---

## 📁 File Structure (Phase 2)

```
backend/
├── services/
│   ├── scheduling-service/
│   │   ├── __init__.py
│   │   ├── main.py (800+ lines)
│   │   ├── schemas.py (500+ lines)
│   │   └── Dockerfile
│   ├── encounter-service/
│   │   ├── __init__.py
│   │   ├── main.py (600+ lines)
│   │   ├── schemas.py (300+ lines)
│   │   └── Dockerfile
│   ├── prm-service/
│   │   ├── __init__.py
│   │   ├── main.py (1,200+ lines)
│   │   ├── schemas.py (700+ lines)
│   │   ├── event_handlers.py (400+ lines)
│   │   └── Dockerfile
│   └── scribe-service/
│       ├── __init__.py
│       ├── main.py (400+ lines)
│       ├── schemas.py (200+ lines)
│       ├── llm_prompts.py (300+ lines)
│       └── Dockerfile
└── shared/
    └── database/
        └── models.py (now 1,000+ lines with Phase 2 models)
```

---

## 🔗 Integration Points

### Event Flow

```
Appointment.Created (Scheduling Service)
    ↓
Journey.Created (PRM Service auto-creates journey instance)
    ↓
Communication.Sent (PRM sends appointment confirmation)
    ↓
Appointment.CheckedIn (Scheduling Service)
    ↓
Encounter.Created (Encounter Service)
    ↓
Journey.StageAdvanced (PRM advances to "day-of-visit")
    ↓
Encounter.Completed (Encounter Service)
    ↓
Journey.StageAdvanced (PRM advances to "post-visit")
    ↓
Communication.Sent (PRM sends follow-up)
```

### Service Dependencies

```
Scheduling Service
    ↓ events
PRM Service (Journey Orchestrator)
    ↓ events
Encounter Service
    ↓ FHIR resources
FHIR Service (storage)
```

---

## 🚀 Quick Commands

### Start Phase 2 Services (after implementation)

```bash
# Start infrastructure
docker-compose up -d postgres redis kafka zookeeper

# Apply migrations
cd backend && source venv/bin/activate
alembic upgrade head

# Start Phase 2 services
docker-compose up scheduling-service encounter-service prm-service scribe-service
```

### Access API Documentation

```
Scheduling Service:  http://localhost:8005/docs
Encounter Service:   http://localhost:8006/docs
PRM Service:         http://localhost:8007/docs
Scribe Service:      http://localhost:8008/docs
```

---

## 💡 Key Design Decisions

1. **Slot Materialization**: Pre-generate slots for better performance vs on-the-fly calculation
2. **Event-Driven PRM**: Journey orchestration driven by events, not polling
3. **Stateless Scribe**: No DB writes, pure transformation service
4. **FHIR-First**: All clinical data stored as FHIR resources
5. **Multi-Channel Comms**: Support WhatsApp, SMS, Email from single API

---

## 📝 Notes

- All services follow Phase 1 patterns (FastAPI, Pydantic, async/await, event publishing)
- Complete FHIR R4 compliance maintained
- Type safety throughout with comprehensive validation
- OpenAPI documentation auto-generated
- Docker containerization for all services

---

**Status**: Ready to implement services
**Next Action**: Create Alembic migration, then implement Scheduling Service
**Estimated Completion**: 12-15 hours for all 4 services

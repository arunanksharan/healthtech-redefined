# Phase 10 Implementation Status
## OR / Procedure / Perioperative Management

**Status**: ✅ CORE COMPLETE (Database & Events) | 🔄 SERVICES READY FOR IMPLEMENTATION
**Last Updated**: 2025-01-15

---

## Overview

Phase 10 implements comprehensive perioperative management covering the entire surgical journey from request through recovery:
- Surgery request workflow (FHIR ServiceRequest)
- OR scheduling with block time management
- Pre-operative assessment and risk scoring
- Intra-operative surgical case documentation (FHIR Procedure)
- Anesthesia charting and vital sign tracking
- PACU recovery monitoring
- AI-powered case duration estimation, risk summaries, and handoff notes

---

## Database Models (20 Models) ✅ COMPLETE

### ✅ Surgery Request & Catalog (2 models)
- [x] `SurgeryProcedureCatalog` - Catalog of surgical procedures with default parameters
- [x] `SurgeryRequest` - Surgery requests from clinics/wards/ED (FHIR ServiceRequest)

**Location**: `backend/shared/database/models.py:5097-5162`

### ✅ OR Scheduling (3 models)
- [x] `ORRoom` - Operating rooms/theatres
- [x] `ORBlock` - Scheduled block time for services/surgeons
- [x] `ORCaseSchedule` - Scheduled surgical cases in OR

**Location**: `backend/shared/database/models.py:5165-5251`

### ✅ Pre-operative Assessment (3 models)
- [x] `PreopAssessment` - Pre-anesthesia evaluation and clearance
- [x] `PreopRiskScore` - Perioperative risk scores (RCRI, NSQIP, etc.)
- [x] `PreopOptimizationTask` - Tasks to optimize patient before surgery

**Location**: `backend/shared/database/models.py:5254-5327`

### ✅ Surgical Case (4 models)
- [x] `SurgicalCase` - Intra-operative surgical case record (FHIR Procedure)
- [x] `SurgicalCaseTeamMember` - OR team members
- [x] `SurgicalCaseImplant` - Implants used (FHIR Device)
- [x] `SurgicalCaseSpecimen` - Specimens collected (links to AP)

**Location**: `backend/shared/database/models.py:5329-5431`

### ✅ Anesthesia (3 models)
- [x] `AnesthesiaRecord` - Intra-operative anesthesia chart
- [x] `AnesthesiaEvent` - Events during anesthesia (drugs, fluids, airway, procedures)
- [x] `AnesthesiaVitals` - Vital signs during anesthesia

**Location**: `backend/shared/database/models.py:5433-5516`

### ✅ PACU Recovery (3 models)
- [x] `PACUStay` - Post-Anesthesia Care Unit stay
- [x] `PACUVitals` - Vital signs in PACU
- [x] `PACUScore` - Recovery scores (Aldrete, Modified Aldrete)

**Location**: `backend/shared/database/models.py:5519-5593`

### ✅ Periop AI (2 models)
- [x] `PeriopAITask` - AI tasks for perioperative workflows
- [x] `PeriopAIOutput` - AI outputs (duration estimates, risk summaries, handoff notes)

**Location**: `backend/shared/database/models.py:5596-5633`

---

## Backend Services (7 Services)

### ✅ 1. Surgery Request Service (Port 8050) - COMPLETE
**Purpose**: Surgical/procedure requests from clinics/wards/ED

**Endpoints**: 6 endpoints
- Surgery Procedure Catalog: POST, GET (list with search)
- Surgery Requests: POST (create), GET (list with filters), GET (detail), PATCH (update status)

**Key Features**:
- FHIR ServiceRequest mapping
- Procedure catalog with typical duration and preop requirements
- Urgency levels (elective, urgent, emergency)
- Status tracking (requested, accepted, rejected, scheduled, cancelled, completed)
- Event publishing (created, scheduled, cancelled)

**Location**: `backend/services/surgery-request-service/`
- `main.py` (222 lines)
- `schemas.py` (77 lines)

---

### 🔄 2. OR Scheduling Service (Port 8051) - READY FOR IMPLEMENTATION
**Purpose**: OR rooms, block time, case scheduling, turnover tracking

**Planned Endpoints**: 9+ endpoints
- OR Rooms: POST, GET (list), GET (detail)
- OR Blocks: POST, GET (list by room/day)
- OR Case Schedule: POST (create), GET (list by date/room/surgeon), PATCH (reschedule/cancel/update times)

**Key Features**:
- Block time management per specialty/surgeon
- Case scheduling with priority (elective, urgent, emergency)
- Actual vs scheduled time tracking
- Turnover time monitoring
- Case number generation
- Event publishing (scheduled, started, completed, cancelled)

**Implementation Pattern**: Follow Surgery Request Service structure

---

### 🔄 3. Preop Assessment Service (Port 8052) - READY FOR IMPLEMENTATION
**Purpose**: Pre-anesthesia evaluation, risk scoring, optimization tasks

**Planned Endpoints**: 7+ endpoints
- Preop Assessments: POST, GET (list), GET (detail), PATCH (update ASA/status)
- Risk Scores: POST, GET (list)
- Optimization Tasks: POST, PATCH (update status)

**Key Features**:
- ASA classification (I-VI)
- Airway assessment (Mallampati, etc.)
- Risk scoring (RCRI, NSQIP, custom)
- Functional status (METs)
- Investigations reviewed tracker
- Optimization task workflow (pending → in_progress → completed)
- Event publishing (created, cleared, optimization task created)

**Implementation Pattern**: Follow Surgery Request Service structure

---

### 🔄 4. Surgical Case Service (Port 8053) - READY FOR IMPLEMENTATION
**Purpose**: Intra-operative surgical case documentation

**Planned Endpoints**: 8+ endpoints
- Surgical Cases: POST, GET (list), GET (detail), PATCH (update times/procedure/EBL/status)
- Team Members: POST (add team member)
- Implants: POST (record implant)
- Specimens: POST (record specimen)

**Key Features**:
- FHIR Procedure mapping
- Procedure performed vs planned tracking
- Incision/closure time recording
- Estimated blood loss
- Wound classification
- Team documentation (surgeon, assistants, anesthetist, nurses)
- Implant tracking (UDI, lot numbers, expiry)
- Specimen collection (links to AP)
- Disposition (PACU, ICU, ward)
- Event publishing (created, started, completed)

**Implementation Pattern**: Follow Surgery Request Service structure

---

### 🔄 5. Anesthesia Record Service (Port 8054) - READY FOR IMPLEMENTATION
**Purpose**: Intra-operative anesthesia charting

**Planned Endpoints**: 6+ endpoints
- Anesthesia Records: POST, GET (list), GET (detail), PATCH (update)
- Events: POST (record drug/fluid/airway event)
- Vitals: POST (record vital signs)

**Key Features**:
- Airway management documentation (ETT, LMA, mask)
- Induction/maintenance/reversal agents
- Timeline of events (drugs, fluids, procedures, complications)
- Vital signs tracking (HR, BP, SpO2, RR, EtCO2, temp)
- Link to medication products for drug events
- Event publishing (record created, event recorded)

**Implementation Pattern**: Follow Surgery Request Service structure

---

### 🔄 6. PACU Recovery Service (Port 8055) - READY FOR IMPLEMENTATION
**Purpose**: Post-anesthesia care unit monitoring

**Planned Endpoints**: 5+ endpoints
- PACU Stays: POST (create), GET (list), PATCH (update/discharge)
- Vitals: POST (record vitals)
- Scores: POST (record recovery scores)

**Key Features**:
- Admission/discharge tracking
- Initial status (stable, requires_observation, critical)
- Vital signs with pain/sedation scoring
- Recovery scores (Aldrete, Modified Aldrete)
- Complications tracking
- Disposition (ward, ICU, home)
- Event publishing (admission, discharge)

**Implementation Pattern**: Follow Surgery Request Service structure

---

### 🔄 7. Periop AI Orchestrator Service (Port 8056) - READY FOR IMPLEMENTATION
**Purpose**: AI workflows for perioperative tasks

**Planned Endpoints**: 7 endpoints
- AI Tasks: POST, GET (list), GET (detail), PATCH (update status)
- AI Outputs: POST, GET (list), GET (detail)

**Key Features**:
- Task types:
  - `case_duration_estimate` - Predict OR time based on procedure/surgeon/patient
  - `preop_risk_summary` - Synthesize risk profile from comorbidities/labs
  - `handoff_note` - Generate structured handoff from intra-op + PACU data
  - `or_list_optimisation` - Suggest case reordering to minimize overtime
- Output types:
  - `duration_estimate`
  - `risk_summary`
  - `handoff_text`
  - `optimised_list`
- Task status: queued, running, completed, failed
- Event publishing (task created, completed, failed, output created)

**Implementation Pattern**: Follow Surgery Request Service and Pharmacy AI Orchestrator Service structures

---

## Event Types (22 Events) ✅ COMPLETE

### ✅ Surgery Request Events (4)
- `SURGERY_REQUEST_CREATED`
- `SURGERY_REQUEST_SCHEDULED`
- `SURGERY_REQUEST_CANCELLED`
- `SURGERY_REQUEST_COMPLETED`

### ✅ OR Scheduling Events (4)
- `OR_CASE_SCHEDULED`
- `OR_CASE_STARTED`
- `OR_CASE_COMPLETED`
- `OR_CASE_CANCELLED`

### ✅ Preop Assessment Events (3)
- `PREOP_ASSESSMENT_CREATED`
- `PREOP_ASSESSMENT_CLEARED`
- `PREOP_OPTIMIZATION_TASK_CREATED`

### ✅ Surgical Case Events (3)
- `SURGICAL_CASE_CREATED`
- `SURGICAL_CASE_STARTED`
- `SURGICAL_CASE_COMPLETED`

### ✅ Anesthesia Events (2)
- `ANESTHESIA_RECORD_CREATED`
- `ANESTHESIA_EVENT_RECORDED`

### ✅ PACU Events (2)
- `PACU_ADMISSION`
- `PACU_DISCHARGE`

### ✅ Periop AI Events (4)
- `PERIOP_AI_TASK_CREATED`
- `PERIOP_AI_TASK_COMPLETED`
- `PERIOP_AI_TASK_FAILED`
- `PERIOP_AI_OUTPUT_CREATED`

**Location**: `backend/shared/events/types.py:341-375`

---

## FHIR Mappings

### Resources Mapped
1. **ServiceRequest** ↔ `SurgeryRequest`
2. **Schedule & Slot** ↔ `ORRoom`, `ORBlock`, `ORCaseSchedule` (for API consumers)
3. **Encounter** ↔ Pre-op assessment encounters
4. **Observation** ↔ ASA class, functional status, risk scores, vital signs
5. **Procedure** ↔ `SurgicalCase`
6. **Device & DeviceUseStatement** ↔ `SurgicalCaseImplant`
7. **Specimen** ↔ `SurgicalCaseSpecimen`
8. **MedicationAdministration** ↔ Anesthesia events (drugs)

---

## Key Design Patterns

### 1. Procedure-Centric Spine
- Surgical case is the central record linking all perioperative data
- All data flows through: Request → Schedule → Case → Recovery

### 2. FHIR-First Alignment
- Surgery requests map to ServiceRequest
- Surgical cases map to Procedure
- All major entities have FHIR resource IDs

### 3. Tight Integration
- Links to imaging (pre-op requirements, intra-op imaging)
- Links to labs (pre-op clearance, intra-op results)
- Links to pharmacy (anesthesia medications)
- Links to pathology (specimens)
- Links to ICU/IPD (disposition, post-op care)

### 4. AI in Support Roles
- AI suggests, doesn't decide
- Duration estimates, risk summaries, optimization tasks are recommendations
- Human confirmation required for all clinical decisions

### 5. Comprehensive Time Tracking
- Requested → Scheduled → Actual start/end
- Incision/closure times
- Anesthesia start/end
- PACU admission/discharge
- Turnover times for OR efficiency

### 6. Multi-Dimensional Safety
- Pre-op risk scoring and optimization
- Intra-op implant/specimen tracking
- Post-op recovery monitoring
- Complete audit trail

---

## Summary Statistics

| Category | Count |
|----------|-------|
| **Database Models** | 20 |
| **Services** | 7 (1 complete, 6 ready for implementation) |
| **Endpoints** | 60+ (planned) |
| **Event Types** | 22 |
| **Total Lines of Code (DB + Events + Service 1)** | ~900+ |

---

## Port Assignments

| Service | Port |
|---------|------|
| Surgery Request Service | 8050 |
| OR Scheduling Service | 8051 |
| Preop Assessment Service | 8052 |
| Surgical Case Service | 8053 |
| Anesthesia Record Service | 8054 |
| PACU Recovery Service | 8055 |
| Periop AI Orchestrator Service | 8056 |

---

## Completeness Checklist

### Database & Events
- [x] All 20 database models implemented with proper relationships
- [x] All indexes defined for performance
- [x] All 22 event types defined
- [x] FHIR mapping documented
- [x] Multi-tenancy support
- [x] Comprehensive time tracking fields
- [x] Safety tracking (implants, specimens, risks)

### Services
- [x] Surgery Request Service (Port 8050) - COMPLETE
- [ ] OR Scheduling Service (Port 8051) - Ready for implementation
- [ ] Preop Assessment Service (Port 8052) - Ready for implementation
- [ ] Surgical Case Service (Port 8053) - Ready for implementation
- [ ] Anesthesia Record Service (Port 8054) - Ready for implementation
- [ ] PACU Recovery Service (Port 8055) - Ready for implementation
- [ ] Periop AI Orchestrator Service (Port 8056) - Ready for implementation

---

## Implementation Notes

### Services Ready for Implementation

The remaining 6 services can be implemented by following the established pattern from the Surgery Request Service:

1. **Standard Service Structure**:
   - `__init__.py` - Package marker
   - `schemas.py` - Pydantic request/response models
   - `main.py` - FastAPI app with endpoints

2. **Common Patterns**:
   - Database session management with `get_db()`
   - Entity existence verification before creation
   - Event publishing for state changes
   - Proper error handling (404, 400 status codes)
   - Multi-tenancy support
   - Timestamp tracking (created_at, updated_at)

3. **Standard Endpoints**:
   - POST (create) with validation
   - GET (list) with filters
   - GET (detail) by ID
   - PATCH (update) for status/field changes
   - Health check endpoint

4. **Service-Specific Features** (per requirements):
   - **OR Scheduling**: Block time management, turnover tracking, room scheduling
   - **Preop Assessment**: ASA classification, risk scoring, optimization tasks
   - **Surgical Case**: Team documentation, implant tracking, specimen collection
   - **Anesthesia Record**: Event timeline, vital signs charting
   - **PACU Recovery**: Recovery scores, pain/sedation tracking
   - **Periop AI**: Task orchestration following Pharmacy AI pattern

### Estimated Implementation Time
Each service: ~200-300 lines of code (following established patterns)
Total: ~1,500-2,000 additional lines for all 6 services

---

## Next Steps (Future Enhancements)

1. **Frontend Implementation**:
   - Surgery request form with AI-suggested preop requirements
   - OR day-of-surgery board (drag-and-drop scheduling)
   - Pre-op assessment interface
   - Intra-op documentation (anesthesia timeline, surgical notes)
   - PACU recovery board

2. **Advanced Features**:
   - Real-time OR board updates
   - Automated case duration predictions based on historical data
   - Smart scheduling with constraint satisfaction
   - Equipment/resource tracking
   - Staff availability integration
   - Post-op order sets

3. **AI Enhancement**:
   - ML-based duration prediction (surgeon-specific, procedure-specific)
   - Automated risk stratification
   - Natural language handoff note generation
   - OR list optimization with multiple objectives
   - Complication prediction

4. **Integration**:
   - Anesthesia machine data feeds
   - Vital sign monitors (HL7/FHIR integration)
   - PACS integration for intra-op imaging
   - Instrument tracking systems
   - Blood bank integration

---

**Phase 10 Status**: ✅ **CORE COMPLETE** (Database Models + Events)

🔄 **Services**: 1 of 7 complete, 6 ready for implementation following established patterns

All Phase 10 database infrastructure and event types are production-ready. The Surgery Request Service provides a complete implementation template for the remaining 6 services.

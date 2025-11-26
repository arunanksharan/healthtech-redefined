# UI/UX Epic to Backend API Mapping - Part 2
## Patient 360 (UX-004) & Organization Management (UX-005)

**Version:** 1.0
**Date:** November 26, 2024
**Purpose:** Map all UI/UX flows to existing backend APIs to ensure no significant backend development is required.

---

## EPIC UX-004: Patient 360 Profile

### Overview
The Patient 360 Profile provides a comprehensive, narrative-based view of patient data. **All required APIs exist via FHIR and existing modules.**

### UI Component: Patient Profile Page

#### Layout Description
```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ← Back to Patients                                            [⚙️] [Print] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        PATIENT HEADER                                │  │
│  │  ┌──────┐                                                            │  │
│  │  │ 👤   │  John Doe                                    [Edit] [⋮]   │  │
│  │  │ Photo│  DOB: Jan 15, 1965 (59y) • Male • MRN: 12345              │  │
│  │  └──────┘  📱 +1 (555) 123-4567 • 📧 john.doe@email.com             │  │
│  │                                                                      │  │
│  │  ⚠️ ALERTS: 🔴 Allergy: Penicillin │ 🟡 Fall Risk │ 🟡 Care Gap    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  HEALTH METRICS                                                      │  │
│  │  ┌─────────┬─────────┬─────────┬─────────┬─────────┐                │  │
│  │  │ BP      │ HR      │ Weight  │ A1C     │ Cholest │                │  │
│  │  │ 138/88  │ 78 bpm  │ 185 lbs │ 7.2%    │ 220     │                │  │
│  │  │ 🟡↑     │ 🟢      │ 🟡↑     │ 🟡↑     │ 🟢↓     │                │  │
│  │  └─────────┴─────────┴─────────┴─────────┴─────────┘                │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  🤖 AI SUMMARY                                         [Regenerate] │  │
│  │  John Doe is a 59-year-old male with Type 2 Diabetes, Hypertension  │  │
│  │  and Hyperlipidemia. Recent activity: BP elevated at last visit...  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  TIMELINE                                  [Filter▼] [View: Story▼] │  │
│  │  ════════════════════════════════════════════════════════════════   │  │
│  │  │ 📅 TODAY                                                         │  │
│  │  │ ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │ │ ⏰ 2:00 PM - Scheduled Appointment                          │  │  │
│  │  │ │    Dr. Sharma • Cardiology Follow-up                        │  │  │
│  │  │ └─────────────────────────────────────────────────────────────┘  │  │
│  │  │                                                                  │  │
│  │  │ 📅 NOV 22                                                        │  │
│  │  │ ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │ │ 🎤 Zoice Call (4 min)                         😤 Frustrated │  │  │
│  │  │ │    Medication side effects concern                          │  │  │
│  │  │ └─────────────────────────────────────────────────────────────┘  │  │
│  │  ════════════════════════════════════════════════════════════════   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ [📅 Book Apt] [💊 Prescribe] [🧪 Order Lab] [📝 Note] [💬 Message] │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### API Mapping

#### 1. Patient Demographics & Header
**UI Action:** Load patient basic info
**Backend APIs:**

| UI Element | Backend API | Endpoint | Notes |
|------------|-------------|----------|-------|
| Patient demographics | Patients | `GET /patients/{id}` | Name, DOB, contact |
| Patient FHIR resource | FHIR | `GET /fhir/Patient/{id}` | Full FHIR patient |
| Next appointment | Patients | `GET /patients/{id}/appointments` | Filter upcoming |
| Insurance info | FHIR | `GET /fhir/Coverage?beneficiary={patient}` | Or stored in patient |
| Primary provider | FHIR | `GET /fhir/Practitioner/{id}` | From patient.generalPractitioner |

```typescript
// Load patient header data
const loadPatientHeader = async (patientId: string) => {
  const [patient, appointments] = await Promise.all([
    api.get(`/patients/${patientId}`),
    api.get(`/patients/${patientId}/appointments`)
  ]);

  const nextAppointment = appointments
    .filter(a => a.status === 'booked' && new Date(a.confirmed_start) > new Date())
    .sort((a, b) => new Date(a.confirmed_start) - new Date(b.confirmed_start))[0];

  return { ...patient, nextAppointment };
};
```

#### 2. Alerts & Allergies
**UI Action:** Display critical patient alerts
**Backend APIs:**

| Alert Type | Backend API | Endpoint |
|------------|-------------|----------|
| Allergies | FHIR | `GET /fhir/AllergyIntolerance?patient={id}` |
| Conditions (fall risk) | FHIR | `GET /fhir/Condition?patient={id}&category=health-concern` |
| Care gaps | Analytics | `GET /analytics/dashboard?patient_id={id}` |

```typescript
// Load patient alerts
const loadPatientAlerts = async (patientId: string) => {
  const [allergies, conditions] = await Promise.all([
    api.get('/fhir/AllergyIntolerance', { params: { patient: patientId } }),
    api.get('/fhir/Condition', { params: { patient: patientId } })
  ]);

  return {
    allergies: allergies.entry?.map(e => e.resource) || [],
    conditions: conditions.entry?.map(e => e.resource) || [],
    // Care gaps would be computed from missing preventive care
  };
};
```

#### 3. Health Metrics Widget
**UI Action:** Display vital signs with trends
**Backend API:** FHIR Observation

| Metric | FHIR Code | Endpoint |
|--------|-----------|----------|
| Blood Pressure | 85354-9 | `GET /fhir/Observation?patient={id}&code=85354-9&_sort=-date` |
| Heart Rate | 8867-4 | `GET /fhir/Observation?patient={id}&code=8867-4&_sort=-date` |
| Weight | 29463-7 | `GET /fhir/Observation?patient={id}&code=29463-7&_sort=-date` |
| A1C | 4548-4 | `GET /fhir/Observation?patient={id}&code=4548-4&_sort=-date` |
| Cholesterol | 2093-3 | `GET /fhir/Observation?patient={id}&code=2093-3&_sort=-date` |

```typescript
// Load health metrics with trends
const loadHealthMetrics = async (patientId: string) => {
  const codes = ['85354-9', '8867-4', '29463-7', '4548-4', '2093-3'];

  const metrics = await Promise.all(
    codes.map(code =>
      api.get('/fhir/Observation', {
        params: {
          patient: patientId,
          code: code,
          _sort: '-date',
          _count: 5 // Get last 5 for trend
        }
      })
    )
  );

  return metrics.map((m, i) => ({
    code: codes[i],
    observations: m.entry?.map(e => e.resource) || []
  }));
};
```

#### 4. AI Summary Generation
**UI Action:** Generate AI summary of patient
**Backend Capability:** Requires LLM integration (frontend or backend)

**Option A: Backend endpoint (if exists)**
```typescript
// Use agents module for summary generation
const generateSummary = async (patientId: string) => {
  return api.post('/agents/run', {
    name: 'generate_patient_summary',
    args: { patient_id: patientId }
  });
};
```

**Option B: Frontend LLM call with FHIR data**
```typescript
// Fetch all patient data and send to LLM
const generateSummary = async (patientId: string) => {
  // Use FHIR $everything operation
  const bundle = await api.get(`/fhir/Patient/${patientId}/$everything`);

  // Send to OpenAI/Claude for summarization
  const prompt = `Summarize this patient's medical history for a physician review:
    ${JSON.stringify(bundle)}`;

  return callLLM(prompt);
};
```

#### 5. Patient Timeline
**UI Action:** Display chronological events
**Backend APIs:** Multiple sources aggregated

| Event Type | Backend API | Endpoint |
|------------|-------------|----------|
| Encounters/Visits | FHIR | `GET /fhir/Encounter?patient={id}&_sort=-date` |
| Appointments | Patients | `GET /patients/{id}/appointments` |
| Voice calls | Conversations | `GET /conversations?patient_id={id}` filtered by source |
| WhatsApp messages | Conversations | `GET /conversations?patient_id={id}` filtered by channel |
| Prescriptions | FHIR | `GET /fhir/MedicationRequest?patient={id}&_sort=-date` |
| Lab results | FHIR | `GET /fhir/DiagnosticReport?patient={id}&_sort=-date` |

```typescript
// Aggregate timeline events
const loadTimeline = async (patientId: string, filters: TimelineFilters) => {
  const [encounters, appointments, conversations, medications, labs] = await Promise.all([
    api.get('/fhir/Encounter', { params: { patient: patientId, _sort: '-date', _count: 20 } }),
    api.get(`/patients/${patientId}/appointments`),
    api.get('/conversations', { params: { patient_id: patientId, limit: 20 } }),
    api.get('/fhir/MedicationRequest', { params: { patient: patientId, _sort: '-date', _count: 20 } }),
    api.get('/fhir/DiagnosticReport', { params: { patient: patientId, _sort: '-date', _count: 20 } })
  ]);

  // Merge and sort all events by date
  const events = [
    ...transformEncounters(encounters),
    ...transformAppointments(appointments),
    ...transformConversations(conversations),
    ...transformMedications(medications),
    ...transformLabs(labs)
  ].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

  return events;
};
```

#### 6. "Ask Patient Data" Feature
**UI Action:** Natural language query about patient
**Implementation:** Frontend LLM + FHIR queries

```typescript
const askPatientData = async (patientId: string, query: string) => {
  // 1. Parse query intent
  const intent = await parseQueryIntent(query);

  // 2. Fetch relevant data based on intent
  let data;
  switch (intent.type) {
    case 'vital_trend':
      data = await api.get('/fhir/Observation', {
        params: {
          patient: patientId,
          code: intent.vitalCode,
          _sort: '-date',
          _count: intent.count || 10
        }
      });
      break;
    case 'medication_list':
      data = await api.get('/fhir/MedicationRequest', {
        params: { patient: patientId, status: 'active' }
      });
      break;
    case 'generate_document':
      // Use LLM to generate letter/referral
      const patientBundle = await api.get(`/fhir/Patient/${patientId}/$everything`);
      data = await generateDocument(intent.documentType, patientBundle);
      break;
  }

  // 3. Format response
  return formatResponse(intent, data);
};
```

#### 7. Care Gaps
**UI Action:** Display overdue preventive care
**Implementation:** Computed from FHIR data

```typescript
// Care gaps are computed by comparing:
// - Last date of specific procedure/observation
// - Recommended intervals for patient demographics

const computeCareGaps = async (patientId: string) => {
  const [patient, procedures, observations] = await Promise.all([
    api.get(`/fhir/Patient/${patientId}`),
    api.get('/fhir/Procedure', { params: { patient: patientId } }),
    api.get('/fhir/Observation', { params: { patient: patientId } })
  ]);

  const gaps = [];
  const age = calculateAge(patient.birthDate);

  // Example: A1C for diabetics every 6 months
  const lastA1C = findLastObservation(observations, '4548-4');
  if (isDiabetic(patient) && monthsSince(lastA1C?.date) > 6) {
    gaps.push({
      type: 'A1C Test',
      lastDate: lastA1C?.date,
      dueDate: addMonths(lastA1C?.date, 6),
      overdue: true
    });
  }

  return gaps;
};
```

#### 8. Communication History
**UI Action:** View all patient communications
**Backend APIs:**

| Source | Backend API | Endpoint |
|--------|-------------|----------|
| All conversations | Conversations | `GET /conversations?patient_id={id}` |
| Messages | Conversations | `GET /conversations/{id}/messages` |
| Media/Attachments | Media | `GET /media?patient_id={id}` |
| Voice recordings | Media | `GET /media?patient_id={id}&category=voice_recording` |

### Gap Analysis for UX-004

| Feature | Backend Status | Gap Level | Notes |
|---------|---------------|-----------|-------|
| Patient demographics | ✅ Complete | None | Full API |
| FHIR Patient | ✅ Complete | None | Full CRUD |
| Observations (vitals) | ✅ Complete | None | Full FHIR search |
| Conditions | ✅ Complete | None | Full FHIR |
| Allergies | ✅ Complete | None | Full FHIR |
| MedicationRequest | ✅ Complete | None | Full FHIR |
| Encounters | ✅ Complete | None | Full FHIR |
| $everything operation | ✅ Complete | None | Implemented |
| Conversations | ✅ Complete | None | Full API |
| Media/recordings | ✅ Complete | None | Full API |
| AI Summary | ⚠️ Partial | Minor | Needs LLM integration (frontend or agents module) |
| Care Gaps | ⚠️ Partial | Minor | Needs frontend computation logic |

**Conclusion:** Backend APIs are complete. AI summary generation and care gap computation are frontend logic using existing data.

---

## EPIC UX-005: Organization & Entity Management

### Overview
This epic covers CRUD for FHIR entities (Organizations, Practitioners, Patients, Locations) and scheduling (Slots, Schedules). **All required APIs exist via FHIR router.**

### UI Component: Entity Management Sidebar

```
┌─────────────────────────────────────────────────────────────────────┐
│ SIDEBAR (200px)                                                     │
│                                                                     │
│ ┌─────────────────────────────┐                                    │
│ │ 🔍 Search entities...       │                                    │
│ └─────────────────────────────┘                                    │
│                                                                     │
│ ORGANIZATION                                                        │
│ ├── 🏢 Organizations                                               │
│ ├── 📍 Locations                                                   │
│ ├── 🏬 Departments                                                 │
│ └── 👥 Teams                                                       │
│                                                                     │
│ PEOPLE                                                              │
│ ├── 👨‍⚕️ Practitioners (Doctors)                                    │
│ ├── 👤 Patients                                                    │
│ └── 👥 Staff                                                       │
│                                                                     │
│ SCHEDULING                                                          │
│ ├── 📅 Schedules                                                   │
│ ├── 🕐 Slots                                                       │
│ └── 📆 Appointments                                                │
│                                                                     │
│ SETTINGS                                                            │
│ ├── ⚙️ Organization Settings                                       │
│ └── 🔐 Access Control                                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### API Mapping by Entity

#### 1. Organizations
**FHIR Resource:** Organization

| UI Action | HTTP Method | Endpoint | Notes |
|-----------|-------------|----------|-------|
| List organizations | GET | `/fhir/Organization` | Supports search params |
| Get organization | GET | `/fhir/Organization/{id}` | |
| Create organization | POST | `/fhir/Organization` | |
| Update organization | PUT | `/fhir/Organization/{id}` | |
| Delete organization | DELETE | `/fhir/Organization/{id}` | Soft delete |
| Search | GET | `/fhir/Organization?name=xxx` | |

```typescript
// Organization CRUD
const organizationApi = {
  list: () => api.get('/fhir/Organization'),
  get: (id: string) => api.get(`/fhir/Organization/${id}`),
  create: (data: Organization) => api.post('/fhir/Organization', data),
  update: (id: string, data: Organization) => api.put(`/fhir/Organization/${id}`, data),
  delete: (id: string) => api.delete(`/fhir/Organization/${id}`),
  search: (params: OrgSearchParams) => api.get('/fhir/Organization', { params })
};
```

#### 2. Locations
**FHIR Resource:** Location

| UI Action | HTTP Method | Endpoint |
|-----------|-------------|----------|
| List locations | GET | `/fhir/Location` |
| Get location | GET | `/fhir/Location/{id}` |
| Create location | POST | `/fhir/Location` |
| Update location | PUT | `/fhir/Location/{id}` |
| Delete location | DELETE | `/fhir/Location/{id}` |
| Search by org | GET | `/fhir/Location?organization={org_id}` |
| Search by name | GET | `/fhir/Location?name=xxx` |

#### 3. Practitioners (Doctors)
**FHIR Resource:** Practitioner, PractitionerRole

| UI Action | HTTP Method | Endpoint |
|-----------|-------------|----------|
| List practitioners | GET | `/fhir/Practitioner` |
| Get practitioner | GET | `/fhir/Practitioner/{id}` |
| Create practitioner | POST | `/fhir/Practitioner` |
| Update practitioner | PUT | `/fhir/Practitioner/{id}` |
| Delete practitioner | DELETE | `/fhir/Practitioner/{id}` |
| Search by name | GET | `/fhir/Practitioner?name=xxx` |
| Search by specialty | GET | `/fhir/Practitioner?specialty=xxx` |
| Get roles | GET | `/fhir/PractitionerRole?practitioner={id}` |

```typescript
// Practitioner list with details
const loadPractitioners = async (filters: PractitionerFilters) => {
  const params: any = { _count: filters.limit || 50 };

  if (filters.name) params.name = filters.name;
  if (filters.specialty) params.specialty = filters.specialty;

  const result = await api.get('/fhir/Practitioner', { params });
  return result.entry?.map(e => e.resource) || [];
};
```

#### 4. Patients
**Backend API:** Patients module (already covered in UX-004)

| UI Action | HTTP Method | Endpoint |
|-----------|-------------|----------|
| List patients | POST | `/patients/search` |
| Get patient | GET | `/patients/{id}` |
| Create patient | POST | `/patients` |
| Update patient | PATCH | `/patients/{id}` |
| Delete patient | DELETE | `/patients/{id}` |
| Search | POST | `/patients/search` |
| Find duplicates | GET | `/patients/{id}/duplicates` |
| Merge patients | POST | `/patients/merge` |
| Statistics | GET | `/patients/stats/demographics` |

#### 5. Schedules
**FHIR Resource:** Schedule (represents practitioner availability)

| UI Action | HTTP Method | Endpoint |
|-----------|-------------|----------|
| List schedules | GET | `/fhir/Schedule` |
| Get schedule | GET | `/fhir/Schedule/{id}` |
| Create schedule | POST | `/fhir/Schedule` |
| Update schedule | PUT | `/fhir/Schedule/{id}` |
| Get by practitioner | GET | `/fhir/Schedule?actor={practitioner_id}` |
| Get by location | GET | `/fhir/Schedule?actor={location_id}` |

#### 6. Slots
**FHIR Resource:** Slot (individual bookable time periods)

| UI Action | HTTP Method | Endpoint |
|-----------|-------------|----------|
| List slots | GET | `/fhir/Slot` |
| Get slot | GET | `/fhir/Slot/{id}` |
| Create slot | POST | `/fhir/Slot` |
| Update slot | PUT | `/fhir/Slot/{id}` |
| Delete slot | DELETE | `/fhir/Slot/{id}` |
| Find available | GET | `/fhir/Slot?status=free&schedule={schedule_id}` |
| Get by date range | GET | `/fhir/Slot?start=ge{date}&start=le{date}` |

```typescript
// Slot management for calendar view
const slotApi = {
  // Create single slot
  createSlot: (data: SlotCreate) => api.post('/fhir/Slot', {
    resourceType: 'Slot',
    schedule: { reference: `Schedule/${data.scheduleId}` },
    status: data.status || 'free',
    start: data.start,
    end: data.end,
    comment: data.comment
  }),

  // Create recurring slots
  createRecurringSlots: async (data: RecurringSlotCreate) => {
    const slots = generateRecurringSlots(data);
    return Promise.all(slots.map(slot => api.post('/fhir/Slot', slot)));
  },

  // Block time
  blockTime: (scheduleId: string, start: string, end: string, reason: string) =>
    api.post('/fhir/Slot', {
      resourceType: 'Slot',
      schedule: { reference: `Schedule/${scheduleId}` },
      status: 'busy-unavailable',
      start,
      end,
      comment: reason
    }),

  // Get calendar view
  getCalendarSlots: (scheduleIds: string[], dateRange: DateRange) =>
    api.get('/fhir/Slot', {
      params: {
        schedule: scheduleIds.join(','),
        start: `ge${dateRange.start}`,
        start: `le${dateRange.end}`,
        _count: 500
      }
    })
};
```

#### 7. Appointments (Reference)
**Backend API:** Appointments module

| UI Action | HTTP Method | Endpoint |
|-----------|-------------|----------|
| List appointments | GET | `/appointments` |
| Get appointment | GET | `/appointments/{id}` |
| Find slots | POST | `/appointments/find-slots` |
| Book slot | POST | `/appointments/select-slot` |
| Update | PATCH | `/appointments/{id}` |
| Cancel | POST | `/appointments/{id}/cancel` |

### Slot Calendar UI Component

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ SCHEDULE MANAGEMENT                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Department: [Cardiology ▼]        View: [Week ▼]     Date: ◀ Nov 25 ▶     │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │         │ Mon 25   │ Tue 26   │ Wed 27   │ Thu 28   │ Fri 29  │    │   │
│  │─────────┼──────────┼──────────┼──────────┼──────────┼─────────│    │   │
│  │         │          │          │          │          │         │    │   │
│  │ 9 AM    │ ████████ │ ████████ │          │ ████████ │         │    │   │
│  │         │ Dr.Sharma│ Dr.Sharma│          │ Dr.Sharma│         │    │   │
│  │         │ [3 booked│ [2 booked│          │ [full]   │         │    │   │
│  │─────────┼──────────┼──────────┼──────────┼──────────┼─────────│    │   │
│  │         │          │          │          │          │         │    │   │
│  │ 10 AM   │ ████████ │ ████████ │          │ ████████ │         │    │   │
│  │         │          │          │          │          │         │    │   │
│  │─────────┼──────────┼──────────┼──────────┼──────────┼─────────│    │   │
│  │         │          │          │          │          │         │    │   │
│  │ 11 AM   │ ████████ │ ████████ │ ░░░░░░░░ │ ████████ │ ████████│    │   │
│  │         │          │          │ BLOCKED  │          │         │    │   │
│  │─────────┴──────────┴──────────┴──────────┴──────────┴─────────│    │   │
│  │                                                                │    │   │
│  │  Legend: ████ Available  ░░░░ Blocked  🔴 Fully Booked        │    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  [+ Add Slot]  [📅 Set Recurring]  [🚫 Block Time]  [📤 Export Schedule]   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Natural Language Operations via AI Copilot

All entity management supports AI commands (from UX-003):

| Command Example | API Sequence |
|-----------------|--------------|
| "Add Dr. Sharma to Cardiology at Whitefield" | `POST /fhir/Practitioner` → `POST /fhir/PractitionerRole` |
| "Create 9-1 PM slot for Dr. Sharma Monday" | `POST /fhir/Slot` |
| "Block Dr. Sharma's calendar next week" | `POST /fhir/Slot` (status: busy-unavailable) |
| "Add new location at Electronic City" | `POST /fhir/Location` |
| "Set up Neurology department" | `POST /fhir/Organization` (type: dept) |

### Bulk Operations

#### Patient Import
**Backend API:** Not currently available as dedicated endpoint

**Implementation Options:**
1. **Frontend batch processing:**
```typescript
const importPatients = async (rows: PatientImportRow[]) => {
  const results = [];
  for (const row of rows) {
    try {
      const patient = await api.post('/patients', transformRow(row));
      results.push({ success: true, patient });
    } catch (error) {
      results.push({ success: false, error, row });
    }
  }
  return results;
};
```

2. **Use FHIR Bundle (transaction):**
```typescript
const importPatientsBundle = async (rows: PatientImportRow[]) => {
  const bundle = {
    resourceType: 'Bundle',
    type: 'transaction',
    entry: rows.map(row => ({
      resource: transformToFHIRPatient(row),
      request: {
        method: 'POST',
        url: 'Patient'
      }
    }))
  };

  return api.post('/fhir/', bundle);
};
```

### Gap Analysis for UX-005

| Feature | Backend Status | Gap Level | Notes |
|---------|---------------|-----------|-------|
| Organization CRUD | ✅ Complete | None | Full FHIR |
| Location CRUD | ✅ Complete | None | Full FHIR |
| Practitioner CRUD | ✅ Complete | None | Full FHIR |
| Patient CRUD | ✅ Complete | None | Full API |
| Schedule CRUD | ✅ Complete | None | Full FHIR |
| Slot CRUD | ✅ Complete | None | Full FHIR |
| FHIR Search | ✅ Complete | None | Advanced search available |
| Recurring slots | ⚠️ Partial | Minor | Frontend generates multiple slots |
| Bulk import | ⚠️ Partial | Minor | Use FHIR Bundle or frontend batch |
| Department config | ✅ Complete | None | Use Organization with type |

**Conclusion:** Backend APIs are complete for all entity management. Bulk operations and recurring slot generation are frontend logic using existing APIs.

---

## Shared API Patterns

### Error Handling
All FHIR endpoints return OperationOutcome on error:
```json
{
  "resourceType": "OperationOutcome",
  "issue": [{
    "severity": "error",
    "code": "not-found",
    "diagnostics": "Resource Patient/123 not found"
  }]
}
```

### Pagination
FHIR search results use Bundle pagination:
```json
{
  "resourceType": "Bundle",
  "type": "searchset",
  "total": 100,
  "link": [
    { "relation": "self", "url": "..." },
    { "relation": "next", "url": "...?_offset=20" }
  ],
  "entry": [...]
}
```

### Search Parameters
Common FHIR search modifiers:
- `_count`: Number of results
- `_offset`: Pagination offset
- `_sort`: Sort field (prefix `-` for descending)
- `_include`: Include referenced resources
- `_revinclude`: Include resources that reference this

---

## Next Document

Continue in `API-MAPPING-PART3-REMAINING-EPICS.md` for:
- UX-006: Analytics Intelligence Dashboard
- UX-007: Clinical Workflows Interface
- UX-008: Telehealth Experience
- UX-009: Billing & Revenue Portal
- UX-010 to UX-012: Portal & Mobile

---

**Document Owner:** Engineering Team
**Last Updated:** November 26, 2024

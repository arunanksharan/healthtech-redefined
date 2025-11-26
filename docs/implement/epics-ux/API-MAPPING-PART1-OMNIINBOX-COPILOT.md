# UI/UX Epic to Backend API Mapping - Part 1
## Omni-Inbox (UX-002) & AI Copilot (UX-003)

**Version:** 1.0
**Date:** November 26, 2024
**Purpose:** Map all UI/UX flows to existing backend APIs to ensure no significant backend development is required.

---

## Backend API Inventory Summary

The PRM backend provides the following modules with complete CRUD APIs:

### Core Modules (prm-service)

| Module | Base Route | Key Capabilities |
|--------|------------|------------------|
| **FHIR** | `/fhir` | Full FHIR R4 compliant CRUD for Patient, Practitioner, Organization, Encounter, Observation, Condition, Location, Procedure, MedicationRequest, AllergyIntolerance |
| **Patients** | `/patients` | Patient CRUD, search, statistics, duplicates detection, merge |
| **Appointments** | `/appointments` | Booking, slots, scheduling, cancellation |
| **Conversations** | `/conversations` | Multi-channel conversation threads, messages, state |
| **Communications** | `/communications` | Multi-channel messaging (WhatsApp, SMS, Email) |
| **Notifications** | `/notifications` | Templates, scheduled/bulk notifications |
| **Journeys** | `/journeys` | Patient journey definitions, instances, stages |
| **Tickets** | `/tickets` | Support ticket management |
| **Analytics** | `/analytics` | Appointments, journeys, communications, voice, dashboard analytics |
| **Reports** | `/reports` | PDF, CSV, Excel report generation |
| **Media** | `/media` | File upload/download, S3 storage |
| **Agents** | `/agents` | AI tool execution, tool registry |
| **Webhooks** | `/webhooks` | Twilio/WhatsApp/Voice agent webhooks |
| **Auth** | `/auth` | JWT authentication, login/logout/refresh |
| **Vector** | `/vector` | Embeddings and semantic search |
| **Intake** | `/intake` | Patient intake flows |

---

## EPIC UX-002: Omni-Inbox & Live Feed

### Overview
The Omni-Inbox is a unified real-time feed of all patient interactions. **All required APIs exist.**

### UI Component: Live Feed

#### Layout Description
```
┌─────────────────────────────────────────────────────────────────────┐
│ SIDEBAR (200px)  │  LIVE FEED (flex-1)      │  CONTEXT PANEL (400px)│
│                  │                          │                       │
│ [Logo]           │  [Greeting Banner]       │  [Empty State]        │
│                  │  "Good morning, Sarah!"  │                       │
│ ────────         │  "12 unread items"       │  "Select an item      │
│ 📬 Inbox         │                          │   to see details"     │
│ 👥 Patients      │  [Filter Bar]            │                       │
│ 📅 Schedule      │  [All▼] [Unread ☑]       │                       │
│ ⚙️ Settings      │                          │                       │
│                  │  ┌─────────────────────┐ │                       │
│                  │  │ Feed Card 1         │ │                       │
│                  │  │ 🎤 ZOICE - 7:45 AM  │ │                       │
│                  │  │ John Doe•Cardiology │ │                       │
│                  │  │ 😤 Frustrated       │ │                       │
│                  │  │ "can't make tomor...│ │                       │
│                  │  └─────────────────────┘ │                       │
│                  │                          │                       │
│                  │  ┌─────────────────────┐ │                       │
│                  │  │ Feed Card 2         │ │                       │
│                  │  │ 💬 WHATSAPP-7:30 AM │ │                       │
│                  │  │ Jane Smith•Insurance│ │                       │
│                  │  │ 📎 [image attached] │ │                       │
│                  │  └─────────────────────┘ │                       │
└─────────────────────────────────────────────────────────────────────┘
```

### API Mapping

#### 1. Feed Item Listing
**UI Action:** Load inbox feed items with filtering
**Backend API:** Multiple endpoints combined

| UI Requirement | Backend API | Endpoint | Notes |
|----------------|-------------|----------|-------|
| List conversations | Conversations | `GET /conversations` | Filter by status, priority |
| Get WhatsApp messages | WhatsApp Webhooks | `GET /whatsapp-webhooks/messages` | Via webhook processing |
| Get Zoice call data | Voice Webhooks | `POST /webhooks/voice-agent` | Stores in conversations |
| Get patient context | Patients | `GET /patients/{id}` | For card display |
| Get appointment context | Appointments | `GET /appointments` | Link to appointments |

**Recommended Approach:**
```typescript
// Frontend aggregation from existing APIs
const loadInboxFeed = async (filters: InboxFilters) => {
  const conversations = await api.get('/conversations', {
    params: {
      status: filters.status,
      priority: filters.priority,
      limit: 50,
      offset: 0
    }
  });

  // Enrich with patient data (can be batched)
  const enrichedItems = await Promise.all(
    conversations.map(async (conv) => ({
      ...conv,
      patient: conv.patient_id
        ? await api.get(`/patients/${conv.patient_id}`)
        : null
    }))
  );

  return enrichedItems;
};
```

#### 2. Real-Time Updates
**UI Action:** New items appear in real-time
**Backend Capability:** WebSocket/Redis Streams exist

| UI Requirement | Backend API | Notes |
|----------------|-------------|-------|
| WebSocket connection | FHIR Subscriptions | `/fhir/Subscription` - Can subscribe to resource changes |
| Event streaming | Analytics | `GET /analytics/realtime` - SSE endpoint exists |

**Implementation Note:** The backend has Redis Streams and FHIR Subscription service. Frontend should:
1. Connect to SSE endpoint for real-time metrics
2. Use FHIR Subscriptions for resource change notifications
3. Poll conversations endpoint as fallback

#### 3. Conversation Detail View (Context Panel)
**UI Action:** Click card to see full details
**Backend APIs:**

| UI Element | Backend API | Endpoint |
|------------|-------------|----------|
| Conversation messages | Conversations | `GET /conversations/{id}/messages` |
| Patient info | Patients | `GET /patients/{id}` |
| Patient appointments | Patients | `GET /patients/{id}/appointments` |
| Conversation state | Conversations | `GET /conversations/{id}/state` |
| Media attachments | Media | `GET /media?conversation_id={id}` |
| Call recording | Media | `GET /media/{id}/download` |

#### 4. Suggested Actions
**UI Action:** AI-suggested actions based on conversation
**Backend APIs:**

| Action Type | Backend API | Endpoint |
|-------------|-------------|----------|
| Reschedule appointment | Appointments | `PATCH /appointments/{id}` |
| Book new appointment | Appointments | `POST /appointments/find-slots`, `POST /appointments/select-slot` |
| Send notification | Notifications | `POST /notifications/send-template` |
| Create ticket | Tickets | `POST /tickets` |
| Execute AI tool | Agents | `POST /agents/run` |

#### 5. Filtering
**UI Action:** Filter by channel, department, status, sentiment
**Backend API:** Conversations endpoint supports filters

```typescript
// Filter parameters supported by existing API
GET /conversations?
  status=open,pending&
  priority=p0,p1&
  patient_id={uuid}&
  limit=50&
  offset=0
```

**Note:** Channel/sentiment filtering may need frontend-side filtering if not in conversation model.

#### 6. Bulk Actions
**UI Action:** Select multiple items and perform bulk action
**Implementation:** Frontend loops through selected items

```typescript
// Bulk mark as read
const bulkMarkRead = async (ids: string[]) => {
  await Promise.all(
    ids.map(id =>
      api.patch(`/conversations/${id}`, { status: 'read' })
    )
  );
};
```

### Gap Analysis for UX-002

| Feature | Backend Status | Gap Level | Notes |
|---------|---------------|-----------|-------|
| Conversation CRUD | ✅ Complete | None | Full API exists |
| Message history | ✅ Complete | None | Endpoint exists |
| Patient context | ✅ Complete | None | Full patient API |
| Real-time updates | ⚠️ Partial | Minor | SSE exists, WebSocket may need enhancement |
| Sentiment analysis | ⚠️ Partial | Minor | Store sentiment in conversation metadata |
| AI intent detection | ✅ Complete | None | Via agents module |
| WhatsApp integration | ✅ Complete | None | Webhook handlers exist |
| Voice call integration | ✅ Complete | None | Voice webhook exists |
| Attachment handling | ✅ Complete | None | Media module complete |

**Conclusion:** No significant backend development required. Minor enhancements for real-time WebSocket broadcast.

---

## EPIC UX-003: AI Copilot & Command Bar

### Overview
The AI Copilot is a global command bar for natural language operations. **All execution APIs exist. AI parsing needs frontend LLM integration.**

### UI Component: Command Bar Modal

#### Layout Description
```
┌─────────────────────────────────────────────────────────────────────┐
│                         DIMMED OVERLAY                               │
│                                                                      │
│    ┌────────────────────────────────────────────────────────────┐   │
│    │ ┌────────────────────────────────────────────────────────┐ │   │
│    │ │ 🤖 Ask anything or type a command...        [🎤] [Esc] │ │   │
│    │ └────────────────────────────────────────────────────────┘ │   │
│    │                                                            │   │
│    │ Recent Commands:                                           │   │
│    │ • Book appointment for John Doe with Dr. Sharma            │   │
│    │ • Add 2PM slot for Dr. Kohli tomorrow                      │   │
│    │ • Show today's schedule for Cardiology                     │   │
│    │                                                            │   │
│    │ Quick Actions:                                             │   │
│    │ ┌────────────┐ ┌────────────┐ ┌────────────────┐          │   │
│    │ │📅 Book Apt │ │👤 Find Pt  │ │📊 View Analytics│          │   │
│    │ └────────────┘ └────────────┘ └────────────────┘          │   │
│    │                                                            │   │
│    │ [Shortcuts: ⌘K to open • Hold Space for voice]            │   │
│    └────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### Ghost Card Display (After Parsing)
```
┌────────────────────────────────────────────────────────────────────────┐
│                        BOOKING PREVIEW                                  │
│                                                                         │
│  I understood this as:                                                  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                                                                  │  │
│  │  📅 ACTION: Book Appointment                                     │  │
│  │                                                                  │  │
│  │  👤 Patient:      ┌──────────────────────────┐ ← Editable Tag   │  │
│  │                   │ Rajesh Kumar           ✓ │                   │  │
│  │                   │ 📱 +91 9844111173        │                   │  │
│  │                   └──────────────────────────┘                   │  │
│  │                                                                  │  │
│  │  👨‍⚕️ Doctor:       ┌──────────────────────────┐                   │  │
│  │                   │ Dr. Virat Kohli        ✓ │                   │  │
│  │                   │ 🦴 Orthopedics           │                   │  │
│  │                   └──────────────────────────┘                   │  │
│  │                                                                  │  │
│  │  🏥 Location:     ┌──────────────────────────┐                   │  │
│  │                   │ Surya Whitefield       ✓ │                   │  │
│  │                   └──────────────────────────┘                   │  │
│  │                                                                  │  │
│  │  🕐 Time:         ┌──────────────────────────┐                   │  │
│  │                   │ Today, 2:00 PM         ✓ │                   │  │
│  │                   │ ⚠️ 1 slot available      │                   │  │
│  │                   └──────────────────────────┘                   │  │
│  │                                                                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  [Cancel]                                        [✓ Book Appointment]   │
└────────────────────────────────────────────────────────────────────────┘
```

### API Mapping

#### 1. AI Intent Parsing
**UI Action:** Parse natural language command
**Implementation:** Frontend LLM call + Entity resolution

| Step | Backend API | Purpose |
|------|-------------|---------|
| Parse intent | External LLM (OpenAI/Claude) | Extract intent and entities |
| Resolve patient | `GET /patients/search` | Find patient by name/phone |
| Resolve practitioner | `GET /fhir/Practitioner?name={name}` | Find doctor |
| Resolve location | `GET /fhir/Location?name={name}` | Find location |
| Check slot availability | `GET /appointments/find-slots` | Verify slot exists |

```typescript
// Entity resolution example
const resolveEntities = async (parsed: ParsedCommand) => {
  const resolved: ResolvedEntities = {};

  // Resolve patient by phone or name
  if (parsed.entities.patient_phone) {
    const patients = await api.post('/patients/search', {
      query: parsed.entities.patient_phone
    });
    resolved.patient = patients[0];
  }

  // Resolve practitioner
  if (parsed.entities.practitioner) {
    const practitioners = await api.get('/fhir/Practitioner', {
      params: { name: parsed.entities.practitioner }
    });
    resolved.practitioner = practitioners.entry?.[0]?.resource;
  }

  return resolved;
};
```

#### 2. Command Execution by Category

##### Appointment Commands
| Command | Backend API | Endpoint |
|---------|-------------|----------|
| Book appointment | Appointments | `POST /appointments/find-slots` → `POST /appointments/select-slot` |
| Reschedule | Appointments | `PATCH /appointments/{id}` |
| Cancel | Appointments | `POST /appointments/{id}/cancel` |
| View schedule | FHIR | `GET /fhir/Schedule?actor={practitioner}` |
| Block calendar | FHIR | `POST /fhir/Slot` with status=busy |

##### Patient Commands
| Command | Backend API | Endpoint |
|---------|-------------|----------|
| Find patient | Patients | `POST /patients/search` |
| Add patient | Patients | `POST /patients` |
| Update patient | Patients | `PATCH /patients/{id}` |
| View history | Patients | `GET /patients/{id}/appointments`, `GET /patients/{id}/conversations` |
| Add allergy | FHIR | `POST /fhir/AllergyIntolerance` |
| Record vitals | FHIR | `POST /fhir/Observation` |

##### Communication Commands
| Command | Backend API | Endpoint |
|---------|-------------|----------|
| Send WhatsApp | Notifications | `POST /notifications/send-template` |
| Send reminder | Notifications | `POST /notifications/send-template` |
| Broadcast message | Notifications | `POST /notifications/send-bulk` |

##### Analytics Commands
| Command | Backend API | Endpoint |
|---------|-------------|----------|
| Today's appointments | Analytics | `GET /analytics/appointments?time_period=today` |
| No-show rate | Analytics | `GET /analytics/appointments?include_breakdown=true` |
| Revenue report | Reports | `POST /reports/generate` |
| Patient volume | Analytics | `GET /analytics/dashboard` |

##### Administrative Commands
| Command | Backend API | Endpoint |
|---------|-------------|----------|
| Add slot | FHIR | `POST /fhir/Slot` |
| Doctor leave | FHIR | `POST /fhir/Schedule` with modifier |
| Add department | FHIR | `POST /fhir/Organization` |

#### 3. Voice Input
**UI Action:** Hold spacebar to speak
**Implementation:** Web Speech API (browser) + Whisper fallback

```typescript
// Voice input using Web Speech API
const recognition = new webkitSpeechRecognition();
recognition.continuous = true;
recognition.interimResults = true;
recognition.lang = 'en-US';

recognition.onresult = (event) => {
  const transcript = Array.from(event.results)
    .map(result => result[0].transcript)
    .join('');
  setInputText(transcript);
};
```

**Backend Fallback:** Use `/core/speech_to_text.py` service exists for Whisper integration.

#### 4. Tool Execution via Agents Module
**UI Action:** Execute parsed command
**Backend API:** Agents module provides tool execution

```typescript
// Use agents module for structured tool execution
const executeCommand = async (intent: string, params: any) => {
  const toolMapping = {
    'book_appointment': 'confirm_appointment',
    'send_notification': 'send_notification',
    'create_ticket': 'create_ticket',
    'update_patient': 'update_patient'
  };

  const toolName = toolMapping[intent];
  if (toolName) {
    return api.post('/agents/run', {
      name: toolName,
      args: params
    });
  }
};
```

### Gap Analysis for UX-003

| Feature | Backend Status | Gap Level | Notes |
|---------|---------------|-----------|-------|
| Patient search | ✅ Complete | None | Full search API |
| Practitioner search | ✅ Complete | None | FHIR search works |
| Appointment booking | ✅ Complete | None | Full booking flow |
| Notification sending | ✅ Complete | None | Multi-channel support |
| Analytics queries | ✅ Complete | None | Dashboard & specific analytics |
| Report generation | ✅ Complete | None | PDF/CSV/Excel |
| Tool execution | ✅ Complete | None | Agents module |
| Voice-to-text | ⚠️ Partial | Minor | Browser API primary, backend fallback exists |
| Intent parsing | ❌ Frontend | N/A | Frontend LLM integration needed |
| Entity resolution | ✅ Complete | None | Search APIs exist |

**Conclusion:** Backend APIs are complete. AI intent parsing is a frontend concern using external LLM (OpenAI/Claude API) with entity resolution against existing backend search endpoints.

---

## Shared UI Components

### AI Assistant Widget (Bottom Right)

```
┌─────────────────────────────────────────────────────────────────────┐
│                               MAIN APP CONTENT                       │
│                                                                      │
│                                                                      │
│                                                                      │
│                                                                      │
│                                                           ┌───────┐ │
│                                                           │  🤖   │ │
│                                                           │ Ask AI│ │
│                                                           └───────┘ │
└─────────────────────────────────────────────────────────────────────┘

Expanded State:
┌───────────────────────────────────────────────────────────────┐
│ ┌─────────────────────────────────────────────────────────┐   │
│ │  AI Assistant                                    [─] [✕] │   │
│ ├─────────────────────────────────────────────────────────┤   │
│ │                                                         │   │
│ │  Chat History Area (scrollable)                         │   │
│ │                                                         │   │
│ │  ┌───────────────────────────────────────────────────┐ │   │
│ │  │ 👤 You: Book appointment for patient 9844111173   │ │   │
│ │  └───────────────────────────────────────────────────┘ │   │
│ │                                                         │   │
│ │  ┌───────────────────────────────────────────────────┐ │   │
│ │  │ 🤖 AI: I found Rajesh Kumar. Here's what I       │ │   │
│ │  │     extracted:                                    │ │   │
│ │  │                                                   │ │   │
│ │  │  ┌─────────────────────────────────────────────┐ │ │   │
│ │  │  │ Patient: Rajesh Kumar                       │ │ │   │
│ │  │  │ Doctor: [Select doctor ▼]                   │ │ │   │
│ │  │  │ Time: [Select time ▼]                       │ │ │   │
│ │  │  └─────────────────────────────────────────────┘ │ │   │
│ │  │                                                   │ │   │
│ │  │  [Confirm Booking]                               │ │   │
│ │  └───────────────────────────────────────────────────┘ │   │
│ │                                                         │   │
│ ├─────────────────────────────────────────────────────────┤   │
│ │ ┌───────────────────────────────────────┐ ┌───┐ ┌───┐  │   │
│ │ │ Type your message...                  │ │ 🎤│ │ ➤│  │   │
│ │ └───────────────────────────────────────┘ └───┘ └───┘  │   │
│ └─────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

**Features:**
- Input field for text commands
- Microphone button toggles voice mode
- Send button submits to AI
- Chat history shows previous interactions
- Extracted entities displayed as editable cards on left side
- Confirmation buttons for actions

**API Integration:**
- Uses same APIs as Command Bar (UX-003)
- Conversations stored via `/conversations` endpoint
- Actions executed via `/agents/run`

---

## Next Document

Continue in `API-MAPPING-PART2-PATIENT360-ORGANIZATION.md` for:
- UX-004: Patient 360 Profile
- UX-005: Organization & Entity Management

---

**Document Owner:** Engineering Team
**Last Updated:** November 26, 2024

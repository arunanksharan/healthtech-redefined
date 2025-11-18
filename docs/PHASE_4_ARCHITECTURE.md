# Phase 4 Architecture - Final Modules

**Date:** November 18, 2024
**Status:** Planning Complete, Ready for Implementation
**Modules:** Vector, Agents, Intake

---

## Overview

Phase 4 completes the PRM backend with three final modules that enable advanced features:

1. **Vector Module** - Semantic search using pgvector and embeddings
2. **Agents Module** - AI agent tool execution and tracking
3. **Intake Module** - Comprehensive clinical intake data collection

These modules represent the final 18.75% of the PRM system, bringing total completion to 100%.

---

## Module 1: Vector Module (Semantic Search)

### Purpose
Enable semantic search across conversations, tickets, and knowledge base using vector embeddings and hybrid search (vector similarity + full-text search).

### Key Features
- **Text chunking** with configurable size and overlap
- **Vector embeddings** (384-dimensional) for semantic similarity
- **Hybrid search** combining vector distance and FTS ranking
- **Multiple source types**: transcript, ticket_note, knowledge
- **Patient consent** checking at both ingestion and retrieval
- **Incremental updates** with source-based deletion

### Database Model

**From shared.database.models:**
```python
class TextChunk(Base):
    """Indexable chunk of text with vector + FTS"""
    id: UUID
    org_id: UUID

    source_type: str  # transcript | ticket_note | knowledge
    source_id: str    # UUID or custom ID
    patient_id: UUID | None

    locator: dict | None  # {"conversation_id": "...", "message_id": "..."}
    text: str
    chunk_index: int

    # pgvector column (384 dimensions)
    embedding: list[float]  # Vector(dim=384)

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
```

**Key Design Points:**
- Uses **pgvector** extension for PostgreSQL
- 384-dimensional embeddings (compatible with many models)
- Soft delete for tracking
- Locator JSON for provenance tracking

### Schemas

**Ingest Schemas:**
```python
class IngestTranscriptsByConversation(BaseModel):
    conversation_id: UUID
    chunk_chars: int = 800  # 200-4000
    overlap: int = 120      # 0-1000

class IngestMessageTranscript(BaseModel):
    message_id: UUID
    chunk_chars: int = 800
    overlap: int = 120

class IngestTicketNotes(BaseModel):
    ticket_id: UUID
    chunk_chars: int = 800
    overlap: int = 120

class IngestKnowledge(BaseModel):
    title: str | None
    text: str
    patient_id: UUID | None
    chunk_chars: int = 1000
    overlap: int = 150
```

**Search Schema:**
```python
class SearchQuery(BaseModel):
    q: str
    top_k: int = 10  # 1-50
    patient_id: UUID | None
    source_type: str | None  # transcript | ticket_note | knowledge

class ChunkOut(BaseModel):
    id: UUID
    org_id: UUID
    source_type: str
    source_id: str
    patient_id: UUID | None
    locator: dict | None
    text: str
    chunk_index: int
    score: float  # Hybrid score
```

### Service Methods

**Chunking Algorithm:**
```python
def _chunk_text(text: str, chunk_chars: int, overlap: int) -> list[str]:
    """
    Split text into overlapping chunks

    Example:
    text = "ABCDEFGHIJ" (10 chars)
    chunk_chars = 4
    overlap = 1

    Result: ["ABCD", "DEFG", "GHIJ"]
    """
```

**Ingest Methods:**
```python
async def ingest_conversation(org_id: UUID, payload: IngestTranscriptsByConversation):
    # 1. Load conversation and check consent
    # 2. Load all transcript messages
    # 3. Chunk each transcript
    # 4. Generate embeddings for all chunks
    # 5. Delete old chunks for this conversation
    # 6. Insert new chunks
    # 7. Commit

async def ingest_message(org_id: UUID, payload: IngestMessageTranscript):
    # Similar but for single message

async def ingest_ticket(org_id: UUID, payload: IngestTicketNotes):
    # Ingest all notes for a ticket

async def ingest_knowledge(org_id: UUID, payload: IngestKnowledge):
    # Ingest free-text knowledge document
    # Generates synthetic source_id
```

**Search Method:**
```python
async def search(org_id: UUID, payload: SearchQuery):
    # 1. Generate embedding for query
    # 2. Execute hybrid search (vector + FTS)
    # 3. Check consent for each result
    # 4. Return filtered results with scores
```

### Hybrid Search Algorithm

**From repository.py:**
```python
# Vector distance (L2, smaller = closer)
dist = TextChunk.embedding.l2_distance(query_vec)

# Full-text search rank
tsvec = to_tsvector('simple', TextChunk.text)
tsq = plainto_tsquery('simple', query_text)
rank = ts_rank_cd(tsvec, tsq)

# Hybrid score
similarity = 1.0 / (1.0 + dist)
score = similarity + (rank * 0.3)

# Order by score DESC
```

**Benefits:**
- Vector search handles semantic similarity
- FTS handles exact keyword matches
- Weighted combination (70% vector, 30% FTS)

### Embeddings Integration

**Requires embeddings provider:**
```python
# From service.py
from app.platform.provider_registry import registry

self.embedder = registry.embeddings()
vectors = await self.embedder.embed([text1, text2, ...])
```

**Our Implementation:**
- Use OpenAI embeddings (text-embedding-3-small, 384 dims)
- Or use local model (sentence-transformers)
- Abstract via embeddings service

### API Endpoints

```
POST /api/v1/prm/vector/ingest/conversation  - Ingest conversation transcripts
POST /api/v1/prm/vector/ingest/message       - Ingest single message
POST /api/v1/prm/vector/ingest/ticket        - Ingest ticket notes
POST /api/v1/prm/vector/ingest/knowledge     - Ingest free-text knowledge
POST /api/v1/prm/vector/search               - Semantic search
```

### Integration Points

- **Conversations Module**: Ingest message transcripts
- **Tickets Module**: Ingest ticket notes
- **Patients Module**: Consent checking for patient data
- **Shared Database**: TextChunk model
- **Event System**: Publish ingestion events

### Security

- **Consent checking** at ingestion (skip if no consent)
- **Consent checking** at retrieval (filter results)
- **Organization isolation** in all queries
- **Soft delete** for audit trail

---

## Module 2: Agents Module (AI Agent Tools)

### Purpose
Track AI agent tool executions and provide standardized tool interfaces for appointment booking, ticket creation, etc.

### Key Features
- **Tool registry** with input schemas
- **Tool execution** with logging
- **Success/failure tracking**
- **Integration** with existing modules (tickets, appointments)

### Database Model

**From shared.database.models:**
```python
class ToolRun(Base):
    """AI agent tool execution log"""
    id: UUID
    org_id: UUID

    tool: str  # Tool name
    inputs: dict  # Input parameters
    outputs: dict | None  # Tool output
    success: bool
    error: str | None

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
```

### Tool Registry

**Available Tools:**
```python
TOOLS = [
    {
        "name": "create_ticket",
        "inputs": {
            "category": "str",
            "priority": "str",
            "summary_human": "str"
        },
        "scopes": ["tickets:write"]
    },
    {
        "name": "confirm_appointment",
        "inputs": {
            "appointment_id": "uuid",
            "start": "iso",
            "end": "iso"
        },
        "scopes": ["appointments:write"]
    }
]
```

**Expandable to:**
- create_patient
- update_patient
- send_notification
- book_appointment
- reschedule_appointment
- create_journey_instance
- etc.

### Schemas

```python
class RunTool(BaseModel):
    name: str
    args: dict

class ToolRunResponse(BaseModel):
    id: UUID
    tool: str
    inputs: dict
    outputs: dict | None
    success: bool
    error: str | None
    created_at: datetime
```

### Service Methods

```python
async def list_tools() -> list[dict]:
    """Return available tools with schemas"""
    return TOOLS

async def execute_tool(org_id: UUID, tool_name: str, args: dict) -> dict:
    """
    Execute a tool and log the run

    1. Create ToolRun record
    2. Route to appropriate service
    3. Execute tool
    4. Update ToolRun with output
    5. Return result
    """
```

### Tool Handlers

**create_ticket:**
```python
if tool_name == "create_ticket":
    ticket_service = TicketService(session)
    ticket = await ticket_service.create_ticket(org_id, args)
    return {"ticket_id": str(ticket.id)}
```

**confirm_appointment:**
```python
if tool_name == "confirm_appointment":
    appointment_service = AppointmentService(session)
    appointment = await appointment_service.confirm(
        org_id,
        args["appointment_id"],
        confirmed_start=args["start"],
        confirmed_end=args["end"]
    )
    return {"appointment_id": str(appointment.id)}
```

### API Endpoints

```
GET  /api/v1/prm/agents/tools      - List available tools
POST /api/v1/prm/agents/run        - Execute tool
GET  /api/v1/prm/agents/runs       - List tool runs (for audit)
GET  /api/v1/prm/agents/runs/{id}  - Get tool run details
```

### Integration Points

- **Tickets Module**: create_ticket, update_ticket
- **Appointments Module**: confirm_appointment, reschedule_appointment
- **Patients Module**: create_patient, update_patient
- **Notifications Module**: send_notification
- **Journeys Module**: create_journey_instance, advance_journey

### Use Cases

1. **Voice Agent**: Execute tools based on conversation
2. **Chatbot**: Book appointments, create tickets
3. **Automation**: Scheduled tasks via tools
4. **Testing**: Standardized tool execution for tests

---

## Module 3: Intake Module (Clinical Intake)

### Purpose
Comprehensive clinical intake data collection system for gathering patient history, symptoms, medications, allergies, and other clinical information before appointments.

### Key Features
- **Intake sessions** with multiple records
- **Chief complaint** capture
- **Symptom tracking** with severity, onset, duration
- **Medication history** with dosage and schedule
- **Allergy tracking** with reactions
- **Condition history** (active/resolved)
- **Family history** tracking
- **Social history** (smoking, alcohol, occupation)
- **Notes** (internal/external)
- **Summary generation**
- **Client-side idempotency** for form submissions
- **Consent checking** for patient linking

### Database Models

**From shared.database.models:**

**1. IntakeSession**
```python
class IntakeSession(Base):
    """Groups all intake data for a patient/lead"""
    id: UUID
    org_id: UUID

    patient_id: UUID | None  # Optional, can be anonymous
    conversation_id: UUID | None  # Link to WhatsApp conversation

    status: str  # open | submitted | closed
    context: dict | None  # Channel, locale, metadata

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
```

**2. IntakeSummary**
```python
class IntakeSummary(Base):
    """AI-generated summary of intake session"""
    id: UUID
    org_id: UUID
    session_id: UUID
    text: str
```

**3. IntakeChiefComplaint**
```python
class IntakeChiefComplaint(Base):
    """Primary reason for visit"""
    id: UUID
    org_id: UUID
    session_id: UUID
    text: str
    codes: dict | None  # {"set": "complaint", "code": "headache"}
```

**4. IntakeSymptom**
```python
class IntakeSymptom(Base):
    """Individual symptom with clinical details"""
    id: UUID
    org_id: UUID
    session_id: UUID
    client_item_id: str | None  # For idempotency

    code: dict | None  # {"set": "symptom", "code": "headache"}
    onset: str | None  # ISO date or "3 days ago"
    duration: str | None
    severity: str | None  # mild | moderate | severe
    frequency: str | None
    laterality: str | None  # left | right | bilateral
    notes: str | None
```

**5. IntakeAllergy**
```python
class IntakeAllergy(Base):
    """Allergy information"""
    id: UUID
    org_id: UUID
    session_id: UUID
    client_item_id: str | None

    substance: str  # e.g., "Penicillin"
    reaction: str | None  # e.g., "Rash"
    severity: str | None  # mild | moderate | severe
```

**6. IntakeMedication**
```python
class IntakeMedication(Base):
    """Current medication"""
    id: UUID
    org_id: UUID
    session_id: UUID
    client_item_id: str | None

    name: str
    dose: str | None  # e.g., "10mg"
    schedule: str | None  # e.g., "twice daily"
    adherence: str | None  # compliant | partial | non-compliant
```

**7. IntakeConditionHistory**
```python
class IntakeConditionHistory(Base):
    """Past medical history"""
    id: UUID
    org_id: UUID
    session_id: UUID
    client_item_id: str | None

    condition: str
    status: str | None  # active | resolved | unknown
    year_or_age: str | None
```

**8. IntakeFamilyHistory**
```python
class IntakeFamilyHistory(Base):
    """Family medical history"""
    id: UUID
    org_id: UUID
    session_id: UUID
    client_item_id: str | None

    relative: str  # father | mother | sibling | child
    condition: str
    age_of_onset: str | None
```

**9. IntakeSocialHistory**
```python
class IntakeSocialHistory(Base):
    """Social history data"""
    id: UUID
    org_id: UUID
    session_id: UUID

    data: dict  # {
                #   "smoking_status": "never",
                #   "alcohol_use": "occasional",
                #   "occupation": "teacher"
                # }
```

**10. IntakeNote**
```python
class IntakeNote(Base):
    """Free-text notes"""
    id: UUID
    org_id: UUID
    session_id: UUID

    text: str
    visibility: str  # internal | external
```

### Schemas

**Session Management:**
```python
class IntakeSessionCreate(BaseModel):
    patient_id: UUID | None
    conversation_id: UUID | None
    context: dict | None

class IntakeSessionOut(BaseModel):
    id: UUID
    org_id: UUID
    status: str
    patient_id: UUID | None
    conversation_id: UUID | None
    context: dict | None
```

**Clinical Records:**
```python
class ChiefComplaint(BaseModel):
    text: str
    codes: dict | None

class SymptomItem(BaseModel):
    client_item_id: str | None
    code: dict | None
    onset: str | None
    duration: str | None
    severity: str | None  # mild | moderate | severe
    frequency: str | None
    laterality: str | None
    notes: str | None

class AllergyItem(BaseModel):
    client_item_id: str | None
    substance: str
    reaction: str | None
    severity: str | None

class MedicationItem(BaseModel):
    client_item_id: str | None
    name: str
    dose: str | None
    schedule: str | None
    adherence: str | None

class ConditionHistoryItem(BaseModel):
    client_item_id: str | None
    condition: str
    status: str | None
    year_or_age: str | None

class FamilyHistoryItem(BaseModel):
    client_item_id: str | None
    relative: str
    condition: str
    age_of_onset: str | None

class SocialHistory(BaseModel):
    smoking_status: str | None
    alcohol_use: str | None
    occupation: str | None
    other: dict | None
```

**Upsert Schema:**
```python
class IntakeRecordsUpsert(BaseModel):
    """Upsert multiple record types at once"""
    chief_complaint: ChiefComplaint | None
    symptoms: list[SymptomItem] | None
    allergies: list[AllergyItem] | None
    medications: list[MedicationItem] | None
    condition_history: list[ConditionHistoryItem] | None
    family_history: list[FamilyHistoryItem] | None
    social_history: SocialHistory | None
    notes: list[NoteItem] | None
```

### Service Methods

**Session Management:**
```python
async def create_session(org_id, patient_id, conversation_id, context):
    # Check consent if patient_id provided
    # Create session
    # Publish event

async def set_session_patient(org_id, session_id, patient_id):
    # Require consent to link patient
    # Update session
    # Publish event

async def submit(org_id, session_id):
    # Mark session as submitted
    # Publish event for downstream processing
```

**Records Management:**
```python
async def upsert_records(org_id, session_id, payload: IntakeRecordsUpsert):
    # For each record type:
    # 1. Check if client_item_id exists
    # 2. Update if exists, insert if new
    # 3. Use upsert_list_by_client_id for idempotency

    # Handles:
    # - chief_complaint (single)
    # - symptoms (list with client_item_id)
    # - allergies (list with client_item_id)
    # - medications (list with client_item_id)
    # - condition_history (list with client_item_id)
    # - family_history (list with client_item_id)
    # - social_history (single, merged dict)
    # - notes (list, append-only)
```

**Client-Side Idempotency:**
```python
# Frontend sends:
{
  "symptoms": [
    {"client_item_id": "symptom-1", "notes": "Headache"},
    {"client_item_id": "symptom-2", "notes": "Fever"}
  ]
}

# If submitted again, updates existing records instead of duplicating
```

### API Endpoints

```
POST   /api/v1/prm/intake/sessions                    - Create session
GET    /api/v1/prm/intake/sessions                    - List sessions
GET    /api/v1/prm/intake/sessions/{id}               - Get session
PUT    /api/v1/prm/intake/sessions/{id}/patient/{pid} - Link patient
PUT    /api/v1/prm/intake/sessions/{id}/records       - Upsert records
PUT    /api/v1/prm/intake/sessions/{id}/summary       - Set AI summary
POST   /api/v1/prm/intake/sessions/{id}/submit        - Submit session
GET    /api/v1/prm/intake/sessions/{id}/export        - Export for EHR
```

### Integration Points

- **Patients Module**: Link intake to patient
- **Conversations Module**: Link intake to WhatsApp conversation
- **Appointments Module**: Pre-fill intake before booking
- **Journeys Module**: Trigger intake in journey stages
- **Vector Module**: Semantic search across intake data
- **Event System**: Publish intake events

### Workflow Examples

**1. WhatsApp Intake Flow:**
```
1. Patient starts WhatsApp conversation
2. Create IntakeSession with conversation_id
3. AI agent asks questions
4. Agent calls upsert_records as data is collected
5. Generate AI summary
6. Submit session
7. Link to patient (with consent)
8. Create appointment with pre-filled data
```

**2. Web Form Intake:**
```
1. User fills out multi-step form
2. Create IntakeSession (anonymous)
3. Form POSTs to upsert_records after each step
4. Use client_item_id for idempotency (user can go back)
5. Submit session when complete
6. Create patient from intake data
7. Book appointment
```

### Data Export

**EHR Integration:**
```python
async def export_intake_for_ehr(session_id):
    # Gather all records for session
    # Format as FHIR Bundle or custom format
    # Return structured data for EHR import

    return {
        "patient": {...},
        "chief_complaint": "...",
        "symptoms": [...],
        "allergies": [...],
        "medications": [...],
        "conditions": [...],
        "family_history": [...],
        "social_history": {...}
    }
```

### Security

- **Consent required** to link patient_id
- **Anonymous sessions** supported (no patient_id)
- **Organization isolation** in all queries
- **Soft delete** for audit trail
- **Internal vs external notes** for visibility control

---

## Cross-Module Integration

### Database Dependencies

**New Models Required:**
```python
# In shared/database/models.py (if not exists)
- TextChunk (pgvector)
- ToolRun
- IntakeSession
- IntakeSummary
- IntakeChiefComplaint
- IntakeSymptom
- IntakeAllergy
- IntakeMedication
- IntakeConditionHistory
- IntakeFamilyHistory
- IntakeSocialHistory
- IntakeNote
```

**pgvector Extension:**
```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- TextChunk table
CREATE TABLE text_chunk (
    id UUID PRIMARY KEY,
    org_id UUID NOT NULL,
    source_type VARCHAR(32) NOT NULL,
    source_id VARCHAR(64) NOT NULL,
    patient_id UUID REFERENCES patient(id),
    locator JSONB,
    text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    embedding vector(384) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP
);

-- Indexes
CREATE INDEX idx_text_chunk_org ON text_chunk(org_id);
CREATE INDEX idx_text_chunk_source ON text_chunk(source_type, source_id);
CREATE INDEX idx_text_chunk_patient ON text_chunk(patient_id);
CREATE INDEX idx_text_chunk_embedding ON text_chunk USING ivfflat (embedding vector_l2_ops);
```

### Event Publishing

**Vector Module:**
- `VECTOR_INGESTED` - Text ingested and indexed
- `VECTOR_SEARCH_PERFORMED` - Search executed

**Agents Module:**
- `TOOL_EXECUTED` - Tool run completed
- `TOOL_FAILED` - Tool execution failed

**Intake Module:**
- `INTAKE_SESSION_CREATED` - New intake session
- `INTAKE_SESSION_PATIENT_SET` - Patient linked
- `INTAKE_RECORD_UPSERTED` - Records updated
- `INTAKE_SUMMARY_SET` - AI summary generated
- `INTAKE_SUBMITTED` - Session submitted

### Shared Services

**Embeddings Service (New):**
```python
# core/embeddings.py
class EmbeddingsService:
    """Generate text embeddings for vector search"""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for texts

        Implementation options:
        1. OpenAI API (text-embedding-3-small, 384 dims)
        2. Local model (sentence-transformers)
        3. Other providers (Cohere, etc.)
        """
        # Use OpenAI for now
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
            dimensions=384
        )

        return [item.embedding for item in response.data]
```

---

## Technical Decisions

### 1. Vector Dimensions (384)
**Why:** Balance between quality and performance
- Smaller than 1536 (OpenAI default) → faster queries
- Larger than 128 → better semantic understanding
- Compatible with many embedding models

### 2. Hybrid Search (Vector + FTS)
**Why:** Best of both worlds
- Vector: semantic similarity
- FTS: exact keyword matching
- Weighted combination (70/30)

### 3. Client-Side Idempotency (Intake)
**Why:** Better UX for multi-step forms
- Users can go back and edit
- No duplicate records on re-submission
- Frontend controls unique IDs

### 4. Consent Checking at Multiple Layers
**Why:** HIPAA compliance
- Check at ingestion (vector)
- Check at retrieval (vector search)
- Check at patient linking (intake)

### 5. Tool Execution Logging
**Why:** Audit trail and debugging
- Track all AI agent actions
- Identify failed tool calls
- Replay capability for testing

---

## Implementation Checklist

### Vector Module
- [ ] Create `modules/vector/__init__.py`
- [ ] Create `modules/vector/schemas.py`
- [ ] Create `modules/vector/repository.py`
- [ ] Create `modules/vector/service.py`
- [ ] Create `modules/vector/router.py`
- [ ] Create `core/embeddings.py`
- [ ] Ensure TextChunk model exists in shared database
- [ ] Add pgvector to requirements

### Agents Module
- [ ] Create `modules/agents/__init__.py`
- [ ] Create `modules/agents/schemas.py`
- [ ] Create `modules/agents/service.py`
- [ ] Create `modules/agents/router.py`
- [ ] Ensure ToolRun model exists in shared database
- [ ] Expand tool registry

### Intake Module
- [ ] Create `modules/intake/__init__.py`
- [ ] Create `modules/intake/schemas.py`
- [ ] Create `modules/intake/repository.py`
- [ ] Create `modules/intake/service.py`
- [ ] Create `modules/intake/router.py`
- [ ] Ensure all intake models exist in shared database
- [ ] Test client-side idempotency

### Integration
- [ ] Update `api/router.py` to include all 3 modules
- [ ] Add embeddings configuration to `core/config.py`
- [ ] Test cross-module integration
- [ ] Update documentation

---

## Testing Strategy

### Vector Module
- Test text chunking with various sizes/overlaps
- Test embedding generation
- Test hybrid search accuracy
- Test consent filtering
- Load test with 10k+ chunks

### Agents Module
- Test each tool execution
- Test error handling and logging
- Test with malformed inputs
- Integration test with real services

### Intake Module
- Test full intake workflow
- Test client-side idempotency
- Test partial submissions
- Test data export for EHR
- Test consent checking

---

## Next Steps

1. Implement Vector Module (highest complexity)
2. Implement Intake Module (most models)
3. Implement Agents Module (simplest)
4. Integrate all modules
5. Comprehensive testing
6. Documentation updates
7. Final deployment prep

---

**Status:** Ready for Implementation
**Priority:** HIGH - Final 3 modules to complete PRM
**Estimated Complexity:**
- Vector: High (pgvector, embeddings, hybrid search)
- Intake: Medium (many models, complex workflows)
- Agents: Low (simple tool execution)

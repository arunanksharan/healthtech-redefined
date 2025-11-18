# Phase 2: WhatsApp Appointment Booking - Architecture & Design

**Date:** November 18, 2024
**Status:** Planning → Implementation

---

## 🎯 Objective

Build a complete, refactored WhatsApp appointment booking flow with:
- **Webhooks Module**: Receive messages from Twilio & voice agent transcripts
- **Conversations Module**: Manage conversation state and threading
- **Appointments Module**: AI-driven slot selection and booking
- **n8n Integration Module**: Workflow automation for confirmations

---

## 🏗️ System Architecture

### Data Flow Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    WhatsApp Appointment Booking Flow             │
└─────────────────────────────────────────────────────────────────┘

1. MESSAGE INGRESS
   ┌──────────────┐
   │   Twilio     │ ─── WhatsApp Message ───┐
   │   Webhook    │                          │
   └──────────────┘                          ▼
                                    ┌─────────────────┐
   ┌──────────────┐                 │   Webhooks      │
   │ Voice Agent  │ ─── Transcript ─▶│   Module        │
   │   (zoice)    │                 └─────────────────┘
   └──────────────┘                          │
                                             │ Parse & Validate
                                             ▼
2. CONVERSATION MANAGEMENT           ┌─────────────────┐
                                     │ Conversations   │
                                     │    Module       │
                                     └─────────────────┘
                                             │
                                ┌────────────┼────────────┐
                                │            │            │
                         Create/Update    Store      Check State
                         Conversation    Message    (Redis)
                                │            │            │
                                └────────────┼────────────┘
                                             ▼
3. INTENT DETECTION & PROCESSING    ┌─────────────────┐
                                    │  State Manager  │
                                    │   (Core)        │
                                    └─────────────────┘
                                             │
                        ┌────────────────────┼────────────────────┐
                        │                    │                    │
                   Booking Intent?      Info Request?      Other?
                        │                    │                    │
                        ▼                    ▼                    ▼
4. APPOINTMENT BOOKING          ┌─────────────────┐
   (If booking intent)          │  Appointments   │
                                │     Module      │
                                └─────────────────┘
                                        │
                        ┌───────────────┼───────────────┐
                        │               │               │
                  Extract Info    Check Slots    Create Booking
                  (Patient,       (Availability) (Confirmed)
                   Doctor, Time)        │               │
                        │               │               │
                        └───────────────┼───────────────┘
                                        ▼
5. WORKFLOW AUTOMATION          ┌─────────────────┐
                                │  n8n Integration│
                                │     Module      │
                                └─────────────────┘
                                        │
                        ┌───────────────┼───────────────┐
                        │               │               │
                  Trigger n8n      Process Response  Confirm/Reject
                  Workflow         (Slot selection)   Booking
                        │               │               │
                        └───────────────┼───────────────┘
                                        ▼
6. JOURNEY ORCHESTRATION        ┌─────────────────┐
                                │    Journeys     │
                                │     Module      │
                                └─────────────────┘
                                        │
                                Create Journey Instance
                                Track Stages
                                Send Reminders
                                        │
                                        ▼
7. COMMUNICATION                ┌─────────────────┐
                                │ Communications  │
                                │     Module      │
                                └─────────────────┘
                                        │
                                Send Confirmation
                                (via Twilio)
```

---

## 📦 Module Details

### Module 1: Webhooks

**Purpose:** Entry point for all external messages

**Endpoints:**
- `POST /api/v1/prm/webhooks/twilio` - Twilio WhatsApp webhook
- `POST /api/v1/prm/webhooks/voice-agent` - Voice agent transcript webhook
- `GET /api/v1/prm/webhooks/twilio/status` - Webhook health check

**Key Improvements over Original:**
- ✅ **Unified webhook handler** - Single entry point with routing
- ✅ **Proper validation** - Pydantic schemas for all webhook payloads
- ✅ **Security** - Twilio signature verification
- ✅ **Error handling** - Graceful degradation, no webhook failures
- ✅ **Async processing** - Non-blocking message handling
- ✅ **Logging & monitoring** - Track all webhook events

**Data Models:**
```python
class TwilioWebhookPayload:
    From: str  # Phone number
    To: str    # Twilio number
    Body: str  # Message text
    NumMedia: int  # Number of media attachments
    MediaUrl0: Optional[str]  # Media URL if present
    MessageSid: str  # Unique message ID

class VoiceAgentWebhookPayload:
    call_id: UUID
    patient_phone: str
    recording_url: str
    transcript: str
    extracted_data: dict  # Intent, entities
    duration_seconds: int
    confidence_score: float
```

**Service Layer:**
```python
class WebhookService:
    async def process_twilio_message(payload)
        → Create/update conversation
        → Store message
        → Route to appropriate handler

    async def process_voice_transcript(payload)
        → Extract structured data
        → Create conversation
        → Trigger booking if intent detected

    async def validate_twilio_signature(request)
        → Security verification
```

---

### Module 2: Conversations

**Purpose:** Manage conversation lifecycle and state

**Endpoints:**
- `POST /api/v1/prm/conversations` - Create conversation
- `GET /api/v1/prm/conversations/{id}` - Get conversation with messages
- `GET /api/v1/prm/conversations` - List conversations (by patient/phone)
- `POST /api/v1/prm/conversations/{id}/messages` - Add message
- `GET /api/v1/prm/conversations/{id}/state` - Get conversation state
- `PATCH /api/v1/prm/conversations/{id}/state` - Update state

**Key Improvements:**
- ✅ **State machine pattern** - Clear conversation states
- ✅ **Redis integration** - Fast state access
- ✅ **Message threading** - Proper conversation continuity
- ✅ **Context awareness** - Track extracted data per conversation
- ✅ **Expiry management** - Auto-cleanup old conversations
- ✅ **Multi-turn support** - Handle complex interactions

**Data Models:**
```python
class ConversationState(Enum):
    INITIATED = "initiated"
    GATHERING_INFO = "gathering_info"
    SLOT_SELECTION = "slot_selection"
    CONFIRMING = "confirming"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class Conversation:
    id: UUID
    patient_id: Optional[UUID]  # Linked after identification
    phone_number: str
    channel: str  # whatsapp, voice
    state: ConversationState
    context: dict  # Extracted data
    started_at: datetime
    last_message_at: datetime
    messages: List[Message]

class Message:
    id: UUID
    conversation_id: UUID
    direction: str  # inbound, outbound
    content: str
    media_urls: List[str]
    sent_at: datetime
    delivered_at: Optional[datetime]
```

**Service Layer:**
```python
class ConversationService:
    async def create_conversation(phone, channel)
        → Check for existing active conversation
        → Create new or resume
        → Initialize Redis state

    async def add_message(conversation_id, message)
        → Store in database
        → Update last_message_at
        → Trigger intent detection

    async def get_state(conversation_id)
        → Fetch from Redis (fast)
        → Fallback to database

    async def update_state(conversation_id, new_state, context)
        → Validate state transition
        → Update Redis
        → Persist to database

    async def extract_booking_intent(messages)
        → LLM-based intent detection
        → Extract: patient info, doctor, time, reason
```

---

### Module 3: Appointments

**Purpose:** AI-driven appointment booking and management

**Endpoints:**
- `POST /api/v1/prm/appointments` - Create appointment
- `GET /api/v1/prm/appointments` - List appointments
- `GET /api/v1/prm/appointments/{id}` - Get appointment
- `PATCH /api/v1/prm/appointments/{id}` - Update appointment
- `GET /api/v1/prm/appointments/slots/available` - Check availability
- `POST /api/v1/prm/appointments/booking/from-intent` - Book from natural language

**Key Improvements:**
- ✅ **AI slot selection** - Natural language → structured booking
- ✅ **Availability engine** - Real-time slot checking
- ✅ **Conflict detection** - Prevent double bookings
- ✅ **Smart matching** - Fuzzy doctor name matching
- ✅ **Multi-criteria** - Time preferences, doctor speciality
- ✅ **Fallback options** - Suggest alternatives if unavailable

**Data Models:**
```python
class BookingIntent:
    patient_phone: str
    patient_name: Optional[str]
    practitioner_name: str
    speciality: Optional[str]
    preferred_date: Optional[date]
    preferred_time: Optional[str]  # "morning", "10AM", etc.
    reason: Optional[str]

class SlotAvailability:
    practitioner_id: UUID
    location_id: UUID
    start_datetime: datetime
    end_datetime: datetime
    is_available: bool
    capacity: int
    booked_count: int

class AppointmentBooking:
    id: UUID
    patient_id: UUID
    practitioner_id: UUID
    time_slot_id: UUID
    status: str  # booked, checked_in, completed, cancelled
    source_channel: str  # whatsapp, voice, web
    conversation_id: Optional[UUID]
    journey_instance_id: Optional[UUID]
    confirmed_start: datetime
    confirmed_end: datetime
```

**Service Layer:**
```python
class AppointmentService:
    async def find_available_slots(criteria)
        → Query time_slots table
        → Apply filters (date, practitioner, speciality)
        → Return available slots

    async def book_from_intent(intent, conversation_id)
        → Parse natural language preferences
        → Match practitioner (fuzzy)
        → Find available slots
        → Rank by preference
        → Create booking
        → Link to journey
        → Send confirmation

    async def suggest_alternatives(original_criteria)
        → Find nearby times
        → Find same speciality different doctors
        → Find same doctor different days

    async def cancel_appointment(appointment_id, reason)
        → Update status
        → Free up slot
        → Notify patient
        → Update journey
```

**AI Slot Selection Logic:**
```python
class SlotSelector:
    async def select_best_slot(intent, available_slots)
        → Score each slot based on:
            - Time preference match (morning/afternoon/evening)
            - Date proximity to requested
            - Doctor preference match
            - Location convenience
        → Return ranked list

    async def parse_time_preference(text)
        → "tomorrow 10AM" → datetime
        → "next Monday morning" → datetime range
        → "as soon as possible" → earliest
```

---

### Module 4: n8n Integration

**Purpose:** Workflow automation for booking confirmations

**Endpoints:**
- `POST /api/v1/prm/n8n/trigger/slot-selection` - Trigger slot selection workflow
- `POST /api/v1/prm/n8n/webhook/booking-response` - Receive n8n response
- `GET /api/v1/prm/n8n/workflows` - List available workflows

**Key Improvements:**
- ✅ **Workflow abstraction** - Hide n8n complexity
- ✅ **Retry logic** - Handle n8n failures gracefully
- ✅ **Async processing** - Don't block on workflow execution
- ✅ **Result tracking** - Monitor workflow execution
- ✅ **Fallback to direct** - Can work without n8n

**Data Models:**
```python
class WorkflowTrigger:
    workflow_name: str
    conversation_id: UUID
    payload: dict
    triggered_at: datetime

class WorkflowResponse:
    conversation_id: UUID
    action: str  # confirm_slot, reject_slots, request_clarification
    data: dict
    reply_to_user: Optional[str]
```

**Service Layer:**
```python
class N8nService:
    async def trigger_workflow(name, payload)
        → Call n8n webhook
        → Track trigger in database
        → Return tracking ID

    async def process_booking_response(response)
        → Parse n8n response
        → Update conversation state
        → If confirm: create appointment
        → If reject: find new slots
        → If clarify: send message
        → Send reply via Twilio

    async def handle_slot_confirmation(conversation_id, selected_slot)
        → Create appointment booking
        → Update conversation state to COMPLETED
        → Create journey instance
        → Send WhatsApp confirmation
        → Publish events
```

---

## 🔄 Interaction Flows

### Flow 1: Simple Booking (Happy Path)

```
User: "I want to book an appointment with Dr. Rajiv for cardiology tomorrow at 10AM"
                                    ↓
            [Twilio Webhook] → [Webhooks Module]
                                    ↓
            [Create/Update Conversation] → [Conversations Module]
                                    ↓
            [Extract Intent & Entities]
                - Patient: From phone number
                - Doctor: "Dr. Rajiv"
                - Speciality: "cardiology"
                - Date: Tomorrow
                - Time: "10AM"
                                    ↓
            [Find Available Slots] → [Appointments Module]
                - Query time_slots for Dr. Rajiv (cardiology)
                - Filter by tomorrow
                - Check 10AM availability
                                    ↓
            [Book Appointment]
                - Create appointment record
                - Link to patient
                - Update slot capacity
                                    ↓
            [Create Journey Instance] → [Journeys Module]
                - Start "OPD Visit Journey"
                - Stage 1: Pre-visit
                                    ↓
            [Send Confirmation] → [Communications Module]
                - WhatsApp message via Twilio
                - "Confirmed: Dr. Rajiv, Cardiology, Nov 19 10:00AM"
```

### Flow 2: Complex Booking (Multiple Interactions)

```
User: "I need to see a heart doctor"
                                    ↓
Bot: "I can help you book a cardiology appointment. What's your preferred date?"
                                    ↓
User: "Tomorrow morning"
                                    ↓
Bot: "Available cardiologists tomorrow morning:
     1. Dr. Rajiv Sharma - 9:00 AM, 10:30 AM
     2. Dr. Priya Gupta - 9:30 AM, 11:00 AM
     Which doctor and time works for you?"
                                    ↓
User: "Dr. Rajiv at 10:30"
                                    ↓
[n8n Workflow Triggered] → [N8n Integration Module]
    - Parse selection
    - Confirm slot availability
    - Send confirmation request
                                    ↓
[n8n Response: Confirm]
                                    ↓
[Create Appointment] → [Appointments Module]
                                    ↓
[Send Confirmation] → [Communications Module]
```

### Flow 3: Voice Agent Integration

```
[Patient Calls] → [Voice Agent (zoice)]
                        ↓
[Call Transcript Generated]
    - Duration: 2 minutes
    - Transcript: "I want to book appointment with Dr. Sharma for tomorrow"
    - Extracted: {doctor: "Dr. Sharma", date: "tomorrow", intent: "booking"}
                        ↓
[Voice Agent Webhook] → [Webhooks Module]
                        ↓
[Create Conversation] → [Conversations Module]
    - Channel: "voice"
    - Context: Extracted data from call
                        ↓
[Process Booking Intent] → [Appointments Module]
    - Find Dr. Sharma
    - Check tomorrow's slots
    - Book appointment
                        ↓
[Send SMS Confirmation] → [Communications Module]
    - SMS (since original channel was voice, not WhatsApp)
    - "Your appointment is confirmed..."
```

---

## 🔐 Security & Validation

### Twilio Webhook Validation
```python
def validate_twilio_signature(request):
    signature = request.headers.get('X-Twilio-Signature')
    url = str(request.url)
    params = request.form

    validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
    return validator.validate(url, params, signature)
```

### Rate Limiting
- Webhook endpoints: 100 requests/minute per phone number
- Booking endpoints: 10 bookings/hour per patient

### Data Validation
- All phone numbers normalized to E.164 format
- Date/time parsing with timezone awareness
- Doctor name fuzzy matching with confidence threshold
- Appointment conflicts checked at booking time

---

## 🎯 Success Criteria

### Functional
- ✅ Receive WhatsApp messages via Twilio
- ✅ Process voice agent transcripts
- ✅ Maintain conversation state across multiple messages
- ✅ Extract booking intent from natural language
- ✅ Find available appointment slots
- ✅ Create confirmed bookings
- ✅ Send confirmations via WhatsApp/SMS
- ✅ Link bookings to journey orchestration

### Non-Functional
- ✅ Webhook response time < 200ms (Twilio requirement)
- ✅ Booking creation < 1 second
- ✅ 99.9% webhook reliability
- ✅ Handle 1000 concurrent conversations
- ✅ Conversation state persists for 24 hours

---

## 📊 Testing Strategy

### Unit Tests
- Each service method tested independently
- Mock external dependencies (Twilio, n8n, Redis)
- Test all edge cases (no slots, invalid input, etc.)

### Integration Tests
- Full flow: Webhook → Conversation → Booking → Confirmation
- Test with real Twilio test credentials
- Test Redis state persistence

### End-to-End Tests
- Simulate real WhatsApp conversation
- Send test message via Twilio
- Verify booking created
- Verify confirmation sent

---

## 🚀 Implementation Order

### Phase 2.1: Webhooks (Priority: CRITICAL)
1. Create schemas for Twilio & voice agent payloads
2. Implement webhook router with validation
3. Build webhook service with message routing
4. Test with Twilio webhook simulator

### Phase 2.2: Conversations (Priority: CRITICAL)
1. Create conversation & message schemas
2. Implement conversation router
3. Build conversation service with Redis integration
4. Implement state machine
5. Add intent extraction logic

### Phase 2.3: Appointments (Priority: HIGH)
1. Create appointment schemas
2. Implement appointments router
3. Build appointment service
4. Implement AI slot selection logic
5. Add booking creation & validation
6. Link to journey orchestration

### Phase 2.4: n8n Integration (Priority: HIGH)
1. Create n8n workflow schemas
2. Implement n8n webhook router
3. Build n8n service
4. Implement workflow triggers
5. Handle booking responses
6. Add fallback logic

### Phase 2.5: Integration & Testing (Priority: HIGH)
1. Register all modules in main router
2. End-to-end testing
3. Performance testing
4. Documentation

---

**Status:** Planning Complete → Ready for Implementation
**Estimated Effort:** ~30-40 files to create
**Timeline:** Comprehensive but achievable

**Next:** Start with Webhooks Module

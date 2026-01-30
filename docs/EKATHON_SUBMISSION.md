# PRM: AI-Native Patient Relationship Management

**Ekathon Health AI 2026 Submission**
**Track 1: Build Health AI using Digital India Rails**
**Team: Kuzushi Labs**

---

## Executive Summary

PRM (Patient Relationship Management) is an **AI-native healthcare platform** that transforms patient engagement through conversational AI interfaces. Unlike traditional healthcare software with forms and menus, PRM enables natural interactions via **voice calls, WhatsApp, and an intelligent conversation widget** that automatically extracts medical data and autofills clinical forms.

**The Core Innovation**: A unified platform where patients can speak naturally—via phone call or chat—and the system automatically:
1. Understands their intent (appointment booking, symptoms, queries)
2. Extracts structured medical data from unstructured conversation
3. Autofills clinical forms with confidence scoring
4. Triggers appropriate workflows (scheduling, triage, notifications)

**Production Status**: 85% complete with 49+ backend microservices, 5 AI agents, FHIR R4 compliance, live Zoice voice integration, and Twilio WhatsApp integration.

---

## Table of Contents

1. [The Problem](#the-problem)
2. [Our Solution](#our-solution)
3. [The AI Conversation Widget](#the-ai-conversation-widget)
4. [Voice AI Integration (Zoice)](#voice-ai-integration-zoice)
5. [WhatsApp Integration (Twilio)](#whatsapp-integration-twilio)
6. [The PRM Dashboard](#the-prm-dashboard)
7. [End-to-End Patient Flows](#end-to-end-patient-flows)
8. [Technical Architecture](#technical-architecture)
9. [FHIR & ABDM Compliance](#fhir--abdm-compliance)
10. [Security & Compliance](#security--compliance)
11. [Implementation Status](#implementation-status)
12. [Demo Script](#demo-script)

---

## The Problem

### India's Healthcare Documentation Crisis

| Challenge | Impact |
|-----------|--------|
| **Manual Form Entry** | Staff spend 30-40% of time on data entry |
| **Phone Call Inefficiency** | 3-5 minutes per call, 20+ minute hold queues |
| **Fragmented Data** | Patient info scattered across paper, WhatsApp, calls |
| **No Structured Extraction** | Valuable clinical data lost in conversations |
| **Language Barriers** | Forms in English, patients speak regional languages |

### The Real Cost

- **Patients**: Wait on hold, repeat information, miss follow-ups
- **Staff**: Drown in paperwork, manual transcription, context switching
- **Clinicians**: Incomplete data, delayed decisions, documentation burden
- **Healthcare System**: Inefficiency, errors, inability to scale

---

## Our Solution

### Three AI-Powered Touchpoints, One Unified Platform

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PATIENT INTERACTION LAYER                            │
├─────────────────────────┬─────────────────────────┬─────────────────────────┤
│      VOICE CALLS        │       WHATSAPP          │   CONVERSATION WIDGET   │
│       (Zoice)           │       (Twilio)          │    (Web/Embedded)       │
├─────────────────────────┼─────────────────────────┼─────────────────────────┤
│ • Inbound/Outbound      │ • 2-way messaging       │ • Text + Voice chat     │
│ • Real-time AI          │ • Rich media support    │ • Form autofill         │
│ • Multi-language        │ • Template messages     │ • Confidence scoring    │
│ • Call transcription    │ • Interactive buttons   │ • Real-time extraction  │
│ • Intent detection      │ • Delivery tracking     │ • Streaming responses   │
└─────────────────────────┴─────────────────────────┴─────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PRM INTELLIGENCE ENGINE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  • Intent Classification    • Entity Extraction    • Confidence Scoring     │
│  • Medical NLP              • Form Schema Mapping  • Workflow Triggers      │
│  • Multi-Agent Orchestration (5 Agents, 30+ Tools)                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRM DATA LAYER                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  • FHIR R4 Resources   • Patient 360° View   • Conversation Threading      │
│  • Journey Instances   • Appointments        • Clinical Observations       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## The AI Conversation Widget

### What It Does

The conversation widget is an **embeddable AI assistant** that enables natural text and voice conversations while automatically extracting structured medical data and autofilling clinical forms.

### Key Capabilities

#### 1. Natural Conversation with Streaming Responses
```
Patient: "I've been having chest pain for the last 3 days,
         it gets worse when I climb stairs"

AI Assistant: "I understand you're experiencing chest pain.
              Let me ask a few questions to better understand...

              On a scale of 1-10, how would you rate the pain?"

[Extracted Fields Appear in Real-Time]:
┌─────────────────────────────────────────────┐
│ Chief Complaint: Chest pain        [98%] ✓  │
│ Duration: 3 days                   [95%] ✓  │
│ Aggravating Factor: Exertion       [90%] ✓  │
│ Pain Location: Chest               [98%] ✓  │
└─────────────────────────────────────────────┘
```

#### 2. Form Autofill with Confidence Scoring

The widget converts form schemas to OpenAI function tools and extracts fields with confidence scores:

| Confidence Level | Score | UI Indicator | Meaning |
|------------------|-------|--------------|---------|
| High | ≥80% | Green | Explicitly stated by patient |
| Medium | 50-79% | Yellow | Strongly implied from context |
| Low | <50% | Red | Inferred, needs verification |

**Supported Field Types**:
- String (free text, names, descriptions)
- Number (age, measurements, scores)
- Boolean (yes/no questions)
- Enum (dropdowns, categorical values)
- Array (multiple selections)
- Object (nested structures)

#### 3. Voice Input Support

- **WebRTC-based audio** for real-time voice conversations
- **Bidirectional audio streams**: Microphone input + AI voice output
- **Voice Activity Detection (VAD)**: Silero-based detection
- **Multiple STT providers**: Deepgram, Google, Gladia, Groq
- **Multiple TTS providers**: ElevenLabs, Google, Sarvam (Indian languages), Cartesia

#### 4. Medical Terminology Support

The extraction system maintains alternate medical terms for better understanding:

```javascript
// Example: Field "chest_pain" also matches
alternateTerms: ["chest discomfort", "heart pain", "angina",
                 "seene mein dard", "chhati mein dard"]
```

### Widget Integration Flow

```
1. Embed Widget
   <kuzushi-widget project-id="abc123" />
                    │
                    ▼
2. Session Initialization
   POST /v1/widget/session/init
   → Returns: JWT token, WebSocket URL, feature flags
                    │
                    ▼
3. WebSocket Connection
   /ws/chat (text) + /ws/voice (audio signaling)
                    │
                    ▼
4. Conversation Loop
   User Message → LLM Response (streaming) → Extraction (async)
                    │
                    ▼
5. Real-Time Extraction Updates
   WebSocket: extraction_update event
   → UI shows fields with confidence badges
```

### Technical Implementation

**Frontend (React 18 + TypeScript)**:
- `ChatLayout.tsx` - Main conversation interface
- `ExtractionPanel.tsx` - Extracted fields display with confidence
- `VoiceControls.tsx` - Voice input controls
- `useChatWebSocket.ts` - Socket.IO client hook
- `useVoiceAssistant.ts` - WebRTC voice hook

**Backend (NestJS + Socket.IO)**:
- `chat.gateway.ts` - WebSocket handler for messages
- `chat.service.ts` - LLM integration, streaming, history
- `extraction.service.ts` - JSON Schema to function tools, confidence scoring
- `voice.gateway.ts` - WebRTC signaling for audio

**State Management (Zustand)**:
- `chatStore.ts` - Messages, connection status, streaming state
- `extractionStore.ts` - Extracted fields, confidence tracking
- `voiceStore.ts` - Voice session state

---

## Voice AI Integration (Zoice)

### What It Does

Zoice is our **telephony AI platform** that handles inbound and outbound voice calls with human-like conversational ability. Patients call the clinic and speak naturally; Zoice understands, responds, and triggers actions in PRM.

### Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           ZOICE VOICE AI PLATFORM                         │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌───────────┐ │
│  │   Plivo     │    │  Pipecat    │    │    LLM      │    │  Storage  │ │
│  │  Telephony  │───▶│  Pipeline   │───▶│  (GPT-4)    │───▶│  (S3)     │ │
│  └─────────────┘    └─────────────┘    └─────────────┘    └───────────┘ │
│         │                 │                  │                  │        │
│         │                 │                  │                  │        │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌───────────┐ │
│  │    STT      │    │    VAD      │    │    TTS      │    │ Extraction│ │
│  │ (Deepgram)  │    │  (Silero)   │    │(ElevenLabs) │    │ (GPT-4)   │ │
│  └─────────────┘    └─────────────┘    └─────────────┘    └───────────┘ │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Webhook
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                            PRM BACKEND                                    │
│                                                                           │
│  POST /api/v1/prm/voice/webhook                                          │
│  ├── Identify/create patient from phone number                           │
│  ├── Store VoiceCall record (transcript, recording, intent)              │
│  ├── Create Conversation thread                                          │
│  ├── If booking intent → Create Appointment                              │
│  └── Send confirmation (WhatsApp/SMS)                                    │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

### Voice Call Flow

```
1. CALL INITIATION
   Patient dials clinic number
   → Plivo routes to Zoice
   → /telephony/call/answer returns WebSocket URL

2. REAL-TIME CONVERSATION
   PipecatBotV1 initializes with:
   - Agent configuration (system prompt, first message)
   - Provider configs (STT, TTS, LLM, VAD)

   Audio Flow:
   Patient speaks → Silero VAD → Deepgram STT → GPT-4 → ElevenLabs TTS → Patient hears

3. INTENT DETECTION
   Throughout conversation, Zoice detects:
   - book_appointment
   - cancel_appointment
   - reschedule_appointment
   - inquiry
   - emergency

4. CALL COMPLETION
   /telephony/call/hangup triggered
   → Recording uploaded to S3
   → Whisper transcription
   → LLM extraction of structured data
   → Webhook to PRM with full payload

5. PRM PROCESSING
   POST /voice/webhook receives:
   {
     "call_id": "zoice_abc123",
     "patient_phone": "+919876543210",
     "duration_seconds": 180,
     "transcript": [...],
     "extracted_intent": {
       "action": "book_appointment",
       "specialty": "cardiology",
       "preferred_date": "2025-02-01",
       "urgency": "routine"
     },
     "recording_url": "https://s3..."
   }

   PRM Actions:
   → Patient lookup/creation
   → VoiceCall record stored
   → If booking: Appointment created
   → Confirmation sent via WhatsApp
```

### Zoice Data Models

**VoiceCall** (stored in PRM):
```
- id, tenant_id, patient_id
- zoice_call_id, plivo_call_id
- call_type: inbound | outbound
- status: scheduled | in_progress | completed | failed | no_answer
- started_at, ended_at, duration_seconds
- detected_intent: book_appointment | cancel | inquiry | emergency
- intent_confidence: 0.0-1.0
- conversation_id (links to conversation thread)
- appointment_id (if booking was made)
```

**VoiceCallTranscript**:
```
- call_id
- full_transcript (complete text)
- turns: [{speaker, text, timestamp}, ...]
- provider: whisper | google_stt | deepgram
- confidence_score
```

**VoiceCallExtraction**:
```
- call_id
- extracted_data: {name, phone, specialty, date, symptoms...}
- confidence_scores: {name: 0.95, specialty: 0.88, ...}
- extraction_model: gpt-4o-mini
```

### Supported Providers

| Category | Providers | Notes |
|----------|-----------|-------|
| **Telephony** | Plivo | PSTN/VoIP calls |
| **STT** | Deepgram, Google, Gladia, Groq | Real-time transcription |
| **TTS** | ElevenLabs, Google, Sarvam, Cartesia | Sarvam for Indian languages |
| **LLM** | OpenAI GPT-4, Groq | Conversation & extraction |
| **VAD** | Silero | Voice activity detection |

### Campaign Calling (Outbound)

Zoice supports bulk outbound calling for:
- Appointment reminders
- Follow-up care calls
- Medication adherence checks
- Preventive care recalls

```
Campaign Flow:
1. Create Campaign with Agent + ContactList
2. Celery task processes contacts (4 concurrent calls)
3. Each call: Agent speaks, extracts responses, updates PRM
4. Webhook delivers results per call
5. Credits deducted based on duration
```

---

## WhatsApp Integration (Twilio)

### What It Does

Two-way WhatsApp messaging for patient communication—appointment confirmations, reminders, pre-visit instructions, and interactive conversations.

### Integration Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│     Patient     │◄───────▶│     Twilio      │◄───────▶│   PRM Backend   │
│   (WhatsApp)    │         │   WhatsApp API  │         │                 │
└─────────────────┘         └─────────────────┘         └─────────────────┘
                                    │
                                    │ Webhooks
                                    ▼
                            POST /whatsapp/webhook (incoming)
                            POST /whatsapp/status (delivery updates)
```

### WhatsApp Webhook Processing

**Incoming Message Handler** (`/api/v1/prm/whatsapp/webhook`):
```python
1. Parse Twilio form-encoded webhook
2. Extract: From, To, Body, MediaUrl, MessageSid

3. Patient Identification:
   - Search by phone number
   - Create new patient if not found

4. Conversation Threading:
   - Find active conversation for patient
   - Create new if none exists
   - Update conversation state

5. Message Storage:
   ConversationMessage {
     conversation_id,
     direction: "inbound",
     content_type: "text" | "media",
     content: message_body,
     external_message_id: MessageSid,
     delivery_status: "delivered"
   }

6. NLP Processing (async):
   - Sentiment analysis
   - Intent detection
   - Entity extraction

7. Return 200 OK to Twilio (within 15 seconds)
```

**Outbound Messaging** (`POST /whatsapp/send`):
```python
Request:
{
  "patient_id": "uuid",
  "template": "appointment_reminder",
  "template_params": {
    "patient_name": "Rajesh Kumar",
    "date": "Feb 1, 2025",
    "time": "3:00 PM",
    "doctor": "Dr. Mehta"
  }
}

Response:
{
  "message_sid": "SM...",
  "status": "queued"
}
```

### Message Templates

**Appointment Reminder**:
```
Hello {{patient_name}},

This is a reminder for your appointment:
📅 Date: {{date}}
⏰ Time: {{time}}
👨‍⚕️ Doctor: {{doctor_name}}
📍 Location: {{clinic_address}}

Reply:
1 - Confirm
2 - Reschedule
3 - Cancel
```

**Post-Visit Follow-up**:
```
Hello {{patient_name}},

Thank you for visiting {{clinic_name}}.

How are you feeling today? Any concerns about your medication?

Reply with any questions, or call us at {{clinic_phone}}.
```

### Delivery Status Tracking

```
Message Lifecycle:
queued → sending → sent → delivered → read

Status Webhook (/whatsapp/status):
- Updates ConversationMessage.delivery_status
- Tracks: MessageSid, MessageStatus, ErrorCode
- Enables delivery reporting and retry logic
```

### Conversation State Management

```
Conversation {
  patient_id,
  channel_type: "whatsapp",
  status: "active" | "resolved" | "pending",
  state_data: {
    current_flow: "appointment_booking",
    step: "confirm_time",
    collected_data: {...}
  },
  extracted_entities: {...},
  first_message_at,
  last_message_at
}
```

---

## The PRM Dashboard

### Overview

The PRM Dashboard is a **Next.js 15 + React 19** application providing staff with a unified interface to manage patients, appointments, communications, and AI interactions.

### AI-Powered Features

#### 1. Natural Language Command Interface

Staff interact via natural language instead of clicking through menus:

```
"Book Rajesh Kumar for cardiology tomorrow at 2pm"
"Send WhatsApp reminder to all patients with appointments today"
"Show me diabetic patients overdue for HbA1c"
"Create post-surgery recovery journey for patient #12345"
```

#### 2. Multi-Agent Orchestration System

**5 Specialized AI Agents**:

| Agent | Tools | Use Cases |
|-------|-------|-----------|
| **AppointmentAgent** | check_availability, book, reschedule, cancel, get, list | Scheduling workflows |
| **PatientAgent** | search, get, create, update, get_360_view, merge | Patient management |
| **JourneyAgent** | create, get, add_step, complete_step, list, update | Care pathway orchestration |
| **CommunicationAgent** | send_whatsapp, send_sms, send_email, bulk_send, get_templates | Multi-channel messaging |
| **TicketAgent** | create, get, update, assign, resolve, close, add_comment | Support ticket management |

**Orchestration Flow**:
```
User Input: "Book appointment for Amit Shah with Dr. Mehta tomorrow"
                    │
                    ▼
            Intent Parser (GPT-4)
            - action: book_appointment
            - patient: "Amit Shah"
            - practitioner: "Dr. Mehta"
            - date: tomorrow
                    │
                    ▼
            Agent Orchestrator
            - Routes to: PatientAgent → AppointmentAgent
                    │
                    ▼
            PatientAgent.search("Amit Shah")
            → Returns: patient_id = "p123"
                    │
                    ▼
            AppointmentAgent.check_availability("Dr. Mehta", tomorrow)
            → Returns: slots = [{10am}, {2pm}, {4pm}]
                    │
                    ▼
            AppointmentAgent.book(patient_id, slot_id)
            → Returns: appointment created
                    │
                    ▼
            CommunicationAgent.send_whatsapp(patient_id, confirmation)
```

#### 3. Voice Input for Commands

- **Web Speech API integration** for browser-based voice input
- **Real-time transcription** as user speaks
- **Voice state management**: inactive → listening → processing
- **Sound wave animation** during listening

**File**: `/components/copilot/voice-input.tsx`

#### 4. Command Bar (Cmd+K)

Universal search and command interface:
- Recent command history (localStorage)
- Pre-defined suggestions
- Real-time execution feedback

**File**: `/components/ai/CommandBar.tsx`

### Dashboard Pages

| Page | Route | Features |
|------|-------|----------|
| **Dashboard** | `/dashboard` | Overview stats, activity feed, upcoming appointments |
| **Patients** | `/dashboard/patients` | Search, filter, add patients, list view |
| **Patient 360°** | `/dashboard/patients/[id]` | Complete profile, timeline, journeys, comms |
| **Appointments** | `/dashboard/appointments` | Calendar (day/week/month), AI-assisted booking |
| **Journeys** | `/dashboard/journeys` | Care pathway management, progress tracking |
| **Communications** | `/dashboard/communications` | Multi-channel message threads |
| **Tickets** | `/dashboard/tickets` | Support ticket management |
| **Analytics** | `/dashboard/analytics` | Dashboards, AI insights, metrics |
| **Zoice Admin** | `/dashboard/admin/zoice/*` | Call history, agents, pipelines, settings |

### Patient 360° View

Single-screen comprehensive patient profile:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PATIENT: Rajesh Kumar (MRN: PRM-2024-001234)                           │
│  Age: 45 | Male | Blood: O+ | Diabetic | Allergies: Penicillin         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐               │
│  │    VITALS     │  │   UPCOMING    │  │    ACTIVE     │               │
│  │  (Last Visit) │  │  APPOINTMENTS │  │   JOURNEYS    │               │
│  ├───────────────┤  ├───────────────┤  ├───────────────┤               │
│  │ BP: 130/85    │  │ Feb 1 - Cardio│  │ Diabetes Mgmt │               │
│  │ Pulse: 78     │  │ Feb 15 - Lab  │  │ ████████░░ 80%│               │
│  │ Weight: 78kg  │  │               │  │               │               │
│  │ HbA1c: 7.2%   │  │ [+ Schedule]  │  │ Post-Angio    │               │
│  └───────────────┘  └───────────────┘  │ ██████░░░░ 60%│               │
│                                         └───────────────┘               │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                         TIMELINE                                  │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │ Jan 28 │ 📞 Voice Call - Zoice - Confirmed Feb 1 appointment    │   │
│  │ Jan 25 │ 💬 WhatsApp - Sent medication reminder                 │   │
│  │ Jan 20 │ 🏥 Visit - Dr. Mehta - Cardiology follow-up            │   │
│  │ Jan 15 │ 🔬 Lab - HbA1c, Lipid Panel results received           │   │
│  │ Jan 10 │ 📞 Voice Call - Zoice - Scheduled lab appointment      │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────┐  ┌─────────────────────────────┐      │
│  │      COMMUNICATIONS        │  │       OPEN TICKETS          │      │
│  ├─────────────────────────────┤  ├─────────────────────────────┤      │
│  │ WhatsApp: 12 messages      │  │ #1234 - Insurance query     │      │
│  │ Voice: 3 calls             │  │ Status: Awaiting response   │      │
│  │ SMS: 5 messages            │  │ [View All]                  │      │
│  └─────────────────────────────┘  └─────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────────────┘
```

### Zoice Admin Integration

The dashboard includes a complete admin interface for managing Zoice:

- **Call History**: View all calls with transcripts, recordings, extracted data
- **Agents**: Configure AI agents (system prompts, voices, providers)
- **Pipelines**: Set up call flows and routing
- **Phone Numbers**: Manage clinic phone numbers
- **Settings**: Webhook configuration, provider settings

**Transparent Proxy Gateway**: `/api/v1/prm/admin/zoice/*` proxies requests to Zoice backend.

---

## End-to-End Patient Flows

### Flow 1: Voice Call → Appointment Booking

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    VOICE APPOINTMENT BOOKING FLOW                        │
└─────────────────────────────────────────────────────────────────────────┘

1. PATIENT CALLS
   Patient: +919876543210 calls clinic number

2. ZOICE ANSWERS
   Zoice: "Good morning, City Heart Clinic. How can I help you today?"

3. CONVERSATION
   Patient: "I need to see a heart doctor, I've been having chest pain"
   Zoice: "I'm sorry to hear that. Is this an emergency?"
   Patient: "No, it started a few days ago, not severe"
   Zoice: "I understand. Dr. Mehta, our cardiologist, has availability
          tomorrow at 10 AM or 3 PM. Which works better?"
   Patient: "3 PM please"
   Zoice: "Perfect. I've booked you for tomorrow at 3 PM with Dr. Mehta.
          You'll receive a WhatsApp confirmation shortly.
          Please arrive 15 minutes early. Anything else?"
   Patient: "No, thank you"
   Zoice: "Take care, goodbye."

4. CALL ENDS → WEBHOOK TO PRM
   POST /api/v1/prm/voice/webhook
   {
     "zoice_call_id": "call_abc123",
     "patient_phone": "+919876543210",
     "duration_seconds": 95,
     "transcript": [...full conversation...],
     "extracted_intent": {
       "action": "book_appointment",
       "specialty": "cardiology",
       "symptom": "chest pain",
       "urgency": "routine",
       "preferred_time": "3 PM tomorrow"
     },
     "recording_url": "https://s3.../recording.mp3"
   }

5. PRM PROCESSING
   - Patient lookup: Found existing patient "Rajesh Kumar"
   - Create VoiceCall record with transcript
   - Create Appointment: Feb 1, 3:00 PM, Dr. Mehta, Cardiology
   - Link VoiceCall → Appointment

6. CONFIRMATION VIA WHATSAPP
   Twilio sends to +919876543210:
   "Hello Rajesh, your appointment is confirmed:
    📅 Feb 1, 2025 at 3:00 PM
    👨‍⚕️ Dr. Mehta (Cardiology)
    📍 City Heart Clinic, Room 205

    Reply 1 to confirm, 2 to reschedule"

7. VISIBLE IN DASHBOARD
   - Appointment appears in calendar
   - Patient 360° shows call in timeline
   - Voice recording accessible for review
```

### Flow 2: Conversation Widget → Form Autofill

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    WIDGET FORM AUTOFILL FLOW                             │
└─────────────────────────────────────────────────────────────────────────┘

1. PATIENT OPENS WIDGET
   Embedded in clinic website or patient portal
   Session initialized with JWT token

2. PATIENT DESCRIBES SYMPTOMS
   Patient: "I've been having headaches for the past week,
            mostly in the morning. Also feeling nauseous sometimes.
            I'm 35 years old, female, no known allergies."

3. AI ASSISTANT RESPONDS (Streaming)
   AI: "I understand you're experiencing morning headaches with nausea.
        Let me gather a bit more information...

        On a scale of 1-10, how severe are the headaches?"

4. REAL-TIME EXTRACTION (Background)
   Form Schema: Pre-Visit Intake Form

   Extracted fields appear with confidence:
   ┌─────────────────────────────────────────────┐
   │ Chief Complaint: Headache          [95%] ✓  │
   │ Duration: 1 week                   [92%] ✓  │
   │ Timing: Morning                    [88%] ✓  │
   │ Associated Symptoms: Nausea        [90%] ✓  │
   │ Age: 35                            [98%] ✓  │
   │ Gender: Female                     [98%] ✓  │
   │ Known Allergies: None              [85%] ✓  │
   │ Pain Severity: [awaiting input]            │
   └─────────────────────────────────────────────┘

5. CONTINUED CONVERSATION
   Patient: "About a 6 or 7"

   Extraction updates:
   │ Pain Severity: 6-7/10              [95%] ✓  │

6. FORM COMPLETION
   All required fields extracted with high confidence
   Staff reviews, approves, form submitted to EHR

7. DATA FLOWS TO PRM
   - FHIR Observation created (headache symptom)
   - FHIR Condition created (if diagnosis made)
   - Patient record updated
   - Ready for clinical encounter
```

### Flow 3: WhatsApp → Journey Progression

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    WHATSAPP JOURNEY FLOW                                 │
└─────────────────────────────────────────────────────────────────────────┘

1. JOURNEY TRIGGER
   Patient "Rajesh Kumar" had angioplasty
   Post-Procedure Journey auto-started (event-driven)

2. DAY 2: FOLLOW-UP MESSAGE
   WhatsApp (automated):
   "Hello Rajesh, this is City Heart Clinic.

    How are you feeling today after your procedure?

    Reply:
    1 - Feeling good
    2 - Some discomfort
    3 - Need to speak with someone"

3. PATIENT RESPONDS
   Rajesh replies: "2"

4. WEBHOOK PROCESSING
   POST /api/v1/prm/whatsapp/webhook
   - Message stored in Conversation
   - Intent detected: "some_discomfort"
   - Journey stage updated

5. FOLLOW-UP TRIGGERED
   WhatsApp (automated):
   "I'm sorry to hear that. Can you describe the discomfort?

    • Where is it located?
    • On a scale of 1-10, how severe?
    • Any other symptoms?"

6. PATIENT DESCRIBES
   Rajesh: "Mild chest soreness around the incision, about 3/10,
           no other symptoms"

7. NLP EXTRACTION
   - Symptom: chest soreness
   - Location: incision site
   - Severity: 3/10 (mild)
   - Assessment: Expected post-procedure discomfort

8. JOURNEY CONTINUES
   WhatsApp:
   "Some soreness around the incision is normal in the first few days.

    ⚠️ Please contact us immediately if:
    • Pain increases significantly
    • You notice bleeding or swelling
    • You have difficulty breathing

    Your follow-up appointment is scheduled for Feb 5.
    Take care!"

9. DASHBOARD VISIBILITY
   - Journey progress: Stage 2/5 completed
   - Conversation visible in patient timeline
   - Alert logged for clinical review (symptom reported)
```

---

## Technical Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND LAYER                                  │
├─────────────────────────────┬─────────────────────────┬─────────────────────┤
│      PRM Dashboard          │   Conversation Widget   │    Patient Portal   │
│    (Next.js 15, React 19)   │     (React 18, Vite)    │     (React 18)      │
└─────────────────────────────┴─────────────────────────┴─────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API GATEWAY                                     │
│                    nginx (Rate Limiting, Auth, SSL)                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
┌───────────────────────┐ ┌───────────────────────┐ ┌───────────────────────┐
│     PRM Backend       │ │    Widget Backend     │ │    Zoice Platform     │
│      (FastAPI)        │ │      (NestJS)         │ │      (FastAPI)        │
├───────────────────────┤ ├───────────────────────┤ ├───────────────────────┤
│ 49+ modules           │ │ Chat Gateway (WS)     │ │ Telephony (Plivo)     │
│ FHIR R4 server        │ │ Voice Gateway (WS)    │ │ Bot (Pipecat)         │
│ Voice webhooks        │ │ Extraction service    │ │ Postprocessing        │
│ WhatsApp webhooks     │ │ LLM integration       │ │ Campaign runner       │
│ Journey orchestration │ │ Session management    │ │ Webhook delivery      │
└───────────────────────┘ └───────────────────────┘ └───────────────────────┘
                    │                   │                   │
                    └───────────────────┴───────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                      │
├────────────────┬────────────────┬────────────────┬──────────────────────────┤
│   PostgreSQL   │    MongoDB     │     Redis      │          S3             │
│   (Primary)    │   (Documents)  │  (Cache/Queue) │    (Media Storage)      │
├────────────────┼────────────────┼────────────────┼──────────────────────────┤
│ • Patients     │ • Audit logs   │ • Session cache│ • Call recordings       │
│ • Appointments │ • Call records │ • API cache    │ • Media attachments     │
│ • FHIR resources│ • Extractions │ • Rate limits  │ • Documents             │
│ • Conversations│ • Analytics    │ • Pipeline conf│                         │
└────────────────┴────────────────┴────────────────┴──────────────────────────┘
```

### Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **PRM Dashboard** | Next.js 15, React 19, TypeScript | Staff interface |
| **Conversation Widget** | React 18, Vite, Socket.IO | Embeddable patient chat |
| **Widget Backend** | NestJS, Socket.IO, Prisma | Real-time chat, extraction |
| **PRM Backend** | FastAPI, SQLAlchemy | Core business logic |
| **Zoice Platform** | FastAPI, Pipecat, Celery | Voice AI |
| **Database** | PostgreSQL 15 | Primary data store |
| **Document Store** | MongoDB | Flexible schemas |
| **Cache/Queue** | Redis | Caching, task queues |
| **LLM** | OpenAI GPT-4, GPT-4o-mini | Conversation, extraction |
| **STT** | Deepgram, Whisper, Google | Speech-to-text |
| **TTS** | ElevenLabs, Sarvam, Google | Text-to-speech |
| **Telephony** | Plivo | Voice calls |
| **Messaging** | Twilio | WhatsApp, SMS |
| **Storage** | AWS S3 | Media files |

### Event-Driven Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EVENT BUS (Kafka)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Topics:                                                                     │
│  • healthtech.patient.events      → Patient created/updated                 │
│  • healthtech.appointment.events  → Appointment lifecycle                   │
│  • healthtech.zoice.events        → Voice call events                       │
│  • healthtech.communication.events→ Message sent/delivered                  │
│  • healthtech.journey.events      → Journey stage transitions               │
│                                                                              │
│  Event Handlers:                                                             │
│  • PATIENT_CREATED        → Start welcome journey                           │
│  • APPOINTMENT_CREATED    → Send confirmation, start pre-visit journey      │
│  • APPOINTMENT_CHECKED_IN → Complete check-in stage                         │
│  • VOICE_CALL_COMPLETED   → Process transcript, update records              │
│  • MESSAGE_RECEIVED       → Update conversation, trigger flows              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## FHIR & ABDM Compliance

### FHIR R4 Implementation

**Endpoint**: `/api/v1/prm/fhir`

**Supported Resources**:
| Resource | Operations | Use Case |
|----------|------------|----------|
| Patient | CRUD, Search, $everything | Demographics, identifiers |
| Practitioner | CRUD, Search | Provider registry |
| Organization | CRUD, Search | Clinic hierarchy |
| Location | CRUD, Search | Physical locations |
| Appointment | CRUD, Search | Scheduling |
| Encounter | CRUD, Search | Clinical visits |
| Observation | CRUD, Search | Vitals, lab results |
| Condition | CRUD, Search | Diagnoses |
| MedicationRequest | CRUD, Search | Prescriptions |
| DiagnosticReport | CRUD, Search | Lab/imaging reports |

**FHIR Operations**:
- `$everything` - Get complete patient record
- `$validate` - Validate resources
- `Bundle` - Transaction/batch operations

**ABDM Alignment**:
- ABHA (Health ID) linking support
- FHIR-based data exchange
- Consent management framework
- Multi-tenant data isolation

---

## Security & Compliance

### Authentication & Authorization

| Mechanism | Use Case |
|-----------|----------|
| **JWT Tokens** | Dashboard & widget sessions |
| **API Keys** | Service-to-service (Zoice ↔ PRM) |
| **Webhook Secrets** | Verify incoming webhooks |
| **X-Tenant-Id** | Multi-tenant isolation |

### Data Security

- **Encryption at rest**: AES-256 for stored data
- **Encryption in transit**: TLS 1.3 for all connections
- **PHI handling**: HIPAA-compliant patterns
- **Audit logging**: All data access logged
- **Webhook URL encryption**: Stored URLs encrypted

### Compliance Ready

- **DPDP Act 2023**: Consent management, data minimization
- **HIPAA**: PHI protection patterns
- **ABDM Guidelines**: FHIR compliance, health data standards

---

## Implementation Status

### Component Completion

| Component | Status | Completion |
|-----------|--------|------------|
| **PRM Backend** | Production Ready | 85% |
| ├─ Voice Webhooks (Zoice) | ✅ Complete | 100% |
| ├─ WhatsApp Webhooks (Twilio) | ✅ Complete | 100% |
| ├─ FHIR R4 Server | ✅ Complete | 100% |
| ├─ Journey Orchestration | ✅ Complete | 100% |
| ├─ Conversation Threading | ✅ Complete | 100% |
| └─ Multi-Agent System | ✅ Complete | 100% |
| **PRM Dashboard** | Production Ready | 100% |
| ├─ AI Chat Interface | ✅ Complete | 100% |
| ├─ Voice Input | ✅ Complete | 100% |
| ├─ Command Bar | ✅ Complete | 100% |
| ├─ Patient 360° | ✅ Complete | 100% |
| └─ Zoice Admin | ✅ Complete | 100% |
| **Conversation Widget** | Production Ready | 95% |
| ├─ Text Chat | ✅ Complete | 100% |
| ├─ Form Autofill | ✅ Complete | 100% |
| ├─ Confidence Scoring | ✅ Complete | 100% |
| └─ Voice Input | ⏳ Framework Ready | 80% |
| **Zoice Voice Platform** | Production Ready | 100% |
| ├─ Inbound/Outbound Calls | ✅ Complete | 100% |
| ├─ Multi-provider STT/TTS | ✅ Complete | 100% |
| ├─ Transcription & Extraction | ✅ Complete | 100% |
| └─ Campaign Calling | ✅ Complete | 100% |

### Code Metrics

| Metric | Count |
|--------|-------|
| PRM Backend Modules | 49+ |
| PRM Dashboard Components | 50+ |
| AI Agents | 5 |
| AI Tools | 30+ |
| FHIR Resources | 10+ |
| API Endpoints | 200+ |
| Database Models | 100+ |

---

## Demo Script

### 5-Minute Demo Flow

**Minute 1: Voice Call Booking**
1. Play recording of patient calling Zoice
2. Show transcript appearing in real-time
3. Demonstrate automatic appointment creation
4. Show WhatsApp confirmation sent to patient

**Minute 2: Conversation Widget Autofill**
1. Open embedded widget on clinic website
2. Patient describes symptoms naturally
3. Watch extracted fields appear with confidence scores
4. Show form auto-populated, ready for review

**Minute 3: Dashboard AI Commands**
1. Type: "Show me patients who missed appointments this week"
2. Results appear instantly
3. Type: "Send WhatsApp reminders to reschedule"
4. Bulk messages sent with single command

**Minute 4: Patient 360° View**
1. Open patient profile
2. Show unified timeline: calls, messages, visits
3. View active care journeys with progress
4. Play back voice call recording

**Minute 5: End-to-End Flow**
1. Voice call creates appointment
2. WhatsApp sends reminder
3. Widget collects pre-visit info
4. All data unified in patient record
5. Ready for clinical encounter

### Q&A Prep (2 minutes)

| Question | Answer |
|----------|--------|
| "Indian languages?" | Sarvam TTS, regional STT support |
| "Data security?" | Encrypted, HIPAA patterns, India hosting |
| "Integration with EHR?" | FHIR R4 APIs, bidirectional sync |
| "Pricing model?" | SaaS per-provider-per-month |
| "Implementation time?" | 2-4 weeks for basic setup |

---

## Why This Matters for India

India has **1 doctor per 1,500 people**. We can't train doctors fast enough, but we can multiply their effectiveness.

**PRM enables**:
- **One receptionist** handling 5x the call volume via AI
- **One clinic** serving patients 24/7 without extra staff
- **Zero manual data entry** via conversational extraction
- **Unified patient view** across voice, WhatsApp, and web

This isn't about replacing healthcare workers—it's about **freeing them to do what only humans can: provide empathetic, high-judgment care**.

---

## Team & Contact

**Built by Kuzushi Labs**

*"Less clicks, more care. Less waiting, more healing."*

---

**Document Version**: 2.0
**Last Updated**: January 2025
**Submission**: Ekathon Health AI 2026 - Track 1

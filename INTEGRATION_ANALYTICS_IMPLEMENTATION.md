# WhatsApp, Voice Agent & Analytics Integration - Implementation Guide

**Status:** In Progress
**Started:** November 19, 2024
**Last Updated:** November 19, 2024

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Database Schema](#database-schema)
4. [Implementation Status](#implementation-status)
5. [API Endpoints](#api-endpoints)
6. [Frontend Components](#frontend-components)
7. [Analytics & Reporting](#analytics--reporting)
8. [AI Assistant Integration](#ai-assistant-integration)
9. [Testing Strategy](#testing-strategy)
10. [Deployment](#deployment)
11. [Next Steps](#next-steps)

---

## Overview

This implementation integrates three major components into the PRM Dashboard:

1. **WhatsApp Chat Ingress** - Display and manage patient conversations from WhatsApp/n8n chatbot
2. **Zucol/Zoice Voice Agents** - Integrate voice call data, transcripts, and recordings
3. **Comprehensive Analytics** - Real-time dashboards, metrics, and AI-powered insights

### Key Requirements

- **Loose Coupling:** Webhook-based integration, no tight dependencies
- **Comprehensive Analytics:** All metrics queryable by AI Assistant via text/voice
- **Real-time Dashboards:** Live metrics with pub/sub updates
- **Export & Reporting:** PDF/CSV/Excel reports with scheduling

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  PRM Dashboard (Next.js)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Conversations│  │ Voice Calls  │  │ Analytics    │ │
│  │ UI           │  │ UI           │  │ Dashboard    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │           AI Assistant (with Analytics Tools)    │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                     HTTP/WebSocket
                          │
┌─────────────────────────────────────────────────────────┐
│              PRM Backend API (FastAPI)                  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Analytics Module                                │  │
│  │  - Query aggregated metrics                      │  │
│  │  - Real-time metrics (SSE/WebSocket)             │  │
│  │  - Report generation                             │  │
│  │  - AI-powered insights                           │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Webhook Endpoints                               │  │
│  │  - /webhooks/voice-agent (Zucol/Zoice)           │  │
│  │  - /webhooks/whatsapp (Twilio)                   │  │
│  │  - /webhooks/n8n (n8n callbacks)                 │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Tool APIs (for Zucol/Zoice to call)             │  │
│  │  - /api/appointments/book                        │  │
│  │  - /api/patients/lookup                          │  │
│  │  - /api/practitioners/available-slots            │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────┐
│               PostgreSQL Database                       │
│  Tables:                                                │
│  - conversations                                        │
│  - conversation_messages                                │
│  - voice_calls                                          │
│  - voice_call_transcripts                               │
│  - voice_call_recordings                                │
│  - voice_call_extractions                               │
│  - analytics_appointment_daily                          │
│  - analytics_journey_daily                              │
│  - analytics_communication_daily                        │
│  - analytics_voice_call_daily                           │
└─────────────────────────────────────────────────────────┘

External Systems:
┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐
│  n8n Chatbot     │  │  Zucol/Zoice     │  │  Twilio      │
│  (WhatsApp)      │  │  Voice Agents    │  │  WhatsApp    │
└──────────────────┘  └──────────────────┘  └──────────────┘
        │                      │                     │
        └──────────────────────┴─────────────────────┘
                      Webhooks to PRM
```

---

## Database Schema

### Tables Created

#### 1. **conversations**
Multi-channel conversation threads (WhatsApp, SMS, Email, Voice, WebChat)

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    patient_id UUID REFERENCES patients(id),
    subject VARCHAR(200),
    status VARCHAR(20) NOT NULL DEFAULT 'open',  -- open, pending, snoozed, closed
    priority VARCHAR(10) NOT NULL DEFAULT 'p2',  -- p0, p1, p2, p3
    channel_type VARCHAR(20) NOT NULL DEFAULT 'whatsapp',
    external_id VARCHAR(255),  -- Twilio conversation SID, etc.
    current_owner_id UUID REFERENCES practitioners(id),
    department_id UUID REFERENCES departments(id),
    state_data JSONB DEFAULT '{}',  -- Conversation state for AI
    extracted_data JSONB DEFAULT '{}',  -- Extracted patient/appointment data
    is_intake_complete BOOLEAN DEFAULT FALSE,
    appointment_id UUID REFERENCES appointments(id),
    journey_instance_id UUID REFERENCES journey_instances(id),
    first_message_at TIMESTAMP WITH TIME ZONE,
    last_message_at TIMESTAMP WITH TIME ZONE,
    closed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_conversations_patient_status ON conversations(patient_id, status);
CREATE INDEX idx_conversations_channel_status ON conversations(channel_type, status);
CREATE INDEX idx_conversations_last_message ON conversations(last_message_at);
```

#### 2. **conversation_messages**
Individual messages within conversations

```sql
CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    direction VARCHAR(10) NOT NULL,  -- inbound, outbound
    actor_type VARCHAR(20) NOT NULL,  -- patient, agent, bot, system
    actor_id UUID,
    content_type VARCHAR(20) NOT NULL DEFAULT 'text',  -- text, media, voice, file
    text_body TEXT,
    media_url VARCHAR(512),
    media_type VARCHAR(100),
    media_size_bytes INTEGER,
    external_message_id VARCHAR(255),  -- Twilio SID, etc.
    delivery_status VARCHAR(20),  -- queued, sent, delivered, failed
    delivered_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE,
    sentiment VARCHAR(20),  -- positive, neutral, negative
    intent VARCHAR(50),  -- book_appointment, ask_question, etc.
    entities JSONB DEFAULT '{}',  -- NER entities
    language VARCHAR(10),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_conv_messages_conversation_created ON conversation_messages(conversation_id, created_at);
CREATE INDEX idx_conv_messages_direction ON conversation_messages(direction, created_at);
```

#### 3. **voice_calls**
Voice call records from Zucol/Zoice platform

```sql
CREATE TABLE voice_calls (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    patient_id UUID REFERENCES patients(id),
    zoice_call_id UUID UNIQUE NOT NULL,  -- Zucol/Zoice call ID
    plivo_call_id VARCHAR(255),
    patient_phone VARCHAR(20) NOT NULL,
    agent_phone VARCHAR(20),
    call_type VARCHAR(20) NOT NULL DEFAULT 'inbound',  -- inbound, outbound
    call_status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    pipeline_id UUID,  -- Zucol/Zoice pipeline
    agent_name VARCHAR(100),
    detected_intent VARCHAR(50),  -- book_appointment, cancel, inquiry, emergency
    call_outcome VARCHAR(50),  -- appointment_booked, query_answered, transferred
    confidence_score FLOAT,
    conversation_id UUID REFERENCES conversations(id),
    appointment_id UUID REFERENCES appointments(id),
    language VARCHAR(10),
    sentiment VARCHAR(20),
    audio_quality_score FLOAT,
    transcription_quality_score FLOAT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_voice_calls_patient_started ON voice_calls(patient_id, started_at);
CREATE INDEX idx_voice_calls_phone_started ON voice_calls(patient_phone, started_at);
CREATE INDEX idx_voice_calls_zoice_id ON voice_calls(zoice_call_id);
```

#### 4. **voice_call_transcripts**
Call transcripts from STT services

```sql
CREATE TABLE voice_call_transcripts (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    call_id UUID NOT NULL REFERENCES voice_calls(id) ON DELETE CASCADE,
    full_transcript TEXT NOT NULL,
    turns JSONB DEFAULT '[]',  -- Turn-by-turn breakdown
    provider VARCHAR(50) NOT NULL,  -- whisper, google_stt, gladia
    language VARCHAR(10),
    confidence_score FLOAT,
    word_count INTEGER,
    processing_duration_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_voice_transcripts_call ON voice_call_transcripts(call_id);
```

#### 5. **voice_call_recordings**
Audio recording storage references

```sql
CREATE TABLE voice_call_recordings (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    call_id UUID NOT NULL REFERENCES voice_calls(id) ON DELETE CASCADE,
    recording_url VARCHAR(512) NOT NULL,
    storage_provider VARCHAR(50),  -- s3, gcs, azure_blob
    storage_path VARCHAR(512),
    format VARCHAR(20),  -- mp3, wav
    duration_seconds INTEGER,
    file_size_bytes INTEGER,
    is_redacted BOOLEAN DEFAULT FALSE,
    retention_expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_voice_recordings_call ON voice_call_recordings(call_id);
CREATE INDEX idx_voice_recordings_retention ON voice_call_recordings(retention_expires_at);
```

#### 6. **voice_call_extractions**
Structured data extracted from transcripts

```sql
CREATE TABLE voice_call_extractions (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    call_id UUID NOT NULL REFERENCES voice_calls(id) ON DELETE CASCADE,
    extraction_type VARCHAR(50) NOT NULL,  -- appointment_booking, patient_info
    pipeline_id UUID,
    prompt_template VARCHAR(100),
    extracted_data JSONB NOT NULL DEFAULT '{}',
    confidence_scores JSONB DEFAULT '{}',
    overall_confidence FLOAT,
    is_validated BOOLEAN DEFAULT FALSE,
    model_used VARCHAR(100),  -- gpt-4, claude-3, etc.
    processing_duration_ms INTEGER,
    tokens_used INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_voice_extractions_call ON voice_call_extractions(call_id);
CREATE INDEX idx_voice_extractions_type ON voice_call_extractions(extraction_type);
```

#### 7-10. **Analytics Tables** (Pre-computed Daily Aggregations)

See the Alembic migration file for full schemas:
- `analytics_appointment_daily` - Appointment metrics by day/hour
- `analytics_journey_daily` - Journey progress metrics
- `analytics_communication_daily` - Message/conversation metrics
- `analytics_voice_call_daily` - Voice call performance metrics

---

## Implementation Status

### ✅ Completed

1. **Database Models** (`conversation_voice_models.py`)
   - 6 core tables for conversations and voice calls
   - 4 analytics aggregation tables
   - Full relationships and indexes

2. **Alembic Migration** (`f548902ab172_add_conversation_voice_analytics_tables.py`)
   - Creates all 10 tables
   - 30+ performance indexes
   - Proper foreign keys and cascades

3. **Analytics Schemas** (`modules/analytics/schemas.py`)
   - Request/response models for all metrics
   - Time period enums (today, last_7_days, etc.)
   - Export formats (CSV, Excel, PDF)
   - AI Assistant query schemas
   - Real-time metrics subscription schemas

### 🚧 In Progress

4. **Analytics Service Layer**
   - Query builders for aggregated metrics
   - Time series data generation
   - Breakdown computations

### ⏳ Pending

5. **Webhook Endpoints**
   - `/api/webhooks/voice-agent` - Receive Zucol/Zoice webhook data
   - `/api/webhooks/whatsapp` - Receive Twilio WhatsApp messages
   - `/api/webhooks/n8n` - Receive n8n callback data

6. **Tool API Endpoints** (for Zucol/Zoice to call)
   - `/api/tools/appointments/book` - Book appointment from voice call
   - `/api/tools/patients/lookup` - Lookup patient by phone
   - `/api/tools/practitioners/slots` - Get available slots

7. **Analytics API Endpoints**
   - `/api/analytics/appointments` - Appointment metrics
   - `/api/analytics/journeys` - Journey metrics
   - `/api/analytics/communication` - Communication metrics
   - `/api/analytics/voice-calls` - Voice call metrics
   - `/api/analytics/dashboard` - Complete dashboard overview
   - `/api/analytics/realtime` - SSE/WebSocket for live metrics

8. **Frontend Components**
   - WhatsApp conversation threads UI (patient-wise view)
   - Voice call history with player and transcripts
   - Analytics dashboard with charts
   - Report generation interface

9. **AI Assistant Tools**
   - Analytics query tools for natural language queries
   - Integration with existing AI Assistant

10. **Testing**
    - Unit tests for services
    - Integration tests for webhooks
    - E2E tests for UI flows

11. **Documentation**
    - API documentation
    - Integration guides
    - User guides

---

## API Endpoints

### Analytics Endpoints

#### GET `/api/v1/analytics/appointments`
Get appointment analytics

**Query Parameters:**
- `time_period`: today | yesterday | last_7_days | last_30_days | custom
- `start_date`: YYYY-MM-DD (required if custom)
- `end_date`: YYYY-MM-DD (required if custom)
- `aggregation`: hourly | daily | weekly | monthly
- `channel_origin`: whatsapp | phone | web | voice_agent (optional filter)
- `practitioner_id`: UUID (optional filter)
- `department_id`: UUID (optional filter)

**Response:**
```json
{
  "summary": {
    "total_appointments": 1250,
    "scheduled": 300,
    "confirmed": 400,
    "completed": 450,
    "canceled": 50,
    "no_show": 50,
    "no_show_rate": 4.0,
    "completion_rate": 90.0,
    "trend": [
      {"date": "2024-11-12", "value": 42},
      {"date": "2024-11-13", "value": 48}
    ]
  },
  "breakdown": {
    "by_channel": {
      "whatsapp": 500,
      "phone": 300,
      "voice_agent": 250,
      "web": 200
    },
    "by_hour_of_day": {
      "9": 120,
      "10": 150,
      "11": 140
    }
  }
}
```

#### GET `/api/v1/analytics/journeys`
Journey analytics

#### GET `/api/v1/analytics/communication`
Communication analytics

#### GET `/api/v1/analytics/voice-calls`
Voice call analytics

#### GET `/api/v1/analytics/dashboard`
Complete dashboard overview with all metrics

#### GET `/api/v1/analytics/realtime` (SSE)
Real-time metrics stream using Server-Sent Events

### Webhook Endpoints

#### POST `/api/v1/webhooks/voice-agent`
Receive voice call data from Zucol/Zoice

**Request Body:**
```json
{
  "call_id": "uuid",
  "patient_phone": "+1234567890",
  "recording_url": "https://...",
  "transcript": "Full conversation...",
  "extracted_data": {
    "patient_name": "John Doe",
    "appointment_date": "2024-11-20"
  },
  "duration_seconds": 180,
  "confidence_score": 0.95,
  "detected_intent": "book_appointment"
}
```

#### POST `/api/v1/webhooks/whatsapp`
Receive WhatsApp messages from Twilio

**Request Body:** Twilio's standard webhook format

### Tool API Endpoints (for Zucol/Zoice)

#### POST `/api/v1/tools/appointments/book`
Book an appointment (called by voice agent during call)

**Request Body:**
```json
{
  "patient_phone": "+1234567890",
  "preferred_date": "2024-11-20",
  "preferred_time": "10:00 AM",
  "practitioner_name": "Dr. Smith",
  "reason": "Checkup"
}
```

#### GET `/api/v1/tools/patients/lookup?phone={phone}`
Lookup patient by phone number

#### GET `/api/v1/tools/practitioners/slots`
Get available appointment slots

---

## Frontend Components

### 1. WhatsApp Conversation Threads

**Location:** `frontend/apps/prm-dashboard/components/communications/ConversationThread.tsx`

**Features:**
- Patient-wise conversation view
- Message bubbles (inbound/outbound)
- Media attachments (images, voice notes, documents)
- Sentiment indicators
- AI-suggested responses
- Search within conversation

### 2. Voice Call History

**Location:** `frontend/apps/prm-dashboard/components/voice/CallHistory.tsx`

**Features:**
- List of all voice calls
- Call duration, status, outcome
- Play/pause audio recordings
- View transcripts (turn-by-turn)
- Extracted data display
- Link to related appointments

### 3. Analytics Dashboard

**Location:** `frontend/apps/prm-dashboard/app/(dashboard)/analytics/page.tsx`

**Features:**
- Real-time metrics (SSE updates every 30s)
- Time period selector
- Multiple chart types (line, bar, pie)
- Breakdown views
- Export buttons
- Filter panels

### 4. Report Generator

**Location:** `frontend/apps/prm-dashboard/components/analytics/ReportGenerator.tsx`

**Features:**
- Report type selection
- Date range picker
- Format selection (PDF/CSV/Excel)
- Email scheduling
- Download generated reports

---

## Analytics & Reporting

### Metrics Categories

#### 1. Appointment Analytics
- Total appointments (by status)
- No-show rate, completion rate, cancellation rate
- Appointments by channel (WhatsApp, Phone, Voice Agent, Web)
- Appointments by practitioner, department, location
- Peak hours/days analysis
- Average wait time

#### 2. Journey Analytics
- Total active journeys
- Completion rates by journey type
- Average journey duration
- Overdue steps count
- Stage progression analysis
- Patient engagement scores

#### 3. Communication Analytics
- Messages sent/received (by channel)
- Response time (average, median)
- Response rate percentage
- Conversation duration
- Sentiment analysis (positive/neutral/negative)
- Volume trends

#### 4. Voice Call Analytics
- Total calls (by intent, outcome)
- Call duration (average, median)
- Audio quality scores
- Transcription confidence
- Appointment booking success rate
- Query resolution rate

#### 5. Patient Analytics
- Total patients (new/active/inactive)
- Patient demographics
- Average appointments per patient
- High-risk patient identification
- Engagement levels

---

## AI Assistant Integration

### Analytics Tools for AI Assistant

The AI Assistant will have tools to query all analytics via natural language.

**Example queries:**
- "How many appointments were booked last week?"
- "What's our no-show rate this month?"
- "Show me voice call performance for yesterday"
- "Which practitioner has the most appointments?"
- "What's the average response time for WhatsApp messages?"

**Implementation:**
```typescript
// AI Assistant Tool Definition
const analyticsTools = [
  {
    name: "get_appointment_metrics",
    description: "Get appointment statistics for a time period",
    parameters: {
      time_period: "today | yesterday | last_7_days | last_30_days",
      filters: "Optional filters (practitioner, department, channel)"
    }
  },
  {
    name: "get_journey_metrics",
    description: "Get journey progress and completion metrics"
  },
  {
    name: "get_communication_metrics",
    description: "Get message and conversation statistics"
  },
  {
    name: "get_voice_call_metrics",
    description: "Get voice call performance metrics"
  },
  {
    name: "generate_insight",
    description: "Generate AI-powered insights from metrics",
    parameters: {
      metric_category: "appointments | journeys | communication | voice_calls",
      analysis_type: "trends | anomalies | recommendations"
    }
  }
];
```

---

## Testing Strategy

### Unit Tests

**Backend:**
```bash
# Test analytics service
pytest backend/services/prm-service/tests/unit/test_analytics_service.py

# Test webhook processing
pytest backend/services/prm-service/tests/unit/test_webhooks.py
```

**Frontend:**
```bash
# Test components
npm test -- ConversationThread.test.tsx
npm test -- CallHistory.test.tsx
npm test -- AnalyticsDashboard.test.tsx
```

### Integration Tests

**Webhook Integration:**
```python
def test_voice_agent_webhook_creates_call_record():
    # Send webhook payload
    response = client.post("/api/v1/webhooks/voice-agent", json=payload)

    # Verify call record created
    call = db.query(VoiceCall).filter_by(zoice_call_id=payload["call_id"]).first()
    assert call is not None
    assert call.patient_phone == payload["patient_phone"]
```

### E2E Tests

**Playwright tests:**
```typescript
test('View patient conversation history', async ({ page }) => {
  await page.goto('/patients/123');
  await page.click('[data-testid="conversations-tab"]');

  // Verify conversations load
  await expect(page.locator('[data-testid="conversation-thread"]')).toBeVisible();

  // Verify messages display
  await expect(page.locator('[data-testid="message"]')).toHaveCount(10);
});
```

---

## Deployment

### Database Migration

```bash
# Run migration
cd backend
alembic upgrade head

# Verify tables created
psql -d prm_db -c "\dt"
```

### Environment Variables

**Backend:**
```bash
# Webhook secrets
ZOICE_WEBHOOK_SECRET=xxx
TWILIO_WEBHOOK_SECRET=xxx

# Analytics cache
REDIS_URL=redis://localhost:6379

# Report storage
REPORTS_STORAGE_BUCKET=s3://prm-reports
```

**Frontend:**
```bash
# Analytics refresh interval
NEXT_PUBLIC_ANALYTICS_REFRESH_INTERVAL=30000  # 30 seconds

# WebSocket URL for real-time metrics
NEXT_PUBLIC_REALTIME_METRICS_URL=wss://api.healthtech.com/analytics/realtime
```

---

## Next Steps

### Immediate (This Week)

1. ✅ Complete analytics service layer implementation
2. ✅ Create webhook endpoints for Zucol/Zoice and WhatsApp
3. ✅ Build tool API endpoints for voice agent
4. ✅ Create WhatsApp conversation threads UI
5. ✅ Create voice call history UI

### Short-term (Next 2 Weeks)

6. ✅ Build analytics dashboard with charts
7. ✅ Implement real-time metrics with SSE
8. ✅ Add AI Assistant analytics tools
9. ✅ Create report generation functionality
10. ✅ Add comprehensive testing

### Long-term (Next Month)

11. ✅ Performance optimization (caching, query optimization)
12. ✅ Advanced analytics (ML-powered insights)
13. ✅ Scheduled reports with email delivery
14. ✅ Mobile-optimized dashboards
15. ✅ Complete documentation and training materials

---

## Notes

- All integrations use webhook-based architecture for loose coupling
- Analytics tables are pre-computed daily for performance
- Real-time metrics use SSE (Server-Sent Events) for efficiency
- AI Assistant can query all metrics via natural language
- PHI is sanitized before sending to any external services
- All voice recordings have retention policies (HIPAA compliance)

---

**For Questions:** Contact the development team or refer to the detailed API documentation.

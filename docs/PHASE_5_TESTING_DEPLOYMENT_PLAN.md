# Phase 5: Testing & Deployment - Comprehensive Plan

**Date:** November 19, 2024
**Status:** In Progress
**Objective:** Complete test coverage and production deployment readiness for all 16 PRM modules

---

## Executive Summary

This document outlines the comprehensive testing and deployment strategy for the Patient Relationship Management (PRM) backend system, covering:

- **Unit Testing:** 100+ unit tests across 16 modules
- **Integration Testing:** Critical multi-module workflows
- **End-to-End Testing:** Complete user journeys
- **Performance Testing:** Load and stress testing
- **Deployment:** Docker, environment configs, CI/CD

---

## Table of Contents

1. [Testing Architecture](#testing-architecture)
2. [Module Testing Breakdown](#module-testing-breakdown)
3. [Integration Test Scenarios](#integration-test-scenarios)
4. [End-to-End Test Flows](#end-to-end-test-flows)
5. [Deployment Configuration](#deployment-configuration)
6. [Test Execution Strategy](#test-execution-strategy)

---

## Testing Architecture

### Test Structure

```
prm-service/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Shared fixtures
│   ├── test_config.py                 # Test configuration
│   │
│   ├── unit/                          # Unit tests (isolated)
│   │   ├── __init__.py
│   │   ├── phase1/
│   │   │   ├── test_journeys_service.py
│   │   │   ├── test_communications_service.py
│   │   │   └── test_tickets_service.py
│   │   ├── phase2/
│   │   │   ├── test_webhooks_service.py
│   │   │   ├── test_conversations_service.py
│   │   │   ├── test_appointments_service.py
│   │   │   └── test_n8n_service.py
│   │   ├── phase3/
│   │   │   ├── test_media_service.py
│   │   │   ├── test_patients_service.py
│   │   │   └── test_notifications_service.py
│   │   └── phase4/
│   │       ├── test_vector_service.py
│   │       ├── test_agents_service.py
│   │       └── test_intake_service.py
│   │
│   ├── integration/                   # Integration tests (multi-module)
│   │   ├── __init__.py
│   │   ├── test_whatsapp_booking_flow.py
│   │   ├── test_journey_orchestration.py
│   │   ├── test_notification_dispatch.py
│   │   └── test_voice_agent_intake.py
│   │
│   ├── e2e/                          # End-to-end tests (full workflows)
│   │   ├── __init__.py
│   │   ├── test_patient_booking_journey.py
│   │   ├── test_voice_call_to_appointment.py
│   │   └── test_intake_to_ehr.py
│   │
│   ├── performance/                   # Performance tests
│   │   ├── __init__.py
│   │   ├── test_load_appointments.py
│   │   └── test_concurrent_messages.py
│   │
│   └── fixtures/                      # Test data factories
│       ├── __init__.py
│       ├── patient_fixtures.py
│       ├── appointment_fixtures.py
│       └── conversation_fixtures.py
```

### Testing Principles

1. **Isolation:** Unit tests should not depend on external services
2. **Mocking:** Use pytest-mock for external dependencies (DB, Redis, APIs)
3. **Factories:** Use factory-boy for generating test data
4. **Coverage:** Target 80%+ code coverage for critical paths
5. **Fast Execution:** Unit tests should run in < 10 seconds total
6. **Deterministic:** Tests should produce consistent results

---

## Module Testing Breakdown

### Phase 1: Core Modules (3 modules)

#### 1. Journeys Module
**Service Tests (`test_journeys_service.py`):**
- `test_create_journey_definition()` - Create new journey
- `test_list_journeys()` - List with filters
- `test_get_journey_by_id()` - Retrieve specific journey
- `test_update_journey()` - Update journey properties
- `test_add_journey_stage()` - Add stage to journey
- `test_create_journey_instance()` - Create instance from definition
- `test_advance_journey_stage()` - Progress through stages
- `test_execute_stage_action()` - Execute stage-specific actions
- `test_journey_not_found()` - Error handling
- `test_invalid_stage_transition()` - Validation

**Coverage Target:** 85%

#### 2. Communications Module
**Service Tests (`test_communications_service.py`):**
- `test_create_whatsapp_communication()` - WhatsApp message
- `test_create_sms_communication()` - SMS message
- `test_create_email_communication()` - Email
- `test_create_voice_communication()` - Voice call
- `test_scheduled_communication()` - Future scheduling
- `test_list_communications_by_patient()` - Filter by patient
- `test_list_communications_by_channel()` - Filter by channel
- `test_invalid_channel()` - Error handling
- `test_send_communication_async()` - Background sending
- `test_communication_retry_logic()` - Retry on failure

**Coverage Target:** 80%

#### 3. Tickets Module
**Service Tests (`test_tickets_service.py`):**
- `test_create_ticket()` - Create support ticket
- `test_list_tickets_with_filters()` - Filtering
- `test_get_ticket_by_id()` - Retrieve ticket
- `test_update_ticket_status()` - Status changes
- `test_assign_ticket()` - Assignment logic
- `test_ticket_priority_handling()` - Priority rules
- `test_auto_assignment_logic()` - Auto-assign
- `test_ticket_not_found()` - Error handling
- `test_concurrent_updates()` - Race conditions

**Coverage Target:** 85%

### Phase 2: WhatsApp & Appointments (4 modules)

#### 4. Webhooks Module
**Service Tests (`test_webhooks_service.py`):**
- `test_process_incoming_whatsapp()` - WhatsApp webhook
- `test_validate_twilio_signature()` - Security
- `test_handle_voice_agent_webhook()` - Voice transcripts
- `test_extract_message_data()` - Data extraction
- `test_route_to_conversation()` - Message routing
- `test_handle_media_webhook()` - Media attachments
- `test_invalid_signature()` - Security failure
- `test_malformed_webhook_data()` - Error handling

**Coverage Target:** 90% (security critical)

#### 5. Conversations Module
**Service Tests (`test_conversations_service.py`):**
- `test_create_conversation()` - New conversation
- `test_add_message_to_conversation()` - Message append
- `test_get_conversation_history()` - Message retrieval
- `test_update_conversation_state()` - State transitions
- `test_conversation_state_machine()` - FSM logic
- `test_context_management()` - Context handling
- `test_concurrent_messages()` - Race conditions
- `test_conversation_not_found()` - Error handling

**Coverage Target:** 85%

#### 6. Appointments Module
**Service Tests (`test_appointments_service.py`):**
- `test_get_available_slots()` - Slot calculation
- `test_book_appointment()` - Booking logic
- `test_update_appointment()` - Modifications
- `test_cancel_appointment()` - Cancellation
- `test_slot_conflict_detection()` - Overlaps
- `test_provider_availability()` - Scheduling rules
- `test_patient_appointment_history()` - History retrieval
- `test_appointment_reminders()` - Reminder logic
- `test_double_booking_prevention()` - Race conditions

**Coverage Target:** 90% (business critical)

#### 7. N8N Integration Module
**Service Tests (`test_n8n_service.py`):**
- `test_trigger_workflow()` - Workflow trigger
- `test_handle_booking_response()` - Response handling
- `test_confirm_slot()` - Slot confirmation
- `test_workflow_timeout()` - Timeout handling
- `test_retry_failed_workflow()` - Retry logic
- `test_invalid_webhook_response()` - Error handling

**Coverage Target:** 80%

### Phase 3: Supporting Modules (3 modules)

#### 8. Media Module
**Service Tests (`test_media_service.py`):**
- `test_generate_presigned_upload_url()` - Upload URL
- `test_generate_presigned_download_url()` - Download URL
- `test_record_media_metadata()` - Metadata storage
- `test_get_media_by_id()` - Retrieval
- `test_list_patient_media()` - Filtering
- `test_check_file_duplicates()` - SHA256 deduplication
- `test_media_not_found()` - Error handling
- `test_invalid_file_type()` - Validation

**Coverage Target:** 80%

#### 9. Patients Module
**Service Tests (`test_patients_service.py`):**
- `test_create_patient()` - Patient creation
- `test_search_patients()` - Search logic
- `test_detect_duplicates()` - Fuzzy matching
- `test_update_patient()` - Updates
- `test_get_patient_timeline()` - Timeline aggregation
- `test_patient_not_found()` - Error handling
- `test_invalid_phone_number()` - Validation

**Coverage Target:** 85%

#### 10. Notifications Module
**Service Tests (`test_notifications_service.py`):**
- `test_send_whatsapp_notification()` - WhatsApp
- `test_send_sms_notification()` - SMS
- `test_send_email_notification()` - Email
- `test_notification_templating()` - Template rendering
- `test_batch_notifications()` - Bulk sending
- `test_notification_retry()` - Retry logic
- `test_invalid_channel()` - Error handling

**Coverage Target:** 80%

### Phase 4: Advanced Modules (3 modules)

#### 11. Vector Module
**Service Tests (`test_vector_service.py`):**
- `test_ingest_conversation_transcripts()` - Ingestion
- `test_chunk_text()` - Chunking algorithm
- `test_generate_embeddings()` - Embedding generation
- `test_hybrid_search()` - Vector + FTS search
- `test_search_by_patient()` - Patient filtering
- `test_delete_source_chunks()` - Cleanup
- `test_vector_similarity()` - Distance calculation
- `test_empty_search_results()` - Edge cases

**Coverage Target:** 85%

#### 12. Agents Module
**Service Tests (`test_agents_service.py`):**
- `test_list_available_tools()` - Tool registry
- `test_execute_create_ticket_tool()` - Ticket creation
- `test_execute_confirm_appointment_tool()` - Appointment confirm
- `test_execute_send_notification_tool()` - Notification
- `test_execute_update_patient_tool()` - Patient update
- `test_tool_execution_logging()` - Audit trail
- `test_tool_execution_failure()` - Error handling
- `test_invalid_tool_name()` - Validation

**Coverage Target:** 80%

#### 13. Intake Module
**Service Tests (`test_intake_service.py`):**
- `test_create_intake_session()` - Session creation
- `test_upsert_intake_records()` - Record updates
- `test_upsert_with_client_id()` - Idempotency
- `test_link_patient()` - Patient linking
- `test_submit_session()` - Submission
- `test_generate_intake_summary()` - AI summary
- `test_get_intake_statistics()` - Analytics
- `test_session_not_found()` - Error handling

**Coverage Target:** 85%

---

## Integration Test Scenarios

### 1. WhatsApp Appointment Booking Flow
**File:** `test_whatsapp_booking_flow.py`

**Scenario:** End-to-end WhatsApp conversation → appointment booking

```python
def test_complete_whatsapp_booking_flow():
    """
    Test complete WhatsApp booking flow:
    1. Incoming WhatsApp message (webhook)
    2. Conversation creation/continuation
    3. State machine progression
    4. Appointment slot query
    5. Slot selection and booking
    6. Confirmation message
    7. Journey stage advancement
    """
```

**Components Tested:**
- Webhooks → Conversations → Appointments → Communications → Journeys

### 2. Journey Orchestration
**File:** `test_journey_orchestration.py`

**Scenario:** Patient progression through multi-stage journey

```python
def test_patient_journey_orchestration():
    """
    Test journey orchestration:
    1. Create journey instance for new patient
    2. Execute initial stage actions (welcome message)
    3. Advance to booking stage
    4. Book appointment
    5. Advance to confirmation stage
    6. Send confirmation
    7. Journey completion
    """
```

**Components Tested:**
- Journeys → Communications → Appointments → Patients

### 3. Notification Dispatch
**File:** `test_notification_dispatch.py`

**Scenario:** Multi-channel notification delivery

```python
def test_multi_channel_notification_dispatch():
    """
    Test notification system:
    1. Appointment booked event
    2. Notification service receives event
    3. Template rendering
    4. Multi-channel dispatch (WhatsApp, SMS, Email)
    5. Delivery confirmation
    """
```

**Components Tested:**
- Notifications → Communications → Events

### 4. Voice Agent Intake
**File:** `test_voice_agent_intake.py`

**Scenario:** Voice call → clinical intake → EHR

```python
def test_voice_call_intake_flow():
    """
    Test voice agent intake:
    1. Voice agent webhook (transcript + data)
    2. Intake session creation
    3. Data extraction and upsert
    4. Patient linking (with consent)
    5. Intake summary generation
    6. EHR update
    """
```

**Components Tested:**
- Webhooks → Intake → Patients → Vector (for search)

---

## End-to-End Test Flows

### E2E Test 1: Patient Booking Journey
**File:** `test_patient_booking_journey.py`

**Full Workflow:**
1. New patient sends WhatsApp message: "I need to see a doctor"
2. System creates conversation, starts journey
3. Bot asks for symptoms, collects info
4. Bot suggests available slots
5. Patient selects slot
6. Appointment booked, confirmation sent
7. Reminder scheduled
8. Patient receives reminder
9. Appointment completed
10. Follow-up journey triggered

**Success Criteria:**
- Journey completes all stages
- Appointment successfully booked
- All notifications delivered
- No errors in logs

### E2E Test 2: Voice Call to Appointment
**File:** `test_voice_call_to_appointment.py`

**Full Workflow:**
1. Patient calls clinic (voice agent handles)
2. Voice transcript sent to PRM webhook
3. Clinical intake session created
4. Symptoms, medications extracted
5. Appointment slot suggested
6. Patient confirms over phone
7. Appointment booked in system
8. SMS confirmation sent
9. Calendar invite sent

**Success Criteria:**
- All clinical data captured
- Appointment booked correctly
- Multiple channel confirmations
- Audit trail complete

### E2E Test 3: Intake to EHR
**File:** `test_intake_to_ehr.py`

**Full Workflow:**
1. Patient completes digital intake form
2. Data validated and stored
3. Patient linked (with consent)
4. AI summary generated
5. Data synced to FHIR-compliant EHR
6. Provider receives notification
7. Chart updated

**Success Criteria:**
- All intake data captured
- FHIR compliance maintained
- Provider notified
- No data loss

---

## Deployment Configuration

### Docker Setup

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  prm-service:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/logs

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=prm
      - POSTGRES_USER=prm_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Environment Configuration

**.env.example:**
```bash
# Database
DATABASE_URL=postgresql://prm_user:password@localhost:5432/prm

# Redis
REDIS_URL=redis://localhost:6379/0

# Twilio (WhatsApp/SMS)
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=xxxxx
TWILIO_PHONE_NUMBER=+1234567890

# OpenAI (Embeddings, Whisper)
OPENAI_API_KEY=sk-xxxxx

# S3 Storage
S3_BUCKET_NAME=prm-media
AWS_ACCESS_KEY_ID=xxxxx
AWS_SECRET_ACCESS_KEY=xxxxx
AWS_REGION=us-east-1

# N8N Integration
N8N_WEBHOOK_URL=https://n8n.example.com/webhook/xxxxx

# Monitoring
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
PROMETHEUS_PORT=9090

# Environment
ENVIRONMENT=production
DEBUG=false
```

### CI/CD Pipeline

**GitHub Actions (.github/workflows/test-deploy.yml):**
```yaml
name: Test and Deploy

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: prm_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Run migrations
      run: |
        alembic upgrade head
      env:
        DATABASE_URL: postgresql://test:test@localhost/prm_test

    - name: Run tests
      run: |
        pytest tests/ -v --cov=. --cov-report=xml
      env:
        DATABASE_URL: postgresql://test:test@localhost/prm_test
        REDIS_URL: redis://localhost:6379

    - name: Upload coverage
      uses: codecov/codecov-action@v3

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest

    steps:
    - name: Deploy to production
      run: |
        # Deployment steps here
        echo "Deploying to production..."
```

---

## Test Execution Strategy

### Local Development

```bash
# Run all tests
pytest tests/ -v

# Run specific module tests
pytest tests/unit/phase1/test_journeys_service.py -v

# Run with coverage
pytest tests/ --cov=modules --cov-report=html

# Run only integration tests
pytest tests/integration/ -v

# Run only fast tests (skip slow E2E)
pytest tests/ -v -m "not slow"
```

### Coverage Goals

| Category | Target | Priority |
|----------|--------|----------|
| Unit Tests | 80%+ | HIGH |
| Critical Paths | 90%+ | CRITICAL |
| Integration | 70%+ | MEDIUM |
| E2E | 60%+ | MEDIUM |
| Overall | 75%+ | HIGH |

### Test Execution Time

- **Unit Tests:** < 30 seconds (all modules)
- **Integration Tests:** < 2 minutes
- **E2E Tests:** < 5 minutes
- **Total Suite:** < 8 minutes

---

## Success Criteria

### Phase 5 Completion Checklist

- [ ] All 16 modules have unit tests (80%+ coverage)
- [ ] 4+ integration test scenarios passing
- [ ] 3+ E2E test flows working
- [ ] Docker setup complete and tested
- [ ] Environment configuration documented
- [ ] CI/CD pipeline configured
- [ ] Deployment runbooks created
- [ ] Performance benchmarks established
- [ ] All tests passing in CI
- [ ] Documentation complete

### Quality Gates

1. **No test should be skipped** - All tests must pass
2. **Coverage threshold** - Must meet 75% overall
3. **Performance** - Tests complete in < 8 minutes
4. **Security** - No secrets in test code
5. **Documentation** - All tests documented

---

## Timeline

### Week 1: Unit Tests
- Day 1-2: Phase 1 modules (Journeys, Communications, Tickets)
- Day 3-4: Phase 2 modules (Webhooks, Conversations, Appointments, N8N)
- Day 5: Phase 3 modules (Media, Patients, Notifications)

### Week 2: Integration & E2E
- Day 6: Phase 4 modules (Vector, Agents, Intake)
- Day 7-8: Integration tests
- Day 9-10: E2E tests

### Week 3: Deployment
- Day 11-12: Docker setup, CI/CD
- Day 13-14: Performance testing, documentation
- Day 15: Final verification and sign-off

---

**Status:** Ready to Execute
**Next Step:** Set up pytest infrastructure and begin unit testing
**Est. Completion:** 3 weeks with dedicated effort

---

**Prepared by:** Claude (Testing & DevOps Specialist)
**Date:** November 19, 2024
**Version:** 1.0

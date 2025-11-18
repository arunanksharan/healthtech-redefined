# Phase 3 Architecture: Supporting Modules

**Date:** November 18, 2024
**Status:** 🔄 In Progress
**Modules:** Media, Notifications, Patients

---

## 🎯 Phase 3 Objectives

Implement critical supporting modules that enable complete patient care workflows:

1. **Media Module** - File uploads, medical records, S3 storage
2. **Notifications Module** - Appointment reminders, alerts, multi-channel messaging
3. **Patients Module** - Enhanced patient management with FHIR compliance

These three modules together complete the core PRM functionality needed for production.

---

## 📋 Module Analysis

### 1. Media Module

**Purpose:** Handle file uploads, medical records, voice recordings, and document storage

**Key Requirements:**
- ✅ Secure file upload with validation
- ✅ S3/cloud storage integration
- ✅ SHA256 hashing for deduplication
- ✅ Presigned URLs for secure downloads
- ✅ File metadata tracking (size, MIME type, duration)
- ✅ Support for images, PDFs, audio (voice messages), video
- ✅ Integration with conversations (attach media to messages)
- ✅ Integration with appointments (medical records)

**Use Cases:**
1. Voice messages in WhatsApp conversations
2. Medical records attached to patient profiles
3. Lab results and imaging attached to appointments
4. Identity verification documents
5. Insurance cards and authorization forms

**Technical Considerations:**
- **Storage:** Use cloud object storage (S3-compatible)
- **Security:** Presigned URLs with expiration, no public access
- **Performance:** SHA256 deduplication to save storage
- **Scalability:** Direct-to-S3 multipart uploads for large files
- **Compliance:** HIPAA-compliant storage, encryption at rest

---

### 2. Notifications Module

**Purpose:** Send appointment reminders, alerts, and notifications across multiple channels

**Key Requirements:**
- ✅ Multi-channel support (WhatsApp, SMS, Email, Voice)
- ✅ Message templates with variable substitution
- ✅ Template management (create, update, list)
- ✅ Scheduled notifications (appointment reminders)
- ✅ Integration with Twilio (WhatsApp, SMS, Voice)
- ✅ Integration with SendGrid/SES (Email)
- ✅ Delivery status tracking
- ✅ Retry logic for failed sends

**Use Cases:**
1. Appointment confirmations (immediate)
2. Appointment reminders (24 hours before, 1 hour before)
3. Appointment cancellation notifications
4. Lab results ready alerts
5. Medication reminders
6. Health tips and wellness messages

**Template Examples:**
```
Template: appointment_reminder_24h
Channel: whatsapp
Subject: N/A
Body: Hi {patient_name}! Reminder: You have an appointment tomorrow at {appointment_time} with Dr. {practitioner_name} at {location_name}. Reply CONFIRM to confirm or CANCEL to cancel.

Template: appointment_confirmed
Channel: whatsapp
Subject: N/A
Body: ✅ Your appointment is confirmed for {appointment_date} at {appointment_time} with Dr. {practitioner_name}. Location: {location_address}. See you then!
```

**Technical Considerations:**
- **Queue:** Background task queue for async sending
- **Retry:** Exponential backoff for failures
- **Rate Limiting:** Respect provider limits (Twilio, SendGrid)
- **Tracking:** Store delivery status for each notification
- **Templates:** Jinja2 or simple variable substitution

---

### 3. Patients Module

**Purpose:** Enhanced patient management with FHIR compliance and comprehensive CRUD

**Key Requirements:**
- ✅ Complete patient CRUD operations
- ✅ FHIR Patient resource compliance
- ✅ Search and filtering (by name, phone, DOB, MRN)
- ✅ Patient demographics management
- ✅ Contact information (multiple phones, emails, addresses)
- ✅ Emergency contacts
- ✅ Insurance information
- ✅ Medical record number (MRN) generation
- ✅ Event publishing for patient lifecycle
- ✅ Soft delete support

**FHIR Patient Resource Fields:**
```python
# Identity
- MRN (Medical Record Number)
- Name (legal name, preferred name, aliases)
- Date of Birth
- Gender
- SSN (encrypted)

# Contact
- Phone numbers (home, mobile, work)
- Email addresses
- Physical addresses
- Preferred contact method

# Demographics
- Race
- Ethnicity
- Preferred language
- Marital status

# Care
- Primary care provider
- Emergency contacts
- Insurance information
- Active/Inactive status
```

**Use Cases:**
1. Patient registration (new patient intake)
2. Patient search (by name, phone, MRN)
3. Patient profile updates
4. Emergency contact management
5. Insurance verification
6. Patient merging (duplicate resolution)

**Technical Considerations:**
- **FHIR Compliance:** Use shared FHIR models
- **Search:** Full-text search on names, phone fuzzy matching
- **Privacy:** PII encryption, access logging
- **Validation:** Phone number validation, email validation
- **Events:** Publish all lifecycle events for integrations

---

## 🏗️ Architecture Design

### Module Structure (Consistent Pattern)

Each module follows the proven pattern from Phases 1 & 2:

```
modules/<module_name>/
├── __init__.py              # Module initialization
├── schemas.py               # Pydantic models (10-20 schemas)
├── router.py                # FastAPI endpoints (5-10 endpoints)
├── service.py               # Business logic (main implementation)
└── [optional files]         # Additional utilities if needed
```

---

## 📊 Media Module Design

### Database Models (Use shared models)

```python
# shared/database/models.py already has:
class MediaAsset(Base):
    id: UUID
    org_id: UUID  # Multi-tenancy
    key: str  # S3 key path
    sha256: str  # For deduplication
    mime_type: str
    size_bytes: int
    duration_ms: Optional[int]  # For audio/video
    source: str  # upload, recording, attachment, import
    created_at: datetime
    updated_at: datetime
```

### API Endpoints

```
POST   /api/v1/prm/media/upload              # Upload file
GET    /api/v1/prm/media/{id}                # Get media metadata
GET    /api/v1/prm/media/{id}/download       # Get presigned download URL
DELETE /api/v1/prm/media/{id}                # Soft delete media
GET    /api/v1/prm/media                     # List media (with filters)
POST   /api/v1/prm/media/attach-to-message   # Attach to conversation message
POST   /api/v1/prm/media/attach-to-patient   # Attach to patient record
```

### Service Methods

```python
class MediaService:
    async def upload_file(file: UploadFile) -> Tuple[MediaAsset, str]
        # 1. Read file data
        # 2. Calculate SHA256 hash
        # 3. Check for existing file (deduplication)
        # 4. Upload to S3 with key: uploads/{org_id}/{sha256}.{ext}
        # 5. Create MediaAsset record
        # 6. Generate presigned download URL (10 min expiry)
        # 7. Return asset + URL

    async def get_download_url(media_id: UUID) -> str
        # Generate presigned URL with 10-minute expiry

    async def attach_to_message(media_id: UUID, message_id: UUID)
        # Link media to message

    async def attach_to_patient(media_id: UUID, patient_id: UUID, category: str)
        # Link media to patient (lab_result, insurance_card, etc.)
```

### S3 Storage Configuration

```python
# core/s3_client.py
class S3StorageClient:
    def __init__(self):
        self.s3 = boto3.client('s3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket = settings.S3_BUCKET_NAME

    def upload_bytes(self, key: str, data: bytes, content_type: str):
        # Upload to S3 with encryption

    def presign_download(self, key: str, expires_seconds: int = 600) -> str:
        # Generate presigned URL

    def delete_object(self, key: str):
        # Delete from S3 (soft delete keeps DB record)
```

---

## 📊 Notifications Module Design

### Database Models

```python
class MessageTemplate(Base):
    id: UUID
    org_id: UUID
    channel: str  # whatsapp, sms, email, voice
    name: str  # appointment_reminder_24h, appointment_confirmed
    subject: Optional[str]  # For email
    body: str  # Template with {variables}
    created_at: datetime
    updated_at: datetime

class OutboundNotification(Base):
    id: UUID
    org_id: UUID
    channel: str
    to: str  # Phone number or email
    subject: Optional[str]
    body: str  # Rendered template
    template_id: Optional[UUID]
    metadata: JSON  # Original variables
    status: str  # queued, sending, sent, failed
    sent_at: Optional[datetime]
    error: Optional[str]
    created_at: datetime
    updated_at: datetime
```

### API Endpoints

```
POST   /api/v1/prm/notifications/templates              # Create template
GET    /api/v1/prm/notifications/templates              # List templates
GET    /api/v1/prm/notifications/templates/{id}         # Get template
PATCH  /api/v1/prm/notifications/templates/{id}         # Update template
DELETE /api/v1/prm/notifications/templates/{id}         # Delete template

POST   /api/v1/prm/notifications/send                   # Send notification
POST   /api/v1/prm/notifications/send-template          # Send using template
GET    /api/v1/prm/notifications                        # List notifications
GET    /api/v1/prm/notifications/{id}                   # Get notification status
POST   /api/v1/prm/notifications/schedule               # Schedule future notification
```

### Service Methods

```python
class NotificationService:
    async def create_template(template_data: TemplateCreate) -> MessageTemplate

    async def send_notification(
        channel: str,
        to: str,
        subject: str,
        body: str,
        variables: Dict[str, Any]
    ) -> OutboundNotification
        # 1. Render template with variables
        # 2. Create OutboundNotification record (status=queued)
        # 3. Queue background task for sending
        # 4. Return notification

    async def send_with_template(
        channel: str,
        to: str,
        template_name: str,
        variables: Dict[str, Any]
    ) -> OutboundNotification
        # 1. Load template
        # 2. Render with variables
        # 3. Send via send_notification()

    async def schedule_notification(
        channel: str,
        to: str,
        template_name: str,
        variables: Dict[str, Any],
        send_at: datetime
    )
        # Store in Redis or DB with scheduled time
        # Background worker picks up at send_at time

    async def _send_via_channel(notification_id: UUID)
        # Background task to actually send
        # 1. Get notification from DB
        # 2. Route to channel handler (Twilio, SendGrid, etc.)
        # 3. Update status based on result
        # 4. Retry on failure
```

### Channel Handlers

```python
class TwilioHandler:
    async def send_whatsapp(to: str, body: str) -> bool
    async def send_sms(to: str, body: str) -> bool
    async def send_voice(to: str, message: str) -> bool

class SendGridHandler:
    async def send_email(to: str, subject: str, body: str) -> bool
```

---

## 📊 Patients Module Design

### Database Models (FHIR-compliant)

```python
# shared/database/models.py - Enhanced Patient model
class Patient(Base):
    id: UUID
    org_id: UUID

    # Identity
    mrn: str  # Medical Record Number (unique per org)
    legal_name: str
    preferred_name: Optional[str]
    date_of_birth: date
    gender: str
    ssn: Optional[str]  # Encrypted

    # Contact
    primary_phone: str
    secondary_phone: Optional[str]
    email: Optional[str]
    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    preferred_contact_method: str  # phone, email, whatsapp

    # Demographics
    race: Optional[str]
    ethnicity: Optional[str]
    preferred_language: str  # en, es, etc.
    marital_status: Optional[str]

    # Care
    primary_care_provider_id: Optional[UUID]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    emergency_contact_relationship: Optional[str]

    # Status
    status: str  # active, inactive, deceased

    # Audit
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]  # Soft delete
```

### API Endpoints

```
POST   /api/v1/prm/patients                     # Create patient
GET    /api/v1/prm/patients                     # List/search patients
GET    /api/v1/prm/patients/{id}                # Get patient
PATCH  /api/v1/prm/patients/{id}                # Update patient
DELETE /api/v1/prm/patients/{id}                # Soft delete patient
POST   /api/v1/prm/patients/{id}/activate       # Reactivate patient
GET    /api/v1/prm/patients/search              # Advanced search
POST   /api/v1/prm/patients/{id}/emergency-contact  # Update emergency contact
GET    /api/v1/prm/patients/{id}/appointments   # Get patient appointments
GET    /api/v1/prm/patients/{id}/media          # Get patient documents
POST   /api/v1/prm/patients/merge               # Merge duplicate patients
```

### Service Methods

```python
class PatientService:
    async def create_patient(patient_data: PatientCreate) -> Patient
        # 1. Validate data
        # 2. Generate MRN if not provided
        # 3. Check for duplicates (name + DOB + phone)
        # 4. Create Patient record
        # 5. Publish PATIENT_CREATED event
        # 6. Return patient

    async def search_patients(
        query: str = None,  # Search name, phone, MRN
        phone: str = None,
        date_of_birth: date = None,
        status: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Patient]
        # Advanced search with fuzzy matching

    async def find_duplicates(patient_id: UUID) -> List[Patient]
        # Find potential duplicate patients
        # Match on: exact name + DOB, phone number, similar names

    async def merge_patients(
        primary_id: UUID,
        duplicate_id: UUID
    ) -> Patient
        # 1. Move all appointments to primary
        # 2. Move all conversations to primary
        # 3. Move all media to primary
        # 4. Soft delete duplicate
        # 5. Publish PATIENTS_MERGED event
        # 6. Return primary patient

    async def generate_mrn() -> str
        # Generate unique MRN
        # Format: MRN-{year}{random_digits}
        # e.g., MRN-2024123456
```

---

## 🔗 Integration Points

### Media ↔ Conversations
- Attach voice messages to WhatsApp conversations
- Attach documents to messages
- Media URLs in conversation history

### Media ↔ Patients
- Patient profile photos
- Insurance cards
- Lab results
- Medical records

### Notifications ↔ Appointments
- Send appointment confirmations
- Send appointment reminders (24h, 1h before)
- Send cancellation notifications

### Notifications ↔ Journeys
- Send journey milestone notifications
- Send care plan reminders
- Send health tips

### Patients ↔ Appointments
- Get all appointments for patient
- Patient demographics in appointment details

### Patients ↔ Conversations
- Link conversations to patient records
- Patient context in conversation state

---

## 📈 Implementation Priority

### Phase 3.1: Media Module (Week 1)
- Essential for voice messages in WhatsApp
- Needed for medical records
- **Priority: CRITICAL**

### Phase 3.2: Patients Module (Week 1-2)
- Enhanced patient management
- FHIR compliance
- **Priority: HIGH**

### Phase 3.3: Notifications Module (Week 2)
- Appointment reminders
- Multi-channel messaging
- **Priority: HIGH**

---

## 🧪 Testing Strategy

### Media Module Tests
1. Upload file → verify S3 storage → get download URL
2. Upload duplicate file → verify deduplication
3. Upload unsupported file type → verify rejection
4. Generate presigned URL → verify expiration
5. Attach media to message → verify link created
6. Delete media → verify soft delete

### Notifications Module Tests
1. Create template → send notification → verify delivery
2. Send with template → verify variable substitution
3. Schedule notification → verify delayed sending
4. Failed send → verify retry logic
5. Rate limiting → verify queuing

### Patients Module Tests
1. Create patient → verify MRN generation → verify event published
2. Search by name → verify fuzzy matching
3. Search by phone → verify normalization
4. Find duplicates → verify similarity algorithm
5. Merge patients → verify data migration
6. Soft delete → verify deletion → verify can reactivate

---

## 🔐 Security Considerations

### Media Module
- ✅ Presigned URLs with short expiration (10 min)
- ✅ No public S3 bucket access
- ✅ File type validation (prevent .exe, .js, etc.)
- ✅ File size limits (prevent DoS)
- ✅ Virus scanning (ClamAV or cloud service)
- ✅ HIPAA-compliant encryption at rest (S3-SSE)

### Notifications Module
- ✅ Rate limiting per channel
- ✅ Template injection prevention
- ✅ PII masking in logs
- ✅ Opt-out handling
- ✅ Do not send to invalid numbers

### Patients Module
- ✅ PII encryption (SSN, sensitive fields)
- ✅ Access logging for audit trail
- ✅ Role-based access control
- ✅ Data validation (phone, email, SSN format)
- ✅ Duplicate detection to prevent fraud

---

## 📊 Success Metrics

### Media Module
- ✅ File upload success rate > 99%
- ✅ Average upload time < 5 seconds
- ✅ Storage deduplication rate > 20%
- ✅ Presigned URL generation < 100ms

### Notifications Module
- ✅ Notification delivery rate > 95%
- ✅ Average delivery time < 30 seconds
- ✅ Template rendering success > 99.9%
- ✅ Failed send retry success > 80%

### Patients Module
- ✅ Patient creation time < 500ms
- ✅ Search response time < 1 second
- ✅ Duplicate detection accuracy > 95%
- ✅ Zero data loss in patient merge

---

**Status:** 📋 Architecture Complete - Ready for Implementation
**Next Step:** Implement Media Module
**Total Files to Create:** ~15 files (5 per module)
**Estimated LOC:** ~2500 lines

**Prepared by:** Claude (Healthcare Systems Expert)
**Date:** November 18, 2024
**Version:** 3.0 (Phase 3 Architecture)

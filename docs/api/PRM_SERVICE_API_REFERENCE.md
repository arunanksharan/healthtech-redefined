# PRM Service API Reference

> Patient Relationship Management Service - Complete API Documentation

**Base URL:** `/api/v1/prm`
**Version:** 0.2.0
**Entry Point:** `main_modular.py` (recommended) or `main.py` (legacy)

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Patients API](#patients-api)
4. [Practitioners API](#practitioners-api)
5. [Appointments API](#appointments-api)
6. [Journeys API](#journeys-api)
7. [Journey Instances API](#journey-instances-api)
8. [Communications API](#communications-api)
9. [Tickets API](#tickets-api)
10. [Analytics API](#analytics-api)
11. [Error Handling](#error-handling)

---

## Overview

The PRM Service provides RESTful APIs for managing patient relationships, including:

- **Patient Management** - CRUD operations, search, 360-degree views
- **Appointment Scheduling** - Booking, calendar views, statistics
- **Journey Orchestration** - Patient engagement workflows with stages
- **Multi-channel Communications** - WhatsApp, SMS, Email messaging
- **Support Tickets** - Issue tracking and resolution
- **Analytics** - Dashboard metrics and reporting

### Architecture

```
/api/v1/prm
├── /patients          # Patient management
├── /appointments      # Appointment scheduling
├── /journeys          # Journey definitions
├── /instances         # Journey instances (active patient journeys)
├── /communications    # Multi-channel messaging
├── /tickets           # Support tickets
└── /analytics         # Metrics and dashboards
```

---

## Authentication

All endpoints require authentication via JWT bearer token (when auth is enabled).

```http
Authorization: Bearer <token>
```

---

## Patients API

Base path: `/api/v1/prm/patients`

### List Patients

```http
GET /patients
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number (1-indexed) |
| `page_size` | int | 20 | Items per page (max 100) |
| `search` | string | - | Search by name, phone, email |
| `tenant_id` | UUID | - | Filter by tenant |
| `status` | string | - | Filter by status (active, deceased) |

**Response:** `PatientSimpleListResponse`

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "has_next": true,
  "has_previous": false
}
```

### Search Patients

```http
GET /patients/search
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Search query (min 2 chars) |
| `type` | enum | No | `name`, `phone`, `mrn`, `email` (default: name) |
| `limit` | int | No | Max results (default 20, max 50) |

**Response:** `List[PatientSimpleResponse]`

### Get Patient Details

```http
GET /patients/{patient_id}
```

**Response:** `PatientDetailResponse` - Full patient demographics with statistics

### Get Patient 360 View

```http
GET /patients/{patient_id}/360
```

Returns comprehensive patient view including:
- Patient demographics
- Recent appointments (last 10)
- Active journey instances
- Open tickets
- Recent communications
- Timeline information

**Response:** `Patient360Response`

```json
{
  "patient": {...},
  "appointments": [...],
  "journeys": [...],
  "tickets": [...],
  "communications": [...],
  "total_appointments": 25,
  "upcoming_appointments": 2,
  "active_journeys": 1,
  "open_tickets": 0,
  "recent_communications": 15,
  "last_visit_date": "2024-01-15T10:00:00Z",
  "next_appointment_date": "2024-02-01T14:30:00Z"
}
```

### Create Patient

```http
POST /patients
```

**Request Body:** `PatientCreate`

**Response:** `PatientResponse` (201 Created)

### Update Patient

```http
PATCH /patients/{patient_id}
```

**Request Body:** `PatientUpdate` (all fields optional)

**Response:** `PatientResponse`

### Delete Patient

```http
DELETE /patients/{patient_id}
```

Soft delete - sets patient to inactive status.

**Response:**
```json
{
  "success": true,
  "message": "Patient deleted successfully",
  "patient_id": "uuid"
}
```

### Additional Patient Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/patients/mrn/{mrn}` | GET | Get patient by MRN |
| `/patients/search` | POST | Advanced search with multiple criteria |
| `/patients/{id}/duplicates` | GET | Find potential duplicate patients |
| `/patients/merge` | POST | Merge duplicate patients |
| `/patients/stats/demographics` | GET | Patient statistics |
| `/patients/{id}/appointments` | GET | Patient's appointments |
| `/patients/{id}/conversations` | GET | Patient's conversations |
| `/patients/{id}/activate` | POST | Reactivate inactive patient |

---

## Practitioners API

Base path: `/api/v1/prm/practitioners`

### List Practitioners

```http
GET /practitioners
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page (max 100) |
| `tenant_id` | UUID | - | Filter by tenant |
| `speciality` | string | - | Filter by speciality |
| `is_active` | bool | - | Filter by active status |
| `search` | string | - | Search by name |

**Response:** `PractitionerListResponse`

### List Practitioners (Simple)

```http
GET /practitioners/simple
```

Optimized endpoint for dropdowns - returns minimal data.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tenant_id` | UUID | - | Filter by tenant |
| `speciality` | string | - | Filter by speciality |
| `active_only` | bool | true | Only active practitioners |

**Response:** `List[PractitionerSimpleResponse]`

```json
[
  {
    "id": "uuid",
    "name": "Dr. John Smith",
    "speciality": "Cardiology",
    "is_active": true
  }
]
```

### List Specialities

```http
GET /practitioners/specialities
```

Returns unique speciality values for filtering.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `tenant_id` | UUID | Filter by tenant |

**Response:** `List[string]`

### Get Practitioner

```http
GET /practitioners/{practitioner_id}
```

**Response:** `PractitionerResponse`

### Create Practitioner

```http
POST /practitioners
```

**Request Body:** `PractitionerCreate`

```json
{
  "tenant_id": "uuid",
  "first_name": "John",
  "last_name": "Smith",
  "middle_name": "A",
  "gender": "male",
  "qualification": "MD, FACC",
  "speciality": "Cardiology",
  "sub_speciality": "Interventional Cardiology",
  "license_number": "MD123456",
  "registration_number": "REG789",
  "phone_primary": "+1234567890",
  "email_primary": "dr.smith@clinic.com",
  "is_active": true,
  "meta_data": {}
}
```

**Response:** `PractitionerResponse` (201 Created)

### Update Practitioner

```http
PATCH /practitioners/{practitioner_id}
```

Partial update - only provided fields are modified.

**Request Body:** `PractitionerUpdate`

**Response:** `PractitionerResponse`

### Delete Practitioner

```http
DELETE /practitioners/{practitioner_id}
```

Permanently removes a practitioner. Consider setting `is_active=false` for soft delete.

**Response:** 204 No Content

---

## Appointments API

Base path: `/api/v1/prm/appointments`

### List Appointments

```http
GET /appointments
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | int | Page number |
| `page_size` | int | Items per page (max 100) |
| `patient_id` | UUID | Filter by patient |
| `practitioner_id` | UUID | Filter by practitioner |
| `location_id` | UUID | Filter by location |
| `status` | string | Filter by status |
| `start_date` | date | Filter from date (YYYY-MM-DD) |
| `end_date` | date | Filter to date (YYYY-MM-DD) |

**Response:** `AppointmentListResponse`

### Get Today's Appointments

```http
GET /appointments/today
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `practitioner_id` | UUID | Filter by practitioner |
| `location_id` | UUID | Filter by location |
| `status` | string | Filter by status |

**Response:** `List[AppointmentDetailResponse]`

### Get Upcoming Appointments

```http
GET /appointments/upcoming
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | int | 10 | Max results (max 50) |
| `patient_id` | UUID | - | Filter by patient |
| `practitioner_id` | UUID | - | Filter by practitioner |

**Response:** `List[AppointmentDetailResponse]`

### Get Appointment Statistics

```http
GET /appointments/stats
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `tenant_id` | UUID | Filter by tenant |
| `start_date` | date | Stats from date |
| `end_date` | date | Stats to date |

**Response:** `AppointmentStats`

```json
{
  "total": 500,
  "today": 25,
  "upcoming": 150,
  "completed": 300,
  "cancelled": 40,
  "no_show": 10,
  "by_status": {
    "booked": 150,
    "completed": 300,
    "cancelled": 40,
    "no_show": 10
  },
  "by_type": {
    "consultation": 200,
    "follow_up": 150,
    "procedure": 100
  }
}
```

### Create Appointment

```http
POST /appointments
```

Direct appointment creation for web portal/admin bookings.

**Request Body:** `AppointmentDirectCreate`

```json
{
  "tenant_id": "uuid",
  "patient_id": "uuid",
  "practitioner_id": "uuid",
  "location_id": "uuid",
  "time_slot_id": "uuid",
  "appointment_type": "consultation",
  "reason_text": "Annual checkup",
  "source_channel": "web"
}
```

**Response:** `AppointmentDetailResponse` (201 Created)

### Get Appointment

```http
GET /appointments/{appointment_id}
```

**Response:** `AppointmentResponse`

### Update Appointment

```http
PATCH /appointments/{appointment_id}
```

**Request Body:** `AppointmentUpdate`

**Response:** `AppointmentResponse`

### Cancel Appointment

```http
POST /appointments/{appointment_id}/cancel
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `notify_patient` | bool | true | Send cancellation notification |

**Response:** `AppointmentResponse`

### Delete Appointment

```http
DELETE /appointments/{appointment_id}
```

Permanently removes an appointment. Consider using cancel endpoint for soft delete.

**Response:** 204 No Content

### Check Appointment Conflicts

```http
GET /appointments/conflicts
```

Pre-flight check for scheduling conflicts before creating/updating appointments.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `practitioner_id` | UUID | Yes | Practitioner to check |
| `start_time` | datetime | Yes | Proposed start time |
| `end_time` | datetime | Yes | Proposed end time |
| `exclude_appointment_id` | UUID | No | Exclude this appointment (for rescheduling) |

**Response:**

```json
{
  "has_conflict": true,
  "conflict_count": 1,
  "conflicting_appointments": [
    {
      "appointment_id": "uuid",
      "patient_id": "uuid",
      "status": "booked",
      "start_time": "2024-02-01T14:00:00Z",
      "end_time": "2024-02-01T14:30:00Z"
    }
  ]
}
```

### Conversational Booking Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/appointments/find-slots` | POST | Find available slots (WhatsApp flow) |
| `/appointments/select-slot` | POST | Process slot selection reply |

---

## Journeys API

Base path: `/api/v1/prm/journeys`

Journey definitions are templates that define stages and automation for patient engagement.

### List Journeys

```http
GET /journeys
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `tenant_id` | UUID | Filter by tenant |
| `journey_type` | string | Filter by type |
| `is_default` | bool | Filter default journeys |
| `page` | int | Page number |
| `page_size` | int | Items per page |

**Response:** `JourneyListResponse`

### Create Journey

```http
POST /journeys
```

**Request Body:** `JourneyCreate`

```json
{
  "tenant_id": "uuid",
  "name": "Post-Surgery Recovery",
  "description": "Patient journey for post-surgical care",
  "journey_type": "post_procedure",
  "is_default": false,
  "trigger_conditions": {},
  "stages": [
    {
      "name": "Day 1 Check-in",
      "order_index": 1,
      "trigger_event": "manual",
      "actions": {}
    }
  ]
}
```

**Response:** `JourneyResponse` (201 Created)

### Get Journey

```http
GET /journeys/{journey_id}
```

**Response:** `JourneyResponse` (includes stages)

### Update Journey

```http
PATCH /journeys/{journey_id}
```

**Request Body:** `JourneyUpdate`

**Response:** `JourneyResponse`

### Journey Stage Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/journeys/{id}/stages` | POST | Add stage to journey |
| `/journeys/{id}/stages/{stage_id}` | PATCH | Update journey stage |

---

## Journey Instances API

Base path: `/api/v1/prm/journeys/instances` (modular) or `/api/v1/prm/instances` (legacy)

Journey instances represent active patient journeys - when a patient is placed on a journey.

### List Journey Instances

```http
GET /journeys/instances
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `patient_id` | UUID | Filter by patient |
| `journey_id` | UUID | Filter by journey definition |
| `status` | string | Filter by status (active, completed, cancelled) |
| `page` | int | Page number |
| `page_size` | int | Items per page |

**Response:** `JourneyInstanceListResponse`

### Get Journey Instance Statistics

```http
GET /journeys/instances/stats
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `tenant_id` | UUID | Filter by tenant |
| `journey_id` | UUID | Filter by journey definition |

**Response:**

```json
{
  "total": 250,
  "active": 100,
  "completed": 140,
  "cancelled": 10,
  "by_status": {
    "active": 100,
    "completed": 140,
    "cancelled": 10
  },
  "by_journey": {
    "Post-Surgery Recovery": 80,
    "New Patient Onboarding": 120
  }
}
```

### Create Journey Instance

```http
POST /journeys/instances
```

Starts a patient on a journey.

**Request Body:** `JourneyInstanceCreate`

```json
{
  "tenant_id": "uuid",
  "journey_id": "uuid",
  "patient_id": "uuid",
  "appointment_id": "uuid (optional)",
  "encounter_id": "uuid (optional)",
  "context": {}
}
```

**Response:** `JourneyInstanceResponse` (201 Created)

### Get Journey Instance

```http
GET /journeys/instances/{instance_id}
```

**Response:** `JourneyInstanceWithStages` (includes stage statuses)

### Advance Journey Stage

```http
POST /journeys/instances/{instance_id}/advance
```

Marks current stage complete and moves to next stage.

**Request Body:** `AdvanceStageRequest`

```json
{
  "notes": "Stage completed successfully"
}
```

**Response:** `JourneyInstanceResponse`

---

## Communications API

Base path: `/api/v1/prm/communications`

### List Communications

```http
GET /communications
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `patient_id` | UUID | Filter by patient |
| `journey_instance_id` | UUID | Filter by journey instance |
| `channel` | string | Filter by channel (whatsapp, sms, email) |
| `status` | string | Filter by status |
| `page` | int | Page number |
| `page_size` | int | Items per page |

**Response:** `CommunicationListResponse`

### Get Communication Statistics

```http
GET /communications/stats
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `tenant_id` | UUID | Filter by tenant |

**Response:**

```json
{
  "total": 1500,
  "by_channel": {
    "whatsapp": 800,
    "sms": 400,
    "email": 300
  },
  "by_status": {
    "sent": 1200,
    "delivered": 1100,
    "read": 900,
    "pending": 50,
    "failed": 20
  },
  "sent": 1200,
  "pending": 50,
  "failed": 20
}
```

### Create Communication

```http
POST /communications
```

**Request Body:** `CommunicationCreate`

```json
{
  "tenant_id": "uuid",
  "patient_id": "uuid",
  "journey_instance_id": "uuid (optional)",
  "channel": "whatsapp",
  "recipient": "+1234567890",
  "subject": "Appointment Reminder",
  "message": "Your appointment is tomorrow at 2pm",
  "template_name": "appointment_reminder",
  "template_vars": {},
  "scheduled_for": "2024-02-01T08:00:00Z (optional)"
}
```

**Response:** `CommunicationResponse` (201 Created)

### Get Communication

```http
GET /communications/{communication_id}
```

**Response:** `CommunicationResponse`

### Update Communication

```http
PATCH /communications/{communication_id}
```

Common uses:
- Mark as read: `status="read", read_at=now`
- Mark as delivered: `status="delivered", delivered_at=now`
- Mark as failed: `status="failed", error_message="..."`

**Request Body:** `CommunicationUpdate`

**Response:** `CommunicationResponse`

### Delete Communication

```http
DELETE /communications/{communication_id}
```

Permanently removes a communication record.

**Response:** 204 No Content

### Mark Communication as Read

```http
PATCH /communications/{communication_id}/read
```

Convenience endpoint to mark a message as read.

**Response:** `CommunicationResponse` with `status="read"` and `read_at` set

### List Communication Templates

```http
GET /communications/templates
```

Returns predefined message templates for quick replies and automation.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `tenant_id` | UUID | Filter by tenant |
| `channel` | string | Filter by channel (whatsapp, sms, email) |
| `category` | string | Filter by category (appointment, instructions, billing, etc.) |

**Response:**

```json
{
  "templates": [
    {
      "id": "apt_reminder",
      "name": "Appointment Reminder",
      "channel": "whatsapp",
      "category": "appointment",
      "subject": "Appointment Reminder",
      "body": "Hi {{patient_name}}, this is a reminder for your appointment on {{appointment_date}}...",
      "variables": ["patient_name", "appointment_date", "appointment_time", "practitioner_name"]
    }
  ],
  "total": 9,
  "channels": ["whatsapp", "sms", "email"],
  "categories": ["appointment", "instructions", "follow_up", "results", "pharmacy", "billing", "general"]
}
```

### Search Communications

```http
GET /communications/search
```

Server-side full-text search across message content.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | Search query (min 2 chars) |
| `patient_id` | UUID | No | Filter by patient |
| `channel` | string | No | Filter by channel |
| `date_from` | datetime | No | Filter from date |
| `date_to` | datetime | No | Filter to date |
| `page` | int | No | Page number (default 1) |
| `page_size` | int | No | Items per page (default 20, max 100) |

**Response:** `CommunicationListResponse`

---

## Tickets API

Base path: `/api/v1/prm/tickets`

### List Tickets

```http
GET /tickets
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `patient_id` | UUID | Filter by patient |
| `status` | string | Filter by status (open, in_progress, resolved, closed) |
| `priority` | string | Filter by priority (low, medium, high, urgent) |
| `assigned_to` | UUID | Filter by assignee |
| `page` | int | Page number |
| `page_size` | int | Items per page |

**Response:** `TicketListResponse`

### Create Ticket

```http
POST /tickets
```

**Request Body:** `TicketCreate`

```json
{
  "tenant_id": "uuid",
  "patient_id": "uuid",
  "journey_instance_id": "uuid (optional)",
  "title": "Prescription refill request",
  "description": "Patient needs refill of medication X",
  "priority": "medium",
  "category": "prescription",
  "assigned_to": "uuid (optional)"
}
```

**Response:** `TicketResponse` (201 Created)

### Get Ticket

```http
GET /tickets/{ticket_id}
```

**Response:** `TicketResponse`

### Update Ticket

```http
PATCH /tickets/{ticket_id}
```

**Request Body:** `TicketUpdate`

```json
{
  "status": "resolved",
  "resolution_notes": "Prescription refill approved and sent to pharmacy"
}
```

**Response:** `TicketResponse`

---

## Analytics API

Base path: `/api/v1/prm/analytics`

### Dashboard Overview

```http
GET /analytics/dashboard
```

Returns all metrics in a single response for dashboard loading.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `tenant_id` | UUID | Required - Tenant ID |
| `time_period` | enum | Time period (TODAY, LAST_7_DAYS, LAST_30_DAYS, etc.) |

**Response:** `DashboardOverviewResponse`

### Appointment Analytics

```http
GET /analytics/appointments
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `tenant_id` | UUID | Required |
| `time_period` | enum | Time period |
| `start_date` | string | Custom start date (YYYY-MM-DD) |
| `end_date` | string | Custom end date (YYYY-MM-DD) |
| `channel_origin` | string | Filter by channel |
| `practitioner_id` | UUID | Filter by practitioner |
| `include_breakdown` | bool | Include dimensional breakdowns |

**Response:** `AppointmentAnalyticsResponse`

### Journey Analytics

```http
GET /analytics/journeys
```

Returns journey metrics including active, completed, overdue counts.

### Communication Analytics

```http
GET /analytics/communication
```

Returns messaging metrics including response times and sentiment.

### Voice Call Analytics

```http
GET /analytics/voice-calls
```

Returns voice agent metrics including call duration and quality.

### Real-time Metrics Stream

```http
GET /analytics/realtime
```

Server-Sent Events (SSE) endpoint for real-time metric updates.

**Client Example:**

```javascript
const eventSource = new EventSource('/api/v1/prm/analytics/realtime?tenant_id=xxx');
eventSource.onmessage = (event) => {
  const metrics = JSON.parse(event.data);
  console.log('New metrics:', metrics);
};
```

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Invalid request body |
| 500 | Internal Server Error |

### Validation Errors

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Pagination

All list endpoints support pagination with consistent response format:

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "has_next": true,
  "has_previous": false
}
```

**Parameters:**

| Parameter | Type | Default | Max |
|-----------|------|---------|-----|
| `page` | int | 1 | - |
| `page_size` | int | 20 | 100 |

---

## Rate Limiting

Rate limiting may be applied based on deployment configuration. Standard limits:

- 100 requests per minute per user
- 1000 requests per minute per tenant

---

## Changelog

### v0.2.0 (Current)
- Modular architecture with separate routers
- Added patient 360 view endpoint
- Added appointment statistics and today/upcoming views
- Added journey instance statistics
- Added communication statistics
- Enhanced analytics with real-time SSE

### v0.1.0
- Initial release with core CRUD operations

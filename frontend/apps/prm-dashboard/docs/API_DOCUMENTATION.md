# PRM Dashboard - API Documentation

Complete API reference for developers integrating with the PRM Dashboard.

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Authorization](#authorization)
4. [Base URL & Versioning](#base-url--versioning)
5. [Request & Response Format](#request--response-format)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [API Endpoints](#api-endpoints)
   - [Authentication](#authentication-endpoints)
   - [Patients](#patients)
   - [Appointments](#appointments)
   - [Journeys](#journeys)
   - [Communications](#communications)
   - [Tickets](#tickets)
   - [Users](#users)
   - [Settings](#settings)
9. [Webhooks](#webhooks)
10. [Code Examples](#code-examples)
11. [SDKs](#sdks)

## Overview

The PRM Dashboard API is a RESTful API that allows you to manage patient relationships, appointments, care journeys, and communications programmatically.

**Key Features:**
- RESTful architecture
- JSON request/response format
- JWT-based authentication
- Role-based access control
- Comprehensive audit logging
- Rate limiting and security
- HIPAA-compliant data handling

**API Base URL:**
```
https://api.healthtech.com/v1
```

**Staging:**
```
https://api-staging.healthtech.com/v1
```

## Authentication

### JWT Authentication

The API uses JWT (JSON Web Tokens) for authentication. All API requests must include a valid access token.

**Authentication Flow:**

1. **Login** - Exchange credentials for tokens
2. **Include Token** - Send access token in Authorization header
3. **Refresh Token** - Use refresh token to get new access token when expired

### Login

```http
POST /auth/login
Content-Type: application/json

{
  "email": "provider@example.com",
  "password": "your-secure-password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "user_123",
    "email": "provider@example.com",
    "name": "Dr. Jane Smith",
    "role": "provider",
    "org_id": "org_456",
    "permissions": ["patient.view", "patient.create", "appointment.create"]
  }
}
```

### Using Access Token

Include the access token in the Authorization header:

```http
GET /patients
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Refresh Token

When the access token expires (after 1 hour), use the refresh token to get a new one:

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### Logout

```http
POST /auth/logout
Authorization: Bearer {access_token}
```

## Authorization

### Roles

The API supports 4 user roles:

1. **admin** - Full access to all resources
2. **provider** - Access to clinical and patient care functions
3. **staff** - Access to administrative functions
4. **patient** - Access to personal health information only

### Permissions

Fine-grained permissions control access to specific operations:

**Patient Permissions:**
- `patient.view` - View patient information
- `patient.create` - Create new patients
- `patient.update` - Update patient information
- `patient.delete` - Delete patients
- `patient.search` - Search patient database

**Appointment Permissions:**
- `appointment.view` - View appointments
- `appointment.create` - Create appointments
- `appointment.update` - Update appointments
- `appointment.cancel` - Cancel appointments
- `appointment.reschedule` - Reschedule appointments

**Journey Permissions:**
- `journey.view` - View care journeys
- `journey.create` - Create journeys
- `journey.update` - Update journeys
- `journey.complete` - Mark journeys complete

**Communication Permissions:**
- `communication.send` - Send individual messages
- `communication.view` - View message history
- `communication.bulk` - Send bulk messages

**Ticket Permissions:**
- `ticket.view` - View support tickets
- `ticket.create` - Create tickets
- `ticket.update` - Update tickets
- `ticket.assign` - Assign tickets
- `ticket.resolve` - Resolve tickets

### Permission Errors

If you don't have permission for an operation, you'll receive a 403 Forbidden response:

```json
{
  "error": "insufficient_permissions",
  "message": "You don't have permission to perform this action",
  "required_permission": "patient.delete"
}
```

## Base URL & Versioning

**Current Version:** v1

**Base URL:**
```
https://api.healthtech.com/v1
```

All endpoints are relative to this base URL. For example:
- Patients: `https://api.healthtech.com/v1/patients`
- Appointments: `https://api.healthtech.com/v1/appointments`

**Version Header (Optional):**
```http
Accept: application/vnd.healthtech.v1+json
```

## Request & Response Format

### Request Format

**Content Type:**
```http
Content-Type: application/json
```

**Request Body:**
All POST, PUT, and PATCH requests should include a JSON body:

```json
{
  "name": "John Doe",
  "email": "john@example.com"
}
```

**Query Parameters:**
For filtering, pagination, and sorting:

```http
GET /patients?page=1&limit=20&sort=created_at:desc&status=active
```

### Response Format

**Success Response:**
```json
{
  "success": true,
  "data": {
    "id": "patient_123",
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

**List Response (with pagination):**
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "total_pages": 8
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "validation_error",
  "message": "Invalid input data",
  "details": {
    "email": "Invalid email format",
    "phone": "Phone number is required"
  }
}
```

### Date/Time Format

All dates and times are in ISO 8601 format with UTC timezone:

```json
{
  "created_at": "2024-11-19T10:30:00Z",
  "updated_at": "2024-11-19T15:45:00Z",
  "date_of_birth": "1990-05-15"
}
```

## Error Handling

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 204 | No Content - Request successful, no response body |
| 400 | Bad Request - Invalid input data |
| 401 | Unauthorized - Authentication required or failed |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 409 | Conflict - Resource already exists or conflict |
| 422 | Unprocessable Entity - Validation failed |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |
| 503 | Service Unavailable - Temporary unavailability |

### Error Response Format

```json
{
  "success": false,
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field": "Specific field error"
  },
  "request_id": "req_abc123"
}
```

### Common Error Codes

| Error Code | Description |
|------------|-------------|
| `validation_error` | Input validation failed |
| `authentication_required` | No authentication token provided |
| `invalid_token` | Token is invalid or expired |
| `insufficient_permissions` | User lacks required permissions |
| `resource_not_found` | Requested resource doesn't exist |
| `resource_conflict` | Resource already exists or conflict |
| `rate_limit_exceeded` | Too many requests |
| `internal_error` | Internal server error |

## Rate Limiting

### Limits

**Authentication Endpoints:**
- Login: 5 attempts per 15 minutes per email
- Password Reset: 3 attempts per hour per email

**API Endpoints:**
- Standard: 100 requests per minute per user
- Bulk operations: 10 requests per minute per user
- Search: 50 requests per minute per user

### Rate Limit Headers

Every API response includes rate limit information:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1700000000
```

### Rate Limit Exceeded

When rate limit is exceeded, you'll receive a 429 response:

```json
{
  "success": false,
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again later.",
  "retry_after": 60
}
```

## API Endpoints

### Authentication Endpoints

#### POST /auth/login

Authenticate user and receive access tokens.

**Request:**
```json
{
  "email": "provider@example.com",
  "password": "secure-password"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc...",
    "expires_in": 3600,
    "user": { ... }
  }
}
```

#### POST /auth/refresh

Refresh access token using refresh token.

**Request:**
```json
{
  "refresh_token": "eyJhbGc..."
}
```

#### POST /auth/logout

Invalidate current session.

#### POST /auth/forgot-password

Request password reset.

**Request:**
```json
{
  "email": "provider@example.com"
}
```

#### POST /auth/reset-password

Reset password with token.

**Request:**
```json
{
  "token": "reset_token_here",
  "password": "new-secure-password"
}
```

---

### Patients

#### GET /patients

List all patients with pagination and filtering.

**Query Parameters:**
- `page` (number) - Page number (default: 1)
- `limit` (number) - Results per page (default: 20, max: 100)
- `sort` (string) - Sort field and order (e.g., `created_at:desc`)
- `search` (string) - Search by name, email, or phone
- `status` (string) - Filter by status: `active`, `inactive`

**Example Request:**
```http
GET /patients?page=1&limit=20&search=john&sort=name:asc
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "patient_123",
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+1-555-123-4567",
      "date_of_birth": "1985-03-15",
      "gender": "male",
      "address": "123 Main St, City, State 12345",
      "status": "active",
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "total_pages": 8
  }
}
```

**Required Permission:** `patient.view` or `patient.search`

#### GET /patients/:id

Get a specific patient by ID.

**Example Request:**
```http
GET /patients/patient_123
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "patient_123",
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-123-4567",
    "date_of_birth": "1985-03-15",
    "gender": "male",
    "address": "123 Main St, City, State 12345",
    "emergency_contact": {
      "name": "Jane Doe",
      "phone": "+1-555-987-6543",
      "relationship": "spouse"
    },
    "medical_info": {
      "blood_type": "O+",
      "allergies": ["penicillin"],
      "conditions": ["hypertension"]
    },
    "status": "active",
    "created_at": "2024-01-15T10:00:00Z",
    "updated_at": "2024-01-15T10:00:00Z"
  }
}
```

**Required Permission:** `patient.view`

#### POST /patients

Create a new patient.

**Request:**
```json
{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "phone": "+1-555-234-5678",
  "date_of_birth": "1992-07-20",
  "gender": "female",
  "address": "456 Oak Ave, City, State 12345",
  "emergency_contact": {
    "name": "John Smith",
    "phone": "+1-555-876-5432",
    "relationship": "husband"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "patient_456",
    "name": "Jane Smith",
    ...
  }
}
```

**Required Permission:** `patient.create`

#### PATCH /patients/:id

Update patient information.

**Request:**
```json
{
  "phone": "+1-555-999-8888",
  "email": "jane.new@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "patient_456",
    "phone": "+1-555-999-8888",
    "email": "jane.new@example.com",
    ...
  }
}
```

**Required Permission:** `patient.update`

#### DELETE /patients/:id

Delete a patient (soft delete).

**Response:**
```json
{
  "success": true,
  "message": "Patient deleted successfully"
}
```

**Required Permission:** `patient.delete`

---

### Appointments

#### GET /appointments

List all appointments with filtering.

**Query Parameters:**
- `page`, `limit`, `sort` - Pagination parameters
- `patient_id` (string) - Filter by patient
- `provider_id` (string) - Filter by provider
- `status` (string) - Filter by status: `scheduled`, `completed`, `cancelled`, `no_show`
- `date_from` (date) - Filter appointments from date
- `date_to` (date) - Filter appointments to date

**Example Request:**
```http
GET /appointments?patient_id=patient_123&status=scheduled&date_from=2024-11-20
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "appt_789",
      "patient_id": "patient_123",
      "patient_name": "John Doe",
      "provider_id": "provider_456",
      "provider_name": "Dr. Jane Smith",
      "appointment_type": "checkup",
      "scheduled_at": "2024-11-25T14:00:00Z",
      "duration_minutes": 30,
      "status": "scheduled",
      "notes": "Annual checkup",
      "created_at": "2024-11-19T10:00:00Z",
      "updated_at": "2024-11-19T10:00:00Z"
    }
  ],
  "pagination": { ... }
}
```

**Required Permission:** `appointment.view`

#### GET /appointments/:id

Get a specific appointment.

**Required Permission:** `appointment.view`

#### POST /appointments

Create a new appointment.

**Request:**
```json
{
  "patient_id": "patient_123",
  "provider_id": "provider_456",
  "appointment_type": "consultation",
  "scheduled_at": "2024-11-25T14:00:00Z",
  "duration_minutes": 45,
  "notes": "Follow-up consultation"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "appt_890",
    "patient_id": "patient_123",
    "scheduled_at": "2024-11-25T14:00:00Z",
    "status": "scheduled",
    ...
  }
}
```

**Required Permission:** `appointment.create`

#### PATCH /appointments/:id

Update an appointment.

**Request:**
```json
{
  "scheduled_at": "2024-11-26T10:00:00Z",
  "notes": "Rescheduled per patient request"
}
```

**Required Permission:** `appointment.update` or `appointment.reschedule`

#### POST /appointments/:id/cancel

Cancel an appointment.

**Request:**
```json
{
  "reason": "Patient requested cancellation",
  "notify_patient": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "appt_890",
    "status": "cancelled",
    "cancelled_at": "2024-11-19T16:00:00Z",
    "cancellation_reason": "Patient requested cancellation"
  }
}
```

**Required Permission:** `appointment.cancel`

---

### Journeys

#### GET /journeys

List all care journeys.

**Query Parameters:**
- `page`, `limit`, `sort` - Pagination parameters
- `patient_id` (string) - Filter by patient
- `type` (string) - Filter by journey type
- `status` (string) - Filter by status: `active`, `completed`, `cancelled`

**Example Request:**
```http
GET /journeys?patient_id=patient_123&status=active
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "journey_101",
      "patient_id": "patient_123",
      "patient_name": "John Doe",
      "type": "post_surgery",
      "title": "Post-Surgery Recovery",
      "description": "Recovery journey after knee surgery",
      "status": "active",
      "progress_percentage": 60,
      "steps": [
        {
          "id": "step_1",
          "title": "First follow-up appointment",
          "description": "Check incision and overall recovery",
          "due_date": "2024-11-20",
          "completed": true,
          "completed_at": "2024-11-20T14:00:00Z"
        },
        {
          "id": "step_2",
          "title": "Physical therapy session 1",
          "description": "Begin physical therapy exercises",
          "due_date": "2024-11-25",
          "completed": false,
          "completed_at": null
        }
      ],
      "created_at": "2024-11-10T10:00:00Z",
      "updated_at": "2024-11-19T10:00:00Z"
    }
  ],
  "pagination": { ... }
}
```

**Required Permission:** `journey.view`

#### GET /journeys/:id

Get a specific journey with all steps.

**Required Permission:** `journey.view`

#### POST /journeys

Create a new care journey.

**Request:**
```json
{
  "patient_id": "patient_123",
  "type": "chronic_disease",
  "title": "Diabetes Management",
  "description": "6-month diabetes management journey",
  "steps": [
    {
      "title": "Initial consultation",
      "description": "Meet with endocrinologist",
      "due_date": "2024-12-01"
    },
    {
      "title": "Diet plan review",
      "description": "Meet with nutritionist",
      "due_date": "2024-12-08"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "journey_102",
    "patient_id": "patient_123",
    "type": "chronic_disease",
    "status": "active",
    ...
  }
}
```

**Required Permission:** `journey.create`

#### PATCH /journeys/:id

Update a journey.

**Required Permission:** `journey.update`

#### POST /journeys/:id/steps/:step_id/complete

Mark a journey step as complete.

**Request:**
```json
{
  "notes": "Patient completed physical therapy session successfully"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "step_2",
    "completed": true,
    "completed_at": "2024-11-25T15:00:00Z",
    "notes": "Patient completed physical therapy session successfully"
  }
}
```

**Required Permission:** `journey.update`

#### POST /journeys/:id/complete

Mark entire journey as complete.

**Required Permission:** `journey.complete`

---

### Communications

#### GET /communications

List all communications.

**Query Parameters:**
- `page`, `limit`, `sort` - Pagination parameters
- `patient_id` (string) - Filter by patient
- `channel` (string) - Filter by channel: `whatsapp`, `sms`, `email`
- `status` (string) - Filter by status: `sent`, `delivered`, `failed`, `pending`
- `date_from` (date) - Filter from date
- `date_to` (date) - Filter to date

**Example Request:**
```http
GET /communications?patient_id=patient_123&channel=whatsapp&status=delivered
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "comm_201",
      "patient_id": "patient_123",
      "patient_name": "John Doe",
      "channel": "whatsapp",
      "message": "Your appointment is confirmed for tomorrow at 2 PM.",
      "status": "delivered",
      "sent_at": "2024-11-19T10:00:00Z",
      "delivered_at": "2024-11-19T10:00:05Z",
      "sent_by": "provider_456",
      "sent_by_name": "Dr. Jane Smith"
    }
  ],
  "pagination": { ... }
}
```

**Required Permission:** `communication.view`

#### POST /communications/send

Send a message to a patient.

**Request:**
```json
{
  "patient_id": "patient_123",
  "channel": "whatsapp",
  "message": "Reminder: Your appointment is tomorrow at 2 PM. Please arrive 10 minutes early.",
  "template_id": "appointment_reminder" // Optional: use predefined template
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "comm_202",
    "patient_id": "patient_123",
    "channel": "whatsapp",
    "status": "sent",
    "sent_at": "2024-11-19T16:00:00Z"
  }
}
```

**Required Permission:** `communication.send`

#### POST /communications/send-bulk

Send messages to multiple patients.

**Request:**
```json
{
  "patient_ids": ["patient_123", "patient_456", "patient_789"],
  "channel": "sms",
  "message": "Our office will be closed on Friday, November 29th for the holiday.",
  "template_id": "office_closure"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "batch_id": "batch_301",
    "total": 3,
    "sent": 3,
    "failed": 0,
    "status": "completed"
  }
}
```

**Required Permission:** `communication.bulk`

**Note:** Bulk communications require additional confirmation and have stricter rate limits.

---

### Tickets

#### GET /tickets

List all support tickets.

**Query Parameters:**
- `page`, `limit`, `sort` - Pagination parameters
- `patient_id` (string) - Filter by patient
- `category` (string) - Filter by category: `billing`, `appointment`, `medical`, `technical`, `general`
- `priority` (string) - Filter by priority: `low`, `medium`, `high`, `urgent`
- `status` (string) - Filter by status: `open`, `in_progress`, `resolved`, `closed`
- `assigned_to` (string) - Filter by assigned user

**Example Request:**
```http
GET /tickets?status=open&priority=high
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "ticket_401",
      "patient_id": "patient_123",
      "patient_name": "John Doe",
      "category": "billing",
      "priority": "high",
      "status": "open",
      "title": "Question about recent bill",
      "description": "I received a bill for $500 but my insurance should have covered this.",
      "assigned_to": "staff_789",
      "assigned_to_name": "Sarah Johnson",
      "created_at": "2024-11-19T09:00:00Z",
      "updated_at": "2024-11-19T09:00:00Z",
      "comments_count": 2
    }
  ],
  "pagination": { ... }
}
```

**Required Permission:** `ticket.view`

#### GET /tickets/:id

Get a specific ticket with all comments.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "ticket_401",
    "patient_id": "patient_123",
    "category": "billing",
    "priority": "high",
    "status": "in_progress",
    "title": "Question about recent bill",
    "description": "I received a bill for $500 but my insurance should have covered this.",
    "assigned_to": "staff_789",
    "comments": [
      {
        "id": "comment_1",
        "author_id": "staff_789",
        "author_name": "Sarah Johnson",
        "content": "I'm looking into this now. Will check with insurance.",
        "created_at": "2024-11-19T10:00:00Z"
      },
      {
        "id": "comment_2",
        "author_id": "patient_123",
        "author_name": "John Doe",
        "content": "Thank you! My policy number is ABC123456.",
        "created_at": "2024-11-19T11:00:00Z"
      }
    ],
    "created_at": "2024-11-19T09:00:00Z",
    "updated_at": "2024-11-19T11:00:00Z"
  }
}
```

**Required Permission:** `ticket.view`

#### POST /tickets

Create a new support ticket.

**Request:**
```json
{
  "patient_id": "patient_456",
  "category": "appointment",
  "priority": "medium",
  "title": "Need to reschedule appointment",
  "description": "I need to reschedule my appointment on Nov 25th to a later date.",
  "assigned_to": "staff_789" // Optional
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "ticket_402",
    "patient_id": "patient_456",
    "category": "appointment",
    "priority": "medium",
    "status": "open",
    ...
  }
}
```

**Required Permission:** `ticket.create`

#### POST /tickets/:id/comments

Add a comment to a ticket.

**Request:**
```json
{
  "content": "I've rescheduled your appointment to December 5th at 2 PM."
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "comment_3",
    "ticket_id": "ticket_402",
    "author_id": "staff_789",
    "content": "I've rescheduled your appointment to December 5th at 2 PM.",
    "created_at": "2024-11-19T14:00:00Z"
  }
}
```

**Required Permission:** `ticket.update`

#### PATCH /tickets/:id

Update ticket status, priority, or assignment.

**Request:**
```json
{
  "status": "resolved",
  "priority": "low",
  "assigned_to": "staff_999"
}
```

**Required Permission:** `ticket.update` or `ticket.assign`

#### POST /tickets/:id/resolve

Resolve a ticket.

**Request:**
```json
{
  "resolution": "Appointment rescheduled successfully. Patient confirmed new date."
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "ticket_402",
    "status": "resolved",
    "resolved_at": "2024-11-19T15:00:00Z",
    "resolution": "Appointment rescheduled successfully. Patient confirmed new date."
  }
}
```

**Required Permission:** `ticket.resolve`

---

### Users

#### GET /users

List all users in the organization (Admin only).

**Query Parameters:**
- `page`, `limit`, `sort` - Pagination parameters
- `role` (string) - Filter by role
- `status` (string) - Filter by status: `active`, `inactive`
- `department` (string) - Filter by department

**Required Permission:** `admin` role

#### GET /users/:id

Get a specific user.

**Required Permission:** `admin` role or own user ID

#### POST /users

Create a new user (Admin only).

**Request:**
```json
{
  "email": "newprovider@example.com",
  "name": "Dr. John Smith",
  "role": "provider",
  "department": "Cardiology",
  "permissions": ["patient.view", "patient.create", "appointment.create"]
}
```

**Required Permission:** `admin` role

#### PATCH /users/:id

Update user information.

**Required Permission:** `admin` role or own user ID (limited fields)

#### DELETE /users/:id

Deactivate a user.

**Required Permission:** `admin` role

---

### Settings

#### GET /settings/organization

Get organization settings.

**Response:**
```json
{
  "success": true,
  "data": {
    "name": "HealthTech Clinic",
    "timezone": "America/New_York",
    "date_format": "MM/DD/YYYY",
    "time_format": "12h",
    "language": "en",
    "logo_url": "https://cdn.healthtech.com/logo.png"
  }
}
```

**Required Permission:** `admin` role

#### PATCH /settings/organization

Update organization settings.

**Required Permission:** `admin` role

#### GET /settings/ai

Get AI assistant configuration.

**Required Permission:** `admin` role

#### PATCH /settings/ai

Update AI assistant settings.

**Request:**
```json
{
  "enabled": true,
  "auto_suggestions": true,
  "require_confirmation": true,
  "max_retries": 3
}
```

**Required Permission:** `admin` role

## Webhooks

Webhooks allow you to receive real-time notifications when events occur in the PRM Dashboard.

### Setting Up Webhooks

1. Navigate to Settings → Webhooks (Admin only)
2. Click "Add Webhook"
3. Enter your endpoint URL (must be HTTPS)
4. Select events to subscribe to
5. Set a secret for signature verification
6. Test the webhook
7. Save

### Webhook Events

**Patient Events:**
- `patient.created` - New patient created
- `patient.updated` - Patient information updated
- `patient.deleted` - Patient deleted

**Appointment Events:**
- `appointment.created` - New appointment created
- `appointment.updated` - Appointment updated
- `appointment.cancelled` - Appointment cancelled
- `appointment.completed` - Appointment marked complete
- `appointment.no_show` - Appointment marked as no-show

**Journey Events:**
- `journey.created` - New journey created
- `journey.step_completed` - Journey step completed
- `journey.completed` - Journey completed

**Communication Events:**
- `communication.sent` - Message sent
- `communication.delivered` - Message delivered
- `communication.failed` - Message failed

**Ticket Events:**
- `ticket.created` - New ticket created
- `ticket.updated` - Ticket updated
- `ticket.resolved` - Ticket resolved
- `ticket.comment_added` - Comment added to ticket

### Webhook Payload

All webhooks include a standard payload format:

```json
{
  "event": "appointment.created",
  "timestamp": "2024-11-19T16:00:00Z",
  "data": {
    "id": "appt_999",
    "patient_id": "patient_123",
    "scheduled_at": "2024-11-25T14:00:00Z",
    ...
  },
  "organization_id": "org_456"
}
```

### Verifying Webhook Signatures

All webhooks include a signature header for security:

```
X-Webhook-Signature: sha256=abc123...
```

**Verification (Node.js):**
```javascript
const crypto = require('crypto');

function verifyWebhookSignature(payload, signature, secret) {
  const hmac = crypto.createHmac('sha256', secret);
  const digest = 'sha256=' + hmac.update(payload).digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(digest)
  );
}

// In your webhook handler
app.post('/webhook', (req, res) => {
  const signature = req.headers['x-webhook-signature'];
  const payload = JSON.stringify(req.body);

  if (!verifyWebhookSignature(payload, signature, WEBHOOK_SECRET)) {
    return res.status(401).send('Invalid signature');
  }

  // Process webhook
  const { event, data } = req.body;
  // ...

  res.status(200).send('OK');
});
```

### Webhook Retry Policy

If your endpoint fails to respond with a 2xx status code:
- First retry: After 1 minute
- Second retry: After 5 minutes
- Third retry: After 15 minutes
- After 3 failed attempts, webhook is marked as failed

## Code Examples

### JavaScript/TypeScript

```typescript
import axios from 'axios';

const API_BASE_URL = 'https://api.healthtech.com/v1';
let accessToken = '';

// Login
async function login(email: string, password: string) {
  const response = await axios.post(`${API_BASE_URL}/auth/login`, {
    email,
    password
  });

  accessToken = response.data.data.access_token;
  return response.data.data;
}

// Create API client with auth
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add auth token to requests
api.interceptors.request.use(config => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

// Get patients
async function getPatients(params?: {
  page?: number;
  limit?: number;
  search?: string;
}) {
  const response = await api.get('/patients', { params });
  return response.data.data;
}

// Create patient
async function createPatient(patient: {
  name: string;
  email: string;
  phone: string;
  date_of_birth: string;
}) {
  const response = await api.post('/patients', patient);
  return response.data.data;
}

// Book appointment
async function bookAppointment(appointment: {
  patient_id: string;
  provider_id: string;
  scheduled_at: string;
  duration_minutes: number;
}) {
  const response = await api.post('/appointments', appointment);
  return response.data.data;
}

// Send communication
async function sendMessage(
  patientId: string,
  channel: 'whatsapp' | 'sms' | 'email',
  message: string
) {
  const response = await api.post('/communications/send', {
    patient_id: patientId,
    channel,
    message
  });
  return response.data.data;
}

// Example usage
async function main() {
  try {
    // Login
    await login('provider@example.com', 'password');

    // Get patients
    const patients = await getPatients({ page: 1, limit: 10 });
    console.log('Patients:', patients);

    // Create patient
    const newPatient = await createPatient({
      name: 'John Doe',
      email: 'john@example.com',
      phone: '+1-555-123-4567',
      date_of_birth: '1985-03-15'
    });
    console.log('Created patient:', newPatient);

    // Book appointment
    const appointment = await bookAppointment({
      patient_id: newPatient.id,
      provider_id: 'provider_123',
      scheduled_at: '2024-11-25T14:00:00Z',
      duration_minutes: 30
    });
    console.log('Booked appointment:', appointment);

    // Send reminder
    await sendMessage(
      newPatient.id,
      'whatsapp',
      'Your appointment is confirmed for Nov 25 at 2 PM'
    );

  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
  }
}
```

### Python

```python
import requests
from typing import Optional, Dict, Any

API_BASE_URL = 'https://api.healthtech.com/v1'

class PRMClient:
    def __init__(self):
        self.access_token: Optional[str] = None
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate and get access token"""
        response = self.session.post(
            f'{API_BASE_URL}/auth/login',
            json={'email': email, 'password': password}
        )
        response.raise_for_status()

        data = response.json()['data']
        self.access_token = data['access_token']
        self.session.headers.update({
            'Authorization': f'Bearer {self.access_token}'
        })
        return data

    def get_patients(self, **params) -> list:
        """Get list of patients"""
        response = self.session.get(f'{API_BASE_URL}/patients', params=params)
        response.raise_for_status()
        return response.json()['data']

    def create_patient(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new patient"""
        response = self.session.post(
            f'{API_BASE_URL}/patients',
            json=patient_data
        )
        response.raise_for_status()
        return response.json()['data']

    def book_appointment(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Book a new appointment"""
        response = self.session.post(
            f'{API_BASE_URL}/appointments',
            json=appointment_data
        )
        response.raise_for_status()
        return response.json()['data']

    def send_message(
        self,
        patient_id: str,
        channel: str,
        message: str
    ) -> Dict[str, Any]:
        """Send a message to a patient"""
        response = self.session.post(
            f'{API_BASE_URL}/communications/send',
            json={
                'patient_id': patient_id,
                'channel': channel,
                'message': message
            }
        )
        response.raise_for_status()
        return response.json()['data']

# Example usage
def main():
    client = PRMClient()

    try:
        # Login
        client.login('provider@example.com', 'password')

        # Get patients
        patients = client.get_patients(page=1, limit=10)
        print(f'Found {len(patients)} patients')

        # Create patient
        new_patient = client.create_patient({
            'name': 'Jane Doe',
            'email': 'jane@example.com',
            'phone': '+1-555-234-5678',
            'date_of_birth': '1992-07-20'
        })
        print(f'Created patient: {new_patient["id"]}')

        # Book appointment
        appointment = client.book_appointment({
            'patient_id': new_patient['id'],
            'provider_id': 'provider_123',
            'scheduled_at': '2024-11-25T14:00:00Z',
            'duration_minutes': 30
        })
        print(f'Booked appointment: {appointment["id"]}')

        # Send reminder
        client.send_message(
            new_patient['id'],
            'whatsapp',
            'Your appointment is confirmed for Nov 25 at 2 PM'
        )

    except requests.HTTPError as e:
        print(f'HTTP Error: {e.response.status_code}')
        print(e.response.json())
    except Exception as e:
        print(f'Error: {str(e)}')

if __name__ == '__main__':
    main()
```

### cURL

```bash
# Login
curl -X POST https://api.healthtech.com/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "provider@example.com",
    "password": "password"
  }'

# Get patients (with token)
curl -X GET "https://api.healthtech.com/v1/patients?page=1&limit=10" \
  -H "Authorization: Bearer eyJhbGc..."

# Create patient
curl -X POST https://api.healthtech.com/v1/patients \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1-555-123-4567",
    "date_of_birth": "1985-03-15"
  }'

# Book appointment
curl -X POST https://api.healthtech.com/v1/appointments \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient_123",
    "provider_id": "provider_456",
    "scheduled_at": "2024-11-25T14:00:00Z",
    "duration_minutes": 30
  }'

# Send message
curl -X POST https://api.healthtech.com/v1/communications/send \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient_123",
    "channel": "whatsapp",
    "message": "Your appointment is confirmed for Nov 25 at 2 PM"
  }'
```

## SDKs

### Official SDKs

**JavaScript/TypeScript:**
```bash
npm install @healthtech/prm-sdk
```

**Python:**
```bash
pip install healthtech-prm
```

**Go:**
```bash
go get github.com/healthtech/prm-go
```

### Community SDKs

- Ruby: `gem install healthtech-prm`
- PHP: `composer require healthtech/prm`
- Java: Available on Maven Central

### SDK Documentation

For detailed SDK documentation, visit:
- https://docs.healthtech.com/sdks/javascript
- https://docs.healthtech.com/sdks/python
- https://docs.healthtech.com/sdks/go

## Support

**Documentation:** https://docs.healthtech.com/api
**Status Page:** https://status.healthtech.com
**Support Email:** api-support@healthtech.com
**Developer Forum:** https://forum.healthtech.com

**API Changelog:** https://docs.healthtech.com/changelog

---

**Last Updated:** November 19, 2024
**API Version:** v1
**For:** Developers and Integration Partners

**Questions?** Contact our API support team at api-support@healthtech.com

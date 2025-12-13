# PRM Dashboard - API Mapping Guide

> Maps every frontend dashboard component to its required backend API endpoint

**Last Updated:** December 2024
**Status:** All APIs Implemented

---

## Quick Reference

| Dashboard Page | API Status | Notes |
|----------------|------------|-------|
| Home Dashboard | ✅ Complete | All stats and widgets connected |
| Appointments | ✅ Complete | Full calendar, stats, CRUD |
| Patients | ✅ Complete | List, search, 360 view, CRUD |
| Inbox | ✅ Complete | Multi-channel messaging |
| Journeys | ✅ Complete | Definitions and instances |
| Tickets | ✅ Complete | Full ticket management |
| Communications | ✅ Complete | Stats and messaging |
| Analytics | ✅ Complete | Dashboard and domain analytics |

---

## 1. Dashboard (Home) `/dashboard`

The main dashboard aggregates data from multiple domains.

### Stats Cards

| UI Component | Data Required | API Endpoint | Status |
|:-------------|:--------------|:-------------|:-------|
| **Today's Appointments** | Count of appointments today | `GET /api/v1/prm/appointments/stats` | ✅ Available |
| **Active Journeys** | Count of active journey instances | `GET /api/v1/prm/journeys/instances/stats` | ✅ Available |
| **Messages Sent** | Count of communications | `GET /api/v1/prm/communications/stats` | ✅ Available |
| **Pending Tickets** | Count of open tickets | `GET /api/v1/prm/tickets?status=open` | ✅ Available |

### Lists & Widgets

| UI Component | Data Required | API Endpoint | Status |
|:-------------|:--------------|:-------------|:-------|
| **Upcoming Appointments** | List of next N appointments | `GET /api/v1/prm/appointments/upcoming?limit=5` | ✅ Available |
| **Recent Communications** | List of last N messages | `GET /api/v1/prm/communications?page_size=5` | ✅ Available |
| **Active Journey Instances** | Currently active journeys | `GET /api/v1/prm/journeys/instances?status=active` | ✅ Available |

### Implementation Example

```typescript
// Dashboard data fetching
async function loadDashboardData() {
  const [
    appointmentStats,
    journeyStats,
    commStats,
    upcomingAppointments,
    recentComms
  ] = await Promise.all([
    api.get('/appointments/stats'),
    api.get('/journeys/instances/stats'),
    api.get('/communications/stats'),
    api.get('/appointments/upcoming?limit=5'),
    api.get('/communications?page_size=5')
  ]);

  return {
    todayAppointments: appointmentStats.today,
    activeJourneys: journeyStats.active,
    messagesSent: commStats.sent,
    pendingTickets: await api.get('/tickets?status=open').then(r => r.total),
    upcomingAppointments,
    recentCommunications: recentComms.items
  };
}
```

---

## 2. Appointments Page `/dashboard/appointments`

### Endpoints Used

| Feature | API Endpoint | Method | Status |
|:--------|:-------------|:-------|:-------|
| Calendar View | `/appointments?start_date=..&end_date=..` | GET | ✅ Available |
| Today's List | `/appointments/today` | GET | ✅ Available |
| Upcoming List | `/appointments/upcoming` | GET | ✅ Available |
| Statistics | `/appointments/stats` | GET | ✅ Available |
| Create Appointment | `/appointments` | POST | ✅ Available |
| Get Appointment | `/appointments/{id}` | GET | ✅ Available |
| Update Appointment | `/appointments/{id}` | PATCH | ✅ Available |
| Cancel Appointment | `/appointments/{id}/cancel` | POST | ✅ Available |

### Response Formats

**Statistics Response:**
```json
{
  "total": 500,
  "today": 25,
  "upcoming": 150,
  "completed": 300,
  "cancelled": 40,
  "no_show": 10,
  "by_status": {"booked": 150, "completed": 300},
  "by_type": {"consultation": 200, "follow_up": 150}
}
```

**Today's Appointments Response:**
```json
[
  {
    "id": "uuid",
    "patient_id": "uuid",
    "patient_name": "John Doe",
    "practitioner_name": "Dr. Smith",
    "location_name": "Main Clinic",
    "scheduled_date": "2024-01-15T09:00:00Z",
    "scheduled_end": "2024-01-15T09:30:00Z",
    "status": "booked",
    "appointment_type": "consultation"
  }
]
```

---

## 3. Patients Page `/dashboard/patients`

### Endpoints Used

| Feature | API Endpoint | Method | Status |
|:--------|:-------------|:-------|:-------|
| Patient List | `/patients` | GET | ✅ Available |
| Search Patients | `/patients/search` | GET | ✅ Available |
| Patient Details | `/patients/{id}` | GET | ✅ Available |
| Patient 360 View | `/patients/{id}/360` | GET | ✅ Available |
| Create Patient | `/patients` | POST | ✅ Available |
| Update Patient | `/patients/{id}` | PATCH | ✅ Available |
| Delete Patient | `/patients/{id}` | DELETE | ✅ Available |
| Demographics Stats | `/patients/stats/demographics` | GET | ✅ Available |

### Search Types

```typescript
// Quick search by type
GET /patients/search?query=john&type=name
GET /patients/search?query=555&type=phone
GET /patients/search?query=MRN123&type=mrn
GET /patients/search?query=john@email.com&type=email
```

### 360 View Response

```json
{
  "patient": {
    "id": "uuid",
    "first_name": "John",
    "last_name": "Doe",
    "phone_primary": "+1234567890",
    "email_primary": "john@example.com"
  },
  "appointments": [
    {"id": "uuid", "scheduled_at": "...", "status": "completed"}
  ],
  "journeys": [
    {"id": "uuid", "journey_id": "uuid", "status": "active"}
  ],
  "tickets": [
    {"id": "uuid", "title": "...", "status": "open"}
  ],
  "communications": [
    {"id": "uuid", "channel": "whatsapp", "direction": "outbound"}
  ],
  "total_appointments": 25,
  "upcoming_appointments": 2,
  "active_journeys": 1,
  "open_tickets": 0,
  "recent_communications": 15,
  "last_visit_date": "2024-01-10T14:00:00Z",
  "next_appointment_date": "2024-02-01T09:00:00Z"
}
```

---

## 4. Inbox Page `/dashboard/inbox`

### Endpoints Used

| Feature | API Endpoint | Method | Status |
|:--------|:-------------|:-------|:-------|
| Message Feed | `/communications` | GET | ✅ Available |
| Filter by Channel | `/communications?channel=whatsapp` | GET | ✅ Available |
| Filter by Patient | `/communications?patient_id=uuid` | GET | ✅ Available |
| Get Single Message | `/communications/{id}` | GET | ✅ Available |
| Mark as Read | `/communications/{id}` | PATCH | ✅ Available |
| Send Reply | `/communications` | POST | ✅ Available |
| Statistics | `/communications/stats` | GET | ✅ Available |

### Mark as Read Example

```typescript
await api.patch(`/communications/${messageId}`, {
  status: 'read',
  read_at: new Date().toISOString()
});
```

---

## 5. Journeys Page `/dashboard/journeys`

### Endpoints Used

| Feature | API Endpoint | Method | Status |
|:--------|:-------------|:-------|:-------|
| Journey Definitions | `/journeys` | GET | ✅ Available |
| Create Journey | `/journeys` | POST | ✅ Available |
| Get Journey | `/journeys/{id}` | GET | ✅ Available |
| Update Journey | `/journeys/{id}` | PATCH | ✅ Available |
| Add Stage | `/journeys/{id}/stages` | POST | ✅ Available |
| Instance List | `/journeys/instances` | GET | ✅ Available |
| Instance Stats | `/journeys/instances/stats` | GET | ✅ Available |
| Create Instance | `/journeys/instances` | POST | ✅ Available |
| Advance Stage | `/journeys/instances/{id}/advance` | POST | ✅ Available |

### Journey Definition vs Instance

- **Journey Definition**: Template with stages (e.g., "Post-Surgery Recovery")
- **Journey Instance**: Active patient journey (e.g., "John Doe on Post-Surgery Recovery")

```typescript
// Get journey templates
const definitions = await api.get('/journeys');

// Get active patient journeys
const instances = await api.get('/journeys/instances?status=active');

// Get stats for dashboard card
const stats = await api.get('/journeys/instances/stats');
// Returns: { total: 250, active: 100, completed: 140, cancelled: 10 }
```

---

## 6. Tickets Page `/dashboard/tickets`

### Endpoints Used

| Feature | API Endpoint | Method | Status |
|:--------|:-------------|:-------|:-------|
| Ticket Board | `/tickets` | GET | ✅ Available |
| Filter by Status | `/tickets?status=open` | GET | ✅ Available |
| Filter by Priority | `/tickets?priority=high` | GET | ✅ Available |
| Get Ticket | `/tickets/{id}` | GET | ✅ Available |
| Create Ticket | `/tickets` | POST | ✅ Available |
| Update Status | `/tickets/{id}` | PATCH | ✅ Available |

### Ticket Status Flow

```
open -> in_progress -> resolved -> closed
                   \-> cancelled
```

### Update Ticket Status Example

```typescript
await api.patch(`/tickets/${ticketId}`, {
  status: 'resolved',
  resolution_notes: 'Issue resolved by...'
});
```

---

## 7. Communications Page `/dashboard/communications`

### Endpoints Used

| Feature | API Endpoint | Method | Status |
|:--------|:-------------|:-------|:-------|
| All Messages | `/communications` | GET | ✅ Available |
| Statistics | `/communications/stats` | GET | ✅ Available |
| Send Message | `/communications` | POST | ✅ Available |
| Filter by Channel | `/communications?channel=sms` | GET | ✅ Available |

### Supported Channels

- `whatsapp`
- `sms`
- `email`
- `voice`
- `push`

---

## 8. Analytics Page `/dashboard/analytics`

### Endpoints Used

| Feature | API Endpoint | Method | Status |
|:--------|:-------------|:-------|:-------|
| Dashboard Overview | `/analytics/dashboard` | GET | ✅ Available |
| Appointment Analytics | `/analytics/appointments` | GET | ✅ Available |
| Journey Analytics | `/analytics/journeys` | GET | ✅ Available |
| Communication Analytics | `/analytics/communication` | GET | ✅ Available |
| Voice Call Analytics | `/analytics/voice-calls` | GET | ✅ Available |
| Real-time Stream | `/analytics/realtime` | GET (SSE) | ✅ Available |

### Time Periods

Available `time_period` values:
- `TODAY`
- `YESTERDAY`
- `LAST_7_DAYS`
- `LAST_30_DAYS`
- `THIS_MONTH`
- `LAST_MONTH`
- `THIS_QUARTER`
- `CUSTOM` (requires `start_date` and `end_date`)

---

## Frontend Integration Pattern

### Recommended API Client Setup

```typescript
// lib/api/client.ts
const API_BASE = process.env.NEXT_PUBLIC_PRM_API_URL || 'http://localhost:8007';

export const prmApi = {
  // Patients
  patients: {
    list: (params) => fetch(`${API_BASE}/api/v1/prm/patients?${new URLSearchParams(params)}`),
    get: (id) => fetch(`${API_BASE}/api/v1/prm/patients/${id}`),
    get360: (id) => fetch(`${API_BASE}/api/v1/prm/patients/${id}/360`),
    search: (query, type = 'name') =>
      fetch(`${API_BASE}/api/v1/prm/patients/search?query=${query}&type=${type}`),
    create: (data) => fetch(`${API_BASE}/api/v1/prm/patients`, {
      method: 'POST', body: JSON.stringify(data)
    }),
  },

  // Appointments
  appointments: {
    list: (params) => fetch(`${API_BASE}/api/v1/prm/appointments?${new URLSearchParams(params)}`),
    today: () => fetch(`${API_BASE}/api/v1/prm/appointments/today`),
    upcoming: (limit = 5) => fetch(`${API_BASE}/api/v1/prm/appointments/upcoming?limit=${limit}`),
    stats: () => fetch(`${API_BASE}/api/v1/prm/appointments/stats`),
    create: (data) => fetch(`${API_BASE}/api/v1/prm/appointments`, {
      method: 'POST', body: JSON.stringify(data)
    }),
  },

  // Journeys
  journeys: {
    list: () => fetch(`${API_BASE}/api/v1/prm/journeys`),
    instances: (params) =>
      fetch(`${API_BASE}/api/v1/prm/journeys/instances?${new URLSearchParams(params)}`),
    instanceStats: () => fetch(`${API_BASE}/api/v1/prm/journeys/instances/stats`),
  },

  // Communications
  communications: {
    list: (params) =>
      fetch(`${API_BASE}/api/v1/prm/communications?${new URLSearchParams(params)}`),
    stats: () => fetch(`${API_BASE}/api/v1/prm/communications/stats`),
    send: (data) => fetch(`${API_BASE}/api/v1/prm/communications`, {
      method: 'POST', body: JSON.stringify(data)
    }),
    markRead: (id) => fetch(`${API_BASE}/api/v1/prm/communications/${id}`, {
      method: 'PATCH', body: JSON.stringify({ status: 'read' })
    }),
  },

  // Tickets
  tickets: {
    list: (params) => fetch(`${API_BASE}/api/v1/prm/tickets?${new URLSearchParams(params)}`),
    create: (data) => fetch(`${API_BASE}/api/v1/prm/tickets`, {
      method: 'POST', body: JSON.stringify(data)
    }),
    update: (id, data) => fetch(`${API_BASE}/api/v1/prm/tickets/${id}`, {
      method: 'PATCH', body: JSON.stringify(data)
    }),
  },

  // Analytics
  analytics: {
    dashboard: (tenantId, timePeriod = 'LAST_30_DAYS') =>
      fetch(`${API_BASE}/api/v1/prm/analytics/dashboard?tenant_id=${tenantId}&time_period=${timePeriod}`),
  },
};
```

---

## Migration Notes

### From Mock to Real API

If previously using mock data, update your data fetching:

```typescript
// Before (mock)
const patients = mockPatients;

// After (real API)
const { data: patients } = await prmApi.patients.list({ page: 1, page_size: 20 });
```

### Error Handling

All endpoints return consistent error format:

```json
{
  "detail": "Error message"
}
```

Handle in your API client:

```typescript
const response = await fetch(url);
if (!response.ok) {
  const error = await response.json();
  throw new Error(error.detail || 'API Error');
}
return response.json();
```

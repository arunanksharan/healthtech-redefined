# PRM Dashboard - API Mapping Guide

This document maps every data point on the frontend dashboard to the required backend API endpoints. It identifies which endpoints are **Available** (in `prm-service`), which are **Missing** (need `identity` or `scheduling` services), and the recommended strategy for the current integration phase.

---

## 1. Dashboard (Home) `/dashboard`

The main dashboard aggregates data from multiple domains.

### **Stats Cards**
| UI Component | Data Required | API Endpoint | Status | Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **Today's Appointments** | Count of appointments today | `GET /api/v1/scheduling/appointments?date=today` | ❌ Missing | **Mock** |
| **Active Journeys** | Count of active journey instances | `GET /api/v1/prm/instances?status=active` | ✅ Available | **Real API** |
| **Messages Sent** | Count of communications | `GET /api/v1/prm/communications` | ✅ Available | **Real API** |
| **Pending Tickets** | Count of open tickets | `GET /api/v1/prm/tickets?status=open` | ✅ Available | **Real API** |

### **Lists & Widgets**
| UI Component | Data Required | API Endpoint | Status | Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **Upcoming Appointments** | List of next 5 appointments | `GET /api/v1/scheduling/appointments?limit=5&sort=asc` | ❌ Missing | **Mock** |
| **Recent Communications** | List of last 5 messages | `GET /api/v1/prm/communications?page_size=5` | ✅ Available | **Real API** |
| **AI Suggestions** | Generated suggestions | `POST /api/v1/prm/suggestions` (Hypothetical) | ❌ Missing | **Mock** (Static for now) |

---

## 2. Appointments Page `/dashboard/appointments`

**Current Status:** Entirely dependent on `scheduling-service`.

| Feature | Data Required | API Endpoint | Status | Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **Calendar View** | Appointments by date range | `GET /api/v1/scheduling/appointments?start_date=..&end_date=..` | ❌ Missing | **Mock** |
| **Stats (Confirmed/Pending)** | Aggregated counts | `GET /api/v1/scheduling/appointments/stats` | ❌ Missing | **Mock** |
| **Create Appointment** | Create new record | `POST /api/v1/scheduling/appointments` | ❌ Missing | **Mock** |

> **Recommendation:** Since we cannot run `scheduling-service` yet, we will use a **Mock Adapter** that simulates these API calls within `lib/api/appointments.ts`.

---

## 3. Patients Page `/dashboard/patients`

**Current Status:** Entirely dependent on `identity-service`.

| Feature | Data Required | API Endpoint | Status | Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **Patient List** | Paginated list of patients | `GET /api/v1/identity/patients` | ❌ Missing | **Mock** |
| **Search** | Search by Name/MRN | `GET /api/v1/identity/patients?search=...` | ❌ Missing | **Mock** |
| **Patient Profile** | Single patient details | `GET /api/v1/identity/patients/{id}` | ❌ Missing | **Mock** |

> **Recommendation:** Use **Mock Adapter** in `lib/api/patients.ts`.

---

## 4. Inbox Page `/dashboard/inbox`

**Current Status:** Fully supported by `prm-service`.

| Feature | Data Required | API Endpoint | Status | Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **Message Feed** | List of communications | `GET /api/v1/prm/communications` | ✅ Available | **Real API** |
| **Filter by Channel** | Filter param | `.../communications?channel=whatsapp` | ✅ Available | **Real API** |
| **Mark as Read** | Update status | `PATCH .../communications/{id}` | ✅ Available | **Real API** |
| **Send Reply** | Create new comm | `POST /api/v1/prm/communications` | ✅ Available | **Real API** |

---

## 5. Journeys Page `/dashboard/journeys`

**Current Status:** Fully supported by `prm-service`.

| Feature | Data Required | API Endpoint | Status | Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **Journey List** | List definitions | `GET /api/v1/prm/journeys` | ✅ Available | **Real API** |
| **Create Journey** | New definition | `POST /api/v1/prm/journeys` | ✅ Available | **Real API** |
| **Journey Stats** | Instance counts | `GET /api/v1/prm/instances/stats` (Derived) | ✅ Available | **Real API** |

---

## 6. Tickets Page `/dashboard/tickets`

**Current Status:** Fully supported by `prm-service`.

| Feature | Data Required | API Endpoint | Status | Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **Ticket Board** | List of tickets | `GET /api/v1/prm/tickets` | ✅ Available | **Real API** |
| **Update Status** | Patch ticket | `PATCH .../tickets/{id}` | ✅ Available | **Real API** |


---

## 7. Communications Page `/dashboard/communications`

**Current Status:** Fully supported by `prm-service`.

| Feature | Data Required | API Endpoint | Status | Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **All Messages** | Searchable list | `GET /api/v1/prm/communications` | ✅ Available | **Real API** |
| **Stats** | Aggregated counts | `GET /api/v1/prm/communications` (Derived from list) | ✅ Available | **Real API** |
| **Send Message** | Create new comm | `POST /api/v1/prm/communications` | ✅ Available | **Real API** |

---

## 8. Analytics Page `/dashboard/analytics`

**Current Status:** Requires specialized analytics service or heavy aggregation.

| Feature | Data Required | API Endpoint | Status | Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **Charts & Trends** | Aggregated metrics | `GET /api/v1/analytics/dashboard` | ❌ Missing | **Mock** |
| **AI Insights** | Generated insights | `GET /api/v1/analytics/insights` | ❌ Missing | **Mock** |

> **Recommendation:** Keep using internal mock data (`mockInsights`, `mockSentimentData`) for now.

---

## 9. Settings Page `/dashboard/settings`

**Current Status:** Dependent on `identity-service` or `tenant-service`.

| Feature | Data Required | API Endpoint | Status | Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **Profile** | User details | `GET /api/v1/identity/me` | ❌ Missing | **Mock** |
| **Preferences** | User settings | `PATCH /api/v1/identity/me/settings` | ❌ Missing | **Mock** |

---

## Summary of Next Steps

1.  **Mock Adapters:** Implement robust mock adapters for `patients`, `appointments`, `analytics`, and `settings` in the frontend API layer.
2.  **Real Integration:** Connect `inbox`, `journeys`, `tickets`, and `communications` to the executing `prm-service`.

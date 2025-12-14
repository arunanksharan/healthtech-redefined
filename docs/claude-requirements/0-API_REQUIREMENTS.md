# PRM Dashboard API Requirements

This document outlines the API endpoints required to fully functionalize the PRM Dashboard, specifically for the **Appointments**, **Inbox**, and **Analytics** pages.

> **Status: ✅ ALL IMPLEMENTED** (Updated: 2025-01-XX)

---

## 🚨 Critical Priority - ✅ COMPLETE
*Blockers for core user workflows (Scheduling, Message Management).*

### Appointments Module
| Method | Endpoint | Description | Status |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/prm/appointments` | **Create Appointment**. Required for the "New Appointment" button. | ✅ Implemented |
| `GET` | `/api/v1/prm/appointments` | **List Appointments**. Paginated with filters. | ✅ Implemented |
| `GET` | `/api/v1/prm/appointments/{id}` | **Get Appointment**. Single appointment details. | ✅ Implemented |
| `PATCH` | `/api/v1/prm/appointments/{id}` | **Update Appointment**. Required for rescheduling or editing. | ✅ Implemented |
| `DELETE` | `/api/v1/prm/appointments/{id}` | **Delete Appointment**. Hard delete (use cancel for soft delete). | ✅ Implemented |
| `POST/PUT` | `/api/v1/prm/appointments/{id}/cancel` | **Cancel Appointment**. Sets status to cancelled. | ✅ Implemented |

### Practitioners Module
| Method | Endpoint | Description | Status |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/prm/practitioners` | **List Practitioners**. For dropdown population. | ✅ Implemented |
| `GET` | `/api/v1/prm/practitioners/simple` | **Simple List**. Optimized for dropdowns. | ✅ Implemented |
| `GET` | `/api/v1/prm/practitioners/specialities` | **List Specialities**. Unique speciality values. | ✅ Implemented |
| `GET` | `/api/v1/prm/practitioners/{id}` | **Get Practitioner**. Single practitioner details. | ✅ Implemented |
| `POST` | `/api/v1/prm/practitioners` | **Create Practitioner**. New provider registration. | ✅ Implemented |
| `PATCH` | `/api/v1/prm/practitioners/{id}` | **Update Practitioner**. Partial update. | ✅ Implemented |
| `DELETE` | `/api/v1/prm/practitioners/{id}` | **Delete Practitioner**. Hard delete. | ✅ Implemented |

### Inbox (Communications) Module
| Method | Endpoint | Description | Status |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/prm/communications` | **Create Communication**. Send message. | ✅ Implemented |
| `GET` | `/api/v1/prm/communications` | **List Communications**. Paginated with filters. | ✅ Implemented |
| `GET` | `/api/v1/prm/communications/{id}` | **Get Communication**. Single message details. | ✅ Implemented |
| `PATCH` | `/api/v1/prm/communications/{id}` | **Update Communication**. Update status/metadata. | ✅ Implemented |
| `DELETE` | `/api/v1/prm/communications/{id}` | **Delete Communication**. Hard delete. | ✅ Implemented |
| `PATCH` | `/api/v1/prm/communications/{id}/read` | **Mark as Read**. Sets status and read_at. | ✅ Implemented |
| `GET` | `/api/v1/prm/communications/templates` | **List Templates**. For quick replies. | ✅ Implemented |

---


## ℹ️ Enhancements (Low Priority) - ✅ COMPLETE
*Performance and usability improvements.*

| Method | Endpoint | Description | Status |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/prm/communications/search` | **Server-side Search**. Full-text search across messages. | ✅ Implemented |
| `GET` | `/api/v1/prm/appointments/conflicts` | **Conflict Check**. Pre-flight scheduling conflict detection. | ✅ Implemented |
| `GET` | `/api/v1/prm/communications/stats` | **Communication Stats**. Aggregated metrics. | ✅ Implemented |
| `GET` | `/api/v1/prm/appointments/stats` | **Appointment Stats**. Aggregated metrics. | ✅ Implemented |
| `GET` | `/api/v1/prm/appointments/today` | **Today's Appointments**. Quick view. | ✅ Implemented |
| `GET` | `/api/v1/prm/appointments/upcoming` | **Upcoming Appointments**. Future appointments. | ✅ Implemented |

---

## Summary

All critical and enhancement APIs have been implemented. The PRM Dashboard now has complete CRUD operations for:

- **Appointments**: Full lifecycle management with conflict detection
- **Practitioners**: Provider management with filtering
- **Communications**: Multi-channel messaging with templates and search

See `docs/api/PRM_SERVICE_API_REFERENCE.md` for complete API documentation.

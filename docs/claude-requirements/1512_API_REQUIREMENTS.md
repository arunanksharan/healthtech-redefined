# Backend API Requirements
To support the frontend pages with dedicated modules (matching the pattern of `patients` and `practitioners`), the backend must expose the following RESTful endpoints.

> **Status: ALL IMPLEMENTED** - All modules created and registered in `api/router.py`

## 1. Organizations
**Base URL:** `/api/v1/prm/organizations`
**Module:** `modules/organizations/`
**Status:** IMPLEMENTED

| Method | Endpoint | Description | Status |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | List all organizations (supports pagination & search) | Done |
| `POST` | `/` | Create a new organization | Done |
| `GET` | `/{id}` | Get organization details | Done |
| `PUT` | `/{id}` | Update organization details | Done |
| `DELETE` | `/{id}` | Delete/Archive organization | Done |

## 2. Locations
**Base URL:** `/api/v1/prm/locations`
**Module:** `modules/locations/`
**Status:** IMPLEMENTED

| Method | Endpoint | Description | Status |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | List all locations | Done |
| `POST` | `/` | Create a new location | Done |
| `GET` | `/{id}` | Get location details | Done |
| `PUT` | `/{id}` | Update location details | Done |

## 3. Encounters
**Base URL:** `/api/v1/prm/encounters`
**Module:** `modules/encounters/`
**Status:** IMPLEMENTED

| Method | Endpoint | Description | Status |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | List all encounters (visits) | Done |
| `POST` | `/` | Record a new encounter | Done |
| `GET` | `/{id}` | Get encounter details | Done |
| `PUT` | `/{id}` | Update encounter | Done |

## 4. Observations
**Base URL:** `/api/v1/prm/observations`
**Module:** `modules/observations/`
**Status:** IMPLEMENTED (uses FHIRResource storage)

| Method | Endpoint | Description | Status |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | List clinical observations (vitals, labs) | Done |
| `POST` | `/` | Create a new observation | Done |
| `GET` | `/{id}` | Get observation details | Done |

## 5. Conditions
**Base URL:** `/api/v1/prm/conditions`
**Module:** `modules/conditions/`
**Status:** IMPLEMENTED (uses FHIRResource storage)

| Method | Endpoint | Description | Status |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | List patient conditions/diagnoses | Done |
| `POST` | `/` | Record a new condition | Done |
| `GET` | `/{id}` | Get condition details | Done (added for completeness) |
| `PUT` | `/{id}` | Resolve or update condition | Done |

## 6. Medications
**Base URL:** `/api/v1/prm/medications`
**Module:** `modules/medications/`
**Status:** IMPLEMENTED (uses FHIRResource storage)

| Method | Endpoint | Description | Status |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | List medication requests/prescriptions | Done |
| `POST` | `/` | Prescribe a medication | Done |
| `GET` | `/{id}` | Get prescription details | Done |

## 7. Diagnostic Reports
**Base URL:** `/api/v1/prm/diagnostic-reports`
**Module:** `modules/diagnostic_reports/`
**Status:** IMPLEMENTED (uses FHIRResource storage)

| Method | Endpoint | Description | Status |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | List diagnostic reports (Lab results, Imaging) | Done |
| `POST` | `/` | Create a report | Done |
| `GET` | `/{id}` | Get report details | Done |

---

## Pre-existing Modules (Already Active)

### Telehealth
**Base URL:** `/api/v1/prm/telehealth`
**Module:** `modules/telehealth/`
**Status:** ACTIVE (comprehensive implementation)

| Endpoint | Methods | Description |
| :--- | :--- | :--- |
| `/sessions` | GET, POST | Video session management |
| `/sessions/{id}` | GET | Get session details |
| `/sessions/{id}/participants` | GET, POST | Participant management |
| `/sessions/{id}/join-token` | POST | Generate join token |
| `/sessions/{id}/end` | POST | End session |
| `/waiting-rooms` | POST | Create waiting room |
| `/waiting-rooms/{id}` | GET | Get waiting room |
| `/waiting-rooms/{id}/check-in` | POST | Patient check-in |
| `/waiting-rooms/{id}/queue` | GET | Queue status |
| `/appointments` | GET, POST | Appointment management |
| `/payments` | GET, POST | Payment processing |
| `/metrics` | GET | Analytics |

### Billing
**Base URL:** `/api/v1/prm/billing`
**Module:** `modules/billing/`
**Status:** ACTIVE (comprehensive implementation)

| Endpoint | Methods | Description |
| :--- | :--- | :--- |
| `/policies` | GET, POST | Insurance policy management |
| `/eligibility/verify` | POST | Real-time eligibility check |
| `/eligibility/batch` | POST | Batch verification |
| `/prior-auth` | GET, POST, PUT | Prior authorization |
| `/claims` | GET, POST | Claims management |
| `/claims/{id}/submit` | POST | Submit to payer |
| `/claims/{id}/validate` | POST | Validate before submission |
| `/payments` | GET, POST | Payment processing |
| `/payment-plans` | GET, POST | Payment plans |
| `/statements` | GET, POST | Patient statements |
| `/fee-schedules` | GET, POST | Fee schedule management |
| `/contracts` | GET, POST | Payer contracts |
| `/denials` | GET, POST | Denial management |
| `/analytics/*` | GET | Revenue cycle analytics |

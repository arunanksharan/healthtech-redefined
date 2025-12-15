# Backend API Requirements
To support the frontend pages with dedicated modules (matching the pattern of `patients` and `practitioners`), the backend must expose the following RESTful endpoints.

## 1. Organizations
**Base URL:** `/api/v1/prm/organizations`

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | List all organizations (supports pagination & search) |
| `POST` | `/` | Create a new organization |
| `GET` | `/{id}` | Get organization details |
| `PUT` | `/{id}` | Update organization details |
| `DELETE` | `/{id}` | Delete/Archive organization |

## 2. Locations
**Base URL:** `/api/v1/prm/locations`

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | List all locations |
| `POST` | `/` | Create a new location |
| `GET` | `/{id}` | Get location details |
| `PUT` | `/{id}` | Update location details |

## 3. Encounters
**Base URL:** `/api/v1/prm/encounters`

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | List all encounters (visits) |
| `POST` | `/` | Record a new encounter |
| `GET` | `/{id}` | Get encounter details |
| `PUT` | `/{id}` | Update encounter |

## 4. Observations
**Base URL:** `/api/v1/prm/observations`

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | List clinical observations (vitals, labs) |
| `POST` | `/` | Create a new observation |
| `GET` | `/{id}` | Get observation details |

## 5. Conditions
**Base URL:** `/api/v1/prm/conditions`

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | List patient conditions/diagnoses |
| `POST` | `/` | Record a new condition |
| `PUT` | `/{id}` | Resolve or update condition |

## 6. Medications
**Base URL:** `/api/v1/prm/medications`

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | List medication requests/prescriptions |
| `POST` | `/` | Prescribe a medication |
| `GET` | `/{id}` | Get prescription details |

## 7. Diagnostic Reports
**Base URL:** `/api/v1/prm/diagnostic-reports`

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | List diagnostic reports (Lab results, Imaging) |
| `POST` | `/` | Create a report |
| `GET` | `/{id}` | Get report details |

---

## These Possibly Exist in the Modules (Please look for them bhaiya)
*These simply need to be activated in `main.py`*

### Telehealth
**Base URL:** `/api/v1/prm/telehealth`
- `/sessions` (GET, POST)
- `/waiting-rooms` (POST)

### Billing
**Base URL:** `/api/v1/prm/billing`
- `/claims` (GET, POST)
- `/payments` (GET, POST)

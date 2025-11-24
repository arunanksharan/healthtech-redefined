# FHIR R4 Quick Start Guide

**For Developers Using the PRM FHIR API**

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Access to the PRM backend environment

### Step 1: Database Setup

```bash
# Connect to PostgreSQL
psql -U postgres -d healthtech

# Run FHIR tables migration
\i backend/alembic/versions/add_fhir_tables.sql

# Verify tables created
\dt fhir*
```

### Step 2: Start the Service

```bash
cd backend/services/prm-service
uvicorn main_modular:app --reload --port 8000
```

### Step 3: Test the API

```bash
# Get server capabilities
curl http://localhost:8000/api/v1/prm/fhir/metadata

# Expected: CapabilityStatement JSON
```

---

## 📝 Basic CRUD Operations

### Create a Patient

```bash
curl -X POST http://localhost:8000/api/v1/prm/fhir/Patient \
  -H "Content-Type: application/json" \
  -d '{
    "resourceType": "Patient",
    "identifier": [{
      "system": "http://hospital.org/patients",
      "value": "MRN123456"
    }],
    "name": [{
      "use": "official",
      "family": "Smith",
      "given": ["John"]
    }],
    "gender": "male",
    "birthDate": "1974-12-25",
    "telecom": [{
      "system": "phone",
      "value": "+1-555-1234",
      "use": "mobile"
    }]
  }'
```

**Response:** 201 Created
```json
{
  "resourceType": "Patient",
  "id": "abc123",
  "meta": {
    "versionId": "1",
    "lastUpdated": "2024-11-24T10:30:00Z"
  },
  "identifier": [...],
  "name": [...],
  ...
}
```

### Read a Patient

```bash
curl http://localhost:8000/api/v1/prm/fhir/Patient/abc123
```

**Response:** 200 OK (Patient resource)

### Update a Patient

```bash
curl -X PUT http://localhost:8000/api/v1/prm/fhir/Patient/abc123 \
  -H "Content-Type: application/json" \
  -d '{
    "resourceType": "Patient",
    "id": "abc123",
    "name": [{
      "use": "official",
      "family": "Smith",
      "given": ["John", "Michael"]
    }],
    "gender": "male",
    "birthDate": "1974-12-25"
  }'
```

**Response:** 200 OK (Updated patient with versionId: "2")

### Delete a Patient

```bash
curl -X DELETE http://localhost:8000/api/v1/prm/fhir/Patient/abc123
```

**Response:** 204 No Content

---

## 🔍 Search Operations

### Search by Name

```bash
curl "http://localhost:8000/api/v1/prm/fhir/Patient?name=Smith"
```

### Search by Identifier

```bash
curl "http://localhost:8000/api/v1/prm/fhir/Patient?identifier=MRN123456"
```

### Pagination

```bash
curl "http://localhost:8000/api/v1/prm/fhir/Patient?_count=20&_offset=0"
```

**Response:** Bundle with search results
```json
{
  "resourceType": "Bundle",
  "type": "searchset",
  "total": 150,
  "entry": [
    {
      "fullUrl": "/fhir/Patient/abc123",
      "resource": {...},
      "search": {"mode": "match"}
    },
    ...
  ]
}
```

---

## 📚 Other Resource Types

### Create an Observation

```bash
curl -X POST http://localhost:8000/api/v1/prm/fhir/Observation \
  -H "Content-Type: application/json" \
  -d '{
    "resourceType": "Observation",
    "status": "final",
    "category": [{
      "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
        "code": "vital-signs"
      }]
    }],
    "code": {
      "coding": [{
        "system": "http://loinc.org",
        "code": "8867-4",
        "display": "Heart rate"
      }]
    },
    "subject": {
      "reference": "Patient/abc123"
    },
    "effectiveDateTime": "2024-11-24T10:30:00Z",
    "valueQuantity": {
      "value": 72,
      "unit": "beats/minute",
      "system": "http://unitsofmeasure.org",
      "code": "/min"
    }
  }'
```

### Create a Condition

```bash
curl -X POST http://localhost:8000/api/v1/prm/fhir/Condition \
  -H "Content-Type: application/json" \
  -d '{
    "resourceType": "Condition",
    "clinicalStatus": {
      "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
        "code": "active"
      }]
    },
    "verificationStatus": {
      "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
        "code": "confirmed"
      }]
    },
    "code": {
      "coding": [{
        "system": "http://snomed.info/sct",
        "code": "38341003",
        "display": "Hypertensive disorder"
      }]
    },
    "subject": {
      "reference": "Patient/abc123"
    },
    "onsetDateTime": "2020-05-15"
  }'
```

---

## 📜 Version History

### Get Resource History

```bash
curl http://localhost:8000/api/v1/prm/fhir/Patient/abc123/_history
```

**Response:** Bundle with all versions

### Read Specific Version

```bash
curl http://localhost:8000/api/v1/prm/fhir/Patient/abc123/_history/2
```

**Response:** Patient resource at version 2

---

## ✅ Validation

### Validate Without Saving

```bash
curl -X POST http://localhost:8000/api/v1/prm/fhir/Patient/$validate \
  -H "Content-Type: application/json" \
  -d '{
    "resourceType": "Patient",
    "birthDate": "2030-01-01"
  }'
```

**Response:** OperationOutcome with validation errors
```json
{
  "resourceType": "OperationOutcome",
  "issue": [{
    "severity": "error",
    "code": "invalid",
    "details": "Birth date cannot be in the future at birthDate"
  }]
}
```

---

## 🐍 Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000/api/v1/prm/fhir"

# Create a patient
patient = {
    "resourceType": "Patient",
    "name": [{
        "family": "Doe",
        "given": ["Jane"]
    }],
    "gender": "female",
    "birthDate": "1990-01-01"
}

response = requests.post(f"{BASE_URL}/Patient", json=patient)
if response.status_code == 201:
    patient_id = response.json()["id"]
    print(f"Created patient: {patient_id}")
    
    # Read the patient back
    patient_response = requests.get(f"{BASE_URL}/Patient/{patient_id}")
    print(patient_response.json())
    
    # Search for patients
    search_response = requests.get(f"{BASE_URL}/Patient?name=Doe")
    print(f"Found {search_response.json()['total']} patients")
```

---

## 🧪 Testing Tips

### 1. Use CapabilityStatement

Always start by checking what the server supports:
```bash
curl http://localhost:8000/api/v1/prm/fhir/metadata | jq '.rest[0].resource'
```

### 2. Validate Before Creating

Use the $validate operation to check your resource before POSTing:
```bash
curl -X POST http://localhost:8000/api/v1/prm/fhir/Patient/$validate \
  -H "Content-Type: application/json" \
  -d @patient.json
```

### 3. Check Version After Update

ETags contain the version number:
```bash
curl -i http://localhost:8000/api/v1/prm/fhir/Patient/abc123 | grep ETag
# ETag: W/"3"
```

---

## ⚠️ Common Errors

### 400 Bad Request
**Cause:** Validation failure  
**Solution:** Check OperationOutcome in response body

### 404 Not Found
**Cause:** Resource doesn't exist  
**Solution:** Verify resource ID and type

### 500 Internal Server Error
**Cause:** Server error  
**Solution:** Check server logs

---

## 📖 Supported Resources

| Resource | Create | Read | Update | Delete | Search |
|----------|--------|------|--------|--------|--------|
| Patient | ✅ | ✅ | ✅ | ✅ | ✅ |
| Practitioner | ✅ | ✅ | ✅ | ✅ | ✅ |
| Organization | ✅ | ✅ | ✅ | ✅ | ✅ |
| Encounter | ✅ | ✅ | ✅ | ✅ | ✅ |
| Observation | ✅ | ✅ | ✅ | ✅ | ✅ |
| Condition | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 🔗 Additional Resources

- **FHIR R4 Spec:** https://www.hl7.org/fhir/R4/
- **API Docs:** http://localhost:8000/docs
- **CapabilityStatement:** http://localhost:8000/api/v1/prm/fhir/metadata

---

## 🆘 Need Help?

**Documentation:** `/docs/implement/epics/EPIC-005-*.md`  
**Code:** `/backend/services/prm-service/modules/fhir/`  
**Issues:** GitHub Issues

---

**Quick Start Guide v1.0**  
**Last Updated:** November 24, 2024

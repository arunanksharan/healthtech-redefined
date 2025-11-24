# FHIR R4 Implementation Guide

## Overview

This module implements **FHIR R4 (Fast Healthcare Interoperability Resources)** support for the Patient Relationship Management (PRM) system. It provides standards-based healthcare data exchange capabilities following the HL7 FHIR R4 specification.

## Features Implemented

### ✅ Core FHIR Resources (US-005.1) - COMPLETE
- **Patient**: Demographics and administrative information
- **Practitioner**: Healthcare professionals
- **PractitionerRole**: Roles and locations for practitioners
- **Organization**: Healthcare organizations
- **Encounter**: Healthcare visits and interactions
- **Observation**: Clinical measurements and assessments
- **Condition**: Diagnoses and health problems

### ✅ FHIR REST API (US-005.2) - COMPLETE
- **CRUD Operations**: Create, Read, Update, Delete for all resources
- **Versioning**: Automatic version tracking with history
- **Search**: Basic search capabilities
- **Validation**: Resource validation endpoint
- **CapabilityStatement**: Server capabilities metadata

### ✅ Repository Layer - COMPLETE
- PostgreSQL JSONB storage for flexible resource management
- Version management and history tracking
- Tenant isolation
- Soft delete support

### ✅ Service Layer - COMPLETE
- Business logic for resource operations
- Integrated validation
- Error handling and logging

## Architecture

```
modules/fhir/
├── models/              # Pydantic models for FHIR resources
│   ├── base.py         # Base data types (Coding, CodeableConcept, etc.)
│   ├── patient.py      # Patient resource
│   ├── practitioner.py # Practitioner & PractitionerRole
│   ├── organization.py # Organization resource
│   ├── encounter.py    # Encounter resource
│   ├── observation.py  # Observation resource
│   └── condition.py    # Condition resource
├── repository/         # Data access layer
│   └── fhir_repository.py
├── services/           # Business logic layer
│   ├── resource_service.py
│   ├── validation_service.py
│   └── search_service.py
└── router.py          # FastAPI REST endpoints
```

## API Endpoints

All FHIR endpoints are prefixed with `/api/v1/prm/fhir`

### Metadata
- `GET /metadata` - Get CapabilityStatement
- `GET /health` - Health check

### Resource Operations
For each resource type (Patient, Practitioner, Organization, Encounter, Observation, Condition):

- `POST /{resourceType}` - Create new resource
- `GET /{resourceType}/{id}` - Read resource by ID
- `PUT /{resourceType}/{id}` - Update resource
- `DELETE /{resourceType}/{id}` - Delete resource (soft delete)
- `GET /{resourceType}` - Search resources
- `GET /{resourceType}/{id}/_history` - Get version history
- `POST /{resourceType}/$validate` - Validate resource without persisting

## Usage Examples

### 1. Create a Patient

```bash
curl -X POST http://localhost:8007/api/v1/prm/fhir/Patient \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: <your-tenant-id>" \
  -d '{
    "resourceType": "Patient",
    "active": true,
    "name": [{
      "use": "official",
      "family": "Smith",
      "given": ["John", "Michael"]
    }],
    "telecom": [{
      "system": "phone",
      "value": "+1-555-1234",
      "use": "mobile"
    }],
    "gender": "male",
    "birthDate": "1974-12-25",
    "address": [{
      "use": "home",
      "line": ["123 Main Street"],
      "city": "Springfield",
      "state": "IL",
      "postalCode": "62701",
      "country": "US"
    }]
  }'
```

### 2. Read a Patient

```bash
curl -X GET http://localhost:8007/api/v1/prm/fhir/Patient/example-001 \
  -H "X-Tenant-ID: <your-tenant-id>"
```

### 3. Update a Patient

```bash
curl -X PUT http://localhost:8007/api/v1/prm/fhir/Patient/example-001 \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: <your-tenant-id>" \
  -d '{
    "resourceType": "Patient",
    "id": "example-001",
    "active": false,
    "name": [{
      "use": "official",
      "family": "Smith",
      "given": ["John", "Michael"]
    }]
  }'
```

### 4. Search Patients

```bash
curl -X GET "http://localhost:8007/api/v1/prm/fhir/Patient?_count=20&_offset=0" \
  -H "X-Tenant-ID: <your-tenant-id>"
```

### 5. Validate a Resource

```bash
curl -X POST http://localhost:8007/api/v1/prm/fhir/Patient/\$validate \
  -H "Content-Type: application/json" \
  -d '{
    "resourceType": "Patient",
    "name": [{
      "family": "TestPatient"
    }]
  }'
```

### 6. Get Resource History

```bash
curl -X GET http://localhost:8007/api/v1/prm/fhir/Patient/example-001/_history \
  -H "X-Tenant-ID: <your-tenant-id>"
```

### 7. Get CapabilityStatement

```bash
curl -X GET http://localhost:8007/api/v1/prm/fhir/metadata
```

## Python Usage

```python
from modules.fhir.models import Patient, HumanName, ContactPoint, Address
from modules.fhir.services.resource_service import FHIRResourceService
from sqlalchemy.orm import Session

# Create a patient resource
patient = Patient(
    resourceType="Patient",
    active=True,
    name=[
        HumanName(
            use="official",
            family="Smith",
            given=["John"]
        )
    ],
    telecom=[
        ContactPoint(
            system="phone",
            value="+1-555-1234",
            use="mobile"
        )
    ],
    gender="male"
)

# Validate the resource
patient_dict = patient.dict(exclude_none=True)

# Use service to persist
service = FHIRResourceService(db_session)
created = service.create_resource(
    tenant_id=tenant_id,
    resource_type="Patient",
    resource_data=patient_dict
)
```

## Database Schema

Resources are stored in the `fhir_resources` table:

```sql
CREATE TABLE fhir_resources (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(100) NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    resource JSONB NOT NULL,
    meta_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Validation

The FHIR implementation includes comprehensive validation:

1. **Schema Validation**: Pydantic models enforce FHIR R4 schema
2. **Data Type Validation**: All FHIR data types are validated
3. **Business Rules**: Custom validators for dates, references, etc.
4. **Reference Validation**: Basic reference format checking

## Multi-Tenancy

All FHIR resources are tenant-isolated:
- Pass `X-Tenant-ID` header with requests
- All queries automatically filter by tenant
- No cross-tenant data access

## Versioning

All resources support versioning:
- Each update creates a new version
- Version history is preserved
- Access specific versions via `?_version=N`
- Delete is soft delete (preserves history)

## Standards Compliance

This implementation follows:
- **FHIR R4** (v4.0.1) specification
- **HL7** standards for healthcare data exchange
- **RESTful API** principles
- **JSON** format (primary)

## Testing

Run tests:
```bash
cd backend/services/prm-service
pytest tests/fhir/
```

## Future Enhancements

### Planned Features:
1. **Advanced Search** (US-005.4)
   - Chained searches
   - Include/revinclude
   - Advanced modifiers

2. **Terminology Services** (US-005.5)
   - CodeSystem, ValueSet support
   - $expand, $validate-code, $lookup operations
   - SNOMED CT, LOINC, ICD-10 integration

3. **FHIR Operations** (US-005.7)
   - Patient/$everything
   - $document generation
   - Custom operations

4. **Subscriptions** (US-005.8)
   - REST hooks
   - WebSocket support
   - Notification delivery

5. **Additional Resources**
   - Medication, MedicationRequest
   - AllergyIntolerance
   - Procedure, DiagnosticReport
   - CarePlan, Goal

## Troubleshooting

### Common Issues:

1. **Validation Errors**
   - Ensure all required fields are present
   - Check date formats (YYYY-MM-DD for dates)
   - Verify references are in format "ResourceType/id"

2. **404 Not Found**
   - Verify tenant ID matches
   - Check resource exists and is not deleted
   - Ensure resource ID is correct

3. **Version Conflicts**
   - Each update creates new version
   - Use history endpoint to see all versions
   - Specify version with `?_version=N` if needed

## Resources

- [FHIR R4 Specification](https://www.hl7.org/fhir/R4/)
- [FHIR Resource List](https://www.hl7.org/fhir/R4/resourcelist.html)
- [FHIR Search](https://www.hl7.org/fhir/R4/search.html)
- [US Core Implementation Guide](http://hl7.org/fhir/us/core/)

## Support

For issues or questions about FHIR implementation:
1. Check this documentation
2. Review FHIR R4 specification
3. Check implementation status in `IMPLEMENTATION_STATUS.md`
4. Contact development team

---

**Version:** 1.0.0  
**Last Updated:** November 24, 2024  
**FHIR Version:** R4 (4.0.1)

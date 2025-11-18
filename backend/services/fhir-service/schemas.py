"""
FHIR Service Pydantic Schemas
Request/Response models for FHIR resource operations
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, validator


class FHIRResourceCreate(BaseModel):
    """Schema for creating a FHIR resource"""

    tenant_id: UUID = Field(..., description="Tenant ID")
    resource_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="FHIR resource type (e.g., Patient, Observation, Encounter)"
    )
    resource_data: Dict[str, Any] = Field(
        ...,
        description="FHIR resource JSON data compliant with FHIR R4 spec"
    )
    subject_id: Optional[UUID] = Field(
        None,
        description="Reference to subject (usually Patient ID)"
    )
    author_id: Optional[UUID] = Field(
        None,
        description="Reference to author (Practitioner/User who created this)"
    )

    @validator("resource_type")
    def validate_resource_type(cls, v):
        """Validate FHIR resource type"""
        # FHIR R4 resource types
        valid_types = {
            # Clinical
            "AllergyIntolerance", "Condition", "Procedure", "Observation",
            "DiagnosticReport", "MedicationRequest", "MedicationStatement",
            "Immunization", "CarePlan", "CareTeam", "Goal",
            # Workflow
            "Appointment", "Encounter", "EpisodeOfCare", "ServiceRequest",
            "Task", "Communication", "CommunicationRequest",
            # Financial
            "Claim", "Coverage", "Invoice", "PaymentNotice",
            # Base
            "Patient", "Practitioner", "Organization", "Location",
            "Device", "Medication", "Substance",
            # Specialized
            "Consent", "QuestionnaireResponse", "DocumentReference"
        }

        if v not in valid_types:
            raise ValueError(
                f"Invalid FHIR resource type. Must be one of: {', '.join(sorted(valid_types))}"
            )
        return v

    @validator("resource_data")
    def validate_resource_data(cls, v, values):
        """Validate that resource_data matches the resource_type"""
        if "resource_type" in values:
            resource_type = values["resource_type"]
            if v.get("resourceType") != resource_type:
                raise ValueError(
                    f"resource_data.resourceType must match resource_type field. "
                    f"Expected '{resource_type}', got '{v.get('resourceType')}'"
                )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "resource_type": "Observation",
                "resource_data": {
                    "resourceType": "Observation",
                    "status": "final",
                    "code": {
                        "coding": [{
                            "system": "http://loinc.org",
                            "code": "85354-9",
                            "display": "Blood pressure"
                        }]
                    },
                    "valueQuantity": {
                        "value": 120,
                        "unit": "mmHg",
                        "system": "http://unitsofmeasure.org"
                    }
                },
                "subject_id": "patient-uuid-here"
            }
        }


class FHIRResourceUpdate(BaseModel):
    """Schema for updating a FHIR resource"""

    resource_data: Dict[str, Any] = Field(
        ...,
        description="Updated FHIR resource JSON data"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "resource_data": {
                    "resourceType": "Observation",
                    "status": "amended",
                    "code": {
                        "coding": [{
                            "system": "http://loinc.org",
                            "code": "85354-9",
                            "display": "Blood pressure"
                        }]
                    },
                    "valueQuantity": {
                        "value": 125,
                        "unit": "mmHg",
                        "system": "http://unitsofmeasure.org"
                    }
                }
            }
        }


class FHIRResourceResponse(BaseModel):
    """Response schema for FHIR resource"""

    id: UUID
    tenant_id: UUID
    resource_type: str
    resource_data: Dict[str, Any]
    version: int
    subject_id: Optional[UUID] = None
    author_id: Optional[UUID] = None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "resource-uuid",
                "tenant_id": "tenant-uuid",
                "resource_type": "Observation",
                "resource_data": {
                    "resourceType": "Observation",
                    "status": "final",
                    "code": {"coding": [{"code": "85354-9"}]},
                    "valueQuantity": {"value": 120}
                },
                "version": 1,
                "subject_id": "patient-uuid",
                "is_deleted": False,
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z"
            }
        }


class FHIRResourceVersionResponse(BaseModel):
    """Response schema for FHIR resource version history"""

    id: UUID
    resource_id: UUID
    version: int
    resource_data: Dict[str, Any]
    changed_by: Optional[UUID] = None
    change_description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FHIRResourceListResponse(BaseModel):
    """Response schema for list of FHIR resources"""

    total: int
    resources: List[FHIRResourceResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


class FHIRSearchParams(BaseModel):
    """Schema for FHIR search parameters"""

    resource_type: Optional[str] = Field(
        None,
        description="Filter by FHIR resource type"
    )
    subject_id: Optional[UUID] = Field(
        None,
        description="Filter by subject/patient ID"
    )
    author_id: Optional[UUID] = Field(
        None,
        description="Filter by author ID"
    )
    status: Optional[str] = Field(
        None,
        description="Filter by status field in resource"
    )
    code: Optional[str] = Field(
        None,
        description="Search by coding code (e.g., LOINC, SNOMED)"
    )
    date_from: Optional[datetime] = Field(
        None,
        description="Filter resources created on or after this date"
    )
    date_to: Optional[datetime] = Field(
        None,
        description="Filter resources created on or before this date"
    )
    include_deleted: bool = Field(
        False,
        description="Include soft-deleted resources in search"
    )
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")


class FHIRBundleResponse(BaseModel):
    """FHIR Bundle response (transaction/batch operations)"""

    resourceType: str = "Bundle"
    type: str = Field(..., description="Bundle type: transaction, batch, searchset")
    total: Optional[int] = None
    entry: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "resourceType": "Bundle",
                "type": "searchset",
                "total": 2,
                "entry": [
                    {
                        "resource": {
                            "resourceType": "Observation",
                            "id": "obs-1",
                            "status": "final"
                        }
                    },
                    {
                        "resource": {
                            "resourceType": "Observation",
                            "id": "obs-2",
                            "status": "final"
                        }
                    }
                ]
            }
        }


class FHIRValidationResponse(BaseModel):
    """Response schema for FHIR resource validation"""

    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    resource_type: str

    class Config:
        json_schema_extra = {
            "example": {
                "valid": True,
                "errors": [],
                "warnings": ["Optional field 'performer' not provided"],
                "resource_type": "Observation"
            }
        }

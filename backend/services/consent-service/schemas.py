"""
Consent Service Pydantic Schemas
Request/Response models for consent management
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, validator


class ConsentCreate(BaseModel):
    """Schema for creating a consent record"""

    tenant_id: UUID = Field(..., description="Tenant ID")
    patient_id: UUID = Field(..., description="Patient granting consent")
    grantee_id: UUID = Field(
        ...,
        description="Who is being granted access (Practitioner, Organization, etc.)"
    )
    grantee_type: str = Field(
        ...,
        description="Type of grantee (practitioner, organization, research_study)"
    )
    purpose: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Purpose of consent (treatment, research, sharing)"
    )
    scope: str = Field(
        ...,
        description="Scope of data access (full_record, specific_resources, specific_period)"
    )
    resource_types: Optional[List[str]] = Field(
        None,
        description="Specific FHIR resource types allowed (if scope is specific_resources)"
    )
    start_date: datetime = Field(
        ...,
        description="When consent becomes effective"
    )
    end_date: Optional[datetime] = Field(
        None,
        description="When consent expires (None = no expiration)"
    )
    privacy_level: str = Field(
        ...,
        description="Privacy level (normal, sensitive, highly_sensitive)"
    )
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Additional notes or conditions"
    )

    @validator("grantee_type")
    def validate_grantee_type(cls, v):
        """Validate grantee type"""
        valid_types = ["practitioner", "organization", "care_team", "research_study", "patient"]
        if v.lower() not in valid_types:
            raise ValueError(f"grantee_type must be one of: {', '.join(valid_types)}")
        return v.lower()

    @validator("purpose")
    def validate_purpose(cls, v):
        """Validate purpose"""
        valid_purposes = ["treatment", "research", "sharing", "marketing", "emergency", "general"]
        if v.lower() not in valid_purposes:
            raise ValueError(f"purpose must be one of: {', '.join(valid_purposes)}")
        return v.lower()

    @validator("scope")
    def validate_scope(cls, v):
        """Validate scope"""
        valid_scopes = ["full_record", "specific_resources", "specific_period", "emergency_only"]
        if v.lower() not in valid_scopes:
            raise ValueError(f"scope must be one of: {', '.join(valid_scopes)}")
        return v.lower()

    @validator("privacy_level")
    def validate_privacy_level(cls, v):
        """Validate privacy level"""
        valid_levels = ["normal", "sensitive", "highly_sensitive"]
        if v.lower() not in valid_levels:
            raise ValueError(f"privacy_level must be one of: {', '.join(valid_levels)}")
        return v.lower()

    @validator("end_date")
    def validate_end_date(cls, v, values):
        """Ensure end_date is after start_date"""
        if v and "start_date" in values:
            if v <= values["start_date"]:
                raise ValueError("end_date must be after start_date")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "patient_id": "patient-uuid",
                "grantee_id": "practitioner-uuid",
                "grantee_type": "practitioner",
                "purpose": "treatment",
                "scope": "full_record",
                "start_date": "2025-01-15T00:00:00Z",
                "end_date": "2026-01-15T00:00:00Z",
                "privacy_level": "normal",
                "notes": "Consent for ongoing diabetes treatment"
            }
        }


class ConsentUpdate(BaseModel):
    """Schema for updating a consent record"""

    end_date: Optional[datetime] = Field(
        None,
        description="Updated expiration date"
    )
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Updated notes"
    )
    privacy_level: Optional[str] = Field(
        None,
        description="Updated privacy level"
    )

    @validator("privacy_level")
    def validate_privacy_level(cls, v):
        """Validate privacy level"""
        if v is not None:
            valid_levels = ["normal", "sensitive", "highly_sensitive"]
            if v.lower() not in valid_levels:
                raise ValueError(f"privacy_level must be one of: {', '.join(valid_levels)}")
            return v.lower()
        return v


class ConsentResponse(BaseModel):
    """Response schema for consent record"""

    id: UUID
    tenant_id: UUID
    patient_id: UUID
    grantee_id: UUID
    grantee_type: str
    purpose: str
    scope: str
    resource_types: Optional[List[str]] = None
    status: str
    start_date: datetime
    end_date: Optional[datetime] = None
    privacy_level: str
    notes: Optional[str] = None
    is_revoked: bool
    revoked_at: Optional[datetime] = None
    revoked_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "consent-uuid",
                "tenant_id": "tenant-uuid",
                "patient_id": "patient-uuid",
                "grantee_id": "practitioner-uuid",
                "grantee_type": "practitioner",
                "purpose": "treatment",
                "scope": "full_record",
                "status": "active",
                "start_date": "2025-01-15T00:00:00Z",
                "end_date": "2026-01-15T00:00:00Z",
                "privacy_level": "normal",
                "is_revoked": False,
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z"
            }
        }


class ConsentListResponse(BaseModel):
    """Response schema for list of consents"""

    total: int
    consents: List[ConsentResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


class ConsentRevoke(BaseModel):
    """Schema for revoking a consent"""

    reason: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Reason for revoking consent"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "reason": "Patient requested to revoke consent for data sharing"
            }
        }


class AccessCheckRequest(BaseModel):
    """Schema for checking if access is permitted"""

    patient_id: UUID = Field(..., description="Patient whose data is being accessed")
    grantee_id: UUID = Field(..., description="Who is requesting access")
    resource_type: Optional[str] = Field(
        None,
        description="Specific FHIR resource type being accessed"
    )
    purpose: str = Field(
        ...,
        description="Purpose of access"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "patient_id": "patient-uuid",
                "grantee_id": "practitioner-uuid",
                "resource_type": "Observation",
                "purpose": "treatment"
            }
        }


class AccessCheckResponse(BaseModel):
    """Response schema for access check"""

    permitted: bool = Field(..., description="Whether access is permitted")
    reason: str = Field(..., description="Reason for permit/deny")
    applicable_consents: List[UUID] = Field(
        default_factory=list,
        description="Consent IDs that apply to this access request"
    )
    privacy_level: Optional[str] = Field(
        None,
        description="Privacy level of the data being accessed"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "permitted": True,
                "reason": "Active consent for treatment purposes exists",
                "applicable_consents": ["consent-uuid-1", "consent-uuid-2"],
                "privacy_level": "normal"
            }
        }


class ConsentAuditResponse(BaseModel):
    """Response schema for consent audit trail"""

    consent_id: UUID
    action: str
    performed_by: Optional[UUID] = None
    timestamp: datetime
    details: Optional[str] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "consent_id": "consent-uuid",
                "action": "consent_created",
                "performed_by": "user-uuid",
                "timestamp": "2025-01-15T10:00:00Z",
                "details": "Initial consent created for treatment"
            }
        }

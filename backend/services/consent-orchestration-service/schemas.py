"""
Consent Orchestration Service Pydantic Schemas
Request/Response models for consent policies and consent records
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator


# ==================== Consent Policy Schemas ====================

class ConsentPolicyCreate(BaseModel):
    """Schema for creating a consent policy template"""

    tenant_id: UUID
    code: str = Field(..., description="Unique policy code (e.g., REFERRAL_SHARE, RESEARCH_CONSENT)")
    name: str
    description: Optional[str] = None
    policy_type: str = Field(..., description="referral, research, emergency_access, app_integration")
    data_categories: List[str] = Field(..., description="Categories of data covered")
    permitted_use_cases: List[str] = Field(..., description="Allowed use cases")
    default_duration_days: Optional[int] = Field(None, description="Default consent duration in days")
    is_revocable: bool = Field(default=True, description="Can patient revoke?")
    requires_patient_signature: bool = Field(default=True)
    template_text: Optional[str] = Field(None, description="Consent form text template")
    is_active: bool = Field(default=True)

    @validator("policy_type")
    def validate_policy_type(cls, v):
        valid_types = [
            "referral", "research", "emergency_access",
            "app_integration", "data_exchange", "marketing"
        ]
        if v.lower() not in valid_types:
            raise ValueError(f"policy_type must be one of: {', '.join(valid_types)}")
        return v.lower()

    @validator("data_categories")
    def validate_data_categories(cls, v):
        valid_categories = [
            "demographics", "vitals", "medications", "labs",
            "imaging", "notes", "diagnoses", "procedures",
            "allergies", "immunizations", "genetic_data"
        ]
        for category in v:
            if category.lower() not in valid_categories:
                raise ValueError(f"Invalid data category: {category}")
        return [c.lower() for c in v]

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "code": "REFERRAL_DATA_SHARE",
                "name": "Referral Data Sharing Consent",
                "description": "Standard consent for sharing patient data with referral partners",
                "policy_type": "referral",
                "data_categories": ["demographics", "diagnoses", "medications", "labs"],
                "permitted_use_cases": ["treatment", "care_coordination"],
                "default_duration_days": 90,
                "is_revocable": True,
                "requires_patient_signature": True,
                "template_text": "I authorize sharing my medical information with the referred facility for treatment purposes."
            }
        }


class ConsentPolicyUpdate(BaseModel):
    """Schema for updating a consent policy"""

    name: Optional[str] = None
    description: Optional[str] = None
    template_text: Optional[str] = None
    is_active: Optional[bool] = None


class ConsentPolicyResponse(BaseModel):
    """Response schema for consent policy"""

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    description: Optional[str] = None
    policy_type: str
    data_categories: List[str]
    permitted_use_cases: List[str]
    default_duration_days: Optional[int] = None
    is_revocable: bool
    requires_patient_signature: bool
    template_text: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConsentPolicyListResponse(BaseModel):
    """Response for list of consent policies"""

    total: int
    policies: List[ConsentPolicyResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Consent Record Schemas ====================

class ConsentRecordCreate(BaseModel):
    """Schema for creating a consent record"""

    patient_id: UUID
    policy_id: UUID
    data_controller_org_id: UUID = Field(..., description="Organization controlling the data")
    data_processor_org_id: Optional[UUID] = Field(None, description="Organization processing the data")
    app_id: Optional[UUID] = Field(None, description="App receiving access")
    consent_type: str = Field(default="explicit", description="explicit, implied, emergency_override")
    status: str = Field(default="active", description="active, revoked, expired")
    given_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    scope_overrides: Optional[Dict[str, Any]] = Field(
        None,
        description="Override default policy scope (narrower permissions)"
    )
    patient_signature: Optional[str] = Field(None, description="Digital signature or consent capture method")
    witness_user_id: Optional[UUID] = Field(None, description="Healthcare worker who witnessed consent")
    notes: Optional[str] = None

    @validator("consent_type")
    def validate_consent_type(cls, v):
        valid_types = ["explicit", "implied", "emergency_override", "opt_out"]
        if v.lower() not in valid_types:
            raise ValueError(f"consent_type must be one of: {', '.join(valid_types)}")
        return v.lower()

    @validator("status")
    def validate_status(cls, v):
        valid_statuses = ["active", "revoked", "expired", "pending"]
        if v.lower() not in valid_statuses:
            raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "patient_id": "patient-uuid-123",
                "policy_id": "policy-uuid-456",
                "data_controller_org_id": "org-internal",
                "data_processor_org_id": "org-apollo-blr",
                "consent_type": "explicit",
                "status": "active",
                "given_at": "2025-11-15T10:00:00Z",
                "expires_at": "2026-02-15T23:59:59Z",
                "scope_overrides": {
                    "exclude_categories": ["genetic_data"],
                    "read_only": True
                },
                "patient_signature": "electronic_signature_hash",
                "witness_user_id": "user-uuid-789"
            }
        }


class ConsentRecordUpdate(BaseModel):
    """Schema for updating a consent record"""

    status: Optional[str] = None
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None

    @validator("status")
    def validate_status(cls, v):
        if v:
            valid_statuses = ["active", "revoked", "expired", "pending"]
            if v.lower() not in valid_statuses:
                raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
            return v.lower()
        return v


class ConsentRecordResponse(BaseModel):
    """Response schema for consent record"""

    id: UUID
    patient_id: UUID
    policy_id: UUID
    data_controller_org_id: UUID
    data_processor_org_id: Optional[UUID] = None
    app_id: Optional[UUID] = None
    consent_type: str
    status: str
    given_at: datetime
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    scope_overrides: Optional[Dict[str, Any]] = None
    patient_signature: Optional[str] = None
    witness_user_id: Optional[UUID] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConsentRecordListResponse(BaseModel):
    """Response for list of consent records"""

    total: int
    consents: List[ConsentRecordResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Consent Evaluation Schemas ====================

class ConsentEvaluationRequest(BaseModel):
    """Request to evaluate if consent exists for an operation"""

    patient_id: UUID
    data_controller_org_id: UUID
    data_processor_org_id: Optional[UUID] = None
    app_id: Optional[UUID] = None
    requested_data_categories: List[str] = Field(..., description="Data categories being accessed")
    use_case: str = Field(..., description="Intended use case (treatment, research, etc.)")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class ConsentEvaluationResponse(BaseModel):
    """Response for consent evaluation"""

    has_consent: bool
    consent_records: List[ConsentRecordResponse] = Field(default_factory=list, description="Matching consents")
    policy_type: Optional[str] = None
    permitted_data_categories: List[str] = Field(default_factory=list)
    restrictions: Optional[Dict[str, Any]] = None
    reason: Optional[str] = Field(None, description="Reason if consent denied")
    emergency_override_available: bool = Field(
        default=False,
        description="True if emergency access override is available"
    )


# ==================== Consent Revocation Schema ====================

class ConsentRevocationRequest(BaseModel):
    """Request to revoke a consent"""

    reason: Optional[str] = Field(None, description="Reason for revocation")
    revoked_by_user_id: Optional[UUID] = Field(None, description="User who performed revocation")

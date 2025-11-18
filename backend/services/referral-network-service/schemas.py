"""
Referral Network Service Pydantic Schemas
Request/Response models for network organizations, referrals, and referral documents
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator


# ==================== Network Organization Schemas ====================

class NetworkOrganizationCreate(BaseModel):
    """Schema for creating a network organization"""

    code: str = Field(..., description="Unique org code (e.g., APOLLO_BLR, NARAYANA_HYD)")
    name: str = Field(..., description="Organization name")
    org_type: str = Field(..., description="HOSPITAL, CLINIC, LAB, DIAGNOSTIC_CENTER, HOMECARE")
    address: Optional[Dict[str, Any]] = Field(None, description="FHIR Address resource")
    contact: Optional[Dict[str, Any]] = Field(None, description="Contact details")
    interop_system_id: Optional[UUID] = Field(None, description="External system for data exchange")
    capabilities: Optional[Dict[str, Any]] = Field(None, description="Services offered")
    is_internal: bool = Field(default=False, description="True if this is our own organization")
    is_active: bool = Field(default=True)

    @validator("org_type")
    def validate_org_type(cls, v):
        valid_types = ["HOSPITAL", "CLINIC", "LAB", "DIAGNOSTIC_CENTER", "HOMECARE", "PHARMACY", "REHABILITATION"]
        if v.upper() not in valid_types:
            raise ValueError(f"org_type must be one of: {', '.join(valid_types)}")
        return v.upper()

    class Config:
        json_schema_extra = {
            "example": {
                "code": "APOLLO_BLR",
                "name": "Apollo Hospitals Bangalore",
                "org_type": "HOSPITAL",
                "address": {
                    "line": ["154/11, Bannerghatta Road"],
                    "city": "Bangalore",
                    "state": "Karnataka",
                    "postalCode": "560076",
                    "country": "IN"
                },
                "contact": {
                    "phone": "+91-80-26304050",
                    "email": "info@apollobangalore.com"
                },
                "capabilities": {
                    "specialties": ["CARDIOLOGY", "ONCOLOGY", "NEUROLOGY"],
                    "has_icu": True,
                    "has_emergency": True
                },
                "is_internal": False
            }
        }


class NetworkOrganizationUpdate(BaseModel):
    """Schema for updating a network organization"""

    name: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    contact: Optional[Dict[str, Any]] = None
    capabilities: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class NetworkOrganizationResponse(BaseModel):
    """Response schema for network organization"""

    id: UUID
    code: str
    name: str
    org_type: str
    address: Optional[Dict[str, Any]] = None
    contact: Optional[Dict[str, Any]] = None
    interop_system_id: Optional[UUID] = None
    capabilities: Optional[Dict[str, Any]] = None
    is_internal: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NetworkOrganizationListResponse(BaseModel):
    """Response for list of network organizations"""

    total: int
    organizations: List[NetworkOrganizationResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Referral Schemas ====================

class ReferralCreate(BaseModel):
    """Schema for creating a referral"""

    patient_id: UUID
    source_org_id: UUID
    target_org_id: UUID
    referral_type: str = Field(..., description="OPD, IPD_TRANSFER, DIAGNOSTIC, HOMECARE")
    service_line: Optional[str] = Field(None, description="CARDIOLOGY, ONCOLOGY, etc.")
    specialty: Optional[str] = None
    priority: str = Field(default="routine", description="routine, urgent, emergency")
    clinical_summary: str = Field(..., description="Reason for referral and clinical context")
    provisional_diagnosis: Optional[List[str]] = Field(None, description="ICD-10 or SNOMED codes")
    requested_services: Optional[List[str]] = Field(None, description="Specific services requested")
    requested_appointment_date: Optional[datetime] = None
    transport_required: bool = Field(default=False)
    metadata: Optional[Dict[str, Any]] = None

    @validator("referral_type")
    def validate_referral_type(cls, v):
        valid_types = ["OPD", "IPD_TRANSFER", "DIAGNOSTIC", "HOMECARE", "REHABILITATION"]
        if v.upper() not in valid_types:
            raise ValueError(f"referral_type must be one of: {', '.join(valid_types)}")
        return v.upper()

    @validator("priority")
    def validate_priority(cls, v):
        valid_priorities = ["routine", "urgent", "emergency"]
        if v.lower() not in valid_priorities:
            raise ValueError(f"priority must be one of: {', '.join(valid_priorities)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "patient_id": "patient-uuid-123",
                "source_org_id": "org-uuid-internal",
                "target_org_id": "org-uuid-apollo-blr",
                "referral_type": "OPD",
                "service_line": "CARDIOLOGY",
                "specialty": "Interventional Cardiology",
                "priority": "urgent",
                "clinical_summary": "62yo male with angina, abnormal stress test. Requires catheterization evaluation.",
                "provisional_diagnosis": ["I20.0"],
                "requested_services": ["coronary_angiography"],
                "requested_appointment_date": "2025-11-20T10:00:00Z",
                "transport_required": False
            }
        }


class ReferralUpdate(BaseModel):
    """Schema for updating a referral"""

    clinical_summary: Optional[str] = None
    requested_appointment_date: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class ReferralStatusUpdate(BaseModel):
    """Schema for status transitions"""

    status: str = Field(..., description="sent, accepted, rejected, scheduled, in_progress, completed, cancelled")
    status_reason: Optional[str] = None
    scheduled_appointment_time: Optional[datetime] = None
    outcome_summary: Optional[str] = None

    @validator("status")
    def validate_status(cls, v):
        valid_statuses = ["sent", "accepted", "rejected", "scheduled", "in_progress", "completed", "cancelled"]
        if v.lower() not in valid_statuses:
            raise ValueError(f"status must be one of: {', '.join(valid_statuses)}")
        return v.lower()


class ReferralResponse(BaseModel):
    """Response schema for referral"""

    id: UUID
    patient_id: UUID
    source_org_id: UUID
    target_org_id: UUID
    referral_type: str
    service_line: Optional[str] = None
    specialty: Optional[str] = None
    priority: str
    clinical_summary: str
    provisional_diagnosis: Optional[List[str]] = None
    requested_services: Optional[List[str]] = None
    status: str
    status_reason: Optional[str] = None
    requested_appointment_date: Optional[datetime] = None
    scheduled_appointment_time: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    outcome_summary: Optional[str] = None
    transport_required: bool
    fhir_service_request_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReferralListResponse(BaseModel):
    """Response for list of referrals"""

    total: int
    referrals: List[ReferralResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Referral Document Schemas ====================

class ReferralDocumentCreate(BaseModel):
    """Schema for attaching a document to a referral"""

    document_type: str = Field(..., description="CLINICAL_SUMMARY, LAB_REPORT, IMAGING, CONSENT_FORM")
    file_url: str = Field(..., description="URL to document in storage")
    file_name: str
    mime_type: str = Field(..., description="application/pdf, image/jpeg, etc.")
    file_size_bytes: Optional[int] = None
    description: Optional[str] = None
    fhir_document_reference_id: Optional[str] = None

    @validator("document_type")
    def validate_document_type(cls, v):
        valid_types = ["CLINICAL_SUMMARY", "LAB_REPORT", "IMAGING", "CONSENT_FORM", "PRESCRIPTION", "DISCHARGE_SUMMARY"]
        if v.upper() not in valid_types:
            raise ValueError(f"document_type must be one of: {', '.join(valid_types)}")
        return v.upper()


class ReferralDocumentResponse(BaseModel):
    """Response schema for referral document"""

    id: UUID
    referral_id: UUID
    document_type: str
    file_url: str
    file_name: str
    mime_type: str
    file_size_bytes: Optional[int] = None
    description: Optional[str] = None
    uploaded_by_user_id: UUID
    fhir_document_reference_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReferralDocumentListResponse(BaseModel):
    """Response for list of referral documents"""

    total: int
    documents: List[ReferralDocumentResponse]

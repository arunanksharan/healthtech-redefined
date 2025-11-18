"""
Interoperability Gateway Service Pydantic Schemas
Request/Response models for external systems, channels, mappings, and message logs
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator


# ==================== External System Schemas ====================

class ExternalSystemCreate(BaseModel):
    """Schema for creating an external system"""

    tenant_id: UUID
    code: str = Field(..., description="Unique system code (e.g., NARAYANA_ATHMA, APOLLO_EPIC)")
    name: str = Field(..., description="System name")
    system_type: str = Field(..., description="EHR, LIS, RIS, PAYER, APP")
    base_url: Optional[str] = None
    auth_type: Optional[str] = Field(None, description="basic, oauth2, mutual_tls, api_key")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="Authentication configuration")
    fhir_capability: Optional[Dict[str, Any]] = Field(None, description="FHIR capabilities")
    hl7v2_capability: Optional[Dict[str, Any]] = Field(None, description="HL7v2 capabilities")
    is_active: bool = Field(default=True)

    @validator("system_type")
    def validate_system_type(cls, v):
        valid_types = ["EHR", "LIS", "RIS", "PAYER", "APP", "IMAGING", "PHARMACY"]
        if v.upper() not in valid_types:
            raise ValueError(f"system_type must be one of: {', '.join(valid_types)}")
        return v.upper()

    @validator("auth_type")
    def validate_auth_type(cls, v):
        if v:
            valid_types = ["basic", "oauth2", "mutual_tls", "api_key", "none"]
            if v.lower() not in valid_types:
                raise ValueError(f"auth_type must be one of: {', '.join(valid_types)}")
            return v.lower()
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "code": "APOLLO_EPIC",
                "name": "Apollo Hospital EPIC EHR",
                "system_type": "EHR",
                "base_url": "https://epic.apollohospitals.com/fhir",
                "auth_type": "oauth2",
                "auth_config": {
                    "client_id": "healthtech_client",
                    "token_url": "https://epic.apollohospitals.com/oauth/token"
                },
                "fhir_capability": {
                    "version": "R4",
                    "resources": ["Patient", "Encounter", "Observation", "DiagnosticReport"]
                }
            }
        }


class ExternalSystemUpdate(BaseModel):
    """Schema for updating an external system"""

    name: Optional[str] = None
    base_url: Optional[str] = None
    auth_type: Optional[str] = None
    auth_config: Optional[Dict[str, Any]] = None
    fhir_capability: Optional[Dict[str, Any]] = None
    hl7v2_capability: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ExternalSystemResponse(BaseModel):
    """Response schema for external system"""

    id: UUID
    tenant_id: UUID
    code: str
    name: str
    system_type: str
    base_url: Optional[str] = None
    auth_type: Optional[str] = None
    auth_config: Optional[Dict[str, Any]] = None
    fhir_capability: Optional[Dict[str, Any]] = None
    hl7v2_capability: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExternalSystemListResponse(BaseModel):
    """Response for list of external systems"""

    total: int
    systems: List[ExternalSystemResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Interop Channel Schemas ====================

class InteropChannelCreate(BaseModel):
    """Schema for creating an interop channel"""

    tenant_id: UUID
    external_system_id: UUID
    channel_type: str = Field(..., description="FHIR_REST, HL7V2_TCP, WEBHOOK, SFTP_DROP")
    direction: str = Field(..., description="inbound, outbound, bidirectional")
    resource_scope: Dict[str, Any] = Field(..., description="Scope of resources/messages")
    mapping_profile_id: Optional[UUID] = None
    is_active: bool = Field(default=True)
    config: Optional[Dict[str, Any]] = Field(None, description="Channel-specific configuration")

    @validator("channel_type")
    def validate_channel_type(cls, v):
        valid_types = ["FHIR_REST", "HL7V2_TCP", "WEBHOOK", "SFTP_DROP", "DIRECT_DB"]
        if v.upper() not in valid_types:
            raise ValueError(f"channel_type must be one of: {', '.join(valid_types)}")
        return v.upper()

    @validator("direction")
    def validate_direction(cls, v):
        valid_directions = ["inbound", "outbound", "bidirectional"]
        if v.lower() not in valid_directions:
            raise ValueError(f"direction must be one of: {', '.join(valid_directions)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "external_system_id": "system-uuid-apollo-epic",
                "channel_type": "FHIR_REST",
                "direction": "bidirectional",
                "resource_scope": {
                    "fhir_resources": ["Patient", "Encounter", "Observation"]
                },
                "config": {
                    "endpoint": "https://epic.apollohospitals.com/fhir/R4",
                    "retry_policy": "exponential_backoff",
                    "timeout_seconds": 30
                }
            }
        }


class InteropChannelUpdate(BaseModel):
    """Schema for updating an interop channel"""

    resource_scope: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    config: Optional[Dict[str, Any]] = None


class InteropChannelResponse(BaseModel):
    """Response schema for interop channel"""

    id: UUID
    tenant_id: UUID
    external_system_id: UUID
    channel_type: str
    direction: str
    resource_scope: Dict[str, Any]
    mapping_profile_id: Optional[UUID] = None
    is_active: bool
    config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InteropChannelListResponse(BaseModel):
    """Response for list of interop channels"""

    total: int
    channels: List[InteropChannelResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Mapping Profile Schemas ====================

class MappingProfileCreate(BaseModel):
    """Schema for creating a mapping profile"""

    tenant_id: UUID
    name: str
    description: Optional[str] = None
    direction: str = Field(..., description="external_to_internal, internal_to_external")
    format: str = Field(..., description="FHIR_R4, HL7V2, CUSTOM_JSON")
    resource_type: Optional[str] = Field(None, description="Target resource type")
    mapping_rules: Dict[str, Any] = Field(..., description="Mapping rules DSL")
    version: str = Field(default="v1")
    is_active: bool = Field(default=True)

    @validator("direction")
    def validate_direction(cls, v):
        valid_directions = ["external_to_internal", "internal_to_external"]
        if v.lower() not in valid_directions:
            raise ValueError(f"direction must be one of: {', '.join(valid_directions)}")
        return v.lower()

    @validator("format")
    def validate_format(cls, v):
        valid_formats = ["FHIR_R4", "FHIR_R5", "HL7V2", "CUSTOM_JSON", "CUSTOM_XML"]
        if v.upper() not in valid_formats:
            raise ValueError(f"format must be one of: {', '.join(valid_formats)}")
        return v.upper()

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "name": "EPIC Patient to Internal Patient",
                "direction": "external_to_internal",
                "format": "FHIR_R4",
                "resource_type": "Patient",
                "mapping_rules": {
                    "identifier": "$.identifier",
                    "name": "$.name[0]",
                    "birthDate": "$.birthDate",
                    "gender": "$.gender"
                }
            }
        }


class MappingProfileResponse(BaseModel):
    """Response schema for mapping profile"""

    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str] = None
    direction: str
    format: str
    resource_type: Optional[str] = None
    mapping_rules: Dict[str, Any]
    version: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Interop Message Log Schemas ====================

class InteropMessageLogResponse(BaseModel):
    """Response schema for interop message log"""

    id: UUID
    tenant_id: UUID
    channel_id: UUID
    external_system_id: UUID
    direction: str
    message_type: Optional[str] = None
    correlation_id: Optional[str] = None
    raw_payload: Optional[str] = None
    mapped_resource_type: Optional[str] = None
    mapped_resource_id: Optional[str] = None
    status: str
    status_detail: Optional[str] = None
    occurred_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class InteropMessageLogListResponse(BaseModel):
    """Response for list of interop message logs"""

    total: int
    messages: List[InteropMessageLogResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Inbound Message Schemas ====================

class FHIRInboundRequest(BaseModel):
    """Schema for inbound FHIR resource"""

    resource: Dict[str, Any] = Field(..., description="FHIR resource JSON")
    correlation_id: Optional[str] = Field(None, description="For tracking request/response")

    class Config:
        json_schema_extra = {
            "example": {
                "resource": {
                    "resourceType": "Patient",
                    "id": "external-patient-123",
                    "identifier": [
                        {
                            "system": "http://apollo.com/patient-id",
                            "value": "APL-123456"
                        }
                    ],
                    "name": [
                        {
                            "family": "Kumar",
                            "given": ["Rajesh"]
                        }
                    ],
                    "birthDate": "1980-05-15",
                    "gender": "male"
                },
                "correlation_id": "msg-12345"
            }
        }


class FHIRInboundResponse(BaseModel):
    """Response for inbound FHIR resource"""

    message_log_id: UUID
    status: str
    mapped_resource_id: Optional[str] = None
    mapped_resource_type: Optional[str] = None
    errors: Optional[List[str]] = None


class HL7InboundRequest(BaseModel):
    """Schema for inbound HL7v2 message"""

    message: str = Field(..., description="HL7v2 message text")
    correlation_id: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "message": "MSH|^~\\&|APOLLO|EPIC|HEALTHTECH|HIS|20250115120000||ADT^A01|MSG00001|P|2.5\nPID|1||APL-123456||Kumar^Rajesh||19800515|M",
                "correlation_id": "msg-12345"
            }
        }


class HL7InboundResponse(BaseModel):
    """Response for inbound HL7v2 message"""

    message_log_id: UUID
    status: str
    message_type: Optional[str] = None
    ack_message: Optional[str] = None
    errors: Optional[List[str]] = None

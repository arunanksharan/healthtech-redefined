"""
Governance & Audit Service Pydantic Schemas
Request/Response models for LLM sessions, tool calls, responses, and policy violations
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, validator


# ==================== LLM Session Schemas ====================

class LLMSessionCreate(BaseModel):
    """Schema for creating an LLM session"""

    tenant_id: UUID
    user_id: Optional[UUID] = None
    patient_id: Optional[UUID] = None
    encounter_id: Optional[UUID] = None
    session_type: str = Field(
        ...,
        description="opd_scribe, cc_agent, care_coordinator, discharge_planner, triage_assistant, radiology_reporter"
    )
    model_name: str = Field(..., description="LLM model identifier (e.g., gpt-4, claude-3-opus)")
    model_version: Optional[str] = None
    system_prompt: Optional[str] = Field(None, description="System prompt used for session")
    initial_context: Optional[Dict[str, Any]] = Field(None, description="Initial context passed to LLM")
    safety_config: Optional[Dict[str, Any]] = Field(None, description="Safety guardrails configuration")

    @validator("session_type")
    def validate_session_type(cls, v):
        valid_types = [
            "opd_scribe", "cc_agent", "care_coordinator", "discharge_planner",
            "triage_assistant", "radiology_reporter", "pathology_reporter",
            "medication_reviewer", "icd_coder", "quality_analyst"
        ]
        if v.lower() not in valid_types:
            raise ValueError(f"session_type must be one of: {', '.join(valid_types)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "00000000-0000-0000-0000-000000000001",
                "user_id": "user-uuid-doctor-sharma",
                "encounter_id": "encounter-uuid-abc123",
                "session_type": "opd_scribe",
                "model_name": "gpt-4",
                "model_version": "gpt-4-0613",
                "system_prompt": "You are a medical scribe assistant...",
                "initial_context": {
                    "patient_age": 67,
                    "chief_complaint": "chest pain"
                },
                "safety_config": {
                    "check_pii": True,
                    "check_toxicity": True,
                    "max_tokens": 4000
                }
            }
        }


class LLMSessionResponse(BaseModel):
    """Response schema for LLM session"""

    id: UUID
    tenant_id: UUID
    user_id: Optional[UUID] = None
    patient_id: Optional[UUID] = None
    encounter_id: Optional[UUID] = None
    session_type: str
    model_name: str
    model_version: Optional[str] = None
    system_prompt: Optional[str] = None
    initial_context: Optional[Dict[str, Any]] = None
    safety_config: Optional[Dict[str, Any]] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    total_tokens: Optional[int] = None
    total_cost_usd: Optional[float] = None
    tool_call_count: Optional[int] = None
    response_count: Optional[int] = None
    violation_count: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EndSessionRequest(BaseModel):
    """Request to end an LLM session"""

    outcome: Optional[str] = Field(None, description="success, error, timeout, user_cancelled")
    final_summary: Optional[str] = Field(None, description="Summary of session outcome")


class LLMSessionListResponse(BaseModel):
    """Response for list of LLM sessions"""

    total: int
    sessions: List[LLMSessionResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool


# ==================== Tool Call Schemas ====================

class LLMToolCallCreate(BaseModel):
    """Schema for logging an LLM tool call"""

    tool_name: str = Field(..., description="Name of the tool called")
    tool_args: Dict[str, Any] = Field(..., description="Arguments passed to tool")
    tool_result: Optional[Dict[str, Any]] = Field(None, description="Result returned by tool")
    latency_ms: Optional[int] = Field(None, description="Tool execution time in milliseconds")
    success: bool = Field(default=True, description="Whether tool call succeeded")
    error_message: Optional[str] = Field(None, description="Error message if tool call failed")

    class Config:
        json_schema_extra = {
            "example": {
                "tool_name": "search_patient_history",
                "tool_args": {
                    "patient_id": "patient-uuid-abc123",
                    "lookback_days": 90
                },
                "tool_result": {
                    "visits": 3,
                    "diagnoses": ["I21.9", "E11.9"]
                },
                "latency_ms": 234,
                "success": True
            }
        }


class LLMToolCallResponse(BaseModel):
    """Response schema for tool call"""

    id: UUID
    llm_session_id: UUID
    tool_name: str
    tool_args: Dict[str, Any]
    tool_result: Optional[Dict[str, Any]] = None
    latency_ms: Optional[int] = None
    success: bool
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== LLM Response Schemas ====================

class LLMResponseCreate(BaseModel):
    """Schema for logging an LLM response"""

    prompt: str = Field(..., description="User prompt or message")
    response: str = Field(..., description="LLM response text")
    prompt_tokens: int = Field(..., description="Tokens in prompt")
    completion_tokens: int = Field(..., description="Tokens in completion")
    total_tokens: int = Field(..., description="Total tokens used")
    latency_ms: int = Field(..., description="Response generation time in milliseconds")
    finish_reason: Optional[str] = Field(None, description="stop, length, content_filter, tool_calls")
    safety_flags: Optional[List[str]] = Field(default_factory=list, description="Safety flags triggered")
    model_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional model metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Generate a discharge summary for this patient",
                "response": "# Discharge Summary\\n\\nPatient was admitted with...",
                "prompt_tokens": 512,
                "completion_tokens": 1024,
                "total_tokens": 1536,
                "latency_ms": 3200,
                "finish_reason": "stop",
                "safety_flags": [],
                "model_metadata": {
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            }
        }


class LLMResponseResponse(BaseModel):
    """Response schema for LLM response"""

    id: UUID
    llm_session_id: UUID
    prompt: str
    response: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: int
    finish_reason: Optional[str] = None
    safety_flags: List[str]
    model_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Policy Violation Schemas ====================

class PolicyViolationCreate(BaseModel):
    """Schema for reporting a policy violation"""

    violation_type: str = Field(
        ...,
        description="pii_exposure, toxicity, hallucination, unsafe_recommendation, policy_breach, data_leak"
    )
    severity: str = Field(..., description="low, medium, high, critical")
    description: str = Field(..., description="Description of the violation")
    detected_by: str = Field(..., description="automated, user_report, manual_review")
    evidence: Optional[Dict[str, Any]] = Field(None, description="Evidence of violation (text, metadata)")
    mitigation_action: Optional[str] = Field(None, description="Immediate action taken")

    @validator("violation_type")
    def validate_violation_type(cls, v):
        valid_types = [
            "pii_exposure", "toxicity", "hallucination", "unsafe_recommendation",
            "policy_breach", "data_leak", "bias", "off_topic"
        ]
        if v.lower() not in valid_types:
            raise ValueError(f"violation_type must be one of: {', '.join(valid_types)}")
        return v.lower()

    @validator("severity")
    def validate_severity(cls, v):
        valid_severities = ["low", "medium", "high", "critical"]
        if v.lower() not in valid_severities:
            raise ValueError(f"severity must be one of: {', '.join(valid_severities)}")
        return v.lower()

    @validator("detected_by")
    def validate_detected_by(cls, v):
        valid_detectors = ["automated", "user_report", "manual_review"]
        if v.lower() not in valid_detectors:
            raise ValueError(f"detected_by must be one of: {', '.join(valid_detectors)}")
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "violation_type": "pii_exposure",
                "severity": "high",
                "description": "LLM response contained patient phone number",
                "detected_by": "automated",
                "evidence": {
                    "response_text": "You can call the patient at 555-1234",
                    "detected_pii": "phone_number"
                },
                "mitigation_action": "Response blocked, user notified"
            }
        }


class PolicyViolationUpdate(BaseModel):
    """Schema for updating a policy violation"""

    resolution_status: Optional[str] = Field(None, description="open, investigating, resolved, false_positive")
    resolution_notes: Optional[str] = None
    resolved_by: Optional[UUID] = None
    resolved_at: Optional[datetime] = None

    @validator("resolution_status")
    def validate_resolution_status(cls, v):
        if v:
            valid_statuses = ["open", "investigating", "resolved", "false_positive"]
            if v.lower() not in valid_statuses:
                raise ValueError(f"resolution_status must be one of: {', '.join(valid_statuses)}")
            return v.lower()
        return v


class PolicyViolationResponse(BaseModel):
    """Response schema for policy violation"""

    id: UUID
    tenant_id: UUID
    llm_session_id: UUID
    violation_type: str
    severity: str
    description: str
    detected_by: str
    evidence: Optional[Dict[str, Any]] = None
    mitigation_action: Optional[str] = None
    resolution_status: str
    resolution_notes: Optional[str] = None
    resolved_by: Optional[UUID] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PolicyViolationListResponse(BaseModel):
    """Response for list of policy violations"""

    total: int
    violations: List[PolicyViolationResponse]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool

"""Ops Command Center API Service Schemas"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel
from decimal import Decimal


# Hospital Overview Schema
class RCMStatusResponse(BaseModel):
    preauth_pending: int
    preauth_sla_risk: int
    claims_to_submit: int
    denials_high_value: int
    ar_total: Optional[Decimal]


class TopAlert(BaseModel):
    alert_id: UUID
    domain: str
    severity: str
    description: str
    triggered_at: datetime


class HospitalOverviewResponse(BaseModel):
    timestamp: datetime
    hospital_occupancy: Optional[Decimal]
    icu_occupancy: Optional[Decimal]
    ed_crowding_index: Optional[Decimal]
    or_utilization_today: Optional[Decimal]
    lab_pending_critical: int
    imaging_pending_urgent: int
    rcm: RCMStatusResponse
    top_alerts: List[TopAlert]


# Unit Snapshot Schema
class UnitSnapshotResponse(BaseModel):
    id: UUID
    unit_id: UUID
    unit_code: str
    unit_name: str
    unit_type: str
    snapshot_time: datetime
    total_beds: Optional[int]
    occupied_beds: Optional[int]
    reserved_beds: Optional[int]
    blocked_beds: Optional[int]
    occupancy_rate: Optional[Decimal]
    acuity_index: Optional[Decimal]
    ed_waiting_count: Optional[int]
    ed_waiting_longer_than_30m: Optional[int]


# Bed Snapshot Schema
class BedSnapshotResponse(BaseModel):
    id: UUID
    bed_id: UUID
    unit_id: UUID
    snapshot_time: datetime
    status: str
    current_patient_id: Optional[UUID]
    current_encounter_id: Optional[UUID]
    last_status_change: Optional[datetime]
    isolation_flag: bool
    acuity_level: Optional[str]

    class Config:
        from_attributes = True


# OR Status Schema
class ORStatusSnapshotResponse(BaseModel):
    id: UUID
    or_room_id: UUID
    snapshot_time: datetime
    current_case_id: Optional[UUID]
    current_case_status: Optional[str]
    scheduled_case_count_today: Optional[int]
    completed_case_count_today: Optional[int]
    delayed_case_count_today: Optional[int]
    avg_delay_minutes_today: Optional[Decimal]
    utilization_rate_today: Optional[Decimal]

    class Config:
        from_attributes = True


# ED Status Schema
class EDStatusSnapshotResponse(BaseModel):
    id: UUID
    ed_unit_id: UUID
    snapshot_time: datetime
    total_in_ed: Optional[int]
    waiting_for_triage: Optional[int]
    waiting_for_provider: Optional[int]
    waiting_for_bed: Optional[int]
    avg_wait_time_triage_minutes: Optional[Decimal]
    avg_wait_time_provider_minutes: Optional[Decimal]
    lwbs_last_4h: Optional[int]

    class Config:
        from_attributes = True


# Lab Workload Schema
class LabWorkloadSnapshotResponse(BaseModel):
    id: UUID
    lab_unit_id: UUID
    snapshot_time: datetime
    total_pending: Optional[int]
    critical_pending: Optional[int]
    median_turnaround_minutes: Optional[Decimal]
    percentile90_turnaround_minutes: Optional[Decimal]
    pending_by_priority: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


# Imaging Workload Schema
class ImagingWorkloadSnapshotResponse(BaseModel):
    id: UUID
    imaging_unit_id: UUID
    snapshot_time: datetime
    total_pending: Optional[int]
    pending_urgent: Optional[int]
    median_report_turnaround_minutes: Optional[Decimal]
    pending_by_modality: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


# RCM Workload Schema
class RCMWorkloadSnapshotResponse(BaseModel):
    id: UUID
    snapshot_time: datetime
    preauth_pending: Optional[int]
    preauth_sla_breach_risk: Optional[int]
    claims_to_submit: Optional[int]
    claims_in_review: Optional[int]
    denials_open: Optional[int]
    denials_high_value: Optional[int]
    ar_total: Optional[Decimal]
    ar_aging_buckets: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


# Alert Schemas
class OpsAlertResponse(BaseModel):
    id: UUID
    alert_rule_id: Optional[UUID]
    domain: str
    metric_name: Optional[str]
    metric_value: Optional[Decimal]
    metric_context: Optional[Dict[str, Any]]
    severity: str
    status: str
    triggered_at: datetime
    resolved_at: Optional[datetime]
    assigned_user_id: Optional[UUID]
    assigned_team: Optional[str]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OpsAlertUpdateRequest(BaseModel):
    status: Optional[str] = None
    assigned_user_id: Optional[UUID] = None
    assigned_team: Optional[str] = None


# Playbook Schemas
class OpsPlaybookStepResponse(BaseModel):
    id: UUID
    step_order: int
    title: str
    instructions: str
    responsible_role: Optional[str]
    expected_completion_minutes: Optional[int]

    class Config:
        from_attributes = True


class OpsPlaybookResponse(BaseModel):
    id: UUID
    name: str
    domain: str
    trigger_alert_rule_id: Optional[UUID]
    description: Optional[str]
    is_active: bool
    steps: List[OpsPlaybookStepResponse]

    class Config:
        from_attributes = True

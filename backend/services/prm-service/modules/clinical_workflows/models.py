"""
Clinical Workflows Database Models

SQLAlchemy models for clinical workflow persistence.
All models support multi-tenancy via tenant_id.
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float,
    DateTime, ForeignKey, Enum as SQLEnum, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# ==================== Prescription Models ====================

class Prescription(Base):
    """Electronic prescription record."""
    __tablename__ = "prescriptions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    prescriber_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    encounter_id = Column(PGUUID(as_uuid=True), nullable=True)

    # Drug information
    rxnorm_code = Column(String(50), nullable=False, index=True)
    drug_name = Column(String(500), nullable=False)
    strength = Column(String(100))
    form = Column(String(100))  # tablet, capsule, liquid, etc.

    # Sig (directions)
    sig_text = Column(Text)
    dose = Column(Float)
    dose_unit = Column(String(50))
    route = Column(String(50))
    frequency = Column(String(100))
    duration = Column(String(100))
    duration_days = Column(Integer)
    as_needed = Column(Boolean, default=False)
    as_needed_reason = Column(String(255))
    special_instructions = Column(Text)

    # Quantity
    quantity = Column(Float, nullable=False)
    quantity_unit = Column(String(50))
    days_supply = Column(Integer)
    refills = Column(Integer, default=0)
    refills_remaining = Column(Integer, default=0)

    # Pharmacy
    pharmacy_id = Column(String(100))
    pharmacy_name = Column(String(255))
    pharmacy_ncpdp = Column(String(20))

    # Status
    status = Column(String(50), default="draft", index=True)
    dispense_as_written = Column(Boolean, default=False)

    # Controlled substance
    is_controlled = Column(Boolean, default=False)
    dea_schedule = Column(String(10))

    # Safety checks
    interactions_checked = Column(Boolean, default=False)
    allergies_checked = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    signed_at = Column(DateTime)
    signed_by = Column(PGUUID(as_uuid=True))
    sent_at = Column(DateTime)
    dispensed_at = Column(DateTime)
    expires_at = Column(DateTime)

    # Notes and metadata
    notes = Column(Text)
    overrides = Column(JSONB, default=list)  # Safety override records

    __table_args__ = (
        Index("ix_prescriptions_tenant_patient", "tenant_id", "patient_id"),
        Index("ix_prescriptions_tenant_status", "tenant_id", "status"),
    )


class DrugInteractionCheck(Base):
    """Drug interaction check record."""
    __tablename__ = "drug_interaction_checks"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    prescription_id = Column(PGUUID(as_uuid=True), ForeignKey("prescriptions.id"), nullable=False)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False)

    # Interaction details
    drug1_rxnorm = Column(String(50), nullable=False)
    drug2_rxnorm = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)  # severe, major, moderate, minor
    description = Column(Text)
    clinical_effects = Column(Text)
    management = Column(Text)

    # Override
    was_overridden = Column(Boolean, default=False)
    override_reason = Column(Text)
    overridden_by = Column(PGUUID(as_uuid=True))
    overridden_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)


# ==================== Lab Order Models ====================

class LabOrder(Base):
    """Laboratory order record."""
    __tablename__ = "lab_orders"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    ordering_provider_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    encounter_id = Column(PGUUID(as_uuid=True), nullable=True)

    # Order details
    tests = Column(JSONB, default=list)  # List of test objects with LOINC codes
    priority = Column(String(20), default="routine")  # routine, urgent, stat, asap
    clinical_indication = Column(Text)
    diagnosis_codes = Column(ARRAY(String(20)), default=list)

    # Lab routing
    performing_lab_id = Column(String(100))
    performing_lab_name = Column(String(255))
    lab_order_number = Column(String(100), index=True)

    # Collection
    fasting_required = Column(Boolean, default=False)
    fasting_status = Column(String(20))
    collection_site = Column(String(255))
    scheduled_date = Column(DateTime)

    # Status
    status = Column(String(50), default="draft", index=True)
    has_critical_results = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ordered_at = Column(DateTime)
    collected_at = Column(DateTime)
    resulted_at = Column(DateTime)
    reviewed_at = Column(DateTime)
    reviewed_by = Column(PGUUID(as_uuid=True))

    notes = Column(Text)

    results = relationship("LabResult", back_populates="order")

    __table_args__ = (
        Index("ix_lab_orders_tenant_patient", "tenant_id", "patient_id"),
        Index("ix_lab_orders_tenant_status", "tenant_id", "status"),
    )


class LabResult(Base):
    """Laboratory result record."""
    __tablename__ = "lab_results"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id = Column(PGUUID(as_uuid=True), ForeignKey("lab_orders.id"), nullable=False)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    # Test identification
    loinc_code = Column(String(20), nullable=False, index=True)
    test_name = Column(String(255), nullable=False)

    # Result value
    value = Column(String(255))
    value_numeric = Column(Float)
    units = Column(String(50))

    # Reference range
    reference_low = Column(Float)
    reference_high = Column(Float)
    reference_text = Column(String(255))

    # Interpretation
    interpretation = Column(String(10))  # N, L, H, LL, HH, A
    is_critical = Column(Boolean, default=False)
    is_abnormal = Column(Boolean, default=False)

    # Status
    status = Column(String(20), default="preliminary")  # preliminary, final, corrected

    # Timestamps
    resulted_at = Column(DateTime, default=datetime.utcnow)
    resulted_by = Column(String(255))

    notes = Column(Text)
    method = Column(String(255))

    order = relationship("LabOrder", back_populates="results")

    __table_args__ = (
        Index("ix_lab_results_tenant_patient", "tenant_id", "patient_id"),
        Index("ix_lab_results_loinc", "loinc_code"),
    )


# ==================== Imaging Models ====================

class ImagingOrder(Base):
    """Imaging/radiology order record."""
    __tablename__ = "imaging_orders"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    ordering_provider_id = Column(PGUUID(as_uuid=True), nullable=False)
    encounter_id = Column(PGUUID(as_uuid=True), nullable=True)

    # Procedure details
    procedure_code = Column(String(20), nullable=False)
    procedure_name = Column(String(255), nullable=False)
    modality = Column(String(10), nullable=False)  # XR, CT, MR, US, etc.
    body_part = Column(String(100))
    laterality = Column(String(20))  # left, right, bilateral

    # Clinical
    priority = Column(String(20), default="routine")
    clinical_indication = Column(Text)
    diagnosis_codes = Column(ARRAY(String(20)), default=list)

    # Contrast
    contrast_required = Column(Boolean, default=False)
    contrast_allergy_checked = Column(Boolean, default=False)

    # Safety
    pregnancy_status_checked = Column(Boolean, default=False)

    # Scheduling
    scheduled_datetime = Column(DateTime)
    performing_location = Column(String(255))

    # Status
    status = Column(String(50), default="draft", index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    notes = Column(Text)

    studies = relationship("ImagingStudy", back_populates="order")


class ImagingStudy(Base):
    """Completed imaging study."""
    __tablename__ = "imaging_studies"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    order_id = Column(PGUUID(as_uuid=True), ForeignKey("imaging_orders.id"))
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    # DICOM identifiers
    accession_number = Column(String(100), index=True)
    study_instance_uid = Column(String(100), unique=True)

    # Study details
    modality = Column(String(10), nullable=False)
    study_description = Column(String(255))
    body_part = Column(String(100))

    # Images
    num_series = Column(Integer, default=0)
    num_images = Column(Integer, default=0)

    # Dose tracking
    radiation_dose_msv = Column(Float)

    # PACS
    pacs_url = Column(String(500))

    # Timestamps
    study_datetime = Column(DateTime, default=datetime.utcnow)

    order = relationship("ImagingOrder", back_populates="studies")


class RadiologyReport(Base):
    """Radiology interpretation report."""
    __tablename__ = "radiology_reports"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    study_id = Column(PGUUID(as_uuid=True), ForeignKey("imaging_studies.id"), nullable=False)
    order_id = Column(PGUUID(as_uuid=True), nullable=False)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    # Report content
    impression = Column(Text)
    findings = Column(Text)
    comparison = Column(Text)
    technique = Column(Text)

    # Radiologist
    radiologist_id = Column(PGUUID(as_uuid=True))
    radiologist_name = Column(String(255))

    # Status
    status = Column(String(20), default="draft")  # draft, preliminary, final, addended

    # Timestamps
    dictated_at = Column(DateTime)
    finalized_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================== Referral Models ====================

class Referral(Base):
    """Patient referral to specialist/service."""
    __tablename__ = "referrals"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    encounter_id = Column(PGUUID(as_uuid=True), nullable=True)

    # Referring provider
    referring_provider_id = Column(PGUUID(as_uuid=True), nullable=False)
    referring_organization_id = Column(PGUUID(as_uuid=True))

    # Receiving provider
    receiving_provider_id = Column(PGUUID(as_uuid=True))
    receiving_organization_id = Column(PGUUID(as_uuid=True))
    target_specialty = Column(String(100), index=True)

    # Referral details
    referral_type = Column(String(50), default="consultation")
    priority = Column(String(20), default="routine")
    reason = Column(Text, nullable=False)
    clinical_question = Column(Text)

    # Diagnosis
    diagnosis_codes = Column(ARRAY(String(20)), default=list)

    # Authorization
    requires_authorization = Column(Boolean, default=False)
    authorization_number = Column(String(100))
    authorization_status = Column(String(20))
    authorized_visits = Column(Integer, default=1)

    # Scheduling
    preferred_date_start = Column(DateTime)
    preferred_date_end = Column(DateTime)
    scheduled_appointment_id = Column(PGUUID(as_uuid=True))
    scheduled_datetime = Column(DateTime)

    # Status
    status = Column(String(50), default="draft", index=True)

    # Response
    consultation_notes = Column(Text)
    recommendations = Column(Text)
    follow_up_needed = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sent_at = Column(DateTime)
    received_at = Column(DateTime)
    completed_at = Column(DateTime)

    documents = relationship("ReferralDocument", back_populates="referral")
    messages = relationship("ReferralMessage", back_populates="referral")


class ReferralDocument(Base):
    """Document attached to referral."""
    __tablename__ = "referral_documents"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    referral_id = Column(PGUUID(as_uuid=True), ForeignKey("referrals.id"), nullable=False)

    document_type = Column(String(50))  # clinical_notes, lab_results, imaging, consent
    file_name = Column(String(255), nullable=False)
    mime_type = Column(String(100))
    storage_url = Column(String(500), nullable=False)

    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(PGUUID(as_uuid=True))

    referral = relationship("Referral", back_populates="documents")


class ReferralMessage(Base):
    """Communication message for referral."""
    __tablename__ = "referral_messages"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    referral_id = Column(PGUUID(as_uuid=True), ForeignKey("referrals.id"), nullable=False)

    sender_id = Column(PGUUID(as_uuid=True), nullable=False)
    sender_type = Column(String(50))  # referring_provider, receiving_provider
    content = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime)

    referral = relationship("Referral", back_populates="messages")


# ==================== Clinical Documentation Models ====================

class ClinicalNote(Base):
    """Clinical documentation note."""
    __tablename__ = "clinical_notes"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    encounter_id = Column(PGUUID(as_uuid=True), index=True)
    author_id = Column(PGUUID(as_uuid=True), nullable=False)

    # Note type and template
    note_type = Column(String(50), nullable=False, index=True)
    template_id = Column(PGUUID(as_uuid=True))

    # Content
    title = Column(String(255))
    content = Column(Text)  # Full rendered content
    structured_content = Column(JSONB)  # SOAP structure

    # Coding
    diagnosis_codes = Column(JSONB, default=list)
    procedure_codes = Column(JSONB, default=list)

    # Status
    status = Column(String(50), default="draft", index=True)

    # Signatures
    signed_by = Column(PGUUID(as_uuid=True))
    signed_at = Column(DateTime)
    cosigned_by = Column(PGUUID(as_uuid=True))
    cosigned_at = Column(DateTime)

    # Amendments
    amendments = Column(JSONB, default=list)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_clinical_notes_tenant_patient", "tenant_id", "patient_id"),
        Index("ix_clinical_notes_encounter", "encounter_id"),
    )


class NoteTemplate(Base):
    """Clinical note template."""
    __tablename__ = "note_templates"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    note_type = Column(String(50), nullable=False)
    specialty = Column(String(100))

    sections = Column(JSONB, default=list)
    default_content = Column(JSONB, default=dict)
    smart_phrases = Column(ARRAY(String(100)), default=list)

    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SmartPhrase(Base):
    """Reusable text snippet/macro."""
    __tablename__ = "smart_phrases"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    owner_id = Column(PGUUID(as_uuid=True))  # NULL = shared

    abbreviation = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100))

    variables = Column(ARRAY(String(50)), default=list)

    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)


# ==================== Care Plan Models ====================

class CarePlan(Base):
    """Patient care plan."""
    __tablename__ = "care_plans"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    # Plan details
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(50), default="chronic_disease")

    # Addresses conditions
    condition_ids = Column(ARRAY(PGUUID(as_uuid=True)), default=list)

    # Author
    author_id = Column(PGUUID(as_uuid=True))

    # Timeline
    period_start = Column(DateTime)
    period_end = Column(DateTime)

    # Status
    status = Column(String(20), default="draft", index=True)

    # Related plans
    based_on_protocol_id = Column(PGUUID(as_uuid=True))
    replaces_plan_id = Column(PGUUID(as_uuid=True))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    goals = relationship("CareGoal", back_populates="care_plan")
    interventions = relationship("CareIntervention", back_populates="care_plan")
    team_members = relationship("CareTeamMember", back_populates="care_plan")


class CareGoal(Base):
    """Care plan goal."""
    __tablename__ = "care_goals"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    care_plan_id = Column(PGUUID(as_uuid=True), ForeignKey("care_plans.id"), nullable=False)
    patient_id = Column(PGUUID(as_uuid=True), nullable=False)

    # Goal definition
    category = Column(String(50))  # behavioral, dietary, physiological
    description = Column(Text, nullable=False)
    priority = Column(String(20), default="medium")

    # Targets
    targets = Column(JSONB, default=list)

    # Timeline
    start_date = Column(DateTime)
    target_date = Column(DateTime)

    # Status
    status = Column(String(20), default="proposed")
    achievement_status = Column(String(20), default="in_progress")

    # Owner
    owner_id = Column(PGUUID(as_uuid=True))

    created_at = Column(DateTime, default=datetime.utcnow)

    care_plan = relationship("CarePlan", back_populates="goals")
    progress_entries = relationship("GoalProgress", back_populates="goal")


class GoalProgress(Base):
    """Progress entry for a care goal."""
    __tablename__ = "goal_progress"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    goal_id = Column(PGUUID(as_uuid=True), ForeignKey("care_goals.id"), nullable=False)

    recorded_at = Column(DateTime, default=datetime.utcnow)
    recorded_by = Column(PGUUID(as_uuid=True), nullable=False)

    measure = Column(String(100), nullable=False)
    value = Column(String(255))
    value_numeric = Column(Float)
    unit = Column(String(50))

    achievement_status = Column(String(20), default="in_progress")
    notes = Column(Text)

    goal = relationship("CareGoal", back_populates="progress_entries")


class CareIntervention(Base):
    """Care plan intervention/activity."""
    __tablename__ = "care_interventions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    care_plan_id = Column(PGUUID(as_uuid=True), ForeignKey("care_plans.id"), nullable=False)
    goal_ids = Column(ARRAY(PGUUID(as_uuid=True)), default=list)

    # Intervention details
    category = Column(String(50))  # medication, procedure, education
    description = Column(Text, nullable=False)
    reason = Column(Text)

    # Timing
    scheduled_timing = Column(String(50))  # daily, weekly, as_needed
    scheduled_datetime = Column(DateTime)

    # Assignment
    assigned_to_id = Column(PGUUID(as_uuid=True))
    assigned_to_type = Column(String(20), default="practitioner")

    # Instructions
    instructions = Column(Text)

    # Status
    status = Column(String(20), default="planned")
    completed_at = Column(DateTime)
    outcome = Column(String(50))
    outcome_notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    care_plan = relationship("CarePlan", back_populates="interventions")


class CareTeamMember(Base):
    """Care team member."""
    __tablename__ = "care_team_members"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    care_plan_id = Column(PGUUID(as_uuid=True), ForeignKey("care_plans.id"), nullable=False)

    provider_id = Column(PGUUID(as_uuid=True))
    patient_id = Column(PGUUID(as_uuid=True))
    caregiver_id = Column(PGUUID(as_uuid=True))

    role = Column(String(50), nullable=False)
    name = Column(String(255))
    specialty = Column(String(100))
    contact_info = Column(String(255))

    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=True)

    care_plan = relationship("CarePlan", back_populates="team_members")


# ==================== Clinical Decision Support Models ====================

class ClinicalAlert(Base):
    """Clinical decision support alert."""
    __tablename__ = "clinical_alerts"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    # Alert details
    category = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # Source
    rule_id = Column(PGUUID(as_uuid=True))
    guideline_id = Column(PGUUID(as_uuid=True))

    # Context
    encounter_id = Column(PGUUID(as_uuid=True))
    order_id = Column(PGUUID(as_uuid=True))
    medication_id = Column(PGUUID(as_uuid=True))

    # Actions
    suggested_actions = Column(JSONB, default=list)

    # Status
    status = Column(String(20), default="active", index=True)
    acknowledged_by = Column(PGUUID(as_uuid=True))
    acknowledged_at = Column(DateTime)
    override_reason = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)


class CDSRule(Base):
    """Clinical decision support rule."""
    __tablename__ = "cds_rules"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False)

    # Conditions
    conditions = Column(JSONB, nullable=False)

    # Alert to generate
    alert_severity = Column(String(20), default="warning")
    alert_title_template = Column(String(255))
    alert_message_template = Column(Text)

    suggested_actions = Column(JSONB, default=list)

    priority = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    requires_override_reason = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ==================== Vital Signs Models ====================

class VitalSign(Base):
    """Vital sign measurement."""
    __tablename__ = "vital_signs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    encounter_id = Column(PGUUID(as_uuid=True), index=True)

    # Measurement type
    vital_type = Column(String(50), nullable=False, index=True)  # blood_pressure, heart_rate, temperature, etc.
    loinc_code = Column(String(20))

    # Value
    value = Column(Float)
    value_string = Column(String(50))  # For BP like "120/80"
    unit = Column(String(20))

    # Additional values (for BP, etc.)
    systolic = Column(Float)
    diastolic = Column(Float)

    # Interpretation
    is_abnormal = Column(Boolean, default=False)
    interpretation = Column(String(20))

    # Recording details
    recorded_at = Column(DateTime, default=datetime.utcnow)
    recorded_by = Column(PGUUID(as_uuid=True))
    device_id = Column(String(100))
    method = Column(String(50))  # manual, device, patient_reported
    position = Column(String(20))  # sitting, standing, supine

    notes = Column(Text)

    __table_args__ = (
        Index("ix_vital_signs_tenant_patient_type", "tenant_id", "patient_id", "vital_type"),
        Index("ix_vital_signs_recorded", "recorded_at"),
    )


class EarlyWarningScore(Base):
    """Early warning score calculation (NEWS, MEWS, etc.)."""
    __tablename__ = "early_warning_scores"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    encounter_id = Column(PGUUID(as_uuid=True))

    # Score type and value
    score_type = Column(String(20), nullable=False)  # NEWS, MEWS, PEWS
    total_score = Column(Integer, nullable=False)
    risk_level = Column(String(20))  # low, medium, high

    # Component scores
    component_scores = Column(JSONB, default=dict)

    # Vital signs used
    vital_sign_ids = Column(ARRAY(PGUUID(as_uuid=True)), default=list)

    # Timestamps
    calculated_at = Column(DateTime, default=datetime.utcnow)
    calculated_by = Column(PGUUID(as_uuid=True))

    # Alerts triggered
    alert_triggered = Column(Boolean, default=False)


# ==================== Discharge Models ====================

class DischargeRecord(Base):
    """Patient discharge record."""
    __tablename__ = "discharge_records"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    patient_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    encounter_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    # Discharge details
    discharge_disposition = Column(String(50))  # home, snf, rehab, expired
    discharge_destination = Column(String(255))

    # Checklist
    checklist_items = Column(JSONB, default=list)
    all_items_completed = Column(Boolean, default=False)

    # Medication reconciliation
    discharge_medications = Column(JSONB, default=list)
    med_reconciliation_completed = Column(Boolean, default=False)

    # Instructions
    discharge_instructions = Column(Text)
    activity_restrictions = Column(Text)
    diet_instructions = Column(Text)

    # Follow-up
    follow_up_appointments = Column(JSONB, default=list)
    follow_up_provider_id = Column(PGUUID(as_uuid=True))
    follow_up_date = Column(DateTime)

    # Readmission risk
    readmission_risk_score = Column(Float)
    readmission_risk_level = Column(String(20))

    # Status
    status = Column(String(20), default="pending")

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    completed_by = Column(PGUUID(as_uuid=True))

"""
Clinical Decision Support (CDS) Database Models

SQLAlchemy models for CDS data persistence:
- Drug interaction checking
- Drug-allergy alerts
- Clinical guidelines
- Quality measures and care gaps
- CDS Hooks integration
- Alert management
- AI diagnostic support

EPIC-020: Clinical Decision Support
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float, DateTime, Date,
    ForeignKey, JSON, Enum as SQLEnum, Index, UniqueConstraint,
    CheckConstraint, Numeric
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
import uuid
import enum

from shared.database import Base


# ============================================================================
# ENUMS
# ============================================================================

class InteractionSeverity(str, enum.Enum):
    """Drug interaction severity levels."""
    CONTRAINDICATED = "contraindicated"
    MAJOR = "major"
    MODERATE = "moderate"
    MINOR = "minor"
    UNKNOWN = "unknown"


class InteractionType(str, enum.Enum):
    """Types of drug interactions."""
    DRUG_DRUG = "drug_drug"
    DRUG_ALLERGY = "drug_allergy"
    DRUG_DISEASE = "drug_disease"
    DRUG_FOOD = "drug_food"
    DRUG_LAB = "drug_lab"
    DUPLICATE_THERAPY = "duplicate_therapy"


class AlertTier(str, enum.Enum):
    """Alert tier for display."""
    HARD_STOP = "hard_stop"  # Cannot proceed without override
    SOFT_STOP = "soft_stop"  # Warning with easy dismiss
    INFORMATIONAL = "informational"  # FYI only


class AlertStatus(str, enum.Enum):
    """Alert status in workflow."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    OVERRIDDEN = "overridden"
    DISMISSED = "dismissed"
    EXPIRED = "expired"


class OverrideReason(str, enum.Enum):
    """Standard override reasons."""
    BENEFIT_OUTWEIGHS_RISK = "benefit_outweighs_risk"
    PATIENT_TOLERATED_PREVIOUSLY = "patient_tolerated_previously"
    WILL_MONITOR = "will_monitor"
    DOSE_ADJUSTED = "dose_adjusted"
    NO_ALTERNATIVE = "no_alternative"
    PATIENT_REQUESTED = "patient_requested"
    EMERGENCY_SITUATION = "emergency_situation"
    CLINICAL_JUDGMENT = "clinical_judgment"
    OTHER = "other"


class GuidelineCategory(str, enum.Enum):
    """Categories of clinical guidelines."""
    TREATMENT = "treatment"
    DIAGNOSTIC = "diagnostic"
    PREVENTIVE = "preventive"
    SCREENING = "screening"
    MEDICATION = "medication"
    PROCEDURE = "procedure"
    LIFESTYLE = "lifestyle"


class GuidelineSource(str, enum.Enum):
    """Sources of clinical guidelines."""
    USPSTF = "uspstf"  # US Preventive Services Task Force
    AHA = "aha"  # American Heart Association
    ADA = "ada"  # American Diabetes Association
    AAFP = "aafp"  # American Academy of Family Physicians
    ACS = "acs"  # American Cancer Society
    CDC = "cdc"  # Centers for Disease Control
    UPTODATE = "uptodate"
    DYNAMED = "dynamed"
    CUSTOM = "custom"


class MeasureType(str, enum.Enum):
    """Types of quality measures."""
    HEDIS = "hedis"
    CMS = "cms"
    MIPS = "mips"
    STATE = "state"
    PAYER = "payer"
    CUSTOM = "custom"


class MeasureStatus(str, enum.Enum):
    """Status of measure evaluation."""
    MET = "met"
    NOT_MET = "not_met"
    EXCLUDED = "excluded"
    PENDING = "pending"
    IN_PROGRESS = "in_progress"


class CareGapPriority(str, enum.Enum):
    """Priority of care gaps."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CareGapStatus(str, enum.Enum):
    """Status of care gaps."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
    SNOOZED = "snoozed"
    NOT_APPLICABLE = "not_applicable"


class CDSHookType(str, enum.Enum):
    """CDS Hooks hook types."""
    PATIENT_VIEW = "patient-view"
    ORDER_SELECT = "order-select"
    ORDER_SIGN = "order-sign"
    MEDICATION_PRESCRIBE = "medication-prescribe"
    ENCOUNTER_START = "encounter-start"
    ENCOUNTER_DISCHARGE = "encounter-discharge"
    APPOINTMENT_BOOK = "appointment-book"


class CDSCardType(str, enum.Enum):
    """CDS card indicator types."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    SUCCESS = "success"


class DiagnosisSuggestionSource(str, enum.Enum):
    """Source of diagnostic suggestions."""
    AI_MODEL = "ai_model"
    CLINICAL_CRITERIA = "clinical_criteria"
    DIFFERENTIAL_ENGINE = "differential_engine"
    KNOWLEDGE_BASE = "knowledge_base"


# ============================================================================
# DRUG INTERACTION MODELS
# ============================================================================

class DrugDatabase(Base):
    """Drug reference database entries."""
    __tablename__ = "cds_drug_database"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Drug identification
    rxnorm_code = Column(String(20), nullable=False, index=True)
    ndc_codes = Column(ARRAY(String), default=list)
    name = Column(String(500), nullable=False)
    generic_name = Column(String(500), nullable=True)
    brand_names = Column(ARRAY(String), default=list)

    # Classification
    drug_class = Column(String(200), nullable=True)
    therapeutic_class = Column(String(200), nullable=True)
    pharmacologic_class = Column(String(200), nullable=True)
    atc_codes = Column(ARRAY(String), default=list)

    # Allergy mapping
    allergy_class_codes = Column(ARRAY(String), default=list)  # NDF-RT codes
    cross_reactive_classes = Column(ARRAY(String), default=list)

    # Metadata
    is_active = Column(Boolean, default=True)
    source = Column(String(50), default="fdb")  # fdb, medi_span
    last_updated = Column(DateTime(timezone=True), nullable=True)
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "rxnorm_code", name="uq_drug_rxnorm"),
        Index("idx_drug_name", "name"),
    )


class DrugInteractionRule(Base):
    """Drug interaction rules from knowledge base."""
    __tablename__ = "cds_drug_interaction_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Interaction pair
    drug1_rxnorm = Column(String(20), nullable=False, index=True)
    drug1_name = Column(String(500), nullable=True)
    drug2_rxnorm = Column(String(20), nullable=False, index=True)
    drug2_name = Column(String(500), nullable=True)

    # Alternative: class-level interactions
    drug_class1 = Column(String(200), nullable=True)
    drug_class2 = Column(String(200), nullable=True)
    is_class_interaction = Column(Boolean, default=False)

    # Interaction details
    interaction_type = Column(SQLEnum(InteractionType), default=InteractionType.DRUG_DRUG)
    severity = Column(SQLEnum(InteractionSeverity), nullable=False)
    description = Column(Text, nullable=False)
    clinical_effect = Column(Text, nullable=True)
    mechanism = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    management = Column(Text, nullable=True)

    # Evidence
    evidence_level = Column(String(20), nullable=True)  # established, probable, suspected
    references = Column(JSONB, default=list)
    source = Column(String(50), default="fdb")

    # Status
    is_active = Column(Boolean, default=True)
    last_updated = Column(DateTime(timezone=True), nullable=True)
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("idx_interaction_drugs", "drug1_rxnorm", "drug2_rxnorm"),
        Index("idx_interaction_severity", "severity"),
    )


class DrugAllergyMapping(Base):
    """Mapping between drugs and allergy classes for cross-reactivity."""
    __tablename__ = "cds_drug_allergy_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Drug
    drug_rxnorm = Column(String(20), nullable=False, index=True)
    drug_name = Column(String(500), nullable=True)

    # Allergy class
    allergy_class_code = Column(String(50), nullable=False)  # NDF-RT
    allergy_class_name = Column(String(200), nullable=False)

    # Cross-reactivity
    cross_reactive_drugs = Column(ARRAY(String), default=list)  # RxNorm codes
    cross_reactivity_risk = Column(String(20), default="unknown")  # high, moderate, low

    # Evidence
    evidence_level = Column(String(20), nullable=True)
    references = Column(JSONB, default=list)

    is_active = Column(Boolean, default=True)
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("idx_allergy_mapping_drug", "drug_rxnorm"),
        Index("idx_allergy_mapping_class", "allergy_class_code"),
    )


class DrugDiseaseContraindication(Base):
    """Drug-disease contraindications."""
    __tablename__ = "cds_drug_disease_contraindications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Drug
    drug_rxnorm = Column(String(20), nullable=False, index=True)
    drug_name = Column(String(500), nullable=True)
    drug_class = Column(String(200), nullable=True)
    is_class_contraindication = Column(Boolean, default=False)

    # Condition
    condition_code = Column(String(20), nullable=False, index=True)  # ICD-10 or SNOMED
    condition_code_system = Column(String(20), default="icd10")
    condition_name = Column(String(500), nullable=False)

    # Contraindication details
    severity = Column(SQLEnum(InteractionSeverity), nullable=False)
    description = Column(Text, nullable=False)
    clinical_effect = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    evidence_level = Column(String(20), nullable=True)
    references = Column(JSONB, default=list)
    source = Column(String(50), default="fdb")
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("idx_contraindication_drug", "drug_rxnorm"),
        Index("idx_contraindication_condition", "condition_code"),
    )


# ============================================================================
# ALERT MODELS
# ============================================================================

class CDSAlert(Base):
    """Clinical decision support alerts."""
    __tablename__ = "cds_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Context
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    encounter_id = Column(UUID(as_uuid=True), nullable=True)
    provider_id = Column(UUID(as_uuid=True), nullable=True)
    order_id = Column(UUID(as_uuid=True), nullable=True)

    # Alert details
    alert_type = Column(SQLEnum(InteractionType), nullable=False)
    severity = Column(SQLEnum(InteractionSeverity), nullable=False)
    tier = Column(SQLEnum(AlertTier), nullable=False)
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.ACTIVE)

    # Content
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSONB, default=dict)
    recommendation = Column(Text, nullable=True)

    # Related entities
    drug1_rxnorm = Column(String(20), nullable=True)
    drug1_name = Column(String(500), nullable=True)
    drug2_rxnorm = Column(String(20), nullable=True)
    drug2_name = Column(String(500), nullable=True)
    allergy_code = Column(String(50), nullable=True)
    condition_code = Column(String(20), nullable=True)

    # Source rule
    rule_id = Column(UUID(as_uuid=True), nullable=True)
    rule_source = Column(String(100), nullable=True)

    # Timestamps
    triggered_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    displayed_at = Column(DateTime(timezone=True), nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Response tracking
    response_time_ms = Column(Integer, nullable=True)
    was_helpful = Column(Boolean, nullable=True)

    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    overrides = relationship("AlertOverride", back_populates="alert", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_cds_alerts_patient_status", "patient_id", "status"),
        Index("idx_cds_alerts_tenant_severity", "tenant_id", "severity"),
        Index("idx_cds_alerts_triggered", "triggered_at"),
    )


class AlertOverride(Base):
    """Alert override documentation."""
    __tablename__ = "cds_alert_overrides"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    alert_id = Column(UUID(as_uuid=True), ForeignKey("cds_alerts.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Override details
    reason = Column(SQLEnum(OverrideReason), nullable=False)
    reason_other = Column(String(500), nullable=True)
    clinical_justification = Column(Text, nullable=False)
    will_monitor = Column(Boolean, default=False)
    monitoring_plan = Column(Text, nullable=True)

    # Context
    supervising_provider_id = Column(UUID(as_uuid=True), nullable=True)
    was_emergency = Column(Boolean, default=False)
    patient_consented = Column(Boolean, nullable=True)

    # Audit
    override_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    ip_address = Column(String(45), nullable=True)
    session_id = Column(String(100), nullable=True)

    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    alert = relationship("CDSAlert", back_populates="overrides")

    __table_args__ = (
        Index("idx_overrides_provider", "provider_id"),
        Index("idx_overrides_reason", "reason"),
    )


class AlertConfiguration(Base):
    """Alert configuration for organization."""
    __tablename__ = "cds_alert_configurations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Configuration scope
    alert_type = Column(SQLEnum(InteractionType), nullable=True)  # null = all types
    severity = Column(SQLEnum(InteractionSeverity), nullable=True)
    drug_class = Column(String(200), nullable=True)

    # Display settings
    tier = Column(SQLEnum(AlertTier), default=AlertTier.SOFT_STOP)
    is_enabled = Column(Boolean, default=True)
    is_suppressible = Column(Boolean, default=True)
    requires_override_reason = Column(Boolean, default=True)

    # Filtering
    min_severity = Column(SQLEnum(InteractionSeverity), default=InteractionSeverity.MINOR)
    exclude_conditions = Column(JSONB, default=list)
    include_only_conditions = Column(JSONB, default=list)

    # Context filters
    provider_roles = Column(ARRAY(String), default=list)  # Empty = all
    care_settings = Column(ARRAY(String), default=list)

    # Audit
    configured_by = Column(UUID(as_uuid=True), nullable=False)
    effective_from = Column(DateTime(timezone=True), nullable=True)
    effective_to = Column(DateTime(timezone=True), nullable=True)

    notes = Column(Text, nullable=True)
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_alert_config_tenant_type", "tenant_id", "alert_type"),
    )


class AlertAnalytics(Base):
    """Aggregated alert analytics."""
    __tablename__ = "cds_alert_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Aggregation period
    period_date = Column(Date, nullable=False)
    period_type = Column(String(20), default="daily")  # daily, weekly, monthly

    # Dimensions
    alert_type = Column(SQLEnum(InteractionType), nullable=True)
    severity = Column(SQLEnum(InteractionSeverity), nullable=True)
    provider_id = Column(UUID(as_uuid=True), nullable=True)
    department = Column(String(100), nullable=True)

    # Metrics
    total_alerts = Column(Integer, default=0)
    acknowledged_count = Column(Integer, default=0)
    overridden_count = Column(Integer, default=0)
    dismissed_count = Column(Integer, default=0)

    # Performance
    avg_response_time_ms = Column(Integer, nullable=True)
    median_response_time_ms = Column(Integer, nullable=True)

    # Effectiveness
    override_rate = Column(Float, nullable=True)
    adverse_events_prevented = Column(Integer, default=0)
    false_positive_count = Column(Integer, default=0)

    # Override reasons distribution
    override_reasons = Column(JSONB, default=dict)

    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "period_date", "period_type", "alert_type", "severity",
                         "provider_id", name="uq_alert_analytics"),
        Index("idx_alert_analytics_date", "tenant_id", "period_date"),
    )


# ============================================================================
# CLINICAL GUIDELINE MODELS
# ============================================================================

class ClinicalGuideline(Base):
    """Clinical guidelines content."""
    __tablename__ = "cds_clinical_guidelines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Identification
    external_id = Column(String(100), nullable=True)  # External source ID
    title = Column(String(500), nullable=False)
    short_title = Column(String(200), nullable=True)
    slug = Column(String(200), nullable=True)

    # Classification
    category = Column(SQLEnum(GuidelineCategory), nullable=False)
    source = Column(SQLEnum(GuidelineSource), nullable=False)
    publisher = Column(String(200), nullable=True)

    # Conditions this guideline applies to
    conditions = Column(ARRAY(String), default=list)  # ICD-10 or SNOMED codes
    condition_names = Column(ARRAY(String), default=list)

    # Content
    summary = Column(Text, nullable=True)
    key_recommendations = Column(JSONB, default=list)
    full_content = Column(Text, nullable=True)
    content_url = Column(String(500), nullable=True)

    # Evidence
    evidence_grade = Column(String(10), nullable=True)  # A, B, C, D
    recommendation_strength = Column(String(20), nullable=True)  # strong, conditional
    references = Column(JSONB, default=list)

    # Applicability
    patient_population = Column(Text, nullable=True)
    age_min = Column(Integer, nullable=True)
    age_max = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)  # male, female, all

    # Currency
    version = Column(String(20), nullable=True)
    published_date = Column(Date, nullable=True)
    last_reviewed = Column(Date, nullable=True)
    next_review = Column(Date, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)

    # Analytics
    view_count = Column(Integer, default=0)
    usefulness_rating = Column(Float, nullable=True)

    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_guidelines_category", "category"),
        Index("idx_guidelines_source", "source"),
        Index("idx_guidelines_active", "is_active"),
    )


class GuidelineAccess(Base):
    """Track guideline access for analytics."""
    __tablename__ = "cds_guideline_access"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    guideline_id = Column(UUID(as_uuid=True), ForeignKey("cds_clinical_guidelines.id"), nullable=False)
    provider_id = Column(UUID(as_uuid=True), nullable=False)
    patient_id = Column(UUID(as_uuid=True), nullable=True)
    encounter_id = Column(UUID(as_uuid=True), nullable=True)

    # Access context
    access_context = Column(String(50), nullable=True)  # chart_review, order_entry, etc.
    search_query = Column(String(500), nullable=True)
    was_recommended = Column(Boolean, default=False)

    # Engagement
    time_spent_seconds = Column(Integer, nullable=True)
    sections_viewed = Column(ARRAY(String), default=list)
    was_helpful = Column(Boolean, nullable=True)
    feedback = Column(Text, nullable=True)

    accessed_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("idx_guideline_access_guideline", "guideline_id"),
        Index("idx_guideline_access_provider", "provider_id"),
    )


# ============================================================================
# QUALITY MEASURE MODELS
# ============================================================================

class QualityMeasure(Base):
    """Quality measure definitions."""
    __tablename__ = "cds_quality_measures"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Identification
    measure_id = Column(String(50), nullable=False, index=True)  # e.g., CMS122v11
    title = Column(String(500), nullable=False)
    short_name = Column(String(100), nullable=True)
    version = Column(String(20), nullable=True)

    # Classification
    measure_type = Column(SQLEnum(MeasureType), nullable=False)
    category = Column(String(100), nullable=True)  # preventive, chronic, acute
    domain = Column(String(100), nullable=True)  # diabetes, cardiovascular, etc.

    # Description
    description = Column(Text, nullable=True)
    rationale = Column(Text, nullable=True)
    clinical_recommendation = Column(Text, nullable=True)

    # Population criteria
    initial_population_cql = Column(Text, nullable=True)
    denominator_cql = Column(Text, nullable=True)
    numerator_cql = Column(Text, nullable=True)
    exclusion_cql = Column(Text, nullable=True)
    exception_cql = Column(Text, nullable=True)

    # Performance targets
    target_rate = Column(Float, nullable=True)  # Expected compliance rate
    benchmark_rate = Column(Float, nullable=True)

    # Reporting
    reporting_period_start = Column(Date, nullable=True)
    reporting_period_end = Column(Date, nullable=True)
    submission_deadline = Column(Date, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    is_required = Column(Boolean, default=False)
    payer_ids = Column(ARRAY(UUID(as_uuid=True)), default=list)

    # Links
    specification_url = Column(String(500), nullable=True)
    value_set_oids = Column(ARRAY(String), default=list)

    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient_measures = relationship("PatientMeasure", back_populates="measure")

    __table_args__ = (
        UniqueConstraint("tenant_id", "measure_id", "version", name="uq_measure_version"),
        Index("idx_measures_type", "measure_type"),
        Index("idx_measures_active", "is_active"),
    )


class PatientMeasure(Base):
    """Patient-level quality measure evaluation."""
    __tablename__ = "cds_patient_measures"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    measure_id = Column(UUID(as_uuid=True), ForeignKey("cds_quality_measures.id"), nullable=False)

    # Evaluation period
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # Population flags
    in_initial_population = Column(Boolean, default=False)
    in_denominator = Column(Boolean, default=False)
    in_numerator = Column(Boolean, default=False)
    is_excluded = Column(Boolean, default=False)
    has_exception = Column(Boolean, default=False)

    # Status
    status = Column(SQLEnum(MeasureStatus), default=MeasureStatus.PENDING)
    evaluation_date = Column(DateTime(timezone=True), nullable=True)

    # Supporting data
    supporting_data = Column(JSONB, default=dict)
    exclusion_reason = Column(String(500), nullable=True)
    exception_reason = Column(String(500), nullable=True)

    # Actions needed
    gap_actions = Column(JSONB, default=list)  # Recommended actions to close gap

    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    measure = relationship("QualityMeasure", back_populates="patient_measures")

    __table_args__ = (
        UniqueConstraint("patient_id", "measure_id", "period_start", "period_end",
                         name="uq_patient_measure_period"),
        Index("idx_patient_measures_status", "status"),
    )


class CareGap(Base):
    """Identified care gaps for patients."""
    __tablename__ = "cds_care_gaps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    measure_id = Column(UUID(as_uuid=True), ForeignKey("cds_quality_measures.id"), nullable=True)
    patient_measure_id = Column(UUID(as_uuid=True), ForeignKey("cds_patient_measures.id"), nullable=True)

    # Gap details
    gap_type = Column(String(50), nullable=False)  # screening, vaccination, lab, medication
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(SQLEnum(CareGapPriority), default=CareGapPriority.MEDIUM)
    status = Column(SQLEnum(CareGapStatus), default=CareGapStatus.OPEN)

    # Recommended action
    recommended_action = Column(String(500), nullable=True)
    action_type = Column(String(50), nullable=True)  # order, referral, education
    order_code = Column(String(50), nullable=True)  # CPT/LOINC for orderables

    # Dates
    due_date = Column(Date, nullable=True)
    last_performed = Column(Date, nullable=True)
    closed_date = Column(Date, nullable=True)

    # Snooze
    snoozed_until = Column(Date, nullable=True)
    snooze_reason = Column(String(500), nullable=True)

    # Attribution
    attributed_provider_id = Column(UUID(as_uuid=True), nullable=True)
    closed_by_provider_id = Column(UUID(as_uuid=True), nullable=True)

    # Closure
    closure_evidence = Column(JSONB, default=dict)  # Related orders, results

    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_care_gaps_patient_status", "patient_id", "status"),
        Index("idx_care_gaps_priority", "priority"),
        Index("idx_care_gaps_due_date", "due_date"),
    )


# ============================================================================
# CDS HOOKS MODELS
# ============================================================================

class CDSService(Base):
    """Registered CDS services."""
    __tablename__ = "cds_services"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Service identification
    service_id = Column(String(100), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    hook = Column(SQLEnum(CDSHookType), nullable=False)

    # Endpoint
    endpoint_url = Column(String(500), nullable=False)
    is_internal = Column(Boolean, default=True)

    # Authentication
    auth_type = Column(String(50), nullable=True)  # none, bearer, basic, oauth2
    auth_credentials = Column(JSONB, default=dict)  # Encrypted

    # Prefetch
    prefetch_templates = Column(JSONB, default=dict)

    # Configuration
    is_enabled = Column(Boolean, default=True)
    timeout_ms = Column(Integer, default=5000)
    priority = Column(Integer, default=100)  # Lower = higher priority

    # Health
    last_health_check = Column(DateTime(timezone=True), nullable=True)
    is_healthy = Column(Boolean, default=True)
    failure_count = Column(Integer, default=0)

    # Analytics
    total_invocations = Column(Integer, default=0)
    avg_response_time_ms = Column(Integer, nullable=True)

    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "service_id", name="uq_cds_service"),
        Index("idx_cds_services_hook", "hook"),
        Index("idx_cds_services_enabled", "is_enabled"),
    )


class CDSHookInvocation(Base):
    """Log of CDS hook invocations."""
    __tablename__ = "cds_hook_invocations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Context
    hook_type = Column(SQLEnum(CDSHookType), nullable=False)
    hook_instance = Column(String(100), nullable=True)  # Unique per workflow
    patient_id = Column(UUID(as_uuid=True), nullable=False)
    encounter_id = Column(UUID(as_uuid=True), nullable=True)
    provider_id = Column(UUID(as_uuid=True), nullable=True)

    # Request
    request_context = Column(JSONB, default=dict)
    prefetch_data = Column(JSONB, default=dict)

    # Services invoked
    services_invoked = Column(ARRAY(String), default=list)

    # Response
    total_cards_returned = Column(Integer, default=0)
    cards_displayed = Column(Integer, default=0)
    response_time_ms = Column(Integer, nullable=True)

    # Errors
    had_errors = Column(Boolean, default=False)
    error_services = Column(ARRAY(String), default=list)

    invoked_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("idx_hook_invocations_patient", "patient_id"),
        Index("idx_hook_invocations_time", "invoked_at"),
    )


class CDSCard(Base):
    """CDS cards returned from services."""
    __tablename__ = "cds_cards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    invocation_id = Column(UUID(as_uuid=True), ForeignKey("cds_hook_invocations.id"), nullable=False)
    service_id = Column(String(100), nullable=False)

    # Card content
    uuid = Column(String(100), nullable=True)  # Card UUID from service
    summary = Column(String(500), nullable=False)
    detail = Column(Text, nullable=True)
    indicator = Column(SQLEnum(CDSCardType), default=CDSCardType.INFO)
    source_label = Column(String(200), nullable=True)
    source_url = Column(String(500), nullable=True)

    # Suggestions and actions
    suggestions = Column(JSONB, default=list)
    links = Column(JSONB, default=list)

    # Selection behavior
    selection_behavior = Column(String(50), nullable=True)

    # User interaction
    was_displayed = Column(Boolean, default=False)
    was_accepted = Column(Boolean, nullable=True)
    suggestion_selected = Column(String(100), nullable=True)
    link_clicked = Column(String(500), nullable=True)
    dismissed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        Index("idx_cds_cards_invocation", "invocation_id"),
        Index("idx_cds_cards_indicator", "indicator"),
    )


# ============================================================================
# DIAGNOSTIC SUPPORT MODELS
# ============================================================================

class DiagnosticSession(Base):
    """AI diagnostic support session."""
    __tablename__ = "cds_diagnostic_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Context
    patient_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    encounter_id = Column(UUID(as_uuid=True), nullable=True)
    provider_id = Column(UUID(as_uuid=True), nullable=False)

    # Input
    chief_complaint = Column(Text, nullable=True)
    symptoms = Column(JSONB, default=list)
    findings = Column(JSONB, default=list)  # Physical exam, vitals
    history = Column(JSONB, default=dict)  # Relevant medical history

    # Patient context
    patient_age = Column(Integer, nullable=True)
    patient_gender = Column(String(20), nullable=True)
    relevant_conditions = Column(ARRAY(String), default=list)
    relevant_medications = Column(ARRAY(String), default=list)

    # Session state
    status = Column(String(50), default="active")  # active, completed, abandoned
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    suggestions = relationship("DiagnosisSuggestion", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_diagnostic_sessions_patient", "patient_id"),
        Index("idx_diagnostic_sessions_provider", "provider_id"),
    )


class DiagnosisSuggestion(Base):
    """AI-suggested diagnoses."""
    __tablename__ = "cds_diagnosis_suggestions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    session_id = Column(UUID(as_uuid=True), ForeignKey("cds_diagnostic_sessions.id"), nullable=False)

    # Diagnosis
    diagnosis_code = Column(String(20), nullable=False)  # ICD-10
    diagnosis_code_system = Column(String(20), default="icd10")
    diagnosis_name = Column(String(500), nullable=False)

    # Probability
    probability = Column(Float, nullable=True)  # 0-1
    confidence = Column(Float, nullable=True)  # Model confidence
    rank = Column(Integer, nullable=True)

    # Classification
    source = Column(SQLEnum(DiagnosisSuggestionSource), nullable=False)
    is_cant_miss = Column(Boolean, default=False)  # Red flag diagnosis
    urgency = Column(String(20), nullable=True)  # emergent, urgent, routine

    # Reasoning
    reasoning = Column(Text, nullable=True)
    supporting_evidence = Column(JSONB, default=list)
    against_evidence = Column(JSONB, default=list)
    diagnostic_criteria = Column(JSONB, default=dict)

    # Recommended workup
    recommended_tests = Column(JSONB, default=list)
    recommended_imaging = Column(JSONB, default=list)
    recommended_referrals = Column(JSONB, default=list)

    # Provider feedback
    was_accepted = Column(Boolean, nullable=True)
    feedback_rating = Column(Integer, nullable=True)  # 1-5
    feedback_comment = Column(Text, nullable=True)
    final_diagnosis = Column(String(20), nullable=True)  # What was actually diagnosed

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    session = relationship("DiagnosticSession", back_populates="suggestions")

    __table_args__ = (
        Index("idx_diagnosis_suggestions_session", "session_id"),
        Index("idx_diagnosis_suggestions_code", "diagnosis_code"),
    )


class DiagnosticFeedback(Base):
    """Aggregated feedback for diagnostic model improvement."""
    __tablename__ = "cds_diagnostic_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Aggregation
    diagnosis_code = Column(String(20), nullable=False, index=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # Metrics
    times_suggested = Column(Integer, default=0)
    times_accepted = Column(Integer, default=0)
    times_rejected = Column(Integer, default=0)
    avg_probability_when_accepted = Column(Float, nullable=True)
    avg_probability_when_rejected = Column(Float, nullable=True)
    avg_rank_when_accepted = Column(Float, nullable=True)

    # Accuracy
    true_positives = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)
    false_negatives = Column(Integer, default=0)  # Correct diagnosis not suggested

    # Quality
    avg_rating = Column(Float, nullable=True)
    feedback_count = Column(Integer, default=0)

    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "diagnosis_code", "period_start", "period_end",
                         name="uq_diagnostic_feedback_period"),
    )

"""Clinical Decision Support

Revision ID: 020_clinical_decision_support
Revises: 019_remote_patient_monitoring
Create Date: 2024-11-25

EPIC-020: Creates tables for Clinical Decision Support system
- Drug interaction checking
- Drug-allergy alerts
- Clinical guidelines
- Quality measures and care gaps
- CDS Hooks integration
- Alert management
- AI diagnostic support
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

# revision identifiers
revision = '020_clinical_decision_support'
down_revision = '019_remote_patient_monitoring'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========================================================================
    # DRUG DATABASE TABLES
    # ========================================================================

    # Drug Database
    op.create_table(
        'cds_drug_database',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('rxnorm_code', sa.String(20), nullable=False),
        sa.Column('ndc_codes', ARRAY(sa.String), default=[]),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('generic_name', sa.String(500), nullable=True),
        sa.Column('brand_names', ARRAY(sa.String), default=[]),
        sa.Column('drug_class', sa.String(200), nullable=True),
        sa.Column('therapeutic_class', sa.String(200), nullable=True),
        sa.Column('pharmacologic_class', sa.String(200), nullable=True),
        sa.Column('atc_codes', ARRAY(sa.String), default=[]),
        sa.Column('allergy_class_codes', ARRAY(sa.String), default=[]),
        sa.Column('cross_reactive_classes', ARRAY(sa.String), default=[]),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('source', sa.String(50), default='fdb'),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'rxnorm_code', name='uq_drug_rxnorm'),
    )
    op.create_index('ix_cds_drug_database_tenant', 'cds_drug_database', ['tenant_id'])
    op.create_index('ix_cds_drug_database_rxnorm', 'cds_drug_database', ['rxnorm_code'])
    op.create_index('idx_drug_name', 'cds_drug_database', ['name'])

    # Drug Interaction Rules
    op.create_table(
        'cds_drug_interaction_rules',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('drug1_rxnorm', sa.String(20), nullable=False),
        sa.Column('drug1_name', sa.String(500), nullable=True),
        sa.Column('drug2_rxnorm', sa.String(20), nullable=False),
        sa.Column('drug2_name', sa.String(500), nullable=True),
        sa.Column('drug_class1', sa.String(200), nullable=True),
        sa.Column('drug_class2', sa.String(200), nullable=True),
        sa.Column('is_class_interaction', sa.Boolean, default=False),
        sa.Column('interaction_type', sa.String(30), default='drug_drug'),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('clinical_effect', sa.Text, nullable=True),
        sa.Column('mechanism', sa.Text, nullable=True),
        sa.Column('recommendation', sa.Text, nullable=True),
        sa.Column('management', sa.Text, nullable=True),
        sa.Column('evidence_level', sa.String(20), nullable=True),
        sa.Column('references', JSONB, default=[]),
        sa.Column('source', sa.String(50), default='fdb'),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_cds_drug_interaction_rules_tenant', 'cds_drug_interaction_rules', ['tenant_id'])
    op.create_index('idx_interaction_drugs', 'cds_drug_interaction_rules', ['drug1_rxnorm', 'drug2_rxnorm'])
    op.create_index('idx_interaction_severity', 'cds_drug_interaction_rules', ['severity'])

    # Drug Allergy Mappings
    op.create_table(
        'cds_drug_allergy_mappings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('drug_rxnorm', sa.String(20), nullable=False),
        sa.Column('drug_name', sa.String(500), nullable=True),
        sa.Column('allergy_class_code', sa.String(50), nullable=False),
        sa.Column('allergy_class_name', sa.String(200), nullable=False),
        sa.Column('cross_reactive_drugs', ARRAY(sa.String), default=[]),
        sa.Column('cross_reactivity_risk', sa.String(20), default='unknown'),
        sa.Column('evidence_level', sa.String(20), nullable=True),
        sa.Column('references', JSONB, default=[]),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_cds_drug_allergy_mappings_tenant', 'cds_drug_allergy_mappings', ['tenant_id'])
    op.create_index('idx_allergy_mapping_drug', 'cds_drug_allergy_mappings', ['drug_rxnorm'])
    op.create_index('idx_allergy_mapping_class', 'cds_drug_allergy_mappings', ['allergy_class_code'])

    # Drug Disease Contraindications
    op.create_table(
        'cds_drug_disease_contraindications',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('drug_rxnorm', sa.String(20), nullable=False),
        sa.Column('drug_name', sa.String(500), nullable=True),
        sa.Column('drug_class', sa.String(200), nullable=True),
        sa.Column('is_class_contraindication', sa.Boolean, default=False),
        sa.Column('condition_code', sa.String(20), nullable=False),
        sa.Column('condition_code_system', sa.String(20), default='icd10'),
        sa.Column('condition_name', sa.String(500), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('clinical_effect', sa.Text, nullable=True),
        sa.Column('recommendation', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('evidence_level', sa.String(20), nullable=True),
        sa.Column('references', JSONB, default=[]),
        sa.Column('source', sa.String(50), default='fdb'),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_cds_drug_disease_contraindications_tenant', 'cds_drug_disease_contraindications', ['tenant_id'])
    op.create_index('idx_contraindication_drug', 'cds_drug_disease_contraindications', ['drug_rxnorm'])
    op.create_index('idx_contraindication_condition', 'cds_drug_disease_contraindications', ['condition_code'])

    # ========================================================================
    # ALERT TABLES
    # ========================================================================

    # CDS Alerts
    op.create_table(
        'cds_alerts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', UUID(as_uuid=True), nullable=False),
        sa.Column('encounter_id', UUID(as_uuid=True), nullable=True),
        sa.Column('provider_id', UUID(as_uuid=True), nullable=True),
        sa.Column('order_id', UUID(as_uuid=True), nullable=True),
        sa.Column('alert_type', sa.String(30), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('tier', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('details', JSONB, default={}),
        sa.Column('recommendation', sa.Text, nullable=True),
        sa.Column('drug1_rxnorm', sa.String(20), nullable=True),
        sa.Column('drug1_name', sa.String(500), nullable=True),
        sa.Column('drug2_rxnorm', sa.String(20), nullable=True),
        sa.Column('drug2_name', sa.String(500), nullable=True),
        sa.Column('allergy_code', sa.String(50), nullable=True),
        sa.Column('condition_code', sa.String(20), nullable=True),
        sa.Column('rule_id', UUID(as_uuid=True), nullable=True),
        sa.Column('rule_source', sa.String(100), nullable=True),
        sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('displayed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('responded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('response_time_ms', sa.Integer, nullable=True),
        sa.Column('was_helpful', sa.Boolean, nullable=True),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_cds_alerts_tenant', 'cds_alerts', ['tenant_id'])
    op.create_index('ix_cds_alerts_patient', 'cds_alerts', ['patient_id'])
    op.create_index('idx_cds_alerts_patient_status', 'cds_alerts', ['patient_id', 'status'])
    op.create_index('idx_cds_alerts_tenant_severity', 'cds_alerts', ['tenant_id', 'severity'])
    op.create_index('idx_cds_alerts_triggered', 'cds_alerts', ['triggered_at'])

    # Alert Overrides
    op.create_table(
        'cds_alert_overrides',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('alert_id', UUID(as_uuid=True), sa.ForeignKey('cds_alerts.id'), nullable=False),
        sa.Column('provider_id', UUID(as_uuid=True), nullable=False),
        sa.Column('reason', sa.String(50), nullable=False),
        sa.Column('reason_other', sa.String(500), nullable=True),
        sa.Column('clinical_justification', sa.Text, nullable=False),
        sa.Column('will_monitor', sa.Boolean, default=False),
        sa.Column('monitoring_plan', sa.Text, nullable=True),
        sa.Column('supervising_provider_id', UUID(as_uuid=True), nullable=True),
        sa.Column('was_emergency', sa.Boolean, default=False),
        sa.Column('patient_consented', sa.Boolean, nullable=True),
        sa.Column('override_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_cds_alert_overrides_tenant', 'cds_alert_overrides', ['tenant_id'])
    op.create_index('idx_overrides_provider', 'cds_alert_overrides', ['provider_id'])
    op.create_index('idx_overrides_reason', 'cds_alert_overrides', ['reason'])

    # Alert Configurations
    op.create_table(
        'cds_alert_configurations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('alert_type', sa.String(30), nullable=True),
        sa.Column('severity', sa.String(20), nullable=True),
        sa.Column('drug_class', sa.String(200), nullable=True),
        sa.Column('tier', sa.String(20), default='soft_stop'),
        sa.Column('is_enabled', sa.Boolean, default=True),
        sa.Column('is_suppressible', sa.Boolean, default=True),
        sa.Column('requires_override_reason', sa.Boolean, default=True),
        sa.Column('min_severity', sa.String(20), default='minor'),
        sa.Column('exclude_conditions', JSONB, default=[]),
        sa.Column('include_only_conditions', JSONB, default=[]),
        sa.Column('provider_roles', ARRAY(sa.String), default=[]),
        sa.Column('care_settings', ARRAY(sa.String), default=[]),
        sa.Column('configured_by', UUID(as_uuid=True), nullable=False),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=True),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_cds_alert_configurations_tenant', 'cds_alert_configurations', ['tenant_id'])
    op.create_index('idx_alert_config_tenant_type', 'cds_alert_configurations', ['tenant_id', 'alert_type'])

    # Alert Analytics
    op.create_table(
        'cds_alert_analytics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('period_date', sa.Date, nullable=False),
        sa.Column('period_type', sa.String(20), default='daily'),
        sa.Column('alert_type', sa.String(30), nullable=True),
        sa.Column('severity', sa.String(20), nullable=True),
        sa.Column('provider_id', UUID(as_uuid=True), nullable=True),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('total_alerts', sa.Integer, default=0),
        sa.Column('acknowledged_count', sa.Integer, default=0),
        sa.Column('overridden_count', sa.Integer, default=0),
        sa.Column('dismissed_count', sa.Integer, default=0),
        sa.Column('avg_response_time_ms', sa.Integer, nullable=True),
        sa.Column('median_response_time_ms', sa.Integer, nullable=True),
        sa.Column('override_rate', sa.Float, nullable=True),
        sa.Column('adverse_events_prevented', sa.Integer, default=0),
        sa.Column('false_positive_count', sa.Integer, default=0),
        sa.Column('override_reasons', JSONB, default={}),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'period_date', 'period_type', 'alert_type', 'severity', 'provider_id',
                           name='uq_alert_analytics'),
    )
    op.create_index('ix_cds_alert_analytics_tenant', 'cds_alert_analytics', ['tenant_id'])
    op.create_index('idx_alert_analytics_date', 'cds_alert_analytics', ['tenant_id', 'period_date'])

    # ========================================================================
    # GUIDELINE TABLES
    # ========================================================================

    # Clinical Guidelines
    op.create_table(
        'cds_clinical_guidelines',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('external_id', sa.String(100), nullable=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('short_title', sa.String(200), nullable=True),
        sa.Column('slug', sa.String(200), nullable=True),
        sa.Column('category', sa.String(30), nullable=False),
        sa.Column('source', sa.String(30), nullable=False),
        sa.Column('publisher', sa.String(200), nullable=True),
        sa.Column('conditions', ARRAY(sa.String), default=[]),
        sa.Column('condition_names', ARRAY(sa.String), default=[]),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('key_recommendations', JSONB, default=[]),
        sa.Column('full_content', sa.Text, nullable=True),
        sa.Column('content_url', sa.String(500), nullable=True),
        sa.Column('evidence_grade', sa.String(10), nullable=True),
        sa.Column('recommendation_strength', sa.String(20), nullable=True),
        sa.Column('references', JSONB, default=[]),
        sa.Column('patient_population', sa.Text, nullable=True),
        sa.Column('age_min', sa.Integer, nullable=True),
        sa.Column('age_max', sa.Integer, nullable=True),
        sa.Column('gender', sa.String(20), nullable=True),
        sa.Column('version', sa.String(20), nullable=True),
        sa.Column('published_date', sa.Date, nullable=True),
        sa.Column('last_reviewed', sa.Date, nullable=True),
        sa.Column('next_review', sa.Date, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_featured', sa.Boolean, default=False),
        sa.Column('view_count', sa.Integer, default=0),
        sa.Column('usefulness_rating', sa.Float, nullable=True),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_cds_clinical_guidelines_tenant', 'cds_clinical_guidelines', ['tenant_id'])
    op.create_index('idx_guidelines_category', 'cds_clinical_guidelines', ['category'])
    op.create_index('idx_guidelines_source', 'cds_clinical_guidelines', ['source'])
    op.create_index('idx_guidelines_active', 'cds_clinical_guidelines', ['is_active'])

    # Guideline Access
    op.create_table(
        'cds_guideline_access',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('guideline_id', UUID(as_uuid=True), sa.ForeignKey('cds_clinical_guidelines.id'), nullable=False),
        sa.Column('provider_id', UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', UUID(as_uuid=True), nullable=True),
        sa.Column('encounter_id', UUID(as_uuid=True), nullable=True),
        sa.Column('access_context', sa.String(50), nullable=True),
        sa.Column('search_query', sa.String(500), nullable=True),
        sa.Column('was_recommended', sa.Boolean, default=False),
        sa.Column('time_spent_seconds', sa.Integer, nullable=True),
        sa.Column('sections_viewed', ARRAY(sa.String), default=[]),
        sa.Column('was_helpful', sa.Boolean, nullable=True),
        sa.Column('feedback', sa.Text, nullable=True),
        sa.Column('accessed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_cds_guideline_access_tenant', 'cds_guideline_access', ['tenant_id'])
    op.create_index('idx_guideline_access_guideline', 'cds_guideline_access', ['guideline_id'])
    op.create_index('idx_guideline_access_provider', 'cds_guideline_access', ['provider_id'])

    # ========================================================================
    # QUALITY MEASURE TABLES
    # ========================================================================

    # Quality Measures
    op.create_table(
        'cds_quality_measures',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('measure_id', sa.String(50), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('short_name', sa.String(100), nullable=True),
        sa.Column('version', sa.String(20), nullable=True),
        sa.Column('measure_type', sa.String(20), nullable=False),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('domain', sa.String(100), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('rationale', sa.Text, nullable=True),
        sa.Column('clinical_recommendation', sa.Text, nullable=True),
        sa.Column('initial_population_cql', sa.Text, nullable=True),
        sa.Column('denominator_cql', sa.Text, nullable=True),
        sa.Column('numerator_cql', sa.Text, nullable=True),
        sa.Column('exclusion_cql', sa.Text, nullable=True),
        sa.Column('exception_cql', sa.Text, nullable=True),
        sa.Column('target_rate', sa.Float, nullable=True),
        sa.Column('benchmark_rate', sa.Float, nullable=True),
        sa.Column('reporting_period_start', sa.Date, nullable=True),
        sa.Column('reporting_period_end', sa.Date, nullable=True),
        sa.Column('submission_deadline', sa.Date, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_required', sa.Boolean, default=False),
        sa.Column('payer_ids', ARRAY(UUID(as_uuid=True)), default=[]),
        sa.Column('specification_url', sa.String(500), nullable=True),
        sa.Column('value_set_oids', ARRAY(sa.String), default=[]),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'measure_id', 'version', name='uq_measure_version'),
    )
    op.create_index('ix_cds_quality_measures_tenant', 'cds_quality_measures', ['tenant_id'])
    op.create_index('idx_measures_type', 'cds_quality_measures', ['measure_type'])
    op.create_index('idx_measures_active', 'cds_quality_measures', ['is_active'])

    # Patient Measures
    op.create_table(
        'cds_patient_measures',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', UUID(as_uuid=True), nullable=False),
        sa.Column('measure_id', UUID(as_uuid=True), sa.ForeignKey('cds_quality_measures.id'), nullable=False),
        sa.Column('period_start', sa.Date, nullable=False),
        sa.Column('period_end', sa.Date, nullable=False),
        sa.Column('in_initial_population', sa.Boolean, default=False),
        sa.Column('in_denominator', sa.Boolean, default=False),
        sa.Column('in_numerator', sa.Boolean, default=False),
        sa.Column('is_excluded', sa.Boolean, default=False),
        sa.Column('has_exception', sa.Boolean, default=False),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('evaluation_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('supporting_data', JSONB, default={}),
        sa.Column('exclusion_reason', sa.String(500), nullable=True),
        sa.Column('exception_reason', sa.String(500), nullable=True),
        sa.Column('gap_actions', JSONB, default=[]),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('patient_id', 'measure_id', 'period_start', 'period_end', name='uq_patient_measure_period'),
    )
    op.create_index('ix_cds_patient_measures_tenant', 'cds_patient_measures', ['tenant_id'])
    op.create_index('ix_cds_patient_measures_patient', 'cds_patient_measures', ['patient_id'])
    op.create_index('idx_patient_measures_status', 'cds_patient_measures', ['status'])

    # Care Gaps
    op.create_table(
        'cds_care_gaps',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', UUID(as_uuid=True), nullable=False),
        sa.Column('measure_id', UUID(as_uuid=True), sa.ForeignKey('cds_quality_measures.id'), nullable=True),
        sa.Column('patient_measure_id', UUID(as_uuid=True), sa.ForeignKey('cds_patient_measures.id'), nullable=True),
        sa.Column('gap_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('priority', sa.String(20), default='medium'),
        sa.Column('status', sa.String(20), default='open'),
        sa.Column('recommended_action', sa.String(500), nullable=True),
        sa.Column('action_type', sa.String(50), nullable=True),
        sa.Column('order_code', sa.String(50), nullable=True),
        sa.Column('due_date', sa.Date, nullable=True),
        sa.Column('last_performed', sa.Date, nullable=True),
        sa.Column('closed_date', sa.Date, nullable=True),
        sa.Column('snoozed_until', sa.Date, nullable=True),
        sa.Column('snooze_reason', sa.String(500), nullable=True),
        sa.Column('attributed_provider_id', UUID(as_uuid=True), nullable=True),
        sa.Column('closed_by_provider_id', UUID(as_uuid=True), nullable=True),
        sa.Column('closure_evidence', JSONB, default={}),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_cds_care_gaps_tenant', 'cds_care_gaps', ['tenant_id'])
    op.create_index('ix_cds_care_gaps_patient', 'cds_care_gaps', ['patient_id'])
    op.create_index('idx_care_gaps_patient_status', 'cds_care_gaps', ['patient_id', 'status'])
    op.create_index('idx_care_gaps_priority', 'cds_care_gaps', ['priority'])
    op.create_index('idx_care_gaps_due_date', 'cds_care_gaps', ['due_date'])

    # ========================================================================
    # CDS HOOKS TABLES
    # ========================================================================

    # CDS Services
    op.create_table(
        'cds_services',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('service_id', sa.String(100), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('hook', sa.String(50), nullable=False),
        sa.Column('endpoint_url', sa.String(500), nullable=False),
        sa.Column('is_internal', sa.Boolean, default=True),
        sa.Column('auth_type', sa.String(50), nullable=True),
        sa.Column('auth_credentials', JSONB, default={}),
        sa.Column('prefetch_templates', JSONB, default={}),
        sa.Column('is_enabled', sa.Boolean, default=True),
        sa.Column('timeout_ms', sa.Integer, default=5000),
        sa.Column('priority', sa.Integer, default=100),
        sa.Column('last_health_check', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_healthy', sa.Boolean, default=True),
        sa.Column('failure_count', sa.Integer, default=0),
        sa.Column('total_invocations', sa.Integer, default=0),
        sa.Column('avg_response_time_ms', sa.Integer, nullable=True),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'service_id', name='uq_cds_service'),
    )
    op.create_index('ix_cds_services_tenant', 'cds_services', ['tenant_id'])
    op.create_index('idx_cds_services_hook', 'cds_services', ['hook'])
    op.create_index('idx_cds_services_enabled', 'cds_services', ['is_enabled'])

    # CDS Hook Invocations
    op.create_table(
        'cds_hook_invocations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('hook_type', sa.String(50), nullable=False),
        sa.Column('hook_instance', sa.String(100), nullable=True),
        sa.Column('patient_id', UUID(as_uuid=True), nullable=False),
        sa.Column('encounter_id', UUID(as_uuid=True), nullable=True),
        sa.Column('provider_id', UUID(as_uuid=True), nullable=True),
        sa.Column('request_context', JSONB, default={}),
        sa.Column('prefetch_data', JSONB, default={}),
        sa.Column('services_invoked', ARRAY(sa.String), default=[]),
        sa.Column('total_cards_returned', sa.Integer, default=0),
        sa.Column('cards_displayed', sa.Integer, default=0),
        sa.Column('response_time_ms', sa.Integer, nullable=True),
        sa.Column('had_errors', sa.Boolean, default=False),
        sa.Column('error_services', ARRAY(sa.String), default=[]),
        sa.Column('invoked_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_cds_hook_invocations_tenant', 'cds_hook_invocations', ['tenant_id'])
    op.create_index('idx_hook_invocations_patient', 'cds_hook_invocations', ['patient_id'])
    op.create_index('idx_hook_invocations_time', 'cds_hook_invocations', ['invoked_at'])

    # CDS Cards
    op.create_table(
        'cds_cards',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('invocation_id', UUID(as_uuid=True), sa.ForeignKey('cds_hook_invocations.id'), nullable=False),
        sa.Column('service_id', sa.String(100), nullable=False),
        sa.Column('uuid', sa.String(100), nullable=True),
        sa.Column('summary', sa.String(500), nullable=False),
        sa.Column('detail', sa.Text, nullable=True),
        sa.Column('indicator', sa.String(20), default='info'),
        sa.Column('source_label', sa.String(200), nullable=True),
        sa.Column('source_url', sa.String(500), nullable=True),
        sa.Column('suggestions', JSONB, default=[]),
        sa.Column('links', JSONB, default=[]),
        sa.Column('selection_behavior', sa.String(50), nullable=True),
        sa.Column('was_displayed', sa.Boolean, default=False),
        sa.Column('was_accepted', sa.Boolean, nullable=True),
        sa.Column('suggestion_selected', sa.String(100), nullable=True),
        sa.Column('link_clicked', sa.String(500), nullable=True),
        sa.Column('dismissed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_cds_cards_tenant', 'cds_cards', ['tenant_id'])
    op.create_index('idx_cds_cards_invocation', 'cds_cards', ['invocation_id'])
    op.create_index('idx_cds_cards_indicator', 'cds_cards', ['indicator'])

    # ========================================================================
    # DIAGNOSTIC SUPPORT TABLES
    # ========================================================================

    # Diagnostic Sessions
    op.create_table(
        'cds_diagnostic_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', UUID(as_uuid=True), nullable=False),
        sa.Column('encounter_id', UUID(as_uuid=True), nullable=True),
        sa.Column('provider_id', UUID(as_uuid=True), nullable=False),
        sa.Column('chief_complaint', sa.Text, nullable=True),
        sa.Column('symptoms', JSONB, default=[]),
        sa.Column('findings', JSONB, default=[]),
        sa.Column('history', JSONB, default={}),
        sa.Column('patient_age', sa.Integer, nullable=True),
        sa.Column('patient_gender', sa.String(20), nullable=True),
        sa.Column('relevant_conditions', ARRAY(sa.String), default=[]),
        sa.Column('relevant_medications', ARRAY(sa.String), default=[]),
        sa.Column('status', sa.String(50), default='active'),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_cds_diagnostic_sessions_tenant', 'cds_diagnostic_sessions', ['tenant_id'])
    op.create_index('idx_diagnostic_sessions_patient', 'cds_diagnostic_sessions', ['patient_id'])
    op.create_index('idx_diagnostic_sessions_provider', 'cds_diagnostic_sessions', ['provider_id'])

    # Diagnosis Suggestions
    op.create_table(
        'cds_diagnosis_suggestions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('cds_diagnostic_sessions.id'), nullable=False),
        sa.Column('diagnosis_code', sa.String(20), nullable=False),
        sa.Column('diagnosis_code_system', sa.String(20), default='icd10'),
        sa.Column('diagnosis_name', sa.String(500), nullable=False),
        sa.Column('probability', sa.Float, nullable=True),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('rank', sa.Integer, nullable=True),
        sa.Column('source', sa.String(30), nullable=False),
        sa.Column('is_cant_miss', sa.Boolean, default=False),
        sa.Column('urgency', sa.String(20), nullable=True),
        sa.Column('reasoning', sa.Text, nullable=True),
        sa.Column('supporting_evidence', JSONB, default=[]),
        sa.Column('against_evidence', JSONB, default=[]),
        sa.Column('diagnostic_criteria', JSONB, default={}),
        sa.Column('recommended_tests', JSONB, default=[]),
        sa.Column('recommended_imaging', JSONB, default=[]),
        sa.Column('recommended_referrals', JSONB, default=[]),
        sa.Column('was_accepted', sa.Boolean, nullable=True),
        sa.Column('feedback_rating', sa.Integer, nullable=True),
        sa.Column('feedback_comment', sa.Text, nullable=True),
        sa.Column('final_diagnosis', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_cds_diagnosis_suggestions_tenant', 'cds_diagnosis_suggestions', ['tenant_id'])
    op.create_index('idx_diagnosis_suggestions_session', 'cds_diagnosis_suggestions', ['session_id'])
    op.create_index('idx_diagnosis_suggestions_code', 'cds_diagnosis_suggestions', ['diagnosis_code'])

    # Diagnostic Feedback
    op.create_table(
        'cds_diagnostic_feedback',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('diagnosis_code', sa.String(20), nullable=False),
        sa.Column('period_start', sa.Date, nullable=False),
        sa.Column('period_end', sa.Date, nullable=False),
        sa.Column('times_suggested', sa.Integer, default=0),
        sa.Column('times_accepted', sa.Integer, default=0),
        sa.Column('times_rejected', sa.Integer, default=0),
        sa.Column('avg_probability_when_accepted', sa.Float, nullable=True),
        sa.Column('avg_probability_when_rejected', sa.Float, nullable=True),
        sa.Column('avg_rank_when_accepted', sa.Float, nullable=True),
        sa.Column('true_positives', sa.Integer, default=0),
        sa.Column('false_positives', sa.Integer, default=0),
        sa.Column('false_negatives', sa.Integer, default=0),
        sa.Column('avg_rating', sa.Float, nullable=True),
        sa.Column('feedback_count', sa.Integer, default=0),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'diagnosis_code', 'period_start', 'period_end',
                           name='uq_diagnostic_feedback_period'),
    )
    op.create_index('ix_cds_diagnostic_feedback_tenant', 'cds_diagnostic_feedback', ['tenant_id'])
    op.create_index('ix_cds_diagnostic_feedback_diagnosis', 'cds_diagnostic_feedback', ['diagnosis_code'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('cds_diagnostic_feedback')
    op.drop_table('cds_diagnosis_suggestions')
    op.drop_table('cds_diagnostic_sessions')
    op.drop_table('cds_cards')
    op.drop_table('cds_hook_invocations')
    op.drop_table('cds_services')
    op.drop_table('cds_care_gaps')
    op.drop_table('cds_patient_measures')
    op.drop_table('cds_quality_measures')
    op.drop_table('cds_guideline_access')
    op.drop_table('cds_clinical_guidelines')
    op.drop_table('cds_alert_analytics')
    op.drop_table('cds_alert_configurations')
    op.drop_table('cds_alert_overrides')
    op.drop_table('cds_alerts')
    op.drop_table('cds_drug_disease_contraindications')
    op.drop_table('cds_drug_allergy_mappings')
    op.drop_table('cds_drug_interaction_rules')
    op.drop_table('cds_drug_database')

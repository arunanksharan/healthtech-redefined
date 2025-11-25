"""EPIC-006: Clinical Workflows Database Tables

Revision ID: 003_clinical_workflows
Revises: 002_multi_tenancy_rls
Create Date: 2024-01-15

This migration creates all tables for EPIC-006 Clinical Workflows:
- Prescriptions (US-006.1)
- Lab Orders & Results (US-006.2)
- Imaging Orders & Studies (US-006.3)
- Referrals (US-006.4)
- Clinical Notes & Templates (US-006.5)
- Care Plans, Goals, Interventions (US-006.7)
- Clinical Alerts & CDS Rules (US-006.9)
- Vital Signs (US-006.10)
- Discharge Records (US-006.8)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '003_clinical_workflows'
down_revision = '002_multi_tenancy_rls'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==================== Prescriptions ====================
    op.create_table(
        'prescriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prescriber_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('rxnorm_code', sa.String(50), nullable=False),
        sa.Column('drug_name', sa.String(500), nullable=False),
        sa.Column('strength', sa.String(100)),
        sa.Column('form', sa.String(100)),
        sa.Column('sig_text', sa.Text),
        sa.Column('dose', sa.Float),
        sa.Column('dose_unit', sa.String(50)),
        sa.Column('route', sa.String(50)),
        sa.Column('frequency', sa.String(100)),
        sa.Column('duration', sa.String(100)),
        sa.Column('duration_days', sa.Integer),
        sa.Column('as_needed', sa.Boolean, default=False),
        sa.Column('as_needed_reason', sa.String(255)),
        sa.Column('special_instructions', sa.Text),
        sa.Column('quantity', sa.Float, nullable=False),
        sa.Column('quantity_unit', sa.String(50)),
        sa.Column('days_supply', sa.Integer),
        sa.Column('refills', sa.Integer, default=0),
        sa.Column('refills_remaining', sa.Integer, default=0),
        sa.Column('pharmacy_id', sa.String(100)),
        sa.Column('pharmacy_name', sa.String(255)),
        sa.Column('pharmacy_ncpdp', sa.String(20)),
        sa.Column('status', sa.String(50), default='draft'),
        sa.Column('dispense_as_written', sa.Boolean, default=False),
        sa.Column('is_controlled', sa.Boolean, default=False),
        sa.Column('dea_schedule', sa.String(10)),
        sa.Column('interactions_checked', sa.Boolean, default=False),
        sa.Column('allergies_checked', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('signed_at', sa.DateTime),
        sa.Column('signed_by', postgresql.UUID(as_uuid=True)),
        sa.Column('sent_at', sa.DateTime),
        sa.Column('dispensed_at', sa.DateTime),
        sa.Column('expires_at', sa.DateTime),
        sa.Column('notes', sa.Text),
        sa.Column('overrides', postgresql.JSONB, default=[]),
    )
    op.create_index('ix_prescriptions_tenant_id', 'prescriptions', ['tenant_id'])
    op.create_index('ix_prescriptions_patient_id', 'prescriptions', ['patient_id'])
    op.create_index('ix_prescriptions_rxnorm_code', 'prescriptions', ['rxnorm_code'])
    op.create_index('ix_prescriptions_status', 'prescriptions', ['status'])
    op.create_index('ix_prescriptions_tenant_patient', 'prescriptions', ['tenant_id', 'patient_id'])

    # Drug interaction checks
    op.create_table(
        'drug_interaction_checks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('prescription_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('prescriptions.id')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('drug1_rxnorm', sa.String(50), nullable=False),
        sa.Column('drug2_rxnorm', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('clinical_effects', sa.Text),
        sa.Column('management', sa.Text),
        sa.Column('was_overridden', sa.Boolean, default=False),
        sa.Column('override_reason', sa.Text),
        sa.Column('overridden_by', postgresql.UUID(as_uuid=True)),
        sa.Column('overridden_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # ==================== Lab Orders ====================
    op.create_table(
        'lab_orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ordering_provider_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True)),
        sa.Column('tests', postgresql.JSONB, default=[]),
        sa.Column('priority', sa.String(20), default='routine'),
        sa.Column('clinical_indication', sa.Text),
        sa.Column('diagnosis_codes', postgresql.ARRAY(sa.String(20)), default=[]),
        sa.Column('performing_lab_id', sa.String(100)),
        sa.Column('performing_lab_name', sa.String(255)),
        sa.Column('lab_order_number', sa.String(100)),
        sa.Column('fasting_required', sa.Boolean, default=False),
        sa.Column('fasting_status', sa.String(20)),
        sa.Column('collection_site', sa.String(255)),
        sa.Column('scheduled_date', sa.DateTime),
        sa.Column('status', sa.String(50), default='draft'),
        sa.Column('has_critical_results', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('ordered_at', sa.DateTime),
        sa.Column('collected_at', sa.DateTime),
        sa.Column('resulted_at', sa.DateTime),
        sa.Column('reviewed_at', sa.DateTime),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True)),
        sa.Column('notes', sa.Text),
    )
    op.create_index('ix_lab_orders_tenant_id', 'lab_orders', ['tenant_id'])
    op.create_index('ix_lab_orders_patient_id', 'lab_orders', ['patient_id'])
    op.create_index('ix_lab_orders_status', 'lab_orders', ['status'])
    op.create_index('ix_lab_orders_lab_order_number', 'lab_orders', ['lab_order_number'])

    # Lab results
    op.create_table(
        'lab_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('lab_orders.id')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('loinc_code', sa.String(20), nullable=False),
        sa.Column('test_name', sa.String(255), nullable=False),
        sa.Column('value', sa.String(255)),
        sa.Column('value_numeric', sa.Float),
        sa.Column('units', sa.String(50)),
        sa.Column('reference_low', sa.Float),
        sa.Column('reference_high', sa.Float),
        sa.Column('reference_text', sa.String(255)),
        sa.Column('interpretation', sa.String(10)),
        sa.Column('is_critical', sa.Boolean, default=False),
        sa.Column('is_abnormal', sa.Boolean, default=False),
        sa.Column('status', sa.String(20), default='preliminary'),
        sa.Column('resulted_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('resulted_by', sa.String(255)),
        sa.Column('notes', sa.Text),
        sa.Column('method', sa.String(255)),
    )
    op.create_index('ix_lab_results_tenant_patient', 'lab_results', ['tenant_id', 'patient_id'])
    op.create_index('ix_lab_results_loinc_code', 'lab_results', ['loinc_code'])

    # ==================== Imaging ====================
    op.create_table(
        'imaging_orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('ordering_provider_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True)),
        sa.Column('procedure_code', sa.String(20), nullable=False),
        sa.Column('procedure_name', sa.String(255), nullable=False),
        sa.Column('modality', sa.String(10), nullable=False),
        sa.Column('body_part', sa.String(100)),
        sa.Column('laterality', sa.String(20)),
        sa.Column('priority', sa.String(20), default='routine'),
        sa.Column('clinical_indication', sa.Text),
        sa.Column('diagnosis_codes', postgresql.ARRAY(sa.String(20)), default=[]),
        sa.Column('contrast_required', sa.Boolean, default=False),
        sa.Column('contrast_allergy_checked', sa.Boolean, default=False),
        sa.Column('pregnancy_status_checked', sa.Boolean, default=False),
        sa.Column('scheduled_datetime', sa.DateTime),
        sa.Column('performing_location', sa.String(255)),
        sa.Column('status', sa.String(50), default='draft'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('notes', sa.Text),
    )
    op.create_index('ix_imaging_orders_tenant_id', 'imaging_orders', ['tenant_id'])
    op.create_index('ix_imaging_orders_patient_id', 'imaging_orders', ['patient_id'])

    op.create_table(
        'imaging_studies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('imaging_orders.id')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('accession_number', sa.String(100)),
        sa.Column('study_instance_uid', sa.String(100), unique=True),
        sa.Column('modality', sa.String(10), nullable=False),
        sa.Column('study_description', sa.String(255)),
        sa.Column('body_part', sa.String(100)),
        sa.Column('num_series', sa.Integer, default=0),
        sa.Column('num_images', sa.Integer, default=0),
        sa.Column('radiation_dose_msv', sa.Float),
        sa.Column('pacs_url', sa.String(500)),
        sa.Column('study_datetime', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_imaging_studies_accession', 'imaging_studies', ['accession_number'])

    op.create_table(
        'radiology_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('study_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('imaging_studies.id')),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('impression', sa.Text),
        sa.Column('findings', sa.Text),
        sa.Column('comparison', sa.Text),
        sa.Column('technique', sa.Text),
        sa.Column('radiologist_id', postgresql.UUID(as_uuid=True)),
        sa.Column('radiologist_name', sa.String(255)),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('dictated_at', sa.DateTime),
        sa.Column('finalized_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # ==================== Referrals ====================
    op.create_table(
        'referrals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True)),
        sa.Column('referring_provider_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('referring_organization_id', postgresql.UUID(as_uuid=True)),
        sa.Column('receiving_provider_id', postgresql.UUID(as_uuid=True)),
        sa.Column('receiving_organization_id', postgresql.UUID(as_uuid=True)),
        sa.Column('target_specialty', sa.String(100)),
        sa.Column('referral_type', sa.String(50), default='consultation'),
        sa.Column('priority', sa.String(20), default='routine'),
        sa.Column('reason', sa.Text, nullable=False),
        sa.Column('clinical_question', sa.Text),
        sa.Column('diagnosis_codes', postgresql.ARRAY(sa.String(20)), default=[]),
        sa.Column('requires_authorization', sa.Boolean, default=False),
        sa.Column('authorization_number', sa.String(100)),
        sa.Column('authorization_status', sa.String(20)),
        sa.Column('authorized_visits', sa.Integer, default=1),
        sa.Column('preferred_date_start', sa.DateTime),
        sa.Column('preferred_date_end', sa.DateTime),
        sa.Column('scheduled_appointment_id', postgresql.UUID(as_uuid=True)),
        sa.Column('scheduled_datetime', sa.DateTime),
        sa.Column('status', sa.String(50), default='draft'),
        sa.Column('consultation_notes', sa.Text),
        sa.Column('recommendations', sa.Text),
        sa.Column('follow_up_needed', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('sent_at', sa.DateTime),
        sa.Column('received_at', sa.DateTime),
        sa.Column('completed_at', sa.DateTime),
    )
    op.create_index('ix_referrals_tenant_id', 'referrals', ['tenant_id'])
    op.create_index('ix_referrals_patient_id', 'referrals', ['patient_id'])
    op.create_index('ix_referrals_status', 'referrals', ['status'])
    op.create_index('ix_referrals_specialty', 'referrals', ['target_specialty'])

    op.create_table(
        'referral_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('referral_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('referrals.id')),
        sa.Column('document_type', sa.String(50)),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('mime_type', sa.String(100)),
        sa.Column('storage_url', sa.String(500), nullable=False),
        sa.Column('uploaded_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True)),
    )

    op.create_table(
        'referral_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('referral_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('referrals.id')),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_type', sa.String(50)),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('read_at', sa.DateTime),
    )

    # ==================== Clinical Documentation ====================
    op.create_table(
        'clinical_notes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True)),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('note_type', sa.String(50), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True)),
        sa.Column('title', sa.String(255)),
        sa.Column('content', sa.Text),
        sa.Column('structured_content', postgresql.JSONB),
        sa.Column('diagnosis_codes', postgresql.JSONB, default=[]),
        sa.Column('procedure_codes', postgresql.JSONB, default=[]),
        sa.Column('status', sa.String(50), default='draft'),
        sa.Column('signed_by', postgresql.UUID(as_uuid=True)),
        sa.Column('signed_at', sa.DateTime),
        sa.Column('cosigned_by', postgresql.UUID(as_uuid=True)),
        sa.Column('cosigned_at', sa.DateTime),
        sa.Column('amendments', postgresql.JSONB, default=[]),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_clinical_notes_tenant_patient', 'clinical_notes', ['tenant_id', 'patient_id'])
    op.create_index('ix_clinical_notes_encounter', 'clinical_notes', ['encounter_id'])
    op.create_index('ix_clinical_notes_type', 'clinical_notes', ['note_type'])

    op.create_table(
        'note_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('note_type', sa.String(50), nullable=False),
        sa.Column('specialty', sa.String(100)),
        sa.Column('sections', postgresql.JSONB, default=[]),
        sa.Column('default_content', postgresql.JSONB, default={}),
        sa.Column('smart_phrases', postgresql.ARRAY(sa.String(100)), default=[]),
        sa.Column('is_default', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        'smart_phrases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True)),
        sa.Column('abbreviation', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('category', sa.String(100)),
        sa.Column('variables', postgresql.ARRAY(sa.String(50)), default=[]),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('usage_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_smart_phrases_abbreviation', 'smart_phrases', ['abbreviation'])

    # ==================== Care Plans ====================
    op.create_table(
        'care_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('category', sa.String(50), default='chronic_disease'),
        sa.Column('condition_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=[]),
        sa.Column('author_id', postgresql.UUID(as_uuid=True)),
        sa.Column('period_start', sa.DateTime),
        sa.Column('period_end', sa.DateTime),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('based_on_protocol_id', postgresql.UUID(as_uuid=True)),
        sa.Column('replaces_plan_id', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_care_plans_tenant_patient', 'care_plans', ['tenant_id', 'patient_id'])
    op.create_index('ix_care_plans_status', 'care_plans', ['status'])

    op.create_table(
        'care_goals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('care_plan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('care_plans.id')),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category', sa.String(50)),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('priority', sa.String(20), default='medium'),
        sa.Column('targets', postgresql.JSONB, default=[]),
        sa.Column('start_date', sa.DateTime),
        sa.Column('target_date', sa.DateTime),
        sa.Column('status', sa.String(20), default='proposed'),
        sa.Column('achievement_status', sa.String(20), default='in_progress'),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'goal_progress',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('goal_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('care_goals.id')),
        sa.Column('recorded_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('recorded_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('measure', sa.String(100), nullable=False),
        sa.Column('value', sa.String(255)),
        sa.Column('value_numeric', sa.Float),
        sa.Column('unit', sa.String(50)),
        sa.Column('achievement_status', sa.String(20), default='in_progress'),
        sa.Column('notes', sa.Text),
    )

    op.create_table(
        'care_interventions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('care_plan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('care_plans.id')),
        sa.Column('goal_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=[]),
        sa.Column('category', sa.String(50)),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('reason', sa.Text),
        sa.Column('scheduled_timing', sa.String(50)),
        sa.Column('scheduled_datetime', sa.DateTime),
        sa.Column('assigned_to_id', postgresql.UUID(as_uuid=True)),
        sa.Column('assigned_to_type', sa.String(20), default='practitioner'),
        sa.Column('instructions', sa.Text),
        sa.Column('status', sa.String(20), default='planned'),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('outcome', sa.String(50)),
        sa.Column('outcome_notes', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'care_team_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('care_plan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('care_plans.id')),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True)),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True)),
        sa.Column('caregiver_id', postgresql.UUID(as_uuid=True)),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255)),
        sa.Column('specialty', sa.String(100)),
        sa.Column('contact_info', sa.String(255)),
        sa.Column('start_date', sa.DateTime),
        sa.Column('end_date', sa.DateTime),
        sa.Column('is_active', sa.Boolean, default=True),
    )

    # ==================== Clinical Decision Support ====================
    op.create_table(
        'clinical_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('rule_id', postgresql.UUID(as_uuid=True)),
        sa.Column('guideline_id', postgresql.UUID(as_uuid=True)),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True)),
        sa.Column('order_id', postgresql.UUID(as_uuid=True)),
        sa.Column('medication_id', postgresql.UUID(as_uuid=True)),
        sa.Column('suggested_actions', postgresql.JSONB, default=[]),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('acknowledged_by', postgresql.UUID(as_uuid=True)),
        sa.Column('acknowledged_at', sa.DateTime),
        sa.Column('override_reason', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime),
    )
    op.create_index('ix_clinical_alerts_tenant_patient', 'clinical_alerts', ['tenant_id', 'patient_id'])
    op.create_index('ix_clinical_alerts_status', 'clinical_alerts', ['status'])

    op.create_table(
        'cds_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('conditions', postgresql.JSONB, nullable=False),
        sa.Column('alert_severity', sa.String(20), default='warning'),
        sa.Column('alert_title_template', sa.String(255)),
        sa.Column('alert_message_template', sa.Text),
        sa.Column('suggested_actions', postgresql.JSONB, default=[]),
        sa.Column('priority', sa.Integer, default=100),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('requires_override_reason', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_cds_rules_tenant', 'cds_rules', ['tenant_id'])

    # ==================== Vital Signs ====================
    op.create_table(
        'vital_signs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True)),
        sa.Column('vital_type', sa.String(50), nullable=False),
        sa.Column('loinc_code', sa.String(20)),
        sa.Column('value', sa.Float),
        sa.Column('value_string', sa.String(50)),
        sa.Column('unit', sa.String(20)),
        sa.Column('systolic', sa.Float),
        sa.Column('diastolic', sa.Float),
        sa.Column('is_abnormal', sa.Boolean, default=False),
        sa.Column('interpretation', sa.String(20)),
        sa.Column('recorded_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('recorded_by', postgresql.UUID(as_uuid=True)),
        sa.Column('device_id', sa.String(100)),
        sa.Column('method', sa.String(50)),
        sa.Column('position', sa.String(20)),
        sa.Column('notes', sa.Text),
    )
    op.create_index('ix_vital_signs_tenant_patient_type', 'vital_signs', ['tenant_id', 'patient_id', 'vital_type'])
    op.create_index('ix_vital_signs_recorded', 'vital_signs', ['recorded_at'])

    op.create_table(
        'early_warning_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True)),
        sa.Column('score_type', sa.String(20), nullable=False),
        sa.Column('total_score', sa.Integer, nullable=False),
        sa.Column('risk_level', sa.String(20)),
        sa.Column('component_scores', postgresql.JSONB, default={}),
        sa.Column('vital_sign_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=[]),
        sa.Column('calculated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('calculated_by', postgresql.UUID(as_uuid=True)),
        sa.Column('alert_triggered', sa.Boolean, default=False),
    )

    # ==================== Discharge ====================
    op.create_table(
        'discharge_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('discharge_disposition', sa.String(50)),
        sa.Column('discharge_destination', sa.String(255)),
        sa.Column('checklist_items', postgresql.JSONB, default=[]),
        sa.Column('all_items_completed', sa.Boolean, default=False),
        sa.Column('discharge_medications', postgresql.JSONB, default=[]),
        sa.Column('med_reconciliation_completed', sa.Boolean, default=False),
        sa.Column('discharge_instructions', sa.Text),
        sa.Column('activity_restrictions', sa.Text),
        sa.Column('diet_instructions', sa.Text),
        sa.Column('follow_up_appointments', postgresql.JSONB, default=[]),
        sa.Column('follow_up_provider_id', postgresql.UUID(as_uuid=True)),
        sa.Column('follow_up_date', sa.DateTime),
        sa.Column('readmission_risk_score', sa.Float),
        sa.Column('readmission_risk_level', sa.String(20)),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('completed_by', postgresql.UUID(as_uuid=True)),
    )
    op.create_index('ix_discharge_records_tenant_patient', 'discharge_records', ['tenant_id', 'patient_id'])
    op.create_index('ix_discharge_records_encounter', 'discharge_records', ['encounter_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('discharge_records')
    op.drop_table('early_warning_scores')
    op.drop_table('vital_signs')
    op.drop_table('cds_rules')
    op.drop_table('clinical_alerts')
    op.drop_table('care_team_members')
    op.drop_table('care_interventions')
    op.drop_table('goal_progress')
    op.drop_table('care_goals')
    op.drop_table('care_plans')
    op.drop_table('smart_phrases')
    op.drop_table('note_templates')
    op.drop_table('clinical_notes')
    op.drop_table('referral_messages')
    op.drop_table('referral_documents')
    op.drop_table('referrals')
    op.drop_table('radiology_reports')
    op.drop_table('imaging_studies')
    op.drop_table('imaging_orders')
    op.drop_table('lab_results')
    op.drop_table('lab_orders')
    op.drop_table('drug_interaction_checks')
    op.drop_table('prescriptions')

"""EPIC-012: Intelligent Automation Platform

Revision ID: 012_intelligent_automation
Revises: 011_advanced_analytics
Create Date: 2024-11-25

This migration creates tables for the Intelligent Automation Platform:
- Workflow definitions and executions
- Appointment optimization and waitlist
- Care gap rules and detection
- Document processing jobs
- Campaign management
- Clinical tasks and automation
- Revenue cycle automation
- Human task management
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

# revision identifiers, used by Alembic.
revision = '012_intelligent_automation'
down_revision = '011_advanced_analytics'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==================== Workflow Management ====================

    # Workflow definitions
    op.create_table(
        'automation_workflows',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('trigger_config', JSONB, nullable=False),
        sa.Column('steps', JSONB, nullable=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('version', sa.Integer, default=1),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('created_by', UUID(as_uuid=True)),
        sa.Column('metadata', JSONB, default={}),
    )
    op.create_index('idx_automation_workflows_tenant', 'automation_workflows', ['tenant_id'])
    op.create_index('idx_automation_workflows_active', 'automation_workflows', ['tenant_id', 'is_active'])

    # Workflow executions
    op.create_table(
        'automation_workflow_executions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('workflow_id', UUID(as_uuid=True), sa.ForeignKey('automation_workflows.id'), nullable=False),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('input_data', JSONB, default={}),
        sa.Column('output_data', JSONB, default={}),
        sa.Column('current_step_id', sa.String(100)),
        sa.Column('steps_completed', sa.Integer, default=0),
        sa.Column('total_steps', sa.Integer, default=0),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('error_message', sa.Text),
        sa.Column('metadata', JSONB, default={}),
    )
    op.create_index('idx_workflow_executions_workflow', 'automation_workflow_executions', ['workflow_id'])
    op.create_index('idx_workflow_executions_status', 'automation_workflow_executions', ['tenant_id', 'status'])

    # ==================== Appointment Optimization ====================

    # No-show predictions
    op.create_table(
        'automation_noshow_predictions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('patient_id', UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('appointment_id', UUID(as_uuid=True)),
        sa.Column('appointment_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('risk_level', sa.String(20), nullable=False),
        sa.Column('probability', sa.Float, nullable=False),
        sa.Column('risk_factors', JSONB, default=[]),
        sa.Column('interventions', JSONB, default=[]),
        sa.Column('actual_outcome', sa.String(20)),  # showed, no_show, cancelled
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_noshow_predictions_patient', 'automation_noshow_predictions', ['patient_id'])
    op.create_index('idx_noshow_predictions_date', 'automation_noshow_predictions', ['appointment_date'])

    # Waitlist
    op.create_table(
        'automation_waitlist',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('patient_id', UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('appointment_type', sa.String(50), nullable=False),
        sa.Column('provider_id', UUID(as_uuid=True)),
        sa.Column('preferred_dates', JSONB, default=[]),
        sa.Column('preferred_times', JSONB, default=[]),
        sa.Column('position', sa.Integer),
        sa.Column('status', sa.String(20), default='waiting'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('fulfilled_at', sa.DateTime(timezone=True)),
        sa.Column('fulfilled_appointment_id', UUID(as_uuid=True)),
    )
    op.create_index('idx_waitlist_tenant_status', 'automation_waitlist', ['tenant_id', 'status'])

    # ==================== Care Gap Detection ====================

    # Care gap rules
    op.create_table(
        'automation_care_gap_rules',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('gap_type', sa.String(50), nullable=False),
        sa.Column('condition_codes', JSONB, default=[]),
        sa.Column('procedure_codes', JSONB, default=[]),
        sa.Column('age_min', sa.Integer),
        sa.Column('age_max', sa.Integer),
        sa.Column('gender', sa.String(10)),
        sa.Column('frequency_days', sa.Integer, default=365),
        sa.Column('measure_id', sa.String(50)),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )
    op.create_index('idx_care_gap_rules_tenant', 'automation_care_gap_rules', ['tenant_id', 'is_active'])

    # Detected care gaps
    op.create_table(
        'automation_care_gaps',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('patient_id', UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('rule_id', UUID(as_uuid=True), sa.ForeignKey('automation_care_gap_rules.id'), nullable=False),
        sa.Column('gap_name', sa.String(200), nullable=False),
        sa.Column('gap_type', sa.String(50), nullable=False),
        sa.Column('priority', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), default='open'),
        sa.Column('due_date', sa.DateTime(timezone=True)),
        sa.Column('last_completed', sa.DateTime(timezone=True)),
        sa.Column('days_overdue', sa.Integer, default=0),
        sa.Column('impact_score', sa.Float, default=0),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('closed_at', sa.DateTime(timezone=True)),
        sa.Column('closed_by', UUID(as_uuid=True)),
        sa.Column('metadata', JSONB, default={}),
    )
    op.create_index('idx_care_gaps_patient', 'automation_care_gaps', ['patient_id', 'status'])
    op.create_index('idx_care_gaps_priority', 'automation_care_gaps', ['tenant_id', 'priority', 'status'])

    # ==================== Document Processing ====================

    # Document processing jobs
    op.create_table(
        'automation_document_jobs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('document_id', UUID(as_uuid=True), nullable=False),
        sa.Column('file_path', sa.Text, nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_type', sa.String(50), nullable=False),
        sa.Column('file_size', sa.Integer),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('document_type', sa.String(50)),
        sa.Column('ocr_text', sa.Text),
        sa.Column('ocr_confidence', sa.Float),
        sa.Column('extracted_fields', JSONB, default=[]),
        sa.Column('validation_errors', JSONB, default=[]),
        sa.Column('requires_review', sa.Boolean, default=False),
        sa.Column('reviewed_by', UUID(as_uuid=True)),
        sa.Column('reviewed_at', sa.DateTime(timezone=True)),
        sa.Column('processing_time_ms', sa.Integer),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('metadata', JSONB, default={}),
    )
    op.create_index('idx_document_jobs_tenant', 'automation_document_jobs', ['tenant_id', 'status'])
    op.create_index('idx_document_jobs_review', 'automation_document_jobs', ['tenant_id', 'requires_review'])

    # ==================== Campaign Management ====================

    # Patient segments
    op.create_table(
        'automation_segments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('criteria', JSONB, nullable=False),
        sa.Column('estimated_size', sa.Integer, default=0),
        sa.Column('is_dynamic', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )
    op.create_index('idx_segments_tenant', 'automation_segments', ['tenant_id'])

    # Message templates
    op.create_table(
        'automation_templates',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('channel', sa.String(50), nullable=False),
        sa.Column('subject', sa.String(500)),
        sa.Column('body', sa.Text, nullable=False),
        sa.Column('variables', JSONB, default=[]),
        sa.Column('language', sa.String(10), default='en'),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
    )
    op.create_index('idx_templates_tenant', 'automation_templates', ['tenant_id', 'is_active'])

    # Campaigns
    op.create_table(
        'automation_campaigns',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('campaign_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), default='draft'),
        sa.Column('segment_id', UUID(as_uuid=True), sa.ForeignKey('automation_segments.id')),
        sa.Column('steps', JSONB, default=[]),
        sa.Column('schedule', JSONB, default={}),
        sa.Column('priority', sa.String(20), default='normal'),
        sa.Column('created_by', UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('metadata', JSONB, default={}),
    )
    op.create_index('idx_campaigns_tenant', 'automation_campaigns', ['tenant_id', 'status'])

    # Campaign messages
    op.create_table(
        'automation_campaign_messages',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('campaign_id', UUID(as_uuid=True), sa.ForeignKey('automation_campaigns.id'), nullable=False),
        sa.Column('patient_id', UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('step_id', sa.String(100)),
        sa.Column('channel', sa.String(50), nullable=False),
        sa.Column('template_id', UUID(as_uuid=True), sa.ForeignKey('automation_templates.id')),
        sa.Column('personalized_content', sa.Text),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('scheduled_at', sa.DateTime(timezone=True)),
        sa.Column('sent_at', sa.DateTime(timezone=True)),
        sa.Column('delivered_at', sa.DateTime(timezone=True)),
        sa.Column('opened_at', sa.DateTime(timezone=True)),
        sa.Column('clicked_at', sa.DateTime(timezone=True)),
        sa.Column('responded_at', sa.DateTime(timezone=True)),
        sa.Column('response_content', sa.Text),
        sa.Column('error_message', sa.Text),
    )
    op.create_index('idx_campaign_messages_campaign', 'automation_campaign_messages', ['campaign_id', 'status'])
    op.create_index('idx_campaign_messages_patient', 'automation_campaign_messages', ['patient_id'])

    # ==================== Clinical Task Automation ====================

    # Clinical tasks
    op.create_table(
        'automation_clinical_tasks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('task_type', sa.String(50), nullable=False),
        sa.Column('priority', sa.String(20), nullable=False),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('patient_id', UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('provider_id', UUID(as_uuid=True)),
        sa.Column('assigned_to', UUID(as_uuid=True)),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('due_date', sa.DateTime(timezone=True)),
        sa.Column('related_entity_type', sa.String(50)),
        sa.Column('related_entity_id', UUID(as_uuid=True)),
        sa.Column('auto_action_taken', sa.String(200)),
        sa.Column('escalation_level', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('completed_by', UUID(as_uuid=True)),
        sa.Column('metadata', JSONB, default={}),
    )
    op.create_index('idx_clinical_tasks_assigned', 'automation_clinical_tasks', ['assigned_to', 'status'])
    op.create_index('idx_clinical_tasks_priority', 'automation_clinical_tasks', ['tenant_id', 'priority', 'status'])
    op.create_index('idx_clinical_tasks_patient', 'automation_clinical_tasks', ['patient_id'])

    # Medication refill requests
    op.create_table(
        'automation_refill_requests',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('patient_id', UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('medication_name', sa.String(300), nullable=False),
        sa.Column('medication_id', UUID(as_uuid=True)),
        sa.Column('strength', sa.String(100)),
        sa.Column('quantity', sa.Integer),
        sa.Column('days_supply', sa.Integer),
        sa.Column('refills_remaining', sa.Integer),
        sa.Column('prescriber_id', UUID(as_uuid=True)),
        sa.Column('pharmacy_id', UUID(as_uuid=True)),
        sa.Column('status', sa.String(50), default='requested'),
        sa.Column('is_controlled', sa.Boolean, default=False),
        sa.Column('requires_review', sa.Boolean, default=False),
        sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(timezone=True)),
        sa.Column('processed_by', UUID(as_uuid=True)),
        sa.Column('denial_reason', sa.Text),
        sa.Column('notes', sa.Text),
    )
    op.create_index('idx_refill_requests_patient', 'automation_refill_requests', ['patient_id'])
    op.create_index('idx_refill_requests_status', 'automation_refill_requests', ['tenant_id', 'status'])

    # ==================== Revenue Cycle ====================

    # Claims
    op.create_table(
        'automation_claims',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('patient_id', UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('encounter_id', UUID(as_uuid=True)),
        sa.Column('payer_id', UUID(as_uuid=True), nullable=False),
        sa.Column('payer_name', sa.String(200)),
        sa.Column('provider_id', UUID(as_uuid=True)),
        sa.Column('provider_npi', sa.String(10)),
        sa.Column('claim_type', sa.String(50)),
        sa.Column('status', sa.String(50), default='draft'),
        sa.Column('lines', JSONB, default=[]),
        sa.Column('total_charges', sa.Numeric(12, 2)),
        sa.Column('total_allowed', sa.Numeric(12, 2)),
        sa.Column('total_paid', sa.Numeric(12, 2)),
        sa.Column('total_adjustments', sa.Numeric(12, 2)),
        sa.Column('patient_responsibility', sa.Numeric(12, 2)),
        sa.Column('service_date_from', sa.DateTime(timezone=True)),
        sa.Column('service_date_to', sa.DateTime(timezone=True)),
        sa.Column('prior_auth_number', sa.String(100)),
        sa.Column('check_number', sa.String(100)),
        sa.Column('era_id', sa.String(100)),
        sa.Column('validation_errors', JSONB, default=[]),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('submitted_at', sa.DateTime(timezone=True)),
        sa.Column('adjudicated_at', sa.DateTime(timezone=True)),
        sa.Column('metadata', JSONB, default={}),
    )
    op.create_index('idx_claims_patient', 'automation_claims', ['patient_id'])
    op.create_index('idx_claims_status', 'automation_claims', ['tenant_id', 'status'])
    op.create_index('idx_claims_payer', 'automation_claims', ['payer_id'])

    # Prior authorizations
    op.create_table(
        'automation_prior_auths',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('patient_id', UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('payer_id', UUID(as_uuid=True)),
        sa.Column('provider_id', UUID(as_uuid=True)),
        sa.Column('procedure_codes', JSONB, default=[]),
        sa.Column('diagnosis_codes', JSONB, default=[]),
        sa.Column('service_type', sa.String(100)),
        sa.Column('units_requested', sa.Integer),
        sa.Column('units_approved', sa.Integer),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('auth_number', sa.String(100)),
        sa.Column('effective_date', sa.DateTime(timezone=True)),
        sa.Column('expiry_date', sa.DateTime(timezone=True)),
        sa.Column('clinical_notes', sa.Text),
        sa.Column('denial_reason', sa.Text),
        sa.Column('requested_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('submitted_at', sa.DateTime(timezone=True)),
        sa.Column('decision_at', sa.DateTime(timezone=True)),
    )
    op.create_index('idx_prior_auths_patient', 'automation_prior_auths', ['patient_id'])
    op.create_index('idx_prior_auths_status', 'automation_prior_auths', ['tenant_id', 'status'])

    # Patient balances
    op.create_table(
        'automation_patient_balances',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('patient_id', UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False, unique=True),
        sa.Column('current_balance', sa.Numeric(12, 2), default=0),
        sa.Column('balance_0_30', sa.Numeric(12, 2), default=0),
        sa.Column('balance_31_60', sa.Numeric(12, 2), default=0),
        sa.Column('balance_61_90', sa.Numeric(12, 2), default=0),
        sa.Column('balance_over_90', sa.Numeric(12, 2), default=0),
        sa.Column('collection_status', sa.String(50), default='current'),
        sa.Column('last_statement_date', sa.DateTime(timezone=True)),
        sa.Column('last_payment_date', sa.DateTime(timezone=True)),
        sa.Column('last_payment_amount', sa.Numeric(12, 2)),
        sa.Column('payment_plan_id', UUID(as_uuid=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_patient_balances_status', 'automation_patient_balances', ['tenant_id', 'collection_status'])

    # ==================== Human Task Management ====================

    # Task queues
    op.create_table(
        'automation_task_queues',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('task_types', JSONB, default=[]),
        sa.Column('assignment_strategy', sa.String(50), default='load_balanced'),
        sa.Column('eligible_roles', JSONB, default=[]),
        sa.Column('eligible_users', JSONB, default=[]),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('max_concurrent_per_user', sa.Integer, default=10),
        sa.Column('auto_assign', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_task_queues_tenant', 'automation_task_queues', ['tenant_id', 'is_active'])

    # Human tasks
    op.create_table(
        'automation_human_tasks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('task_type', sa.String(50), nullable=False),
        sa.Column('priority', sa.String(20), nullable=False),
        sa.Column('state', sa.String(50), default='created'),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('form_data', JSONB, default={}),
        sa.Column('patient_id', UUID(as_uuid=True), sa.ForeignKey('patients.id')),
        sa.Column('provider_id', UUID(as_uuid=True)),
        sa.Column('queue_id', UUID(as_uuid=True), sa.ForeignKey('automation_task_queues.id')),
        sa.Column('assigned_to', UUID(as_uuid=True)),
        sa.Column('assigned_at', sa.DateTime(timezone=True)),
        sa.Column('claimed_at', sa.DateTime(timezone=True)),
        sa.Column('due_date', sa.DateTime(timezone=True)),
        sa.Column('sla_deadline', sa.DateTime(timezone=True)),
        sa.Column('sla_breached', sa.Boolean, default=False),
        sa.Column('escalation_level', sa.Integer, default=0),
        sa.Column('source_system', sa.String(100)),
        sa.Column('source_entity_type', sa.String(100)),
        sa.Column('source_entity_id', UUID(as_uuid=True)),
        sa.Column('outcome', sa.String(100)),
        sa.Column('outcome_data', JSONB, default={}),
        sa.Column('tags', JSONB, default=[]),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('completed_by', UUID(as_uuid=True)),
        sa.Column('metadata', JSONB, default={}),
    )
    op.create_index('idx_human_tasks_assigned', 'automation_human_tasks', ['assigned_to', 'state'])
    op.create_index('idx_human_tasks_queue', 'automation_human_tasks', ['queue_id', 'state'])
    op.create_index('idx_human_tasks_priority', 'automation_human_tasks', ['tenant_id', 'priority', 'state'])
    op.create_index('idx_human_tasks_patient', 'automation_human_tasks', ['patient_id'])

    # Task history
    op.create_table(
        'automation_task_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('task_id', UUID(as_uuid=True), sa.ForeignKey('automation_human_tasks.id'), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('from_state', sa.String(50)),
        sa.Column('to_state', sa.String(50)),
        sa.Column('performed_by', UUID(as_uuid=True)),
        sa.Column('performed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('details', JSONB, default={}),
    )
    op.create_index('idx_task_history_task', 'automation_task_history', ['task_id'])

    # Task comments
    op.create_table(
        'automation_task_comments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('task_id', UUID(as_uuid=True), sa.ForeignKey('automation_human_tasks.id'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('is_internal', sa.Boolean, default=False),
        sa.Column('attachments', JSONB, default=[]),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_task_comments_task', 'automation_task_comments', ['task_id'])


def downgrade() -> None:
    # Human task management
    op.drop_table('automation_task_comments')
    op.drop_table('automation_task_history')
    op.drop_table('automation_human_tasks')
    op.drop_table('automation_task_queues')

    # Revenue cycle
    op.drop_table('automation_patient_balances')
    op.drop_table('automation_prior_auths')
    op.drop_table('automation_claims')

    # Clinical task automation
    op.drop_table('automation_refill_requests')
    op.drop_table('automation_clinical_tasks')

    # Campaign management
    op.drop_table('automation_campaign_messages')
    op.drop_table('automation_campaigns')
    op.drop_table('automation_templates')
    op.drop_table('automation_segments')

    # Document processing
    op.drop_table('automation_document_jobs')

    # Care gap detection
    op.drop_table('automation_care_gaps')
    op.drop_table('automation_care_gap_rules')

    # Appointment optimization
    op.drop_table('automation_waitlist')
    op.drop_table('automation_noshow_predictions')

    # Workflow management
    op.drop_table('automation_workflow_executions')
    op.drop_table('automation_workflows')

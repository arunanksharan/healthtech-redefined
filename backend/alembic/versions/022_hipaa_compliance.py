"""HIPAA Compliance

Revision ID: 022_hipaa_compliance
Revises: 021_security_hardening
Create Date: 2024-11-25

EPIC-022: HIPAA Compliance
Creates tables for audit logging, access controls, data retention,
breach management, BAA tracking, training, and risk assessment.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '022_hipaa_compliance'
down_revision = '021_security_hardening'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # =========================================================================
    # Audit Logging Tables
    # =========================================================================

    # PHI Audit Logs - Tamper-proof logging
    op.create_table(
        'hipaa_phi_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_id', sa.String(100), unique=True, nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('outcome', sa.String(50), nullable=False, default='success'),
        sa.Column('recorded_at', sa.DateTime, nullable=False),
        sa.Column('event_start', sa.DateTime, nullable=True),
        sa.Column('event_end', sa.DateTime, nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_type', sa.String(50), nullable=True),
        sa.Column('user_name', sa.String(200), nullable=True),
        sa.Column('user_role', sa.String(100), nullable=True),
        sa.Column('source_ip', postgresql.INET, nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('geo_location', sa.String(200), nullable=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('request_id', sa.String(100), nullable=True),
        sa.Column('phi_category', sa.String(50), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('patient_mrn', sa.String(50), nullable=True),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('justification', sa.String(50), nullable=True),
        sa.Column('justification_details', sa.Text, nullable=True),
        sa.Column('fields_accessed', postgresql.JSONB, nullable=True),
        sa.Column('query_parameters', postgresql.JSONB, nullable=True),
        sa.Column('data_before', postgresql.JSONB, nullable=True),
        sa.Column('data_after', postgresql.JSONB, nullable=True),
        sa.Column('fhir_audit_event_id', sa.String(100), nullable=True),
        sa.Column('fhir_event_coding', postgresql.JSONB, nullable=True),
        sa.Column('previous_hash', sa.String(64), nullable=True),
        sa.Column('record_hash', sa.String(64), nullable=False),
        sa.Column('hash_algorithm', sa.String(20), default='sha256'),
        sa.Column('service_name', sa.String(100), nullable=True),
        sa.Column('api_endpoint', sa.String(500), nullable=True),
        sa.Column('http_method', sa.String(10), nullable=True),
        sa.Column('response_code', sa.Integer, nullable=True),
        sa.Column('archived', sa.Boolean, default=False),
        sa.Column('archived_at', sa.DateTime, nullable=True),
        sa.Column('archive_location', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
    )
    op.create_index('ix_phi_audit_tenant_id', 'hipaa_phi_audit_logs', ['tenant_id'])
    op.create_index('ix_phi_audit_tenant_recorded', 'hipaa_phi_audit_logs', ['tenant_id', 'recorded_at'])
    op.create_index('ix_phi_audit_user_recorded', 'hipaa_phi_audit_logs', ['user_id', 'recorded_at'])
    op.create_index('ix_phi_audit_patient_recorded', 'hipaa_phi_audit_logs', ['patient_id', 'recorded_at'])
    op.create_index('ix_phi_audit_action_category', 'hipaa_phi_audit_logs', ['action', 'phi_category'])

    # Audit Retention Policies
    op.create_table(
        'hipaa_audit_retention_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('retention_days', sa.Integer, nullable=False, default=2555),
        sa.Column('archive_after_days', sa.Integer, nullable=False, default=365),
        sa.Column('archive_storage_class', sa.String(50), default='GLACIER'),
        sa.Column('applies_to_actions', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('applies_to_categories', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_default', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index('ix_audit_retention_tenant', 'hipaa_audit_retention_policies', ['tenant_id'])

    # =========================================================================
    # Access Control Tables
    # =========================================================================

    # Treatment Relationships
    op.create_table(
        'hipaa_treatment_relationships',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_type', sa.String(50), nullable=False),
        sa.Column('relationship_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), default='active'),
        sa.Column('effective_date', sa.Date, nullable=False),
        sa.Column('expiration_date', sa.Date, nullable=True),
        sa.Column('referral_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('authorization_number', sa.String(100), nullable=True),
        sa.Column('care_team_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('care_team_role', sa.String(100), nullable=True),
        sa.Column('facility_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('department', sa.String(200), nullable=True),
        sa.Column('allowed_phi_categories', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('restricted_phi_categories', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.UniqueConstraint('tenant_id', 'patient_id', 'provider_id', 'relationship_type',
                          name='uq_treatment_relationship'),
    )
    op.create_index('ix_treatment_rel_patient', 'hipaa_treatment_relationships', ['patient_id'])
    op.create_index('ix_treatment_rel_provider', 'hipaa_treatment_relationships', ['provider_id'])
    op.create_index('ix_treatment_rel_patient_provider', 'hipaa_treatment_relationships', ['patient_id', 'provider_id'])

    # Access Requests
    op.create_table(
        'hipaa_access_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('request_number', sa.String(50), unique=True, nullable=False),
        sa.Column('requester_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('requester_name', sa.String(200), nullable=True),
        sa.Column('requester_role', sa.String(100), nullable=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('requested_phi_categories', postgresql.ARRAY(sa.String), nullable=False),
        sa.Column('requested_resources', postgresql.JSONB, nullable=True),
        sa.Column('justification', sa.String(50), nullable=False),
        sa.Column('justification_details', sa.Text, nullable=False),
        sa.Column('clinical_context', sa.Text, nullable=True),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('approver_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approver_name', sa.String(200), nullable=True),
        sa.Column('approval_date', sa.DateTime, nullable=True),
        sa.Column('denial_reason', sa.Text, nullable=True),
        sa.Column('access_start', sa.DateTime, nullable=True),
        sa.Column('access_end', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now()),
    )
    op.create_index('ix_access_request_tenant', 'hipaa_access_requests', ['tenant_id'])
    op.create_index('ix_access_request_requester', 'hipaa_access_requests', ['requester_id'])
    op.create_index('ix_access_request_patient', 'hipaa_access_requests', ['patient_id'])
    op.create_index('ix_access_request_status', 'hipaa_access_requests', ['status', 'created_at'])

    # Certification Campaigns
    op.create_table(
        'hipaa_certification_campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('start_date', sa.DateTime, nullable=False),
        sa.Column('end_date', sa.DateTime, nullable=False),
        sa.Column('scope_type', sa.String(50), nullable=False),
        sa.Column('scope_criteria', postgresql.JSONB, nullable=True),
        sa.Column('total_certifications', sa.Integer, default=0),
        sa.Column('completed_certifications', sa.Integer, default=0),
        sa.Column('certified_count', sa.Integer, default=0),
        sa.Column('decertified_count', sa.Integer, default=0),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index('ix_cert_campaign_tenant', 'hipaa_certification_campaigns', ['tenant_id'])

    # Access Certifications
    op.create_table(
        'hipaa_access_certifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('campaign_name', sa.String(200), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_name', sa.String(200), nullable=True),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('role_name', sa.String(200), nullable=True),
        sa.Column('access_type', sa.String(50), nullable=False),
        sa.Column('access_details', postgresql.JSONB, nullable=False),
        sa.Column('reviewer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reviewer_name', sa.String(200), nullable=True),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('certification_date', sa.DateTime, nullable=True),
        sa.Column('comments', sa.Text, nullable=True),
        sa.Column('due_date', sa.DateTime, nullable=False),
        sa.Column('reminder_sent', sa.Boolean, default=False),
        sa.Column('escalated', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now()),
        sa.ForeignKeyConstraint(['campaign_id'], ['hipaa_certification_campaigns.id']),
    )
    op.create_index('ix_access_cert_tenant', 'hipaa_access_certifications', ['tenant_id'])
    op.create_index('ix_access_cert_campaign', 'hipaa_access_certifications', ['campaign_id'])
    op.create_index('ix_access_cert_user', 'hipaa_access_certifications', ['user_id'])
    op.create_index('ix_access_cert_reviewer', 'hipaa_access_certifications', ['reviewer_id'])

    # Access Anomalies
    op.create_table(
        'hipaa_access_anomalies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('anomaly_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_name', sa.String(200), nullable=True),
        sa.Column('user_role', sa.String(100), nullable=True),
        sa.Column('detected_at', sa.DateTime, nullable=False, default=sa.func.now()),
        sa.Column('source_ip', postgresql.INET, nullable=True),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('evidence', postgresql.JSONB, nullable=False),
        sa.Column('baseline_comparison', postgresql.JSONB, nullable=True),
        sa.Column('affected_patient_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('audit_log_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('acknowledged', sa.Boolean, default=False),
        sa.Column('acknowledged_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime, nullable=True),
        sa.Column('investigation_notes', sa.Text, nullable=True),
        sa.Column('resolved', sa.Boolean, default=False),
        sa.Column('resolution', sa.Text, nullable=True),
        sa.Column('false_positive', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now()),
    )
    op.create_index('ix_access_anomaly_tenant', 'hipaa_access_anomalies', ['tenant_id'])
    op.create_index('ix_access_anomaly_severity', 'hipaa_access_anomalies', ['severity', 'detected_at'])
    op.create_index('ix_access_anomaly_type_user', 'hipaa_access_anomalies', ['anomaly_type', 'user_id'])

    # VIP Patients
    op.create_table(
        'hipaa_vip_patients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('vip_reason', sa.String(200), nullable=False),
        sa.Column('enhanced_monitoring', sa.Boolean, default=True),
        sa.Column('access_alerts_enabled', sa.Boolean, default=True),
        sa.Column('allowed_user_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('allowed_roles', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('alert_recipients', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index('ix_vip_patients_tenant', 'hipaa_vip_patients', ['tenant_id'])

    # =========================================================================
    # Data Retention Tables
    # =========================================================================

    # Retention Policies
    op.create_table(
        'hipaa_retention_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('resource_types', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('retention_years', sa.Integer, nullable=False),
        sa.Column('retention_months', sa.Integer, default=0),
        sa.Column('applies_to_minors', sa.Boolean, default=False),
        sa.Column('minor_retention_from_age', sa.Integer, default=18),
        sa.Column('minor_additional_years', sa.Integer, default=0),
        sa.Column('jurisdiction', sa.String(50), nullable=True),
        sa.Column('regulation_reference', sa.String(200), nullable=True),
        sa.Column('destruction_method', sa.String(50), default='cryptographic_erasure'),
        sa.Column('require_destruction_certificate', sa.Boolean, default=True),
        sa.Column('archive_before_destruction', sa.Boolean, default=True),
        sa.Column('archive_storage_class', sa.String(50), default='GLACIER'),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_default', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index('ix_retention_policy_tenant', 'hipaa_retention_policies', ['tenant_id'])
    op.create_index('ix_retention_policy_category', 'hipaa_retention_policies', ['category', 'is_active'])

    # Retention Schedules
    op.create_table(
        'hipaa_retention_schedules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('record_date', sa.Date, nullable=False),
        sa.Column('retention_start_date', sa.Date, nullable=False),
        sa.Column('scheduled_destruction_date', sa.Date, nullable=False),
        sa.Column('status', sa.String(50), default='active'),
        sa.Column('archived_at', sa.DateTime, nullable=True),
        sa.Column('archive_location', sa.String(500), nullable=True),
        sa.Column('destruction_approved', sa.Boolean, default=False),
        sa.Column('destruction_approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('destruction_approved_at', sa.DateTime, nullable=True),
        sa.Column('destroyed_at', sa.DateTime, nullable=True),
        sa.Column('destruction_certificate_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now()),
        sa.ForeignKeyConstraint(['policy_id'], ['hipaa_retention_policies.id']),
        sa.UniqueConstraint('resource_type', 'resource_id', name='uq_retention_schedule_resource'),
    )
    op.create_index('ix_retention_schedule_tenant', 'hipaa_retention_schedules', ['tenant_id'])
    op.create_index('ix_retention_schedule_patient', 'hipaa_retention_schedules', ['patient_id'])
    op.create_index('ix_retention_schedule_status_date', 'hipaa_retention_schedules', ['status', 'scheduled_destruction_date'])

    # Legal Holds
    op.create_table(
        'hipaa_legal_holds',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('hold_number', sa.String(50), unique=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('hold_type', sa.String(50), nullable=False),
        sa.Column('matter_reference', sa.String(200), nullable=True),
        sa.Column('scope_type', sa.String(50), nullable=False),
        sa.Column('scope_criteria', postgresql.JSONB, nullable=False),
        sa.Column('affected_patient_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('affected_record_count', sa.Integer, default=0),
        sa.Column('legal_contact_name', sa.String(200), nullable=True),
        sa.Column('legal_contact_email', sa.String(200), nullable=True),
        sa.Column('status', sa.String(50), default='active'),
        sa.Column('effective_date', sa.Date, nullable=False),
        sa.Column('release_date', sa.Date, nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('released_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('release_approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('release_reason', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now()),
        sa.Column('released_at', sa.DateTime, nullable=True),
    )
    op.create_index('ix_legal_hold_tenant', 'hipaa_legal_holds', ['tenant_id'])

    # Destruction Certificates
    op.create_table(
        'hipaa_destruction_certificates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('certificate_number', sa.String(50), unique=True, nullable=False),
        sa.Column('destruction_date', sa.DateTime, nullable=False),
        sa.Column('destruction_method', sa.String(50), nullable=False),
        sa.Column('record_count', sa.Integer, nullable=False),
        sa.Column('record_summary', postgresql.JSONB, nullable=False),
        sa.Column('resource_types', postgresql.ARRAY(sa.String), nullable=False),
        sa.Column('affected_patient_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('verified', sa.Boolean, default=False),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('verified_at', sa.DateTime, nullable=True),
        sa.Column('verification_method', sa.String(200), nullable=True),
        sa.Column('authorized_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('authorization_date', sa.DateTime, nullable=False),
        sa.Column('certificate_hash', sa.String(64), nullable=False),
        sa.Column('certificate_retention_date', sa.Date, nullable=False),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
    )
    op.create_index('ix_destruction_cert_tenant', 'hipaa_destruction_certificates', ['tenant_id'])

    # Right of Access Requests
    op.create_table(
        'hipaa_right_of_access_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('request_number', sa.String(50), unique=True, nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('requestor_type', sa.String(50), nullable=False),
        sa.Column('representative_name', sa.String(200), nullable=True),
        sa.Column('representative_relationship', sa.String(100), nullable=True),
        sa.Column('delivery_email', sa.String(200), nullable=True),
        sa.Column('delivery_address', sa.Text, nullable=True),
        sa.Column('delivery_method', sa.String(50), nullable=False),
        sa.Column('requested_records', postgresql.JSONB, nullable=False),
        sa.Column('date_range_start', sa.Date, nullable=True),
        sa.Column('date_range_end', sa.Date, nullable=True),
        sa.Column('identity_verified', sa.Boolean, default=False),
        sa.Column('verification_method', sa.String(200), nullable=True),
        sa.Column('verification_date', sa.DateTime, nullable=True),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(50), default='received'),
        sa.Column('received_date', sa.DateTime, nullable=False),
        sa.Column('due_date', sa.DateTime, nullable=False),
        sa.Column('extension_granted', sa.Boolean, default=False),
        sa.Column('extension_reason', sa.Text, nullable=True),
        sa.Column('extended_due_date', sa.DateTime, nullable=True),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('processing_started_at', sa.DateTime, nullable=True),
        sa.Column('export_format', sa.String(50), nullable=True),
        sa.Column('export_size_bytes', sa.BigInteger, nullable=True),
        sa.Column('export_location', sa.String(500), nullable=True),
        sa.Column('export_password_protected', sa.Boolean, default=True),
        sa.Column('delivered_at', sa.DateTime, nullable=True),
        sa.Column('delivery_confirmation', sa.String(200), nullable=True),
        sa.Column('denied', sa.Boolean, default=False),
        sa.Column('denial_reason', sa.Text, nullable=True),
        sa.Column('denial_code', sa.String(50), nullable=True),
        sa.Column('fee_amount', sa.Float, nullable=True),
        sa.Column('fee_paid', sa.Boolean, default=False),
        sa.Column('fee_waived', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now()),
    )
    op.create_index('ix_roa_tenant', 'hipaa_right_of_access_requests', ['tenant_id'])
    op.create_index('ix_roa_patient', 'hipaa_right_of_access_requests', ['patient_id'])
    op.create_index('ix_roa_status_due', 'hipaa_right_of_access_requests', ['status', 'due_date'])

    # =========================================================================
    # Breach Management Tables
    # =========================================================================

    # Breach Incidents
    op.create_table(
        'hipaa_breach_incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('incident_number', sa.String(50), unique=True, nullable=False),
        sa.Column('discovered_date', sa.DateTime, nullable=False),
        sa.Column('discovered_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('discovery_method', sa.String(200), nullable=True),
        sa.Column('breach_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('breach_date', sa.Date, nullable=True),
        sa.Column('breach_start', sa.DateTime, nullable=True),
        sa.Column('breach_end', sa.DateTime, nullable=True),
        sa.Column('status', sa.String(50), default='suspected'),
        sa.Column('affected_individuals_count', sa.Integer, default=0),
        sa.Column('affected_patient_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('phi_categories_involved', postgresql.ARRAY(sa.String), nullable=False),
        sa.Column('phi_description', sa.Text, nullable=True),
        sa.Column('breach_source', sa.String(200), nullable=True),
        sa.Column('root_cause', sa.Text, nullable=True),
        sa.Column('lead_investigator', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('investigation_notes', sa.Text, nullable=True),
        sa.Column('hhs_notification_deadline', sa.DateTime, nullable=True),
        sa.Column('patient_notification_deadline', sa.DateTime, nullable=True),
        sa.Column('containment_actions', sa.Text, nullable=True),
        sa.Column('remediation_actions', sa.Text, nullable=True),
        sa.Column('lessons_learned', sa.Text, nullable=True),
        sa.Column('closed_at', sa.DateTime, nullable=True),
        sa.Column('closed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now()),
    )
    op.create_index('ix_breach_incident_tenant', 'hipaa_breach_incidents', ['tenant_id'])
    op.create_index('ix_breach_incident_status', 'hipaa_breach_incidents', ['status', 'discovered_date'])

    # Breach Assessments
    op.create_table(
        'hipaa_breach_assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assessed_date', sa.DateTime, nullable=False),
        sa.Column('assessed_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assessor_name', sa.String(200), nullable=True),
        sa.Column('factor1_phi_nature', sa.Text, nullable=False),
        sa.Column('factor1_phi_types', postgresql.ARRAY(sa.String), nullable=False),
        sa.Column('factor1_identifiability', sa.String(50), nullable=False),
        sa.Column('factor1_score', sa.Integer, nullable=False),
        sa.Column('factor2_recipient_description', sa.Text, nullable=False),
        sa.Column('factor2_recipient_type', sa.String(100), nullable=True),
        sa.Column('factor2_obligation_to_protect', sa.Boolean, nullable=True),
        sa.Column('factor2_score', sa.Integer, nullable=False),
        sa.Column('factor3_phi_accessed', sa.String(50), nullable=False),
        sa.Column('factor3_access_evidence', sa.Text, nullable=True),
        sa.Column('factor3_score', sa.Integer, nullable=False),
        sa.Column('factor4_mitigation_actions', sa.Text, nullable=False),
        sa.Column('factor4_assurances_obtained', sa.Boolean, default=False),
        sa.Column('factor4_phi_returned_destroyed', sa.Boolean, default=False),
        sa.Column('factor4_score', sa.Integer, nullable=False),
        sa.Column('overall_risk_score', sa.Integer, nullable=False),
        sa.Column('risk_level', sa.String(50), nullable=False),
        sa.Column('notification_required', sa.Boolean, nullable=False),
        sa.Column('notification_determination_reason', sa.Text, nullable=False),
        sa.Column('low_probability_exception', sa.Boolean, default=False),
        sa.Column('exception_justification', sa.Text, nullable=True),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime, nullable=True),
        sa.Column('review_comments', sa.Text, nullable=True),
        sa.Column('approved', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now()),
        sa.ForeignKeyConstraint(['incident_id'], ['hipaa_breach_incidents.id']),
    )
    op.create_index('ix_breach_assessment_tenant', 'hipaa_breach_assessments', ['tenant_id'])
    op.create_index('ix_breach_assessment_incident', 'hipaa_breach_assessments', ['incident_id'])

    # Breach Notifications
    op.create_table(
        'hipaa_breach_notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('notification_type', sa.String(50), nullable=False),
        sa.Column('recipient_type', sa.String(50), nullable=False),
        sa.Column('recipient_name', sa.String(200), nullable=True),
        sa.Column('recipient_email', sa.String(200), nullable=True),
        sa.Column('recipient_address', sa.Text, nullable=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notification_content', sa.Text, nullable=False),
        sa.Column('letter_template_used', sa.String(100), nullable=True),
        sa.Column('status', sa.String(50), default='draft'),
        sa.Column('scheduled_date', sa.DateTime, nullable=True),
        sa.Column('sent_date', sa.DateTime, nullable=True),
        sa.Column('delivered_date', sa.DateTime, nullable=True),
        sa.Column('delivery_method', sa.String(50), nullable=True),
        sa.Column('tracking_number', sa.String(100), nullable=True),
        sa.Column('delivery_confirmation', sa.String(200), nullable=True),
        sa.Column('failed_reason', sa.Text, nullable=True),
        sa.Column('retry_count', sa.Integer, default=0),
        sa.Column('alternative_notification_used', sa.Boolean, default=False),
        sa.Column('hhs_submission_id', sa.String(100), nullable=True),
        sa.Column('hhs_acknowledgment', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['incident_id'], ['hipaa_breach_incidents.id']),
    )
    op.create_index('ix_breach_notification_tenant', 'hipaa_breach_notifications', ['tenant_id'])
    op.create_index('ix_breach_notification_incident', 'hipaa_breach_notifications', ['incident_id', 'notification_type'])

    # =========================================================================
    # BAA Management Tables
    # =========================================================================

    # Business Associate Agreements
    op.create_table(
        'hipaa_business_associate_agreements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('baa_number', sa.String(50), unique=True, nullable=False),
        sa.Column('baa_type', sa.String(50), nullable=False),
        sa.Column('counterparty_name', sa.String(300), nullable=False),
        sa.Column('counterparty_type', sa.String(50), nullable=False),
        sa.Column('counterparty_address', sa.Text, nullable=True),
        sa.Column('counterparty_contact_name', sa.String(200), nullable=True),
        sa.Column('counterparty_contact_email', sa.String(200), nullable=True),
        sa.Column('counterparty_contact_phone', sa.String(50), nullable=True),
        sa.Column('services_description', sa.Text, nullable=False),
        sa.Column('phi_categories_covered', postgresql.ARRAY(sa.String), nullable=False),
        sa.Column('status', sa.String(50), default='draft'),
        sa.Column('template_used', sa.String(100), nullable=True),
        sa.Column('document_url', sa.String(500), nullable=True),
        sa.Column('document_hash', sa.String(64), nullable=True),
        sa.Column('execution_date', sa.Date, nullable=True),
        sa.Column('effective_date', sa.Date, nullable=True),
        sa.Column('expiration_date', sa.Date, nullable=True),
        sa.Column('auto_renew', sa.Boolean, default=False),
        sa.Column('renewal_term_months', sa.Integer, nullable=True),
        sa.Column('our_signatory_name', sa.String(200), nullable=True),
        sa.Column('our_signatory_title', sa.String(200), nullable=True),
        sa.Column('our_signature_date', sa.Date, nullable=True),
        sa.Column('counterparty_signatory_name', sa.String(200), nullable=True),
        sa.Column('counterparty_signatory_title', sa.String(200), nullable=True),
        sa.Column('counterparty_signature_date', sa.Date, nullable=True),
        sa.Column('esignature_envelope_id', sa.String(100), nullable=True),
        sa.Column('esignature_status', sa.String(50), nullable=True),
        sa.Column('terminated', sa.Boolean, default=False),
        sa.Column('termination_date', sa.Date, nullable=True),
        sa.Column('termination_reason', sa.Text, nullable=True),
        sa.Column('last_compliance_review', sa.Date, nullable=True),
        sa.Column('compliance_notes', sa.Text, nullable=True),
        sa.Column('parent_baa_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['parent_baa_id'], ['hipaa_business_associate_agreements.id']),
    )
    op.create_index('ix_baa_tenant', 'hipaa_business_associate_agreements', ['tenant_id'])
    op.create_index('ix_baa_status_expiration', 'hipaa_business_associate_agreements', ['status', 'expiration_date'])
    op.create_index('ix_baa_counterparty', 'hipaa_business_associate_agreements', ['counterparty_name'])

    # BAA Amendments
    op.create_table(
        'hipaa_baa_amendments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('baa_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amendment_number', sa.Integer, nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('changes_summary', sa.Text, nullable=False),
        sa.Column('effective_date', sa.Date, nullable=False),
        sa.Column('document_url', sa.String(500), nullable=True),
        sa.Column('executed', sa.Boolean, default=False),
        sa.Column('execution_date', sa.Date, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['baa_id'], ['hipaa_business_associate_agreements.id']),
    )
    op.create_index('ix_baa_amendment_tenant', 'hipaa_baa_amendments', ['tenant_id'])
    op.create_index('ix_baa_amendment_baa', 'hipaa_baa_amendments', ['baa_id'])

    # BAA Templates
    op.create_table(
        'hipaa_baa_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('template_type', sa.String(50), nullable=False),
        sa.Column('template_content', sa.Text, nullable=False),
        sa.Column('variable_fields', postgresql.JSONB, nullable=True),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('previous_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved', sa.Boolean, default=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime, nullable=True),
        sa.Column('legal_review_date', sa.Date, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_default', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index('ix_baa_template_tenant', 'hipaa_baa_templates', ['tenant_id'])

    # =========================================================================
    # Training Management Tables
    # =========================================================================

    # Training Modules
    op.create_table(
        'hipaa_training_modules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('training_type', sa.String(50), nullable=False),
        sa.Column('content_url', sa.String(500), nullable=True),
        sa.Column('duration_minutes', sa.Integer, nullable=False),
        sa.Column('passing_score', sa.Integer, default=80),
        sa.Column('required_for_roles', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('required_for_all', sa.Boolean, default=False),
        sa.Column('required_for_phi_access', sa.Boolean, default=False),
        sa.Column('recurrence_months', sa.Integer, nullable=True),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('effective_date', sa.Date, nullable=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index('ix_training_module_tenant', 'hipaa_training_modules', ['tenant_id'])

    # Training Assignments
    op.create_table(
        'hipaa_training_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('module_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_name', sa.String(200), nullable=True),
        sa.Column('user_email', sa.String(200), nullable=True),
        sa.Column('user_role', sa.String(100), nullable=True),
        sa.Column('assigned_date', sa.DateTime, nullable=False),
        sa.Column('due_date', sa.DateTime, nullable=False),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(50), default='assigned'),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('score', sa.Integer, nullable=True),
        sa.Column('passed', sa.Boolean, nullable=True),
        sa.Column('attempts', sa.Integer, default=0),
        sa.Column('certificate_id', sa.String(100), nullable=True),
        sa.Column('certificate_url', sa.String(500), nullable=True),
        sa.Column('reminder_sent_count', sa.Integer, default=0),
        sa.Column('last_reminder_sent', sa.DateTime, nullable=True),
        sa.Column('next_due_date', sa.DateTime, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now()),
        sa.ForeignKeyConstraint(['module_id'], ['hipaa_training_modules.id']),
    )
    op.create_index('ix_training_assignment_tenant', 'hipaa_training_assignments', ['tenant_id'])
    op.create_index('ix_training_assignment_user', 'hipaa_training_assignments', ['user_id', 'module_id'])
    op.create_index('ix_training_assignment_status', 'hipaa_training_assignments', ['status', 'due_date'])

    # Policy Documents
    op.create_table(
        'hipaa_policy_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('policy_number', sa.String(50), unique=True, nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('previous_version_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('effective_date', sa.Date, nullable=False),
        sa.Column('review_date', sa.Date, nullable=True),
        sa.Column('approved', sa.Boolean, default=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime, nullable=True),
        sa.Column('requires_acknowledgment', sa.Boolean, default=True),
        sa.Column('required_for_roles', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('required_for_all', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index('ix_policy_document_tenant', 'hipaa_policy_documents', ['tenant_id'])

    # Policy Acknowledgments
    op.create_table(
        'hipaa_policy_acknowledgments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('policy_version', sa.String(20), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_name', sa.String(200), nullable=True),
        sa.Column('user_role', sa.String(100), nullable=True),
        sa.Column('acknowledged', sa.Boolean, default=False),
        sa.Column('acknowledged_at', sa.DateTime, nullable=True),
        sa.Column('signature_ip', postgresql.INET, nullable=True),
        sa.Column('signature_user_agent', sa.Text, nullable=True),
        sa.Column('signature_hash', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.ForeignKeyConstraint(['policy_id'], ['hipaa_policy_documents.id']),
        sa.UniqueConstraint('policy_id', 'policy_version', 'user_id', name='uq_policy_acknowledgment'),
    )
    op.create_index('ix_policy_ack_tenant', 'hipaa_policy_acknowledgments', ['tenant_id'])
    op.create_index('ix_policy_ack_user', 'hipaa_policy_acknowledgments', ['user_id'])

    # =========================================================================
    # Risk Assessment Tables
    # =========================================================================

    # Risk Assessments
    op.create_table(
        'hipaa_risk_assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assessment_number', sa.String(50), unique=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('assessment_type', sa.String(50), nullable=False),
        sa.Column('scope_description', sa.Text, nullable=False),
        sa.Column('systems_in_scope', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('departments_in_scope', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('target_completion_date', sa.Date, nullable=False),
        sa.Column('actual_completion_date', sa.Date, nullable=True),
        sa.Column('lead_assessor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lead_assessor_name', sa.String(200), nullable=True),
        sa.Column('assessment_team', postgresql.JSONB, nullable=True),
        sa.Column('methodology', sa.String(100), nullable=True),
        sa.Column('methodology_version', sa.String(20), nullable=True),
        sa.Column('total_risks_identified', sa.Integer, default=0),
        sa.Column('critical_risks', sa.Integer, default=0),
        sa.Column('high_risks', sa.Integer, default=0),
        sa.Column('medium_risks', sa.Integer, default=0),
        sa.Column('low_risks', sa.Integer, default=0),
        sa.Column('overall_risk_level', sa.String(50), nullable=True),
        sa.Column('status', sa.String(50), default='in_progress'),
        sa.Column('approved', sa.Boolean, default=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime, nullable=True),
        sa.Column('executive_summary', sa.Text, nullable=True),
        sa.Column('report_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index('ix_risk_assessment_tenant', 'hipaa_risk_assessments', ['tenant_id'])

    # Risk Items
    op.create_table(
        'hipaa_risk_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('risk_number', sa.String(50), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('safeguard_type', sa.String(100), nullable=True),
        sa.Column('hipaa_reference', sa.String(100), nullable=True),
        sa.Column('threat_source', sa.String(200), nullable=True),
        sa.Column('vulnerability', sa.Text, nullable=True),
        sa.Column('existing_controls', sa.Text, nullable=True),
        sa.Column('likelihood', sa.Integer, nullable=False),
        sa.Column('impact', sa.Integer, nullable=False),
        sa.Column('inherent_risk_score', sa.Integer, nullable=False),
        sa.Column('risk_level', sa.String(50), nullable=False),
        sa.Column('control_effectiveness', sa.Integer, nullable=True),
        sa.Column('residual_risk_score', sa.Integer, nullable=True),
        sa.Column('residual_risk_level', sa.String(50), nullable=True),
        sa.Column('evidence', sa.Text, nullable=True),
        sa.Column('affected_assets', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('status', sa.String(50), default='planned'),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now()),
        sa.ForeignKeyConstraint(['assessment_id'], ['hipaa_risk_assessments.id']),
        sa.UniqueConstraint('assessment_id', 'risk_number', name='uq_risk_item_number'),
    )
    op.create_index('ix_risk_item_tenant', 'hipaa_risk_items', ['tenant_id'])
    op.create_index('ix_risk_item_assessment', 'hipaa_risk_items', ['assessment_id'])
    op.create_index('ix_risk_item_level', 'hipaa_risk_items', ['risk_level', 'status'])

    # Remediation Plans
    op.create_table(
        'hipaa_remediation_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('risk_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('owner_name', sa.String(200), nullable=True),
        sa.Column('planned_start_date', sa.Date, nullable=False),
        sa.Column('target_completion_date', sa.Date, nullable=False),
        sa.Column('actual_start_date', sa.Date, nullable=True),
        sa.Column('actual_completion_date', sa.Date, nullable=True),
        sa.Column('status', sa.String(50), default='planned'),
        sa.Column('percent_complete', sa.Integer, default=0),
        sa.Column('risk_acceptance_approved', sa.Boolean, default=False),
        sa.Column('risk_acceptance_approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('risk_acceptance_reason', sa.Text, nullable=True),
        sa.Column('risk_acceptance_expiration', sa.Date, nullable=True),
        sa.Column('verification_required', sa.Boolean, default=True),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('verified_at', sa.DateTime, nullable=True),
        sa.Column('verification_evidence', sa.Text, nullable=True),
        sa.Column('estimated_cost', sa.Float, nullable=True),
        sa.Column('actual_cost', sa.Float, nullable=True),
        sa.Column('implementation_notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['risk_id'], ['hipaa_risk_items.id']),
    )
    op.create_index('ix_remediation_plan_tenant', 'hipaa_remediation_plans', ['tenant_id'])
    op.create_index('ix_remediation_plan_risk', 'hipaa_remediation_plans', ['risk_id'])
    op.create_index('ix_remediation_status_date', 'hipaa_remediation_plans', ['status', 'target_completion_date'])

    # Risk Register
    op.create_table(
        'hipaa_risk_register',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('risk_id', sa.String(50), unique=True, nullable=False),
        sa.Column('source_assessment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_risk_item_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('current_risk_level', sa.String(50), nullable=False),
        sa.Column('current_likelihood', sa.Integer, nullable=False),
        sa.Column('current_impact', sa.Integer, nullable=False),
        sa.Column('target_risk_level', sa.String(50), nullable=True),
        sa.Column('treatment_strategy', sa.String(50), nullable=False),
        sa.Column('treatment_status', sa.String(50), default='planned'),
        sa.Column('risk_owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('risk_owner_name', sa.String(200), nullable=True),
        sa.Column('identified_date', sa.Date, nullable=False),
        sa.Column('target_resolution_date', sa.Date, nullable=True),
        sa.Column('last_review_date', sa.Date, nullable=True),
        sa.Column('next_review_date', sa.Date, nullable=True),
        sa.Column('risk_trend', sa.String(20), nullable=True),
        sa.Column('historical_scores', postgresql.JSONB, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now()),
        sa.ForeignKeyConstraint(['source_assessment_id'], ['hipaa_risk_assessments.id']),
        sa.ForeignKeyConstraint(['source_risk_item_id'], ['hipaa_risk_items.id']),
    )
    op.create_index('ix_risk_register_tenant', 'hipaa_risk_register', ['tenant_id'])
    op.create_index('ix_risk_register_level', 'hipaa_risk_register', ['current_risk_level', 'is_active'])


def downgrade() -> None:
    # Risk Assessment Tables
    op.drop_index('ix_risk_register_level', 'hipaa_risk_register')
    op.drop_index('ix_risk_register_tenant', 'hipaa_risk_register')
    op.drop_table('hipaa_risk_register')

    op.drop_index('ix_remediation_status_date', 'hipaa_remediation_plans')
    op.drop_index('ix_remediation_plan_risk', 'hipaa_remediation_plans')
    op.drop_index('ix_remediation_plan_tenant', 'hipaa_remediation_plans')
    op.drop_table('hipaa_remediation_plans')

    op.drop_index('ix_risk_item_level', 'hipaa_risk_items')
    op.drop_index('ix_risk_item_assessment', 'hipaa_risk_items')
    op.drop_index('ix_risk_item_tenant', 'hipaa_risk_items')
    op.drop_table('hipaa_risk_items')

    op.drop_index('ix_risk_assessment_tenant', 'hipaa_risk_assessments')
    op.drop_table('hipaa_risk_assessments')

    # Training Tables
    op.drop_index('ix_policy_ack_user', 'hipaa_policy_acknowledgments')
    op.drop_index('ix_policy_ack_tenant', 'hipaa_policy_acknowledgments')
    op.drop_table('hipaa_policy_acknowledgments')

    op.drop_index('ix_policy_document_tenant', 'hipaa_policy_documents')
    op.drop_table('hipaa_policy_documents')

    op.drop_index('ix_training_assignment_status', 'hipaa_training_assignments')
    op.drop_index('ix_training_assignment_user', 'hipaa_training_assignments')
    op.drop_index('ix_training_assignment_tenant', 'hipaa_training_assignments')
    op.drop_table('hipaa_training_assignments')

    op.drop_index('ix_training_module_tenant', 'hipaa_training_modules')
    op.drop_table('hipaa_training_modules')

    # BAA Tables
    op.drop_index('ix_baa_template_tenant', 'hipaa_baa_templates')
    op.drop_table('hipaa_baa_templates')

    op.drop_index('ix_baa_amendment_baa', 'hipaa_baa_amendments')
    op.drop_index('ix_baa_amendment_tenant', 'hipaa_baa_amendments')
    op.drop_table('hipaa_baa_amendments')

    op.drop_index('ix_baa_counterparty', 'hipaa_business_associate_agreements')
    op.drop_index('ix_baa_status_expiration', 'hipaa_business_associate_agreements')
    op.drop_index('ix_baa_tenant', 'hipaa_business_associate_agreements')
    op.drop_table('hipaa_business_associate_agreements')

    # Breach Tables
    op.drop_index('ix_breach_notification_incident', 'hipaa_breach_notifications')
    op.drop_index('ix_breach_notification_tenant', 'hipaa_breach_notifications')
    op.drop_table('hipaa_breach_notifications')

    op.drop_index('ix_breach_assessment_incident', 'hipaa_breach_assessments')
    op.drop_index('ix_breach_assessment_tenant', 'hipaa_breach_assessments')
    op.drop_table('hipaa_breach_assessments')

    op.drop_index('ix_breach_incident_status', 'hipaa_breach_incidents')
    op.drop_index('ix_breach_incident_tenant', 'hipaa_breach_incidents')
    op.drop_table('hipaa_breach_incidents')

    # Retention Tables
    op.drop_index('ix_roa_status_due', 'hipaa_right_of_access_requests')
    op.drop_index('ix_roa_patient', 'hipaa_right_of_access_requests')
    op.drop_index('ix_roa_tenant', 'hipaa_right_of_access_requests')
    op.drop_table('hipaa_right_of_access_requests')

    op.drop_index('ix_destruction_cert_tenant', 'hipaa_destruction_certificates')
    op.drop_table('hipaa_destruction_certificates')

    op.drop_index('ix_legal_hold_tenant', 'hipaa_legal_holds')
    op.drop_table('hipaa_legal_holds')

    op.drop_index('ix_retention_schedule_status_date', 'hipaa_retention_schedules')
    op.drop_index('ix_retention_schedule_patient', 'hipaa_retention_schedules')
    op.drop_index('ix_retention_schedule_tenant', 'hipaa_retention_schedules')
    op.drop_table('hipaa_retention_schedules')

    op.drop_index('ix_retention_policy_category', 'hipaa_retention_policies')
    op.drop_index('ix_retention_policy_tenant', 'hipaa_retention_policies')
    op.drop_table('hipaa_retention_policies')

    # Access Control Tables
    op.drop_index('ix_vip_patients_tenant', 'hipaa_vip_patients')
    op.drop_table('hipaa_vip_patients')

    op.drop_index('ix_access_anomaly_type_user', 'hipaa_access_anomalies')
    op.drop_index('ix_access_anomaly_severity', 'hipaa_access_anomalies')
    op.drop_index('ix_access_anomaly_tenant', 'hipaa_access_anomalies')
    op.drop_table('hipaa_access_anomalies')

    op.drop_index('ix_access_cert_reviewer', 'hipaa_access_certifications')
    op.drop_index('ix_access_cert_user', 'hipaa_access_certifications')
    op.drop_index('ix_access_cert_campaign', 'hipaa_access_certifications')
    op.drop_index('ix_access_cert_tenant', 'hipaa_access_certifications')
    op.drop_table('hipaa_access_certifications')

    op.drop_index('ix_cert_campaign_tenant', 'hipaa_certification_campaigns')
    op.drop_table('hipaa_certification_campaigns')

    op.drop_index('ix_access_request_status', 'hipaa_access_requests')
    op.drop_index('ix_access_request_patient', 'hipaa_access_requests')
    op.drop_index('ix_access_request_requester', 'hipaa_access_requests')
    op.drop_index('ix_access_request_tenant', 'hipaa_access_requests')
    op.drop_table('hipaa_access_requests')

    op.drop_index('ix_treatment_rel_patient_provider', 'hipaa_treatment_relationships')
    op.drop_index('ix_treatment_rel_provider', 'hipaa_treatment_relationships')
    op.drop_index('ix_treatment_rel_patient', 'hipaa_treatment_relationships')
    op.drop_table('hipaa_treatment_relationships')

    # Audit Tables
    op.drop_index('ix_audit_retention_tenant', 'hipaa_audit_retention_policies')
    op.drop_table('hipaa_audit_retention_policies')

    op.drop_index('ix_phi_audit_action_category', 'hipaa_phi_audit_logs')
    op.drop_index('ix_phi_audit_patient_recorded', 'hipaa_phi_audit_logs')
    op.drop_index('ix_phi_audit_user_recorded', 'hipaa_phi_audit_logs')
    op.drop_index('ix_phi_audit_tenant_recorded', 'hipaa_phi_audit_logs')
    op.drop_index('ix_phi_audit_tenant_id', 'hipaa_phi_audit_logs')
    op.drop_table('hipaa_phi_audit_logs')

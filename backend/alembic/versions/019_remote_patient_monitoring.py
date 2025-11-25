"""Remote Patient Monitoring

Revision ID: 019_remote_patient_monitoring
Revises: 018_api_marketplace
Create Date: 2024-11-25

EPIC-019: Creates tables for Remote Patient Monitoring platform
- Device integration and management
- Data ingestion pipeline
- Alert management system
- Care protocol automation
- RPM billing (CPT codes 99453, 99454, 99457, 99458)
- Patient engagement features
- Analytics and trend analysis
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

# revision identifiers
revision = '019_remote_patient_monitoring'
down_revision = '018_api_marketplace'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========================================================================
    # DEVICE TABLES
    # ========================================================================

    # RPM Devices
    op.create_table(
        'rpm_devices',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('serial_number', sa.String(100), nullable=True),
        sa.Column('mac_address', sa.String(50), nullable=True),
        sa.Column('device_identifier', sa.String(200), nullable=False),
        sa.Column('vendor', sa.String(30), nullable=False),
        sa.Column('device_type', sa.String(50), nullable=False),
        sa.Column('model', sa.String(200), nullable=True),
        sa.Column('firmware_version', sa.String(50), nullable=True),
        sa.Column('fhir_device_id', UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(30), default='registered'),
        sa.Column('battery_level', sa.Integer, nullable=True),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_reading_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('oauth_access_token', sa.Text, nullable=True),
        sa.Column('oauth_refresh_token', sa.Text, nullable=True),
        sa.Column('oauth_token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'vendor', 'device_identifier', name='uq_rpm_device_identifier'),
    )
    op.create_index('ix_rpm_devices_tenant', 'rpm_devices', ['tenant_id'])
    op.create_index('idx_rpm_devices_tenant_status', 'rpm_devices', ['tenant_id', 'status'])
    op.create_index('idx_rpm_devices_vendor', 'rpm_devices', ['vendor'])

    # RPM Enrollments (needed early for foreign keys)
    op.create_table(
        'rpm_enrollments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', UUID(as_uuid=True), nullable=False),
        sa.Column('fhir_patient_id', UUID(as_uuid=True), nullable=True),
        sa.Column('protocol_id', UUID(as_uuid=True), nullable=True),
        sa.Column('program_name', sa.String(200), nullable=False),
        sa.Column('primary_condition', sa.String(100), nullable=False),
        sa.Column('secondary_conditions', ARRAY(sa.String), default=[]),
        sa.Column('primary_provider_id', UUID(as_uuid=True), nullable=False),
        sa.Column('care_team_ids', ARRAY(UUID(as_uuid=True)), default=[]),
        sa.Column('status', sa.String(30), default='pending'),
        sa.Column('enrolled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('discharge_reason', sa.String(200), nullable=True),
        sa.Column('consent_obtained', sa.Boolean, default=False),
        sa.Column('consent_date', sa.Date, nullable=True),
        sa.Column('consent_document_id', UUID(as_uuid=True), nullable=True),
        sa.Column('target_readings_per_day', sa.Integer, default=1),
        sa.Column('goals', JSONB, default={}),
        sa.Column('enrolled_by', UUID(as_uuid=True), nullable=False),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_rpm_enrollments_tenant', 'rpm_enrollments', ['tenant_id'])
    op.create_index('ix_rpm_enrollments_patient', 'rpm_enrollments', ['patient_id'])
    op.create_index('idx_enrollments_patient_status', 'rpm_enrollments', ['patient_id', 'status'])
    op.create_index('idx_enrollments_tenant_condition', 'rpm_enrollments', ['tenant_id', 'primary_condition'])
    op.create_index('idx_enrollments_provider', 'rpm_enrollments', ['primary_provider_id'])

    # Device Assignments
    op.create_table(
        'rpm_device_assignments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', UUID(as_uuid=True), sa.ForeignKey('rpm_devices.id'), nullable=False),
        sa.Column('patient_id', UUID(as_uuid=True), nullable=False),
        sa.Column('enrollment_id', UUID(as_uuid=True), sa.ForeignKey('rpm_enrollments.id'), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('assigned_by', UUID(as_uuid=True), nullable=False),
        sa.Column('unassigned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('unassigned_by', UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('reading_frequency', sa.String(50), default='daily'),
        sa.Column('target_readings_per_day', sa.Integer, default=1),
        sa.Column('reminder_times', ARRAY(sa.String), default=[]),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_rpm_device_assignments_tenant', 'rpm_device_assignments', ['tenant_id'])
    op.create_index('ix_rpm_device_assignments_patient', 'rpm_device_assignments', ['patient_id'])
    op.create_index('idx_device_assignments_patient_active', 'rpm_device_assignments', ['patient_id', 'is_active'])
    op.create_index('idx_device_assignments_device_active', 'rpm_device_assignments', ['device_id', 'is_active'])

    # ========================================================================
    # READING TABLES
    # ========================================================================

    # Device Readings
    op.create_table(
        'rpm_device_readings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', UUID(as_uuid=True), sa.ForeignKey('rpm_devices.id'), nullable=True),
        sa.Column('patient_id', UUID(as_uuid=True), nullable=False),
        sa.Column('enrollment_id', UUID(as_uuid=True), sa.ForeignKey('rpm_enrollments.id'), nullable=True),
        sa.Column('reading_type', sa.String(50), nullable=False),
        sa.Column('value', sa.Float, nullable=False),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('secondary_value', sa.Float, nullable=True),
        sa.Column('secondary_unit', sa.String(50), nullable=True),
        sa.Column('measured_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('timezone', sa.String(50), nullable=True),
        sa.Column('status', sa.String(30), default='pending'),
        sa.Column('is_manual', sa.Boolean, default=False),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('is_valid', sa.Boolean, default=True),
        sa.Column('validation_errors', ARRAY(sa.String), default=[]),
        sa.Column('flagged_reason', sa.String(500), nullable=True),
        sa.Column('fhir_observation_id', UUID(as_uuid=True), nullable=True),
        sa.Column('context', JSONB, default={}),
        sa.Column('raw_data', JSONB, default={}),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_rpm_device_readings_tenant', 'rpm_device_readings', ['tenant_id'])
    op.create_index('ix_rpm_device_readings_patient', 'rpm_device_readings', ['patient_id'])
    op.create_index('idx_readings_patient_type_time', 'rpm_device_readings', ['patient_id', 'reading_type', 'measured_at'])
    op.create_index('idx_readings_tenant_time', 'rpm_device_readings', ['tenant_id', 'measured_at'])
    op.create_index('idx_readings_enrollment_time', 'rpm_device_readings', ['enrollment_id', 'measured_at'])
    op.create_index('idx_readings_device_time', 'rpm_device_readings', ['device_id', 'measured_at'])

    # Reading Batches
    op.create_table(
        'rpm_reading_batches',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('source', sa.String(100), nullable=False),
        sa.Column('source_reference', sa.String(200), nullable=True),
        sa.Column('total_readings', sa.Integer, default=0),
        sa.Column('processed_readings', sa.Integer, default=0),
        sa.Column('failed_readings', sa.Integer, default=0),
        sa.Column('duplicate_readings', sa.Integer, default=0),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_rpm_reading_batches_tenant', 'rpm_reading_batches', ['tenant_id'])
    op.create_index('idx_reading_batches_tenant_status', 'rpm_reading_batches', ['tenant_id', 'status'])

    # Data Quality Metrics
    op.create_table(
        'rpm_data_quality_metrics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', UUID(as_uuid=True), sa.ForeignKey('rpm_devices.id'), nullable=True),
        sa.Column('period_start', sa.Date, nullable=False),
        sa.Column('period_end', sa.Date, nullable=False),
        sa.Column('expected_readings', sa.Integer, default=0),
        sa.Column('actual_readings', sa.Integer, default=0),
        sa.Column('valid_readings', sa.Integer, default=0),
        sa.Column('flagged_readings', sa.Integer, default=0),
        sa.Column('compliance_rate', sa.Float, default=0.0),
        sa.Column('days_with_data', sa.Integer, default=0),
        sa.Column('longest_gap_hours', sa.Float, default=0.0),
        sa.Column('avg_reading_interval_hours', sa.Float, nullable=True),
        sa.Column('data_quality_score', sa.Float, default=100.0),
        sa.Column('consistency_score', sa.Float, default=100.0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('patient_id', 'device_id', 'period_start', 'period_end', name='uq_data_quality_period'),
    )
    op.create_index('ix_rpm_data_quality_tenant', 'rpm_data_quality_metrics', ['tenant_id'])
    op.create_index('ix_rpm_data_quality_patient', 'rpm_data_quality_metrics', ['patient_id'])
    op.create_index('idx_data_quality_patient_period', 'rpm_data_quality_metrics', ['patient_id', 'period_start'])

    # ========================================================================
    # ALERT TABLES
    # ========================================================================

    # Alert Rules
    op.create_table(
        'rpm_alert_rules',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('reading_type', sa.String(50), nullable=True),
        sa.Column('is_global', sa.Boolean, default=False),
        sa.Column('threshold_low', sa.Float, nullable=True),
        sa.Column('threshold_high', sa.Float, nullable=True),
        sa.Column('threshold_critical_low', sa.Float, nullable=True),
        sa.Column('threshold_critical_high', sa.Float, nullable=True),
        sa.Column('trend_direction', sa.String(20), nullable=True),
        sa.Column('trend_threshold_percent', sa.Float, nullable=True),
        sa.Column('trend_window_hours', sa.Integer, nullable=True),
        sa.Column('severity', sa.String(20), default='medium'),
        sa.Column('alert_type', sa.String(30), default='threshold_breach'),
        sa.Column('cooldown_minutes', sa.Integer, default=60),
        sa.Column('notify_provider', sa.Boolean, default=True),
        sa.Column('notify_patient', sa.Boolean, default=False),
        sa.Column('notify_care_team', sa.Boolean, default=True),
        sa.Column('escalation_minutes', sa.Integer, default=30),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('conditions', JSONB, default={}),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_by', UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_rpm_alert_rules_tenant', 'rpm_alert_rules', ['tenant_id'])
    op.create_index('idx_alert_rules_tenant_type', 'rpm_alert_rules', ['tenant_id', 'reading_type'])
    op.create_index('idx_alert_rules_active', 'rpm_alert_rules', ['is_active'])

    # Patient Alert Rules
    op.create_table(
        'rpm_patient_alert_rules',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('rule_id', UUID(as_uuid=True), sa.ForeignKey('rpm_alert_rules.id'), nullable=False),
        sa.Column('patient_id', UUID(as_uuid=True), nullable=False),
        sa.Column('enrollment_id', UUID(as_uuid=True), sa.ForeignKey('rpm_enrollments.id'), nullable=True),
        sa.Column('threshold_low', sa.Float, nullable=True),
        sa.Column('threshold_high', sa.Float, nullable=True),
        sa.Column('threshold_critical_low', sa.Float, nullable=True),
        sa.Column('threshold_critical_high', sa.Float, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_muted', sa.Boolean, default=False),
        sa.Column('muted_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('rule_id', 'patient_id', name='uq_patient_rule'),
    )
    op.create_index('ix_rpm_patient_alert_rules_tenant', 'rpm_patient_alert_rules', ['tenant_id'])
    op.create_index('ix_rpm_patient_alert_rules_patient', 'rpm_patient_alert_rules', ['patient_id'])
    op.create_index('idx_patient_rules_patient', 'rpm_patient_alert_rules', ['patient_id'])

    # RPM Alerts
    op.create_table(
        'rpm_alerts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', UUID(as_uuid=True), nullable=False),
        sa.Column('enrollment_id', UUID(as_uuid=True), sa.ForeignKey('rpm_enrollments.id'), nullable=True),
        sa.Column('rule_id', UUID(as_uuid=True), sa.ForeignKey('rpm_alert_rules.id'), nullable=True),
        sa.Column('reading_id', UUID(as_uuid=True), sa.ForeignKey('rpm_device_readings.id'), nullable=True),
        sa.Column('alert_type', sa.String(30), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('status', sa.String(30), default='triggered'),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('reading_value', sa.Float, nullable=True),
        sa.Column('threshold_value', sa.Float, nullable=True),
        sa.Column('reading_type', sa.String(50), nullable=True),
        sa.Column('ai_analysis', sa.Text, nullable=True),
        sa.Column('ai_recommendation', sa.Text, nullable=True),
        sa.Column('ai_confidence', sa.Float, nullable=True),
        sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledged_by', UUID(as_uuid=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', UUID(as_uuid=True), nullable=True),
        sa.Column('resolution_notes', sa.Text, nullable=True),
        sa.Column('escalated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('escalation_level', sa.Integer, default=0),
        sa.Column('escalated_to', ARRAY(UUID(as_uuid=True)), default=[]),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_rpm_alerts_tenant', 'rpm_alerts', ['tenant_id'])
    op.create_index('ix_rpm_alerts_patient', 'rpm_alerts', ['patient_id'])
    op.create_index('idx_alerts_patient_status', 'rpm_alerts', ['patient_id', 'status'])
    op.create_index('idx_alerts_tenant_severity', 'rpm_alerts', ['tenant_id', 'severity', 'status'])
    op.create_index('idx_alerts_triggered_at', 'rpm_alerts', ['triggered_at'])

    # Alert Notifications
    op.create_table(
        'rpm_alert_notifications',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('alert_id', UUID(as_uuid=True), sa.ForeignKey('rpm_alerts.id'), nullable=False),
        sa.Column('recipient_id', UUID(as_uuid=True), nullable=False),
        sa.Column('recipient_type', sa.String(50), nullable=False),
        sa.Column('channel', sa.String(30), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), default='sent'),
        sa.Column('external_id', sa.String(200), nullable=True),
        sa.Column('metadata', JSONB, default={}),
    )
    op.create_index('ix_rpm_alert_notifications_tenant', 'rpm_alert_notifications', ['tenant_id'])
    op.create_index('idx_alert_notifications_alert', 'rpm_alert_notifications', ['alert_id'])

    # ========================================================================
    # CARE PROTOCOL TABLES
    # ========================================================================

    # Care Protocols
    op.create_table(
        'rpm_care_protocols',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('condition', sa.String(100), nullable=False),
        sa.Column('version', sa.String(20), default='1.0'),
        sa.Column('duration_days', sa.Integer, nullable=True),
        sa.Column('reading_types', ARRAY(sa.String), default=[]),
        sa.Column('target_readings_per_day', sa.Integer, default=1),
        sa.Column('status', sa.String(30), default='draft'),
        sa.Column('is_template', sa.Boolean, default=False),
        sa.Column('clinical_guidelines', JSONB, default={}),
        sa.Column('evidence_references', ARRAY(sa.String), default=[]),
        sa.Column('created_by', UUID(as_uuid=True), nullable=False),
        sa.Column('approved_by', UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_rpm_care_protocols_tenant', 'rpm_care_protocols', ['tenant_id'])
    op.create_index('idx_protocols_tenant_condition', 'rpm_care_protocols', ['tenant_id', 'condition'])
    op.create_index('idx_protocols_status', 'rpm_care_protocols', ['status'])

    # Add protocol_id foreign key to enrollments
    op.create_foreign_key(
        'fk_enrollment_protocol',
        'rpm_enrollments', 'rpm_care_protocols',
        ['protocol_id'], ['id']
    )

    # Protocol Triggers
    op.create_table(
        'rpm_protocol_triggers',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('protocol_id', UUID(as_uuid=True), sa.ForeignKey('rpm_care_protocols.id'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('trigger_type', sa.String(30), nullable=False),
        sa.Column('reading_type', sa.String(50), nullable=True),
        sa.Column('condition_operator', sa.String(20), nullable=True),
        sa.Column('condition_value', sa.Float, nullable=True),
        sa.Column('condition_value_2', sa.Float, nullable=True),
        sa.Column('condition_unit', sa.String(50), nullable=True),
        sa.Column('consecutive_count', sa.Integer, default=1),
        sa.Column('schedule_cron', sa.String(100), nullable=True),
        sa.Column('schedule_days', ARRAY(sa.Integer), default=[]),
        sa.Column('priority', sa.Integer, default=50),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('conditions', JSONB, default={}),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_triggers_protocol', 'rpm_protocol_triggers', ['protocol_id'])

    # Protocol Actions
    op.create_table(
        'rpm_protocol_actions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('trigger_id', UUID(as_uuid=True), sa.ForeignKey('rpm_protocol_triggers.id'), nullable=False),
        sa.Column('action_type', sa.String(30), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('message_template', sa.Text, nullable=True),
        sa.Column('channel', sa.String(30), nullable=True),
        sa.Column('recipient_type', sa.String(50), nullable=True),
        sa.Column('delay_minutes', sa.Integer, default=0),
        sa.Column('requires_approval', sa.Boolean, default=False),
        sa.Column('approval_role', sa.String(50), nullable=True),
        sa.Column('sequence', sa.Integer, default=0),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('config', JSONB, default={}),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_actions_trigger', 'rpm_protocol_actions', ['trigger_id'])

    # Protocol Executions
    op.create_table(
        'rpm_protocol_executions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('enrollment_id', UUID(as_uuid=True), sa.ForeignKey('rpm_enrollments.id'), nullable=False),
        sa.Column('action_id', UUID(as_uuid=True), sa.ForeignKey('rpm_protocol_actions.id'), nullable=False),
        sa.Column('trigger_reading_id', UUID(as_uuid=True), sa.ForeignKey('rpm_device_readings.id'), nullable=True),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('requires_approval', sa.Boolean, default=False),
        sa.Column('approved_by', UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text, nullable=True),
        sa.Column('success', sa.Boolean, nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('result_data', JSONB, default={}),
        sa.Column('external_reference', sa.String(200), nullable=True),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_rpm_protocol_executions_tenant', 'rpm_protocol_executions', ['tenant_id'])
    op.create_index('idx_executions_enrollment', 'rpm_protocol_executions', ['enrollment_id'])
    op.create_index('idx_executions_status', 'rpm_protocol_executions', ['status'])

    # ========================================================================
    # BILLING TABLES
    # ========================================================================

    # Monitoring Periods
    op.create_table(
        'rpm_monitoring_periods',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('enrollment_id', UUID(as_uuid=True), sa.ForeignKey('rpm_enrollments.id'), nullable=False),
        sa.Column('patient_id', UUID(as_uuid=True), nullable=False),
        sa.Column('period_start', sa.Date, nullable=False),
        sa.Column('period_end', sa.Date, nullable=False),
        sa.Column('period_month', sa.Integer, nullable=False),
        sa.Column('is_current', sa.Boolean, default=True),
        sa.Column('days_with_readings', sa.Integer, default=0),
        sa.Column('total_readings', sa.Integer, default=0),
        sa.Column('qualifies_for_99454', sa.Boolean, default=False),
        sa.Column('clinical_time_minutes', sa.Integer, default=0),
        sa.Column('interactive_time_minutes', sa.Integer, default=0),
        sa.Column('qualifies_for_99457', sa.Boolean, default=False),
        sa.Column('qualifies_for_99458', sa.Boolean, default=False),
        sa.Column('device_setup_done', sa.Boolean, default=False),
        sa.Column('device_setup_date', sa.Date, nullable=True),
        sa.Column('billing_generated', sa.Boolean, default=False),
        sa.Column('billing_generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('billing_codes', ARRAY(sa.String), default=[]),
        sa.Column('time_entries', JSONB, default=[]),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('enrollment_id', 'period_month', name='uq_monitoring_period'),
    )
    op.create_index('ix_rpm_monitoring_periods_tenant', 'rpm_monitoring_periods', ['tenant_id'])
    op.create_index('ix_rpm_monitoring_periods_patient', 'rpm_monitoring_periods', ['patient_id'])
    op.create_index('idx_monitoring_periods_patient_month', 'rpm_monitoring_periods', ['patient_id', 'period_month'])

    # Clinical Time Entries
    op.create_table(
        'rpm_clinical_time_entries',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('monitoring_period_id', UUID(as_uuid=True), sa.ForeignKey('rpm_monitoring_periods.id'), nullable=False),
        sa.Column('enrollment_id', UUID(as_uuid=True), sa.ForeignKey('rpm_enrollments.id'), nullable=False),
        sa.Column('provider_id', UUID(as_uuid=True), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Integer, nullable=False),
        sa.Column('activity_type', sa.String(100), nullable=False),
        sa.Column('is_interactive', sa.Boolean, default=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('alert_id', UUID(as_uuid=True), sa.ForeignKey('rpm_alerts.id'), nullable=True),
        sa.Column('reading_ids', ARRAY(UUID(as_uuid=True)), default=[]),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_rpm_clinical_time_entries_tenant', 'rpm_clinical_time_entries', ['tenant_id'])
    op.create_index('idx_time_entries_period', 'rpm_clinical_time_entries', ['monitoring_period_id'])
    op.create_index('idx_time_entries_provider', 'rpm_clinical_time_entries', ['provider_id'])

    # RPM Billing Events
    op.create_table(
        'rpm_billing_events',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('enrollment_id', UUID(as_uuid=True), sa.ForeignKey('rpm_enrollments.id'), nullable=False),
        sa.Column('monitoring_period_id', UUID(as_uuid=True), sa.ForeignKey('rpm_monitoring_periods.id'), nullable=True),
        sa.Column('patient_id', UUID(as_uuid=True), nullable=False),
        sa.Column('cpt_code', sa.String(10), nullable=False),
        sa.Column('service_date', sa.Date, nullable=False),
        sa.Column('units', sa.Integer, default=1),
        sa.Column('billing_provider_id', UUID(as_uuid=True), nullable=False),
        sa.Column('supervising_provider_id', UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('claim_id', UUID(as_uuid=True), nullable=True),
        sa.Column('external_claim_id', sa.String(200), nullable=True),
        sa.Column('billed_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('allowed_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('paid_amount', sa.Numeric(10, 2), nullable=True),
        sa.Column('documentation', JSONB, default={}),
        sa.Column('days_with_data', sa.Integer, nullable=True),
        sa.Column('clinical_minutes', sa.Integer, nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('adjudicated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_rpm_billing_events_tenant', 'rpm_billing_events', ['tenant_id'])
    op.create_index('ix_rpm_billing_events_patient', 'rpm_billing_events', ['patient_id'])
    op.create_index('idx_billing_events_patient_date', 'rpm_billing_events', ['patient_id', 'service_date'])
    op.create_index('idx_billing_events_status', 'rpm_billing_events', ['status'])
    op.create_index('idx_billing_events_claim', 'rpm_billing_events', ['claim_id'])

    # ========================================================================
    # PATIENT ENGAGEMENT TABLES
    # ========================================================================

    # Patient Reminders
    op.create_table(
        'rpm_patient_reminders',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', UUID(as_uuid=True), nullable=False),
        sa.Column('enrollment_id', UUID(as_uuid=True), sa.ForeignKey('rpm_enrollments.id'), nullable=True),
        sa.Column('device_assignment_id', UUID(as_uuid=True), sa.ForeignKey('rpm_device_assignments.id'), nullable=True),
        sa.Column('reminder_type', sa.String(50), nullable=False),
        sa.Column('reading_type', sa.String(50), nullable=True),
        sa.Column('scheduled_time', sa.String(10), nullable=False),
        sa.Column('days_of_week', ARRAY(sa.Integer), default=[0, 1, 2, 3, 4, 5, 6]),
        sa.Column('timezone', sa.String(50), default='UTC'),
        sa.Column('channel', sa.String(30), default='push'),
        sa.Column('message_template', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('last_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reminders_sent', sa.Integer, default=0),
        sa.Column('readings_after_reminder', sa.Integer, default=0),
        sa.Column('response_rate', sa.Float, default=0.0),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_rpm_patient_reminders_tenant', 'rpm_patient_reminders', ['tenant_id'])
    op.create_index('ix_rpm_patient_reminders_patient', 'rpm_patient_reminders', ['patient_id'])
    op.create_index('idx_reminders_patient_active', 'rpm_patient_reminders', ['patient_id', 'is_active'])
    op.create_index('idx_reminders_next_scheduled', 'rpm_patient_reminders', ['next_scheduled_at'])

    # Patient Goals
    op.create_table(
        'rpm_patient_goals',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', UUID(as_uuid=True), nullable=False),
        sa.Column('enrollment_id', UUID(as_uuid=True), sa.ForeignKey('rpm_enrollments.id'), nullable=True),
        sa.Column('reading_type', sa.String(50), nullable=False),
        sa.Column('goal_type', sa.String(50), nullable=False),
        sa.Column('target_value', sa.Float, nullable=True),
        sa.Column('target_low', sa.Float, nullable=True),
        sa.Column('target_high', sa.Float, nullable=True),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=True),
        sa.Column('current_value', sa.Float, nullable=True),
        sa.Column('progress_percent', sa.Float, default=0.0),
        sa.Column('is_achieved', sa.Boolean, default=False),
        sa.Column('achieved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('set_by', UUID(as_uuid=True), nullable=False),
        sa.Column('set_by_type', sa.String(50), nullable=False),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_rpm_patient_goals_tenant', 'rpm_patient_goals', ['tenant_id'])
    op.create_index('ix_rpm_patient_goals_patient', 'rpm_patient_goals', ['patient_id'])
    op.create_index('idx_goals_patient_active', 'rpm_patient_goals', ['patient_id', 'is_active'])
    op.create_index('idx_goals_reading_type', 'rpm_patient_goals', ['reading_type'])

    # Educational Content
    op.create_table(
        'rpm_educational_content',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('content_type', sa.String(50), nullable=False),
        sa.Column('content_url', sa.String(500), nullable=True),
        sa.Column('content_body', sa.Text, nullable=True),
        sa.Column('condition', sa.String(100), nullable=True),
        sa.Column('tags', ARRAY(sa.String), default=[]),
        sa.Column('reading_types', ARRAY(sa.String), default=[]),
        sa.Column('duration_minutes', sa.Integer, nullable=True),
        sa.Column('difficulty_level', sa.String(20), default='beginner'),
        sa.Column('language', sa.String(10), default='en'),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_featured', sa.Boolean, default=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('view_count', sa.Integer, default=0),
        sa.Column('completion_count', sa.Integer, default=0),
        sa.Column('average_rating', sa.Float, nullable=True),
        sa.Column('created_by', UUID(as_uuid=True), nullable=False),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_rpm_educational_content_tenant', 'rpm_educational_content', ['tenant_id'])
    op.create_index('idx_content_condition', 'rpm_educational_content', ['condition'])
    op.create_index('idx_content_active_featured', 'rpm_educational_content', ['is_active', 'is_featured'])

    # Patient Content Engagement
    op.create_table(
        'rpm_patient_content_engagement',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', UUID(as_uuid=True), nullable=False),
        sa.Column('content_id', UUID(as_uuid=True), sa.ForeignKey('rpm_educational_content.id'), nullable=False),
        sa.Column('viewed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('time_spent_seconds', sa.Integer, default=0),
        sa.Column('progress_percent', sa.Float, default=0.0),
        sa.Column('rating', sa.Integer, nullable=True),
        sa.Column('feedback', sa.Text, nullable=True),
        sa.Column('quiz_score', sa.Float, nullable=True),
        sa.Column('quiz_attempts', sa.Integer, default=0),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('patient_id', 'content_id', name='uq_patient_content'),
    )
    op.create_index('ix_rpm_patient_content_engagement_tenant', 'rpm_patient_content_engagement', ['tenant_id'])
    op.create_index('ix_rpm_patient_content_engagement_patient', 'rpm_patient_content_engagement', ['patient_id'])
    op.create_index('idx_engagement_patient', 'rpm_patient_content_engagement', ['patient_id'])

    # ========================================================================
    # ANALYTICS TABLES
    # ========================================================================

    # Patient Trend Analysis
    op.create_table(
        'rpm_patient_trend_analysis',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', UUID(as_uuid=True), nullable=False),
        sa.Column('reading_type', sa.String(50), nullable=False),
        sa.Column('analysis_date', sa.Date, nullable=False),
        sa.Column('period_days', sa.Integer, default=30),
        sa.Column('reading_count', sa.Integer, default=0),
        sa.Column('avg_value', sa.Float, nullable=True),
        sa.Column('min_value', sa.Float, nullable=True),
        sa.Column('max_value', sa.Float, nullable=True),
        sa.Column('std_dev', sa.Float, nullable=True),
        sa.Column('trend_direction', sa.String(20), nullable=True),
        sa.Column('trend_slope', sa.Float, nullable=True),
        sa.Column('trend_significance', sa.Float, nullable=True),
        sa.Column('baseline_value', sa.Float, nullable=True),
        sa.Column('baseline_deviation_percent', sa.Float, nullable=True),
        sa.Column('goal_id', UUID(as_uuid=True), sa.ForeignKey('rpm_patient_goals.id'), nullable=True),
        sa.Column('in_goal_range_percent', sa.Float, nullable=True),
        sa.Column('ai_summary', sa.Text, nullable=True),
        sa.Column('ai_recommendations', JSONB, default=[]),
        sa.Column('anomaly_count', sa.Integer, default=0),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('patient_id', 'reading_type', 'analysis_date', name='uq_trend_analysis'),
    )
    op.create_index('ix_rpm_patient_trend_analysis_tenant', 'rpm_patient_trend_analysis', ['tenant_id'])
    op.create_index('ix_rpm_patient_trend_analysis_patient', 'rpm_patient_trend_analysis', ['patient_id'])
    op.create_index('idx_trend_patient_type', 'rpm_patient_trend_analysis', ['patient_id', 'reading_type'])

    # Population Health Metrics
    op.create_table(
        'rpm_population_health_metrics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('metric_date', sa.Date, nullable=False),
        sa.Column('condition', sa.String(100), nullable=True),
        sa.Column('reading_type', sa.String(50), nullable=True),
        sa.Column('cohort_filter', JSONB, default={}),
        sa.Column('total_patients', sa.Integer, default=0),
        sa.Column('active_patients', sa.Integer, default=0),
        sa.Column('compliant_patients', sa.Integer, default=0),
        sa.Column('at_goal_patients', sa.Integer, default=0),
        sa.Column('avg_compliance_rate', sa.Float, default=0.0),
        sa.Column('avg_readings_per_patient', sa.Float, default=0.0),
        sa.Column('avg_value', sa.Float, nullable=True),
        sa.Column('in_control_percent', sa.Float, nullable=True),
        sa.Column('alert_rate', sa.Float, nullable=True),
        sa.Column('avg_engagement_score', sa.Float, nullable=True),
        sa.Column('education_completion_rate', sa.Float, nullable=True),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_rpm_population_health_metrics_tenant', 'rpm_population_health_metrics', ['tenant_id'])
    op.create_index('idx_population_metrics_date', 'rpm_population_health_metrics', ['tenant_id', 'metric_date'])
    op.create_index('idx_population_metrics_condition', 'rpm_population_health_metrics', ['condition'])


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_table('rpm_population_health_metrics')
    op.drop_table('rpm_patient_trend_analysis')
    op.drop_table('rpm_patient_content_engagement')
    op.drop_table('rpm_educational_content')
    op.drop_table('rpm_patient_goals')
    op.drop_table('rpm_patient_reminders')
    op.drop_table('rpm_billing_events')
    op.drop_table('rpm_clinical_time_entries')
    op.drop_table('rpm_monitoring_periods')
    op.drop_table('rpm_protocol_executions')
    op.drop_table('rpm_protocol_actions')
    op.drop_table('rpm_protocol_triggers')
    op.drop_foreign_key('fk_enrollment_protocol', 'rpm_enrollments')
    op.drop_table('rpm_care_protocols')
    op.drop_table('rpm_alert_notifications')
    op.drop_table('rpm_alerts')
    op.drop_table('rpm_patient_alert_rules')
    op.drop_table('rpm_alert_rules')
    op.drop_table('rpm_data_quality_metrics')
    op.drop_table('rpm_reading_batches')
    op.drop_table('rpm_device_readings')
    op.drop_table('rpm_device_assignments')
    op.drop_table('rpm_enrollments')
    op.drop_table('rpm_devices')

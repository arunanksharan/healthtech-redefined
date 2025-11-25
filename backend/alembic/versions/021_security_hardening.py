"""Security Hardening

Revision ID: 021_security_hardening
Revises: 020_clinical_decision_support
Create Date: 2024-11-25

EPIC-021: Security Hardening
Creates tables for:
- MFA (enrollments, backup codes, policies)
- Session Management (sessions, policies, login attempts)
- RBAC (roles, permissions, user roles, break-the-glass)
- Encryption (keys, field configs, certificates)
- Security Monitoring (events, rules, incidents, audit logs)
- Vulnerability Management (vulnerabilities, scans)
- API Security (policies, request logs)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '021_security_hardening'
down_revision = '020_clinical_decision_support'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # MFA Tables
    # ==========================================================================

    # MFA Enrollments
    op.create_table(
        'security_mfa_enrollments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('method', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), default='disabled', nullable=False),
        sa.Column('is_primary', sa.Boolean, default=False),
        sa.Column('secret_encrypted', sa.LargeBinary),
        sa.Column('phone_number_hash', sa.String(64)),
        sa.Column('email_hash', sa.String(64)),
        sa.Column('webauthn_credential_id', sa.String(512)),
        sa.Column('webauthn_public_key', sa.Text),
        sa.Column('verified_at', sa.DateTime),
        sa.Column('last_used_at', sa.DateTime),
        sa.Column('use_count', sa.Integer, default=0),
        sa.Column('device_name', sa.String(255)),
        sa.Column('enrolled_ip', postgresql.INET),
        sa.Column('enrolled_user_agent', sa.Text),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )
    op.create_index('idx_mfa_user_method', 'security_mfa_enrollments', ['user_id', 'method'])

    # MFA Backup Codes
    op.create_table(
        'security_mfa_backup_codes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('code_hash', sa.String(64), nullable=False),
        sa.Column('is_used', sa.Boolean, default=False),
        sa.Column('used_at', sa.DateTime),
        sa.Column('used_ip', postgresql.INET),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('expires_at', sa.DateTime),
    )
    op.create_index('idx_backup_codes_user', 'security_mfa_backup_codes', ['user_id', 'is_used'])

    # MFA Policies
    op.create_table(
        'security_mfa_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('required_for_all', sa.Boolean, default=False),
        sa.Column('required_roles', postgresql.ARRAY(sa.String)),
        sa.Column('allowed_methods', postgresql.ARRAY(sa.String)),
        sa.Column('grace_period_hours', sa.Integer, default=72),
        sa.Column('remember_device_days', sa.Integer, default=30),
        sa.Column('require_for_phi_access', sa.Boolean, default=True),
        sa.Column('require_for_admin_actions', sa.Boolean, default=True),
        sa.Column('require_on_new_device', sa.Boolean, default=True),
        sa.Column('require_on_new_location', sa.Boolean, default=True),
        sa.Column('require_on_suspicious_activity', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )

    # ==========================================================================
    # Session Management Tables
    # ==========================================================================

    # User Sessions
    op.create_table(
        'security_user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('session_token_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('refresh_token_hash', sa.String(64), unique=True),
        sa.Column('status', sa.String(50), default='active', nullable=False),
        sa.Column('ip_address', postgresql.INET),
        sa.Column('user_agent', sa.Text),
        sa.Column('device_fingerprint', sa.String(64)),
        sa.Column('device_type', sa.String(50)),
        sa.Column('browser', sa.String(100)),
        sa.Column('os', sa.String(100)),
        sa.Column('location_country', sa.String(2)),
        sa.Column('location_city', sa.String(255)),
        sa.Column('location_lat', sa.Float),
        sa.Column('location_lon', sa.Float),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('last_activity_at', sa.DateTime),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('revoked_at', sa.DateTime),
        sa.Column('revoked_reason', sa.String(255)),
        sa.Column('mfa_verified', sa.Boolean, default=False),
        sa.Column('mfa_verified_at', sa.DateTime),
        sa.Column('mfa_method_used', sa.String(50)),
        sa.Column('risk_score', sa.Float, default=0.0),
        sa.Column('is_trusted_device', sa.Boolean, default=False),
    )
    op.create_index('idx_sessions_user_status', 'security_user_sessions', ['user_id', 'status'])
    op.create_index('idx_sessions_expires', 'security_user_sessions', ['expires_at'])
    op.create_index('idx_sessions_activity', 'security_user_sessions', ['last_activity_at'])

    # Session Policies
    op.create_table(
        'security_session_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_default', sa.Boolean, default=False),
        sa.Column('idle_timeout_minutes', sa.Integer, default=15),
        sa.Column('absolute_timeout_minutes', sa.Integer, default=480),
        sa.Column('refresh_token_lifetime_minutes', sa.Integer, default=10080),
        sa.Column('max_concurrent_sessions', sa.Integer, default=5),
        sa.Column('on_exceed_action', sa.String(50), default='revoke_oldest'),
        sa.Column('bind_to_ip', sa.Boolean, default=False),
        sa.Column('bind_to_device', sa.Boolean, default=True),
        sa.Column('require_mfa_on_new_device', sa.Boolean, default=True),
        sa.Column('warn_before_timeout_minutes', sa.Integer, default=2),
        sa.Column('extend_on_activity', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )

    # Login Attempts
    op.create_table(
        'security_login_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), index=True),
        sa.Column('username', sa.String(255), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), index=True),
        sa.Column('success', sa.Boolean, nullable=False),
        sa.Column('failure_reason', sa.String(255)),
        sa.Column('ip_address', postgresql.INET, nullable=False, index=True),
        sa.Column('user_agent', sa.Text),
        sa.Column('device_fingerprint', sa.String(64)),
        sa.Column('location_country', sa.String(2)),
        sa.Column('location_city', sa.String(255)),
        sa.Column('mfa_required', sa.Boolean, default=False),
        sa.Column('mfa_method', sa.String(50)),
        sa.Column('mfa_success', sa.Boolean),
        sa.Column('attempted_at', sa.DateTime, nullable=False, index=True),
        sa.Column('response_time_ms', sa.Integer),
    )
    op.create_index('idx_login_attempts_ip_time', 'security_login_attempts', ['ip_address', 'attempted_at'])
    op.create_index('idx_login_attempts_user_time', 'security_login_attempts', ['username', 'attempted_at'])

    # ==========================================================================
    # RBAC Tables
    # ==========================================================================

    # Roles
    op.create_table(
        'security_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), index=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('role_type', sa.String(50), default='custom', nullable=False),
        sa.Column('is_system_role', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('parent_role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('security_roles.id')),
        sa.Column('hierarchy_level', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_role_tenant_name'),
    )
    op.create_index('idx_roles_tenant_type', 'security_roles', ['tenant_id', 'role_type'])

    # Permissions
    op.create_table(
        'security_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('scope', sa.String(50)),
        sa.Column('conditions', postgresql.JSONB),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.UniqueConstraint('resource_type', 'action', 'scope', name='uq_permission_resource_action'),
    )
    op.create_index('idx_permissions_resource', 'security_permissions', ['resource_type'])

    # Role Permissions
    op.create_table(
        'security_role_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('security_roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('security_permissions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_granted', sa.Boolean, default=True),
        sa.Column('conditions_override', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('granted_by', postgresql.UUID(as_uuid=True)),
        sa.UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'),
    )

    # User Roles
    op.create_table(
        'security_user_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('security_roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('scope_type', sa.String(50)),
        sa.Column('scope_id', postgresql.UUID(as_uuid=True)),
        sa.Column('valid_from', sa.DateTime),
        sa.Column('valid_until', sa.DateTime),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True)),
        sa.UniqueConstraint('user_id', 'role_id', 'scope_type', 'scope_id', name='uq_user_role_scope'),
    )
    op.create_index('idx_user_roles_user', 'security_user_roles', ['user_id', 'is_active'])

    # Break The Glass Access
    op.create_table(
        'security_break_glass_access',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('reason', sa.Text, nullable=False),
        sa.Column('emergency_type', sa.String(100)),
        sa.Column('resources_accessed', postgresql.JSONB),
        sa.Column('access_started_at', sa.DateTime, nullable=False),
        sa.Column('access_ended_at', sa.DateTime),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True)),
        sa.Column('reviewed_at', sa.DateTime),
        sa.Column('review_outcome', sa.String(50)),
        sa.Column('review_notes', sa.Text),
        sa.Column('ip_address', postgresql.INET),
        sa.Column('user_agent', sa.Text),
    )
    op.create_index('idx_break_glass_patient', 'security_break_glass_access', ['patient_id', 'access_started_at'])
    op.create_index('idx_break_glass_user', 'security_break_glass_access', ['user_id', 'access_started_at'])

    # ==========================================================================
    # Encryption Tables
    # ==========================================================================

    # Encryption Keys
    op.create_table(
        'security_encryption_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), index=True),
        sa.Column('key_id', sa.String(255), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('key_type', sa.String(50), nullable=False),
        sa.Column('algorithm', sa.String(50), nullable=False),
        sa.Column('key_size_bits', sa.Integer),
        sa.Column('status', sa.String(50), default='active', nullable=False),
        sa.Column('parent_key_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('security_encryption_keys.id')),
        sa.Column('version', sa.Integer, default=1),
        sa.Column('rotation_schedule_days', sa.Integer),
        sa.Column('last_rotated_at', sa.DateTime),
        sa.Column('next_rotation_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('expires_at', sa.DateTime),
        sa.Column('destroyed_at', sa.DateTime),
        sa.Column('kms_provider', sa.String(50)),
        sa.Column('kms_key_arn', sa.String(512)),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )
    op.create_index('idx_keys_tenant_type', 'security_encryption_keys', ['tenant_id', 'key_type', 'status'])

    # Field Encryption Configs
    op.create_table(
        'security_field_encryption_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), index=True),
        sa.Column('table_name', sa.String(255), nullable=False),
        sa.Column('column_name', sa.String(255), nullable=False),
        sa.Column('encryption_key_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('security_encryption_keys.id')),
        sa.Column('algorithm', sa.String(50), default='aes_256_gcm'),
        sa.Column('is_searchable', sa.Boolean, default=False),
        sa.Column('search_algorithm', sa.String(100)),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
        sa.UniqueConstraint('tenant_id', 'table_name', 'column_name', name='uq_field_encryption'),
    )

    # Certificates
    op.create_table(
        'security_certificates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('domain', sa.String(255), nullable=False),
        sa.Column('common_name', sa.String(255)),
        sa.Column('san_domains', postgresql.ARRAY(sa.String)),
        sa.Column('serial_number', sa.String(255)),
        sa.Column('fingerprint_sha256', sa.String(64)),
        sa.Column('issuer', sa.String(512)),
        sa.Column('issued_at', sa.DateTime),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('auto_renew', sa.Boolean, default=True),
        sa.Column('last_renewed_at', sa.DateTime),
        sa.Column('renewal_attempts', sa.Integer, default=0),
        sa.Column('provider', sa.String(100)),
        sa.Column('provider_certificate_id', sa.String(512)),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    op.create_index('idx_certificates_domain', 'security_certificates', ['domain'])
    op.create_index('idx_certificates_expires', 'security_certificates', ['expires_at'])

    # ==========================================================================
    # Security Monitoring Tables
    # ==========================================================================

    # Security Events
    op.create_table(
        'security_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), index=True),
        sa.Column('event_type', sa.String(100), nullable=False, index=True),
        sa.Column('threat_type', sa.String(50)),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('details', postgresql.JSONB),
        sa.Column('source_ip', postgresql.INET),
        sa.Column('source_user_id', postgresql.UUID(as_uuid=True)),
        sa.Column('source_service', sa.String(255)),
        sa.Column('target_resource_type', sa.String(100)),
        sa.Column('target_resource_id', sa.String(255)),
        sa.Column('target_user_id', postgresql.UUID(as_uuid=True)),
        sa.Column('detected_at', sa.DateTime, nullable=False, index=True),
        sa.Column('detection_rule_id', sa.String(255)),
        sa.Column('confidence_score', sa.Float),
        sa.Column('is_acknowledged', sa.Boolean, default=False),
        sa.Column('acknowledged_by', postgresql.UUID(as_uuid=True)),
        sa.Column('acknowledged_at', sa.DateTime),
        sa.Column('correlation_id', sa.String(255), index=True),
        sa.Column('related_event_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True))),
    )
    op.create_index('idx_security_events_tenant_time', 'security_events', ['tenant_id', 'detected_at'])
    op.create_index('idx_security_events_severity', 'security_events', ['severity', 'detected_at'])

    # Threat Detection Rules
    op.create_table(
        'security_threat_detection_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('threat_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('rule_type', sa.String(50)),
        sa.Column('conditions', postgresql.JSONB, nullable=False),
        sa.Column('threshold_count', sa.Integer),
        sa.Column('threshold_window_minutes', sa.Integer),
        sa.Column('actions', postgresql.JSONB),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_system_rule', sa.Boolean, default=False),
        sa.Column('trigger_count', sa.Integer, default=0),
        sa.Column('last_triggered_at', sa.DateTime),
        sa.Column('false_positive_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )

    # Security Incidents
    op.create_table(
        'security_incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), index=True),
        sa.Column('incident_number', sa.String(50), nullable=False, unique=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), default='new', nullable=False),
        sa.Column('threat_type', sa.String(50)),
        sa.Column('attack_vector', sa.String(255)),
        sa.Column('affected_systems', postgresql.ARRAY(sa.String)),
        sa.Column('data_breach', sa.Boolean, default=False),
        sa.Column('phi_involved', sa.Boolean, default=False),
        sa.Column('affected_user_count', sa.Integer),
        sa.Column('affected_patient_count', sa.Integer),
        sa.Column('detected_at', sa.DateTime, nullable=False),
        sa.Column('contained_at', sa.DateTime),
        sa.Column('eradicated_at', sa.DateTime),
        sa.Column('recovered_at', sa.DateTime),
        sa.Column('closed_at', sa.DateTime),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True)),
        sa.Column('escalated_to', postgresql.UUID(as_uuid=True)),
        sa.Column('related_event_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True))),
        sa.Column('root_cause', sa.Text),
        sa.Column('remediation_steps', postgresql.JSONB),
        sa.Column('lessons_learned', sa.Text),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )
    op.create_index('idx_incidents_status', 'security_incidents', ['status', 'severity'])
    op.create_index('idx_incidents_detected', 'security_incidents', ['detected_at'])

    # Incident Responses
    op.create_table(
        'security_incident_responses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('security_incidents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action_type', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('evidence_collected', postgresql.JSONB),
        sa.Column('attachments', postgresql.ARRAY(sa.String)),
        sa.Column('performed_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('performed_at', sa.DateTime, nullable=False),
    )
    op.create_index('idx_incident_responses_incident', 'security_incident_responses', ['incident_id', 'performed_at'])

    # Security Audit Logs
    op.create_table(
        'security_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), index=True),
        sa.Column('event_category', sa.String(100), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_action', sa.String(100), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True), index=True),
        sa.Column('actor_type', sa.String(50)),
        sa.Column('actor_ip', postgresql.INET),
        sa.Column('target_type', sa.String(100)),
        sa.Column('target_id', sa.String(255)),
        sa.Column('description', sa.Text),
        sa.Column('details', postgresql.JSONB),
        sa.Column('outcome', sa.String(50)),
        sa.Column('failure_reason', sa.String(255)),
        sa.Column('hipaa_relevant', sa.Boolean, default=False),
        sa.Column('phi_accessed', sa.Boolean, default=False),
        sa.Column('occurred_at', sa.DateTime, nullable=False, index=True),
    )
    op.create_index('idx_audit_tenant_time', 'security_audit_logs', ['tenant_id', 'occurred_at'])
    op.create_index('idx_audit_actor_time', 'security_audit_logs', ['actor_id', 'occurred_at'])
    op.create_index('idx_audit_category', 'security_audit_logs', ['event_category', 'occurred_at'])

    # ==========================================================================
    # Vulnerability Management Tables
    # ==========================================================================

    # Vulnerabilities
    op.create_table(
        'security_vulnerabilities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), index=True),
        sa.Column('cve_id', sa.String(50), index=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('cvss_score', sa.Float),
        sa.Column('cvss_vector', sa.String(255)),
        sa.Column('scan_type', sa.String(50), nullable=False),
        sa.Column('scanner', sa.String(100)),
        sa.Column('scan_id', sa.String(255)),
        sa.Column('component_type', sa.String(100)),
        sa.Column('component_name', sa.String(255)),
        sa.Column('component_version', sa.String(100)),
        sa.Column('affected_file', sa.String(512)),
        sa.Column('affected_line', sa.Integer),
        sa.Column('status', sa.String(50), default='open', nullable=False),
        sa.Column('fix_available', sa.Boolean),
        sa.Column('fixed_version', sa.String(100)),
        sa.Column('remediation_guidance', sa.Text),
        sa.Column('sla_due_date', sa.DateTime),
        sa.Column('discovered_at', sa.DateTime, nullable=False),
        sa.Column('remediated_at', sa.DateTime),
        sa.Column('verified_at', sa.DateTime),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True)),
    )
    op.create_index('idx_vulns_status_severity', 'security_vulnerabilities', ['status', 'severity'])
    op.create_index('idx_vulns_sla', 'security_vulnerabilities', ['sla_due_date', 'status'])

    # Security Scans
    op.create_table(
        'security_scans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), index=True),
        sa.Column('scan_type', sa.String(50), nullable=False),
        sa.Column('scanner', sa.String(100), nullable=False),
        sa.Column('target', sa.String(512)),
        sa.Column('target_version', sa.String(100)),
        sa.Column('started_at', sa.DateTime, nullable=False),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('duration_seconds', sa.Integer),
        sa.Column('status', sa.String(50)),
        sa.Column('error_message', sa.Text),
        sa.Column('total_findings', sa.Integer, default=0),
        sa.Column('critical_count', sa.Integer, default=0),
        sa.Column('high_count', sa.Integer, default=0),
        sa.Column('medium_count', sa.Integer, default=0),
        sa.Column('low_count', sa.Integer, default=0),
        sa.Column('scan_config', postgresql.JSONB),
        sa.Column('triggered_by', sa.String(100)),
        sa.Column('triggered_by_user', postgresql.UUID(as_uuid=True)),
    )
    op.create_index('idx_scans_type_time', 'security_scans', ['scan_type', 'started_at'])

    # ==========================================================================
    # API Security Tables
    # ==========================================================================

    # API Security Policies
    op.create_table(
        'security_api_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('rate_limit_requests', sa.Integer),
        sa.Column('rate_limit_window_seconds', sa.Integer),
        sa.Column('burst_limit', sa.Integer),
        sa.Column('allowed_ips', postgresql.ARRAY(postgresql.INET)),
        sa.Column('blocked_ips', postgresql.ARRAY(postgresql.INET)),
        sa.Column('geo_restrictions', postgresql.ARRAY(sa.String)),
        sa.Column('max_request_size_bytes', sa.Integer, default=10485760),
        sa.Column('allowed_content_types', postgresql.ARRAY(sa.String)),
        sa.Column('require_https', sa.Boolean, default=True),
        sa.Column('cors_allowed_origins', postgresql.ARRAY(sa.String)),
        sa.Column('cors_allowed_methods', postgresql.ARRAY(sa.String)),
        sa.Column('cors_allowed_headers', postgresql.ARRAY(sa.String)),
        sa.Column('cors_max_age_seconds', sa.Integer, default=86400),
        sa.Column('security_headers', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime),
    )

    # API Request Logs
    op.create_table(
        'security_api_request_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), index=True),
        sa.Column('request_id', sa.String(64), nullable=False, index=True),
        sa.Column('trace_id', sa.String(64), index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), index=True),
        sa.Column('api_key_id', postgresql.UUID(as_uuid=True)),
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('path', sa.String(512), nullable=False),
        sa.Column('query_params_hash', sa.String(64)),
        sa.Column('ip_address', postgresql.INET, nullable=False),
        sa.Column('user_agent', sa.String(512)),
        sa.Column('status_code', sa.Integer),
        sa.Column('response_time_ms', sa.Integer),
        sa.Column('response_size_bytes', sa.Integer),
        sa.Column('authenticated', sa.Boolean),
        sa.Column('authorized', sa.Boolean),
        sa.Column('mfa_verified', sa.Boolean),
        sa.Column('requested_at', sa.DateTime, nullable=False, index=True),
    )
    op.create_index('idx_api_logs_tenant_time', 'security_api_request_logs', ['tenant_id', 'requested_at'])
    op.create_index('idx_api_logs_user_time', 'security_api_request_logs', ['user_id', 'requested_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('security_api_request_logs')
    op.drop_table('security_api_policies')
    op.drop_table('security_scans')
    op.drop_table('security_vulnerabilities')
    op.drop_table('security_audit_logs')
    op.drop_table('security_incident_responses')
    op.drop_table('security_incidents')
    op.drop_table('security_threat_detection_rules')
    op.drop_table('security_events')
    op.drop_table('security_certificates')
    op.drop_table('security_field_encryption_configs')
    op.drop_table('security_encryption_keys')
    op.drop_table('security_break_glass_access')
    op.drop_table('security_user_roles')
    op.drop_table('security_role_permissions')
    op.drop_table('security_permissions')
    op.drop_table('security_roles')
    op.drop_table('security_login_attempts')
    op.drop_table('security_session_policies')
    op.drop_table('security_user_sessions')
    op.drop_table('security_mfa_policies')
    op.drop_table('security_mfa_backup_codes')
    op.drop_table('security_mfa_enrollments')

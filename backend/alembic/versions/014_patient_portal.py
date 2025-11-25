"""Patient Portal Platform

Revision ID: 014_patient_portal
Revises: 013_omnichannel_communications
Create Date: 2024-11-25

EPIC-014: Patient Portal Platform
- Portal user accounts and authentication
- Session management
- Proxy/family access
- Secure messaging
- User preferences
- Billing and payments
- Prescription refills
- Audit logging
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '014_patient_portal'
down_revision = '013_omnichannel_communications'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUMs
    portal_user_status = postgresql.ENUM(
        'pending_verification', 'active', 'suspended', 'locked', 'deactivated',
        name='portal_user_status', create_type=False
    )
    portal_user_status.create(op.get_bind(), checkfirst=True)

    verification_type = postgresql.ENUM(
        'email', 'sms', 'identity', 'mfa',
        name='verification_type', create_type=False
    )
    verification_type.create(op.get_bind(), checkfirst=True)

    mfa_method = postgresql.ENUM(
        'totp', 'sms', 'email', 'biometric', 'backup_code',
        name='mfa_method', create_type=False
    )
    mfa_method.create(op.get_bind(), checkfirst=True)

    session_status = postgresql.ENUM(
        'active', 'expired', 'revoked', 'logged_out',
        name='session_status', create_type=False
    )
    session_status.create(op.get_bind(), checkfirst=True)

    proxy_relationship = postgresql.ENUM(
        'parent', 'guardian', 'spouse', 'child', 'caregiver',
        'power_of_attorney', 'healthcare_proxy', 'other',
        name='proxy_relationship', create_type=False
    )
    proxy_relationship.create(op.get_bind(), checkfirst=True)

    proxy_access_level = postgresql.ENUM(
        'full', 'read_only', 'appointments_only', 'messages_only',
        'billing_only', 'custom',
        name='proxy_access_level', create_type=False
    )
    proxy_access_level.create(op.get_bind(), checkfirst=True)

    message_folder = postgresql.ENUM(
        'inbox', 'sent', 'drafts', 'archived', 'trash',
        name='message_folder', create_type=False
    )
    message_folder.create(op.get_bind(), checkfirst=True)

    message_priority = postgresql.ENUM(
        'low', 'normal', 'high', 'urgent',
        name='message_priority', create_type=False
    )
    message_priority.create(op.get_bind(), checkfirst=True)

    message_status_portal = postgresql.ENUM(
        'draft', 'sent', 'delivered', 'read', 'replied', 'archived', 'deleted',
        name='message_status_portal', create_type=False
    )
    message_status_portal.create(op.get_bind(), checkfirst=True)

    audit_action = postgresql.ENUM(
        'login', 'logout', 'login_failed', 'password_change', 'password_reset',
        'mfa_enabled', 'mfa_disabled', 'profile_update', 'records_accessed',
        'records_downloaded', 'records_shared', 'message_sent', 'message_read',
        'appointment_booked', 'appointment_cancelled', 'payment_made',
        'prescription_refill', 'proxy_access_granted', 'proxy_access_revoked',
        'account_locked', 'account_unlocked',
        name='audit_action', create_type=False
    )
    audit_action.create(op.get_bind(), checkfirst=True)

    payment_method_type = postgresql.ENUM(
        'credit_card', 'debit_card', 'ach', 'apple_pay', 'google_pay', 'hsa', 'fsa',
        name='payment_method_type', create_type=False
    )
    payment_method_type.create(op.get_bind(), checkfirst=True)

    payment_status = postgresql.ENUM(
        'pending', 'processing', 'completed', 'failed', 'refunded', 'disputed',
        name='payment_status', create_type=False
    )
    payment_status.create(op.get_bind(), checkfirst=True)

    refill_status = postgresql.ENUM(
        'requested', 'pending_approval', 'approved', 'denied', 'processing',
        'ready_for_pickup', 'shipped', 'completed', 'cancelled',
        name='refill_status', create_type=False
    )
    refill_status.create(op.get_bind(), checkfirst=True)

    # ==================== Portal Users ====================
    op.create_table(
        'portal_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),

        # Authentication
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255)),
        sa.Column('password_salt', sa.String(64)),
        sa.Column('password_changed_at', sa.DateTime(timezone=True)),
        sa.Column('password_expires_at', sa.DateTime(timezone=True)),
        sa.Column('require_password_change', sa.Boolean(), default=False),

        # Account Status
        sa.Column('status', sa.Enum('pending_verification', 'active', 'suspended', 'locked', 'deactivated', name='portal_user_status'), default='pending_verification'),
        sa.Column('activation_code', sa.String(100)),
        sa.Column('activation_code_expires_at', sa.DateTime(timezone=True)),

        # Email Verification
        sa.Column('email_verified', sa.Boolean(), default=False),
        sa.Column('email_verified_at', sa.DateTime(timezone=True)),
        sa.Column('email_verification_token', sa.String(255)),
        sa.Column('email_verification_expires_at', sa.DateTime(timezone=True)),

        # Phone Verification
        sa.Column('phone_number', sa.String(20)),
        sa.Column('phone_verified', sa.Boolean(), default=False),
        sa.Column('phone_verified_at', sa.DateTime(timezone=True)),
        sa.Column('phone_verification_code', sa.String(10)),
        sa.Column('phone_verification_expires_at', sa.DateTime(timezone=True)),

        # MFA
        sa.Column('mfa_enabled', sa.Boolean(), default=False),
        sa.Column('mfa_method', sa.Enum('totp', 'sms', 'email', 'biometric', 'backup_code', name='mfa_method')),
        sa.Column('mfa_secret', sa.String(255)),
        sa.Column('mfa_backup_codes', postgresql.JSONB(), default=[]),
        sa.Column('mfa_enabled_at', sa.DateTime(timezone=True)),

        # Security
        sa.Column('login_attempts', sa.Integer(), default=0),
        sa.Column('last_failed_login_at', sa.DateTime(timezone=True)),
        sa.Column('locked_until', sa.DateTime(timezone=True)),
        sa.Column('security_questions', postgresql.JSONB(), default=[]),

        # Session tracking
        sa.Column('last_login_at', sa.DateTime(timezone=True)),
        sa.Column('last_login_ip', postgresql.INET()),
        sa.Column('last_login_user_agent', sa.String(500)),
        sa.Column('last_activity_at', sa.DateTime(timezone=True)),
        sa.Column('total_logins', sa.Integer(), default=0),

        # Profile
        sa.Column('display_name', sa.String(100)),
        sa.Column('avatar_url', sa.String(500)),
        sa.Column('preferred_language', sa.String(10), default='en'),
        sa.Column('timezone', sa.String(50), default='UTC'),

        # Terms
        sa.Column('terms_accepted', sa.Boolean(), default=False),
        sa.Column('terms_accepted_at', sa.DateTime(timezone=True)),
        sa.Column('terms_version', sa.String(20)),
        sa.Column('privacy_accepted', sa.Boolean(), default=False),
        sa.Column('privacy_accepted_at', sa.DateTime(timezone=True)),

        # SSO
        sa.Column('sso_provider', sa.String(50)),
        sa.Column('sso_provider_id', sa.String(255)),
        sa.Column('sso_linked_at', sa.DateTime(timezone=True)),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deactivated_at', sa.DateTime(timezone=True)),
        sa.Column('deactivation_reason', sa.Text()),

        sa.UniqueConstraint('tenant_id', 'email', name='uq_portal_user_email'),
        sa.Index('ix_portal_user_patient', 'tenant_id', 'patient_id'),
        sa.Index('ix_portal_users_tenant', 'tenant_id'),
    )

    # ==================== Portal Sessions ====================
    op.create_table(
        'portal_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_users.id'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),

        # Token
        sa.Column('token_hash', sa.String(255), unique=True, nullable=False),
        sa.Column('refresh_token_hash', sa.String(255), unique=True),

        # Session info
        sa.Column('status', sa.Enum('active', 'expired', 'revoked', 'logged_out', name='session_status'), default='active'),
        sa.Column('device_type', sa.String(50)),
        sa.Column('device_name', sa.String(100)),
        sa.Column('browser', sa.String(100)),
        sa.Column('os', sa.String(100)),
        sa.Column('ip_address', postgresql.INET()),
        sa.Column('user_agent', sa.Text()),
        sa.Column('location', postgresql.JSONB()),

        # Expiration
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('refresh_expires_at', sa.DateTime(timezone=True)),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.func.now()),

        # Termination
        sa.Column('ended_at', sa.DateTime(timezone=True)),
        sa.Column('end_reason', sa.String(50)),

        # Proxy context
        sa.Column('is_proxy_session', sa.Boolean(), default=False),
        sa.Column('proxy_patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id')),

        sa.Index('ix_portal_sessions_user', 'user_id'),
    )

    # ==================== Proxy Access ====================
    op.create_table(
        'proxy_access',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),

        # Parties
        sa.Column('grantor_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),
        sa.Column('grantee_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_users.id'), nullable=False),

        # Relationship
        sa.Column('relationship_type', sa.Enum('parent', 'guardian', 'spouse', 'child', 'caregiver', 'power_of_attorney', 'healthcare_proxy', 'other', name='proxy_relationship'), nullable=False),
        sa.Column('relationship_description', sa.String(255)),

        # Access
        sa.Column('access_level', sa.Enum('full', 'read_only', 'appointments_only', 'messages_only', 'billing_only', 'custom', name='proxy_access_level'), nullable=False),
        sa.Column('custom_permissions', postgresql.JSONB(), default={}),

        # Permission flags
        sa.Column('can_view_records', sa.Boolean(), default=True),
        sa.Column('can_download_records', sa.Boolean(), default=False),
        sa.Column('can_share_records', sa.Boolean(), default=False),
        sa.Column('can_book_appointments', sa.Boolean(), default=True),
        sa.Column('can_cancel_appointments', sa.Boolean(), default=True),
        sa.Column('can_send_messages', sa.Boolean(), default=True),
        sa.Column('can_view_billing', sa.Boolean(), default=True),
        sa.Column('can_make_payments', sa.Boolean(), default=False),
        sa.Column('can_request_refills', sa.Boolean(), default=True),
        sa.Column('can_view_sensitive_records', sa.Boolean(), default=False),

        # Validity
        sa.Column('valid_from', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('valid_until', sa.DateTime(timezone=True)),
        sa.Column('is_permanent', sa.Boolean(), default=False),

        # Status
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True)),
        sa.Column('revoked_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('revocation_reason', sa.Text()),

        # Verification
        sa.Column('verification_required', sa.Boolean(), default=True),
        sa.Column('verified', sa.Boolean(), default=False),
        sa.Column('verified_at', sa.DateTime(timezone=True)),
        sa.Column('verified_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('verification_document_id', postgresql.UUID(as_uuid=True)),

        # Legal
        sa.Column('legal_document_id', postgresql.UUID(as_uuid=True)),
        sa.Column('legal_document_type', sa.String(50)),
        sa.Column('consent_obtained', sa.Boolean(), default=False),
        sa.Column('consent_obtained_at', sa.DateTime(timezone=True)),

        # Minor access
        sa.Column('is_minor_access', sa.Boolean(), default=False),
        sa.Column('minor_date_of_birth', sa.Date()),
        sa.Column('minor_age_out_date', sa.Date()),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),

        sa.UniqueConstraint('grantor_id', 'grantee_id', name='uq_proxy_grantor_grantee'),
        sa.Index('ix_proxy_access_tenant', 'tenant_id'),
        sa.Index('ix_proxy_access_grantee', 'grantee_id'),
    )

    # ==================== Message Threads ====================
    op.create_table(
        'message_threads',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),

        # Thread info
        sa.Column('subject', sa.String(255), nullable=False),
        sa.Column('category', sa.String(50)),
        sa.Column('tags', postgresql.ARRAY(sa.String()), default=[]),

        # Participants
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('provider_name', sa.String(255)),
        sa.Column('department', sa.String(100)),
        sa.Column('care_team_id', postgresql.UUID(as_uuid=True)),

        # Status
        sa.Column('is_open', sa.Boolean(), default=True),
        sa.Column('is_urgent', sa.Boolean(), default=False),
        sa.Column('requires_response', sa.Boolean(), default=True),
        sa.Column('auto_response_sent', sa.Boolean(), default=False),

        # Message counts
        sa.Column('message_count', sa.Integer(), default=0),
        sa.Column('unread_patient_count', sa.Integer(), default=0),
        sa.Column('unread_provider_count', sa.Integer(), default=0),

        # Timestamps
        sa.Column('last_message_at', sa.DateTime(timezone=True)),
        sa.Column('last_patient_message_at', sa.DateTime(timezone=True)),
        sa.Column('last_provider_message_at', sa.DateTime(timezone=True)),
        sa.Column('resolved_at', sa.DateTime(timezone=True)),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),

        # Related resources
        sa.Column('related_appointment_id', postgresql.UUID(as_uuid=True)),
        sa.Column('related_encounter_id', postgresql.UUID(as_uuid=True)),

        # SLA
        sa.Column('response_due_at', sa.DateTime(timezone=True)),
        sa.Column('response_sla_met', sa.Boolean()),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('archived_at', sa.DateTime(timezone=True)),

        sa.Index('ix_message_threads_tenant', 'tenant_id'),
        sa.Index('ix_message_threads_patient', 'patient_id'),
    )

    # ==================== Secure Messages ====================
    op.create_table(
        'secure_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('thread_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('message_threads.id'), nullable=False),

        # Parties
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_users.id')),
        sa.Column('sender_type', sa.String(20), nullable=False),
        sa.Column('sender_name', sa.String(255)),
        sa.Column('recipient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_users.id')),
        sa.Column('recipient_type', sa.String(20)),
        sa.Column('recipient_name', sa.String(255)),

        # Content
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_html', sa.Text()),
        sa.Column('is_encrypted', sa.Boolean(), default=True),
        sa.Column('encryption_key_id', sa.String(100)),

        # Attachments
        sa.Column('has_attachments', sa.Boolean(), default=False),
        sa.Column('attachment_count', sa.Integer(), default=0),

        # Status
        sa.Column('status', sa.Enum('draft', 'sent', 'delivered', 'read', 'replied', 'archived', 'deleted', name='message_status_portal'), default='sent'),
        sa.Column('priority', sa.Enum('low', 'normal', 'high', 'urgent', name='message_priority'), default='normal'),
        sa.Column('folder', sa.Enum('inbox', 'sent', 'drafts', 'archived', 'trash', name='message_folder'), default='inbox'),

        # Delivery
        sa.Column('sent_at', sa.DateTime(timezone=True)),
        sa.Column('delivered_at', sa.DateTime(timezone=True)),
        sa.Column('read_at', sa.DateTime(timezone=True)),
        sa.Column('replied_at', sa.DateTime(timezone=True)),

        # Reply context
        sa.Column('reply_to_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('secure_messages.id')),
        sa.Column('is_auto_response', sa.Boolean(), default=False),
        sa.Column('auto_response_type', sa.String(50)),

        # Forwarding
        sa.Column('forwarded_from_id', postgresql.UUID(as_uuid=True)),
        sa.Column('forwarded_to', postgresql.ARRAY(postgresql.UUID(as_uuid=True))),
        sa.Column('forwarded_at', sa.DateTime(timezone=True)),

        # Proxy context
        sa.Column('sent_via_proxy', sa.Boolean(), default=False),
        sa.Column('proxy_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_users.id')),

        # Metadata
        sa.Column('metadata', postgresql.JSONB(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True)),

        sa.Index('ix_secure_messages_thread', 'thread_id'),
        sa.Index('ix_secure_messages_sender', 'sender_id'),
    )

    # ==================== Portal Message Attachments ====================
    op.create_table(
        'portal_message_attachments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('secure_messages.id'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),

        # File info
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_type', sa.String(50)),
        sa.Column('mime_type', sa.String(100)),
        sa.Column('file_size', sa.BigInteger()),

        # Storage
        sa.Column('storage_provider', sa.String(20), default='s3'),
        sa.Column('storage_key', sa.String(500)),
        sa.Column('storage_url', sa.String(1000)),

        # Security
        sa.Column('is_encrypted', sa.Boolean(), default=True),
        sa.Column('encryption_key_id', sa.String(100)),
        sa.Column('checksum', sa.String(64)),

        # Scanning
        sa.Column('virus_scanned', sa.Boolean(), default=False),
        sa.Column('virus_scan_result', sa.String(50)),
        sa.Column('scanned_at', sa.DateTime(timezone=True)),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),

        sa.Index('ix_portal_message_attachments_message', 'message_id'),
    )

    # ==================== Portal Preferences ====================
    op.create_table(
        'portal_preferences',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_users.id'), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),

        # Display
        sa.Column('language', sa.String(10), default='en'),
        sa.Column('timezone', sa.String(50), default='UTC'),
        sa.Column('date_format', sa.String(20), default='MM/DD/YYYY'),
        sa.Column('time_format', sa.String(10), default='12h'),
        sa.Column('theme', sa.String(20), default='light'),

        # Accessibility
        sa.Column('accessibility_settings', postgresql.JSONB(), default={}),

        # Notifications
        sa.Column('notification_settings', postgresql.JSONB(), default={}),

        # Dashboard
        sa.Column('dashboard_layout', postgresql.JSONB(), default={}),

        # Privacy
        sa.Column('privacy_settings', postgresql.JSONB(), default={}),

        # Communication
        sa.Column('communication_preferences', postgresql.JSONB(), default={}),

        # Quick actions
        sa.Column('favorite_actions', postgresql.ARRAY(sa.String()), default=[]),

        # Onboarding
        sa.Column('onboarding_completed', sa.Boolean(), default=False),
        sa.Column('onboarding_completed_at', sa.DateTime(timezone=True)),
        sa.Column('tour_completed', sa.Boolean(), default=False),
        sa.Column('feature_tips_shown', postgresql.JSONB(), default={}),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # ==================== Saved Payment Methods ====================
    op.create_table(
        'saved_payment_methods',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_users.id'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),

        # Payment method
        sa.Column('payment_type', sa.Enum('credit_card', 'debit_card', 'ach', 'apple_pay', 'google_pay', 'hsa', 'fsa', name='payment_method_type'), nullable=False),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('nickname', sa.String(50)),

        # Card details
        sa.Column('card_brand', sa.String(20)),
        sa.Column('card_last_four', sa.String(4)),
        sa.Column('card_exp_month', sa.Integer()),
        sa.Column('card_exp_year', sa.Integer()),
        sa.Column('card_holder_name', sa.String(255)),

        # Bank details
        sa.Column('bank_name', sa.String(100)),
        sa.Column('account_type', sa.String(20)),
        sa.Column('account_last_four', sa.String(4)),
        sa.Column('routing_number_last_four', sa.String(4)),

        # Payment processor
        sa.Column('processor', sa.String(50), default='stripe'),
        sa.Column('processor_token', sa.String(255)),
        sa.Column('processor_customer_id', sa.String(255)),

        # Billing address
        sa.Column('billing_address', postgresql.JSONB()),

        # Status
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('verified_at', sa.DateTime(timezone=True)),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),

        sa.Index('ix_saved_payment_methods_user', 'user_id'),
    )

    # ==================== Portal Payments ====================
    op.create_table(
        'portal_payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_users.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),

        # Payment details
        sa.Column('payment_method_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('saved_payment_methods.id')),
        sa.Column('payment_type', sa.Enum('credit_card', 'debit_card', 'ach', 'apple_pay', 'google_pay', 'hsa', 'fsa', name='payment_method_type'), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('currency', sa.String(3), default='USD'),

        # Allocation
        sa.Column('statement_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True))),
        sa.Column('encounter_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True))),
        sa.Column('payment_plan_id', postgresql.UUID(as_uuid=True)),

        # Processing
        sa.Column('status', sa.Enum('pending', 'processing', 'completed', 'failed', 'refunded', 'disputed', name='payment_status'), default='pending'),
        sa.Column('processor', sa.String(50)),
        sa.Column('processor_transaction_id', sa.String(255)),
        sa.Column('processor_response', postgresql.JSONB()),

        # Confirmation
        sa.Column('confirmation_number', sa.String(50)),
        sa.Column('receipt_url', sa.String(500)),
        sa.Column('receipt_sent', sa.Boolean(), default=False),
        sa.Column('receipt_sent_at', sa.DateTime(timezone=True)),

        # Timestamps
        sa.Column('initiated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('failed_at', sa.DateTime(timezone=True)),

        # Error handling
        sa.Column('error_code', sa.String(50)),
        sa.Column('error_message', sa.Text()),
        sa.Column('retry_count', sa.Integer(), default=0),

        # Refund
        sa.Column('refunded', sa.Boolean(), default=False),
        sa.Column('refund_amount', sa.Numeric(10, 2)),
        sa.Column('refunded_at', sa.DateTime(timezone=True)),
        sa.Column('refund_reason', sa.Text()),

        # Metadata
        sa.Column('metadata', postgresql.JSONB(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),

        sa.Index('ix_portal_payments_tenant', 'tenant_id'),
        sa.Index('ix_portal_payments_user', 'user_id'),
    )

    # ==================== Payment Plans ====================
    op.create_table(
        'payment_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_users.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),

        # Plan details
        sa.Column('name', sa.String(100)),
        sa.Column('total_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('remaining_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('monthly_payment', sa.Numeric(10, 2), nullable=False),
        sa.Column('number_of_payments', sa.Integer(), nullable=False),
        sa.Column('payments_made', sa.Integer(), default=0),

        # Schedule
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('next_payment_date', sa.Date()),
        sa.Column('payment_day_of_month', sa.Integer()),

        # Auto-pay
        sa.Column('auto_pay_enabled', sa.Boolean(), default=False),
        sa.Column('payment_method_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('saved_payment_methods.id')),

        # Interest
        sa.Column('interest_rate', sa.Numeric(5, 2), default=0),
        sa.Column('total_interest', sa.Numeric(10, 2), default=0),

        # Status
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('cancelled_at', sa.DateTime(timezone=True)),
        sa.Column('cancellation_reason', sa.Text()),

        # Delinquency
        sa.Column('missed_payments', sa.Integer(), default=0),
        sa.Column('is_delinquent', sa.Boolean(), default=False),
        sa.Column('delinquent_since', sa.Date()),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),

        sa.Index('ix_payment_plans_tenant', 'tenant_id'),
        sa.Index('ix_payment_plans_user', 'user_id'),
    )

    # ==================== Refill Requests ====================
    op.create_table(
        'refill_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_users.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),

        # Prescription reference
        sa.Column('prescription_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('medication_name', sa.String(255), nullable=False),
        sa.Column('medication_dosage', sa.String(100)),
        sa.Column('medication_instructions', sa.Text()),

        # Request details
        sa.Column('quantity_requested', sa.Integer()),
        sa.Column('days_supply_requested', sa.Integer()),
        sa.Column('notes', sa.Text()),
        sa.Column('urgent', sa.Boolean(), default=False),

        # Pharmacy
        sa.Column('pharmacy_id', postgresql.UUID(as_uuid=True)),
        sa.Column('pharmacy_name', sa.String(255)),
        sa.Column('pharmacy_phone', sa.String(20)),
        sa.Column('pharmacy_address', postgresql.JSONB()),
        sa.Column('delivery_requested', sa.Boolean(), default=False),
        sa.Column('delivery_address', postgresql.JSONB()),

        # Status
        sa.Column('status', sa.Enum('requested', 'pending_approval', 'approved', 'denied', 'processing', 'ready_for_pickup', 'shipped', 'completed', 'cancelled', name='refill_status'), default='requested'),
        sa.Column('status_updated_at', sa.DateTime(timezone=True)),
        sa.Column('status_updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),

        # Approval
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('approved_at', sa.DateTime(timezone=True)),
        sa.Column('denial_reason', sa.Text()),
        sa.Column('requires_appointment', sa.Boolean(), default=False),

        # Prior authorization
        sa.Column('prior_auth_required', sa.Boolean(), default=False),
        sa.Column('prior_auth_status', sa.String(50)),
        sa.Column('prior_auth_number', sa.String(100)),

        # Processing
        sa.Column('processed_at', sa.DateTime(timezone=True)),
        sa.Column('ready_at', sa.DateTime(timezone=True)),
        sa.Column('picked_up_at', sa.DateTime(timezone=True)),
        sa.Column('shipped_at', sa.DateTime(timezone=True)),
        sa.Column('tracking_number', sa.String(100)),

        # Cost
        sa.Column('estimated_cost', sa.Numeric(10, 2)),
        sa.Column('copay_amount', sa.Numeric(10, 2)),
        sa.Column('insurance_coverage', sa.Numeric(10, 2)),

        # Proxy context
        sa.Column('requested_via_proxy', sa.Boolean(), default=False),
        sa.Column('proxy_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_users.id')),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),

        sa.Index('ix_refill_requests_tenant', 'tenant_id'),
        sa.Index('ix_refill_requests_user', 'user_id'),
        sa.Index('ix_refill_requests_patient', 'patient_id'),
    )

    # ==================== Portal Notifications ====================
    op.create_table(
        'portal_notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_users.id'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),

        # Notification
        sa.Column('notification_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('icon', sa.String(50)),
        sa.Column('action_url', sa.String(500)),
        sa.Column('action_text', sa.String(100)),

        # Priority
        sa.Column('priority', sa.String(20), default='normal'),
        sa.Column('is_urgent', sa.Boolean(), default=False),

        # Status
        sa.Column('is_read', sa.Boolean(), default=False),
        sa.Column('read_at', sa.DateTime(timezone=True)),
        sa.Column('is_dismissed', sa.Boolean(), default=False),
        sa.Column('dismissed_at', sa.DateTime(timezone=True)),

        # Delivery
        sa.Column('channels_sent', postgresql.ARRAY(sa.String()), default=[]),
        sa.Column('email_sent', sa.Boolean(), default=False),
        sa.Column('email_sent_at', sa.DateTime(timezone=True)),
        sa.Column('sms_sent', sa.Boolean(), default=False),
        sa.Column('sms_sent_at', sa.DateTime(timezone=True)),
        sa.Column('push_sent', sa.Boolean(), default=False),
        sa.Column('push_sent_at', sa.DateTime(timezone=True)),

        # Reference
        sa.Column('reference_type', sa.String(50)),
        sa.Column('reference_id', postgresql.UUID(as_uuid=True)),

        # Expiration
        sa.Column('expires_at', sa.DateTime(timezone=True)),

        # Metadata
        sa.Column('metadata', postgresql.JSONB(), default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),

        sa.Index('ix_portal_notifications_user', 'user_id'),
    )

    # ==================== Record Access Logs ====================
    op.create_table(
        'record_access_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_users.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),

        # Record info
        sa.Column('record_type', sa.String(50), nullable=False),
        sa.Column('record_id', postgresql.UUID(as_uuid=True)),
        sa.Column('record_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True))),
        sa.Column('record_date_from', sa.Date()),
        sa.Column('record_date_to', sa.Date()),

        # Access type
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('access_method', sa.String(50)),

        # Download/Share details
        sa.Column('download_format', sa.String(20)),
        sa.Column('share_recipient', sa.String(255)),
        sa.Column('share_method', sa.String(50)),
        sa.Column('share_expiry', sa.DateTime(timezone=True)),
        sa.Column('share_access_count', sa.Integer(), default=0),

        # Proxy context
        sa.Column('accessed_via_proxy', sa.Boolean(), default=False),
        sa.Column('proxy_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_users.id')),

        # Context
        sa.Column('ip_address', postgresql.INET()),
        sa.Column('user_agent', sa.String(500)),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_sessions.id')),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),

        sa.Index('ix_record_access_logs_tenant', 'tenant_id'),
        sa.Index('ix_record_access_logs_user', 'user_id'),
        sa.Index('ix_record_access_logs_patient', 'patient_id'),
    )

    # ==================== Record Share Links ====================
    op.create_table(
        'record_share_links',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_users.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),

        # Link
        sa.Column('token', sa.String(255), unique=True, nullable=False),
        sa.Column('share_url', sa.String(500)),

        # Content
        sa.Column('record_type', sa.String(50)),
        sa.Column('record_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True))),
        sa.Column('include_attachments', sa.Boolean(), default=False),

        # Recipient
        sa.Column('recipient_name', sa.String(255)),
        sa.Column('recipient_email', sa.String(255)),
        sa.Column('recipient_organization', sa.String(255)),
        sa.Column('purpose', sa.String(255)),

        # Security
        sa.Column('password_protected', sa.Boolean(), default=False),
        sa.Column('password_hash', sa.String(255)),
        sa.Column('max_access_count', sa.Integer()),
        sa.Column('access_count', sa.Integer(), default=0),

        # Validity
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True)),

        # Notification
        sa.Column('notification_sent', sa.Boolean(), default=False),
        sa.Column('notification_sent_at', sa.DateTime(timezone=True)),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True)),

        sa.Index('ix_record_share_links_tenant', 'tenant_id'),
        sa.Index('ix_record_share_links_token', 'token'),
    )

    # ==================== Portal Audit Log ====================
    op.create_table(
        'portal_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_users.id')),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id')),

        # Action
        sa.Column('action', sa.Enum(
            'login', 'logout', 'login_failed', 'password_change', 'password_reset',
            'mfa_enabled', 'mfa_disabled', 'profile_update', 'records_accessed',
            'records_downloaded', 'records_shared', 'message_sent', 'message_read',
            'appointment_booked', 'appointment_cancelled', 'payment_made',
            'prescription_refill', 'proxy_access_granted', 'proxy_access_revoked',
            'account_locked', 'account_unlocked', name='audit_action'), nullable=False),
        sa.Column('action_category', sa.String(50)),
        sa.Column('action_description', sa.Text()),

        # Resource
        sa.Column('resource_type', sa.String(50)),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True)),
        sa.Column('resource_name', sa.String(255)),

        # Details
        sa.Column('details', postgresql.JSONB(), default={}),
        sa.Column('changes', postgresql.JSONB()),
        sa.Column('request_body', postgresql.JSONB()),

        # Context
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_sessions.id')),
        sa.Column('ip_address', postgresql.INET()),
        sa.Column('user_agent', sa.String(500)),
        sa.Column('device_type', sa.String(50)),
        sa.Column('location', postgresql.JSONB()),

        # Proxy context
        sa.Column('is_proxy_action', sa.Boolean(), default=False),
        sa.Column('proxy_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_users.id')),
        sa.Column('on_behalf_of_patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id')),

        # PHI
        sa.Column('contains_phi', sa.Boolean(), default=False),
        sa.Column('phi_fields_accessed', postgresql.ARRAY(sa.String())),

        # Result
        sa.Column('success', sa.Boolean(), default=True),
        sa.Column('error_code', sa.String(50)),
        sa.Column('error_message', sa.Text()),

        # Request info
        sa.Column('request_id', sa.String(100)),
        sa.Column('request_method', sa.String(10)),
        sa.Column('request_path', sa.String(500)),
        sa.Column('response_status', sa.Integer()),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),

        sa.Index('ix_portal_audit_log_tenant', 'tenant_id'),
        sa.Index('ix_portal_audit_log_user', 'user_id'),
        sa.Index('ix_portal_audit_log_created', 'created_at'),
    )

    # ==================== Identity Verifications ====================
    op.create_table(
        'identity_verifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portal_users.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),

        # Verification method
        sa.Column('verification_type', sa.Enum('email', 'sms', 'identity', 'mfa', name='verification_type'), nullable=False),
        sa.Column('verification_method', sa.String(50)),

        # Identity matching
        sa.Column('match_fields', postgresql.JSONB()),
        sa.Column('match_score', sa.Float()),
        sa.Column('match_threshold', sa.Float(), default=0.8),

        # Document verification
        sa.Column('document_type', sa.String(50)),
        sa.Column('document_number_last_four', sa.String(4)),
        sa.Column('document_expiry', sa.Date()),
        sa.Column('document_verified', sa.Boolean(), default=False),

        # Third-party verification
        sa.Column('provider', sa.String(50)),
        sa.Column('provider_reference_id', sa.String(255)),
        sa.Column('provider_response', postgresql.JSONB()),

        # Status
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('verified', sa.Boolean(), default=False),
        sa.Column('verified_at', sa.DateTime(timezone=True)),
        sa.Column('failed_reason', sa.Text()),
        sa.Column('attempts', sa.Integer(), default=1),

        # Metadata
        sa.Column('ip_address', postgresql.INET()),
        sa.Column('user_agent', sa.String(500)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True)),

        sa.Index('ix_identity_verifications_tenant', 'tenant_id'),
        sa.Index('ix_identity_verifications_user', 'user_id'),
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('identity_verifications')
    op.drop_table('portal_audit_log')
    op.drop_table('record_share_links')
    op.drop_table('record_access_logs')
    op.drop_table('portal_notifications')
    op.drop_table('refill_requests')
    op.drop_table('payment_plans')
    op.drop_table('portal_payments')
    op.drop_table('saved_payment_methods')
    op.drop_table('portal_preferences')
    op.drop_table('portal_message_attachments')
    op.drop_table('secure_messages')
    op.drop_table('message_threads')
    op.drop_table('proxy_access')
    op.drop_table('portal_sessions')
    op.drop_table('portal_users')

    # Drop ENUMs
    op.execute('DROP TYPE IF EXISTS refill_status')
    op.execute('DROP TYPE IF EXISTS payment_status')
    op.execute('DROP TYPE IF EXISTS payment_method_type')
    op.execute('DROP TYPE IF EXISTS audit_action')
    op.execute('DROP TYPE IF EXISTS message_status_portal')
    op.execute('DROP TYPE IF EXISTS message_priority')
    op.execute('DROP TYPE IF EXISTS message_folder')
    op.execute('DROP TYPE IF EXISTS proxy_access_level')
    op.execute('DROP TYPE IF EXISTS proxy_relationship')
    op.execute('DROP TYPE IF EXISTS session_status')
    op.execute('DROP TYPE IF EXISTS mfa_method')
    op.execute('DROP TYPE IF EXISTS verification_type')
    op.execute('DROP TYPE IF EXISTS portal_user_status')

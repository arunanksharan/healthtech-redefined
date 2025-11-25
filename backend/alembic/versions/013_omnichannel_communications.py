"""Omnichannel Communications Platform Tables

Revision ID: 013_omnichannel_communications
Revises: 012_intelligent_automation
Create Date: 2024-11-25

EPIC-013: Omnichannel Communications Platform

Tables:
- Channel Configuration:
  - omnichannel_providers: Provider configurations (Twilio, WhatsApp, SendGrid, etc.)
  - omnichannel_templates: Message templates for all channels
  - template_approvals: Template approval workflow tracking

- Conversations & Messages:
  - omnichannel_conversations: Unified conversation threads
  - omnichannel_messages: Messages across all channels
  - message_attachments: Media and file attachments
  - message_delivery_status: Delivery tracking and receipts

- Preferences & Consent:
  - communication_preferences: Patient channel preferences
  - consent_records: HIPAA-compliant consent tracking
  - opt_out_records: Opt-out management

- Campaign Management:
  - campaigns: Multi-channel campaign definitions
  - campaign_segments: Audience segmentation
  - campaign_schedules: Scheduling configurations
  - campaign_executions: Execution tracking
  - ab_test_variants: A/B testing configurations

- Unified Inbox:
  - inbox_assignments: Agent conversation assignments
  - canned_responses: Pre-defined response templates
  - conversation_tags: Categorization and labeling
  - sla_configurations: SLA definitions
  - sla_tracking: SLA compliance tracking

- Analytics:
  - channel_analytics_daily: Daily channel metrics
  - campaign_analytics: Campaign performance metrics
  - engagement_scores: Patient engagement scoring
  - delivery_analytics: Delivery success tracking

- Audit & Compliance:
  - communication_audit_log: HIPAA audit trail
  - encryption_keys: Key management for message encryption
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '013_omnichannel_communications'
down_revision = '012_intelligent_automation'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==================== Enums ====================

    # Channel Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE omni_channel_type AS ENUM (
                'whatsapp', 'sms', 'email', 'voice', 'in_app', 'push_notification', 'webchat'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Message Direction
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE message_direction AS ENUM (
                'inbound', 'outbound'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Delivery Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE delivery_status AS ENUM (
                'pending', 'queued', 'sent', 'delivered', 'read', 'failed', 'bounced', 'blocked', 'expired'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Conversation Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE conversation_status AS ENUM (
                'new', 'open', 'pending', 'resolved', 'closed', 'spam'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Priority Level
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE conversation_priority AS ENUM (
                'low', 'normal', 'high', 'urgent'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Template Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE template_status AS ENUM (
                'draft', 'pending_approval', 'approved', 'rejected', 'deprecated'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Template Category (WhatsApp)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE template_category AS ENUM (
                'authentication', 'marketing', 'utility', 'appointment_update', 'alert_update',
                'payment_update', 'shipping_update', 'ticket_update', 'account_update'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Provider Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE provider_type AS ENUM (
                'twilio_sms', 'twilio_voice', 'twilio_whatsapp',
                'aws_sns', 'aws_ses', 'aws_connect',
                'sendgrid', 'messagebird', 'vonage',
                'meta_whatsapp', 'firebase_push'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Campaign Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE campaign_status AS ENUM (
                'draft', 'scheduled', 'running', 'paused', 'completed', 'cancelled', 'failed'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Campaign Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE campaign_type AS ENUM (
                'one_time', 'recurring', 'triggered', 'drip', 'ab_test'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Consent Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE consent_type AS ENUM (
                'marketing', 'transactional', 'appointment_reminders', 'health_tips',
                'surveys', 'emergency', 'all_communications'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Consent Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE consent_status AS ENUM (
                'granted', 'denied', 'withdrawn', 'expired', 'pending'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ==================== Provider Configuration Tables ====================

    # Omnichannel Providers
    op.create_table(
        'omnichannel_providers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('provider_type', postgresql.ENUM('twilio_sms', 'twilio_voice', 'twilio_whatsapp',
                                                    'aws_sns', 'aws_ses', 'aws_connect', 'sendgrid',
                                                    'messagebird', 'vonage', 'meta_whatsapp', 'firebase_push',
                                                    name='provider_type', create_type=False), nullable=False),
        sa.Column('channel', postgresql.ENUM('whatsapp', 'sms', 'email', 'voice', 'in_app', 'push_notification', 'webchat',
                                             name='omni_channel_type', create_type=False), nullable=False),
        sa.Column('is_primary', sa.Boolean, default=False),
        sa.Column('is_fallback', sa.Boolean, default=False),
        sa.Column('priority', sa.Integer, default=0),

        # Encrypted credentials (JSONB with encrypted values)
        sa.Column('credentials', postgresql.JSONB, nullable=False),
        sa.Column('credentials_encrypted', sa.Boolean, default=True),

        # Configuration
        sa.Column('config', postgresql.JSONB, default={}),
        sa.Column('rate_limit_per_second', sa.Integer, default=10),
        sa.Column('rate_limit_per_day', sa.Integer),
        sa.Column('daily_usage_count', sa.Integer, default=0),
        sa.Column('daily_usage_reset_at', sa.DateTime(timezone=True)),

        # Sender identities
        sa.Column('from_phone_number', sa.String(20)),
        sa.Column('from_email', sa.String(255)),
        sa.Column('from_name', sa.String(100)),
        sa.Column('reply_to_email', sa.String(255)),

        # WhatsApp specific
        sa.Column('whatsapp_business_account_id', sa.String(100)),
        sa.Column('whatsapp_phone_number_id', sa.String(100)),
        sa.Column('whatsapp_verified', sa.Boolean, default=False),

        # Status and monitoring
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('last_health_check', sa.DateTime(timezone=True)),
        sa.Column('health_status', sa.String(20), default='healthy'),
        sa.Column('failure_count', sa.Integer, default=0),
        sa.Column('last_failure_at', sa.DateTime(timezone=True)),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
    )
    op.create_index('ix_omnichannel_providers_tenant_channel', 'omnichannel_providers', ['tenant_id', 'channel'])
    op.create_index('ix_omnichannel_providers_active', 'omnichannel_providers', ['tenant_id', 'is_active', 'channel'])

    # ==================== Message Templates ====================

    # Omnichannel Templates
    op.create_table(
        'omnichannel_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),  # Internal template code
        sa.Column('description', sa.Text),

        # Channel configuration
        sa.Column('channel', postgresql.ENUM('whatsapp', 'sms', 'email', 'voice', 'in_app', 'push_notification', 'webchat',
                                             name='omni_channel_type', create_type=False), nullable=False),
        sa.Column('category', postgresql.ENUM('authentication', 'marketing', 'utility', 'appointment_update',
                                               'alert_update', 'payment_update', 'shipping_update',
                                               'ticket_update', 'account_update',
                                               name='template_category', create_type=False)),

        # Template content
        sa.Column('subject', sa.String(255)),  # For email
        sa.Column('body', sa.Text, nullable=False),
        sa.Column('body_html', sa.Text),  # For email
        sa.Column('header_text', sa.String(255)),  # WhatsApp header
        sa.Column('footer_text', sa.String(255)),  # WhatsApp footer

        # Dynamic content
        sa.Column('variables', postgresql.JSONB, default=[]),  # List of variable names
        sa.Column('default_values', postgresql.JSONB, default={}),

        # WhatsApp specific
        sa.Column('whatsapp_template_id', sa.String(100)),  # External template ID
        sa.Column('whatsapp_template_name', sa.String(100)),
        sa.Column('buttons', postgresql.JSONB, default=[]),  # Button configurations
        sa.Column('quick_replies', postgresql.JSONB, default=[]),

        # Media attachments
        sa.Column('media_type', sa.String(20)),  # image, document, video, audio
        sa.Column('media_url', sa.String(500)),
        sa.Column('media_filename', sa.String(255)),

        # Status and approval
        sa.Column('status', postgresql.ENUM('draft', 'pending_approval', 'approved', 'rejected', 'deprecated',
                                            name='template_status', create_type=False), default='draft'),
        sa.Column('approved_at', sa.DateTime(timezone=True)),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('rejection_reason', sa.Text),

        # Versioning
        sa.Column('version', sa.Integer, default=1),
        sa.Column('previous_version_id', postgresql.UUID(as_uuid=True)),

        # Localization
        sa.Column('language', sa.String(10), default='en'),
        sa.Column('translations', postgresql.JSONB, default={}),  # {lang_code: {body: ..., subject: ...}}

        # Usage stats
        sa.Column('usage_count', sa.Integer, default=0),
        sa.Column('last_used_at', sa.DateTime(timezone=True)),

        # Metadata
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
    )
    op.create_index('ix_omnichannel_templates_tenant_code', 'omnichannel_templates', ['tenant_id', 'code'], unique=True)
    op.create_index('ix_omnichannel_templates_channel', 'omnichannel_templates', ['tenant_id', 'channel', 'status'])

    # Template Approvals
    op.create_table(
        'template_approvals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('omnichannel_templates.id'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('submitted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('reviewed_at', sa.DateTime(timezone=True)),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('comments', sa.Text),
        sa.Column('external_approval_id', sa.String(100)),  # WhatsApp/provider approval ID
        sa.Column('external_status', sa.String(50)),
    )
    op.create_index('ix_template_approvals_status', 'template_approvals', ['tenant_id', 'status'])

    # ==================== Conversations & Messages ====================

    # Omnichannel Conversations
    op.create_table(
        'omnichannel_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id')),
        sa.Column('external_contact_id', sa.String(255)),  # Phone number, email, etc.
        sa.Column('external_contact_name', sa.String(255)),

        # Conversation identification
        sa.Column('conversation_key', sa.String(255), nullable=False),  # Unique key for deduplication
        sa.Column('session_id', sa.String(100)),  # WhatsApp session ID

        # Channel information
        sa.Column('primary_channel', postgresql.ENUM('whatsapp', 'sms', 'email', 'voice', 'in_app', 'push_notification', 'webchat',
                                                     name='omni_channel_type', create_type=False), nullable=False),
        sa.Column('channels_used', postgresql.ARRAY(sa.String), default=[]),  # All channels used in conversation

        # Status and priority
        sa.Column('status', postgresql.ENUM('new', 'open', 'pending', 'resolved', 'closed', 'spam',
                                            name='conversation_status', create_type=False), default='new'),
        sa.Column('priority', postgresql.ENUM('low', 'normal', 'high', 'urgent',
                                              name='conversation_priority', create_type=False), default='normal'),
        sa.Column('sentiment', sa.String(20)),  # positive, negative, neutral
        sa.Column('sentiment_score', sa.Float),

        # Assignment
        sa.Column('assigned_agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('assigned_team_id', postgresql.UUID(as_uuid=True)),
        sa.Column('assigned_at', sa.DateTime(timezone=True)),
        sa.Column('last_agent_reply_at', sa.DateTime(timezone=True)),

        # Message counts
        sa.Column('message_count', sa.Integer, default=0),
        sa.Column('inbound_count', sa.Integer, default=0),
        sa.Column('outbound_count', sa.Integer, default=0),
        sa.Column('unread_count', sa.Integer, default=0),

        # Context and tagging
        sa.Column('topic', sa.String(100)),  # appointment, billing, prescription, etc.
        sa.Column('sub_topic', sa.String(100)),
        sa.Column('tags', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('context', postgresql.JSONB, default={}),  # Additional context data

        # Related resources
        sa.Column('related_resource_type', sa.String(50)),  # Appointment, Encounter, etc.
        sa.Column('related_resource_id', postgresql.UUID(as_uuid=True)),

        # SLA tracking
        sa.Column('sla_config_id', postgresql.UUID(as_uuid=True)),
        sa.Column('first_response_at', sa.DateTime(timezone=True)),
        sa.Column('first_response_sla_met', sa.Boolean),
        sa.Column('resolution_sla_met', sa.Boolean),

        # Timestamps
        sa.Column('first_message_at', sa.DateTime(timezone=True)),
        sa.Column('last_message_at', sa.DateTime(timezone=True)),
        sa.Column('last_patient_message_at', sa.DateTime(timezone=True)),
        sa.Column('resolved_at', sa.DateTime(timezone=True)),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('closed_at', sa.DateTime(timezone=True)),
        sa.Column('closed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_omnichannel_conversations_tenant_patient', 'omnichannel_conversations', ['tenant_id', 'patient_id'])
    op.create_index('ix_omnichannel_conversations_key', 'omnichannel_conversations', ['tenant_id', 'conversation_key'], unique=True)
    op.create_index('ix_omnichannel_conversations_status', 'omnichannel_conversations', ['tenant_id', 'status', 'assigned_agent_id'])
    op.create_index('ix_omnichannel_conversations_contact', 'omnichannel_conversations', ['tenant_id', 'external_contact_id'])

    # Omnichannel Messages
    op.create_table(
        'omnichannel_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('omnichannel_conversations.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id')),

        # Message identification
        sa.Column('external_id', sa.String(255)),  # Provider message ID
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('omnichannel_providers.id')),

        # Channel and direction
        sa.Column('channel', postgresql.ENUM('whatsapp', 'sms', 'email', 'voice', 'in_app', 'push_notification', 'webchat',
                                             name='omni_channel_type', create_type=False), nullable=False),
        sa.Column('direction', postgresql.ENUM('inbound', 'outbound', name='message_direction', create_type=False), nullable=False),

        # Sender/Recipient
        sa.Column('sender_type', sa.String(20)),  # patient, agent, system, bot
        sa.Column('sender_id', postgresql.UUID(as_uuid=True)),  # User ID if agent/system
        sa.Column('sender_name', sa.String(255)),
        sa.Column('sender_contact', sa.String(255)),  # Phone/email
        sa.Column('recipient_contact', sa.String(255)),

        # Content
        sa.Column('message_type', sa.String(50), default='text'),  # text, image, document, audio, video, template, interactive, location
        sa.Column('content', sa.Text),
        sa.Column('content_encrypted', sa.Boolean, default=False),
        sa.Column('content_structured', postgresql.JSONB),  # For interactive messages

        # Template information
        sa.Column('template_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('omnichannel_templates.id')),
        sa.Column('template_variables', postgresql.JSONB),

        # Email specific
        sa.Column('subject', sa.String(255)),
        sa.Column('cc', postgresql.ARRAY(sa.String)),
        sa.Column('bcc', postgresql.ARRAY(sa.String)),

        # Interactive elements (WhatsApp)
        sa.Column('buttons', postgresql.JSONB),
        sa.Column('list_sections', postgresql.JSONB),
        sa.Column('selected_button_id', sa.String(100)),
        sa.Column('selected_list_item_id', sa.String(100)),

        # Reply context
        sa.Column('reply_to_message_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('omnichannel_messages.id')),
        sa.Column('reply_to_external_id', sa.String(255)),

        # Delivery status
        sa.Column('status', postgresql.ENUM('pending', 'queued', 'sent', 'delivered', 'read', 'failed', 'bounced', 'blocked', 'expired',
                                            name='delivery_status', create_type=False), default='pending'),
        sa.Column('error_code', sa.String(50)),
        sa.Column('error_message', sa.Text),
        sa.Column('retry_count', sa.Integer, default=0),
        sa.Column('max_retries', sa.Integer, default=3),
        sa.Column('next_retry_at', sa.DateTime(timezone=True)),

        # Timestamps
        sa.Column('queued_at', sa.DateTime(timezone=True)),
        sa.Column('sent_at', sa.DateTime(timezone=True)),
        sa.Column('delivered_at', sa.DateTime(timezone=True)),
        sa.Column('read_at', sa.DateTime(timezone=True)),
        sa.Column('failed_at', sa.DateTime(timezone=True)),

        # Cost tracking
        sa.Column('cost', sa.Numeric(10, 4)),
        sa.Column('cost_currency', sa.String(3), default='USD'),
        sa.Column('segments', sa.Integer, default=1),  # SMS segments

        # NLP/AI analysis
        sa.Column('intent', sa.String(100)),
        sa.Column('entities', postgresql.JSONB),
        sa.Column('sentiment', sa.String(20)),
        sa.Column('sentiment_score', sa.Float),
        sa.Column('language_detected', sa.String(10)),
        sa.Column('auto_translated', sa.Boolean, default=False),
        sa.Column('original_content', sa.Text),

        # Metadata
        sa.Column('metadata', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
    )
    op.create_index('ix_omnichannel_messages_conversation', 'omnichannel_messages', ['conversation_id', 'created_at'])
    op.create_index('ix_omnichannel_messages_external', 'omnichannel_messages', ['external_id'])
    op.create_index('ix_omnichannel_messages_tenant_patient', 'omnichannel_messages', ['tenant_id', 'patient_id', 'created_at'])
    op.create_index('ix_omnichannel_messages_status', 'omnichannel_messages', ['tenant_id', 'status', 'next_retry_at'])

    # Message Attachments
    op.create_table(
        'message_attachments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('omnichannel_messages.id'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),

        # File information
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_type', sa.String(50)),  # image, document, audio, video
        sa.Column('mime_type', sa.String(100)),
        sa.Column('file_size', sa.BigInteger),

        # Storage
        sa.Column('storage_provider', sa.String(20), default='s3'),
        sa.Column('storage_key', sa.String(500)),
        sa.Column('storage_url', sa.String(1000)),
        sa.Column('signed_url', sa.String(2000)),
        sa.Column('signed_url_expires_at', sa.DateTime(timezone=True)),

        # Provider specific
        sa.Column('external_media_id', sa.String(255)),  # WhatsApp media ID
        sa.Column('external_url', sa.String(1000)),

        # Security
        sa.Column('is_encrypted', sa.Boolean, default=True),
        sa.Column('encryption_key_id', sa.String(100)),
        sa.Column('checksum', sa.String(64)),

        # Thumbnails (for images/videos)
        sa.Column('thumbnail_url', sa.String(1000)),
        sa.Column('width', sa.Integer),
        sa.Column('height', sa.Integer),
        sa.Column('duration_seconds', sa.Integer),  # For audio/video

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_message_attachments_message', 'message_attachments', ['message_id'])

    # Message Delivery Status (detailed tracking)
    op.create_table(
        'message_delivery_status',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('omnichannel_messages.id'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),

        # Status tracking
        sa.Column('status', postgresql.ENUM('pending', 'queued', 'sent', 'delivered', 'read', 'failed', 'bounced', 'blocked', 'expired',
                                            name='delivery_status', create_type=False), nullable=False),
        sa.Column('status_at', sa.DateTime(timezone=True), server_default=sa.func.now()),

        # Provider information
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('omnichannel_providers.id')),
        sa.Column('provider_status', sa.String(50)),
        sa.Column('provider_response', postgresql.JSONB),

        # Error details
        sa.Column('error_code', sa.String(50)),
        sa.Column('error_message', sa.Text),
        sa.Column('is_permanent_failure', sa.Boolean, default=False),

        # Webhook data
        sa.Column('webhook_payload', postgresql.JSONB),
        sa.Column('webhook_received_at', sa.DateTime(timezone=True)),
    )
    op.create_index('ix_message_delivery_status_message', 'message_delivery_status', ['message_id', 'status_at'])

    # ==================== Preferences & Consent ====================

    # Communication Preferences
    op.create_table(
        'communication_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),

        # Channel preferences
        sa.Column('preferred_channel', postgresql.ENUM('whatsapp', 'sms', 'email', 'voice', 'in_app', 'push_notification', 'webchat',
                                                       name='omni_channel_type', create_type=False)),
        sa.Column('fallback_channel', postgresql.ENUM('whatsapp', 'sms', 'email', 'voice', 'in_app', 'push_notification', 'webchat',
                                                      name='omni_channel_type', create_type=False)),
        sa.Column('channel_preferences', postgresql.JSONB, default={}),  # {channel: {enabled: bool, priority: int}}

        # Contact information
        sa.Column('phone_primary', sa.String(20)),
        sa.Column('phone_secondary', sa.String(20)),
        sa.Column('email_primary', sa.String(255)),
        sa.Column('email_secondary', sa.String(255)),
        sa.Column('whatsapp_number', sa.String(20)),

        # Time preferences
        sa.Column('preferred_language', sa.String(10), default='en'),
        sa.Column('timezone', sa.String(50), default='UTC'),
        sa.Column('preferred_time_start', sa.Time),  # Preferred contact window start
        sa.Column('preferred_time_end', sa.Time),
        sa.Column('do_not_disturb_start', sa.Time),
        sa.Column('do_not_disturb_end', sa.Time),
        sa.Column('allow_weekend_contact', sa.Boolean, default=True),

        # Frequency preferences
        sa.Column('max_messages_per_day', sa.Integer),
        sa.Column('max_messages_per_week', sa.Integer),
        sa.Column('min_hours_between_messages', sa.Integer, default=1),

        # Category preferences
        sa.Column('appointment_reminders', sa.Boolean, default=True),
        sa.Column('appointment_reminder_hours', postgresql.ARRAY(sa.Integer), default=[24, 2]),  # Hours before appointment
        sa.Column('health_tips', sa.Boolean, default=False),
        sa.Column('marketing_messages', sa.Boolean, default=False),
        sa.Column('survey_invitations', sa.Boolean, default=True),
        sa.Column('lab_results', sa.Boolean, default=True),
        sa.Column('prescription_reminders', sa.Boolean, default=True),
        sa.Column('billing_notifications', sa.Boolean, default=True),
        sa.Column('emergency_alerts', sa.Boolean, default=True),

        # Smart routing preferences
        sa.Column('auto_channel_selection', sa.Boolean, default=True),  # Let system choose best channel
        sa.Column('cost_optimization', sa.Boolean, default=False),  # Prefer cheaper channels

        # Metadata
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
    )
    op.create_index('ix_communication_preferences_patient', 'communication_preferences', ['tenant_id', 'patient_id'], unique=True)

    # Consent Records
    op.create_table(
        'consent_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),

        # Consent details
        sa.Column('consent_type', postgresql.ENUM('marketing', 'transactional', 'appointment_reminders', 'health_tips',
                                                  'surveys', 'emergency', 'all_communications',
                                                  name='consent_type', create_type=False), nullable=False),
        sa.Column('channel', postgresql.ENUM('whatsapp', 'sms', 'email', 'voice', 'in_app', 'push_notification', 'webchat',
                                             name='omni_channel_type', create_type=False)),  # NULL = all channels

        # Status
        sa.Column('status', postgresql.ENUM('granted', 'denied', 'withdrawn', 'expired', 'pending',
                                            name='consent_status', create_type=False), nullable=False),

        # Capture details
        sa.Column('capture_method', sa.String(50)),  # web_form, sms_keyword, voice_ivr, paper, api
        sa.Column('capture_source', sa.String(100)),  # Source system/form
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.String(500)),

        # Legal compliance
        sa.Column('consent_text', sa.Text),  # The actual text consented to
        sa.Column('consent_version', sa.String(20)),
        sa.Column('legal_basis', sa.String(50)),  # explicit_consent, legitimate_interest, etc.
        sa.Column('purposes', postgresql.ARRAY(sa.String)),

        # Validity
        sa.Column('valid_from', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('valid_until', sa.DateTime(timezone=True)),  # NULL = indefinite

        # Withdrawal
        sa.Column('withdrawn_at', sa.DateTime(timezone=True)),
        sa.Column('withdrawal_method', sa.String(50)),
        sa.Column('withdrawal_reason', sa.Text),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_consent_records_patient', 'consent_records', ['tenant_id', 'patient_id', 'consent_type'])
    op.create_index('ix_consent_records_status', 'consent_records', ['tenant_id', 'status', 'valid_until'])

    # Opt-Out Records
    op.create_table(
        'opt_out_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id')),

        # Contact identifier (can opt out without patient record)
        sa.Column('contact_type', sa.String(20), nullable=False),  # phone, email, whatsapp
        sa.Column('contact_value', sa.String(255), nullable=False),

        # Opt-out details
        sa.Column('channel', postgresql.ENUM('whatsapp', 'sms', 'email', 'voice', 'in_app', 'push_notification', 'webchat',
                                             name='omni_channel_type', create_type=False)),  # NULL = all channels
        sa.Column('opt_out_type', sa.String(50)),  # all, marketing, transactional
        sa.Column('reason', sa.Text),

        # Capture details
        sa.Column('method', sa.String(50)),  # sms_stop, email_unsubscribe, web_form, dnc_list
        sa.Column('source_message_id', postgresql.UUID(as_uuid=True)),
        sa.Column('source_campaign_id', postgresql.UUID(as_uuid=True)),

        # Status
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('opted_out_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('opted_back_in_at', sa.DateTime(timezone=True)),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_opt_out_records_contact', 'opt_out_records', ['tenant_id', 'contact_type', 'contact_value', 'is_active'])

    # ==================== Campaign Management ====================

    # Campaigns
    op.create_table(
        'campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),

        # Campaign configuration
        sa.Column('campaign_type', postgresql.ENUM('one_time', 'recurring', 'triggered', 'drip', 'ab_test',
                                                   name='campaign_type', create_type=False), nullable=False),
        sa.Column('channels', postgresql.ARRAY(sa.String), nullable=False),  # Channels to use
        sa.Column('primary_channel', postgresql.ENUM('whatsapp', 'sms', 'email', 'voice', 'in_app', 'push_notification', 'webchat',
                                                     name='omni_channel_type', create_type=False)),

        # Content
        sa.Column('template_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('omnichannel_templates.id')),
        sa.Column('subject', sa.String(255)),  # For email
        sa.Column('content', sa.Text),
        sa.Column('content_html', sa.Text),

        # Audience
        sa.Column('segment_id', postgresql.UUID(as_uuid=True)),  # Reference to segment
        sa.Column('segment_query', postgresql.JSONB),  # Dynamic segment query
        sa.Column('estimated_audience_size', sa.Integer),
        sa.Column('exclusion_lists', postgresql.ARRAY(postgresql.UUID)),  # Segment IDs to exclude

        # Scheduling
        sa.Column('scheduled_at', sa.DateTime(timezone=True)),
        sa.Column('timezone', sa.String(50), default='UTC'),
        sa.Column('send_window_start', sa.Time),  # Optimal send time window
        sa.Column('send_window_end', sa.Time),
        sa.Column('respect_dnd', sa.Boolean, default=True),

        # Recurring configuration
        sa.Column('recurrence_rule', sa.String(255)),  # RRULE format
        sa.Column('recurrence_end_date', sa.DateTime(timezone=True)),
        sa.Column('next_execution_at', sa.DateTime(timezone=True)),

        # Trigger configuration (for triggered campaigns)
        sa.Column('trigger_event', sa.String(100)),  # appointment_created, lab_result_ready, etc.
        sa.Column('trigger_conditions', postgresql.JSONB),
        sa.Column('trigger_delay_minutes', sa.Integer, default=0),

        # A/B Testing
        sa.Column('is_ab_test', sa.Boolean, default=False),
        sa.Column('ab_test_percentage', sa.Integer, default=20),  # % of audience for test
        sa.Column('ab_winner_criteria', sa.String(50)),  # open_rate, click_rate, conversion
        sa.Column('ab_test_duration_hours', sa.Integer, default=24),
        sa.Column('ab_winner_variant_id', postgresql.UUID(as_uuid=True)),

        # Status
        sa.Column('status', postgresql.ENUM('draft', 'scheduled', 'running', 'paused', 'completed', 'cancelled', 'failed',
                                            name='campaign_status', create_type=False), default='draft'),

        # Budget
        sa.Column('budget_limit', sa.Numeric(10, 2)),
        sa.Column('budget_spent', sa.Numeric(10, 2), default=0),
        sa.Column('cost_per_message', sa.Numeric(10, 4)),

        # Metrics
        sa.Column('total_recipients', sa.Integer, default=0),
        sa.Column('messages_sent', sa.Integer, default=0),
        sa.Column('messages_delivered', sa.Integer, default=0),
        sa.Column('messages_failed', sa.Integer, default=0),
        sa.Column('messages_opened', sa.Integer, default=0),
        sa.Column('messages_clicked', sa.Integer, default=0),
        sa.Column('opt_outs', sa.Integer, default=0),

        # Timestamps
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('paused_at', sa.DateTime(timezone=True)),
        sa.Column('cancelled_at', sa.DateTime(timezone=True)),

        # Metadata
        sa.Column('tags', postgresql.ARRAY(sa.String)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
    )
    op.create_index('ix_campaigns_tenant_status', 'campaigns', ['tenant_id', 'status'])
    op.create_index('ix_campaigns_scheduled', 'campaigns', ['tenant_id', 'status', 'scheduled_at'])

    # Campaign Segments
    op.create_table(
        'campaign_segments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),

        # Segment definition
        sa.Column('conditions', postgresql.JSONB, nullable=False),  # Filter conditions
        sa.Column('condition_logic', sa.String(10), default='AND'),  # AND, OR

        # Size tracking
        sa.Column('estimated_size', sa.Integer),
        sa.Column('last_calculated_at', sa.DateTime(timezone=True)),
        sa.Column('auto_refresh', sa.Boolean, default=True),
        sa.Column('refresh_interval_hours', sa.Integer, default=24),

        # Membership
        sa.Column('is_static', sa.Boolean, default=False),  # Static vs dynamic
        sa.Column('static_members', postgresql.ARRAY(postgresql.UUID)),  # For static segments

        # Metadata
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
    )
    op.create_index('ix_campaign_segments_tenant', 'campaign_segments', ['tenant_id', 'is_active'])

    # A/B Test Variants
    op.create_table(
        'ab_test_variants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('campaigns.id'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),

        # Variant configuration
        sa.Column('name', sa.String(50), nullable=False),  # A, B, C, etc.
        sa.Column('weight', sa.Integer, default=50),  # Distribution weight

        # Content variations
        sa.Column('subject', sa.String(255)),
        sa.Column('content', sa.Text),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('omnichannel_templates.id')),

        # Metrics
        sa.Column('recipients', sa.Integer, default=0),
        sa.Column('sent', sa.Integer, default=0),
        sa.Column('delivered', sa.Integer, default=0),
        sa.Column('opened', sa.Integer, default=0),
        sa.Column('clicked', sa.Integer, default=0),
        sa.Column('converted', sa.Integer, default=0),

        # Calculated rates
        sa.Column('delivery_rate', sa.Float),
        sa.Column('open_rate', sa.Float),
        sa.Column('click_rate', sa.Float),
        sa.Column('conversion_rate', sa.Float),

        # Winner flag
        sa.Column('is_winner', sa.Boolean, default=False),
        sa.Column('winner_declared_at', sa.DateTime(timezone=True)),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_ab_test_variants_campaign', 'ab_test_variants', ['campaign_id'])

    # Campaign Executions
    op.create_table(
        'campaign_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('campaigns.id'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),

        # Execution tracking
        sa.Column('execution_number', sa.Integer, default=1),
        sa.Column('status', sa.String(20), default='pending'),  # pending, running, completed, failed
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),

        # Metrics
        sa.Column('total_recipients', sa.Integer, default=0),
        sa.Column('processed', sa.Integer, default=0),
        sa.Column('sent', sa.Integer, default=0),
        sa.Column('delivered', sa.Integer, default=0),
        sa.Column('failed', sa.Integer, default=0),
        sa.Column('skipped', sa.Integer, default=0),

        # Cost
        sa.Column('total_cost', sa.Numeric(10, 2), default=0),

        # Errors
        sa.Column('error_message', sa.Text),
        sa.Column('error_details', postgresql.JSONB),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_campaign_executions_campaign', 'campaign_executions', ['campaign_id', 'execution_number'])

    # ==================== Unified Inbox ====================

    # Inbox Assignments
    op.create_table(
        'inbox_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('omnichannel_conversations.id'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),

        # Assignment details
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('assignment_type', sa.String(20), default='manual'),  # manual, auto, transfer, round_robin

        # Status
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('unassigned_at', sa.DateTime(timezone=True)),
        sa.Column('unassignment_reason', sa.String(50)),

        # Transfer info
        sa.Column('transferred_from', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('transfer_notes', sa.Text),
    )
    op.create_index('ix_inbox_assignments_agent', 'inbox_assignments', ['agent_id', 'is_active'])
    op.create_index('ix_inbox_assignments_conversation', 'inbox_assignments', ['conversation_id', 'is_active'])

    # Canned Responses
    op.create_table(
        'canned_responses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),

        # Response content
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('shortcut', sa.String(50)),  # Quick access code
        sa.Column('content', sa.Text, nullable=False),

        # Categorization
        sa.Column('category', sa.String(50)),
        sa.Column('tags', postgresql.ARRAY(sa.String)),

        # Scope
        sa.Column('is_global', sa.Boolean, default=True),  # Available to all agents
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),  # Personal response

        # Variables
        sa.Column('variables', postgresql.ARRAY(sa.String)),  # Placeholders in content

        # Usage
        sa.Column('usage_count', sa.Integer, default=0),
        sa.Column('last_used_at', sa.DateTime(timezone=True)),

        # Metadata
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
    )
    op.create_index('ix_canned_responses_tenant', 'canned_responses', ['tenant_id', 'is_active'])
    op.create_index('ix_canned_responses_shortcut', 'canned_responses', ['tenant_id', 'shortcut'])

    # Conversation Tags
    op.create_table(
        'conversation_tags',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('color', sa.String(7)),  # Hex color
        sa.Column('description', sa.Text),
        sa.Column('is_system', sa.Boolean, default=False),  # System-managed tags
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_conversation_tags_tenant', 'conversation_tags', ['tenant_id', 'is_active'])

    # SLA Configurations
    op.create_table(
        'sla_configurations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),

        # Priority thresholds (minutes)
        sa.Column('first_response_time_low', sa.Integer, default=60),
        sa.Column('first_response_time_normal', sa.Integer, default=30),
        sa.Column('first_response_time_high', sa.Integer, default=15),
        sa.Column('first_response_time_urgent', sa.Integer, default=5),

        sa.Column('resolution_time_low', sa.Integer, default=1440),  # 24 hours
        sa.Column('resolution_time_normal', sa.Integer, default=480),  # 8 hours
        sa.Column('resolution_time_high', sa.Integer, default=240),  # 4 hours
        sa.Column('resolution_time_urgent', sa.Integer, default=60),

        # Business hours
        sa.Column('business_hours_only', sa.Boolean, default=True),
        sa.Column('business_hours_start', sa.Time, default='09:00:00'),
        sa.Column('business_hours_end', sa.Time, default='17:00:00'),
        sa.Column('business_days', postgresql.ARRAY(sa.Integer), default=[1, 2, 3, 4, 5]),  # Mon-Fri

        # Escalation
        sa.Column('escalation_enabled', sa.Boolean, default=True),
        sa.Column('escalation_threshold_percentage', sa.Integer, default=80),  # Escalate at 80% of SLA
        sa.Column('escalation_notify_emails', postgresql.ARRAY(sa.String)),

        # Metadata
        sa.Column('is_default', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_sla_configurations_tenant', 'sla_configurations', ['tenant_id', 'is_active'])

    # SLA Tracking
    op.create_table(
        'sla_tracking',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('omnichannel_conversations.id'), nullable=False),
        sa.Column('sla_config_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sla_configurations.id'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),

        # First response
        sa.Column('first_response_due_at', sa.DateTime(timezone=True)),
        sa.Column('first_response_at', sa.DateTime(timezone=True)),
        sa.Column('first_response_breached', sa.Boolean, default=False),
        sa.Column('first_response_time_seconds', sa.Integer),

        # Resolution
        sa.Column('resolution_due_at', sa.DateTime(timezone=True)),
        sa.Column('resolved_at', sa.DateTime(timezone=True)),
        sa.Column('resolution_breached', sa.Boolean, default=False),
        sa.Column('resolution_time_seconds', sa.Integer),

        # Escalation
        sa.Column('escalated', sa.Boolean, default=False),
        sa.Column('escalated_at', sa.DateTime(timezone=True)),
        sa.Column('escalation_level', sa.Integer, default=0),

        # Pause tracking (for customer waiting time)
        sa.Column('paused_at', sa.DateTime(timezone=True)),
        sa.Column('total_paused_seconds', sa.Integer, default=0),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_sla_tracking_conversation', 'sla_tracking', ['conversation_id'])

    # ==================== Analytics ====================

    # Channel Analytics Daily
    op.create_table(
        'channel_analytics_daily',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('date', sa.Date, nullable=False),
        sa.Column('channel', postgresql.ENUM('whatsapp', 'sms', 'email', 'voice', 'in_app', 'push_notification', 'webchat',
                                             name='omni_channel_type', create_type=False), nullable=False),

        # Volume metrics
        sa.Column('messages_sent', sa.Integer, default=0),
        sa.Column('messages_delivered', sa.Integer, default=0),
        sa.Column('messages_failed', sa.Integer, default=0),
        sa.Column('messages_received', sa.Integer, default=0),
        sa.Column('conversations_started', sa.Integer, default=0),
        sa.Column('conversations_resolved', sa.Integer, default=0),

        # Rate metrics
        sa.Column('delivery_rate', sa.Float),
        sa.Column('open_rate', sa.Float),
        sa.Column('click_rate', sa.Float),
        sa.Column('response_rate', sa.Float),

        # Response time metrics
        sa.Column('avg_first_response_seconds', sa.Float),
        sa.Column('avg_resolution_seconds', sa.Float),
        sa.Column('median_first_response_seconds', sa.Float),
        sa.Column('median_resolution_seconds', sa.Float),

        # Cost metrics
        sa.Column('total_cost', sa.Numeric(10, 2), default=0),
        sa.Column('cost_per_message', sa.Numeric(10, 4)),

        # SLA metrics
        sa.Column('sla_first_response_met', sa.Integer, default=0),
        sa.Column('sla_first_response_breached', sa.Integer, default=0),
        sa.Column('sla_resolution_met', sa.Integer, default=0),
        sa.Column('sla_resolution_breached', sa.Integer, default=0),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_channel_analytics_daily_date', 'channel_analytics_daily', ['tenant_id', 'date', 'channel'], unique=True)

    # Campaign Analytics
    op.create_table(
        'campaign_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('campaigns.id'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('date', sa.Date, nullable=False),

        # Delivery metrics
        sa.Column('sent', sa.Integer, default=0),
        sa.Column('delivered', sa.Integer, default=0),
        sa.Column('bounced', sa.Integer, default=0),
        sa.Column('failed', sa.Integer, default=0),

        # Engagement metrics
        sa.Column('opened', sa.Integer, default=0),
        sa.Column('unique_opens', sa.Integer, default=0),
        sa.Column('clicked', sa.Integer, default=0),
        sa.Column('unique_clicks', sa.Integer, default=0),
        sa.Column('replied', sa.Integer, default=0),
        sa.Column('unsubscribed', sa.Integer, default=0),
        sa.Column('spam_reports', sa.Integer, default=0),

        # Conversion metrics
        sa.Column('conversions', sa.Integer, default=0),
        sa.Column('conversion_value', sa.Numeric(10, 2), default=0),

        # Calculated rates
        sa.Column('delivery_rate', sa.Float),
        sa.Column('open_rate', sa.Float),
        sa.Column('click_rate', sa.Float),
        sa.Column('conversion_rate', sa.Float),

        # Cost
        sa.Column('total_cost', sa.Numeric(10, 2), default=0),
        sa.Column('cost_per_conversion', sa.Numeric(10, 2)),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_campaign_analytics_campaign', 'campaign_analytics', ['campaign_id', 'date'])

    # Engagement Scores
    op.create_table(
        'engagement_scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id'), nullable=False),

        # Score
        sa.Column('overall_score', sa.Float, nullable=False),
        sa.Column('score_tier', sa.String(20)),  # high, medium, low, inactive

        # Component scores
        sa.Column('response_score', sa.Float),
        sa.Column('open_score', sa.Float),
        sa.Column('click_score', sa.Float),
        sa.Column('recency_score', sa.Float),
        sa.Column('frequency_score', sa.Float),

        # Activity metrics (for scoring)
        sa.Column('messages_received_30d', sa.Integer, default=0),
        sa.Column('messages_opened_30d', sa.Integer, default=0),
        sa.Column('messages_clicked_30d', sa.Integer, default=0),
        sa.Column('responses_30d', sa.Integer, default=0),
        sa.Column('last_interaction_at', sa.DateTime(timezone=True)),

        # Channel engagement
        sa.Column('preferred_channel', sa.String(20)),
        sa.Column('best_engagement_time', sa.Time),
        sa.Column('best_engagement_day', sa.Integer),

        # Metadata
        sa.Column('calculated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_engagement_scores_patient', 'engagement_scores', ['tenant_id', 'patient_id'], unique=True)
    op.create_index('ix_engagement_scores_tier', 'engagement_scores', ['tenant_id', 'score_tier'])

    # ==================== Audit & Compliance ====================

    # Communication Audit Log
    op.create_table(
        'communication_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),

        # Resource identification
        sa.Column('resource_type', sa.String(50), nullable=False),  # message, conversation, campaign, etc.
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('patients.id')),

        # Action details
        sa.Column('action', sa.String(50), nullable=False),  # create, read, update, delete, send, receive
        sa.Column('action_details', postgresql.JSONB),

        # Actor information
        sa.Column('actor_type', sa.String(20), nullable=False),  # user, system, api, webhook
        sa.Column('actor_id', postgresql.UUID(as_uuid=True)),
        sa.Column('actor_name', sa.String(255)),
        sa.Column('actor_ip', sa.String(45)),
        sa.Column('actor_user_agent', sa.String(500)),

        # PHI tracking
        sa.Column('contains_phi', sa.Boolean, default=False),
        sa.Column('phi_accessed', postgresql.ARRAY(sa.String)),  # Fields accessed

        # Channel information
        sa.Column('channel', sa.String(20)),
        sa.Column('external_id', sa.String(255)),

        # Request/Response
        sa.Column('request_id', sa.String(100)),
        sa.Column('request_method', sa.String(10)),
        sa.Column('request_path', sa.String(500)),

        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_communication_audit_log_resource', 'communication_audit_log', ['resource_type', 'resource_id'])
    op.create_index('ix_communication_audit_log_patient', 'communication_audit_log', ['tenant_id', 'patient_id', 'created_at'])
    op.create_index('ix_communication_audit_log_date', 'communication_audit_log', ['tenant_id', 'created_at'])

    # Encryption Keys
    op.create_table(
        'encryption_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False),

        # Key details
        sa.Column('key_id', sa.String(100), nullable=False),  # External key reference
        sa.Column('key_type', sa.String(20), nullable=False),  # message, attachment, credential
        sa.Column('algorithm', sa.String(20), default='AES-256-GCM'),

        # Key versioning
        sa.Column('version', sa.Integer, default=1),
        sa.Column('is_active', sa.Boolean, default=True),

        # Rotation
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('rotated_at', sa.DateTime(timezone=True)),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('rotated_from_id', postgresql.UUID(as_uuid=True)),
    )
    op.create_index('ix_encryption_keys_tenant', 'encryption_keys', ['tenant_id', 'key_type', 'is_active'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('encryption_keys')
    op.drop_table('communication_audit_log')
    op.drop_table('engagement_scores')
    op.drop_table('campaign_analytics')
    op.drop_table('channel_analytics_daily')
    op.drop_table('sla_tracking')
    op.drop_table('sla_configurations')
    op.drop_table('conversation_tags')
    op.drop_table('canned_responses')
    op.drop_table('inbox_assignments')
    op.drop_table('campaign_executions')
    op.drop_table('ab_test_variants')
    op.drop_table('campaign_segments')
    op.drop_table('campaigns')
    op.drop_table('opt_out_records')
    op.drop_table('consent_records')
    op.drop_table('communication_preferences')
    op.drop_table('message_delivery_status')
    op.drop_table('message_attachments')
    op.drop_table('omnichannel_messages')
    op.drop_table('omnichannel_conversations')
    op.drop_table('template_approvals')
    op.drop_table('omnichannel_templates')
    op.drop_table('omnichannel_providers')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS consent_status CASCADE")
    op.execute("DROP TYPE IF EXISTS consent_type CASCADE")
    op.execute("DROP TYPE IF EXISTS campaign_type CASCADE")
    op.execute("DROP TYPE IF EXISTS campaign_status CASCADE")
    op.execute("DROP TYPE IF EXISTS provider_type CASCADE")
    op.execute("DROP TYPE IF EXISTS template_category CASCADE")
    op.execute("DROP TYPE IF EXISTS template_status CASCADE")
    op.execute("DROP TYPE IF EXISTS conversation_priority CASCADE")
    op.execute("DROP TYPE IF EXISTS conversation_status CASCADE")
    op.execute("DROP TYPE IF EXISTS delivery_status CASCADE")
    op.execute("DROP TYPE IF EXISTS message_direction CASCADE")
    op.execute("DROP TYPE IF EXISTS omni_channel_type CASCADE")

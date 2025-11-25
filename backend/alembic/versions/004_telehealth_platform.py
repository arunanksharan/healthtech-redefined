"""EPIC-007: Telehealth Platform Database Tables

Revision ID: 004_telehealth_platform
Revises: 003_clinical_workflows
Create Date: 2024-01-20

This migration creates all tables for EPIC-007 Telehealth Platform:
- Video Sessions & Participants (US-007.1)
- Virtual Waiting Room (US-007.2)
- Telehealth Appointments & Scheduling (US-007.4)
- Session Recording & Consent (US-007.10)
- Payment Processing (US-007.6)
- Analytics & Satisfaction Surveys (US-007.8)
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '004_telehealth_platform'
down_revision = '003_clinical_workflows'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==================== Telehealth Appointments ====================
    # Created first since telehealth_sessions references it
    op.create_table(
        'telehealth_appointments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_name', sa.String(200)),
        sa.Column('provider_name', sa.String(200)),
        sa.Column('appointment_type', sa.String(50), default='video_visit'),
        sa.Column('scheduled_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('scheduled_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Integer, default=30),
        sa.Column('patient_timezone', sa.String(50), default='UTC'),
        sa.Column('provider_timezone', sa.String(50), default='UTC'),
        sa.Column('reason_for_visit', sa.Text),
        sa.Column('chief_complaint', sa.Text),
        sa.Column('diagnosis_codes', postgresql.ARRAY(sa.String(20)), default=[]),
        sa.Column('session_id', postgresql.UUID(as_uuid=True)),
        sa.Column('join_url', sa.String(500)),
        sa.Column('status', sa.String(50), default='scheduled'),
        sa.Column('confirmed_at', sa.DateTime(timezone=True)),
        sa.Column('cancelled_at', sa.DateTime(timezone=True)),
        sa.Column('cancellation_reason', sa.Text),
        sa.Column('cancelled_by', postgresql.UUID(as_uuid=True)),
        sa.Column('rescheduled_from', postgresql.UUID(as_uuid=True)),
        sa.Column('rescheduled_to', postgresql.UUID(as_uuid=True)),
        sa.Column('copay_amount', sa.Float, default=0),
        sa.Column('payment_status', sa.String(50), default='pending'),
        sa.Column('payment_id', sa.String(100)),
        sa.Column('insurance_verified', sa.Boolean, default=False),
        sa.Column('insurance_verification_id', sa.String(100)),
        sa.Column('pre_visit_notes', sa.Text),
        sa.Column('post_visit_notes', sa.Text),
        sa.Column('metadata', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_telehealth_appointments_tenant', 'telehealth_appointments', ['tenant_id'])
    op.create_index('ix_telehealth_appointments_patient', 'telehealth_appointments', ['patient_id'])
    op.create_index('ix_telehealth_appointments_provider', 'telehealth_appointments', ['provider_id'])
    op.create_index('ix_telehealth_appointments_status', 'telehealth_appointments', ['status'])
    op.create_index('idx_telehealth_appointments_tenant_patient', 'telehealth_appointments', ['tenant_id', 'patient_id'])
    op.create_index('idx_telehealth_appointments_tenant_provider', 'telehealth_appointments', ['tenant_id', 'provider_id'])
    op.create_index('idx_telehealth_appointments_tenant_scheduled', 'telehealth_appointments', ['tenant_id', 'scheduled_start'])
    op.create_index('idx_telehealth_appointments_tenant_status', 'telehealth_appointments', ['tenant_id', 'status'])

    # Appointment Reminders
    op.create_table(
        'appointment_reminders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('appointment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('telehealth_appointments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reminder_type', sa.String(20), nullable=False),
        sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True)),
        sa.Column('content', sa.Text),
        sa.Column('delivery_status', sa.String(50), default='pending'),
        sa.Column('delivery_error', sa.Text),
    )
    op.create_index('ix_appointment_reminders_tenant', 'appointment_reminders', ['tenant_id'])
    op.create_index('idx_appointment_reminders_scheduled', 'appointment_reminders', ['scheduled_for'])
    op.create_index('idx_appointment_reminders_status', 'appointment_reminders', ['delivery_status'])

    # ==================== Telehealth Sessions ====================
    op.create_table(
        'telehealth_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('appointment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('telehealth_appointments.id')),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True)),
        sa.Column('room_name', sa.String(100), nullable=False, unique=True),
        sa.Column('room_token', sa.Text),
        sa.Column('session_type', sa.String(50), default='video_visit'),
        sa.Column('scheduled_duration_minutes', sa.Integer, default=30),
        sa.Column('max_participants', sa.Integer, default=10),
        sa.Column('status', sa.String(50), default='scheduled'),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('ended_at', sa.DateTime(timezone=True)),
        sa.Column('actual_duration_seconds', sa.Integer),
        sa.Column('is_recording', sa.Boolean, default=False),
        sa.Column('recording_id', postgresql.UUID(as_uuid=True)),
        sa.Column('consent_obtained', sa.Boolean, default=False),
        sa.Column('encryption_key_id', sa.String(100)),
        sa.Column('join_password', sa.String(100)),
        sa.Column('waiting_room_enabled', sa.Boolean, default=True),
        sa.Column('screen_sharing_enabled', sa.Boolean, default=True),
        sa.Column('chat_enabled', sa.Boolean, default=True),
        sa.Column('file_sharing_enabled', sa.Boolean, default=True),
        sa.Column('whiteboard_enabled', sa.Boolean, default=False),
        sa.Column('metadata', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_telehealth_sessions_tenant', 'telehealth_sessions', ['tenant_id'])
    op.create_index('ix_telehealth_sessions_status', 'telehealth_sessions', ['status'])
    op.create_index('idx_telehealth_sessions_tenant_status', 'telehealth_sessions', ['tenant_id', 'status'])
    op.create_index('idx_telehealth_sessions_appointment', 'telehealth_sessions', ['appointment_id'])

    # Session Participants
    op.create_table(
        'session_participants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('telehealth_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('display_name', sa.String(200)),
        sa.Column('avatar_url', sa.String(500)),
        sa.Column('status', sa.String(50), default='invited'),
        sa.Column('connection_id', sa.String(100)),
        sa.Column('device_info', postgresql.JSONB, default={}),
        sa.Column('connection_quality', postgresql.JSONB, default={}),
        sa.Column('video_enabled', sa.Boolean, default=True),
        sa.Column('audio_enabled', sa.Boolean, default=True),
        sa.Column('screen_sharing', sa.Boolean, default=False),
        sa.Column('invited_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('joined_at', sa.DateTime(timezone=True)),
        sa.Column('left_at', sa.DateTime(timezone=True)),
        sa.Column('can_share_screen', sa.Boolean, default=True),
        sa.Column('can_record', sa.Boolean, default=False),
        sa.Column('can_admit_participants', sa.Boolean, default=False),
    )
    op.create_index('ix_session_participants_tenant', 'session_participants', ['tenant_id'])
    op.create_index('idx_session_participants_session', 'session_participants', ['session_id'])
    op.create_index('idx_session_participants_user', 'session_participants', ['user_id'])

    # Session Events
    op.create_table(
        'session_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('telehealth_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('participant_id', postgresql.UUID(as_uuid=True)),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('data', postgresql.JSONB, default={}),
    )
    op.create_index('ix_session_events_tenant', 'session_events', ['tenant_id'])
    op.create_index('idx_session_events_session', 'session_events', ['session_id'])
    op.create_index('idx_session_events_type', 'session_events', ['event_type'])

    # ==================== Provider Schedules ====================
    op.create_table(
        'provider_schedules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('weekly_hours', postgresql.JSONB, default={}),
        sa.Column('timezone', sa.String(50), default='America/New_York'),
        sa.Column('appointment_types', postgresql.ARRAY(sa.String(50)), default=[]),
        sa.Column('default_duration_minutes', sa.Integer, default=30),
        sa.Column('buffer_minutes', sa.Integer, default=5),
        sa.Column('max_daily_appointments', sa.Integer),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'provider_id', name='uq_provider_schedule'),
    )
    op.create_index('ix_provider_schedules_tenant', 'provider_schedules', ['tenant_id'])
    op.create_index('ix_provider_schedules_provider', 'provider_schedules', ['provider_id'])

    # Schedule Blocked Times
    op.create_table(
        'schedule_blocked_times',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('schedule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('provider_schedules.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reason', sa.String(200)),
        sa.Column('is_recurring', sa.Boolean, default=False),
        sa.Column('recurrence_pattern', sa.String(50)),
    )
    op.create_index('ix_schedule_blocked_times_tenant', 'schedule_blocked_times', ['tenant_id'])

    # ==================== Waiting Rooms ====================
    op.create_table(
        'waiting_rooms',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True)),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True)),
        sa.Column('max_wait_minutes', sa.Integer, default=60),
        sa.Column('auto_notify_minutes', sa.Integer, default=5),
        sa.Column('device_check_required', sa.Boolean, default=True),
        sa.Column('forms_required', sa.Boolean, default=True),
        sa.Column('is_open', sa.Boolean, default=True),
        sa.Column('current_delay_minutes', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_waiting_rooms_tenant', 'waiting_rooms', ['tenant_id'])
    op.create_index('ix_waiting_rooms_provider', 'waiting_rooms', ['provider_id'])

    # Waiting Room Entries
    op.create_table(
        'waiting_room_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('waiting_room_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('waiting_rooms.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True)),
        sa.Column('appointment_id', postgresql.UUID(as_uuid=True)),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(50), default='checked_in'),
        sa.Column('priority', sa.Integer, default=0),
        sa.Column('checked_in_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('scheduled_time', sa.DateTime(timezone=True)),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True)),
        sa.Column('provider_name', sa.String(200)),
        sa.Column('provider_available', sa.Boolean, default=False),
        sa.Column('device_check_status', sa.String(50), default='not_started'),
        sa.Column('device_check_result', postgresql.JSONB, default={}),
        sa.Column('queue_position', sa.Integer, default=0),
        sa.Column('estimated_wait_minutes', sa.Integer, default=0),
        sa.Column('forms_completed', sa.Boolean, default=False),
        sa.Column('metadata', postgresql.JSONB, default={}),
        sa.Column('departed_at', sa.DateTime(timezone=True)),
        sa.Column('departure_reason', sa.String(100)),
    )
    op.create_index('ix_waiting_room_entries_tenant', 'waiting_room_entries', ['tenant_id'])
    op.create_index('ix_waiting_room_entries_patient', 'waiting_room_entries', ['patient_id'])
    op.create_index('ix_waiting_room_entries_status', 'waiting_room_entries', ['status'])
    op.create_index('idx_waiting_room_entries_tenant_patient', 'waiting_room_entries', ['tenant_id', 'patient_id'])
    op.create_index('idx_waiting_room_entries_room_status', 'waiting_room_entries', ['waiting_room_id', 'status'])

    # Waiting Room Messages
    op.create_table(
        'waiting_room_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entry_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('waiting_room_entries.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_type', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('read', sa.Boolean, default=False),
    )
    op.create_index('ix_waiting_room_messages_tenant', 'waiting_room_messages', ['tenant_id'])

    # Pre-Visit Forms
    op.create_table(
        'pre_visit_forms',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entry_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('waiting_room_entries.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('form_type', sa.String(50), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('questions', postgresql.JSONB, default=[]),
        sa.Column('responses', postgresql.JSONB, default={}),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
    )
    op.create_index('ix_pre_visit_forms_tenant', 'pre_visit_forms', ['tenant_id'])

    # ==================== Session Recordings ====================
    op.create_table(
        'session_recordings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('telehealth_sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(50), default='initializing'),
        sa.Column('format', sa.String(20), default='mp4'),
        sa.Column('duration_seconds', sa.Integer),
        sa.Column('file_size_bytes', sa.Integer),
        sa.Column('storage_path', sa.String(500)),
        sa.Column('storage_bucket', sa.String(100)),
        sa.Column('storage_provider', sa.String(50), default='s3'),
        sa.Column('encryption_key_id', sa.String(100)),
        sa.Column('encryption_algorithm', sa.String(50), default='AES-256-GCM'),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('ended_at', sa.DateTime(timezone=True)),
        sa.Column('processed_at', sa.DateTime(timezone=True)),
        sa.Column('retention_days', sa.Integer, default=365),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
    )
    op.create_index('ix_session_recordings_tenant', 'session_recordings', ['tenant_id'])
    op.create_index('ix_session_recordings_session', 'session_recordings', ['session_id'])

    # Recording Consents
    op.create_table(
        'recording_consents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('recording_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('session_recordings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('participant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('consented', sa.Boolean, nullable=False),
        sa.Column('consented_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('ip_address', sa.String(50)),
        sa.Column('user_agent', sa.String(500)),
    )
    op.create_index('ix_recording_consents_tenant', 'recording_consents', ['tenant_id'])

    # ==================== Session Analytics ====================
    op.create_table(
        'session_analytics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('avg_latency_ms', sa.Float),
        sa.Column('avg_packet_loss_percent', sa.Float),
        sa.Column('avg_jitter_ms', sa.Float),
        sa.Column('avg_mos_score', sa.Float),
        sa.Column('avg_video_bitrate_kbps', sa.Integer),
        sa.Column('video_quality_changes', sa.Integer, default=0),
        sa.Column('video_freeze_count', sa.Integer, default=0),
        sa.Column('video_freeze_duration_seconds', sa.Integer, default=0),
        sa.Column('avg_audio_bitrate_kbps', sa.Integer),
        sa.Column('audio_dropout_count', sa.Integer, default=0),
        sa.Column('audio_dropout_duration_seconds', sa.Integer, default=0),
        sa.Column('connection_attempts', sa.Integer, default=1),
        sa.Column('reconnection_count', sa.Integer, default=0),
        sa.Column('total_connection_time_seconds', sa.Integer),
        sa.Column('technical_issues', postgresql.JSONB, default=[]),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_session_analytics_tenant', 'session_analytics', ['tenant_id'])
    op.create_index('ix_session_analytics_session', 'session_analytics', ['session_id'])

    # ==================== Telehealth Payments ====================
    op.create_table(
        'telehealth_payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('appointment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount_cents', sa.Integer, nullable=False),
        sa.Column('currency', sa.String(3), default='USD'),
        sa.Column('payment_method', sa.String(50)),
        sa.Column('payment_provider', sa.String(50), default='stripe'),
        sa.Column('external_payment_id', sa.String(100)),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('card_last_four', sa.String(4)),
        sa.Column('card_brand', sa.String(20)),
        sa.Column('authorized_at', sa.DateTime(timezone=True)),
        sa.Column('captured_at', sa.DateTime(timezone=True)),
        sa.Column('refunded_at', sa.DateTime(timezone=True)),
        sa.Column('refund_amount_cents', sa.Integer),
        sa.Column('refund_reason', sa.String(200)),
        sa.Column('receipt_url', sa.String(500)),
        sa.Column('metadata', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_telehealth_payments_tenant', 'telehealth_payments', ['tenant_id'])
    op.create_index('ix_telehealth_payments_appointment', 'telehealth_payments', ['appointment_id'])
    op.create_index('ix_telehealth_payments_status', 'telehealth_payments', ['status'])

    # ==================== Patient Satisfaction Surveys ====================
    op.create_table(
        'patient_satisfaction_surveys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('appointment_id', postgresql.UUID(as_uuid=True)),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('overall_rating', sa.Integer),
        sa.Column('video_quality_rating', sa.Integer),
        sa.Column('audio_quality_rating', sa.Integer),
        sa.Column('provider_rating', sa.Integer),
        sa.Column('ease_of_use_rating', sa.Integer),
        sa.Column('would_recommend', sa.Boolean),
        sa.Column('nps_score', sa.Integer),
        sa.Column('feedback_text', sa.Text),
        sa.Column('technical_issues_reported', postgresql.JSONB, default=[]),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
    )
    op.create_index('ix_patient_satisfaction_surveys_tenant', 'patient_satisfaction_surveys', ['tenant_id'])
    op.create_index('ix_patient_satisfaction_surveys_session', 'patient_satisfaction_surveys', ['session_id'])


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_table('patient_satisfaction_surveys')
    op.drop_table('telehealth_payments')
    op.drop_table('session_analytics')
    op.drop_table('recording_consents')
    op.drop_table('session_recordings')
    op.drop_table('pre_visit_forms')
    op.drop_table('waiting_room_messages')
    op.drop_table('waiting_room_entries')
    op.drop_table('waiting_rooms')
    op.drop_table('schedule_blocked_times')
    op.drop_table('provider_schedules')
    op.drop_table('session_events')
    op.drop_table('session_participants')
    op.drop_table('telehealth_sessions')
    op.drop_table('appointment_reminders')
    op.drop_table('telehealth_appointments')

"""add_conversation_voice_analytics_tables

Revision ID: f548902ab172
Revises: e6c03f64750e
Create Date: 2025-11-19 04:12:55.569293

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f548902ab172'
down_revision: Union[str, Sequence[str], None] = 'e6c03f64750e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add conversation, voice call, and analytics tables."""

    # ============================================================================
    # CONVERSATIONS TABLE
    # ============================================================================
    op.create_table(
        'conversations',
        sa.Column('id', sa.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('patient_id', sa.UUID(), nullable=True),
        sa.Column('subject', sa.String(200), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='open'),
        sa.Column('priority', sa.String(10), nullable=False, server_default='p2'),
        sa.Column('channel_type', sa.String(20), nullable=False, server_default='whatsapp'),
        sa.Column('external_id', sa.String(255), nullable=True),
        sa.Column('current_owner_id', sa.UUID(), nullable=True),
        sa.Column('department_id', sa.UUID(), nullable=True),
        sa.Column('state_data', sa.dialects.postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('extracted_data', sa.dialects.postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('is_intake_complete', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('appointment_id', sa.UUID(), nullable=True),
        sa.Column('journey_instance_id', sa.UUID(), nullable=True),
        sa.Column('first_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.ForeignKeyConstraint(['current_owner_id'], ['practitioners.id']),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id']),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id']),
        sa.ForeignKeyConstraint(['journey_instance_id'], ['journey_instances.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_conversations_tenant', 'conversations', ['tenant_id'])
    op.create_index('idx_conversations_patient_status', 'conversations', ['patient_id', 'status'])
    op.create_index('idx_conversations_channel_status', 'conversations', ['channel_type', 'status'])
    op.create_index('idx_conversations_owner', 'conversations', ['current_owner_id', 'status'])
    op.create_index('idx_conversations_last_message', 'conversations', ['last_message_at'])
    op.create_index('idx_conversations_external_id', 'conversations', ['external_id'])

    # ============================================================================
    # CONVERSATION MESSAGES TABLE
    # ============================================================================
    op.create_table(
        'conversation_messages',
        sa.Column('id', sa.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('conversation_id', sa.UUID(), nullable=False),
        sa.Column('direction', sa.String(10), nullable=False),
        sa.Column('actor_type', sa.String(20), nullable=False),
        sa.Column('actor_id', sa.UUID(), nullable=True),
        sa.Column('content_type', sa.String(20), nullable=False, server_default='text'),
        sa.Column('text_body', sa.Text(), nullable=True),
        sa.Column('media_url', sa.String(512), nullable=True),
        sa.Column('media_type', sa.String(100), nullable=True),
        sa.Column('media_size_bytes', sa.Integer(), nullable=True),
        sa.Column('external_message_id', sa.String(255), nullable=True),
        sa.Column('delivery_status', sa.String(20), nullable=True),
        sa.Column('delivery_error', sa.Text(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sentiment', sa.String(20), nullable=True),
        sa.Column('intent', sa.String(50), nullable=True),
        sa.Column('entities', sa.dialects.postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('language', sa.String(10), nullable=True),
        sa.Column('metadata', sa.dialects.postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_conv_messages_tenant', 'conversation_messages', ['tenant_id'])
    op.create_index('idx_conv_messages_conversation', 'conversation_messages', ['conversation_id'])
    op.create_index('idx_conv_messages_conversation_created', 'conversation_messages', ['conversation_id', 'created_at'])
    op.create_index('idx_conv_messages_direction', 'conversation_messages', ['direction', 'created_at'])
    op.create_index('idx_conv_messages_external_id', 'conversation_messages', ['external_message_id'])

    # ============================================================================
    # VOICE CALLS TABLE
    # ============================================================================
    op.create_table(
        'voice_calls',
        sa.Column('id', sa.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('patient_id', sa.UUID(), nullable=True),
        sa.Column('zoice_call_id', sa.UUID(), nullable=False, unique=True),
        sa.Column('plivo_call_id', sa.String(255), nullable=True),
        sa.Column('patient_phone', sa.String(20), nullable=False),
        sa.Column('agent_phone', sa.String(20), nullable=True),
        sa.Column('call_type', sa.String(20), nullable=False, server_default='inbound'),
        sa.Column('call_status', sa.String(20), nullable=False, server_default='scheduled'),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('pipeline_id', sa.UUID(), nullable=True),
        sa.Column('agent_name', sa.String(100), nullable=True),
        sa.Column('detected_intent', sa.String(50), nullable=True),
        sa.Column('call_outcome', sa.String(50), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('conversation_id', sa.UUID(), nullable=True),
        sa.Column('appointment_id', sa.UUID(), nullable=True),
        sa.Column('language', sa.String(10), nullable=True),
        sa.Column('sentiment', sa.String(20), nullable=True),
        sa.Column('audio_quality_score', sa.Float(), nullable=True),
        sa.Column('transcription_quality_score', sa.Float(), nullable=True),
        sa.Column('metadata', sa.dialects.postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id']),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_voice_calls_tenant', 'voice_calls', ['tenant_id'])
    op.create_index('idx_voice_calls_patient_started', 'voice_calls', ['patient_id', 'started_at'])
    op.create_index('idx_voice_calls_phone_started', 'voice_calls', ['patient_phone', 'started_at'])
    op.create_index('idx_voice_calls_status_started', 'voice_calls', ['call_status', 'started_at'])
    op.create_index('idx_voice_calls_intent', 'voice_calls', ['detected_intent'])
    op.create_index('idx_voice_calls_zoice_id', 'voice_calls', ['zoice_call_id'])
    op.create_index('idx_voice_calls_plivo_id', 'voice_calls', ['plivo_call_id'])

    # ============================================================================
    # VOICE CALL TRANSCRIPTS TABLE
    # ============================================================================
    op.create_table(
        'voice_call_transcripts',
        sa.Column('id', sa.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('call_id', sa.UUID(), nullable=False),
        sa.Column('full_transcript', sa.Text(), nullable=False),
        sa.Column('turns', sa.dialects.postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('language', sa.String(10), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('processing_duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['call_id'], ['voice_calls.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_voice_transcripts_tenant', 'voice_call_transcripts', ['tenant_id'])
    op.create_index('idx_voice_transcripts_call', 'voice_call_transcripts', ['call_id'])

    # ============================================================================
    # VOICE CALL RECORDINGS TABLE
    # ============================================================================
    op.create_table(
        'voice_call_recordings',
        sa.Column('id', sa.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('call_id', sa.UUID(), nullable=False),
        sa.Column('recording_url', sa.String(512), nullable=False),
        sa.Column('storage_provider', sa.String(50), nullable=True),
        sa.Column('storage_path', sa.String(512), nullable=True),
        sa.Column('format', sa.String(20), nullable=True),
        sa.Column('codec', sa.String(50), nullable=True),
        sa.Column('sample_rate', sa.Integer(), nullable=True),
        sa.Column('channels', sa.Integer(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('audio_quality', sa.String(20), nullable=True),
        sa.Column('bitrate_kbps', sa.Integer(), nullable=True),
        sa.Column('is_redacted', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('retention_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['call_id'], ['voice_calls.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_voice_recordings_tenant', 'voice_call_recordings', ['tenant_id'])
    op.create_index('idx_voice_recordings_call', 'voice_call_recordings', ['call_id'])
    op.create_index('idx_voice_recordings_retention', 'voice_call_recordings', ['retention_expires_at'])

    # ============================================================================
    # VOICE CALL EXTRACTIONS TABLE
    # ============================================================================
    op.create_table(
        'voice_call_extractions',
        sa.Column('id', sa.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('call_id', sa.UUID(), nullable=False),
        sa.Column('extraction_type', sa.String(50), nullable=False),
        sa.Column('pipeline_id', sa.UUID(), nullable=True),
        sa.Column('prompt_template', sa.String(100), nullable=True),
        sa.Column('extracted_data', sa.dialects.postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('confidence_scores', sa.dialects.postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('overall_confidence', sa.Float(), nullable=True),
        sa.Column('is_validated', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('validation_errors', sa.dialects.postgresql.JSONB(), nullable=True, server_default='[]'),
        sa.Column('model_used', sa.String(100), nullable=True),
        sa.Column('processing_duration_ms', sa.Integer(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['call_id'], ['voice_calls.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_voice_extractions_tenant', 'voice_call_extractions', ['tenant_id'])
    op.create_index('idx_voice_extractions_call', 'voice_call_extractions', ['call_id'])
    op.create_index('idx_voice_extractions_type', 'voice_call_extractions', ['extraction_type'])

    # ============================================================================
    # ANALYTICS TABLES
    # ============================================================================

    # Analytics - Appointment Daily
    op.create_table(
        'analytics_appointment_daily',
        sa.Column('id', sa.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('hour', sa.Integer(), nullable=True),
        sa.Column('channel_origin', sa.String(20), nullable=True),
        sa.Column('practitioner_id', sa.UUID(), nullable=True),
        sa.Column('department_id', sa.UUID(), nullable=True),
        sa.Column('location_id', sa.UUID(), nullable=True),
        sa.Column('total_appointments', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('scheduled_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('confirmed_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('completed_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('canceled_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('no_show_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('rescheduled_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('no_show_rate', sa.Float(), nullable=True),
        sa.Column('completion_rate', sa.Float(), nullable=True),
        sa.Column('cancellation_rate', sa.Float(), nullable=True),
        sa.Column('computed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['practitioner_id'], ['practitioners.id']),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id']),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_analytics_appt_tenant_date', 'analytics_appointment_daily', ['tenant_id', 'date'])
    op.create_index('idx_analytics_appt_channel_date', 'analytics_appointment_daily', ['channel_origin', 'date'])
    op.create_index('idx_analytics_appt_practitioner_date', 'analytics_appointment_daily', ['practitioner_id', 'date'])
    op.create_index('idx_analytics_appt_dept_date', 'analytics_appointment_daily', ['department_id', 'date'])

    # Analytics - Journey Daily
    op.create_table(
        'analytics_journey_daily',
        sa.Column('id', sa.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('journey_id', sa.UUID(), nullable=True),
        sa.Column('journey_type', sa.String(50), nullable=True),
        sa.Column('department_id', sa.UUID(), nullable=True),
        sa.Column('total_active_journeys', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('completed_journeys', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('paused_journeys', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('canceled_journeys', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('new_journeys_started', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('avg_completion_percentage', sa.Float(), nullable=True),
        sa.Column('overdue_steps_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_journey_steps_completed', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('avg_steps_per_journey', sa.Float(), nullable=True),
        sa.Column('computed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['journey_id'], ['journeys.id']),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_analytics_journey_tenant_date', 'analytics_journey_daily', ['tenant_id', 'date'])
    op.create_index('idx_analytics_journey_type_date', 'analytics_journey_daily', ['journey_type', 'date'])
    op.create_index('idx_analytics_journey_dept_date', 'analytics_journey_daily', ['department_id', 'date'])

    # Analytics - Communication Daily
    op.create_table(
        'analytics_communication_daily',
        sa.Column('id', sa.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('hour', sa.Integer(), nullable=True),
        sa.Column('channel_type', sa.String(20), nullable=True),
        sa.Column('direction', sa.String(10), nullable=True),
        sa.Column('total_messages', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_conversations', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('new_conversations', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('closed_conversations', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('avg_response_time_seconds', sa.Float(), nullable=True),
        sa.Column('median_response_time_seconds', sa.Float(), nullable=True),
        sa.Column('response_rate_percentage', sa.Float(), nullable=True),
        sa.Column('avg_messages_per_conversation', sa.Float(), nullable=True),
        sa.Column('avg_conversation_duration_hours', sa.Float(), nullable=True),
        sa.Column('positive_sentiment_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('neutral_sentiment_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('negative_sentiment_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('computed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_analytics_comm_tenant_date', 'analytics_communication_daily', ['tenant_id', 'date'])
    op.create_index('idx_analytics_comm_channel_date', 'analytics_communication_daily', ['channel_type', 'date'])

    # Analytics - Voice Call Daily
    op.create_table(
        'analytics_voice_call_daily',
        sa.Column('id', sa.UUID(), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('hour', sa.Integer(), nullable=True),
        sa.Column('call_type', sa.String(20), nullable=True),
        sa.Column('detected_intent', sa.String(50), nullable=True),
        sa.Column('call_outcome', sa.String(50), nullable=True),
        sa.Column('total_calls', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('completed_calls', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('failed_calls', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('no_answer_calls', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('avg_call_duration_seconds', sa.Float(), nullable=True),
        sa.Column('median_call_duration_seconds', sa.Float(), nullable=True),
        sa.Column('total_call_duration_seconds', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('avg_audio_quality_score', sa.Float(), nullable=True),
        sa.Column('avg_transcription_quality_score', sa.Float(), nullable=True),
        sa.Column('avg_confidence_score', sa.Float(), nullable=True),
        sa.Column('appointment_booked_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('query_resolved_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('transferred_to_human_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('booking_success_rate', sa.Float(), nullable=True),
        sa.Column('query_resolution_rate', sa.Float(), nullable=True),
        sa.Column('computed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_analytics_voice_tenant_date', 'analytics_voice_call_daily', ['tenant_id', 'date'])
    op.create_index('idx_analytics_voice_intent_date', 'analytics_voice_call_daily', ['detected_intent', 'date'])
    op.create_index('idx_analytics_voice_outcome_date', 'analytics_voice_call_daily', ['call_outcome', 'date'])


def downgrade() -> None:
    """Downgrade schema - Drop all conversation, voice call, and analytics tables."""

    # Drop analytics tables first
    op.drop_table('analytics_voice_call_daily')
    op.drop_table('analytics_communication_daily')
    op.drop_table('analytics_journey_daily')
    op.drop_table('analytics_appointment_daily')

    # Drop voice call related tables
    op.drop_table('voice_call_extractions')
    op.drop_table('voice_call_recordings')
    op.drop_table('voice_call_transcripts')
    op.drop_table('voice_calls')

    # Drop conversation related tables
    op.drop_table('conversation_messages')
    op.drop_table('conversations')

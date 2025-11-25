"""EPIC-015: Provider Collaboration Platform

Revision ID: 015_provider_collaboration
Revises: 014_patient_portal
Create Date: 2024-11-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '015_provider_collaboration'
down_revision = '014_patient_portal'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUMs
    conversation_type = postgresql.ENUM(
        'direct', 'group', 'consultation', 'care_team', 'case_discussion', 'handoff', 'on_call', 'broadcast',
        name='conversation_type', create_type=True
    )
    conversation_type.create(op.get_bind(), checkfirst=True)

    message_type = postgresql.ENUM(
        'text', 'voice', 'image', 'document', 'dicom', 'video', 'system', 'alert',
        name='provider_message_type', create_type=True
    )
    message_type.create(op.get_bind(), checkfirst=True)

    message_priority = postgresql.ENUM(
        'low', 'normal', 'high', 'urgent', 'emergent',
        name='provider_message_priority', create_type=True
    )
    message_priority.create(op.get_bind(), checkfirst=True)

    message_status = postgresql.ENUM(
        'pending', 'sent', 'delivered', 'read', 'failed', 'recalled',
        name='provider_message_status', create_type=True
    )
    message_status.create(op.get_bind(), checkfirst=True)

    presence_status = postgresql.ENUM(
        'online', 'away', 'busy', 'do_not_disturb', 'in_procedure', 'on_call', 'offline',
        name='presence_status', create_type=True
    )
    presence_status.create(op.get_bind(), checkfirst=True)

    consultation_status = postgresql.ENUM(
        'pending', 'accepted', 'declined', 'in_progress', 'awaiting_response', 'completed', 'cancelled', 'expired',
        name='consultation_status', create_type=True
    )
    consultation_status.create(op.get_bind(), checkfirst=True)

    consultation_urgency = postgresql.ENUM(
        'routine', 'urgent', 'emergent', 'stat',
        name='consultation_urgency', create_type=True
    )
    consultation_urgency.create(op.get_bind(), checkfirst=True)

    care_team_role = postgresql.ENUM(
        'attending_physician', 'consulting_physician', 'primary_nurse', 'charge_nurse',
        'care_coordinator', 'case_manager', 'social_worker', 'pharmacist',
        'physical_therapist', 'occupational_therapist', 'dietitian', 'respiratory_therapist',
        'resident', 'medical_student', 'other',
        name='care_team_role', create_type=True
    )
    care_team_role.create(op.get_bind(), checkfirst=True)

    care_team_status = postgresql.ENUM(
        'active', 'inactive', 'discharged', 'transferred',
        name='care_team_status', create_type=True
    )
    care_team_status.create(op.get_bind(), checkfirst=True)

    handoff_status = postgresql.ENUM(
        'scheduled', 'in_progress', 'completed', 'cancelled', 'incomplete',
        name='handoff_status', create_type=True
    )
    handoff_status.create(op.get_bind(), checkfirst=True)

    handoff_type = postgresql.ENUM(
        'shift_change', 'patient_transfer', 'service_transfer', 'escalation', 'temporary_coverage',
        name='handoff_type', create_type=True
    )
    handoff_type.create(op.get_bind(), checkfirst=True)

    on_call_status = postgresql.ENUM(
        'scheduled', 'active', 'completed', 'traded', 'cancelled',
        name='on_call_status', create_type=True
    )
    on_call_status.create(op.get_bind(), checkfirst=True)

    on_call_request_status = postgresql.ENUM(
        'pending', 'acknowledged', 'in_progress', 'resolved', 'escalated', 'timed_out',
        name='on_call_request_status', create_type=True
    )
    on_call_request_status.create(op.get_bind(), checkfirst=True)

    alert_type = postgresql.ENUM(
        'critical_lab', 'vital_sign', 'medication', 'clinical_deterioration', 'care_gap',
        'task_due', 'consult_response', 'handoff_required', 'on_call_request', 'system', 'custom',
        name='clinical_alert_type', create_type=True
    )
    alert_type.create(op.get_bind(), checkfirst=True)

    alert_severity = postgresql.ENUM(
        'info', 'warning', 'critical', 'life_threatening',
        name='alert_severity', create_type=True
    )
    alert_severity.create(op.get_bind(), checkfirst=True)

    alert_status = postgresql.ENUM(
        'active', 'acknowledged', 'snoozed', 'resolved', 'expired', 'escalated',
        name='alert_status', create_type=True
    )
    alert_status.create(op.get_bind(), checkfirst=True)

    case_discussion_type = postgresql.ENUM(
        'clinical_case', 'teaching_case', 'morbidity_mortality', 'tumor_board', 'peer_review', 'grand_rounds',
        name='case_discussion_type', create_type=True
    )
    case_discussion_type.create(op.get_bind(), checkfirst=True)

    vote_type = postgresql.ENUM(
        'agree', 'disagree', 'abstain', 'need_more_info',
        name='vote_type', create_type=True
    )
    vote_type.create(op.get_bind(), checkfirst=True)

    # Create provider_presence table
    op.create_table(
        'provider_presence',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Enum('online', 'away', 'busy', 'do_not_disturb', 'in_procedure', 'on_call', 'offline', name='presence_status'), nullable=True),
        sa.Column('status_message', sa.String(255), nullable=True),
        sa.Column('custom_status', sa.String(100), nullable=True),
        sa.Column('device_type', sa.String(50), nullable=True),
        sa.Column('device_id', sa.String(255), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('location', sa.String(100), nullable=True),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('is_typing_in', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('auto_away_enabled', sa.Boolean(), default=True, nullable=True),
        sa.Column('auto_away_after_minutes', sa.Integer(), default=5, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['provider_id'], ['providers.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('tenant_id', 'provider_id', name='uq_provider_presence')
    )
    op.create_index('ix_provider_presence_tenant', 'provider_presence', ['tenant_id'])
    op.create_index('ix_provider_presence_provider', 'provider_presence', ['provider_id'])
    op.create_index('ix_provider_presence_status', 'provider_presence', ['tenant_id', 'status'])

    # Create provider_conversations table
    op.create_table(
        'provider_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.Enum('direct', 'group', 'consultation', 'care_team', 'case_discussion', 'handoff', 'on_call', 'broadcast', name='conversation_type'), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('consultation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('care_team_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('handoff_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('case_discussion_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('settings', postgresql.JSONB(), default={}, nullable=True),
        sa.Column('is_encrypted', sa.Boolean(), default=True, nullable=True),
        sa.Column('message_retention_days', sa.Integer(), default=90, nullable=True),
        sa.Column('allow_file_sharing', sa.Boolean(), default=True, nullable=True),
        sa.Column('allow_video_calls', sa.Boolean(), default=True, nullable=True),
        sa.Column('is_read_only', sa.Boolean(), default=False, nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=True),
        sa.Column('is_archived', sa.Boolean(), default=False, nullable=True),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_message_preview', sa.String(255), nullable=True),
        sa.Column('message_count', sa.Integer(), default=0, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.ForeignKeyConstraint(['created_by'], ['providers.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_provider_conv_tenant', 'provider_conversations', ['tenant_id'])
    op.create_index('ix_provider_conv_patient', 'provider_conversations', ['tenant_id', 'patient_id'])
    op.create_index('ix_provider_conv_type', 'provider_conversations', ['tenant_id', 'type', 'is_active'])

    # Create conversation_participants table
    op.create_table(
        'conversation_participants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(50), nullable=True),
        sa.Column('care_team_role', sa.Enum('attending_physician', 'consulting_physician', 'primary_nurse', 'charge_nurse', 'care_coordinator', 'case_manager', 'social_worker', 'pharmacist', 'physical_therapist', 'occupational_therapist', 'dietitian', 'respiratory_therapist', 'resident', 'medical_student', 'other', name='care_team_role'), nullable=True),
        sa.Column('notifications_enabled', sa.Boolean(), default=True, nullable=True),
        sa.Column('notification_sound', sa.String(50), default='default', nullable=True),
        sa.Column('muted_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_read_message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('unread_count', sa.Integer(), default=0, nullable=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('left_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=True),
        sa.Column('can_add_members', sa.Boolean(), default=False, nullable=True),
        sa.Column('can_remove_members', sa.Boolean(), default=False, nullable=True),
        sa.Column('can_edit_settings', sa.Boolean(), default=False, nullable=True),
        sa.Column('can_delete_messages', sa.Boolean(), default=False, nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['provider_conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['provider_id'], ['providers.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('conversation_id', 'provider_id', name='uq_conversation_participant')
    )
    op.create_index('ix_conv_participant_conv', 'conversation_participants', ['conversation_id'])
    op.create_index('ix_conv_participant_provider', 'conversation_participants', ['provider_id'])

    # Create provider_messages table
    op.create_table(
        'provider_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('content_encrypted', sa.Boolean(), default=True, nullable=True),
        sa.Column('message_type', sa.Enum('text', 'voice', 'image', 'document', 'dicom', 'video', 'system', 'alert', name='provider_message_type'), nullable=True),
        sa.Column('priority', sa.Enum('low', 'normal', 'high', 'urgent', 'emergent', name='provider_message_priority'), nullable=True),
        sa.Column('attachments', postgresql.JSONB(), default=[], nullable=True),
        sa.Column('dicom_references', postgresql.JSONB(), nullable=True),
        sa.Column('formatted_content', sa.Text(), nullable=True),
        sa.Column('mentions', postgresql.JSONB(), nullable=True),
        sa.Column('patient_references', postgresql.JSONB(), nullable=True),
        sa.Column('reply_to_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('thread_root_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('thread_count', sa.Integer(), default=0, nullable=True),
        sa.Column('status', sa.Enum('pending', 'sent', 'delivered', 'read', 'failed', 'recalled', name='provider_message_status'), nullable=True),
        sa.Column('is_edited', sa.Boolean(), default=False, nullable=True),
        sa.Column('edited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), default=False, nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_recalled', sa.Boolean(), default=False, nullable=True),
        sa.Column('recalled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('recall_reason', sa.String(255), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_scheduled', sa.Boolean(), default=False, nullable=True),
        sa.Column('metadata', postgresql.JSONB(), default={}, nullable=True),
        sa.Column('client_message_id', sa.String(100), nullable=True),
        sa.Column('contains_phi', sa.Boolean(), default=False, nullable=True),
        sa.Column('phi_detected_types', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['conversation_id'], ['provider_conversations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['providers.id']),
        sa.ForeignKeyConstraint(['reply_to_id'], ['provider_messages.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_provider_msg_tenant', 'provider_messages', ['tenant_id'])
    op.create_index('ix_provider_msg_conv', 'provider_messages', ['conversation_id'])
    op.create_index('ix_provider_msg_sender', 'provider_messages', ['sender_id'])
    op.create_index('ix_provider_msg_conv_created', 'provider_messages', ['conversation_id', 'created_at'])
    op.create_index('ix_provider_msg_thread', 'provider_messages', ['thread_root_id'])

    # Create message_receipts table
    op.create_table(
        'message_receipts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('device_type', sa.String(50), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['provider_messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['provider_id'], ['providers.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id', 'provider_id', name='uq_message_receipt')
    )
    op.create_index('ix_message_receipt_msg', 'message_receipts', ['message_id'])
    op.create_index('ix_message_receipt_provider', 'message_receipts', ['provider_id'])

    # Create message_reactions table
    op.create_table(
        'message_reactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('emoji', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['provider_messages.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['provider_id'], ['providers.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('message_id', 'provider_id', 'emoji', name='uq_message_reaction')
    )
    op.create_index('ix_message_reaction_msg', 'message_reactions', ['message_id'])

    # Create consultations table
    op.create_table(
        'consultations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('requesting_provider_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('requesting_service', sa.String(100), nullable=True),
        sa.Column('requesting_department', sa.String(100), nullable=True),
        sa.Column('consultant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('consultant_specialty', sa.String(100), nullable=False),
        sa.Column('preferred_consultant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('urgency', sa.Enum('routine', 'urgent', 'emergent', 'stat', name='consultation_urgency'), nullable=True),
        sa.Column('clinical_question', sa.Text(), nullable=False),
        sa.Column('relevant_history', sa.Text(), nullable=True),
        sa.Column('working_diagnosis', sa.Text(), nullable=True),
        sa.Column('reason_for_consult', sa.Text(), nullable=True),
        sa.Column('attachments', postgresql.JSONB(), default=[], nullable=True),
        sa.Column('lab_references', postgresql.JSONB(), nullable=True),
        sa.Column('imaging_references', postgresql.JSONB(), nullable=True),
        sa.Column('medication_list', postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'accepted', 'declined', 'in_progress', 'awaiting_response', 'completed', 'cancelled', 'expired', name='consultation_status'), nullable=True),
        sa.Column('status_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('response_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expected_response_hours', sa.Integer(), nullable=True),
        sa.Column('first_response_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sla_met', sa.Boolean(), nullable=True),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('accepted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('decline_reason', sa.Text(), nullable=True),
        sa.Column('declined_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completion_notes', sa.Text(), nullable=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('has_report', sa.Boolean(), default=False, nullable=True),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('quality_rating', sa.Integer(), nullable=True),
        sa.Column('quality_feedback', sa.Text(), nullable=True),
        sa.Column('rated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('rated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('billing_code', sa.String(20), nullable=True),
        sa.Column('is_billable', sa.Boolean(), default=True, nullable=True),
        sa.Column('billed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cme_eligible', sa.Boolean(), default=False, nullable=True),
        sa.Column('cme_credit_hours', sa.Numeric(4, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['requesting_provider_id'], ['providers.id']),
        sa.ForeignKeyConstraint(['consultant_id'], ['providers.id']),
        sa.ForeignKeyConstraint(['preferred_consultant_id'], ['providers.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.ForeignKeyConstraint(['accepted_by'], ['providers.id']),
        sa.ForeignKeyConstraint(['rated_by'], ['providers.id']),
        sa.ForeignKeyConstraint(['conversation_id'], ['provider_conversations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_consultation_tenant', 'consultations', ['tenant_id'])
    op.create_index('ix_consultation_requesting', 'consultations', ['requesting_provider_id'])
    op.create_index('ix_consultation_consultant', 'consultations', ['consultant_id', 'status'])
    op.create_index('ix_consultation_patient', 'consultations', ['patient_id'])
    op.create_index('ix_consultation_status', 'consultations', ['tenant_id', 'status', 'urgency'])

    # Create consultation_reports table
    op.create_table(
        'consultation_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('consultation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('impression', sa.Text(), nullable=False),
        sa.Column('recommendations', sa.Text(), nullable=False),
        sa.Column('assessment', sa.Text(), nullable=True),
        sa.Column('plan', sa.Text(), nullable=True),
        sa.Column('follow_up_required', sa.Boolean(), default=False, nullable=True),
        sa.Column('follow_up_instructions', sa.Text(), nullable=True),
        sa.Column('diagnoses', postgresql.JSONB(), nullable=True),
        sa.Column('differential_diagnoses', postgresql.JSONB(), nullable=True),
        sa.Column('recommended_tests', postgresql.JSONB(), nullable=True),
        sa.Column('recommended_procedures', postgresql.JSONB(), nullable=True),
        sa.Column('medication_recommendations', postgresql.JSONB(), nullable=True),
        sa.Column('is_draft', sa.Boolean(), default=True, nullable=True),
        sa.Column('is_signed', sa.Boolean(), default=False, nullable=True),
        sa.Column('signed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('signed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('addendums', postgresql.JSONB(), default=[], nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['consultation_id'], ['consultations.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['author_id'], ['providers.id']),
        sa.ForeignKeyConstraint(['signed_by'], ['providers.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('consultation_id')
    )
    op.create_index('ix_consultation_report_tenant', 'consultation_reports', ['tenant_id'])

    # Create care_teams table
    op.create_table(
        'care_teams',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('team_type', sa.String(50), nullable=True),
        sa.Column('lead_provider_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.Enum('active', 'inactive', 'discharged', 'transferred', name='care_team_status'), nullable=True),
        sa.Column('status_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('care_plan', postgresql.JSONB(), nullable=True),
        sa.Column('care_plan_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('goals', postgresql.JSONB(), default=[], nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('discharged_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.ForeignKeyConstraint(['lead_provider_id'], ['providers.id']),
        sa.ForeignKeyConstraint(['conversation_id'], ['provider_conversations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_care_team_tenant', 'care_teams', ['tenant_id'])
    op.create_index('ix_care_team_patient', 'care_teams', ['tenant_id', 'patient_id', 'status'])

    # Create care_team_members table
    op.create_table(
        'care_team_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('care_team_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.Enum('attending_physician', 'consulting_physician', 'primary_nurse', 'charge_nurse', 'care_coordinator', 'case_manager', 'social_worker', 'pharmacist', 'physical_therapist', 'occupational_therapist', 'dietitian', 'respiratory_therapist', 'resident', 'medical_student', 'other', name='care_team_role'), nullable=False),
        sa.Column('custom_role', sa.String(100), nullable=True),
        sa.Column('responsibilities', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=True),
        sa.Column('is_primary', sa.Boolean(), default=False, nullable=True),
        sa.Column('notifications_enabled', sa.Boolean(), default=True, nullable=True),
        sa.Column('notify_on_updates', sa.Boolean(), default=True, nullable=True),
        sa.Column('notify_on_tasks', sa.Boolean(), default=True, nullable=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('left_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['care_team_id'], ['care_teams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['provider_id'], ['providers.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('care_team_id', 'provider_id', name='uq_care_team_member')
    )
    op.create_index('ix_care_team_member_team', 'care_team_members', ['care_team_id'])
    op.create_index('ix_care_team_member_provider', 'care_team_members', ['provider_id'])

    # Create care_team_tasks table
    op.create_table(
        'care_team_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('care_team_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('assigned_role', sa.Enum('attending_physician', 'consulting_physician', 'primary_nurse', 'charge_nurse', 'care_coordinator', 'case_manager', 'social_worker', 'pharmacist', 'physical_therapist', 'occupational_therapist', 'dietitian', 'respiratory_therapist', 'resident', 'medical_student', 'other', name='care_team_role'), nullable=True),
        sa.Column('priority', sa.Enum('low', 'normal', 'high', 'urgent', 'emergent', name='provider_message_priority'), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reminder_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(20), default='pending', nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('completion_notes', sa.Text(), nullable=True),
        sa.Column('linked_order_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('linked_medication_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['care_team_id'], ['care_teams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['assigned_to'], ['providers.id']),
        sa.ForeignKeyConstraint(['assigned_by'], ['providers.id']),
        sa.ForeignKeyConstraint(['completed_by'], ['providers.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_care_team_task_team', 'care_team_tasks', ['care_team_id'])
    op.create_index('ix_care_team_task_tenant', 'care_team_tasks', ['tenant_id'])
    op.create_index('ix_care_team_task_assigned', 'care_team_tasks', ['assigned_to', 'status'])
    op.create_index('ix_care_team_task_due', 'care_team_tasks', ['due_date', 'status'])

    # Create shift_handoffs table
    op.create_table(
        'shift_handoffs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('outgoing_provider_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('incoming_provider_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('handoff_type', sa.Enum('shift_change', 'patient_transfer', 'service_transfer', 'escalation', 'temporary_coverage', name='handoff_type'), nullable=True),
        sa.Column('service', sa.String(100), nullable=True),
        sa.Column('unit', sa.String(100), nullable=True),
        sa.Column('location', sa.String(100), nullable=True),
        sa.Column('shift_date', sa.Date(), nullable=False),
        sa.Column('scheduled_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('scheduled', 'in_progress', 'completed', 'cancelled', 'incomplete', name='handoff_status'), nullable=True),
        sa.Column('status_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('patient_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('patient_count', sa.Integer(), default=0, nullable=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('audio_recording_url', sa.String(500), nullable=True),
        sa.Column('recording_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('transcription', sa.Text(), nullable=True),
        sa.Column('acknowledged', sa.Boolean(), default=False, nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('signature_outgoing', sa.String(255), nullable=True),
        sa.Column('signature_incoming', sa.String(255), nullable=True),
        sa.Column('quality_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('incident_reported', sa.Boolean(), default=False, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['outgoing_provider_id'], ['providers.id']),
        sa.ForeignKeyConstraint(['incoming_provider_id'], ['providers.id']),
        sa.ForeignKeyConstraint(['conversation_id'], ['provider_conversations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_handoff_tenant', 'shift_handoffs', ['tenant_id'])
    op.create_index('ix_handoff_date', 'shift_handoffs', ['tenant_id', 'shift_date', 'service'])
    op.create_index('ix_handoff_outgoing', 'shift_handoffs', ['outgoing_provider_id', 'shift_date'])
    op.create_index('ix_handoff_incoming', 'shift_handoffs', ['incoming_provider_id', 'shift_date'])

    # Create patient_handoffs table
    op.create_table(
        'patient_handoffs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shift_handoff_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('situation', postgresql.JSONB(), nullable=True),
        sa.Column('background', postgresql.JSONB(), nullable=True),
        sa.Column('assessment', postgresql.JSONB(), nullable=True),
        sa.Column('recommendations', postgresql.JSONB(), nullable=True),
        sa.Column('critical_items', postgresql.JSONB(), default=[], nullable=True),
        sa.Column('has_critical_items', sa.Boolean(), default=False, nullable=True),
        sa.Column('pending_tasks', postgresql.JSONB(), default=[], nullable=True),
        sa.Column('reviewed', sa.Boolean(), default=False, nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('questions_raised', postgresql.JSONB(), default=[], nullable=True),
        sa.Column('questions_resolved', sa.Boolean(), default=True, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['shift_handoff_id'], ['shift_handoffs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_patient_handoff_shift', 'patient_handoffs', ['shift_handoff_id'])
    op.create_index('ix_patient_handoff_patient', 'patient_handoffs', ['patient_id'])

    # Create on_call_schedule table
    op.create_table(
        'on_call_schedule',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('service', sa.String(100), nullable=False),
        sa.Column('specialty', sa.String(100), nullable=True),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('level', sa.Integer(), default=1, nullable=True),
        sa.Column('backup_providers', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('status', sa.Enum('scheduled', 'active', 'completed', 'traded', 'cancelled', name='on_call_status'), nullable=True),
        sa.Column('status_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('original_provider_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('traded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trade_approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['provider_id'], ['providers.id']),
        sa.ForeignKeyConstraint(['original_provider_id'], ['providers.id']),
        sa.ForeignKeyConstraint(['trade_approved_by'], ['providers.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('end_time > start_time', name='check_on_call_time_range')
    )
    op.create_index('ix_on_call_tenant', 'on_call_schedule', ['tenant_id'])
    op.create_index('ix_on_call_provider', 'on_call_schedule', ['provider_id', 'start_time'])
    op.create_index('ix_on_call_active', 'on_call_schedule', ['tenant_id', 'service', 'start_time', 'end_time'])

    # Create on_call_requests table
    op.create_table(
        'on_call_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('service', sa.String(100), nullable=False),
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('requested_by_name', sa.String(255), nullable=True),
        sa.Column('requested_by_unit', sa.String(100), nullable=True),
        sa.Column('callback_number', sa.String(20), nullable=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('patient_name', sa.String(255), nullable=True),
        sa.Column('patient_mrn', sa.String(50), nullable=True),
        sa.Column('patient_location', sa.String(100), nullable=True),
        sa.Column('urgency', sa.Enum('routine', 'urgent', 'emergent', 'stat', name='consultation_urgency'), nullable=True),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('brief_description', sa.String(500), nullable=True),
        sa.Column('on_call_provider_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('schedule_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.Enum('pending', 'acknowledged', 'in_progress', 'resolved', 'escalated', 'timed_out', name='on_call_request_status'), nullable=True),
        sa.Column('status_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('response_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('escalation_level', sa.Integer(), default=0, nullable=True),
        sa.Column('escalated_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('escalated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('escalation_reason', sa.String(255), nullable=True),
        sa.Column('sla_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sla_met', sa.Boolean(), nullable=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['requested_by'], ['providers.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.ForeignKeyConstraint(['on_call_provider_id'], ['providers.id']),
        sa.ForeignKeyConstraint(['schedule_id'], ['on_call_schedule.id']),
        sa.ForeignKeyConstraint(['escalated_to'], ['providers.id']),
        sa.ForeignKeyConstraint(['conversation_id'], ['provider_conversations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_on_call_request_tenant', 'on_call_requests', ['tenant_id'])
    op.create_index('ix_on_call_request_status', 'on_call_requests', ['tenant_id', 'service', 'status'])
    op.create_index('ix_on_call_request_provider', 'on_call_requests', ['on_call_provider_id'])
    op.create_index('ix_on_call_request_patient', 'on_call_requests', ['patient_id'])

    # Create clinical_alerts table
    op.create_table(
        'clinical_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('alert_type', sa.Enum('critical_lab', 'vital_sign', 'medication', 'clinical_deterioration', 'care_gap', 'task_due', 'consult_response', 'handoff_required', 'on_call_request', 'system', 'custom', name='clinical_alert_type'), nullable=False),
        sa.Column('severity', sa.Enum('info', 'warning', 'critical', 'life_threatening', name='alert_severity'), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('clinical_data', postgresql.JSONB(), nullable=True),
        sa.Column('threshold_violated', sa.String(255), nullable=True),
        sa.Column('reference_range', sa.String(100), nullable=True),
        sa.Column('source_type', sa.String(50), nullable=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('recipient_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('recipient_role', sa.String(50), nullable=True),
        sa.Column('care_team_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.Enum('active', 'acknowledged', 'snoozed', 'resolved', 'expired', 'escalated', name='alert_status'), nullable=True),
        sa.Column('status_updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledged_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('acknowledgment_note', sa.Text(), nullable=True),
        sa.Column('snoozed_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('snooze_count', sa.Integer(), default=0, nullable=True),
        sa.Column('max_snooze_count', sa.Integer(), default=3, nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolution_note', sa.Text(), nullable=True),
        sa.Column('resolution_action', sa.String(100), nullable=True),
        sa.Column('escalation_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('escalated', sa.Boolean(), default=False, nullable=True),
        sa.Column('escalated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('escalated_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('delivery_channels', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('delivered_via', postgresql.JSONB(), default={}, nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.ForeignKeyConstraint(['recipient_id'], ['providers.id']),
        sa.ForeignKeyConstraint(['care_team_id'], ['care_teams.id']),
        sa.ForeignKeyConstraint(['acknowledged_by'], ['providers.id']),
        sa.ForeignKeyConstraint(['resolved_by'], ['providers.id']),
        sa.ForeignKeyConstraint(['escalated_to'], ['providers.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_clinical_alert_tenant', 'clinical_alerts', ['tenant_id'])
    op.create_index('ix_clinical_alert_recipient', 'clinical_alerts', ['recipient_id', 'status'])
    op.create_index('ix_clinical_alert_patient', 'clinical_alerts', ['patient_id', 'status'])
    op.create_index('ix_clinical_alert_severity', 'clinical_alerts', ['tenant_id', 'severity', 'status'])

    # Create alert_rules table
    op.create_table(
        'alert_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('alert_type', sa.Enum('critical_lab', 'vital_sign', 'medication', 'clinical_deterioration', 'care_gap', 'task_due', 'consult_response', 'handoff_required', 'on_call_request', 'system', 'custom', name='clinical_alert_type'), nullable=False),
        sa.Column('severity', sa.Enum('info', 'warning', 'critical', 'life_threatening', name='alert_severity'), nullable=True),
        sa.Column('trigger_conditions', postgresql.JSONB(), nullable=False),
        sa.Column('trigger_logic', sa.String(10), default='AND', nullable=True),
        sa.Column('applies_to_all', sa.Boolean(), default=True, nullable=True),
        sa.Column('applies_to_services', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('applies_to_departments', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('patient_criteria', postgresql.JSONB(), nullable=True),
        sa.Column('default_recipients', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('notify_care_team', sa.Boolean(), default=True, nullable=True),
        sa.Column('notify_attending', sa.Boolean(), default=True, nullable=True),
        sa.Column('escalation_path', postgresql.JSONB(), nullable=True),
        sa.Column('delivery_channels', postgresql.ARRAY(sa.String()), default=['in_app'], nullable=True),
        sa.Column('quiet_hours_start', sa.Time(), nullable=True),
        sa.Column('quiet_hours_end', sa.Time(), nullable=True),
        sa.Column('respect_quiet_hours', sa.Boolean(), default=False, nullable=True),
        sa.Column('throttle_minutes', sa.Integer(), default=0, nullable=True),
        sa.Column('max_per_day', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=True),
        sa.Column('is_system', sa.Boolean(), default=False, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['created_by'], ['providers.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_alert_rules_tenant', 'alert_rules', ['tenant_id'])

    # Create case_discussions table
    op.create_table(
        'case_discussions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('discussion_type', sa.Enum('clinical_case', 'teaching_case', 'morbidity_mortality', 'tumor_board', 'peer_review', 'grand_rounds', name='case_discussion_type'), nullable=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_anonymized', sa.Boolean(), default=False, nullable=True),
        sa.Column('presenter_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('presenting_service', sa.String(100), nullable=True),
        sa.Column('case_presentation', postgresql.JSONB(), nullable=True),
        sa.Column('presentation_template', sa.String(50), nullable=True),
        sa.Column('clinical_question', sa.Text(), nullable=True),
        sa.Column('decision_required', sa.Boolean(), default=False, nullable=True),
        sa.Column('attachments', postgresql.JSONB(), default=[], nullable=True),
        sa.Column('references', postgresql.JSONB(), default=[], nullable=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('is_recurring', sa.Boolean(), default=False, nullable=True),
        sa.Column('recurrence_rule', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), default='scheduled', nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('consensus_reached', sa.Boolean(), nullable=True),
        sa.Column('outcome_summary', sa.Text(), nullable=True),
        sa.Column('action_items', postgresql.JSONB(), default=[], nullable=True),
        sa.Column('follow_up_date', sa.Date(), nullable=True),
        sa.Column('learning_objectives', postgresql.JSONB(), default=[], nullable=True),
        sa.Column('cme_eligible', sa.Boolean(), default=False, nullable=True),
        sa.Column('cme_credit_hours', sa.Numeric(4, 2), nullable=True),
        sa.Column('is_public', sa.Boolean(), default=False, nullable=True),
        sa.Column('invited_services', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('invited_providers', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.ForeignKeyConstraint(['presenter_id'], ['providers.id']),
        sa.ForeignKeyConstraint(['conversation_id'], ['provider_conversations.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_case_discussion_tenant', 'case_discussions', ['tenant_id'])
    op.create_index('ix_case_discussion_patient', 'case_discussions', ['patient_id'])
    op.create_index('ix_case_discussion_presenter', 'case_discussions', ['presenter_id'])

    # Create case_discussion_participants table
    op.create_table(
        'case_discussion_participants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('discussion_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(50), nullable=True),
        sa.Column('invited_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('rsvp_status', sa.String(20), nullable=True),
        sa.Column('attended', sa.Boolean(), default=False, nullable=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('left_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('contributed', sa.Boolean(), default=False, nullable=True),
        sa.Column('contribution_summary', sa.Text(), nullable=True),
        sa.Column('cme_claimed', sa.Boolean(), default=False, nullable=True),
        sa.Column('cme_claimed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['discussion_id'], ['case_discussions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['provider_id'], ['providers.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('discussion_id', 'provider_id', name='uq_case_discussion_participant')
    )
    op.create_index('ix_case_disc_participant_disc', 'case_discussion_participants', ['discussion_id'])
    op.create_index('ix_case_disc_participant_provider', 'case_discussion_participants', ['provider_id'])

    # Create case_discussion_votes table
    op.create_table(
        'case_discussion_votes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('discussion_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question', sa.String(500), nullable=True),
        sa.Column('vote', sa.Enum('agree', 'disagree', 'abstain', 'need_more_info', name='vote_type'), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['discussion_id'], ['case_discussions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['provider_id'], ['providers.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_case_disc_vote_disc', 'case_discussion_votes', ['discussion_id'])

    # Create collaboration_audit_logs table
    op.create_table(
        'collaboration_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('provider_name', sa.String(255), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('action_category', sa.String(50), nullable=True),
        sa.Column('action_description', sa.Text(), nullable=True),
        sa.Column('entity_type', sa.String(50), nullable=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('details', postgresql.JSONB(), default={}, nullable=True),
        sa.Column('old_values', postgresql.JSONB(), nullable=True),
        sa.Column('new_values', postgresql.JSONB(), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('device_type', sa.String(50), nullable=True),
        sa.Column('success', sa.Boolean(), default=True, nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['provider_id'], ['providers.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_collab_audit_tenant', 'collaboration_audit_logs', ['tenant_id'])
    op.create_index('ix_collab_audit_action', 'collaboration_audit_logs', ['tenant_id', 'action_category', 'created_at'])
    op.create_index('ix_collab_audit_provider', 'collaboration_audit_logs', ['provider_id', 'created_at'])
    op.create_index('ix_collab_audit_entity', 'collaboration_audit_logs', ['entity_id'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('collaboration_audit_logs')
    op.drop_table('case_discussion_votes')
    op.drop_table('case_discussion_participants')
    op.drop_table('case_discussions')
    op.drop_table('alert_rules')
    op.drop_table('clinical_alerts')
    op.drop_table('on_call_requests')
    op.drop_table('on_call_schedule')
    op.drop_table('patient_handoffs')
    op.drop_table('shift_handoffs')
    op.drop_table('care_team_tasks')
    op.drop_table('care_team_members')
    op.drop_table('care_teams')
    op.drop_table('consultation_reports')
    op.drop_table('consultations')
    op.drop_table('message_reactions')
    op.drop_table('message_receipts')
    op.drop_table('provider_messages')
    op.drop_table('conversation_participants')
    op.drop_table('provider_conversations')
    op.drop_table('provider_presence')

    # Drop ENUMs
    op.execute('DROP TYPE IF EXISTS vote_type')
    op.execute('DROP TYPE IF EXISTS case_discussion_type')
    op.execute('DROP TYPE IF EXISTS alert_status')
    op.execute('DROP TYPE IF EXISTS alert_severity')
    op.execute('DROP TYPE IF EXISTS clinical_alert_type')
    op.execute('DROP TYPE IF EXISTS on_call_request_status')
    op.execute('DROP TYPE IF EXISTS on_call_status')
    op.execute('DROP TYPE IF EXISTS handoff_type')
    op.execute('DROP TYPE IF EXISTS handoff_status')
    op.execute('DROP TYPE IF EXISTS care_team_status')
    op.execute('DROP TYPE IF EXISTS care_team_role')
    op.execute('DROP TYPE IF EXISTS consultation_urgency')
    op.execute('DROP TYPE IF EXISTS consultation_status')
    op.execute('DROP TYPE IF EXISTS presence_status')
    op.execute('DROP TYPE IF EXISTS provider_message_status')
    op.execute('DROP TYPE IF EXISTS provider_message_priority')
    op.execute('DROP TYPE IF EXISTS provider_message_type')
    op.execute('DROP TYPE IF EXISTS conversation_type')

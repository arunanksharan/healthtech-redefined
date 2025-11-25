"""AI Platform Tables

Revision ID: 006_ai_platform
Revises: 005_billing_platform
Create Date: 2024-11-25

EPIC-009: Core AI Integration

Tables:
- ai_request_logs: AI request logging for monitoring
- ai_conversations: Conversational AI sessions
- ai_conversation_messages: Individual conversation messages
- medical_knowledge_documents: Knowledge base documents
- medical_knowledge_chunks: Document chunks for vector search
- phi_audit_logs: PHI access audit trail
- patient_ai_consents: Patient consent for AI processing
- ai_experiments: A/B testing experiments
- prompt_templates: Reusable prompt templates
- ai_cost_summaries: Daily cost aggregations
- ai_cost_alerts: Cost alert configurations
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '006_ai_platform'
down_revision = '005_billing_platform'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==================== Enums ====================

    # AI Provider Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE ai_provider_type AS ENUM (
                'openai', 'anthropic', 'azure_openai', 'local', 'huggingface'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # AI Request Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE ai_request_type AS ENUM (
                'chat_completion', 'streaming', 'embedding', 'ner',
                'classification', 'triage', 'documentation',
                'semantic_search', 'function_call'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Conversation Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE conversation_status AS ENUM (
                'active', 'paused', 'waiting_input', 'completed', 'escalated'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Conversation Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE ai_conversation_type AS ENUM (
                'general_inquiry', 'appointment_booking', 'symptom_assessment',
                'medication_question', 'billing_inquiry', 'prescription_refill',
                'lab_results', 'provider_message'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Document Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE knowledge_document_type AS ENUM (
                'clinical_guideline', 'drug_info', 'medical_literature',
                'protocol', 'policy', 'faq', 'patient_education',
                'procedure', 'diagnosis', 'treatment'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Evidence Level
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE evidence_level AS ENUM ('A', 'B', 'C', 'D', 'N/A');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # PHI Action Type
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE phi_action_type AS ENUM (
                'detect', 'deidentify', 'reidentify', 'access',
                'consent_record', 'consent_revoke'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Experiment Status
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE experiment_status AS ENUM (
                'draft', 'running', 'paused', 'completed'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ==================== AI Request Logs ====================

    op.create_table(
        'ai_request_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('request_type', sa.Enum('chat_completion', 'streaming', 'embedding', 'ner',
                                          'classification', 'triage', 'documentation',
                                          'semantic_search', 'function_call',
                                          name='ai_request_type'), nullable=False),
        sa.Column('provider', sa.Enum('openai', 'anthropic', 'azure_openai', 'local', 'huggingface',
                                      name='ai_provider_type'), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('prompt_hash', sa.String(64), nullable=False),
        sa.Column('input_tokens', sa.Integer, default=0),
        sa.Column('output_tokens', sa.Integer, default=0),
        sa.Column('total_tokens', sa.Integer, default=0),
        sa.Column('latency_ms', sa.Float, default=0),
        sa.Column('time_to_first_token_ms', sa.Float, nullable=True),
        sa.Column('finish_reason', sa.String(50), default='stop'),
        sa.Column('estimated_cost_usd', sa.Float, default=0),
        sa.Column('success', sa.Boolean, default=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('error_type', sa.String(100), nullable=True),
        sa.Column('confidence_score', sa.Float, nullable=True),
        sa.Column('quality_rating', sa.String(20), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('feature', sa.String(50), nullable=True),
        sa.Column('experiment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('variant', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_ai_request_logs_tenant_id', 'ai_request_logs', ['tenant_id'])
    op.create_index('ix_ai_request_logs_tenant_created', 'ai_request_logs', ['tenant_id', 'created_at'])
    op.create_index('ix_ai_request_logs_conversation_id', 'ai_request_logs', ['conversation_id'])
    op.create_index('ix_ai_request_logs_model', 'ai_request_logs', ['model'])
    op.create_index('ix_ai_request_logs_request_type', 'ai_request_logs', ['request_type'])
    op.create_index('ix_ai_request_logs_experiment_id', 'ai_request_logs', ['experiment_id'])

    # ==================== AI Conversations ====================

    op.create_table(
        'ai_conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_type', sa.Enum('general_inquiry', 'appointment_booking',
                                               'symptom_assessment', 'medication_question',
                                               'billing_inquiry', 'prescription_refill',
                                               'lab_results', 'provider_message',
                                               name='ai_conversation_type'), nullable=False),
        sa.Column('status', sa.Enum('active', 'paused', 'waiting_input', 'completed', 'escalated',
                                    name='conversation_status'), default='active'),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('assigned_agent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('channel', sa.String(50), default='web'),
        sa.Column('language', sa.String(10), default='en'),
        sa.Column('context', postgresql.JSONB, default={}),
        sa.Column('turn_count', sa.Integer, default=0),
        sa.Column('total_tokens_used', sa.Integer, default=0),
        sa.Column('total_cost_usd', sa.Float, default=0),
        sa.Column('escalation_reason', sa.Text, nullable=True),
        sa.Column('escalated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('satisfaction_rating', sa.Integer, nullable=True),
        sa.Column('feedback', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index('ix_ai_conversations_tenant_id', 'ai_conversations', ['tenant_id'])
    op.create_index('ix_ai_conversations_tenant_status', 'ai_conversations', ['tenant_id', 'status'])
    op.create_index('ix_ai_conversations_patient_id', 'ai_conversations', ['patient_id'])

    # ==================== AI Conversation Messages ====================

    op.create_table(
        'ai_conversation_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('ai_conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('intent_type', sa.String(50), nullable=True),
        sa.Column('intent_confidence', sa.Float, nullable=True),
        sa.Column('intent_entities', postgresql.JSONB, nullable=True),
        sa.Column('model_used', sa.String(100), nullable=True),
        sa.Column('tokens_used', sa.Integer, nullable=True),
        sa.Column('latency_ms', sa.Float, nullable=True),
        sa.Column('function_name', sa.String(100), nullable=True),
        sa.Column('function_args', postgresql.JSONB, nullable=True),
        sa.Column('function_result', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_ai_conversation_messages_conversation', 'ai_conversation_messages',
                    ['conversation_id', 'created_at'])

    # ==================== Medical Knowledge Documents ====================

    op.create_table(
        'medical_knowledge_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('document_type', sa.Enum('clinical_guideline', 'drug_info', 'medical_literature',
                                           'protocol', 'policy', 'faq', 'patient_education',
                                           'procedure', 'diagnosis', 'treatment',
                                           name='knowledge_document_type'), nullable=False),
        sa.Column('specialty', sa.String(100), nullable=True),
        sa.Column('condition_codes', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('procedure_codes', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('snomed_codes', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('drug_codes', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('keywords', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('source', sa.String(500), nullable=True),
        sa.Column('source_url', sa.String(1000), nullable=True),
        sa.Column('author', sa.String(200), nullable=True),
        sa.Column('publication_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('evidence_level', sa.Enum('A', 'B', 'C', 'D', 'N/A', name='evidence_level'),
                  default='N/A'),
        sa.Column('is_indexed', sa.Boolean, default=False),
        sa.Column('indexed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('chunk_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('ix_knowledge_docs_tenant_id', 'medical_knowledge_documents', ['tenant_id'])
    op.create_index('ix_knowledge_docs_tenant_type', 'medical_knowledge_documents',
                    ['tenant_id', 'document_type'])
    op.create_index('ix_knowledge_docs_specialty', 'medical_knowledge_documents', ['specialty'])

    # ==================== Medical Knowledge Chunks ====================

    op.create_table(
        'medical_knowledge_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('document_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('medical_knowledge_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('text', sa.Text, nullable=False),
        sa.Column('chunk_index', sa.Integer, nullable=False),
        sa.Column('start_offset', sa.Integer, nullable=False),
        sa.Column('end_offset', sa.Integer, nullable=False),
        sa.Column('embedding', postgresql.JSONB, nullable=True),  # In production, use pgvector
        sa.Column('metadata', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_knowledge_chunks_document', 'medical_knowledge_chunks',
                    ['document_id', 'chunk_index'])

    # ==================== PHI Audit Logs ====================

    op.create_table(
        'phi_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.Enum('detect', 'deidentify', 'reidentify', 'access',
                                    'consent_record', 'consent_revoke',
                                    name='phi_action_type'), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('service_name', sa.String(100), nullable=True),
        sa.Column('phi_types_detected', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('phi_count', sa.Integer, default=0),
        sa.Column('consent_verified', sa.Boolean, default=False),
        sa.Column('consent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reason', sa.Text, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_index('ix_phi_audit_logs_tenant_id', 'phi_audit_logs', ['tenant_id'])
    op.create_index('ix_phi_audit_logs_tenant_action', 'phi_audit_logs', ['tenant_id', 'action'])
    op.create_index('ix_phi_audit_logs_created_at', 'phi_audit_logs', ['created_at'])

    # ==================== Patient AI Consents ====================

    op.create_table(
        'patient_ai_consents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('purpose', sa.String(100), nullable=False),
        sa.Column('granted', sa.Boolean, default=True),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('allowed_phi_types', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('allowed_uses', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('revoked', sa.Boolean, default=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('ix_patient_ai_consents_tenant_id', 'patient_ai_consents', ['tenant_id'])
    op.create_index('ix_patient_ai_consents_patient_id', 'patient_ai_consents', ['patient_id'])
    op.create_unique_constraint('uq_patient_consent_purpose', 'patient_ai_consents',
                                ['tenant_id', 'patient_id', 'purpose'])

    # ==================== AI Experiments ====================

    op.create_table(
        'ai_experiments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('status', sa.Enum('draft', 'running', 'paused', 'completed',
                                    name='experiment_status'), default='draft'),
        sa.Column('variants', postgresql.JSONB, nullable=False),
        sa.Column('traffic_split', postgresql.JSONB, nullable=False),
        sa.Column('primary_metric', sa.String(100), nullable=True),
        sa.Column('secondary_metrics', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('results', postgresql.JSONB, default={}),
        sa.Column('winning_variant', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index('ix_ai_experiments_tenant_id', 'ai_experiments', ['tenant_id'])
    op.create_index('ix_ai_experiments_tenant_status', 'ai_experiments', ['tenant_id', 'status'])

    # ==================== Prompt Templates ====================

    op.create_table(
        'prompt_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('version', sa.Integer, default=1),
        sa.Column('system_prompt', sa.Text, nullable=False),
        sa.Column('user_template', sa.Text, nullable=False),
        sa.Column('variables', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('default_model', sa.String(100), nullable=True),
        sa.Column('default_temperature', sa.Float, default=0.7),
        sa.Column('default_max_tokens', sa.Integer, default=1000),
        sa.Column('use_count', sa.Integer, default=0),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('ix_prompt_templates_tenant_id', 'prompt_templates', ['tenant_id'])
    op.create_index('ix_prompt_templates_category', 'prompt_templates', ['category'])
    op.create_unique_constraint('uq_prompt_template_name_version', 'prompt_templates',
                                ['tenant_id', 'name', 'version'])

    # ==================== AI Cost Summaries ====================

    op.create_table(
        'ai_cost_summaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('summary_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_input_tokens', sa.Integer, default=0),
        sa.Column('total_output_tokens', sa.Integer, default=0),
        sa.Column('total_tokens', sa.Integer, default=0),
        sa.Column('total_cost_usd', sa.Float, default=0),
        sa.Column('cost_by_model', postgresql.JSONB, default={}),
        sa.Column('cost_by_feature', postgresql.JSONB, default={}),
        sa.Column('total_requests', sa.Integer, default=0),
        sa.Column('successful_requests', sa.Integer, default=0),
        sa.Column('failed_requests', sa.Integer, default=0),
        sa.Column('avg_latency_ms', sa.Float, default=0),
        sa.Column('p95_latency_ms', sa.Float, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('ix_ai_cost_summaries_tenant_id', 'ai_cost_summaries', ['tenant_id'])
    op.create_index('ix_ai_cost_summaries_date', 'ai_cost_summaries', ['summary_date'])
    op.create_unique_constraint('uq_cost_summary_tenant_date', 'ai_cost_summaries',
                                ['tenant_id', 'summary_date'])

    # ==================== AI Cost Alerts ====================

    op.create_table(
        'ai_cost_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('threshold_usd', sa.Float, nullable=False),
        sa.Column('period', sa.String(20), nullable=False),
        sa.Column('notify_emails', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('notify_webhook_url', sa.String(1000), nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trigger_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_index('ix_ai_cost_alerts_tenant_id', 'ai_cost_alerts', ['tenant_id'])
    op.create_index('ix_ai_cost_alerts_tenant_active', 'ai_cost_alerts', ['tenant_id', 'is_active'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('ai_cost_alerts')
    op.drop_table('ai_cost_summaries')
    op.drop_table('prompt_templates')
    op.drop_table('ai_experiments')
    op.drop_table('patient_ai_consents')
    op.drop_table('phi_audit_logs')
    op.drop_table('medical_knowledge_chunks')
    op.drop_table('medical_knowledge_documents')
    op.drop_table('ai_conversation_messages')
    op.drop_table('ai_conversations')
    op.drop_table('ai_request_logs')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS experiment_status')
    op.execute('DROP TYPE IF EXISTS phi_action_type')
    op.execute('DROP TYPE IF EXISTS evidence_level')
    op.execute('DROP TYPE IF EXISTS knowledge_document_type')
    op.execute('DROP TYPE IF EXISTS ai_conversation_type')
    op.execute('DROP TYPE IF EXISTS conversation_status')
    op.execute('DROP TYPE IF EXISTS ai_request_type')
    op.execute('DROP TYPE IF EXISTS ai_provider_type')

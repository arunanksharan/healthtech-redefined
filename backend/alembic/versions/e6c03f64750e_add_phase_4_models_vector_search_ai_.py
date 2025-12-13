"""Add Phase 4 models: Vector search, AI agents, Clinical intake

Revision ID: e6c03f64750e
Revises:
Create Date: 2025-11-19 00:18:30.685432

This migration adds 12 new tables for Phase 4 functionality:
- Vector Search: text_chunk (1 table)
- AI Agents: tool_run (1 table)
- Clinical Intake: intake_session + 9 related tables (10 tables total)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = 'e6c03f64750e'
down_revision: Union[str, Sequence[str], None] = '024_production_readiness'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create Phase 4 tables for:
    - Vector semantic search
    - AI agent tool execution tracking
    - Clinical intake data collection
    """

    # ========== Vector Search Module ==========

    # Create text_chunk table
    op.create_table(
        'text_chunk',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('source_type', sa.String(32), nullable=False, index=True),
        sa.Column('source_id', sa.String(64), nullable=False, index=True),
        sa.Column('patient_id', UUID(as_uuid=True), sa.ForeignKey('patients.id'), index=True),
        sa.Column('locator', JSONB),
        sa.Column('text', sa.Text, nullable=False),
        sa.Column('chunk_index', sa.Integer, default=0, nullable=False),
        sa.Column('embedding', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
    )

    # ========== AI Agents Module ==========

    # Create tool_run table
    op.create_table(
        'tool_run',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('tool', sa.String(64), nullable=False, index=True),
        sa.Column('inputs', JSONB, nullable=False),
        sa.Column('outputs', JSONB),
        sa.Column('success', sa.Boolean, default=True, nullable=False, index=True),
        sa.Column('error', sa.String(400)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # ========== Clinical Intake Module ==========

    # Create intake_session table
    op.create_table(
        'intake_session',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('patient_id', UUID(as_uuid=True), sa.ForeignKey('patients.id'), index=True),
        sa.Column('conversation_id', UUID(as_uuid=True), index=True),
        sa.Column('status', sa.String(16), default='open', nullable=False, index=True),
        sa.Column('context', JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
    )

    # Create intake_summary table
    op.create_table(
        'intake_summary',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('intake_session.id'), nullable=False, index=True),
        sa.Column('text', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create intake_chief_complaint table
    op.create_table(
        'intake_chief_complaint',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('intake_session.id'), nullable=False, index=True),
        sa.Column('text', sa.Text, nullable=False),
        sa.Column('codes', JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create intake_symptom table
    op.create_table(
        'intake_symptom',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('intake_session.id'), nullable=False, index=True),
        sa.Column('client_item_id', sa.String(64), index=True),
        sa.Column('code', JSONB),
        sa.Column('onset', sa.String(32)),
        sa.Column('duration', sa.String(32)),
        sa.Column('severity', sa.String(32)),
        sa.Column('frequency', sa.String(32)),
        sa.Column('laterality', sa.String(32)),
        sa.Column('notes', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create intake_allergy table
    op.create_table(
        'intake_allergy',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('intake_session.id'), nullable=False, index=True),
        sa.Column('client_item_id', sa.String(64), index=True),
        sa.Column('substance', sa.String(120), nullable=False),
        sa.Column('reaction', sa.String(120)),
        sa.Column('severity', sa.String(32)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create intake_medication table
    op.create_table(
        'intake_medication',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('intake_session.id'), nullable=False, index=True),
        sa.Column('client_item_id', sa.String(64), index=True),
        sa.Column('name', sa.String(120), nullable=False),
        sa.Column('dose', sa.String(120)),
        sa.Column('schedule', sa.String(120)),
        sa.Column('adherence', sa.String(64)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create intake_condition_history table
    op.create_table(
        'intake_condition_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('intake_session.id'), nullable=False, index=True),
        sa.Column('client_item_id', sa.String(64), index=True),
        sa.Column('condition', sa.String(160), nullable=False),
        sa.Column('status', sa.String(32)),
        sa.Column('year_or_age', sa.String(32)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create intake_family_history table
    op.create_table(
        'intake_family_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('intake_session.id'), nullable=False, index=True),
        sa.Column('client_item_id', sa.String(64), index=True),
        sa.Column('relative', sa.String(64), nullable=False),
        sa.Column('condition', sa.String(160), nullable=False),
        sa.Column('age_of_onset', sa.String(32)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create intake_social_history table
    op.create_table(
        'intake_social_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('intake_session.id'), nullable=False, index=True),
        sa.Column('data', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create intake_note table
    op.create_table(
        'intake_note',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', UUID(as_uuid=True), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('session_id', UUID(as_uuid=True), sa.ForeignKey('intake_session.id'), nullable=False, index=True),
        sa.Column('text', sa.Text, nullable=False),
        sa.Column('visibility', sa.String(16), default='internal', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    """
    Drop all Phase 4 tables in reverse order to respect foreign key constraints.
    """
    # Drop intake tables (in reverse order)
    op.drop_table('intake_note')
    op.drop_table('intake_social_history')
    op.drop_table('intake_family_history')
    op.drop_table('intake_condition_history')
    op.drop_table('intake_medication')
    op.drop_table('intake_allergy')
    op.drop_table('intake_symptom')
    op.drop_table('intake_chief_complaint')
    op.drop_table('intake_summary')
    op.drop_table('intake_session')

    # Drop agents tables
    op.drop_table('tool_run')

    # Drop vector search tables
    op.drop_table('text_chunk')

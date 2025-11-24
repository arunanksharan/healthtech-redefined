"""add_fhir_resource_tables

Revision ID: 001fhir001
Revises: f548902ab172
Create Date: 2024-11-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001fhir001'
down_revision: Union[str, Sequence[str], None] = 'f548902ab172'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add FHIR R4 resource storage tables."""

    # ============================================================================
    # FHIR RESOURCES TABLE
    # ============================================================================
    op.create_table(
        'fhir_resources',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('fhir_id', sa.String(64), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('resource_data', postgresql.JSONB(), nullable=False),
        sa.Column('search_tokens', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('search_strings', postgresql.TSVECTOR(), nullable=True),
        sa.Column('deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE')
    )

    # Create indexes for FHIR resources
    op.create_index(
        'idx_fhir_resources_unique',
        'fhir_resources',
        ['tenant_id', 'resource_type', 'fhir_id'],
        unique=True,
        postgresql_where=sa.text('deleted = false')
    )
    op.create_index('idx_fhir_resources_tenant_type', 'fhir_resources', ['tenant_id', 'resource_type'])
    op.create_index('idx_fhir_resources_fhir_id', 'fhir_resources', ['fhir_id'])
    op.create_index('idx_fhir_resources_type', 'fhir_resources', ['resource_type'])
    op.create_index('idx_fhir_resources_deleted', 'fhir_resources', ['deleted'])
    op.create_index('idx_fhir_resources_last_updated', 'fhir_resources', ['last_updated'])

    # GIN indexes for JSONB search optimization
    op.create_index('idx_fhir_resources_data', 'fhir_resources', ['resource_data'], postgresql_using='gin')
    op.create_index('idx_fhir_resources_search_tokens', 'fhir_resources', ['search_tokens'], postgresql_using='gin')

    # Full-text search index
    op.create_index('idx_fhir_resources_search_strings', 'fhir_resources', ['search_strings'], postgresql_using='gin')

    # ============================================================================
    # FHIR RESOURCE HISTORY TABLE
    # ============================================================================
    op.create_table(
        'fhir_resource_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('fhir_id', sa.String(64), nullable=False),
        sa.Column('version_id', sa.Integer(), nullable=False),
        sa.Column('resource_data', postgresql.JSONB(), nullable=False),
        sa.Column('operation', sa.String(10), nullable=False),
        sa.Column('changed_by', sa.String(255), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE')
    )

    # Create indexes for FHIR resource history
    op.create_index('idx_fhir_history_resource', 'fhir_resource_history', ['resource_id'])
    op.create_index('idx_fhir_history_tenant_type_id', 'fhir_resource_history', ['tenant_id', 'resource_type', 'fhir_id'])
    op.create_index('idx_fhir_history_version', 'fhir_resource_history', ['resource_id', 'version_id'])
    op.create_index('idx_fhir_history_changed_at', 'fhir_resource_history', ['changed_at'])

    # ============================================================================
    # FHIR CODE SYSTEMS TABLE
    # ============================================================================
    op.create_table(
        'fhir_code_systems',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('url', sa.String(255), nullable=False),
        sa.Column('version', sa.String(50), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('content', sa.String(20), nullable=False),
        sa.Column('count', sa.Integer(), nullable=True),
        sa.Column('resource_data', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE')
    )

    # Create indexes for code systems
    op.create_index('idx_fhir_codesystems_tenant', 'fhir_code_systems', ['tenant_id'])
    op.create_index('idx_fhir_codesystems_url', 'fhir_code_systems', ['url'])
    op.create_index('idx_fhir_codesystems_status', 'fhir_code_systems', ['status'])

    # ============================================================================
    # FHIR VALUE SETS TABLE
    # ============================================================================
    op.create_table(
        'fhir_value_sets',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('url', sa.String(255), nullable=False),
        sa.Column('version', sa.String(50), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('expansion_data', postgresql.JSONB(), nullable=True),
        sa.Column('expansion_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resource_data', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE')
    )

    # Create indexes for value sets
    op.create_index('idx_fhir_valuesets_tenant', 'fhir_value_sets', ['tenant_id'])
    op.create_index('idx_fhir_valuesets_url', 'fhir_value_sets', ['url'])
    op.create_index('idx_fhir_valuesets_status', 'fhir_value_sets', ['status'])

    # ============================================================================
    # FHIR CONCEPT MAPS TABLE
    # ============================================================================
    op.create_table(
        'fhir_concept_maps',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('url', sa.String(255), nullable=False),
        sa.Column('version', sa.String(50), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('title', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('source_url', sa.String(255), nullable=True),
        sa.Column('target_url', sa.String(255), nullable=True),
        sa.Column('resource_data', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE')
    )

    # Create indexes for concept maps
    op.create_index('idx_fhir_conceptmaps_tenant', 'fhir_concept_maps', ['tenant_id'])
    op.create_index('idx_fhir_conceptmaps_url', 'fhir_concept_maps', ['url'])
    op.create_index('idx_fhir_conceptmaps_source_target', 'fhir_concept_maps', ['source_url', 'target_url'])

    # ============================================================================
    # FHIR SUBSCRIPTIONS TABLE
    # ============================================================================
    op.create_table(
        'fhir_subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('fhir_id', sa.String(64), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('criteria', sa.Text(), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=True),
        sa.Column('channel_type', sa.String(20), nullable=False),
        sa.Column('channel_endpoint', sa.String(500), nullable=True),
        sa.Column('channel_payload', sa.String(20), nullable=False, server_default='application/fhir+json'),
        sa.Column('channel_headers', postgresql.JSONB(), nullable=True),
        sa.Column('error_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('last_error_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivery_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('resource_data', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE')
    )

    # Create indexes for subscriptions
    op.create_index('idx_fhir_subscriptions_tenant', 'fhir_subscriptions', ['tenant_id'])
    op.create_index('idx_fhir_subscriptions_status', 'fhir_subscriptions', ['status'])
    op.create_index('idx_fhir_subscriptions_resource_type', 'fhir_subscriptions', ['resource_type'])
    op.create_index(
        'idx_fhir_subscriptions_active',
        'fhir_subscriptions',
        ['tenant_id', 'status'],
        postgresql_where=sa.text("status = 'active'")
    )


def downgrade() -> None:
    """Downgrade schema - Remove FHIR R4 resource storage tables."""

    # Drop tables in reverse order
    op.drop_table('fhir_subscriptions')
    op.drop_table('fhir_concept_maps')
    op.drop_table('fhir_value_sets')
    op.drop_table('fhir_code_systems')
    op.drop_table('fhir_resource_history')
    op.drop_table('fhir_resources')

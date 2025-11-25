"""
Multi-Tenancy Row-Level Security and Enhanced Tenant Model

EPIC-004: Multi-Tenancy Implementation

This migration:
1. Enhances the tenants table with tier, status, limits, settings, branding
2. Creates API keys table for tenant authentication
3. Creates tenant audit log table
4. Creates tenant usage tracking tables
5. Implements PostgreSQL Row-Level Security (RLS) policies
6. Creates indexes for optimal multi-tenant query performance

Revision ID: 002_multi_tenancy_rls
Revises: f548902ab172
Create Date: 2024-11-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_multi_tenancy_rls'
down_revision = 'f548902ab172'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema for multi-tenancy."""

    # ========================================================================
    # 1. ENHANCE TENANTS TABLE
    # ========================================================================

    # Add new columns to tenants table
    op.add_column('tenants', sa.Column('slug', sa.String(100), nullable=True))
    op.add_column('tenants', sa.Column('tier', sa.String(50), nullable=False, server_default='free'))
    op.add_column('tenants', sa.Column('status', sa.String(50), nullable=False, server_default='pending'))
    op.add_column('tenants', sa.Column('owner_email', sa.String(255), nullable=True))
    op.add_column('tenants', sa.Column('owner_name', sa.String(255), nullable=True))
    op.add_column('tenants', sa.Column('phone', sa.String(50), nullable=True))
    op.add_column('tenants', sa.Column('address', sa.Text(), nullable=True))
    op.add_column('tenants', sa.Column('country', sa.String(100), nullable=True))
    op.add_column('tenants', sa.Column('timezone', sa.String(100), server_default='UTC'))

    # Resource limits stored as JSONB
    op.add_column('tenants', sa.Column('limits', postgresql.JSONB(), nullable=False, server_default='{}'))

    # Settings stored as JSONB
    op.add_column('tenants', sa.Column('settings', postgresql.JSONB(), nullable=False, server_default='{}'))

    # Branding stored as JSONB
    op.add_column('tenants', sa.Column('branding', postgresql.JSONB(), nullable=False, server_default='{}'))

    # Feature flags
    op.add_column('tenants', sa.Column('features', postgresql.JSONB(), nullable=False, server_default='{}'))

    # Integrations configuration
    op.add_column('tenants', sa.Column('integrations', postgresql.JSONB(), nullable=False, server_default='{}'))

    # Billing information
    op.add_column('tenants', sa.Column('billing_email', sa.String(255), nullable=True))
    op.add_column('tenants', sa.Column('billing_address', sa.Text(), nullable=True))
    op.add_column('tenants', sa.Column('stripe_customer_id', sa.String(255), nullable=True))
    op.add_column('tenants', sa.Column('subscription_id', sa.String(255), nullable=True))
    op.add_column('tenants', sa.Column('trial_ends_at', sa.DateTime(timezone=True), nullable=True))

    # Compliance
    op.add_column('tenants', sa.Column('hipaa_baa_signed', sa.Boolean(), server_default='false'))
    op.add_column('tenants', sa.Column('hipaa_baa_signed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('tenants', sa.Column('data_processing_agreement_signed', sa.Boolean(), server_default='false'))

    # Suspension info
    op.add_column('tenants', sa.Column('suspended_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('tenants', sa.Column('suspension_reason', sa.Text(), nullable=True))

    # Soft delete
    op.add_column('tenants', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('tenants', sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True))

    # Create unique index on slug
    op.create_unique_constraint('uq_tenants_slug', 'tenants', ['slug'])
    op.create_index('idx_tenants_tier', 'tenants', ['tier'])
    op.create_index('idx_tenants_status', 'tenants', ['status'])
    op.create_index('idx_tenants_deleted_at', 'tenants', ['deleted_at'])

    # ========================================================================
    # 2. CREATE API KEYS TABLE
    # ========================================================================

    op.create_table(
        'tenant_api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('key_prefix', sa.String(20), nullable=False),  # First 8 chars of key for identification
        sa.Column('key_hash', sa.String(255), nullable=False),  # bcrypt hash of full key
        sa.Column('scopes', postgresql.ARRAY(sa.String(100)), nullable=False, server_default='{}'),
        sa.Column('rate_limit', sa.Integer(), server_default='1000'),  # requests per minute
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_ip', sa.String(45), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    op.create_index('idx_tenant_api_keys_tenant', 'tenant_api_keys', ['tenant_id'])
    op.create_index('idx_tenant_api_keys_prefix', 'tenant_api_keys', ['key_prefix'])
    op.create_index('idx_tenant_api_keys_active', 'tenant_api_keys', ['is_active'])

    # ========================================================================
    # 3. CREATE TENANT AUDIT LOG TABLE
    # ========================================================================

    op.create_table(
        'tenant_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),  # CREATE, READ, UPDATE, DELETE, LOGIN, etc.
        sa.Column('resource_type', sa.String(100), nullable=False),  # patient, appointment, etc.
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('old_values', postgresql.JSONB(), nullable=True),  # Previous state
        sa.Column('new_values', postgresql.JSONB(), nullable=True),  # New state
        sa.Column('changes', postgresql.JSONB(), nullable=True),  # Diff only
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('request_id', sa.String(100), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    # Partition-ready indexes for time-based queries
    op.create_index('idx_audit_logs_tenant_time', 'tenant_audit_logs', ['tenant_id', 'created_at'])
    op.create_index('idx_audit_logs_user', 'tenant_audit_logs', ['user_id', 'created_at'])
    op.create_index('idx_audit_logs_resource', 'tenant_audit_logs', ['resource_type', 'resource_id'])
    op.create_index('idx_audit_logs_action', 'tenant_audit_logs', ['action', 'created_at'])

    # ========================================================================
    # 4. CREATE USAGE TRACKING TABLES
    # ========================================================================

    # Daily usage aggregates
    op.create_table(
        'tenant_usage_daily',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('api_calls', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('api_calls_by_endpoint', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('storage_bytes', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('storage_delta_bytes', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('active_users', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unique_patients_accessed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('appointments_created', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('encounters_created', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('documents_uploaded', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('documents_bytes', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('ai_requests', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('ai_tokens_used', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('telehealth_minutes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('sms_sent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('emails_sent', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('whatsapp_messages', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('errors', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('errors_by_type', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('tenant_id', 'date', name='uq_tenant_usage_daily_tenant_date'),
    )

    op.create_index('idx_usage_daily_tenant_date', 'tenant_usage_daily', ['tenant_id', 'date'])
    op.create_index('idx_usage_daily_date', 'tenant_usage_daily', ['date'])

    # Real-time usage counters (for rate limiting)
    op.create_table(
        'tenant_usage_realtime',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('metric', sa.String(100), nullable=False),  # api_calls, storage, etc.
        sa.Column('window_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('window_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('tenant_id', 'metric', 'window_start', name='uq_tenant_usage_realtime'),
    )

    op.create_index('idx_usage_realtime_tenant_metric', 'tenant_usage_realtime', ['tenant_id', 'metric', 'window_start'])

    # ========================================================================
    # 5. CREATE TENANT INVITATIONS TABLE
    # ========================================================================

    op.create_table(
        'tenant_invitations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('role', sa.String(100), nullable=False, server_default='user'),
        sa.Column('token', sa.String(255), nullable=False),
        sa.Column('invited_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('accepted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    op.create_index('idx_invitations_tenant', 'tenant_invitations', ['tenant_id'])
    op.create_index('idx_invitations_token', 'tenant_invitations', ['token'], unique=True)
    op.create_index('idx_invitations_email', 'tenant_invitations', ['email'])

    # ========================================================================
    # 6. CREATE TENANT DATA EXPORTS TABLE
    # ========================================================================

    op.create_table(
        'tenant_data_exports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('export_type', sa.String(50), nullable=False),  # full, partial, gdpr_request
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),  # pending, processing, completed, failed
        sa.Column('format', sa.String(20), nullable=False, server_default='json'),  # json, csv, fhir_bundle
        sa.Column('include_tables', postgresql.ARRAY(sa.String(100)), nullable=True),  # null = all tables
        sa.Column('filters', postgresql.JSONB(), nullable=True),  # date range, etc.
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('records_exported', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    op.create_index('idx_exports_tenant', 'tenant_data_exports', ['tenant_id'])
    op.create_index('idx_exports_status', 'tenant_data_exports', ['status'])

    # ========================================================================
    # 7. CREATE TENANT ENCRYPTION KEYS TABLE
    # ========================================================================

    op.create_table(
        'tenant_encryption_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('key_type', sa.String(50), nullable=False),  # data, backup, signing
        sa.Column('key_id', sa.String(255), nullable=False),  # AWS KMS key ID or similar
        sa.Column('algorithm', sa.String(50), nullable=False, server_default='AES-256-GCM'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('rotation_interval_days', sa.Integer(), nullable=False, server_default='90'),
        sa.Column('last_rotated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_rotation_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    op.create_index('idx_encryption_keys_tenant', 'tenant_encryption_keys', ['tenant_id'])
    op.create_index('idx_encryption_keys_active', 'tenant_encryption_keys', ['is_active'])

    # ========================================================================
    # 8. ROW-LEVEL SECURITY POLICIES
    # ========================================================================

    # Create function to get current tenant from session
    op.execute("""
        CREATE OR REPLACE FUNCTION current_tenant_id()
        RETURNS UUID AS $$
        BEGIN
            RETURN NULLIF(current_setting('app.current_tenant', true), '')::uuid;
        EXCEPTION WHEN OTHERS THEN
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql STABLE;
    """)

    # Create function to check if RLS should be bypassed (for admin operations)
    op.execute("""
        CREATE OR REPLACE FUNCTION is_rls_bypassed()
        RETURNS BOOLEAN AS $$
        BEGIN
            RETURN COALESCE(current_setting('app.bypass_rls', true), 'false')::boolean;
        EXCEPTION WHEN OTHERS THEN
            RETURN false;
        END;
        $$ LANGUAGE plpgsql STABLE;
    """)

    # List of tables that need RLS
    tenant_tables = [
        'patients',
        'practitioners',
        'organizations',
        'locations',
        'users',
        'roles',
        'appointments',
        'encounters',
        'consents',
        'communications',
        'tickets',
        'journeys',
        'journey_stages',
        'journey_instances',
        'journey_stage_instances',
        'provider_schedules',
        'schedule_overrides',
    ]

    for table in tenant_tables:
        # Enable RLS on table
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")

        # Create policy for select
        op.execute(f"""
            CREATE POLICY {table}_tenant_isolation_select ON {table}
            FOR SELECT
            USING (
                is_rls_bypassed()
                OR tenant_id = current_tenant_id()
            );
        """)

        # Create policy for insert
        op.execute(f"""
            CREATE POLICY {table}_tenant_isolation_insert ON {table}
            FOR INSERT
            WITH CHECK (
                is_rls_bypassed()
                OR tenant_id = current_tenant_id()
            );
        """)

        # Create policy for update
        op.execute(f"""
            CREATE POLICY {table}_tenant_isolation_update ON {table}
            FOR UPDATE
            USING (
                is_rls_bypassed()
                OR tenant_id = current_tenant_id()
            )
            WITH CHECK (
                is_rls_bypassed()
                OR tenant_id = current_tenant_id()
            );
        """)

        # Create policy for delete
        op.execute(f"""
            CREATE POLICY {table}_tenant_isolation_delete ON {table}
            FOR DELETE
            USING (
                is_rls_bypassed()
                OR tenant_id = current_tenant_id()
            );
        """)

    # ========================================================================
    # 9. CREATE HELPER FUNCTIONS FOR TENANT MANAGEMENT
    # ========================================================================

    # Function to set tenant context for a session
    op.execute("""
        CREATE OR REPLACE FUNCTION set_tenant_context(p_tenant_id UUID)
        RETURNS void AS $$
        BEGIN
            PERFORM set_config('app.current_tenant', p_tenant_id::text, false);
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Function to clear tenant context
    op.execute("""
        CREATE OR REPLACE FUNCTION clear_tenant_context()
        RETURNS void AS $$
        BEGIN
            PERFORM set_config('app.current_tenant', '', false);
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Function to bypass RLS for admin operations
    op.execute("""
        CREATE OR REPLACE FUNCTION set_bypass_rls(p_bypass BOOLEAN)
        RETURNS void AS $$
        BEGIN
            PERFORM set_config('app.bypass_rls', p_bypass::text, false);
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Function to get tenant usage statistics
    op.execute("""
        CREATE OR REPLACE FUNCTION get_tenant_usage_stats(p_tenant_id UUID)
        RETURNS TABLE (
            user_count BIGINT,
            patient_count BIGINT,
            appointment_count BIGINT,
            encounter_count BIGINT,
            storage_bytes BIGINT
        ) AS $$
        BEGIN
            -- Temporarily bypass RLS for counting
            PERFORM set_config('app.bypass_rls', 'true', true);

            RETURN QUERY
            SELECT
                (SELECT COUNT(*) FROM users WHERE tenant_id = p_tenant_id AND is_active = true),
                (SELECT COUNT(*) FROM patients WHERE tenant_id = p_tenant_id),
                (SELECT COUNT(*) FROM appointments WHERE tenant_id = p_tenant_id),
                (SELECT COUNT(*) FROM encounters WHERE tenant_id = p_tenant_id),
                COALESCE((
                    SELECT SUM(storage_bytes)::BIGINT
                    FROM tenant_usage_daily
                    WHERE tenant_id = p_tenant_id
                    ORDER BY date DESC LIMIT 1
                ), 0);

            PERFORM set_config('app.bypass_rls', 'false', true);
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)

    # ========================================================================
    # 10. CREATE TRIGGERS FOR AUTOMATIC AUDIT LOGGING
    # ========================================================================

    # Create audit trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION audit_trigger_func()
        RETURNS TRIGGER AS $$
        DECLARE
            v_old_data JSONB;
            v_new_data JSONB;
            v_action TEXT;
            v_tenant_id UUID;
            v_user_id UUID;
        BEGIN
            -- Get current tenant and user from session
            v_tenant_id := current_tenant_id();
            BEGIN
                v_user_id := NULLIF(current_setting('app.current_user', true), '')::uuid;
            EXCEPTION WHEN OTHERS THEN
                v_user_id := NULL;
            END;

            -- Determine action
            IF TG_OP = 'INSERT' THEN
                v_action := 'CREATE';
                v_new_data := to_jsonb(NEW);
                v_old_data := NULL;
                v_tenant_id := COALESCE(v_tenant_id, NEW.tenant_id);
            ELSIF TG_OP = 'UPDATE' THEN
                v_action := 'UPDATE';
                v_old_data := to_jsonb(OLD);
                v_new_data := to_jsonb(NEW);
                v_tenant_id := COALESCE(v_tenant_id, NEW.tenant_id);
            ELSIF TG_OP = 'DELETE' THEN
                v_action := 'DELETE';
                v_old_data := to_jsonb(OLD);
                v_new_data := NULL;
                v_tenant_id := COALESCE(v_tenant_id, OLD.tenant_id);
            END IF;

            -- Skip if no tenant context
            IF v_tenant_id IS NULL THEN
                RETURN COALESCE(NEW, OLD);
            END IF;

            -- Insert audit record
            INSERT INTO tenant_audit_logs (
                tenant_id,
                user_id,
                action,
                resource_type,
                resource_id,
                old_values,
                new_values,
                created_at
            ) VALUES (
                v_tenant_id,
                v_user_id,
                v_action,
                TG_TABLE_NAME,
                COALESCE(NEW.id, OLD.id),
                v_old_data,
                v_new_data,
                NOW()
            );

            RETURN COALESCE(NEW, OLD);
        END;
        $$ LANGUAGE plpgsql SECURITY DEFINER;
    """)

    # Apply audit triggers to critical tables
    audit_tables = ['patients', 'appointments', 'encounters', 'users', 'consents']

    for table in audit_tables:
        op.execute(f"""
            CREATE TRIGGER audit_trigger_{table}
            AFTER INSERT OR UPDATE OR DELETE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION audit_trigger_func();
        """)


def downgrade() -> None:
    """Downgrade database schema."""

    # Remove audit triggers
    audit_tables = ['patients', 'appointments', 'encounters', 'users', 'consents']
    for table in audit_tables:
        op.execute(f"DROP TRIGGER IF EXISTS audit_trigger_{table} ON {table};")

    # Drop audit trigger function
    op.execute("DROP FUNCTION IF EXISTS audit_trigger_func();")

    # Drop helper functions
    op.execute("DROP FUNCTION IF EXISTS get_tenant_usage_stats(UUID);")
    op.execute("DROP FUNCTION IF EXISTS set_bypass_rls(BOOLEAN);")
    op.execute("DROP FUNCTION IF EXISTS clear_tenant_context();")
    op.execute("DROP FUNCTION IF EXISTS set_tenant_context(UUID);")

    # Remove RLS policies
    tenant_tables = [
        'patients',
        'practitioners',
        'organizations',
        'locations',
        'users',
        'roles',
        'appointments',
        'encounters',
        'consents',
        'communications',
        'tickets',
        'journeys',
        'journey_stages',
        'journey_instances',
        'journey_stage_instances',
        'provider_schedules',
        'schedule_overrides',
    ]

    for table in tenant_tables:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation_select ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation_insert ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation_update ON {table};")
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation_delete ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS is_rls_bypassed();")
    op.execute("DROP FUNCTION IF EXISTS current_tenant_id();")

    # Drop new tables
    op.drop_table('tenant_encryption_keys')
    op.drop_table('tenant_data_exports')
    op.drop_table('tenant_invitations')
    op.drop_table('tenant_usage_realtime')
    op.drop_table('tenant_usage_daily')
    op.drop_table('tenant_audit_logs')
    op.drop_table('tenant_api_keys')

    # Drop indexes on tenants
    op.drop_index('idx_tenants_deleted_at', table_name='tenants')
    op.drop_index('idx_tenants_status', table_name='tenants')
    op.drop_index('idx_tenants_tier', table_name='tenants')
    op.drop_constraint('uq_tenants_slug', 'tenants')

    # Remove columns from tenants
    columns_to_drop = [
        'slug', 'tier', 'status', 'owner_email', 'owner_name', 'phone', 'address',
        'country', 'timezone', 'limits', 'settings', 'branding', 'features',
        'integrations', 'billing_email', 'billing_address', 'stripe_customer_id',
        'subscription_id', 'trial_ends_at', 'hipaa_baa_signed', 'hipaa_baa_signed_at',
        'data_processing_agreement_signed', 'suspended_at', 'suspension_reason',
        'deleted_at', 'deleted_by'
    ]

    for col in columns_to_drop:
        op.drop_column('tenants', col)

"""API Marketplace & Developer Platform

Revision ID: 018_api_marketplace
Revises: 017_revenue_infrastructure
Create Date: 2024-11-25

EPIC-018: Creates tables for developer platform and API marketplace
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

# revision identifiers
revision = '018_api_marketplace'
down_revision = '017_revenue_infrastructure'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========================================================================
    # Developer Organization Tables
    # ========================================================================

    # Developer Organizations
    op.create_table(
        'developer_organizations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(100), unique=True, nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('website', sa.String(500)),
        sa.Column('description', sa.Text),
        sa.Column('logo_url', sa.String(500)),
        sa.Column('contact_name', sa.String(200)),
        sa.Column('contact_email', sa.String(255)),
        sa.Column('contact_phone', sa.String(50)),
        sa.Column('address_line1', sa.String(255)),
        sa.Column('address_line2', sa.String(255)),
        sa.Column('city', sa.String(100)),
        sa.Column('state', sa.String(100)),
        sa.Column('postal_code', sa.String(20)),
        sa.Column('country', sa.String(2), default='US'),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('verified_at', sa.DateTime),
        sa.Column('verification_data', JSONB, default={}),
        sa.Column('agreed_to_terms', sa.Boolean, default=False),
        sa.Column('terms_accepted_at', sa.DateTime),
        sa.Column('terms_version', sa.String(20)),
        sa.Column('settings', JSONB, default={}),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_dev_org_slug', 'developer_organizations', ['slug'])
    op.create_index('ix_dev_org_status', 'developer_organizations', ['status'])
    op.create_index('ix_dev_org_email', 'developer_organizations', ['email'])

    # Developer Members
    op.create_table(
        'developer_members',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', UUID(as_uuid=True), sa.ForeignKey('developer_organizations.id'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('name', sa.String(200)),
        sa.Column('role', sa.String(20), default='developer'),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('invited_by', UUID(as_uuid=True)),
        sa.Column('invited_at', sa.DateTime),
        sa.Column('accepted_at', sa.DateTime),
        sa.Column('invitation_token', sa.String(64), unique=True),
        sa.Column('two_factor_enabled', sa.Boolean, default=False),
        sa.Column('two_factor_secret', sa.String(64)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_login_at', sa.DateTime),
        sa.UniqueConstraint('organization_id', 'email', name='uq_dev_member_org_email'),
    )
    op.create_index('ix_dev_member_org', 'developer_members', ['organization_id'])
    op.create_index('ix_dev_member_user', 'developer_members', ['user_id'])

    # ========================================================================
    # OAuth Application Tables
    # ========================================================================

    # OAuth Applications
    op.create_table(
        'oauth_applications',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', UUID(as_uuid=True), sa.ForeignKey('developer_organizations.id'), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(100), unique=True, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('app_type', sa.String(20), default='web'),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('client_id', sa.String(64), unique=True, nullable=False),
        sa.Column('client_secret_hash', sa.String(128)),
        sa.Column('client_secret_prefix', sa.String(8)),
        sa.Column('redirect_uris', ARRAY(sa.String), default=[]),
        sa.Column('allowed_grant_types', ARRAY(sa.String), default=['authorization_code']),
        sa.Column('allowed_scopes', ARRAY(sa.String), default=[]),
        sa.Column('default_scopes', ARRAY(sa.String), default=[]),
        sa.Column('is_smart_on_fhir', sa.Boolean, default=False),
        sa.Column('launch_uri', sa.String(500)),
        sa.Column('smart_capabilities', JSONB, default={}),
        sa.Column('homepage_url', sa.String(500)),
        sa.Column('privacy_policy_url', sa.String(500)),
        sa.Column('terms_of_service_url', sa.String(500)),
        sa.Column('support_url', sa.String(500)),
        sa.Column('logo_url', sa.String(500)),
        sa.Column('icon_url', sa.String(500)),
        sa.Column('primary_color', sa.String(7)),
        sa.Column('access_token_ttl', sa.Integer, default=3600),
        sa.Column('refresh_token_ttl', sa.Integer, default=2592000),
        sa.Column('require_pkce', sa.Boolean, default=True),
        sa.Column('allowed_origins', ARRAY(sa.String), default=[]),
        sa.Column('ip_allowlist', ARRAY(sa.String), default=[]),
        sa.Column('settings', JSONB, default={}),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_oauth_app_slug', 'oauth_applications', ['slug'])
    op.create_index('ix_oauth_app_client_id', 'oauth_applications', ['client_id'])
    op.create_index('ix_oauth_app_org', 'oauth_applications', ['organization_id'])
    op.create_index('ix_oauth_app_status', 'oauth_applications', ['status'])

    # API Keys
    op.create_table(
        'api_keys',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('application_id', UUID(as_uuid=True), sa.ForeignKey('oauth_applications.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('key_prefix', sa.String(8), nullable=False),
        sa.Column('key_hash', sa.String(128), unique=True, nullable=False),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('scopes', ARRAY(sa.String), default=[]),
        sa.Column('is_test_key', sa.Boolean, default=False),
        sa.Column('rate_limit_per_minute', sa.Integer, default=60),
        sa.Column('rate_limit_per_day', sa.Integer, default=10000),
        sa.Column('monthly_quota', sa.Integer),
        sa.Column('ip_allowlist', ARRAY(sa.String), default=[]),
        sa.Column('allowed_referrers', ARRAY(sa.String), default=[]),
        sa.Column('expires_at', sa.DateTime),
        sa.Column('last_used_at', sa.DateTime),
        sa.Column('last_used_ip', sa.String(45)),
        sa.Column('total_requests', sa.Integer, default=0),
        sa.Column('created_by', UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('revoked_at', sa.DateTime),
    )
    op.create_index('ix_api_key_app', 'api_keys', ['application_id'])
    op.create_index('ix_api_key_prefix', 'api_keys', ['key_prefix'])
    op.create_index('ix_api_key_hash', 'api_keys', ['key_hash'])

    # OAuth Tokens
    op.create_table(
        'oauth_tokens',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('application_id', UUID(as_uuid=True), sa.ForeignKey('oauth_applications.id'), nullable=False),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('token_type', sa.String(30), nullable=False),
        sa.Column('token_hash', sa.String(128), unique=True, nullable=False),
        sa.Column('token_prefix', sa.String(8)),
        sa.Column('user_id', UUID(as_uuid=True)),
        sa.Column('patient_id', UUID(as_uuid=True)),
        sa.Column('grant_type', sa.String(30)),
        sa.Column('scopes', ARRAY(sa.String), default=[]),
        sa.Column('launch_context', JSONB, default={}),
        sa.Column('parent_token_id', UUID(as_uuid=True)),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('is_revoked', sa.Boolean, default=False),
        sa.Column('revoked_at', sa.DateTime),
        sa.Column('code_challenge', sa.String(128)),
        sa.Column('code_challenge_method', sa.String(10)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('last_used_at', sa.DateTime),
    )
    op.create_index('ix_oauth_token_app', 'oauth_tokens', ['application_id'])
    op.create_index('ix_oauth_token_tenant', 'oauth_tokens', ['tenant_id'])
    op.create_index('ix_oauth_token_user', 'oauth_tokens', ['user_id'])
    op.create_index('ix_oauth_token_expires', 'oauth_tokens', ['expires_at'])
    op.create_index('ix_oauth_token_hash', 'oauth_tokens', ['token_hash'])

    # OAuth Consents
    op.create_table(
        'oauth_consents',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('application_id', UUID(as_uuid=True), sa.ForeignKey('oauth_applications.id'), nullable=False),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', UUID(as_uuid=True)),
        sa.Column('granted_scopes', ARRAY(sa.String), default=[]),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('granted_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime),
        sa.Column('revoked_at', sa.DateTime),
        sa.UniqueConstraint('application_id', 'tenant_id', 'user_id', 'patient_id', name='uq_oauth_consent_app_user'),
    )
    op.create_index('ix_oauth_consent_app', 'oauth_consents', ['application_id'])
    op.create_index('ix_oauth_consent_tenant', 'oauth_consents', ['tenant_id'])
    op.create_index('ix_oauth_consent_user', 'oauth_consents', ['user_id'])

    # ========================================================================
    # Webhook Tables
    # ========================================================================

    # Webhook Endpoints
    op.create_table(
        'webhook_endpoints',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('application_id', UUID(as_uuid=True), sa.ForeignKey('oauth_applications.id'), nullable=False),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('description', sa.String(200)),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('subscribed_events', ARRAY(sa.String), default=[]),
        sa.Column('secret', sa.String(64)),
        sa.Column('secret_hash', sa.String(128)),
        sa.Column('timeout_seconds', sa.Integer, default=30),
        sa.Column('max_retries', sa.Integer, default=3),
        sa.Column('total_deliveries', sa.Integer, default=0),
        sa.Column('successful_deliveries', sa.Integer, default=0),
        sa.Column('failed_deliveries', sa.Integer, default=0),
        sa.Column('last_delivery_at', sa.DateTime),
        sa.Column('last_status_code', sa.Integer),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_webhook_app', 'webhook_endpoints', ['application_id'])

    # Webhook Deliveries
    op.create_table(
        'webhook_deliveries',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('endpoint_id', UUID(as_uuid=True), sa.ForeignKey('webhook_endpoints.id'), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_id', sa.String(64), nullable=False),
        sa.Column('payload', JSONB, nullable=False),
        sa.Column('attempt_number', sa.Integer, default=1),
        sa.Column('status_code', sa.Integer),
        sa.Column('response_body', sa.Text),
        sa.Column('response_time_ms', sa.Integer),
        sa.Column('is_successful', sa.Boolean),
        sa.Column('error_message', sa.Text),
        sa.Column('scheduled_at', sa.DateTime),
        sa.Column('delivered_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_webhook_delivery_endpoint', 'webhook_deliveries', ['endpoint_id'])
    op.create_index('ix_webhook_delivery_event', 'webhook_deliveries', ['event_id'])

    # ========================================================================
    # Marketplace Tables
    # ========================================================================

    # Marketplace Apps
    op.create_table(
        'marketplace_apps',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('application_id', UUID(as_uuid=True), sa.ForeignKey('oauth_applications.id'), unique=True, nullable=False),
        sa.Column('organization_id', UUID(as_uuid=True), sa.ForeignKey('developer_organizations.id'), nullable=False),
        sa.Column('display_name', sa.String(200), nullable=False),
        sa.Column('short_description', sa.String(300), nullable=False),
        sa.Column('long_description', sa.Text),
        sa.Column('tagline', sa.String(100)),
        sa.Column('category', sa.String(30), default='other'),
        sa.Column('subcategory', sa.String(50)),
        sa.Column('tags', ARRAY(sa.String), default=[]),
        sa.Column('icon_url', sa.String(500)),
        sa.Column('banner_url', sa.String(500)),
        sa.Column('screenshots', JSONB, default=[]),
        sa.Column('video_url', sa.String(500)),
        sa.Column('documentation_url', sa.String(500)),
        sa.Column('changelog_url', sa.String(500)),
        sa.Column('support_email', sa.String(255)),
        sa.Column('is_free', sa.Boolean, default=True),
        sa.Column('pricing_model', sa.String(50)),
        sa.Column('price_monthly', sa.Numeric(10, 2)),
        sa.Column('price_annual', sa.Numeric(10, 2)),
        sa.Column('pricing_details', JSONB, default={}),
        sa.Column('install_count', sa.Integer, default=0),
        sa.Column('average_rating', sa.Numeric(2, 1), default=0),
        sa.Column('review_count', sa.Integer, default=0),
        sa.Column('is_featured', sa.Boolean, default=False),
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('is_visible', sa.Boolean, default=True),
        sa.Column('sort_order', sa.Integer, default=0),
        sa.Column('required_scopes', ARRAY(sa.String), default=[]),
        sa.Column('optional_scopes', ARRAY(sa.String), default=[]),
        sa.Column('min_platform_version', sa.String(20)),
        sa.Column('current_version', sa.String(20)),
        sa.Column('latest_release_at', sa.DateTime),
        sa.Column('published_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_marketplace_app_app', 'marketplace_apps', ['application_id'])
    op.create_index('ix_marketplace_app_org', 'marketplace_apps', ['organization_id'])
    op.create_index('ix_marketplace_app_category', 'marketplace_apps', ['category'])
    op.create_index('ix_marketplace_app_featured', 'marketplace_apps', ['is_featured'])
    op.create_index('ix_marketplace_app_rating', 'marketplace_apps', ['average_rating'])

    # App Versions
    op.create_table(
        'app_versions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('marketplace_app_id', UUID(as_uuid=True), sa.ForeignKey('marketplace_apps.id'), nullable=False),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('version_name', sa.String(100)),
        sa.Column('release_notes', sa.Text),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('scope_changes', JSONB, default={}),
        sa.Column('breaking_changes', sa.Boolean, default=False),
        sa.Column('submitted_at', sa.DateTime),
        sa.Column('reviewed_at', sa.DateTime),
        sa.Column('reviewed_by', UUID(as_uuid=True)),
        sa.Column('review_notes', sa.Text),
        sa.Column('rollout_percentage', sa.Integer, default=100),
        sa.Column('is_current', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('published_at', sa.DateTime),
        sa.UniqueConstraint('marketplace_app_id', 'version', name='uq_app_version'),
    )
    op.create_index('ix_app_version_app', 'app_versions', ['marketplace_app_id'])

    # App Installations
    op.create_table(
        'app_installations',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('application_id', UUID(as_uuid=True), sa.ForeignKey('oauth_applications.id'), nullable=False),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('granted_scopes', ARRAY(sa.String), default=[]),
        sa.Column('configured_scopes', ARRAY(sa.String), default=[]),
        sa.Column('installed_by', UUID(as_uuid=True)),
        sa.Column('installed_version', sa.String(20)),
        sa.Column('configuration', JSONB, default={}),
        sa.Column('last_used_at', sa.DateTime),
        sa.Column('api_calls_count', sa.Integer, default=0),
        sa.Column('installed_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('uninstalled_at', sa.DateTime),
        sa.UniqueConstraint('application_id', 'tenant_id', name='uq_app_installation_tenant'),
    )
    op.create_index('ix_installation_app', 'app_installations', ['application_id'])
    op.create_index('ix_installation_tenant', 'app_installations', ['tenant_id'])
    op.create_index('ix_installation_status', 'app_installations', ['status'])

    # App Reviews
    op.create_table(
        'app_reviews',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('marketplace_app_id', UUID(as_uuid=True), sa.ForeignKey('marketplace_apps.id'), nullable=False),
        sa.Column('tenant_id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('rating', sa.Integer, nullable=False),
        sa.Column('title', sa.String(200)),
        sa.Column('body', sa.Text),
        sa.Column('is_verified_purchase', sa.Boolean, default=False),
        sa.Column('installation_id', UUID(as_uuid=True)),
        sa.Column('is_visible', sa.Boolean, default=True),
        sa.Column('is_flagged', sa.Boolean, default=False),
        sa.Column('moderation_notes', sa.Text),
        sa.Column('publisher_response', sa.Text),
        sa.Column('publisher_responded_at', sa.DateTime),
        sa.Column('helpful_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('marketplace_app_id', 'tenant_id', 'user_id', name='uq_app_review_user'),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='ck_rating_range'),
    )
    op.create_index('ix_app_review_app', 'app_reviews', ['marketplace_app_id'])
    op.create_index('ix_app_review_tenant', 'app_reviews', ['tenant_id'])

    # ========================================================================
    # Sandbox Tables
    # ========================================================================

    # Sandbox Environments
    op.create_table(
        'sandbox_environments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', UUID(as_uuid=True), sa.ForeignKey('developer_organizations.id'), nullable=False),
        sa.Column('name', sa.String(100), default='Default Sandbox'),
        sa.Column('status', sa.String(20), default='provisioning'),
        sa.Column('sandbox_tenant_id', UUID(as_uuid=True), unique=True),
        sa.Column('has_sample_data', sa.Boolean, default=True),
        sa.Column('sample_data_config', JSONB, default={}),
        sa.Column('test_api_key_prefix', sa.String(8)),
        sa.Column('test_api_key_hash', sa.String(128)),
        sa.Column('max_api_calls_per_day', sa.Integer, default=1000),
        sa.Column('max_records', sa.Integer, default=100),
        sa.Column('api_calls_today', sa.Integer, default=0),
        sa.Column('total_api_calls', sa.Integer, default=0),
        sa.Column('last_reset_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime),
        sa.Column('last_used_at', sa.DateTime),
    )
    op.create_index('ix_sandbox_org', 'sandbox_environments', ['organization_id'])
    op.create_index('ix_sandbox_status', 'sandbox_environments', ['status'])
    op.create_index('ix_sandbox_tenant', 'sandbox_environments', ['sandbox_tenant_id'])

    # ========================================================================
    # API Usage Tables
    # ========================================================================

    # API Usage Logs (partitioned by timestamp for performance)
    op.create_table(
        'api_usage_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('application_id', UUID(as_uuid=True)),
        sa.Column('api_key_id', UUID(as_uuid=True)),
        sa.Column('tenant_id', UUID(as_uuid=True)),
        sa.Column('endpoint', sa.String(200), nullable=False),
        sa.Column('method', sa.String(10), nullable=False),
        sa.Column('status_code', sa.Integer),
        sa.Column('response_time_ms', sa.Integer),
        sa.Column('client_ip', sa.String(45)),
        sa.Column('user_agent', sa.String(500)),
        sa.Column('timestamp', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_api_usage_app', 'api_usage_logs', ['application_id'])
    op.create_index('ix_api_usage_key', 'api_usage_logs', ['api_key_id'])
    op.create_index('ix_api_usage_tenant', 'api_usage_logs', ['tenant_id'])
    op.create_index('ix_api_usage_timestamp', 'api_usage_logs', ['timestamp'])
    op.create_index('ix_api_usage_app_time', 'api_usage_logs', ['application_id', 'timestamp'])

    # Rate Limit Buckets
    op.create_table(
        'rate_limit_buckets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('bucket_key', sa.String(200), unique=True, nullable=False),
        sa.Column('request_count', sa.Integer, default=0),
        sa.Column('limit_per_window', sa.Integer, nullable=False),
        sa.Column('window_size_seconds', sa.Integer, nullable=False),
        sa.Column('window_start', sa.DateTime, nullable=False),
        sa.Column('window_end', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_rate_limit_key', 'rate_limit_buckets', ['bucket_key'])

    # ========================================================================
    # Audit Tables
    # ========================================================================

    # Developer Audit Logs
    op.create_table(
        'developer_audit_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', UUID(as_uuid=True)),
        sa.Column('user_id', UUID(as_uuid=True)),
        sa.Column('application_id', UUID(as_uuid=True)),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(50)),
        sa.Column('entity_id', UUID(as_uuid=True)),
        sa.Column('details', JSONB, default={}),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.String(500)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_dev_audit_org', 'developer_audit_logs', ['organization_id'])
    op.create_index('ix_dev_audit_user', 'developer_audit_logs', ['user_id'])
    op.create_index('ix_dev_audit_app', 'developer_audit_logs', ['application_id'])
    op.create_index('ix_dev_audit_time', 'developer_audit_logs', ['created_at'])
    op.create_index('ix_dev_audit_org_time', 'developer_audit_logs', ['organization_id', 'created_at'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('developer_audit_logs')
    op.drop_table('rate_limit_buckets')
    op.drop_table('api_usage_logs')
    op.drop_table('sandbox_environments')
    op.drop_table('app_reviews')
    op.drop_table('app_installations')
    op.drop_table('app_versions')
    op.drop_table('marketplace_apps')
    op.drop_table('webhook_deliveries')
    op.drop_table('webhook_endpoints')
    op.drop_table('oauth_consents')
    op.drop_table('oauth_tokens')
    op.drop_table('api_keys')
    op.drop_table('oauth_applications')
    op.drop_table('developer_members')
    op.drop_table('developer_organizations')

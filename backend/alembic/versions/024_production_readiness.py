"""024 - Production Readiness

EPIC-024: Production Readiness
Creates tables for infrastructure management, monitoring & observability,
alerting, deployments, backup/DR, runbooks, and go-live preparation.

Revision ID: 024_production_readiness
Revises: 023_quality_testing
Create Date: 2024-11-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '024_production_readiness'
down_revision = '023_quality_testing'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # Infrastructure Tables
    # ==========================================================================

    # Infrastructure Resources
    op.create_table(
        'production_infrastructure_resources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('resource_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), default='provisioning'),
        sa.Column('cloud_provider', sa.String(50), nullable=False),
        sa.Column('environment', sa.String(50), nullable=False),
        sa.Column('region', sa.String(100), nullable=False),
        sa.Column('availability_zone', sa.String(100)),
        sa.Column('resource_id', sa.String(255)),
        sa.Column('resource_arn', sa.String(500)),
        sa.Column('instance_type', sa.String(100)),
        sa.Column('cpu_cores', sa.Integer),
        sa.Column('memory_gb', sa.Float),
        sa.Column('storage_gb', sa.Float),
        sa.Column('private_ip', sa.String(50)),
        sa.Column('public_ip', sa.String(50)),
        sa.Column('dns_name', sa.String(255)),
        sa.Column('tags', postgresql.JSONB, default=dict),
        sa.Column('metadata', postgresql.JSONB, default=dict),
        sa.Column('hourly_cost', sa.Float, default=0.0),
        sa.Column('monthly_cost', sa.Float, default=0.0),
        sa.Column('terraform_resource', sa.String(255)),
        sa.Column('terraform_state_key', sa.String(255)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )
    op.create_index('ix_prod_resource_tenant_env', 'production_infrastructure_resources', ['tenant_id', 'environment'])
    op.create_index('ix_prod_resource_type_status', 'production_infrastructure_resources', ['resource_type', 'status'])

    # Auto-Scaling Configurations
    op.create_table(
        'production_auto_scaling_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('production_infrastructure_resources.id')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('enabled', sa.Boolean, default=True),
        sa.Column('min_instances', sa.Integer, default=1),
        sa.Column('max_instances', sa.Integer, default=10),
        sa.Column('desired_instances', sa.Integer, default=2),
        sa.Column('scale_up_cpu_threshold', sa.Float, default=70.0),
        sa.Column('scale_down_cpu_threshold', sa.Float, default=30.0),
        sa.Column('scale_up_memory_threshold', sa.Float, default=80.0),
        sa.Column('scale_down_memory_threshold', sa.Float, default=40.0),
        sa.Column('scale_up_cooldown', sa.Integer, default=300),
        sa.Column('scale_down_cooldown', sa.Integer, default=600),
        sa.Column('custom_metrics', postgresql.JSONB, default=list),
        sa.Column('predictive_scaling_enabled', sa.Boolean, default=False),
        sa.Column('predictive_scaling_mode', sa.String(50)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Network Configurations
    op.create_table(
        'production_network_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('environment', sa.String(50), nullable=False),
        sa.Column('vpc_id', sa.String(100)),
        sa.Column('vpc_cidr', sa.String(20)),
        sa.Column('public_subnets', postgresql.ARRAY(sa.String), default=list),
        sa.Column('private_subnets', postgresql.ARRAY(sa.String), default=list),
        sa.Column('database_subnets', postgresql.ARRAY(sa.String), default=list),
        sa.Column('security_groups', postgresql.JSONB, default=list),
        sa.Column('load_balancer_arn', sa.String(500)),
        sa.Column('load_balancer_dns', sa.String(255)),
        sa.Column('service_mesh_enabled', sa.Boolean, default=False),
        sa.Column('service_mesh_type', sa.String(50)),
        sa.Column('dns_zone_id', sa.String(100)),
        sa.Column('domain_name', sa.String(255)),
        sa.Column('waf_enabled', sa.Boolean, default=False),
        sa.Column('waf_rules', postgresql.JSONB, default=list),
        sa.Column('ddos_protection_enabled', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    # ==========================================================================
    # Monitoring Tables
    # ==========================================================================

    # Metric Definitions
    op.create_table(
        'production_metric_definitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('metric_type', sa.String(50), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('prometheus_query', sa.Text),
        sa.Column('labels', postgresql.ARRAY(sa.String), default=list),
        sa.Column('unit', sa.String(50)),
        sa.Column('display_name', sa.String(255)),
        sa.Column('warning_threshold', sa.Float),
        sa.Column('critical_threshold', sa.Float),
        sa.Column('aggregation_method', sa.String(50)),
        sa.Column('aggregation_interval', sa.String(20)),
        sa.Column('enabled', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_metric_tenant_name'),
    )

    # Dashboards
    op.create_table(
        'production_dashboards',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('dashboard_type', sa.String(100)),
        sa.Column('grafana_uid', sa.String(100)),
        sa.Column('grafana_url', sa.String(500)),
        sa.Column('grafana_json', postgresql.JSONB),
        sa.Column('panels', postgresql.JSONB, default=list),
        sa.Column('is_public', sa.Boolean, default=False),
        sa.Column('allowed_roles', postgresql.ARRAY(sa.String), default=list),
        sa.Column('auto_refresh_interval', sa.String(20)),
        sa.Column('time_range', sa.String(50)),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True)),
        sa.Column('starred', sa.Boolean, default=False),
        sa.Column('folder', sa.String(100)),
        sa.Column('tags', postgresql.ARRAY(sa.String), default=list),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Health Checks
    op.create_table(
        'production_health_checks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('service_name', sa.String(255), nullable=False),
        sa.Column('check_type', sa.String(50), nullable=False),
        sa.Column('endpoint', sa.String(500), nullable=False),
        sa.Column('method', sa.String(10), default='GET'),
        sa.Column('expected_status_code', sa.Integer, default=200),
        sa.Column('expected_response', postgresql.JSONB),
        sa.Column('interval_seconds', sa.Integer, default=30),
        sa.Column('timeout_seconds', sa.Integer, default=10),
        sa.Column('success_threshold', sa.Integer, default=1),
        sa.Column('failure_threshold', sa.Integer, default=3),
        sa.Column('current_status', sa.String(50), default='unknown'),
        sa.Column('last_check_at', sa.DateTime),
        sa.Column('last_success_at', sa.DateTime),
        sa.Column('last_failure_at', sa.DateTime),
        sa.Column('consecutive_failures', sa.Integer, default=0),
        sa.Column('dependencies', postgresql.JSONB, default=list),
        sa.Column('enabled', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_prod_health_service_type', 'production_health_checks', ['service_name', 'check_type'])

    # SLO Definitions
    op.create_table(
        'production_slo_definitions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('service_name', sa.String(255), nullable=False),
        sa.Column('target_percentage', sa.Float, nullable=False),
        sa.Column('window_days', sa.Integer, default=30),
        sa.Column('error_budget_minutes', sa.Float),
        sa.Column('error_budget_remaining', sa.Float),
        sa.Column('error_budget_consumed_percent', sa.Float, default=0.0),
        sa.Column('sli_query', sa.Text),
        sa.Column('sli_type', sa.String(50)),
        sa.Column('burn_rate_alert_enabled', sa.Boolean, default=True),
        sa.Column('fast_burn_threshold', sa.Float, default=14.4),
        sa.Column('slow_burn_threshold', sa.Float, default=1.0),
        sa.Column('current_sli_value', sa.Float),
        sa.Column('slo_met', sa.Boolean),
        sa.Column('last_calculated_at', sa.DateTime),
        sa.Column('enabled', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'name', name='uq_slo_tenant_name'),
    )

    # SLI Records
    op.create_table(
        'production_sli_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('slo_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('production_slo_definitions.id')),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.Column('good_events', sa.Integer, default=0),
        sa.Column('total_events', sa.Integer, default=0),
        sa.Column('sli_value', sa.Float),
        sa.Column('window_start', sa.DateTime),
        sa.Column('window_end', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_prod_sli_slo_timestamp', 'production_sli_records', ['slo_id', 'timestamp'])

    # ==========================================================================
    # Alerting Tables
    # ==========================================================================

    # Alert Rules
    op.create_table(
        'production_alert_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('prometheus_query', sa.Text, nullable=False),
        sa.Column('threshold_operator', sa.String(10)),
        sa.Column('threshold_value', sa.Float),
        sa.Column('for_duration', sa.String(20)),
        sa.Column('evaluation_interval', sa.String(20), default='1m'),
        sa.Column('notification_channels', postgresql.ARRAY(sa.String), default=list),
        sa.Column('runbook_url', sa.String(500)),
        sa.Column('runbook_id', postgresql.UUID(as_uuid=True)),
        sa.Column('labels', postgresql.JSONB, default=dict),
        sa.Column('annotations', postgresql.JSONB, default=dict),
        sa.Column('group_by', postgresql.ARRAY(sa.String), default=list),
        sa.Column('inhibit_rules', postgresql.JSONB, default=list),
        sa.Column('enabled', sa.Boolean, default=True),
        sa.Column('silenced_until', sa.DateTime),
        sa.Column('last_triggered_at', sa.DateTime),
        sa.Column('trigger_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )

    # Alert Incidents
    op.create_table(
        'production_alert_incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('alert_rule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('production_alert_rules.id')),
        sa.Column('incident_number', sa.String(50), unique=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), default='triggered'),
        sa.Column('triggered_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('acknowledged_at', sa.DateTime),
        sa.Column('resolved_at', sa.DateTime),
        sa.Column('closed_at', sa.DateTime),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True)),
        sa.Column('escalation_level', sa.Integer, default=0),
        sa.Column('affected_services', postgresql.ARRAY(sa.String), default=list),
        sa.Column('affected_users', sa.Integer, default=0),
        sa.Column('customer_impact', sa.Text),
        sa.Column('status_page_updated', sa.Boolean, default=False),
        sa.Column('communication_sent', sa.Boolean, default=False),
        sa.Column('root_cause', sa.Text),
        sa.Column('resolution_summary', sa.Text),
        sa.Column('postmortem_url', sa.String(500)),
        sa.Column('time_to_acknowledge_seconds', sa.Integer),
        sa.Column('time_to_resolve_seconds', sa.Integer),
        sa.Column('pagerduty_incident_id', sa.String(100)),
        sa.Column('jira_ticket_id', sa.String(50)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_prod_incident_status_severity', 'production_alert_incidents', ['status', 'severity'])
    op.create_index('ix_prod_incident_tenant_triggered', 'production_alert_incidents', ['tenant_id', 'triggered_at'])

    # On-Call Schedules
    op.create_table(
        'production_on_call_schedules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('team_name', sa.String(255), nullable=False),
        sa.Column('members', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=list),
        sa.Column('rotation_type', sa.String(50)),
        sa.Column('rotation_start_day', sa.Integer),
        sa.Column('rotation_start_hour', sa.Integer, default=9),
        sa.Column('handoff_time', sa.String(10), default='09:00'),
        sa.Column('timezone', sa.String(50), default='UTC'),
        sa.Column('current_primary', postgresql.UUID(as_uuid=True)),
        sa.Column('current_secondary', postgresql.UUID(as_uuid=True)),
        sa.Column('next_rotation_at', sa.DateTime),
        sa.Column('pagerduty_schedule_id', sa.String(100)),
        sa.Column('opsgenie_schedule_id', sa.String(100)),
        sa.Column('enabled', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Escalation Policies
    op.create_table(
        'production_escalation_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('escalation_levels', postgresql.JSONB, default=list),
        sa.Column('repeat_enabled', sa.Boolean, default=False),
        sa.Column('repeat_limit', sa.Integer, default=3),
        sa.Column('require_acknowledgment', sa.Boolean, default=True),
        sa.Column('acknowledgment_timeout_minutes', sa.Integer, default=30),
        sa.Column('pagerduty_policy_id', sa.String(100)),
        sa.Column('opsgenie_policy_id', sa.String(100)),
        sa.Column('enabled', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    # ==========================================================================
    # Deployment Tables
    # ==========================================================================

    # Deployments
    op.create_table(
        'production_deployments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('deployment_number', sa.String(50)),
        sa.Column('service_name', sa.String(255), nullable=False),
        sa.Column('version', sa.String(100), nullable=False),
        sa.Column('previous_version', sa.String(100)),
        sa.Column('commit_sha', sa.String(40)),
        sa.Column('environment', sa.String(50), nullable=False),
        sa.Column('strategy', sa.String(50), default='rolling'),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('replicas', sa.Integer, default=2),
        sa.Column('config_changes', postgresql.JSONB, default=dict),
        sa.Column('scheduled_at', sa.DateTime),
        sa.Column('started_at', sa.DateTime),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('health_check_passed', sa.Boolean),
        sa.Column('health_check_attempts', sa.Integer, default=0),
        sa.Column('rolled_back', sa.Boolean, default=False),
        sa.Column('rollback_reason', sa.Text),
        sa.Column('rollback_deployment_id', postgresql.UUID(as_uuid=True)),
        sa.Column('requires_approval', sa.Boolean, default=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True)),
        sa.Column('approved_at', sa.DateTime),
        sa.Column('docker_image', sa.String(500)),
        sa.Column('helm_chart_version', sa.String(50)),
        sa.Column('release_notes', sa.Text),
        sa.Column('deployment_notes', sa.Text),
        sa.Column('duration_seconds', sa.Integer),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )
    op.create_index('ix_prod_deploy_service_env', 'production_deployments', ['service_name', 'environment'])
    op.create_index('ix_prod_deploy_status_started', 'production_deployments', ['status', 'started_at'])

    # Environment Promotions
    op.create_table(
        'production_environment_promotions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('service_name', sa.String(255), nullable=False),
        sa.Column('version', sa.String(100), nullable=False),
        sa.Column('source_environment', sa.String(50), nullable=False),
        sa.Column('target_environment', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('approval_required', sa.Boolean, default=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True)),
        sa.Column('approved_at', sa.DateTime),
        sa.Column('rejection_reason', sa.Text),
        sa.Column('tests_passed', sa.Boolean),
        sa.Column('security_scan_passed', sa.Boolean),
        sa.Column('pre_checks_result', postgresql.JSONB),
        sa.Column('deployment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('production_deployments.id')),
        sa.Column('requested_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('promoted_at', sa.DateTime),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Feature Flags
    op.create_table(
        'production_feature_flags',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('key', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('status', sa.String(50), default='disabled'),
        sa.Column('environment', sa.String(50)),
        sa.Column('percentage_rollout', sa.Float, default=0.0),
        sa.Column('targeted_users', postgresql.ARRAY(sa.String), default=list),
        sa.Column('targeted_tenants', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=list),
        sa.Column('variants', postgresql.JSONB, default=list),
        sa.Column('default_variant', sa.String(100)),
        sa.Column('rules', postgresql.JSONB, default=list),
        sa.Column('last_evaluated_at', sa.DateTime),
        sa.Column('evaluation_count', sa.Integer, default=0),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True)),
        sa.Column('owner_team', sa.String(255)),
        sa.Column('launchdarkly_key', sa.String(255)),
        sa.Column('unleash_name', sa.String(255)),
        sa.Column('expires_at', sa.DateTime),
        sa.Column('archived', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.UniqueConstraint('tenant_id', 'key', name='uq_feature_flag_tenant_key'),
    )

    # Database Migrations
    op.create_table(
        'production_database_migrations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('migration_id', sa.String(255), nullable=False),
        sa.Column('migration_name', sa.String(500)),
        sa.Column('database_name', sa.String(255), nullable=False),
        sa.Column('environment', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('started_at', sa.DateTime),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('duration_seconds', sa.Integer),
        sa.Column('rollback_available', sa.Boolean, default=True),
        sa.Column('rolled_back', sa.Boolean, default=False),
        sa.Column('rollback_at', sa.DateTime),
        sa.Column('error_message', sa.Text),
        sa.Column('error_details', postgresql.JSONB),
        sa.Column('up_sql', sa.Text),
        sa.Column('down_sql', sa.Text),
        sa.Column('pre_migration_checksum', sa.String(64)),
        sa.Column('post_migration_checksum', sa.String(64)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('executed_by', postgresql.UUID(as_uuid=True)),
    )

    # ==========================================================================
    # Backup & DR Tables
    # ==========================================================================

    # Backups
    op.create_table(
        'production_backups',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('backup_id', sa.String(100), unique=True),
        sa.Column('backup_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('source_database', sa.String(255), nullable=False),
        sa.Column('source_region', sa.String(100)),
        sa.Column('source_environment', sa.String(50), nullable=False),
        sa.Column('storage_location', sa.String(500)),
        sa.Column('storage_region', sa.String(100)),
        sa.Column('cross_region_copy', sa.Boolean, default=False),
        sa.Column('cross_region_location', sa.String(500)),
        sa.Column('size_bytes', sa.Float),
        sa.Column('started_at', sa.DateTime),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('duration_seconds', sa.Integer),
        sa.Column('encrypted', sa.Boolean, default=True),
        sa.Column('encryption_key_id', sa.String(255)),
        sa.Column('retention_days', sa.Integer, default=30),
        sa.Column('expires_at', sa.DateTime),
        sa.Column('verified', sa.Boolean, default=False),
        sa.Column('verified_at', sa.DateTime),
        sa.Column('verification_result', postgresql.JSONB),
        sa.Column('pitr_enabled', sa.Boolean, default=False),
        sa.Column('earliest_restore_time', sa.DateTime),
        sa.Column('latest_restore_time', sa.DateTime),
        sa.Column('metadata', postgresql.JSONB, default=dict),
        sa.Column('tags', postgresql.JSONB, default=dict),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )
    op.create_index('ix_prod_backup_status_env', 'production_backups', ['status', 'source_environment'])
    op.create_index('ix_prod_backup_tenant_created', 'production_backups', ['tenant_id', 'created_at'])

    # Restore Operations
    op.create_table(
        'production_restore_operations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('backup_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('production_backups.id')),
        sa.Column('restore_id', sa.String(100), unique=True),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('target_database', sa.String(255), nullable=False),
        sa.Column('target_environment', sa.String(50), nullable=False),
        sa.Column('restore_to_point_in_time', sa.DateTime),
        sa.Column('started_at', sa.DateTime),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('duration_seconds', sa.Integer),
        sa.Column('data_verification_passed', sa.Boolean),
        sa.Column('verification_details', postgresql.JSONB),
        sa.Column('error_message', sa.Text),
        sa.Column('retry_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('initiated_by', postgresql.UUID(as_uuid=True)),
    )

    # DR Plans
    op.create_table(
        'production_dr_plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('scenario', sa.String(50), nullable=False),
        sa.Column('rto_hours', sa.Float, nullable=False),
        sa.Column('rpo_hours', sa.Float, nullable=False),
        sa.Column('recovery_steps', postgresql.JSONB, default=list),
        sa.Column('communication_plan', postgresql.JSONB),
        sa.Column('escalation_contacts', postgresql.JSONB, default=list),
        sa.Column('primary_region', sa.String(100)),
        sa.Column('dr_region', sa.String(100)),
        sa.Column('affected_services', postgresql.ARRAY(sa.String), default=list),
        sa.Column('last_tested_at', sa.DateTime),
        sa.Column('last_test_result', sa.String(50)),
        sa.Column('next_test_date', sa.DateTime),
        sa.Column('test_frequency_days', sa.Integer, default=90),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('version', sa.Integer, default=1),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )

    # DR Drills
    op.create_table(
        'production_dr_drills',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('dr_plan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('production_dr_plans.id')),
        sa.Column('drill_id', sa.String(100), unique=True),
        sa.Column('status', sa.String(50), default='scheduled'),
        sa.Column('scheduled_at', sa.DateTime, nullable=False),
        sa.Column('started_at', sa.DateTime),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('participants', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=list),
        sa.Column('coordinator', postgresql.UUID(as_uuid=True)),
        sa.Column('steps_completed', postgresql.JSONB, default=list),
        sa.Column('issues_encountered', postgresql.JSONB, default=list),
        sa.Column('rto_achieved_minutes', sa.Float),
        sa.Column('rpo_achieved_minutes', sa.Float),
        sa.Column('rto_target_met', sa.Boolean),
        sa.Column('rpo_target_met', sa.Boolean),
        sa.Column('success', sa.Boolean),
        sa.Column('lessons_learned', sa.Text),
        sa.Column('action_items', postgresql.JSONB, default=list),
        sa.Column('drill_report_url', sa.String(500)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    # ==========================================================================
    # Runbook Tables
    # ==========================================================================

    # Runbooks
    op.create_table(
        'production_runbooks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('runbook_type', sa.String(50), nullable=False),
        sa.Column('steps', postgresql.JSONB, default=list),
        sa.Column('prerequisites', postgresql.JSONB, default=list),
        sa.Column('required_access', postgresql.ARRAY(sa.String), default=list),
        sa.Column('associated_alerts', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=list),
        sa.Column('affected_services', postgresql.ARRAY(sa.String), default=list),
        sa.Column('automated_steps', postgresql.JSONB, default=list),
        sa.Column('automation_script_url', sa.String(500)),
        sa.Column('estimated_duration_minutes', sa.Integer),
        sa.Column('difficulty_level', sa.String(20)),
        sa.Column('version', sa.Integer, default=1),
        sa.Column('last_reviewed_at', sa.DateTime),
        sa.Column('next_review_date', sa.DateTime),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True)),
        sa.Column('owner_team', sa.String(255)),
        sa.Column('times_used', sa.Integer, default=0),
        sa.Column('last_used_at', sa.DateTime),
        sa.Column('tags', postgresql.ARRAY(sa.String), default=list),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )

    # Add runbook_id FK to alert_rules after runbooks table exists
    op.create_foreign_key(
        'fk_alert_rules_runbook',
        'production_alert_rules',
        'production_runbooks',
        ['runbook_id'],
        ['id']
    )

    # Incident Playbooks
    op.create_table(
        'production_incident_playbooks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('symptoms', postgresql.JSONB, default=list),
        sa.Column('diagnosis_steps', postgresql.JSONB, default=list),
        sa.Column('immediate_actions', postgresql.JSONB, default=list),
        sa.Column('long_term_fixes', postgresql.JSONB, default=list),
        sa.Column('communication_template', sa.Text),
        sa.Column('stakeholders_to_notify', postgresql.JSONB, default=list),
        sa.Column('related_runbooks', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=list),
        sa.Column('related_alerts', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=list),
        sa.Column('times_used', sa.Integer, default=0),
        sa.Column('avg_resolution_minutes', sa.Float),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )

    # ==========================================================================
    # Go-Live Tables
    # ==========================================================================

    # Go-Live Checklists
    op.create_table(
        'production_go_live_checklists',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('target_go_live_date', sa.DateTime),
        sa.Column('environment', sa.String(50), default='production'),
        sa.Column('total_items', sa.Integer, default=0),
        sa.Column('completed_items', sa.Integer, default=0),
        sa.Column('blocked_items', sa.Integer, default=0),
        sa.Column('completion_percentage', sa.Float, default=0.0),
        sa.Column('is_ready', sa.Boolean, default=False),
        sa.Column('blockers', postgresql.JSONB, default=list),
        sa.Column('required_approvers', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=list),
        sa.Column('approvals_received', postgresql.JSONB, default=list),
        sa.Column('started_at', sa.DateTime),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('actual_go_live_at', sa.DateTime),
        sa.Column('release_notes_url', sa.String(500)),
        sa.Column('rollback_plan_url', sa.String(500)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )

    # Go-Live Checklist Items
    op.create_table(
        'production_go_live_checklist_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('checklist_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('production_go_live_checklists.id')),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('is_critical', sa.Boolean, default=False),
        sa.Column('is_blocker', sa.Boolean, default=False),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True)),
        sa.Column('owner_team', sa.String(255)),
        sa.Column('verification_method', sa.Text),
        sa.Column('evidence_url', sa.String(500)),
        sa.Column('depends_on', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=list),
        sa.Column('due_date', sa.DateTime),
        sa.Column('started_at', sa.DateTime),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('notes', sa.Text),
        sa.Column('blocker_reason', sa.Text),
        sa.Column('display_order', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_prod_checklist_item_category', 'production_go_live_checklist_items', ['checklist_id', 'category'])

    # Status Page Components
    op.create_table(
        'production_status_page_components',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('status', sa.String(50), default='healthy'),
        sa.Column('group_name', sa.String(255)),
        sa.Column('display_order', sa.Integer, default=0),
        sa.Column('health_check_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('production_health_checks.id')),
        sa.Column('show_on_public_page', sa.Boolean, default=True),
        sa.Column('show_uptime', sa.Boolean, default=True),
        sa.Column('statuspage_component_id', sa.String(100)),
        sa.Column('uptime_percentage', sa.Float),
        sa.Column('last_incident_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Status Page Incidents
    op.create_table(
        'production_status_page_incidents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('alert_incident_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('production_alert_incidents.id')),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('status', sa.String(50)),
        sa.Column('impact', sa.String(50)),
        sa.Column('affected_components', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=list),
        sa.Column('updates', postgresql.JSONB, default=list),
        sa.Column('started_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('resolved_at', sa.DateTime),
        sa.Column('statuspage_incident_id', sa.String(100)),
        sa.Column('is_public', sa.Boolean, default=True),
        sa.Column('scheduled_maintenance', sa.Boolean, default=False),
        sa.Column('scheduled_start', sa.DateTime),
        sa.Column('scheduled_end', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_table('production_status_page_incidents')
    op.drop_table('production_status_page_components')
    op.drop_index('ix_prod_checklist_item_category')
    op.drop_table('production_go_live_checklist_items')
    op.drop_table('production_go_live_checklists')
    op.drop_table('production_incident_playbooks')
    op.drop_constraint('fk_alert_rules_runbook', 'production_alert_rules', type_='foreignkey')
    op.drop_table('production_runbooks')
    op.drop_table('production_dr_drills')
    op.drop_table('production_dr_plans')
    op.drop_table('production_restore_operations')
    op.drop_index('ix_prod_backup_tenant_created')
    op.drop_index('ix_prod_backup_status_env')
    op.drop_table('production_backups')
    op.drop_table('production_database_migrations')
    op.drop_table('production_feature_flags')
    op.drop_table('production_environment_promotions')
    op.drop_index('ix_prod_deploy_status_started')
    op.drop_index('ix_prod_deploy_service_env')
    op.drop_table('production_deployments')
    op.drop_table('production_escalation_policies')
    op.drop_table('production_on_call_schedules')
    op.drop_index('ix_prod_incident_tenant_triggered')
    op.drop_index('ix_prod_incident_status_severity')
    op.drop_table('production_alert_incidents')
    op.drop_table('production_alert_rules')
    op.drop_index('ix_prod_sli_slo_timestamp')
    op.drop_table('production_sli_records')
    op.drop_table('production_slo_definitions')
    op.drop_index('ix_prod_health_service_type')
    op.drop_table('production_health_checks')
    op.drop_table('production_dashboards')
    op.drop_table('production_metric_definitions')
    op.drop_table('production_network_configs')
    op.drop_table('production_auto_scaling_configs')
    op.drop_index('ix_prod_resource_type_status')
    op.drop_index('ix_prod_resource_tenant_env')
    op.drop_table('production_infrastructure_resources')

"""EPIC-023: Quality & Testing

Revision ID: 023_quality_testing
Revises: 022_hipaa_compliance
Create Date: 2024-11-25

Creates tables for:
- Test suites, runs, and results
- Code coverage reports and thresholds
- Performance test scenarios and results
- Security scans and vulnerabilities
- Test data management
- Flaky test tracking
- Quality gates
- CI/CD pipeline tracking
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '023_quality_testing'
down_revision = '022_hipaa_compliance'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ==========================================================================
    # Test Suite and Run Tables
    # ==========================================================================

    op.create_table(
        'quality_test_suites',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('test_type', sa.String(50), nullable=False),
        sa.Column('file_patterns', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('exclude_patterns', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('timeout_seconds', sa.Integer, default=3600),
        sa.Column('parallel_workers', sa.Integer, default=4),
        sa.Column('retry_count', sa.Integer, default=2),
        sa.Column('tags', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('metadata', postgresql.JSONB, default={}),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('last_run_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'quality_test_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('suite_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quality_test_suites.id')),
        sa.Column('run_number', sa.Integer, nullable=False),
        sa.Column('branch', sa.String(255)),
        sa.Column('commit_sha', sa.String(40)),
        sa.Column('pull_request_id', sa.String(50)),
        sa.Column('environment', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='queued'),
        sa.Column('triggered_by', sa.String(255)),
        sa.Column('started_at', sa.DateTime),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('duration_seconds', sa.Float),
        sa.Column('total_tests', sa.Integer, default=0),
        sa.Column('passed_tests', sa.Integer, default=0),
        sa.Column('failed_tests', sa.Integer, default=0),
        sa.Column('skipped_tests', sa.Integer, default=0),
        sa.Column('error_tests', sa.Integer, default=0),
        sa.Column('flaky_tests', sa.Integer, default=0),
        sa.Column('config', postgresql.JSONB, default={}),
        sa.Column('error_message', sa.Text),
        sa.Column('error_stacktrace', sa.Text),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_test_runs_status_env', 'quality_test_runs', ['status', 'environment'])
    op.create_index('ix_test_runs_branch_commit', 'quality_test_runs', ['branch', 'commit_sha'])

    op.create_table(
        'quality_test_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('test_run_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quality_test_runs.id'), nullable=False),
        sa.Column('test_name', sa.String(500), nullable=False),
        sa.Column('test_file', sa.String(500)),
        sa.Column('test_class', sa.String(255)),
        sa.Column('test_method', sa.String(255)),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('duration_ms', sa.Float),
        sa.Column('retry_count', sa.Integer, default=0),
        sa.Column('failure_message', sa.Text),
        sa.Column('failure_stacktrace', sa.Text),
        sa.Column('failure_type', sa.String(255)),
        sa.Column('assertions_passed', sa.Integer, default=0),
        sa.Column('assertions_failed', sa.Integer, default=0),
        sa.Column('stdout', sa.Text),
        sa.Column('stderr', sa.Text),
        sa.Column('artifacts', postgresql.JSONB, default=[]),
        sa.Column('tags', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('parameters', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_test_results_status', 'quality_test_results', ['status'])
    op.create_index('ix_test_results_test_name', 'quality_test_results', ['test_name'])

    # ==========================================================================
    # Coverage Tables
    # ==========================================================================

    op.create_table(
        'quality_coverage_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('test_run_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quality_test_runs.id')),
        sa.Column('branch', sa.String(255)),
        sa.Column('commit_sha', sa.String(40)),
        sa.Column('line_coverage', sa.Float),
        sa.Column('branch_coverage', sa.Float),
        sa.Column('function_coverage', sa.Float),
        sa.Column('statement_coverage', sa.Float),
        sa.Column('total_lines', sa.Integer),
        sa.Column('covered_lines', sa.Integer),
        sa.Column('total_branches', sa.Integer),
        sa.Column('covered_branches', sa.Integer),
        sa.Column('total_functions', sa.Integer),
        sa.Column('covered_functions', sa.Integer),
        sa.Column('line_threshold', sa.Float, default=80.0),
        sa.Column('branch_threshold', sa.Float, default=80.0),
        sa.Column('threshold_passed', sa.Boolean),
        sa.Column('coverage_delta', sa.Float),
        sa.Column('previous_coverage', sa.Float),
        sa.Column('html_report_url', sa.String(500)),
        sa.Column('xml_report_url', sa.String(500)),
        sa.Column('json_report_url', sa.String(500)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_coverage_branch_commit', 'quality_coverage_reports', ['branch', 'commit_sha'])

    op.create_table(
        'quality_file_coverages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('report_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quality_coverage_reports.id'), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('package_name', sa.String(255)),
        sa.Column('line_coverage', sa.Float),
        sa.Column('branch_coverage', sa.Float),
        sa.Column('function_coverage', sa.Float),
        sa.Column('total_lines', sa.Integer),
        sa.Column('covered_lines', sa.Integer),
        sa.Column('uncovered_lines', postgresql.ARRAY(sa.Integer), default=[]),
    )

    op.create_table(
        'quality_coverage_thresholds',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('line_threshold', sa.Float, default=80.0),
        sa.Column('branch_threshold', sa.Float, default=80.0),
        sa.Column('function_threshold', sa.Float, default=80.0),
        sa.Column('is_blocking', sa.Boolean, default=True),
        sa.Column('applies_to_branches', postgresql.ARRAY(sa.String), default=['main', 'master']),
        sa.Column('excluded_paths', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    # ==========================================================================
    # Performance Testing Tables
    # ==========================================================================

    op.create_table(
        'quality_performance_scenarios',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('test_type', sa.String(50), nullable=False),
        sa.Column('target_url', sa.String(500)),
        sa.Column('target_endpoints', postgresql.JSONB, default=[]),
        sa.Column('virtual_users', sa.Integer, default=100),
        sa.Column('ramp_up_seconds', sa.Integer, default=60),
        sa.Column('duration_seconds', sa.Integer, default=300),
        sa.Column('max_latency_p95_ms', sa.Integer, default=500),
        sa.Column('max_latency_p99_ms', sa.Integer, default=1000),
        sa.Column('max_error_rate_percent', sa.Float, default=1.0),
        sa.Column('min_throughput_rps', sa.Float),
        sa.Column('k6_script', sa.Text),
        sa.Column('script_config', postgresql.JSONB, default={}),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'quality_performance_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('scenario_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quality_performance_scenarios.id')),
        sa.Column('branch', sa.String(255)),
        sa.Column('commit_sha', sa.String(40)),
        sa.Column('environment', sa.String(50), nullable=False),
        sa.Column('started_at', sa.DateTime, nullable=False),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('duration_seconds', sa.Float),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('thresholds_passed', sa.Boolean),
        sa.Column('total_requests', sa.Integer),
        sa.Column('successful_requests', sa.Integer),
        sa.Column('failed_requests', sa.Integer),
        sa.Column('latency_p50_ms', sa.Float),
        sa.Column('latency_p95_ms', sa.Float),
        sa.Column('latency_p99_ms', sa.Float),
        sa.Column('latency_min_ms', sa.Float),
        sa.Column('latency_max_ms', sa.Float),
        sa.Column('latency_avg_ms', sa.Float),
        sa.Column('requests_per_second', sa.Float),
        sa.Column('bytes_received', sa.BigInteger),
        sa.Column('bytes_sent', sa.BigInteger),
        sa.Column('peak_concurrent_users', sa.Integer),
        sa.Column('error_rate_percent', sa.Float),
        sa.Column('error_breakdown', postgresql.JSONB, default={}),
        sa.Column('baseline_comparison', postgresql.JSONB),
        sa.Column('performance_degradation_percent', sa.Float),
        sa.Column('report_url', sa.String(500)),
        sa.Column('grafana_dashboard_url', sa.String(500)),
        sa.Column('raw_metrics_url', sa.String(500)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'quality_endpoint_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('test_result_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quality_performance_results.id'), nullable=False),
        sa.Column('endpoint_url', sa.String(500), nullable=False),
        sa.Column('http_method', sa.String(10)),
        sa.Column('total_requests', sa.Integer),
        sa.Column('successful_requests', sa.Integer),
        sa.Column('failed_requests', sa.Integer),
        sa.Column('latency_p50_ms', sa.Float),
        sa.Column('latency_p95_ms', sa.Float),
        sa.Column('latency_p99_ms', sa.Float),
        sa.Column('latency_avg_ms', sa.Float),
        sa.Column('requests_per_second', sa.Float),
    )

    op.create_table(
        'quality_performance_baselines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('scenario_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quality_performance_scenarios.id')),
        sa.Column('test_result_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quality_performance_results.id')),
        sa.Column('latency_p50_ms', sa.Float),
        sa.Column('latency_p95_ms', sa.Float),
        sa.Column('latency_p99_ms', sa.Float),
        sa.Column('throughput_rps', sa.Float),
        sa.Column('error_rate_percent', sa.Float),
        sa.Column('latency_tolerance_percent', sa.Float, default=10.0),
        sa.Column('throughput_tolerance_percent', sa.Float, default=10.0),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )

    # ==========================================================================
    # Security Testing Tables
    # ==========================================================================

    op.create_table(
        'quality_security_scans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('scan_type', sa.String(50), nullable=False),
        sa.Column('branch', sa.String(255)),
        sa.Column('commit_sha', sa.String(40)),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('started_at', sa.DateTime, nullable=False),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('duration_seconds', sa.Float),
        sa.Column('scanner_name', sa.String(100)),
        sa.Column('scanner_version', sa.String(50)),
        sa.Column('total_findings', sa.Integer, default=0),
        sa.Column('critical_findings', sa.Integer, default=0),
        sa.Column('high_findings', sa.Integer, default=0),
        sa.Column('medium_findings', sa.Integer, default=0),
        sa.Column('low_findings', sa.Integer, default=0),
        sa.Column('info_findings', sa.Integer, default=0),
        sa.Column('gate_passed', sa.Boolean),
        sa.Column('blocking_findings', sa.Integer, default=0),
        sa.Column('report_url', sa.String(500)),
        sa.Column('sarif_url', sa.String(500)),
        sa.Column('scan_config', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_security_scans_type_status', 'quality_security_scans', ['scan_type', 'status'])

    op.create_table(
        'quality_vulnerabilities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('scan_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quality_security_scans.id')),
        sa.Column('vulnerability_id', sa.String(100)),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('category', sa.String(100)),
        sa.Column('cwe_id', sa.String(20)),
        sa.Column('cve_id', sa.String(20)),
        sa.Column('file_path', sa.String(500)),
        sa.Column('line_number', sa.Integer),
        sa.Column('column_number', sa.Integer),
        sa.Column('code_snippet', sa.Text),
        sa.Column('package_name', sa.String(255)),
        sa.Column('package_version', sa.String(50)),
        sa.Column('fixed_version', sa.String(50)),
        sa.Column('image_name', sa.String(255)),
        sa.Column('layer_id', sa.String(100)),
        sa.Column('status', sa.String(50), nullable=False, default='open'),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True)),
        sa.Column('due_date', sa.DateTime),
        sa.Column('resolution_notes', sa.Text),
        sa.Column('resolved_at', sa.DateTime),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True)),
        sa.Column('cvss_score', sa.Float),
        sa.Column('cvss_vector', sa.String(100)),
        sa.Column('is_suppressed', sa.Boolean, default=False),
        sa.Column('suppression_reason', sa.Text),
        sa.Column('suppressed_by', postgresql.UUID(as_uuid=True)),
        sa.Column('suppressed_until', sa.DateTime),
        sa.Column('references', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('remediation_guidance', sa.Text),
        sa.Column('first_detected_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('last_seen_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_vulnerabilities_severity_status', 'quality_vulnerabilities', ['severity', 'status'])
    op.create_index('ix_vulnerabilities_cve', 'quality_vulnerabilities', ['cve_id'])

    op.create_table(
        'quality_security_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('block_critical', sa.Boolean, default=True),
        sa.Column('block_high', sa.Boolean, default=True),
        sa.Column('block_medium', sa.Boolean, default=False),
        sa.Column('max_critical_age_days', sa.Integer, default=1),
        sa.Column('max_high_age_days', sa.Integer, default=7),
        sa.Column('max_medium_age_days', sa.Integer, default=30),
        sa.Column('exempt_paths', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('exempt_rules', postgresql.ARRAY(sa.String), default=[]),
        sa.Column('notify_on_critical', sa.Boolean, default=True),
        sa.Column('notification_channels', postgresql.JSONB, default=[]),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    # ==========================================================================
    # Test Data Management Tables
    # ==========================================================================

    op.create_table(
        'quality_test_data_sets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('data_type', sa.String(50), nullable=False),
        sa.Column('record_count', sa.Integer),
        sa.Column('generator_config', postgresql.JSONB, default={}),
        sa.Column('seed', sa.Integer),
        sa.Column('storage_url', sa.String(500)),
        sa.Column('file_format', sa.String(50)),
        sa.Column('file_size_bytes', sa.BigInteger),
        sa.Column('checksum', sa.String(64)),
        sa.Column('contains_pii', sa.Boolean, default=False),
        sa.Column('pii_masked', sa.Boolean, default=True),
        sa.Column('masking_rules', postgresql.JSONB, default={}),
        sa.Column('compatible_environments', postgresql.ARRAY(sa.String), default=['local', 'ci', 'staging']),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
    )

    op.create_table(
        'quality_data_seed_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('data_set_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quality_test_data_sets.id'), nullable=False),
        sa.Column('environment', sa.String(50), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('started_at', sa.DateTime, nullable=False),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('duration_seconds', sa.Float),
        sa.Column('records_seeded', sa.Integer),
        sa.Column('records_failed', sa.Integer),
        sa.Column('error_message', sa.Text),
        sa.Column('executed_by', postgresql.UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'quality_synthetic_generators',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('data_type', sa.String(50), nullable=False),
        sa.Column('fhir_resource_type', sa.String(100)),
        sa.Column('fhir_profile', sa.String(500)),
        sa.Column('field_generators', postgresql.JSONB, nullable=False),
        sa.Column('relationships', postgresql.JSONB, default={}),
        sa.Column('validation_schema', postgresql.JSONB),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    # ==========================================================================
    # Flaky Test Tables
    # ==========================================================================

    op.create_table(
        'quality_flaky_tests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('test_name', sa.String(500), nullable=False, unique=True),
        sa.Column('test_file', sa.String(500)),
        sa.Column('test_suite_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quality_test_suites.id')),
        sa.Column('status', sa.String(50), nullable=False, default='detected'),
        sa.Column('first_detected_at', sa.DateTime, nullable=False),
        sa.Column('last_flake_at', sa.DateTime),
        sa.Column('flake_count', sa.Integer, default=1),
        sa.Column('total_runs', sa.Integer, default=1),
        sa.Column('flake_rate', sa.Float),
        sa.Column('failure_patterns', postgresql.JSONB, default=[]),
        sa.Column('suspected_cause', sa.Text),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True)),
        sa.Column('resolution_notes', sa.Text),
        sa.Column('fixed_at', sa.DateTime),
        sa.Column('fixed_by', postgresql.UUID(as_uuid=True)),
        sa.Column('quarantined_at', sa.DateTime),
        sa.Column('quarantine_reason', sa.Text),
        sa.Column('quarantine_expires_at', sa.DateTime),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_flaky_tests_status', 'quality_flaky_tests', ['status'])

    # ==========================================================================
    # Quality Gate Tables
    # ==========================================================================

    op.create_table(
        'quality_gates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('conditions', postgresql.JSONB, nullable=False),
        sa.Column('applies_to_branches', postgresql.ARRAY(sa.String), default=['main', 'master']),
        sa.Column('applies_to_environments', postgresql.ARRAY(sa.String), default=['ci', 'staging']),
        sa.Column('is_blocking', sa.Boolean, default=True),
        sa.Column('warn_only', sa.Boolean, default=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        'quality_gate_evaluations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('gate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('quality_gates.id'), nullable=False),
        sa.Column('branch', sa.String(255)),
        sa.Column('commit_sha', sa.String(40)),
        sa.Column('pull_request_id', sa.String(50)),
        sa.Column('environment', sa.String(50)),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('condition_results', postgresql.JSONB, nullable=False),
        sa.Column('total_conditions', sa.Integer),
        sa.Column('passed_conditions', sa.Integer),
        sa.Column('failed_conditions', sa.Integer),
        sa.Column('evaluated_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_gate_evals_branch_commit', 'quality_gate_evaluations', ['branch', 'commit_sha'])

    # ==========================================================================
    # CI/CD Tables
    # ==========================================================================

    op.create_table(
        'quality_ci_pipelines',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('pipeline_id', sa.String(100), nullable=False),
        sa.Column('workflow_name', sa.String(255)),
        sa.Column('run_number', sa.Integer),
        sa.Column('branch', sa.String(255)),
        sa.Column('commit_sha', sa.String(40)),
        sa.Column('commit_message', sa.Text),
        sa.Column('pull_request_id', sa.String(50)),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('started_at', sa.DateTime, nullable=False),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('duration_seconds', sa.Float),
        sa.Column('triggered_by', sa.String(255)),
        sa.Column('trigger_event', sa.String(100)),
        sa.Column('jobs_total', sa.Integer),
        sa.Column('jobs_passed', sa.Integer),
        sa.Column('jobs_failed', sa.Integer),
        sa.Column('test_run_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=[]),
        sa.Column('coverage_report_id', postgresql.UUID(as_uuid=True)),
        sa.Column('security_scan_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=[]),
        sa.Column('quality_gate_evaluation_id', postgresql.UUID(as_uuid=True)),
        sa.Column('logs_url', sa.String(500)),
        sa.Column('artifacts_url', sa.String(500)),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index('ix_ci_pipelines_branch_status', 'quality_ci_pipelines', ['branch', 'status'])
    op.create_index('ix_ci_pipelines_pr', 'quality_ci_pipelines', ['pull_request_id'])

    op.create_table(
        'quality_test_trend_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('date', sa.DateTime, nullable=False),
        sa.Column('total_tests', sa.Integer),
        sa.Column('passed_tests', sa.Integer),
        sa.Column('failed_tests', sa.Integer),
        sa.Column('skipped_tests', sa.Integer),
        sa.Column('flaky_tests', sa.Integer),
        sa.Column('pass_rate', sa.Float),
        sa.Column('line_coverage', sa.Float),
        sa.Column('branch_coverage', sa.Float),
        sa.Column('avg_latency_p95', sa.Float),
        sa.Column('open_vulnerabilities', sa.Integer),
        sa.Column('critical_vulnerabilities', sa.Integer),
        sa.Column('pipeline_success_rate', sa.Float),
        sa.Column('avg_pipeline_duration', sa.Float),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('tenant_id', 'date', name='uq_trend_metrics_tenant_date'),
    )
    op.create_index('ix_trend_metrics_date', 'quality_test_trend_metrics', ['date'])


def downgrade() -> None:
    op.drop_table('quality_test_trend_metrics')
    op.drop_table('quality_ci_pipelines')
    op.drop_table('quality_gate_evaluations')
    op.drop_table('quality_gates')
    op.drop_table('quality_flaky_tests')
    op.drop_table('quality_synthetic_generators')
    op.drop_table('quality_data_seed_executions')
    op.drop_table('quality_test_data_sets')
    op.drop_table('quality_security_policies')
    op.drop_table('quality_vulnerabilities')
    op.drop_table('quality_security_scans')
    op.drop_table('quality_performance_baselines')
    op.drop_table('quality_endpoint_metrics')
    op.drop_table('quality_performance_results')
    op.drop_table('quality_performance_scenarios')
    op.drop_table('quality_coverage_thresholds')
    op.drop_table('quality_file_coverages')
    op.drop_table('quality_coverage_reports')
    op.drop_table('quality_test_results')
    op.drop_table('quality_test_runs')
    op.drop_table('quality_test_suites')

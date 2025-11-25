"""
Quality & Testing Models

SQLAlchemy models for EPIC-023: Quality & Testing
Including test runs, coverage reports, performance tests, security scans,
test data management, and CI/CD integration.
"""

from datetime import datetime
from enum import Enum
from uuid import uuid4

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY, JSONB
from sqlalchemy.orm import relationship

from shared.database import Base


# =============================================================================
# Enums
# =============================================================================

class TestType(str, Enum):
    """Types of tests."""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"
    SMOKE = "smoke"
    REGRESSION = "regression"
    ACCEPTANCE = "acceptance"


class TestStatus(str, Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    TIMEOUT = "timeout"
    FLAKY = "flaky"


class TestRunStatus(str, Enum):
    """Test run status."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TestEnvironment(str, Enum):
    """Test execution environment."""
    LOCAL = "local"
    CI = "ci"
    STAGING = "staging"
    PRODUCTION = "production"


class CoverageType(str, Enum):
    """Code coverage type."""
    LINE = "line"
    BRANCH = "branch"
    FUNCTION = "function"
    STATEMENT = "statement"


class PerformanceTestType(str, Enum):
    """Performance test types."""
    LOAD = "load"
    STRESS = "stress"
    SPIKE = "spike"
    SOAK = "soak"
    BASELINE = "baseline"


class PerformanceMetricType(str, Enum):
    """Performance metric types."""
    LATENCY_P50 = "latency_p50"
    LATENCY_P95 = "latency_p95"
    LATENCY_P99 = "latency_p99"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    CONCURRENT_USERS = "concurrent_users"
    RESPONSE_TIME = "response_time"


class SecurityScanType(str, Enum):
    """Security scan types."""
    SAST = "sast"
    DAST = "dast"
    DEPENDENCY = "dependency"
    CONTAINER = "container"
    SECRETS = "secrets"
    API = "api"


class VulnerabilitySeverity(str, Enum):
    """Vulnerability severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityStatus(str, Enum):
    """Vulnerability status."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    FIXED = "fixed"
    WONT_FIX = "wont_fix"
    FALSE_POSITIVE = "false_positive"
    ACCEPTED = "accepted"


class QualityGateStatus(str, Enum):
    """Quality gate status."""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


class DataGeneratorType(str, Enum):
    """Test data generator types."""
    PATIENT = "patient"
    PRACTITIONER = "practitioner"
    ORGANIZATION = "organization"
    ENCOUNTER = "encounter"
    OBSERVATION = "observation"
    CONDITION = "condition"
    MEDICATION = "medication"
    APPOINTMENT = "appointment"
    CLAIM = "claim"


class FlakyTestStatus(str, Enum):
    """Flaky test status."""
    DETECTED = "detected"
    QUARANTINED = "quarantined"
    INVESTIGATING = "investigating"
    FIXED = "fixed"
    PERMANENT_QUARANTINE = "permanent_quarantine"


# =============================================================================
# Test Run Models
# =============================================================================

class TestSuite(Base):
    """Test suite definition."""
    __tablename__ = "quality_test_suites"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text)
    test_type = Column(SQLEnum(TestType), nullable=False)

    file_patterns = Column(ARRAY(String), default=[])
    exclude_patterns = Column(ARRAY(String), default=[])
    timeout_seconds = Column(Integer, default=3600)
    parallel_workers = Column(Integer, default=4)
    retry_count = Column(Integer, default=2)

    tags = Column(ARRAY(String), default=[])
    metadata = Column(JSONB, default={})

    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    test_runs = relationship("TestRun", back_populates="suite")


class TestRun(Base):
    """Test execution run."""
    __tablename__ = "quality_test_runs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    suite_id = Column(PGUUID(as_uuid=True), ForeignKey("quality_test_suites.id"))

    run_number = Column(Integer, nullable=False)
    branch = Column(String(255))
    commit_sha = Column(String(40))
    pull_request_id = Column(String(50))

    environment = Column(SQLEnum(TestEnvironment), nullable=False)
    status = Column(SQLEnum(TestRunStatus), nullable=False, default=TestRunStatus.QUEUED)
    triggered_by = Column(String(255))

    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)

    total_tests = Column(Integer, default=0)
    passed_tests = Column(Integer, default=0)
    failed_tests = Column(Integer, default=0)
    skipped_tests = Column(Integer, default=0)
    error_tests = Column(Integer, default=0)
    flaky_tests = Column(Integer, default=0)

    config = Column(JSONB, default={})

    error_message = Column(Text)
    error_stacktrace = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    suite = relationship("TestSuite", back_populates="test_runs")
    test_results = relationship("TestResult", back_populates="test_run")

    __table_args__ = (
        Index("ix_test_runs_status_env", "status", "environment"),
        Index("ix_test_runs_branch_commit", "branch", "commit_sha"),
    )


class TestResult(Base):
    """Individual test result."""
    __tablename__ = "quality_test_results"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    test_run_id = Column(PGUUID(as_uuid=True), ForeignKey("quality_test_runs.id"), nullable=False)

    test_name = Column(String(500), nullable=False)
    test_file = Column(String(500))
    test_class = Column(String(255))
    test_method = Column(String(255))

    status = Column(SQLEnum(TestStatus), nullable=False)
    duration_ms = Column(Float)
    retry_count = Column(Integer, default=0)

    failure_message = Column(Text)
    failure_stacktrace = Column(Text)
    failure_type = Column(String(255))

    assertions_passed = Column(Integer, default=0)
    assertions_failed = Column(Integer, default=0)

    stdout = Column(Text)
    stderr = Column(Text)
    artifacts = Column(JSONB, default=[])

    tags = Column(ARRAY(String), default=[])
    parameters = Column(JSONB, default={})

    created_at = Column(DateTime, default=datetime.utcnow)

    test_run = relationship("TestRun", back_populates="test_results")

    __table_args__ = (
        Index("ix_test_results_status", "status"),
        Index("ix_test_results_test_name", "test_name"),
    )


# =============================================================================
# Code Coverage Models
# =============================================================================

class CoverageReport(Base):
    """Code coverage report."""
    __tablename__ = "quality_coverage_reports"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    test_run_id = Column(PGUUID(as_uuid=True), ForeignKey("quality_test_runs.id"))

    branch = Column(String(255))
    commit_sha = Column(String(40))

    line_coverage = Column(Float)
    branch_coverage = Column(Float)
    function_coverage = Column(Float)
    statement_coverage = Column(Float)

    total_lines = Column(Integer)
    covered_lines = Column(Integer)
    total_branches = Column(Integer)
    covered_branches = Column(Integer)
    total_functions = Column(Integer)
    covered_functions = Column(Integer)

    line_threshold = Column(Float, default=80.0)
    branch_threshold = Column(Float, default=80.0)
    threshold_passed = Column(Boolean)

    coverage_delta = Column(Float)
    previous_coverage = Column(Float)

    html_report_url = Column(String(500))
    xml_report_url = Column(String(500))
    json_report_url = Column(String(500))

    created_at = Column(DateTime, default=datetime.utcnow)

    file_coverages = relationship("FileCoverage", back_populates="report")

    __table_args__ = (
        Index("ix_coverage_branch_commit", "branch", "commit_sha"),
    )


class FileCoverage(Base):
    """Per-file code coverage."""
    __tablename__ = "quality_file_coverages"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    report_id = Column(PGUUID(as_uuid=True), ForeignKey("quality_coverage_reports.id"), nullable=False)

    file_path = Column(String(500), nullable=False)
    package_name = Column(String(255))

    line_coverage = Column(Float)
    branch_coverage = Column(Float)
    function_coverage = Column(Float)

    total_lines = Column(Integer)
    covered_lines = Column(Integer)
    uncovered_lines = Column(ARRAY(Integer), default=[])

    report = relationship("CoverageReport", back_populates="file_coverages")


class CoverageThreshold(Base):
    """Coverage threshold configuration."""
    __tablename__ = "quality_coverage_thresholds"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text)

    line_threshold = Column(Float, default=80.0)
    branch_threshold = Column(Float, default=80.0)
    function_threshold = Column(Float, default=80.0)

    is_blocking = Column(Boolean, default=True)
    applies_to_branches = Column(ARRAY(String), default=["main", "master"])

    excluded_paths = Column(ARRAY(String), default=[])

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# =============================================================================
# Performance Test Models
# =============================================================================

class PerformanceTestScenario(Base):
    """Performance test scenario definition."""
    __tablename__ = "quality_performance_scenarios"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text)
    test_type = Column(SQLEnum(PerformanceTestType), nullable=False)

    target_url = Column(String(500))
    target_endpoints = Column(JSONB, default=[])

    virtual_users = Column(Integer, default=100)
    ramp_up_seconds = Column(Integer, default=60)
    duration_seconds = Column(Integer, default=300)

    max_latency_p95_ms = Column(Integer, default=500)
    max_latency_p99_ms = Column(Integer, default=1000)
    max_error_rate_percent = Column(Float, default=1.0)
    min_throughput_rps = Column(Float)

    k6_script = Column(Text)
    script_config = Column(JSONB, default={})

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    test_results = relationship("PerformanceTestResult", back_populates="scenario")


class PerformanceTestResult(Base):
    """Performance test execution result."""
    __tablename__ = "quality_performance_results"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    scenario_id = Column(PGUUID(as_uuid=True), ForeignKey("quality_performance_scenarios.id"))

    branch = Column(String(255))
    commit_sha = Column(String(40))
    environment = Column(SQLEnum(TestEnvironment), nullable=False)

    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)

    status = Column(SQLEnum(TestRunStatus), nullable=False)
    thresholds_passed = Column(Boolean)

    total_requests = Column(Integer)
    successful_requests = Column(Integer)
    failed_requests = Column(Integer)

    latency_p50_ms = Column(Float)
    latency_p95_ms = Column(Float)
    latency_p99_ms = Column(Float)
    latency_min_ms = Column(Float)
    latency_max_ms = Column(Float)
    latency_avg_ms = Column(Float)

    requests_per_second = Column(Float)
    bytes_received = Column(Integer)
    bytes_sent = Column(Integer)

    peak_concurrent_users = Column(Integer)

    error_rate_percent = Column(Float)
    error_breakdown = Column(JSONB, default={})

    baseline_comparison = Column(JSONB)
    performance_degradation_percent = Column(Float)

    report_url = Column(String(500))
    grafana_dashboard_url = Column(String(500))
    raw_metrics_url = Column(String(500))

    created_at = Column(DateTime, default=datetime.utcnow)

    scenario = relationship("PerformanceTestScenario", back_populates="test_results")
    endpoint_metrics = relationship("EndpointPerformanceMetric", back_populates="test_result")


class EndpointPerformanceMetric(Base):
    """Per-endpoint performance metrics."""
    __tablename__ = "quality_endpoint_metrics"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    test_result_id = Column(PGUUID(as_uuid=True), ForeignKey("quality_performance_results.id"), nullable=False)

    endpoint_url = Column(String(500), nullable=False)
    http_method = Column(String(10))

    total_requests = Column(Integer)
    successful_requests = Column(Integer)
    failed_requests = Column(Integer)

    latency_p50_ms = Column(Float)
    latency_p95_ms = Column(Float)
    latency_p99_ms = Column(Float)
    latency_avg_ms = Column(Float)

    requests_per_second = Column(Float)

    test_result = relationship("PerformanceTestResult", back_populates="endpoint_metrics")


class PerformanceBaseline(Base):
    """Performance baseline for comparison."""
    __tablename__ = "quality_performance_baselines"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    scenario_id = Column(PGUUID(as_uuid=True), ForeignKey("quality_performance_scenarios.id"))

    test_result_id = Column(PGUUID(as_uuid=True), ForeignKey("quality_performance_results.id"))

    latency_p50_ms = Column(Float)
    latency_p95_ms = Column(Float)
    latency_p99_ms = Column(Float)
    throughput_rps = Column(Float)
    error_rate_percent = Column(Float)

    latency_tolerance_percent = Column(Float, default=10.0)
    throughput_tolerance_percent = Column(Float, default=10.0)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(PGUUID(as_uuid=True))


# =============================================================================
# Security Test Models
# =============================================================================

class SecurityScan(Base):
    """Security scan execution."""
    __tablename__ = "quality_security_scans"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    scan_type = Column(SQLEnum(SecurityScanType), nullable=False)
    branch = Column(String(255))
    commit_sha = Column(String(40))

    status = Column(SQLEnum(TestRunStatus), nullable=False)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)

    scanner_name = Column(String(100))
    scanner_version = Column(String(50))

    total_findings = Column(Integer, default=0)
    critical_findings = Column(Integer, default=0)
    high_findings = Column(Integer, default=0)
    medium_findings = Column(Integer, default=0)
    low_findings = Column(Integer, default=0)
    info_findings = Column(Integer, default=0)

    gate_passed = Column(Boolean)
    blocking_findings = Column(Integer, default=0)

    report_url = Column(String(500))
    sarif_url = Column(String(500))

    scan_config = Column(JSONB, default={})

    created_at = Column(DateTime, default=datetime.utcnow)

    vulnerabilities = relationship("Vulnerability", back_populates="scan")

    __table_args__ = (
        Index("ix_security_scans_type_status", "scan_type", "status"),
    )


class Vulnerability(Base):
    """Security vulnerability finding."""
    __tablename__ = "quality_vulnerabilities"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    scan_id = Column(PGUUID(as_uuid=True), ForeignKey("quality_security_scans.id"))

    vulnerability_id = Column(String(100))
    title = Column(String(500), nullable=False)
    description = Column(Text)

    severity = Column(SQLEnum(VulnerabilitySeverity), nullable=False)
    category = Column(String(100))
    cwe_id = Column(String(20))
    cve_id = Column(String(20))

    file_path = Column(String(500))
    line_number = Column(Integer)
    column_number = Column(Integer)
    code_snippet = Column(Text)

    package_name = Column(String(255))
    package_version = Column(String(50))
    fixed_version = Column(String(50))

    image_name = Column(String(255))
    layer_id = Column(String(100))

    status = Column(SQLEnum(VulnerabilityStatus), nullable=False, default=VulnerabilityStatus.OPEN)
    assigned_to = Column(PGUUID(as_uuid=True))
    due_date = Column(DateTime)

    resolution_notes = Column(Text)
    resolved_at = Column(DateTime)
    resolved_by = Column(PGUUID(as_uuid=True))

    cvss_score = Column(Float)
    cvss_vector = Column(String(100))

    is_suppressed = Column(Boolean, default=False)
    suppression_reason = Column(Text)
    suppressed_by = Column(PGUUID(as_uuid=True))
    suppressed_until = Column(DateTime)

    references = Column(ARRAY(String), default=[])
    remediation_guidance = Column(Text)

    first_detected_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    scan = relationship("SecurityScan", back_populates="vulnerabilities")

    __table_args__ = (
        Index("ix_vulnerabilities_severity_status", "severity", "status"),
        Index("ix_vulnerabilities_cve", "cve_id"),
    )


class SecurityPolicy(Base):
    """Security policy configuration."""
    __tablename__ = "quality_security_policies"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text)

    block_critical = Column(Boolean, default=True)
    block_high = Column(Boolean, default=True)
    block_medium = Column(Boolean, default=False)

    max_critical_age_days = Column(Integer, default=1)
    max_high_age_days = Column(Integer, default=7)
    max_medium_age_days = Column(Integer, default=30)

    exempt_paths = Column(ARRAY(String), default=[])
    exempt_rules = Column(ARRAY(String), default=[])

    notify_on_critical = Column(Boolean, default=True)
    notification_channels = Column(JSONB, default=[])

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# =============================================================================
# Test Data Management Models
# =============================================================================

class TestDataSet(Base):
    """Test data set definition."""
    __tablename__ = "quality_test_data_sets"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text)
    version = Column(String(50), nullable=False)

    data_type = Column(SQLEnum(DataGeneratorType), nullable=False)
    record_count = Column(Integer)

    generator_config = Column(JSONB, default={})
    seed = Column(Integer)

    storage_url = Column(String(500))
    file_format = Column(String(50))
    file_size_bytes = Column(Integer)
    checksum = Column(String(64))

    contains_pii = Column(Boolean, default=False)
    pii_masked = Column(Boolean, default=True)
    masking_rules = Column(JSONB, default={})

    compatible_environments = Column(ARRAY(String), default=["local", "ci", "staging"])

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(PGUUID(as_uuid=True))

    seed_executions = relationship("DataSeedExecution", back_populates="data_set")


class DataSeedExecution(Base):
    """Test data seeding execution."""
    __tablename__ = "quality_data_seed_executions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    data_set_id = Column(PGUUID(as_uuid=True), ForeignKey("quality_test_data_sets.id"), nullable=False)

    environment = Column(SQLEnum(TestEnvironment), nullable=False)
    status = Column(SQLEnum(TestRunStatus), nullable=False)

    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)

    records_seeded = Column(Integer)
    records_failed = Column(Integer)

    error_message = Column(Text)

    executed_by = Column(PGUUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)

    data_set = relationship("TestDataSet", back_populates="seed_executions")


class SyntheticDataGenerator(Base):
    """Synthetic data generator configuration."""
    __tablename__ = "quality_synthetic_generators"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text)
    data_type = Column(SQLEnum(DataGeneratorType), nullable=False)

    fhir_resource_type = Column(String(100))
    fhir_profile = Column(String(500))

    field_generators = Column(JSONB, nullable=False)

    relationships = Column(JSONB, default={})

    validation_schema = Column(JSONB)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# =============================================================================
# Flaky Test Management
# =============================================================================

class FlakyTest(Base):
    """Flaky test tracking."""
    __tablename__ = "quality_flaky_tests"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    test_name = Column(String(500), nullable=False, unique=True)
    test_file = Column(String(500))
    test_suite_id = Column(PGUUID(as_uuid=True), ForeignKey("quality_test_suites.id"))

    status = Column(SQLEnum(FlakyTestStatus), nullable=False, default=FlakyTestStatus.DETECTED)

    first_detected_at = Column(DateTime, nullable=False)
    last_flake_at = Column(DateTime)
    flake_count = Column(Integer, default=1)
    total_runs = Column(Integer, default=1)
    flake_rate = Column(Float)

    failure_patterns = Column(JSONB, default=[])
    suspected_cause = Column(Text)

    assigned_to = Column(PGUUID(as_uuid=True))
    resolution_notes = Column(Text)
    fixed_at = Column(DateTime)
    fixed_by = Column(PGUUID(as_uuid=True))

    quarantined_at = Column(DateTime)
    quarantine_reason = Column(Text)
    quarantine_expires_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_flaky_tests_status", "status"),
    )


# =============================================================================
# Quality Gates
# =============================================================================

class QualityGate(Base):
    """Quality gate definition."""
    __tablename__ = "quality_gates"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text)

    conditions = Column(JSONB, nullable=False)

    applies_to_branches = Column(ARRAY(String), default=["main", "master"])
    applies_to_environments = Column(ARRAY(String), default=["ci", "staging"])

    is_blocking = Column(Boolean, default=True)
    warn_only = Column(Boolean, default=False)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    evaluations = relationship("QualityGateEvaluation", back_populates="gate")


class QualityGateEvaluation(Base):
    """Quality gate evaluation result."""
    __tablename__ = "quality_gate_evaluations"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)
    gate_id = Column(PGUUID(as_uuid=True), ForeignKey("quality_gates.id"), nullable=False)

    branch = Column(String(255))
    commit_sha = Column(String(40))
    pull_request_id = Column(String(50))
    environment = Column(SQLEnum(TestEnvironment))

    status = Column(SQLEnum(QualityGateStatus), nullable=False)

    condition_results = Column(JSONB, nullable=False)

    total_conditions = Column(Integer)
    passed_conditions = Column(Integer)
    failed_conditions = Column(Integer)

    evaluated_at = Column(DateTime, default=datetime.utcnow)

    gate = relationship("QualityGate", back_populates="evaluations")

    __table_args__ = (
        Index("ix_gate_evals_branch_commit", "branch", "commit_sha"),
    )


# =============================================================================
# CI/CD Integration
# =============================================================================

class CIPipeline(Base):
    """CI/CD pipeline execution."""
    __tablename__ = "quality_ci_pipelines"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    pipeline_id = Column(String(100), nullable=False)
    workflow_name = Column(String(255))
    run_number = Column(Integer)

    branch = Column(String(255))
    commit_sha = Column(String(40))
    commit_message = Column(Text)
    pull_request_id = Column(String(50))

    status = Column(SQLEnum(TestRunStatus), nullable=False)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)

    triggered_by = Column(String(255))
    trigger_event = Column(String(100))

    jobs_total = Column(Integer)
    jobs_passed = Column(Integer)
    jobs_failed = Column(Integer)

    test_run_ids = Column(ARRAY(PGUUID(as_uuid=True)), default=[])
    coverage_report_id = Column(PGUUID(as_uuid=True))
    security_scan_ids = Column(ARRAY(PGUUID(as_uuid=True)), default=[])
    quality_gate_evaluation_id = Column(PGUUID(as_uuid=True))

    logs_url = Column(String(500))
    artifacts_url = Column(String(500))

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_ci_pipelines_branch_status", "branch", "status"),
        Index("ix_ci_pipelines_pr", "pull_request_id"),
    )


class TestTrendMetric(Base):
    """Test metrics over time for trend analysis."""
    __tablename__ = "quality_test_trend_metrics"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PGUUID(as_uuid=True), nullable=False, index=True)

    date = Column(DateTime, nullable=False)

    total_tests = Column(Integer)
    passed_tests = Column(Integer)
    failed_tests = Column(Integer)
    skipped_tests = Column(Integer)
    flaky_tests = Column(Integer)

    pass_rate = Column(Float)

    line_coverage = Column(Float)
    branch_coverage = Column(Float)

    avg_latency_p95 = Column(Float)

    open_vulnerabilities = Column(Integer)
    critical_vulnerabilities = Column(Integer)

    pipeline_success_rate = Column(Float)
    avg_pipeline_duration = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("tenant_id", "date", name="uq_trend_metrics_tenant_date"),
        Index("ix_trend_metrics_date", "date"),
    )

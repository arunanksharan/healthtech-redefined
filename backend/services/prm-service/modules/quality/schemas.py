"""
Quality & Testing Schemas

Pydantic schemas for EPIC-023: Quality & Testing
Request/response validation for test execution, coverage, performance, and security.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# Enums (mirroring models.py)
# =============================================================================

class TestType(str, Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"
    SMOKE = "smoke"
    REGRESSION = "regression"
    ACCEPTANCE = "acceptance"


class TestStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    TIMEOUT = "timeout"
    FLAKY = "flaky"


class TestRunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TestEnvironment(str, Enum):
    LOCAL = "local"
    CI = "ci"
    STAGING = "staging"
    PRODUCTION = "production"


class CoverageType(str, Enum):
    LINE = "line"
    BRANCH = "branch"
    FUNCTION = "function"
    STATEMENT = "statement"


class PerformanceTestType(str, Enum):
    LOAD = "load"
    STRESS = "stress"
    SPIKE = "spike"
    SOAK = "soak"
    BASELINE = "baseline"


class SecurityScanType(str, Enum):
    SAST = "sast"
    DAST = "dast"
    DEPENDENCY = "dependency"
    CONTAINER = "container"
    SECRETS = "secrets"
    API = "api"


class VulnerabilitySeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    FIXED = "fixed"
    WONT_FIX = "wont_fix"
    FALSE_POSITIVE = "false_positive"
    ACCEPTED = "accepted"


class QualityGateStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


class DataGeneratorType(str, Enum):
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
    DETECTED = "detected"
    QUARANTINED = "quarantined"
    INVESTIGATING = "investigating"
    FIXED = "fixed"
    PERMANENT_QUARANTINE = "permanent_quarantine"


# =============================================================================
# Test Suite Schemas
# =============================================================================

class TestSuiteCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    test_type: TestType
    file_patterns: List[str] = []
    exclude_patterns: List[str] = []
    timeout_seconds: int = 3600
    parallel_workers: int = 4
    retry_count: int = 2
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


class TestSuiteResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    test_type: TestType
    file_patterns: List[str]
    exclude_patterns: List[str]
    timeout_seconds: int
    parallel_workers: int
    retry_count: int
    tags: List[str]
    metadata: Dict[str, Any]
    is_active: bool
    last_run_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestSuiteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    file_patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None
    timeout_seconds: Optional[int] = None
    parallel_workers: Optional[int] = None
    retry_count: Optional[int] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


# =============================================================================
# Test Run Schemas
# =============================================================================

class TestRunCreate(BaseModel):
    suite_id: Optional[UUID] = None
    branch: Optional[str] = None
    commit_sha: Optional[str] = Field(None, max_length=40)
    pull_request_id: Optional[str] = None
    environment: TestEnvironment
    triggered_by: Optional[str] = None
    config: Dict[str, Any] = {}


class TestRunResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    suite_id: Optional[UUID]
    run_number: int
    branch: Optional[str]
    commit_sha: Optional[str]
    pull_request_id: Optional[str]
    environment: TestEnvironment
    status: TestRunStatus
    triggered_by: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    flaky_tests: int
    config: Dict[str, Any]
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TestRunUpdate(BaseModel):
    status: Optional[TestRunStatus] = None
    completed_at: Optional[datetime] = None
    total_tests: Optional[int] = None
    passed_tests: Optional[int] = None
    failed_tests: Optional[int] = None
    skipped_tests: Optional[int] = None
    error_tests: Optional[int] = None
    error_message: Optional[str] = None


# =============================================================================
# Test Result Schemas
# =============================================================================

class TestResultCreate(BaseModel):
    test_run_id: UUID
    test_name: str = Field(..., max_length=500)
    test_file: Optional[str] = None
    test_class: Optional[str] = None
    test_method: Optional[str] = None
    status: TestStatus
    duration_ms: Optional[float] = None
    retry_count: int = 0
    failure_message: Optional[str] = None
    failure_stacktrace: Optional[str] = None
    failure_type: Optional[str] = None
    assertions_passed: int = 0
    assertions_failed: int = 0
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    artifacts: List[str] = []
    tags: List[str] = []
    parameters: Dict[str, Any] = {}


class TestResultResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    test_run_id: UUID
    test_name: str
    test_file: Optional[str]
    test_class: Optional[str]
    test_method: Optional[str]
    status: TestStatus
    duration_ms: Optional[float]
    retry_count: int
    failure_message: Optional[str]
    failure_stacktrace: Optional[str]
    failure_type: Optional[str]
    assertions_passed: int
    assertions_failed: int
    tags: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Coverage Schemas
# =============================================================================

class CoverageReportCreate(BaseModel):
    test_run_id: Optional[UUID] = None
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    line_coverage: float = Field(..., ge=0, le=100)
    branch_coverage: Optional[float] = Field(None, ge=0, le=100)
    function_coverage: Optional[float] = Field(None, ge=0, le=100)
    statement_coverage: Optional[float] = Field(None, ge=0, le=100)
    total_lines: int
    covered_lines: int
    total_branches: Optional[int] = None
    covered_branches: Optional[int] = None
    total_functions: Optional[int] = None
    covered_functions: Optional[int] = None
    line_threshold: float = 80.0
    branch_threshold: float = 80.0
    html_report_url: Optional[str] = None
    xml_report_url: Optional[str] = None


class CoverageReportResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    test_run_id: Optional[UUID]
    branch: Optional[str]
    commit_sha: Optional[str]
    line_coverage: Optional[float]
    branch_coverage: Optional[float]
    function_coverage: Optional[float]
    statement_coverage: Optional[float]
    total_lines: Optional[int]
    covered_lines: Optional[int]
    threshold_passed: Optional[bool]
    coverage_delta: Optional[float]
    previous_coverage: Optional[float]
    html_report_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class FileCoverageCreate(BaseModel):
    report_id: UUID
    file_path: str
    package_name: Optional[str] = None
    line_coverage: float
    branch_coverage: Optional[float] = None
    function_coverage: Optional[float] = None
    total_lines: int
    covered_lines: int
    uncovered_lines: List[int] = []


class FileCoverageResponse(BaseModel):
    id: UUID
    report_id: UUID
    file_path: str
    package_name: Optional[str]
    line_coverage: Optional[float]
    branch_coverage: Optional[float]
    function_coverage: Optional[float]
    total_lines: Optional[int]
    covered_lines: Optional[int]
    uncovered_lines: List[int]

    class Config:
        from_attributes = True


class CoverageThresholdCreate(BaseModel):
    name: str
    description: Optional[str] = None
    line_threshold: float = 80.0
    branch_threshold: float = 80.0
    function_threshold: float = 80.0
    is_blocking: bool = True
    applies_to_branches: List[str] = ["main", "master"]
    excluded_paths: List[str] = []


class CoverageThresholdResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    line_threshold: float
    branch_threshold: float
    function_threshold: float
    is_blocking: bool
    applies_to_branches: List[str]
    excluded_paths: List[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Performance Test Schemas
# =============================================================================

class PerformanceScenarioCreate(BaseModel):
    name: str
    description: Optional[str] = None
    test_type: PerformanceTestType
    target_url: Optional[str] = None
    target_endpoints: List[Dict[str, Any]] = []
    virtual_users: int = 100
    ramp_up_seconds: int = 60
    duration_seconds: int = 300
    max_latency_p95_ms: int = 500
    max_latency_p99_ms: int = 1000
    max_error_rate_percent: float = 1.0
    min_throughput_rps: Optional[float] = None
    k6_script: Optional[str] = None
    script_config: Dict[str, Any] = {}


class PerformanceScenarioResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    test_type: PerformanceTestType
    target_url: Optional[str]
    virtual_users: int
    ramp_up_seconds: int
    duration_seconds: int
    max_latency_p95_ms: int
    max_latency_p99_ms: int
    max_error_rate_percent: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PerformanceResultCreate(BaseModel):
    scenario_id: Optional[UUID] = None
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    environment: TestEnvironment
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: TestRunStatus
    thresholds_passed: Optional[bool] = None
    total_requests: int
    successful_requests: int
    failed_requests: int
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    latency_min_ms: Optional[float] = None
    latency_max_ms: Optional[float] = None
    latency_avg_ms: Optional[float] = None
    requests_per_second: float
    peak_concurrent_users: Optional[int] = None
    error_rate_percent: float
    error_breakdown: Dict[str, int] = {}
    report_url: Optional[str] = None


class PerformanceResultResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    scenario_id: Optional[UUID]
    branch: Optional[str]
    commit_sha: Optional[str]
    environment: TestEnvironment
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    status: TestRunStatus
    thresholds_passed: Optional[bool]
    total_requests: Optional[int]
    successful_requests: Optional[int]
    failed_requests: Optional[int]
    latency_p50_ms: Optional[float]
    latency_p95_ms: Optional[float]
    latency_p99_ms: Optional[float]
    requests_per_second: Optional[float]
    error_rate_percent: Optional[float]
    performance_degradation_percent: Optional[float]
    report_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PerformanceBaselineCreate(BaseModel):
    scenario_id: UUID
    test_result_id: UUID
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    throughput_rps: float
    error_rate_percent: float
    latency_tolerance_percent: float = 10.0
    throughput_tolerance_percent: float = 10.0


class PerformanceBaselineResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    scenario_id: Optional[UUID]
    test_result_id: Optional[UUID]
    latency_p50_ms: Optional[float]
    latency_p95_ms: Optional[float]
    latency_p99_ms: Optional[float]
    throughput_rps: Optional[float]
    error_rate_percent: Optional[float]
    latency_tolerance_percent: float
    throughput_tolerance_percent: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Security Scan Schemas
# =============================================================================

class SecurityScanCreate(BaseModel):
    scan_type: SecurityScanType
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    scanner_name: str
    scanner_version: Optional[str] = None
    scan_config: Dict[str, Any] = {}


class SecurityScanResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    scan_type: SecurityScanType
    branch: Optional[str]
    commit_sha: Optional[str]
    status: TestRunStatus
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    scanner_name: Optional[str]
    scanner_version: Optional[str]
    total_findings: int
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    info_findings: int
    gate_passed: Optional[bool]
    report_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class VulnerabilityCreate(BaseModel):
    scan_id: Optional[UUID] = None
    vulnerability_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    severity: VulnerabilitySeverity
    category: Optional[str] = None
    cwe_id: Optional[str] = None
    cve_id: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    package_name: Optional[str] = None
    package_version: Optional[str] = None
    fixed_version: Optional[str] = None
    image_name: Optional[str] = None
    cvss_score: Optional[float] = None
    cvss_vector: Optional[str] = None
    references: List[str] = []
    remediation_guidance: Optional[str] = None


class VulnerabilityResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    scan_id: Optional[UUID]
    vulnerability_id: Optional[str]
    title: str
    description: Optional[str]
    severity: VulnerabilitySeverity
    category: Optional[str]
    cwe_id: Optional[str]
    cve_id: Optional[str]
    file_path: Optional[str]
    line_number: Optional[int]
    package_name: Optional[str]
    package_version: Optional[str]
    fixed_version: Optional[str]
    status: VulnerabilityStatus
    assigned_to: Optional[UUID]
    due_date: Optional[datetime]
    cvss_score: Optional[float]
    is_suppressed: bool
    first_detected_at: datetime
    last_seen_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class VulnerabilityUpdate(BaseModel):
    status: Optional[VulnerabilityStatus] = None
    assigned_to: Optional[UUID] = None
    due_date: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    is_suppressed: Optional[bool] = None
    suppression_reason: Optional[str] = None
    suppressed_until: Optional[datetime] = None


class SecurityPolicyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    block_critical: bool = True
    block_high: bool = True
    block_medium: bool = False
    max_critical_age_days: int = 1
    max_high_age_days: int = 7
    max_medium_age_days: int = 30
    exempt_paths: List[str] = []
    exempt_rules: List[str] = []
    notify_on_critical: bool = True
    notification_channels: List[Dict[str, Any]] = []


class SecurityPolicyResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    block_critical: bool
    block_high: bool
    block_medium: bool
    max_critical_age_days: int
    max_high_age_days: int
    max_medium_age_days: int
    exempt_paths: List[str]
    exempt_rules: List[str]
    notify_on_critical: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Test Data Schemas
# =============================================================================

class TestDataSetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    version: str
    data_type: DataGeneratorType
    record_count: Optional[int] = None
    generator_config: Dict[str, Any] = {}
    seed: Optional[int] = None
    contains_pii: bool = False
    pii_masked: bool = True
    masking_rules: Dict[str, Any] = {}
    compatible_environments: List[str] = ["local", "ci", "staging"]


class TestDataSetResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    version: str
    data_type: DataGeneratorType
    record_count: Optional[int]
    storage_url: Optional[str]
    file_format: Optional[str]
    file_size_bytes: Optional[int]
    checksum: Optional[str]
    contains_pii: bool
    pii_masked: bool
    compatible_environments: List[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DataSeedExecutionCreate(BaseModel):
    data_set_id: UUID
    environment: TestEnvironment


class DataSeedExecutionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    data_set_id: UUID
    environment: TestEnvironment
    status: TestRunStatus
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    records_seeded: Optional[int]
    records_failed: Optional[int]
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class SyntheticGeneratorCreate(BaseModel):
    name: str
    description: Optional[str] = None
    data_type: DataGeneratorType
    fhir_resource_type: Optional[str] = None
    fhir_profile: Optional[str] = None
    field_generators: Dict[str, Any]
    relationships: Dict[str, Any] = {}
    validation_schema: Optional[Dict[str, Any]] = None


class SyntheticGeneratorResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    data_type: DataGeneratorType
    fhir_resource_type: Optional[str]
    fhir_profile: Optional[str]
    field_generators: Dict[str, Any]
    relationships: Dict[str, Any]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# Flaky Test Schemas
# =============================================================================

class FlakyTestCreate(BaseModel):
    test_name: str
    test_file: Optional[str] = None
    test_suite_id: Optional[UUID] = None
    failure_patterns: List[Dict[str, Any]] = []
    suspected_cause: Optional[str] = None


class FlakyTestResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    test_name: str
    test_file: Optional[str]
    test_suite_id: Optional[UUID]
    status: FlakyTestStatus
    first_detected_at: datetime
    last_flake_at: Optional[datetime]
    flake_count: int
    total_runs: int
    flake_rate: Optional[float]
    suspected_cause: Optional[str]
    assigned_to: Optional[UUID]
    quarantined_at: Optional[datetime]
    quarantine_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class FlakyTestUpdate(BaseModel):
    status: Optional[FlakyTestStatus] = None
    suspected_cause: Optional[str] = None
    assigned_to: Optional[UUID] = None
    resolution_notes: Optional[str] = None
    quarantine_reason: Optional[str] = None
    quarantine_expires_at: Optional[datetime] = None


# =============================================================================
# Quality Gate Schemas
# =============================================================================

class QualityGateCondition(BaseModel):
    type: str  # coverage, test_pass_rate, security, performance
    metric: str
    operator: str  # >=, <=, ==, >, <
    value: float
    is_blocking: bool = True


class QualityGateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    conditions: List[QualityGateCondition]
    applies_to_branches: List[str] = ["main", "master"]
    applies_to_environments: List[str] = ["ci", "staging"]
    is_blocking: bool = True
    warn_only: bool = False


class QualityGateResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    conditions: List[Dict[str, Any]]
    applies_to_branches: List[str]
    applies_to_environments: List[str]
    is_blocking: bool
    warn_only: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class QualityGateEvaluationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    gate_id: UUID
    branch: Optional[str]
    commit_sha: Optional[str]
    pull_request_id: Optional[str]
    environment: Optional[TestEnvironment]
    status: QualityGateStatus
    condition_results: List[Dict[str, Any]]
    total_conditions: Optional[int]
    passed_conditions: Optional[int]
    failed_conditions: Optional[int]
    evaluated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# CI/CD Schemas
# =============================================================================

class CIPipelineCreate(BaseModel):
    pipeline_id: str
    workflow_name: Optional[str] = None
    run_number: Optional[int] = None
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    commit_message: Optional[str] = None
    pull_request_id: Optional[str] = None
    triggered_by: Optional[str] = None
    trigger_event: Optional[str] = None


class CIPipelineResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    pipeline_id: str
    workflow_name: Optional[str]
    run_number: Optional[int]
    branch: Optional[str]
    commit_sha: Optional[str]
    pull_request_id: Optional[str]
    status: TestRunStatus
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    triggered_by: Optional[str]
    trigger_event: Optional[str]
    jobs_total: Optional[int]
    jobs_passed: Optional[int]
    jobs_failed: Optional[int]
    logs_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CIPipelineUpdate(BaseModel):
    status: Optional[TestRunStatus] = None
    completed_at: Optional[datetime] = None
    jobs_total: Optional[int] = None
    jobs_passed: Optional[int] = None
    jobs_failed: Optional[int] = None
    test_run_ids: Optional[List[UUID]] = None
    coverage_report_id: Optional[UUID] = None
    security_scan_ids: Optional[List[UUID]] = None
    quality_gate_evaluation_id: Optional[UUID] = None
    logs_url: Optional[str] = None
    artifacts_url: Optional[str] = None


# =============================================================================
# Dashboard and Report Schemas
# =============================================================================

class TestSummary(BaseModel):
    total_tests: int
    passed: int
    failed: int
    skipped: int
    error: int
    flaky: int
    pass_rate: float
    duration_seconds: float


class CoverageSummary(BaseModel):
    line_coverage: float
    branch_coverage: Optional[float]
    function_coverage: Optional[float]
    threshold_passed: bool
    coverage_trend: str  # up, down, stable


class SecuritySummary(BaseModel):
    total_vulnerabilities: int
    critical: int
    high: int
    medium: int
    low: int
    open_count: int
    fixed_count: int


class PerformanceSummary(BaseModel):
    latency_p95_ms: float
    latency_p99_ms: float
    throughput_rps: float
    error_rate_percent: float
    thresholds_passed: bool


class QualityDashboard(BaseModel):
    tenant_id: UUID
    as_of: datetime
    test_summary: TestSummary
    coverage_summary: CoverageSummary
    security_summary: SecuritySummary
    performance_summary: Optional[PerformanceSummary]
    quality_gate_status: QualityGateStatus
    recent_test_runs: List[TestRunResponse]
    recent_pipelines: List[CIPipelineResponse]
    flaky_tests_count: int
    open_vulnerabilities: List[VulnerabilityResponse]


class TrendMetricResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    date: datetime
    total_tests: Optional[int]
    passed_tests: Optional[int]
    failed_tests: Optional[int]
    pass_rate: Optional[float]
    line_coverage: Optional[float]
    branch_coverage: Optional[float]
    avg_latency_p95: Optional[float]
    open_vulnerabilities: Optional[int]
    critical_vulnerabilities: Optional[int]
    pipeline_success_rate: Optional[float]

    class Config:
        from_attributes = True


class GenerateTestDataRequest(BaseModel):
    data_type: DataGeneratorType
    count: int = Field(default=10, ge=1, le=10000)
    fhir_profile: Optional[str] = None
    seed: Optional[int] = None
    config: Dict[str, Any] = {}


class GenerateTestDataResponse(BaseModel):
    data_type: DataGeneratorType
    count: int
    records: List[Dict[str, Any]]
    seed: Optional[int]
    generation_time_ms: float


class RunTestsRequest(BaseModel):
    suite_id: Optional[UUID] = None
    test_type: Optional[TestType] = None
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    environment: TestEnvironment = TestEnvironment.CI
    config: Dict[str, Any] = {}


class EvaluateQualityGateRequest(BaseModel):
    gate_id: UUID
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    pull_request_id: Optional[str] = None
    environment: TestEnvironment
    test_run_id: Optional[UUID] = None
    coverage_report_id: Optional[UUID] = None
    security_scan_id: Optional[UUID] = None
    performance_result_id: Optional[UUID] = None

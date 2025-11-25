"""
Quality & Testing Router

FastAPI router for EPIC-023: Quality & Testing.
Provides endpoints for test execution, coverage, performance, security, and test data.
"""

import time
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from modules.quality.models import (
    TestType, TestStatus, TestRunStatus, TestEnvironment,
    PerformanceTestType, SecurityScanType, VulnerabilitySeverity,
    VulnerabilityStatus, DataGeneratorType, FlakyTestStatus,
    QualityGateStatus,
    TestSuite, TestRun, TestResult, CoverageReport, CoverageThreshold,
    PerformanceTestScenario, PerformanceTestResult, PerformanceBaseline,
    SecurityScan, Vulnerability, SecurityPolicy,
    TestDataSet, SyntheticDataGenerator,
    FlakyTest, QualityGate, QualityGateEvaluation, CIPipeline,
)
from modules.quality.schemas import (
    TestSuiteCreate, TestSuiteResponse, TestSuiteUpdate,
    TestRunCreate, TestRunResponse, TestRunUpdate,
    TestResultCreate, TestResultResponse,
    CoverageReportCreate, CoverageReportResponse,
    FileCoverageCreate, FileCoverageResponse,
    CoverageThresholdCreate, CoverageThresholdResponse,
    PerformanceScenarioCreate, PerformanceScenarioResponse,
    PerformanceResultCreate, PerformanceResultResponse,
    PerformanceBaselineCreate, PerformanceBaselineResponse,
    SecurityScanCreate, SecurityScanResponse,
    VulnerabilityCreate, VulnerabilityResponse, VulnerabilityUpdate,
    SecurityPolicyCreate, SecurityPolicyResponse,
    TestDataSetCreate, TestDataSetResponse,
    DataSeedExecutionCreate, DataSeedExecutionResponse,
    SyntheticGeneratorCreate, SyntheticGeneratorResponse,
    FlakyTestResponse, FlakyTestUpdate,
    QualityGateCreate, QualityGateResponse, QualityGateEvaluationResponse,
    CIPipelineCreate, CIPipelineResponse, CIPipelineUpdate,
    QualityDashboard, TestSummary, CoverageSummary, SecuritySummary,
    PerformanceSummary, TrendMetricResponse,
    GenerateTestDataRequest, GenerateTestDataResponse,
    RunTestsRequest, EvaluateQualityGateRequest,
)
from modules.quality.services import (
    TestRunnerService,
    CoverageService,
    PerformanceService,
    SecurityScanService,
    TestDataService,
)


router = APIRouter(prefix="/quality", tags=["Quality & Testing"])


# Dependency placeholder - replace with actual implementation
async def get_db() -> AsyncSession:
    raise NotImplementedError("Database session dependency not configured")


async def get_tenant_id() -> UUID:
    raise NotImplementedError("Tenant ID dependency not configured")


# =============================================================================
# Test Suite Endpoints
# =============================================================================

@router.post("/suites", response_model=TestSuiteResponse)
async def create_test_suite(
    data: TestSuiteCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Create a new test suite."""
    service = TestRunnerService(db, tenant_id)
    suite = await service.create_test_suite(
        name=data.name,
        test_type=data.test_type,
        description=data.description,
        file_patterns=data.file_patterns,
        exclude_patterns=data.exclude_patterns,
        timeout_seconds=data.timeout_seconds,
        parallel_workers=data.parallel_workers,
        retry_count=data.retry_count,
        tags=data.tags,
        metadata=data.metadata,
    )
    await db.commit()
    return suite


@router.get("/suites", response_model=List[TestSuiteResponse])
async def list_test_suites(
    test_type: Optional[TestType] = None,
    is_active: bool = True,
    tags: Optional[List[str]] = Query(None),
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """List test suites."""
    service = TestRunnerService(db, tenant_id)
    return await service.list_test_suites(
        test_type=test_type,
        is_active=is_active,
        tags=tags,
    )


@router.get("/suites/{suite_id}", response_model=TestSuiteResponse)
async def get_test_suite(
    suite_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get a test suite by ID."""
    service = TestRunnerService(db, tenant_id)
    suite = await service.get_test_suite(suite_id)
    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")
    return suite


@router.patch("/suites/{suite_id}", response_model=TestSuiteResponse)
async def update_test_suite(
    suite_id: UUID,
    data: TestSuiteUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Update a test suite."""
    service = TestRunnerService(db, tenant_id)
    suite = await service.update_test_suite(
        suite_id,
        **data.model_dump(exclude_unset=True),
    )
    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")
    await db.commit()
    return suite


# =============================================================================
# Test Run Endpoints
# =============================================================================

@router.post("/runs", response_model=TestRunResponse)
async def create_test_run(
    data: TestRunCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Create a new test run."""
    service = TestRunnerService(db, tenant_id)
    run = await service.create_test_run(
        environment=data.environment,
        suite_id=data.suite_id,
        branch=data.branch,
        commit_sha=data.commit_sha,
        pull_request_id=data.pull_request_id,
        triggered_by=data.triggered_by,
        config=data.config,
    )
    await db.commit()
    return run


@router.get("/runs", response_model=List[TestRunResponse])
async def list_test_runs(
    suite_id: Optional[UUID] = None,
    branch: Optional[str] = None,
    status: Optional[TestRunStatus] = None,
    environment: Optional[TestEnvironment] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """List test runs."""
    service = TestRunnerService(db, tenant_id)
    return await service.list_test_runs(
        suite_id=suite_id,
        branch=branch,
        status=status,
        environment=environment,
        limit=limit,
    )


@router.get("/runs/{run_id}", response_model=TestRunResponse)
async def get_test_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get a test run by ID."""
    service = TestRunnerService(db, tenant_id)
    run = await service.get_test_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    return run


@router.post("/runs/{run_id}/start", response_model=TestRunResponse)
async def start_test_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Start a test run."""
    service = TestRunnerService(db, tenant_id)
    run = await service.start_test_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    await db.commit()
    return run


@router.post("/runs/{run_id}/complete", response_model=TestRunResponse)
async def complete_test_run(
    run_id: UUID,
    data: TestRunUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Complete a test run."""
    service = TestRunnerService(db, tenant_id)
    run = await service.complete_test_run(
        run_id,
        status=data.status or TestRunStatus.COMPLETED,
        total_tests=data.total_tests or 0,
        passed_tests=data.passed_tests or 0,
        failed_tests=data.failed_tests or 0,
        skipped_tests=data.skipped_tests or 0,
        error_tests=data.error_tests or 0,
        error_message=data.error_message,
    )
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    await db.commit()
    return run


# =============================================================================
# Test Result Endpoints
# =============================================================================

@router.post("/results", response_model=TestResultResponse)
async def create_test_result(
    data: TestResultCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Record a test result."""
    service = TestRunnerService(db, tenant_id)
    result = await service.create_test_result(
        test_run_id=data.test_run_id,
        test_name=data.test_name,
        status=data.status,
        test_file=data.test_file,
        test_class=data.test_class,
        test_method=data.test_method,
        duration_ms=data.duration_ms,
        retry_count=data.retry_count,
        failure_message=data.failure_message,
        failure_stacktrace=data.failure_stacktrace,
        failure_type=data.failure_type,
        assertions_passed=data.assertions_passed,
        assertions_failed=data.assertions_failed,
        stdout=data.stdout,
        stderr=data.stderr,
        artifacts=data.artifacts,
        tags=data.tags,
        parameters=data.parameters,
    )
    await db.commit()
    return result


@router.get("/runs/{run_id}/results", response_model=List[TestResultResponse])
async def get_test_results(
    run_id: UUID,
    status: Optional[TestStatus] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get test results for a run."""
    service = TestRunnerService(db, tenant_id)
    return await service.get_test_results(run_id, status=status)


@router.get("/runs/{run_id}/failures", response_model=List[TestResultResponse])
async def get_failed_tests(
    run_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get failed tests for a run."""
    service = TestRunnerService(db, tenant_id)
    return await service.get_failed_tests(run_id)


# =============================================================================
# Coverage Endpoints
# =============================================================================

@router.post("/coverage", response_model=CoverageReportResponse)
async def create_coverage_report(
    data: CoverageReportCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Create a coverage report."""
    service = CoverageService(db, tenant_id)
    report = await service.create_coverage_report(
        line_coverage=data.line_coverage,
        total_lines=data.total_lines,
        covered_lines=data.covered_lines,
        test_run_id=data.test_run_id,
        branch=data.branch,
        commit_sha=data.commit_sha,
        branch_coverage=data.branch_coverage,
        function_coverage=data.function_coverage,
        statement_coverage=data.statement_coverage,
        total_branches=data.total_branches,
        covered_branches=data.covered_branches,
        total_functions=data.total_functions,
        covered_functions=data.covered_functions,
        line_threshold=data.line_threshold,
        branch_threshold=data.branch_threshold,
        html_report_url=data.html_report_url,
        xml_report_url=data.xml_report_url,
    )
    await db.commit()
    return report


@router.get("/coverage", response_model=List[CoverageReportResponse])
async def list_coverage_reports(
    branch: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """List coverage reports."""
    service = CoverageService(db, tenant_id)
    return await service.list_coverage_reports(branch=branch, limit=limit)


@router.get("/coverage/{report_id}", response_model=CoverageReportResponse)
async def get_coverage_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get a coverage report by ID."""
    service = CoverageService(db, tenant_id)
    report = await service.get_coverage_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Coverage report not found")
    return report


@router.get("/coverage/{report_id}/files", response_model=List[FileCoverageResponse])
async def get_file_coverages(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get file-level coverage for a report."""
    service = CoverageService(db, tenant_id)
    return await service.get_file_coverages(report_id)


@router.post("/coverage/{report_id}/evaluate")
async def evaluate_coverage(
    report_id: UUID,
    branch: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Evaluate coverage against thresholds."""
    service = CoverageService(db, tenant_id)
    return await service.evaluate_coverage(report_id, branch)


@router.post("/coverage/thresholds", response_model=CoverageThresholdResponse)
async def create_coverage_threshold(
    data: CoverageThresholdCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Create a coverage threshold configuration."""
    service = CoverageService(db, tenant_id)
    threshold = await service.create_coverage_threshold(
        name=data.name,
        line_threshold=data.line_threshold,
        branch_threshold=data.branch_threshold,
        function_threshold=data.function_threshold,
        description=data.description,
        is_blocking=data.is_blocking,
        applies_to_branches=data.applies_to_branches,
        excluded_paths=data.excluded_paths,
    )
    await db.commit()
    return threshold


# =============================================================================
# Performance Testing Endpoints
# =============================================================================

@router.post("/performance/scenarios", response_model=PerformanceScenarioResponse)
async def create_performance_scenario(
    data: PerformanceScenarioCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Create a performance test scenario."""
    service = PerformanceService(db, tenant_id)
    scenario = await service.create_scenario(
        name=data.name,
        test_type=data.test_type,
        description=data.description,
        target_url=data.target_url,
        target_endpoints=data.target_endpoints,
        virtual_users=data.virtual_users,
        ramp_up_seconds=data.ramp_up_seconds,
        duration_seconds=data.duration_seconds,
        max_latency_p95_ms=data.max_latency_p95_ms,
        max_latency_p99_ms=data.max_latency_p99_ms,
        max_error_rate_percent=data.max_error_rate_percent,
        min_throughput_rps=data.min_throughput_rps,
        k6_script=data.k6_script,
        script_config=data.script_config,
    )
    await db.commit()
    return scenario


@router.get("/performance/scenarios", response_model=List[PerformanceScenarioResponse])
async def list_performance_scenarios(
    test_type: Optional[PerformanceTestType] = None,
    is_active: bool = True,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """List performance scenarios."""
    service = PerformanceService(db, tenant_id)
    return await service.list_scenarios(test_type=test_type, is_active=is_active)


@router.post("/performance/results", response_model=PerformanceResultResponse)
async def create_performance_result(
    data: PerformanceResultCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Record a performance test result."""
    service = PerformanceService(db, tenant_id)
    result = await service.create_test_result(
        environment=data.environment,
        started_at=data.started_at,
        status=data.status,
        total_requests=data.total_requests,
        successful_requests=data.successful_requests,
        failed_requests=data.failed_requests,
        latency_p50_ms=data.latency_p50_ms,
        latency_p95_ms=data.latency_p95_ms,
        latency_p99_ms=data.latency_p99_ms,
        requests_per_second=data.requests_per_second,
        error_rate_percent=data.error_rate_percent,
        scenario_id=data.scenario_id,
        branch=data.branch,
        commit_sha=data.commit_sha,
        completed_at=data.completed_at,
        latency_min_ms=data.latency_min_ms,
        latency_max_ms=data.latency_max_ms,
        latency_avg_ms=data.latency_avg_ms,
        peak_concurrent_users=data.peak_concurrent_users,
        error_breakdown=data.error_breakdown,
        report_url=data.report_url,
    )
    await db.commit()
    return result


@router.get("/performance/results", response_model=List[PerformanceResultResponse])
async def list_performance_results(
    scenario_id: Optional[UUID] = None,
    environment: Optional[TestEnvironment] = None,
    branch: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """List performance test results."""
    service = PerformanceService(db, tenant_id)
    return await service.list_test_results(
        scenario_id=scenario_id,
        environment=environment,
        branch=branch,
        limit=limit,
    )


@router.post("/performance/baselines", response_model=PerformanceBaselineResponse)
async def create_performance_baseline(
    data: PerformanceBaselineCreate,
    created_by: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Create a performance baseline."""
    service = PerformanceService(db, tenant_id)
    baseline = await service.create_baseline(
        scenario_id=data.scenario_id,
        test_result_id=data.test_result_id,
        created_by=created_by,
        latency_tolerance_percent=data.latency_tolerance_percent,
        throughput_tolerance_percent=data.throughput_tolerance_percent,
    )
    if not baseline:
        raise HTTPException(status_code=404, detail="Test result not found")
    await db.commit()
    return baseline


@router.get("/performance/results/{result_id}/compare")
async def compare_to_baseline(
    result_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Compare a performance result to baseline."""
    service = PerformanceService(db, tenant_id)
    return await service.compare_to_baseline(result_id)


# =============================================================================
# Security Testing Endpoints
# =============================================================================

@router.post("/security/scans", response_model=SecurityScanResponse)
async def create_security_scan(
    data: SecurityScanCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Create a security scan."""
    service = SecurityScanService(db, tenant_id)
    scan = await service.create_scan(
        scan_type=data.scan_type,
        scanner_name=data.scanner_name,
        branch=data.branch,
        commit_sha=data.commit_sha,
        scanner_version=data.scanner_version,
        scan_config=data.scan_config,
    )
    await db.commit()
    return scan


@router.get("/security/scans", response_model=List[SecurityScanResponse])
async def list_security_scans(
    scan_type: Optional[SecurityScanType] = None,
    branch: Optional[str] = None,
    status: Optional[TestRunStatus] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """List security scans."""
    service = SecurityScanService(db, tenant_id)
    return await service.list_scans(
        scan_type=scan_type,
        branch=branch,
        status=status,
        limit=limit,
    )


@router.get("/security/scans/{scan_id}", response_model=SecurityScanResponse)
async def get_security_scan(
    scan_id: UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get a security scan by ID."""
    service = SecurityScanService(db, tenant_id)
    scan = await service.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Security scan not found")
    return scan


@router.post("/security/vulnerabilities", response_model=VulnerabilityResponse)
async def create_vulnerability(
    data: VulnerabilityCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Create a vulnerability finding."""
    service = SecurityScanService(db, tenant_id)
    vuln = await service.create_vulnerability(
        title=data.title,
        severity=data.severity,
        scan_id=data.scan_id,
        vulnerability_id=data.vulnerability_id,
        description=data.description,
        category=data.category,
        cwe_id=data.cwe_id,
        cve_id=data.cve_id,
        file_path=data.file_path,
        line_number=data.line_number,
        code_snippet=data.code_snippet,
        package_name=data.package_name,
        package_version=data.package_version,
        fixed_version=data.fixed_version,
        image_name=data.image_name,
        cvss_score=data.cvss_score,
        cvss_vector=data.cvss_vector,
        references=data.references,
        remediation_guidance=data.remediation_guidance,
    )
    await db.commit()
    return vuln


@router.get("/security/vulnerabilities", response_model=List[VulnerabilityResponse])
async def list_vulnerabilities(
    scan_id: Optional[UUID] = None,
    severity: Optional[VulnerabilitySeverity] = None,
    status: Optional[VulnerabilityStatus] = None,
    include_suppressed: bool = False,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """List vulnerabilities."""
    service = SecurityScanService(db, tenant_id)
    return await service.list_vulnerabilities(
        scan_id=scan_id,
        severity=severity,
        status=status,
        include_suppressed=include_suppressed,
        limit=limit,
    )


@router.patch("/security/vulnerabilities/{vuln_id}", response_model=VulnerabilityResponse)
async def update_vulnerability(
    vuln_id: UUID,
    data: VulnerabilityUpdate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Update a vulnerability."""
    service = SecurityScanService(db, tenant_id)
    vuln = await service.update_vulnerability(
        vuln_id,
        status=data.status,
        assigned_to=data.assigned_to,
        due_date=data.due_date,
        resolution_notes=data.resolution_notes,
    )
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    await db.commit()
    return vuln


@router.post("/security/policies", response_model=SecurityPolicyResponse)
async def create_security_policy(
    data: SecurityPolicyCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Create a security policy."""
    service = SecurityScanService(db, tenant_id)
    policy = await service.create_policy(
        name=data.name,
        description=data.description,
        block_critical=data.block_critical,
        block_high=data.block_high,
        block_medium=data.block_medium,
        max_critical_age_days=data.max_critical_age_days,
        max_high_age_days=data.max_high_age_days,
        max_medium_age_days=data.max_medium_age_days,
        exempt_paths=data.exempt_paths,
        exempt_rules=data.exempt_rules,
        notify_on_critical=data.notify_on_critical,
        notification_channels=data.notification_channels,
    )
    await db.commit()
    return policy


# =============================================================================
# Test Data Endpoints
# =============================================================================

@router.post("/test-data/generate", response_model=GenerateTestDataResponse)
async def generate_test_data(
    data: GenerateTestDataRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Generate synthetic test data."""
    service = TestDataService(db, tenant_id)
    start_time = time.time()
    records = service.generate_batch(
        data_type=data.data_type,
        count=data.count,
        seed=data.seed,
        config=data.config,
    )
    generation_time = (time.time() - start_time) * 1000
    return GenerateTestDataResponse(
        data_type=data.data_type,
        count=len(records),
        records=records,
        seed=data.seed,
        generation_time_ms=round(generation_time, 2),
    )


@router.post("/test-data/sets", response_model=TestDataSetResponse)
async def create_test_data_set(
    data: TestDataSetCreate,
    created_by: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Create a test data set definition."""
    service = TestDataService(db, tenant_id)
    data_set = await service.create_data_set(
        name=data.name,
        version=data.version,
        data_type=data.data_type,
        record_count=data.record_count,
        description=data.description,
        generator_config=data.generator_config,
        seed=data.seed,
        contains_pii=data.contains_pii,
        pii_masked=data.pii_masked,
        masking_rules=data.masking_rules,
        compatible_environments=data.compatible_environments,
        created_by=created_by,
    )
    await db.commit()
    return data_set


@router.get("/test-data/sets", response_model=List[TestDataSetResponse])
async def list_test_data_sets(
    data_type: Optional[DataGeneratorType] = None,
    is_active: bool = True,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """List test data sets."""
    service = TestDataService(db, tenant_id)
    return await service.list_data_sets(data_type=data_type, is_active=is_active)


@router.post("/test-data/sets/{data_set_id}/generate")
async def generate_from_data_set(
    data_set_id: UUID,
    count: int = 100,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Generate data from a data set definition."""
    service = TestDataService(db, tenant_id)
    result = await service.generate_and_store(data_set_id, count)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    await db.commit()
    return result


@router.post("/test-data/generators", response_model=SyntheticGeneratorResponse)
async def create_synthetic_generator(
    data: SyntheticGeneratorCreate,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Create a custom synthetic data generator."""
    service = TestDataService(db, tenant_id)
    generator = await service.create_generator(
        name=data.name,
        data_type=data.data_type,
        field_generators=data.field_generators,
        description=data.description,
        fhir_resource_type=data.fhir_resource_type,
        fhir_profile=data.fhir_profile,
        relationships=data.relationships,
        validation_schema=data.validation_schema,
    )
    await db.commit()
    return generator


# =============================================================================
# Flaky Test Endpoints
# =============================================================================

@router.get("/flaky-tests", response_model=List[FlakyTestResponse])
async def list_flaky_tests(
    status: Optional[FlakyTestStatus] = None,
    min_flake_rate: Optional[float] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """List flaky tests."""
    service = TestRunnerService(db, tenant_id)
    return await service.list_flaky_tests(status=status, min_flake_rate=min_flake_rate)


@router.post("/flaky-tests/{flaky_id}/quarantine", response_model=FlakyTestResponse)
async def quarantine_flaky_test(
    flaky_id: UUID,
    reason: str,
    expires_at: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Quarantine a flaky test."""
    service = TestRunnerService(db, tenant_id)
    flaky = await service.quarantine_flaky_test(flaky_id, reason, expires_at)
    if not flaky:
        raise HTTPException(status_code=404, detail="Flaky test not found")
    await db.commit()
    return flaky


@router.post("/flaky-tests/{flaky_id}/fix", response_model=FlakyTestResponse)
async def fix_flaky_test(
    flaky_id: UUID,
    fixed_by: UUID,
    resolution_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Mark a flaky test as fixed."""
    service = TestRunnerService(db, tenant_id)
    flaky = await service.fix_flaky_test(flaky_id, fixed_by, resolution_notes)
    if not flaky:
        raise HTTPException(status_code=404, detail="Flaky test not found")
    await db.commit()
    return flaky


# =============================================================================
# Statistics and Dashboard
# =============================================================================

@router.get("/statistics/tests")
async def get_test_statistics(
    branch: Optional[str] = None,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get test execution statistics."""
    service = TestRunnerService(db, tenant_id)
    return await service.get_test_statistics(branch=branch, days=days)


@router.get("/statistics/coverage")
async def get_coverage_summary(
    branch: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get coverage summary."""
    service = CoverageService(db, tenant_id)
    return await service.get_coverage_summary(branch=branch)


@router.get("/statistics/performance")
async def get_performance_summary(
    scenario_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get performance testing summary."""
    service = PerformanceService(db, tenant_id)
    return await service.get_performance_summary(scenario_id=scenario_id)


@router.get("/statistics/security")
async def get_security_summary(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get security testing summary."""
    service = SecurityScanService(db, tenant_id)
    return await service.get_security_summary()


@router.get("/dashboard")
async def get_quality_dashboard(
    db: AsyncSession = Depends(get_db),
    tenant_id: UUID = Depends(get_tenant_id),
):
    """Get comprehensive quality dashboard."""
    test_service = TestRunnerService(db, tenant_id)
    coverage_service = CoverageService(db, tenant_id)
    performance_service = PerformanceService(db, tenant_id)
    security_service = SecurityScanService(db, tenant_id)

    test_stats = await test_service.get_test_statistics()
    coverage_summary = await coverage_service.get_coverage_summary()
    performance_summary = await performance_service.get_performance_summary()
    security_summary = await security_service.get_security_summary()

    recent_runs = await test_service.list_test_runs(limit=5)
    flaky_tests = await test_service.list_flaky_tests(status=FlakyTestStatus.DETECTED)
    open_vulns = await security_service.get_open_vulnerabilities()

    return {
        "tenant_id": str(tenant_id),
        "as_of": datetime.utcnow(),
        "test_summary": test_stats,
        "coverage_summary": coverage_summary,
        "performance_summary": performance_summary,
        "security_summary": security_summary,
        "recent_test_runs": [
            {"id": str(r.id), "status": r.status.value, "pass_rate": (r.passed_tests / r.total_tests * 100) if r.total_tests else 0}
            for r in recent_runs
        ],
        "flaky_tests_count": len(flaky_tests),
        "open_critical_vulnerabilities": len([v for v in open_vulns if v.severity == VulnerabilitySeverity.CRITICAL]),
    }

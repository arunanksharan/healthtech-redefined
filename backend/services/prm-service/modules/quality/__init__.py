"""
Quality & Testing Module

Comprehensive quality assurance and testing infrastructure for EPIC-023: Quality & Testing.
Including unit testing, integration testing, E2E testing, performance testing,
security testing, test data management, and CI/CD integration.
"""

from modules.quality.models import (
    # Enums
    TestType,
    TestStatus,
    TestRunStatus,
    TestEnvironment,
    CoverageType,
    PerformanceTestType,
    PerformanceMetricType,
    SecurityScanType,
    VulnerabilitySeverity,
    VulnerabilityStatus,
    QualityGateStatus,
    DataGeneratorType,
    FlakyTestStatus,
    # Test Run Models
    TestSuite,
    TestRun,
    TestResult,
    # Coverage Models
    CoverageReport,
    FileCoverage,
    CoverageThreshold,
    # Performance Models
    PerformanceTestScenario,
    PerformanceTestResult,
    EndpointPerformanceMetric,
    PerformanceBaseline,
    # Security Models
    SecurityScan,
    Vulnerability,
    SecurityPolicy,
    # Test Data Models
    TestDataSet,
    DataSeedExecution,
    SyntheticDataGenerator,
    # Flaky Test Models
    FlakyTest,
    # Quality Gate Models
    QualityGate,
    QualityGateEvaluation,
    # CI/CD Models
    CIPipeline,
    TestTrendMetric,
)

from modules.quality.router import router

from modules.quality.services import (
    TestRunnerService,
    CoverageService,
    PerformanceService,
    SecurityScanService,
    TestDataService,
    FHIR_GENERATORS,
)

__all__ = [
    # Router
    "router",
    # Enums
    "TestType",
    "TestStatus",
    "TestRunStatus",
    "TestEnvironment",
    "CoverageType",
    "PerformanceTestType",
    "PerformanceMetricType",
    "SecurityScanType",
    "VulnerabilitySeverity",
    "VulnerabilityStatus",
    "QualityGateStatus",
    "DataGeneratorType",
    "FlakyTestStatus",
    # Test Run Models
    "TestSuite",
    "TestRun",
    "TestResult",
    # Coverage Models
    "CoverageReport",
    "FileCoverage",
    "CoverageThreshold",
    # Performance Models
    "PerformanceTestScenario",
    "PerformanceTestResult",
    "EndpointPerformanceMetric",
    "PerformanceBaseline",
    # Security Models
    "SecurityScan",
    "Vulnerability",
    "SecurityPolicy",
    # Test Data Models
    "TestDataSet",
    "DataSeedExecution",
    "SyntheticDataGenerator",
    # Flaky Test Models
    "FlakyTest",
    # Quality Gate Models
    "QualityGate",
    "QualityGateEvaluation",
    # CI/CD Models
    "CIPipeline",
    "TestTrendMetric",
    # Services
    "TestRunnerService",
    "CoverageService",
    "PerformanceService",
    "SecurityScanService",
    "TestDataService",
    "FHIR_GENERATORS",
]

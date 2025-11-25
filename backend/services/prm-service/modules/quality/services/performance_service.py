"""
Performance Testing Service

Service for managing performance test scenarios, execution, and baselines.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from modules.quality.models import (
    PerformanceTestScenario, PerformanceTestResult,
    EndpointPerformanceMetric, PerformanceBaseline,
    PerformanceTestType, TestRunStatus, TestEnvironment
)


class PerformanceService:
    """Service for performance testing management."""

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id

    # =========================================================================
    # Performance Scenarios
    # =========================================================================

    async def create_scenario(
        self,
        name: str,
        test_type: PerformanceTestType,
        description: Optional[str] = None,
        target_url: Optional[str] = None,
        target_endpoints: List[Dict[str, Any]] = None,
        virtual_users: int = 100,
        ramp_up_seconds: int = 60,
        duration_seconds: int = 300,
        max_latency_p95_ms: int = 500,
        max_latency_p99_ms: int = 1000,
        max_error_rate_percent: float = 1.0,
        min_throughput_rps: Optional[float] = None,
        k6_script: Optional[str] = None,
        script_config: Dict[str, Any] = None,
    ) -> PerformanceTestScenario:
        """Create a performance test scenario."""
        scenario = PerformanceTestScenario(
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            test_type=test_type,
            target_url=target_url,
            target_endpoints=target_endpoints or [],
            virtual_users=virtual_users,
            ramp_up_seconds=ramp_up_seconds,
            duration_seconds=duration_seconds,
            max_latency_p95_ms=max_latency_p95_ms,
            max_latency_p99_ms=max_latency_p99_ms,
            max_error_rate_percent=max_error_rate_percent,
            min_throughput_rps=min_throughput_rps,
            k6_script=k6_script,
            script_config=script_config or {},
        )
        self.session.add(scenario)
        await self.session.flush()
        return scenario

    async def get_scenario(
        self,
        scenario_id: UUID,
    ) -> Optional[PerformanceTestScenario]:
        """Get a performance scenario by ID."""
        result = await self.session.execute(
            select(PerformanceTestScenario).where(
                and_(
                    PerformanceTestScenario.id == scenario_id,
                    PerformanceTestScenario.tenant_id == self.tenant_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_scenarios(
        self,
        test_type: Optional[PerformanceTestType] = None,
        is_active: bool = True,
    ) -> List[PerformanceTestScenario]:
        """List performance scenarios."""
        query = select(PerformanceTestScenario).where(
            and_(
                PerformanceTestScenario.tenant_id == self.tenant_id,
                PerformanceTestScenario.is_active == is_active,
            )
        )
        if test_type:
            query = query.where(PerformanceTestScenario.test_type == test_type)

        query = query.order_by(PerformanceTestScenario.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # Performance Test Results
    # =========================================================================

    async def create_test_result(
        self,
        environment: TestEnvironment,
        started_at: datetime,
        status: TestRunStatus,
        total_requests: int,
        successful_requests: int,
        failed_requests: int,
        latency_p50_ms: float,
        latency_p95_ms: float,
        latency_p99_ms: float,
        requests_per_second: float,
        error_rate_percent: float,
        scenario_id: Optional[UUID] = None,
        branch: Optional[str] = None,
        commit_sha: Optional[str] = None,
        completed_at: Optional[datetime] = None,
        latency_min_ms: Optional[float] = None,
        latency_max_ms: Optional[float] = None,
        latency_avg_ms: Optional[float] = None,
        bytes_received: Optional[int] = None,
        bytes_sent: Optional[int] = None,
        peak_concurrent_users: Optional[int] = None,
        error_breakdown: Dict[str, int] = None,
        report_url: Optional[str] = None,
        grafana_dashboard_url: Optional[str] = None,
        raw_metrics_url: Optional[str] = None,
    ) -> PerformanceTestResult:
        """Record a performance test result."""
        # Check against thresholds if scenario exists
        thresholds_passed = None
        baseline_comparison = None
        degradation = None

        if scenario_id:
            scenario = await self.get_scenario(scenario_id)
            if scenario:
                thresholds_passed = (
                    latency_p95_ms <= scenario.max_latency_p95_ms and
                    latency_p99_ms <= scenario.max_latency_p99_ms and
                    error_rate_percent <= scenario.max_error_rate_percent
                )
                if scenario.min_throughput_rps:
                    thresholds_passed = (
                        thresholds_passed and
                        requests_per_second >= scenario.min_throughput_rps
                    )

            # Compare to baseline
            baseline = await self.get_active_baseline(scenario_id)
            if baseline:
                baseline_comparison = {
                    "latency_p95_change": (
                        (latency_p95_ms - baseline.latency_p95_ms) /
                        baseline.latency_p95_ms * 100
                    ) if baseline.latency_p95_ms else None,
                    "throughput_change": (
                        (requests_per_second - baseline.throughput_rps) /
                        baseline.throughput_rps * 100
                    ) if baseline.throughput_rps else None,
                }
                if baseline_comparison["latency_p95_change"]:
                    degradation = baseline_comparison["latency_p95_change"]

        duration_seconds = None
        if completed_at and started_at:
            duration_seconds = (completed_at - started_at).total_seconds()

        test_result = PerformanceTestResult(
            tenant_id=self.tenant_id,
            scenario_id=scenario_id,
            branch=branch,
            commit_sha=commit_sha,
            environment=environment,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration_seconds,
            status=status,
            thresholds_passed=thresholds_passed,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            latency_p50_ms=latency_p50_ms,
            latency_p95_ms=latency_p95_ms,
            latency_p99_ms=latency_p99_ms,
            latency_min_ms=latency_min_ms,
            latency_max_ms=latency_max_ms,
            latency_avg_ms=latency_avg_ms,
            requests_per_second=requests_per_second,
            bytes_received=bytes_received,
            bytes_sent=bytes_sent,
            peak_concurrent_users=peak_concurrent_users,
            error_rate_percent=error_rate_percent,
            error_breakdown=error_breakdown or {},
            baseline_comparison=baseline_comparison,
            performance_degradation_percent=degradation,
            report_url=report_url,
            grafana_dashboard_url=grafana_dashboard_url,
            raw_metrics_url=raw_metrics_url,
        )
        self.session.add(test_result)
        await self.session.flush()
        return test_result

    async def get_test_result(
        self,
        result_id: UUID,
    ) -> Optional[PerformanceTestResult]:
        """Get a performance test result by ID."""
        result = await self.session.execute(
            select(PerformanceTestResult).where(
                and_(
                    PerformanceTestResult.id == result_id,
                    PerformanceTestResult.tenant_id == self.tenant_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_test_results(
        self,
        scenario_id: Optional[UUID] = None,
        environment: Optional[TestEnvironment] = None,
        branch: Optional[str] = None,
        limit: int = 50,
    ) -> List[PerformanceTestResult]:
        """List performance test results."""
        query = select(PerformanceTestResult).where(
            PerformanceTestResult.tenant_id == self.tenant_id
        )
        if scenario_id:
            query = query.where(PerformanceTestResult.scenario_id == scenario_id)
        if environment:
            query = query.where(PerformanceTestResult.environment == environment)
        if branch:
            query = query.where(PerformanceTestResult.branch == branch)

        query = query.order_by(desc(PerformanceTestResult.created_at)).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # Endpoint Metrics
    # =========================================================================

    async def add_endpoint_metric(
        self,
        test_result_id: UUID,
        endpoint_url: str,
        http_method: str,
        total_requests: int,
        successful_requests: int,
        failed_requests: int,
        latency_p50_ms: float,
        latency_p95_ms: float,
        latency_p99_ms: float,
        latency_avg_ms: float,
        requests_per_second: float,
    ) -> EndpointPerformanceMetric:
        """Add endpoint-level metrics to a test result."""
        metric = EndpointPerformanceMetric(
            test_result_id=test_result_id,
            endpoint_url=endpoint_url,
            http_method=http_method,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            latency_p50_ms=latency_p50_ms,
            latency_p95_ms=latency_p95_ms,
            latency_p99_ms=latency_p99_ms,
            latency_avg_ms=latency_avg_ms,
            requests_per_second=requests_per_second,
        )
        self.session.add(metric)
        await self.session.flush()
        return metric

    async def get_endpoint_metrics(
        self,
        test_result_id: UUID,
    ) -> List[EndpointPerformanceMetric]:
        """Get endpoint metrics for a test result."""
        result = await self.session.execute(
            select(EndpointPerformanceMetric)
            .where(EndpointPerformanceMetric.test_result_id == test_result_id)
            .order_by(desc(EndpointPerformanceMetric.latency_p95_ms))
        )
        return list(result.scalars().all())

    # =========================================================================
    # Baselines
    # =========================================================================

    async def create_baseline(
        self,
        scenario_id: UUID,
        test_result_id: UUID,
        created_by: UUID,
        latency_tolerance_percent: float = 10.0,
        throughput_tolerance_percent: float = 10.0,
    ) -> Optional[PerformanceBaseline]:
        """Create a performance baseline from a test result."""
        test_result = await self.get_test_result(test_result_id)
        if not test_result:
            return None

        # Deactivate existing baselines for this scenario
        await self.session.execute(
            select(PerformanceBaseline)
            .where(
                and_(
                    PerformanceBaseline.scenario_id == scenario_id,
                    PerformanceBaseline.tenant_id == self.tenant_id,
                    PerformanceBaseline.is_active == True,
                )
            )
        )
        existing = await self.session.execute(
            select(PerformanceBaseline).where(
                and_(
                    PerformanceBaseline.scenario_id == scenario_id,
                    PerformanceBaseline.tenant_id == self.tenant_id,
                    PerformanceBaseline.is_active == True,
                )
            )
        )
        for baseline in existing.scalars().all():
            baseline.is_active = False

        # Create new baseline
        baseline = PerformanceBaseline(
            tenant_id=self.tenant_id,
            scenario_id=scenario_id,
            test_result_id=test_result_id,
            latency_p50_ms=test_result.latency_p50_ms,
            latency_p95_ms=test_result.latency_p95_ms,
            latency_p99_ms=test_result.latency_p99_ms,
            throughput_rps=test_result.requests_per_second,
            error_rate_percent=test_result.error_rate_percent,
            latency_tolerance_percent=latency_tolerance_percent,
            throughput_tolerance_percent=throughput_tolerance_percent,
            is_active=True,
            created_by=created_by,
        )
        self.session.add(baseline)
        await self.session.flush()
        return baseline

    async def get_active_baseline(
        self,
        scenario_id: UUID,
    ) -> Optional[PerformanceBaseline]:
        """Get the active baseline for a scenario."""
        result = await self.session.execute(
            select(PerformanceBaseline).where(
                and_(
                    PerformanceBaseline.scenario_id == scenario_id,
                    PerformanceBaseline.tenant_id == self.tenant_id,
                    PerformanceBaseline.is_active == True,
                )
            )
        )
        return result.scalar_one_or_none()

    async def compare_to_baseline(
        self,
        test_result_id: UUID,
    ) -> Dict[str, Any]:
        """Compare a test result to its scenario's baseline."""
        test_result = await self.get_test_result(test_result_id)
        if not test_result or not test_result.scenario_id:
            return {"error": "Test result or scenario not found"}

        baseline = await self.get_active_baseline(test_result.scenario_id)
        if not baseline:
            return {"error": "No baseline found for scenario"}

        latency_change = (
            (test_result.latency_p95_ms - baseline.latency_p95_ms) /
            baseline.latency_p95_ms * 100
        ) if baseline.latency_p95_ms else 0

        throughput_change = (
            (test_result.requests_per_second - baseline.throughput_rps) /
            baseline.throughput_rps * 100
        ) if baseline.throughput_rps else 0

        latency_within_tolerance = abs(latency_change) <= baseline.latency_tolerance_percent
        throughput_within_tolerance = abs(throughput_change) <= baseline.throughput_tolerance_percent

        return {
            "test_result_id": str(test_result_id),
            "baseline_id": str(baseline.id),
            "latency_p95": {
                "baseline": baseline.latency_p95_ms,
                "actual": test_result.latency_p95_ms,
                "change_percent": round(latency_change, 2),
                "tolerance_percent": baseline.latency_tolerance_percent,
                "within_tolerance": latency_within_tolerance,
            },
            "throughput": {
                "baseline": baseline.throughput_rps,
                "actual": test_result.requests_per_second,
                "change_percent": round(throughput_change, 2),
                "tolerance_percent": baseline.throughput_tolerance_percent,
                "within_tolerance": throughput_within_tolerance,
            },
            "overall_passed": latency_within_tolerance and throughput_within_tolerance,
        }

    # =========================================================================
    # Statistics
    # =========================================================================

    async def get_performance_summary(
        self,
        scenario_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Get performance testing summary."""
        results = await self.list_test_results(scenario_id=scenario_id, limit=10)
        if not results:
            return {
                "total_tests": 0,
                "avg_latency_p95": 0,
                "avg_throughput": 0,
                "pass_rate": 0,
            }

        total = len(results)
        passed = sum(1 for r in results if r.thresholds_passed)
        avg_latency = sum(r.latency_p95_ms or 0 for r in results) / total
        avg_throughput = sum(r.requests_per_second or 0 for r in results) / total

        return {
            "total_tests": total,
            "passed_tests": passed,
            "pass_rate": round(passed / total * 100, 2),
            "avg_latency_p95_ms": round(avg_latency, 2),
            "avg_throughput_rps": round(avg_throughput, 2),
            "latest_result": {
                "id": str(results[0].id),
                "status": results[0].status.value,
                "thresholds_passed": results[0].thresholds_passed,
                "latency_p95_ms": results[0].latency_p95_ms,
            } if results else None,
        }

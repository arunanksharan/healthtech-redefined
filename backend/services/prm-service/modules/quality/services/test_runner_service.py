"""
Test Runner Service

Service for managing test execution, test suites, and test results.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from modules.quality.models import (
    TestSuite, TestRun, TestResult, FlakyTest,
    TestType, TestStatus, TestRunStatus, TestEnvironment, FlakyTestStatus
)


class TestRunnerService:
    """Service for test execution management."""

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id

    # =========================================================================
    # Test Suite Management
    # =========================================================================

    async def create_test_suite(
        self,
        name: str,
        test_type: TestType,
        description: Optional[str] = None,
        file_patterns: List[str] = None,
        exclude_patterns: List[str] = None,
        timeout_seconds: int = 3600,
        parallel_workers: int = 4,
        retry_count: int = 2,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
    ) -> TestSuite:
        """Create a new test suite."""
        suite = TestSuite(
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            test_type=test_type,
            file_patterns=file_patterns or [],
            exclude_patterns=exclude_patterns or [],
            timeout_seconds=timeout_seconds,
            parallel_workers=parallel_workers,
            retry_count=retry_count,
            tags=tags or [],
            metadata=metadata or {},
        )
        self.session.add(suite)
        await self.session.flush()
        return suite

    async def get_test_suite(self, suite_id: UUID) -> Optional[TestSuite]:
        """Get a test suite by ID."""
        result = await self.session.execute(
            select(TestSuite).where(
                and_(
                    TestSuite.id == suite_id,
                    TestSuite.tenant_id == self.tenant_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_test_suites(
        self,
        test_type: Optional[TestType] = None,
        is_active: bool = True,
        tags: Optional[List[str]] = None,
    ) -> List[TestSuite]:
        """List test suites with optional filtering."""
        query = select(TestSuite).where(
            and_(
                TestSuite.tenant_id == self.tenant_id,
                TestSuite.is_active == is_active,
            )
        )

        if test_type:
            query = query.where(TestSuite.test_type == test_type)

        if tags:
            query = query.where(TestSuite.tags.overlap(tags))

        query = query.order_by(desc(TestSuite.created_at))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_test_suite(
        self,
        suite_id: UUID,
        **kwargs,
    ) -> Optional[TestSuite]:
        """Update a test suite."""
        suite = await self.get_test_suite(suite_id)
        if not suite:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(suite, key):
                setattr(suite, key, value)

        suite.updated_at = datetime.utcnow()
        await self.session.flush()
        return suite

    # =========================================================================
    # Test Run Management
    # =========================================================================

    async def create_test_run(
        self,
        environment: TestEnvironment,
        suite_id: Optional[UUID] = None,
        branch: Optional[str] = None,
        commit_sha: Optional[str] = None,
        pull_request_id: Optional[str] = None,
        triggered_by: Optional[str] = None,
        config: Dict[str, Any] = None,
    ) -> TestRun:
        """Create a new test run."""
        # Get next run number
        max_run = await self.session.execute(
            select(func.max(TestRun.run_number)).where(
                TestRun.tenant_id == self.tenant_id
            )
        )
        run_number = (max_run.scalar() or 0) + 1

        test_run = TestRun(
            tenant_id=self.tenant_id,
            suite_id=suite_id,
            run_number=run_number,
            branch=branch,
            commit_sha=commit_sha,
            pull_request_id=pull_request_id,
            environment=environment,
            status=TestRunStatus.QUEUED,
            triggered_by=triggered_by,
            config=config or {},
        )
        self.session.add(test_run)
        await self.session.flush()

        # Update suite last run
        if suite_id:
            suite = await self.get_test_suite(suite_id)
            if suite:
                suite.last_run_at = datetime.utcnow()

        return test_run

    async def start_test_run(self, run_id: UUID) -> Optional[TestRun]:
        """Mark a test run as started."""
        test_run = await self.get_test_run(run_id)
        if not test_run:
            return None

        test_run.status = TestRunStatus.RUNNING
        test_run.started_at = datetime.utcnow()
        await self.session.flush()
        return test_run

    async def complete_test_run(
        self,
        run_id: UUID,
        status: TestRunStatus,
        total_tests: int = 0,
        passed_tests: int = 0,
        failed_tests: int = 0,
        skipped_tests: int = 0,
        error_tests: int = 0,
        flaky_tests: int = 0,
        error_message: Optional[str] = None,
    ) -> Optional[TestRun]:
        """Mark a test run as completed."""
        test_run = await self.get_test_run(run_id)
        if not test_run:
            return None

        test_run.status = status
        test_run.completed_at = datetime.utcnow()
        test_run.total_tests = total_tests
        test_run.passed_tests = passed_tests
        test_run.failed_tests = failed_tests
        test_run.skipped_tests = skipped_tests
        test_run.error_tests = error_tests
        test_run.flaky_tests = flaky_tests
        test_run.error_message = error_message

        if test_run.started_at:
            test_run.duration_seconds = (
                test_run.completed_at - test_run.started_at
            ).total_seconds()

        await self.session.flush()
        return test_run

    async def get_test_run(self, run_id: UUID) -> Optional[TestRun]:
        """Get a test run by ID."""
        result = await self.session.execute(
            select(TestRun).where(
                and_(
                    TestRun.id == run_id,
                    TestRun.tenant_id == self.tenant_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_test_runs(
        self,
        suite_id: Optional[UUID] = None,
        branch: Optional[str] = None,
        status: Optional[TestRunStatus] = None,
        environment: Optional[TestEnvironment] = None,
        limit: int = 50,
    ) -> List[TestRun]:
        """List test runs with optional filtering."""
        query = select(TestRun).where(TestRun.tenant_id == self.tenant_id)

        if suite_id:
            query = query.where(TestRun.suite_id == suite_id)
        if branch:
            query = query.where(TestRun.branch == branch)
        if status:
            query = query.where(TestRun.status == status)
        if environment:
            query = query.where(TestRun.environment == environment)

        query = query.order_by(desc(TestRun.created_at)).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # Test Result Management
    # =========================================================================

    async def create_test_result(
        self,
        test_run_id: UUID,
        test_name: str,
        status: TestStatus,
        test_file: Optional[str] = None,
        test_class: Optional[str] = None,
        test_method: Optional[str] = None,
        duration_ms: Optional[float] = None,
        retry_count: int = 0,
        failure_message: Optional[str] = None,
        failure_stacktrace: Optional[str] = None,
        failure_type: Optional[str] = None,
        assertions_passed: int = 0,
        assertions_failed: int = 0,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        artifacts: List[str] = None,
        tags: List[str] = None,
        parameters: Dict[str, Any] = None,
    ) -> TestResult:
        """Record a test result."""
        result = TestResult(
            tenant_id=self.tenant_id,
            test_run_id=test_run_id,
            test_name=test_name,
            test_file=test_file,
            test_class=test_class,
            test_method=test_method,
            status=status,
            duration_ms=duration_ms,
            retry_count=retry_count,
            failure_message=failure_message,
            failure_stacktrace=failure_stacktrace,
            failure_type=failure_type,
            assertions_passed=assertions_passed,
            assertions_failed=assertions_failed,
            stdout=stdout,
            stderr=stderr,
            artifacts=artifacts or [],
            tags=tags or [],
            parameters=parameters or {},
        )
        self.session.add(result)
        await self.session.flush()

        # Check for flaky test
        if status == TestStatus.FLAKY or (retry_count > 0 and status == TestStatus.PASSED):
            await self._track_flaky_test(test_name, test_file)

        return result

    async def get_test_results(
        self,
        test_run_id: UUID,
        status: Optional[TestStatus] = None,
    ) -> List[TestResult]:
        """Get test results for a test run."""
        query = select(TestResult).where(
            and_(
                TestResult.test_run_id == test_run_id,
                TestResult.tenant_id == self.tenant_id,
            )
        )

        if status:
            query = query.where(TestResult.status == status)

        query = query.order_by(TestResult.test_name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_failed_tests(self, test_run_id: UUID) -> List[TestResult]:
        """Get failed tests for a test run."""
        return await self.get_test_results(test_run_id, status=TestStatus.FAILED)

    # =========================================================================
    # Flaky Test Management
    # =========================================================================

    async def _track_flaky_test(
        self,
        test_name: str,
        test_file: Optional[str],
    ) -> FlakyTest:
        """Track or update a flaky test."""
        result = await self.session.execute(
            select(FlakyTest).where(
                and_(
                    FlakyTest.test_name == test_name,
                    FlakyTest.tenant_id == self.tenant_id,
                )
            )
        )
        flaky = result.scalar_one_or_none()

        if flaky:
            flaky.flake_count += 1
            flaky.total_runs += 1
            flaky.last_flake_at = datetime.utcnow()
            flaky.flake_rate = flaky.flake_count / flaky.total_runs
        else:
            flaky = FlakyTest(
                tenant_id=self.tenant_id,
                test_name=test_name,
                test_file=test_file,
                status=FlakyTestStatus.DETECTED,
                first_detected_at=datetime.utcnow(),
                last_flake_at=datetime.utcnow(),
                flake_count=1,
                total_runs=1,
                flake_rate=1.0,
            )
            self.session.add(flaky)

        await self.session.flush()
        return flaky

    async def list_flaky_tests(
        self,
        status: Optional[FlakyTestStatus] = None,
        min_flake_rate: Optional[float] = None,
    ) -> List[FlakyTest]:
        """List flaky tests."""
        query = select(FlakyTest).where(FlakyTest.tenant_id == self.tenant_id)

        if status:
            query = query.where(FlakyTest.status == status)
        if min_flake_rate:
            query = query.where(FlakyTest.flake_rate >= min_flake_rate)

        query = query.order_by(desc(FlakyTest.flake_rate))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def quarantine_flaky_test(
        self,
        flaky_test_id: UUID,
        reason: str,
        expires_at: Optional[datetime] = None,
    ) -> Optional[FlakyTest]:
        """Quarantine a flaky test."""
        result = await self.session.execute(
            select(FlakyTest).where(
                and_(
                    FlakyTest.id == flaky_test_id,
                    FlakyTest.tenant_id == self.tenant_id,
                )
            )
        )
        flaky = result.scalar_one_or_none()
        if not flaky:
            return None

        flaky.status = FlakyTestStatus.QUARANTINED
        flaky.quarantined_at = datetime.utcnow()
        flaky.quarantine_reason = reason
        flaky.quarantine_expires_at = expires_at
        await self.session.flush()
        return flaky

    async def fix_flaky_test(
        self,
        flaky_test_id: UUID,
        fixed_by: UUID,
        resolution_notes: Optional[str] = None,
    ) -> Optional[FlakyTest]:
        """Mark a flaky test as fixed."""
        result = await self.session.execute(
            select(FlakyTest).where(
                and_(
                    FlakyTest.id == flaky_test_id,
                    FlakyTest.tenant_id == self.tenant_id,
                )
            )
        )
        flaky = result.scalar_one_or_none()
        if not flaky:
            return None

        flaky.status = FlakyTestStatus.FIXED
        flaky.fixed_at = datetime.utcnow()
        flaky.fixed_by = fixed_by
        flaky.resolution_notes = resolution_notes
        await self.session.flush()
        return flaky

    # =========================================================================
    # Statistics
    # =========================================================================

    async def get_test_statistics(
        self,
        branch: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get test execution statistics."""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)

        query = select(TestRun).where(
            and_(
                TestRun.tenant_id == self.tenant_id,
                TestRun.created_at >= cutoff,
            )
        )
        if branch:
            query = query.where(TestRun.branch == branch)

        result = await self.session.execute(query)
        runs = list(result.scalars().all())

        if not runs:
            return {
                "total_runs": 0,
                "pass_rate": 0.0,
                "avg_duration_seconds": 0.0,
                "total_tests": 0,
                "flaky_tests": 0,
            }

        total_runs = len(runs)
        completed_runs = [r for r in runs if r.status == TestRunStatus.COMPLETED]
        passed_runs = [
            r for r in completed_runs
            if r.failed_tests == 0 and r.error_tests == 0
        ]

        pass_rate = len(passed_runs) / total_runs if total_runs > 0 else 0.0

        durations = [r.duration_seconds for r in runs if r.duration_seconds]
        avg_duration = sum(durations) / len(durations) if durations else 0.0

        total_tests = sum(r.total_tests or 0 for r in runs)
        total_flaky = sum(r.flaky_tests or 0 for r in runs)

        return {
            "total_runs": total_runs,
            "completed_runs": len(completed_runs),
            "pass_rate": round(pass_rate * 100, 2),
            "avg_duration_seconds": round(avg_duration, 2),
            "total_tests": total_tests,
            "flaky_tests": total_flaky,
        }

    async def get_test_history(
        self,
        test_name: str,
        limit: int = 100,
    ) -> List[TestResult]:
        """Get execution history for a specific test."""
        result = await self.session.execute(
            select(TestResult)
            .where(
                and_(
                    TestResult.test_name == test_name,
                    TestResult.tenant_id == self.tenant_id,
                )
            )
            .order_by(desc(TestResult.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

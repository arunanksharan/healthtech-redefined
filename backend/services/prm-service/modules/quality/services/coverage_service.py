"""
Coverage Service

Service for managing code coverage reports and thresholds.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from modules.quality.models import (
    CoverageReport, FileCoverage, CoverageThreshold
)


class CoverageService:
    """Service for code coverage management."""

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id

    # =========================================================================
    # Coverage Reports
    # =========================================================================

    async def create_coverage_report(
        self,
        line_coverage: float,
        total_lines: int,
        covered_lines: int,
        test_run_id: Optional[UUID] = None,
        branch: Optional[str] = None,
        commit_sha: Optional[str] = None,
        branch_coverage: Optional[float] = None,
        function_coverage: Optional[float] = None,
        statement_coverage: Optional[float] = None,
        total_branches: Optional[int] = None,
        covered_branches: Optional[int] = None,
        total_functions: Optional[int] = None,
        covered_functions: Optional[int] = None,
        line_threshold: float = 80.0,
        branch_threshold: float = 80.0,
        html_report_url: Optional[str] = None,
        xml_report_url: Optional[str] = None,
        json_report_url: Optional[str] = None,
    ) -> CoverageReport:
        """Create a new coverage report."""
        # Get previous coverage for delta calculation
        previous = await self._get_latest_coverage(branch)
        previous_coverage = previous.line_coverage if previous else None
        coverage_delta = None
        if previous_coverage is not None:
            coverage_delta = line_coverage - previous_coverage

        # Check thresholds
        threshold_passed = line_coverage >= line_threshold
        if branch_coverage is not None:
            threshold_passed = threshold_passed and branch_coverage >= branch_threshold

        report = CoverageReport(
            tenant_id=self.tenant_id,
            test_run_id=test_run_id,
            branch=branch,
            commit_sha=commit_sha,
            line_coverage=line_coverage,
            branch_coverage=branch_coverage,
            function_coverage=function_coverage,
            statement_coverage=statement_coverage,
            total_lines=total_lines,
            covered_lines=covered_lines,
            total_branches=total_branches,
            covered_branches=covered_branches,
            total_functions=total_functions,
            covered_functions=covered_functions,
            line_threshold=line_threshold,
            branch_threshold=branch_threshold,
            threshold_passed=threshold_passed,
            coverage_delta=coverage_delta,
            previous_coverage=previous_coverage,
            html_report_url=html_report_url,
            xml_report_url=xml_report_url,
            json_report_url=json_report_url,
        )
        self.session.add(report)
        await self.session.flush()
        return report

    async def _get_latest_coverage(
        self,
        branch: Optional[str],
    ) -> Optional[CoverageReport]:
        """Get the latest coverage report for a branch."""
        query = select(CoverageReport).where(
            CoverageReport.tenant_id == self.tenant_id
        )
        if branch:
            query = query.where(CoverageReport.branch == branch)

        query = query.order_by(desc(CoverageReport.created_at)).limit(1)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_coverage_report(
        self,
        report_id: UUID,
    ) -> Optional[CoverageReport]:
        """Get a coverage report by ID."""
        result = await self.session.execute(
            select(CoverageReport).where(
                and_(
                    CoverageReport.id == report_id,
                    CoverageReport.tenant_id == self.tenant_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_coverage_reports(
        self,
        branch: Optional[str] = None,
        limit: int = 50,
    ) -> List[CoverageReport]:
        """List coverage reports."""
        query = select(CoverageReport).where(
            CoverageReport.tenant_id == self.tenant_id
        )
        if branch:
            query = query.where(CoverageReport.branch == branch)

        query = query.order_by(desc(CoverageReport.created_at)).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_coverage_trend(
        self,
        branch: str,
        limit: int = 30,
    ) -> List[Dict[str, Any]]:
        """Get coverage trend for a branch."""
        reports = await self.list_coverage_reports(branch=branch, limit=limit)
        return [
            {
                "date": r.created_at,
                "commit_sha": r.commit_sha,
                "line_coverage": r.line_coverage,
                "branch_coverage": r.branch_coverage,
                "delta": r.coverage_delta,
            }
            for r in reversed(reports)
        ]

    # =========================================================================
    # File Coverage
    # =========================================================================

    async def add_file_coverage(
        self,
        report_id: UUID,
        file_path: str,
        line_coverage: float,
        total_lines: int,
        covered_lines: int,
        package_name: Optional[str] = None,
        branch_coverage: Optional[float] = None,
        function_coverage: Optional[float] = None,
        uncovered_lines: List[int] = None,
    ) -> FileCoverage:
        """Add file-level coverage to a report."""
        file_cov = FileCoverage(
            report_id=report_id,
            file_path=file_path,
            package_name=package_name,
            line_coverage=line_coverage,
            branch_coverage=branch_coverage,
            function_coverage=function_coverage,
            total_lines=total_lines,
            covered_lines=covered_lines,
            uncovered_lines=uncovered_lines or [],
        )
        self.session.add(file_cov)
        await self.session.flush()
        return file_cov

    async def get_file_coverages(
        self,
        report_id: UUID,
    ) -> List[FileCoverage]:
        """Get all file coverages for a report."""
        result = await self.session.execute(
            select(FileCoverage)
            .where(FileCoverage.report_id == report_id)
            .order_by(FileCoverage.line_coverage)
        )
        return list(result.scalars().all())

    async def get_low_coverage_files(
        self,
        report_id: UUID,
        threshold: float = 50.0,
    ) -> List[FileCoverage]:
        """Get files with coverage below threshold."""
        result = await self.session.execute(
            select(FileCoverage)
            .where(
                and_(
                    FileCoverage.report_id == report_id,
                    FileCoverage.line_coverage < threshold,
                )
            )
            .order_by(FileCoverage.line_coverage)
        )
        return list(result.scalars().all())

    # =========================================================================
    # Coverage Thresholds
    # =========================================================================

    async def create_coverage_threshold(
        self,
        name: str,
        line_threshold: float = 80.0,
        branch_threshold: float = 80.0,
        function_threshold: float = 80.0,
        description: Optional[str] = None,
        is_blocking: bool = True,
        applies_to_branches: List[str] = None,
        excluded_paths: List[str] = None,
    ) -> CoverageThreshold:
        """Create a coverage threshold configuration."""
        threshold = CoverageThreshold(
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            line_threshold=line_threshold,
            branch_threshold=branch_threshold,
            function_threshold=function_threshold,
            is_blocking=is_blocking,
            applies_to_branches=applies_to_branches or ["main", "master"],
            excluded_paths=excluded_paths or [],
        )
        self.session.add(threshold)
        await self.session.flush()
        return threshold

    async def get_coverage_threshold(
        self,
        threshold_id: UUID,
    ) -> Optional[CoverageThreshold]:
        """Get a coverage threshold by ID."""
        result = await self.session.execute(
            select(CoverageThreshold).where(
                and_(
                    CoverageThreshold.id == threshold_id,
                    CoverageThreshold.tenant_id == self.tenant_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_active_threshold(
        self,
        branch: str,
    ) -> Optional[CoverageThreshold]:
        """Get the active threshold for a branch."""
        result = await self.session.execute(
            select(CoverageThreshold).where(
                and_(
                    CoverageThreshold.tenant_id == self.tenant_id,
                    CoverageThreshold.is_active == True,
                    CoverageThreshold.applies_to_branches.contains([branch]),
                )
            )
        )
        return result.scalar_one_or_none()

    async def evaluate_coverage(
        self,
        report_id: UUID,
        branch: str,
    ) -> Dict[str, Any]:
        """Evaluate coverage against thresholds."""
        report = await self.get_coverage_report(report_id)
        if not report:
            return {"error": "Report not found"}

        threshold = await self.get_active_threshold(branch)
        if not threshold:
            # Use defaults
            threshold_line = 80.0
            threshold_branch = 80.0
            threshold_function = 80.0
        else:
            threshold_line = threshold.line_threshold
            threshold_branch = threshold.branch_threshold
            threshold_function = threshold.function_threshold

        results = []

        # Line coverage check
        line_passed = (report.line_coverage or 0) >= threshold_line
        results.append({
            "metric": "line_coverage",
            "actual": report.line_coverage,
            "threshold": threshold_line,
            "passed": line_passed,
        })

        # Branch coverage check
        if report.branch_coverage is not None:
            branch_passed = report.branch_coverage >= threshold_branch
            results.append({
                "metric": "branch_coverage",
                "actual": report.branch_coverage,
                "threshold": threshold_branch,
                "passed": branch_passed,
            })

        # Function coverage check
        if report.function_coverage is not None:
            function_passed = report.function_coverage >= threshold_function
            results.append({
                "metric": "function_coverage",
                "actual": report.function_coverage,
                "threshold": threshold_function,
                "passed": function_passed,
            })

        all_passed = all(r["passed"] for r in results)

        return {
            "report_id": str(report_id),
            "branch": branch,
            "all_passed": all_passed,
            "is_blocking": threshold.is_blocking if threshold else True,
            "results": results,
        }

    # =========================================================================
    # Statistics
    # =========================================================================

    async def get_coverage_summary(
        self,
        branch: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get coverage summary."""
        latest = await self._get_latest_coverage(branch)
        if not latest:
            return {
                "line_coverage": 0.0,
                "branch_coverage": None,
                "function_coverage": None,
                "threshold_passed": False,
                "trend": "unknown",
            }

        # Determine trend
        trend = "stable"
        if latest.coverage_delta:
            if latest.coverage_delta > 0.5:
                trend = "up"
            elif latest.coverage_delta < -0.5:
                trend = "down"

        return {
            "line_coverage": latest.line_coverage,
            "branch_coverage": latest.branch_coverage,
            "function_coverage": latest.function_coverage,
            "threshold_passed": latest.threshold_passed,
            "coverage_delta": latest.coverage_delta,
            "trend": trend,
            "report_id": str(latest.id),
            "report_date": latest.created_at,
        }

"""
Security Scan Service

Service for managing security scans, vulnerabilities, and security policies.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, and_, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession

from modules.quality.models import (
    SecurityScan, Vulnerability, SecurityPolicy,
    SecurityScanType, VulnerabilitySeverity, VulnerabilityStatus,
    TestRunStatus
)


class SecurityScanService:
    """Service for security testing management."""

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id

    # =========================================================================
    # Security Scans
    # =========================================================================

    async def create_scan(
        self,
        scan_type: SecurityScanType,
        scanner_name: str,
        branch: Optional[str] = None,
        commit_sha: Optional[str] = None,
        scanner_version: Optional[str] = None,
        scan_config: Dict[str, Any] = None,
    ) -> SecurityScan:
        """Create a new security scan."""
        scan = SecurityScan(
            tenant_id=self.tenant_id,
            scan_type=scan_type,
            branch=branch,
            commit_sha=commit_sha,
            status=TestRunStatus.RUNNING,
            started_at=datetime.utcnow(),
            scanner_name=scanner_name,
            scanner_version=scanner_version,
            scan_config=scan_config or {},
        )
        self.session.add(scan)
        await self.session.flush()
        return scan

    async def complete_scan(
        self,
        scan_id: UUID,
        status: TestRunStatus,
        total_findings: int = 0,
        critical_findings: int = 0,
        high_findings: int = 0,
        medium_findings: int = 0,
        low_findings: int = 0,
        info_findings: int = 0,
        report_url: Optional[str] = None,
        sarif_url: Optional[str] = None,
    ) -> Optional[SecurityScan]:
        """Complete a security scan with results."""
        scan = await self.get_scan(scan_id)
        if not scan:
            return None

        scan.status = status
        scan.completed_at = datetime.utcnow()
        scan.duration_seconds = (
            scan.completed_at - scan.started_at
        ).total_seconds()
        scan.total_findings = total_findings
        scan.critical_findings = critical_findings
        scan.high_findings = high_findings
        scan.medium_findings = medium_findings
        scan.low_findings = low_findings
        scan.info_findings = info_findings
        scan.report_url = report_url
        scan.sarif_url = sarif_url

        # Evaluate against policy
        policy = await self.get_active_policy()
        if policy:
            blocking = 0
            if policy.block_critical:
                blocking += critical_findings
            if policy.block_high:
                blocking += high_findings
            if policy.block_medium:
                blocking += medium_findings

            scan.blocking_findings = blocking
            scan.gate_passed = blocking == 0
        else:
            scan.gate_passed = critical_findings == 0 and high_findings == 0

        await self.session.flush()
        return scan

    async def get_scan(self, scan_id: UUID) -> Optional[SecurityScan]:
        """Get a security scan by ID."""
        result = await self.session.execute(
            select(SecurityScan).where(
                and_(
                    SecurityScan.id == scan_id,
                    SecurityScan.tenant_id == self.tenant_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_scans(
        self,
        scan_type: Optional[SecurityScanType] = None,
        branch: Optional[str] = None,
        status: Optional[TestRunStatus] = None,
        limit: int = 50,
    ) -> List[SecurityScan]:
        """List security scans."""
        query = select(SecurityScan).where(
            SecurityScan.tenant_id == self.tenant_id
        )
        if scan_type:
            query = query.where(SecurityScan.scan_type == scan_type)
        if branch:
            query = query.where(SecurityScan.branch == branch)
        if status:
            query = query.where(SecurityScan.status == status)

        query = query.order_by(desc(SecurityScan.created_at)).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # Vulnerabilities
    # =========================================================================

    async def create_vulnerability(
        self,
        title: str,
        severity: VulnerabilitySeverity,
        scan_id: Optional[UUID] = None,
        vulnerability_id: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        cwe_id: Optional[str] = None,
        cve_id: Optional[str] = None,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        column_number: Optional[int] = None,
        code_snippet: Optional[str] = None,
        package_name: Optional[str] = None,
        package_version: Optional[str] = None,
        fixed_version: Optional[str] = None,
        image_name: Optional[str] = None,
        layer_id: Optional[str] = None,
        cvss_score: Optional[float] = None,
        cvss_vector: Optional[str] = None,
        references: List[str] = None,
        remediation_guidance: Optional[str] = None,
    ) -> Vulnerability:
        """Create a vulnerability finding."""
        # Check for existing vulnerability (dedup by CVE or file+line)
        existing = None
        if cve_id:
            result = await self.session.execute(
                select(Vulnerability).where(
                    and_(
                        Vulnerability.cve_id == cve_id,
                        Vulnerability.tenant_id == self.tenant_id,
                        Vulnerability.status != VulnerabilityStatus.FIXED,
                    )
                )
            )
            existing = result.scalar_one_or_none()

        if existing:
            existing.last_seen_at = datetime.utcnow()
            existing.scan_id = scan_id
            await self.session.flush()
            return existing

        vuln = Vulnerability(
            tenant_id=self.tenant_id,
            scan_id=scan_id,
            vulnerability_id=vulnerability_id,
            title=title,
            description=description,
            severity=severity,
            category=category,
            cwe_id=cwe_id,
            cve_id=cve_id,
            file_path=file_path,
            line_number=line_number,
            column_number=column_number,
            code_snippet=code_snippet,
            package_name=package_name,
            package_version=package_version,
            fixed_version=fixed_version,
            image_name=image_name,
            layer_id=layer_id,
            status=VulnerabilityStatus.OPEN,
            cvss_score=cvss_score,
            cvss_vector=cvss_vector,
            references=references or [],
            remediation_guidance=remediation_guidance,
        )
        self.session.add(vuln)
        await self.session.flush()
        return vuln

    async def get_vulnerability(
        self,
        vuln_id: UUID,
    ) -> Optional[Vulnerability]:
        """Get a vulnerability by ID."""
        result = await self.session.execute(
            select(Vulnerability).where(
                and_(
                    Vulnerability.id == vuln_id,
                    Vulnerability.tenant_id == self.tenant_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def update_vulnerability(
        self,
        vuln_id: UUID,
        status: Optional[VulnerabilityStatus] = None,
        assigned_to: Optional[UUID] = None,
        due_date: Optional[datetime] = None,
        resolution_notes: Optional[str] = None,
        resolved_by: Optional[UUID] = None,
    ) -> Optional[Vulnerability]:
        """Update a vulnerability."""
        vuln = await self.get_vulnerability(vuln_id)
        if not vuln:
            return None

        if status:
            vuln.status = status
            if status == VulnerabilityStatus.FIXED:
                vuln.resolved_at = datetime.utcnow()
                vuln.resolved_by = resolved_by

        if assigned_to:
            vuln.assigned_to = assigned_to
        if due_date:
            vuln.due_date = due_date
        if resolution_notes:
            vuln.resolution_notes = resolution_notes

        vuln.updated_at = datetime.utcnow()
        await self.session.flush()
        return vuln

    async def suppress_vulnerability(
        self,
        vuln_id: UUID,
        reason: str,
        suppressed_by: UUID,
        suppressed_until: Optional[datetime] = None,
    ) -> Optional[Vulnerability]:
        """Suppress a vulnerability (false positive or accepted risk)."""
        vuln = await self.get_vulnerability(vuln_id)
        if not vuln:
            return None

        vuln.is_suppressed = True
        vuln.suppression_reason = reason
        vuln.suppressed_by = suppressed_by
        vuln.suppressed_until = suppressed_until
        vuln.status = VulnerabilityStatus.ACCEPTED
        vuln.updated_at = datetime.utcnow()
        await self.session.flush()
        return vuln

    async def list_vulnerabilities(
        self,
        scan_id: Optional[UUID] = None,
        severity: Optional[VulnerabilitySeverity] = None,
        status: Optional[VulnerabilityStatus] = None,
        include_suppressed: bool = False,
        limit: int = 100,
    ) -> List[Vulnerability]:
        """List vulnerabilities."""
        query = select(Vulnerability).where(
            Vulnerability.tenant_id == self.tenant_id
        )
        if scan_id:
            query = query.where(Vulnerability.scan_id == scan_id)
        if severity:
            query = query.where(Vulnerability.severity == severity)
        if status:
            query = query.where(Vulnerability.status == status)
        if not include_suppressed:
            query = query.where(Vulnerability.is_suppressed == False)

        query = query.order_by(
            Vulnerability.severity,
            desc(Vulnerability.created_at)
        ).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_open_vulnerabilities(
        self,
        severity: Optional[VulnerabilitySeverity] = None,
    ) -> List[Vulnerability]:
        """Get all open vulnerabilities."""
        return await self.list_vulnerabilities(
            status=VulnerabilityStatus.OPEN,
            severity=severity,
        )

    async def get_overdue_vulnerabilities(self) -> List[Vulnerability]:
        """Get vulnerabilities past their due date."""
        now = datetime.utcnow()
        result = await self.session.execute(
            select(Vulnerability).where(
                and_(
                    Vulnerability.tenant_id == self.tenant_id,
                    Vulnerability.status == VulnerabilityStatus.OPEN,
                    Vulnerability.due_date < now,
                )
            ).order_by(Vulnerability.due_date)
        )
        return list(result.scalars().all())

    # =========================================================================
    # Security Policies
    # =========================================================================

    async def create_policy(
        self,
        name: str,
        description: Optional[str] = None,
        block_critical: bool = True,
        block_high: bool = True,
        block_medium: bool = False,
        max_critical_age_days: int = 1,
        max_high_age_days: int = 7,
        max_medium_age_days: int = 30,
        exempt_paths: List[str] = None,
        exempt_rules: List[str] = None,
        notify_on_critical: bool = True,
        notification_channels: List[Dict[str, Any]] = None,
    ) -> SecurityPolicy:
        """Create a security policy."""
        policy = SecurityPolicy(
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            block_critical=block_critical,
            block_high=block_high,
            block_medium=block_medium,
            max_critical_age_days=max_critical_age_days,
            max_high_age_days=max_high_age_days,
            max_medium_age_days=max_medium_age_days,
            exempt_paths=exempt_paths or [],
            exempt_rules=exempt_rules or [],
            notify_on_critical=notify_on_critical,
            notification_channels=notification_channels or [],
        )
        self.session.add(policy)
        await self.session.flush()
        return policy

    async def get_active_policy(self) -> Optional[SecurityPolicy]:
        """Get the active security policy."""
        result = await self.session.execute(
            select(SecurityPolicy).where(
                and_(
                    SecurityPolicy.tenant_id == self.tenant_id,
                    SecurityPolicy.is_active == True,
                )
            )
        )
        return result.scalar_one_or_none()

    async def evaluate_policy(
        self,
        scan_id: UUID,
    ) -> Dict[str, Any]:
        """Evaluate a scan against the active policy."""
        scan = await self.get_scan(scan_id)
        if not scan:
            return {"error": "Scan not found"}

        policy = await self.get_active_policy()
        if not policy:
            return {
                "scan_id": str(scan_id),
                "policy": None,
                "gate_passed": scan.critical_findings == 0,
                "blocking_findings": scan.critical_findings,
            }

        blocking = 0
        violations = []

        if policy.block_critical and scan.critical_findings > 0:
            blocking += scan.critical_findings
            violations.append({
                "rule": "block_critical",
                "count": scan.critical_findings,
            })

        if policy.block_high and scan.high_findings > 0:
            blocking += scan.high_findings
            violations.append({
                "rule": "block_high",
                "count": scan.high_findings,
            })

        if policy.block_medium and scan.medium_findings > 0:
            blocking += scan.medium_findings
            violations.append({
                "rule": "block_medium",
                "count": scan.medium_findings,
            })

        return {
            "scan_id": str(scan_id),
            "policy_id": str(policy.id),
            "policy_name": policy.name,
            "gate_passed": blocking == 0,
            "blocking_findings": blocking,
            "violations": violations,
            "total_findings": scan.total_findings,
        }

    # =========================================================================
    # Statistics
    # =========================================================================

    async def get_security_summary(self) -> Dict[str, Any]:
        """Get security testing summary."""
        # Count open vulnerabilities by severity
        result = await self.session.execute(
            select(
                Vulnerability.severity,
                func.count(Vulnerability.id)
            )
            .where(
                and_(
                    Vulnerability.tenant_id == self.tenant_id,
                    Vulnerability.status == VulnerabilityStatus.OPEN,
                    Vulnerability.is_suppressed == False,
                )
            )
            .group_by(Vulnerability.severity)
        )
        severity_counts = dict(result.all())

        total_open = sum(severity_counts.values())

        # Count fixed in last 30 days
        cutoff = datetime.utcnow() - timedelta(days=30)
        fixed_result = await self.session.execute(
            select(func.count(Vulnerability.id)).where(
                and_(
                    Vulnerability.tenant_id == self.tenant_id,
                    Vulnerability.status == VulnerabilityStatus.FIXED,
                    Vulnerability.resolved_at >= cutoff,
                )
            )
        )
        fixed_count = fixed_result.scalar() or 0

        # Get latest scans
        latest_scans = await self.list_scans(limit=5)

        return {
            "total_open_vulnerabilities": total_open,
            "critical": severity_counts.get(VulnerabilitySeverity.CRITICAL, 0),
            "high": severity_counts.get(VulnerabilitySeverity.HIGH, 0),
            "medium": severity_counts.get(VulnerabilitySeverity.MEDIUM, 0),
            "low": severity_counts.get(VulnerabilitySeverity.LOW, 0),
            "fixed_last_30_days": fixed_count,
            "latest_scans": [
                {
                    "id": str(s.id),
                    "type": s.scan_type.value,
                    "status": s.status.value,
                    "gate_passed": s.gate_passed,
                    "findings": s.total_findings,
                    "date": s.created_at,
                }
                for s in latest_scans
            ],
        }

    async def get_vulnerability_trends(
        self,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """Get vulnerability trends over time."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        result = await self.session.execute(
            select(
                func.date_trunc('day', Vulnerability.first_detected_at).label('date'),
                Vulnerability.severity,
                func.count(Vulnerability.id).label('count')
            )
            .where(
                and_(
                    Vulnerability.tenant_id == self.tenant_id,
                    Vulnerability.first_detected_at >= cutoff,
                )
            )
            .group_by('date', Vulnerability.severity)
            .order_by('date')
        )

        trends = {}
        for row in result.all():
            date_str = row.date.strftime('%Y-%m-%d')
            if date_str not in trends:
                trends[date_str] = {
                    "date": date_str,
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                }
            trends[date_str][row.severity.value] = row.count

        return list(trends.values())

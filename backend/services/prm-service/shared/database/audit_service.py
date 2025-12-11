"""
Audit Logging Service

EPIC-004: Multi-Tenancy Implementation
US-004.6: Tenant Security & Compliance

Provides comprehensive audit logging:
- Action tracking
- Change history
- Compliance reporting
- Audit trail export
- HIPAA compliance support
"""

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from .tenant_context import get_current_tenant

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """Types of auditable actions."""
    # CRUD Operations
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"

    # Authentication
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    LOGIN_FAILED = "LOGIN_FAILED"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    PASSWORD_RESET = "PASSWORD_RESET"
    MFA_ENABLED = "MFA_ENABLED"
    MFA_DISABLED = "MFA_DISABLED"

    # Access Control
    PERMISSION_GRANTED = "PERMISSION_GRANTED"
    PERMISSION_REVOKED = "PERMISSION_REVOKED"
    ROLE_ASSIGNED = "ROLE_ASSIGNED"
    ROLE_REMOVED = "ROLE_REMOVED"

    # Data Access
    PHI_ACCESSED = "PHI_ACCESSED"
    EXPORT_REQUESTED = "EXPORT_REQUESTED"
    EXPORT_DOWNLOADED = "EXPORT_DOWNLOADED"
    REPORT_GENERATED = "REPORT_GENERATED"

    # Administrative
    CONFIG_CHANGED = "CONFIG_CHANGED"
    USER_INVITED = "USER_INVITED"
    USER_SUSPENDED = "USER_SUSPENDED"
    API_KEY_CREATED = "API_KEY_CREATED"
    API_KEY_REVOKED = "API_KEY_REVOKED"

    # System
    SYSTEM_ERROR = "SYSTEM_ERROR"
    SECURITY_ALERT = "SECURITY_ALERT"


class AuditCategory(str, Enum):
    """Categories for audit entries."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    CONFIGURATION = "configuration"
    SECURITY = "security"
    COMPLIANCE = "compliance"


@dataclass
class AuditEntry:
    """An audit log entry."""
    tenant_id: str
    action: AuditAction
    resource_type: str
    resource_id: Optional[str] = None
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    changes: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    category: AuditCategory = AuditCategory.DATA_ACCESS
    severity: str = "INFO"
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AuditService:
    """
    Manages audit logging for tenants.

    Provides HIPAA-compliant audit trail functionality.
    """

    def __init__(self, db_session_factory, async_writer=None):
        self.db_factory = db_session_factory
        self.async_writer = async_writer  # Optional async queue for high-throughput

    def log(self, entry: AuditEntry):
        """
        Log an audit entry synchronously.

        Args:
            entry: Audit entry to log
        """
        db = self.db_factory()
        try:
            db.execute(
                text("""
                    INSERT INTO tenant_audit_logs (
                        tenant_id, user_id, action, resource_type, resource_id,
                        old_values, new_values, changes, ip_address, user_agent,
                        request_id, session_id, metadata, created_at
                    ) VALUES (
                        :tenant_id, :user_id, :action, :resource_type, :resource_id,
                        :old_values, :new_values, :changes, :ip_address, :user_agent,
                        :request_id, :session_id, :metadata, :created_at
                    )
                """),
                {
                    "tenant_id": entry.tenant_id,
                    "user_id": entry.user_id,
                    "action": entry.action.value,
                    "resource_type": entry.resource_type,
                    "resource_id": entry.resource_id,
                    "old_values": json.dumps(entry.old_values) if entry.old_values else None,
                    "new_values": json.dumps(entry.new_values) if entry.new_values else None,
                    "changes": json.dumps(entry.changes) if entry.changes else None,
                    "ip_address": entry.ip_address,
                    "user_agent": entry.user_agent,
                    "request_id": entry.request_id,
                    "session_id": entry.session_id,
                    "metadata": json.dumps({
                        "category": entry.category.value,
                        "severity": entry.severity,
                        **entry.metadata,
                    }),
                    "created_at": entry.timestamp,
                }
            )
            db.commit()
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
            db.rollback()
            raise
        finally:
            db.close()

    async def log_async(self, entry: AuditEntry):
        """
        Log an audit entry asynchronously.

        Args:
            entry: Audit entry to log
        """
        if self.async_writer:
            await self.async_writer.write(entry)
        else:
            self.log(entry)

    def log_action(
        self,
        action: AuditAction,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        old_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
        **metadata,
    ):
        """
        Convenience method to log an action.

        Args:
            action: The action being performed
            resource_type: Type of resource (e.g., "patient", "appointment")
            resource_id: ID of the specific resource
            user_id: ID of the user performing the action
            user_email: Email of the user
            old_values: Previous state (for updates)
            new_values: New state (for creates/updates)
            ip_address: Client IP address
            request_id: Request correlation ID
            **metadata: Additional metadata
        """
        tenant_id = get_current_tenant()
        if not tenant_id:
            logger.warning("Audit log without tenant context")
            return

        # Calculate changes
        changes = None
        if old_values and new_values:
            changes = self._compute_changes(old_values, new_values)

        # Determine category
        category = self._get_category(action)

        entry = AuditEntry(
            tenant_id=tenant_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            user_email=user_email,
            old_values=old_values,
            new_values=new_values,
            changes=changes,
            ip_address=ip_address,
            request_id=request_id,
            category=category,
            metadata=metadata,
        )

        self.log(entry)

    def query(
        self,
        tenant_id: str,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        category: Optional[AuditCategory] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[Dict], int]:
        """
        Query audit logs with filters.

        Returns:
            Tuple of (entries, total_count)
        """
        conditions = ["tenant_id = :tenant_id"]
        params = {"tenant_id": tenant_id, "limit": limit, "offset": offset}

        if action:
            conditions.append("action = :action")
            params["action"] = action.value

        if resource_type:
            conditions.append("resource_type = :resource_type")
            params["resource_type"] = resource_type

        if resource_id:
            conditions.append("resource_id = :resource_id")
            params["resource_id"] = resource_id

        if user_id:
            conditions.append("user_id = :user_id")
            params["user_id"] = user_id

        if start_date:
            conditions.append("created_at >= :start_date")
            params["start_date"] = start_date

        if end_date:
            conditions.append("created_at <= :end_date")
            params["end_date"] = end_date

        if category:
            conditions.append("metadata->>'category' = :category")
            params["category"] = category.value

        where_clause = " AND ".join(conditions)

        db = self.db_factory()
        try:
            # Get count
            count = db.execute(
                text(f"SELECT COUNT(*) FROM tenant_audit_logs WHERE {where_clause}"),
                params
            ).scalar()

            # Get entries
            results = db.execute(
                text(f"""
                    SELECT
                        id, action, resource_type, resource_id, user_id,
                        old_values, new_values, changes, ip_address, user_agent,
                        request_id, session_id, metadata, created_at
                    FROM tenant_audit_logs
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """),
                params
            ).fetchall()

            entries = [
                {
                    "id": str(r.id),
                    "action": r.action,
                    "resource_type": r.resource_type,
                    "resource_id": str(r.resource_id) if r.resource_id else None,
                    "user_id": str(r.user_id) if r.user_id else None,
                    "old_values": r.old_values,
                    "new_values": r.new_values,
                    "changes": r.changes,
                    "ip_address": r.ip_address,
                    "user_agent": r.user_agent,
                    "request_id": r.request_id,
                    "metadata": r.metadata,
                    "created_at": r.created_at.isoformat(),
                }
                for r in results
            ]

            return entries, count
        finally:
            db.close()

    def get_user_activity(
        self,
        tenant_id: str,
        user_id: str,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get activity summary for a user."""
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        db = self.db_factory()
        try:
            # Get action counts
            result = db.execute(
                text("""
                    SELECT action, COUNT(*) as count
                    FROM tenant_audit_logs
                    WHERE tenant_id = :tenant_id
                      AND user_id = :user_id
                      AND created_at >= :start_date
                    GROUP BY action
                    ORDER BY count DESC
                """),
                {"tenant_id": tenant_id, "user_id": user_id, "start_date": start_date}
            ).fetchall()

            action_counts = {r.action: r.count for r in result}

            # Get resource type counts
            result = db.execute(
                text("""
                    SELECT resource_type, COUNT(*) as count
                    FROM tenant_audit_logs
                    WHERE tenant_id = :tenant_id
                      AND user_id = :user_id
                      AND created_at >= :start_date
                    GROUP BY resource_type
                    ORDER BY count DESC
                """),
                {"tenant_id": tenant_id, "user_id": user_id, "start_date": start_date}
            ).fetchall()

            resource_counts = {r.resource_type: r.count for r in result}

            # Get last activity
            last_activity = db.execute(
                text("""
                    SELECT created_at
                    FROM tenant_audit_logs
                    WHERE tenant_id = :tenant_id AND user_id = :user_id
                    ORDER BY created_at DESC
                    LIMIT 1
                """),
                {"tenant_id": tenant_id, "user_id": user_id}
            ).scalar()

            return {
                "user_id": user_id,
                "period_days": days,
                "action_counts": action_counts,
                "resource_counts": resource_counts,
                "total_actions": sum(action_counts.values()),
                "last_activity": last_activity.isoformat() if last_activity else None,
            }
        finally:
            db.close()

    def get_resource_history(
        self,
        tenant_id: str,
        resource_type: str,
        resource_id: str,
        limit: int = 50,
    ) -> List[Dict]:
        """Get change history for a specific resource."""
        entries, _ = self.query(
            tenant_id=tenant_id,
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit,
        )
        return entries

    def generate_compliance_report(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """
        Generate a compliance report for audit purposes.

        Useful for HIPAA compliance audits.
        """
        db = self.db_factory()
        try:
            # Get overall stats
            stats = db.execute(
                text("""
                    SELECT
                        COUNT(*) as total_events,
                        COUNT(DISTINCT user_id) as unique_users,
                        COUNT(DISTINCT resource_type) as resource_types,
                        COUNT(CASE WHEN action = 'PHI_ACCESSED' THEN 1 END) as phi_accesses,
                        COUNT(CASE WHEN action IN ('LOGIN_FAILED', 'SECURITY_ALERT') THEN 1 END) as security_events
                    FROM tenant_audit_logs
                    WHERE tenant_id = :tenant_id
                      AND created_at >= :start_date
                      AND created_at <= :end_date
                """),
                {"tenant_id": tenant_id, "start_date": start_date, "end_date": end_date}
            ).fetchone()

            # Get actions by category
            categories = db.execute(
                text("""
                    SELECT
                        metadata->>'category' as category,
                        COUNT(*) as count
                    FROM tenant_audit_logs
                    WHERE tenant_id = :tenant_id
                      AND created_at >= :start_date
                      AND created_at <= :end_date
                    GROUP BY metadata->>'category'
                """),
                {"tenant_id": tenant_id, "start_date": start_date, "end_date": end_date}
            ).fetchall()

            # Get top users by activity
            top_users = db.execute(
                text("""
                    SELECT
                        l.user_id,
                        u.email as user_email,
                        COUNT(*) as action_count
                    FROM tenant_audit_logs l
                    LEFT JOIN users u ON l.user_id = u.id
                    WHERE l.tenant_id = :tenant_id
                      AND l.created_at >= :start_date
                      AND l.created_at <= :end_date
                      AND l.user_id IS NOT NULL
                    GROUP BY l.user_id, u.email
                    ORDER BY action_count DESC
                    LIMIT 10
                """),
                {"tenant_id": tenant_id, "start_date": start_date, "end_date": end_date}
            ).fetchall()

            # Get security events
            security_events = db.execute(
                text("""
                    SELECT action, COUNT(*) as count
                    FROM tenant_audit_logs
                    WHERE tenant_id = :tenant_id
                      AND created_at >= :start_date
                      AND created_at <= :end_date
                      AND action IN ('LOGIN_FAILED', 'SECURITY_ALERT', 'PERMISSION_REVOKED', 'USER_SUSPENDED')
                    GROUP BY action
                """),
                {"tenant_id": tenant_id, "start_date": start_date, "end_date": end_date}
            ).fetchall()

            return {
                "tenant_id": tenant_id,
                "report_period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "summary": {
                    "total_events": stats.total_events,
                    "unique_users": stats.unique_users,
                    "resource_types": stats.resource_types,
                    "phi_accesses": stats.phi_accesses,
                    "security_events": stats.security_events,
                },
                "by_category": {c.category: c.count for c in categories if c.category},
                "top_users": [
                    {"user_id": str(u.user_id), "email": u.user_email, "actions": u.action_count}
                    for u in top_users
                ],
                "security_events": {s.action: s.count for s in security_events},
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
        finally:
            db.close()

    def export_audit_trail(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
        format: str = "json",
    ) -> str:
        """
        Export audit trail for compliance or archival.

        Returns file path of exported data.
        """
        entries, _ = self.query(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            limit=1000000,  # Export all
        )

        # TODO: Implement actual file export to S3 or local storage
        # For now, return as JSON string
        import json
        return json.dumps({
            "tenant_id": tenant_id,
            "export_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "total_entries": len(entries),
            "entries": entries,
        }, indent=2, default=str)

    def _compute_changes(
        self,
        old_values: Dict,
        new_values: Dict,
    ) -> Dict[str, Dict]:
        """Compute the diff between old and new values."""
        changes = {}

        all_keys = set(old_values.keys()) | set(new_values.keys())

        for key in all_keys:
            old_val = old_values.get(key)
            new_val = new_values.get(key)

            if old_val != new_val:
                changes[key] = {
                    "old": old_val,
                    "new": new_val,
                }

        return changes if changes else None

    def _get_category(self, action: AuditAction) -> AuditCategory:
        """Determine category for an action."""
        auth_actions = {
            AuditAction.LOGIN, AuditAction.LOGOUT, AuditAction.LOGIN_FAILED,
            AuditAction.PASSWORD_CHANGE, AuditAction.PASSWORD_RESET,
            AuditAction.MFA_ENABLED, AuditAction.MFA_DISABLED,
        }

        authz_actions = {
            AuditAction.PERMISSION_GRANTED, AuditAction.PERMISSION_REVOKED,
            AuditAction.ROLE_ASSIGNED, AuditAction.ROLE_REMOVED,
        }

        data_access_actions = {
            AuditAction.READ, AuditAction.PHI_ACCESSED,
            AuditAction.EXPORT_REQUESTED, AuditAction.EXPORT_DOWNLOADED,
            AuditAction.REPORT_GENERATED,
        }

        config_actions = {
            AuditAction.CONFIG_CHANGED, AuditAction.USER_INVITED,
            AuditAction.API_KEY_CREATED, AuditAction.API_KEY_REVOKED,
        }

        security_actions = {
            AuditAction.SECURITY_ALERT, AuditAction.USER_SUSPENDED,
        }

        if action in auth_actions:
            return AuditCategory.AUTHENTICATION
        elif action in authz_actions:
            return AuditCategory.AUTHORIZATION
        elif action in data_access_actions:
            return AuditCategory.DATA_ACCESS
        elif action in config_actions:
            return AuditCategory.CONFIGURATION
        elif action in security_actions:
            return AuditCategory.SECURITY
        else:
            return AuditCategory.DATA_MODIFICATION


# Audit decorator for automatic logging
def audited(
    action: AuditAction,
    resource_type: str,
    id_param: str = "id",
):
    """
    Decorator to automatically audit function calls.

    Usage:
        @audited(AuditAction.UPDATE, "patient", id_param="patient_id")
        async def update_patient(patient_id: str, data: PatientUpdate):
            ...
    """
    def decorator(func):
        import functools
        import inspect

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Get resource ID from kwargs
            resource_id = kwargs.get(id_param)

            # Get audit service (injected or global)
            audit_service = kwargs.get("audit_service")

            try:
                result = await func(*args, **kwargs)

                if audit_service:
                    audit_service.log_action(
                        action=action,
                        resource_type=resource_type,
                        resource_id=str(resource_id) if resource_id else None,
                    )

                return result
            except Exception as e:
                if audit_service:
                    audit_service.log_action(
                        action=AuditAction.SYSTEM_ERROR,
                        resource_type=resource_type,
                        resource_id=str(resource_id) if resource_id else None,
                        error=str(e),
                    )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            resource_id = kwargs.get(id_param)
            audit_service = kwargs.get("audit_service")

            try:
                result = func(*args, **kwargs)

                if audit_service:
                    audit_service.log_action(
                        action=action,
                        resource_type=resource_type,
                        resource_id=str(resource_id) if resource_id else None,
                    )

                return result
            except Exception as e:
                if audit_service:
                    audit_service.log_action(
                        action=AuditAction.SYSTEM_ERROR,
                        resource_type=resource_type,
                        resource_id=str(resource_id) if resource_id else None,
                        error=str(e),
                    )
                raise

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator

"""
Security Monitoring and Threat Detection Service

Provides real-time security monitoring, threat detection, and incident response.
EPIC-021: Security Hardening
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
import secrets

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from modules.security.models import (
    SecurityEvent,
    ThreatDetectionRule,
    SecurityIncident,
    IncidentResponse,
    SecurityAuditLog,
    ThreatType,
    ThreatSeverity,
    IncidentStatus,
)


class SecurityMonitoringService:
    """Security Monitoring and Threat Detection Service"""

    # Incident number prefix
    INCIDENT_PREFIX = "SEC"

    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # Security Event Management
    # =========================================================================

    def create_event(
        self,
        event_type: str,
        severity: ThreatSeverity,
        title: str,
        tenant_id: Optional[UUID] = None,
        threat_type: Optional[ThreatType] = None,
        description: Optional[str] = None,
        details: Optional[Dict] = None,
        source_ip: Optional[str] = None,
        source_user_id: Optional[UUID] = None,
        source_service: Optional[str] = None,
        target_resource_type: Optional[str] = None,
        target_resource_id: Optional[str] = None,
        target_user_id: Optional[UUID] = None,
        detection_rule_id: Optional[str] = None,
        confidence_score: Optional[float] = None,
        correlation_id: Optional[str] = None,
    ) -> SecurityEvent:
        """Create a security event"""

        event = SecurityEvent(
            tenant_id=tenant_id,
            event_type=event_type,
            threat_type=threat_type,
            severity=severity,
            title=title,
            description=description,
            details=details,
            source_ip=source_ip,
            source_user_id=source_user_id,
            source_service=source_service,
            target_resource_type=target_resource_type,
            target_resource_id=target_resource_id,
            target_user_id=target_user_id,
            detection_rule_id=detection_rule_id,
            confidence_score=confidence_score,
            correlation_id=correlation_id or secrets.token_hex(16),
        )

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        # Check if this event should trigger automated response
        self._check_automated_response(event)

        return event

    def get_event(
        self,
        event_id: UUID,
    ) -> Optional[SecurityEvent]:
        """Get security event by ID"""

        return self.db.query(SecurityEvent).filter(
            SecurityEvent.id == event_id,
        ).first()

    def list_events(
        self,
        tenant_id: Optional[UUID] = None,
        severity: Optional[ThreatSeverity] = None,
        threat_type: Optional[ThreatType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 100,
    ) -> List[SecurityEvent]:
        """List security events with filters"""

        query = self.db.query(SecurityEvent)

        if tenant_id:
            query = query.filter(SecurityEvent.tenant_id == tenant_id)
        if severity:
            query = query.filter(SecurityEvent.severity == severity)
        if threat_type:
            query = query.filter(SecurityEvent.threat_type == threat_type)
        if start_time:
            query = query.filter(SecurityEvent.detected_at >= start_time)
        if end_time:
            query = query.filter(SecurityEvent.detected_at <= end_time)
        if acknowledged is not None:
            query = query.filter(SecurityEvent.is_acknowledged == acknowledged)

        return query.order_by(SecurityEvent.detected_at.desc()).limit(limit).all()

    def acknowledge_event(
        self,
        event_id: UUID,
        acknowledged_by: UUID,
    ) -> bool:
        """Acknowledge a security event"""

        event = self.get_event(event_id)
        if not event:
            return False

        event.is_acknowledged = True
        event.acknowledged_by = acknowledged_by
        event.acknowledged_at = datetime.utcnow()

        self.db.commit()

        return True

    def correlate_events(
        self,
        correlation_id: str,
    ) -> List[SecurityEvent]:
        """Get all events with same correlation ID"""

        return self.db.query(SecurityEvent).filter(
            SecurityEvent.correlation_id == correlation_id,
        ).order_by(SecurityEvent.detected_at).all()

    # =========================================================================
    # Threat Detection Rules
    # =========================================================================

    def create_detection_rule(
        self,
        name: str,
        threat_type: ThreatType,
        severity: ThreatSeverity,
        conditions: Dict[str, Any],
        tenant_id: Optional[UUID] = None,
        description: Optional[str] = None,
        rule_type: str = "threshold",
        threshold_count: Optional[int] = None,
        threshold_window_minutes: Optional[int] = None,
        actions: Optional[Dict] = None,
    ) -> ThreatDetectionRule:
        """Create a threat detection rule"""

        rule = ThreatDetectionRule(
            tenant_id=tenant_id,
            name=name,
            description=description,
            threat_type=threat_type,
            severity=severity,
            rule_type=rule_type,
            conditions=conditions,
            threshold_count=threshold_count,
            threshold_window_minutes=threshold_window_minutes,
            actions=actions or {"alert": True},
        )

        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)

        return rule

    def get_detection_rule(
        self,
        rule_id: UUID,
    ) -> Optional[ThreatDetectionRule]:
        """Get detection rule by ID"""

        return self.db.query(ThreatDetectionRule).filter(
            ThreatDetectionRule.id == rule_id,
        ).first()

    def list_detection_rules(
        self,
        tenant_id: Optional[UUID] = None,
        threat_type: Optional[ThreatType] = None,
        is_active: bool = True,
    ) -> List[ThreatDetectionRule]:
        """List detection rules"""

        query = self.db.query(ThreatDetectionRule)

        if tenant_id:
            query = query.filter(
                or_(
                    ThreatDetectionRule.tenant_id == tenant_id,
                    ThreatDetectionRule.tenant_id == None,
                )
            )
        if threat_type:
            query = query.filter(ThreatDetectionRule.threat_type == threat_type)

        query = query.filter(ThreatDetectionRule.is_active == is_active)

        return query.order_by(ThreatDetectionRule.severity.desc()).all()

    def update_detection_rule(
        self,
        rule_id: UUID,
        **kwargs,
    ) -> Optional[ThreatDetectionRule]:
        """Update detection rule"""

        rule = self.get_detection_rule(rule_id)
        if not rule:
            return None

        if rule.is_system_rule:
            raise ValueError("Cannot modify system rules")

        for key, value in kwargs.items():
            if hasattr(rule, key) and key not in ["id", "is_system_rule"]:
                setattr(rule, key, value)

        rule.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(rule)

        return rule

    def evaluate_rules(
        self,
        event_type: str,
        context: Dict[str, Any],
        tenant_id: Optional[UUID] = None,
    ) -> List[Dict[str, Any]]:
        """Evaluate detection rules against context"""

        rules = self.list_detection_rules(tenant_id=tenant_id)
        triggered_rules = []

        for rule in rules:
            if self._evaluate_rule(rule, event_type, context):
                triggered_rules.append({
                    "rule_id": str(rule.id),
                    "rule_name": rule.name,
                    "threat_type": rule.threat_type.value,
                    "severity": rule.severity.value,
                    "actions": rule.actions,
                })

                # Update rule stats
                rule.trigger_count += 1
                rule.last_triggered_at = datetime.utcnow()

        self.db.commit()

        return triggered_rules

    def _evaluate_rule(
        self,
        rule: ThreatDetectionRule,
        event_type: str,
        context: Dict[str, Any],
    ) -> bool:
        """Evaluate a single detection rule"""

        conditions = rule.conditions or {}

        # Check event type match
        if "event_types" in conditions:
            if event_type not in conditions["event_types"]:
                return False

        # Check threshold conditions
        if rule.rule_type == "threshold":
            threshold_field = conditions.get("field")
            if threshold_field:
                value = context.get(threshold_field, 0)
                if value < rule.threshold_count:
                    return False

        # Check pattern conditions
        if rule.rule_type == "pattern":
            pattern = conditions.get("pattern")
            field = conditions.get("field")
            if pattern and field:
                import re
                value = context.get(field, "")
                if not re.search(pattern, str(value)):
                    return False

        return True

    # =========================================================================
    # Security Incident Management
    # =========================================================================

    def create_incident(
        self,
        title: str,
        severity: ThreatSeverity,
        tenant_id: Optional[UUID] = None,
        description: Optional[str] = None,
        threat_type: Optional[ThreatType] = None,
        attack_vector: Optional[str] = None,
        affected_systems: Optional[List[str]] = None,
        data_breach: bool = False,
        phi_involved: bool = False,
        detected_at: Optional[datetime] = None,
        related_event_ids: Optional[List[UUID]] = None,
    ) -> SecurityIncident:
        """Create a security incident"""

        # Generate incident number
        incident_count = self.db.query(SecurityIncident).count()
        incident_number = f"{self.INCIDENT_PREFIX}-{datetime.utcnow().strftime('%Y%m')}-{incident_count + 1:04d}"

        incident = SecurityIncident(
            tenant_id=tenant_id,
            incident_number=incident_number,
            title=title,
            description=description,
            severity=severity,
            status=IncidentStatus.NEW,
            threat_type=threat_type,
            attack_vector=attack_vector,
            affected_systems=affected_systems or [],
            data_breach=data_breach,
            phi_involved=phi_involved,
            detected_at=detected_at or datetime.utcnow(),
            related_event_ids=related_event_ids or [],
        )

        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)

        return incident

    def get_incident(
        self,
        incident_id: UUID,
    ) -> Optional[SecurityIncident]:
        """Get incident by ID"""

        return self.db.query(SecurityIncident).filter(
            SecurityIncident.id == incident_id,
        ).first()

    def get_incident_by_number(
        self,
        incident_number: str,
    ) -> Optional[SecurityIncident]:
        """Get incident by number"""

        return self.db.query(SecurityIncident).filter(
            SecurityIncident.incident_number == incident_number,
        ).first()

    def list_incidents(
        self,
        tenant_id: Optional[UUID] = None,
        status: Optional[IncidentStatus] = None,
        severity: Optional[ThreatSeverity] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[SecurityIncident]:
        """List security incidents"""

        query = self.db.query(SecurityIncident)

        if tenant_id:
            query = query.filter(SecurityIncident.tenant_id == tenant_id)
        if status:
            query = query.filter(SecurityIncident.status == status)
        if severity:
            query = query.filter(SecurityIncident.severity == severity)
        if start_time:
            query = query.filter(SecurityIncident.detected_at >= start_time)
        if end_time:
            query = query.filter(SecurityIncident.detected_at <= end_time)

        return query.order_by(SecurityIncident.detected_at.desc()).limit(limit).all()

    def update_incident_status(
        self,
        incident_id: UUID,
        status: IncidentStatus,
        assigned_to: Optional[UUID] = None,
    ) -> Optional[SecurityIncident]:
        """Update incident status"""

        incident = self.get_incident(incident_id)
        if not incident:
            return None

        incident.status = status
        incident.updated_at = datetime.utcnow()

        # Update timestamps based on status
        if status == IncidentStatus.CONTAINED:
            incident.contained_at = datetime.utcnow()
        elif status == IncidentStatus.ERADICATED:
            incident.eradicated_at = datetime.utcnow()
        elif status == IncidentStatus.RECOVERED:
            incident.recovered_at = datetime.utcnow()
        elif status == IncidentStatus.CLOSED:
            incident.closed_at = datetime.utcnow()

        if assigned_to:
            incident.assigned_to = assigned_to

        self.db.commit()
        self.db.refresh(incident)

        return incident

    def add_incident_response(
        self,
        incident_id: UUID,
        action_type: str,
        description: str,
        performed_by: UUID,
        evidence_collected: Optional[Dict] = None,
        attachments: Optional[List[str]] = None,
    ) -> IncidentResponse:
        """Add incident response action"""

        response = IncidentResponse(
            incident_id=incident_id,
            action_type=action_type,
            description=description,
            performed_by=performed_by,
            evidence_collected=evidence_collected,
            attachments=attachments or [],
        )

        self.db.add(response)
        self.db.commit()
        self.db.refresh(response)

        return response

    def get_incident_responses(
        self,
        incident_id: UUID,
    ) -> List[IncidentResponse]:
        """Get all responses for incident"""

        return self.db.query(IncidentResponse).filter(
            IncidentResponse.incident_id == incident_id,
        ).order_by(IncidentResponse.performed_at).all()

    def close_incident(
        self,
        incident_id: UUID,
        root_cause: Optional[str] = None,
        remediation_steps: Optional[Dict] = None,
        lessons_learned: Optional[str] = None,
    ) -> Optional[SecurityIncident]:
        """Close incident with post-mortem details"""

        incident = self.get_incident(incident_id)
        if not incident:
            return None

        incident.status = IncidentStatus.CLOSED
        incident.closed_at = datetime.utcnow()
        incident.root_cause = root_cause
        incident.remediation_steps = remediation_steps
        incident.lessons_learned = lessons_learned
        incident.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(incident)

        return incident

    # =========================================================================
    # Security Audit Logging
    # =========================================================================

    def log_audit_event(
        self,
        event_category: str,
        event_type: str,
        event_action: str,
        outcome: str,
        tenant_id: Optional[UUID] = None,
        actor_id: Optional[UUID] = None,
        actor_type: Optional[str] = None,
        actor_ip: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        description: Optional[str] = None,
        details: Optional[Dict] = None,
        failure_reason: Optional[str] = None,
        hipaa_relevant: bool = False,
        phi_accessed: bool = False,
    ) -> SecurityAuditLog:
        """Log a security audit event"""

        audit = SecurityAuditLog(
            tenant_id=tenant_id,
            event_category=event_category,
            event_type=event_type,
            event_action=event_action,
            actor_id=actor_id,
            actor_type=actor_type,
            actor_ip=actor_ip,
            target_type=target_type,
            target_id=target_id,
            description=description,
            details=details,
            outcome=outcome,
            failure_reason=failure_reason,
            hipaa_relevant=hipaa_relevant,
            phi_accessed=phi_accessed,
        )

        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)

        return audit

    def list_audit_logs(
        self,
        tenant_id: Optional[UUID] = None,
        actor_id: Optional[UUID] = None,
        event_category: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        hipaa_only: bool = False,
        limit: int = 100,
    ) -> List[SecurityAuditLog]:
        """List audit logs with filters"""

        query = self.db.query(SecurityAuditLog)

        if tenant_id:
            query = query.filter(SecurityAuditLog.tenant_id == tenant_id)
        if actor_id:
            query = query.filter(SecurityAuditLog.actor_id == actor_id)
        if event_category:
            query = query.filter(SecurityAuditLog.event_category == event_category)
        if start_time:
            query = query.filter(SecurityAuditLog.occurred_at >= start_time)
        if end_time:
            query = query.filter(SecurityAuditLog.occurred_at <= end_time)
        if hipaa_only:
            query = query.filter(SecurityAuditLog.hipaa_relevant == True)

        return query.order_by(SecurityAuditLog.occurred_at.desc()).limit(limit).all()

    # =========================================================================
    # Security Dashboard & Analytics
    # =========================================================================

    def get_security_dashboard(
        self,
        tenant_id: Optional[UUID] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get security dashboard metrics"""

        since = datetime.utcnow() - timedelta(days=days)

        # Event statistics
        total_events = self.db.query(SecurityEvent).filter(
            SecurityEvent.tenant_id == tenant_id if tenant_id else True,
            SecurityEvent.detected_at >= since,
        ).count()

        events_by_severity = dict(
            self.db.query(
                SecurityEvent.severity,
                func.count(SecurityEvent.id),
            ).filter(
                SecurityEvent.tenant_id == tenant_id if tenant_id else True,
                SecurityEvent.detected_at >= since,
            ).group_by(SecurityEvent.severity).all()
        )

        events_by_type = dict(
            self.db.query(
                SecurityEvent.threat_type,
                func.count(SecurityEvent.id),
            ).filter(
                SecurityEvent.tenant_id == tenant_id if tenant_id else True,
                SecurityEvent.detected_at >= since,
                SecurityEvent.threat_type != None,
            ).group_by(SecurityEvent.threat_type).all()
        )

        # Incident statistics
        open_incidents = self.db.query(SecurityIncident).filter(
            SecurityIncident.tenant_id == tenant_id if tenant_id else True,
            SecurityIncident.status.not_in([IncidentStatus.CLOSED, IncidentStatus.RECOVERED]),
        ).count()

        incidents_last_30_days = self.db.query(SecurityIncident).filter(
            SecurityIncident.tenant_id == tenant_id if tenant_id else True,
            SecurityIncident.detected_at >= since,
        ).count()

        # Calculate average response time
        closed_incidents = self.db.query(SecurityIncident).filter(
            SecurityIncident.tenant_id == tenant_id if tenant_id else True,
            SecurityIncident.closed_at != None,
            SecurityIncident.detected_at >= since,
        ).all()

        avg_response_hours = 0
        if closed_incidents:
            total_hours = sum(
                (i.closed_at - i.detected_at).total_seconds() / 3600
                for i in closed_incidents
            )
            avg_response_hours = total_hours / len(closed_incidents)

        # Top threats
        top_threats = self.db.query(
            SecurityEvent.threat_type,
            func.count(SecurityEvent.id).label("count"),
        ).filter(
            SecurityEvent.tenant_id == tenant_id if tenant_id else True,
            SecurityEvent.detected_at >= since,
            SecurityEvent.threat_type != None,
        ).group_by(
            SecurityEvent.threat_type,
        ).order_by(
            func.count(SecurityEvent.id).desc(),
        ).limit(5).all()

        return {
            "period_days": days,
            "events": {
                "total": total_events,
                "by_severity": {
                    k.value if k else "unknown": v
                    for k, v in events_by_severity.items()
                },
                "by_type": {
                    k.value if k else "unknown": v
                    for k, v in events_by_type.items()
                },
                "unacknowledged": self.db.query(SecurityEvent).filter(
                    SecurityEvent.tenant_id == tenant_id if tenant_id else True,
                    SecurityEvent.is_acknowledged == False,
                ).count(),
            },
            "incidents": {
                "open": open_incidents,
                "last_30_days": incidents_last_30_days,
                "avg_response_hours": round(avg_response_hours, 2),
            },
            "top_threats": [
                {"type": t[0].value if t[0] else "unknown", "count": t[1]}
                for t in top_threats
            ],
            "compliance": {
                "phi_access_events": self.db.query(SecurityAuditLog).filter(
                    SecurityAuditLog.tenant_id == tenant_id if tenant_id else True,
                    SecurityAuditLog.phi_accessed == True,
                    SecurityAuditLog.occurred_at >= since,
                ).count(),
            },
        }

    # =========================================================================
    # Automated Response
    # =========================================================================

    def _check_automated_response(
        self,
        event: SecurityEvent,
    ) -> None:
        """Check if event should trigger automated response"""

        # Get applicable rules
        rules = self.db.query(ThreatDetectionRule).filter(
            or_(
                ThreatDetectionRule.tenant_id == event.tenant_id,
                ThreatDetectionRule.tenant_id == None,
            ),
            ThreatDetectionRule.threat_type == event.threat_type,
            ThreatDetectionRule.is_active == True,
        ).all()

        for rule in rules:
            actions = rule.actions or {}

            # Auto-create incident for critical events
            if actions.get("create_incident") and event.severity in [ThreatSeverity.CRITICAL, ThreatSeverity.HIGH]:
                self.create_incident(
                    title=f"Auto-generated: {event.title}",
                    severity=event.severity,
                    tenant_id=event.tenant_id,
                    threat_type=event.threat_type,
                    detected_at=event.detected_at,
                    related_event_ids=[event.id],
                )

            # Future: Add more automated responses
            # - Account lockout
            # - Session termination
            # - IP blocking
            # - Alert notifications

    # =========================================================================
    # Initialize Default Rules
    # =========================================================================

    def initialize_default_rules(self) -> int:
        """Initialize default threat detection rules"""

        default_rules = [
            {
                "name": "Brute Force Detection",
                "threat_type": ThreatType.BRUTE_FORCE,
                "severity": ThreatSeverity.HIGH,
                "rule_type": "threshold",
                "conditions": {"event_types": ["login_failed"]},
                "threshold_count": 5,
                "threshold_window_minutes": 5,
                "actions": {"alert": True, "lock_account": True},
            },
            {
                "name": "Credential Stuffing Detection",
                "threat_type": ThreatType.CREDENTIAL_STUFFING,
                "severity": ThreatSeverity.HIGH,
                "rule_type": "threshold",
                "conditions": {"event_types": ["login_failed"], "unique_users": True},
                "threshold_count": 10,
                "threshold_window_minutes": 10,
                "actions": {"alert": True, "block_ip": True},
            },
            {
                "name": "Privilege Escalation Attempt",
                "threat_type": ThreatType.PRIVILEGE_ESCALATION,
                "severity": ThreatSeverity.CRITICAL,
                "rule_type": "pattern",
                "conditions": {"event_types": ["permission_denied", "role_change_attempt"]},
                "threshold_count": 3,
                "threshold_window_minutes": 60,
                "actions": {"alert": True, "create_incident": True},
            },
            {
                "name": "Data Exfiltration Detection",
                "threat_type": ThreatType.DATA_EXFILTRATION,
                "severity": ThreatSeverity.CRITICAL,
                "rule_type": "threshold",
                "conditions": {"event_types": ["bulk_export", "api_rate_exceeded"]},
                "threshold_count": 1,
                "threshold_window_minutes": 60,
                "actions": {"alert": True, "create_incident": True},
            },
            {
                "name": "Unauthorized PHI Access",
                "threat_type": ThreatType.UNAUTHORIZED_ACCESS,
                "severity": ThreatSeverity.HIGH,
                "rule_type": "pattern",
                "conditions": {"event_types": ["phi_access_denied", "break_glass_access"]},
                "threshold_count": 1,
                "threshold_window_minutes": 1,
                "actions": {"alert": True},
            },
        ]

        count = 0
        for rule_config in default_rules:
            existing = self.db.query(ThreatDetectionRule).filter(
                ThreatDetectionRule.name == rule_config["name"],
                ThreatDetectionRule.is_system_rule == True,
            ).first()

            if not existing:
                rule = ThreatDetectionRule(
                    name=rule_config["name"],
                    threat_type=rule_config["threat_type"],
                    severity=rule_config["severity"],
                    rule_type=rule_config["rule_type"],
                    conditions=rule_config["conditions"],
                    threshold_count=rule_config.get("threshold_count"),
                    threshold_window_minutes=rule_config.get("threshold_window_minutes"),
                    actions=rule_config["actions"],
                    is_system_rule=True,
                )
                self.db.add(rule)
                count += 1

        self.db.commit()

        return count

"""
PHI Audit Logging Service

Comprehensive audit logging for HIPAA compliance with tamper-proof storage.
Maps to FHIR AuditEvent resource format.
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID, uuid4
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from modules.hipaa.models import (
    PHIAuditLog,
    AuditRetentionPolicy,
    AuditAction,
    AuditOutcome,
    PHICategory,
    AccessJustification,
)


class AuditService:
    """
    Service for HIPAA-compliant PHI audit logging.

    Features:
    - High-performance async logging
    - Tamper-proof hash chain verification
    - FHIR AuditEvent mapping
    - Comprehensive search and filtering
    - Retention policy management
    - Archive to cold storage
    """

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    async def log_phi_access(
        self,
        event_type: str,
        action: AuditAction,
        phi_category: PHICategory,
        resource_type: str,
        resource_id: Optional[UUID] = None,
        patient_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        user_name: Optional[str] = None,
        user_type: Optional[str] = None,
        user_role: Optional[str] = None,
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[UUID] = None,
        request_id: Optional[str] = None,
        patient_mrn: Optional[str] = None,
        encounter_id: Optional[UUID] = None,
        justification: Optional[AccessJustification] = None,
        justification_details: Optional[str] = None,
        fields_accessed: Optional[List[str]] = None,
        query_parameters: Optional[Dict[str, Any]] = None,
        data_before: Optional[Dict[str, Any]] = None,
        data_after: Optional[Dict[str, Any]] = None,
        outcome: AuditOutcome = AuditOutcome.SUCCESS,
        service_name: Optional[str] = None,
        api_endpoint: Optional[str] = None,
        http_method: Optional[str] = None,
        response_code: Optional[int] = None,
    ) -> PHIAuditLog:
        """
        Log a PHI access event with tamper-proof hash chain.
        """
        # Generate unique event ID
        event_id = f"AUD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8].upper()}"

        # Get previous hash for chain
        previous_hash = await self._get_previous_hash()

        # Create audit log entry
        audit_log = PHIAuditLog(
            tenant_id=self.tenant_id,
            event_id=event_id,
            event_type=event_type,
            action=action,
            outcome=outcome,
            recorded_at=datetime.utcnow(),
            user_id=user_id,
            user_type=user_type,
            user_name=user_name,
            user_role=user_role,
            source_ip=source_ip,
            user_agent=user_agent,
            session_id=session_id,
            request_id=request_id,
            phi_category=phi_category,
            resource_type=resource_type,
            resource_id=resource_id,
            patient_id=patient_id,
            patient_mrn=patient_mrn,
            encounter_id=encounter_id,
            justification=justification,
            justification_details=justification_details,
            fields_accessed=fields_accessed,
            query_parameters=query_parameters,
            data_before=data_before,
            data_after=data_after,
            service_name=service_name,
            api_endpoint=api_endpoint,
            http_method=http_method,
            response_code=response_code,
            previous_hash=previous_hash,
            record_hash="",  # Will be set below
        )

        # Calculate record hash
        audit_log.record_hash = self._calculate_record_hash(audit_log, previous_hash)

        # Generate FHIR AuditEvent ID and coding
        audit_log.fhir_audit_event_id = f"AuditEvent/{audit_log.id}"
        audit_log.fhir_event_coding = self._generate_fhir_coding(action, phi_category)

        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)

        return audit_log

    async def _get_previous_hash(self) -> Optional[str]:
        """Get the hash of the previous audit log entry for chain verification."""
        query = (
            select(PHIAuditLog.record_hash)
            .where(PHIAuditLog.tenant_id == self.tenant_id)
            .order_by(desc(PHIAuditLog.created_at))
            .limit(1)
        )
        result = await self.db.execute(query)
        row = result.scalar_one_or_none()
        return row

    def _calculate_record_hash(self, log: PHIAuditLog, previous_hash: Optional[str]) -> str:
        """Calculate SHA-256 hash of audit record for tamper detection."""
        hash_input = {
            "event_id": log.event_id,
            "event_type": log.event_type,
            "action": log.action.value if log.action else None,
            "outcome": log.outcome.value if log.outcome else None,
            "recorded_at": log.recorded_at.isoformat() if log.recorded_at else None,
            "user_id": str(log.user_id) if log.user_id else None,
            "phi_category": log.phi_category.value if log.phi_category else None,
            "resource_type": log.resource_type,
            "resource_id": str(log.resource_id) if log.resource_id else None,
            "patient_id": str(log.patient_id) if log.patient_id else None,
            "previous_hash": previous_hash,
        }
        hash_string = json.dumps(hash_input, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()

    def _generate_fhir_coding(self, action: AuditAction, phi_category: PHICategory) -> Dict[str, Any]:
        """Generate FHIR AuditEvent coding based on action type."""
        action_codes = {
            AuditAction.CREATE: ("C", "Create"),
            AuditAction.READ: ("R", "Read"),
            AuditAction.UPDATE: ("U", "Update"),
            AuditAction.DELETE: ("D", "Delete"),
            AuditAction.EXECUTE: ("E", "Execute"),
        }
        code, display = action_codes.get(action, ("R", "Read"))

        return {
            "type": {
                "system": "http://dicom.nema.org/resources/ontology/DCM",
                "code": "110110",
                "display": "Patient Record",
            },
            "subtype": [{
                "system": "http://hl7.org/fhir/restful-interaction",
                "code": code.lower(),
                "display": display.lower(),
            }],
            "action": code,
        }

    async def search_logs(
        self,
        user_id: Optional[UUID] = None,
        patient_id: Optional[UUID] = None,
        action: Optional[AuditAction] = None,
        phi_category: Optional[PHICategory] = None,
        resource_type: Optional[str] = None,
        outcome: Optional[AuditOutcome] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        source_ip: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[PHIAuditLog], int]:
        """
        Search audit logs with comprehensive filtering.
        """
        query = select(PHIAuditLog).where(PHIAuditLog.tenant_id == self.tenant_id)

        # Apply filters
        if user_id:
            query = query.where(PHIAuditLog.user_id == user_id)
        if patient_id:
            query = query.where(PHIAuditLog.patient_id == patient_id)
        if action:
            query = query.where(PHIAuditLog.action == action)
        if phi_category:
            query = query.where(PHIAuditLog.phi_category == phi_category)
        if resource_type:
            query = query.where(PHIAuditLog.resource_type == resource_type)
        if outcome:
            query = query.where(PHIAuditLog.outcome == outcome)
        if start_date:
            query = query.where(PHIAuditLog.recorded_at >= start_date)
        if end_date:
            query = query.where(PHIAuditLog.recorded_at <= end_date)
        if source_ip:
            query = query.where(PHIAuditLog.source_ip == source_ip)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and ordering
        query = query.order_by(desc(PHIAuditLog.recorded_at))
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        logs = list(result.scalars().all())

        return logs, total

    async def get_log_by_id(self, log_id: UUID) -> Optional[PHIAuditLog]:
        """Get a specific audit log entry."""
        query = select(PHIAuditLog).where(
            and_(
                PHIAuditLog.id == log_id,
                PHIAuditLog.tenant_id == self.tenant_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def verify_log_integrity(self, log_id: UUID) -> Dict[str, Any]:
        """Verify the integrity of an audit log entry and its chain."""
        log = await self.get_log_by_id(log_id)
        if not log:
            return {"valid": False, "error": "Log not found"}

        # Recalculate hash
        calculated_hash = self._calculate_record_hash(log, log.previous_hash)

        if calculated_hash != log.record_hash:
            return {
                "valid": False,
                "error": "Hash mismatch - record may have been tampered",
                "stored_hash": log.record_hash,
                "calculated_hash": calculated_hash,
            }

        # Verify chain if previous hash exists
        if log.previous_hash:
            query = select(PHIAuditLog).where(
                and_(
                    PHIAuditLog.tenant_id == self.tenant_id,
                    PHIAuditLog.record_hash == log.previous_hash
                )
            )
            result = await self.db.execute(query)
            previous_log = result.scalar_one_or_none()

            if not previous_log:
                return {
                    "valid": False,
                    "error": "Previous log in chain not found",
                    "missing_hash": log.previous_hash,
                }

        return {"valid": True, "log_id": str(log_id), "hash": log.record_hash}

    async def get_patient_access_history(
        self,
        patient_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[PHIAuditLog]:
        """Get complete access history for a specific patient."""
        query = select(PHIAuditLog).where(
            and_(
                PHIAuditLog.tenant_id == self.tenant_id,
                PHIAuditLog.patient_id == patient_id
            )
        )

        if start_date:
            query = query.where(PHIAuditLog.recorded_at >= start_date)
        if end_date:
            query = query.where(PHIAuditLog.recorded_at <= end_date)

        query = query.order_by(desc(PHIAuditLog.recorded_at))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_user_access_history(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[PHIAuditLog]:
        """Get complete access history for a specific user."""
        query = select(PHIAuditLog).where(
            and_(
                PHIAuditLog.tenant_id == self.tenant_id,
                PHIAuditLog.user_id == user_id
            )
        )

        if start_date:
            query = query.where(PHIAuditLog.recorded_at >= start_date)
        if end_date:
            query = query.where(PHIAuditLog.recorded_at <= end_date)

        query = query.order_by(desc(PHIAuditLog.recorded_at))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_audit_statistics(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, Any]:
        """Get audit log statistics for reporting."""
        base_query = select(PHIAuditLog).where(
            and_(
                PHIAuditLog.tenant_id == self.tenant_id,
                PHIAuditLog.recorded_at >= start_date,
                PHIAuditLog.recorded_at <= end_date
            )
        )

        # Total count
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.db.execute(count_query)
        total_events = total_result.scalar()

        # Count by action
        action_query = (
            select(PHIAuditLog.action, func.count(PHIAuditLog.id))
            .where(
                and_(
                    PHIAuditLog.tenant_id == self.tenant_id,
                    PHIAuditLog.recorded_at >= start_date,
                    PHIAuditLog.recorded_at <= end_date
                )
            )
            .group_by(PHIAuditLog.action)
        )
        action_result = await self.db.execute(action_query)
        events_by_action = {row[0].value: row[1] for row in action_result.all()}

        # Count by PHI category
        category_query = (
            select(PHIAuditLog.phi_category, func.count(PHIAuditLog.id))
            .where(
                and_(
                    PHIAuditLog.tenant_id == self.tenant_id,
                    PHIAuditLog.recorded_at >= start_date,
                    PHIAuditLog.recorded_at <= end_date
                )
            )
            .group_by(PHIAuditLog.phi_category)
        )
        category_result = await self.db.execute(category_query)
        events_by_category = {row[0].value: row[1] for row in category_result.all()}

        # Count by outcome
        outcome_query = (
            select(PHIAuditLog.outcome, func.count(PHIAuditLog.id))
            .where(
                and_(
                    PHIAuditLog.tenant_id == self.tenant_id,
                    PHIAuditLog.recorded_at >= start_date,
                    PHIAuditLog.recorded_at <= end_date
                )
            )
            .group_by(PHIAuditLog.outcome)
        )
        outcome_result = await self.db.execute(outcome_query)
        events_by_outcome = {row[0].value: row[1] for row in outcome_result.all()}

        # Top users
        user_query = (
            select(PHIAuditLog.user_id, PHIAuditLog.user_name, func.count(PHIAuditLog.id).label("count"))
            .where(
                and_(
                    PHIAuditLog.tenant_id == self.tenant_id,
                    PHIAuditLog.recorded_at >= start_date,
                    PHIAuditLog.recorded_at <= end_date,
                    PHIAuditLog.user_id.isnot(None)
                )
            )
            .group_by(PHIAuditLog.user_id, PHIAuditLog.user_name)
            .order_by(desc("count"))
            .limit(10)
        )
        user_result = await self.db.execute(user_query)
        top_users = [
            {"user_id": str(row[0]), "user_name": row[1], "count": row[2]}
            for row in user_result.all()
        ]

        return {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "total_events": total_events,
            "events_by_action": events_by_action,
            "events_by_category": events_by_category,
            "events_by_outcome": events_by_outcome,
            "top_users": top_users,
        }

    # =========================================================================
    # Retention Policy Management
    # =========================================================================

    async def create_retention_policy(
        self,
        name: str,
        retention_days: int = 2555,  # 7 years default
        archive_after_days: int = 365,
        archive_storage_class: str = "GLACIER",
        description: Optional[str] = None,
        applies_to_actions: Optional[List[str]] = None,
        applies_to_categories: Optional[List[str]] = None,
        is_default: bool = False,
        created_by: Optional[UUID] = None,
    ) -> AuditRetentionPolicy:
        """Create an audit retention policy."""
        if is_default:
            # Clear existing default
            query = select(AuditRetentionPolicy).where(
                and_(
                    AuditRetentionPolicy.tenant_id == self.tenant_id,
                    AuditRetentionPolicy.is_default == True
                )
            )
            result = await self.db.execute(query)
            existing_default = result.scalar_one_or_none()
            if existing_default:
                existing_default.is_default = False

        policy = AuditRetentionPolicy(
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            retention_days=retention_days,
            archive_after_days=archive_after_days,
            archive_storage_class=archive_storage_class,
            applies_to_actions=applies_to_actions,
            applies_to_categories=applies_to_categories,
            is_default=is_default,
            created_by=created_by,
        )

        self.db.add(policy)
        await self.db.commit()
        await self.db.refresh(policy)

        return policy

    async def list_retention_policies(self, active_only: bool = True) -> List[AuditRetentionPolicy]:
        """List audit retention policies."""
        query = select(AuditRetentionPolicy).where(
            AuditRetentionPolicy.tenant_id == self.tenant_id
        )

        if active_only:
            query = query.where(AuditRetentionPolicy.is_active == True)

        query = query.order_by(AuditRetentionPolicy.created_at)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_logs_for_archival(self, archive_after_days: int) -> List[PHIAuditLog]:
        """Get audit logs that should be archived based on retention policy."""
        cutoff_date = datetime.utcnow() - timedelta(days=archive_after_days)

        query = select(PHIAuditLog).where(
            and_(
                PHIAuditLog.tenant_id == self.tenant_id,
                PHIAuditLog.recorded_at < cutoff_date,
                PHIAuditLog.archived == False
            )
        ).order_by(PHIAuditLog.recorded_at)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def mark_logs_archived(
        self,
        log_ids: List[UUID],
        archive_location: str,
    ) -> int:
        """Mark logs as archived after successful archival to cold storage."""
        for log_id in log_ids:
            query = select(PHIAuditLog).where(
                and_(
                    PHIAuditLog.id == log_id,
                    PHIAuditLog.tenant_id == self.tenant_id
                )
            )
            result = await self.db.execute(query)
            log = result.scalar_one_or_none()

            if log:
                log.archived = True
                log.archived_at = datetime.utcnow()
                log.archive_location = archive_location

        await self.db.commit()
        return len(log_ids)

    async def export_logs_for_investigation(
        self,
        patient_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Export audit logs for investigation in a format suitable for external review."""
        logs, _ = await self.search_logs(
            patient_id=patient_id,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=10000,  # Max export limit
        )

        export_data = []
        for log in logs:
            export_data.append({
                "event_id": log.event_id,
                "recorded_at": log.recorded_at.isoformat(),
                "action": log.action.value if log.action else None,
                "outcome": log.outcome.value if log.outcome else None,
                "user_id": str(log.user_id) if log.user_id else None,
                "user_name": log.user_name,
                "user_role": log.user_role,
                "source_ip": str(log.source_ip) if log.source_ip else None,
                "phi_category": log.phi_category.value if log.phi_category else None,
                "resource_type": log.resource_type,
                "resource_id": str(log.resource_id) if log.resource_id else None,
                "patient_id": str(log.patient_id) if log.patient_id else None,
                "justification": log.justification.value if log.justification else None,
                "justification_details": log.justification_details,
                "fields_accessed": log.fields_accessed,
                "record_hash": log.record_hash,
                "previous_hash": log.previous_hash,
            })

        return export_data

    async def generate_fhir_audit_event(self, log: PHIAuditLog) -> Dict[str, Any]:
        """Generate FHIR R4 AuditEvent resource from audit log."""
        return {
            "resourceType": "AuditEvent",
            "id": str(log.id),
            "type": log.fhir_event_coding.get("type") if log.fhir_event_coding else None,
            "subtype": log.fhir_event_coding.get("subtype") if log.fhir_event_coding else None,
            "action": log.fhir_event_coding.get("action") if log.fhir_event_coding else None,
            "recorded": log.recorded_at.isoformat() + "Z",
            "outcome": "0" if log.outcome == AuditOutcome.SUCCESS else "8",
            "agent": [{
                "type": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                        "code": "AUT",
                    }]
                },
                "who": {
                    "reference": f"Practitioner/{log.user_id}" if log.user_id else None,
                    "display": log.user_name,
                },
                "requestor": True,
                "network": {
                    "address": str(log.source_ip) if log.source_ip else None,
                    "type": "2",
                } if log.source_ip else None,
            }],
            "source": {
                "site": "PRM Healthcare Platform",
                "observer": {
                    "reference": "Device/prm-api-server",
                },
            },
            "entity": [{
                "what": {
                    "reference": f"Patient/{log.patient_id}" if log.patient_id else None,
                },
                "type": {
                    "system": "http://terminology.hl7.org/CodeSystem/audit-entity-type",
                    "code": "1",
                    "display": "Person",
                },
                "role": {
                    "system": "http://terminology.hl7.org/CodeSystem/object-role",
                    "code": "1",
                    "display": "Patient",
                },
            }] if log.patient_id else [],
        }

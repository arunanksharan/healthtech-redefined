"""
Training and Policy Management Service

HIPAA training tracking and policy acknowledgment for compliance.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
import hashlib

from modules.hipaa.models import (
    TrainingModule,
    TrainingAssignment,
    PolicyDocument,
    PolicyAcknowledgment,
    TrainingType,
    TrainingStatus,
)


class TrainingService:
    """
    Service for HIPAA training and policy management.

    Features:
    - Training module management
    - Training assignment and tracking
    - Training completion and certificates
    - Policy document management
    - Policy acknowledgment workflow
    - Compliance reporting
    """

    def __init__(self, db: AsyncSession, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    # =========================================================================
    # Training Module Management
    # =========================================================================

    async def create_training_module(
        self,
        name: str,
        training_type: TrainingType,
        duration_minutes: int,
        version: str,
        effective_date: date,
        description: Optional[str] = None,
        content_url: Optional[str] = None,
        passing_score: int = 80,
        required_for_roles: Optional[List[str]] = None,
        required_for_all: bool = False,
        required_for_phi_access: bool = False,
        recurrence_months: Optional[int] = None,
        created_by: Optional[UUID] = None,
    ) -> TrainingModule:
        """Create a training module."""
        module = TrainingModule(
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            training_type=training_type,
            content_url=content_url,
            duration_minutes=duration_minutes,
            passing_score=passing_score,
            required_for_roles=required_for_roles,
            required_for_all=required_for_all,
            required_for_phi_access=required_for_phi_access,
            recurrence_months=recurrence_months,
            version=version,
            effective_date=effective_date,
            created_by=created_by,
        )

        self.db.add(module)
        await self.db.commit()
        await self.db.refresh(module)

        return module

    async def get_module(self, module_id: UUID) -> Optional[TrainingModule]:
        """Get training module by ID."""
        query = select(TrainingModule).where(
            and_(
                TrainingModule.id == module_id,
                TrainingModule.tenant_id == self.tenant_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_modules(
        self,
        training_type: Optional[TrainingType] = None,
        active_only: bool = True,
    ) -> List[TrainingModule]:
        """List training modules."""
        query = select(TrainingModule).where(
            TrainingModule.tenant_id == self.tenant_id
        )

        if training_type:
            query = query.where(TrainingModule.training_type == training_type)
        if active_only:
            query = query.where(TrainingModule.is_active == True)

        query = query.order_by(TrainingModule.name)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_required_modules_for_role(
        self,
        role: str,
        has_phi_access: bool = False,
    ) -> List[TrainingModule]:
        """Get required training modules for a specific role."""
        query = select(TrainingModule).where(
            and_(
                TrainingModule.tenant_id == self.tenant_id,
                TrainingModule.is_active == True,
                or_(
                    TrainingModule.required_for_all == True,
                    TrainingModule.required_for_roles.contains([role]),
                    and_(
                        TrainingModule.required_for_phi_access == True,
                        has_phi_access == True
                    )
                )
            )
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def deactivate_module(
        self,
        module_id: UUID,
    ) -> Optional[TrainingModule]:
        """Deactivate a training module."""
        module = await self.get_module(module_id)
        if module:
            module.is_active = False
            module.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(module)
        return module

    # =========================================================================
    # Training Assignments
    # =========================================================================

    async def assign_training(
        self,
        module_id: UUID,
        user_id: UUID,
        due_date: datetime,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        user_role: Optional[str] = None,
        assigned_by: Optional[UUID] = None,
    ) -> TrainingAssignment:
        """Assign training to a user."""
        assignment = TrainingAssignment(
            tenant_id=self.tenant_id,
            module_id=module_id,
            user_id=user_id,
            user_name=user_name,
            user_email=user_email,
            user_role=user_role,
            due_date=due_date,
            assigned_by=assigned_by,
            status=TrainingStatus.ASSIGNED,
        )

        self.db.add(assignment)
        await self.db.commit()
        await self.db.refresh(assignment)

        return assignment

    async def bulk_assign_training(
        self,
        module_id: UUID,
        users: List[Dict[str, Any]],
        due_date: datetime,
        assigned_by: Optional[UUID] = None,
    ) -> List[TrainingAssignment]:
        """Bulk assign training to multiple users."""
        assignments = []
        for user in users:
            assignment = TrainingAssignment(
                tenant_id=self.tenant_id,
                module_id=module_id,
                user_id=user["user_id"],
                user_name=user.get("user_name"),
                user_email=user.get("user_email"),
                user_role=user.get("user_role"),
                due_date=due_date,
                assigned_by=assigned_by,
                status=TrainingStatus.ASSIGNED,
            )
            self.db.add(assignment)
            assignments.append(assignment)

        await self.db.commit()
        for assignment in assignments:
            await self.db.refresh(assignment)

        return assignments

    async def get_assignment(
        self,
        assignment_id: UUID,
    ) -> Optional[TrainingAssignment]:
        """Get training assignment by ID."""
        query = select(TrainingAssignment).where(
            and_(
                TrainingAssignment.id == assignment_id,
                TrainingAssignment.tenant_id == self.tenant_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def start_training(
        self,
        assignment_id: UUID,
    ) -> Optional[TrainingAssignment]:
        """Mark training as started."""
        assignment = await self.get_assignment(assignment_id)
        if assignment:
            assignment.status = TrainingStatus.IN_PROGRESS
            assignment.started_at = datetime.utcnow()
            assignment.attempts += 1
            assignment.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(assignment)

        return assignment

    async def complete_training(
        self,
        assignment_id: UUID,
        score: int,
    ) -> Optional[TrainingAssignment]:
        """Complete training with score."""
        assignment = await self.get_assignment(assignment_id)
        if not assignment:
            return None

        # Get module for passing score
        module = await self.get_module(assignment.module_id)
        if not module:
            return None

        passed = score >= module.passing_score

        assignment.status = TrainingStatus.COMPLETED
        assignment.completed_at = datetime.utcnow()
        assignment.score = score
        assignment.passed = passed
        assignment.updated_at = datetime.utcnow()

        # Generate certificate if passed
        if passed:
            assignment.certificate_id = f"CERT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(assignment.id)[:8].upper()}"
            assignment.certificate_url = f"/certificates/{assignment.certificate_id}"

        # Calculate next due date for recurring training
        if module.recurrence_months:
            assignment.next_due_date = datetime.utcnow() + timedelta(days=module.recurrence_months * 30)

        await self.db.commit()
        await self.db.refresh(assignment)

        return assignment

    async def get_user_assignments(
        self,
        user_id: UUID,
        status: Optional[TrainingStatus] = None,
    ) -> List[TrainingAssignment]:
        """Get training assignments for a user."""
        query = select(TrainingAssignment).where(
            and_(
                TrainingAssignment.tenant_id == self.tenant_id,
                TrainingAssignment.user_id == user_id
            )
        )

        if status:
            query = query.where(TrainingAssignment.status == status)

        query = query.order_by(TrainingAssignment.due_date)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_overdue_assignments(self) -> List[TrainingAssignment]:
        """Get all overdue training assignments."""
        now = datetime.utcnow()

        query = select(TrainingAssignment).where(
            and_(
                TrainingAssignment.tenant_id == self.tenant_id,
                TrainingAssignment.status.in_([
                    TrainingStatus.ASSIGNED,
                    TrainingStatus.IN_PROGRESS,
                ]),
                TrainingAssignment.due_date < now
            )
        ).order_by(TrainingAssignment.due_date)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def mark_assignments_overdue(self) -> int:
        """Mark past-due assignments as overdue."""
        now = datetime.utcnow()

        query = select(TrainingAssignment).where(
            and_(
                TrainingAssignment.tenant_id == self.tenant_id,
                TrainingAssignment.status.in_([
                    TrainingStatus.ASSIGNED,
                    TrainingStatus.IN_PROGRESS,
                ]),
                TrainingAssignment.due_date < now
            )
        )

        result = await self.db.execute(query)
        count = 0
        for assignment in result.scalars().all():
            assignment.status = TrainingStatus.OVERDUE
            assignment.updated_at = datetime.utcnow()
            count += 1

        await self.db.commit()
        return count

    async def send_reminder(
        self,
        assignment_id: UUID,
    ) -> Optional[TrainingAssignment]:
        """Record that a reminder was sent."""
        assignment = await self.get_assignment(assignment_id)
        if assignment:
            assignment.reminder_sent_count += 1
            assignment.last_reminder_sent = datetime.utcnow()
            assignment.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(assignment)

        return assignment

    # =========================================================================
    # Policy Management
    # =========================================================================

    async def create_policy(
        self,
        title: str,
        policy_number: str,
        category: str,
        content: str,
        version: str,
        effective_date: date,
        summary: Optional[str] = None,
        review_date: Optional[date] = None,
        requires_acknowledgment: bool = True,
        required_for_roles: Optional[List[str]] = None,
        required_for_all: bool = False,
        created_by: Optional[UUID] = None,
    ) -> PolicyDocument:
        """Create a policy document."""
        policy = PolicyDocument(
            tenant_id=self.tenant_id,
            title=title,
            policy_number=policy_number,
            category=category,
            content=content,
            summary=summary,
            version=version,
            effective_date=effective_date,
            review_date=review_date,
            requires_acknowledgment=requires_acknowledgment,
            required_for_roles=required_for_roles,
            required_for_all=required_for_all,
            created_by=created_by,
        )

        self.db.add(policy)
        await self.db.commit()
        await self.db.refresh(policy)

        return policy

    async def get_policy(self, policy_id: UUID) -> Optional[PolicyDocument]:
        """Get policy document by ID."""
        query = select(PolicyDocument).where(
            and_(
                PolicyDocument.id == policy_id,
                PolicyDocument.tenant_id == self.tenant_id
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_policies(
        self,
        category: Optional[str] = None,
        active_only: bool = True,
        requires_acknowledgment: Optional[bool] = None,
    ) -> List[PolicyDocument]:
        """List policy documents."""
        query = select(PolicyDocument).where(
            PolicyDocument.tenant_id == self.tenant_id
        )

        if category:
            query = query.where(PolicyDocument.category == category)
        if active_only:
            query = query.where(PolicyDocument.is_active == True)
        if requires_acknowledgment is not None:
            query = query.where(PolicyDocument.requires_acknowledgment == requires_acknowledgment)

        query = query.order_by(PolicyDocument.category, PolicyDocument.title)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def approve_policy(
        self,
        policy_id: UUID,
        approved_by: UUID,
    ) -> Optional[PolicyDocument]:
        """Approve a policy document."""
        policy = await self.get_policy(policy_id)
        if policy:
            policy.approved = True
            policy.approved_by = approved_by
            policy.approved_at = datetime.utcnow()
            policy.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(policy)

        return policy

    async def update_policy_version(
        self,
        policy_id: UUID,
        new_content: str,
        new_version: str,
        new_effective_date: date,
        new_summary: Optional[str] = None,
    ) -> PolicyDocument:
        """Create a new version of a policy."""
        old_policy = await self.get_policy(policy_id)
        if not old_policy:
            raise ValueError("Policy not found")

        # Create new version
        new_policy = PolicyDocument(
            tenant_id=self.tenant_id,
            title=old_policy.title,
            policy_number=old_policy.policy_number,
            category=old_policy.category,
            content=new_content,
            summary=new_summary or old_policy.summary,
            version=new_version,
            previous_version_id=policy_id,
            effective_date=new_effective_date,
            requires_acknowledgment=old_policy.requires_acknowledgment,
            required_for_roles=old_policy.required_for_roles,
            required_for_all=old_policy.required_for_all,
        )

        # Deactivate old version
        old_policy.is_active = False

        self.db.add(new_policy)
        await self.db.commit()
        await self.db.refresh(new_policy)

        return new_policy

    # =========================================================================
    # Policy Acknowledgments
    # =========================================================================

    async def acknowledge_policy(
        self,
        policy_id: UUID,
        user_id: UUID,
        user_name: Optional[str] = None,
        user_role: Optional[str] = None,
        signature_ip: Optional[str] = None,
        signature_user_agent: Optional[str] = None,
    ) -> PolicyAcknowledgment:
        """Record policy acknowledgment."""
        policy = await self.get_policy(policy_id)
        if not policy:
            raise ValueError("Policy not found")

        # Calculate signature hash
        signature_data = f"{user_id}:{policy_id}:{policy.version}:{datetime.utcnow().isoformat()}"
        signature_hash = hashlib.sha256(signature_data.encode()).hexdigest()

        acknowledgment = PolicyAcknowledgment(
            tenant_id=self.tenant_id,
            policy_id=policy_id,
            policy_version=policy.version,
            user_id=user_id,
            user_name=user_name,
            user_role=user_role,
            acknowledged=True,
            acknowledged_at=datetime.utcnow(),
            signature_ip=signature_ip,
            signature_user_agent=signature_user_agent,
            signature_hash=signature_hash,
        )

        self.db.add(acknowledgment)
        await self.db.commit()
        await self.db.refresh(acknowledgment)

        return acknowledgment

    async def has_acknowledged_policy(
        self,
        policy_id: UUID,
        user_id: UUID,
    ) -> Tuple[bool, Optional[PolicyAcknowledgment]]:
        """Check if user has acknowledged current policy version."""
        policy = await self.get_policy(policy_id)
        if not policy:
            return False, None

        query = select(PolicyAcknowledgment).where(
            and_(
                PolicyAcknowledgment.tenant_id == self.tenant_id,
                PolicyAcknowledgment.policy_id == policy_id,
                PolicyAcknowledgment.policy_version == policy.version,
                PolicyAcknowledgment.user_id == user_id,
                PolicyAcknowledgment.acknowledged == True
            )
        )
        result = await self.db.execute(query)
        acknowledgment = result.scalar_one_or_none()

        return (acknowledgment is not None, acknowledgment)

    async def get_pending_acknowledgments(
        self,
        user_id: UUID,
    ) -> List[PolicyDocument]:
        """Get policies pending acknowledgment for a user."""
        # Get all active policies requiring acknowledgment
        policy_query = select(PolicyDocument).where(
            and_(
                PolicyDocument.tenant_id == self.tenant_id,
                PolicyDocument.is_active == True,
                PolicyDocument.requires_acknowledgment == True
            )
        )
        policy_result = await self.db.execute(policy_query)
        policies = list(policy_result.scalars().all())

        pending = []
        for policy in policies:
            has_ack, _ = await self.has_acknowledged_policy(policy.id, user_id)
            if not has_ack:
                pending.append(policy)

        return pending

    async def get_policy_acknowledgment_status(
        self,
        policy_id: UUID,
    ) -> Dict[str, Any]:
        """Get acknowledgment status for a policy."""
        # Count total acknowledgments
        ack_query = select(func.count()).select_from(PolicyAcknowledgment).where(
            and_(
                PolicyAcknowledgment.tenant_id == self.tenant_id,
                PolicyAcknowledgment.policy_id == policy_id,
                PolicyAcknowledgment.acknowledged == True
            )
        )
        ack_result = await self.db.execute(ack_query)
        acknowledged_count = ack_result.scalar()

        return {
            "policy_id": str(policy_id),
            "acknowledged_count": acknowledged_count,
        }

    # =========================================================================
    # Training Compliance Reporting
    # =========================================================================

    async def get_training_compliance_report(self) -> Dict[str, Any]:
        """Generate training compliance report."""
        # Total assignments by status
        status_query = (
            select(TrainingAssignment.status, func.count(TrainingAssignment.id))
            .where(TrainingAssignment.tenant_id == self.tenant_id)
            .group_by(TrainingAssignment.status)
        )
        status_result = await self.db.execute(status_query)
        by_status = {row[0].value: row[1] for row in status_result.all()}

        # Overdue count
        overdue_assignments = await self.get_overdue_assignments()
        overdue_count = len(overdue_assignments)

        # Calculate completion rate
        total_query = select(func.count()).select_from(TrainingAssignment).where(
            TrainingAssignment.tenant_id == self.tenant_id
        )
        total_result = await self.db.execute(total_query)
        total_assignments = total_result.scalar()

        completed_count = by_status.get("completed", 0)
        completion_rate = (completed_count / total_assignments * 100) if total_assignments > 0 else 0

        # By module
        module_query = (
            select(
                TrainingModule.name,
                func.count(TrainingAssignment.id),
                func.sum(
                    func.cast(TrainingAssignment.status == TrainingStatus.COMPLETED, Integer)
                )
            )
            .join(TrainingModule, TrainingModule.id == TrainingAssignment.module_id)
            .where(TrainingAssignment.tenant_id == self.tenant_id)
            .group_by(TrainingModule.name)
        )
        # Note: This query might need adjustment based on actual SQL support
        # Simplified version below

        return {
            "total_assignments": total_assignments,
            "by_status": by_status,
            "overdue_count": overdue_count,
            "completion_rate": round(completion_rate, 2),
        }

    async def get_user_training_status(
        self,
        user_id: UUID,
    ) -> Dict[str, Any]:
        """Get training status summary for a user."""
        assignments = await self.get_user_assignments(user_id)

        completed = sum(1 for a in assignments if a.status == TrainingStatus.COMPLETED)
        pending = sum(1 for a in assignments if a.status in [TrainingStatus.ASSIGNED, TrainingStatus.IN_PROGRESS])
        overdue = sum(1 for a in assignments if a.status == TrainingStatus.OVERDUE)

        return {
            "user_id": str(user_id),
            "total_assignments": len(assignments),
            "completed": completed,
            "pending": pending,
            "overdue": overdue,
            "compliant": overdue == 0,
        }


# Type hint import for Integer
from sqlalchemy import Integer
Tuple = tuple

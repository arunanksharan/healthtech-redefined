"""
Patient Engagement Service for RPM

Handles patient reminders, goals, and educational content.

EPIC-019: Remote Patient Monitoring
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
import logging

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    PatientReminder, PatientGoal, EducationalContent,
    PatientContentEngagement, DeviceReading, ReadingType, OutreachChannel
)
from ..schemas import (
    PatientReminderCreate, PatientReminderUpdate, PatientReminderResponse,
    PatientGoalCreate, PatientGoalUpdate, PatientGoalResponse,
    EducationalContentCreate, EducationalContentResponse,
    ContentEngagementCreate
)

logger = logging.getLogger(__name__)


class EngagementService:
    """Service for patient engagement features."""

    # =========================================================================
    # Reminders
    # =========================================================================

    async def create_reminder(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        reminder_data: PatientReminderCreate
    ) -> PatientReminder:
        """Create a patient reminder."""
        reminder = PatientReminder(
            tenant_id=tenant_id,
            patient_id=reminder_data.patient_id,
            enrollment_id=reminder_data.enrollment_id,
            device_assignment_id=reminder_data.device_assignment_id,
            reminder_type=reminder_data.reminder_type,
            reading_type=reminder_data.reading_type,
            scheduled_time=reminder_data.scheduled_time,
            days_of_week=reminder_data.days_of_week,
            timezone=reminder_data.timezone,
            channel=reminder_data.channel,
            message_template=reminder_data.message_template,
            is_active=True
        )

        # Calculate next scheduled time
        reminder.next_scheduled_at = self._calculate_next_scheduled(
            reminder_data.scheduled_time,
            reminder_data.days_of_week,
            reminder_data.timezone
        )

        db.add(reminder)
        await db.commit()
        await db.refresh(reminder)

        logger.info(f"Created reminder {reminder.id} for patient {reminder_data.patient_id}")
        return reminder

    def _calculate_next_scheduled(
        self,
        scheduled_time: str,
        days_of_week: List[int],
        timezone: str
    ) -> datetime:
        """Calculate next scheduled reminder time."""
        now = datetime.utcnow()
        hour, minute = map(int, scheduled_time.split(':'))

        # Find next day that matches
        for days_ahead in range(8):
            next_date = now.date() + timedelta(days=days_ahead)
            weekday = next_date.weekday()

            if weekday in days_of_week:
                next_time = datetime.combine(next_date, datetime.min.time())
                next_time = next_time.replace(hour=hour, minute=minute)

                if next_time > now:
                    return next_time

        # Fallback to tomorrow
        return now + timedelta(days=1)

    async def get_reminder(
        self,
        db: AsyncSession,
        reminder_id: UUID,
        tenant_id: UUID
    ) -> Optional[PatientReminder]:
        """Get reminder by ID."""
        result = await db.execute(
            select(PatientReminder).where(
                and_(
                    PatientReminder.id == reminder_id,
                    PatientReminder.tenant_id == tenant_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_patient_reminders(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        patient_id: UUID,
        active_only: bool = True
    ) -> List[PatientReminder]:
        """Get all reminders for a patient."""
        query = select(PatientReminder).where(
            and_(
                PatientReminder.tenant_id == tenant_id,
                PatientReminder.patient_id == patient_id
            )
        )

        if active_only:
            query = query.where(PatientReminder.is_active == True)

        result = await db.execute(query.order_by(PatientReminder.scheduled_time))
        return list(result.scalars().all())

    async def update_reminder(
        self,
        db: AsyncSession,
        reminder_id: UUID,
        tenant_id: UUID,
        update_data: PatientReminderUpdate
    ) -> Optional[PatientReminder]:
        """Update a reminder."""
        reminder = await self.get_reminder(db, reminder_id, tenant_id)
        if not reminder:
            return None

        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(reminder, field, value)

        # Recalculate next scheduled if time changed
        if 'scheduled_time' in update_dict or 'days_of_week' in update_dict:
            reminder.next_scheduled_at = self._calculate_next_scheduled(
                reminder.scheduled_time,
                reminder.days_of_week,
                reminder.timezone
            )

        reminder.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(reminder)
        return reminder

    async def record_reminder_sent(
        self,
        db: AsyncSession,
        reminder_id: UUID,
        tenant_id: UUID
    ) -> Optional[PatientReminder]:
        """Record that a reminder was sent."""
        reminder = await self.get_reminder(db, reminder_id, tenant_id)
        if not reminder:
            return None

        reminder.last_sent_at = datetime.utcnow()
        reminder.reminders_sent += 1
        reminder.next_scheduled_at = self._calculate_next_scheduled(
            reminder.scheduled_time,
            reminder.days_of_week,
            reminder.timezone
        )
        reminder.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(reminder)
        return reminder

    async def record_reminder_response(
        self,
        db: AsyncSession,
        reminder_id: UUID,
        tenant_id: UUID
    ) -> Optional[PatientReminder]:
        """Record that patient responded to reminder (took reading)."""
        reminder = await self.get_reminder(db, reminder_id, tenant_id)
        if not reminder:
            return None

        reminder.readings_after_reminder += 1
        if reminder.reminders_sent > 0:
            reminder.response_rate = reminder.readings_after_reminder / reminder.reminders_sent
        reminder.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(reminder)
        return reminder

    async def get_due_reminders(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        limit: int = 100
    ) -> List[PatientReminder]:
        """Get reminders that are due to be sent."""
        now = datetime.utcnow()

        result = await db.execute(
            select(PatientReminder).where(
                and_(
                    PatientReminder.tenant_id == tenant_id,
                    PatientReminder.is_active == True,
                    PatientReminder.next_scheduled_at <= now
                )
            ).order_by(PatientReminder.next_scheduled_at).limit(limit)
        )
        return list(result.scalars().all())

    # =========================================================================
    # Goals
    # =========================================================================

    async def create_goal(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        set_by: UUID,
        set_by_type: str,
        goal_data: PatientGoalCreate
    ) -> PatientGoal:
        """Create a patient goal."""
        goal = PatientGoal(
            tenant_id=tenant_id,
            patient_id=goal_data.patient_id,
            enrollment_id=goal_data.enrollment_id,
            reading_type=goal_data.reading_type,
            goal_type=goal_data.goal_type,
            target_value=goal_data.target_value,
            target_low=goal_data.target_low,
            target_high=goal_data.target_high,
            unit=goal_data.unit,
            start_date=goal_data.start_date,
            end_date=goal_data.end_date,
            set_by=set_by,
            set_by_type=set_by_type,
            notes=goal_data.notes,
            is_active=True
        )

        db.add(goal)
        await db.commit()
        await db.refresh(goal)

        logger.info(f"Created goal {goal.id} for patient {goal_data.patient_id}")
        return goal

    async def get_goal(
        self,
        db: AsyncSession,
        goal_id: UUID,
        tenant_id: UUID
    ) -> Optional[PatientGoal]:
        """Get goal by ID."""
        result = await db.execute(
            select(PatientGoal).where(
                and_(
                    PatientGoal.id == goal_id,
                    PatientGoal.tenant_id == tenant_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_patient_goals(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        patient_id: UUID,
        reading_type: Optional[ReadingType] = None,
        active_only: bool = True
    ) -> List[PatientGoal]:
        """Get goals for a patient."""
        query = select(PatientGoal).where(
            and_(
                PatientGoal.tenant_id == tenant_id,
                PatientGoal.patient_id == patient_id
            )
        )

        if reading_type:
            query = query.where(PatientGoal.reading_type == reading_type)
        if active_only:
            query = query.where(PatientGoal.is_active == True)

        result = await db.execute(query.order_by(PatientGoal.created_at.desc()))
        return list(result.scalars().all())

    async def update_goal(
        self,
        db: AsyncSession,
        goal_id: UUID,
        tenant_id: UUID,
        update_data: PatientGoalUpdate
    ) -> Optional[PatientGoal]:
        """Update a goal."""
        goal = await self.get_goal(db, goal_id, tenant_id)
        if not goal:
            return None

        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(goal, field, value)

        goal.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(goal)
        return goal

    async def update_goal_progress(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        patient_id: UUID,
        reading_type: ReadingType,
        current_value: float
    ) -> List[PatientGoal]:
        """Update progress for matching goals."""
        goals = await self.get_patient_goals(
            db, tenant_id, patient_id, reading_type, active_only=True
        )

        updated_goals = []
        for goal in goals:
            goal.current_value = current_value

            # Calculate progress
            if goal.goal_type == "target" and goal.target_value:
                # For targets, progress is how close we are
                if goal.target_value > 0:
                    goal.progress_percent = min(
                        (current_value / goal.target_value) * 100, 100
                    )
                    goal.is_achieved = current_value >= goal.target_value

            elif goal.goal_type == "range":
                # For ranges, check if in range
                in_range = True
                if goal.target_low and current_value < goal.target_low:
                    in_range = False
                if goal.target_high and current_value > goal.target_high:
                    in_range = False
                goal.is_achieved = in_range
                goal.progress_percent = 100 if in_range else 0

            if goal.is_achieved and not goal.achieved_at:
                goal.achieved_at = datetime.utcnow()

            goal.updated_at = datetime.utcnow()
            updated_goals.append(goal)

        await db.commit()
        return updated_goals

    # =========================================================================
    # Educational Content
    # =========================================================================

    async def create_content(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        created_by: UUID,
        content_data: EducationalContentCreate
    ) -> EducationalContent:
        """Create educational content."""
        content = EducationalContent(
            tenant_id=tenant_id,
            title=content_data.title,
            description=content_data.description,
            content_type=content_data.content_type,
            content_url=content_data.content_url,
            content_body=content_data.content_body,
            condition=content_data.condition,
            tags=content_data.tags or [],
            reading_types=content_data.reading_types or [],
            duration_minutes=content_data.duration_minutes,
            difficulty_level=content_data.difficulty_level,
            language=content_data.language,
            is_featured=content_data.is_featured,
            is_active=True,
            created_by=created_by
        )

        db.add(content)
        await db.commit()
        await db.refresh(content)
        return content

    async def get_content(
        self,
        db: AsyncSession,
        content_id: UUID,
        tenant_id: UUID
    ) -> Optional[EducationalContent]:
        """Get content by ID."""
        result = await db.execute(
            select(EducationalContent).where(
                and_(
                    EducationalContent.id == content_id,
                    EducationalContent.tenant_id == tenant_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_content(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        condition: Optional[str] = None,
        content_type: Optional[str] = None,
        featured_only: bool = False,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[EducationalContent], int]:
        """List educational content."""
        query = select(EducationalContent).where(
            and_(
                EducationalContent.tenant_id == tenant_id,
                EducationalContent.is_active == True
            )
        )

        if condition:
            query = query.where(EducationalContent.condition == condition)
        if content_type:
            query = query.where(EducationalContent.content_type == content_type)
        if featured_only:
            query = query.where(EducationalContent.is_featured == True)

        count_result = await db.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()

        query = query.offset(skip).limit(limit).order_by(
            EducationalContent.is_featured.desc(),
            EducationalContent.view_count.desc()
        )
        result = await db.execute(query)
        content = result.scalars().all()

        return list(content), total

    async def get_recommended_content(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        patient_id: UUID,
        condition: Optional[str] = None,
        limit: int = 5
    ) -> List[EducationalContent]:
        """Get recommended content for a patient."""
        # Get content patient hasn't viewed
        viewed_result = await db.execute(
            select(PatientContentEngagement.content_id).where(
                PatientContentEngagement.patient_id == patient_id
            )
        )
        viewed_ids = [row[0] for row in viewed_result.all()]

        query = select(EducationalContent).where(
            and_(
                EducationalContent.tenant_id == tenant_id,
                EducationalContent.is_active == True,
                ~EducationalContent.id.in_(viewed_ids) if viewed_ids else True
            )
        )

        if condition:
            query = query.where(
                or_(
                    EducationalContent.condition == condition,
                    EducationalContent.condition.is_(None)
                )
            )

        query = query.order_by(
            EducationalContent.is_featured.desc(),
            EducationalContent.average_rating.desc().nullslast()
        ).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def record_engagement(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        patient_id: UUID,
        engagement_data: ContentEngagementCreate
    ) -> PatientContentEngagement:
        """Record patient engagement with content."""
        # Check for existing engagement
        result = await db.execute(
            select(PatientContentEngagement).where(
                and_(
                    PatientContentEngagement.patient_id == patient_id,
                    PatientContentEngagement.content_id == engagement_data.content_id
                )
            )
        )
        engagement = result.scalar_one_or_none()

        if engagement:
            # Update existing
            engagement.time_spent_seconds += engagement_data.time_spent_seconds
            engagement.progress_percent = max(
                engagement.progress_percent,
                engagement_data.progress_percent
            )
            if engagement_data.completed:
                engagement.completed_at = datetime.utcnow()
            if engagement_data.rating:
                engagement.rating = engagement_data.rating
            if engagement_data.feedback:
                engagement.feedback = engagement_data.feedback
            if engagement_data.quiz_score is not None:
                engagement.quiz_score = engagement_data.quiz_score
                engagement.quiz_attempts += 1
        else:
            # Create new
            engagement = PatientContentEngagement(
                tenant_id=tenant_id,
                patient_id=patient_id,
                content_id=engagement_data.content_id,
                time_spent_seconds=engagement_data.time_spent_seconds,
                progress_percent=engagement_data.progress_percent,
                completed_at=datetime.utcnow() if engagement_data.completed else None,
                rating=engagement_data.rating,
                feedback=engagement_data.feedback,
                quiz_score=engagement_data.quiz_score,
                quiz_attempts=1 if engagement_data.quiz_score is not None else 0
            )
            db.add(engagement)

            # Update content view count
            content = await self.get_content(db, engagement_data.content_id, tenant_id)
            if content:
                content.view_count += 1
                if engagement_data.completed:
                    content.completion_count += 1

        await db.commit()
        await db.refresh(engagement)
        return engagement

    async def get_patient_engagement(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        patient_id: UUID
    ) -> Dict[str, Any]:
        """Get patient's overall engagement metrics."""
        # Content viewed
        viewed_result = await db.execute(
            select(func.count()).select_from(PatientContentEngagement).where(
                PatientContentEngagement.patient_id == patient_id
            )
        )
        content_viewed = viewed_result.scalar()

        # Content completed
        completed_result = await db.execute(
            select(func.count()).select_from(PatientContentEngagement).where(
                and_(
                    PatientContentEngagement.patient_id == patient_id,
                    PatientContentEngagement.completed_at.isnot(None)
                )
            )
        )
        content_completed = completed_result.scalar()

        # Total time spent
        time_result = await db.execute(
            select(func.sum(PatientContentEngagement.time_spent_seconds)).where(
                PatientContentEngagement.patient_id == patient_id
            )
        )
        total_time = time_result.scalar() or 0

        # Goal achievement
        goals_result = await db.execute(
            select(
                func.count().label("total"),
                func.count().filter(PatientGoal.is_achieved == True).label("achieved")
            ).where(
                and_(
                    PatientGoal.patient_id == patient_id,
                    PatientGoal.is_active == True
                )
            )
        )
        goals_row = goals_result.one()

        return {
            "content_viewed": content_viewed,
            "content_completed": content_completed,
            "total_time_minutes": total_time // 60,
            "goals_total": goals_row.total,
            "goals_achieved": goals_row.achieved,
            "goal_achievement_rate": (
                goals_row.achieved / goals_row.total * 100
                if goals_row.total > 0 else 0
            )
        }

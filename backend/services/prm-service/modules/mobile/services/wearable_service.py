"""
Wearable Device Service
EPIC-016: Wearable integration and health metrics
"""
from datetime import datetime, timezone, timedelta, date
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func, desc

from modules.mobile.models import (
    WearableDevice, HealthMetric, HealthMetricGoal,
    WearableType, HealthMetricType, DeviceStatus
)
from modules.mobile.schemas import (
    WearableConnect, WearableUpdate, WearableResponse, WearableListResponse,
    HealthMetricRecord, HealthMetricBulkRecord, HealthMetricResponse,
    HealthMetricListResponse, HealthMetricSummary, HealthMetricGoalCreate,
    HealthMetricGoalResponse
)


class WearableService:
    """
    Handles wearable device integration:
    - Apple Watch, Wear OS, Fitbit, Garmin, Samsung Galaxy Watch
    - HealthKit and Google Fit integration
    - Health metric recording and analysis
    - Goal tracking and progress
    """

    # Metric units by type
    METRIC_UNITS = {
        HealthMetricType.HEART_RATE: "bpm",
        HealthMetricType.HEART_RATE_VARIABILITY: "ms",
        HealthMetricType.RESTING_HEART_RATE: "bpm",
        HealthMetricType.BLOOD_OXYGEN: "%",
        HealthMetricType.RESPIRATORY_RATE: "breaths/min",
        HealthMetricType.BLOOD_PRESSURE_SYSTOLIC: "mmHg",
        HealthMetricType.BLOOD_PRESSURE_DIASTOLIC: "mmHg",
        HealthMetricType.BLOOD_GLUCOSE: "mg/dL",
        HealthMetricType.BODY_TEMPERATURE: "°F",
        HealthMetricType.STEPS: "steps",
        HealthMetricType.DISTANCE: "meters",
        HealthMetricType.CALORIES_BURNED: "kcal",
        HealthMetricType.ACTIVE_MINUTES: "minutes",
        HealthMetricType.FLOORS_CLIMBED: "floors",
        HealthMetricType.SLEEP_DURATION: "hours",
        HealthMetricType.SLEEP_QUALITY: "score",
        HealthMetricType.DEEP_SLEEP: "hours",
        HealthMetricType.REM_SLEEP: "hours",
        HealthMetricType.LIGHT_SLEEP: "hours",
        HealthMetricType.WEIGHT: "kg",
        HealthMetricType.BODY_FAT: "%",
        HealthMetricType.BMI: "kg/m²",
        HealthMetricType.MUSCLE_MASS: "kg",
        HealthMetricType.WATER_INTAKE: "ml",
        HealthMetricType.CAFFEINE_INTAKE: "mg",
        HealthMetricType.STRESS_LEVEL: "score",
        HealthMetricType.MINDFULNESS_MINUTES: "minutes",
        HealthMetricType.VO2_MAX: "mL/kg/min",
        HealthMetricType.ECG: "raw",
        HealthMetricType.MENSTRUAL_CYCLE: "day"
    }

    async def connect_wearable(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        data: WearableConnect
    ) -> WearableResponse:
        """Connect a new wearable device"""

        # Check if device already connected
        result = await db.execute(
            select(WearableDevice).where(
                and_(
                    WearableDevice.tenant_id == tenant_id,
                    WearableDevice.user_id == user_id,
                    WearableDevice.device_identifier == data.device_identifier
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Reactivate if disconnected
            existing.status = DeviceStatus.ACTIVE
            existing.access_token = data.access_token
            existing.refresh_token = data.refresh_token
            existing.token_expires_at = data.token_expires_at
            existing.last_sync_at = datetime.now(timezone.utc)
            existing.updated_at = datetime.now(timezone.utc)
            wearable = existing
        else:
            # Create new wearable connection
            wearable = WearableDevice(
                id=uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
                device_identifier=data.device_identifier,
                device_name=data.device_name,
                wearable_type=WearableType(data.wearable_type.value),
                manufacturer=data.manufacturer,
                model=data.model,
                firmware_version=data.firmware_version,
                access_token=data.access_token,
                refresh_token=data.refresh_token,
                token_expires_at=data.token_expires_at,
                status=DeviceStatus.ACTIVE,
                capabilities=data.capabilities or [],
                last_sync_at=datetime.now(timezone.utc)
            )
            db.add(wearable)

        await db.commit()
        await db.refresh(wearable)

        return self._wearable_to_response(wearable)

    async def update_wearable(
        self,
        db: AsyncSession,
        wearable_id: UUID,
        user_id: UUID,
        data: WearableUpdate
    ) -> WearableResponse:
        """Update wearable device information"""

        result = await db.execute(
            select(WearableDevice).where(
                and_(
                    WearableDevice.id == wearable_id,
                    WearableDevice.user_id == user_id
                )
            )
        )
        wearable = result.scalar_one_or_none()

        if not wearable:
            raise ValueError("Wearable device not found")

        if data.device_name is not None:
            wearable.device_name = data.device_name
        if data.firmware_version is not None:
            wearable.firmware_version = data.firmware_version
        if data.access_token is not None:
            wearable.access_token = data.access_token
        if data.refresh_token is not None:
            wearable.refresh_token = data.refresh_token
        if data.token_expires_at is not None:
            wearable.token_expires_at = data.token_expires_at
        if data.sync_enabled is not None:
            wearable.sync_enabled = data.sync_enabled
        if data.sync_frequency_minutes is not None:
            wearable.sync_frequency_minutes = data.sync_frequency_minutes
        if data.enabled_metrics is not None:
            wearable.enabled_metrics = data.enabled_metrics

        wearable.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(wearable)

        return self._wearable_to_response(wearable)

    async def disconnect_wearable(
        self,
        db: AsyncSession,
        wearable_id: UUID,
        user_id: UUID
    ) -> None:
        """Disconnect a wearable device"""

        result = await db.execute(
            select(WearableDevice).where(
                and_(
                    WearableDevice.id == wearable_id,
                    WearableDevice.user_id == user_id
                )
            )
        )
        wearable = result.scalar_one_or_none()

        if not wearable:
            raise ValueError("Wearable device not found")

        wearable.status = DeviceStatus.INACTIVE
        wearable.access_token = None
        wearable.refresh_token = None
        wearable.updated_at = datetime.now(timezone.utc)

        await db.commit()

    async def get_wearable(
        self,
        db: AsyncSession,
        wearable_id: UUID,
        user_id: UUID
    ) -> WearableResponse:
        """Get wearable device by ID"""

        result = await db.execute(
            select(WearableDevice).where(
                and_(
                    WearableDevice.id == wearable_id,
                    WearableDevice.user_id == user_id
                )
            )
        )
        wearable = result.scalar_one_or_none()

        if not wearable:
            raise ValueError("Wearable device not found")

        return self._wearable_to_response(wearable)

    async def list_user_wearables(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        active_only: bool = True
    ) -> WearableListResponse:
        """List all wearable devices for a user"""

        query = select(WearableDevice).where(
            and_(
                WearableDevice.user_id == user_id,
                WearableDevice.tenant_id == tenant_id
            )
        )

        if active_only:
            query = query.where(WearableDevice.status == DeviceStatus.ACTIVE)

        result = await db.execute(query)
        wearables = result.scalars().all()

        return WearableListResponse(
            wearables=[self._wearable_to_response(w) for w in wearables],
            total=len(wearables)
        )

    async def record_health_metric(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        data: HealthMetricRecord
    ) -> HealthMetricResponse:
        """Record a single health metric"""

        metric = HealthMetric(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            wearable_id=data.wearable_id,
            metric_type=HealthMetricType(data.metric_type.value),
            value=Decimal(str(data.value)),
            unit=data.unit or self.METRIC_UNITS.get(
                HealthMetricType(data.metric_type.value), ""
            ),
            recorded_at=data.recorded_at or datetime.now(timezone.utc),
            source=data.source or "manual",
            metadata=data.metadata or {}
        )
        db.add(metric)

        # Check goals and trigger alerts if needed
        await self._check_metric_goals(db, user_id, tenant_id, metric)

        await db.commit()
        await db.refresh(metric)

        return self._metric_to_response(metric)

    async def record_bulk_metrics(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        data: HealthMetricBulkRecord
    ) -> List[HealthMetricResponse]:
        """Record multiple health metrics at once"""

        metrics = []
        for record in data.metrics:
            metric = HealthMetric(
                id=uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
                wearable_id=data.wearable_id or record.wearable_id,
                metric_type=HealthMetricType(record.metric_type.value),
                value=Decimal(str(record.value)),
                unit=record.unit or self.METRIC_UNITS.get(
                    HealthMetricType(record.metric_type.value), ""
                ),
                recorded_at=record.recorded_at or datetime.now(timezone.utc),
                source=data.source or record.source or "wearable",
                metadata=record.metadata or {}
            )
            db.add(metric)
            metrics.append(metric)

        await db.commit()

        # Refresh all metrics
        for metric in metrics:
            await db.refresh(metric)

        return [self._metric_to_response(m) for m in metrics]

    async def get_health_metrics(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        metric_type: Optional[HealthMetricType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        wearable_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> HealthMetricListResponse:
        """Get health metrics for a user"""

        query = select(HealthMetric).where(
            and_(
                HealthMetric.user_id == user_id,
                HealthMetric.tenant_id == tenant_id
            )
        )

        if metric_type:
            query = query.where(HealthMetric.metric_type == metric_type)

        if start_date:
            query = query.where(HealthMetric.recorded_at >= start_date)

        if end_date:
            query = query.where(HealthMetric.recorded_at <= end_date)

        if wearable_id:
            query = query.where(HealthMetric.wearable_id == wearable_id)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = query.order_by(desc(HealthMetric.recorded_at))
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        metrics = result.scalars().all()

        return HealthMetricListResponse(
            metrics=[self._metric_to_response(m) for m in metrics],
            total=total
        )

    async def get_metric_summary(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        metric_type: HealthMetricType,
        period: str = "day",  # day, week, month
        date_ref: date = None
    ) -> HealthMetricSummary:
        """Get summary statistics for a metric type"""

        if date_ref is None:
            date_ref = date.today()

        # Calculate period boundaries
        if period == "day":
            start = datetime.combine(date_ref, datetime.min.time(), timezone.utc)
            end = start + timedelta(days=1)
        elif period == "week":
            start_of_week = date_ref - timedelta(days=date_ref.weekday())
            start = datetime.combine(start_of_week, datetime.min.time(), timezone.utc)
            end = start + timedelta(days=7)
        elif period == "month":
            start = datetime.combine(
                date_ref.replace(day=1), datetime.min.time(), timezone.utc
            )
            if date_ref.month == 12:
                end = datetime.combine(
                    date_ref.replace(year=date_ref.year + 1, month=1, day=1),
                    datetime.min.time(), timezone.utc
                )
            else:
                end = datetime.combine(
                    date_ref.replace(month=date_ref.month + 1, day=1),
                    datetime.min.time(), timezone.utc
                )
        else:
            raise ValueError(f"Invalid period: {period}")

        # Query aggregates
        result = await db.execute(
            select(
                func.avg(HealthMetric.value),
                func.min(HealthMetric.value),
                func.max(HealthMetric.value),
                func.count(HealthMetric.id)
            ).where(
                and_(
                    HealthMetric.user_id == user_id,
                    HealthMetric.tenant_id == tenant_id,
                    HealthMetric.metric_type == metric_type,
                    HealthMetric.recorded_at >= start,
                    HealthMetric.recorded_at < end
                )
            )
        )
        row = result.one()
        avg_val, min_val, max_val, count = row

        # Get goal for comparison
        goal = await self._get_active_goal(db, user_id, tenant_id, metric_type)
        goal_progress = None
        if goal and avg_val:
            if goal.goal_type == "minimum":
                goal_progress = float(avg_val) / float(goal.target_value) * 100
            elif goal.goal_type == "maximum":
                goal_progress = (1 - float(avg_val) / float(goal.target_value)) * 100
            else:
                goal_progress = float(avg_val) / float(goal.target_value) * 100

        return HealthMetricSummary(
            metric_type=metric_type.value,
            period=period,
            start_date=start,
            end_date=end,
            average=float(avg_val) if avg_val else None,
            minimum=float(min_val) if min_val else None,
            maximum=float(max_val) if max_val else None,
            count=count,
            unit=self.METRIC_UNITS.get(metric_type, ""),
            goal_target=float(goal.target_value) if goal else None,
            goal_progress=goal_progress
        )

    async def get_daily_trends(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        metric_type: HealthMetricType,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get daily trend data for a metric"""

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Get daily averages
        result = await db.execute(
            select(
                func.date_trunc('day', HealthMetric.recorded_at).label('day'),
                func.avg(HealthMetric.value).label('avg'),
                func.min(HealthMetric.value).label('min'),
                func.max(HealthMetric.value).label('max'),
                func.count(HealthMetric.id).label('count')
            ).where(
                and_(
                    HealthMetric.user_id == user_id,
                    HealthMetric.tenant_id == tenant_id,
                    HealthMetric.metric_type == metric_type,
                    HealthMetric.recorded_at >= start_date,
                    HealthMetric.recorded_at <= end_date
                )
            ).group_by(
                func.date_trunc('day', HealthMetric.recorded_at)
            ).order_by(
                func.date_trunc('day', HealthMetric.recorded_at)
            )
        )
        rows = result.all()

        trends = []
        for row in rows:
            trends.append({
                "date": row.day.isoformat() if row.day else None,
                "average": float(row.avg) if row.avg else None,
                "minimum": float(row.min) if row.min else None,
                "maximum": float(row.max) if row.max else None,
                "count": row.count
            })

        return trends

    async def create_health_goal(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        data: HealthMetricGoalCreate
    ) -> HealthMetricGoalResponse:
        """Create a health metric goal"""

        # Deactivate existing goal for same metric type
        await db.execute(
            update(HealthMetricGoal).where(
                and_(
                    HealthMetricGoal.user_id == user_id,
                    HealthMetricGoal.tenant_id == tenant_id,
                    HealthMetricGoal.metric_type == HealthMetricType(data.metric_type.value),
                    HealthMetricGoal.is_active == True
                )
            ).values(is_active=False)
        )

        goal = HealthMetricGoal(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            metric_type=HealthMetricType(data.metric_type.value),
            target_value=Decimal(str(data.target_value)),
            goal_type=data.goal_type,
            frequency=data.frequency,
            start_date=data.start_date or date.today(),
            end_date=data.end_date,
            reminder_enabled=data.reminder_enabled,
            reminder_time=data.reminder_time,
            is_active=True
        )
        db.add(goal)

        await db.commit()
        await db.refresh(goal)

        return self._goal_to_response(goal)

    async def update_health_goal(
        self,
        db: AsyncSession,
        goal_id: UUID,
        user_id: UUID,
        data: Dict[str, Any]
    ) -> HealthMetricGoalResponse:
        """Update a health goal"""

        result = await db.execute(
            select(HealthMetricGoal).where(
                and_(
                    HealthMetricGoal.id == goal_id,
                    HealthMetricGoal.user_id == user_id
                )
            )
        )
        goal = result.scalar_one_or_none()

        if not goal:
            raise ValueError("Goal not found")

        for key, value in data.items():
            if hasattr(goal, key) and value is not None:
                if key == "target_value":
                    value = Decimal(str(value))
                setattr(goal, key, value)

        goal.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(goal)

        return self._goal_to_response(goal)

    async def delete_health_goal(
        self,
        db: AsyncSession,
        goal_id: UUID,
        user_id: UUID
    ) -> None:
        """Delete a health goal"""

        await db.execute(
            delete(HealthMetricGoal).where(
                and_(
                    HealthMetricGoal.id == goal_id,
                    HealthMetricGoal.user_id == user_id
                )
            )
        )
        await db.commit()

    async def get_user_goals(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        active_only: bool = True
    ) -> List[HealthMetricGoalResponse]:
        """Get all health goals for a user"""

        query = select(HealthMetricGoal).where(
            and_(
                HealthMetricGoal.user_id == user_id,
                HealthMetricGoal.tenant_id == tenant_id
            )
        )

        if active_only:
            query = query.where(HealthMetricGoal.is_active == True)

        result = await db.execute(query)
        goals = result.scalars().all()

        return [self._goal_to_response(g) for g in goals]

    async def get_goal_progress(
        self,
        db: AsyncSession,
        goal_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Get progress for a specific goal"""

        result = await db.execute(
            select(HealthMetricGoal).where(
                and_(
                    HealthMetricGoal.id == goal_id,
                    HealthMetricGoal.user_id == user_id
                )
            )
        )
        goal = result.scalar_one_or_none()

        if not goal:
            raise ValueError("Goal not found")

        # Calculate progress based on frequency
        today = date.today()
        if goal.frequency == "daily":
            start = datetime.combine(today, datetime.min.time(), timezone.utc)
            end = start + timedelta(days=1)
        elif goal.frequency == "weekly":
            start_of_week = today - timedelta(days=today.weekday())
            start = datetime.combine(start_of_week, datetime.min.time(), timezone.utc)
            end = start + timedelta(days=7)
        else:  # monthly
            start = datetime.combine(
                today.replace(day=1), datetime.min.time(), timezone.utc
            )
            if today.month == 12:
                end = datetime.combine(
                    today.replace(year=today.year + 1, month=1, day=1),
                    datetime.min.time(), timezone.utc
                )
            else:
                end = datetime.combine(
                    today.replace(month=today.month + 1, day=1),
                    datetime.min.time(), timezone.utc
                )

        # Get aggregate for period
        agg_result = await db.execute(
            select(
                func.sum(HealthMetric.value) if goal.goal_type == "cumulative"
                else func.avg(HealthMetric.value)
            ).where(
                and_(
                    HealthMetric.user_id == user_id,
                    HealthMetric.metric_type == goal.metric_type,
                    HealthMetric.recorded_at >= start,
                    HealthMetric.recorded_at < end
                )
            )
        )
        current_value = agg_result.scalar()

        progress_pct = 0
        if current_value and goal.target_value:
            progress_pct = float(current_value) / float(goal.target_value) * 100

        return {
            "goal_id": str(goal.id),
            "metric_type": goal.metric_type.value,
            "target_value": float(goal.target_value),
            "current_value": float(current_value) if current_value else 0,
            "progress_percentage": min(progress_pct, 100),
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
            "is_achieved": progress_pct >= 100,
            "unit": self.METRIC_UNITS.get(goal.metric_type, "")
        }

    async def sync_wearable_data(
        self,
        db: AsyncSession,
        wearable_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Sync data from wearable device.
        In production, this would call the wearable's API.
        """

        result = await db.execute(
            select(WearableDevice).where(
                and_(
                    WearableDevice.id == wearable_id,
                    WearableDevice.user_id == user_id,
                    WearableDevice.status == DeviceStatus.ACTIVE
                )
            )
        )
        wearable = result.scalar_one_or_none()

        if not wearable:
            raise ValueError("Wearable device not found or inactive")

        # In production, this would:
        # 1. Check if token needs refresh
        # 2. Call wearable API to fetch new data
        # 3. Parse and store health metrics
        # 4. Update last_sync_at

        wearable.last_sync_at = datetime.now(timezone.utc)
        await db.commit()

        return {
            "wearable_id": str(wearable_id),
            "status": "synced",
            "last_sync_at": wearable.last_sync_at.isoformat(),
            "metrics_synced": 0  # Would be actual count
        }

    # Private helper methods

    async def _check_metric_goals(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        metric: HealthMetric
    ) -> None:
        """Check if metric value triggers any goal alerts"""

        goal = await self._get_active_goal(
            db, user_id, tenant_id, metric.metric_type
        )

        if not goal:
            return

        # Check if goal achieved (simplified logic)
        # In production, would be more sophisticated
        if goal.goal_type == "minimum" and metric.value >= goal.target_value:
            # Goal achieved notification could be triggered here
            pass
        elif goal.goal_type == "maximum" and metric.value <= goal.target_value:
            pass

    async def _get_active_goal(
        self,
        db: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        metric_type: HealthMetricType
    ) -> Optional[HealthMetricGoal]:
        """Get active goal for a metric type"""

        result = await db.execute(
            select(HealthMetricGoal).where(
                and_(
                    HealthMetricGoal.user_id == user_id,
                    HealthMetricGoal.tenant_id == tenant_id,
                    HealthMetricGoal.metric_type == metric_type,
                    HealthMetricGoal.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()

    def _wearable_to_response(self, wearable: WearableDevice) -> WearableResponse:
        """Convert wearable model to response"""
        return WearableResponse(
            id=wearable.id,
            device_identifier=wearable.device_identifier,
            device_name=wearable.device_name,
            wearable_type=wearable.wearable_type.value,
            manufacturer=wearable.manufacturer,
            model=wearable.model,
            firmware_version=wearable.firmware_version,
            status=wearable.status.value,
            capabilities=wearable.capabilities,
            sync_enabled=wearable.sync_enabled,
            sync_frequency_minutes=wearable.sync_frequency_minutes,
            enabled_metrics=wearable.enabled_metrics,
            last_sync_at=wearable.last_sync_at,
            battery_level=wearable.battery_level,
            connected_at=wearable.created_at
        )

    def _metric_to_response(self, metric: HealthMetric) -> HealthMetricResponse:
        """Convert health metric model to response"""
        return HealthMetricResponse(
            id=metric.id,
            metric_type=metric.metric_type.value,
            value=float(metric.value),
            unit=metric.unit,
            recorded_at=metric.recorded_at,
            source=metric.source,
            wearable_id=metric.wearable_id,
            metadata=metric.metadata
        )

    def _goal_to_response(self, goal: HealthMetricGoal) -> HealthMetricGoalResponse:
        """Convert goal model to response"""
        return HealthMetricGoalResponse(
            id=goal.id,
            metric_type=goal.metric_type.value,
            target_value=float(goal.target_value),
            goal_type=goal.goal_type,
            frequency=goal.frequency,
            start_date=goal.start_date,
            end_date=goal.end_date,
            reminder_enabled=goal.reminder_enabled,
            reminder_time=goal.reminder_time.isoformat() if goal.reminder_time else None,
            is_active=goal.is_active,
            created_at=goal.created_at
        )

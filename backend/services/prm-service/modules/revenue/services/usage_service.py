"""
Usage Metering Service
EPIC-017: Usage tracking and aggregation
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, desc, text

from modules.revenue.models import (
    UsageRecord, UsageAggregate, Subscription, Plan, Entitlement,
    UsageMetricType, SubscriptionStatus
)
from modules.revenue.schemas import (
    UsageRecordCreate, UsageRecordBatch, UsageRecordResponse,
    UsageSummary, UsageDashboard, UsageAlert
)


class UsageMeteringService:
    """
    Handles usage tracking:
    - Record usage events
    - Aggregate usage by period
    - Calculate overage
    - Generate usage alerts
    """

    # Metric units
    METRIC_UNITS = {
        UsageMetricType.AI_INTERACTION: "interactions",
        UsageMetricType.AI_TOKENS: "tokens",
        UsageMetricType.TRIAGE_AGENT: "calls",
        UsageMetricType.SCRIBE_AGENT: "calls",
        UsageMetricType.CODING_AGENT: "calls",
        UsageMetricType.API_CALL: "calls",
        UsageMetricType.FHIR_API: "calls",
        UsageMetricType.TELEHEALTH_MINUTES: "minutes",
        UsageMetricType.SMS_MESSAGE: "messages",
        UsageMetricType.VOICE_MINUTE: "minutes",
        UsageMetricType.WHATSAPP_MESSAGE: "messages",
        UsageMetricType.EMAIL_SEND: "emails",
        UsageMetricType.STORAGE_GB: "GB",
        UsageMetricType.DOCUMENT_PROCESSED: "documents",
        UsageMetricType.ACTIVE_PATIENT: "patients",
        UsageMetricType.ACTIVE_PROVIDER: "providers"
    }

    async def record_usage(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        data: UsageRecordCreate,
        subscription_id: UUID = None
    ) -> UsageRecordResponse:
        """Record a single usage event"""

        # Get subscription if not provided
        if not subscription_id:
            subscription_id = await self._get_active_subscription_id(db, tenant_id)

        record = UsageRecord(
            id=uuid4(),
            tenant_id=tenant_id,
            subscription_id=subscription_id,
            metric_type=UsageMetricType(data.metric_type.value),
            quantity=Decimal(str(data.quantity)),
            unit=self.METRIC_UNITS.get(UsageMetricType(data.metric_type.value)),
            user_id=data.user_id,
            resource_id=data.resource_id,
            recorded_at=data.recorded_at or datetime.now(timezone.utc),
            is_billable=True,
            metadata=data.metadata or {}
        )
        db.add(record)

        # Update entitlement usage counter
        await self._update_entitlement_usage(
            db, tenant_id, subscription_id, data.metric_type.value, data.quantity
        )

        await db.commit()
        await db.refresh(record)

        return self._record_to_response(record)

    async def record_usage_batch(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        data: UsageRecordBatch,
        subscription_id: UUID = None
    ) -> List[UsageRecordResponse]:
        """Record multiple usage events"""

        if not subscription_id:
            subscription_id = await self._get_active_subscription_id(db, tenant_id)

        records = []
        for record_data in data.records:
            record = UsageRecord(
                id=uuid4(),
                tenant_id=tenant_id,
                subscription_id=subscription_id,
                metric_type=UsageMetricType(record_data.metric_type.value),
                quantity=Decimal(str(record_data.quantity)),
                unit=self.METRIC_UNITS.get(UsageMetricType(record_data.metric_type.value)),
                user_id=record_data.user_id,
                resource_id=record_data.resource_id,
                recorded_at=record_data.recorded_at or datetime.now(timezone.utc),
                is_billable=True,
                metadata=record_data.metadata or {}
            )
            db.add(record)
            records.append(record)

        await db.commit()

        return [self._record_to_response(r) for r in records]

    async def get_usage_summary(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        metric_type: UsageMetricType,
        period_start: datetime,
        period_end: datetime
    ) -> UsageSummary:
        """Get usage summary for a metric in a period"""

        # Get aggregate
        result = await db.execute(
            select(
                func.sum(UsageRecord.quantity),
                func.count(UsageRecord.id)
            ).where(
                and_(
                    UsageRecord.tenant_id == tenant_id,
                    UsageRecord.metric_type == metric_type,
                    UsageRecord.recorded_at >= period_start,
                    UsageRecord.recorded_at < period_end,
                    UsageRecord.is_billable == True
                )
            )
        )
        row = result.one()
        total_quantity = float(row[0]) if row[0] else 0

        # Get included quantity from subscription
        included = await self._get_included_quantity(db, tenant_id, metric_type)
        overage = max(0, total_quantity - included)

        # Get overage rate
        overage_rate = await self._get_overage_rate(db, tenant_id, metric_type)
        overage_amount = overage * overage_rate

        return UsageSummary(
            metric_type=metric_type.value,
            period_start=period_start,
            period_end=period_end,
            total_quantity=total_quantity,
            included_quantity=included,
            overage_quantity=overage,
            overage_amount=overage_amount,
            unit=self.METRIC_UNITS.get(metric_type)
        )

    async def get_usage_dashboard(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        period_start: datetime = None,
        period_end: datetime = None
    ) -> UsageDashboard:
        """Get full usage dashboard for tenant"""

        # Default to current billing period
        if not period_start or not period_end:
            period_start, period_end = await self._get_current_billing_period(db, tenant_id)

        summaries = []
        total_overage = 0
        usage_percentages = {}

        for metric_type in UsageMetricType:
            summary = await self.get_usage_summary(
                db, tenant_id, metric_type, period_start, period_end
            )
            summaries.append(summary)
            total_overage += summary.overage_amount

            if summary.included_quantity > 0:
                usage_percentages[metric_type.value] = (
                    summary.total_quantity / summary.included_quantity * 100
                )

        return UsageDashboard(
            period_start=period_start,
            period_end=period_end,
            summaries=summaries,
            total_overage_amount=total_overage,
            usage_percentage=usage_percentages
        )

    async def check_usage_alerts(
        self,
        db: AsyncSession,
        tenant_id: UUID
    ) -> List[UsageAlert]:
        """Check for usage threshold alerts"""

        alerts = []
        period_start, period_end = await self._get_current_billing_period(db, tenant_id)

        for metric_type in UsageMetricType:
            summary = await self.get_usage_summary(
                db, tenant_id, metric_type, period_start, period_end
            )

            if summary.included_quantity == 0:
                continue

            usage_percent = (summary.total_quantity / summary.included_quantity) * 100

            # Check thresholds
            for threshold in [80, 90, 100]:
                if usage_percent >= threshold:
                    alerts.append(UsageAlert(
                        metric_type=metric_type.value,
                        threshold_percent=threshold,
                        current_usage=summary.total_quantity,
                        included_limit=summary.included_quantity,
                        usage_percent=usage_percent,
                        alert_message=self._get_alert_message(metric_type, threshold, usage_percent)
                    ))
                    break  # Only return highest threshold crossed

        return alerts

    async def aggregate_usage(
        self,
        db: AsyncSession,
        period_type: str,  # hourly, daily, monthly
        period_start: datetime,
        period_end: datetime
    ) -> int:
        """Aggregate usage records into summary table"""

        # Get all tenants with usage in period
        tenants_result = await db.execute(
            select(UsageRecord.tenant_id).where(
                and_(
                    UsageRecord.recorded_at >= period_start,
                    UsageRecord.recorded_at < period_end
                )
            ).distinct()
        )
        tenant_ids = [row[0] for row in tenants_result]

        aggregated = 0

        for tenant_id in tenant_ids:
            for metric_type in UsageMetricType:
                # Calculate aggregate
                result = await db.execute(
                    select(
                        func.sum(UsageRecord.quantity),
                        func.count(UsageRecord.id)
                    ).where(
                        and_(
                            UsageRecord.tenant_id == tenant_id,
                            UsageRecord.metric_type == metric_type,
                            UsageRecord.recorded_at >= period_start,
                            UsageRecord.recorded_at < period_end,
                            UsageRecord.is_billable == True
                        )
                    )
                )
                row = result.one()

                if row[0] is None or row[0] == 0:
                    continue

                total_quantity = Decimal(str(row[0]))
                record_count = row[1]

                # Get subscription
                subscription_id = await self._get_active_subscription_id(db, tenant_id)

                # Get included and calculate overage
                included = await self._get_included_quantity(db, tenant_id, metric_type)
                overage = max(Decimal("0"), total_quantity - Decimal(str(included)))
                overage_rate = await self._get_overage_rate(db, tenant_id, metric_type)
                overage_amount = float(overage) * overage_rate

                # Upsert aggregate
                existing_result = await db.execute(
                    select(UsageAggregate).where(
                        and_(
                            UsageAggregate.tenant_id == tenant_id,
                            UsageAggregate.metric_type == metric_type,
                            UsageAggregate.period_type == period_type,
                            UsageAggregate.period_start == period_start
                        )
                    )
                )
                existing = existing_result.scalar_one_or_none()

                if existing:
                    existing.total_quantity = total_quantity
                    existing.record_count = record_count
                    existing.included_quantity = Decimal(str(included))
                    existing.overage_quantity = overage
                    existing.overage_rate = Decimal(str(overage_rate))
                    existing.overage_amount = Decimal(str(overage_amount))
                    existing.updated_at = datetime.now(timezone.utc)
                else:
                    aggregate = UsageAggregate(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        subscription_id=subscription_id,
                        period_type=period_type,
                        period_start=period_start,
                        period_end=period_end,
                        metric_type=metric_type,
                        total_quantity=total_quantity,
                        record_count=record_count,
                        included_quantity=Decimal(str(included)),
                        overage_quantity=overage,
                        overage_rate=Decimal(str(overage_rate)),
                        overage_amount=Decimal(str(overage_amount))
                    )
                    db.add(aggregate)

                aggregated += 1

        await db.commit()
        return aggregated

    async def get_usage_for_billing(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        period_start: datetime,
        period_end: datetime
    ) -> List[Dict[str, Any]]:
        """Get usage data for invoice generation"""

        usage_items = []

        for metric_type in UsageMetricType:
            summary = await self.get_usage_summary(
                db, tenant_id, metric_type, period_start, period_end
            )

            if summary.overage_quantity > 0:
                usage_items.append({
                    "metric_type": metric_type.value,
                    "description": f"{metric_type.value.replace('_', ' ').title()} Overage",
                    "quantity": summary.overage_quantity,
                    "unit": summary.unit,
                    "unit_price": await self._get_overage_rate(db, tenant_id, metric_type),
                    "amount": summary.overage_amount
                })

        return usage_items

    async def mark_usage_billed(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        period_start: datetime,
        period_end: datetime,
        invoice_line_item_id: UUID
    ) -> int:
        """Mark usage records as billed"""

        result = await db.execute(
            update(UsageRecord).where(
                and_(
                    UsageRecord.tenant_id == tenant_id,
                    UsageRecord.recorded_at >= period_start,
                    UsageRecord.recorded_at < period_end,
                    UsageRecord.is_billable == True,
                    UsageRecord.billed_at.is_(None)
                )
            ).values(
                billed_at=datetime.now(timezone.utc),
                invoice_line_item_id=invoice_line_item_id
            )
        )
        await db.commit()
        return result.rowcount

    async def get_usage_trend(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        metric_type: UsageMetricType,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get daily usage trend"""

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        result = await db.execute(
            select(
                func.date_trunc('day', UsageRecord.recorded_at).label('day'),
                func.sum(UsageRecord.quantity).label('total')
            ).where(
                and_(
                    UsageRecord.tenant_id == tenant_id,
                    UsageRecord.metric_type == metric_type,
                    UsageRecord.recorded_at >= start_date,
                    UsageRecord.recorded_at < end_date
                )
            ).group_by(
                func.date_trunc('day', UsageRecord.recorded_at)
            ).order_by(
                func.date_trunc('day', UsageRecord.recorded_at)
            )
        )

        return [
            {"date": row.day.isoformat(), "total": float(row.total)}
            for row in result
        ]

    async def forecast_usage(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        metric_type: UsageMetricType
    ) -> Dict[str, Any]:
        """Forecast usage for current period"""

        period_start, period_end = await self._get_current_billing_period(db, tenant_id)
        now = datetime.now(timezone.utc)

        # Days elapsed and remaining
        total_days = (period_end - period_start).days
        days_elapsed = (now - period_start).days

        if days_elapsed == 0:
            return {
                "current_usage": 0,
                "projected_usage": 0,
                "included_limit": await self._get_included_quantity(db, tenant_id, metric_type),
                "projected_overage": 0,
                "confidence": "low"
            }

        # Get current usage
        summary = await self.get_usage_summary(
            db, tenant_id, metric_type, period_start, now
        )

        # Project based on daily average
        daily_avg = summary.total_quantity / days_elapsed
        projected_usage = daily_avg * total_days
        projected_overage = max(0, projected_usage - summary.included_quantity)

        return {
            "current_usage": summary.total_quantity,
            "projected_usage": round(projected_usage, 2),
            "included_limit": summary.included_quantity,
            "projected_overage": round(projected_overage, 2),
            "daily_average": round(daily_avg, 2),
            "days_remaining": total_days - days_elapsed,
            "confidence": "high" if days_elapsed > 7 else "medium" if days_elapsed > 3 else "low"
        }

    # Private helper methods

    async def _get_active_subscription_id(
        self,
        db: AsyncSession,
        tenant_id: UUID
    ) -> Optional[UUID]:
        """Get active subscription for tenant"""
        result = await db.execute(
            select(Subscription.id).where(
                and_(
                    Subscription.tenant_id == tenant_id,
                    Subscription.status.in_([
                        SubscriptionStatus.ACTIVE,
                        SubscriptionStatus.TRIALING
                    ])
                )
            ).limit(1)
        )
        row = result.scalar_one_or_none()
        return row

    async def _get_current_billing_period(
        self,
        db: AsyncSession,
        tenant_id: UUID
    ) -> tuple:
        """Get current billing period for tenant"""
        result = await db.execute(
            select(
                Subscription.current_period_start,
                Subscription.current_period_end
            ).where(
                and_(
                    Subscription.tenant_id == tenant_id,
                    Subscription.status.in_([
                        SubscriptionStatus.ACTIVE,
                        SubscriptionStatus.TRIALING
                    ])
                )
            ).limit(1)
        )
        row = result.one_or_none()

        if row:
            return row.current_period_start, row.current_period_end

        # Default to current month
        now = datetime.now(timezone.utc)
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if now.month == 12:
            end = start.replace(year=now.year + 1, month=1)
        else:
            end = start.replace(month=now.month + 1)

        return start, end

    async def _get_included_quantity(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        metric_type: UsageMetricType
    ) -> float:
        """Get included quantity from subscription plan"""

        # Map metric type to feature key
        feature_key_map = {
            UsageMetricType.AI_INTERACTION: "ai_interactions",
            UsageMetricType.TELEHEALTH_MINUTES: "telehealth_minutes",
            UsageMetricType.SMS_MESSAGE: "sms_messages",
            UsageMetricType.FHIR_API: "fhir_api_calls",
            UsageMetricType.STORAGE_GB: "storage_gb",
            UsageMetricType.ACTIVE_PATIENT: "patients",
            UsageMetricType.ACTIVE_PROVIDER: "providers"
        }

        feature_key = feature_key_map.get(metric_type)
        if not feature_key:
            return 0

        result = await db.execute(
            select(Entitlement.limit_value).where(
                and_(
                    Entitlement.tenant_id == tenant_id,
                    Entitlement.feature_key == feature_key,
                    Entitlement.is_enabled == True
                )
            ).limit(1)
        )
        limit = result.scalar_one_or_none()

        return float(limit) if limit else 0

    async def _get_overage_rate(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        metric_type: UsageMetricType
    ) -> float:
        """Get overage rate from subscription plan"""

        result = await db.execute(
            select(Plan.overage_rates).join(
                Subscription, Subscription.plan_id == Plan.id
            ).where(
                and_(
                    Subscription.tenant_id == tenant_id,
                    Subscription.status.in_([
                        SubscriptionStatus.ACTIVE,
                        SubscriptionStatus.TRIALING
                    ])
                )
            ).limit(1)
        )
        overage_rates = result.scalar_one_or_none()

        if overage_rates:
            rate_key_map = {
                UsageMetricType.AI_INTERACTION: "ai_interactions",
                UsageMetricType.TELEHEALTH_MINUTES: "telehealth_minutes",
                UsageMetricType.SMS_MESSAGE: "sms_messages",
                UsageMetricType.STORAGE_GB: "storage_gb"
            }
            rate_key = rate_key_map.get(metric_type)
            if rate_key and rate_key in overage_rates:
                return float(overage_rates[rate_key])

        return 0

    async def _update_entitlement_usage(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        subscription_id: UUID,
        metric_type_value: str,
        quantity: Decimal
    ) -> None:
        """Update entitlement usage counter"""

        feature_key_map = {
            "ai_interaction": "ai_interactions",
            "telehealth_minutes": "telehealth_minutes",
            "sms_message": "sms_messages",
            "fhir_api": "fhir_api_calls",
            "storage_gb": "storage_gb",
            "active_patient": "patients",
            "active_provider": "providers"
        }

        feature_key = feature_key_map.get(metric_type_value)
        if not feature_key:
            return

        await db.execute(
            update(Entitlement).where(
                and_(
                    Entitlement.tenant_id == tenant_id,
                    Entitlement.feature_key == feature_key
                )
            ).values(
                current_usage=Entitlement.current_usage + int(quantity)
            )
        )

    def _get_alert_message(
        self,
        metric_type: UsageMetricType,
        threshold: int,
        usage_percent: float
    ) -> str:
        """Generate alert message"""
        metric_name = metric_type.value.replace("_", " ").title()

        if threshold == 100:
            return f"You have exceeded your {metric_name} limit ({usage_percent:.0f}% used). Overage charges will apply."
        elif threshold == 90:
            return f"You are approaching your {metric_name} limit ({usage_percent:.0f}% used)."
        else:
            return f"You have used {usage_percent:.0f}% of your {metric_name} allocation."

    def _record_to_response(self, record: UsageRecord) -> UsageRecordResponse:
        """Convert record to response"""
        return UsageRecordResponse(
            id=record.id,
            metric_type=record.metric_type.value,
            quantity=float(record.quantity),
            user_id=record.user_id,
            resource_id=record.resource_id,
            recorded_at=record.recorded_at,
            is_billable=record.is_billable,
            billed_at=record.billed_at
        )

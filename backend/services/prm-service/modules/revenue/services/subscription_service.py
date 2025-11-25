"""
Subscription Service
EPIC-017: Subscription lifecycle management
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_, or_, func, desc

from modules.revenue.models import (
    Subscription, Plan, SubscriptionChange, Customer,
    Entitlement, BillingAuditLog,
    SubscriptionStatus, BillingCycle, PlanType
)
from modules.revenue.schemas import (
    SubscriptionCreate, SubscriptionUpdate, SubscriptionChangePlan,
    SubscriptionCancel, SubscriptionResponse, SubscriptionListResponse,
    ProrationPreview
)


class SubscriptionService:
    """
    Handles subscription lifecycle:
    - Create subscriptions with trial
    - Upgrade/downgrade plans
    - Quantity changes
    - Cancellation with grace period
    - Renewal processing
    """

    async def create_subscription(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        data: SubscriptionCreate,
        user_id: UUID = None
    ) -> SubscriptionResponse:
        """Create a new subscription"""

        # Get plan
        plan = await self._get_plan(db, data.plan_id)
        if not plan:
            raise ValueError("Plan not found")

        if not plan.is_active:
            raise ValueError("Plan is not available")

        # Calculate pricing
        unit_price = self._get_unit_price(plan, data.billing_cycle)
        if unit_price is None:
            raise ValueError(f"Plan does not support {data.billing_cycle.value} billing")

        # Calculate period dates
        now = datetime.now(timezone.utc)
        trial_start = None
        trial_end = None
        period_start = now
        period_end = self._calculate_period_end(now, data.billing_cycle)

        if data.start_trial and plan.trial_enabled and plan.trial_days > 0:
            trial_start = now
            trial_end = now + timedelta(days=plan.trial_days)
            period_end = trial_end  # First period ends at trial end

        # Create subscription
        subscription = Subscription(
            id=uuid4(),
            tenant_id=tenant_id,
            plan_id=plan.id,
            status=SubscriptionStatus.TRIALING if trial_start else SubscriptionStatus.ACTIVE,
            billing_cycle=BillingCycle(data.billing_cycle.value),
            quantity=data.quantity,
            provider_count=data.provider_count,
            facility_count=data.facility_count,
            current_period_start=period_start,
            current_period_end=period_end,
            trial_start=trial_start,
            trial_end=trial_end,
            unit_price=unit_price,
            discount_percent=Decimal("0"),
            metadata=data.metadata or {}
        )

        # Calculate MRR/ARR
        subscription.mrr = self._calculate_mrr(subscription, plan)
        subscription.arr = subscription.mrr * 12

        db.add(subscription)

        # Create entitlements from plan
        await self._create_entitlements(db, tenant_id, subscription.id, plan)

        # Log audit
        await self._log_audit(
            db, tenant_id, user_id, "subscription_created", "subscription",
            subscription.id, new_values={
                "plan_id": str(plan.id),
                "billing_cycle": data.billing_cycle.value,
                "quantity": data.quantity
            }
        )

        await db.commit()
        await db.refresh(subscription)

        return await self._subscription_to_response(db, subscription)

    async def get_subscription(
        self,
        db: AsyncSession,
        subscription_id: UUID,
        tenant_id: UUID
    ) -> SubscriptionResponse:
        """Get subscription by ID"""

        result = await db.execute(
            select(Subscription).where(
                and_(
                    Subscription.id == subscription_id,
                    Subscription.tenant_id == tenant_id
                )
            )
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise ValueError("Subscription not found")

        return await self._subscription_to_response(db, subscription)

    async def get_tenant_subscription(
        self,
        db: AsyncSession,
        tenant_id: UUID
    ) -> Optional[SubscriptionResponse]:
        """Get active subscription for a tenant"""

        result = await db.execute(
            select(Subscription).where(
                and_(
                    Subscription.tenant_id == tenant_id,
                    Subscription.status.in_([
                        SubscriptionStatus.TRIALING,
                        SubscriptionStatus.ACTIVE,
                        SubscriptionStatus.PAST_DUE
                    ])
                )
            ).order_by(desc(Subscription.created_at)).limit(1)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            return None

        return await self._subscription_to_response(db, subscription)

    async def list_subscriptions(
        self,
        db: AsyncSession,
        status: Optional[SubscriptionStatus] = None,
        plan_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> SubscriptionListResponse:
        """List all subscriptions"""

        query = select(Subscription)

        if status:
            query = query.where(Subscription.status == status)
        if plan_id:
            query = query.where(Subscription.plan_id == plan_id)

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total = count_result.scalar()

        # Get results
        query = query.order_by(desc(Subscription.created_at))
        query = query.offset(offset).limit(limit)

        result = await db.execute(query)
        subscriptions = result.scalars().all()

        responses = []
        for sub in subscriptions:
            responses.append(await self._subscription_to_response(db, sub))

        return SubscriptionListResponse(subscriptions=responses, total=total)

    async def change_plan(
        self,
        db: AsyncSession,
        subscription_id: UUID,
        tenant_id: UUID,
        data: SubscriptionChangePlan,
        user_id: UUID = None
    ) -> SubscriptionResponse:
        """Change subscription plan (upgrade/downgrade)"""

        # Get subscription
        result = await db.execute(
            select(Subscription).where(
                and_(
                    Subscription.id == subscription_id,
                    Subscription.tenant_id == tenant_id
                )
            )
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise ValueError("Subscription not found")

        if subscription.status not in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]:
            raise ValueError("Cannot change plan for inactive subscription")

        # Get current and new plans
        current_plan = await self._get_plan(db, subscription.plan_id)
        new_plan = await self._get_plan(db, data.new_plan_id)

        if not new_plan or not new_plan.is_active:
            raise ValueError("New plan not available")

        # Calculate proration
        proration = await self.calculate_proration(
            db, subscription, current_plan, new_plan, data.billing_cycle
        )

        # Determine billing cycle
        billing_cycle = data.billing_cycle or BillingCycle(subscription.billing_cycle.value)
        new_unit_price = self._get_unit_price(new_plan, billing_cycle)

        if new_unit_price is None:
            raise ValueError(f"New plan does not support {billing_cycle.value} billing")

        # Record change
        change = SubscriptionChange(
            id=uuid4(),
            subscription_id=subscription.id,
            change_type="upgrade" if new_unit_price > subscription.unit_price else "downgrade",
            from_plan_id=subscription.plan_id,
            to_plan_id=new_plan.id,
            proration_amount=Decimal(str(proration.proration_amount)),
            proration_credit=Decimal(str(proration.proration_credit)),
            effective_at=proration.effective_date,
            changed_by=user_id,
            change_reason=f"Plan change from {current_plan.name} to {new_plan.name}"
        )
        db.add(change)

        # Update subscription
        old_values = {
            "plan_id": str(subscription.plan_id),
            "unit_price": float(subscription.unit_price)
        }

        subscription.plan_id = new_plan.id
        subscription.unit_price = new_unit_price
        subscription.billing_cycle = billing_cycle

        if data.effective_immediately:
            change.processed_at = datetime.now(timezone.utc)

        # Recalculate MRR
        subscription.mrr = self._calculate_mrr(subscription, new_plan)
        subscription.arr = subscription.mrr * 12
        subscription.updated_at = datetime.now(timezone.utc)

        # Update entitlements
        await self._update_entitlements(db, tenant_id, subscription.id, new_plan)

        # Log audit
        await self._log_audit(
            db, tenant_id, user_id, "subscription_plan_changed", "subscription",
            subscription.id,
            old_values=old_values,
            new_values={"plan_id": str(new_plan.id), "unit_price": float(new_unit_price)}
        )

        await db.commit()
        await db.refresh(subscription)

        return await self._subscription_to_response(db, subscription)

    async def update_quantity(
        self,
        db: AsyncSession,
        subscription_id: UUID,
        tenant_id: UUID,
        data: SubscriptionUpdate,
        user_id: UUID = None
    ) -> SubscriptionResponse:
        """Update subscription quantity"""

        result = await db.execute(
            select(Subscription).where(
                and_(
                    Subscription.id == subscription_id,
                    Subscription.tenant_id == tenant_id
                )
            )
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise ValueError("Subscription not found")

        old_values = {}
        new_values = {}

        if data.quantity is not None and data.quantity != subscription.quantity:
            old_values["quantity"] = subscription.quantity
            new_values["quantity"] = data.quantity

            # Record change
            change = SubscriptionChange(
                id=uuid4(),
                subscription_id=subscription.id,
                change_type="quantity_change",
                from_quantity=subscription.quantity,
                to_quantity=data.quantity,
                effective_at=datetime.now(timezone.utc),
                processed_at=datetime.now(timezone.utc),
                changed_by=user_id
            )
            db.add(change)

            subscription.quantity = data.quantity

        if data.provider_count is not None:
            old_values["provider_count"] = subscription.provider_count
            subscription.provider_count = data.provider_count
            new_values["provider_count"] = data.provider_count

        if data.facility_count is not None:
            old_values["facility_count"] = subscription.facility_count
            subscription.facility_count = data.facility_count
            new_values["facility_count"] = data.facility_count

        if data.metadata is not None:
            subscription.metadata = data.metadata

        # Recalculate MRR
        plan = await self._get_plan(db, subscription.plan_id)
        subscription.mrr = self._calculate_mrr(subscription, plan)
        subscription.arr = subscription.mrr * 12
        subscription.updated_at = datetime.now(timezone.utc)

        if old_values:
            await self._log_audit(
                db, tenant_id, user_id, "subscription_updated", "subscription",
                subscription.id, old_values=old_values, new_values=new_values
            )

        await db.commit()
        await db.refresh(subscription)

        return await self._subscription_to_response(db, subscription)

    async def cancel_subscription(
        self,
        db: AsyncSession,
        subscription_id: UUID,
        tenant_id: UUID,
        data: SubscriptionCancel,
        user_id: UUID = None
    ) -> SubscriptionResponse:
        """Cancel a subscription"""

        result = await db.execute(
            select(Subscription).where(
                and_(
                    Subscription.id == subscription_id,
                    Subscription.tenant_id == tenant_id
                )
            )
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise ValueError("Subscription not found")

        if subscription.status in [SubscriptionStatus.CANCELED, SubscriptionStatus.EXPIRED]:
            raise ValueError("Subscription already canceled")

        subscription.cancel_at_period_end = data.cancel_at_period_end
        subscription.canceled_at = datetime.now(timezone.utc)
        subscription.cancellation_reason = data.reason
        subscription.cancellation_feedback = data.feedback

        if not data.cancel_at_period_end:
            # Immediate cancellation
            subscription.status = SubscriptionStatus.CANCELED
            subscription.ended_at = datetime.now(timezone.utc)

        subscription.updated_at = datetime.now(timezone.utc)

        # Record change
        change = SubscriptionChange(
            id=uuid4(),
            subscription_id=subscription.id,
            change_type="cancel",
            effective_at=subscription.ended_at or subscription.current_period_end,
            changed_by=user_id,
            change_reason=data.reason
        )
        db.add(change)

        await self._log_audit(
            db, tenant_id, user_id, "subscription_canceled", "subscription",
            subscription.id, new_values={
                "cancel_at_period_end": data.cancel_at_period_end,
                "reason": data.reason
            }
        )

        await db.commit()
        await db.refresh(subscription)

        return await self._subscription_to_response(db, subscription)

    async def reactivate_subscription(
        self,
        db: AsyncSession,
        subscription_id: UUID,
        tenant_id: UUID,
        user_id: UUID = None
    ) -> SubscriptionResponse:
        """Reactivate a canceled subscription"""

        result = await db.execute(
            select(Subscription).where(
                and_(
                    Subscription.id == subscription_id,
                    Subscription.tenant_id == tenant_id
                )
            )
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise ValueError("Subscription not found")

        if subscription.status != SubscriptionStatus.CANCELED:
            if not subscription.cancel_at_period_end:
                raise ValueError("Subscription is not pending cancellation")

        # Remove cancellation
        subscription.cancel_at_period_end = False
        subscription.canceled_at = None
        subscription.cancellation_reason = None
        subscription.cancellation_feedback = None

        if subscription.status == SubscriptionStatus.CANCELED:
            subscription.status = SubscriptionStatus.ACTIVE
            subscription.ended_at = None

        subscription.updated_at = datetime.now(timezone.utc)

        await self._log_audit(
            db, tenant_id, user_id, "subscription_reactivated", "subscription",
            subscription.id
        )

        await db.commit()
        await db.refresh(subscription)

        return await self._subscription_to_response(db, subscription)

    async def calculate_proration(
        self,
        db: AsyncSession,
        subscription: Subscription,
        current_plan: Plan,
        new_plan: Plan,
        new_billing_cycle: BillingCycle = None
    ) -> ProrationPreview:
        """Calculate proration for plan change"""

        now = datetime.now(timezone.utc)
        billing_cycle = new_billing_cycle or subscription.billing_cycle

        # Days remaining in current period
        total_days = (subscription.current_period_end - subscription.current_period_start).days
        days_remaining = max(0, (subscription.current_period_end - now).days)

        # Current plan credit (unused portion)
        current_daily_rate = float(subscription.unit_price) / total_days if total_days > 0 else 0
        proration_credit = current_daily_rate * days_remaining

        # New plan charge (for remaining period)
        new_unit_price = self._get_unit_price(new_plan, billing_cycle)
        new_daily_rate = float(new_unit_price) / total_days if total_days > 0 else 0
        proration_amount = new_daily_rate * days_remaining

        net_amount = proration_amount - proration_credit

        return ProrationPreview(
            current_plan=current_plan.name,
            new_plan=new_plan.name,
            proration_amount=round(proration_amount, 2),
            proration_credit=round(proration_credit, 2),
            net_amount=round(net_amount, 2),
            effective_date=now,
            next_billing_date=subscription.current_period_end
        )

    async def process_renewals(
        self,
        db: AsyncSession,
        batch_size: int = 100
    ) -> Dict[str, int]:
        """Process subscription renewals"""

        now = datetime.now(timezone.utc)

        # Find subscriptions due for renewal
        result = await db.execute(
            select(Subscription).where(
                and_(
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    Subscription.current_period_end <= now,
                    Subscription.cancel_at_period_end == False
                )
            ).limit(batch_size)
        )
        subscriptions = result.scalars().all()

        renewed = 0
        failed = 0

        for subscription in subscriptions:
            try:
                # Advance to next period
                subscription.current_period_start = subscription.current_period_end
                subscription.current_period_end = self._calculate_period_end(
                    subscription.current_period_start,
                    subscription.billing_cycle
                )
                subscription.updated_at = now
                renewed += 1
            except Exception:
                failed += 1

        # Handle canceled subscriptions at period end
        result = await db.execute(
            select(Subscription).where(
                and_(
                    Subscription.cancel_at_period_end == True,
                    Subscription.current_period_end <= now,
                    Subscription.status != SubscriptionStatus.CANCELED
                )
            ).limit(batch_size)
        )
        to_cancel = result.scalars().all()

        canceled = 0
        for subscription in to_cancel:
            subscription.status = SubscriptionStatus.CANCELED
            subscription.ended_at = now
            canceled += 1

        await db.commit()

        return {
            "renewed": renewed,
            "failed": failed,
            "canceled": canceled
        }

    async def activate_after_trial(
        self,
        db: AsyncSession,
        subscription_id: UUID
    ) -> None:
        """Activate subscription after trial ends"""

        result = await db.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            return

        if subscription.status != SubscriptionStatus.TRIALING:
            return

        now = datetime.now(timezone.utc)

        if subscription.trial_end and subscription.trial_end <= now:
            subscription.status = SubscriptionStatus.ACTIVE
            subscription.current_period_start = now
            subscription.current_period_end = self._calculate_period_end(
                now, subscription.billing_cycle
            )
            subscription.updated_at = now

            await db.commit()

    # Private helper methods

    async def _get_plan(self, db: AsyncSession, plan_id: UUID) -> Optional[Plan]:
        """Get plan by ID"""
        result = await db.execute(
            select(Plan).where(Plan.id == plan_id)
        )
        return result.scalar_one_or_none()

    def _get_unit_price(
        self,
        plan: Plan,
        billing_cycle: BillingCycle
    ) -> Optional[Decimal]:
        """Get unit price for billing cycle"""
        if billing_cycle == BillingCycle.MONTHLY:
            return plan.monthly_price
        elif billing_cycle == BillingCycle.ANNUAL:
            return plan.annual_price
        elif billing_cycle == BillingCycle.QUARTERLY:
            return plan.quarterly_price
        return None

    def _calculate_period_end(
        self,
        start: datetime,
        billing_cycle: BillingCycle
    ) -> datetime:
        """Calculate period end date"""
        if billing_cycle == BillingCycle.MONTHLY:
            return start + timedelta(days=30)
        elif billing_cycle == BillingCycle.QUARTERLY:
            return start + timedelta(days=90)
        elif billing_cycle == BillingCycle.ANNUAL:
            return start + timedelta(days=365)
        return start + timedelta(days=30)

    def _calculate_mrr(
        self,
        subscription: Subscription,
        plan: Plan
    ) -> Decimal:
        """Calculate monthly recurring revenue"""
        if subscription.billing_cycle == BillingCycle.MONTHLY:
            base = subscription.unit_price
        elif subscription.billing_cycle == BillingCycle.ANNUAL:
            base = subscription.unit_price / 12
        elif subscription.billing_cycle == BillingCycle.QUARTERLY:
            base = subscription.unit_price / 3
        else:
            base = subscription.unit_price

        return base * subscription.quantity

    async def _create_entitlements(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        subscription_id: UUID,
        plan: Plan
    ) -> None:
        """Create entitlements from plan features"""

        features = plan.features or {}
        limits = plan.limits or {}

        # Combine features and limits
        all_features = {**features, **limits}

        for key, value in all_features.items():
            if isinstance(value, bool):
                limit_type = "boolean"
                limit_value = None
                is_enabled = value
            elif value is None or value == -1:
                limit_type = "unlimited"
                limit_value = None
                is_enabled = True
            else:
                limit_type = "count"
                limit_value = int(value)
                is_enabled = True

            entitlement = Entitlement(
                id=uuid4(),
                tenant_id=tenant_id,
                subscription_id=subscription_id,
                feature_key=key,
                feature_name=key.replace("_", " ").title(),
                limit_type=limit_type,
                limit_value=limit_value,
                is_enabled=is_enabled
            )
            db.add(entitlement)

    async def _update_entitlements(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        subscription_id: UUID,
        plan: Plan
    ) -> None:
        """Update entitlements for plan change"""

        # Delete existing entitlements
        await db.execute(
            Entitlement.__table__.delete().where(
                Entitlement.subscription_id == subscription_id
            )
        )

        # Create new entitlements
        await self._create_entitlements(db, tenant_id, subscription_id, plan)

    async def _log_audit(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        action: str,
        resource_type: str,
        resource_id: UUID,
        old_values: Dict = None,
        new_values: Dict = None
    ) -> None:
        """Log billing audit event"""

        log = BillingAuditLog(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            actor_type="user" if user_id else "system",
            action=action,
            action_category="subscription",
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values
        )
        db.add(log)

    async def _subscription_to_response(
        self,
        db: AsyncSession,
        subscription: Subscription
    ) -> SubscriptionResponse:
        """Convert subscription to response"""

        plan = await self._get_plan(db, subscription.plan_id)
        plan_name = plan.name if plan else None

        return SubscriptionResponse(
            id=subscription.id,
            tenant_id=subscription.tenant_id,
            plan_id=subscription.plan_id,
            plan_name=plan_name,
            status=subscription.status.value,
            billing_cycle=subscription.billing_cycle.value,
            quantity=subscription.quantity,
            provider_count=subscription.provider_count,
            facility_count=subscription.facility_count,
            unit_price=float(subscription.unit_price),
            discount_percent=float(subscription.discount_percent),
            mrr=float(subscription.mrr) if subscription.mrr else None,
            arr=float(subscription.arr) if subscription.arr else None,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            trial_start=subscription.trial_start,
            trial_end=subscription.trial_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
            canceled_at=subscription.canceled_at,
            created_at=subscription.created_at
        )

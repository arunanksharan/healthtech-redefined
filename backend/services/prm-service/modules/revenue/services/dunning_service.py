"""
Dunning Service
EPIC-017: Revenue Infrastructure - Collections Management

Handles payment failure recovery, dunning campaigns, automated reminders,
payment retry logic, and account status management.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from sqlalchemy import select, func, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from modules.revenue.models import (
    DunningCampaign, Invoice, Subscription, Customer,
    Payment, BillingAuditLog,
    InvoiceStatus, SubscriptionStatus, PaymentStatus, AuditAction
)
from modules.revenue.schemas import (
    DunningCampaignCreate, DunningCampaignResponse,
    DunningActionResponse
)


class DunningService:
    """
    Service for dunning and collections management.

    Handles:
    - Automated payment retry logic
    - Dunning campaign management
    - Customer communication scheduling
    - Account status escalation
    - Recovery tracking and analytics
    """

    # Default dunning schedule (days after due date)
    DEFAULT_DUNNING_SCHEDULE = [
        {"days": 1, "action": "reminder_email", "description": "First reminder"},
        {"days": 3, "action": "reminder_email", "description": "Second reminder"},
        {"days": 7, "action": "payment_retry", "description": "First retry attempt"},
        {"days": 10, "action": "reminder_email", "description": "Third reminder + warning"},
        {"days": 14, "action": "payment_retry", "description": "Second retry attempt"},
        {"days": 21, "action": "final_notice", "description": "Final notice before suspension"},
        {"days": 28, "action": "suspend_account", "description": "Account suspension"},
        {"days": 45, "action": "cancel_subscription", "description": "Subscription cancellation"},
    ]

    async def create_dunning_campaign(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        data: DunningCampaignCreate,
        user_id: Optional[UUID] = None
    ) -> DunningCampaignResponse:
        """Create a new dunning campaign."""
        campaign = DunningCampaign(
            tenant_id=tenant_id,
            name=data.name,
            description=data.description,
            is_active=data.is_active,
            schedule=data.schedule or self.DEFAULT_DUNNING_SCHEDULE,
            email_templates=data.email_templates or {},
            retry_config=data.retry_config or {
                "max_retries": 3,
                "retry_interval_days": 3
            }
        )

        db.add(campaign)

        # Log audit
        audit_log = BillingAuditLog(
            tenant_id=tenant_id,
            entity_type="dunning_campaign",
            entity_id=campaign.id,
            action=AuditAction.SUBSCRIPTION_CREATED,
            user_id=user_id,
            details={"campaign_name": data.name}
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(campaign)

        return self._to_campaign_response(campaign)

    async def get_dunning_campaign(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        campaign_id: UUID
    ) -> DunningCampaignResponse:
        """Get dunning campaign by ID."""
        query = select(DunningCampaign).where(
            and_(
                DunningCampaign.id == campaign_id,
                DunningCampaign.tenant_id == tenant_id
            )
        )
        result = await db.execute(query)
        campaign = result.scalar_one_or_none()

        if not campaign:
            raise ValueError("Dunning campaign not found")

        return self._to_campaign_response(campaign)

    async def list_dunning_campaigns(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        active_only: bool = False
    ) -> List[DunningCampaignResponse]:
        """List all dunning campaigns for tenant."""
        query = select(DunningCampaign).where(
            DunningCampaign.tenant_id == tenant_id
        )

        if active_only:
            query = query.where(DunningCampaign.is_active == True)

        query = query.order_by(DunningCampaign.created_at.desc())

        result = await db.execute(query)
        campaigns = result.scalars().all()

        return [self._to_campaign_response(c) for c in campaigns]

    async def process_dunning(
        self,
        db: AsyncSession,
        tenant_id: Optional[UUID] = None,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Process dunning actions for overdue invoices.
        This should be run as a scheduled job.
        """
        stats = {
            "processed": 0,
            "reminders_sent": 0,
            "retries_attempted": 0,
            "accounts_suspended": 0,
            "subscriptions_canceled": 0,
            "recovered_amount": Decimal("0.00"),
            "errors": []
        }

        # Get overdue invoices
        query = select(Invoice).where(
            and_(
                Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PENDING]),
                Invoice.due_date < datetime.utcnow()
            )
        )

        if tenant_id:
            query = query.where(Invoice.tenant_id == tenant_id)

        query = query.limit(batch_size)

        result = await db.execute(query)
        invoices = result.scalars().all()

        for invoice in invoices:
            try:
                action_result = await self._process_invoice_dunning(db, invoice)
                stats["processed"] += 1

                if action_result.get("action") == "reminder_email":
                    stats["reminders_sent"] += 1
                elif action_result.get("action") == "payment_retry":
                    stats["retries_attempted"] += 1
                    if action_result.get("success"):
                        stats["recovered_amount"] += invoice.total_amount
                elif action_result.get("action") == "suspend_account":
                    stats["accounts_suspended"] += 1
                elif action_result.get("action") == "cancel_subscription":
                    stats["subscriptions_canceled"] += 1

            except Exception as e:
                stats["errors"].append({
                    "invoice_id": str(invoice.id),
                    "error": str(e)
                })

        await db.commit()
        return stats

    async def _process_invoice_dunning(
        self,
        db: AsyncSession,
        invoice: Invoice
    ) -> Dict[str, Any]:
        """Process dunning for a single invoice."""
        days_overdue = (datetime.utcnow() - invoice.due_date).days

        # Get applicable dunning campaign
        campaign = await self._get_campaign_for_invoice(db, invoice)

        if not campaign:
            # Use default schedule
            schedule = self.DEFAULT_DUNNING_SCHEDULE
        else:
            schedule = campaign.schedule

        # Determine current dunning step
        current_step = None
        for step in schedule:
            if days_overdue >= step["days"]:
                current_step = step

        if not current_step:
            return {"action": "none", "days_overdue": days_overdue}

        # Execute dunning action
        action = current_step["action"]
        result = {"action": action, "days_overdue": days_overdue}

        if action == "reminder_email":
            await self._send_dunning_reminder(db, invoice, current_step)
            result["success"] = True

        elif action == "payment_retry":
            retry_result = await self._retry_payment(db, invoice)
            result["success"] = retry_result

        elif action == "final_notice":
            await self._send_final_notice(db, invoice)
            result["success"] = True

        elif action == "suspend_account":
            await self._suspend_subscription(db, invoice)
            result["success"] = True

        elif action == "cancel_subscription":
            await self._cancel_subscription_for_nonpayment(db, invoice)
            result["success"] = True

        # Update invoice dunning metadata
        invoice.dunning_step = current_step.get("description")
        invoice.dunning_last_action = datetime.utcnow()

        return result

    async def _get_campaign_for_invoice(
        self,
        db: AsyncSession,
        invoice: Invoice
    ) -> Optional[DunningCampaign]:
        """Get the applicable dunning campaign for an invoice."""
        query = select(DunningCampaign).where(
            and_(
                DunningCampaign.tenant_id == invoice.tenant_id,
                DunningCampaign.is_active == True
            )
        ).order_by(DunningCampaign.created_at.desc()).limit(1)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def _send_dunning_reminder(
        self,
        db: AsyncSession,
        invoice: Invoice,
        step: Dict[str, Any]
    ) -> None:
        """Send dunning reminder email."""
        # Get customer
        customer_query = select(Customer).where(Customer.id == invoice.customer_id)
        result = await db.execute(customer_query)
        customer = result.scalar_one_or_none()

        if not customer:
            return

        # TODO: Integrate with email service
        # - Load appropriate email template based on dunning step
        # - Include payment link
        # - Track email delivery

        # Log the action
        audit_log = BillingAuditLog(
            tenant_id=invoice.tenant_id,
            entity_type="invoice",
            entity_id=invoice.id,
            action=AuditAction.DUNNING_EMAIL_SENT,
            details={
                "step": step.get("description"),
                "days_overdue": step.get("days"),
                "customer_email": customer.email
            }
        )
        db.add(audit_log)

    async def _send_final_notice(
        self,
        db: AsyncSession,
        invoice: Invoice
    ) -> None:
        """Send final notice before account suspension."""
        # Similar to reminder but with more urgent messaging
        # TODO: Integrate with email service with final notice template

        audit_log = BillingAuditLog(
            tenant_id=invoice.tenant_id,
            entity_type="invoice",
            entity_id=invoice.id,
            action=AuditAction.DUNNING_EMAIL_SENT,
            details={"type": "final_notice"}
        )
        db.add(audit_log)

    async def _retry_payment(
        self,
        db: AsyncSession,
        invoice: Invoice
    ) -> bool:
        """Attempt to retry payment for an overdue invoice."""
        # Get customer's default payment method
        # TODO: Integrate with PaymentService to attempt charge

        # Check retry limits
        retry_count = invoice.retry_count or 0
        max_retries = 3  # From campaign config

        if retry_count >= max_retries:
            return False

        # Attempt payment (placeholder)
        # payment_result = await payment_service.charge_invoice(invoice)

        # For now, log the attempt
        invoice.retry_count = retry_count + 1
        invoice.last_retry_at = datetime.utcnow()

        audit_log = BillingAuditLog(
            tenant_id=invoice.tenant_id,
            entity_type="invoice",
            entity_id=invoice.id,
            action=AuditAction.PAYMENT_FAILED,
            details={
                "retry_attempt": retry_count + 1,
                "reason": "placeholder_retry"
            }
        )
        db.add(audit_log)

        return False  # Placeholder - would return True on successful payment

    async def _suspend_subscription(
        self,
        db: AsyncSession,
        invoice: Invoice
    ) -> None:
        """Suspend subscription due to non-payment."""
        if not invoice.subscription_id:
            return

        subscription_query = select(Subscription).where(
            Subscription.id == invoice.subscription_id
        )
        result = await db.execute(subscription_query)
        subscription = result.scalar_one_or_none()

        if subscription and subscription.status == SubscriptionStatus.ACTIVE:
            subscription.status = SubscriptionStatus.PAST_DUE
            subscription.suspended_at = datetime.utcnow()
            subscription.suspension_reason = "non_payment"

            audit_log = BillingAuditLog(
                tenant_id=invoice.tenant_id,
                entity_type="subscription",
                entity_id=subscription.id,
                action=AuditAction.SUBSCRIPTION_CHANGE,
                details={
                    "change": "suspended",
                    "reason": "non_payment",
                    "invoice_id": str(invoice.id)
                }
            )
            db.add(audit_log)

    async def _cancel_subscription_for_nonpayment(
        self,
        db: AsyncSession,
        invoice: Invoice
    ) -> None:
        """Cancel subscription due to prolonged non-payment."""
        if not invoice.subscription_id:
            return

        subscription_query = select(Subscription).where(
            Subscription.id == invoice.subscription_id
        )
        result = await db.execute(subscription_query)
        subscription = result.scalar_one_or_none()

        if subscription and subscription.status in [
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.PAST_DUE
        ]:
            subscription.status = SubscriptionStatus.CANCELED
            subscription.canceled_at = datetime.utcnow()
            subscription.cancel_reason = "non_payment"
            subscription.cancel_at_period_end = False

            # Mark invoice as uncollectible
            invoice.status = InvoiceStatus.UNCOLLECTIBLE
            invoice.written_off_at = datetime.utcnow()

            audit_log = BillingAuditLog(
                tenant_id=invoice.tenant_id,
                entity_type="subscription",
                entity_id=subscription.id,
                action=AuditAction.SUBSCRIPTION_CANCELED,
                details={
                    "reason": "non_payment",
                    "invoice_id": str(invoice.id),
                    "amount_written_off": str(invoice.total_amount)
                }
            )
            db.add(audit_log)

    async def recover_subscription(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        subscription_id: UUID,
        payment_id: UUID,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Recover a suspended subscription after payment is received.
        """
        subscription_query = select(Subscription).where(
            and_(
                Subscription.id == subscription_id,
                Subscription.tenant_id == tenant_id
            )
        )
        result = await db.execute(subscription_query)
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise ValueError("Subscription not found")

        if subscription.status != SubscriptionStatus.PAST_DUE:
            raise ValueError("Subscription is not in past due status")

        # Reactivate subscription
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.suspended_at = None
        subscription.suspension_reason = None

        # Update overdue invoices
        await db.execute(
            update(Invoice)
            .where(
                and_(
                    Invoice.subscription_id == subscription_id,
                    Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PENDING])
                )
            )
            .values(
                status=InvoiceStatus.PAID,
                payment_id=payment_id,
                paid_at=datetime.utcnow()
            )
        )

        audit_log = BillingAuditLog(
            tenant_id=tenant_id,
            entity_type="subscription",
            entity_id=subscription.id,
            action=AuditAction.SUBSCRIPTION_CHANGE,
            user_id=user_id,
            details={
                "change": "recovered",
                "payment_id": str(payment_id)
            }
        )
        db.add(audit_log)

        await db.commit()

        return {
            "subscription_id": str(subscription_id),
            "status": subscription.status.value,
            "recovered_at": datetime.utcnow().isoformat()
        }

    async def get_dunning_statistics(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, Any]:
        """Get dunning and collections statistics."""
        # Total overdue amount
        overdue_query = select(func.sum(Invoice.total_amount)).where(
            and_(
                Invoice.tenant_id == tenant_id,
                Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PENDING]),
                Invoice.due_date < datetime.utcnow()
            )
        )
        overdue_result = await db.execute(overdue_query)
        overdue_amount = overdue_result.scalar() or Decimal("0.00")

        # Overdue invoice count
        overdue_count_query = select(func.count(Invoice.id)).where(
            and_(
                Invoice.tenant_id == tenant_id,
                Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PENDING]),
                Invoice.due_date < datetime.utcnow()
            )
        )
        overdue_count_result = await db.execute(overdue_count_query)
        overdue_count = overdue_count_result.scalar() or 0

        # Recovered amount in period
        recovered_query = select(func.sum(Invoice.total_amount)).where(
            and_(
                Invoice.tenant_id == tenant_id,
                Invoice.status == InvoiceStatus.PAID,
                Invoice.paid_at >= period_start,
                Invoice.paid_at <= period_end,
                Invoice.dunning_step.isnot(None)  # Was in dunning
            )
        )
        recovered_result = await db.execute(recovered_query)
        recovered_amount = recovered_result.scalar() or Decimal("0.00")

        # Written off amount in period
        written_off_query = select(func.sum(Invoice.total_amount)).where(
            and_(
                Invoice.tenant_id == tenant_id,
                Invoice.status == InvoiceStatus.UNCOLLECTIBLE,
                Invoice.written_off_at >= period_start,
                Invoice.written_off_at <= period_end
            )
        )
        written_off_result = await db.execute(written_off_query)
        written_off_amount = written_off_result.scalar() or Decimal("0.00")

        # Aging buckets
        now = datetime.utcnow()
        aging_buckets = {
            "1_30_days": Decimal("0.00"),
            "31_60_days": Decimal("0.00"),
            "61_90_days": Decimal("0.00"),
            "over_90_days": Decimal("0.00")
        }

        for bucket, min_days, max_days in [
            ("1_30_days", 1, 30),
            ("31_60_days", 31, 60),
            ("61_90_days", 61, 90),
            ("over_90_days", 91, 999)
        ]:
            bucket_query = select(func.sum(Invoice.total_amount)).where(
                and_(
                    Invoice.tenant_id == tenant_id,
                    Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PENDING]),
                    Invoice.due_date < now - timedelta(days=min_days),
                    Invoice.due_date >= now - timedelta(days=max_days) if max_days < 999 else True
                )
            )
            bucket_result = await db.execute(bucket_query)
            aging_buckets[bucket] = bucket_result.scalar() or Decimal("0.00")

        return {
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "total_overdue_amount": float(overdue_amount),
            "overdue_invoice_count": overdue_count,
            "recovered_amount": float(recovered_amount),
            "written_off_amount": float(written_off_amount),
            "recovery_rate": float(
                recovered_amount / (recovered_amount + written_off_amount) * 100
            ) if (recovered_amount + written_off_amount) > 0 else 0,
            "aging_buckets": {k: float(v) for k, v in aging_buckets.items()},
            "average_days_to_pay": 0  # TODO: Calculate from paid invoices
        }

    def _to_campaign_response(self, campaign: DunningCampaign) -> DunningCampaignResponse:
        """Convert campaign to response model."""
        return DunningCampaignResponse(
            id=campaign.id,
            name=campaign.name,
            description=campaign.description,
            is_active=campaign.is_active,
            schedule=campaign.schedule,
            email_templates=campaign.email_templates,
            retry_config=campaign.retry_config,
            created_at=campaign.created_at,
            updated_at=campaign.updated_at
        )

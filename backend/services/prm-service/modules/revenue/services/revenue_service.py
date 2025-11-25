"""
Revenue Service
EPIC-017: Revenue Infrastructure - Revenue Recognition and Reporting

Handles ASC 606 compliant revenue recognition, deferred revenue tracking,
SaaS metrics calculation (MRR, ARR, churn, LTV), and financial reporting.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import UUID
from dateutil.relativedelta import relativedelta
from sqlalchemy import select, func, and_, or_, extract
from sqlalchemy.ext.asyncio import AsyncSession

from modules.revenue.models import (
    RevenueSchedule, RevenueRecognition, Invoice, Subscription,
    Payment, Customer, Plan, BillingAuditLog,
    InvoiceStatus, SubscriptionStatus, PaymentStatus, AuditAction
)
from modules.revenue.schemas import (
    RevenueScheduleResponse, RevenueRecognitionResponse,
    SaaSMetricsResponse, MRRBreakdown, ChurnAnalysis
)


class RevenueService:
    """
    Service for revenue recognition and financial reporting.

    Handles:
    - ASC 606 compliant revenue recognition
    - Deferred revenue tracking
    - MRR/ARR calculation
    - Churn analysis
    - Customer lifetime value (LTV)
    - Cohort analysis
    - Financial reporting
    """

    async def create_revenue_schedule(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        invoice_id: UUID,
        user_id: Optional[UUID] = None
    ) -> RevenueScheduleResponse:
        """
        Create a revenue recognition schedule for an invoice.
        Implements ASC 606 revenue recognition principles.
        """
        # Get invoice
        invoice_query = select(Invoice).where(
            and_(
                Invoice.id == invoice_id,
                Invoice.tenant_id == tenant_id
            )
        )
        result = await db.execute(invoice_query)
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise ValueError("Invoice not found")

        # Calculate recognition periods
        period_start = invoice.billing_period_start
        period_end = invoice.billing_period_end

        if not period_start or not period_end:
            raise ValueError("Invoice must have billing period dates")

        # Calculate total days in period
        total_days = (period_end - period_start).days

        if total_days <= 0:
            raise ValueError("Invalid billing period")

        # Create revenue schedule
        schedule = RevenueSchedule(
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            subscription_id=invoice.subscription_id,
            total_amount=invoice.total_amount,
            recognized_amount=Decimal("0.00"),
            deferred_amount=invoice.total_amount,
            recognition_start=period_start,
            recognition_end=period_end,
            recognition_method="straight_line",  # ASC 606 default
            status="pending"
        )

        db.add(schedule)
        await db.flush()

        # Create monthly recognition entries
        await self._create_recognition_entries(db, tenant_id, schedule, total_days)

        # Log audit
        audit_log = BillingAuditLog(
            tenant_id=tenant_id,
            entity_type="revenue_schedule",
            entity_id=schedule.id,
            action=AuditAction.INVOICE_GENERATED,
            user_id=user_id,
            details={
                "invoice_id": str(invoice_id),
                "total_amount": str(invoice.total_amount),
                "recognition_period": f"{period_start.date()} to {period_end.date()}"
            }
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(schedule)

        return await self._to_schedule_response(db, schedule)

    async def _create_recognition_entries(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        schedule: RevenueSchedule,
        total_days: int
    ) -> None:
        """Create individual recognition entries for each period."""
        current_date = schedule.recognition_start
        daily_amount = schedule.total_amount / Decimal(str(total_days))

        while current_date < schedule.recognition_end:
            # Calculate month end or recognition end, whichever is earlier
            month_end = (current_date.replace(day=1) + relativedelta(months=1)) - timedelta(days=1)
            period_end = min(month_end, schedule.recognition_end)

            # Calculate days in this period
            period_days = (period_end - current_date).days + 1
            period_amount = daily_amount * Decimal(str(period_days))

            recognition = RevenueRecognition(
                tenant_id=tenant_id,
                schedule_id=schedule.id,
                period_start=current_date,
                period_end=period_end,
                amount=period_amount.quantize(Decimal("0.01")),
                recognized_at=None,
                status="pending"
            )

            db.add(recognition)

            # Move to next month
            current_date = period_end + timedelta(days=1)

    async def process_revenue_recognition(
        self,
        db: AsyncSession,
        tenant_id: Optional[UUID] = None,
        recognition_date: Optional[datetime] = None,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Process pending revenue recognition entries.
        Should be run daily or at period close.
        """
        if not recognition_date:
            recognition_date = datetime.utcnow()

        stats = {
            "processed": 0,
            "recognized_amount": Decimal("0.00"),
            "errors": []
        }

        # Get pending recognition entries that should be recognized
        query = select(RevenueRecognition).where(
            and_(
                RevenueRecognition.status == "pending",
                RevenueRecognition.period_end <= recognition_date
            )
        )

        if tenant_id:
            query = query.where(RevenueRecognition.tenant_id == tenant_id)

        query = query.limit(batch_size)

        result = await db.execute(query)
        entries = result.scalars().all()

        for entry in entries:
            try:
                entry.status = "recognized"
                entry.recognized_at = recognition_date

                # Update schedule totals
                schedule_query = select(RevenueSchedule).where(
                    RevenueSchedule.id == entry.schedule_id
                )
                schedule_result = await db.execute(schedule_query)
                schedule = schedule_result.scalar_one_or_none()

                if schedule:
                    schedule.recognized_amount = (
                        schedule.recognized_amount or Decimal("0.00")
                    ) + entry.amount
                    schedule.deferred_amount = (
                        schedule.total_amount - schedule.recognized_amount
                    )

                    if schedule.deferred_amount <= Decimal("0.00"):
                        schedule.status = "completed"

                stats["processed"] += 1
                stats["recognized_amount"] += entry.amount

            except Exception as e:
                stats["errors"].append({
                    "entry_id": str(entry.id),
                    "error": str(e)
                })

        await db.commit()
        return {
            **stats,
            "recognized_amount": float(stats["recognized_amount"])
        }

    async def calculate_mrr(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        as_of_date: Optional[datetime] = None
    ) -> MRRBreakdown:
        """
        Calculate Monthly Recurring Revenue with breakdown.
        """
        if not as_of_date:
            as_of_date = datetime.utcnow()

        # Get all active subscriptions
        subscriptions_query = select(Subscription).where(
            and_(
                Subscription.tenant_id == tenant_id,
                Subscription.status == SubscriptionStatus.ACTIVE
            )
        )
        result = await db.execute(subscriptions_query)
        subscriptions = result.scalars().all()

        # Calculate current MRR
        current_mrr = Decimal("0.00")
        plan_ids = set()

        for sub in subscriptions:
            plan_ids.add(sub.plan_id)
            mrr_value = sub.mrr_value or Decimal("0.00")
            current_mrr += mrr_value

        # Get previous month MRR for comparison
        previous_month = as_of_date - relativedelta(months=1)

        # Calculate MRR changes
        new_mrr = await self._calculate_new_mrr(db, tenant_id, as_of_date)
        expansion_mrr = await self._calculate_expansion_mrr(db, tenant_id, as_of_date)
        contraction_mrr = await self._calculate_contraction_mrr(db, tenant_id, as_of_date)
        churned_mrr = await self._calculate_churned_mrr(db, tenant_id, as_of_date)
        reactivation_mrr = await self._calculate_reactivation_mrr(db, tenant_id, as_of_date)

        net_mrr_change = new_mrr + expansion_mrr + reactivation_mrr - contraction_mrr - churned_mrr

        return MRRBreakdown(
            current_mrr=float(current_mrr),
            arr=float(current_mrr * 12),
            new_mrr=float(new_mrr),
            expansion_mrr=float(expansion_mrr),
            contraction_mrr=float(contraction_mrr),
            churned_mrr=float(churned_mrr),
            reactivation_mrr=float(reactivation_mrr),
            net_mrr_change=float(net_mrr_change),
            mrr_growth_rate=float(
                (net_mrr_change / (current_mrr - net_mrr_change) * 100)
                if (current_mrr - net_mrr_change) > 0 else 0
            ),
            as_of_date=as_of_date.isoformat()
        )

    async def _calculate_new_mrr(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        as_of_date: datetime
    ) -> Decimal:
        """Calculate MRR from new subscriptions in the current month."""
        month_start = as_of_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        query = select(func.sum(Subscription.mrr_value)).where(
            and_(
                Subscription.tenant_id == tenant_id,
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.activated_at >= month_start,
                Subscription.activated_at <= as_of_date
            )
        )
        result = await db.execute(query)
        return result.scalar() or Decimal("0.00")

    async def _calculate_expansion_mrr(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        as_of_date: datetime
    ) -> Decimal:
        """Calculate MRR from upgrades in the current month."""
        # This would track plan changes that increased MRR
        # For now, return placeholder
        return Decimal("0.00")

    async def _calculate_contraction_mrr(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        as_of_date: datetime
    ) -> Decimal:
        """Calculate MRR lost from downgrades in the current month."""
        return Decimal("0.00")

    async def _calculate_churned_mrr(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        as_of_date: datetime
    ) -> Decimal:
        """Calculate MRR lost from cancellations in the current month."""
        month_start = as_of_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Get MRR of subscriptions canceled this month
        query = select(func.sum(Subscription.mrr_value)).where(
            and_(
                Subscription.tenant_id == tenant_id,
                Subscription.status == SubscriptionStatus.CANCELED,
                Subscription.canceled_at >= month_start,
                Subscription.canceled_at <= as_of_date
            )
        )
        result = await db.execute(query)
        return result.scalar() or Decimal("0.00")

    async def _calculate_reactivation_mrr(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        as_of_date: datetime
    ) -> Decimal:
        """Calculate MRR from reactivated subscriptions."""
        return Decimal("0.00")

    async def calculate_churn(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        period_start: datetime,
        period_end: datetime
    ) -> ChurnAnalysis:
        """
        Calculate churn metrics for a period.
        """
        # Count subscriptions at start of period
        start_count_query = select(func.count(Subscription.id)).where(
            and_(
                Subscription.tenant_id == tenant_id,
                Subscription.created_at < period_start,
                or_(
                    Subscription.canceled_at.is_(None),
                    Subscription.canceled_at >= period_start
                )
            )
        )
        start_result = await db.execute(start_count_query)
        subscriptions_at_start = start_result.scalar() or 0

        # Count churned subscriptions
        churned_query = select(func.count(Subscription.id)).where(
            and_(
                Subscription.tenant_id == tenant_id,
                Subscription.status == SubscriptionStatus.CANCELED,
                Subscription.canceled_at >= period_start,
                Subscription.canceled_at <= period_end
            )
        )
        churned_result = await db.execute(churned_query)
        churned_count = churned_result.scalar() or 0

        # Calculate MRR at start
        mrr_start_query = select(func.sum(Subscription.mrr_value)).where(
            and_(
                Subscription.tenant_id == tenant_id,
                Subscription.created_at < period_start,
                or_(
                    Subscription.canceled_at.is_(None),
                    Subscription.canceled_at >= period_start
                )
            )
        )
        mrr_start_result = await db.execute(mrr_start_query)
        mrr_at_start = mrr_start_result.scalar() or Decimal("0.00")

        # Calculate churned MRR
        churned_mrr_query = select(func.sum(Subscription.mrr_value)).where(
            and_(
                Subscription.tenant_id == tenant_id,
                Subscription.status == SubscriptionStatus.CANCELED,
                Subscription.canceled_at >= period_start,
                Subscription.canceled_at <= period_end
            )
        )
        churned_mrr_result = await db.execute(churned_mrr_query)
        churned_mrr = churned_mrr_result.scalar() or Decimal("0.00")

        # Calculate rates
        customer_churn_rate = (
            (churned_count / subscriptions_at_start * 100)
            if subscriptions_at_start > 0 else 0
        )
        revenue_churn_rate = (
            float(churned_mrr / mrr_at_start * 100)
            if mrr_at_start > 0 else 0
        )

        # Get churn reasons
        reasons_query = select(
            Subscription.cancel_reason,
            func.count(Subscription.id)
        ).where(
            and_(
                Subscription.tenant_id == tenant_id,
                Subscription.status == SubscriptionStatus.CANCELED,
                Subscription.canceled_at >= period_start,
                Subscription.canceled_at <= period_end
            )
        ).group_by(Subscription.cancel_reason)

        reasons_result = await db.execute(reasons_query)
        churn_reasons = {
            reason or "unknown": count
            for reason, count in reasons_result.all()
        }

        return ChurnAnalysis(
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat(),
            subscriptions_at_start=subscriptions_at_start,
            churned_subscriptions=churned_count,
            customer_churn_rate=customer_churn_rate,
            revenue_churn_rate=revenue_churn_rate,
            churned_mrr=float(churned_mrr),
            mrr_at_start=float(mrr_at_start),
            churn_reasons=churn_reasons,
            net_revenue_retention=100 - revenue_churn_rate
        )

    async def calculate_ltv(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        customer_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Calculate Customer Lifetime Value.
        """
        if customer_id:
            # Calculate LTV for specific customer
            return await self._calculate_customer_ltv(db, tenant_id, customer_id)
        else:
            # Calculate average LTV across all customers
            return await self._calculate_average_ltv(db, tenant_id)

    async def _calculate_customer_ltv(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        customer_id: UUID
    ) -> Dict[str, Any]:
        """Calculate LTV for a specific customer."""
        # Get total revenue from customer
        payments_query = select(func.sum(Payment.amount)).where(
            and_(
                Payment.tenant_id == tenant_id,
                Payment.customer_id == customer_id,
                Payment.status == PaymentStatus.COMPLETED
            )
        )
        payments_result = await db.execute(payments_query)
        total_revenue = payments_result.scalar() or Decimal("0.00")

        # Get customer tenure
        customer_query = select(Customer).where(
            and_(
                Customer.id == customer_id,
                Customer.tenant_id == tenant_id
            )
        )
        customer_result = await db.execute(customer_query)
        customer = customer_result.scalar_one_or_none()

        if not customer:
            raise ValueError("Customer not found")

        tenure_months = (
            (datetime.utcnow() - customer.created_at).days / 30
            if customer.created_at else 0
        )

        # Get current MRR
        mrr_query = select(func.sum(Subscription.mrr_value)).where(
            and_(
                Subscription.tenant_id == tenant_id,
                Subscription.customer_id == customer_id,
                Subscription.status == SubscriptionStatus.ACTIVE
            )
        )
        mrr_result = await db.execute(mrr_query)
        current_mrr = mrr_result.scalar() or Decimal("0.00")

        # Simple LTV calculation
        avg_monthly_revenue = (
            total_revenue / Decimal(str(max(1, tenure_months)))
        )

        return {
            "customer_id": str(customer_id),
            "total_revenue": float(total_revenue),
            "tenure_months": round(tenure_months, 1),
            "current_mrr": float(current_mrr),
            "avg_monthly_revenue": float(avg_monthly_revenue),
            "estimated_ltv": float(avg_monthly_revenue * 24)  # Assuming 24 month average lifetime
        }

    async def _calculate_average_ltv(
        self,
        db: AsyncSession,
        tenant_id: UUID
    ) -> Dict[str, Any]:
        """Calculate average LTV across all customers."""
        # Get total customers
        customer_count_query = select(func.count(Customer.id)).where(
            Customer.tenant_id == tenant_id
        )
        count_result = await db.execute(customer_count_query)
        customer_count = count_result.scalar() or 0

        # Get total revenue
        revenue_query = select(func.sum(Payment.amount)).where(
            and_(
                Payment.tenant_id == tenant_id,
                Payment.status == PaymentStatus.COMPLETED
            )
        )
        revenue_result = await db.execute(revenue_query)
        total_revenue = revenue_result.scalar() or Decimal("0.00")

        # Get current total MRR
        mrr_query = select(func.sum(Subscription.mrr_value)).where(
            and_(
                Subscription.tenant_id == tenant_id,
                Subscription.status == SubscriptionStatus.ACTIVE
            )
        )
        mrr_result = await db.execute(mrr_query)
        total_mrr = mrr_result.scalar() or Decimal("0.00")

        arpu = total_mrr / Decimal(str(max(1, customer_count)))

        return {
            "customer_count": customer_count,
            "total_revenue": float(total_revenue),
            "total_mrr": float(total_mrr),
            "arpu": float(arpu),
            "estimated_avg_ltv": float(arpu * 24)  # Assuming 24 month lifetime
        }

    async def get_saas_metrics(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        period: str = "month"
    ) -> SaaSMetricsResponse:
        """
        Get comprehensive SaaS metrics dashboard.
        """
        now = datetime.utcnow()

        # Calculate period boundaries
        if period == "month":
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            period_end = now
        elif period == "quarter":
            quarter_start_month = ((now.month - 1) // 3) * 3 + 1
            period_start = now.replace(month=quarter_start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
            period_end = now
        else:  # year
            period_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            period_end = now

        # Get MRR breakdown
        mrr = await self.calculate_mrr(db, tenant_id, now)

        # Get churn analysis
        churn = await self.calculate_churn(db, tenant_id, period_start, period_end)

        # Get LTV
        ltv = await self._calculate_average_ltv(db, tenant_id)

        # Get active subscription count
        active_subs_query = select(func.count(Subscription.id)).where(
            and_(
                Subscription.tenant_id == tenant_id,
                Subscription.status == SubscriptionStatus.ACTIVE
            )
        )
        active_result = await db.execute(active_subs_query)
        active_subscriptions = active_result.scalar() or 0

        # Get total customers
        customers_query = select(func.count(Customer.id)).where(
            Customer.tenant_id == tenant_id
        )
        customers_result = await db.execute(customers_query)
        total_customers = customers_result.scalar() or 0

        # Get revenue this period
        revenue_query = select(func.sum(Payment.amount)).where(
            and_(
                Payment.tenant_id == tenant_id,
                Payment.status == PaymentStatus.COMPLETED,
                Payment.created_at >= period_start,
                Payment.created_at <= period_end
            )
        )
        revenue_result = await db.execute(revenue_query)
        period_revenue = revenue_result.scalar() or Decimal("0.00")

        # Get deferred revenue
        deferred_query = select(func.sum(RevenueSchedule.deferred_amount)).where(
            and_(
                RevenueSchedule.tenant_id == tenant_id,
                RevenueSchedule.status != "completed"
            )
        )
        deferred_result = await db.execute(deferred_query)
        deferred_revenue = deferred_result.scalar() or Decimal("0.00")

        return SaaSMetricsResponse(
            period=period,
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat(),
            mrr=mrr.current_mrr,
            arr=mrr.arr,
            mrr_growth_rate=mrr.mrr_growth_rate,
            active_subscriptions=active_subscriptions,
            total_customers=total_customers,
            arpu=ltv["arpu"],
            customer_churn_rate=churn.customer_churn_rate,
            revenue_churn_rate=churn.revenue_churn_rate,
            net_revenue_retention=churn.net_revenue_retention,
            ltv=ltv["estimated_avg_ltv"],
            ltv_cac_ratio=0,  # CAC not tracked yet
            period_revenue=float(period_revenue),
            deferred_revenue=float(deferred_revenue),
            mrr_breakdown={
                "new": mrr.new_mrr,
                "expansion": mrr.expansion_mrr,
                "contraction": mrr.contraction_mrr,
                "churned": mrr.churned_mrr,
                "reactivation": mrr.reactivation_mrr
            }
        )

    async def get_revenue_recognition_report(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, Any]:
        """
        Generate ASC 606 compliant revenue recognition report.
        """
        # Get recognized revenue in period
        recognized_query = select(func.sum(RevenueRecognition.amount)).where(
            and_(
                RevenueRecognition.tenant_id == tenant_id,
                RevenueRecognition.status == "recognized",
                RevenueRecognition.recognized_at >= period_start,
                RevenueRecognition.recognized_at <= period_end
            )
        )
        recognized_result = await db.execute(recognized_query)
        recognized_revenue = recognized_result.scalar() or Decimal("0.00")

        # Get deferred revenue at period end
        deferred_query = select(func.sum(RevenueSchedule.deferred_amount)).where(
            and_(
                RevenueSchedule.tenant_id == tenant_id,
                RevenueSchedule.status != "completed",
                RevenueSchedule.recognition_start <= period_end
            )
        )
        deferred_result = await db.execute(deferred_query)
        deferred_revenue = deferred_result.scalar() or Decimal("0.00")

        # Monthly breakdown
        monthly_breakdown = []
        current = period_start

        while current < period_end:
            month_end = min(
                (current.replace(day=1) + relativedelta(months=1)) - timedelta(days=1),
                period_end
            )

            month_query = select(func.sum(RevenueRecognition.amount)).where(
                and_(
                    RevenueRecognition.tenant_id == tenant_id,
                    RevenueRecognition.status == "recognized",
                    RevenueRecognition.recognized_at >= current,
                    RevenueRecognition.recognized_at <= month_end
                )
            )
            month_result = await db.execute(month_query)
            month_revenue = month_result.scalar() or Decimal("0.00")

            monthly_breakdown.append({
                "month": current.strftime("%Y-%m"),
                "recognized_revenue": float(month_revenue)
            })

            current = month_end + timedelta(days=1)

        return {
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "total_recognized_revenue": float(recognized_revenue),
            "total_deferred_revenue": float(deferred_revenue),
            "recognition_method": "straight_line",
            "compliance_standard": "ASC 606",
            "monthly_breakdown": monthly_breakdown
        }

    async def _to_schedule_response(
        self,
        db: AsyncSession,
        schedule: RevenueSchedule
    ) -> RevenueScheduleResponse:
        """Convert schedule to response model."""
        # Get recognition entries
        entries_query = select(RevenueRecognition).where(
            RevenueRecognition.schedule_id == schedule.id
        ).order_by(RevenueRecognition.period_start)

        entries_result = await db.execute(entries_query)
        entries = entries_result.scalars().all()

        recognition_entries = [
            RevenueRecognitionResponse(
                id=e.id,
                schedule_id=e.schedule_id,
                period_start=e.period_start,
                period_end=e.period_end,
                amount=e.amount,
                status=e.status,
                recognized_at=e.recognized_at
            )
            for e in entries
        ]

        return RevenueScheduleResponse(
            id=schedule.id,
            invoice_id=schedule.invoice_id,
            subscription_id=schedule.subscription_id,
            total_amount=schedule.total_amount,
            recognized_amount=schedule.recognized_amount,
            deferred_amount=schedule.deferred_amount,
            recognition_start=schedule.recognition_start,
            recognition_end=schedule.recognition_end,
            recognition_method=schedule.recognition_method,
            status=schedule.status,
            entries=recognition_entries,
            created_at=schedule.created_at
        )

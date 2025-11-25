"""
Invoice Service
EPIC-017: Revenue Infrastructure - Invoice Generation and Delivery

Handles invoice creation, line item management, PDF generation,
delivery via email, and credit memo processing.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from modules.revenue.models import (
    Invoice, InvoiceLineItem, CreditMemo, Subscription,
    Customer, UsageAggregate, BillingAuditLog, Plan,
    InvoiceStatus, UsageMetricType, AuditAction
)
from modules.revenue.schemas import (
    InvoiceCreate, InvoiceResponse, InvoiceLineItemCreate,
    InvoiceLineItemResponse, CreditMemoCreate, CreditMemoResponse,
    InvoiceListResponse
)


class InvoiceService:
    """
    Service for invoice generation, delivery, and management.

    Handles:
    - Automatic invoice generation from subscriptions
    - Usage-based billing line items
    - PDF generation and delivery
    - Credit memo processing
    - Invoice status tracking
    """

    def __init__(self):
        self.tax_rate = Decimal("0.00")  # Configure per jurisdiction

    async def generate_invoice(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        subscription_id: UUID,
        billing_period_start: datetime,
        billing_period_end: datetime,
        user_id: Optional[UUID] = None
    ) -> InvoiceResponse:
        """
        Generate an invoice for a subscription billing period.
        Includes base subscription charges and usage-based fees.
        """
        # Get subscription with plan details
        subscription_query = (
            select(Subscription)
            .options(selectinload(Subscription.plan))
            .where(
                and_(
                    Subscription.id == subscription_id,
                    Subscription.tenant_id == tenant_id
                )
            )
        )
        subscription_result = await db.execute(subscription_query)
        subscription = subscription_result.scalar_one_or_none()

        if not subscription:
            raise ValueError("Subscription not found")

        # Get customer
        customer_query = select(Customer).where(
            and_(
                Customer.id == subscription.customer_id,
                Customer.tenant_id == tenant_id
            )
        )
        customer_result = await db.execute(customer_query)
        customer = customer_result.scalar_one_or_none()

        if not customer:
            raise ValueError("Customer not found")

        # Generate invoice number
        invoice_number = await self._generate_invoice_number(db, tenant_id)

        # Create invoice
        invoice = Invoice(
            tenant_id=tenant_id,
            subscription_id=subscription_id,
            customer_id=customer.id,
            invoice_number=invoice_number,
            status=InvoiceStatus.DRAFT,
            billing_period_start=billing_period_start,
            billing_period_end=billing_period_end,
            issue_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=subscription.payment_terms_days or 30),
            subtotal=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            total_amount=Decimal("0.00"),
            currency=subscription.currency,
            billing_address=customer.billing_address
        )

        db.add(invoice)
        await db.flush()

        # Add subscription base charge line item
        plan = subscription.plan
        base_amount = plan.monthly_price if subscription.billing_cycle.value == "monthly" else plan.annual_price

        if base_amount and base_amount > 0:
            base_line_item = InvoiceLineItem(
                tenant_id=tenant_id,
                invoice_id=invoice.id,
                description=f"{plan.display_name} - {subscription.billing_cycle.value.title()} Subscription",
                quantity=1,
                unit_price=base_amount,
                amount=base_amount,
                line_type="subscription",
                period_start=billing_period_start,
                period_end=billing_period_end
            )
            db.add(base_line_item)

        # Add usage-based line items
        await self._add_usage_line_items(
            db, tenant_id, invoice.id, subscription,
            billing_period_start, billing_period_end
        )

        # Calculate totals
        await self._calculate_invoice_totals(db, invoice)

        await db.flush()

        # Log audit
        audit_log = BillingAuditLog(
            tenant_id=tenant_id,
            entity_type="invoice",
            entity_id=invoice.id,
            action=AuditAction.INVOICE_GENERATED,
            user_id=user_id,
            details={
                "invoice_number": invoice_number,
                "subscription_id": str(subscription_id),
                "total_amount": str(invoice.total_amount)
            }
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(invoice)

        return await self._to_invoice_response(invoice)

    async def _add_usage_line_items(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        invoice_id: UUID,
        subscription: Subscription,
        period_start: datetime,
        period_end: datetime
    ) -> None:
        """Add usage-based billing line items to an invoice."""
        # Get usage aggregates for the billing period
        usage_query = select(UsageAggregate).where(
            and_(
                UsageAggregate.tenant_id == tenant_id,
                UsageAggregate.subscription_id == subscription.id,
                UsageAggregate.period_start >= period_start,
                UsageAggregate.period_end <= period_end
            )
        )
        usage_result = await db.execute(usage_query)
        usage_records = usage_result.scalars().all()

        # Get plan pricing for usage metrics
        plan = subscription.plan
        usage_pricing = plan.usage_pricing or {}

        for usage in usage_records:
            metric_type = usage.metric_type.value

            if metric_type not in usage_pricing:
                continue

            pricing = usage_pricing[metric_type]
            included = pricing.get("included", 0)
            price_per_unit = Decimal(str(pricing.get("price_per_unit", 0)))

            # Calculate billable units (overage)
            billable_units = max(0, usage.total_count - included)

            if billable_units > 0:
                amount = Decimal(str(billable_units)) * price_per_unit

                line_item = InvoiceLineItem(
                    tenant_id=tenant_id,
                    invoice_id=invoice_id,
                    description=f"{self._format_metric_name(metric_type)} - {billable_units:,} units (overage)",
                    quantity=billable_units,
                    unit_price=price_per_unit,
                    amount=amount,
                    line_type="usage",
                    period_start=period_start,
                    period_end=period_end,
                    metadata={"metric_type": metric_type, "included": included}
                )
                db.add(line_item)

    async def _calculate_invoice_totals(
        self,
        db: AsyncSession,
        invoice: Invoice
    ) -> None:
        """Calculate and update invoice totals."""
        # Sum line items
        line_items_query = select(func.sum(InvoiceLineItem.amount)).where(
            InvoiceLineItem.invoice_id == invoice.id
        )
        result = await db.execute(line_items_query)
        subtotal = result.scalar() or Decimal("0.00")

        # Calculate tax
        tax_amount = subtotal * self.tax_rate

        # Apply credits
        credits_query = select(func.sum(CreditMemo.amount)).where(
            and_(
                CreditMemo.applied_to_invoice_id == invoice.id,
                CreditMemo.status == "applied"
            )
        )
        credits_result = await db.execute(credits_query)
        credit_amount = credits_result.scalar() or Decimal("0.00")

        # Calculate total
        total_amount = subtotal + tax_amount - credit_amount

        # Update invoice
        invoice.subtotal = subtotal
        invoice.tax_amount = tax_amount
        invoice.credit_applied = credit_amount
        invoice.total_amount = max(Decimal("0.00"), total_amount)

    async def finalize_invoice(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        invoice_id: UUID,
        user_id: Optional[UUID] = None
    ) -> InvoiceResponse:
        """Finalize a draft invoice and prepare for delivery."""
        invoice = await self._get_invoice(db, tenant_id, invoice_id)

        if invoice.status != InvoiceStatus.DRAFT:
            raise ValueError(f"Invoice cannot be finalized from status: {invoice.status}")

        invoice.status = InvoiceStatus.PENDING
        invoice.finalized_at = datetime.utcnow()

        # Generate PDF URL (placeholder - implement PDF generation)
        invoice.pdf_url = f"/api/v1/invoices/{invoice_id}/pdf"

        # Log audit
        audit_log = BillingAuditLog(
            tenant_id=tenant_id,
            entity_type="invoice",
            entity_id=invoice.id,
            action=AuditAction.SUBSCRIPTION_CHANGE,
            user_id=user_id,
            details={"action": "finalized", "invoice_number": invoice.invoice_number}
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(invoice)

        return await self._to_invoice_response(invoice)

    async def send_invoice(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        invoice_id: UUID,
        delivery_method: str = "email",
        user_id: Optional[UUID] = None
    ) -> InvoiceResponse:
        """Send invoice to customer via specified delivery method."""
        invoice = await self._get_invoice(db, tenant_id, invoice_id)

        if invoice.status == InvoiceStatus.DRAFT:
            raise ValueError("Invoice must be finalized before sending")

        # Get customer email
        customer_query = select(Customer).where(Customer.id == invoice.customer_id)
        customer_result = await db.execute(customer_query)
        customer = customer_result.scalar_one_or_none()

        if not customer:
            raise ValueError("Customer not found")

        # Send via delivery method (placeholder - implement actual delivery)
        if delivery_method == "email":
            await self._send_invoice_email(invoice, customer)

        invoice.sent_at = datetime.utcnow()
        invoice.delivery_method = delivery_method

        # Update status if pending
        if invoice.status == InvoiceStatus.PENDING:
            invoice.status = InvoiceStatus.SENT

        await db.commit()
        await db.refresh(invoice)

        return await self._to_invoice_response(invoice)

    async def _send_invoice_email(
        self,
        invoice: Invoice,
        customer: Customer
    ) -> None:
        """Send invoice via email (placeholder implementation)."""
        # TODO: Integrate with email service
        # - Generate PDF
        # - Send email with PDF attachment
        # - Track delivery status
        pass

    async def mark_as_paid(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        invoice_id: UUID,
        payment_id: UUID,
        user_id: Optional[UUID] = None
    ) -> InvoiceResponse:
        """Mark invoice as paid."""
        invoice = await self._get_invoice(db, tenant_id, invoice_id)

        invoice.status = InvoiceStatus.PAID
        invoice.payment_id = payment_id
        invoice.paid_at = datetime.utcnow()
        invoice.amount_paid = invoice.total_amount

        # Log audit
        audit_log = BillingAuditLog(
            tenant_id=tenant_id,
            entity_type="invoice",
            entity_id=invoice.id,
            action=AuditAction.PAYMENT_RECEIVED,
            user_id=user_id,
            details={
                "payment_id": str(payment_id),
                "amount": str(invoice.total_amount)
            }
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(invoice)

        return await self._to_invoice_response(invoice)

    async def create_credit_memo(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        data: CreditMemoCreate,
        user_id: Optional[UUID] = None
    ) -> CreditMemoResponse:
        """Create a credit memo for a customer."""
        # Verify customer exists
        customer_query = select(Customer).where(
            and_(
                Customer.id == data.customer_id,
                Customer.tenant_id == tenant_id
            )
        )
        customer_result = await db.execute(customer_query)
        customer = customer_result.scalar_one_or_none()

        if not customer:
            raise ValueError("Customer not found")

        # Generate credit memo number
        credit_number = await self._generate_credit_memo_number(db, tenant_id)

        credit_memo = CreditMemo(
            tenant_id=tenant_id,
            customer_id=data.customer_id,
            original_invoice_id=data.original_invoice_id,
            credit_number=credit_number,
            amount=data.amount,
            reason=data.reason,
            status="issued"
        )

        db.add(credit_memo)

        # Log audit
        audit_log = BillingAuditLog(
            tenant_id=tenant_id,
            entity_type="credit_memo",
            entity_id=credit_memo.id,
            action=AuditAction.INVOICE_GENERATED,
            user_id=user_id,
            details={
                "credit_number": credit_number,
                "amount": str(data.amount),
                "reason": data.reason
            }
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(credit_memo)

        return CreditMemoResponse(
            id=credit_memo.id,
            customer_id=credit_memo.customer_id,
            original_invoice_id=credit_memo.original_invoice_id,
            credit_number=credit_memo.credit_number,
            amount=credit_memo.amount,
            reason=credit_memo.reason,
            status=credit_memo.status,
            created_at=credit_memo.created_at
        )

    async def apply_credit_memo(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        credit_memo_id: UUID,
        invoice_id: UUID,
        user_id: Optional[UUID] = None
    ) -> CreditMemoResponse:
        """Apply a credit memo to an invoice."""
        # Get credit memo
        credit_query = select(CreditMemo).where(
            and_(
                CreditMemo.id == credit_memo_id,
                CreditMemo.tenant_id == tenant_id
            )
        )
        credit_result = await db.execute(credit_query)
        credit_memo = credit_result.scalar_one_or_none()

        if not credit_memo:
            raise ValueError("Credit memo not found")

        if credit_memo.status != "issued":
            raise ValueError("Credit memo has already been applied or voided")

        # Verify invoice
        invoice = await self._get_invoice(db, tenant_id, invoice_id)

        if invoice.customer_id != credit_memo.customer_id:
            raise ValueError("Credit memo and invoice must belong to the same customer")

        # Apply credit
        credit_memo.applied_to_invoice_id = invoice_id
        credit_memo.applied_at = datetime.utcnow()
        credit_memo.status = "applied"

        # Recalculate invoice totals
        await self._calculate_invoice_totals(db, invoice)

        await db.commit()
        await db.refresh(credit_memo)

        return CreditMemoResponse(
            id=credit_memo.id,
            customer_id=credit_memo.customer_id,
            original_invoice_id=credit_memo.original_invoice_id,
            applied_to_invoice_id=credit_memo.applied_to_invoice_id,
            credit_number=credit_memo.credit_number,
            amount=credit_memo.amount,
            reason=credit_memo.reason,
            status=credit_memo.status,
            applied_at=credit_memo.applied_at,
            created_at=credit_memo.created_at
        )

    async def get_invoice(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        invoice_id: UUID
    ) -> InvoiceResponse:
        """Get invoice by ID."""
        invoice = await self._get_invoice(db, tenant_id, invoice_id)
        return await self._to_invoice_response(invoice)

    async def list_invoices(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        customer_id: Optional[UUID] = None,
        subscription_id: Optional[UUID] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> InvoiceListResponse:
        """List invoices with filters."""
        query = select(Invoice).where(Invoice.tenant_id == tenant_id)

        if customer_id:
            query = query.where(Invoice.customer_id == customer_id)
        if subscription_id:
            query = query.where(Invoice.subscription_id == subscription_id)
        if status:
            query = query.where(Invoice.status == InvoiceStatus(status))

        # Count total
        count_query = select(func.count(Invoice.id)).where(Invoice.tenant_id == tenant_id)
        if customer_id:
            count_query = count_query.where(Invoice.customer_id == customer_id)
        if subscription_id:
            count_query = count_query.where(Invoice.subscription_id == subscription_id)
        if status:
            count_query = count_query.where(Invoice.status == InvoiceStatus(status))

        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0

        # Get invoices
        query = query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        invoices = result.scalars().all()

        invoice_responses = [await self._to_invoice_response(inv) for inv in invoices]

        return InvoiceListResponse(
            items=invoice_responses,
            total=total,
            skip=skip,
            limit=limit
        )

    async def get_overdue_invoices(
        self,
        db: AsyncSession,
        tenant_id: Optional[UUID] = None,
        days_overdue: int = 0
    ) -> List[InvoiceResponse]:
        """Get overdue invoices for dunning processing."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_overdue)

        query = select(Invoice).where(
            and_(
                Invoice.status.in_([InvoiceStatus.SENT, InvoiceStatus.PENDING]),
                Invoice.due_date < cutoff_date
            )
        )

        if tenant_id:
            query = query.where(Invoice.tenant_id == tenant_id)

        query = query.order_by(Invoice.due_date.asc())

        result = await db.execute(query)
        invoices = result.scalars().all()

        return [await self._to_invoice_response(inv) for inv in invoices]

    async def void_invoice(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        invoice_id: UUID,
        reason: str,
        user_id: Optional[UUID] = None
    ) -> InvoiceResponse:
        """Void an invoice."""
        invoice = await self._get_invoice(db, tenant_id, invoice_id)

        if invoice.status == InvoiceStatus.PAID:
            raise ValueError("Cannot void a paid invoice - create a credit memo instead")

        invoice.status = InvoiceStatus.VOID
        invoice.void_reason = reason
        invoice.voided_at = datetime.utcnow()

        # Log audit
        audit_log = BillingAuditLog(
            tenant_id=tenant_id,
            entity_type="invoice",
            entity_id=invoice.id,
            action=AuditAction.SUBSCRIPTION_CHANGE,
            user_id=user_id,
            details={"action": "voided", "reason": reason}
        )
        db.add(audit_log)

        await db.commit()
        await db.refresh(invoice)

        return await self._to_invoice_response(invoice)

    async def _get_invoice(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        invoice_id: UUID
    ) -> Invoice:
        """Get invoice by ID with validation."""
        query = select(Invoice).where(
            and_(
                Invoice.id == invoice_id,
                Invoice.tenant_id == tenant_id
            )
        )
        result = await db.execute(query)
        invoice = result.scalar_one_or_none()

        if not invoice:
            raise ValueError("Invoice not found")

        return invoice

    async def _generate_invoice_number(
        self,
        db: AsyncSession,
        tenant_id: UUID
    ) -> str:
        """Generate unique invoice number."""
        count_query = select(func.count(Invoice.id)).where(
            Invoice.tenant_id == tenant_id
        )
        result = await db.execute(count_query)
        count = result.scalar() or 0

        year = datetime.utcnow().year
        return f"INV-{year}-{str(count + 1).zfill(6)}"

    async def _generate_credit_memo_number(
        self,
        db: AsyncSession,
        tenant_id: UUID
    ) -> str:
        """Generate unique credit memo number."""
        count_query = select(func.count(CreditMemo.id)).where(
            CreditMemo.tenant_id == tenant_id
        )
        result = await db.execute(count_query)
        count = result.scalar() or 0

        year = datetime.utcnow().year
        return f"CM-{year}-{str(count + 1).zfill(6)}"

    def _format_metric_name(self, metric_type: str) -> str:
        """Format metric type for display."""
        names = {
            "ai_tokens": "AI Token Usage",
            "telehealth_minutes": "Telehealth Minutes",
            "sms_messages": "SMS Messages",
            "fax_pages": "Fax Pages",
            "api_calls": "API Calls",
            "storage_gb": "Storage (GB)",
            "active_patients": "Active Patients"
        }
        return names.get(metric_type, metric_type.replace("_", " ").title())

    async def _to_invoice_response(self, invoice: Invoice) -> InvoiceResponse:
        """Convert invoice to response model."""
        return InvoiceResponse(
            id=invoice.id,
            subscription_id=invoice.subscription_id,
            customer_id=invoice.customer_id,
            invoice_number=invoice.invoice_number,
            status=invoice.status.value,
            billing_period_start=invoice.billing_period_start,
            billing_period_end=invoice.billing_period_end,
            issue_date=invoice.issue_date,
            due_date=invoice.due_date,
            subtotal=invoice.subtotal,
            tax_amount=invoice.tax_amount,
            total_amount=invoice.total_amount,
            amount_paid=invoice.amount_paid,
            amount_due=invoice.total_amount - (invoice.amount_paid or Decimal("0.00")),
            currency=invoice.currency,
            pdf_url=invoice.pdf_url,
            paid_at=invoice.paid_at,
            created_at=invoice.created_at
        )

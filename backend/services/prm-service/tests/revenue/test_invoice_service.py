"""
Invoice Service Tests
EPIC-017: Unit tests for invoice generation and management
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from modules.revenue.services.invoice_service import InvoiceService
from modules.revenue.schemas import CreditMemoCreate
from modules.revenue.models import (
    Invoice, InvoiceLineItem, CreditMemo, Subscription,
    Customer, Plan, UsageAggregate,
    InvoiceStatus, SubscriptionStatus, BillingCycle, PlanType
)


@pytest.fixture
def invoice_service():
    return InvoiceService()


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.flush = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def mock_plan():
    plan = MagicMock(spec=Plan)
    plan.id = uuid4()
    plan.name = "Professional"
    plan.display_name = "Professional Plan"
    plan.monthly_price = Decimal("199.00")
    plan.annual_price = Decimal("1990.00")
    plan.usage_pricing = {
        "ai_tokens": {"included": 10000, "price_per_unit": Decimal("0.01")},
        "telehealth_minutes": {"included": 100, "price_per_unit": Decimal("0.50")}
    }
    return plan


@pytest.fixture
def mock_subscription(mock_plan):
    sub = MagicMock(spec=Subscription)
    sub.id = uuid4()
    sub.tenant_id = uuid4()
    sub.customer_id = uuid4()
    sub.plan_id = mock_plan.id
    sub.plan = mock_plan
    sub.status = SubscriptionStatus.ACTIVE
    sub.billing_cycle = BillingCycle.MONTHLY
    sub.currency = "USD"
    sub.payment_terms_days = 30
    sub.current_period_start = datetime.utcnow()
    sub.current_period_end = datetime.utcnow() + timedelta(days=30)
    return sub


@pytest.fixture
def mock_customer():
    customer = MagicMock(spec=Customer)
    customer.id = uuid4()
    customer.tenant_id = uuid4()
    customer.name = "Test Healthcare Inc"
    customer.email = "billing@testhealthcare.com"
    customer.billing_address = {
        "line1": "123 Medical Ave",
        "city": "Healthcare City",
        "state": "CA",
        "postal_code": "90210",
        "country": "US"
    }
    return customer


@pytest.fixture
def mock_invoice(mock_subscription, mock_customer):
    invoice = MagicMock(spec=Invoice)
    invoice.id = uuid4()
    invoice.tenant_id = mock_subscription.tenant_id
    invoice.subscription_id = mock_subscription.id
    invoice.customer_id = mock_customer.id
    invoice.invoice_number = "INV-2024-000001"
    invoice.status = InvoiceStatus.DRAFT
    invoice.billing_period_start = datetime.utcnow()
    invoice.billing_period_end = datetime.utcnow() + timedelta(days=30)
    invoice.issue_date = datetime.utcnow()
    invoice.due_date = datetime.utcnow() + timedelta(days=30)
    invoice.subtotal = Decimal("199.00")
    invoice.tax_amount = Decimal("0.00")
    invoice.total_amount = Decimal("199.00")
    invoice.amount_paid = Decimal("0.00")
    invoice.currency = "USD"
    invoice.created_at = datetime.utcnow()
    return invoice


class TestInvoiceGeneration:
    """Tests for invoice generation"""

    @pytest.mark.asyncio
    async def test_generate_invoice_basic(
        self, invoice_service, mock_db, mock_subscription, mock_customer
    ):
        """Test basic invoice generation"""
        tenant_id = mock_subscription.tenant_id
        billing_start = datetime.utcnow()
        billing_end = datetime.utcnow() + timedelta(days=30)

        # Mock subscription query
        sub_result = AsyncMock()
        sub_result.scalar_one_or_none.return_value = mock_subscription

        # Mock customer query
        cust_result = AsyncMock()
        cust_result.scalar_one_or_none.return_value = mock_customer

        # Mock invoice count for number generation
        count_result = AsyncMock()
        count_result.scalar.return_value = 0

        # Setup execute to return different mocks for different queries
        mock_db.execute.side_effect = [
            sub_result, cust_result, count_result, count_result, count_result
        ]

        with patch.object(invoice_service, '_add_usage_line_items', new_callable=AsyncMock):
            with patch.object(invoice_service, '_calculate_invoice_totals', new_callable=AsyncMock):
                result = await invoice_service.generate_invoice(
                    mock_db, tenant_id, mock_subscription.id,
                    billing_start, billing_end
                )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_generate_invoice_subscription_not_found(
        self, invoice_service, mock_db
    ):
        """Test invoice generation with non-existent subscription"""
        tenant_id = uuid4()
        subscription_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Subscription not found"):
            await invoice_service.generate_invoice(
                mock_db, tenant_id, subscription_id,
                datetime.utcnow(), datetime.utcnow() + timedelta(days=30)
            )

    @pytest.mark.asyncio
    async def test_generate_invoice_number_format(
        self, invoice_service, mock_db
    ):
        """Test invoice number generation format"""
        tenant_id = uuid4()

        # Mock count query
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 5

        mock_db.execute.return_value = mock_result

        invoice_number = await invoice_service._generate_invoice_number(
            mock_db, tenant_id
        )

        current_year = datetime.utcnow().year
        assert invoice_number.startswith(f"INV-{current_year}-")
        assert invoice_number == f"INV-{current_year}-000006"


class TestInvoiceStatusTransitions:
    """Tests for invoice status transitions"""

    @pytest.mark.asyncio
    async def test_finalize_draft_invoice(
        self, invoice_service, mock_db, mock_invoice
    ):
        """Test finalizing a draft invoice"""
        tenant_id = mock_invoice.tenant_id
        mock_invoice.status = InvoiceStatus.DRAFT

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_invoice
        mock_db.execute.return_value = mock_result

        result = await invoice_service.finalize_invoice(
            mock_db, tenant_id, mock_invoice.id
        )

        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_finalize_non_draft_fails(
        self, invoice_service, mock_db, mock_invoice
    ):
        """Test that finalizing non-draft invoice fails"""
        tenant_id = mock_invoice.tenant_id
        mock_invoice.status = InvoiceStatus.PAID

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_invoice
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="cannot be finalized"):
            await invoice_service.finalize_invoice(
                mock_db, tenant_id, mock_invoice.id
            )

    @pytest.mark.asyncio
    async def test_send_invoice(
        self, invoice_service, mock_db, mock_invoice, mock_customer
    ):
        """Test sending an invoice"""
        tenant_id = mock_invoice.tenant_id
        mock_invoice.status = InvoiceStatus.PENDING

        # Mock invoice query
        inv_result = AsyncMock()
        inv_result.scalar_one_or_none.return_value = mock_invoice

        # Mock customer query
        cust_result = AsyncMock()
        cust_result.scalar_one_or_none.return_value = mock_customer

        mock_db.execute.side_effect = [inv_result, cust_result]

        result = await invoice_service.send_invoice(
            mock_db, tenant_id, mock_invoice.id, "email"
        )

        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_send_draft_invoice_fails(
        self, invoice_service, mock_db, mock_invoice
    ):
        """Test that sending a draft invoice fails"""
        tenant_id = mock_invoice.tenant_id
        mock_invoice.status = InvoiceStatus.DRAFT

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_invoice
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="must be finalized"):
            await invoice_service.send_invoice(
                mock_db, tenant_id, mock_invoice.id
            )

    @pytest.mark.asyncio
    async def test_mark_invoice_paid(
        self, invoice_service, mock_db, mock_invoice
    ):
        """Test marking an invoice as paid"""
        tenant_id = mock_invoice.tenant_id
        payment_id = uuid4()
        mock_invoice.status = InvoiceStatus.SENT

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_invoice
        mock_db.execute.return_value = mock_result

        result = await invoice_service.mark_as_paid(
            mock_db, tenant_id, mock_invoice.id, payment_id
        )

        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_void_unpaid_invoice(
        self, invoice_service, mock_db, mock_invoice
    ):
        """Test voiding an unpaid invoice"""
        tenant_id = mock_invoice.tenant_id
        mock_invoice.status = InvoiceStatus.SENT

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_invoice
        mock_db.execute.return_value = mock_result

        result = await invoice_service.void_invoice(
            mock_db, tenant_id, mock_invoice.id, "Customer requested"
        )

        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_void_paid_invoice_fails(
        self, invoice_service, mock_db, mock_invoice
    ):
        """Test that voiding a paid invoice fails"""
        tenant_id = mock_invoice.tenant_id
        mock_invoice.status = InvoiceStatus.PAID

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_invoice
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Cannot void a paid invoice"):
            await invoice_service.void_invoice(
                mock_db, tenant_id, mock_invoice.id, "Mistake"
            )


class TestCreditMemos:
    """Tests for credit memo management"""

    @pytest.mark.asyncio
    async def test_create_credit_memo(
        self, invoice_service, mock_db, mock_customer
    ):
        """Test creating a credit memo"""
        tenant_id = mock_customer.tenant_id

        data = CreditMemoCreate(
            customer_id=mock_customer.id,
            amount=Decimal("50.00"),
            reason="service_issue"
        )

        # Mock customer query
        cust_result = AsyncMock()
        cust_result.scalar_one_or_none.return_value = mock_customer

        # Mock count for credit memo number
        count_result = AsyncMock()
        count_result.scalar.return_value = 0

        mock_db.execute.side_effect = [cust_result, count_result]

        result = await invoice_service.create_credit_memo(
            mock_db, tenant_id, data
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_create_credit_memo_customer_not_found(
        self, invoice_service, mock_db
    ):
        """Test creating credit memo for non-existent customer fails"""
        tenant_id = uuid4()

        data = CreditMemoCreate(
            customer_id=uuid4(),
            amount=Decimal("50.00"),
            reason="billing_error"
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Customer not found"):
            await invoice_service.create_credit_memo(
                mock_db, tenant_id, data
            )

    @pytest.mark.asyncio
    async def test_apply_credit_memo(
        self, invoice_service, mock_db, mock_invoice, mock_customer
    ):
        """Test applying credit memo to invoice"""
        tenant_id = mock_invoice.tenant_id

        mock_credit_memo = MagicMock(spec=CreditMemo)
        mock_credit_memo.id = uuid4()
        mock_credit_memo.customer_id = mock_customer.id
        mock_credit_memo.amount = Decimal("50.00")
        mock_credit_memo.status = "issued"

        mock_invoice.customer_id = mock_customer.id

        # Mock credit memo query
        credit_result = AsyncMock()
        credit_result.scalar_one_or_none.return_value = mock_credit_memo

        # Mock invoice query
        inv_result = AsyncMock()
        inv_result.scalar_one_or_none.return_value = mock_invoice

        # Mock line items sum
        sum_result = AsyncMock()
        sum_result.scalar.return_value = Decimal("199.00")

        # Mock applied credits sum
        credit_sum_result = AsyncMock()
        credit_sum_result.scalar.return_value = Decimal("50.00")

        mock_db.execute.side_effect = [
            credit_result, inv_result, sum_result, credit_sum_result
        ]

        result = await invoice_service.apply_credit_memo(
            mock_db, tenant_id, mock_credit_memo.id, mock_invoice.id
        )

        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_apply_already_applied_credit_memo_fails(
        self, invoice_service, mock_db
    ):
        """Test that applying already-applied credit memo fails"""
        tenant_id = uuid4()

        mock_credit_memo = MagicMock(spec=CreditMemo)
        mock_credit_memo.id = uuid4()
        mock_credit_memo.status = "applied"

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_credit_memo
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="already been applied"):
            await invoice_service.apply_credit_memo(
                mock_db, tenant_id, mock_credit_memo.id, uuid4()
            )


class TestInvoiceListing:
    """Tests for invoice listing and retrieval"""

    @pytest.mark.asyncio
    async def test_list_invoices_all(
        self, invoice_service, mock_db, mock_invoice
    ):
        """Test listing all invoices"""
        tenant_id = mock_invoice.tenant_id

        # Mock count query
        count_result = AsyncMock()
        count_result.scalar.return_value = 1

        # Mock invoices query
        list_result = AsyncMock()
        list_result.scalars.return_value.all.return_value = [mock_invoice]

        mock_db.execute.side_effect = [count_result, list_result]

        result = await invoice_service.list_invoices(
            mock_db, tenant_id
        )

        assert result.total == 1
        assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_list_invoices_by_status(
        self, invoice_service, mock_db, mock_invoice
    ):
        """Test listing invoices filtered by status"""
        tenant_id = mock_invoice.tenant_id

        count_result = AsyncMock()
        count_result.scalar.return_value = 1

        list_result = AsyncMock()
        list_result.scalars.return_value.all.return_value = [mock_invoice]

        mock_db.execute.side_effect = [count_result, list_result]

        result = await invoice_service.list_invoices(
            mock_db, tenant_id, status="draft"
        )

        assert result.total == 1

    @pytest.mark.asyncio
    async def test_get_overdue_invoices(
        self, invoice_service, mock_db, mock_invoice
    ):
        """Test getting overdue invoices"""
        mock_invoice.status = InvoiceStatus.SENT
        mock_invoice.due_date = datetime.utcnow() - timedelta(days=10)

        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = [mock_invoice]
        mock_db.execute.return_value = mock_result

        result = await invoice_service.get_overdue_invoices(
            mock_db, days_overdue=5
        )

        assert len(result) == 1


class TestInvoiceTotals:
    """Tests for invoice total calculation"""

    @pytest.mark.asyncio
    async def test_calculate_invoice_totals(
        self, invoice_service, mock_db, mock_invoice
    ):
        """Test calculating invoice totals"""
        # Mock line items sum
        sum_result = AsyncMock()
        sum_result.scalar.return_value = Decimal("249.00")

        # Mock credits sum
        credit_result = AsyncMock()
        credit_result.scalar.return_value = Decimal("0.00")

        mock_db.execute.side_effect = [sum_result, credit_result]

        await invoice_service._calculate_invoice_totals(mock_db, mock_invoice)

        assert mock_invoice.subtotal == Decimal("249.00")
        assert mock_invoice.total_amount >= Decimal("0.00")

    @pytest.mark.asyncio
    async def test_calculate_totals_with_credits(
        self, invoice_service, mock_db, mock_invoice
    ):
        """Test calculating totals with applied credits"""
        # Mock line items sum
        sum_result = AsyncMock()
        sum_result.scalar.return_value = Decimal("249.00")

        # Mock credits sum
        credit_result = AsyncMock()
        credit_result.scalar.return_value = Decimal("50.00")

        mock_db.execute.side_effect = [sum_result, credit_result]

        await invoice_service._calculate_invoice_totals(mock_db, mock_invoice)

        assert mock_invoice.subtotal == Decimal("249.00")
        assert mock_invoice.credit_applied == Decimal("50.00")
        # Total should be reduced by credits
        assert mock_invoice.total_amount == Decimal("199.00")

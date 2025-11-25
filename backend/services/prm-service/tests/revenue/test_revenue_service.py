"""
Revenue Service Tests
EPIC-017: Unit tests for revenue recognition and SaaS metrics
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from modules.revenue.services.revenue_service import RevenueService
from modules.revenue.models import (
    Invoice, Subscription, Customer, Payment, Plan,
    RevenueSchedule, RevenueRecognition,
    InvoiceStatus, SubscriptionStatus, PaymentStatus
)


@pytest.fixture
def revenue_service():
    return RevenueService()


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
def mock_invoice():
    invoice = MagicMock(spec=Invoice)
    invoice.id = uuid4()
    invoice.tenant_id = uuid4()
    invoice.subscription_id = uuid4()
    invoice.total_amount = Decimal("1200.00")
    invoice.billing_period_start = datetime.utcnow()
    invoice.billing_period_end = datetime.utcnow() + timedelta(days=365)
    return invoice


@pytest.fixture
def mock_subscription():
    sub = MagicMock(spec=Subscription)
    sub.id = uuid4()
    sub.tenant_id = uuid4()
    sub.status = SubscriptionStatus.ACTIVE
    sub.mrr_value = Decimal("199.00")
    sub.created_at = datetime.utcnow() - timedelta(days=30)
    sub.activated_at = datetime.utcnow() - timedelta(days=30)
    sub.canceled_at = None
    return sub


@pytest.fixture
def mock_revenue_schedule(mock_invoice):
    schedule = MagicMock(spec=RevenueSchedule)
    schedule.id = uuid4()
    schedule.tenant_id = mock_invoice.tenant_id
    schedule.invoice_id = mock_invoice.id
    schedule.subscription_id = mock_invoice.subscription_id
    schedule.total_amount = Decimal("1200.00")
    schedule.recognized_amount = Decimal("0.00")
    schedule.deferred_amount = Decimal("1200.00")
    schedule.recognition_start = datetime.utcnow()
    schedule.recognition_end = datetime.utcnow() + timedelta(days=365)
    schedule.recognition_method = "straight_line"
    schedule.status = "pending"
    schedule.created_at = datetime.utcnow()
    return schedule


class TestRevenueSchedule:
    """Tests for revenue recognition schedule creation"""

    @pytest.mark.asyncio
    async def test_create_revenue_schedule(
        self, revenue_service, mock_db, mock_invoice
    ):
        """Test creating a revenue recognition schedule"""
        tenant_id = mock_invoice.tenant_id

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_invoice
        mock_db.execute.return_value = mock_result

        with patch.object(revenue_service, '_create_recognition_entries', new_callable=AsyncMock):
            result = await revenue_service.create_revenue_schedule(
                mock_db, tenant_id, mock_invoice.id
            )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_create_schedule_invoice_not_found(
        self, revenue_service, mock_db
    ):
        """Test creating schedule with non-existent invoice fails"""
        tenant_id = uuid4()
        invoice_id = uuid4()

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Invoice not found"):
            await revenue_service.create_revenue_schedule(
                mock_db, tenant_id, invoice_id
            )

    @pytest.mark.asyncio
    async def test_create_schedule_invalid_period(
        self, revenue_service, mock_db, mock_invoice
    ):
        """Test creating schedule with invalid billing period fails"""
        tenant_id = mock_invoice.tenant_id
        mock_invoice.billing_period_start = None
        mock_invoice.billing_period_end = None

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_invoice
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="billing period"):
            await revenue_service.create_revenue_schedule(
                mock_db, tenant_id, mock_invoice.id
            )


class TestRevenueRecognition:
    """Tests for revenue recognition processing"""

    @pytest.mark.asyncio
    async def test_process_recognition_entries(
        self, revenue_service, mock_db, mock_revenue_schedule
    ):
        """Test processing pending revenue recognition entries"""
        mock_entry = MagicMock(spec=RevenueRecognition)
        mock_entry.id = uuid4()
        mock_entry.schedule_id = mock_revenue_schedule.id
        mock_entry.amount = Decimal("100.00")
        mock_entry.status = "pending"
        mock_entry.period_end = datetime.utcnow() - timedelta(days=1)

        # Mock pending entries query
        entries_result = AsyncMock()
        entries_result.scalars.return_value.all.return_value = [mock_entry]

        # Mock schedule query
        schedule_result = AsyncMock()
        schedule_result.scalar_one_or_none.return_value = mock_revenue_schedule

        mock_db.execute.side_effect = [entries_result, schedule_result]

        result = await revenue_service.process_revenue_recognition(mock_db)

        assert result["processed"] == 1
        assert result["recognized_amount"] == 100.0
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_process_recognition_no_pending(
        self, revenue_service, mock_db
    ):
        """Test processing with no pending entries"""
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        result = await revenue_service.process_revenue_recognition(mock_db)

        assert result["processed"] == 0
        assert result["recognized_amount"] == 0


class TestMRRCalculation:
    """Tests for MRR calculation"""

    @pytest.mark.asyncio
    async def test_calculate_mrr_basic(
        self, revenue_service, mock_db, mock_subscription
    ):
        """Test basic MRR calculation"""
        tenant_id = mock_subscription.tenant_id

        # Mock active subscriptions
        sub_result = AsyncMock()
        sub_result.scalars.return_value.all.return_value = [mock_subscription]

        # Mock various MRR component queries
        new_mrr_result = AsyncMock()
        new_mrr_result.scalar.return_value = Decimal("199.00")

        churned_mrr_result = AsyncMock()
        churned_mrr_result.scalar.return_value = Decimal("0.00")

        mock_db.execute.side_effect = [
            sub_result, new_mrr_result, churned_mrr_result
        ]

        result = await revenue_service.calculate_mrr(mock_db, tenant_id)

        assert result.current_mrr == 199.0
        assert result.arr == 199.0 * 12

    @pytest.mark.asyncio
    async def test_calculate_new_mrr(
        self, revenue_service, mock_db
    ):
        """Test calculating MRR from new subscriptions"""
        tenant_id = uuid4()
        as_of_date = datetime.utcnow()

        mock_result = AsyncMock()
        mock_result.scalar.return_value = Decimal("599.00")
        mock_db.execute.return_value = mock_result

        result = await revenue_service._calculate_new_mrr(
            mock_db, tenant_id, as_of_date
        )

        assert result == Decimal("599.00")

    @pytest.mark.asyncio
    async def test_calculate_churned_mrr(
        self, revenue_service, mock_db
    ):
        """Test calculating churned MRR"""
        tenant_id = uuid4()
        as_of_date = datetime.utcnow()

        mock_result = AsyncMock()
        mock_result.scalar.return_value = Decimal("99.00")
        mock_db.execute.return_value = mock_result

        result = await revenue_service._calculate_churned_mrr(
            mock_db, tenant_id, as_of_date
        )

        assert result == Decimal("99.00")


class TestChurnAnalysis:
    """Tests for churn analysis"""

    @pytest.mark.asyncio
    async def test_calculate_churn(
        self, revenue_service, mock_db
    ):
        """Test churn calculation"""
        tenant_id = uuid4()
        period_start = datetime.utcnow() - timedelta(days=30)
        period_end = datetime.utcnow()

        # Mock subscriptions at start
        start_count_result = AsyncMock()
        start_count_result.scalar.return_value = 100

        # Mock churned count
        churned_count_result = AsyncMock()
        churned_count_result.scalar.return_value = 5

        # Mock MRR at start
        mrr_start_result = AsyncMock()
        mrr_start_result.scalar.return_value = Decimal("19900.00")

        # Mock churned MRR
        churned_mrr_result = AsyncMock()
        churned_mrr_result.scalar.return_value = Decimal("995.00")

        # Mock churn reasons
        reasons_result = AsyncMock()
        reasons_result.all.return_value = [("too_expensive", 3), ("competitor", 2)]

        mock_db.execute.side_effect = [
            start_count_result, churned_count_result,
            mrr_start_result, churned_mrr_result, reasons_result
        ]

        result = await revenue_service.calculate_churn(
            mock_db, tenant_id, period_start, period_end
        )

        assert result.subscriptions_at_start == 100
        assert result.churned_subscriptions == 5
        assert result.customer_churn_rate == 5.0  # 5/100 * 100

    @pytest.mark.asyncio
    async def test_calculate_churn_no_subs(
        self, revenue_service, mock_db
    ):
        """Test churn calculation with no subscriptions"""
        tenant_id = uuid4()
        period_start = datetime.utcnow() - timedelta(days=30)
        period_end = datetime.utcnow()

        # Mock zero subscriptions
        zero_result = AsyncMock()
        zero_result.scalar.return_value = 0

        reasons_result = AsyncMock()
        reasons_result.all.return_value = []

        mock_db.execute.side_effect = [
            zero_result, zero_result, zero_result, zero_result, reasons_result
        ]

        result = await revenue_service.calculate_churn(
            mock_db, tenant_id, period_start, period_end
        )

        assert result.subscriptions_at_start == 0
        assert result.customer_churn_rate == 0


class TestLTVCalculation:
    """Tests for LTV calculation"""

    @pytest.mark.asyncio
    async def test_calculate_customer_ltv(
        self, revenue_service, mock_db
    ):
        """Test calculating LTV for a specific customer"""
        tenant_id = uuid4()
        customer_id = uuid4()

        # Mock customer
        mock_customer = MagicMock(spec=Customer)
        mock_customer.id = customer_id
        mock_customer.created_at = datetime.utcnow() - timedelta(days=180)

        # Mock total payments
        payments_result = AsyncMock()
        payments_result.scalar.return_value = Decimal("1194.00")

        # Mock customer query
        customer_result = AsyncMock()
        customer_result.scalar_one_or_none.return_value = mock_customer

        # Mock current MRR
        mrr_result = AsyncMock()
        mrr_result.scalar.return_value = Decimal("199.00")

        mock_db.execute.side_effect = [
            payments_result, customer_result, mrr_result
        ]

        result = await revenue_service._calculate_customer_ltv(
            mock_db, tenant_id, customer_id
        )

        assert result["customer_id"] == str(customer_id)
        assert result["total_revenue"] == 1194.0
        assert result["current_mrr"] == 199.0

    @pytest.mark.asyncio
    async def test_calculate_average_ltv(
        self, revenue_service, mock_db
    ):
        """Test calculating average LTV across all customers"""
        tenant_id = uuid4()

        # Mock customer count
        count_result = AsyncMock()
        count_result.scalar.return_value = 50

        # Mock total revenue
        revenue_result = AsyncMock()
        revenue_result.scalar.return_value = Decimal("100000.00")

        # Mock total MRR
        mrr_result = AsyncMock()
        mrr_result.scalar.return_value = Decimal("9950.00")

        mock_db.execute.side_effect = [
            count_result, revenue_result, mrr_result
        ]

        result = await revenue_service._calculate_average_ltv(mock_db, tenant_id)

        assert result["customer_count"] == 50
        assert result["total_revenue"] == 100000.0
        assert result["arpu"] == 199.0  # 9950/50


class TestSaaSMetrics:
    """Tests for comprehensive SaaS metrics"""

    @pytest.mark.asyncio
    async def test_get_saas_metrics(
        self, revenue_service, mock_db, mock_subscription
    ):
        """Test getting comprehensive SaaS metrics"""
        tenant_id = mock_subscription.tenant_id

        with patch.object(revenue_service, 'calculate_mrr', new_callable=AsyncMock) as mock_mrr:
            with patch.object(revenue_service, 'calculate_churn', new_callable=AsyncMock) as mock_churn:
                with patch.object(revenue_service, '_calculate_average_ltv', new_callable=AsyncMock) as mock_ltv:
                    # Setup mock returns
                    mock_mrr.return_value = MagicMock(
                        current_mrr=19900.0, arr=238800.0,
                        new_mrr=1000.0, expansion_mrr=500.0,
                        contraction_mrr=200.0, churned_mrr=300.0,
                        reactivation_mrr=100.0, net_mrr_change=1100.0,
                        mrr_growth_rate=5.5
                    )
                    mock_churn.return_value = MagicMock(
                        customer_churn_rate=2.0,
                        revenue_churn_rate=1.5,
                        net_revenue_retention=105.0
                    )
                    mock_ltv.return_value = {
                        "arpu": 199.0,
                        "estimated_avg_ltv": 4776.0
                    }

                    # Mock subscription count
                    sub_count_result = AsyncMock()
                    sub_count_result.scalar.return_value = 100

                    # Mock customer count
                    cust_count_result = AsyncMock()
                    cust_count_result.scalar.return_value = 100

                    # Mock period revenue
                    revenue_result = AsyncMock()
                    revenue_result.scalar.return_value = Decimal("20000.00")

                    # Mock deferred revenue
                    deferred_result = AsyncMock()
                    deferred_result.scalar.return_value = Decimal("50000.00")

                    mock_db.execute.side_effect = [
                        sub_count_result, cust_count_result,
                        revenue_result, deferred_result
                    ]

                    result = await revenue_service.get_saas_metrics(
                        mock_db, tenant_id, "month"
                    )

                    assert result.mrr == 19900.0
                    assert result.arr == 238800.0
                    assert result.active_subscriptions == 100


class TestRevenueReport:
    """Tests for revenue recognition report"""

    @pytest.mark.asyncio
    async def test_get_recognition_report(
        self, revenue_service, mock_db
    ):
        """Test getting revenue recognition report"""
        tenant_id = uuid4()
        period_start = datetime.utcnow() - timedelta(days=30)
        period_end = datetime.utcnow()

        # Mock recognized revenue
        recognized_result = AsyncMock()
        recognized_result.scalar.return_value = Decimal("15000.00")

        # Mock deferred revenue
        deferred_result = AsyncMock()
        deferred_result.scalar.return_value = Decimal("45000.00")

        # Mock monthly breakdown (for each month in period)
        monthly_result = AsyncMock()
        monthly_result.scalar.return_value = Decimal("15000.00")

        mock_db.execute.side_effect = [
            recognized_result, deferred_result, monthly_result
        ]

        result = await revenue_service.get_revenue_recognition_report(
            mock_db, tenant_id, period_start, period_end
        )

        assert result["total_recognized_revenue"] == 15000.0
        assert result["total_deferred_revenue"] == 45000.0
        assert result["compliance_standard"] == "ASC 606"
        assert "monthly_breakdown" in result

"""
Subscription Service Tests
EPIC-017: Unit tests for subscription lifecycle management
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from modules.revenue.services.subscription_service import SubscriptionService
from modules.revenue.schemas import (
    SubscriptionCreate, SubscriptionUpdate, SubscriptionChangePlan,
    SubscriptionCancel, BillingCycleSchema
)
from modules.revenue.models import (
    Plan, Subscription, SubscriptionChange, Entitlement,
    PlanType, BillingCycle, SubscriptionStatus
)


@pytest.fixture
def subscription_service():
    return SubscriptionService()


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
    plan.slug = "professional"
    plan.plan_type = PlanType.PROFESSIONAL
    plan.monthly_price = Decimal("199.00")
    plan.annual_price = Decimal("1990.00")
    plan.trial_enabled = True
    plan.trial_days = 14
    plan.is_active = True
    plan.features = {"patients": 500, "providers": 10}
    plan.limits = {"patients": 500, "providers": 10}
    plan.usage_pricing = {}
    return plan


@pytest.fixture
def mock_subscription(mock_plan):
    sub = MagicMock(spec=Subscription)
    sub.id = uuid4()
    sub.tenant_id = uuid4()
    sub.plan_id = mock_plan.id
    sub.status = SubscriptionStatus.ACTIVE
    sub.billing_cycle = BillingCycle.MONTHLY
    sub.quantity = 1
    sub.provider_count = 1
    sub.facility_count = 1
    sub.unit_price = Decimal("199.00")
    sub.discount_percent = Decimal("0")
    sub.mrr_value = Decimal("199.00")
    sub.current_period_start = datetime.utcnow()
    sub.current_period_end = datetime.utcnow() + timedelta(days=30)
    sub.trial_start = None
    sub.trial_end = None
    sub.cancel_at_period_end = False
    sub.canceled_at = None
    sub.created_at = datetime.utcnow()
    sub.plan = mock_plan
    return sub


class TestSubscriptionService:
    """Tests for SubscriptionService"""

    @pytest.mark.asyncio
    async def test_create_subscription_with_trial(
        self, subscription_service, mock_db, mock_plan
    ):
        """Test creating a subscription with trial period"""
        tenant_id = uuid4()
        user_id = uuid4()

        data = SubscriptionCreate(
            plan_id=mock_plan.id,
            billing_cycle=BillingCycleSchema.MONTHLY,
            quantity=1,
            provider_count=1,
            facility_count=1,
            start_trial=True
        )

        # Mock plan query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_plan
        mock_db.execute.return_value = mock_result

        with patch.object(subscription_service, '_create_entitlements', new_callable=AsyncMock):
            result = await subscription_service.create_subscription(
                mock_db, tenant_id, data, user_id
            )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_create_subscription_without_trial(
        self, subscription_service, mock_db, mock_plan
    ):
        """Test creating a subscription without trial"""
        tenant_id = uuid4()
        user_id = uuid4()

        # Disable trial on plan
        mock_plan.trial_enabled = False

        data = SubscriptionCreate(
            plan_id=mock_plan.id,
            billing_cycle=BillingCycleSchema.MONTHLY,
            quantity=1,
            start_trial=False
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_plan
        mock_db.execute.return_value = mock_result

        with patch.object(subscription_service, '_create_entitlements', new_callable=AsyncMock):
            result = await subscription_service.create_subscription(
                mock_db, tenant_id, data, user_id
            )

        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_create_subscription_inactive_plan_fails(
        self, subscription_service, mock_db, mock_plan
    ):
        """Test that creating subscription with inactive plan fails"""
        tenant_id = uuid4()
        mock_plan.is_active = False

        data = SubscriptionCreate(
            plan_id=mock_plan.id,
            billing_cycle=BillingCycleSchema.MONTHLY
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_plan
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Plan is not active"):
            await subscription_service.create_subscription(
                mock_db, tenant_id, data, None
            )

    @pytest.mark.asyncio
    async def test_create_subscription_plan_not_found(
        self, subscription_service, mock_db
    ):
        """Test that creating subscription with non-existent plan fails"""
        tenant_id = uuid4()

        data = SubscriptionCreate(
            plan_id=uuid4(),
            billing_cycle=BillingCycleSchema.MONTHLY
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Plan not found"):
            await subscription_service.create_subscription(
                mock_db, tenant_id, data, None
            )

    @pytest.mark.asyncio
    async def test_cancel_subscription_at_period_end(
        self, subscription_service, mock_db, mock_subscription
    ):
        """Test canceling subscription at period end"""
        tenant_id = mock_subscription.tenant_id
        user_id = uuid4()

        data = SubscriptionCancel(
            reason="Too expensive",
            cancel_at_period_end=True
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_subscription
        mock_db.execute.return_value = mock_result

        result = await subscription_service.cancel_subscription(
            mock_db, mock_subscription.id, tenant_id, data, user_id
        )

        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_cancel_subscription_immediately(
        self, subscription_service, mock_db, mock_subscription
    ):
        """Test canceling subscription immediately"""
        tenant_id = mock_subscription.tenant_id
        user_id = uuid4()

        data = SubscriptionCancel(
            reason="Switching providers",
            cancel_at_period_end=False
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_subscription
        mock_db.execute.return_value = mock_result

        result = await subscription_service.cancel_subscription(
            mock_db, mock_subscription.id, tenant_id, data, user_id
        )

        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_reactivate_canceled_subscription(
        self, subscription_service, mock_db, mock_subscription
    ):
        """Test reactivating a subscription scheduled for cancellation"""
        tenant_id = mock_subscription.tenant_id
        user_id = uuid4()

        mock_subscription.cancel_at_period_end = True
        mock_subscription.canceled_at = datetime.utcnow()

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_subscription
        mock_db.execute.return_value = mock_result

        result = await subscription_service.reactivate_subscription(
            mock_db, mock_subscription.id, tenant_id, user_id
        )

        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_update_subscription_quantity(
        self, subscription_service, mock_db, mock_subscription
    ):
        """Test updating subscription quantity"""
        tenant_id = mock_subscription.tenant_id
        user_id = uuid4()

        data = SubscriptionUpdate(
            quantity=5,
            provider_count=3
        )

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_subscription
        mock_db.execute.return_value = mock_result

        result = await subscription_service.update_quantity(
            mock_db, mock_subscription.id, tenant_id, data, user_id
        )

        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_calculate_mrr_monthly(
        self, subscription_service, mock_plan
    ):
        """Test MRR calculation for monthly billing"""
        mrr = subscription_service._calculate_mrr(
            mock_plan,
            BillingCycle.MONTHLY,
            quantity=1,
            discount_percent=Decimal("0")
        )
        assert mrr == Decimal("199.00")

    @pytest.mark.asyncio
    async def test_calculate_mrr_annual(
        self, subscription_service, mock_plan
    ):
        """Test MRR calculation for annual billing (should be annual/12)"""
        mrr = subscription_service._calculate_mrr(
            mock_plan,
            BillingCycle.ANNUAL,
            quantity=1,
            discount_percent=Decimal("0")
        )
        # Annual price is 1990, MRR = 1990/12 ≈ 165.83
        expected = (Decimal("1990.00") / 12).quantize(Decimal("0.01"))
        assert mrr == expected

    @pytest.mark.asyncio
    async def test_calculate_mrr_with_discount(
        self, subscription_service, mock_plan
    ):
        """Test MRR calculation with discount"""
        mrr = subscription_service._calculate_mrr(
            mock_plan,
            BillingCycle.MONTHLY,
            quantity=1,
            discount_percent=Decimal("20")
        )
        # 199 * (1 - 0.20) = 159.20
        assert mrr == Decimal("159.20")

    @pytest.mark.asyncio
    async def test_calculate_mrr_with_quantity(
        self, subscription_service, mock_plan
    ):
        """Test MRR calculation with quantity > 1"""
        mrr = subscription_service._calculate_mrr(
            mock_plan,
            BillingCycle.MONTHLY,
            quantity=3,
            discount_percent=Decimal("0")
        )
        assert mrr == Decimal("597.00")


class TestSubscriptionEntitlements:
    """Tests for subscription entitlements"""

    @pytest.mark.asyncio
    async def test_create_entitlements(
        self, subscription_service, mock_db, mock_subscription, mock_plan
    ):
        """Test creating entitlements for a subscription"""
        await subscription_service._create_entitlements(
            mock_db, mock_subscription, mock_plan
        )

        # Should add entitlements based on plan features
        assert mock_db.add.called

    @pytest.mark.asyncio
    async def test_check_entitlement_allowed(
        self, subscription_service, mock_db
    ):
        """Test checking an allowed entitlement"""
        tenant_id = uuid4()

        # Mock entitlement that allows feature
        mock_entitlement = MagicMock(spec=Entitlement)
        mock_entitlement.is_enabled = True
        mock_entitlement.limit_value = 100
        mock_entitlement.current_usage = 50

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_entitlement
        mock_db.execute.return_value = mock_result

        result = await subscription_service.check_entitlement(
            mock_db, tenant_id, "patients"
        )

        assert result.is_allowed is True
        assert result.remaining == 50

    @pytest.mark.asyncio
    async def test_check_entitlement_limit_exceeded(
        self, subscription_service, mock_db
    ):
        """Test checking entitlement when limit is exceeded"""
        tenant_id = uuid4()

        mock_entitlement = MagicMock(spec=Entitlement)
        mock_entitlement.is_enabled = True
        mock_entitlement.limit_value = 100
        mock_entitlement.current_usage = 100

        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_entitlement
        mock_db.execute.return_value = mock_result

        result = await subscription_service.check_entitlement(
            mock_db, tenant_id, "patients"
        )

        assert result.is_allowed is False
        assert result.remaining == 0


class TestProrationCalculation:
    """Tests for proration calculation"""

    @pytest.mark.asyncio
    async def test_calculate_proration_upgrade(
        self, subscription_service, mock_db, mock_subscription, mock_plan
    ):
        """Test proration calculation for upgrade"""
        # Create a higher tier plan
        new_plan = MagicMock(spec=Plan)
        new_plan.id = uuid4()
        new_plan.name = "Enterprise"
        new_plan.monthly_price = Decimal("499.00")

        # Subscription is halfway through the period
        mock_subscription.current_period_start = datetime.utcnow() - timedelta(days=15)
        mock_subscription.current_period_end = datetime.utcnow() + timedelta(days=15)

        result = await subscription_service.calculate_proration(
            mock_db, mock_subscription, mock_plan, new_plan
        )

        assert result.current_plan == "Professional"
        assert result.new_plan == "Enterprise"
        # Net amount should be positive for upgrade
        assert result.net_amount >= 0

    @pytest.mark.asyncio
    async def test_calculate_proration_downgrade(
        self, subscription_service, mock_db, mock_subscription, mock_plan
    ):
        """Test proration calculation for downgrade"""
        # Create a lower tier plan
        new_plan = MagicMock(spec=Plan)
        new_plan.id = uuid4()
        new_plan.name = "Starter"
        new_plan.monthly_price = Decimal("49.00")

        mock_subscription.current_period_start = datetime.utcnow() - timedelta(days=15)
        mock_subscription.current_period_end = datetime.utcnow() + timedelta(days=15)

        result = await subscription_service.calculate_proration(
            mock_db, mock_subscription, mock_plan, new_plan
        )

        assert result.current_plan == "Professional"
        assert result.new_plan == "Starter"
        # Credit should be positive for downgrade
        assert result.proration_credit >= 0

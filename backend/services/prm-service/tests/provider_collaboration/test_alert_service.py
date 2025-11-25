"""
Alert Service Tests
EPIC-015: Unit tests for clinical alerts and notification service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone, timedelta

from modules.provider_collaboration.services.alert_service import AlertService
from modules.provider_collaboration.schemas import (
    AlertCreate, AlertRuleCreate, AlertRuleUpdate,
    AlertPrioritySchema, AlertRuleTypeSchema
)
from modules.provider_collaboration.models import (
    AlertPriority, AlertStatus, AlertDeliveryStatus, AlertRuleType
)


class TestAlertService:
    """Tests for AlertService"""

    @pytest.fixture
    def service(self):
        return AlertService()

    @pytest.fixture
    def mock_db(self):
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        db.delete = AsyncMock()
        return db

    @pytest.fixture
    def provider_id(self):
        return uuid4()

    @pytest.fixture
    def tenant_id(self):
        return uuid4()

    # ==================== Alert Creation Tests ====================

    @pytest.mark.asyncio
    async def test_create_alert(self, service, mock_db, provider_id, tenant_id):
        """Test creating a clinical alert"""
        recipient_id = uuid4()
        patient_id = uuid4()

        data = AlertCreate(
            alert_type="critical_lab",
            priority=AlertPrioritySchema.CRITICAL,
            title="Critical Lab Result",
            message="Potassium level 6.8 mEq/L requires immediate attention",
            patient_id=patient_id,
            recipient_id=recipient_id,
            requires_acknowledgment=True,
            delivery_channels=["in_app", "sms"]
        )

        result = await service.create_alert(
            mock_db, provider_id, tenant_id, data, "127.0.0.1"
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_create_alert_with_action(self, service, mock_db, provider_id, tenant_id):
        """Test creating alert with required action"""
        recipient_id = uuid4()

        data = AlertCreate(
            alert_type="medication_approval",
            priority=AlertPrioritySchema.HIGH,
            title="Medication Approval Required",
            message="High-risk medication requires physician approval",
            recipient_id=recipient_id,
            action_required="Approve or deny medication order",
            action_url="/medications/orders/12345"
        )

        result = await service.create_alert(
            mock_db, provider_id, tenant_id, data, "127.0.0.1"
        )

        assert mock_db.add.called

    @pytest.mark.asyncio
    async def test_create_alert_calculates_escalation_deadline(self, service, mock_db, provider_id, tenant_id):
        """Test that escalation deadline is set based on priority"""
        recipient_id = uuid4()

        data = AlertCreate(
            alert_type="test_alert",
            priority=AlertPrioritySchema.CRITICAL,
            title="Critical Alert",
            message="Test message",
            recipient_id=recipient_id,
            requires_acknowledgment=True
        )

        result = await service.create_alert(
            mock_db, provider_id, tenant_id, data, "127.0.0.1"
        )

        # Critical alerts should have 5 minute escalation
        assert service.escalation_timeouts[AlertPriority.CRITICAL] == 5

    # ==================== Alert Status Tests ====================

    @pytest.mark.asyncio
    async def test_mark_as_read(self, service, mock_db, provider_id):
        """Test marking an alert as read"""
        alert_id = uuid4()

        alert = MagicMock()
        alert.id = alert_id
        alert.read_at = None
        alert.alert_type = "test"
        alert.priority = AlertPriority.MEDIUM
        alert.title = "Test"
        alert.message = "Test message"
        alert.patient_id = None
        alert.sender_id = uuid4()
        alert.recipient_id = provider_id
        alert.recipient_group = None
        alert.care_team_id = None
        alert.related_entity_type = None
        alert.related_entity_id = None
        alert.status = AlertStatus.ACTIVE
        alert.delivery_status = AlertDeliveryStatus.DELIVERED
        alert.delivery_channels = ["in_app"]
        alert.requires_acknowledgment = False
        alert.acknowledged_at = None
        alert.acknowledged_by = None
        alert.resolved_at = None
        alert.resolution = None
        alert.escalated_at = None
        alert.escalation_count = 0
        alert.action_required = None
        alert.action_url = None
        alert.created_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = alert
        mock_db.execute.return_value = mock_result

        result = await service.mark_as_read(mock_db, provider_id, alert_id)

        assert alert.read_at is not None
        assert alert.read_by == provider_id
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, service, mock_db, provider_id):
        """Test acknowledging an alert"""
        alert_id = uuid4()

        alert = MagicMock()
        alert.id = alert_id
        alert.status = AlertStatus.ACTIVE
        alert.read_at = None
        alert.alert_type = "critical_lab"
        alert.priority = AlertPriority.CRITICAL
        alert.title = "Critical Alert"
        alert.message = "Test"
        alert.patient_id = uuid4()
        alert.sender_id = uuid4()
        alert.recipient_id = provider_id
        alert.recipient_group = None
        alert.care_team_id = None
        alert.related_entity_type = None
        alert.related_entity_id = None
        alert.delivery_status = AlertDeliveryStatus.DELIVERED
        alert.delivery_channels = ["in_app"]
        alert.requires_acknowledgment = True
        alert.acknowledged_at = None
        alert.acknowledged_by = None
        alert.resolved_at = None
        alert.resolution = None
        alert.escalated_at = None
        alert.escalation_count = 0
        alert.action_required = None
        alert.action_url = None
        alert.created_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = alert
        mock_db.execute.return_value = mock_result

        result = await service.acknowledge_alert(
            mock_db, provider_id, alert_id, "Reviewing patient now"
        )

        assert alert.acknowledged_at is not None
        assert alert.acknowledged_by == provider_id
        assert alert.status == AlertStatus.ACKNOWLEDGED
        assert alert.acknowledgment_notes == "Reviewing patient now"
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_acknowledge_inactive_alert(self, service, mock_db, provider_id):
        """Test that inactive alerts cannot be acknowledged"""
        alert_id = uuid4()

        alert = MagicMock()
        alert.id = alert_id
        alert.status = AlertStatus.RESOLVED

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = alert
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="not active"):
            await service.acknowledge_alert(mock_db, provider_id, alert_id)

    @pytest.mark.asyncio
    async def test_resolve_alert(self, service, mock_db, provider_id):
        """Test resolving an alert"""
        alert_id = uuid4()

        alert = MagicMock()
        alert.id = alert_id
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.alert_type = "test"
        alert.priority = AlertPriority.HIGH
        alert.title = "Test"
        alert.message = "Test"
        alert.patient_id = uuid4()
        alert.sender_id = uuid4()
        alert.recipient_id = provider_id
        alert.recipient_group = None
        alert.care_team_id = None
        alert.related_entity_type = None
        alert.related_entity_id = None
        alert.delivery_status = AlertDeliveryStatus.DELIVERED
        alert.delivery_channels = ["in_app"]
        alert.requires_acknowledgment = True
        alert.read_at = datetime.now(timezone.utc)
        alert.acknowledged_at = datetime.now(timezone.utc)
        alert.acknowledged_by = provider_id
        alert.resolved_at = None
        alert.resolution = None
        alert.escalated_at = None
        alert.escalation_count = 0
        alert.action_required = None
        alert.action_url = None
        alert.created_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = alert
        mock_db.execute.return_value = mock_result

        result = await service.resolve_alert(
            mock_db, provider_id, alert_id, "Potassium corrected with insulin/glucose"
        )

        assert alert.status == AlertStatus.RESOLVED
        assert alert.resolved_at is not None
        assert alert.resolved_by == provider_id
        assert alert.resolution == "Potassium corrected with insulin/glucose"
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_dismiss_alert(self, service, mock_db, provider_id):
        """Test dismissing an alert"""
        alert_id = uuid4()

        alert = MagicMock()
        alert.id = alert_id
        alert.status = AlertStatus.ACTIVE
        alert.alert_type = "low_priority"
        alert.priority = AlertPriority.LOW
        alert.title = "Test"
        alert.message = "Test"
        alert.patient_id = None
        alert.sender_id = uuid4()
        alert.recipient_id = provider_id
        alert.recipient_group = None
        alert.care_team_id = None
        alert.related_entity_type = None
        alert.related_entity_id = None
        alert.delivery_status = AlertDeliveryStatus.DELIVERED
        alert.delivery_channels = ["in_app"]
        alert.requires_acknowledgment = False
        alert.read_at = None
        alert.acknowledged_at = None
        alert.acknowledged_by = None
        alert.resolved_at = None
        alert.resolution = None
        alert.escalated_at = None
        alert.escalation_count = 0
        alert.action_required = None
        alert.action_url = None
        alert.created_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = alert
        mock_db.execute.return_value = mock_result

        result = await service.dismiss_alert(
            mock_db, provider_id, alert_id, "Not relevant to current patient"
        )

        assert alert.status == AlertStatus.DISMISSED
        assert alert.dismissed_at is not None
        assert alert.dismissed_by == provider_id
        assert alert.dismissal_reason == "Not relevant to current patient"
        assert mock_db.commit.called

    # ==================== Alert Rule Tests ====================

    @pytest.mark.asyncio
    async def test_create_rule(self, service, mock_db, provider_id, tenant_id):
        """Test creating an alert rule"""
        data = AlertRuleCreate(
            name="Critical Potassium",
            description="Alert when potassium > 6.0",
            rule_type=AlertRuleTypeSchema.LAB_RESULT,
            trigger_conditions={"lab_type": "potassium", "value_gt": 6.0},
            alert_type="critical_lab",
            priority=AlertPrioritySchema.CRITICAL,
            title_template="Critical Potassium: {value}",
            message_template="Patient {patient_name} has potassium of {value} mEq/L",
            delivery_channels=["in_app", "sms"],
            requires_acknowledgment=True,
            is_active=True
        )

        result = await service.create_rule(
            mock_db, provider_id, tenant_id, data, "127.0.0.1"
        )

        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_update_rule(self, service, mock_db, provider_id, tenant_id):
        """Test updating an alert rule"""
        rule_id = uuid4()

        rule = MagicMock()
        rule.id = rule_id
        rule.tenant_id = tenant_id
        rule.name = "Old Name"
        rule.description = None
        rule.rule_type = AlertRuleType.LAB_RESULT
        rule.trigger_conditions = {}
        rule.alert_template = {}
        rule.recipient_config = {}
        rule.is_active = True
        rule.trigger_count = 0
        rule.last_triggered_at = None
        rule.created_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = rule
        mock_db.execute.return_value = mock_result

        data = AlertRuleUpdate(
            name="Updated Rule Name",
            is_active=False
        )

        result = await service.update_rule(
            mock_db, provider_id, tenant_id, rule_id, data
        )

        assert rule.name == "Updated Rule Name"
        assert rule.is_active is False
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_toggle_rule(self, service, mock_db, tenant_id):
        """Test toggling alert rule active status"""
        rule_id = uuid4()

        rule = MagicMock()
        rule.id = rule_id
        rule.tenant_id = tenant_id
        rule.is_active = True
        rule.name = "Test Rule"
        rule.description = None
        rule.rule_type = AlertRuleType.VITAL_SIGN
        rule.trigger_conditions = {}
        rule.alert_template = {}
        rule.recipient_config = {}
        rule.trigger_count = 5
        rule.last_triggered_at = datetime.now(timezone.utc)
        rule.created_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = rule
        mock_db.execute.return_value = mock_result

        result = await service.toggle_rule(mock_db, tenant_id, rule_id)

        assert rule.is_active is False
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_delete_rule(self, service, mock_db, tenant_id):
        """Test deleting an alert rule"""
        rule_id = uuid4()

        rule = MagicMock()
        rule.id = rule_id
        rule.tenant_id = tenant_id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = rule
        mock_db.execute.return_value = mock_result

        result = await service.delete_rule(mock_db, tenant_id, rule_id)

        assert result is True
        assert mock_db.delete.called
        assert mock_db.commit.called


class TestAlertServiceConditionEvaluation:
    """Condition evaluation tests for AlertService"""

    @pytest.fixture
    def service(self):
        return AlertService()

    def test_evaluate_simple_equality(self, service):
        """Test simple equality condition"""
        conditions = {"status": "critical"}
        context = {"status": "critical"}

        result = service._evaluate_conditions(conditions, context)
        assert result is True

    def test_evaluate_simple_inequality(self, service):
        """Test simple inequality condition"""
        conditions = {"status": "critical"}
        context = {"status": "normal"}

        result = service._evaluate_conditions(conditions, context)
        assert result is False

    def test_evaluate_greater_than(self, service):
        """Test greater than condition"""
        conditions = {"value_gt": 6.0}
        context = {"value": 6.5}

        result = service._evaluate_conditions(conditions, context)
        assert result is True

    def test_evaluate_less_than(self, service):
        """Test less than condition"""
        conditions = {"value_lt": 3.5}
        context = {"value": 3.0}

        result = service._evaluate_conditions(conditions, context)
        assert result is True

    def test_evaluate_greater_than_or_equal(self, service):
        """Test greater than or equal condition"""
        conditions = {"value_gte": 6.0}
        context = {"value": 6.0}

        result = service._evaluate_conditions(conditions, context)
        assert result is True

    def test_evaluate_less_than_or_equal(self, service):
        """Test less than or equal condition"""
        conditions = {"value_lte": 3.5}
        context = {"value": 3.5}

        result = service._evaluate_conditions(conditions, context)
        assert result is True

    def test_evaluate_in_list(self, service):
        """Test in list condition"""
        conditions = {"status_in": ["critical", "warning"]}
        context = {"status": "warning"}

        result = service._evaluate_conditions(conditions, context)
        assert result is True

    def test_evaluate_contains(self, service):
        """Test contains condition"""
        conditions = {"message_contains": "urgent"}
        context = {"message": "This is an urgent message"}

        result = service._evaluate_conditions(conditions, context)
        assert result is True

    def test_evaluate_and_conditions(self, service):
        """Test AND conditions"""
        conditions = {
            "and": [
                {"lab_type": "potassium"},
                {"value_gt": 6.0}
            ]
        }
        context = {"lab_type": "potassium", "value": 6.8}

        result = service._evaluate_conditions(conditions, context)
        assert result is True

    def test_evaluate_or_conditions(self, service):
        """Test OR conditions"""
        conditions = {
            "or": [
                {"value_gt": 6.0},
                {"value_lt": 3.5}
            ]
        }
        context = {"value": 3.0}

        result = service._evaluate_conditions(conditions, context)
        assert result is True

    def test_evaluate_not_condition(self, service):
        """Test NOT condition"""
        conditions = {
            "not": {"status": "normal"}
        }
        context = {"status": "critical"}

        result = service._evaluate_conditions(conditions, context)
        assert result is True

    def test_interpolate_template(self, service):
        """Test template interpolation"""
        template = "Patient {patient_name} has {lab_type} of {value}"
        context = {
            "patient_name": "John Doe",
            "lab_type": "potassium",
            "value": "6.8"
        }

        result = service._interpolate_template(template, context)
        assert result == "Patient John Doe has potassium of 6.8"

    def test_interpolate_template_missing_key(self, service):
        """Test template with missing key returns original"""
        template = "Patient {patient_name} has {missing_key}"
        context = {"patient_name": "John Doe"}

        result = service._interpolate_template(template, context)
        # Should return original template since key is missing
        assert result == template


class TestAlertServiceEscalation:
    """Escalation tests for AlertService"""

    @pytest.fixture
    def service(self):
        return AlertService()

    def test_escalation_timeouts_configured(self, service):
        """Test escalation timeouts are correctly configured"""
        assert service.escalation_timeouts[AlertPriority.LOW] == 120
        assert service.escalation_timeouts[AlertPriority.MEDIUM] == 60
        assert service.escalation_timeouts[AlertPriority.HIGH] == 15
        assert service.escalation_timeouts[AlertPriority.CRITICAL] == 5

    @pytest.mark.asyncio
    async def test_escalate_alert(self, service):
        """Test escalating an unacknowledged alert"""
        mock_db = AsyncMock()
        alert_id = uuid4()
        new_recipient = uuid4()

        alert = MagicMock()
        alert.id = alert_id
        alert.status = AlertStatus.ACTIVE
        alert.priority = AlertPriority.CRITICAL
        alert.escalation_count = 0
        alert.alert_type = "test"
        alert.title = "Test"
        alert.message = "Test"
        alert.patient_id = None
        alert.sender_id = uuid4()
        alert.recipient_id = uuid4()
        alert.recipient_group = None
        alert.care_team_id = None
        alert.related_entity_type = None
        alert.related_entity_id = None
        alert.delivery_status = AlertDeliveryStatus.DELIVERED
        alert.delivery_channels = ["in_app"]
        alert.requires_acknowledgment = True
        alert.read_at = None
        alert.acknowledged_at = None
        alert.acknowledged_by = None
        alert.resolved_at = None
        alert.resolution = None
        alert.escalated_at = None
        alert.action_required = None
        alert.action_url = None
        alert.created_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = alert
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        result = await service.escalate_alert(mock_db, alert_id, new_recipient)

        assert alert.status == AlertStatus.ESCALATED
        assert alert.escalated_at is not None
        assert alert.escalation_count == 1
        assert alert.recipient_id == new_recipient

    @pytest.mark.asyncio
    async def test_get_alerts_needing_escalation(self, service):
        """Test getting alerts past escalation deadline"""
        mock_db = AsyncMock()
        tenant_id = uuid4()

        alert1 = MagicMock()
        alert1.id = uuid4()
        alert1.status = AlertStatus.ACTIVE
        alert1.priority = AlertPriority.CRITICAL
        alert1.alert_type = "test"
        alert1.title = "Test 1"
        alert1.message = "Test"
        alert1.patient_id = None
        alert1.sender_id = uuid4()
        alert1.recipient_id = uuid4()
        alert1.recipient_group = None
        alert1.care_team_id = None
        alert1.related_entity_type = None
        alert1.related_entity_id = None
        alert1.delivery_status = AlertDeliveryStatus.DELIVERED
        alert1.delivery_channels = ["in_app"]
        alert1.requires_acknowledgment = True
        alert1.read_at = None
        alert1.acknowledged_at = None
        alert1.acknowledged_by = None
        alert1.resolved_at = None
        alert1.resolution = None
        alert1.escalated_at = None
        alert1.escalation_count = 0
        alert1.action_required = None
        alert1.action_url = None
        alert1.created_at = datetime.now(timezone.utc)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [alert1]
        mock_db.execute.return_value = mock_result

        result = await service.get_alerts_needing_escalation(mock_db, tenant_id)

        assert len(result) == 1

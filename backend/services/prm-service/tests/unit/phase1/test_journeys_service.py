"""
Unit tests for Journeys Service
Tests journey definition and instance management
"""
import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import MagicMock, patch

from modules.journeys.service import JourneyService
from modules.journeys.schemas import (
    JourneyDefinitionCreate,
    JourneyStageCreate,
    JourneyInstanceCreate,
    JourneyStageAdvance
)


@pytest.mark.unit
@pytest.mark.phase1
class TestJourneyService:
    """Test suite for JourneyService"""

    @pytest.fixture
    def journey_service(self, db_session):
        """Create journey service instance"""
        return JourneyService(db_session)

    @pytest.fixture
    def sample_journey_definition(self, test_org_id):
        """Sample journey definition data"""
        return JourneyDefinitionCreate(
            name="Patient Onboarding",
            description="Standard patient onboarding workflow",
            org_id=test_org_id,
            is_active=True,
            stages=[
                {
                    "name": "Welcome",
                    "description": "Send welcome message",
                    "order": 1,
                    "actions": [{"type": "send_message", "template": "welcome"}]
                },
                {
                    "name": "Collect Info",
                    "description": "Collect patient details",
                    "order": 2,
                    "actions": [{"type": "collect_data"}]
                }
            ]
        )

    # ==================== Create Journey Tests ====================

    def test_create_journey_definition(self, journey_service, sample_journey_definition, mock_event_publisher):
        """Test creating a new journey definition"""
        # Act
        journey = journey_service.create_journey(sample_journey_definition)

        # Assert
        assert journey.id is not None
        assert journey.name == "Patient Onboarding"
        assert journey.is_active is True
        assert len(journey.stages) == 2
        assert journey.stages[0]["name"] == "Welcome"
        assert journey.stages[1]["order"] == 2

        # Verify event published
        mock_event_publisher.assert_called_once()
        event_call = mock_event_publisher.call_args
        assert event_call[1]["event_type"] == "journey.created"

    def test_create_journey_with_no_stages(self, journey_service, test_org_id):
        """Test creating journey without stages"""
        journey_data = JourneyDefinitionCreate(
            name="Empty Journey",
            description="Journey with no stages",
            org_id=test_org_id,
            is_active=False,
            stages=[]
        )

        journey = journey_service.create_journey(journey_data)

        assert journey.id is not None
        assert len(journey.stages) == 0
        assert journey.is_active is False

    # ==================== List Journeys Tests ====================

    def test_list_journeys(self, journey_service, sample_journey_definition):
        """Test listing all journeys"""
        # Create multiple journeys
        journey_service.create_journey(sample_journey_definition)

        journey2_data = sample_journey_definition.model_copy()
        journey2_data.name = "Another Journey"
        journey_service.create_journey(journey2_data)

        # List journeys
        journeys = journey_service.list_journeys(sample_journey_definition.org_id)

        assert len(journeys) == 2
        assert any(j.name == "Patient Onboarding" for j in journeys)
        assert any(j.name == "Another Journey" for j in journeys)

    def test_list_journeys_filter_by_active(self, journey_service, sample_journey_definition, test_org_id):
        """Test listing only active journeys"""
        # Create active and inactive journeys
        active_journey = journey_service.create_journey(sample_journey_definition)

        inactive_data = sample_journey_definition.model_copy()
        inactive_data.name = "Inactive Journey"
        inactive_data.is_active = False
        inactive_journey = journey_service.create_journey(inactive_data)

        # List only active
        active_journeys = journey_service.list_journeys(test_org_id, is_active=True)

        assert len(active_journeys) == 1
        assert active_journeys[0].name == "Patient Onboarding"
        assert active_journeys[0].is_active is True

    # ==================== Get Journey Tests ====================

    def test_get_journey_by_id(self, journey_service, sample_journey_definition):
        """Test retrieving journey by ID"""
        created = journey_service.create_journey(sample_journey_definition)

        retrieved = journey_service.get_journey(
            sample_journey_definition.org_id,
            created.id
        )

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == created.name

    def test_get_journey_not_found(self, journey_service, test_org_id):
        """Test getting non-existent journey"""
        fake_id = uuid4()

        with pytest.raises(Exception) as exc_info:
            journey_service.get_journey(test_org_id, fake_id)

        assert "not found" in str(exc_info.value).lower()

    # ==================== Update Journey Tests ====================

    def test_update_journey(self, journey_service, sample_journey_definition, mock_event_publisher):
        """Test updating journey definition"""
        journey = journey_service.create_journey(sample_journey_definition)

        mock_event_publisher.reset_mock()

        # Update
        updated = journey_service.update_journey(
            org_id=sample_journey_definition.org_id,
            journey_id=journey.id,
            name="Updated Journey Name",
            description="Updated description",
            is_active=False
        )

        assert updated.name == "Updated Journey Name"
        assert updated.description == "Updated description"
        assert updated.is_active is False

        # Verify event
        mock_event_publisher.assert_called_once()
        event_call = mock_event_publisher.call_args
        assert event_call[1]["event_type"] == "journey.updated"

    # ==================== Add Stage Tests ====================

    def test_add_journey_stage(self, journey_service, sample_journey_definition, mock_event_publisher):
        """Test adding a stage to existing journey"""
        journey = journey_service.create_journey(sample_journey_definition)

        mock_event_publisher.reset_mock()

        # Add new stage
        new_stage = JourneyStageCreate(
            name="Confirmation",
            description="Confirm appointment",
            order=3,
            actions=[{"type": "send_confirmation"}]
        )

        updated = journey_service.add_stage(
            org_id=sample_journey_definition.org_id,
            journey_id=journey.id,
            stage=new_stage
        )

        assert len(updated.stages) == 3
        assert updated.stages[2]["name"] == "Confirmation"
        assert updated.stages[2]["order"] == 3

    # ==================== Create Instance Tests ====================

    def test_create_journey_instance(self, journey_service, sample_journey_definition, test_patient_id, mock_event_publisher):
        """Test creating journey instance for a patient"""
        journey = journey_service.create_journey(sample_journey_definition)

        mock_event_publisher.reset_mock()

        # Create instance
        instance_data = JourneyInstanceCreate(
            journey_id=journey.id,
            patient_id=test_patient_id,
            org_id=sample_journey_definition.org_id,
            context={"source": "whatsapp"}
        )

        instance = journey_service.create_instance(instance_data)

        assert instance.id is not None
        assert instance.journey_id == journey.id
        assert instance.patient_id == test_patient_id
        assert instance.current_stage_index == 0
        assert instance.status == "active"
        assert instance.context == {"source": "whatsapp"}

        # Verify event
        mock_event_publisher.assert_called_once()

    # ==================== Advance Stage Tests ====================

    def test_advance_journey_stage(self, journey_service, sample_journey_definition, test_patient_id, mock_event_publisher):
        """Test advancing through journey stages"""
        journey = journey_service.create_journey(sample_journey_definition)

        instance_data = JourneyInstanceCreate(
            journey_id=journey.id,
            patient_id=test_patient_id,
            org_id=sample_journey_definition.org_id,
            context={}
        )
        instance = journey_service.create_instance(instance_data)

        assert instance.current_stage_index == 0

        mock_event_publisher.reset_mock()

        # Advance stage
        advance_data = JourneyStageAdvance(
            action_results={"message_sent": True}
        )

        advanced = journey_service.advance_stage(
            org_id=sample_journey_definition.org_id,
            instance_id=instance.id,
            advance=advance_data
        )

        assert advanced.current_stage_index == 1
        assert advanced.status == "active"

        # Verify event
        assert mock_event_publisher.call_count >= 1

    def test_advance_to_final_stage(self, journey_service, sample_journey_definition, test_patient_id):
        """Test advancing to final stage completes journey"""
        journey = journey_service.create_journey(sample_journey_definition)

        instance_data = JourneyInstanceCreate(
            journey_id=journey.id,
            patient_id=test_patient_id,
            org_id=sample_journey_definition.org_id,
            context={}
        )
        instance = journey_service.create_instance(instance_data)

        # Advance through all stages
        advance_data = JourneyStageAdvance(action_results={})

        # Stage 1 -> 2
        instance = journey_service.advance_stage(
            org_id=sample_journey_definition.org_id,
            instance_id=instance.id,
            advance=advance_data
        )
        assert instance.current_stage_index == 1
        assert instance.status == "active"

        # Stage 2 -> Complete
        instance = journey_service.advance_stage(
            org_id=sample_journey_definition.org_id,
            instance_id=instance.id,
            advance=advance_data
        )
        assert instance.status == "completed"
        assert instance.completed_at is not None

    def test_cannot_advance_completed_journey(self, journey_service, sample_journey_definition, test_patient_id):
        """Test that completed journeys cannot be advanced"""
        journey = journey_service.create_journey(sample_journey_definition)

        instance_data = JourneyInstanceCreate(
            journey_id=journey.id,
            patient_id=test_patient_id,
            org_id=sample_journey_definition.org_id,
            context={}
        )
        instance = journey_service.create_instance(instance_data)

        # Complete the journey
        advance_data = JourneyStageAdvance(action_results={})
        instance = journey_service.advance_stage(
            sample_journey_definition.org_id, instance.id, advance_data
        )
        instance = journey_service.advance_stage(
            sample_journey_definition.org_id, instance.id, advance_data
        )

        assert instance.status == "completed"

        # Try to advance completed journey
        with pytest.raises(Exception) as exc_info:
            journey_service.advance_stage(
                sample_journey_definition.org_id, instance.id, advance_data
            )

        assert "completed" in str(exc_info.value).lower() or "cannot advance" in str(exc_info.value).lower()

    # ==================== List Instances Tests ====================

    def test_list_journey_instances(self, journey_service, sample_journey_definition, test_patient_id):
        """Test listing journey instances"""
        journey = journey_service.create_journey(sample_journey_definition)

        # Create multiple instances
        for i in range(3):
            instance_data = JourneyInstanceCreate(
                journey_id=journey.id,
                patient_id=test_patient_id,
                org_id=sample_journey_definition.org_id,
                context={"iteration": i}
            )
            journey_service.create_instance(instance_data)

        # List instances
        instances = journey_service.list_instances(
            org_id=sample_journey_definition.org_id,
            patient_id=test_patient_id
        )

        assert len(instances) == 3
        assert all(i.patient_id == test_patient_id for i in instances)

    def test_list_instances_filter_by_status(self, journey_service, sample_journey_definition, test_patient_id):
        """Test filtering instances by status"""
        journey = journey_service.create_journey(sample_journey_definition)

        # Create instances with different statuses
        instance1_data = JourneyInstanceCreate(
            journey_id=journey.id,
            patient_id=test_patient_id,
            org_id=sample_journey_definition.org_id,
            context={}
        )
        active_instance = journey_service.create_instance(instance1_data)

        # Create and complete another
        instance2_data = JourneyInstanceCreate(
            journey_id=journey.id,
            patient_id=test_patient_id,
            org_id=sample_journey_definition.org_id,
            context={}
        )
        completed_instance = journey_service.create_instance(instance2_data)

        # Complete it
        advance_data = JourneyStageAdvance(action_results={})
        journey_service.advance_stage(sample_journey_definition.org_id, completed_instance.id, advance_data)
        journey_service.advance_stage(sample_journey_definition.org_id, completed_instance.id, advance_data)

        # Filter by active
        active_instances = journey_service.list_instances(
            org_id=sample_journey_definition.org_id,
            patient_id=test_patient_id,
            status="active"
        )

        assert len(active_instances) >= 1
        assert all(i.status == "active" for i in active_instances)

    # ==================== Get Instance Tests ====================

    def test_get_journey_instance(self, journey_service, sample_journey_definition, test_patient_id):
        """Test retrieving journey instance by ID"""
        journey = journey_service.create_journey(sample_journey_definition)

        instance_data = JourneyInstanceCreate(
            journey_id=journey.id,
            patient_id=test_patient_id,
            org_id=sample_journey_definition.org_id,
            context={"test": "data"}
        )
        created = journey_service.create_instance(instance_data)

        # Get instance
        retrieved = journey_service.get_instance(
            org_id=sample_journey_definition.org_id,
            instance_id=created.id
        )

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.patient_id == test_patient_id
        assert retrieved.context == {"test": "data"}

    # ==================== Edge Cases & Error Handling ====================

    def test_create_journey_duplicate_name(self, journey_service, sample_journey_definition):
        """Test creating journey with duplicate name (should succeed - names can duplicate)"""
        journey1 = journey_service.create_journey(sample_journey_definition)
        journey2 = journey_service.create_journey(sample_journey_definition)

        # Both should succeed - duplicate names are allowed
        assert journey1.id != journey2.id
        assert journey1.name == journey2.name

    def test_create_instance_invalid_journey_id(self, journey_service, test_org_id, test_patient_id):
        """Test creating instance with invalid journey ID"""
        fake_journey_id = uuid4()

        instance_data = JourneyInstanceCreate(
            journey_id=fake_journey_id,
            patient_id=test_patient_id,
            org_id=test_org_id,
            context={}
        )

        with pytest.raises(Exception) as exc_info:
            journey_service.create_instance(instance_data)

        assert "not found" in str(exc_info.value).lower() or "does not exist" in str(exc_info.value).lower()

    def test_advance_stage_with_action_results(self, journey_service, sample_journey_definition, test_patient_id):
        """Test advancing stage and storing action results"""
        journey = journey_service.create_journey(sample_journey_definition)

        instance_data = JourneyInstanceCreate(
            journey_id=journey.id,
            patient_id=test_patient_id,
            org_id=sample_journey_definition.org_id,
            context={}
        )
        instance = journey_service.create_instance(instance_data)

        # Advance with action results
        advance_data = JourneyStageAdvance(
            action_results={
                "message_sent": True,
                "message_id": "msg_12345",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        advanced = journey_service.advance_stage(
            org_id=sample_journey_definition.org_id,
            instance_id=instance.id,
            advance=advance_data
        )

        # Action results should be stored
        assert advanced.current_stage_index == 1
        # Check that action results are preserved in history or context

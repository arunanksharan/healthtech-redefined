"""
Intake Service
Business logic for clinical intake data collection
"""
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from loguru import logger

from modules.intake.repository import IntakeRepository
from shared.database.models import (
    IntakeSession,
    IntakeSymptom,
    IntakeAllergy,
    IntakeMedication,
    IntakeConditionHistory,
    IntakeFamilyHistory
)
from modules.intake.schemas import (
    IntakeSessionCreate,
    IntakeRecordsUpsert,
    IntakeStatistics
)
from shared.events.publisher import publish_event, EventType


class IntakeService:
    """Service for intake session management"""

    def __init__(self, db: Session):
        self.db = db
        self.repo = IntakeRepository(db)

    # ==================== Session Management ====================

    async def create_session(
        self,
        org_id: UUID,
        payload: IntakeSessionCreate
    ) -> IntakeSession:
        """
        Create new intake session

        Checks:
          - If patient_id provided, consent is checked (TODO)
          - If no consent, session created as anonymous

        Returns:
            Created IntakeSession
        """
        # TODO: Check patient consent for data_processing
        # For now, proceed with provided patient_id

        session = self.repo.create_session(
            org_id=org_id,
            patient_id=payload.patient_id,
            conversation_id=payload.conversation_id,
            context=payload.context
        )

        self.db.commit()

        # Publish event
        await publish_event(
            event_type=EventType.CUSTOM,
            org_id=org_id,
            resource_type="intake_session",
            resource_id=session.id,
            data={
                "status": "created",
                "patient_id": str(payload.patient_id) if payload.patient_id else None
            }
        )

        logger.info(f"Created intake session {session.id}")

        return session

    async def get_session(
        self,
        org_id: UUID,
        session_id: UUID
    ) -> Optional[IntakeSession]:
        """Get session by ID"""
        return self.repo.get_session(org_id, session_id)

    async def list_sessions(
        self,
        org_id: UUID,
        patient_id: Optional[UUID] = None,
        conversation_id: Optional[UUID] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[IntakeSession]:
        """List sessions with filters"""
        return self.repo.list_sessions(
            org_id=org_id,
            patient_id=patient_id,
            conversation_id=conversation_id,
            status=status,
            limit=limit,
            offset=offset
        )

    async def set_session_patient(
        self,
        org_id: UUID,
        session_id: UUID,
        patient_id: UUID
    ) -> Tuple[Optional[IntakeSession], Optional[str]]:
        """
        Link patient to session

        Requires patient consent for data_processing.

        Returns:
            (IntakeSession, error_code)
            error_code: None | "consent_required" | "not_found"
        """
        # TODO: Check patient consent
        # For now, proceed

        session = self.repo.set_patient(org_id, session_id, patient_id)

        if not session:
            return None, "not_found"

        self.db.commit()

        # Publish event
        await publish_event(
            event_type=EventType.CUSTOM,
            org_id=org_id,
            resource_type="intake_session",
            resource_id=session.id,
            data={
                "patient_linked": True,
                "patient_id": str(patient_id)
            }
        )

        logger.info(f"Linked patient {patient_id} to intake session {session_id}")

        return session, None

    async def submit(
        self,
        org_id: UUID,
        session_id: UUID
    ) -> Optional[IntakeSession]:
        """
        Submit intake session

        Marks session as complete and ready for review.
        """
        session = self.repo.submit(org_id, session_id)

        if not session:
            return None

        self.db.commit()

        # Publish event
        await publish_event(
            event_type=EventType.CUSTOM,
            org_id=org_id,
            resource_type="intake_session",
            resource_id=session.id,
            data={
                "status": "submitted"
            }
        )

        logger.info(f"Submitted intake session {session_id}")

        return session

    # ==================== Records Management ====================

    async def upsert_records(
        self,
        org_id: UUID,
        session_id: UUID,
        payload: IntakeRecordsUpsert
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Upsert multiple record types at once

        Supports partial updates - only provided fields are updated.

        Uses client-side idempotency:
          - Items with client_item_id are upserted (update if exists, insert if new)
          - Items without client_item_id are always inserted

        Returns:
            (result_dict, error_code)
            error_code: None | "not_found"
        """
        # Check session exists
        session = self.repo.get_session(org_id, session_id)

        if not session:
            return None, "not_found"

        data = payload.dict(exclude_unset=True)
        sections_updated = []

        # Chief complaint (single)
        if "chief_complaint" in data:
            cc = data["chief_complaint"]
            self.repo.upsert_chief_complaint(
                org_id,
                session_id,
                cc["text"],
                cc.get("codes")
            )
            sections_updated.append("chief_complaint")

        # Symptoms (list with idempotency)
        if "symptoms" in data and data["symptoms"]:
            self.repo.upsert_list_by_client_id(
                org_id,
                session_id,
                IntakeSymptom,
                data["symptoms"]
            )
            sections_updated.append("symptoms")

        # Allergies (list with idempotency)
        if "allergies" in data and data["allergies"]:
            self.repo.upsert_list_by_client_id(
                org_id,
                session_id,
                IntakeAllergy,
                data["allergies"]
            )
            sections_updated.append("allergies")

        # Medications (list with idempotency)
        if "medications" in data and data["medications"]:
            self.repo.upsert_list_by_client_id(
                org_id,
                session_id,
                IntakeMedication,
                data["medications"]
            )
            sections_updated.append("medications")

        # Condition history (list with idempotency)
        if "condition_history" in data and data["condition_history"]:
            self.repo.upsert_list_by_client_id(
                org_id,
                session_id,
                IntakeConditionHistory,
                data["condition_history"]
            )
            sections_updated.append("condition_history")

        # Family history (list with idempotency)
        if "family_history" in data and data["family_history"]:
            self.repo.upsert_list_by_client_id(
                org_id,
                session_id,
                IntakeFamilyHistory,
                data["family_history"]
            )
            sections_updated.append("family_history")

        # Social history (merged dict)
        if "social_history" in data and data["social_history"]:
            sh = data["social_history"]
            merged = {k: v for k, v in sh.items() if v is not None}
            self.repo.set_social_history(org_id, session_id, merged)
            sections_updated.append("social_history")

        # Notes (append-only)
        if "notes" in data and data["notes"]:
            self.repo.add_notes(org_id, session_id, data["notes"])
            sections_updated.append("notes")

        self.db.commit()

        # Publish event
        await publish_event(
            event_type=EventType.CUSTOM,
            org_id=org_id,
            resource_type="intake_session",
            resource_id=session_id,
            data={
                "records_updated": True,
                "sections": sections_updated
            }
        )

        logger.info(
            f"Updated {len(sections_updated)} sections for intake session {session_id}"
        )

        return {
            "updated": True,
            "sections": sections_updated
        }, None

    async def set_summary(
        self,
        org_id: UUID,
        session_id: UUID,
        text: str
    ) -> Tuple[Optional[Any], Optional[str]]:
        """
        Set AI-generated summary

        Returns:
            (IntakeSummary, error_code)
        """
        session = self.repo.get_session(org_id, session_id)

        if not session:
            return None, "not_found"

        summary = self.repo.set_summary(org_id, session_id, text)

        self.db.commit()

        # Publish event
        await publish_event(
            event_type=EventType.CUSTOM,
            org_id=org_id,
            resource_type="intake_session",
            resource_id=session_id,
            data={
                "summary_set": True,
                "length": len(text)
            }
        )

        logger.info(f"Set summary for intake session {session_id}")

        return summary, None

    # ==================== Statistics ====================

    async def get_statistics(
        self,
        org_id: UUID
    ) -> IntakeStatistics:
        """Get intake session statistics"""
        stats = self.repo.get_statistics(org_id)

        return IntakeStatistics(
            total_sessions=stats["total_sessions"],
            open_sessions=stats["open_sessions"],
            submitted_sessions=stats["submitted_sessions"],
            closed_sessions=stats["closed_sessions"],
            avg_completion_time_minutes=0.0,  # TODO: Calculate
            by_conversation=stats["by_conversation"],
            by_patient=stats["by_patient"]
        )

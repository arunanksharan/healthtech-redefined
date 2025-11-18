"""
Intake Repository
Database operations for intake sessions and records
"""
from typing import List, Optional, Dict, Any, Type
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func, desc
from datetime import datetime
from loguru import logger

from shared.database.models import (
    IntakeSession,
    IntakeSummary,
    IntakeChiefComplaint,
    IntakeSymptom,
    IntakeAllergy,
    IntakeMedication,
    IntakeConditionHistory,
    IntakeFamilyHistory,
    IntakeSocialHistory,
    IntakeNote
)


class IntakeRepository:
    """Repository for intake data operations"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== Session Management ====================

    def create_session(
        self,
        org_id: UUID,
        patient_id: Optional[UUID],
        conversation_id: Optional[UUID],
        context: Optional[Dict[str, Any]]
    ) -> IntakeSession:
        """Create new intake session"""
        session = IntakeSession(
            id=uuid4(),
            org_id=org_id,
            patient_id=patient_id,
            conversation_id=conversation_id,
            status="open",
            context=context
        )

        self.db.add(session)
        self.db.flush()

        return session

    def get_session(
        self,
        org_id: UUID,
        session_id: UUID
    ) -> Optional[IntakeSession]:
        """Get session by ID"""
        query = select(IntakeSession).where(
            and_(
                IntakeSession.id == session_id,
                IntakeSession.org_id == org_id,
                IntakeSession.deleted_at.is_(None)
            )
        )

        result = self.db.execute(query)
        return result.scalar_one_or_none()

    def list_sessions(
        self,
        org_id: UUID,
        patient_id: Optional[UUID] = None,
        conversation_id: Optional[UUID] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[IntakeSession]:
        """List sessions with filters"""
        conditions = [
            IntakeSession.org_id == org_id,
            IntakeSession.deleted_at.is_(None)
        ]

        if patient_id:
            conditions.append(IntakeSession.patient_id == patient_id)

        if conversation_id:
            conditions.append(IntakeSession.conversation_id == conversation_id)

        if status:
            conditions.append(IntakeSession.status == status)

        query = (
            select(IntakeSession)
            .where(and_(*conditions))
            .order_by(desc(IntakeSession.created_at))
            .limit(limit)
            .offset(offset)
        )

        result = self.db.execute(query)
        return result.scalars().all()

    def set_patient(
        self,
        org_id: UUID,
        session_id: UUID,
        patient_id: Optional[UUID]
    ) -> Optional[IntakeSession]:
        """Link patient to session"""
        session = self.get_session(org_id, session_id)

        if not session:
            return None

        session.patient_id = patient_id
        session.updated_at = datetime.utcnow()

        self.db.flush()

        return session

    def submit(
        self,
        org_id: UUID,
        session_id: UUID
    ) -> Optional[IntakeSession]:
        """Submit session (mark as complete)"""
        session = self.get_session(org_id, session_id)

        if not session:
            return None

        session.status = "submitted"
        session.updated_at = datetime.utcnow()

        self.db.flush()

        return session

    # ==================== Chief Complaint ====================

    def upsert_chief_complaint(
        self,
        org_id: UUID,
        session_id: UUID,
        text: str,
        codes: Optional[Dict[str, str]]
    ) -> IntakeChiefComplaint:
        """Upsert chief complaint (only one per session)"""
        # Check if exists
        query = select(IntakeChiefComplaint).where(
            and_(
                IntakeChiefComplaint.org_id == org_id,
                IntakeChiefComplaint.session_id == session_id
            )
        )

        result = self.db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            # Update
            existing.text = text
            existing.codes = codes
            existing.updated_at = datetime.utcnow()
            self.db.flush()
            return existing
        else:
            # Insert
            cc = IntakeChiefComplaint(
                id=uuid4(),
                org_id=org_id,
                session_id=session_id,
                text=text,
                codes=codes
            )
            self.db.add(cc)
            self.db.flush()
            return cc

    # ==================== List Items with Idempotency ====================

    def upsert_list_by_client_id(
        self,
        org_id: UUID,
        session_id: UUID,
        model_class: Type,
        items: List[Dict[str, Any]]
    ) -> List[Any]:
        """
        Upsert list items with client-side idempotency

        For each item:
          - If client_item_id provided and exists: UPDATE
          - Otherwise: INSERT

        This allows frontend to:
          - Go back and edit (by re-submitting with same client_item_id)
          - Add new items (with new client_item_id)
          - Not create duplicates on retry
        """
        results = []

        for item_data in items:
            client_item_id = item_data.get("client_item_id")

            if client_item_id:
                # Try to find existing
                query = select(model_class).where(
                    and_(
                        model_class.org_id == org_id,
                        model_class.session_id == session_id,
                        model_class.client_item_id == client_item_id
                    )
                )

                result = self.db.execute(query)
                existing = result.scalar_one_or_none()

                if existing:
                    # Update
                    for key, value in item_data.items():
                        if hasattr(existing, key) and key not in ['id', 'org_id', 'session_id', 'created_at']:
                            setattr(existing, key, value)

                    existing.updated_at = datetime.utcnow()
                    self.db.flush()
                    results.append(existing)
                    continue

            # Insert new
            item = model_class(
                id=uuid4(),
                org_id=org_id,
                session_id=session_id,
                **item_data
            )
            self.db.add(item)
            self.db.flush()
            results.append(item)

        return results

    # ==================== Social History ====================

    def set_social_history(
        self,
        org_id: UUID,
        session_id: UUID,
        data: Dict[str, Any]
    ) -> IntakeSocialHistory:
        """Set social history (merge with existing)"""
        # Check if exists
        query = select(IntakeSocialHistory).where(
            and_(
                IntakeSocialHistory.org_id == org_id,
                IntakeSocialHistory.session_id == session_id
            )
        )

        result = self.db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            # Merge data
            merged_data = {**(existing.data or {}), **data}
            existing.data = merged_data
            existing.updated_at = datetime.utcnow()
            self.db.flush()
            return existing
        else:
            # Insert
            sh = IntakeSocialHistory(
                id=uuid4(),
                org_id=org_id,
                session_id=session_id,
                data=data
            )
            self.db.add(sh)
            self.db.flush()
            return sh

    # ==================== Notes ====================

    def add_notes(
        self,
        org_id: UUID,
        session_id: UUID,
        notes: List[Dict[str, Any]]
    ) -> List[IntakeNote]:
        """Add notes (append-only)"""
        note_objects = []

        for note_data in notes:
            note = IntakeNote(
                id=uuid4(),
                org_id=org_id,
                session_id=session_id,
                text=note_data["text"],
                visibility=note_data.get("visibility", "internal")
            )
            self.db.add(note)
            note_objects.append(note)

        self.db.flush()

        return note_objects

    # ==================== Summary ====================

    def set_summary(
        self,
        org_id: UUID,
        session_id: UUID,
        text: str
    ) -> IntakeSummary:
        """Set AI summary (upsert)"""
        # Check if exists
        query = select(IntakeSummary).where(
            and_(
                IntakeSummary.org_id == org_id,
                IntakeSummary.session_id == session_id
            )
        )

        result = self.db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            existing.text = text
            existing.updated_at = datetime.utcnow()
            self.db.flush()
            return existing
        else:
            summary = IntakeSummary(
                id=uuid4(),
                org_id=org_id,
                session_id=session_id,
                text=text
            )
            self.db.add(summary)
            self.db.flush()
            return summary

    # ==================== Statistics ====================

    def get_statistics(
        self,
        org_id: UUID
    ) -> Dict[str, Any]:
        """Get intake session statistics"""
        # Total sessions
        total_query = select(func.count(IntakeSession.id)).where(
            and_(
                IntakeSession.org_id == org_id,
                IntakeSession.deleted_at.is_(None)
            )
        )
        total_result = self.db.execute(total_query)
        total_sessions = total_result.scalar() or 0

        # By status
        status_query = (
            select(
                IntakeSession.status,
                func.count(IntakeSession.id).label('count')
            )
            .where(
                and_(
                    IntakeSession.org_id == org_id,
                    IntakeSession.deleted_at.is_(None)
                )
            )
            .group_by(IntakeSession.status)
        )
        status_result = self.db.execute(status_query)
        by_status = {row[0]: row[1] for row in status_result.all()}

        # With conversation
        with_conversation_query = select(func.count(IntakeSession.id)).where(
            and_(
                IntakeSession.org_id == org_id,
                IntakeSession.deleted_at.is_(None),
                IntakeSession.conversation_id.isnot(None)
            )
        )
        with_conversation_result = self.db.execute(with_conversation_query)
        by_conversation = with_conversation_result.scalar() or 0

        # With patient
        with_patient_query = select(func.count(IntakeSession.id)).where(
            and_(
                IntakeSession.org_id == org_id,
                IntakeSession.deleted_at.is_(None),
                IntakeSession.patient_id.isnot(None)
            )
        )
        with_patient_result = self.db.execute(with_patient_query)
        by_patient = with_patient_result.scalar() or 0

        return {
            "total_sessions": total_sessions,
            "open_sessions": by_status.get("open", 0),
            "submitted_sessions": by_status.get("submitted", 0),
            "closed_sessions": by_status.get("closed", 0),
            "by_conversation": by_conversation,
            "by_patient": by_patient
        }

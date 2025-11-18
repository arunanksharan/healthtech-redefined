"""
Patient Service
Business logic for FHIR-compliant patient management
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, extract
from loguru import logger
from typing import List, Optional, Tuple
from uuid import UUID, uuid4
from datetime import datetime, date
import random

from shared.database.models import Patient, Appointment, Conversation, MediaAsset
from shared.events.publisher import publish_event
from shared.events.schemas import EventType

from modules.patients.schemas import (
    PatientCreate,
    PatientUpdate,
    PatientSearch,
    PatientResponse,
    PatientDetailResponse,
    DuplicatePatient,
    PatientMergeRequest,
    PatientMergeResult,
    PatientStatistics,
    PatientStatus
)


class PatientService:
    """Service for patient management"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== CRUD Operations ====================

    async def create_patient(
        self,
        patient_data: PatientCreate,
        org_id: Optional[UUID] = None
    ) -> Patient:
        """
        Create new patient

        Features:
        - Auto-generate MRN if not provided
        - Check for potential duplicates
        - Validate data
        - Publish event
        """
        try:
            # Generate MRN
            mrn = await self._generate_mrn()

            # Check for potential duplicates (warn but don't block)
            potential_duplicates = await self._find_potential_duplicates(
                name=patient_data.legal_name,
                date_of_birth=patient_data.date_of_birth,
                phone=patient_data.primary_phone
            )

            if potential_duplicates:
                logger.warning(
                    f"Found {len(potential_duplicates)} potential duplicate(s) for "
                    f"{patient_data.legal_name} (DOB: {patient_data.date_of_birth})"
                )

            # Create patient
            patient = Patient(
                id=uuid4(),
                org_id=org_id,
                mrn=mrn,
                legal_name=patient_data.legal_name,
                preferred_name=patient_data.preferred_name,
                date_of_birth=patient_data.date_of_birth,
                gender=patient_data.gender.value,
                ssn_encrypted=patient_data.ssn,  # TODO: Encrypt before storage
                primary_phone=patient_data.primary_phone,
                secondary_phone=patient_data.secondary_phone,
                email=patient_data.email,
                preferred_contact_method=patient_data.preferred_contact_method.value,
                race=patient_data.race,
                ethnicity=patient_data.ethnicity,
                preferred_language=patient_data.preferred_language,
                marital_status=patient_data.marital_status.value if patient_data.marital_status else None,
                primary_care_provider_id=patient_data.primary_care_provider_id,
                status=PatientStatus.ACTIVE.value,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            # Handle address (store as JSON or in separate table)
            if patient_data.address:
                patient.address_json = patient_data.address.dict()

            # Handle emergency contact
            if patient_data.emergency_contact:
                patient.emergency_contact_json = patient_data.emergency_contact.dict()

            # Handle insurance
            if patient_data.insurance:
                patient.insurance_json = patient_data.insurance.dict()

            self.db.add(patient)
            self.db.commit()
            self.db.refresh(patient)

            logger.info(f"Created patient: {patient.id} (MRN: {mrn})")

            # Publish event
            await publish_event(
                event_type=EventType.PATIENT_CREATED,
                entity_id=patient.id,
                entity_type="patient",
                data={
                    "patient_id": str(patient.id),
                    "mrn": mrn,
                    "name": patient.legal_name,
                    "phone": patient.primary_phone
                }
            )

            return patient

        except Exception as e:
            logger.error(f"Error creating patient: {e}", exc_info=True)
            self.db.rollback()
            raise

    async def _generate_mrn(self) -> str:
        """
        Generate unique Medical Record Number

        Format: MRN-{YEAR}{6-digit-random}
        Example: MRN-2024123456
        """
        year = datetime.utcnow().year

        # Generate until unique
        max_attempts = 10
        for _ in range(max_attempts):
            random_digits = random.randint(100000, 999999)
            mrn = f"MRN-{year}{random_digits}"

            # Check if MRN already exists
            existing = self.db.query(Patient).filter(
                Patient.mrn == mrn
            ).first()

            if not existing:
                return mrn

        # Fallback: use UUID suffix
        import uuid
        mrn = f"MRN-{year}{str(uuid.uuid4())[:6].upper()}"
        return mrn

    async def get_patient(self, patient_id: UUID) -> Optional[Patient]:
        """Get patient by ID"""
        return self.db.query(Patient).filter(
            Patient.id == patient_id
        ).first()

    async def get_patient_by_mrn(self, mrn: str) -> Optional[Patient]:
        """Get patient by Medical Record Number"""
        return self.db.query(Patient).filter(
            Patient.mrn == mrn
        ).first()

    async def update_patient(
        self,
        patient_id: UUID,
        update_data: PatientUpdate
    ) -> Optional[Patient]:
        """Update patient information"""
        patient = await self.get_patient(patient_id)

        if not patient:
            return None

        # Update fields
        update_dict = update_data.dict(exclude_unset=True, exclude_none=True)

        for field, value in update_dict.items():
            if hasattr(patient, field):
                # Handle enums
                if hasattr(value, 'value'):
                    setattr(patient, field, value.value)
                else:
                    setattr(patient, field, value)

        patient.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(patient)

        logger.info(f"Updated patient: {patient_id}")

        # Publish event
        await publish_event(
            event_type=EventType.PATIENT_UPDATED,
            entity_id=patient_id,
            entity_type="patient",
            data=update_dict
        )

        return patient

    async def delete_patient(self, patient_id: UUID) -> bool:
        """Soft delete patient"""
        patient = await self.get_patient(patient_id)

        if not patient:
            return False

        # Soft delete (set status to inactive)
        patient.status = PatientStatus.INACTIVE.value
        patient.updated_at = datetime.utcnow()

        self.db.commit()

        logger.info(f"Soft deleted patient: {patient_id}")

        # Publish event
        await publish_event(
            event_type=EventType.PATIENT_DELETED,
            entity_id=patient_id,
            entity_type="patient",
            data={"patient_id": str(patient_id)}
        )

        return True

    # ==================== Search & Discovery ====================

    async def search_patients(
        self,
        search_params: PatientSearch
    ) -> List[Patient]:
        """
        Advanced patient search

        Supports:
        - Full-text search (name, MRN, phone, email)
        - Fuzzy name matching
        - Exact matching on DOB, gender
        - Filtering by status, provider
        """
        query = self.db.query(Patient)

        # General query search (name, MRN, phone, email)
        if search_params.query:
            search_term = f"%{search_params.query}%"
            query = query.filter(
                or_(
                    Patient.legal_name.ilike(search_term),
                    Patient.preferred_name.ilike(search_term),
                    Patient.mrn.ilike(search_term),
                    Patient.primary_phone.contains(search_params.query),
                    Patient.email.ilike(search_term)
                )
            )

        # Specific filters
        if search_params.name:
            query = query.filter(
                Patient.legal_name.ilike(f"%{search_params.name}%")
            )

        if search_params.phone:
            # Normalize phone for search
            phone_digits = ''.join(c for c in search_params.phone if c.isdigit())
            query = query.filter(
                Patient.primary_phone.contains(phone_digits)
            )

        if search_params.email:
            query = query.filter(
                Patient.email.ilike(f"%{search_params.email}%")
            )

        if search_params.date_of_birth:
            query = query.filter(
                Patient.date_of_birth == search_params.date_of_birth
            )

        if search_params.gender:
            query = query.filter(
                Patient.gender == search_params.gender.value
            )

        if search_params.status:
            query = query.filter(
                Patient.status == search_params.status.value
            )

        if search_params.primary_care_provider_id:
            query = query.filter(
                Patient.primary_care_provider_id == search_params.primary_care_provider_id
            )

        if search_params.created_after:
            query = query.filter(
                Patient.created_at >= search_params.created_after
            )

        if search_params.created_before:
            query = query.filter(
                Patient.created_at <= search_params.created_before
            )

        # Order by relevance (most recent first)
        query = query.order_by(Patient.created_at.desc())

        # Pagination
        query = query.offset(search_params.offset).limit(search_params.limit)

        return query.all()

    # ==================== Duplicate Detection ====================

    async def find_duplicates(
        self,
        patient_id: UUID
    ) -> List[DuplicatePatient]:
        """
        Find potential duplicate patients

        Matching criteria:
        - Exact name + DOB
        - Same phone number
        - Very similar names (fuzzy)
        """
        patient = await self.get_patient(patient_id)

        if not patient:
            return []

        duplicates = await self._find_potential_duplicates(
            name=patient.legal_name,
            date_of_birth=patient.date_of_birth,
            phone=patient.primary_phone,
            exclude_id=patient_id
        )

        return duplicates

    async def _find_potential_duplicates(
        self,
        name: str,
        date_of_birth: date,
        phone: str,
        exclude_id: Optional[UUID] = None
    ) -> List[DuplicatePatient]:
        """
        Find potential duplicates using multiple criteria

        Returns list of potential duplicates with match scores
        """
        potential_duplicates = []

        # Search criteria
        query = self.db.query(Patient).filter(
            Patient.status == PatientStatus.ACTIVE.value
        )

        if exclude_id:
            query = query.filter(Patient.id != exclude_id)

        # Find by exact name + DOB
        exact_matches = query.filter(
            and_(
                Patient.legal_name.ilike(name),
                Patient.date_of_birth == date_of_birth
            )
        ).all()

        for match in exact_matches:
            potential_duplicates.append(DuplicatePatient(
                patient=PatientResponse.from_orm(match),
                match_score=0.95,
                match_reasons=["Exact name and date of birth match"]
            ))

        # Find by phone number
        phone_digits = ''.join(c for c in phone if c.isdigit())
        phone_matches = query.filter(
            Patient.primary_phone.contains(phone_digits)
        ).all()

        for match in phone_matches:
            if match not in exact_matches:
                potential_duplicates.append(DuplicatePatient(
                    patient=PatientResponse.from_orm(match),
                    match_score=0.85,
                    match_reasons=["Same phone number"]
                ))

        return potential_duplicates

    # ==================== Patient Merge ====================

    async def merge_patients(
        self,
        merge_request: PatientMergeRequest
    ) -> PatientMergeResult:
        """
        Merge duplicate patients

        Process:
        1. Validate both patients exist
        2. Move all appointments to primary
        3. Move all conversations to primary
        4. Move all media to primary
        5. Deactivate duplicate
        6. Publish event
        """
        try:
            primary = await self.get_patient(merge_request.primary_patient_id)
            duplicate = await self.get_patient(merge_request.duplicate_patient_id)

            if not primary or not duplicate:
                return PatientMergeResult(
                    success=False,
                    primary_patient=None,
                    merged_data={},
                    errors=["One or both patients not found"]
                )

            merged_data = {
                "appointments_moved": 0,
                "conversations_moved": 0,
                "media_moved": 0
            }

            # Move appointments
            appointments = self.db.query(Appointment).filter(
                Appointment.patient_id == duplicate.id
            ).all()

            for appt in appointments:
                appt.patient_id = primary.id
                merged_data["appointments_moved"] += 1

            # Move conversations
            conversations = self.db.query(Conversation).filter(
                Conversation.patient_id == duplicate.id
            ).all()

            for conv in conversations:
                conv.patient_id = primary.id
                merged_data["conversations_moved"] += 1

            # Move media
            media_files = self.db.query(MediaAsset).filter(
                MediaAsset.patient_id == duplicate.id
            ).all()

            for media in media_files:
                media.patient_id = primary.id
                merged_data["media_moved"] += 1

            # Deactivate duplicate
            duplicate.status = PatientStatus.INACTIVE.value
            duplicate.updated_at = datetime.utcnow()

            # Add merge note to duplicate
            duplicate.merge_note = f"Merged into patient {primary.id} at {datetime.utcnow()}"

            self.db.commit()

            logger.info(
                f"Merged patient {duplicate.id} into {primary.id}: "
                f"{merged_data}"
            )

            # Publish event
            await publish_event(
                event_type=EventType.PATIENTS_MERGED,
                entity_id=primary.id,
                entity_type="patient",
                data={
                    "primary_patient_id": str(primary.id),
                    "duplicate_patient_id": str(duplicate.id),
                    "merged_data": merged_data,
                    "reason": merge_request.reason
                }
            )

            return PatientMergeResult(
                success=True,
                primary_patient=PatientResponse.from_orm(primary),
                merged_data=merged_data,
                errors=[]
            )

        except Exception as e:
            logger.error(f"Error merging patients: {e}", exc_info=True)
            self.db.rollback()
            return PatientMergeResult(
                success=False,
                primary_patient=None,
                merged_data={},
                errors=[str(e)]
            )

    # ==================== Statistics ====================

    async def get_statistics(
        self,
        org_id: Optional[UUID] = None
    ) -> PatientStatistics:
        """Get patient demographics and statistics"""
        query = self.db.query(Patient)

        if org_id:
            query = query.filter(Patient.org_id == org_id)

        # Total counts
        total_patients = query.count()
        active_patients = query.filter(
            Patient.status == PatientStatus.ACTIVE.value
        ).count()
        inactive_patients = query.filter(
            Patient.status == PatientStatus.INACTIVE.value
        ).count()

        # New patients this month
        first_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
        new_this_month = query.filter(
            Patient.created_at >= first_of_month
        ).count()

        # By gender
        gender_results = self.db.query(
            Patient.gender,
            func.count(Patient.id)
        ).group_by(Patient.gender).all()

        patients_by_gender = {gender: count for gender, count in gender_results}

        # By age group
        age_groups = {
            "0-18": 0,
            "19-35": 0,
            "36-50": 0,
            "51-65": 0,
            "66+": 0
        }

        patients = query.all()
        total_age = 0

        for patient in patients:
            age = (date.today() - patient.date_of_birth).days // 365

            if age <= 18:
                age_groups["0-18"] += 1
            elif age <= 35:
                age_groups["19-35"] += 1
            elif age <= 50:
                age_groups["36-50"] += 1
            elif age <= 65:
                age_groups["51-65"] += 1
            else:
                age_groups["66+"] += 1

            total_age += age

        # Average age
        avg_age = total_age / total_patients if total_patients > 0 else 0

        # By status
        status_results = self.db.query(
            Patient.status,
            func.count(Patient.id)
        ).group_by(Patient.status).all()

        patients_by_status = {status: count for status, count in status_results}

        return PatientStatistics(
            total_patients=total_patients,
            active_patients=active_patients,
            inactive_patients=inactive_patients,
            new_patients_this_month=new_this_month,
            patients_by_gender=patients_by_gender,
            patients_by_age_group=age_groups,
            patients_by_status=patients_by_status,
            average_age=avg_age
        )

    # ==================== Detail Response ====================

    async def get_patient_detail(
        self,
        patient_id: UUID
    ) -> Optional[PatientDetailResponse]:
        """
        Get patient with statistics

        Includes counts for appointments, conversations, media
        """
        patient = await self.get_patient(patient_id)

        if not patient:
            return None

        # Count appointments
        total_appointments = self.db.query(Appointment).filter(
            Appointment.patient_id == patient_id
        ).count()

        upcoming_appointments = self.db.query(Appointment).filter(
            and_(
                Appointment.patient_id == patient_id,
                Appointment.confirmed_start >= datetime.utcnow(),
                Appointment.status == "confirmed"
            )
        ).count()

        # Count conversations
        total_conversations = self.db.query(Conversation).filter(
            Conversation.patient_id == patient_id
        ).count()

        # Count media
        total_media = self.db.query(MediaAsset).filter(
            MediaAsset.patient_id == patient_id
        ).count()

        # Get last visit
        last_appt = self.db.query(Appointment).filter(
            and_(
                Appointment.patient_id == patient_id,
                Appointment.confirmed_start < datetime.utcnow(),
                Appointment.status == "completed"
            )
        ).order_by(Appointment.confirmed_start.desc()).first()

        # Get next appointment
        next_appt = self.db.query(Appointment).filter(
            and_(
                Appointment.patient_id == patient_id,
                Appointment.confirmed_start >= datetime.utcnow(),
                Appointment.status == "confirmed"
            )
        ).order_by(Appointment.confirmed_start.asc()).first()

        return PatientDetailResponse(
            **PatientResponse.from_orm(patient).dict(),
            total_appointments=total_appointments,
            upcoming_appointments=upcoming_appointments,
            total_conversations=total_conversations,
            total_media_files=total_media,
            last_visit_date=last_appt.confirmed_start if last_appt else None,
            next_appointment_date=next_appt.confirmed_start if next_appt else None
        )

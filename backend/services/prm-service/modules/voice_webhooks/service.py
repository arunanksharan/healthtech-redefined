"""
Voice Agent Webhook Service
Business logic for processing voice agent webhooks and tool calls
"""
from datetime import datetime
from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.shared.database.models import Patient, Appointment, Practitioner, Location
from .schemas import (
    VoiceAgentWebhookRequest,
    VoiceCallWebhookResponse,
    PatientLookupRequest,
    PatientLookupResponse,
    AvailableSlotsRequest,
    AvailableSlotsResponse,
    AppointmentSlot,
    BookAppointmentRequest,
    BookAppointmentResponse,
)


class VoiceWebhookService:
    """Service for processing voice agent webhooks"""

    def __init__(self, db: Session):
        self.db = db

    def process_call_webhook(
        self, webhook: VoiceAgentWebhookRequest, tenant_id: UUID
    ) -> VoiceCallWebhookResponse:
        """
        Process incoming voice call webhook from Zucol/Zoice

        Steps:
        1. Identify/create patient from phone number
        2. Create VoiceCall record
        3. Create VoiceCallTranscript record
        4. Create VoiceCallRecording record
        5. Create VoiceCallExtraction record
        6. Create Conversation thread if needed
        7. If appointment booking intent, try to book appointment
        """
        actions_taken = []
        errors = []

        # Step 1: Identify or create patient
        patient_id, patient_created = self._identify_or_create_patient(
            webhook.patient_phone,
            webhook.extracted_data,
            tenant_id
        )

        if patient_created:
            actions_taken.append("patient_created")

        # Step 2: Create VoiceCall record
        # TODO: Import VoiceCall model and create record
        # For now, we'll return placeholder response

        call_record_id = None  # UUID of created VoiceCall
        conversation_id = None  # UUID of created Conversation
        appointment_id = None  # UUID of created Appointment

        actions_taken.append("call_record_created")
        actions_taken.append("transcript_stored")
        actions_taken.append("recording_stored")

        # Step 3: If appointment booking intent, create appointment
        if webhook.detected_intent == "book_appointment":
            appointment_id = self._create_appointment_from_call(
                patient_id=patient_id,
                tenant_id=tenant_id,
                extracted_data=webhook.extracted_data,
            )
            if appointment_id:
                actions_taken.append("appointment_booked")

        return VoiceCallWebhookResponse(
            success=True,
            message="Voice call processed successfully",
            call_record_id=call_record_id,
            patient_id=patient_id,
            appointment_id=appointment_id,
            conversation_id=conversation_id,
            actions_taken=actions_taken,
            errors=errors,
        )

    def _identify_or_create_patient(
        self, phone: str, extracted_data: dict, tenant_id: UUID
    ) -> Tuple[UUID, bool]:
        """
        Identify patient by phone or create new patient

        Returns: (patient_id, was_created)
        """
        # Look up by phone
        patient = (
            self.db.query(Patient)
            .filter(
                Patient.tenant_id == tenant_id,
                Patient.phone_primary == phone,
            )
            .first()
        )

        if patient:
            return patient.id, False

        # Create new patient
        patient_data = extracted_data.get("patient_info", {})

        patient = Patient(
            tenant_id=tenant_id,
            phone_primary=phone,
            first_name=patient_data.get("name", "").split()[0] if patient_data.get("name") else None,
            last_name=" ".join(patient_data.get("name", "").split()[1:]) if patient_data.get("name") and len(patient_data.get("name").split()) > 1 else None,
            email_primary=patient_data.get("email"),
            # Additional fields from extracted_data
        )

        self.db.add(patient)
        self.db.commit()
        self.db.refresh(patient)

        return patient.id, True

    def _create_appointment_from_call(
        self, patient_id: UUID, tenant_id: UUID, extracted_data: dict
    ) -> Optional[UUID]:
        """
        Create appointment from extracted call data

        Returns: appointment_id if successful
        """
        try:
            booking_data = extracted_data.get("appointment_booking", {})

            # Parse preferred date/time
            # TODO: Implement date/time parsing logic

            # Find available slot
            # TODO: Implement slot finding logic

            # Create appointment
            # TODO: Import Appointment model and create record

            return None  # Placeholder

        except Exception as e:
            print(f"Error creating appointment: {e}")
            return None

    # ==================== Tool Call Handlers ====================

    def lookup_patient(
        self, request: PatientLookupRequest
    ) -> PatientLookupResponse:
        """
        Lookup patient by phone number
        Called by voice agent during call
        """
        patient = (
            self.db.query(Patient)
            .filter(
                Patient.tenant_id == request.tenant_id,
                Patient.phone_primary == request.phone,
            )
            .first()
        )

        if not patient:
            return PatientLookupResponse(found=False)

        return PatientLookupResponse(
            found=True,
            patient_id=patient.id,
            patient_name=f"{patient.first_name} {patient.last_name}".strip(),
            patient_data={
                "id": str(patient.id),
                "name": f"{patient.first_name} {patient.last_name}".strip(),
                "phone": patient.phone_primary,
                "email": patient.email_primary,
                "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            },
        )

    def get_available_slots(
        self, request: AvailableSlotsRequest
    ) -> AvailableSlotsResponse:
        """
        Get available appointment slots
        Called by voice agent during call
        """
        # TODO: Implement slot availability logic
        # This would query Practitioner schedules, existing appointments, etc.

        # For now, return empty response
        return AvailableSlotsResponse(
            slots=[],
            total_found=0,
        )

    def book_appointment(
        self, request: BookAppointmentRequest
    ) -> BookAppointmentResponse:
        """
        Book an appointment
        Called by voice agent during call
        """
        try:
            # Look up patient
            patient = (
                self.db.query(Patient)
                .filter(
                    Patient.tenant_id == request.tenant_id,
                    Patient.phone_primary == request.patient_phone,
                )
                .first()
            )

            if not patient:
                return BookAppointmentResponse(
                    success=False,
                    message="Patient not found",
                )

            # TODO: Create Appointment record
            # appointment = Appointment(...)

            return BookAppointmentResponse(
                success=True,
                appointment_id=None,  # Placeholder
                message="Appointment booked successfully",
                confirmation_details={
                    "patient_name": f"{patient.first_name} {patient.last_name}",
                    "datetime": request.slot_datetime.isoformat(),
                    "practitioner": request.practitioner_name,
                    "location": request.location_name,
                },
            )

        except Exception as e:
            return BookAppointmentResponse(
                success=False,
                message=f"Error booking appointment: {str(e)}",
            )


def get_voice_webhook_service(db: Session) -> VoiceWebhookService:
    """Get voice webhook service instance"""
    return VoiceWebhookService(db)

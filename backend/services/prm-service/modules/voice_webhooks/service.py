"""
Voice Agent Webhook Service
Business logic for processing voice agent webhooks and tool calls
"""
from datetime import datetime, timedelta, time
from typing import Optional, List, Tuple
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from sqlalchemy import and_
from loguru import logger
import dateparser

from backend.shared.database.models import Patient, Appointment, Practitioner, Location, PractitionerSchedule
from backend.shared.database.conversation_voice_models import (
    VoiceCall,
    VoiceCallTranscript,
    VoiceCallRecording,
    VoiceCallExtraction,
    Conversation,
)
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

        try:
            # Step 1: Identify or create patient
            patient_id, patient_created = self._identify_or_create_patient(
                webhook.patient_phone,
                webhook.extracted_data,
                tenant_id
            )

            if patient_created:
                actions_taken.append("patient_created")

            # Step 2: Create VoiceCall record
            voice_call = VoiceCall(
                id=uuid4(),
                tenant_id=tenant_id,
                patient_id=patient_id,
                zoice_call_id=webhook.call_id,
                plivo_call_id=webhook.plivo_call_id,
                patient_phone=webhook.patient_phone,
                agent_phone=webhook.agent_phone,
                call_type=webhook.call_type,
                call_status="completed",
                started_at=webhook.call_started_at,
                ended_at=webhook.call_ended_at,
                duration_seconds=webhook.duration_seconds,
                pipeline_id=webhook.pipeline_id,
                agent_name=webhook.agent_name,
                detected_intent=webhook.detected_intent,
                call_outcome=webhook.call_outcome,
                confidence_score=webhook.confidence_score,
                language=webhook.language,
                sentiment=webhook.sentiment,
                metadata=webhook.metadata or {},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            self.db.add(voice_call)
            self.db.flush()  # Get ID without committing
            actions_taken.append("call_record_created")

            call_record_id = voice_call.id

            # Step 3: Create VoiceCallTranscript record
            if webhook.transcript:
                transcript = VoiceCallTranscript(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    call_id=voice_call.id,
                    full_transcript=webhook.transcript,
                    turns=webhook.transcript_turns or [],
                    provider=webhook.transcription_provider or "zoice",
                    language=webhook.language,
                    confidence_score=webhook.transcription_confidence,
                    word_count=len(webhook.transcript.split()) if webhook.transcript else 0,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                self.db.add(transcript)
                actions_taken.append("transcript_stored")

            # Step 4: Create VoiceCallRecording record
            if webhook.recording_url:
                recording = VoiceCallRecording(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    call_id=voice_call.id,
                    recording_url=webhook.recording_url,
                    storage_provider=webhook.storage_provider or "zoice",
                    storage_path=webhook.recording_url,
                    format=webhook.recording_format or "mp3",
                    duration_seconds=webhook.duration_seconds,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                self.db.add(recording)
                actions_taken.append("recording_stored")

            # Step 5: Create VoiceCallExtraction record
            if webhook.extracted_data:
                extraction = VoiceCallExtraction(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    call_id=voice_call.id,
                    extraction_type=webhook.detected_intent or "general",
                    pipeline_id=webhook.pipeline_id,
                    extracted_data=webhook.extracted_data,
                    confidence_scores=webhook.confidence_scores or {},
                    overall_confidence=webhook.confidence_score,
                    model_used=webhook.model_used or "gpt-4",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                self.db.add(extraction)
                actions_taken.append("extraction_stored")

            # Step 6: Create Conversation thread
            conversation = Conversation(
                id=uuid4(),
                tenant_id=tenant_id,
                patient_id=patient_id,
                subject=f"Voice Call - {webhook.detected_intent or 'General'}",
                status="closed",  # Voice calls are one-time, mark as closed
                channel_type="phone",
                external_id=str(webhook.call_id),
                state_data={},
                extracted_data=webhook.extracted_data or {},
                is_intake_complete=True,
                first_message_at=webhook.call_started_at,
                last_message_at=webhook.call_ended_at,
                closed_at=webhook.call_ended_at,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            self.db.add(conversation)
            self.db.flush()  # Get ID
            actions_taken.append("conversation_created")

            conversation_id = conversation.id

            # Link conversation to voice call
            voice_call.conversation_id = conversation_id

            # Step 7: If appointment booking intent, create appointment
            appointment_id = None
            if webhook.detected_intent == "book_appointment":
                appointment_id = self._create_appointment_from_call(
                    patient_id=patient_id,
                    tenant_id=tenant_id,
                    extracted_data=webhook.extracted_data,
                )
                if appointment_id:
                    actions_taken.append("appointment_booked")
                    voice_call.appointment_id = appointment_id
                    conversation.appointment_id = appointment_id
                else:
                    errors.append("Failed to create appointment from call data")

            # Commit all changes
            self.db.commit()
            self.db.refresh(voice_call)

            logger.info(
                f"Processed voice call {webhook.call_id}: "
                f"patient_id={patient_id}, conversation_id={conversation_id}, "
                f"appointment_id={appointment_id}"
            )

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

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error processing voice call webhook: {e}", exc_info=True)
            errors.append(str(e))

            return VoiceCallWebhookResponse(
                success=False,
                message=f"Failed to process voice call: {str(e)}",
                call_record_id=None,
                patient_id=None,
                appointment_id=None,
                conversation_id=None,
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

            if not booking_data:
                logger.warning("No appointment booking data in extracted_data")
                return None

            # Parse preferred date/time
            preferred_datetime_str = booking_data.get("preferred_datetime")
            preferred_date_str = booking_data.get("preferred_date")
            preferred_time_str = booking_data.get("preferred_time")

            # Try to parse datetime
            appointment_datetime = None

            if preferred_datetime_str:
                # Parse full datetime string
                appointment_datetime = dateparser.parse(
                    preferred_datetime_str,
                    settings={'PREFER_DATES_FROM': 'future'}
                )
            elif preferred_date_str and preferred_time_str:
                # Parse date and time separately, then combine
                combined = f"{preferred_date_str} {preferred_time_str}"
                appointment_datetime = dateparser.parse(
                    combined,
                    settings={'PREFER_DATES_FROM': 'future'}
                )
            elif preferred_date_str:
                # Just date provided, default to 9 AM
                appointment_datetime = dateparser.parse(
                    f"{preferred_date_str} 09:00 AM",
                    settings={'PREFER_DATES_FROM': 'future'}
                )

            if not appointment_datetime:
                logger.warning("Could not parse appointment datetime from call data")
                return None

            # Get practitioner info
            practitioner_name = booking_data.get("practitioner_name")
            practitioner_id = booking_data.get("practitioner_id")

            # If practitioner name provided but no ID, try to find practitioner
            if practitioner_name and not practitioner_id:
                practitioner = self.db.query(Practitioner).filter(
                    Practitioner.tenant_id == tenant_id,
                    Practitioner.name.ilike(f"%{practitioner_name}%")
                ).first()

                if practitioner:
                    practitioner_id = practitioner.id
                    practitioner_name = practitioner.name
                else:
                    logger.warning(f"Practitioner not found: {practitioner_name}")
                    # Try to get any available practitioner
                    practitioner = self.db.query(Practitioner).filter(
                        Practitioner.tenant_id == tenant_id
                    ).first()

                    if practitioner:
                        practitioner_id = practitioner.id
                        practitioner_name = practitioner.name

            if not practitioner_id:
                logger.warning("No practitioner available for appointment")
                return None

            # Get location info
            location_name = booking_data.get("location_name")
            location_id = booking_data.get("location_id")

            # If location name provided but no ID, try to find location
            if location_name and not location_id:
                location = self.db.query(Location).filter(
                    Location.tenant_id == tenant_id,
                    Location.name.ilike(f"%{location_name}%")
                ).first()

                if location:
                    location_id = location.id
                    location_name = location.name

            # Default duration: 30 minutes
            duration_minutes = booking_data.get("duration_minutes", 30)

            # Create appointment
            appointment = Appointment(
                id=uuid4(),
                tenant_id=tenant_id,
                patient_id=patient_id,
                practitioner_id=practitioner_id,
                practitioner_name=practitioner_name,
                location_id=location_id,
                location_name=location_name,
                status="confirmed",
                confirmed_start=appointment_datetime,
                confirmed_end=appointment_datetime + timedelta(minutes=duration_minutes),
                channel_origin="voice_agent",
                reason=booking_data.get("reason") or extracted_data.get("chief_complaint"),
                notes=booking_data.get("notes"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            self.db.add(appointment)
            self.db.flush()  # Get ID without committing yet

            logger.info(
                f"Created appointment {appointment.id} from voice call: "
                f"patient_id={patient_id}, datetime={appointment_datetime}"
            )

            return appointment.id

        except Exception as e:
            logger.error(f"Error creating appointment from call: {e}", exc_info=True)
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
        try:
            # Parse preferred date
            preferred_date = None
            if request.preferred_date:
                preferred_date = dateparser.parse(
                    request.preferred_date,
                    settings={'PREFER_DATES_FROM': 'future'}
                )

            # Set search range: next 14 days from preferred_date or today
            start_date = preferred_date.date() if preferred_date else datetime.utcnow().date()
            end_date = start_date + timedelta(days=14)

            # Find practitioners matching criteria
            query = self.db.query(Practitioner, Location).join(
                Location,
                Practitioner.location_id == Location.id
            ).filter(
                Practitioner.tenant_id == request.tenant_id
            )

            # Filter by practitioner name if provided
            if request.practitioner_name:
                query = query.filter(
                    Practitioner.name.ilike(f"%{request.practitioner_name}%")
                )

            # Filter by location if provided
            if request.location_name:
                query = query.filter(
                    Location.name.ilike(f"%{request.location_name}%")
                )

            # Filter by specialty if provided
            if request.specialty:
                query = query.filter(
                    Practitioner.specialty.ilike(f"%{request.specialty}%")
                )

            practitioners = query.all()

            if not practitioners:
                logger.warning(f"No practitioners found matching criteria")
                return AvailableSlotsResponse(
                    slots=[],
                    total_found=0,
                )

            # Generate slots for each practitioner
            all_slots = []
            for practitioner, location in practitioners:
                slots = self._generate_slots_for_practitioner(
                    practitioner=practitioner,
                    location=location,
                    start_date=start_date,
                    end_date=end_date,
                    preferred_time=request.preferred_time,
                )
                all_slots.extend(slots)

            # Filter out booked slots
            available_slots = self._filter_booked_slots(all_slots)

            # Limit to max 10 slots
            available_slots = available_slots[:10]

            logger.info(f"Found {len(available_slots)} available slots")

            return AvailableSlotsResponse(
                slots=available_slots,
                total_found=len(available_slots),
            )

        except Exception as e:
            logger.error(f"Error getting available slots: {e}", exc_info=True)
            return AvailableSlotsResponse(
                slots=[],
                total_found=0,
            )

    def _generate_slots_for_practitioner(
        self,
        practitioner: Practitioner,
        location: Location,
        start_date: datetime.date,
        end_date: datetime.date,
        preferred_time: Optional[str] = None,
    ) -> List[AppointmentSlot]:
        """Generate appointment slots for practitioner based on schedule"""
        slots = []

        # Get practitioner's weekly schedule
        schedules = self.db.query(PractitionerSchedule).filter(
            PractitionerSchedule.practitioner_id == practitioner.id
        ).all()

        if not schedules:
            return []

        # Parse preferred time if provided
        preferred_hour = None
        if preferred_time:
            preferred_time_lower = preferred_time.lower()
            if "morning" in preferred_time_lower:
                preferred_hour = 9  # 9 AM
            elif "afternoon" in preferred_time_lower:
                preferred_hour = 14  # 2 PM
            elif "evening" in preferred_time_lower:
                preferred_hour = 17  # 5 PM
            else:
                # Try to parse as time
                parsed_time = dateparser.parse(preferred_time)
                if parsed_time:
                    preferred_hour = parsed_time.hour

        # Generate slots for each day in range
        current_date = start_date
        while current_date <= end_date:
            day_of_week = current_date.weekday()  # 0=Monday, 6=Sunday

            # Find schedule for this day
            for schedule in schedules:
                if schedule.day_of_week == day_of_week:
                    # Generate slots for this schedule
                    day_slots = self._generate_day_slots(
                        date=current_date,
                        schedule=schedule,
                        practitioner=practitioner,
                        location=location,
                        preferred_hour=preferred_hour,
                    )
                    slots.extend(day_slots)

            current_date += timedelta(days=1)

        return slots

    def _generate_day_slots(
        self,
        date: datetime.date,
        schedule: PractitionerSchedule,
        practitioner: Practitioner,
        location: Location,
        preferred_hour: Optional[int] = None,
    ) -> List[AppointmentSlot]:
        """Generate slots for a specific day"""
        slots = []

        # Convert schedule times to datetime
        start_time = datetime.combine(
            date,
            time(hour=schedule.start_minute // 60, minute=schedule.start_minute % 60)
        )
        end_time = datetime.combine(
            date,
            time(hour=schedule.end_minute // 60, minute=schedule.end_minute % 60)
        )

        # Generate slots at regular intervals
        current_slot = start_time
        while current_slot < end_time:
            # Skip past slots
            if current_slot > datetime.utcnow():
                # If preferred hour specified, prioritize slots near that hour
                if preferred_hour is None or abs(current_slot.hour - preferred_hour) <= 2:
                    # Format datetime for display
                    formatted_time = current_slot.strftime("%A, %B %d at %I:%M %p")

                    slots.append(AppointmentSlot(
                        datetime=current_slot,
                        practitioner_name=practitioner.name,
                        practitioner_id=str(practitioner.id),
                        location_name=location.name if location else "Unknown",
                        location_id=str(location.id) if location else None,
                        formatted_time=formatted_time,
                    ))

            current_slot += timedelta(minutes=schedule.slot_minutes)

        return slots

    def _filter_booked_slots(
        self,
        slots: List[AppointmentSlot]
    ) -> List[AppointmentSlot]:
        """Remove slots that are already booked"""
        if not slots:
            return []

        # Get all confirmed appointments in the relevant time range
        min_time = min(s.datetime for s in slots)
        max_time = max(s.datetime for s in slots)

        booked = self.db.query(Appointment).filter(
            and_(
                Appointment.confirmed_start >= min_time,
                Appointment.confirmed_start <= max_time,
                Appointment.status == "confirmed"
            )
        ).all()

        # Create set of booked (datetime, practitioner_name) pairs
        booked_set = {
            (appt.confirmed_start, appt.practitioner_name)
            for appt in booked
            if appt.confirmed_start and appt.practitioner_name
        }

        # Filter out booked slots
        available = [
            slot for slot in slots
            if (slot.datetime, slot.practitioner_name) not in booked_set
        ]

        return available

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
                # Create patient if not found
                patient_name = request.patient_name or "Unknown Patient"
                name_parts = patient_name.split()
                first_name = name_parts[0] if name_parts else "Unknown"
                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

                patient = Patient(
                    id=uuid4(),
                    tenant_id=request.tenant_id,
                    phone_primary=request.patient_phone,
                    first_name=first_name,
                    last_name=last_name,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                self.db.add(patient)
                self.db.flush()

            # Check if slot is still available
            existing = self.db.query(Appointment).filter(
                and_(
                    Appointment.tenant_id == request.tenant_id,
                    Appointment.practitioner_id == request.practitioner_id,
                    Appointment.confirmed_start == request.slot_datetime,
                    Appointment.status == "confirmed"
                )
            ).first()

            if existing:
                return BookAppointmentResponse(
                    success=False,
                    message="This time slot is no longer available",
                )

            # Create appointment
            duration_minutes = request.duration_minutes or 30

            appointment = Appointment(
                id=uuid4(),
                tenant_id=request.tenant_id,
                patient_id=patient.id,
                practitioner_id=request.practitioner_id,
                practitioner_name=request.practitioner_name,
                location_id=request.location_id,
                location_name=request.location_name,
                status="confirmed",
                confirmed_start=request.slot_datetime,
                confirmed_end=request.slot_datetime + timedelta(minutes=duration_minutes),
                channel_origin="voice_agent",
                reason=request.reason,
                notes=request.notes,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            self.db.add(appointment)
            self.db.commit()
            self.db.refresh(appointment)

            logger.info(
                f"Booked appointment {appointment.id} via voice agent: "
                f"patient_id={patient.id}, practitioner={request.practitioner_name}, "
                f"datetime={request.slot_datetime}"
            )

            # Format confirmation details
            formatted_datetime = request.slot_datetime.strftime("%A, %B %d at %I:%M %p")

            return BookAppointmentResponse(
                success=True,
                appointment_id=appointment.id,
                message="Appointment booked successfully",
                confirmation_details={
                    "patient_name": f"{patient.first_name} {patient.last_name}".strip(),
                    "datetime": request.slot_datetime.isoformat(),
                    "formatted_datetime": formatted_datetime,
                    "practitioner": request.practitioner_name,
                    "location": request.location_name,
                    "reason": request.reason,
                },
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error booking appointment: {e}", exc_info=True)
            return BookAppointmentResponse(
                success=False,
                message=f"Error booking appointment: {str(e)}",
            )


def get_voice_webhook_service(db: Session) -> VoiceWebhookService:
    """Get voice webhook service instance"""
    return VoiceWebhookService(db)

"""
Appointments Service
Business logic for appointment booking and slot management
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from loguru import logger
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timedelta, time
import re
import json

from shared.database.models import Appointment, Patient, Practitioner, Location, ProviderSchedule
from shared.events.publisher import publish_event
from shared.events import EventType

from core.twilio_client import twilio_client
from modules.conversations.state_service import ConversationStateService

from modules.appointments.schemas import (
    AppointmentBookingRequest,
    AppointmentConfirmation,
    AppointmentUpdate,
    AppointmentResponse,
    AppointmentSlot,
    SlotsAvailable,
    SlotSelectionReply,
    SlotSelectionResult,
    SlotSelectionAction,
    BookingResult,
    AppointmentStatus,
    SlotPreferences
)


class AppointmentService:
    """Service for appointment management"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== Slot Discovery ====================

    async def find_available_slots(
        self,
        conversation_id: UUID,
        preferences: Optional[SlotPreferences] = None,
        max_slots: int = 5
    ) -> List[AppointmentSlot]:
        """
        Find available appointment slots based on preferences

        Algorithm:
        1. Get preferences from conversation state (or use provided)
        2. Find practitioners matching department/location
        3. Get their schedules for next 14 days
        4. Filter out booked slots
        5. Score and rank slots by preference match
        6. Return top N slots
        """
        try:
            # 1. Get preferences from Redis if not provided
            if not preferences:
                preferences = await self._get_preferences_from_state(conversation_id)

            logger.info(
                f"Finding slots for conversation {conversation_id} with preferences: "
                f"dept={preferences.department}, loc={preferences.preferred_location}"
            )

            # 2. Find practitioners
            practitioners = await self._find_practitioners(
                department=preferences.department,
                location_filter=preferences.preferred_location
            )

            if not practitioners:
                logger.warning(f"No practitioners found for department: {preferences.department}")
                return []

            # 3. Generate all possible slots from schedules
            all_slots = []
            for practitioner, location in practitioners:
                slots = await self._generate_slots_for_practitioner(
                    practitioner=practitioner,
                    location=location,
                    days_ahead=14
                )
                all_slots.extend(slots)

            logger.info(f"Generated {len(all_slots)} total slots before filtering")

            # 4. Remove duplicates and filter booked slots
            unique_slots = await self._deduplicate_slots(all_slots)
            available_slots = await self._filter_booked_slots(unique_slots)

            logger.info(f"{len(available_slots)} slots available after filtering")

            # 5. Score and rank by preferences
            scored_slots = self._score_slots_by_preferences(
                available_slots,
                preferences
            )

            # 6. Return top N
            top_slots = scored_slots[:max_slots]

            logger.info(f"Returning top {len(top_slots)} slots")
            return top_slots

        except Exception as e:
            logger.error(f"Error finding available slots: {e}", exc_info=True)
            return []

    async def _get_preferences_from_state(
        self,
        conversation_id: UUID
    ) -> SlotPreferences:
        """Extract booking preferences from conversation state"""
        state_service = ConversationStateService(str(conversation_id))
        extracted_data = await state_service.get_extracted_data()

        # Parse preferences
        preferred_day_str = extracted_data.get("appointment_request.preferred_day")
        preferred_day = None
        if preferred_day_str and preferred_day_str.lower() != "none":
            try:
                preferred_day = int(preferred_day_str)
            except (ValueError, TypeError):
                pass

        preferred_time_str = extracted_data.get("appointment_request.preferred_time")
        preferred_time_minutes = None
        if preferred_time_str and preferred_time_str.lower() != "none":
            try:
                preferred_time_minutes = int(preferred_time_str)
            except (ValueError, TypeError):
                pass

        return SlotPreferences(
            department=extracted_data.get("appointment_request.best_department"),
            preferred_location=extracted_data.get("appointment_request.preferred_location"),
            preferred_practitioner=extracted_data.get("practitioner_name"),
            preferred_day=preferred_day,
            preferred_time_minutes=preferred_time_minutes
        )

    async def _find_practitioners(
        self,
        department: Optional[str],
        location_filter: Optional[str] = None
    ) -> List[tuple]:
        """
        Find practitioners matching department and location

        Returns list of (Practitioner, Location) tuples
        """
        if not department:
            return []

        # Build query
        query = self.db.query(Practitioner, Location).join(
            Location,
            Practitioner.location_id == Location.id
        ).filter(
            Practitioner.specialty == department
        )

        # Apply location filter if provided
        if location_filter and location_filter.lower() != "none":
            query = query.filter(
                Location.name.ilike(f"%{location_filter}%")
            )

        practitioners = query.all()

        # Fallback: if no results with location, try without
        if not practitioners and location_filter:
            logger.info("No practitioners found with location filter, trying without")
            query = self.db.query(Practitioner, Location).join(
                Location,
                Practitioner.location_id == Location.id
            ).filter(
                Practitioner.specialty == department
            )
            practitioners = query.all()

        return practitioners

    async def _generate_slots_for_practitioner(
        self,
        practitioner: Practitioner,
        location: Location,
        days_ahead: int = 14
    ) -> List[AppointmentSlot]:
        """
        Generate all possible slots for practitioner based on their schedule

        Returns slots for next N days based on practitioner's weekly schedule
        """
        slots = []

        # Get practitioner's weekly schedule
        schedules = self.db.query(ProviderSchedule).filter(
            ProviderSchedule.practitioner_id == practitioner.id
        ).all()

        if not schedules:
            logger.warning(f"No schedule found for practitioner {practitioner.name}")
            return []

        # Generate slots for each day
        today = datetime.utcnow().date()
        for i in range(days_ahead):
            current_date = today + timedelta(days=i)
            day_of_week = current_date.weekday()  # 0=Monday, 6=Sunday

            # Find schedule for this day of week
            for schedule in schedules:
                if schedule.day_of_week == day_of_week:
                    # Generate slots for this schedule period
                    day_slots = self._generate_day_slots(
                        current_date,
                        schedule,
                        practitioner,
                        location
                    )
                    slots.extend(day_slots)

        return slots

    def _generate_day_slots(
        self,
        date: datetime.date,
        schedule: ProviderSchedule,
        practitioner: Practitioner,
        location: Location
    ) -> List[AppointmentSlot]:
        """Generate slots for a specific day based on schedule"""
        slots = []

        # Convert schedule times to datetime (ProviderSchedule uses Time objects)
        start_time = datetime.combine(date, schedule.start_time)
        end_time = datetime.combine(date, schedule.end_time)

        # Generate slots at regular intervals
        current_slot = start_time
        while current_slot < end_time:
            # Skip past slots
            if current_slot > datetime.utcnow():
                slots.append(AppointmentSlot(
                    slot_datetime=current_slot,
                    practitioner_name=practitioner.name,
                    practitioner_id=practitioner.id,
                    location_name=location.name if location else "Unknown",
                    location_id=location.id if location else None,
                    duration_minutes=schedule.slot_minutes,
                    specialty=practitioner.specialty
                ))

            current_slot += timedelta(minutes=schedule.slot_minutes)

        return slots

    async def _deduplicate_slots(
        self,
        slots: List[AppointmentSlot]
    ) -> List[AppointmentSlot]:
        """Remove duplicate slots"""
        seen = set()
        unique = []

        for slot in slots:
            key = (
                slot.slot_datetime,
                slot.practitioner_name,
                slot.location_name
            )
            if key not in seen:
                unique.append(slot)
                seen.add(key)

        return unique

    async def _filter_booked_slots(
        self,
        slots: List[AppointmentSlot]
    ) -> List[AppointmentSlot]:
        """Remove slots that are already booked"""
        if not slots:
            return []

        # Get all confirmed appointments in the relevant time range
        min_time = min(s.slot_datetime for s in slots)
        max_time = max(s.slot_datetime for s in slots)

        booked = self.db.query(Appointment).filter(
            and_(
                Appointment.confirmed_start >= min_time,
                Appointment.confirmed_start <= max_time,
                Appointment.status == AppointmentStatus.CONFIRMED.value
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
            if (slot.slot_datetime, slot.practitioner_name) not in booked_set
        ]

        return available

    def _score_slots_by_preferences(
        self,
        slots: List[AppointmentSlot],
        preferences: SlotPreferences
    ) -> List[AppointmentSlot]:
        """
        Score and rank slots by how well they match preferences

        Scoring:
        - Exact day match: +100
        - Time within 1 hour: +50
        - Time within 2 hours: +25
        - Location match: +30
        - Practitioner match: +40
        """
        scored = []

        for slot in slots:
            score = 0

            # Day preference
            if preferences.preferred_day is not None:
                if slot.slot_datetime.weekday() == preferences.preferred_day:
                    score += 100

            # Time preference (minutes from midnight)
            if preferences.preferred_time_minutes is not None:
                slot_minutes = slot.slot_datetime.hour * 60 + slot.slot_datetime.minute
                time_diff = abs(slot_minutes - preferences.preferred_time_minutes)

                if time_diff <= 60:  # Within 1 hour
                    score += 50
                elif time_diff <= 120:  # Within 2 hours
                    score += 25

            # Location preference
            if preferences.preferred_location:
                if preferences.preferred_location.lower() in slot.location_name.lower():
                    score += 30

            # Practitioner preference
            if preferences.preferred_practitioner:
                if preferences.preferred_practitioner.lower() in slot.practitioner_name.lower():
                    score += 40

            # Sooner is better (slight preference for earlier dates)
            days_from_now = (slot.slot_datetime.date() - datetime.utcnow().date()).days
            score -= days_from_now * 0.5

            scored.append((score, slot))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        return [slot for score, slot in scored]

    # ==================== Slot Presentation ====================

    async def present_slots_to_user(
        self,
        conversation_id: UUID,
        patient_phone: str,
        max_slots: int = 5
    ) -> SlotsAvailable:
        """
        Find slots and present them to user via WhatsApp

        Returns formatted message with slot options
        """
        # Find available slots
        slots = await self.find_available_slots(conversation_id, max_slots=max_slots)

        if not slots:
            # No slots available
            message = (
                "I'm sorry, I couldn't find any available appointments matching your preferences. "
                "Would you like to:\n"
                "1. Try different dates/times\n"
                "2. See availability at other locations\n"
                "3. Join the waitlist"
            )

            if twilio_client:
                twilio_client.send_message(to=patient_phone, body=message)

            return SlotsAvailable(
                conversation_id=conversation_id,
                slots=[],
                message_to_user=message,
                total_slots=0
            )

        # Format slots for presentation
        message = self._format_slots_message(slots)

        # Store slots in conversation state
        state_service = ConversationStateService(str(conversation_id))
        await state_service.set_available_slots(
            [slot.dict() for slot in slots]
        )

        # Send to user
        if twilio_client:
            twilio_client.send_message(to=patient_phone, body=message)

        return SlotsAvailable(
            conversation_id=conversation_id,
            slots=slots,
            message_to_user=message,
            total_slots=len(slots)
        )

    def _format_slots_message(self, slots: List[AppointmentSlot]) -> str:
        """Format slots into user-friendly message"""
        message = "Great! Here are some available appointment times:\n\n"

        for i, slot in enumerate(slots, 1):
            message += (
                f"{i}. {slot.formatted_datetime}\n"
                f"   📍 {slot.location_name}\n"
                f"   👨‍⚕️ Dr. {slot.practitioner_name}\n\n"
            )

        message += "Please reply with the number of your preferred time slot (e.g., '1', '2', '3'), or say 'none' if you'd like different options."

        return message

    # ==================== Slot Selection ====================

    async def handle_slot_reply(
        self,
        conversation_id: UUID,
        user_text: str
    ) -> SlotSelectionResult:
        """
        Process user's reply to slot options

        Handles:
        - Numeric selection (1, 2, 3...)
        - Text selection ("first", "second"...)
        - Time-based selection ("10:00 AM")
        - Rejection ("none", "no")
        - Ambiguous responses
        """
        try:
            # Get available slots from state
            state_service = ConversationStateService(str(conversation_id))
            slots_data = await state_service.get_available_slots()

            if not slots_data:
                return SlotSelectionResult(
                    success=False,
                    message="No slots found in conversation state",
                    action=SlotSelectionAction.AMBIGUOUS,
                    needs_clarification=True,
                    follow_up_message="I'm sorry, I lost track of the appointment options. Let me find new time slots for you."
                )

            slots = [AppointmentSlot(**s) for s in slots_data]

            # Parse user's choice
            choice = self._parse_slot_choice(user_text, len(slots))

            if choice["type"] == "none":
                # User rejected all slots
                await state_service.clear_slot_selection()
                return SlotSelectionResult(
                    success=True,
                    message="User rejected slots",
                    action=SlotSelectionAction.REJECT,
                    follow_up_message="No problem! Let me find some different appointment times for you."
                )

            elif choice["type"] == "index":
                # User selected slot by number
                index = choice["value"] - 1  # Convert to 0-based
                selected_slot = slots[index]

                # Confirm appointment
                result = await self._confirm_slot_selection(
                    conversation_id=conversation_id,
                    selected_slot=selected_slot,
                    state_service=state_service
                )

                return result

            elif choice["type"] == "ambiguous":
                # Couldn't understand user's choice
                return SlotSelectionResult(
                    success=False,
                    message="Ambiguous slot selection",
                    action=SlotSelectionAction.AMBIGUOUS,
                    needs_clarification=True,
                    follow_up_message=(
                        "I'm not sure which time slot you meant. "
                        "Please reply with just the number (1, 2, 3, etc.) of your preferred slot."
                    )
                )

        except Exception as e:
            logger.error(f"Error handling slot reply: {e}", exc_info=True)
            return SlotSelectionResult(
                success=False,
                message=f"Error processing selection: {str(e)}",
                action=SlotSelectionAction.AMBIGUOUS,
                needs_clarification=True
            )

    def _parse_slot_choice(
        self,
        user_text: str,
        total_slots: int
    ) -> Dict[str, Any]:
        """
        Parse user's slot selection

        Returns:
            {"type": "index", "value": 1}  # Selected slot 1
            {"type": "none"}                # Rejected all
            {"type": "ambiguous"}           # Couldn't parse
        """
        text = user_text.strip().lower()

        # Check for rejection
        if any(word in text for word in ["none", "no", "nothing", "different", "other"]):
            return {"type": "none"}

        # Check for numeric selection (1, 2, 3...)
        match = re.search(r"\b(\d+)\b", text)
        if match:
            slot_num = int(match.group(1))
            if 1 <= slot_num <= total_slots:
                return {"type": "index", "value": slot_num}

        # Check for word numbers (first, second, third...)
        words_to_num = {
            "first": 1, "1st": 1,
            "second": 2, "2nd": 2,
            "third": 3, "3rd": 3,
            "fourth": 4, "4th": 4,
            "fifth": 5, "5th": 5
        }
        for word, num in words_to_num.items():
            if word in text and num <= total_slots:
                return {"type": "index", "value": num}

        # Couldn't parse
        return {"type": "ambiguous"}

    async def _confirm_slot_selection(
        self,
        conversation_id: UUID,
        selected_slot: AppointmentSlot,
        state_service: ConversationStateService
    ) -> SlotSelectionResult:
        """
        Confirm and book the selected slot

        Creates appointment record and sends confirmation
        """
        try:
            # Get patient info from state
            extracted_data = await state_service.get_extracted_data()
            patient_phone = await state_service.get_patient_phone()
            patient_id = extracted_data.get("patient_id")

            if not patient_id:
                # Try to find/create patient
                patient_id = await self._find_or_create_patient(
                    phone=patient_phone,
                    name=extracted_data.get("patient.name")
                )

            # Create appointment
            appointment = Appointment(
                id=uuid4(),
                patient_id=UUID(patient_id) if isinstance(patient_id, str) else patient_id,
                practitioner_id=selected_slot.practitioner_id,
                practitioner_name=selected_slot.practitioner_name,
                location_id=selected_slot.location_id,
                location_name=selected_slot.location_name,
                status=AppointmentStatus.CONFIRMED.value,
                confirmed_start=selected_slot.slot_datetime,
                confirmed_end=selected_slot.slot_datetime + timedelta(minutes=selected_slot.duration_minutes),
                channel_origin="whatsapp",
                reason=extracted_data.get("intake.chief_complaint.text"),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            self.db.add(appointment)
            self.db.commit()
            self.db.refresh(appointment)

            # Store appointment ID in state
            await state_service.set_field("appointment_id", str(appointment.id))

            # Clear slot selection state
            await state_service.clear_slot_selection()

            # Send confirmation message
            confirmation_message = (
                f"✅ Appointment Confirmed!\n\n"
                f"📅 {selected_slot.formatted_datetime}\n"
                f"👨‍⚕️ Dr. {selected_slot.practitioner_name}\n"
                f"📍 {selected_slot.location_name}\n\n"
                f"You'll receive a reminder before your appointment. "
                f"If you need to reschedule, just let me know!"
            )

            if twilio_client and patient_phone:
                twilio_client.send_message(to=patient_phone, body=confirmation_message)

            # Publish event
            await publish_event(
                event_type=EventType.APPOINTMENT_CREATED,
                entity_id=appointment.id,
                entity_type="appointment",
                data={
                    "appointment_id": str(appointment.id),
                    "patient_id": str(appointment.patient_id),
                    "start_time": appointment.confirmed_start.isoformat()
                }
            )

            logger.info(f"Appointment {appointment.id} confirmed for conversation {conversation_id}")

            return SlotSelectionResult(
                success=True,
                message="Appointment confirmed",
                action=SlotSelectionAction.CONFIRM,
                appointment_id=appointment.id,
                follow_up_message=confirmation_message
            )

        except Exception as e:
            logger.error(f"Error confirming appointment: {e}", exc_info=True)
            return SlotSelectionResult(
                success=False,
                message=f"Failed to confirm appointment: {str(e)}",
                action=SlotSelectionAction.AMBIGUOUS,
                needs_clarification=True,
                follow_up_message="I'm sorry, there was an error booking your appointment. Please try again."
            )

    async def _find_or_create_patient(
        self,
        phone: str,
        name: Optional[str] = None
    ) -> UUID:
        """Find patient by phone or create new patient"""
        # Try to find existing patient
        patient = self.db.query(Patient).filter(
            Patient.phone == phone
        ).first()

        if patient:
            return patient.id

        # Create new patient
        patient = Patient(
            id=uuid4(),
            phone=phone,
            name=name or "Patient",
            created_at=datetime.utcnow()
        )

        self.db.add(patient)
        self.db.commit()
        self.db.refresh(patient)

        logger.info(f"Created new patient {patient.id} for phone {phone}")
        return patient.id

    # ==================== Appointment Management ====================

    async def get_appointment(self, appointment_id: UUID) -> Optional[Appointment]:
        """Get appointment by ID"""
        return self.db.query(Appointment).filter(
            Appointment.id == appointment_id
        ).first()

    async def update_appointment(
        self,
        appointment_id: UUID,
        update_data: AppointmentUpdate
    ) -> Optional[Appointment]:
        """Update appointment"""
        appointment = await self.get_appointment(appointment_id)
        if not appointment:
            return None

        if update_data.status:
            appointment.status = update_data.status.value

        if update_data.confirmed_start:
            appointment.confirmed_start = update_data.confirmed_start

        if update_data.confirmed_end:
            appointment.confirmed_end = update_data.confirmed_end

        if update_data.notes:
            appointment.notes = update_data.notes

        appointment.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(appointment)

        return appointment

    async def cancel_appointment(
        self,
        appointment_id: UUID,
        notify_patient: bool = True
    ) -> Optional[Appointment]:
        """Cancel appointment"""
        appointment = await self.update_appointment(
            appointment_id,
            AppointmentUpdate(status=AppointmentStatus.CANCELED)
        )

        if appointment and notify_patient:
            # TODO: Send cancellation notification
            pass

        return appointment

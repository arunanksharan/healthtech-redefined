"""
Telehealth Scheduling Service

Handles scheduling of telehealth appointments:
- Appointment types and configuration
- Provider availability
- Time zone handling
- Reminders and notifications
- Calendar integration

EPIC-007: US-007.4 Telehealth Scheduling
"""

from datetime import datetime, timezone, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import logging
import pytz

logger = logging.getLogger(__name__)


class AppointmentType(str, Enum):
    """Types of telehealth appointments."""
    VIDEO_VISIT = "video_visit"
    PHONE_CALL = "phone_call"
    FOLLOW_UP = "follow_up"
    NEW_PATIENT = "new_patient"
    GROUP_THERAPY = "group_therapy"
    URGENT_CARE = "urgent_care"
    MENTAL_HEALTH = "mental_health"
    CHRONIC_CARE = "chronic_care"


class AppointmentStatus(str, Enum):
    """Telehealth appointment status."""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class ReminderType(str, Enum):
    """Types of appointment reminders."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


@dataclass
class AppointmentTypeConfig:
    """Configuration for an appointment type."""
    type_code: str
    name: str
    duration_minutes: int = 30
    buffer_minutes: int = 5  # Time between appointments

    # Pricing
    base_price: float = 0
    requires_payment: bool = False

    # Requirements
    requires_insurance: bool = False
    new_patients_allowed: bool = True
    min_age: Optional[int] = None
    max_age: Optional[int] = None

    # Forms
    required_forms: List[str] = field(default_factory=list)

    # Availability
    available_days: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])  # Mon-Fri
    earliest_time: str = "08:00"
    latest_time: str = "17:00"


@dataclass
class ProviderSlot:
    """An available appointment slot for a provider."""
    slot_id: str
    provider_id: str
    start_time: datetime
    end_time: datetime
    appointment_type: AppointmentType
    is_available: bool = True
    tenant_id: Optional[str] = None


@dataclass
class Reminder:
    """Appointment reminder."""
    reminder_id: str
    appointment_id: str
    reminder_type: ReminderType
    scheduled_for: datetime
    sent_at: Optional[datetime] = None
    content: str = ""


@dataclass
class TelehealthAppointment:
    """A telehealth appointment."""
    appointment_id: str
    tenant_id: str

    # Participants
    patient_id: str
    provider_id: str
    patient_name: Optional[str] = None
    provider_name: Optional[str] = None

    # Type and timing
    appointment_type: AppointmentType = AppointmentType.VIDEO_VISIT
    scheduled_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    scheduled_end: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_minutes: int = 30

    # Time zones
    patient_timezone: str = "UTC"
    provider_timezone: str = "UTC"

    # Reason
    reason_for_visit: str = ""
    chief_complaint: str = ""
    diagnosis_codes: List[str] = field(default_factory=list)

    # Session
    session_id: Optional[str] = None
    join_url: Optional[str] = None

    # Status
    status: AppointmentStatus = AppointmentStatus.SCHEDULED
    confirmed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None

    # Reminders
    reminders: List[Reminder] = field(default_factory=list)

    # Billing
    copay_amount: float = 0
    payment_status: str = "pending"  # pending, paid, waived

    # Notes
    pre_visit_notes: str = ""
    post_visit_notes: str = ""

    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderSchedule:
    """Provider's weekly schedule."""
    provider_id: str
    tenant_id: str

    # Weekly availability
    weekly_hours: Dict[int, List[Tuple[str, str]]] = field(default_factory=dict)
    # Format: {0: [("09:00", "12:00"), ("13:00", "17:00")]} for Monday

    # Time zone
    timezone: str = "America/New_York"

    # Exceptions
    blocked_dates: List[date] = field(default_factory=list)
    blocked_times: List[Tuple[datetime, datetime]] = field(default_factory=list)

    # Appointment types offered
    appointment_types: List[AppointmentType] = field(default_factory=list)


class TelehealthScheduler:
    """
    Telehealth scheduling service.

    Manages:
    - Appointment booking
    - Provider availability
    - Time zone handling
    - Reminders
    """

    def __init__(self):
        self._appointments: Dict[str, TelehealthAppointment] = {}
        self._provider_schedules: Dict[str, ProviderSchedule] = {}
        self._appointment_configs: Dict[AppointmentType, AppointmentTypeConfig] = {}

        # Initialize default configs
        self._initialize_default_configs()

    def _initialize_default_configs(self):
        """Initialize default appointment type configurations."""
        self._appointment_configs = {
            AppointmentType.VIDEO_VISIT: AppointmentTypeConfig(
                type_code="video_visit",
                name="Video Visit",
                duration_minutes=30,
                buffer_minutes=5,
            ),
            AppointmentType.FOLLOW_UP: AppointmentTypeConfig(
                type_code="follow_up",
                name="Follow-up Visit",
                duration_minutes=15,
                buffer_minutes=5,
            ),
            AppointmentType.NEW_PATIENT: AppointmentTypeConfig(
                type_code="new_patient",
                name="New Patient Visit",
                duration_minutes=45,
                buffer_minutes=10,
                required_forms=["new_patient_intake", "hipaa_consent"],
            ),
            AppointmentType.URGENT_CARE: AppointmentTypeConfig(
                type_code="urgent_care",
                name="Urgent Care",
                duration_minutes=20,
                buffer_minutes=5,
            ),
            AppointmentType.MENTAL_HEALTH: AppointmentTypeConfig(
                type_code="mental_health",
                name="Mental Health Visit",
                duration_minutes=60,
                buffer_minutes=10,
            ),
        }

    async def set_provider_schedule(
        self,
        provider_id: str,
        tenant_id: str,
        weekly_hours: Dict[int, List[Tuple[str, str]]],
        timezone_str: str = "America/New_York",
        appointment_types: Optional[List[AppointmentType]] = None,
    ) -> ProviderSchedule:
        """Set a provider's weekly schedule."""
        schedule = ProviderSchedule(
            provider_id=provider_id,
            tenant_id=tenant_id,
            weekly_hours=weekly_hours,
            timezone=timezone_str,
            appointment_types=appointment_types or list(AppointmentType),
        )

        self._provider_schedules[provider_id] = schedule
        return schedule

    async def get_available_slots(
        self,
        tenant_id: str,
        provider_id: str,
        appointment_type: AppointmentType,
        start_date: date,
        end_date: date,
        patient_timezone: str = "UTC",
    ) -> List[ProviderSlot]:
        """Get available appointment slots for a provider."""
        schedule = self._provider_schedules.get(provider_id)
        if not schedule:
            return []

        config = self._appointment_configs.get(appointment_type)
        if not config:
            return []

        slots = []
        provider_tz = pytz.timezone(schedule.timezone)
        patient_tz = pytz.timezone(patient_timezone)

        current_date = start_date
        while current_date <= end_date:
            # Check if day is blocked
            if current_date in schedule.blocked_dates:
                current_date += timedelta(days=1)
                continue

            weekday = current_date.weekday()

            # Get hours for this day
            day_hours = schedule.weekly_hours.get(weekday, [])

            for start_str, end_str in day_hours:
                # Parse hours
                start_hour, start_min = map(int, start_str.split(":"))
                end_hour, end_min = map(int, end_str.split(":"))

                # Create datetime in provider timezone
                day_start = provider_tz.localize(datetime(
                    current_date.year, current_date.month, current_date.day,
                    start_hour, start_min
                ))
                day_end = provider_tz.localize(datetime(
                    current_date.year, current_date.month, current_date.day,
                    end_hour, end_min
                ))

                # Generate slots
                slot_start = day_start
                slot_duration = timedelta(minutes=config.duration_minutes)
                buffer = timedelta(minutes=config.buffer_minutes)

                while slot_start + slot_duration <= day_end:
                    slot_end = slot_start + slot_duration

                    # Check if slot is available
                    is_available = await self._check_slot_available(
                        provider_id, slot_start, slot_end
                    )

                    # Check blocked times
                    for blocked_start, blocked_end in schedule.blocked_times:
                        if slot_start < blocked_end and slot_end > blocked_start:
                            is_available = False
                            break

                    # Only include future slots
                    if slot_start > datetime.now(timezone.utc):
                        slots.append(ProviderSlot(
                            slot_id=str(uuid4()),
                            provider_id=provider_id,
                            start_time=slot_start.astimezone(patient_tz),
                            end_time=slot_end.astimezone(patient_tz),
                            appointment_type=appointment_type,
                            is_available=is_available,
                            tenant_id=tenant_id,
                        ))

                    slot_start = slot_end + buffer

            current_date += timedelta(days=1)

        return [s for s in slots if s.is_available]

    async def _check_slot_available(
        self,
        provider_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> bool:
        """Check if a slot conflicts with existing appointments."""
        for appt in self._appointments.values():
            if appt.provider_id != provider_id:
                continue
            if appt.status in (AppointmentStatus.CANCELLED, AppointmentStatus.RESCHEDULED):
                continue

            # Check overlap
            if start_time < appt.scheduled_end and end_time > appt.scheduled_start:
                return False

        return True

    async def book_appointment(
        self,
        tenant_id: str,
        patient_id: str,
        provider_id: str,
        appointment_type: AppointmentType,
        start_time: datetime,
        patient_timezone: str = "UTC",
        reason_for_visit: str = "",
        patient_name: Optional[str] = None,
        provider_name: Optional[str] = None,
    ) -> TelehealthAppointment:
        """Book a telehealth appointment."""
        config = self._appointment_configs.get(appointment_type)
        if not config:
            raise ValueError(f"Unknown appointment type: {appointment_type}")

        # Calculate end time
        end_time = start_time + timedelta(minutes=config.duration_minutes)

        # Verify slot is available
        if not await self._check_slot_available(provider_id, start_time, end_time):
            raise ValueError("Selected time slot is not available")

        # Get provider timezone
        schedule = self._provider_schedules.get(provider_id)
        provider_timezone = schedule.timezone if schedule else "UTC"

        appointment = TelehealthAppointment(
            appointment_id=str(uuid4()),
            tenant_id=tenant_id,
            patient_id=patient_id,
            provider_id=provider_id,
            patient_name=patient_name,
            provider_name=provider_name,
            appointment_type=appointment_type,
            scheduled_start=start_time,
            scheduled_end=end_time,
            duration_minutes=config.duration_minutes,
            patient_timezone=patient_timezone,
            provider_timezone=provider_timezone,
            reason_for_visit=reason_for_visit,
        )

        # Generate join URL
        appointment.join_url = f"/telehealth/join/{appointment.appointment_id}"

        # Create reminders
        await self._create_reminders(appointment)

        self._appointments[appointment.appointment_id] = appointment

        logger.info(f"Booked telehealth appointment: {appointment.appointment_id}")
        return appointment

    async def _create_reminders(self, appointment: TelehealthAppointment):
        """Create appointment reminders."""
        # 24 hours before
        appointment.reminders.append(Reminder(
            reminder_id=str(uuid4()),
            appointment_id=appointment.appointment_id,
            reminder_type=ReminderType.EMAIL,
            scheduled_for=appointment.scheduled_start - timedelta(hours=24),
            content=f"Reminder: Your telehealth appointment is tomorrow at {appointment.scheduled_start.strftime('%I:%M %p')}",
        ))

        # 1 hour before
        appointment.reminders.append(Reminder(
            reminder_id=str(uuid4()),
            appointment_id=appointment.appointment_id,
            reminder_type=ReminderType.SMS,
            scheduled_for=appointment.scheduled_start - timedelta(hours=1),
            content=f"Your telehealth appointment starts in 1 hour. Join: {appointment.join_url}",
        ))

        # 15 minutes before
        appointment.reminders.append(Reminder(
            reminder_id=str(uuid4()),
            appointment_id=appointment.appointment_id,
            reminder_type=ReminderType.PUSH,
            scheduled_for=appointment.scheduled_start - timedelta(minutes=15),
            content="Your telehealth appointment starts in 15 minutes. Click to join.",
        ))

    async def confirm_appointment(
        self,
        appointment_id: str,
    ) -> TelehealthAppointment:
        """Confirm an appointment."""
        appointment = self._appointments.get(appointment_id)
        if not appointment:
            raise ValueError(f"Appointment not found: {appointment_id}")

        appointment.status = AppointmentStatus.CONFIRMED
        appointment.confirmed_at = datetime.now(timezone.utc)
        appointment.updated_at = datetime.now(timezone.utc)

        return appointment

    async def cancel_appointment(
        self,
        appointment_id: str,
        reason: str = "",
        cancelled_by: str = "",
    ) -> TelehealthAppointment:
        """Cancel an appointment."""
        appointment = self._appointments.get(appointment_id)
        if not appointment:
            raise ValueError(f"Appointment not found: {appointment_id}")

        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancelled_at = datetime.now(timezone.utc)
        appointment.cancellation_reason = reason
        appointment.updated_at = datetime.now(timezone.utc)

        logger.info(f"Cancelled appointment: {appointment_id}")
        return appointment

    async def reschedule_appointment(
        self,
        appointment_id: str,
        new_start_time: datetime,
    ) -> TelehealthAppointment:
        """Reschedule an appointment."""
        appointment = self._appointments.get(appointment_id)
        if not appointment:
            raise ValueError(f"Appointment not found: {appointment_id}")

        # Calculate new end time
        new_end_time = new_start_time + timedelta(minutes=appointment.duration_minutes)

        # Check availability
        if not await self._check_slot_available(appointment.provider_id, new_start_time, new_end_time):
            raise ValueError("New time slot is not available")

        # Mark original as rescheduled
        appointment.status = AppointmentStatus.RESCHEDULED

        # Create new appointment
        new_appointment = TelehealthAppointment(
            appointment_id=str(uuid4()),
            tenant_id=appointment.tenant_id,
            patient_id=appointment.patient_id,
            provider_id=appointment.provider_id,
            patient_name=appointment.patient_name,
            provider_name=appointment.provider_name,
            appointment_type=appointment.appointment_type,
            scheduled_start=new_start_time,
            scheduled_end=new_end_time,
            duration_minutes=appointment.duration_minutes,
            patient_timezone=appointment.patient_timezone,
            provider_timezone=appointment.provider_timezone,
            reason_for_visit=appointment.reason_for_visit,
            metadata={"rescheduled_from": appointment_id},
        )

        new_appointment.join_url = f"/telehealth/join/{new_appointment.appointment_id}"
        await self._create_reminders(new_appointment)

        self._appointments[new_appointment.appointment_id] = new_appointment

        logger.info(f"Rescheduled appointment {appointment_id} to {new_appointment.appointment_id}")
        return new_appointment

    async def get_appointment(
        self,
        appointment_id: str,
    ) -> Optional[TelehealthAppointment]:
        """Get an appointment by ID."""
        return self._appointments.get(appointment_id)

    async def get_patient_appointments(
        self,
        tenant_id: str,
        patient_id: str,
        include_past: bool = False,
    ) -> List[TelehealthAppointment]:
        """Get appointments for a patient."""
        appointments = [
            a for a in self._appointments.values()
            if a.tenant_id == tenant_id and a.patient_id == patient_id
        ]

        if not include_past:
            now = datetime.now(timezone.utc)
            appointments = [a for a in appointments if a.scheduled_end > now]

        return sorted(appointments, key=lambda a: a.scheduled_start)

    async def get_provider_appointments(
        self,
        tenant_id: str,
        provider_id: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> List[TelehealthAppointment]:
        """Get appointments for a provider."""
        appointments = [
            a for a in self._appointments.values()
            if a.tenant_id == tenant_id and a.provider_id == provider_id
        ]

        if date_from:
            start_datetime = datetime.combine(date_from, datetime.min.time()).replace(tzinfo=timezone.utc)
            appointments = [a for a in appointments if a.scheduled_start >= start_datetime]

        if date_to:
            end_datetime = datetime.combine(date_to, datetime.max.time()).replace(tzinfo=timezone.utc)
            appointments = [a for a in appointments if a.scheduled_start <= end_datetime]

        return sorted(appointments, key=lambda a: a.scheduled_start)

    async def get_pending_reminders(self) -> List[Reminder]:
        """Get reminders that need to be sent."""
        now = datetime.now(timezone.utc)
        pending = []

        for appointment in self._appointments.values():
            if appointment.status in (AppointmentStatus.CANCELLED, AppointmentStatus.RESCHEDULED):
                continue

            for reminder in appointment.reminders:
                if reminder.sent_at is None and reminder.scheduled_for <= now:
                    pending.append(reminder)

        return pending

    async def mark_reminder_sent(
        self,
        reminder_id: str,
        appointment_id: str,
    ):
        """Mark a reminder as sent."""
        appointment = self._appointments.get(appointment_id)
        if not appointment:
            return

        for reminder in appointment.reminders:
            if reminder.reminder_id == reminder_id:
                reminder.sent_at = datetime.now(timezone.utc)
                break

    def generate_ics_content(
        self,
        appointment: TelehealthAppointment,
    ) -> str:
        """Generate ICS calendar content for an appointment."""
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Healthcare PRM//Telehealth//EN",
            "BEGIN:VEVENT",
            f"UID:{appointment.appointment_id}@prm.healthcare",
            f"DTSTAMP:{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
            f"DTSTART:{appointment.scheduled_start.strftime('%Y%m%dT%H%M%SZ')}",
            f"DTEND:{appointment.scheduled_end.strftime('%Y%m%dT%H%M%SZ')}",
            f"SUMMARY:Telehealth Appointment with {appointment.provider_name or 'Provider'}",
            f"DESCRIPTION:Join URL: {appointment.join_url}\\n\\nReason: {appointment.reason_for_visit}",
            f"URL:{appointment.join_url}",
            "END:VEVENT",
            "END:VCALENDAR",
        ]

        return "\r\n".join(lines)


# Global scheduler instance
telehealth_scheduler = TelehealthScheduler()

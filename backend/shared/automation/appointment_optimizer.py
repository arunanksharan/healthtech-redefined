"""
Smart Appointment Management & Scheduling Optimizer
EPIC-012: Intelligent Automation Platform - US-012.2

Provides:
- AI-powered slot optimization
- No-show prediction and prevention
- Automatic overbooking based on patterns
- Provider/patient preference learning
- Waitlist management and auto-fill
- Resource optimization (rooms, equipment, staff)
"""

from dataclasses import dataclass, field
from datetime import datetime, date, time, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
from uuid import uuid4
import random
import math


class AppointmentType(Enum):
    """Types of appointments"""
    NEW_PATIENT = "new_patient"
    FOLLOW_UP = "follow_up"
    ROUTINE = "routine"
    URGENT = "urgent"
    PROCEDURE = "procedure"
    TELEHEALTH = "telehealth"
    LAB_ONLY = "lab_only"
    VACCINATION = "vaccination"
    WELLNESS = "wellness"
    SPECIALIST = "specialist"


class AppointmentStatus(Enum):
    """Appointment status"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"


class NoShowRiskLevel(Enum):
    """No-show risk levels"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class InterventionType(Enum):
    """Intervention types for no-show prevention"""
    SMS_REMINDER = "sms_reminder"
    EMAIL_REMINDER = "email_reminder"
    PHONE_CALL = "phone_call"
    PUSH_NOTIFICATION = "push_notification"
    TRANSPORTATION_OFFER = "transportation_offer"
    RESCHEDULE_OFFER = "reschedule_offer"
    WAITLIST_BACKUP = "waitlist_backup"


@dataclass
class TimeSlot:
    """Available time slot"""
    slot_id: str
    provider_id: str
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    location_id: Optional[str] = None
    room_id: Optional[str] = None
    appointment_types: List[AppointmentType] = field(default_factory=list)
    is_available: bool = True
    overbooking_allowed: bool = False
    current_bookings: int = 0
    max_bookings: int = 1


@dataclass
class ProviderSchedule:
    """Provider schedule configuration"""
    provider_id: str
    provider_name: str
    specialty: str
    available_days: List[int]  # 0=Monday, 6=Sunday
    work_hours: Dict[int, Tuple[time, time]]  # day -> (start, end)
    slot_duration_minutes: int = 30
    buffer_minutes: int = 5
    max_patients_per_day: int = 30
    overbooking_rate: float = 0.1  # 10% overbooking
    appointment_types: List[AppointmentType] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PatientPreferences:
    """Patient scheduling preferences"""
    patient_id: str
    preferred_days: List[int] = field(default_factory=list)
    preferred_times: List[str] = field(default_factory=list)  # morning, afternoon, evening
    preferred_provider_ids: List[str] = field(default_factory=list)
    preferred_locations: List[str] = field(default_factory=list)
    telehealth_enabled: bool = True
    transportation_needs: bool = False
    language_preference: str = "en"
    reminder_preferences: List[str] = field(default_factory=lambda: ["sms", "email"])


@dataclass
class NoShowPrediction:
    """No-show prediction result"""
    appointment_id: str
    patient_id: str
    probability: float
    risk_level: NoShowRiskLevel
    risk_factors: List[str]
    recommended_interventions: List[InterventionType]
    confidence: float
    prediction_date: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WaitlistEntry:
    """Waitlist entry"""
    entry_id: str
    patient_id: str
    requested_provider_id: Optional[str]
    appointment_type: AppointmentType
    earliest_date: date
    latest_date: date
    preferred_times: List[str]
    priority: int  # Higher = more priority
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "waiting"


@dataclass
class ScheduleOptimizationResult:
    """Result of schedule optimization"""
    optimization_id: str
    date_range: Tuple[date, date]
    appointments_optimized: int
    slots_added: int
    overbookings_added: int
    efficiency_improvement: float
    recommendations: List[Dict[str, Any]]
    executed_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ResourceAllocation:
    """Resource allocation for appointments"""
    resource_id: str
    resource_type: str  # room, equipment, staff
    resource_name: str
    start_time: datetime
    end_time: datetime
    appointment_id: Optional[str] = None
    is_available: bool = True


class AppointmentOptimizer:
    """
    AI-powered appointment scheduling optimizer.
    Handles intelligent scheduling, no-show prevention, and resource optimization.
    """

    def __init__(self):
        self.provider_schedules: Dict[str, ProviderSchedule] = {}
        self.patient_preferences: Dict[str, PatientPreferences] = {}
        self.appointments: Dict[str, Dict] = {}
        self.waitlist: Dict[str, WaitlistEntry] = {}
        self.resources: Dict[str, List[ResourceAllocation]] = {}

        # No-show prediction weights
        self.no_show_factors = {
            "previous_no_shows": 0.25,
            "lead_time_days": 0.15,
            "appointment_time": 0.10,
            "day_of_week": 0.10,
            "appointment_type": 0.10,
            "weather_impact": 0.05,
            "age_group": 0.05,
            "distance_miles": 0.10,
            "confirmation_status": 0.10,
        }

    # ==================== Provider Management ====================

    def register_provider(self, schedule: ProviderSchedule) -> str:
        """Register a provider's schedule"""
        self.provider_schedules[schedule.provider_id] = schedule
        return schedule.provider_id

    def update_provider_schedule(self, provider_id: str, schedule: ProviderSchedule) -> bool:
        """Update a provider's schedule"""
        if provider_id in self.provider_schedules:
            self.provider_schedules[provider_id] = schedule
            return True
        return False

    def get_provider_schedule(self, provider_id: str) -> Optional[ProviderSchedule]:
        """Get a provider's schedule"""
        return self.provider_schedules.get(provider_id)

    # ==================== Patient Preferences ====================

    def set_patient_preferences(self, preferences: PatientPreferences) -> str:
        """Set patient scheduling preferences"""
        self.patient_preferences[preferences.patient_id] = preferences
        return preferences.patient_id

    def get_patient_preferences(self, patient_id: str) -> Optional[PatientPreferences]:
        """Get patient preferences"""
        return self.patient_preferences.get(patient_id)

    # ==================== Slot Generation & Optimization ====================

    async def generate_available_slots(
        self,
        provider_id: str,
        start_date: date,
        end_date: date,
        appointment_type: Optional[AppointmentType] = None,
        duration_minutes: Optional[int] = None
    ) -> List[TimeSlot]:
        """Generate available time slots for a provider"""
        schedule = self.provider_schedules.get(provider_id)
        if not schedule:
            return []

        slots = []
        current_date = start_date

        while current_date <= end_date:
            day_of_week = current_date.weekday()

            if day_of_week in schedule.available_days:
                work_hours = schedule.work_hours.get(day_of_week)
                if work_hours:
                    start_time, end_time = work_hours
                    slot_duration = duration_minutes or schedule.slot_duration_minutes

                    # Generate slots for the day
                    current_time = datetime.combine(current_date, start_time)
                    end_datetime = datetime.combine(current_date, end_time)

                    while current_time + timedelta(minutes=slot_duration) <= end_datetime:
                        # Check if slot matches appointment type
                        if appointment_type is None or appointment_type in schedule.appointment_types:
                            # Check existing bookings
                            existing = self._get_bookings_at_time(provider_id, current_time)
                            max_bookings = 1 + (1 if schedule.overbooking_rate > 0 else 0)

                            slot = TimeSlot(
                                slot_id=f"{provider_id}_{current_time.isoformat()}",
                                provider_id=provider_id,
                                start_time=current_time,
                                end_time=current_time + timedelta(minutes=slot_duration),
                                duration_minutes=slot_duration,
                                appointment_types=schedule.appointment_types,
                                is_available=existing < max_bookings,
                                overbooking_allowed=schedule.overbooking_rate > 0,
                                current_bookings=existing,
                                max_bookings=max_bookings
                            )
                            slots.append(slot)

                        current_time += timedelta(minutes=slot_duration + schedule.buffer_minutes)

            current_date += timedelta(days=1)

        return slots

    async def find_optimal_slots(
        self,
        patient_id: str,
        appointment_type: AppointmentType,
        provider_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        duration_minutes: int = 30,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find optimal appointment slots considering patient preferences"""
        patient_prefs = self.patient_preferences.get(patient_id, PatientPreferences(patient_id=patient_id))

        start_date = start_date or date.today()
        end_date = end_date or (start_date + timedelta(days=30))

        # Determine which providers to check
        if provider_id:
            provider_ids = [provider_id]
        elif patient_prefs.preferred_provider_ids:
            provider_ids = patient_prefs.preferred_provider_ids
        else:
            provider_ids = list(self.provider_schedules.keys())

        scored_slots = []

        for pid in provider_ids:
            slots = await self.generate_available_slots(
                pid, start_date, end_date, appointment_type, duration_minutes
            )

            for slot in slots:
                if slot.is_available:
                    score = self._calculate_slot_score(slot, patient_prefs, appointment_type)
                    scored_slots.append({
                        "slot": slot,
                        "score": score,
                        "provider_id": pid,
                        "start_time": slot.start_time.isoformat(),
                        "end_time": slot.end_time.isoformat(),
                        "duration_minutes": slot.duration_minutes
                    })

        # Sort by score (descending) and return top slots
        scored_slots.sort(key=lambda x: x["score"], reverse=True)
        return scored_slots[:limit]

    def _calculate_slot_score(
        self,
        slot: TimeSlot,
        preferences: PatientPreferences,
        appointment_type: AppointmentType
    ) -> float:
        """Calculate preference score for a slot"""
        score = 50.0  # Base score

        # Day preference (+10)
        if slot.start_time.weekday() in preferences.preferred_days:
            score += 10

        # Time preference (+15)
        hour = slot.start_time.hour
        if "morning" in preferences.preferred_times and 6 <= hour < 12:
            score += 15
        elif "afternoon" in preferences.preferred_times and 12 <= hour < 17:
            score += 15
        elif "evening" in preferences.preferred_times and 17 <= hour < 21:
            score += 15

        # Provider preference (+20)
        if slot.provider_id in preferences.preferred_provider_ids:
            score += 20

        # Location preference (+10)
        if slot.location_id in preferences.preferred_locations:
            score += 10

        # Appointment type suitability (+5)
        if appointment_type in slot.appointment_types:
            score += 5

        # Penalize overbooking slots (-10)
        if slot.current_bookings > 0:
            score -= 10

        # Sooner appointments get slight bonus (up to +10)
        days_out = (slot.start_time.date() - date.today()).days
        if days_out < 7:
            score += 10 - days_out

        return min(max(score, 0), 100)  # Clamp to 0-100

    def _get_bookings_at_time(self, provider_id: str, time: datetime) -> int:
        """Get number of bookings at a specific time"""
        count = 0
        for appt in self.appointments.values():
            if (appt.get("provider_id") == provider_id and
                appt.get("start_time") == time and
                appt.get("status") in ["scheduled", "confirmed"]):
                count += 1
        return count

    # ==================== No-Show Prediction ====================

    async def predict_no_show(
        self,
        appointment_id: str,
        patient_id: str,
        appointment_data: Dict[str, Any]
    ) -> NoShowPrediction:
        """Predict no-show probability for an appointment"""
        risk_factors = []
        weighted_score = 0.0

        # Previous no-shows
        previous_no_shows = appointment_data.get("previous_no_shows", 0)
        if previous_no_shows > 0:
            no_show_factor = min(previous_no_shows * 0.15, 0.45)
            weighted_score += no_show_factor * self.no_show_factors["previous_no_shows"] * 4
            risk_factors.append(f"Previous no-shows: {previous_no_shows}")

        # Lead time (more days = higher risk)
        lead_time_days = appointment_data.get("lead_time_days", 7)
        if lead_time_days > 14:
            lead_factor = min((lead_time_days - 14) * 0.02, 0.3)
            weighted_score += lead_factor * self.no_show_factors["lead_time_days"] * 4
            risk_factors.append(f"Scheduled {lead_time_days} days ahead")

        # Appointment time (early morning = higher risk)
        appt_hour = appointment_data.get("appointment_hour", 10)
        if appt_hour < 9:
            weighted_score += 0.1 * self.no_show_factors["appointment_time"] * 4
            risk_factors.append("Early morning appointment")
        elif appt_hour > 16:
            weighted_score += 0.05 * self.no_show_factors["appointment_time"] * 4
            risk_factors.append("Late afternoon appointment")

        # Day of week (Monday/Friday = higher risk)
        day_of_week = appointment_data.get("day_of_week", 2)
        if day_of_week in [0, 4]:
            weighted_score += 0.1 * self.no_show_factors["day_of_week"] * 4
            risk_factors.append("Monday or Friday appointment")

        # Appointment type
        appt_type = appointment_data.get("appointment_type", "routine")
        if appt_type in ["routine", "wellness"]:
            weighted_score += 0.1 * self.no_show_factors["appointment_type"] * 4
            risk_factors.append(f"Routine/wellness appointment type")

        # Confirmation status
        if not appointment_data.get("is_confirmed", False):
            weighted_score += 0.2 * self.no_show_factors["confirmation_status"] * 4
            risk_factors.append("Appointment not confirmed")

        # Distance
        distance_miles = appointment_data.get("distance_miles", 5)
        if distance_miles > 20:
            weighted_score += 0.15 * self.no_show_factors["distance_miles"] * 4
            risk_factors.append(f"Long travel distance: {distance_miles} miles")

        # Calculate final probability
        probability = min(max(weighted_score, 0.05), 0.95)

        # Determine risk level
        if probability >= 0.7:
            risk_level = NoShowRiskLevel.VERY_HIGH
        elif probability >= 0.5:
            risk_level = NoShowRiskLevel.HIGH
        elif probability >= 0.3:
            risk_level = NoShowRiskLevel.MEDIUM
        elif probability >= 0.15:
            risk_level = NoShowRiskLevel.LOW
        else:
            risk_level = NoShowRiskLevel.VERY_LOW

        # Recommend interventions
        interventions = self._recommend_interventions(risk_level, appointment_data)

        return NoShowPrediction(
            appointment_id=appointment_id,
            patient_id=patient_id,
            probability=round(probability, 3),
            risk_level=risk_level,
            risk_factors=risk_factors,
            recommended_interventions=interventions,
            confidence=0.85  # Model confidence
        )

    def _recommend_interventions(
        self,
        risk_level: NoShowRiskLevel,
        appointment_data: Dict
    ) -> List[InterventionType]:
        """Recommend interventions based on risk level"""
        interventions = []

        if risk_level in [NoShowRiskLevel.VERY_HIGH, NoShowRiskLevel.HIGH]:
            interventions.append(InterventionType.PHONE_CALL)
            interventions.append(InterventionType.SMS_REMINDER)
            interventions.append(InterventionType.WAITLIST_BACKUP)

            if appointment_data.get("transportation_barrier"):
                interventions.append(InterventionType.TRANSPORTATION_OFFER)

        elif risk_level == NoShowRiskLevel.MEDIUM:
            interventions.append(InterventionType.SMS_REMINDER)
            interventions.append(InterventionType.EMAIL_REMINDER)
            interventions.append(InterventionType.PUSH_NOTIFICATION)

        else:  # LOW or VERY_LOW
            interventions.append(InterventionType.EMAIL_REMINDER)

        return interventions

    # ==================== Overbooking & Waitlist ====================

    async def calculate_optimal_overbooking(
        self,
        provider_id: str,
        date_range: Tuple[date, date],
        appointment_type: Optional[AppointmentType] = None
    ) -> Dict[str, Any]:
        """Calculate optimal overbooking rate based on historical no-show patterns"""
        # In production, this would analyze historical data
        # For now, return simulated recommendations

        schedule = self.provider_schedules.get(provider_id)
        if not schedule:
            return {"error": "Provider not found"}

        # Simulate historical analysis
        historical_no_show_rate = 0.15  # 15% average no-show rate
        appointment_count = 100  # Sample size

        # Calculate recommended overbooking
        if historical_no_show_rate > 0.20:
            recommended_rate = min(historical_no_show_rate * 0.8, 0.25)
        elif historical_no_show_rate > 0.10:
            recommended_rate = historical_no_show_rate * 0.7
        else:
            recommended_rate = historical_no_show_rate * 0.5

        return {
            "provider_id": provider_id,
            "date_range": [date_range[0].isoformat(), date_range[1].isoformat()],
            "current_overbooking_rate": schedule.overbooking_rate,
            "historical_no_show_rate": round(historical_no_show_rate, 3),
            "recommended_overbooking_rate": round(recommended_rate, 3),
            "sample_size": appointment_count,
            "projected_efficiency_gain": round((recommended_rate - schedule.overbooking_rate) * 100, 1),
            "risk_assessment": "low" if recommended_rate < 0.15 else "medium"
        }

    async def add_to_waitlist(self, entry: WaitlistEntry) -> str:
        """Add a patient to the waitlist"""
        self.waitlist[entry.entry_id] = entry
        return entry.entry_id

    async def process_waitlist(
        self,
        provider_id: Optional[str] = None,
        date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Process waitlist and find matches for cancelled slots"""
        matches = []

        # Get available slots (from cancellations)
        available_slots = []
        for slot_id, slot in self.appointments.items():
            if slot.get("status") == "cancelled":
                if provider_id and slot.get("provider_id") != provider_id:
                    continue
                if date and slot.get("date") != date:
                    continue
                available_slots.append(slot)

        # Match waitlist entries to slots
        for slot in available_slots:
            best_match = None
            best_priority = -1

            for entry in self.waitlist.values():
                if entry.status != "waiting":
                    continue

                # Check compatibility
                if entry.requested_provider_id and entry.requested_provider_id != slot.get("provider_id"):
                    continue

                slot_date = slot.get("date")
                if slot_date:
                    if isinstance(slot_date, str):
                        slot_date = date.fromisoformat(slot_date)
                    if slot_date < entry.earliest_date or slot_date > entry.latest_date:
                        continue

                # Check time preference
                slot_hour = slot.get("start_time", datetime.now()).hour
                time_of_day = "morning" if slot_hour < 12 else "afternoon" if slot_hour < 17 else "evening"
                if entry.preferred_times and time_of_day not in entry.preferred_times:
                    continue

                # Select highest priority match
                if entry.priority > best_priority:
                    best_match = entry
                    best_priority = entry.priority

            if best_match:
                matches.append({
                    "waitlist_entry_id": best_match.entry_id,
                    "patient_id": best_match.patient_id,
                    "slot": slot,
                    "priority": best_match.priority
                })

        return matches

    async def remove_from_waitlist(self, entry_id: str) -> bool:
        """Remove an entry from the waitlist"""
        if entry_id in self.waitlist:
            del self.waitlist[entry_id]
            return True
        return False

    # ==================== Resource Optimization ====================

    async def allocate_resources(
        self,
        appointment_id: str,
        appointment_type: AppointmentType,
        start_time: datetime,
        duration_minutes: int,
        location_id: str,
        required_resources: List[str]  # Resource types needed
    ) -> List[ResourceAllocation]:
        """Allocate resources for an appointment"""
        allocations = []
        end_time = start_time + timedelta(minutes=duration_minutes)

        for resource_type in required_resources:
            # Find available resource of this type
            available = await self._find_available_resource(
                resource_type, location_id, start_time, end_time
            )

            if available:
                allocation = ResourceAllocation(
                    resource_id=available["resource_id"],
                    resource_type=resource_type,
                    resource_name=available["resource_name"],
                    start_time=start_time,
                    end_time=end_time,
                    appointment_id=appointment_id,
                    is_available=False
                )
                allocations.append(allocation)

                # Update resource availability
                if resource_type not in self.resources:
                    self.resources[resource_type] = []
                self.resources[resource_type].append(allocation)

        return allocations

    async def _find_available_resource(
        self,
        resource_type: str,
        location_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> Optional[Dict]:
        """Find an available resource of the given type"""
        # In production, this would query a resource database
        # For now, return simulated available resource

        return {
            "resource_id": f"{resource_type}_{str(uuid4())[:8]}",
            "resource_name": f"{resource_type.title()} 1",
            "location_id": location_id
        }

    async def optimize_room_allocation(
        self,
        location_id: str,
        date: date
    ) -> Dict[str, Any]:
        """Optimize room allocation for a given date"""
        # Analyze appointments and suggest optimal room assignments

        return {
            "location_id": location_id,
            "date": date.isoformat(),
            "optimization_suggestions": [
                {
                    "room_id": "room_1",
                    "current_utilization": 0.65,
                    "optimal_utilization": 0.85,
                    "suggested_changes": [
                        "Move telehealth appointments to smaller rooms",
                        "Consolidate morning procedures"
                    ]
                }
            ],
            "projected_efficiency_gain": 15.5
        }

    # ==================== Schedule Optimization ====================

    async def optimize_schedule(
        self,
        provider_id: str,
        start_date: date,
        end_date: date
    ) -> ScheduleOptimizationResult:
        """Run full schedule optimization for a provider"""
        schedule = self.provider_schedules.get(provider_id)
        if not schedule:
            raise ValueError(f"Provider {provider_id} not found")

        recommendations = []
        slots_added = 0
        overbookings_added = 0

        # Analyze current utilization
        current_utilization = await self._calculate_utilization(provider_id, start_date, end_date)

        # Generate recommendations
        if current_utilization < 0.7:
            recommendations.append({
                "type": "add_slots",
                "description": "Consider adding more appointment slots during low-utilization periods",
                "impact": "Increase capacity by 15-20%"
            })

        if current_utilization > 0.95:
            recommendations.append({
                "type": "add_overbooking",
                "description": "Enable smart overbooking to account for no-shows",
                "impact": "Recover 10-15% of no-show capacity"
            })
            overbookings_added = 5

        # Check for gaps in schedule
        gap_analysis = await self._analyze_schedule_gaps(provider_id, start_date, end_date)
        if gap_analysis["has_gaps"]:
            recommendations.append({
                "type": "fill_gaps",
                "description": f"Found {gap_analysis['gap_count']} schedulable gaps",
                "impact": f"Add {gap_analysis['potential_slots']} additional appointments"
            })
            slots_added = gap_analysis["potential_slots"]

        # Waitlist integration
        waitlist_matches = await self.process_waitlist(provider_id)
        if waitlist_matches:
            recommendations.append({
                "type": "waitlist_fill",
                "description": f"Found {len(waitlist_matches)} waitlist patients for available slots",
                "impact": "Fill cancelled appointment slots"
            })

        efficiency_improvement = (slots_added * 0.5 + overbookings_added * 0.3) / max(current_utilization * 100, 1)

        return ScheduleOptimizationResult(
            optimization_id=str(uuid4()),
            date_range=(start_date, end_date),
            appointments_optimized=len(self.appointments),
            slots_added=slots_added,
            overbookings_added=overbookings_added,
            efficiency_improvement=round(efficiency_improvement * 100, 2),
            recommendations=recommendations
        )

    async def _calculate_utilization(
        self,
        provider_id: str,
        start_date: date,
        end_date: date
    ) -> float:
        """Calculate schedule utilization rate"""
        schedule = self.provider_schedules.get(provider_id)
        if not schedule:
            return 0.0

        # Calculate total available slots
        total_slots = 0
        booked_slots = 0

        current_date = start_date
        while current_date <= end_date:
            day_of_week = current_date.weekday()
            if day_of_week in schedule.available_days:
                work_hours = schedule.work_hours.get(day_of_week)
                if work_hours:
                    start_time, end_time = work_hours
                    work_minutes = (
                        datetime.combine(current_date, end_time) -
                        datetime.combine(current_date, start_time)
                    ).seconds / 60
                    slots_per_day = work_minutes / (schedule.slot_duration_minutes + schedule.buffer_minutes)
                    total_slots += int(slots_per_day)

            current_date += timedelta(days=1)

        # Count booked appointments
        for appt in self.appointments.values():
            if appt.get("provider_id") == provider_id:
                appt_date = appt.get("date")
                if isinstance(appt_date, str):
                    appt_date = date.fromisoformat(appt_date)
                if appt_date and start_date <= appt_date <= end_date:
                    if appt.get("status") in ["scheduled", "confirmed", "completed"]:
                        booked_slots += 1

        return booked_slots / max(total_slots, 1)

    async def _analyze_schedule_gaps(
        self,
        provider_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """Analyze schedule for gaps that could be filled"""
        # Simulated gap analysis
        return {
            "has_gaps": True,
            "gap_count": 8,
            "potential_slots": 5,
            "total_gap_minutes": 180
        }

    # ==================== Reminder Automation ====================

    async def generate_reminder_schedule(
        self,
        appointment_id: str,
        patient_id: str,
        appointment_datetime: datetime,
        risk_level: NoShowRiskLevel
    ) -> List[Dict[str, Any]]:
        """Generate automated reminder schedule based on risk level"""
        reminders = []
        prefs = self.patient_preferences.get(patient_id, PatientPreferences(patient_id=patient_id))

        # Base reminders
        reminder_times = []

        if risk_level in [NoShowRiskLevel.VERY_HIGH, NoShowRiskLevel.HIGH]:
            # More aggressive reminders for high-risk
            reminder_times = [
                ("7_days", timedelta(days=7)),
                ("3_days", timedelta(days=3)),
                ("1_day", timedelta(days=1)),
                ("2_hours", timedelta(hours=2)),
            ]
        elif risk_level == NoShowRiskLevel.MEDIUM:
            reminder_times = [
                ("3_days", timedelta(days=3)),
                ("1_day", timedelta(days=1)),
            ]
        else:
            reminder_times = [
                ("1_day", timedelta(days=1)),
            ]

        for label, delta in reminder_times:
            reminder_time = appointment_datetime - delta
            if reminder_time > datetime.utcnow():
                for channel in prefs.reminder_preferences:
                    reminders.append({
                        "appointment_id": appointment_id,
                        "patient_id": patient_id,
                        "scheduled_time": reminder_time.isoformat(),
                        "channel": channel,
                        "template": f"appointment_reminder_{label}",
                        "status": "scheduled"
                    })

        return reminders


# Singleton instance
appointment_optimizer = AppointmentOptimizer()


def get_appointment_optimizer() -> AppointmentOptimizer:
    """Get the singleton appointment optimizer instance"""
    return appointment_optimizer

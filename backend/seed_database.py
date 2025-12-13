#!/usr/bin/env python3
"""
Seed Database Script for PRM Service
=====================================

This script loads seed data from a JSON file and inserts it into the PostgreSQL database.
It handles dependencies between tables by inserting in the correct order.

Usage:
    python seed_database.py [--database-url URL] [--seed-file FILE] [--drop-existing]

Environment Variables:
    DATABASE_URL: PostgreSQL connection URL (default: from .env or fallback)

Example:
    python seed_database.py --database-url "postgresql://user:pass@localhost:5432/healthtech"
"""

import argparse
import json
import os
import random
import sys
from datetime import datetime, date, time, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

# Add parent directories to path for imports
script_dir = Path(__file__).parent
service_dir = script_dir.parent
backend_dir = service_dir.parent.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(service_dir))

try:
    from dotenv import load_dotenv
    # Try to load .env from various locations
    for env_path in [
        backend_dir / ".env",
        service_dir / ".env",
        script_dir / ".env",
    ]:
        if env_path.exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass  # dotenv not installed, rely on environment variables

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from loguru import logger

# Configure logger
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO"
)


# Table insertion order based on foreign key dependencies
TABLE_ORDER = [
    # Foundation tables (no dependencies)
    "tenants",
    "permissions",

    # Organization structure
    "organizations",
    "locations",

    # User management
    "roles",
    "practitioners",
    "users",

    # Patient management
    "patients",
    "patient_identifiers",
    "consents",

    # Scheduling
    "provider_schedules",
    "time_slots",

    # Clinical
    "encounters",
    "appointments",

    # Patient journeys
    "journeys",
    "journey_stages",
    "journey_instances",
    "journey_instance_stage_statuses",

    # Communication
    "communications",
    "tickets",

    # Facility management
    "wards",
    "beds",
    "bed_assignments",

    # IPD
    "admissions",
    "nursing_tasks",
    "nursing_observations",
    "orders",
    "ews_scores",
    "icu_alerts",

    # Outcomes & Quality
    "episodes",
    "outcomes",
    "proms",
    "prems",
    "quality_metrics",
    "quality_metric_values",
    "qi_projects",
    "qi_project_metrics",

    # Risk stratification
    "risk_models",
    "risk_model_versions",
    "risk_scores",
    "risk_model_performance",

    # Voice & Collaboration
    "voice_sessions",
    "voice_segments",
    "collab_threads",
    "collab_messages",
    "note_revisions",

    # LLM & Governance
    "llm_sessions",
    "llm_tool_calls",
    "llm_responses",
    "policy_violations",

    # Interoperability
    "network_organizations",
    "external_systems",
    "mapping_profiles",
    "interop_channels",
    "interop_message_log",

    # Referrals
    "referrals",
    "referral_documents",

    # Remote monitoring
    "remote_devices",
    "device_bindings",
    "remote_measurements",
    "remote_alerts",

    # Apps & Marketplace
    "apps",
    "app_keys",
    "app_scopes",
    "app_usage_log",

    # Consent orchestration
    "consent_policies",
    "consent_records",

    # Research
    "deid_configs",
    "pseudo_id_spaces",
    "pseudo_id_mappings",
    "deid_jobs",
    "deid_job_outputs",
    "registries",
    "registry_criteria",
    "registry_enrollments",
    "registry_data_elements",
    "registry_data_values",

    # Trials
    "trials",
    "trial_arms",
    "trial_visits",
    "trial_subjects",
    "trial_subject_visits",
    "trial_crfs",
    "trial_crf_responses",
    "trial_protocol_deviations",

    # Guidelines
    "guidelines",
    "guideline_versions",
    "cds_rules",
    "cds_triggers",
]

# Reference IDs from seed_data.json
TENANT_ID = "00000000-0000-0000-0000-000000000001"
PRACTITIONER_IDS = [
    "30000000-0000-0000-0000-000000000001",  # Dr. Rajesh Sharma - Cardiology
    "30000000-0000-0000-0000-000000000002",  # Dr. Priya Menon - Orthopedics
    "30000000-0000-0000-0000-000000000003",  # Dr. Arun Patel - Internal Medicine
    "30000000-0000-0000-0000-000000000004",  # Dr. Sunita Reddy - Endocrinology
    "30000000-0000-0000-0000-000000000005",  # Dr. Vikram Singh - Emergency
]
LOCATION_IDS = [
    "20000000-0000-0000-0000-000000000002",  # Cardiology OPD
    "20000000-0000-0000-0000-000000000003",  # Orthopedics OPD
    "20000000-0000-0000-0000-000000000004",  # General Medicine OPD
    "20000000-0000-0000-0000-000000000006",  # Endocrinology OPD
    "20000000-0000-0000-0000-000000000005",  # Emergency Department
]
PATIENT_IDS = [
    "40000000-0000-0000-0000-000000000001",
    "40000000-0000-0000-0000-000000000002",
    "40000000-0000-0000-0000-000000000003",
    "40000000-0000-0000-0000-000000000004",
    "40000000-0000-0000-0000-000000000005",
    "40000000-0000-0000-0000-000000000006",
    "40000000-0000-0000-0000-000000000007",
    "40000000-0000-0000-0000-000000000008",
    "40000000-0000-0000-0000-000000000009",
    "40000000-0000-0000-0000-000000000010",
    "40000000-0000-0000-0000-000000000011",
    "40000000-0000-0000-0000-000000000012",
]
SCHEDULE_IDS = [
    "70000000-0000-0000-0000-000000000001",
    "70000000-0000-0000-0000-000000000002",
    "70000000-0000-0000-0000-000000000003",
    "70000000-0000-0000-0000-000000000004",
    "70000000-0000-0000-0000-000000000005",
]


def generate_uuid_for_date(base_prefix: str, date_offset: int, slot_num: int) -> str:
    """Generate a deterministic UUID based on date offset and slot number"""
    return f"{base_prefix}{abs(date_offset):02d}{slot_num:02d}-0000-0000-0000-000000000001"


def generate_time_slots(seed_data: Dict) -> List[Dict]:
    """Generate time slots for the next 2 weeks and past week"""
    logger.info("Generating dynamic time slots...")
    time_slots = []
    today = date.today()

    # Generate slots from 7 days ago to 14 days ahead
    slot_counter = 0
    for day_offset in range(-7, 15):
        current_date = today + timedelta(days=day_offset)
        day_of_week = current_date.weekday()  # 0 = Monday, 6 = Sunday

        # Skip weekends
        if day_of_week >= 5:
            continue

        # For each practitioner, create slots
        for prac_idx, practitioner_id in enumerate(PRACTITIONER_IDS[:4]):  # Skip emergency doc
            location_id = LOCATION_IDS[prac_idx]
            schedule_id = SCHEDULE_IDS[prac_idx] if prac_idx < len(SCHEDULE_IDS) else SCHEDULE_IDS[0]

            # Morning slots (9:00 - 13:00)
            for hour in range(9, 13):
                for minute in [0, 30]:
                    slot_counter += 1
                    slot_id = f"TS{slot_counter:06d}-0000-0000-0000-000000000001"
                    start_time = time(hour, minute)
                    end_time = time(hour, minute + 30) if minute == 0 else time(hour + 1, 0)

                    # Determine status based on date
                    if day_offset < 0:
                        status = random.choice(["booked", "completed", "completed", "completed"])
                    elif day_offset == 0:
                        if hour < datetime.now().hour:
                            status = random.choice(["completed", "no_show"])
                        else:
                            status = random.choice(["booked", "available", "available"])
                    else:
                        status = random.choice(["available", "available", "available", "booked"])

                    time_slots.append({
                        "id": slot_id,
                        "tenant_id": TENANT_ID,
                        "schedule_id": schedule_id,
                        "practitioner_id": practitioner_id,
                        "location_id": location_id,
                        "slot_date": current_date.isoformat(),
                        "start_time": start_time.strftime("%H:%M:%S"),
                        "end_time": end_time.strftime("%H:%M:%S"),
                        "status": status,
                        "meta_data": {}
                    })

            # Afternoon slots (14:00 - 17:00) for select practitioners
            if prac_idx in [0, 2]:  # Cardiology and Gen Med have afternoon slots
                for hour in range(14, 17):
                    for minute in [0, 30]:
                        slot_counter += 1
                        slot_id = f"TS{slot_counter:06d}-0000-0000-0000-000000000001"
                        start_time = time(hour, minute)
                        end_time = time(hour, minute + 30) if minute == 0 else time(hour + 1, 0)

                        if day_offset < 0:
                            status = random.choice(["booked", "completed", "completed"])
                        elif day_offset == 0:
                            if hour < datetime.now().hour:
                                status = random.choice(["completed", "no_show"])
                            else:
                                status = random.choice(["booked", "available"])
                        else:
                            status = random.choice(["available", "available", "booked"])

                        time_slots.append({
                            "id": slot_id,
                            "tenant_id": TENANT_ID,
                            "schedule_id": schedule_id,
                            "practitioner_id": practitioner_id,
                            "location_id": location_id,
                            "slot_date": current_date.isoformat(),
                            "start_time": start_time.strftime("%H:%M:%S"),
                            "end_time": end_time.strftime("%H:%M:%S"),
                            "status": status,
                            "meta_data": {}
                        })

    logger.info(f"  Generated {len(time_slots)} time slots")
    return time_slots


def generate_appointments(seed_data: Dict, time_slots: List[Dict]) -> List[Dict]:
    """Generate appointments based on booked time slots"""
    logger.info("Generating dynamic appointments...")
    appointments = []
    today = date.today()

    # Get booked/completed slots
    booked_slots = [s for s in time_slots if s["status"] in ["booked", "completed", "no_show"]]

    # Shuffle patients to distribute across appointments
    patient_pool = PATIENT_IDS.copy()

    appointment_counter = 0
    for slot in booked_slots:
        slot_date = date.fromisoformat(slot["slot_date"])
        day_offset = (slot_date - today).days

        # Pick a patient
        patient_id = patient_pool[appointment_counter % len(patient_pool)]

        # Determine appointment status based on slot status and date
        if slot["status"] == "completed":
            status = "completed"
        elif slot["status"] == "no_show":
            status = "no_show"
        elif day_offset < 0:
            status = "completed"
        elif day_offset == 0:
            slot_hour = int(slot["start_time"].split(":")[0])
            if slot_hour < datetime.now().hour:
                status = random.choice(["completed", "checked_in"])
            else:
                status = random.choice(["confirmed", "checked_in"])
        else:
            status = random.choice(["scheduled", "confirmed", "confirmed"])

        # Create appointment datetime
        start_time_parts = slot["start_time"].split(":")
        scheduled_at = datetime.combine(
            slot_date,
            time(int(start_time_parts[0]), int(start_time_parts[1]))
        )

        appointment_counter += 1
        apt_id = f"APT{appointment_counter:05d}-0000-0000-0000-000000000001"

        # Appointment types based on patient and practitioner
        apt_types = ["consultation", "follow_up", "checkup", "routine_visit"]
        apt_type = random.choice(apt_types)

        # Visit reasons
        reasons = [
            "Regular checkup",
            "Follow-up visit",
            "Consultation for symptoms",
            "Routine monitoring",
            "Lab results review",
            "Medication adjustment",
            "Health screening"
        ]

        appointments.append({
            "id": apt_id,
            "tenant_id": TENANT_ID,
            "patient_id": patient_id,
            "practitioner_id": slot["practitioner_id"],
            "location_id": slot["location_id"],
            "time_slot_id": slot["id"],
            "status": status,
            "appointment_type": apt_type,
            "scheduled_at": scheduled_at.isoformat(),
            "duration_minutes": 30,
            "visit_reason": random.choice(reasons),
            "source": random.choice(["web", "phone", "whatsapp", "walk_in"]),
            "is_first_visit": random.choice([True, False, False]),
            "fhir_resource": {},
            "meta_data": {}
        })

    logger.info(f"  Generated {len(appointments)} appointments")
    return appointments


def generate_encounters(seed_data: Dict, appointments: List[Dict]) -> List[Dict]:
    """Generate encounters for completed and checked-in appointments"""
    logger.info("Generating dynamic encounters...")
    encounters = []

    # Only create encounters for completed or checked_in appointments
    eligible_appointments = [a for a in appointments if a["status"] in ["completed", "checked_in"]]

    encounter_counter = 0
    for apt in eligible_appointments:
        encounter_counter += 1
        enc_id = f"ENC{encounter_counter:05d}-0000-0000-0000-000000000001"

        # Determine encounter status
        if apt["status"] == "completed":
            status = "finished"
        else:
            status = "in-progress"

        # Create encounter time (slightly after appointment start)
        apt_time = datetime.fromisoformat(apt["scheduled_at"])
        start_time = apt_time + timedelta(minutes=random.randint(0, 10))

        # End time for finished encounters
        end_time = None
        if status == "finished":
            end_time = start_time + timedelta(minutes=random.randint(15, 45))

        # Chief complaints
        complaints = [
            "Chest pain", "Shortness of breath", "Joint pain", "Fever",
            "Fatigue", "Dizziness", "Back pain", "Headache",
            "Blood sugar monitoring", "Blood pressure check", "General wellness"
        ]

        encounters.append({
            "id": enc_id,
            "tenant_id": TENANT_ID,
            "patient_id": apt["patient_id"],
            "practitioner_id": apt["practitioner_id"],
            "location_id": apt["location_id"],
            "appointment_id": apt["id"],
            "status": status,
            "encounter_class": "AMB",  # Ambulatory
            "type_code": apt["appointment_type"],
            "started_at": start_time.isoformat(),
            "ended_at": end_time.isoformat() if end_time else None,
            "chief_complaint": random.choice(complaints),
            "fhir_resource": {},
            "meta_data": {}
        })

    logger.info(f"  Generated {len(encounters)} encounters")
    return encounters


def generate_communications(seed_data: Dict, appointments: List[Dict]) -> List[Dict]:
    """Generate communications (reminders, confirmations, etc.)"""
    logger.info("Generating dynamic communications...")
    communications = []
    today = datetime.now()

    comm_counter = 0

    # Generate appointment reminders and confirmations
    for apt in appointments:
        apt_time = datetime.fromisoformat(apt["scheduled_at"])
        apt_date = apt_time.date()
        day_offset = (apt_date - today.date()).days

        # Appointment confirmation (sent when booked)
        if day_offset >= -7:  # Recent appointments
            comm_counter += 1
            comm_id = f"COMM{comm_counter:05d}-0000-0000-0000-000000000001"

            # Confirmation sent 1-3 days before the actual appointment or at booking
            if day_offset > 3:
                sent_at = apt_time - timedelta(days=random.randint(2, 5))
            else:
                sent_at = apt_time - timedelta(days=1, hours=random.randint(1, 12))

            communications.append({
                "id": comm_id,
                "tenant_id": TENANT_ID,
                "patient_id": apt["patient_id"],
                "direction": "outbound",
                "channel": random.choice(["sms", "whatsapp", "email"]),
                "status": "delivered",
                "message_type": "appointment_confirmation",
                "subject": "Appointment Confirmation",
                "content": f"Your appointment is confirmed for {apt_time.strftime('%B %d, %Y at %I:%M %p')}",
                "sent_at": sent_at.isoformat(),
                "meta_data": {"appointment_id": apt["id"]}
            })

        # Day-before reminder for upcoming appointments
        if 0 < day_offset <= 7:
            comm_counter += 1
            comm_id = f"COMM{comm_counter:05d}-0000-0000-0000-000000000001"
            reminder_time = apt_time - timedelta(days=1, hours=random.randint(8, 12))

            communications.append({
                "id": comm_id,
                "tenant_id": TENANT_ID,
                "patient_id": apt["patient_id"],
                "direction": "outbound",
                "channel": random.choice(["sms", "whatsapp"]),
                "status": "delivered",
                "message_type": "appointment_reminder",
                "subject": "Appointment Reminder",
                "content": f"Reminder: You have an appointment tomorrow at {apt_time.strftime('%I:%M %p')}",
                "sent_at": reminder_time.isoformat(),
                "meta_data": {"appointment_id": apt["id"]}
            })

        # Same-day reminder (2 hours before)
        if day_offset == 0 and apt_time > today:
            comm_counter += 1
            comm_id = f"COMM{comm_counter:05d}-0000-0000-0000-000000000001"
            reminder_time = apt_time - timedelta(hours=2)

            if reminder_time > today:
                communications.append({
                    "id": comm_id,
                    "tenant_id": TENANT_ID,
                    "patient_id": apt["patient_id"],
                    "direction": "outbound",
                    "channel": "sms",
                    "status": "sent",
                    "message_type": "appointment_reminder",
                    "subject": "Appointment Today",
                    "content": f"Your appointment is in 2 hours at {apt_time.strftime('%I:%M %p')}",
                    "sent_at": reminder_time.isoformat(),
                    "meta_data": {"appointment_id": apt["id"]}
                })

        # Post-visit follow-up for completed appointments
        if apt["status"] == "completed":
            comm_counter += 1
            comm_id = f"COMM{comm_counter:05d}-0000-0000-0000-000000000001"
            followup_time = apt_time + timedelta(hours=random.randint(2, 24))

            communications.append({
                "id": comm_id,
                "tenant_id": TENANT_ID,
                "patient_id": apt["patient_id"],
                "direction": "outbound",
                "channel": random.choice(["sms", "whatsapp", "email"]),
                "status": "delivered",
                "message_type": "post_visit",
                "subject": "Thank you for visiting",
                "content": "Thank you for visiting Apollo Hospital. We hope you had a good experience.",
                "sent_at": followup_time.isoformat(),
                "meta_data": {"appointment_id": apt["id"]}
            })

    # Add some general health tips/communications
    for patient_id in PATIENT_IDS[:6]:
        comm_counter += 1
        comm_id = f"COMM{comm_counter:05d}-0000-0000-0000-000000000001"
        sent_days_ago = random.randint(1, 14)

        health_tips = [
            "Remember to stay hydrated and drink at least 8 glasses of water daily.",
            "Regular exercise can help manage blood pressure and blood sugar levels.",
            "Don't forget to take your medications as prescribed.",
            "Schedule your annual health checkup today!",
            "Healthy eating starts with small changes. Try adding more vegetables to your diet."
        ]

        communications.append({
            "id": comm_id,
            "tenant_id": TENANT_ID,
            "patient_id": patient_id,
            "direction": "outbound",
            "channel": "whatsapp",
            "status": "delivered",
            "message_type": "health_tip",
            "subject": "Health Tip",
            "content": random.choice(health_tips),
            "sent_at": (today - timedelta(days=sent_days_ago)).isoformat(),
            "meta_data": {}
        })

    logger.info(f"  Generated {len(communications)} communications")
    return communications


def generate_tickets(seed_data: Dict) -> List[Dict]:
    """Generate support tickets"""
    logger.info("Generating dynamic tickets...")
    tickets = []
    today = datetime.now()

    # User IDs for created_by and assigned_to
    USER_IDS = [
        "60000000-0000-0000-0000-000000000001",  # Admin
        "60000000-0000-0000-0000-000000000002",  # Dr. Rajesh
        "60000000-0000-0000-0000-000000000003",  # Dr. Priya
        "60000000-0000-0000-0000-000000000004",  # Dr. Arun
        "60000000-0000-0000-0000-000000000005",  # Receptionist
        "60000000-0000-0000-0000-000000000006",  # Nurse Mary
    ]

    ticket_data = [
        {
            "patient_id": PATIENT_IDS[0],
            "title": "Prescription refill request",
            "description": "Need refill for blood pressure medication",
            "category": "prescription",
            "priority": "medium",
            "status": "open",
            "created_by_user_id": USER_IDS[4]  # Receptionist
        },
        {
            "patient_id": PATIENT_IDS[2],
            "title": "Lab results inquiry",
            "description": "When will my blood test results be available?",
            "category": "inquiry",
            "priority": "low",
            "status": "in_progress",
            "created_by_user_id": USER_IDS[4],
            "assigned_to_user_id": USER_IDS[3]  # Dr. Arun
        },
        {
            "patient_id": PATIENT_IDS[4],
            "title": "Billing question",
            "description": "Question about insurance coverage for recent procedure",
            "category": "billing",
            "priority": "medium",
            "status": "open",
            "created_by_user_id": USER_IDS[4]
        },
        {
            "patient_id": PATIENT_IDS[5],
            "title": "Appointment reschedule",
            "description": "Need to reschedule my appointment to next week",
            "category": "scheduling",
            "priority": "high",
            "status": "resolved",
            "created_by_user_id": USER_IDS[4]
        },
        {
            "patient_id": PATIENT_IDS[7],
            "title": "Side effects concern",
            "description": "Experiencing mild dizziness after starting new medication",
            "category": "medical",
            "priority": "high",
            "status": "in_progress",
            "created_by_user_id": USER_IDS[5],  # Nurse
            "assigned_to_user_id": USER_IDS[1]  # Dr. Rajesh
        },
        {
            "patient_id": PATIENT_IDS[9],
            "title": "Medical records request",
            "description": "Need copy of medical records for insurance claim",
            "category": "records",
            "priority": "medium",
            "status": "open",
            "created_by_user_id": USER_IDS[4]
        },
        {
            "patient_id": PATIENT_IDS[11],
            "title": "Diet plan inquiry",
            "description": "Looking for dietary guidance for diabetes management",
            "category": "inquiry",
            "priority": "low",
            "status": "resolved",
            "created_by_user_id": USER_IDS[4]
        },
        {
            "patient_id": PATIENT_IDS[4],
            "title": "Urgent: Abnormal lab results",
            "description": "HbA1c result requires immediate attention - value 9.2%",
            "category": "clinical",
            "priority": "urgent",
            "status": "open",
            "created_by_user_id": USER_IDS[5],
            "assigned_to_user_id": USER_IDS[3]
        }
    ]

    for idx, ticket in enumerate(ticket_data):
        ticket_id = f"TKT{idx+1:05d}-0000-0000-0000-000000000001"

        ticket_record = {
            "id": ticket_id,
            "tenant_id": TENANT_ID,
            "patient_id": ticket["patient_id"],
            "title": ticket["title"],
            "description": ticket["description"],
            "category": ticket.get("category"),
            "priority": ticket["priority"],
            "status": ticket["status"],
            "meta_data": {}
        }

        # Add optional fields if present
        if "created_by_user_id" in ticket:
            ticket_record["created_by_user_id"] = ticket["created_by_user_id"]
        if "assigned_to_user_id" in ticket:
            ticket_record["assigned_to_user_id"] = ticket["assigned_to_user_id"]

        tickets.append(ticket_record)

    logger.info(f"  Generated {len(tickets)} tickets")
    return tickets


def generate_dynamic_data(seed_data: Dict) -> Dict[str, List[Dict]]:
    """Generate all dynamic data that requires current dates"""
    logger.info("\n" + "=" * 60)
    logger.info("Generating Dynamic Data")
    logger.info("=" * 60)

    # Generate in order (some depend on others)
    time_slots = generate_time_slots(seed_data)
    appointments = generate_appointments(seed_data, time_slots)
    encounters = generate_encounters(seed_data, appointments)
    communications = generate_communications(seed_data, appointments)
    tickets = generate_tickets(seed_data)

    return {
        "time_slots": time_slots,
        "appointments": appointments,
        "encounters": encounters,
        "communications": communications,
        "tickets": tickets
    }


def get_database_url() -> str:
    """Get database URL from environment or default"""
    return os.getenv(
        "DATABASE_URL",
        "postgresql://healthtech:healthtech@localhost:5432/healthtech"
    )


def parse_value(value: Any, column_type: str = None) -> Any:
    """Parse JSON value to appropriate Python/SQLAlchemy type"""
    if value is None:
        return None

    # Handle UUID strings
    if isinstance(value, str) and len(value) == 36 and value.count('-') == 4:
        try:
            return UUID(value)
        except ValueError:
            pass

    # Handle datetime strings
    if isinstance(value, str):
        # ISO datetime with timezone
        for fmt in [
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
        ]:
            try:
                return datetime.strptime(value.replace("+05:30", "+0530"), fmt)
            except ValueError:
                continue

        # Date only
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            pass

        # Time only
        try:
            return datetime.strptime(value, "%H:%M:%S").time()
        except ValueError:
            pass
            
    # Serialize dict/list to JSON string for psycopg2
    if isinstance(value, (dict, list)):
        return json.dumps(value)

    return value


def prepare_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare a record for database insertion"""
    prepared = {}
    for key, value in record.items():
        # Skip metadata keys
        if key.startswith("_"):
            continue
        prepared[key] = parse_value(value)

    # Add timestamps if not present
    now = datetime.utcnow()
    if "created_at" not in prepared:
        prepared["created_at"] = now
    if "updated_at" not in prepared:
        prepared["updated_at"] = now

    return prepared


def get_existing_tables(engine) -> set:
    """Get set of existing table names in database"""
    inspector = inspect(engine)
    return set(inspector.get_table_names())


def truncate_table(session: Session, table_name: str) -> None:
    """Truncate a table (delete all rows)"""
    try:
        session.execute(text(f'TRUNCATE TABLE "{table_name}" CASCADE'))
        session.commit()
        logger.info(f"  Truncated table: {table_name}")
    except Exception as e:
        session.rollback()
        logger.warning(f"  Could not truncate {table_name}: {e}")


def insert_records(
    session: Session,
    table_name: str,
    records: List[Dict[str, Any]],
    existing_tables: set
) -> int:
    """Insert records into a table using raw SQL"""
    if table_name not in existing_tables:
        logger.warning(f"  Table '{table_name}' does not exist, skipping")
        return 0

    if not records:
        return 0

    inserted = 0
    for record in records:
        try:
            prepared = prepare_record(record)
            columns = list(prepared.keys())
            placeholders = [f":{col}" for col in columns]

            sql = text(f"""
                INSERT INTO "{table_name}" ({", ".join(f'"{c}"' for c in columns)})
                VALUES ({", ".join(placeholders)})
                ON CONFLICT DO NOTHING
            """)

            session.execute(sql, prepared)
            inserted += 1
        except IntegrityError as e:
            session.rollback()
            logger.warning(f"  Skipping duplicate record in {table_name}: {e}")
        except Exception as e:
            session.rollback()
            logger.error(f"  Error inserting record in {table_name}: {e}")
            logger.debug(f"  Record: {record}")
            print(f"CRITICAL ERROR in {table_name}: {e}")

    session.commit()
    return inserted


def load_seed_data(seed_file: Path) -> Dict[str, List[Dict]]:
    """Load seed data from JSON file"""
    logger.info(f"Loading seed data from: {seed_file}")

    with open(seed_file, 'r') as f:
        data = json.load(f)

    # Remove metadata keys
    return {k: v for k, v in data.items() if not k.startswith("_")}


def seed_database(
    database_url: str,
    seed_file: Path,
    drop_existing: bool = False
) -> None:
    """Main function to seed the database"""
    logger.info("=" * 60)
    logger.info("PRM Service Database Seeder")
    logger.info("=" * 60)

    # Create engine and session
    logger.info(f"Connecting to database...")
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        # Test connection
        session.execute(text("SELECT 1"))
        logger.info("Database connection successful!")

        # Get existing tables
        existing_tables = get_existing_tables(engine)
        logger.info(f"Found {len(existing_tables)} existing tables")

        # Load seed data
        seed_data = load_seed_data(seed_file)
        logger.info(f"Loaded data for {len(seed_data)} tables")

        # Generate dynamic data (time slots, appointments, encounters, communications)
        dynamic_data = generate_dynamic_data(seed_data)

        # Merge dynamic data into seed data (overwriting any static placeholders)
        for table_name, records in dynamic_data.items():
            seed_data[table_name] = records
            logger.info(f"  Added dynamic {table_name}: {len(records)} records")

        # Optionally truncate existing data
        if drop_existing:
            logger.warning("Dropping existing data...")
            # Truncate in reverse order to handle foreign keys
            for table_name in reversed(TABLE_ORDER):
                if table_name in existing_tables and table_name in seed_data:
                    truncate_table(session, table_name)

        # Insert data in dependency order
        logger.info("\nInserting seed data...")
        total_inserted = 0

        for table_name in TABLE_ORDER:
            if table_name in seed_data:
                records = seed_data[table_name]
                count = insert_records(session, table_name, records, existing_tables)
                if count > 0:
                    logger.info(f"  {table_name}: {count} records inserted")
                    total_inserted += count

        # Handle any tables not in the predefined order
        for table_name, records in seed_data.items():
            if table_name not in TABLE_ORDER:
                count = insert_records(session, table_name, records, existing_tables)
                if count > 0:
                    logger.info(f"  {table_name}: {count} records inserted")
                    total_inserted += count

        logger.info("\n" + "=" * 60)
        logger.info(f"Seeding completed! Total records inserted: {total_inserted}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error during seeding: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Seed the PRM Service database with initial data"
    )
    parser.add_argument(
        "--database-url",
        "-d",
        type=str,
        default=None,
        help="PostgreSQL database URL (default: from DATABASE_URL env var)"
    )
    parser.add_argument(
        "--seed-file",
        "-f",
        type=str,
        default=None,
        help="Path to seed data JSON file (default: ./seed_data.json)"
    )
    parser.add_argument(
        "--drop-existing",
        "-x",
        action="store_true",
        help="Drop existing data before seeding (CAUTION: destructive)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logger.remove()
        logger.add(sys.stdout, level="DEBUG")

    # Determine database URL
    database_url = args.database_url or get_database_url()

    # Determine seed file path
    if args.seed_file:
        seed_file = Path(args.seed_file)
    else:
        seed_file = script_dir / "seed_data.json"

    if not seed_file.exists():
        logger.error(f"Seed file not found: {seed_file}")
        sys.exit(1)

    # Confirm destructive operation
    if args.drop_existing:
        logger.warning("=" * 60)
        logger.warning("WARNING: --drop-existing will DELETE all existing data!")
        logger.warning("=" * 60)
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != "yes":
            logger.info("Operation cancelled.")
            sys.exit(0)

    # Run seeder
    try:
        seed_database(
            database_url=database_url,
            seed_file=seed_file,
            drop_existing=args.drop_existing
        )
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Seed Appointments Script - Fixed version
Creates time slots and appointments for testing
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4
import random

# Add paths
script_dir = Path(__file__).parent
service_dir = script_dir.parent
backend_dir = service_dir.parent.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(service_dir))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}", level="INFO")

# Database URL (localhost)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://healthtech:healthtech@localhost:5433/healthtech"
)

def seed_appointments():
    """Seed time slots and appointments"""
    logger.info("Connecting to database...")
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Get a tenant
        result = conn.execute(text("SELECT id FROM tenants LIMIT 1"))
        tenant_row = result.fetchone()
        if not tenant_row:
            logger.error("No tenants found! Run the main seed first.")
            return
        tenant_id = tenant_row[0]
        logger.info(f"Using tenant: {tenant_id}")
        
        # Get practitioners
        result = conn.execute(text("SELECT id FROM practitioners LIMIT 5"))
        practitioners = [row[0] for row in result.fetchall()]
        if not practitioners:
            logger.error("No practitioners found! Run the main seed first.")
            return
        logger.info(f"Found {len(practitioners)} practitioners")
        
        # Get locations
        result = conn.execute(text("SELECT id FROM locations LIMIT 5"))
        locations = [row[0] for row in result.fetchall()]
        if not locations:
            logger.error("No locations found! Run the main seed first.")
            return
        logger.info(f"Found {len(locations)} locations")
        
        # Get patients
        result = conn.execute(text("SELECT id FROM patients LIMIT 10"))
        patients = [row[0] for row in result.fetchall()]
        if not patients:
            logger.error("No patients found! Run the main seed first.")
            return
        logger.info(f"Found {len(patients)} patients")
        
        # Get schedules
        result = conn.execute(text("SELECT id FROM provider_schedules LIMIT 5"))
        schedules = [row[0] for row in result.fetchall()]
        if not schedules:
            logger.error("No provider schedules found! Run the main seed first.")
            return
        logger.info(f"Found {len(schedules)} schedules")
        
        # Generate time slots for next 14 days
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        slots_created = 0
        appointments_created = 0
        
        logger.info("Creating time slots and appointments...")
        
        # Prepare all data first
        slot_data = []
        appointment_data = []
        
        for day_offset in range(0, 14):
            current_date = today + timedelta(days=day_offset)
            
            # Skip weekends
            if current_date.weekday() >= 5:
                continue
            
            # Create slots for each practitioner
            for prac_idx, practitioner_id in enumerate(practitioners):
                location_id = locations[prac_idx % len(locations)]
                schedule_id = schedules[prac_idx % len(schedules)]
                
                # Morning slots: 9:00 - 12:30
                for hour in range(9, 13):
                    for minute in [0, 30]:
                        slot_id = uuid4()
                        start_dt = current_date.replace(hour=hour, minute=minute)
                        end_dt = start_dt + timedelta(minutes=30)
                        
                        # Determine status - more booked slots
                        status = random.choice(["available", "available", "full", "full"])
                        
                        slot_data.append({
                            "id": slot_id,
                            "tenant_id": tenant_id,
                            "practitioner_id": practitioner_id,
                            "location_id": location_id,
                            "schedule_id": schedule_id,
                            "start_dt": start_dt,
                            "end_dt": end_dt,
                            "booked": 1 if status == "full" else 0,
                            "status": status
                        })
                        
                        # Create appointment for full slots
                        if status == "full":
                            patient_id = random.choice(patients)
                            appt_status = random.choice(["booked", "confirmed", "confirmed"])
                            
                            appointment_data.append({
                                "id": uuid4(),
                                "tenant_id": tenant_id,
                                "patient_id": patient_id,
                                "practitioner_id": practitioner_id,
                                "location_id": location_id,
                                "time_slot_id": slot_id,
                                "status": appt_status,
                                "apt_type": random.choice(["consultation", "follow_up", "checkup"]),
                                "reason": random.choice([
                                    "Regular checkup",
                                    "Follow-up visit",
                                    "Health screening",
                                    "Lab results review"
                                ])
                            })
        
        # Insert time slots in batches
        logger.info(f"Inserting {len(slot_data)} time slots...")
        for slot in slot_data:
            try:
                conn.execute(
                    text("""
                    INSERT INTO time_slots (id, tenant_id, practitioner_id, location_id, schedule_id,
                        start_datetime, end_datetime, capacity, booked_count, status, created_at, updated_at)
                    VALUES (:id, :tenant_id, :practitioner_id, :location_id, :schedule_id,
                        :start_dt, :end_dt, 1, :booked, :status, NOW(), NOW())
                    ON CONFLICT DO NOTHING
                    """),
                    slot
                )
                slots_created += 1
            except Exception as e:
                logger.error(f"Error inserting slot: {e}")
                conn.rollback()
                continue
        
        conn.commit()
        logger.success(f"Created {slots_created} time slots")
        
        # Insert appointments
        logger.info(f"Inserting {len(appointment_data)} appointments...")
        for apt in appointment_data:
            try:
                conn.execute(
                    text("""
                    INSERT INTO appointments (id, tenant_id, patient_id, practitioner_id, location_id,
                        time_slot_id, status, appointment_type, reason_text, created_at, updated_at)
                    VALUES (:id, :tenant_id, :patient_id, :practitioner_id, :location_id,
                        :time_slot_id, :status, :apt_type, :reason, NOW(), NOW())
                    ON CONFLICT DO NOTHING
                    """),
                    apt
                )
                appointments_created += 1
            except Exception as e:
                logger.error(f"Error inserting appointment: {e}")
                conn.rollback()
                continue
        
        conn.commit()
        logger.success(f"Created {appointments_created} appointments")
        logger.success("Seeding complete!")

if __name__ == "__main__":
    seed_appointments()

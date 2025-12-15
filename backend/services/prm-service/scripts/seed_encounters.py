#!/usr/bin/env python3
"""
Seed Encounters Script
Creates encounters for existing appointments and some standalone encounters.
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
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}", level="INFO")

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://healthtech:healthtech@localhost:5433/healthtech"
)

def seed_encounters():
    """Seed encounters"""
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
        
        # 1. Create Encounters for Appointments
        logger.info("Fetching appointments...")
        result = conn.execute(text("""
            SELECT id, patient_id, practitioner_id, status, appointment_type 
            FROM appointments 
            WHERE encounter_id IS NULL
            LIMIT 50
        """))
        appointments = result.fetchall()
        
        encounters_created = 0
        
        if appointments:
            logger.info(f"files Found {len(appointments)} appointments without encounters. Creating encounters...")
            
            for appt in appointments:
                appt_id, patient_id, practitioner_id, appt_status, appt_type = appt
                
                # Map appointment status to encounter status
                enc_status = "planned"
                if appt_status == "completed":
                    enc_status = "finished" 
                elif appt_status == "checked_in":
                    enc_status = "in-progress"
                elif appt_status == "cancelled":
                    enc_status = "cancelled"
                
                # Create Encounter
                enc_id = uuid4()
                enc_fhir_id = f"enc-{str(enc_id)[:8]}"
                
                try:
                    # Insert Encounter
                    conn.execute(
                        text("""
                        INSERT INTO encounters (
                            id, tenant_id, encounter_fhir_id, patient_id, practitioner_id, 
                            appointment_id, status, class_code, started_at, created_at, updated_at
                        ) VALUES (
                            :id, :tenant_id, :fhir_id, :patient_id, :practitioner_id,
                            :appt_id, :status, 'AMB', NOW(), NOW(), NOW()
                        )
                        """),
                        {
                            "id": enc_id,
                            "tenant_id": tenant_id,
                            "fhir_id": enc_fhir_id,
                            "patient_id": patient_id,
                            "practitioner_id": practitioner_id,
                            "appt_id": appt_id,
                            "status": enc_status
                        }
                    )
                    
                    # Update Appointment with Encounter ID
                    conn.execute(
                        text("UPDATE appointments SET encounter_id = :enc_id WHERE id = :appt_id"),
                        {"enc_id": enc_id, "appt_id": appt_id}
                    )
                    
                    encounters_created += 1
                except Exception as e:
                    logger.error(f"Error creating encounter for appointment {appt_id}: {e}")
                    continue
        else:
            logger.info("No appointments found that need encounters.")
            
        
        # 2. Create some standalone encounters (Emergency/Inpatient)
        logger.info("Creating standalone encounters...")
        
        # Get some patients and practitioners
        patients = [row[0] for row in conn.execute(text("SELECT id FROM patients LIMIT 10")).fetchall()]
        practitioners = [row[0] for row in conn.execute(text("SELECT id FROM practitioners LIMIT 5")).fetchall()]
        
        standalone_created = 0
        if patients and practitioners:
            for _ in range(10): # Create 10 random encounters
                patient_id = random.choice(patients)
                practitioner_id = random.choice(practitioners)
                
                enc_id = uuid4()
                enc_fhir_id = f"enc-{str(enc_id)[:8]}"
                class_code = random.choice(["chk", "EMER", "IMP"])
                status = random.choice(["in-progress", "completed", "planned"])
                
                try:
                    conn.execute(
                        text("""
                        INSERT INTO encounters (
                            id, tenant_id, encounter_fhir_id, patient_id, practitioner_id, 
                            status, class_code, started_at, created_at, updated_at
                        ) VALUES (
                            :id, :tenant_id, :fhir_id, :patient_id, :practitioner_id,
                            :status, :class_code, NOW(), NOW(), NOW()
                        )
                        """),
                        {
                            "id": enc_id,
                            "tenant_id": tenant_id,
                            "fhir_id": enc_fhir_id,
                            "patient_id": patient_id,
                            "practitioner_id": practitioner_id,
                            "status": status,
                            "class_code": class_code
                        }
                    )
                    standalone_created += 1
                except Exception as e:
                    logger.error(f"Error creating standalone encounter: {e}")
                    continue
        
        conn.commit()
        logger.success(f"Created {encounters_created} appointment-based encounters and {standalone_created} standalone encounters.")

if __name__ == "__main__":
    seed_encounters()

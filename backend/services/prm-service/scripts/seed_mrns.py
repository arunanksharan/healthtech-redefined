#!/usr/bin/env python3
"""
Seed MRNs Script
Backfills Medical Record Numbers (MRN) for patients who don't have them.
"""
import sys
import os
import random
import string
from pathlib import Path
from datetime import datetime
from uuid import uuid4

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

def generate_mrn():
    """Generate a random 8-digit MRN"""
    return ''.join(random.choices(string.digits, k=8))

def seed_mrns():
    """Backfill MRNs for all patients"""
    logger.info("Connecting to database...")
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Get all patients
        result = conn.execute(text("SELECT id, first_name, last_name, mrn FROM patients"))
        patients = result.fetchall()
        
        logger.info(f"Found {len(patients)} patients")
        
        updated_count = 0
        
        for patient in patients:
            p_id, first, last, existing_mrn = patient
            
            # Skip if already has MRN (unless you want to force overwrite, but usually we just backfill)
            if existing_mrn:
                continue
                
            new_mrn = generate_mrn()
            
            # Check for uniqueness (simple check, in prod constraint should handle it)
            while True:
                exists = conn.execute(text("SELECT 1 FROM patients WHERE mrn = :mrn"), {"mrn": new_mrn}).fetchone()
                if not exists:
                    break
                new_mrn = generate_mrn()
            
            # Update patient
            conn.execute(
                text("UPDATE patients SET mrn = :mrn, updated_at = NOW() WHERE id = :id"),
                {"mrn": new_mrn, "id": p_id}
            )
            
            # Also ensure an identifier record exists (best practice for our schema)
            # Check if identifier exists
            id_exists = conn.execute(
                text("SELECT 1 FROM patient_identifiers WHERE patient_id = :pid AND type = 'MRN'"),
                {"pid": p_id}
            ).fetchone()
            
            if not id_exists:
                conn.execute(
                    text("""
                        INSERT INTO patient_identifiers (id, tenant_id, patient_id, use, type, system, value, created_at, updated_at)
                        SELECT :uuid, tenant_id, :pid, 'official', 'MRN', 'http://hospital.org/mrn', :mrn, NOW(), NOW()
                        FROM patients WHERE id = :pid
                    """),
                    {"uuid": uuid4(), "pid": p_id, "mrn": new_mrn}
                )

            updated_count += 1
            logger.info(f"Assigned MRN {new_mrn} to {first} {last}")
            
        conn.commit()
        logger.success(f"Successfully backfilled MRNs for {updated_count} patients")

if __name__ == "__main__":
    seed_mrns()

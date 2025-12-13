"""
Script to seed journey instances (patients enrolled in journeys)
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import uuid

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://healthtech:healthtech@127.0.0.1:5433/healthtech")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Get required data from the database
tenant_result = session.execute(text("SELECT id FROM tenants LIMIT 1")).fetchone()
journeys = session.execute(text("SELECT id, name FROM journeys")).fetchall()
patients = session.execute(text("SELECT id, first_name, last_name FROM patients LIMIT 5")).fetchall()
stages = session.execute(text("SELECT id, journey_id, name, order_index FROM journey_stages ORDER BY journey_id, order_index")).fetchall()

if not tenant_result or not journeys or not patients:
    print("Missing required data. Please seed tenants, journeys, and patients first.")
    print(f"  Tenants: {1 if tenant_result else 0}")
    print(f"  Journeys: {len(journeys)}")
    print(f"  Patients: {len(patients)}")
    sys.exit(1)

tenant_id = tenant_result[0]
print(f"Using tenant_id: {tenant_id}")
print(f"Found {len(journeys)} journeys")
print(f"Found {len(patients)} patients")
print(f"Found {len(stages)} stages")

# Group stages by journey_id
journey_stages = {}
for stage in stages:
    jid = str(stage[1])
    if jid not in journey_stages:
        journey_stages[jid] = []
    journey_stages[jid].append({
        "id": str(stage[0]),
        "name": stage[2],
        "order_index": stage[3]
    })

# Create journey instances
now = datetime.utcnow()
instances_created = 0

for i, patient in enumerate(patients):
    patient_id = str(patient[0])
    patient_name = f"{patient[1]} {patient[2]}"
    
    # Assign patient to a journey (cycle through journeys)
    journey_idx = i % len(journeys)
    journey = journeys[journey_idx]
    journey_id = str(journey[0])
    journey_name = journey[1]
    
    # Get stages for this journey
    j_stages = journey_stages.get(journey_id, [])
    if not j_stages:
        print(f"  No stages for journey {journey_name}, skipping...")
        continue
    
    # Pick current stage (vary by patient - some early, some further along)
    stage_idx = min(i % 3, len(j_stages) - 1)  # 0, 1, or 2
    current_stage = j_stages[stage_idx]
    
    # Create instance
    instance_id = str(uuid.uuid4())
    created_at = now - timedelta(days=i*2, hours=i*3)  # Vary start times
    
    # Determine status - most active, some completed
    status = "completed" if i == 4 else "active"
    
    insert_instance = text("""
    INSERT INTO journey_instances (id, tenant_id, journey_id, patient_id, current_stage_id, status, created_at, updated_at)
    VALUES (:id, :tenant_id, :journey_id, :patient_id, :current_stage_id, :status, :created_at, :updated_at)
    ON CONFLICT (id) DO NOTHING
    """)
    
    session.execute(insert_instance, {
        "id": instance_id,
        "tenant_id": str(tenant_id),
        "journey_id": journey_id,
        "patient_id": patient_id,
        "current_stage_id": current_stage["id"],
        "status": status,
        "created_at": created_at,
        "updated_at": created_at
    })
    
    # Create stage statuses for this instance
    for j, stage in enumerate(j_stages):
        if j < stage_idx:
            stage_status = "completed"
            entered_at = created_at + timedelta(days=j)
            completed_at = created_at + timedelta(days=j+1)
        elif j == stage_idx:
            stage_status = "in_progress"
            entered_at = created_at + timedelta(days=j)
            completed_at = None
        else:
            stage_status = "pending"
            entered_at = None
            completed_at = None
        
        insert_stage_status = text("""
        INSERT INTO journey_instance_stage_status (id, journey_instance_id, stage_id, status, entered_at, completed_at)
        VALUES (:id, :journey_instance_id, :stage_id, :status, :entered_at, :completed_at)
        ON CONFLICT (id) DO NOTHING
        """)
        
        session.execute(insert_stage_status, {
            "id": str(uuid.uuid4()),
            "journey_instance_id": instance_id,
            "stage_id": stage["id"],
            "status": stage_status,
            "entered_at": entered_at,
            "completed_at": completed_at
        })
    
    print(f"  Created instance: {patient_name} → {journey_name} (Stage: {current_stage['name']}, Status: {status})")
    instances_created += 1

session.commit()
print(f"\nSuccessfully seeded {instances_created} journey instances!")
session.close()

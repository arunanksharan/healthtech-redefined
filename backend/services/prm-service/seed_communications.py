"""
Script to seed sample communications
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
import json

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://healthtech:healthtech@127.0.0.1:5433/healthtech")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Get required data
tenant_result = session.execute(text("SELECT id FROM tenants LIMIT 1")).fetchone()
patient_result = session.execute(text("SELECT id FROM patients LIMIT 1")).fetchone()
instance_result = session.execute(text("SELECT id FROM journey_instances LIMIT 1")).fetchone()
user_result = session.execute(text("SELECT id FROM users LIMIT 1")).fetchone()

if not tenant_result:
    print("No tenant found. Please seed basic data first.")
    sys.exit(1)

tenant_id = tenant_result[0]
patient_id = patient_result[0] if patient_result else None
instance_id = instance_result[0] if instance_result else None
user_id = user_result[0] if user_result else None

print(f"Using tenant_id: {tenant_id}")
print(f"Using patient_id: {patient_id}")

# Sample communications matching the Model structure
# Model has: channel, direction, template_code, content, status, related_resource_type...
communications = [
    {
        "id": str(uuid.uuid4()),
        "tenant_id": str(tenant_id),
        "patient_id": str(patient_id) if patient_id else None,
        "journey_instance_id": str(instance_id) if instance_id else None,
        "channel": "sms",
        "direction": "outbound",
        "template_code": "APPT_REMINDER",
        "content": "Reminder: You have an appointment with Dr. Sharma tomorrow at 10:00 AM. Reply C to confirm.",
        "content_structured": json.dumps({"text": "Reminder: You have an appointment with Dr. Sharma tomorrow at 10:00 AM. Reply C to confirm."}),
        "status": "delivered",
        "related_resource_type": "Appointment",
        "created_by_user_id": None
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": str(tenant_id),
        "patient_id": str(patient_id) if patient_id else None,
        "journey_instance_id": None,
        "channel": "whatsapp",
        "direction": "outbound",
        "template_code": "WELCOME_MSG",
        "content": "Welcome to Apollo Hospital! We are here to support your health journey.",
        "content_structured": json.dumps({"type": "text", "body": "Welcome to Apollo Hospital! We are here to support your health journey."}),
        "status": "read",
        "related_resource_type": "Patient",
        "created_by_user_id": str(user_id) if user_id else None
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": str(tenant_id),
        "patient_id": str(patient_id) if patient_id else None,
        "journey_instance_id": str(instance_id) if instance_id else None,
        "channel": "email",
        "direction": "outbound",
        "template_code": "LAB_RESULTS",
        "content": "Your lab results are ready. Please log in to the patient portal to view them.",
        "content_structured": json.dumps({"subject": "Lab Results Ready", "body": "Your lab results are ready..."}),
        "status": "sent",
        "related_resource_type": "Encounter",
        "created_by_user_id": None
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": str(tenant_id),
        "patient_id": str(patient_id) if patient_id else None,
        "journey_instance_id": None,
        "channel": "sms",
        "direction": "inbound",
        "template_code": None,
        "content": "C",
        "content_structured": None,
        "status": "received",
        "related_resource_type": "Appointment",
        "created_by_user_id": None
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": str(tenant_id),
        "patient_id": str(patient_id) if patient_id else None,
        "journey_instance_id": None,
        "channel": "phone",
        "direction": "outbound",
        "template_code": "FOLLOW_UP_CALL",
        "content": "Transcribed call log: Patient is feeling better, no pain.",
        "content_structured": json.dumps({"duration": 120, "notes": "Patient feeling better"}),
        "status": "completed",
        "related_resource_type": "Task",
        "created_by_user_id": str(user_id) if user_id else None
    }
]

# Insert communications
now = datetime.utcnow()
for i, comm in enumerate(communications):
    created_at = now - timedelta(hours=i*4)
    
    insert_query = text("""
    INSERT INTO communications (
        id, tenant_id, patient_id, journey_instance_id, channel, direction, 
        template_code, content, content_structured, status, related_resource_type, 
        created_by_user_id, created_at, updated_at
    )
    VALUES (
        :id, :tenant_id, :patient_id, :journey_instance_id, :channel, :direction,
        :template_code, :content, :content_structured, :status, :related_resource_type,
        :created_by_user_id, :created_at, :updated_at
    )
    ON CONFLICT (id) DO NOTHING
    """)
    
    session.execute(insert_query, {
        **comm,
        "created_at": created_at,
        "updated_at": created_at
    })
    print(f"Inserted {comm['channel']} communication...")

session.commit()
print(f"\nSuccessfully seeded {len(communications)} communications!")
session.close()

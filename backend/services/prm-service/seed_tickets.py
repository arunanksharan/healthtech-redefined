"""
Script to seed sample tickets for testing
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

# Get a tenant, patient, and user from the database
tenant_result = session.execute(text("SELECT id FROM tenants LIMIT 1")).fetchone()
patient_result = session.execute(text("SELECT id FROM patients LIMIT 1")).fetchone()
user_result = session.execute(text("SELECT id FROM users LIMIT 1")).fetchone()

if not tenant_result:
    print("No tenant found in database. Please seed basic data first.")
    sys.exit(1)

tenant_id = tenant_result[0]
patient_id = patient_result[0] if patient_result else None
user_id = user_result[0] if user_result else None

print(f"Using tenant_id: {tenant_id}")
print(f"Using patient_id: {patient_id}")
print(f"Using user_id: {user_id}")

# Sample tickets
tickets = [
    {
        "id": str(uuid.uuid4()),
        "tenant_id": str(tenant_id),
        "patient_id": str(patient_id) if patient_id else None,
        "title": "Patient unable to access appointment booking portal",
        "description": "Patient reports getting an error message when trying to book an appointment online. They have tried multiple browsers and cleared cache.",
        "status": "open",
        "priority": "high",
        "created_by_user_id": str(user_id) if user_id else None,
        "assigned_to_user_id": str(user_id) if user_id else None,
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": str(tenant_id),
        "patient_id": str(patient_id) if patient_id else None,
        "title": "Request for medical records copy",
        "description": "Patient requesting a copy of their complete medical records for insurance purposes.",
        "status": "in_progress",
        "priority": "medium",
        "created_by_user_id": str(user_id) if user_id else None,
        "assigned_to_user_id": str(user_id) if user_id else None,
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": str(tenant_id),
        "patient_id": str(patient_id) if patient_id else None,
        "title": "Billing inquiry - duplicate charge",
        "description": "Patient noticed a duplicate charge on their last visit bill and requests clarification.",
        "status": "open",
        "priority": "urgent",
        "created_by_user_id": str(user_id) if user_id else None,
        "assigned_to_user_id": None,
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": str(tenant_id),
        "patient_id": str(patient_id) if patient_id else None,
        "title": "Prescription refill request",
        "description": "Patient needs a refill on their blood pressure medication. Current prescription expires in 3 days.",
        "status": "resolved",
        "priority": "high",
        "created_by_user_id": str(user_id) if user_id else None,
        "assigned_to_user_id": str(user_id) if user_id else None,
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": str(tenant_id),
        "patient_id": None,  # General inquiry, no patient
        "title": "Inquiry about new cardiology department hours",
        "description": "General inquiry about the operating hours of the new cardiology department.",
        "status": "closed",
        "priority": "low",
        "created_by_user_id": str(user_id) if user_id else None,
        "assigned_to_user_id": str(user_id) if user_id else None,
    },
    {
        "id": str(uuid.uuid4()),
        "tenant_id": str(tenant_id),
        "patient_id": str(patient_id) if patient_id else None,
        "title": "Follow-up appointment not scheduled",
        "description": "Patient was supposed to receive a follow-up appointment after their cardiac procedure but hasn't been contacted.",
        "status": "in_progress",
        "priority": "high",
        "created_by_user_id": str(user_id) if user_id else None,
        "assigned_to_user_id": str(user_id) if user_id else None,
    },
]

# Insert tickets
now = datetime.utcnow()
for i, ticket in enumerate(tickets):
    # Vary created_at times
    created_at = now - timedelta(days=i, hours=i*2)
    
    insert_query = text("""
    INSERT INTO tickets (id, tenant_id, patient_id, title, description, status, priority, 
                        created_by_user_id, assigned_to_user_id, created_at, updated_at)
    VALUES (:id, :tenant_id, :patient_id, :title, :description, :status, :priority,
            :created_by_user_id, :assigned_to_user_id, :created_at, :updated_at)
    ON CONFLICT (id) DO NOTHING
    """)
    
    session.execute(
        insert_query,
        {
            **ticket,
            "created_at": created_at,
            "updated_at": created_at
        }
    )
    print(f"Inserted ticket: {ticket['title'][:50]}...")

session.commit()
print(f"\nSuccessfully seeded {len(tickets)} tickets!")
session.close()


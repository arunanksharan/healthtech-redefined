"""
Script to seed journey definitions (The Map)
"""
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add paths
script_dir = Path(__file__).parent
service_dir = script_dir.parent
backend_dir = service_dir.parent.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(service_dir))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}", level="INFO")

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://healthtech:healthtech@127.0.0.1:5433/healthtech")

def seed_journeys():
    """Seed journey definitions and stages"""
    logger.info("Seeding journey definitions...")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Get tenant
        tenant_result = session.execute(text("SELECT id FROM tenants LIMIT 1")).fetchone()
        if not tenant_result:
            logger.error("No tenant found. Please seed basic data first.")
            return

        tenant_id = str(tenant_result[0])
        logger.info(f"Using tenant_id: {tenant_id}")

        # 1. JOURNEYS
        journeys = [
            {"id": "90000000-0000-0000-0000-000000000001", "tenant_id": tenant_id, "journey_type": "opd", "name": "Cardiology New Patient Journey", "description": "Pre-visit to post-visit journey for new cardiology patients", "is_default": False, "trigger_conditions": json.dumps({"condition": "Appointment.Created", "specialty": "Cardiology"})},
            {"id": "90000000-0000-0000-0000-000000000002", "tenant_id": tenant_id, "journey_type": "procedure", "name": "Orthopedic Post-Surgery Journey", "description": "Post-operative care journey for orthopedic patients", "is_default": False, "trigger_conditions": json.dumps({"condition": "Surgery.Completed", "type": "Ortho"})},
            {"id": "90000000-0000-0000-0000-000000000003", "tenant_id": tenant_id, "journey_type": "chronic_care", "name": "Diabetes Management Program", "description": "Ongoing diabetes care and monitoring journey", "is_default": True, "trigger_conditions": json.dumps({"condition": "Diagnosis.Added", "code": "E11"})},
            {"id": "90000000-0000-0000-0000-000000000004", "tenant_id": tenant_id, "journey_type": "wellness", "name": "General Follow-up Journey", "description": "Standard follow-up care journey", "is_default": False, "trigger_conditions": json.dumps({"condition": "Discharge.Completed"})}
        ]

        now = datetime.utcnow()
        
        for journey in journeys:
            insert_journey = text("""
            INSERT INTO journeys (id, tenant_id, journey_type, name, description, is_default, trigger_conditions, created_at, updated_at)
            VALUES (:id, :tenant_id, :journey_type, :name, :description, :is_default, :trigger_conditions, :created_at, :updated_at)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                journey_type = EXCLUDED.journey_type,
                trigger_conditions = EXCLUDED.trigger_conditions
            """)
            
            session.execute(insert_journey, {**journey, "created_at": now, "updated_at": now})
            logger.info(f"Seeded journey: {journey['name']}")

        # 2. STAGES
        # Note: 'actions' field in DB corresponds to 'config' in JSON for simplicity
        stages = [
            {"id": "91000000-0000-0000-0000-000000000001", "journey_id": "90000000-0000-0000-0000-000000000001", "order_index": 1, "name": "Pre-Visit Preparation", "description": "Patient preparation before appointment", "trigger_event": "Appointment.Created", "actions": json.dumps({"days_before": 3, "send_reminders": True})},
            {"id": "91000000-0000-0000-0000-000000000002", "journey_id": "90000000-0000-0000-0000-000000000001", "order_index": 2, "name": "Day of Visit", "description": "Check-in and consultation", "trigger_event": "Appointment.CheckedIn", "actions": json.dumps({})},
            {"id": "91000000-0000-0000-0000-000000000003", "journey_id": "90000000-0000-0000-0000-000000000001", "order_index": 3, "name": "Post-Visit Follow-up", "description": "Post-consultation care instructions", "trigger_event": "Encounter.Completed", "actions": json.dumps({"follow_up_days": 7})},
            
            {"id": "91000000-0000-0000-0000-000000000004", "journey_id": "90000000-0000-0000-0000-000000000002", "order_index": 1, "name": "Immediate Post-Op", "description": "First 24-48 hours after surgery", "trigger_event": "Surgery.Completed", "actions": json.dumps({})},
            {"id": "91000000-0000-0000-0000-000000000005", "journey_id": "90000000-0000-0000-0000-000000000002", "order_index": 2, "name": "Recovery Phase", "description": "First 2 weeks of recovery", "trigger_event": "Task.Completed", "actions": json.dumps({"duration_days": 14})},
            {"id": "91000000-0000-0000-0000-000000000006", "journey_id": "90000000-0000-0000-0000-000000000002", "order_index": 3, "name": "Rehabilitation", "description": "Physical therapy and recovery exercises", "trigger_event": "Task.Completed", "actions": json.dumps({"duration_weeks": 6})},
            
            {"id": "91000000-0000-0000-0000-000000000007", "journey_id": "90000000-0000-0000-0000-000000000003", "order_index": 1, "name": "Initial Assessment", "description": "Comprehensive diabetes evaluation", "trigger_event": "Enrollment", "actions": json.dumps({})},
            {"id": "91000000-0000-0000-0000-000000000008", "journey_id": "90000000-0000-0000-0000-000000000003", "order_index": 2, "name": "Ongoing Monitoring", "description": "Regular monitoring and adjustments", "trigger_event": "Assessment.Completed", "actions": json.dumps({"check_interval_days": 30})},
            
            {"id": "91000000-0000-0000-0000-000000000009", "journey_id": "90000000-0000-0000-0000-000000000004", "order_index": 1, "name": "Schedule Follow-up", "description": "Schedule next appointment", "trigger_event": "Discharge", "actions": json.dumps({})},
            {"id": "91000000-0000-0000-0000-000000000010", "journey_id": "90000000-0000-0000-0000-000000000004", "order_index": 2, "name": "Follow-up Complete", "description": "Follow-up completed", "trigger_event": "Appointment.Completed", "actions": json.dumps({})}
        ]

        for stage in stages:
            insert_stage = text("""
            INSERT INTO journey_stages (id, journey_id, name, description, order_index, trigger_event, actions, created_at, updated_at)
            VALUES (:id, :journey_id, :name, :description, :order_index, :trigger_event, :actions, :created_at, :updated_at)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                order_index = EXCLUDED.order_index,
                actions = EXCLUDED.actions
            """)
            
            session.execute(insert_stage, {**stage, "created_at": now, "updated_at": now})
            
        session.commit()
        logger.success(f"Successfully seeded {len(stages)} journey stages!")
        
    finally:
        session.close()

if __name__ == "__main__":
    seed_journeys()

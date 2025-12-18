#!/usr/bin/env python3
"""
Seed Clinical Data Script
Creates Observations, Conditions, Medications, and Diagnostic Reports.
Stores them in the fhir_resources table.
"""
import sys
import os
import json
import random
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4

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

# Common Conditions
CONDITIONS = [
    {"code": "I10", "display": "Essential (primary) hypertension", "severity": "moderate"},
    {"code": "E11", "display": "Type 2 diabetes mellitus", "severity": "moderate"},
    {"code": "J45", "display": "Asthma", "severity": "mild"},
    {"code": "K21.9", "display": "Gastro-oesophageal reflux disease", "severity": "mild"},
    {"code": "M54.5", "display": "Low back pain", "severity": "moderate"},
    {"code": "R51", "display": "Headache", "severity": "mild"},
    {"code": "J00", "display": "Acute nasopharyngitis [common cold]", "severity": "mild"},
]

# Common Vitals
VITALS = [
    {"code": "8867-4", "display": "Heart rate", "unit": "beats/min", "min": 60, "max": 100},
    {"code": "8310-5", "display": "Body temperature", "unit": "degC", "min": 36.1, "max": 37.5},
    {"code": "9279-1", "display": "Respiratory rate", "unit": "breaths/min", "min": 12, "max": 20},
    {"code": "8480-6", "display": "Systolic blood pressure", "unit": "mmHg", "min": 100, "max": 140},
    {"code": "8462-4", "display": "Diastolic blood pressure", "unit": "mmHg", "min": 60, "max": 90},
]

# Common Medications
MEDICATIONS = [
    {"code": "1191", "display": "Aspirin 81 MG", "system": "http://www.nlm.nih.gov/research/umls/rxnorm"},
    {"code": "197361", "display": "Lisinopril 10 MG", "system": "http://www.nlm.nih.gov/research/umls/rxnorm"},
    {"code": "860975", "display": "Metformin 500 MG", "system": "http://www.nlm.nih.gov/research/umls/rxnorm"},
    {"code": "197381", "display": "Atorvastatin 20 MG", "system": "http://www.nlm.nih.gov/research/umls/rxnorm"},
    {"code": "308136", "display": "Amoxicillin 500 MG", "system": "http://www.nlm.nih.gov/research/umls/rxnorm"},
]

# Common Reports
REPORTS = [
    {"code": "58410-2", "display": "CBC with Auto Differential panel", "category": "LAB"},
    {"code": "24331-1", "display": "Lipid Panel", "category": "LAB"},
    {"code": "4548-4", "display": "Hemoglobin A1c", "category": "LAB"},
    {"code": "36642-7", "display": "Chest X-Ray 2 Views", "category": "RAD"},
    {"code": "24725-4", "display": "CT Head w/o contrast", "category": "RAD"},
]

def seed_clinical_data():
    """Seed clinical data"""
    logger.info("Connecting to database...")
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Get Tenant
        result = conn.execute(text("SELECT id FROM tenants LIMIT 1"))
        tenant_row = result.fetchone()
        if not tenant_row:
            logger.error("No tenants found! Run the main seed first.")
            return
        tenant_id = str(tenant_row[0])
        
        # Get Patients
        patients = [str(row[0]) for row in conn.execute(text("SELECT id FROM patients LIMIT 50")).fetchall()]
        if not patients:
            logger.error("No patients found!")
            return
        
        logger.info(f"Seeding data for {len(patients)} patients...")
        
        obs_count = 0
        cond_count = 0
        med_count = 0
        rep_count = 0
        
        for patient_id in patients:
            # 1. Create Conditions (1-3 per patient)
            for _ in range(random.randint(1, 3)):
                cond_def = random.choice(CONDITIONS)
                cond_id = uuid4()
                fhir_id = f"cond-{str(cond_id)[:8]}"
                
                resource_data = {
                    "resourceType": "Condition",
                    "id": fhir_id,
                    "clinicalStatus": {
                        "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]
                    },
                    "verificationStatus": {
                        "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": "confirmed"}]
                    },
                    "category": [{
                        "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-category", "code": "problem-list-item"}]
                    }],
                    "severity": {
                        "coding": [{"system": "http://snomed.info/sct", "code": cond_def["severity"]}]
                    },
                    "code": {
                        "coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": cond_def["code"], "display": cond_def["display"]}]
                    },
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "onsetDateTime": (datetime.utcnow() - timedelta(days=random.randint(10, 365))).isoformat()
                }
                
                conn.execute(
                    text("""
                    INSERT INTO fhir_resources (
                        id, tenant_id, resource_type, resource_id, version, is_current, 
                        resource, meta_data, created_at, updated_at
                    ) VALUES (
                        :id, :tenant_id, 'Condition', :resource_id, 1, true,
                        :resource, :meta_data, NOW(), NOW()
                    )
                    """),
                    {
                        "id": cond_id,
                        "tenant_id": tenant_id,
                        "resource_id": fhir_id,
                        "resource": json.dumps(resource_data),
                        "meta_data": json.dumps({})
                    }
                )
                cond_count += 1

            # 2. Medications (1-2 per patient)
            for _ in range(random.randint(1, 2)):
                med_def = random.choice(MEDICATIONS)
                med_id = uuid4()
                fhir_id = f"medrx-{str(med_id)[:8]}"
                dt = datetime.utcnow() - timedelta(days=random.randint(1, 60))
                
                status = random.choice(["active", "completed", "active", "active"]) # mostly active

                resource_data = {
                    "resourceType": "MedicationRequest",
                    "id": fhir_id,
                    "status": status,
                    "intent": "order",
                    "medicationCodeableConcept": {
                        "coding": [{
                            "system": med_def["system"],
                            "code": med_def["code"],
                            "display": med_def["display"]
                        }]
                    },
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "authoredOn": dt.isoformat(),
                    "dosageInstruction": [{
                        "text": "1 pill daily",
                        "timing": {"code": {"text": "QD"}},
                        "route": {"text": "Oral"}
                    }]
                }
                
                conn.execute(
                    text("""
                    INSERT INTO fhir_resources (
                        id, tenant_id, resource_type, resource_id, version, is_current, 
                        resource, meta_data, created_at, updated_at
                    ) VALUES (
                        :id, :tenant_id, 'MedicationRequest', :resource_id, 1, true,
                        :resource, :meta_data, :created_at, :updated_at
                    )
                    """),
                    {
                        "id": med_id,
                        "tenant_id": tenant_id,
                        "resource_id": fhir_id,
                        "resource": json.dumps(resource_data),
                        "meta_data": json.dumps({}),
                        "created_at": dt,
                        "updated_at": dt
                    }
                )
                med_count += 1

            # 3. Encounters & Related (Obs, Reports)
            encounters = [str(row[0]) for row in conn.execute(text(f"SELECT id FROM encounters WHERE patient_id = '{patient_id}'")).fetchall()]
            targets = encounters if encounters else [None] * 2 
            
            for enc_id in targets:
                # Vitals
                for _ in range(random.randint(1, 2)):
                    vital_def = random.choice(VITALS)
                    obs_id = uuid4()
                    fhir_id = f"obs-{str(obs_id)[:8]}"
                    
                    val = round(random.uniform(vital_def["min"], vital_def["max"]), 1)
                    interp = "normal"
                    if val > vital_def["max"] * 0.95: interp = "high"
                    if val < vital_def["min"] * 1.05: interp = "low"
                    if val > vital_def["max"] or val < vital_def["min"]: interp = "abnormal"

                    dt = datetime.utcnow() - timedelta(days=random.randint(0, 30))
                    
                    resource_data = {
                        "resourceType": "Observation",
                        "id": fhir_id,
                        "status": "final",
                        "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}]}],
                        "code": {"coding": [{"system": "http://loinc.org", "code": vital_def["code"], "display": vital_def["display"]}]},
                        "subject": {"reference": f"Patient/{patient_id}"},
                        "valueQuantity": {
                            "value": val,
                            "unit": vital_def["unit"],
                            "system": "http://unitsofmeasure.org",
                            "code": vital_def["unit"]
                        },
                        "effectiveDateTime": dt.isoformat(),
                        "interpretation": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation", "code": interp}]}]
                    }
                    if enc_id:
                        resource_data["encounter"] = {"reference": f"Encounter/{enc_id}"}
                    
                    conn.execute(
                        text("""
                        INSERT INTO fhir_resources (
                            id, tenant_id, resource_type, resource_id, version, is_current, 
                            resource, meta_data, created_at, updated_at
                        ) VALUES (
                            :id, :tenant_id, 'Observation', :resource_id, 1, true,
                            :resource, :meta_data, :created_at, :updated_at
                        )
                        """),
                        {
                            "id": obs_id,
                            "tenant_id": tenant_id,
                            "resource_id": fhir_id,
                            "resource": json.dumps(resource_data),
                            "meta_data": json.dumps({}),
                            "created_at": dt,
                            "updated_at": dt
                        }
                    )
                    obs_count += 1
                
                # Diagnostic Reports (occasional)
                if random.random() < 0.4: # 40% chance per encounter/moment
                    rep_def = random.choice(REPORTS)
                    rep_id = uuid4()
                    fhir_id = f"dr-{str(rep_id)[:8]}"
                    dt = datetime.utcnow() - timedelta(days=random.randint(1, 30))
                    
                    resource_data = {
                        "resourceType": "DiagnosticReport",
                        "id": fhir_id,
                        "status": "final",
                        "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0074", "code": rep_def["category"]}]}],
                        "code": {"coding": [{"system": "http://loinc.org", "code": rep_def["code"], "display": rep_def["display"]}]},
                        "subject": {"reference": f"Patient/{patient_id}"},
                        "effectiveDateTime": dt.isoformat(),
                        "issued": dt.isoformat(),
                        "conclusion": "Findings within normal limits."
                    }
                    if enc_id:
                        resource_data["encounter"] = {"reference": f"Encounter/{enc_id}"}

                    conn.execute(
                        text("""
                        INSERT INTO fhir_resources (
                            id, tenant_id, resource_type, resource_id, version, is_current, 
                            resource, meta_data, created_at, updated_at
                        ) VALUES (
                            :id, :tenant_id, 'DiagnosticReport', :resource_id, 1, true,
                            :resource, :meta_data, :created_at, :updated_at
                        )
                        """),
                        {
                            "id": rep_id,
                            "tenant_id": tenant_id,
                            "resource_id": fhir_id,
                            "resource": json.dumps(resource_data),
                            "meta_data": json.dumps({}),
                            "created_at": dt,
                            "updated_at": dt
                        }
                    )
                    rep_count += 1
                    
        conn.commit()
        logger.success(f"Seeded: {cond_count} Conditions, {med_count} Medications, {obs_count} Observations, {rep_count} Reports.")

if __name__ == "__main__":
    seed_clinical_data()

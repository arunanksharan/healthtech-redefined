"""
Test Data Service

Service for synthetic test data generation and management.
"""

import hashlib
import json
import random
import string
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from modules.quality.models import (
    TestDataSet, DataSeedExecution, SyntheticDataGenerator,
    DataGeneratorType, TestEnvironment, TestRunStatus
)


# FHIR resource generators
FHIR_GENERATORS = {
    DataGeneratorType.PATIENT: {
        "resourceType": "Patient",
        "fields": {
            "id": {"type": "uuid"},
            "identifier": {"type": "mrn"},
            "name": {"type": "human_name"},
            "gender": {"type": "choice", "options": ["male", "female", "other", "unknown"]},
            "birthDate": {"type": "date", "min_age": 0, "max_age": 100},
            "telecom": {"type": "contact_points"},
            "address": {"type": "address"},
        },
    },
    DataGeneratorType.PRACTITIONER: {
        "resourceType": "Practitioner",
        "fields": {
            "id": {"type": "uuid"},
            "identifier": {"type": "npi"},
            "name": {"type": "human_name"},
            "telecom": {"type": "contact_points"},
            "qualification": {"type": "qualification"},
        },
    },
    DataGeneratorType.ORGANIZATION: {
        "resourceType": "Organization",
        "fields": {
            "id": {"type": "uuid"},
            "identifier": {"type": "org_id"},
            "name": {"type": "org_name"},
            "type": {"type": "org_type"},
            "telecom": {"type": "contact_points"},
            "address": {"type": "address"},
        },
    },
    DataGeneratorType.ENCOUNTER: {
        "resourceType": "Encounter",
        "fields": {
            "id": {"type": "uuid"},
            "status": {"type": "choice", "options": ["planned", "arrived", "in-progress", "finished", "cancelled"]},
            "class": {"type": "encounter_class"},
            "type": {"type": "encounter_type"},
            "period": {"type": "period"},
            "reasonCode": {"type": "condition_code"},
        },
    },
    DataGeneratorType.OBSERVATION: {
        "resourceType": "Observation",
        "fields": {
            "id": {"type": "uuid"},
            "status": {"type": "choice", "options": ["registered", "preliminary", "final", "amended"]},
            "code": {"type": "observation_code"},
            "effectiveDateTime": {"type": "datetime"},
            "valueQuantity": {"type": "quantity"},
        },
    },
    DataGeneratorType.CONDITION: {
        "resourceType": "Condition",
        "fields": {
            "id": {"type": "uuid"},
            "clinicalStatus": {"type": "choice", "options": ["active", "recurrence", "relapse", "inactive", "remission", "resolved"]},
            "verificationStatus": {"type": "choice", "options": ["unconfirmed", "provisional", "differential", "confirmed", "refuted"]},
            "code": {"type": "condition_code"},
            "onsetDateTime": {"type": "datetime"},
        },
    },
    DataGeneratorType.MEDICATION: {
        "resourceType": "MedicationRequest",
        "fields": {
            "id": {"type": "uuid"},
            "status": {"type": "choice", "options": ["active", "on-hold", "cancelled", "completed", "stopped"]},
            "intent": {"type": "choice", "options": ["proposal", "plan", "order", "original-order"]},
            "medicationCodeableConcept": {"type": "medication_code"},
            "dosageInstruction": {"type": "dosage"},
        },
    },
    DataGeneratorType.APPOINTMENT: {
        "resourceType": "Appointment",
        "fields": {
            "id": {"type": "uuid"},
            "status": {"type": "choice", "options": ["proposed", "pending", "booked", "arrived", "fulfilled", "cancelled", "noshow"]},
            "appointmentType": {"type": "appointment_type"},
            "start": {"type": "future_datetime"},
            "end": {"type": "future_datetime"},
            "minutesDuration": {"type": "choice", "options": [15, 30, 45, 60]},
        },
    },
    DataGeneratorType.CLAIM: {
        "resourceType": "Claim",
        "fields": {
            "id": {"type": "uuid"},
            "status": {"type": "choice", "options": ["active", "cancelled", "draft", "entered-in-error"]},
            "type": {"type": "claim_type"},
            "use": {"type": "choice", "options": ["claim", "preauthorization", "predetermination"]},
            "created": {"type": "datetime"},
            "total": {"type": "money"},
        },
    },
}

# Sample data for realistic generation
FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
STREET_NAMES = ["Main St", "Oak Ave", "Maple Dr", "Cedar Ln", "Pine Rd", "Elm St", "Washington Ave", "Park Blvd"]
CITIES = ["Springfield", "Riverside", "Clinton", "Georgetown", "Franklin", "Salem", "Madison", "Chester"]
STATES = ["CA", "TX", "FL", "NY", "IL", "PA", "OH", "GA", "NC", "MI"]

ICD10_CODES = [
    ("J06.9", "Acute upper respiratory infection"),
    ("E11.9", "Type 2 diabetes mellitus"),
    ("I10", "Essential hypertension"),
    ("K21.0", "Gastro-esophageal reflux disease"),
    ("M54.5", "Low back pain"),
    ("J45.909", "Unspecified asthma"),
]

MEDICATION_CODES = [
    ("197361", "Metformin 500 MG"),
    ("314076", "Lisinopril 10 MG"),
    ("308136", "Atorvastatin 20 MG"),
    ("311671", "Omeprazole 20 MG"),
    ("197806", "Ibuprofen 400 MG"),
]


class TestDataService:
    """Service for test data management."""

    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self._random = random.Random()

    def _set_seed(self, seed: Optional[int]):
        """Set random seed for reproducibility."""
        if seed is not None:
            self._random.seed(seed)

    # =========================================================================
    # Data Generation
    # =========================================================================

    def generate_fhir_resource(
        self,
        data_type: DataGeneratorType,
        config: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Generate a single FHIR resource."""
        generator_config = FHIR_GENERATORS.get(data_type)
        if not generator_config:
            raise ValueError(f"Unknown data type: {data_type}")

        resource = {"resourceType": generator_config["resourceType"]}

        for field_name, field_config in generator_config["fields"].items():
            value = self._generate_field(field_config, config)
            if value is not None:
                resource[field_name] = value

        return resource

    def _generate_field(
        self,
        field_config: Dict[str, Any],
        context: Dict[str, Any] = None,
    ) -> Any:
        """Generate a field value based on config."""
        field_type = field_config["type"]

        if field_type == "uuid":
            return str(uuid4())

        elif field_type == "mrn":
            return [{
                "system": "http://hospital.example.org/mrn",
                "value": f"MRN{self._random.randint(100000, 999999)}",
            }]

        elif field_type == "npi":
            return [{
                "system": "http://hl7.org/fhir/sid/us-npi",
                "value": f"{self._random.randint(1000000000, 9999999999)}",
            }]

        elif field_type == "human_name":
            return [{
                "family": self._random.choice(LAST_NAMES),
                "given": [self._random.choice(FIRST_NAMES)],
            }]

        elif field_type == "choice":
            return self._random.choice(field_config["options"])

        elif field_type == "date":
            min_age = field_config.get("min_age", 0)
            max_age = field_config.get("max_age", 100)
            age = self._random.randint(min_age, max_age)
            birth_date = datetime.now() - timedelta(days=age * 365)
            return birth_date.strftime("%Y-%m-%d")

        elif field_type == "datetime":
            days_ago = self._random.randint(1, 365)
            dt = datetime.now() - timedelta(days=days_ago)
            return dt.isoformat()

        elif field_type == "future_datetime":
            days_ahead = self._random.randint(1, 90)
            dt = datetime.now() + timedelta(days=days_ahead)
            return dt.isoformat()

        elif field_type == "contact_points":
            return [{
                "system": "phone",
                "value": f"({self._random.randint(200, 999)}) {self._random.randint(200, 999)}-{self._random.randint(1000, 9999)}",
                "use": "home",
            }]

        elif field_type == "address":
            return [{
                "line": [f"{self._random.randint(100, 9999)} {self._random.choice(STREET_NAMES)}"],
                "city": self._random.choice(CITIES),
                "state": self._random.choice(STATES),
                "postalCode": f"{self._random.randint(10000, 99999)}",
                "country": "US",
            }]

        elif field_type == "condition_code":
            code, display = self._random.choice(ICD10_CODES)
            return [{
                "coding": [{
                    "system": "http://hl7.org/fhir/sid/icd-10-cm",
                    "code": code,
                    "display": display,
                }]
            }]

        elif field_type == "medication_code":
            code, display = self._random.choice(MEDICATION_CODES)
            return {
                "coding": [{
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": code,
                    "display": display,
                }]
            }

        elif field_type == "quantity":
            return {
                "value": round(self._random.uniform(50, 200), 1),
                "unit": "mg/dL",
                "system": "http://unitsofmeasure.org",
            }

        elif field_type == "money":
            return {
                "value": round(self._random.uniform(100, 10000), 2),
                "currency": "USD",
            }

        elif field_type == "period":
            start = datetime.now() - timedelta(days=self._random.randint(1, 30))
            end = start + timedelta(hours=self._random.randint(1, 8))
            return {
                "start": start.isoformat(),
                "end": end.isoformat(),
            }

        elif field_type == "encounter_class":
            return {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": self._random.choice(["AMB", "EMER", "IMP", "OBSENC"]),
            }

        return None

    def generate_batch(
        self,
        data_type: DataGeneratorType,
        count: int,
        seed: Optional[int] = None,
        config: Dict[str, Any] = None,
    ) -> List[Dict[str, Any]]:
        """Generate a batch of FHIR resources."""
        self._set_seed(seed)
        return [
            self.generate_fhir_resource(data_type, config)
            for _ in range(count)
        ]

    # =========================================================================
    # Test Data Sets
    # =========================================================================

    async def create_data_set(
        self,
        name: str,
        version: str,
        data_type: DataGeneratorType,
        record_count: Optional[int] = None,
        description: Optional[str] = None,
        generator_config: Dict[str, Any] = None,
        seed: Optional[int] = None,
        contains_pii: bool = False,
        pii_masked: bool = True,
        masking_rules: Dict[str, Any] = None,
        compatible_environments: List[str] = None,
        created_by: Optional[UUID] = None,
    ) -> TestDataSet:
        """Create a test data set definition."""
        data_set = TestDataSet(
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            version=version,
            data_type=data_type,
            record_count=record_count,
            generator_config=generator_config or {},
            seed=seed,
            contains_pii=contains_pii,
            pii_masked=pii_masked,
            masking_rules=masking_rules or {},
            compatible_environments=compatible_environments or ["local", "ci", "staging"],
            created_by=created_by,
        )
        self.session.add(data_set)
        await self.session.flush()
        return data_set

    async def get_data_set(self, data_set_id: UUID) -> Optional[TestDataSet]:
        """Get a test data set by ID."""
        result = await self.session.execute(
            select(TestDataSet).where(
                and_(
                    TestDataSet.id == data_set_id,
                    TestDataSet.tenant_id == self.tenant_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_data_sets(
        self,
        data_type: Optional[DataGeneratorType] = None,
        is_active: bool = True,
    ) -> List[TestDataSet]:
        """List test data sets."""
        query = select(TestDataSet).where(
            and_(
                TestDataSet.tenant_id == self.tenant_id,
                TestDataSet.is_active == is_active,
            )
        )
        if data_type:
            query = query.where(TestDataSet.data_type == data_type)

        query = query.order_by(desc(TestDataSet.created_at))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def generate_and_store(
        self,
        data_set_id: UUID,
        count: int,
    ) -> Dict[str, Any]:
        """Generate data for a data set and return it."""
        data_set = await self.get_data_set(data_set_id)
        if not data_set:
            return {"error": "Data set not found"}

        records = self.generate_batch(
            data_type=data_set.data_type,
            count=count,
            seed=data_set.seed,
            config=data_set.generator_config,
        )

        # Apply PII masking if needed
        if data_set.pii_masked and data_set.masking_rules:
            records = [self._apply_masking(r, data_set.masking_rules) for r in records]

        # Calculate checksum
        content = json.dumps(records, sort_keys=True)
        checksum = hashlib.sha256(content.encode()).hexdigest()

        # Update data set
        data_set.record_count = count
        data_set.file_size_bytes = len(content)
        data_set.checksum = checksum
        data_set.file_format = "json"
        await self.session.flush()

        return {
            "data_set_id": str(data_set_id),
            "count": count,
            "records": records,
            "checksum": checksum,
        }

    def _apply_masking(
        self,
        record: Dict[str, Any],
        rules: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Apply PII masking rules to a record."""
        masked = record.copy()

        for field, rule in rules.items():
            if field in masked:
                if rule == "redact":
                    masked[field] = "[REDACTED]"
                elif rule == "hash":
                    if isinstance(masked[field], str):
                        masked[field] = hashlib.md5(masked[field].encode()).hexdigest()[:8]
                elif rule == "anonymize":
                    masked[field] = self._anonymize_field(masked[field])

        return masked

    def _anonymize_field(self, value: Any) -> Any:
        """Anonymize a field value."""
        if isinstance(value, str):
            return ''.join(self._random.choices(string.ascii_letters, k=len(value)))
        elif isinstance(value, list) and value:
            return [self._anonymize_field(v) for v in value]
        elif isinstance(value, dict):
            return {k: self._anonymize_field(v) for k, v in value.items()}
        return value

    # =========================================================================
    # Data Seeding
    # =========================================================================

    async def execute_seed(
        self,
        data_set_id: UUID,
        environment: TestEnvironment,
        executed_by: Optional[UUID] = None,
    ) -> DataSeedExecution:
        """Execute data seeding for a data set."""
        execution = DataSeedExecution(
            tenant_id=self.tenant_id,
            data_set_id=data_set_id,
            environment=environment,
            status=TestRunStatus.RUNNING,
            started_at=datetime.utcnow(),
            executed_by=executed_by,
        )
        self.session.add(execution)
        await self.session.flush()
        return execution

    async def complete_seed_execution(
        self,
        execution_id: UUID,
        status: TestRunStatus,
        records_seeded: int = 0,
        records_failed: int = 0,
        error_message: Optional[str] = None,
    ) -> Optional[DataSeedExecution]:
        """Complete a seed execution."""
        result = await self.session.execute(
            select(DataSeedExecution).where(
                and_(
                    DataSeedExecution.id == execution_id,
                    DataSeedExecution.tenant_id == self.tenant_id,
                )
            )
        )
        execution = result.scalar_one_or_none()
        if not execution:
            return None

        execution.status = status
        execution.completed_at = datetime.utcnow()
        execution.duration_seconds = (
            execution.completed_at - execution.started_at
        ).total_seconds()
        execution.records_seeded = records_seeded
        execution.records_failed = records_failed
        execution.error_message = error_message
        await self.session.flush()
        return execution

    async def list_seed_executions(
        self,
        data_set_id: Optional[UUID] = None,
        environment: Optional[TestEnvironment] = None,
        limit: int = 50,
    ) -> List[DataSeedExecution]:
        """List seed executions."""
        query = select(DataSeedExecution).where(
            DataSeedExecution.tenant_id == self.tenant_id
        )
        if data_set_id:
            query = query.where(DataSeedExecution.data_set_id == data_set_id)
        if environment:
            query = query.where(DataSeedExecution.environment == environment)

        query = query.order_by(desc(DataSeedExecution.created_at)).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # Synthetic Data Generators
    # =========================================================================

    async def create_generator(
        self,
        name: str,
        data_type: DataGeneratorType,
        field_generators: Dict[str, Any],
        description: Optional[str] = None,
        fhir_resource_type: Optional[str] = None,
        fhir_profile: Optional[str] = None,
        relationships: Dict[str, Any] = None,
        validation_schema: Dict[str, Any] = None,
    ) -> SyntheticDataGenerator:
        """Create a custom synthetic data generator."""
        generator = SyntheticDataGenerator(
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            data_type=data_type,
            fhir_resource_type=fhir_resource_type,
            fhir_profile=fhir_profile,
            field_generators=field_generators,
            relationships=relationships or {},
            validation_schema=validation_schema,
        )
        self.session.add(generator)
        await self.session.flush()
        return generator

    async def list_generators(
        self,
        data_type: Optional[DataGeneratorType] = None,
    ) -> List[SyntheticDataGenerator]:
        """List synthetic data generators."""
        query = select(SyntheticDataGenerator).where(
            and_(
                SyntheticDataGenerator.tenant_id == self.tenant_id,
                SyntheticDataGenerator.is_active == True,
            )
        )
        if data_type:
            query = query.where(SyntheticDataGenerator.data_type == data_type)

        query = query.order_by(SyntheticDataGenerator.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

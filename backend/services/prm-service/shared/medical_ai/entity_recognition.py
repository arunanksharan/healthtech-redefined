"""
Advanced Medical Entity Recognition Service

EPIC-010: Medical AI Capabilities
US-010.3: Medical Entity Recognition

BioBERT-style medical entity extraction:
- Disease/condition extraction
- Medication identification
- Procedure recognition
- Anatomy mapping
- Lab value extraction
- Temporal information parsing
- SNOMED CT / RxNorm / LOINC normalization
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Set
from uuid import uuid4, UUID
import re


class EntityType(str, Enum):
    """Medical entity types."""
    CONDITION = "condition"
    SYMPTOM = "symptom"
    MEDICATION = "medication"
    PROCEDURE = "procedure"
    ANATOMY = "anatomy"
    LAB_TEST = "lab_test"
    LAB_VALUE = "lab_value"
    VITAL_SIGN = "vital_sign"
    DOSAGE = "dosage"
    FREQUENCY = "frequency"
    DURATION = "duration"
    DEVICE = "device"
    ALLERGY = "allergy"
    FAMILY_HISTORY = "family_history"
    SOCIAL_HISTORY = "social_history"
    TEMPORAL = "temporal"


class NegationStatus(str, Enum):
    """Negation status for entities."""
    AFFIRMED = "affirmed"
    NEGATED = "negated"
    UNCERTAIN = "uncertain"
    HYPOTHETICAL = "hypothetical"
    FAMILY_HISTORY = "family_history"
    HISTORICAL = "historical"


class CodingSystem(str, Enum):
    """Medical coding systems."""
    SNOMED_CT = "SNOMED-CT"
    ICD10_CM = "ICD-10-CM"
    RXNORM = "RxNorm"
    LOINC = "LOINC"
    CPT = "CPT"
    HCPCS = "HCPCS"
    NDC = "NDC"


@dataclass
class NormalizedCode:
    """Normalized medical code."""
    system: CodingSystem
    code: str
    display: str
    confidence: float
    preferred_term: bool = False


@dataclass
class ExtractedEntity:
    """Extracted medical entity with full metadata."""
    entity_id: UUID
    entity_type: EntityType
    text: str
    normalized_text: str
    start_offset: int
    end_offset: int
    confidence: float

    # Context
    negation_status: NegationStatus
    temporal_context: Optional[str] = None
    certainty: float = 1.0

    # Normalized codes
    codes: List[NormalizedCode] = field(default_factory=list)

    # Relationships
    related_entities: List[UUID] = field(default_factory=list)
    modifiers: List[str] = field(default_factory=list)

    # Source
    section: Optional[str] = None
    sentence_index: Optional[int] = None


@dataclass
class EntityRelationship:
    """Relationship between entities."""
    relationship_type: str  # "treats", "causes", "manifestation_of", etc.
    source_entity_id: UUID
    target_entity_id: UUID
    confidence: float


@dataclass
class ExtractionResult:
    """Complete entity extraction result."""
    extraction_id: UUID
    text: str
    entities: List[ExtractedEntity]
    relationships: List[EntityRelationship]
    processing_time_ms: float
    model_version: str
    created_at: datetime


class MedicalEntityExtractor:
    """Advanced medical entity extraction using pattern matching and NER."""

    def __init__(self):
        self.condition_patterns = self._load_condition_patterns()
        self.medication_patterns = self._load_medication_patterns()
        self.anatomy_patterns = self._load_anatomy_patterns()
        self.lab_patterns = self._load_lab_patterns()
        self.snomed_lookup = self._load_snomed_lookup()
        self.rxnorm_lookup = self._load_rxnorm_lookup()
        self.loinc_lookup = self._load_loinc_lookup()

    def _load_condition_patterns(self) -> Dict[str, Dict]:
        """Load condition/disease patterns with SNOMED mappings."""
        return {
            # Cardiovascular
            'hypertension': {
                'patterns': [r'\bhypertension\b', r'\bhigh blood pressure\b', r'\bHTN\b', r'\belevated BP\b'],
                'snomed': '38341003',
                'icd10': 'I10',
                'display': 'Hypertensive disorder'
            },
            'diabetes_type2': {
                'patterns': [r'\btype 2 diabetes\b', r'\bT2DM\b', r'\bDM2\b', r'\bniddm\b', r'\bdiabetes mellitus type 2\b'],
                'snomed': '44054006',
                'icd10': 'E11.9',
                'display': 'Type 2 diabetes mellitus'
            },
            'diabetes_type1': {
                'patterns': [r'\btype 1 diabetes\b', r'\bT1DM\b', r'\bDM1\b', r'\biddm\b'],
                'snomed': '46635009',
                'icd10': 'E10.9',
                'display': 'Type 1 diabetes mellitus'
            },
            'coronary_artery_disease': {
                'patterns': [r'\bcoronary artery disease\b', r'\bCAD\b', r'\bCHD\b', r'\bischemic heart disease\b'],
                'snomed': '53741008',
                'icd10': 'I25.10',
                'display': 'Coronary artery disease'
            },
            'heart_failure': {
                'patterns': [r'\bheart failure\b', r'\bCHF\b', r'\bcongestive heart failure\b', r'\bHF\b'],
                'snomed': '84114007',
                'icd10': 'I50.9',
                'display': 'Heart failure'
            },
            'atrial_fibrillation': {
                'patterns': [r'\batrial fibrillation\b', r'\bAFib\b', r'\bA-fib\b', r'\bAF\b'],
                'snomed': '49436004',
                'icd10': 'I48.91',
                'display': 'Atrial fibrillation'
            },

            # Respiratory
            'asthma': {
                'patterns': [r'\basthma\b', r'\basthmatic\b', r'\breactive airway\b'],
                'snomed': '195967001',
                'icd10': 'J45.909',
                'display': 'Asthma'
            },
            'copd': {
                'patterns': [r'\bCOPD\b', r'\bchronic obstructive pulmonary\b', r'\bemphysema\b', r'\bchronic bronchitis\b'],
                'snomed': '13645005',
                'icd10': 'J44.9',
                'display': 'COPD'
            },
            'pneumonia': {
                'patterns': [r'\bpneumonia\b', r'\bPNA\b', r'\blung infection\b'],
                'snomed': '233604007',
                'icd10': 'J18.9',
                'display': 'Pneumonia'
            },

            # Neurological
            'stroke': {
                'patterns': [r'\bstroke\b', r'\bCVA\b', r'\bcerebrovascular accident\b'],
                'snomed': '230690007',
                'icd10': 'I63.9',
                'display': 'Stroke'
            },
            'migraine': {
                'patterns': [r'\bmigraine\b', r'\bmigrainous\b'],
                'snomed': '37796009',
                'icd10': 'G43.909',
                'display': 'Migraine'
            },
            'epilepsy': {
                'patterns': [r'\bepilepsy\b', r'\bseizure disorder\b'],
                'snomed': '84757009',
                'icd10': 'G40.909',
                'display': 'Epilepsy'
            },

            # Gastrointestinal
            'gerd': {
                'patterns': [r'\bGERD\b', r'\bacid reflux\b', r'\bgastroesophageal reflux\b', r'\bheartburn\b'],
                'snomed': '235595009',
                'icd10': 'K21.0',
                'display': 'GERD'
            },
            'cirrhosis': {
                'patterns': [r'\bcirrhosis\b', r'\bliver cirrhosis\b'],
                'snomed': '19943007',
                'icd10': 'K74.60',
                'display': 'Cirrhosis of liver'
            },

            # Renal
            'ckd': {
                'patterns': [r'\bCKD\b', r'\bchronic kidney disease\b', r'\bchronic renal\b'],
                'snomed': '709044004',
                'icd10': 'N18.9',
                'display': 'Chronic kidney disease'
            },

            # Mental Health
            'depression': {
                'patterns': [r'\bdepression\b', r'\bMDD\b', r'\bmajor depressive\b', r'\bdepressed\b'],
                'snomed': '35489007',
                'icd10': 'F32.9',
                'display': 'Major depressive disorder'
            },
            'anxiety': {
                'patterns': [r'\banxiety\b', r'\bGAD\b', r'\banxious\b', r'\banxiety disorder\b'],
                'snomed': '197480006',
                'icd10': 'F41.9',
                'display': 'Anxiety disorder'
            },

            # Cancer
            'breast_cancer': {
                'patterns': [r'\bbreast cancer\b', r'\bbreast carcinoma\b'],
                'snomed': '254837009',
                'icd10': 'C50.919',
                'display': 'Breast cancer'
            },
            'lung_cancer': {
                'patterns': [r'\blung cancer\b', r'\bpulmonary carcinoma\b', r'\bnsclc\b', r'\bsclc\b'],
                'snomed': '363358000',
                'icd10': 'C34.90',
                'display': 'Lung cancer'
            },
        }

    def _load_medication_patterns(self) -> Dict[str, Dict]:
        """Load medication patterns with RxNorm mappings."""
        return {
            # Cardiovascular
            'metoprolol': {
                'patterns': [r'\bmetoprolol\b', r'\blopressor\b', r'\btoprol\b'],
                'rxnorm': '6918',
                'class': 'Beta blocker',
                'display': 'Metoprolol'
            },
            'lisinopril': {
                'patterns': [r'\blisinopril\b', r'\bprinivil\b', r'\bzestril\b'],
                'rxnorm': '29046',
                'class': 'ACE inhibitor',
                'display': 'Lisinopril'
            },
            'amlodipine': {
                'patterns': [r'\bamlodipine\b', r'\bnorvasc\b'],
                'rxnorm': '17767',
                'class': 'Calcium channel blocker',
                'display': 'Amlodipine'
            },
            'atorvastatin': {
                'patterns': [r'\batorvastatin\b', r'\blipitor\b'],
                'rxnorm': '83367',
                'class': 'Statin',
                'display': 'Atorvastatin'
            },
            'aspirin': {
                'patterns': [r'\baspirin\b', r'\bASA\b', r'\bacetylsalicylic acid\b'],
                'rxnorm': '1191',
                'class': 'Antiplatelet',
                'display': 'Aspirin'
            },
            'warfarin': {
                'patterns': [r'\bwarfarin\b', r'\bcoumadin\b'],
                'rxnorm': '11289',
                'class': 'Anticoagulant',
                'display': 'Warfarin'
            },
            'clopidogrel': {
                'patterns': [r'\bclopidogrel\b', r'\bplavix\b'],
                'rxnorm': '32968',
                'class': 'Antiplatelet',
                'display': 'Clopidogrel'
            },

            # Diabetes
            'metformin': {
                'patterns': [r'\bmetformin\b', r'\bglucophage\b'],
                'rxnorm': '6809',
                'class': 'Biguanide',
                'display': 'Metformin'
            },
            'insulin_glargine': {
                'patterns': [r'\binsulin glargine\b', r'\blantus\b', r'\bbasaglar\b'],
                'rxnorm': '274783',
                'class': 'Long-acting insulin',
                'display': 'Insulin glargine'
            },
            'sitagliptin': {
                'patterns': [r'\bsitagliptin\b', r'\bjanuvia\b'],
                'rxnorm': '593411',
                'class': 'DPP-4 inhibitor',
                'display': 'Sitagliptin'
            },

            # Pain/Anti-inflammatory
            'ibuprofen': {
                'patterns': [r'\bibuprofen\b', r'\badvil\b', r'\bmotrin\b'],
                'rxnorm': '5640',
                'class': 'NSAID',
                'display': 'Ibuprofen'
            },
            'acetaminophen': {
                'patterns': [r'\bacetaminophen\b', r'\btylenol\b', r'\bAPAP\b'],
                'rxnorm': '161',
                'class': 'Analgesic',
                'display': 'Acetaminophen'
            },
            'gabapentin': {
                'patterns': [r'\bgabapentin\b', r'\bneurontin\b'],
                'rxnorm': '25480',
                'class': 'Anticonvulsant',
                'display': 'Gabapentin'
            },

            # Respiratory
            'albuterol': {
                'patterns': [r'\balbuterol\b', r'\bventolin\b', r'\bproair\b', r'\bproventil\b'],
                'rxnorm': '435',
                'class': 'Beta-2 agonist',
                'display': 'Albuterol'
            },
            'fluticasone': {
                'patterns': [r'\bfluticasone\b', r'\bflonase\b', r'\bflovent\b'],
                'rxnorm': '41126',
                'class': 'Corticosteroid',
                'display': 'Fluticasone'
            },

            # Mental Health
            'sertraline': {
                'patterns': [r'\bsertraline\b', r'\bzoloft\b'],
                'rxnorm': '36437',
                'class': 'SSRI',
                'display': 'Sertraline'
            },
            'escitalopram': {
                'patterns': [r'\bescitalopram\b', r'\blexapro\b'],
                'rxnorm': '321988',
                'class': 'SSRI',
                'display': 'Escitalopram'
            },
            'lorazepam': {
                'patterns': [r'\blorazepam\b', r'\bativan\b'],
                'rxnorm': '6470',
                'class': 'Benzodiazepine',
                'display': 'Lorazepam'
            },

            # GI
            'omeprazole': {
                'patterns': [r'\bomeprazole\b', r'\bprilosec\b'],
                'rxnorm': '7646',
                'class': 'PPI',
                'display': 'Omeprazole'
            },
            'pantoprazole': {
                'patterns': [r'\bpantoprazole\b', r'\bprotonix\b'],
                'rxnorm': '40790',
                'class': 'PPI',
                'display': 'Pantoprazole'
            },
        }

    def _load_anatomy_patterns(self) -> Dict[str, Dict]:
        """Load anatomy patterns with SNOMED mappings."""
        return {
            # Head and Neck
            'brain': {'patterns': [r'\bbrain\b', r'\bcerebral\b', r'\bcerebrum\b'], 'snomed': '12738006'},
            'heart': {'patterns': [r'\bheart\b', r'\bcardiac\b', r'\bmyocardium\b'], 'snomed': '80891009'},
            'lung': {'patterns': [r'\blungs?\b', r'\bpulmonary\b'], 'snomed': '39607008'},
            'liver': {'patterns': [r'\bliver\b', r'\bhepatic\b'], 'snomed': '10200004'},
            'kidney': {'patterns': [r'\bkidneys?\b', r'\brenal\b'], 'snomed': '64033007'},
            'stomach': {'patterns': [r'\bstomach\b', r'\bgastric\b'], 'snomed': '69695003'},
            'colon': {'patterns': [r'\bcolon\b', r'\bcolonic\b', r'\blarge intestine\b'], 'snomed': '71854001'},
            'pancreas': {'patterns': [r'\bpancreas\b', r'\bpancreatic\b'], 'snomed': '15776009'},
            'thyroid': {'patterns': [r'\bthyroid\b'], 'snomed': '69748006'},
            'spine': {'patterns': [r'\bspine\b', r'\bspinal\b', r'\bvertebr\w*\b'], 'snomed': '421060004'},
        }

    def _load_lab_patterns(self) -> Dict[str, Dict]:
        """Load lab test patterns with LOINC mappings."""
        return {
            # Chemistry
            'glucose': {
                'patterns': [r'\bglucose\b', r'\bblood sugar\b', r'\bBS\b', r'\bFBS\b'],
                'loinc': '2345-7',
                'unit': 'mg/dL',
                'display': 'Glucose'
            },
            'hemoglobin_a1c': {
                'patterns': [r'\bA1C\b', r'\bHbA1c\b', r'\bhemoglobin A1c\b', r'\bglycated hemoglobin\b'],
                'loinc': '4548-4',
                'unit': '%',
                'display': 'Hemoglobin A1c'
            },
            'creatinine': {
                'patterns': [r'\bcreatinine\b', r'\bCr\b', r'\bserum creatinine\b'],
                'loinc': '2160-0',
                'unit': 'mg/dL',
                'display': 'Creatinine'
            },
            'bun': {
                'patterns': [r'\bBUN\b', r'\bblood urea nitrogen\b'],
                'loinc': '3094-0',
                'unit': 'mg/dL',
                'display': 'BUN'
            },
            'egfr': {
                'patterns': [r'\beGFR\b', r'\bGFR\b', r'\bestimated GFR\b'],
                'loinc': '33914-3',
                'unit': 'mL/min/1.73m2',
                'display': 'eGFR'
            },
            'sodium': {
                'patterns': [r'\bsodium\b', r'\bNa\b'],
                'loinc': '2951-2',
                'unit': 'mEq/L',
                'display': 'Sodium'
            },
            'potassium': {
                'patterns': [r'\bpotassium\b', r'\bK\b'],
                'loinc': '2823-3',
                'unit': 'mEq/L',
                'display': 'Potassium'
            },

            # Hematology
            'hemoglobin': {
                'patterns': [r'\bhemoglobin\b', r'\bHgb\b', r'\bHb\b'],
                'loinc': '718-7',
                'unit': 'g/dL',
                'display': 'Hemoglobin'
            },
            'wbc': {
                'patterns': [r'\bWBC\b', r'\bwhite blood cell\b', r'\bleukocyte\b'],
                'loinc': '6690-2',
                'unit': 'K/uL',
                'display': 'WBC'
            },
            'platelet': {
                'patterns': [r'\bplatelet\b', r'\bPLT\b', r'\bthrombocyte\b'],
                'loinc': '777-3',
                'unit': 'K/uL',
                'display': 'Platelet count'
            },

            # Lipids
            'cholesterol': {
                'patterns': [r'\bcholesterol\b', r'\btotal cholesterol\b'],
                'loinc': '2093-3',
                'unit': 'mg/dL',
                'display': 'Total cholesterol'
            },
            'ldl': {
                'patterns': [r'\bLDL\b', r'\bLDL cholesterol\b', r'\bLDL-C\b'],
                'loinc': '2089-1',
                'unit': 'mg/dL',
                'display': 'LDL cholesterol'
            },
            'hdl': {
                'patterns': [r'\bHDL\b', r'\bHDL cholesterol\b', r'\bHDL-C\b'],
                'loinc': '2085-9',
                'unit': 'mg/dL',
                'display': 'HDL cholesterol'
            },
            'triglycerides': {
                'patterns': [r'\btriglycerides\b', r'\bTG\b'],
                'loinc': '2571-8',
                'unit': 'mg/dL',
                'display': 'Triglycerides'
            },

            # Cardiac
            'troponin': {
                'patterns': [r'\btroponin\b', r'\btrop\b', r'\bTnI\b', r'\bTnT\b'],
                'loinc': '10839-9',
                'unit': 'ng/mL',
                'display': 'Troponin'
            },
            'bnp': {
                'patterns': [r'\bBNP\b', r'\bNT-proBNP\b', r'\bproBNP\b'],
                'loinc': '30934-4',
                'unit': 'pg/mL',
                'display': 'BNP'
            },
        }

    def _load_snomed_lookup(self) -> Dict[str, str]:
        """Load SNOMED CT display terms."""
        lookup = {}
        for condition_data in self.condition_patterns.values():
            lookup[condition_data['snomed']] = condition_data['display']
        return lookup

    def _load_rxnorm_lookup(self) -> Dict[str, str]:
        """Load RxNorm display terms."""
        lookup = {}
        for med_data in self.medication_patterns.values():
            lookup[med_data['rxnorm']] = med_data['display']
        return lookup

    def _load_loinc_lookup(self) -> Dict[str, str]:
        """Load LOINC display terms."""
        lookup = {}
        for lab_data in self.lab_patterns.values():
            lookup[lab_data['loinc']] = lab_data['display']
        return lookup

    async def extract_entities(
        self,
        text: str,
        entity_types: Optional[List[EntityType]] = None
    ) -> ExtractionResult:
        """Extract all medical entities from text."""
        import time
        start_time = time.time()

        entities: List[ExtractedEntity] = []
        relationships: List[EntityRelationship] = []

        # Extract by entity type
        if entity_types is None:
            entity_types = list(EntityType)

        if EntityType.CONDITION in entity_types:
            entities.extend(self._extract_conditions(text))

        if EntityType.MEDICATION in entity_types:
            entities.extend(self._extract_medications(text))

        if EntityType.ANATOMY in entity_types:
            entities.extend(self._extract_anatomy(text))

        if EntityType.LAB_TEST in entity_types or EntityType.LAB_VALUE in entity_types:
            entities.extend(self._extract_labs(text))

        if EntityType.DOSAGE in entity_types:
            entities.extend(self._extract_dosages(text))

        if EntityType.TEMPORAL in entity_types:
            entities.extend(self._extract_temporal(text))

        if EntityType.SYMPTOM in entity_types:
            entities.extend(self._extract_symptoms(text))

        # Apply negation detection
        entities = self._apply_negation_detection(entities, text)

        # Extract relationships
        relationships = self._extract_relationships(entities, text)

        processing_time = (time.time() - start_time) * 1000

        return ExtractionResult(
            extraction_id=uuid4(),
            text=text,
            entities=entities,
            relationships=relationships,
            processing_time_ms=processing_time,
            model_version="1.0.0",
            created_at=datetime.now(timezone.utc)
        )

    def _extract_conditions(self, text: str) -> List[ExtractedEntity]:
        """Extract condition/disease entities."""
        entities = []
        text_lower = text.lower()

        for condition_name, condition_data in self.condition_patterns.items():
            for pattern in condition_data['patterns']:
                for match in re.finditer(pattern, text_lower, re.IGNORECASE):
                    codes = [
                        NormalizedCode(
                            system=CodingSystem.SNOMED_CT,
                            code=condition_data['snomed'],
                            display=condition_data['display'],
                            confidence=0.9,
                            preferred_term=True
                        ),
                        NormalizedCode(
                            system=CodingSystem.ICD10_CM,
                            code=condition_data['icd10'],
                            display=condition_data['display'],
                            confidence=0.85,
                            preferred_term=False
                        )
                    ]

                    entities.append(ExtractedEntity(
                        entity_id=uuid4(),
                        entity_type=EntityType.CONDITION,
                        text=match.group(),
                        normalized_text=condition_data['display'],
                        start_offset=match.start(),
                        end_offset=match.end(),
                        confidence=0.9,
                        negation_status=NegationStatus.AFFIRMED,
                        codes=codes
                    ))
                    break  # One match per condition

        return entities

    def _extract_medications(self, text: str) -> List[ExtractedEntity]:
        """Extract medication entities."""
        entities = []
        text_lower = text.lower()

        for med_name, med_data in self.medication_patterns.items():
            for pattern in med_data['patterns']:
                for match in re.finditer(pattern, text_lower, re.IGNORECASE):
                    codes = [
                        NormalizedCode(
                            system=CodingSystem.RXNORM,
                            code=med_data['rxnorm'],
                            display=med_data['display'],
                            confidence=0.92,
                            preferred_term=True
                        )
                    ]

                    entities.append(ExtractedEntity(
                        entity_id=uuid4(),
                        entity_type=EntityType.MEDICATION,
                        text=match.group(),
                        normalized_text=med_data['display'],
                        start_offset=match.start(),
                        end_offset=match.end(),
                        confidence=0.92,
                        negation_status=NegationStatus.AFFIRMED,
                        codes=codes,
                        modifiers=[med_data['class']]
                    ))
                    break

        return entities

    def _extract_anatomy(self, text: str) -> List[ExtractedEntity]:
        """Extract anatomy entities."""
        entities = []
        text_lower = text.lower()

        for anatomy_name, anatomy_data in self.anatomy_patterns.items():
            for pattern in anatomy_data['patterns']:
                for match in re.finditer(pattern, text_lower, re.IGNORECASE):
                    codes = [
                        NormalizedCode(
                            system=CodingSystem.SNOMED_CT,
                            code=anatomy_data['snomed'],
                            display=anatomy_name.replace('_', ' ').title(),
                            confidence=0.95,
                            preferred_term=True
                        )
                    ]

                    entities.append(ExtractedEntity(
                        entity_id=uuid4(),
                        entity_type=EntityType.ANATOMY,
                        text=match.group(),
                        normalized_text=anatomy_name.replace('_', ' ').title(),
                        start_offset=match.start(),
                        end_offset=match.end(),
                        confidence=0.95,
                        negation_status=NegationStatus.AFFIRMED,
                        codes=codes
                    ))

        return entities

    def _extract_labs(self, text: str) -> List[ExtractedEntity]:
        """Extract lab test and value entities."""
        entities = []
        text_lower = text.lower()

        # Extract lab names
        for lab_name, lab_data in self.lab_patterns.items():
            for pattern in lab_data['patterns']:
                for match in re.finditer(pattern, text_lower, re.IGNORECASE):
                    codes = [
                        NormalizedCode(
                            system=CodingSystem.LOINC,
                            code=lab_data['loinc'],
                            display=lab_data['display'],
                            confidence=0.9,
                            preferred_term=True
                        )
                    ]

                    entity = ExtractedEntity(
                        entity_id=uuid4(),
                        entity_type=EntityType.LAB_TEST,
                        text=match.group(),
                        normalized_text=lab_data['display'],
                        start_offset=match.start(),
                        end_offset=match.end(),
                        confidence=0.9,
                        negation_status=NegationStatus.AFFIRMED,
                        codes=codes,
                        modifiers=[lab_data['unit']]
                    )

                    # Try to extract associated value
                    value_pattern = rf'{pattern}\s*(?:of|is|was|:)?\s*(\d+\.?\d*)\s*({lab_data["unit"]})?'
                    value_match = re.search(value_pattern, text, re.IGNORECASE)
                    if value_match:
                        entity.modifiers.append(f"value: {value_match.group(1)}")

                    entities.append(entity)
                    break

        # Extract standalone numeric lab values
        value_patterns = [
            r'(\d+\.?\d*)\s*(mg/dL|mmol/L|g/dL|%|mEq/L|K/uL|ng/mL|pg/mL)',
        ]

        for pattern in value_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append(ExtractedEntity(
                    entity_id=uuid4(),
                    entity_type=EntityType.LAB_VALUE,
                    text=match.group(),
                    normalized_text=match.group(),
                    start_offset=match.start(),
                    end_offset=match.end(),
                    confidence=0.85,
                    negation_status=NegationStatus.AFFIRMED,
                    codes=[]
                ))

        return entities

    def _extract_dosages(self, text: str) -> List[ExtractedEntity]:
        """Extract medication dosage entities."""
        entities = []

        dosage_patterns = [
            r'(\d+\.?\d*)\s*(mg|mcg|g|mL|units?|IU)',
            r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*(mg|mcg|g)',
        ]

        for pattern in dosage_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append(ExtractedEntity(
                    entity_id=uuid4(),
                    entity_type=EntityType.DOSAGE,
                    text=match.group(),
                    normalized_text=match.group().lower(),
                    start_offset=match.start(),
                    end_offset=match.end(),
                    confidence=0.95,
                    negation_status=NegationStatus.AFFIRMED,
                    codes=[]
                ))

        return entities

    def _extract_temporal(self, text: str) -> List[ExtractedEntity]:
        """Extract temporal information."""
        entities = []

        temporal_patterns = [
            r'(\d+)\s*(day|week|month|year|hour|minute)s?\s*ago',
            r'(yesterday|today|last week|last month)',
            r'for\s+(\d+)\s*(day|week|month|year)s?',
            r'(daily|twice daily|weekly|monthly|as needed|PRN)',
            r'(morning|evening|night|bedtime)',
        ]

        for pattern in temporal_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append(ExtractedEntity(
                    entity_id=uuid4(),
                    entity_type=EntityType.TEMPORAL,
                    text=match.group(),
                    normalized_text=match.group().lower(),
                    start_offset=match.start(),
                    end_offset=match.end(),
                    confidence=0.9,
                    negation_status=NegationStatus.AFFIRMED,
                    codes=[]
                ))

        return entities

    def _extract_symptoms(self, text: str) -> List[ExtractedEntity]:
        """Extract symptom entities."""
        entities = []
        text_lower = text.lower()

        symptom_patterns = {
            'pain': r'\b(pain|ache|aching|sore|soreness)\b',
            'nausea': r'\b(nausea|nauseous|queasy)\b',
            'vomiting': r'\b(vomit|vomiting|throwing up)\b',
            'fever': r'\b(fever|febrile|temperature)\b',
            'fatigue': r'\b(fatigue|fatigue|tired|tiredness|exhaustion)\b',
            'headache': r'\b(headache|head pain|cephalalgia)\b',
            'dizziness': r'\b(dizzy|dizziness|lightheaded|vertigo)\b',
            'shortness_of_breath': r'\b(shortness of breath|dyspnea|SOB|difficulty breathing)\b',
            'cough': r'\b(cough|coughing)\b',
            'chest_pain': r'\b(chest pain|chest discomfort)\b',
            'swelling': r'\b(swell|swelling|edema|swollen)\b',
            'rash': r'\b(rash|hives|urticaria)\b',
        }

        for symptom_name, pattern in symptom_patterns.items():
            for match in re.finditer(pattern, text_lower, re.IGNORECASE):
                entities.append(ExtractedEntity(
                    entity_id=uuid4(),
                    entity_type=EntityType.SYMPTOM,
                    text=match.group(),
                    normalized_text=symptom_name.replace('_', ' ').title(),
                    start_offset=match.start(),
                    end_offset=match.end(),
                    confidence=0.85,
                    negation_status=NegationStatus.AFFIRMED,
                    codes=[]
                ))

        return entities

    def _apply_negation_detection(
        self,
        entities: List[ExtractedEntity],
        text: str
    ) -> List[ExtractedEntity]:
        """Apply negation detection to entities using NegEx-style rules."""
        # Negation triggers (pre-negation)
        pre_negation = [
            'no', 'not', 'without', 'denies', 'denied', 'negative for',
            'no evidence of', 'rules out', 'r/o', 'absence of', 'free of',
            'never had', 'no history of'
        ]

        # Uncertainty triggers
        uncertainty = [
            'possible', 'possibly', 'probable', 'probably', 'suggests',
            'may have', 'might have', 'could be', 'suspicious for',
            'concerning for', 'cannot rule out'
        ]

        # Family history triggers
        family = [
            'family history of', 'fh of', 'father had', 'mother had',
            'sibling with', 'brother with', 'sister with', 'parent with'
        ]

        # Historical triggers
        historical = [
            'history of', 'h/o', 'previous', 'prior', 'past', 'former',
            'resolved', 'had'
        ]

        text_lower = text.lower()

        for entity in entities:
            # Get context window (30 chars before entity)
            start = max(0, entity.start_offset - 30)
            context = text_lower[start:entity.start_offset].strip()

            # Check for negation
            if any(neg in context for neg in pre_negation):
                entity.negation_status = NegationStatus.NEGATED
                entity.certainty = 0.9

            # Check for uncertainty
            elif any(unc in context for unc in uncertainty):
                entity.negation_status = NegationStatus.UNCERTAIN
                entity.certainty = 0.5

            # Check for family history
            elif any(fam in context for fam in family):
                entity.negation_status = NegationStatus.FAMILY_HISTORY
                entity.certainty = 0.95

            # Check for historical
            elif any(hist in context for hist in historical):
                entity.negation_status = NegationStatus.HISTORICAL
                entity.certainty = 0.9

        return entities

    def _extract_relationships(
        self,
        entities: List[ExtractedEntity],
        text: str
    ) -> List[EntityRelationship]:
        """Extract relationships between entities."""
        relationships = []

        # Find medication-condition relationships
        medications = [e for e in entities if e.entity_type == EntityType.MEDICATION]
        conditions = [e for e in entities if e.entity_type == EntityType.CONDITION]

        treatment_patterns = [
            r'(taking|on|prescribed|for)\s+\w+\s+for\s+',
            r'\w+\s+(treats?|for|manages?)',
        ]

        for med in medications:
            for condition in conditions:
                # Check if they're mentioned close together
                if abs(med.start_offset - condition.start_offset) < 100:
                    relationships.append(EntityRelationship(
                        relationship_type="treats",
                        source_entity_id=med.entity_id,
                        target_entity_id=condition.entity_id,
                        confidence=0.7
                    ))

        # Find dosage-medication relationships
        dosages = [e for e in entities if e.entity_type == EntityType.DOSAGE]

        for dosage in dosages:
            for med in medications:
                if abs(dosage.start_offset - med.end_offset) < 20:
                    relationships.append(EntityRelationship(
                        relationship_type="dose_of",
                        source_entity_id=dosage.entity_id,
                        target_entity_id=med.entity_id,
                        confidence=0.9
                    ))

        return relationships


# Global instance
medical_entity_extractor = MedicalEntityExtractor()
